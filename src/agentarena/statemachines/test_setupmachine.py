"""
Tests for the SetupMachine class.
"""

from unittest.mock import MagicMock

import pytest

from agentarena.factories.logger import LoggingService
from agentarena.models.contest import Contest
from agentarena.models.contest import ContestStatus
from agentarena.statemachines.setupmachine import SetupMachine


@pytest.fixture()
def contest():
    """Create a mock Contest object for testing."""
    mock = MagicMock(spec=Contest)
    mock.id = "test-contest-id"
    mock.status = ContestStatus.CREATED
    return mock


@pytest.fixture()
def logging():
    return LoggingService(True)


class TestSetupMachine:
    """Test suite for the SetupMachine class."""

    def test_initialization(self, contest, logging):
        """Test that the SetupMachine initializes correctly."""
        # Create a setup machine
        setup_machine = SetupMachine(contest, logging=logging)

        # Check initial state
        assert setup_machine.current_state.id == "generating_features"
        assert setup_machine.current_state.initial
        assert not setup_machine.current_state.final

        # Check that the contest was set correctly
        assert setup_machine.contest == contest

    def test_transition_to_generating_positions(self, contest, logging):
        """Test transition from generating_features to generating_positions."""
        setup_machine = SetupMachine(contest, logging=logging)

        # Transition to generating_positions
        setup_machine.features_generated()

        # Check current state
        assert setup_machine.current_state.id == "generating_positions"
        assert not setup_machine.current_state.initial
        assert not setup_machine.current_state.final

    def test_transition_to_describing_setup(self, contest, logging):
        """Test transition from generating_positions to describing_setup."""
        setup_machine = SetupMachine(contest, logging=logging)

        # Transition to generating_positions first
        setup_machine.features_generated()

        # Then transition to describing_setup
        setup_machine.positions_generated()

        # Check current state
        assert setup_machine.current_state.id == "describing_setup"
        assert not setup_machine.current_state.initial
        assert setup_machine.current_state.final

    def test_cycle_transition(self, contest, logging):
        """Test the cycle transition method."""
        setup_machine = SetupMachine(contest, logging=logging)

        # Initial state should be generating_features
        assert setup_machine.current_state.id == "generating_features"

        # First cycle should transition to generating_positions
        setup_machine.cycle()
        assert setup_machine.current_state.id == "generating_positions"

        # Second cycle should transition to describing_setup
        setup_machine.cycle()
        assert setup_machine.current_state.id == "describing_setup"

        # Check that we're in the final state
        assert setup_machine.current_state.final

    def test_complete_workflow(self, contest, logging):
        """Test the complete workflow of the SetupMachine."""
        setup_machine = SetupMachine(contest, logging=logging)

        # Check initial state
        assert setup_machine.current_state.id == "generating_features"

        # Transition through all states
        setup_machine.features_generated()
        assert setup_machine.current_state.id == "generating_positions"

        setup_machine.positions_generated()
        assert setup_machine.current_state.id == "describing_setup"

        # Check that we're in the final state
        assert setup_machine.current_state.final
