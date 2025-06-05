import pytest

from agentarena.arena.models import Arena
from agentarena.arena.models import Contest
from agentarena.arena.models import ContestState
from agentarena.arena.models import Participant
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.constants import RoleType
from agentarena.statemachines.round_machine import RoundMachine


def make_agent(agent_id="agent1", role=RoleType.PLAYER):
    return Participant(
        id=f"p.{agent_id}",
        role=role,
        name="Test Agent",
        description="A test agent",
    )


def make_arena():
    return Arena(
        id="arena1",
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
    return Contest(
        id="contest1",
        arena_id="arena1",
        current_round=1,
        player_positions="1,2;3,4",
        state=ContestState.CREATED,
        start_time=None,
        end_time=None,
        winner=None,
    )


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.fixture
def log(logging):
    return logging.get_logger("test")


def test_initial_state(log):
    contest = make_contest()
    machine = RoundMachine(contest, log=log)
    assert machine.current_state.id == "round_prompting"


def test_prompt_sent_transition(log):
    contest = make_contest()
    machine = RoundMachine(contest, log=log)
    machine.prompt_sent("")
    assert machine.current_state.id == "awaiting_actions"


def test_actions_received_transition(log):
    contest = make_contest()
    machine = RoundMachine(contest, log=log)
    machine.prompt_sent("")
    machine.actions_received("")
    assert machine.current_state.id == "judging_actions"


def test_raw_results_transition(log):
    contest = make_contest()
    machine = RoundMachine(contest, log=log)
    machine.prompt_sent("")
    machine.actions_received("")
    machine.raw_results("")
    assert machine.current_state.id == "applying_effects"


def test_effects_determined_transition(log):
    contest = make_contest()
    machine = RoundMachine(contest, log=log)
    machine.prompt_sent("")
    machine.actions_received("")
    machine.raw_results("")
    machine.effects_determined("")
    assert machine.current_state.id == "describing_results"


def test_results_ready_transition(log):
    contest = make_contest()
    machine = RoundMachine(contest, log=log)
    machine.prompt_sent("")
    machine.actions_received("")
    machine.raw_results("")
    machine.effects_determined("")
    machine.results_ready("")
    assert machine.current_state.id == "presenting_results"
    assert machine.current_state.final


def test_full_round_sequence(log):
    contest = make_contest()
    machine = RoundMachine(contest, log=log)
    assert machine.current_state.id == "round_prompting"
    machine.prompt_sent("")
    assert machine.current_state.id == "awaiting_actions"
    machine.actions_received("")
    assert machine.current_state.id == "judging_actions"
    machine.raw_results("")
    assert machine.current_state.id == "applying_effects"
    machine.effects_determined("")
    assert machine.current_state.id == "describing_results"
    machine.results_ready("")
    assert machine.current_state.id == "presenting_results"
    assert machine.current_state.final


def test_on_enter_methods_are_callable(log):
    # These are empty, but we check they exist and are callable
    contest = make_contest()
    machine = RoundMachine(contest, log=log)
    for method in [
        machine.on_enter_round_prompting,
        machine.on_enter_awaiting_actions,
        machine.on_enter_judging_actions,
        machine.on_enter_applying_effects,
        machine.on_enter_describing_results,
        machine.on_enter_presenting_results,
    ]:
        method()  # Should not raise
