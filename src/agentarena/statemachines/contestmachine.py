"""
The Contest State Machine
"""

from typing import Any
from typing import Dict
from typing import Optional

from statemachine import State
from statemachine import StateMachine

from agentarena.models.contest import Contest

from .roundmachine import RoundMachine
from .setupmachine import SetupMachine


class ContestMachine(StateMachine):
    """
    Top-level Contest machine that manages the overall contest flow.

    States:
    - Idle: Initial state
    - InSetup: State for setup
    - Ready: State for ready
    - InRound: State for round
    - CheckingEnd: State for checking end
    - Completed: Final state
    """

    idle = State("Idle", initial=True)
    in_setup = State("InSetup")
    ready = State("Ready")
    in_round = State("InRound")
    checking_end = State("CheckingEnd")
    completed = State("Completed", final=True)

    # Transitions
    start_contest = idle.to(in_setup)
    setup_done = in_setup.to(ready)
    start_round = ready.to(in_round)
    round_done = in_round.to(checking_end)
    end_condition_met = checking_end.to(completed)
    more_rounds_remain = checking_end.to(ready)

    def __init__(self, contest: Contest, logging=None):
        """Initialize the contest machine."""
        self._setup_machine = None
        self._round_machine = None
        self.contest = contest
        self.log = logging.get_logger(
            "contestmachine", contest=contest.id if contest is not None else "none"
        )
        super().__init__()

    def on_enter_in_setup(self):
        """Called when entering the InSetup state."""
        # Create a new setup machine when entering the InSetup state
        print("Creating setup machine")
        self._setup_machine = SetupMachine(self.contest)
        print(f"Current setup machine state {self._setup_machine.current_state.id}")

    def on_enter_in_round(self):
        """Called when entering the InRound state."""
        # Create a new round machine when entering the InRound state
        self._round_machine = RoundMachine(self.contest)

    def on_enter_checking_end(self):
        """Called when entering the CheckingEnd state."""

    def on_enter_completed(self):
        """Called when entering the Completed state."""

    @property
    def setup_machine(self) -> Optional[SetupMachine]:
        """
        Get the setup machine if in the InSetup state.

        Returns:
            Optional[SetupMachine]: The setup machine or None if not in InSetup state.
        """
        if not self.in_setup.is_active:
            return None
        return self._setup_machine

    @property
    def round_machine(self) -> Optional[RoundMachine]:
        """
        Get the round machine if in the InRound state.

        Returns:
            Optional[RoundMachine]: The round machine or None if not in InRound state.
        """
        if not self.in_round.is_active:
            return None
        return self._round_machine

    def check_setup_done(self) -> bool:
        """
        Check if setup is done.

        Returns:
            bool: True if setup is done, False otherwise.
        """
        if self._setup_machine is None:
            return False
        return self._setup_machine.describing_setup.is_active

    def check_round_done(self) -> bool:
        """
        Check if round is done.

        Returns:
            bool: True if round is done, False otherwise.
        """
        if self._round_machine is None:
            return False
        return self._round_machine.presenting_results.is_active

    def get_state_dict(self) -> Dict[str, Any]:
        """
        Get a dictionary representation of the current state.

        Returns:
            Dict[str, Any]: Dictionary with state information.
        """
        result = {
            "contest_state": self.current_state.id,
        }

        if self.in_setup.is_active and self._setup_machine is not None:
            result["setup_state"] = self._setup_machine.current_state.id

        if self.in_round.is_active and self._round_machine is not None:
            result["round_state"] = self._round_machine.current_state.id

        return result

    # logging changes
    def after_transition(self, event, source, target):
        self.log.debug(f"{self.name} after: {source.id}--({event})-->{target.id}")

    def on_enter_state(self, target, event):
        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")
