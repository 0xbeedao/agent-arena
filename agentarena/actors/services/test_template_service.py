import json
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest
from jinja2 import Template
from jinja2 import TemplateNotFound
from sqlmodel import Session

from agentarena.actors.models import Agent
from agentarena.actors.models import StrategyPrompt
from agentarena.actors.services.template_service import InvalidTemplateException
from agentarena.actors.services.template_service import TemplateService
from agentarena.models.constants import PromptType
from agentarena.models.requests import ParticipantRequest


@pytest.fixture
def mock_strategy_service():
    return MagicMock()


@pytest.fixture
def mock_logger():
    logger = MagicMock()
    logger.get_logger.return_value = MagicMock()
    return logger


@pytest.fixture
def template_service(mock_strategy_service, mock_logger):
    return TemplateService(mock_strategy_service, mock_logger)


@pytest.fixture
def mock_session():
    return MagicMock(spec=Session)


@pytest.mark.asyncio
async def test_expand_prompt_raw(template_service, mock_session):
    """Test expanding a raw prompt (non-Jinja)"""
    agent = Agent(id="agent1", strategy_id="strategy1", participant_id="participant1")
    req = ParticipantRequest(
        job_id="job1",
        command=PromptType.PLAYER_PLAYER_ACTION,
        data="{}",
        message="test",
    )

    # Mock get_prompt to return a raw prompt
    template_service.get_prompt = AsyncMock(
        return_value=StrategyPrompt(
            strategy_id="strategy1",
            key=PromptType.PLAYER_PLAYER_ACTION,
            prompt="Hello World",
        )
    )

    result = await template_service.expand_prompt(agent, req, mock_session)
    assert result == "Hello World"


@pytest.mark.asyncio
async def test_expand_prompt_jinja(template_service, mock_session):
    """Test expanding a Jinja-templated prompt"""
    agent = Agent(id="agent1", strategy_id="strategy1", participant_id="participant1")
    req = ParticipantRequest(
        job_id="job1",
        command=PromptType.PLAYER_PLAYER_ACTION,
        data=json.dumps({"name": "Alice"}),
    )

    # Mock get_prompt to return a Jinja prompt
    template_service.get_prompt = AsyncMock(
        return_value=StrategyPrompt(
            strategy_id="strategy1",
            key=PromptType.PLAYER_PLAYER_ACTION,
            prompt="#jinja:greeting",
        )
    )

    # Mock template rendering
    template_service.render_template = MagicMock(return_value="Hello Alice")

    result = await template_service.expand_prompt(agent, req, mock_session)
    assert result == "Hello Alice"
    template_service.render_template.assert_called_with(
        "greeting", {"name": "Alice", "agent": agent}
    )


@pytest.mark.asyncio
async def test_expand_prompt_invalid_template(template_service, mock_session):
    """Test error handling for invalid templates"""
    agent = Agent(id="agent1", strategy_id="strategy1", participant_id="participant1")
    req = ParticipantRequest(
        job_id="job1", command=PromptType.PLAYER_PLAYER_ACTION, data=json.dumps({})
    )

    template_service.get_prompt = AsyncMock(
        return_value=StrategyPrompt(
            strategy_id="strategy1",
            key=PromptType.PLAYER_PLAYER_ACTION,
            prompt="#jinja:invalid_template",
        )
    )
    template_service.render_template = MagicMock(
        side_effect=InvalidTemplateException("invalid_template")
    )

    with pytest.raises(InvalidTemplateException):
        await template_service.expand_prompt(agent, req, mock_session)


@pytest.mark.asyncio
async def test_get_prompt_success(template_service, mock_session):
    """Test successfully retrieving a prompt"""
    stmt_mock = MagicMock()
    mock_session.exec.return_value = stmt_mock
    stmt_mock.first.return_value = StrategyPrompt(
        strategy_id="strategy1",
        key=PromptType.PLAYER_PLAYER_ACTION,
        prompt="Test prompt",
    )

    result = await template_service.get_prompt(
        "strategy1", PromptType.PLAYER_PLAYER_ACTION, mock_session
    )
    assert result.prompt == "Test prompt"
    mock_session.exec.assert_called_once()


@pytest.mark.asyncio
async def test_get_prompt_not_found(template_service, mock_session):
    """Test error when prompt not found"""
    stmt_mock = MagicMock()
    mock_session.exec.return_value = stmt_mock
    stmt_mock.first.return_value = None

    with pytest.raises(InvalidTemplateException) as excinfo:
        await template_service.get_prompt(
            "strategy1", PromptType.PLAYER_PLAYER_ACTION, mock_session
        )

    assert "No such template player_player_action for strategy strategy1" in str(
        excinfo.value
    )


def test_get_template_success(template_service):
    """Test finding an existing template"""
    # Mock Jinja environment
    mock_template = MagicMock()
    template_service.env.select_template = MagicMock(return_value=mock_template)

    template = template_service.get_template("valid_template")
    assert template == mock_template
    template_service.env.select_template.assert_called_with(
        ["valid_template", "valid_template.md", "valid_template.md.j2"]
    )


def test_get_template_not_found(template_service):
    """Test error when template not found"""
    template_service.env.select_template = MagicMock(
        side_effect=TemplateNotFound("missing")
    )

    with pytest.raises(InvalidTemplateException) as excinfo:
        template_service.get_template("missing_template")

    assert "missing_template" in str(excinfo.value)
    template_service.log.error.assert_called_with(
        "could not find template", key="missing_template"
    )


def test_render_template(template_service):
    """Test template rendering with data"""
    tpl = Template("Hello {{ test }}")
    template_service.get_template = MagicMock(return_value=tpl)

    data = {"test": "there, you sexy tester"}
    result = template_service.render_template("test", data)
    assert result == "Hello there, you sexy tester"
