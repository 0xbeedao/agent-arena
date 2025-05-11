from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from pydantic import BaseModel
from pydantic import Field
from ulid import ULID

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.event import JobEvent
from agentarena.services.event_bus import DbEventBus
from agentarena.services.event_bus import InMemoryEventBus


class DummyEvent(BaseModel):
    name: str = Field(default="test")


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.mark.asyncio
async def test_inmemoryeventbus_publish_triggers_handler(logging):
    bus = InMemoryEventBus(logging=logging)
    handler = AsyncMock()
    k = ULID().hex
    event = DummyEvent(name=k)
    bus.subscribe(k, handler)
    await bus.publish(event)
    handler.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_inmemoryeventbus_no_handler_for_event_type(logging):
    bus = InMemoryEventBus(logging=logging)
    handler = AsyncMock()
    bus.subscribe(str, handler)
    k = ULID().hex
    await bus.publish(DummyEvent(name=k))  # Should not call handler
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_inmemoryeventbus_multiple_handlers(logging):
    bus = InMemoryEventBus(logging=logging)
    handler1 = AsyncMock()
    handler2 = AsyncMock()
    k = ULID().hex
    event = DummyEvent(name=k)
    bus.subscribe(k, handler1)
    bus.subscribe(k, handler2)
    await bus.publish(event)
    handler1.assert_awaited_once_with(event)
    handler2.assert_awaited_once_with(event)


@pytest.mark.asyncio
async def test_inmemoryeventbus_unsubscribe_removes_handler(logging):
    bus = InMemoryEventBus(logging=logging)
    handler = AsyncMock()
    k = ULID().hex
    event = DummyEvent(name=k)

    # Subscribe the handler
    bus.subscribe(k, handler)

    # Unsubscribe the handler
    result = bus.unsubscribe(k, handler)
    assert result is True

    # Verify handler is not called when event is published
    await bus.publish(event)
    handler.assert_not_awaited()


@pytest.mark.asyncio
async def test_inmemoryeventbus_unsubscribe_nonexistent_handler(logging):
    bus = InMemoryEventBus(logging=logging)
    handler1 = AsyncMock()
    handler2 = AsyncMock()

    k = ULID().hex
    # Subscribe only handler1
    bus.subscribe(k, handler1)

    # Try to unsubscribe handler2 which wasn't subscribed
    result = bus.unsubscribe(k, handler2)
    assert result is False

    # Verify handler1 is still subscribed
    event = DummyEvent(name=k)
    await bus.publish(event)
    handler1.assert_awaited_once_with(event)


def test_inmemoryeventbus_unsubscribe_nonexistent_event(logging):
    bus = InMemoryEventBus(logging=logging)
    handler = AsyncMock()

    # Try to unsubscribe from event type that has no handlers
    result = bus.unsubscribe(DummyEvent, handler)
    assert result is False


@pytest.mark.asyncio
async def test_dbeventbus_publish_success_dispatches_and_logs(logging):
    mock_inner = AsyncMock(spec=InMemoryEventBus)
    mock_model_service = Mock()
    # Simulate model_service.create returns (event, response)
    mock_event = Mock(spec=JobEvent)
    mock_event.id = "testid"
    mock_response = Mock()
    mock_response.success = True
    mock_model_service.create.return_value = (mock_event, mock_response)

    bus = DbEventBus(
        model_service=mock_model_service, inner=mock_inner, logging=logging
    )
    await bus.publish(mock_event)
    # Should call inner.publish (not awaited in the SUT, but should have been called)
    mock_inner.publish.assert_called_once_with(mock_event)


@pytest.mark.asyncio
async def test_dbeventbus_publish_failure_logs_warn(logging):
    mock_inner = AsyncMock(spec=InMemoryEventBus)
    mock_model_service = Mock()
    mock_event = Mock(spec=JobEvent)
    mock_response = Mock()
    mock_response.success = False
    mock_model_service.create.return_value = (mock_event, mock_response)

    bus = DbEventBus(
        model_service=mock_model_service, inner=mock_inner, logging=logging
    )
    await bus.publish(mock_event)
    mock_inner.publish.assert_not_called()


def test_dbeventbus_subscribe_delegates_to_inner(logging):
    mock_inner = Mock(spec=InMemoryEventBus)
    handler = Mock()
    bus = DbEventBus(model_service=None, inner=mock_inner, logging=logging)
    k = ULID().hex
    bus.subscribe(k, handler)
    mock_inner.subscribe.assert_called_once_with(k, handler)


def test_dbeventbus_unsubscribe_delegates_to_inner(logging):
    mock_inner = Mock(spec=InMemoryEventBus)
    # Setup mock to return True when unsubscribe is called
    mock_inner.unsubscribe.return_value = True

    handler = Mock()
    bus = DbEventBus(model_service=None, inner=mock_inner, logging=logging)

    # Call unsubscribe and verify it delegates to inner
    k = ULID().hex
    result = bus.unsubscribe(k, handler)
    mock_inner.unsubscribe.assert_called_once_with(k, handler)
    assert result is True
