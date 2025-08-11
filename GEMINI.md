# Agent Arena Project - Gemini Context

## Project Overview

Agent Arena is a Python-based system that orchestrates contests between AI agents using an actor-agent architecture. The system features:

- **Replayability**: Contests can be replayed with different configurations
- **Multi-agents**: Supports multiple AI agents competing in contests
- **External client support**: Allows external clients to interact with the system

The system is built using FastAPI and follows a microservices architecture with distinct components:

1. **Actor Service** (port 8001): Handles agent interactions and responses
2. **Arena Service** (port 8000): Manages contest orchestration and coordination
3. **Scheduler Service** (port 8002): Handles job scheduling and background tasks

## Key Technologies

- **Python 3.11+** with uv for package management
- **FastAPI** for REST API endpoints
- **SQLite** for data persistence
- **NATS** message broker for inter-service communication
- **Dependency Injector** for dependency management
- **Pydantic** for data validation
- **LLM integrations** with support for multiple providers (OpenAI, Anthropic, etc.)

## Project Structure

```
agent-arena/
├── agentarena/              # Main Python package
│   ├── actors/              # Actor service components
│   ├── arena/               # Arena service components
│   ├── clients/             # Client integrations
│   ├── controlpanel/        # Control panel UI
│   ├── core/                # Core services and factories
│   ├── integration/         # Integration utilities
│   ├── models/              # Data models
│   └── util/                # Utility functions
├── scripts/                 # Service startup scripts
├── docs/                    # Documentation
├── etc/                     # Configuration files and word lists
├── notebooks/               # Jupyter notebooks
├── .venv/                   # Python virtual environment
├── agent-arena-config.yaml  # Main configuration file
└── pyproject.toml           # Python project configuration
```

## Building and Running

### Prerequisites

1. Python 3.11+
2. uv package manager (`pip install uv`)
3. NATS message broker (for inter-service communication)

### Setup

1. **Activate the virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **Install dependencies** (if not already installed):
   ```bash
   uv sync
   ```

### Running Services

The project uses `just` as a command runner. Install it with:
```bash
# On macOS
brew install just

# On Linux
# See https://github.com/casey/just#installation
```

Start all services:
```bash
just all
```

Or start individual services:
```bash
# Start the actor service
just actor

# Start the arena service
just arena

# Start the scheduler service
just scheduler

# Start the control panel
just control
```

Alternative manual startup:
```bash
# Actor service
PYTHONPATH=. python scripts/agentarena.actor

# Arena service
PYTHONPATH=. python scripts/agentarena.arena

# Scheduler service
PYTHONPATH=. python scripts/agentarena.scheduler

# Control panel
PYTHONPATH=. python scripts/agentarena.control
```

### Loading Fixtures

To load initial data:
```bash
just load
# or
PYTHONPATH=. python scripts/load_fixtures.py etc/fixtures
```

## Development

### Code Organization

The project follows a domain-driven design with these key modules:

1. **actors/**: Manages AI agents, strategies, and their interactions
2. **arena/**: Handles contest orchestration, rounds, and game state
3. **core/**: Provides shared services like database, logging, and dependency injection
4. **models/**: Contains Pydantic models for data validation
5. **clients/**: Integrations with external services

### Testing

Run tests with:
```bash
just test
# or
PYTHONPATH=. pytest
```

### Code Quality

The project uses several tools for code quality:

1. **Black** for code formatting
2. **isort** for import sorting
3. **autoflake** for removing unused imports
4. **mypy** for type checking

Run formatting and linting:
```bash
just lint
```

### Configuration

The system uses YAML configuration files:
- `agent-arena-config.yaml`: Main configuration
- `agent-arena-test-config.yaml`: Test configuration

Key configuration sections:
- Database settings
- Logging configuration
- Service URLs
- Message broker connection
- LLM model definitions

### Logging

Each service has its own log file:
- `actor.log`: Actor service logs
- `arena.log`: Arena service logs
- `scheduler.log`: Scheduler service logs

Log levels and locations are configurable in the YAML files.

### Database

The system uses SQLite databases:
- `arena.db`: Arena service database
- `actor.db`: Actor service database
- `scheduler.db`: Scheduler service database

Test databases are separate:
- `arena-test.db`
- `actor-test.db`
- `scheduler-test.db`

## API Endpoints

### Actor Service (localhost:8001)
- `/health`: Health check endpoint
- Agent management endpoints
- Strategy management endpoints

### Arena Service (localhost:8000)
- `/health`: Health check endpoint
- Contest management endpoints
- Arena management endpoints

### Common Patterns
- All services follow REST conventions
- JSON request/response bodies
- Standard HTTP status codes

## Architecture

The system follows an actor-agent architecture with these key components:

1. **Arena**: Orchestrates the contest between AI agents
2. **Actor**: Handles the contest orchestration and communication
3. **Agent**: Manages AI agent interactions and responses
4. **Judge**: Evaluates player actions
5. **Announcer**: Describes rounds to players in various personas

### Contest Flow

1. **Setup Phase**: Create arena, add features, configure agents
2. **Round Flow**: 
   - Send round prompt to players
   - Collect player actions
   - Judge actions
   - Apply effects
   - Describe results
3. **Repeat**: Continue for each round until completion

## LLM Integration

The system supports numerous LLM providers through a unified interface:
- OpenAI (GPT models)
- Anthropic (Claude models)
- Mistral
- Qwen
- Gemini
- And many others

Models are configured in the YAML configuration files with provider keys.

## Development Conventions

1. **Dependency Injection**: Uses `dependency-injector` for managing dependencies
2. **State Machines**: Implements contest and round state management using `python-statemachine`
3. **Async/Await**: Extensive use of async/await for non-blocking operations
4. **Type Hints**: Comprehensive type annotations throughout the codebase
5. **Pydantic Models**: Data validation using Pydantic models
6. **Factory Pattern**: Uses factories for creating services and resources
7. **Middleware**: Custom middleware for logging and error handling

## Troubleshooting

1. **Services won't start**: Check if NATS broker is running
2. **Database issues**: Verify database file permissions and paths
3. **LLM errors**: Check API keys and model configurations
4. **Port conflicts**: Ensure ports 8000-8002 are available

To kill running services:
```bash
just kill
```