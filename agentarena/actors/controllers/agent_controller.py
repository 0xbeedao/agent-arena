"""
Responder controller for Agent Response endpoints
"""

from sqlmodel import Field
from sqlmodel import Session

from agentarena.actors.models import Agent
from agentarena.actors.models import AgentCreate
from agentarena.actors.models import AgentPublic
from agentarena.actors.models import AgentUpdate
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.subscribing_service import SubscribingService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState
from agentarena.models.requests import HealthStatus
from nats.aio.msg import Msg


class AgentController(
    ModelController[Agent, AgentCreate, AgentUpdate, AgentPublic], SubscribingService
):

    def __init__(
        self,
        base_path: str = "/api",
        agent_service: ModelService[Agent, AgentCreate] = Field(
            description="the participant service"
        ),
        message_broker: MessageBroker = Field(
            description="Message broker client for publishing messages"
        ),
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
        self.message_broker = message_broker
        self.uuid_service = uuid_service

    async def healthcheck_message(self, msg: Msg) -> None:
        """
        Handle healthcheck requests for agents.
        """
        self.log.info("healthcheck message received", msg=msg)
        agent_id = msg.data.decode("utf-8")
        with self.model_service.db_service.get_session() as session:
            response = await self.healthcheck(agent_id, session)
            await self.message_broker.publish_response(msg, response)

    async def healthcheck(self, agent_id: str, session: Session) -> JobResponse:
        agent, response = await self.model_service.get(agent_id, session)
        uuid = self.uuid_service.make_id()
        self.log.info(
            "healthcheck",
            agent_id=agent_id,
            participant=agent,
            uuid=uuid,
        )

        if not response.success or not agent:
            return JobResponse(
                channel="",
                state=JobResponseState.FAIL,
                message=f"no such responder: {agent_id}",
                job_id=uuid,
                data=HealthStatus(
                    name=agent_id,
                    state="FAIL",
                    version="1",
                ).model_dump(),
            )

        self.log.info("healthcheck complete", uuid=uuid)

        channel = f"actor.agent.health.response.{agent_id}"
        response = JobResponse(
            channel=channel,
            state=JobResponseState.COMPLETE,
            message="OK",
            job_id=uuid,
            data=HealthStatus(name=agent.name, state="OK", version="1").model_dump(),
            url=f"{self.base_path}/{agent_id}/health",
        )
        return response

    def get_router(self):
        router = super().get_router()

        @router.get("/{agent_id}/health", response_model=JobResponse)
        async def health(agent_id: str):
            with self.model_service.db_service.get_session() as session:
                return await self.healthcheck(agent_id, session)

        return router
