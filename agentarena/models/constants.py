from enum import Enum


class PromptType(str, Enum):
    """
    Enum for prompt keys
    """

    ARENA_DESCRIBE_ARENA = "arena.describe_arena"
    ARENA_GENERATE_FEATURES = "arena.generate_features"
    JUDGE_PLAYER_ACTION_JUDGEMENT = "judge.player_action_judgement"
    PLAYER_PLAYER_ACTION = "player.player_action"


class RoleType(str, Enum):
    """
    Roles for participants in contests
    """

    PLAYER = "player"
    ARENA = "arena"
    JUDGE = "judge"
    ANNOUNCER = "announcer"
