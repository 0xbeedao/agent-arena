"""
Responder controller for Agent Response endpoints
"""

from typing import Optional
from typing import Tuple

from fastapi import BackgroundTasks
from fastapi import Body
from fastapi import HTTPException
from nats.aio.msg import Msg
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import select

from agentarena.actors.models import Agent
from agentarena.actors.models import AgentCreate
from agentarena.actors.models import AgentPublic
from agentarena.actors.models import AgentUpdate
from agentarena.actors.services.template_service import TemplateService
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.llm_service import LLMService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.subscribing_service import SubscribingService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import JobResponseState
from agentarena.models.constants import JobState
from agentarena.models.constants import PromptType
from agentarena.models.job import GenerateJob
from agentarena.models.job import GenerateJobCreate
from agentarena.models.job import JobResponse
from agentarena.models.requests import HealthStatus
from agentarena.models.requests import ParticipantRequest


class AgentController(
    ModelController[Agent, AgentCreate, AgentUpdate, AgentPublic], SubscribingService
):

    def __init__(
        self,
        base_path: str = "/api",
        agent_service: ModelService[Agent, AgentCreate] = Field(
            description="the participant service"
        ),
        job_service: ModelService[GenerateJob, GenerateJobCreate] = Field(),
        llm_service: LLMService = Field(),
        message_broker: MessageBroker = Field(
            description="Message broker client for publishing messages"
        ),
        template_service: TemplateService = Field(),
        uuid_service: UUIDService = Field(description="UUID Service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        super().__init__(
            base_path=base_path,
            model_name="agent",
            model_create=AgentCreate,
            model_update=AgentUpdate,
            model_public=AgentPublic,
            model_service=agent_service,
            logging=logging,
        )
        to_subscribe = [
            ("actor.agent.health.request", self.healthcheck_message),
        ]
        # Initialize the SubscribingService with the subscriptions
        SubscribingService.__init__(self, to_subscribe, self.log)
        self.job_service = job_service
        self.llm_service = llm_service
        self.message_broker = message_broker
        self.template_service = template_service
        self.uuid_service = uuid_service

    async def healthcheck_message(self, msg: Msg) -> None:
        """
        Handle healthcheck requests for agents.
        """
        self.log.info("healthcheck message received", msg=msg)
        participant_id = msg.data.decode("utf-8")
        with self.model_service.db_service.get_session() as session:
            response = await self.healthcheck(participant_id, session)
            await self.message_broker.publish_response(msg, response)

    async def healthcheck(self, participant_id: str, session: Session) -> JobResponse:
        stmt = select(Agent).where(Agent.participant_id == participant_id)

        agent = session.exec(stmt).one_or_none()

        uuid = self.uuid_service.make_id()
        self.log.info(
            "healthcheck",
            participant_id=participant_id,
            participant=agent,
            uuid=uuid,
        )

        if not agent:
            return JobResponse(
                channel="",
                state=JobResponseState.FAIL,
                message=f"no such responder: {participant_id}",
                job_id=uuid,
                data=HealthStatus(
                    name=participant_id,
                    state="FAIL",
                    version="1",
                ).model_dump_json(),
                url="",
            )

        self.log.info("healthcheck complete", uuid=uuid)

        channel = f"actor.agent.health.response.{participant_id}"
        response = JobResponse(
            channel=channel,
            state=JobResponseState.COMPLETE,
            message="OK",
            job_id=uuid,
            data=HealthStatus(
                name=agent.name, state="OK", version="1"
            ).model_dump_json(),
            url=f"{self.base_path}/{participant_id}/health",
        )
        return response

    async def agent_request(
        self,
        participant_id: str,
        req: ParticipantRequest,
        session: Session,
        background_tasks: BackgroundTasks,
    ):
        stmt = select(Agent).where(Agent.participant_id == participant_id)
        agent = session.exec(stmt).one_or_none()
        job_id = req.job_id
        log = self.log.bind(job=job_id, cmd=req.command, participant=participant_id)
        url = f"{self.base_path}/agent/{participant_id}/request"
        if not agent:
            log.info("No such agent")
            return JobResponse(
                channel="",
                state=JobResponseState.FAIL,
                message=f"no such responder: {participant_id}",
                job_id=job_id,
                url=url,
            )

        # do we already have this job?
        stmt = select(GenerateJob).where(GenerateJob.job_id == job_id)
        job = session.exec(stmt).one_or_none()
        if job:
            response_state = JobResponseState.PENDING
            if job.state == JobState.COMPLETE:
                response_state = JobResponseState.COMPLETE
            elif job.state == JobState.FAIL:
                response_state = JobResponseState.FAIL

            log.info("responding", state=response_state.value)
            return JobResponse(
                job_id=job_id,
                channel="",
                delay=3 if response_state == JobResponseState.PENDING else 0,
                state=response_state,
                data=job.generated,
            )

        log.info("new job")

        job = None
        response = None
        if req.command in [
            PromptType.ARENA_GENERATE_FEATURES,
            PromptType.ANNOUNCER_DESCRIBE_ARENA,
        ]:
            job, response = await self.make_generate_job(agent, req, session, log)

        if job and response:
            session.commit()
            gen_id = job.id
            log.info(f"adding generate job to background tasks {gen_id}")
            background_tasks.add_task(self.llm_service.execute_job, gen_id)
            return response

        session.rollback()
        log.warn("no handler for command")
        raise HTTPException(
            status_code=404, detail=f"Command not recognized: {req.command}"
        )

    async def make_generate_job(
        self, agent: Agent, req: ParticipantRequest, session: Session, log: ILogger
    ) -> Tuple[Optional[GenerateJob], JobResponse]:
        prompt = await self.template_service.expand_prompt(agent, req, session)
        self.log.debug(f"prompt:\n{prompt}", command=req.command.value)
        gc = self.llm_service.make_generate_job(req.job_id, agent.model, prompt)
        job, response = await self.job_service.create(gc, session)
        if not response.success or not job:
            self.log.error("error", response=response)
            return None, JobResponse(
                channel="",
                state=JobResponseState.FAIL,
                message="Error creating job",
                job_id=req.job_id,
                url=f"{self.base_path}/agent/{agent.participant_id}/request",
            )
        session.commit()
        log.info("Created generate job")
        return job, JobResponse(
            channel="",
            state=JobResponseState.PENDING,
            delay=2,
            message=prompt,
            job_id=req.job_id,
            url=f"{self.base_path}/agent/{agent.participant_id}/request",
        )

    def get_router(self):
        router = super().get_router()

        @router.get("/{agent_id}/health", response_model=JobResponse)
        async def health(agent_id: str):
            with self.model_service.db_service.get_session() as session:
                return await self.healthcheck(agent_id, session)

        @router.post("/{agent_id}/request", response_model=JobResponse)
        async def agent_request(
            agent_id: str,
            background_tasks: BackgroundTasks,
            req: ParticipantRequest = Body(...),
        ):
            with self.model_service.get_session() as session:
                return await self.agent_request(
                    agent_id, req, session, background_tasks
                )

        @router.get("/request/{job_id}", response_model=GenerateJob)
        async def get_job(job_id: str):
            with self.model_service.get_session() as session:
                job, result = await self.job_service.get(job_id, session)

                if job and result.success:
                    return job

            raise HTTPException(status_code=404, detail=result)

        return router
