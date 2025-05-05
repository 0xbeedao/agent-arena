from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from agentarena.controllers import agent_controller
from agentarena.models.agent import AgentDTO
from agentarena.models.validation import ValidationResponse
from agentarena.services.model_service import ModelResponse


@pytest.fixture
def mock_agent_service():
    service = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_create_agent_success(mock_agent_service):
    agent = AgentDTO(
        id="a1", name="Agent1", description="desc", type="player", version="1.0"
    )
    mock_agent_service.create.return_value = ["a1", ModelResponse(success=True)]
    result = await agent_controller.create_agent(
        agent_config=agent, agent_service=mock_agent_service
    )
    assert result == {"id": "a1"}
    mock_agent_service.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_agent_failure(mock_agent_service):
    agent = AgentDTO(
        id="a1",
        name="Agent1",
        description="desc",
        version="1.0",
        endpoint="/test",
    )
    mock_agent_service.create.return_value = [
        None,
        ModelResponse(success=False, validation=None),
    ]
    with pytest.raises(HTTPException) as exc:
        await agent_controller.create_agent(
            agent_config=agent, agent_service=mock_agent_service
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_get_agent_success(mock_agent_service):
    agent = AgentDTO(
        id="a1", name="Agent1", description="desc", type="player", version="1.0"
    )
    mock_agent_service.get.return_value = [agent, ModelResponse(success=True)]
    result = await agent_controller.get_agent(
        agent_id="a1", agent_service=mock_agent_service
    )
    assert result == agent
    mock_agent_service.get.assert_awaited_once_with("a1")


@pytest.mark.asyncio
async def test_get_agent_not_found(mock_agent_service):
    mock_agent_service.get.return_value = [
        None,
        ModelResponse(success=False, error="not found"),
    ]
    with pytest.raises(HTTPException) as exc:
        await agent_controller.get_agent(
            agent_id="a1", agent_service=mock_agent_service
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_agent_list(mock_agent_service):
    agent = AgentDTO(
        id="a1", name="Agent1", description="desc", type="player", version="1.0"
    )
    mock_agent_service.list.return_value = [agent]
    result = await agent_controller.get_agent_list(agent_service=mock_agent_service)
    assert result == [agent]
    mock_agent_service.list.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_agent_success(mock_agent_service):
    agent = AgentDTO(
        id="a1", name="Agent1", description="desc", type="player", version="1.0"
    )
    mock_agent_service.update.return_value = ModelResponse(success=True)
    result = await agent_controller.update_agent(
        agent_id="a1", agent_config=agent, agent_service=mock_agent_service
    )
    assert result == {"success": True}
    mock_agent_service.update.assert_awaited_once_with("a1", agent)


@pytest.mark.asyncio
async def test_update_agent_failure(mock_agent_service):
    agent = AgentDTO(
        id="a1", name="Agent1", description="desc", type="player", version="1.0"
    )
    mock_agent_service.update.return_value = ModelResponse(
        success=False, validation=None
    )
    with pytest.raises(HTTPException) as exc:
        await agent_controller.update_agent(
            agent_id="a1", agent_config=agent, agent_service=mock_agent_service
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_delete_agent_success(mock_agent_service):
    mock_agent_service.delete_model.return_value = ModelResponse(success=True)
    result = await agent_controller.delete_agent(
        agent_id="a1", agent_service=mock_agent_service
    )
    assert result == {"success": True}
    mock_agent_service.delete_model.assert_awaited_once_with("a1", mock_agent_service)


@pytest.mark.asyncio
async def test_delete_agent_failure(mock_agent_service):
    mock_agent_service.delete_model.return_value = ModelResponse(
        success=False, validation=ValidationResponse(success=False, message="test")
    )
    with pytest.raises(HTTPException) as exc:
        await agent_controller.delete_agent(
            agent_id="a1", agent_service=mock_agent_service
        )
    assert exc.value.status_code == 422
