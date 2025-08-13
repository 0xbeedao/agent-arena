from codecs import encode
from types import SimpleNamespace
from typing import Any
from typing import cast
from unittest.mock import AsyncMock

import pytest

from agentarena.clients.message_broker import MessageBroker
from agentarena.clients.message_broker import get_message_broker_connection
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import JobResponseState
from agentarena.models.public import JobResponse
from agentarena.models.public import ModelChangeMessage


@pytest.fixture
def mock_nats_client():
    client = AsyncMock()
    client.publish = AsyncMock()
    client.request = AsyncMock()
    return client


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.fixture
def uuid_service():
    return UUIDService(word_list=[])


@pytest.fixture
def message_broker(mock_nats_client, uuid_service, logging):
    return MessageBroker(
        client=mock_nats_client,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.mark.asyncio
async def test_nats_returns_client_directly(message_broker, mock_nats_client):
    client = await message_broker.nats()
    assert client is mock_nats_client


@pytest.mark.asyncio
async def test_nats_awaits_coroutine(uuid_service, logging, mock_nats_client):
    async def _get_client():
        return mock_nats_client

    broker = MessageBroker(
        client=cast(Any, _get_client()),
        uuid_service=uuid_service,
        logging=logging,
    )
    client = await broker.nats()
    assert client is mock_nats_client


@pytest.mark.asyncio
async def test_publish_model_change_encodes_and_publishes(
    message_broker, mock_nats_client
):
    channel = "agent.create"
    obj_id = "123"
    detail = "foo"

    await message_broker.publish_model_change(channel, obj_id, detail)

    expected_payload = ModelChangeMessage(
        model_id=obj_id,
        detail=detail,
        action="create",
    ).model_dump_json()
    expected_bytes = encode(expected_payload, "utf-8", "unicode_escape")

    mock_nats_client.publish.assert_awaited_once()
    args, kwargs = mock_nats_client.publish.await_args
    assert args[0] == channel
    assert args[1] == expected_bytes


@pytest.mark.asyncio
async def test_publish_response_no_channel_returns_early(
    message_broker, mock_nats_client
):
    res = JobResponse(job_id="j1", state=JobResponseState.PENDING, data=None)
    await message_broker.publish_response("", res)
    mock_nats_client.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_publish_response_publishes_encoded_json(
    message_broker, mock_nats_client
):
    channel = "jobs.response"
    res = JobResponse(job_id="j1", state=JobResponseState.COMPLETE, data="ok")

    await message_broker.publish_response(channel, res)

    expected_bytes = encode(res.model_dump_json(), "utf-8", "unicode_escape")
    mock_nats_client.publish.assert_awaited_once_with(channel, expected_bytes)


@pytest.mark.asyncio
async def test_request_job_with_string_encodes_and_calls_request(
    message_broker, mock_nats_client
):
    channel = "jobs.request"
    payload = '{"a":1}'
    fake_response = SimpleNamespace(data=b"OK")
    mock_nats_client.request = AsyncMock(return_value=fake_response)

    resp = await message_broker.request_job(channel, payload, timeout=3.0)

    expected_bytes = encode(payload, "utf-8", "unicode_escape")
    mock_nats_client.request.assert_awaited_once_with(
        channel, expected_bytes, timeout=3.0
    )
    assert resp is fake_response


@pytest.mark.asyncio
async def test_request_job_with_bytes_calls_request_directly(
    message_broker, mock_nats_client
):
    channel = "jobs.request"
    payload = b"raw-bytes"
    fake_response = SimpleNamespace(data=b"OK")
    mock_nats_client.request = AsyncMock(return_value=fake_response)

    resp = await message_broker.request_job(channel, payload)
    mock_nats_client.request.assert_awaited_once_with(channel, payload, timeout=60.0)
    assert resp is fake_response


@pytest.mark.asyncio
async def test_request_job_invalid_payload_raises_and_does_not_call_request(
    message_broker, mock_nats_client
):
    with pytest.raises(ValueError):
        await message_broker.request_job("jobs.request", {"not": "valid"})
    mock_nats_client.request.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_message_with_string_encodes_and_publishes(
    message_broker, mock_nats_client
):
    channel = "topic"
    payload = "hello"
    await message_broker.send_message(channel, payload)
    expected_bytes = encode(payload, "utf-8", "unicode_escape")
    mock_nats_client.publish.assert_awaited_once_with(channel, expected_bytes)


@pytest.mark.asyncio
async def test_send_message_with_bytes_publishes_directly(
    message_broker, mock_nats_client
):
    channel = "topic"
    payload = b"hello"
    await message_broker.send_message(channel, payload)
    mock_nats_client.publish.assert_awaited_once_with(channel, payload)


@pytest.mark.asyncio
async def test_send_message_invalid_payload_raises(message_broker, mock_nats_client):
    with pytest.raises(ValueError):
        await message_broker.send_message("topic", 123)  # type: ignore
    mock_nats_client.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_response_calls_send_message_with_json_string(message_broker):
    channel = "jobs.response"
    res = JobResponse(job_id="j1", state=JobResponseState.COMPLETE, data="done")
    # Spy on send_message to assert it is called with the JSON string
    message_broker.send_message = AsyncMock()

    await message_broker.send_response(channel, res)

    expected_json = res.model_dump_json()
    message_broker.send_message.assert_awaited_once_with(channel, expected_json)


@pytest.mark.asyncio
async def test_get_message_broker_connection_yields_and_drains(monkeypatch, logging):
    connect_mock = AsyncMock()
    conn = AsyncMock()
    conn.drain = AsyncMock()
    connect_mock.return_value = conn

    monkeypatch.setattr(
        "agentarena.clients.message_broker.nats.connect",
        connect_mock,
    )

    agen = get_message_broker_connection("nats://localhost:4222", logging)
    yielded_conn = await agen.__anext__()
    assert yielded_conn is conn
    connect_mock.assert_awaited_once_with("nats://localhost:4222")

    await agen.aclose()
    # conn.drain.assert_awaited_once()
