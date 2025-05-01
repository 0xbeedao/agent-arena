"""
Test script to verify that all models can be imported correctly.
"""

from agentarena.models import (
    StrategyDTO,
    AgentDTO,
    ArenaDTO,
    ContestDTO,
    ArenaStateDTO,
    PlayerStateDTO,
    PlayerAction,
    JudgeResult,
    FeatureDTO,
    RoundStatsDTO,
)


def main():
    """Print all model classes to verify they can be imported."""
    models = [
        StrategyDTO,
        AgentDTO,
        ArenaDTO,
        ContestDTO,
        ArenaStateDTO,
        PlayerStateDTO,
        PlayerAction,
        JudgeResult,
        FeatureDTO,
        RoundStatsDTO,
    ]
    
    print("Successfully imported the following models:")
    for model in models:
        print(f"- {model.__name__}")


if __name__ == "__main__":
    main()