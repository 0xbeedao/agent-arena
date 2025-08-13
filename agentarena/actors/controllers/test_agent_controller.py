from datetime import datetime
from unittest.mock import AsyncMock

import pytest

# from agentarena.actors.controllers.responder_controller import ResponderController
# from agentarena.models.arena.models import Participant
from agentarena.actors.controllers.agent_controller import AgentController
from agentarena.actors.controllers.strategy_controller import StrategyController
from agentarena.actors.models import Agent
from agentarena.actors.models import AgentCreate
from agentarena.actors.models import Strategy
from agentarena.actors.models import StrategyCreate
from agentarena.actors.models import StrategyPrompt
from agentarena.actors.models import StrategyPromptCreate
from agentarena.actors.services.template_service import TemplateService
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.llm_service import LLMService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import PromptType
from agentarena.models.constants import RoleType
from agentarena.models.job import GenerateJob
from agentarena.models.job import GenerateJobCreate
from agentarena.models.public import ArenaPublic
from agentarena.models.public import ContestPublic
from agentarena.models.public import ContestRoundPublic
from agentarena.models.requests import ContestRequestPayload
from agentarena.models.requests import ParticipantContestRequest

# from agentarena.models.requests import HealthResponse
# from agentarena.models.requests import HealthStatus


@pytest.fixture
def uuid_service():
    return UUIDService(word_list=[])


@pytest.fixture
def message_broker():
    """Fixture to create a mock message broker"""
    broker = AsyncMock()
    broker.publish_model_change = AsyncMock()
    broker.publish_response = AsyncMock()
    return broker


@pytest.fixture
def llm_service(db_service, message_broker, uuid_service, logging):
    return LLMService(
        llm_map=[],
        db_service=db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def db_service(uuid_service, logging):
    """Fixture to create an in-memory DB service"""
    service = DbService(
        str(get_project_root()),
        dbfile="test.db",
        get_engine=get_engine,
        memory=True,
        prod=False,
        uuid_service=uuid_service,
        logging=logging,
    )
    return service.create_db()


@pytest.fixture
def agent_service(db_service, message_broker, uuid_service, logging):
    return ModelService[Agent, AgentCreate](
        model_class=Agent,  # type: ignore
        db_service=db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def job_service(db_service, message_broker, uuid_service, logging):
    return ModelService[GenerateJob, GenerateJobCreate](
        model_class=GenerateJob,
        db_service=db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def strategy_service(db_service, message_broker, uuid_service, logging):
    return ModelService[Strategy, StrategyCreate](
        model_class=Strategy,
        db_service=db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def prompt_service(db_service, message_broker, uuid_service, logging):
    return ModelService[StrategyPrompt, StrategyPromptCreate](
        model_class=StrategyPrompt,
        db_service=db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def template_service(strategy_service, logging):
    return TemplateService(strategy_service=strategy_service, logging=logging)


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.fixture
def agent_ctrl(
    agent_service,
    message_broker,
    template_service,
    uuid_service,
    llm_service,
    job_service,
    logging,
):
    return AgentController(
        agent_service=agent_service,
        message_broker=message_broker,
        template_service=template_service,
        uuid_service=uuid_service,
        llm_service=llm_service,
        job_service=job_service,
        logging=logging,
    )


@pytest.fixture
def strategy_ctrl(
    strategy_service,
    prompt_service,
    uuid_service,
    message_broker,
    logging,
):
    return StrategyController(
        message_broker=message_broker,
        prompt_service=prompt_service,
        strategy_service=strategy_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.mark.asyncio
async def test_generate_feature(
    agent_ctrl, strategy_ctrl, db_service, uuid_service, message_broker
):
    arena = ArenaPublic(
        id="arena-test-1",
        name="Super Fun Test Arena",
        description="An entertaining proving ground",
        height=20,
        width=20,
        rules="Capture the flag, no pvp, max two squares movement per turn if running, else one with other actions, such as moving and searching",
        winning_condition="",
    )
    round = ContestRoundPublic(
        features=[],
        narrative="",
        players=[],
        round_no=0,
        state=ContestRoundState.GENERATING_FEATURES,
    )
    contest = ContestPublic(
        arena=arena,
        rounds=[round],
        end_time=0,
        start_time=int(datetime.now().timestamp()),
    )
    req = ParticipantContestRequest(
        command=PromptType.ARENA_GENERATE_FEATURES,
        data=ContestRequestPayload(contest=contest),
        message="test",
    )

    sc = StrategyCreate(
        name="Simple Arena",
        personality="straightforward arena",
        description="A proving ground for tests and trials",
        role=RoleType.ARENA,
        prompts=[
            StrategyPromptCreate(
                key=PromptType.ARENA_GENERATE_FEATURES,
                prompt="#jinja:arena.base.generate_features",
            )
        ],
    )

    with db_service.get_session() as session:
        strategy = await strategy_ctrl.create_strategy(sc, session)
        session.flush()
        assert strategy
        assert strategy.id
        pid = "external-1"
        ac = AgentCreate(
            name="Captain Arena",
            participant_id=pid,
            strategy_id=strategy.id,
        )
        agent = await agent_ctrl.create_model(ac, session)
        session.flush()
        assert agent
        assert agent.id
        assert agent.participant_id == pid
        session.commit()

        job_id = uuid_service.make_id()
        await agent_ctrl.agent_request(
            pid,
            job_id,
            PromptType.ARENA_GENERATE_FEATURES,
            req,
            "test.arena_generate_features",
            session,
        )
        assert message_broker.publish_response.call_count == 1
