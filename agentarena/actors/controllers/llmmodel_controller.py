import json
from typing import Any
from typing import List

import httpx
from fastapi import APIRouter
from fastapi import Query
from nats.aio.msg import Msg
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import select

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.subscribing_service import SubscribingService
from agentarena.models.job import JobLock
from agentarena.models.llm import LlmModel
from agentarena.models.llm import LlmModelCreate
from agentarena.models.llm import LlmModelPrice
from agentarena.models.llm import LlmModelPriceCreate
from agentarena.models.llm import LlmModelUpdate
from agentarena.models.public import LlmModelPublic


class LlmModelController(
    ModelController[LlmModel, LlmModelCreate, LlmModelUpdate, LlmModelPublic],
    SubscribingService,
):

    def __init__(
        self,
        base_path: str = "/api",
        message_broker: MessageBroker = Field(
            description="Message broker client for publishing messages"
        ),
        model_service: ModelService[LlmModel, LlmModelCreate] = Field(),
        pricing_service: ModelService[LlmModelPrice, LlmModelPriceCreate] = Field(),
        configured_models: List[dict[str, Any]] = Field(),
        logging: LoggingService = Field(),
    ):

        self.configured_models = configured_models
        self.message_broker = message_broker
        self.pricing_service = pricing_service
        super().__init__(
            base_path=base_path,
            model_name="llmmodel",
            model_create=LlmModelCreate,
            model_update=LlmModelUpdate,
            model_public=LlmModelPublic,
            model_service=model_service,
            logging=logging,
        )

        to_subscribe = [
            # actor.eval.<prompt_type>.request.job_id
            (f"actor.eval.*.request.*", self.handle_eval_request),
        ]
        SubscribingService.__init__(self, to_subscribe, self.log)

    async def handle_eval_request(self, msg: Msg):
        parts = msg.subject.split(".")
        prompt_type = parts[2]
        job_id = parts[-1]
        log = self.log.bind(prompt_type=prompt_type, job_id=job_id, channel=msg.subject)
        log.info("Eval request received", msg=msg)
        with self.model_service.get_session() as session:
            job_lock = session.get(JobLock, job_id)
            if job_lock:
                log.debug("Job is locked, ignoring")
                return
            job_lock = JobLock(id=job_id)
            try:
                session.add(job_lock)
                session.commit()
                log.info("Job lock acquired")
            except Exception as e:
                errstr = "already locked" if "IntegrityError" in str(e) else str(e)
                log.debug("Failed to acquire job lock", error=errstr)
                return

            req = json.loads(msg.data)
            strategies = req["strategies"]

    async def get_model_list(self, session: Session) -> List[LlmModelPublic]:
        db_models = session.exec(select(LlmModel)).all()
        map = {x.model_id: x for x in db_models}
        for model in self.configured_models:
            if model["key"] not in map:
                llm_model = LlmModelCreate(
                    name=model["name"],
                    model_id=model["key"],
                    canonical_id=model.get("canonical_id", ""),
                    supports_json=model.get("supports_json", False),
                    supports_schema=model.get("supports_schema", False),
                    score=model.get("score", 0),
                )
                created, _ = await self.model_service.create(llm_model, session)
                if created:
                    self.log.info("Created model", model=created)
                    map[model["key"]] = created
                    session.commit()
        keys = list(map.keys())
        keys.sort()
        return [self.convert_to_public(map[k]) for k in keys]

    async def update_pricing(self, session: Session):
        db_models = session.exec(select(LlmModel)).all()
        prices = session.exec(select(LlmModelPrice)).all()
        for price in prices:
            session.delete(price)
        session.commit()

        model_data = httpx.get("https://openrouter.ai/api/v1/models")
        model_data.raise_for_status()
        model_data = model_data.json()
        model_data = model_data["data"]
        models = {f'openrouter/{x["id"]}': x for x in model_data}
        for model in db_models:
            if model.model_id not in models:
                if model.active:
                    if "openrouter" in model.model_id:
                        model.active = False
                        notes = model.notes
                        if notes is None:
                            notes = ""
                        elif notes:
                            notes += "\n\n"
                        notes += "Model is no longer available in OpenRouter API"
                        model.notes = notes
                        self.log.info("Deactivating model", model=model)
                    else:
                        self.log.info("Not an openrouter model, skipping", model=model)
                else:
                    self.log.info(
                        "Model is not found in Openrouter data and not active, skipping",
                        model=model,
                    )
                continue
            model_data = models[model.model_id]
            model.canonical_id = model_data.get("canonical_slug", "")
            # set json/schema support
            params = model_data["supported_parameters"]
            supports_json = "response_format" in params or "structured_output" in params
            model.supports_json = supports_json
            supports_schema = any(
                param in params
                for param in ["functions", "tools", "function_call", "tool_choice"]
            )
            model.supports_schema = supports_schema
            # set score
            score = 0
            if supports_json:
                score += 10
            if supports_schema:
                score += 10
            model.score = score
            session.flush()

            # set pricing
            model_pricing = model_data["pricing"]
            pricing = LlmModelPriceCreate(
                llm_model_id=model.id,
                prompt_price=model_pricing["prompt"],
                completion_price=model_pricing["completion"],
                request_price=model_pricing["request"],
                image_price=model_pricing["image"],
                web_search_price=model_pricing["web_search"],
                internal_reasoning_price=model_pricing["internal_reasoning"],
                context_length=model_data["top_provider"]["context_length"],
            )
            pricing, _ = await self.pricing_service.create(pricing, session)
            if not pricing:
                self.log.info("Failed to create pricing", pricing=pricing)
            else:
                self.log.info("Created pricing", pricing=pricing)
        session.commit()

    async def disable_expensive_models(
        self, session: Session, max_price: float = 0.00000125
    ):
        prices = session.exec(select(LlmModelPrice)).all()
        disabled = []
        for price in prices:
            if price.prompt_price > max_price:
                model = session.get(LlmModel, price.llm_model_id)
                if model:
                    model.active = False
                    notes = model.notes
                    if notes is None:
                        notes = ""
                    elif notes:
                        notes += "\n\n"
                    notes += "Model is too expensive, disabled by system"
                    model.notes = notes
                    session.add(model)
                    disabled.append(model.model_id)
        session.commit()
        return disabled

    def get_router(self):
        router = APIRouter(prefix=self.base_path, tags=[self.model_name])

        @router.post("/update-pricing")
        async def update_pricing():
            with self.model_service.get_session() as session:
                await self.update_pricing(session)
                return {"message": "Pricing updated"}

        @router.post("/disable-expensive-models")
        async def disable_expensive_models(max_price: float = Query(0.00000125)):
            with self.model_service.get_session() as session:
                disabled = await self.disable_expensive_models(session, max_price)
                return {"message": "Expensive models disabled", "disabled": disabled}

        return self.add_routes(router)
