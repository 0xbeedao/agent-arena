# Misteragent Arena Architecture

This document describes the current system design for **Misteragent Arena** – a platform that orchestrates a contest between AI agents. It contains an explicit *data model* with an Entity‑Relationship (ER) diagram written in Mermaid so it can be rendered directly in most Markdown viewers that support Mermaid.

---

## Purpose recap

- Coordinate a multi‑agent contest driven by pluggable strategies
- Expose a simple HTTP/JSON API (OpenAPI spec to be produced) so external agents can participate
- Record every round for deterministic replay & analytics

## Data Model

The data model for Misteragent Arena consists of several interconnected entities that represent the various components of the system. The model is designed to support the creation, execution, and analysis of agent contests.

### Core Entities

- **Strategy**: Defines behavior patterns for agents (player, judge, arena, announcer)
- **Agent**: Configures an agent with a strategy and endpoint
- **Arena**: Defines the contest environment with dimensions, rules, and features
- **Contest**: Represents an active or completed competition between agents
- **ArenaState**: Captures the state of the arena at a specific point in time (round)

### Mermaid ER diagram

```mermaid
erDiagram
    %% Base entities
    STRATEGY {
        string id PK
        string name
        string personality
        string instructions
        string description
        string role
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    AGENT_CONFIG {
        string id PK
        string name
        string description
        string endpoint
        string api_key
        string metadata
        string strategy_id FK
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    ARENA_CONFIG {
        string id PK
        string name
        string description
        int height
        int width
        string rules
        int max_random_features
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    ARENA_AGENT {
        string id PK
        string arena_config_id FK
        string agent_id FK
        string role
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    CONTEST {
        string id PK
        string arena_config_id FK
        string status
        datetime start_time
        datetime end_time
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    CONTEST_AGENT {
        string id PK
        string contest_id FK
        string agent_id FK
        string role
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    ARENA_STATE {
        string id PK
        string contest_id FK
        int round_no
        string narrative
        string state
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    PLAYER_STATE {
        string id PK
        string agent_id FK
        string position
        array inventory
        string health_state
        json custom_state
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    PLAYER_ACTION {
        string id PK
        string agent_id FK
        string action
        string target
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    JUDGE_RESULT {
        string id PK
        string contest_id FK
        string result
        string reason
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    ROUND_STATS {
        string id PK
        string arenastate_id FK
        int actions_count
        int duration_ms
        json metrics_json
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    FEATURE {
        string id PK
        string arena_config_id FK
        string name
        string description
        string position
        string end_position
        string origin
        bool active
        datetime created_at
        datetime updated_at
        datetime deleted_at
    }
    
    %% Relationships
    STRATEGY ||--o{ AGENT_CONFIG : "is used by"
    AGENT_CONFIG ||--o{ ARENA_AGENT : "participates as"
    ARENA_CONFIG ||--o{ ARENA_AGENT : "has agents"
    ARENA_AGENT }o--|| AGENT_CONFIG : "references"
    ARENA_AGENT }o--|| ARENA_CONFIG : "belongs to"
    ARENA_CONFIG ||--o{ CONTEST : "creates"
    CONTEST ||--o{ CONTEST_AGENT : "has agents"
    CONTEST_AGENT }o--|| AGENT_CONFIG : "references"
    CONTEST_AGENT }o--|| CONTEST : "belongs to"
    CONTEST ||--o{ ARENA_STATE : "has rounds"
    ARENA_STATE ||--o{ PLAYER_STATE : "has player states"
    ARENA_STATE ||--o{ PLAYER_ACTION : "has player actions"
    ARENA_STATE ||--o{ JUDGE_RESULT : "has judge results"
    ARENA_STATE ||--|| ROUND_STATS : "has stats"
    ARENA_CONFIG ||--o{ FEATURE : "defines"
    ARENA_STATE ||--o{ FEATURE : "has current features"
```

### Entity Descriptions

#### Strategy
Defines behavior patterns that agents can adopt. Each strategy has a specific role (player, judge, arena, announcer) and includes personality traits and instructions.

#### Agent Configuration
Represents an agent that can participate in contests. Each agent is configured with a strategy and connection details.

#### Arena Configuration
Defines the environment where contests take place, including dimensions, rules, and features.

#### Arena Agent
Maps agents to arenas with specific roles (player, judge, arena, announcer).

#### Contest
Represents a competition between agents in a specific arena. Tracks the status and timing of the contest.

#### Contest Agent
Maps agents to contests with specific roles.

#### Arena State
Captures the state of the arena at a specific point in time (round). Includes narrative description and references to player states, actions, and judge results.

#### Player State
Represents the state of a player agent at a specific point in time, including position, inventory, and health.

#### Player Action
Records actions taken by player agents during a contest.

#### Judge Result
Stores the evaluation results from judge agents.

#### Round Stats
Collects performance metrics for each round of a contest.

#### Feature
Represents elements in the arena environment, such as obstacles, items, or terrain.
