"""
Test script to verify that all models can be imported correctly.
"""

from agentarena.models import (
    Strategy,
    AgentConfig,
    ArenaConfig,
    Contest,
    ArenaState,
    PlayerState,
    PlayerAction,
    JudgeResult,
    Feature,
    RoundStats,
)


def main():
    """Print all model classes to verify they can be imported."""
    models = [
        Strategy,
        AgentConfig,
        ArenaConfig,
        Contest,
        ArenaState,
        PlayerState,
        PlayerAction,
        JudgeResult,
        Feature,
        RoundStats,
    ]
    
    print("Successfully imported the following models:")
    for model in models:
        print(f"- {model.__name__}")


if __name__ == "__main__":
    main()