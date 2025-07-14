"""
Tests for the SetupMachine class.
"""

from multiprocessing.heap import Arena
from unittest.mock import AsyncMock

import pytest

from agentarena.arena.models import Arena
from agentarena.arena.models import ArenaCreate
from agentarena.arena.models import Contest
from agentarena.arena.models import ContestCreate
from agentarena.arena.models import PlayerState
from agentarena.arena.models import PlayerStateCreate
from agentarena.arena.services.round_service import RoundService
from agentarena.arena.statemachines.setup_machine import SetupMachine
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService


@pytest.fixture()
def logging():
    return LoggingService(True)


@pytest.fixture
def log(logging):
    return logging.get_logger("test")


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
def arena_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create an ArenaService for Arena"""
    return ModelService[Arena, ArenaCreate](
        model_class=Arena,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def arena(arena_service):
    """Fixture to create an Arena object for testing."""
    ac = ArenaCreate(
        name="Test Arena",
        description="Test Arena",
        width=10,
        height=10,
        rules="Test Rules",
        winning_condition="Test Winning Condition",
        max_random_features=10,
        features=[],
    )
    with arena_service.get_session() as session:
        arena, _ = arena_service.create(ac, session=session)
        return arena


@pytest.fixture
def contest_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a FeatureService for Feature"""

    return ModelService[Contest, ContestCreate](
        model_class=Contest,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture()
def contest(contest_service, arena):
    cc = ContestCreate(
        arena_id=arena.id,
        participant_ids=[],
    )
    with contest_service.get_session() as session:
        contest, _ = contest_service.create(cc, session=session)
        return contest


@pytest.fixture
def playerstate_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a PlayerStateService for PlayerState"""
    return ModelService[PlayerState, PlayerStateCreate](
        model_class=PlayerState,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def round_service(
    db_service, uuid_service, message_broker, logging, playerstate_service
):
    """Fixture to create a RoundService for ContestRound"""
    return RoundService(
        message_broker=message_broker,
        playerstate_service=playerstate_service,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
        message_prefix="test",
    )


@pytest.mark.asyncio
async def test_initialization(contest, round_service, message_broker, log):
    """Test that the SetupMachine initializes correctly."""
    # Create a setup machine
    setup_machine = SetupMachine(
        contest,
        round_service=round_service,
        message_broker=message_broker,
        log=log,
    )
    await setup_machine.activate_initial_state()  # type: ignore

    # Check initial state
    assert setup_machine.current_state.id == "generating_features"
    assert setup_machine.current_state.initial
    assert not setup_machine.current_state.final

    # Check that the contest was set correctly
    assert setup_machine.contest == contest


@pytest.mark.asyncio
async def test_transition_to_generating_positions(
    contest, round_service, message_broker, log
):
    """Test transition from generating_features to generating_positions."""
    setup_machine = SetupMachine(
        contest,
        round_service=round_service,
        message_broker=message_broker,
        log=log,
    )
    await setup_machine.activate_initial_state()  # type: ignore

    # Transition to generating_positions
    await setup_machine.features_generated("")

    # Check current state
    assert setup_machine.current_state.id == "generating_positions"
    assert not setup_machine.current_state.initial
    assert not setup_machine.current_state.final


@pytest.mark.asyncio
async def test_transition_to_describing_setup(
    contest, round_service, message_broker, log
):
    """Test transition from generating_positions to describing_setup."""
    setup_machine = SetupMachine(
        contest, round_service=round_service, message_broker=message_broker, log=log
    )
    await setup_machine.activate_initial_state()  # type: ignore
    # Transition to generating_positions first
    await setup_machine.features_generated("")

    # Then transition to describing_setup
    await setup_machine.positions_generated("")

    # Check current state
    assert setup_machine.current_state.id == "describing_setup"
    assert not setup_machine.current_state.initial
    assert setup_machine.current_state.final


@pytest.mark.asyncio
async def test_cycle_transition(contest, round_service, message_broker, log):
    """Test the cycle transition method."""
    setup_machine = SetupMachine(
        contest, round_service=round_service, message_broker=message_broker, log=log
    )
    await setup_machine.activate_initial_state()  # type: ignore
    # Initial state should be generating_features
    assert setup_machine.current_state.id == "generating_features"

    # First cycle should transition to generating_positions
    await setup_machine.cycle("")
    assert setup_machine.current_state.id == "generating_positions"

    # Second cycle should transition to describing_setup
    await setup_machine.cycle("")
    assert setup_machine.current_state.id == "describing_setup"

    # Check that we're in the final state
    assert setup_machine.current_state.final


@pytest.mark.asyncio
async def test_complete_workflow(contest, round_service, message_broker, log):
    """Test the complete workflow of the SetupMachine."""
    setup_machine = SetupMachine(
        contest, round_service=round_service, message_broker=message_broker, log=log
    )
    await setup_machine.activate_initial_state()  # type: ignore

    # Check initial state
    assert setup_machine.current_state.id == "generating_features"

    # Transition through all states
    await setup_machine.features_generated("")
    assert setup_machine.current_state.id == "generating_positions"

    await setup_machine.positions_generated("")
    assert setup_machine.current_state.id == "describing_setup"

    # Check that we're in the final state
    assert setup_machine.current_state.final
