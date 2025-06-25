from typing import Dict
from typing import List

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from sqlmodel import Field
from sqlmodel import Session

from agentarena.actors.models import Strategy
from agentarena.actors.models import StrategyCreate
from agentarena.actors.models import StrategyPrompt
from agentarena.actors.models import StrategyPromptCreate
from agentarena.actors.models import StrategyPublic
from agentarena.actors.models import StrategyUpdate
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.jinja_renderer import JinjaRenderer
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService


class StrategyController(
    ModelController[Strategy, StrategyCreate, StrategyUpdate, StrategyPublic]
):

    def __init__(
        self,
        base_path: str = "/api",
        message_broker: MessageBroker = Field(
            description="Message broker client for publishing messages"
        ),
        prompt_service: ModelService[StrategyPrompt, StrategyPromptCreate] = Field(
            description="prompt service",
        ),
        strategy_service: ModelService[Strategy, StrategyCreate] = Field(
            description="strategy service"
        ),
        template_service: JinjaRenderer = Field(description="The template service"),
        uuid_service: UUIDService = Field(description="UUID Service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.message_broker = message_broker
        self.prompt_service = prompt_service
        self.uuid_service = uuid_service
        super().__init__(
            base_path=base_path,
            model_name="Strategy",
            model_create=StrategyCreate,
            model_update=StrategyUpdate,
            model_public=StrategyPublic,
            model_service=strategy_service,
            template_service=template_service,
            logging=logging,
        )

    async def create_strategy(
        self, req: StrategyCreate, session: Session
    ) -> StrategyPublic:
        log = self.log.bind(method="create_strategy", strategy=req.name)
        prompts = req.prompts
        del req.prompts
        strategy, result = await self.model_service.create(req, session)
        if not result.success:
            raise HTTPException(status_code=422, detail=result.model_dump())
        if not strategy:
            raise HTTPException(status_code=422, detail="internal error")

        session.commit()
        log = log.bind(strategy_id=strategy.id)

        for p in prompts:
            to_create = StrategyPrompt(
                id=self.uuid_service.make_id(),
                prompt=p.prompt,
                key=p.key,
                strategy_id=strategy.id,
            )

            # because these aren't many-to-many, we just directly add the object to the list
            # and commit to save

            strategy.prompts.append(to_create)

        log.info("Added prompts", ct=len(prompts))
        session.commit()

        log.info("created")
        return strategy.get_public()

    def get_router(self):
        prefix = self.base_path
        self.log.info("setting up routes", path=prefix)
        router = APIRouter(prefix=prefix, tags=["arena"])

        @router.post("/", response_model=StrategyPublic)
        async def create(req: StrategyCreate = Body(...)):
            with self.model_service.get_session() as session:
                return await self.create_strategy(req, session)

        @router.get("/{obj_id}.{format}", response_model=str)
        async def get_md(obj_id: str, format: str = "md"):
            with self.model_service.get_session() as session:
                return await self.get_model_with_format(obj_id, session, format=format)

        @router.get("/{obj_id}", response_model=StrategyPublic)
        async def get(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.get_model(obj_id, session)

        @router.get("", response_model=List[StrategyPublic])
        async def list_all():
            with self.model_service.get_session() as session:
                return await self.get_model_list(session)

        @router.put("/", response_model=StrategyPublic)
        async def update(req_id: str, req: StrategyUpdate = Body(...)):
            with self.model_service.get_session() as session:
                return await self.update_model(req_id, req, session)

        @router.delete("/{obj_id}", response_model=Dict[str, bool])
        async def delete(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.delete_model(obj_id, session)

        return router
