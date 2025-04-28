# ModelService

The `ModelService` is a generic service that provides CRUD operations for any model that inherits from `DbBase`. It abstracts away the common database operations, allowing you to focus on your business logic.

## Overview

The `ModelService` class is designed to work with any Pydantic model that inherits from `DbBase`. It provides the following operations:

- `create`: Create a new model instance
- `get`: Get a model instance by ID
- `update`: Update a model instance
- `delete`: Delete a model instance
- `list`: List all model instances

## Usage

### Basic Usage

```python
from agentarena.services.model_service import ModelService
from agentarena.models.agent import AgentConfig
from agentarena.services.db_service import DbService

# Initialize the DbService
db_service = DbService(...)

# Create a ModelService for AgentConfig
agent_service = ModelService(AgentConfig, db_service, "agents")

# Create a new agent
agent = AgentConfig(name="Agent 1", endpoint="https://example.com")
agent_id = await agent_service.create(agent)

# Get the agent
agent = await agent_service.get(agent_id)

# Update the agent
agent.name = "Updated Agent"
success = await agent_service.update(agent_id, agent)

# Delete the agent
success = await agent_service.delete(agent_id)

# List all agents
agents = await agent_service.list()
```

### Table Name Inference

If you don't provide a table name, the `ModelService` will infer it from the model class name:

```python
# This will use the "agents" table
agent_service = ModelService(AgentConfig, db_service)
```

The table name is inferred by converting the model class name to lowercase and adding an "s" at the end. For example:

- `AgentConfig` -> `agentconfigs`
- `Strategy` -> `strategies` (special case)

### Dependency Injection

You can use the `ModelService` with dependency injection in your controllers:

```python
from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from agentarena.services.model_service import ModelService
from agentarena.models.agent import AgentConfig
from agentarena.config.containers import Container

@inject
async def create_agent(
    agent_config: AgentConfig,
    agent_service: ModelService[AgentConfig] = Depends(Provide[Container.agent_service])
):
    agent_id = await agent_service.create(agent_config)
    return {"id": agent_id}
```

## Implementation Details

The `ModelService` class is implemented as a generic class that takes a type parameter `T` which must be a subclass of `DbBase`. This allows the service to work with any model that inherits from `DbBase`.

```python
T = TypeVar('T', bound=DbBase)

class ModelService(Generic[T]):
    def __init__(self, model_class: Type[T], dbService: DbService, table_name: Optional[str] = None):
        # ...
```

The service uses the `model_class` parameter to validate and convert database rows to model instances. It also uses the model class name for logging and audit purposes.

## Benefits

Using the `ModelService` provides several benefits:

1. **Reduced code duplication**: You don't need to implement the same CRUD operations for each model.
2. **Consistent behavior**: All models are handled in the same way, making the code more predictable.
3. **Type safety**: The service is generic, so you get type checking for free.
4. **Easier testing**: You can mock the service for testing purposes.
5. **Simplified dependency injection**: You can inject the service into your controllers.

## Example

See `src/test_model_service.py` for a complete example of how to use the `ModelService`.