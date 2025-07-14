"""
Responder controller for Agent Response endpoints
"""

from typing import Optional

from fastapi import Body
from fastapi import HTTPException
from fastapi import Response
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
from agentarena.models.job import JobLock
from agentarena.models.public import JobResponse
from agentarena.models.requests import HealthStatus
from agentarena.models.requests import ParticipantActionRequest
from agentarena.models.requests import ParticipantContestRequest
from agentarena.models.requests import ParticipantContestRoundRequest

PROMPT_TO_REQUEST = {
    PromptType.ANNOUNCER_DESCRIBE_ARENA: ParticipantContestRequest,
    PromptType.ANNOUNCER_DESCRIBE_RESULTS: ParticipantContestRoundRequest,
    PromptType.ARENA_GENERATE_FEATURES: ParticipantContestRequest,
    PromptType.JUDGE_APPLY_EFFECTS: ParticipantContestRequest,
    PromptType.JUDGE_PLAYER_ACTION_JUDGEMENT: ParticipantActionRequest,
    PromptType.PLAYER_PLAYER_ACTION: ParticipantContestRequest,
}


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
            template_service=template_service,
            logging=logging,
        )
        # actor.agent.Bridge-arable-MATURE-Vanish-Sheet.request.health.some-job-id
        to_subscribe = [
            (f"actor.agent.*.request.>", self.agent_request_message),
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

        actor.agent.<participant_id>.request.health
        """
        parts = msg.subject.split(".")
        participant_id = parts[2]
        self.log.info(
            "healthcheck message received", msg=msg, participant_id=participant_id
        )
        with self.model_service.db_service.get_session() as session:
            response = await self.healthcheck(participant_id, session)
            channel = (
                msg.reply
                or f"actor.agent.{participant_id}.response.health.{response.job_id}"
            )
            await self.message_broker.publish_response(channel, response)  # type: ignore

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
                state=JobResponseState.FAIL,
                message=f"no such responder: {participant_id}",
                job_id=uuid,
                data=HealthStatus(
                    name=participant_id,
                    state="FAIL",
                    version="1",
                ).model_dump_json(),
            )

        self.log.info("healthcheck complete", uuid=uuid)

        channel = f"actor.agent.{participant_id}.response.health"
        response = JobResponse(
            state=JobResponseState.COMPLETE,
            message="OK",
            job_id=uuid,
            data=HealthStatus(
                name=agent.name, state="OK", version="1"
            ).model_dump_json(),
        )
        return response

    async def agent_prompt(
        self,
        agent_id: str,
        job_id: str,
        req: (
            ParticipantContestRequest
            | ParticipantContestRoundRequest
            | ParticipantActionRequest
        ),
        session: Session,
    ) -> Response:
        stmt = select(Agent).where(Agent.participant_id == agent_id)
        agent = session.exec(stmt).one_or_none()
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        raw = await self.template_service.expand_prompt(agent, job_id, req, session)
        return Response(content=raw, media_type="text/markdown")

    async def agent_request_message(self, msg: Msg) -> None:
        """
        Handle agent request messages.

        actor.agent.<agent_id>.request.<prompt_type>.<job_id>
        """
        parts = msg.subject.split(".")
        agent_id = parts[2]
        prompt_type = parts[4]
        job_id = parts[-1]

        log = self.log.bind(
            agent=agent_id, prompt_type=prompt_type, job_id=job_id, channel=msg.subject
        )

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

            if prompt_type == "health":
                await self.healthcheck_message(msg)
            else:
                log.info("agent request message received", msg=msg)
                participant_id = agent_id  # we always look up using the id the arena has, not our internal ID

                try:
                    pt = PromptType(prompt_type)
                    req = PROMPT_TO_REQUEST[pt].model_validate_json(msg.data)
                    reply_channel = (
                        msg.reply
                        or f"actor.agent.{participant_id}.response.{pt.value}.{job_id}"
                    )
                    await self.agent_request(
                        participant_id,
                        job_id,
                        pt,
                        req,
                        reply_channel,
                        session,
                    )
                except ValueError:
                    log.error("invalid prompt type", prompt_type=prompt_type)
                    return

    async def agent_request(
        self,
        participant_id: str,
        job_id: str,
        prompt_type: PromptType,
        req: (
            ParticipantContestRequest
            | ParticipantContestRoundRequest
            | ParticipantActionRequest
        ),
        channel: str,
        session: Session,
    ):
        """
        Handle a request for prompting an agent.
        """
        if job_id == "":
            job_id = self.uuid_service.make_id()

        stmt = select(Agent).where(Agent.participant_id == participant_id)
        agent = session.exec(stmt).one_or_none()
        log = self.log.bind(job=job_id, cmd=req.command, participant=participant_id)
        response = None
        job = None
        if agent is None:
            log.info("No such agent")
            response = JobResponse(
                state=JobResponseState.FAIL,
                message=f"no such responder: {participant_id}",
                job_id=job_id,
            )
        else:
            job = await self.make_generate_job(agent, job_id, req, session, log)

        if job:
            req.command = prompt_type
            gen_job = await self.llm_service.execute_job(job.id, session)
            if not gen_job or gen_job.state != JobState.COMPLETE:
                log.error("Error executing job", gen_job=gen_job)
                response = JobResponse(
                    state=JobResponseState.FAIL,
                    message="Error executing job",
                    job_id=job_id,
                )
            else:

                log.info("Job completed", gen_job=gen_job)
                response = JobResponse(
                    state=JobResponseState.COMPLETE,
                    data=gen_job.generated,
                    job_id=job_id,
                )
        if not response:
            log.warn("Error creating job")
            response = JobResponse(
                state=JobResponseState.FAIL,
                message="Error creating job",
                job_id=job_id,
            )
        session.commit()
        await self.message_broker.publish_response(channel, response)

    async def make_generate_job(
        self,
        agent: Agent,
        job_id: str,
        req: (
            ParticipantContestRequest
            | ParticipantContestRoundRequest
            | ParticipantActionRequest
        ),
        session: Session,
        log: ILogger,
    ) -> Optional[GenerateJob]:
        prompt = await self.template_service.expand_prompt(agent, job_id, req, session)
        prompt_type = req.command
        self.log.debug(f"prompt:\n{prompt}", command=prompt_type.value)
        gc = self.llm_service.make_generate_job(
            job_id, agent.model, prompt, prompt_type
        )
        job, response = await self.job_service.create(gc, session)
        if not response.success or not job:
            self.log.error("error", response=response)
            return None
        session.flush()
        log.info("Created generate job")
        return job

    def get_router(self):
        router = super().get_router()

        @router.get("/{agent_id}.{format}", response_model=str)
        async def get_md(agent_id: str, format: str = "md"):
            with self.model_service.get_session() as session:
                return await self.get_model_with_format(
                    agent_id, session, format=format
                )

        @router.get("/{agent_id}/health", response_model=JobResponse)
        async def health(agent_id: str):
            with self.model_service.db_service.get_session() as session:
                return await self.healthcheck(agent_id, session)

        @router.post(
            "/{agent_id}/{job_id}/"
            + PromptType.ANNOUNCER_DESCRIBE_ARENA.value
            + "/prompt",
            response_model=str,
        )
        async def prompt_announcer_describe_arena(
            agent_id: str,
            job_id: str,
            req: ParticipantContestRequest = Body(...),
        ):
            with self.model_service.get_session() as session:
                return await self.agent_prompt(agent_id, job_id, req, session)

        @router.post(
            "/{agent_id}/{job_id}/"
            + PromptType.ANNOUNCER_DESCRIBE_RESULTS.value
            + "/prompt",
            response_model=str,
        )
        async def prompt_announcer_describe_results(
            agent_id: str,
            job_id: str,
            req: ParticipantContestRequest = Body(...),
        ):
            with self.model_service.get_session() as session:
                return await self.agent_prompt(agent_id, job_id, req, session)

        @router.post(
            "/{agent_id}/{job_id}/"
            + PromptType.ARENA_GENERATE_FEATURES.value
            + "/prompt",
            response_model=str,
        )
        async def prompt_arena_generate_features(
            agent_id: str,
            job_id: str,
            req: ParticipantContestRequest = Body(...),
        ):
            with self.model_service.get_session() as session:
                return await self.agent_prompt(agent_id, job_id, req, session)

        @router.post(
            "/{agent_id}/{job_id}/" + PromptType.JUDGE_APPLY_EFFECTS.value + "/prompt",
            response_model=str,
        )
        async def prompt_judge_apply_effects(
            agent_id: str,
            job_id: str,
            req: ParticipantContestRequest = Body(...),
        ):
            with self.model_service.get_session() as session:
                return await self.agent_prompt(agent_id, job_id, req, session)

        @router.post(
            "/{agent_id}/{job_id}/"
            + PromptType.JUDGE_PLAYER_ACTION_JUDGEMENT.value
            + "/prompt",
            response_model=str,
        )
        async def prompt_judge_player_action_judgement(
            agent_id: str,
            job_id: str,
            req: ParticipantActionRequest = Body(...),
        ):
            with self.model_service.get_session() as session:
                return await self.agent_prompt(agent_id, job_id, req, session)

        @router.post(
            "/{agent_id}/{job_id}/" + PromptType.PLAYER_PLAYER_ACTION.value + "/prompt",
            response_model=str,
        )
        async def prompt_player_player_action(
            agent_id: str,
            job_id: str,
            req: ParticipantContestRequest = Body(...),
        ):
            with self.model_service.get_session() as session:
                return await self.agent_prompt(agent_id, job_id, req, session)

        return router
