from unittest.mock import AsyncMock

import pytest

from agentarena.arena.models import Arena
from agentarena.arena.models import Contest
from agentarena.arena.models import ContestRound
from agentarena.arena.models import ContestRoundCreate
from agentarena.arena.models import ContestState
from agentarena.arena.models import Feature
from agentarena.arena.models import FeatureCreate
from agentarena.arena.models import Participant
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import RoleType
from agentarena.statemachines.contest_machine import ContestMachine


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
def feature_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a ModelService for Features"""
    return ModelService[Feature, FeatureCreate](
        model_class=Feature,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def round_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a ModelService for CommandJob"""
    return ModelService[ContestRound, ContestRoundCreate](
        model_class=ContestRound,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


def make_agent(agent_id="agent1", role=RoleType.PLAYER):
    return Participant(
        id=agent_id,
        role=role,
        name="Test Agent",
        description="A test agent",
    )


def make_arena():
    return Arena(
        name="Test Arena",
        description="A test arena",
        height=10,
        width=10,
        rules="No rules",
        max_random_features=0,
        features=[],
        winning_condition="",
    )


def make_contest():
    c = Contest(
        arena_id="arena1",
        player_positions="0,0;1,1;2,2",
    )
    c.participants = [
        make_agent("agent1", RoleType.PLAYER),
        make_agent("agent2", RoleType.PLAYER),
        make_agent("agent3", RoleType.ARENA),
        make_agent("agent4", RoleType.ANNOUNCER),
        make_agent("agent5", RoleType.JUDGE),
    ]
    return c


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.fixture
def log(logging):
    return logging.get_logger("test_contest_machine")


@pytest.mark.asyncio
async def test_initial_state(
    log, message_broker, uuid_service, feature_service, round_service
):
    contest = make_contest()

    machine = ContestMachine(
        contest,
        log=log,
        feature_service=feature_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        round_service=round_service,
    )

    await machine.activate_initial_state()  # type: ignore
    assert machine.current_state.id == ContestState.STARTING.value


@pytest.mark.asyncio
async def test_start_contest_transition_sends_batch(
    log,
    message_broker,
    uuid_service,
    round_service,
    feature_service,
):
    contest = make_contest()
    machine = ContestMachine(
        contest,
        log=log,
        feature_service=feature_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        round_service=round_service,
    )
    await machine.activate_initial_state()  # type: ignore
    assert machine.current_state.id == ContestState.STARTING.value
    await machine.start_contest("")
    # should have send requests to participants
    message_broker.send_batch.assert_awaited()


@pytest.mark.asyncio
async def test_start_state(
    log, message_broker, uuid_service, feature_service, round_service
):
    contest = make_contest()
    contest.state = ContestState.IN_ROUND
    machine = ContestMachine(
        contest,
        log=log,
        feature_service=feature_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        round_service=round_service,
    )
    await machine.activate_initial_state()  # type: ignore
    assert machine.current_state.id == ContestState.IN_ROUND.value
    # should not have send requests to participants, since it skipped the role call
    message_broker.send_batch.assert_not_awaited()


@pytest.mark.asyncio
async def test_roles_present_transition(
    log, message_broker, uuid_service, round_service, feature_service
):
    contest = make_contest()
    contest.state = ContestState.ROLE_CALL
    machine = ContestMachine(
        contest,
        log=log,
        feature_service=feature_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        round_service=round_service,
    )
    await machine.activate_initial_state()  # type: ignore
    assert machine.current_state.id == ContestState.ROLE_CALL.value
    await machine.roles_present("test")  # type: ignore
    assert machine.current_state.id == ContestState.SETUP_ARENA.value
    states = machine.get_state_dict()
    assert "setup_state" in states
    assert "contest_state" in states
    assert states["contest_state"] == ContestState.SETUP_ARENA.value


# def test_setup_done_transition(log, message_broker, uuid_service):
#     contest = make_contest()
#     machine = ContestMachine(
#         contest, log=log, message_broker=message_broker, uuid_service=uuid_service
#     )
#     machine.start_contest()
#     machine.setup_done()
#     assert machine.current_state.id == "ready"


# def test_start_round_transition_creates_round_machine(
#     log, message_broker, uuid_service
# ):
#     contest = make_contest()
#     machine = ContestMachine(
#         contest, log=log, message_broker=message_broker, uuid_service=uuid_service
#     )
#     machine.start_contest()
#     machine.setup_done()
#     machine.start_round()
#     assert machine.current_state.id == "in_round"
#     # RoundMachine should be created
#     assert machine._round_machine is not None
#     assert machine.round_machine is not None
#     assert machine.round_machine.current_state.id == "round_prompting" or hasattr(
#         machine.round_machine, "current_state"
#     )


# def test_round_done_transition(log, message_broker, uuid_service):
#     contest = make_contest()
#     machine = ContestMachine(
#         contest, log=log, message_broker=message_broker, uuid_service=uuid_service
#     )
#     machine.start_contest()
#     machine.setup_done()
#     machine.start_round()
#     machine.round_done()
#     assert machine.current_state.id == "checking_end"


# def test_end_condition_met_transition(log, message_broker, uuid_service):
#     contest = make_contest()
#     machine = ContestMachine(
#         contest, log=log, message_broker=message_broker, uuid_service=uuid_service
#     )
#     machine.start_contest()
#     machine.setup_done()
#     machine.start_round()
#     machine.round_done()
#     machine.end_condition_met()
#     assert machine.current_state.id == "completed"
#     assert machine.current_state.final


# def test_more_rounds_remain_transition(log, message_broker, uuid_service):
#     contest = make_contest()
#     machine = ContestMachine(
#         contest, log=log, message_broker=message_broker, uuid_service=uuid_service
#     )
#     machine.start_contest()
#     machine.setup_done()
#     machine.start_round()
#     machine.round_done()
#     machine.more_rounds_remain()
#     assert machine.current_state.id == "ready"


# def test_full_contest_sequence(log, message_broker, uuid_service):
#     contest = make_contest()
#     machine = ContestMachine(
#         contest, log=log, message_broker=message_broker, uuid_service=uuid_service
#     )
#     assert machine.current_state.id == "idle"
#     machine.start_contest()
#     assert machine.current_state.id == "in_setup"
#     machine.setup_done()
#     assert machine.current_state.id == "ready"
#     machine.start_round()
#     assert machine.current_state.id == "in_round"
#     machine.round_done()
#     assert machine.current_state.id == "checking_end"
#     machine.end_condition_met()
#     assert machine.current_state.id == "completed"
#     assert machine.current_state.final


# def test_setup_machine_property_none_when_not_in_setup(
#     log, message_broker, uuid_service
# ):
#     contest = make_contest()
#     machine = ContestMachine(
#         contest, log=log, message_broker=message_broker, uuid_service=uuid_service
#     )
#     assert machine.setup_machine is None
#     machine.start_contest()
#     assert machine.setup_machine is not None
#     machine.setup_done()
#     assert machine.setup_machine is None


# def test_round_machine_property_none_when_not_in_round(
#     log, message_broker, uuid_service
# ):
#     contest = make_contest()
#     machine = ContestMachine(
#         contest, log=log, message_broker=message_broker, uuid_service=uuid_service
#     )
#     assert machine.round_machine is None
#     machine.start_contest()
#     machine.setup_done()
#     assert machine.round_machine is None
#     machine.start_round()
#     assert machine.round_machine is not None
#     machine.round_done()
#     assert machine.round_machine is None


# def test_check_setup_done_and_check_round_done(log, message_broker, uuid_service):
#     contest = make_contest()
#     machine = ContestMachine(
#         contest, log=log, message_broker=message_broker, uuid_service=uuid_service
#     )
#     assert not machine.check_setup_done()
#     assert not machine.check_round_done()
#     machine.start_contest()
#     # SetupMachine created, but not in describing_setup state
#     assert not machine.check_setup_done()
#     # Move setup_machine to describing_setup state if possible
#     if hasattr(machine._setup_machine, "describing_setup"):
#         # Simulate transition
#         try:
#             machine._setup_machine.setup_prompt_sent()
#             machine._setup_machine.actions_received()
#             machine._setup_machine.results_ready()
#         except Exception:
#             pass
#         assert machine.check_setup_done() == (
#             machine._setup_machine.describing_setup.is_active
#         )
#     machine.setup_done()
#     machine.start_round()
#     # RoundMachine created, but not in presenting_results state
#     assert not machine.check_round_done()
#     # Move round_machine to presenting_results state if possible
#     if hasattr(machine._round_machine, "presenting_results"):
#         try:
#             machine._round_machine.prompt_sent()
#             machine._round_machine.actions_received()
#             machine._round_machine.raw_results()
#             machine._round_machine.effects_determined()
#             machine._round_machine.results_ready()
#         except Exception:
#             pass
#         assert machine.check_round_done() == (
#             machine._round_machine.presenting_results.is_active
#         )


# def test_get_state_dict(log, message_broker, uuid_service):
#     contest = make_contest()
#     machine = ContestMachine(
#         contest, log=log, message_broker=message_broker, uuid_service=uuid_service
#     )
#     state_dict = machine.get_state_dict()
#     assert state_dict["contest_state"] == "idle"
#     machine.start_contest()
#     state_dict = machine.get_state_dict()
#     assert state_dict["contest_state"] == "in_setup"
#     assert "setup_state" in state_dict
#     machine.setup_done()
#     machine.start_round()
#     state_dict = machine.get_state_dict()
#     assert state_dict["contest_state"] == "in_round"
#     assert "round_state" in state_dict


# def test_on_enter_methods_are_callable(log, message_broker, uuid_service):
#     contest = make_contest()
#     machine = ContestMachine(
#         contest, log=log, message_broker=message_broker, uuid_service=uuid_service
#     )
#     # Only test methods that are not just pass
#     machine.on_enter_in_setup()
#     machine.on_enter_in_round()
#     machine.on_enter_checking_end()
#     machine.on_enter_completed()
