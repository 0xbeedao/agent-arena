"""
State machines for the Agent Arena application.

This module implements the state machines for contests, setup, and rounds
as defined in the state-machine.md documentation.
"""

from typing import Optional, Any, Dict
from statemachine import StateMachine, State


class SetupMachine(StateMachine):
    """
    Setup machine for generating features, positions, and descriptions.
    
    States:
    - GeneratingFeatures: Initial state for generating features
    - GeneratingPositions: State for generating positions
    - DescribingSetup: State for describing the setup
    """
    generating_features = State('GeneratingFeatures', initial=True)
    generating_positions = State('GeneratingPositions')
    describing_setup = State('DescribingSetup')
    complete = State('Complete', final=True)
    
    # Transitions
    features_generated = generating_features.to(generating_positions)
    positions_generated = generating_positions.to(describing_setup)

    cycle = (
        generating_features.to(generating_positions)
        | generating_positions.to(describing_setup)
        | describing_setup.to(complete)
    )
    
    def __init__(self, model: Optional[Any] = None):
        """Initialize the setup machine."""
        super().__init__(model=model)
        
    def on_enter_generating_features(self):
        """Called when entering the GeneratingFeatures state."""
        pass
        
    def on_enter_generating_positions(self):
        """Called when entering the GeneratingPositions state."""
        pass
        
    def on_enter_describing_setup(self):
        """Called when entering the DescribingSetup state."""
        pass

    def on_enter_complete(self):
        """Called when setup complete."""
        pass

class RoundMachine(StateMachine):
    """
    Round machine for handling the flow of a single round.
    
    States:
    - RoundPrompting: Initial state for prompting
    - AwaitingActions: State for awaiting actions
    - JudgingActions: State for judging actions
    - ApplyingEffects: State for applying effects
    - DescribingResults: State for describing results
    - PresentingResults: State for presenting results
    """
    round_prompting = State('RoundPrompting', initial=True)
    awaiting_actions = State('AwaitingActions')
    judging_actions = State('JudgingActions')
    applying_effects = State('ApplyingEffects')
    describing_results = State('DescribingResults')
    presenting_results = State('PresentingResults')
    complete = State('complete', final=True)
    
    # cycle = (
    #     round_prompting.to(awaiting_actions)
    #     | awaiting_actions.to(judging_actions)
    #     | judging_actions.to(applying_effects)
    #     | applying_effects.to(describing_results)
    #     | presenting_results.to(complete)
    # )

    # Transitions
    prompt_sent = round_prompting.to(awaiting_actions)
    actions_received = awaiting_actions.to(judging_actions)
    raw_results = judging_actions.to(applying_effects)
    effects_determined = applying_effects.to(describing_results)
    results_ready = describing_results.to(presenting_results)
    
    def __init__(self, model: Optional[Any] = None):
        """Initialize the round machine."""
        super().__init__(model=model)
        
    def on_enter_round_prompting(self):
        """Called when entering the RoundPrompting state."""
        pass
        
    def on_enter_awaiting_actions(self):
        """Called when entering the AwaitingActions state."""
        pass
        
    def on_enter_judging_actions(self):
        """Called when entering the JudgingActions state."""
        pass
        
    def on_enter_applying_effects(self):
        """Called when entering the ApplyingEffects state."""
        pass
        
    def on_enter_describing_results(self):
        """Called when entering the DescribingResults state."""
        pass
        
    def on_enter_presenting_results(self):
        """Called when entering the PresentingResults state."""
        pass


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
    idle = State('Idle', initial=True)
    in_setup = State('InSetup')
    ready = State('Ready')
    in_round = State('InRound')
    checking_end = State('CheckingEnd')
    completed = State('Completed', final=True)
    
    # Transitions
    start_contest = idle.to(in_setup)
    setup_done = in_setup.to(ready)
    start_round = ready.to(in_round)
    round_done = in_round.to(checking_end)
    end_condition_met = checking_end.to(completed)
    more_rounds_remain = checking_end.to(ready)
    
    def __init__(self, model: Optional[Any] = None):
        """Initialize the contest machine."""
        super().__init__(model=model)
        self._setup_machine = None
        self._round_machine = None
        
    def on_enter_in_setup(self):
        """Called when entering the InSetup state."""
        # Create a new setup machine when entering the InSetup state
        print("Creating setup machine")
        self._setup_machine = SetupMachine()
        print(f"Current setup machine state {self._setup_machine.current_state.id}")
        
    def on_enter_in_round(self):
        """Called when entering the InRound state."""
        # Create a new round machine when entering the InRound state
        self._round_machine = RoundMachine()
        
    def on_enter_checking_end(self):
        """Called when entering the CheckingEnd state."""
        pass
        
    def on_enter_completed(self):
        """Called when entering the Completed state."""
        pass
    
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