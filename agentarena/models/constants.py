from enum import Enum


class ContestRoundState(str, Enum):
    """
    Represents the state of a contest round.
    """

    IDLE = "idle"
    CREATING_ROUND = "creating_round"
    ADDING_FIXED_FEATURES = "adding_fixed_features"
    GENERATING_FEATURES = "generating_features"
    GENERATING_POSITIONS = "generating_positions"
    DESCRIBING_SETUP = "describing_setup"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    FAIL = "fail"


class ContestState(str, Enum):
    """
    Status of a contest.
    """

    # Initial states
    CREATED = "created"

    # In progress states
    STARTING = "starting"
    ROLE_CALL = "role_call"
    SETUP_ARENA = "setup_arena"
    IN_ROUND = "in_round"
    CHECK_WIN = "check_win"

    # Final states
    FAIL = "fail"
    COMPLETE = "complete"


class JobState(str, Enum):
    IDLE = "idle"
    REQUEST = "request"
    RESPONSE = "response"
    WAITING = "waiting"
    FAIL = "fail"
    COMPLETE = "complete"


class JobResponseState(str, Enum):
    COMPLETE = "complete"
    PENDING = "pending"
    FAIL = "fail"


class PromptType(str, Enum):
    """
    Enum for prompt keys
    """

    ANNOUNCER_DESCRIBE_ARENA = "announcer_describe_arena"
    ARENA_GENERATE_FEATURES = "arena_generate_features"
    JUDGE_PLAYER_ACTION_JUDGEMENT = "judge_player_action_judgement"
    PLAYER_PLAYER_ACTION = "player_player_action"


class RoleType(str, Enum):
    """
    Roles for participants in contests
    """

    PLAYER = "player"
    ARENA = "arena"
    JUDGE = "judge"
    ANNOUNCER = "announcer"


DEFAULT_AGENT_MODEL = "openrouter/deepseek/deepseek-chat-v3-0324:free"
# "openrouter/deepseek/deepseek-r1-0528:free"
