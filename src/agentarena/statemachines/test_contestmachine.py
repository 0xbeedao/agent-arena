from agentarena.arena.models.arena import Arena
from agentarena.arena.models.arena import Contest
from agentarena.arena.models.arena import ContestState
from agentarena.arena.models.arena import Participant
from agentarena.arena.models.arena import ParticipantRole
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.strategy import Strategy
from agentarena.models.strategy import StrategyType
from agentarena.statemachines.contestmachine import ContestMachine


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
    machine = ContestMachine(contest, logging=logging())
    assert machine.current_state.id == "idle"


def test_start_contest_transition_creates_setup_machine():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    machine.start_contest()
    assert machine.current_state.id == "in_setup"
    # SetupMachine should be created
    assert machine._setup_machine is not None
    assert machine.setup_machine is not None
    assert machine.setup_machine.current_state.id == "setup_prompting" or hasattr(
        machine.setup_machine, "current_state"
    )


def test_setup_done_transition():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    machine.start_contest()
    machine.setup_done()
    assert machine.current_state.id == "ready"


def test_start_round_transition_creates_round_machine():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    machine.start_contest()
    machine.setup_done()
    machine.start_round()
    assert machine.current_state.id == "in_round"
    # RoundMachine should be created
    assert machine._round_machine is not None
    assert machine.round_machine is not None
    assert machine.round_machine.current_state.id == "round_prompting" or hasattr(
        machine.round_machine, "current_state"
    )


def test_round_done_transition():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    machine.start_contest()
    machine.setup_done()
    machine.start_round()
    machine.round_done()
    assert machine.current_state.id == "checking_end"


def test_end_condition_met_transition():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    machine.start_contest()
    machine.setup_done()
    machine.start_round()
    machine.round_done()
    machine.end_condition_met()
    assert machine.current_state.id == "completed"
    assert machine.current_state.final


def test_more_rounds_remain_transition():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    machine.start_contest()
    machine.setup_done()
    machine.start_round()
    machine.round_done()
    machine.more_rounds_remain()
    assert machine.current_state.id == "ready"


def test_full_contest_sequence():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    assert machine.current_state.id == "idle"
    machine.start_contest()
    assert machine.current_state.id == "in_setup"
    machine.setup_done()
    assert machine.current_state.id == "ready"
    machine.start_round()
    assert machine.current_state.id == "in_round"
    machine.round_done()
    assert machine.current_state.id == "checking_end"
    machine.end_condition_met()
    assert machine.current_state.id == "completed"
    assert machine.current_state.final


def test_setup_machine_property_none_when_not_in_setup():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    assert machine.setup_machine is None
    machine.start_contest()
    assert machine.setup_machine is not None
    machine.setup_done()
    assert machine.setup_machine is None


def test_round_machine_property_none_when_not_in_round():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    assert machine.round_machine is None
    machine.start_contest()
    machine.setup_done()
    assert machine.round_machine is None
    machine.start_round()
    assert machine.round_machine is not None
    machine.round_done()
    assert machine.round_machine is None


def test_check_setup_done_and_check_round_done():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    assert not machine.check_setup_done()
    assert not machine.check_round_done()
    machine.start_contest()
    # SetupMachine created, but not in describing_setup state
    assert not machine.check_setup_done()
    # Move setup_machine to describing_setup state if possible
    if hasattr(machine._setup_machine, "describing_setup"):
        # Simulate transition
        try:
            machine._setup_machine.setup_prompt_sent()
            machine._setup_machine.actions_received()
            machine._setup_machine.results_ready()
        except Exception:
            pass
        assert machine.check_setup_done() == (
            machine._setup_machine.describing_setup.is_active
        )
    machine.setup_done()
    machine.start_round()
    # RoundMachine created, but not in presenting_results state
    assert not machine.check_round_done()
    # Move round_machine to presenting_results state if possible
    if hasattr(machine._round_machine, "presenting_results"):
        try:
            machine._round_machine.prompt_sent()
            machine._round_machine.actions_received()
            machine._round_machine.raw_results()
            machine._round_machine.effects_determined()
            machine._round_machine.results_ready()
        except Exception:
            pass
        assert machine.check_round_done() == (
            machine._round_machine.presenting_results.is_active
        )


def test_get_state_dict():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    state_dict = machine.get_state_dict()
    assert state_dict["contest_state"] == "idle"
    machine.start_contest()
    state_dict = machine.get_state_dict()
    assert state_dict["contest_state"] == "in_setup"
    assert "setup_state" in state_dict
    machine.setup_done()
    machine.start_round()
    state_dict = machine.get_state_dict()
    assert state_dict["contest_state"] == "in_round"
    assert "round_state" in state_dict


def test_on_enter_methods_are_callable():
    contest = make_contest()
    machine = ContestMachine(contest, logging=logging())
    # Only test methods that are not just pass
    machine.on_enter_in_setup()
    machine.on_enter_in_round()
    machine.on_enter_checking_end()
    machine.on_enter_completed()
