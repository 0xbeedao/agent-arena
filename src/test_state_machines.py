"""
Test file for state machines.

This file demonstrates how to use the state machines implemented in
src/agentarena/models/state_machines.py.
"""

from agentarena.models.state_machines import ContestMachine, SetupMachine, RoundMachine


def test_setup_machine():
    """Test the setup machine."""
    print("\n=== Testing SetupMachine ===")
    
    # Create a setup machine
    setup = SetupMachine()
    print(f"Initial state: {setup.current_state.id}")

    # Transition through states
    while not setup.current_state.final:
        setup.cycle()
        print(f"Current state: {setup.current_state.id}")
        
    # Check if we're in the final state
    print(f"Is in final state: {setup.current_state.final}")

def test_round_machine():
    """Test the round machine."""
    print("\n=== Testing RoundMachine ===")
    
    # Create a round machine
    round_machine = RoundMachine()
    print(f"Initial state: {round_machine.current_state.id}")
    
    # Transition through states
    print("Sending prompt...")
    round_machine.prompt_sent()
    print(f"Current state: {round_machine.current_state.id}")
    
    print("Receiving actions...")
    round_machine.actions_received()
    print(f"Current state: {round_machine.current_state.id}")
    
    print("Judging actions...")
    round_machine.raw_results()
    print(f"Current state: {round_machine.current_state.id}")
    
    print("Applying effects...")
    round_machine.effects_determined()
    print(f"Current state: {round_machine.current_state.id}")
    
    print("Describing results...")
    round_machine.results_ready()
    print(f"Current state: {round_machine.current_state.id}")
    
    # Check if we're in the final state
    print(f"Is in final state: {round_machine.presenting_results.is_active}")


def test_contest_machine():
    """Test the contest machine."""
    print("\n=== Testing ContestMachine ===")
    
    # Create a contest machine
    contest = ContestMachine()
    print(f"Initial state: {contest.current_state.id}")
    
    # Start contest
    print("Starting contest...")
    contest.start_contest()
    print(f"Contest state: {contest.current_state.id}")
    
    # Get the setup machine
    setup_machine = contest.setup_machine
    if setup_machine is not None:
        print(f"Setup machine initial state: {setup_machine.current_state.id}")
        
        # Transition through setup states
        print("Generating features...")
        setup_machine.features_generated()
        print(f"Setup machine state: {setup_machine.current_state.id}")
        
        print("Generating positions...")
        setup_machine.positions_generated()
        print(f"Setup machine state: {setup_machine.current_state.id}")
        
        # Check if setup is done
        print(f"Setup done: {contest.check_setup_done()}")
    else:
        print("Setup machine not available")
    
    # Move to ready state
    print("\nSetup done, moving to ready state...")
    contest.setup_done()
    print(f"Contest state: {contest.current_state.id}")
    
    # Start round
    print("\nStarting round...")
    contest.start_round()
    print(f"Contest state: {contest.current_state.id}")
    
    # Get the round machine
    round_machine = contest.round_machine
    if round_machine:
        print(f"Round machine initial state: {round_machine.current_state.id}")
        
        # Transition through round states
        print("Sending prompt...")
        round_machine.prompt_sent()
        print(f"Round machine state: {round_machine.current_state.id}")
        
        print("Receiving actions...")
        round_machine.actions_received()
        print(f"Round machine state: {round_machine.current_state.id}")
        
        print("Judging actions...")
        round_machine.raw_results()
        print(f"Round machine state: {round_machine.current_state.id}")
        
        print("Applying effects...")
        round_machine.effects_determined()
        print(f"Round machine state: {round_machine.current_state.id}")
        
        print("Describing results...")
        round_machine.results_ready()
        print(f"Round machine state: {round_machine.current_state.id}")
        
        # Check if round is done
        print(f"Round done: {contest.check_round_done()}")
    else:
        print("Round machine not available")
    
    # Move to checking end state
    print("\nRound done, moving to checking end state...")
    contest.round_done()
    print(f"Contest state: {contest.current_state.id}")
    
    # Check if more rounds remain
    print("\nMore rounds remain...")
    contest.more_rounds_remain()
    print(f"Contest state: {contest.current_state.id}")
    
    # Start another round
    print("\nStarting another round...")
    contest.start_round()
    print(f"Contest state: {contest.current_state.id}")
    
    # Complete the round quickly
    round_machine = contest.round_machine
    if round_machine:
        print(f"New round machine initial state: {round_machine.current_state.id}")
        round_machine.prompt_sent()
        round_machine.actions_received()
        round_machine.raw_results()
        round_machine.effects_determined()
        round_machine.results_ready()
        print(f"Round machine final state: {round_machine.current_state.id}")
    else:
        print("Round machine not available")
    
    # Move to checking end state
    print("\nRound done, moving to checking end state...")
    contest.round_done()
    print(f"Contest state: {contest.current_state.id}")
    
    # End condition met
    print("\nEnd condition met...")
    contest.end_condition_met()
    print(f"Contest state: {contest.current_state.id}")
    
    # Check if we're in the final state
    print(f"Is in final state: {contest.completed.is_active}")
    
    # Get state dictionary
    state_dict = contest.get_state_dict()
    print(f"\nState dictionary: {state_dict}")


def main():
    """Run all tests."""
    test_setup_machine()
    # test_round_machine()
    # test_contest_machine()


if __name__ == "__main__":
    main()