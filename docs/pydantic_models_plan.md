# Pydantic Models Plan

This document outlines the plan for implementing Pydantic models based on the ER diagram in `docs/model-diagrams.md` and the schemas in `openapi.yaml`.

## Directory Structure

```
src/agentarena/models/
├── __init__.py
├── strategy.py
├── agent.py
├── arena.py
├── contest.py
├── state.py
├── player.py
├── judge.py
├── feature.py
└── stats.py
```

## Model Implementations

### __init__.py

```python
"""
Pydantic models for the Agent Arena application.
"""

from .strategy import Strategy
from .agent import AgentConfig
from .arena import ArenaConfig
from .contest import Contest
from .state import ArenaState
from .player import PlayerState, PlayerAction
from .judge import JudgeResult
from .feature import Feature
from .stats import RoundStats

__all__ = [
    "Strategy",
    "AgentConfig",
    "ArenaConfig",
    "Contest",
    "ArenaState",
    "PlayerState",
    "PlayerAction",
    "JudgeResult",
    "Feature",
    "RoundStats",
]
```

### strategy.py

```python
from datetime import datetime
from pydantic import BaseModel, Field

class Strategy(BaseModel):
    """
    Represents a strategy that can be used by an agent.
    
    Maps to the STRATEGY entity in the ER diagram.
    """
    id: str = Field(description="Unique identifier (ULID)")
    name: str = Field(description="Strategy name")
    personality: str = Field(description="Personality description")
    instructions: str = Field(description="Strategy instructions")
    created_at: datetime = Field(description="Creation timestamp")
```

### agent.py

```python
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    """
    Configuration for an agent.
    
    Maps to the AGENT_CONFIG entity in the ER diagram.
    """
    id: str = Field(description="Unique identifier (ULID)")
    name: str = Field(description="Agent name")
    endpoint: str = Field(description="API endpoint for the agent")
    api_key: str = Field(description="API key for authentication")
    metadata: str = Field(description="Additional metadata")
    strategy_id: str = Field(description="Reference to Strategy")
```

### arena.py

```python
from datetime import datetime
from pydantic import BaseModel, Field

class ArenaConfig(BaseModel):
    """
    Configuration for an arena.
    
    Maps to the ARENA_CONFIG entity in the ER diagram.
    """
    id: str = Field(description="Unique identifier (ULID)")
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    max_random_features: int = Field(description="Maximum number of random features", ge=0)
    judge_id: str = Field(description="Reference to Judge agent")
    created_at: datetime = Field(description="Creation timestamp")
```

### contest.py

```python
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum

class ContestStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Contest(BaseModel):
    """
    Represents a contest between agents.
    
    Maps to the CONTEST entity in the ER diagram.
    """
    id: str = Field(description="Unique identifier (ULID)")
    arena_config_id: str = Field(description="Reference to ArenaConfig")
    status: ContestStatus = Field(description="Contest status")
    started_at: datetime | None = Field(default=None, description="Start timestamp")
    ended_at: datetime | None = Field(default=None, description="End timestamp")
```

### state.py

```python
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .feature import Feature
from .player import PlayerState, PlayerAction
from .judge import JudgeResult

class ArenaState(BaseModel):
    """
    Represents the state of the arena at a specific point in time.
    
    Maps to the ARENA_STATE entity in the ER diagram.
    """
    id: str = Field(description="Unique identifier (ULID)")
    contest_id: str = Field(description="Reference to Contest")
    round_no: int = Field(description="Round number", ge=0)
    schema_version: int = Field(description="Schema version")
    narrative: Optional[str] = Field(default=None, description="Round narrative")
    state: str = Field(description="Arena state")
    timestamp: datetime = Field(description="Timestamp")
    
    # These fields are from the OpenAPI schema but not in the ER diagram
    features: List[Feature] = Field(default_factory=list, description="Arena features")
    player_states: Dict[str, PlayerState] = Field(default_factory=dict, description="Player states")
    player_actions: Dict[str, PlayerAction] = Field(default_factory=dict, description="Player actions")
    judge_results: Dict[str, JudgeResult] = Field(default_factory=dict, description="Judge results")
```

### player.py

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PlayerState(BaseModel):
    """
    Represents the state of a player.
    
    Maps to the PLAYER_STATE entity in the ER diagram.
    """
    agent_id: str = Field(description="Agent identifier")
    position: str = Field(description="Grid coordinate as 'x,y'")
    inventory: Optional[List[str]] = Field(default=None, description="Player inventory")
    health_state: str = Field(description="Health state")
    custom_state: Optional[Dict[str, Any]] = Field(default=None, description="Custom state data")

class PlayerAction(BaseModel):
    """
    Represents an action taken by a player.
    
    Maps to the PLAYER_ACTION entity in the ER diagram.
    """
    agent_id: str = Field(description="Agent identifier")
    action: str = Field(description="Action description")
    target: Optional[str] = Field(default=None, description="Target coordinate as 'x,y'")
```

### judge.py

```python
from pydantic import BaseModel, Field

class JudgeResult(BaseModel):
    """
    Represents the result of a judge's evaluation.
    
    Maps to the JUDGE_RESULT entity in the ER diagram.
    """
    agent_id: str = Field(description="Agent identifier")
    result: str = Field(description="Result description")
    reason: Optional[str] = Field(default=None, description="Reason for the result")
```

### feature.py

```python
from typing import Optional
from pydantic import BaseModel, Field

class Feature(BaseModel):
    """
    Represents a feature in the arena.
    
    Maps to the FEATURE entity in the ER diagram.
    """
    id: str = Field(description="Unique identifier (ULID)")
    name: str = Field(description="Feature name")
    position: str = Field(description="Grid coordinate as 'x,y'")
    end_position: Optional[str] = Field(default=None, description="End coordinate for features with area")
    state: Optional[str] = Field(default=None, description="Feature state")
```

### stats.py

```python
from typing import Dict, Any
from pydantic import BaseModel, Field

class RoundStats(BaseModel):
    """
    Statistics for a round.
    
    Maps to the ROUND_STATS entity in the ER diagram.
    """
    arena_state_id: str = Field(description="Reference to ArenaState")
    actions_count: int = Field(description="Number of actions in the round")
    duration_ms: int = Field(description="Round duration in milliseconds")
    metrics_json: Dict[str, Any] = Field(description="Additional metrics as JSON")
```

## Implementation Notes

1. All models use Pydantic v2 BaseModel
2. Models follow Python naming conventions (PascalCase for class names, snake_case for fields)
3. All fields include proper type annotations and descriptions
4. Validation is included where appropriate based on the ER diagram and OpenAPI schema
5. IDs are handled as ULIDs according to the specification at https://github.com/ulid/spec

## Next Steps

1. Switch to Code mode to implement these models
2. Create the directory structure
3. Implement each model file
4. Add tests to verify the models work as expected