from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.arena import Arena
from agentarena.models.contest import Contest
from agentarena.models.contest import ContestState
from agentarena.models.participant import Participant
from agentarena.models.participant import ParticipantRole
from agentarena.models.strategy import Strategy
from agentarena.models.strategy import StrategyType
from agentarena.statemachines.roundmachine import RoundMachine


def make_strategy():
    return Strategy(
        id="strategy1",
        name="Test Strategy",
        personality="Neutral",
        instructions="Do nothing",
        description="A test strategy",
        role=StrategyType.PLAYER,
    )


def make_agent(agent_id="agent1", role=ParticipantRole.PLAYER):
    return Participant(
        id=f"p.{agent_id}",
        agent_id=agent_id,
        role=role,
        name="Test Agent",
        description="A test agent",
        strategy=make_strategy(),
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
        participants=[make_agent()],
    )


def make_contest():
    return Contest(
        id="contest1",
        arena=make_arena(),
        current_round=1,
        player_positions=["A"],
        state=ContestState.CREATED,
        start_time=None,
        end_time=None,
        winner=None,
    )


def logging():
    return LoggingService(True)


def test_initial_state():
    contest = make_contest()
    machine = RoundMachine(contest, logging=logging())
    assert machine.current_state.id == "round_prompting"


def test_prompt_sent_transition():
    contest = make_contest()
    machine = RoundMachine(contest, logging=logging())
    machine.prompt_sent()
    assert machine.current_state.id == "awaiting_actions"


def test_actions_received_transition():
    contest = make_contest()
    machine = RoundMachine(contest, logging=logging())
    machine.prompt_sent()
    machine.actions_received()
    assert machine.current_state.id == "judging_actions"


def test_raw_results_transition():
    contest = make_contest()
    machine = RoundMachine(contest, logging=logging())
    machine.prompt_sent()
    machine.actions_received()
    machine.raw_results()
    assert machine.current_state.id == "applying_effects"


def test_effects_determined_transition():
    contest = make_contest()
    machine = RoundMachine(contest, logging=logging())
    machine.prompt_sent()
    machine.actions_received()
    machine.raw_results()
    machine.effects_determined()
    assert machine.current_state.id == "describing_results"


def test_results_ready_transition():
    contest = make_contest()
    machine = RoundMachine(contest, logging=logging())
    machine.prompt_sent()
    machine.actions_received()
    machine.raw_results()
    machine.effects_determined()
    machine.results_ready()
    assert machine.current_state.id == "presenting_results"
    assert machine.current_state.final


def test_full_round_sequence():
    contest = make_contest()
    machine = RoundMachine(contest, logging=logging())
    assert machine.current_state.id == "round_prompting"
    machine.prompt_sent()
    assert machine.current_state.id == "awaiting_actions"
    machine.actions_received()
    assert machine.current_state.id == "judging_actions"
    machine.raw_results()
    assert machine.current_state.id == "applying_effects"
    machine.effects_determined()
    assert machine.current_state.id == "describing_results"
    machine.results_ready()
    assert machine.current_state.id == "presenting_results"
    assert machine.current_state.final


def test_on_enter_methods_are_callable():
    # These are empty, but we check they exist and are callable
    contest = make_contest()
    machine = RoundMachine(contest, logging=logging())
    for method in [
        machine.on_enter_round_prompting,
        machine.on_enter_awaiting_actions,
        machine.on_enter_judging_actions,
        machine.on_enter_applying_effects,
        machine.on_enter_describing_results,
        machine.on_enter_presenting_results,
    ]:
        method()  # Should not raise
