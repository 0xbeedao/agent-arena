"""
Tests for the SetupMachine class.
"""

from unittest.mock import AsyncMock

import pytest

from agentarena.arena.models import Contest
from agentarena.arena.models import ContestRound
from agentarena.arena.models import ContestRoundCreate
from agentarena.arena.models import ContestState
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.arena.services.round_service import RoundService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.statemachines.setup_machine import SetupMachine


@pytest.fixture()
def contest():
    """Create a mock Contest object for testing."""
    return Contest(
        id="contest1",
        arena_id="arena1",
        current_round=1,
        player_positions="1,2;3,4",
        state=ContestState.CREATED,
    )


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
def round_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a RoundService for ContestRound"""
    return RoundService(
        model_class=ContestRound,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
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
