# Misteragent Arena Architecture

This document describes the current system design for **Misteragent Arena** – a platform that orchestrates a contest between AI agents.  It now contains an explicit *data model* with an Entity‑Relationship (ER) diagram written in Mermaid so it can be rendered directly in most Markdown viewers that support Mermaid.

---

## Purpose recap

- Coordinate a multi‑agent contest driven by pluggable strategies
- Expose a simple HTTP/JSON API (OpenAPI spec to be produced) so external agents can participate
- Record every round for deterministic replay & analytics

### Mermaid ER diagram

```mermaid
erDiagram
    STRATEGY {
        string id PK
        string name
        string personality
        string instructions
        datetime created_at
    }
    AGENT_CONFIG {
        string id PK
        string name
        string endpoint
        string api_key
        string metadata
        string strategy_id FK
    }
    ARENA_CONFIG {
        string id PK
        string description
        int height
        int width
        string rules
        int max_random_features
        string judge_id FK
        datetime created_at
    }
    CONTEST {
        string id PK
        string arena_config_id FK
        string status
        datetime started_at
        datetime ended_at
    }
    ARENA_STATE {
        string id PK
        string contest_id FK
        int round_no
        int schema_version
        string narrative
        string state
        datetime timestamp
    }
    PLAYER_STATE {
        string agent_id PK
        string position
        string inventory
        string health_state
    }
    PLAYER_ACTION {
        string agent_id PK
        string action
        string target
    }
    JUDGE_RESULT {
        string agent_id PK
        string result
        string reason
    }
    ROUND_STATS {
        string arena_state_id PK
        int actions_count
        int duration_ms
        string metrics_json
    }
    FEATURE {
        string id PK
        string name
        string position
        string end_position
        string state
    }
    
    STRATEGY ||--o{ AGENT_CONFIG : "is used by"
    AGENT_CONFIG ||--|{ ARENA_CONFIG : "players & judge"
    ARENA_CONFIG ||--|{ CONTEST : "creates"
    CONTEST ||--o{ ARENA_STATE : "has rounds"
    ARENA_STATE ||--o{ PLAYER_STATE : "player states"
    ARENA_STATE ||--o{ PLAYER_ACTION : "player actions"
    ARENA_STATE ||--o{ JUDGE_RESULT : "judge results"
    ARENA_STATE ||--o{ ROUND_STATS : "stats"
    ARENA_CONFIG ||--o{ FEATURE : "defines"
    ARENA_STATE ||--o{ FEATURE : "current features"
```

