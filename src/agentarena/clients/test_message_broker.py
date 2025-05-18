from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.job import CommandJobBatchRequest
from agentarena.models.job import CommandJobRequest
from agentarena.models.job import JobState
from agentarena.models.job import UrlJobRequest
from agentarena.core.services.uuid_service import UUIDService


@pytest.fixture
def mock_nats_client():
    client = AsyncMock()
    client.publish = AsyncMock()
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
async def test_send_job(message_broker, mock_nats_client):
    test_job = CommandJobRequest(
        id="test",
        channel="test.command",
        data={"key": "value"},
        method="POST",
        priority=1,
        send_at=int(datetime.now().timestamp()),
        state=JobState.IDLE.value,
        url="",
    )

    await message_broker.send_job(test_job)

    expected = (
        '{"id":"test","parent_id":null,"channel":"test.command","data":{"key":"value"},"method":"POST","priority":1,"send_at":'
        + str(test_job.send_at)
        + ',"state":"idle","url":""}'
    )
    mock_nats_client.publish.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_job_with_prefix(message_broker, mock_nats_client):
    message_broker.prefix = "custom"
    send_at = int(datetime.now().timestamp())
    test_job = CommandJobRequest(
        id="test",
        channel="test.command",
        data={"key": "value"},
        method="POST",
        priority=1,
        send_at=send_at,
        state=JobState.IDLE.value,
        url="",
    )

    await message_broker.send_job(test_job)
    expected = (
        '{"id":"test","parent_id":null,"channel":"custom.test.command","data":{"key":"value"},"method":"POST","priority":1,"send_at":'
        + str(test_job.send_at)
        + ',"state":"idle","url":""}'
    )

    mock_nats_client.publish.assert_awaited_once_with(
        "custom.test.command", expected.encode("utf-8")
    )


@pytest.mark.asyncio
async def test_send_batch(message_broker, mock_nats_client):
    parent_job = CommandJobRequest(
        channel="parent.command",
        data={"parent": "data"},
        method="POST",
        priority=2,
        send_at=int(datetime.now().timestamp()),
        state=JobState.IDLE.value,
        id="",
        url="",
    )

    child_request = UrlJobRequest(
        command="child.command",
        data={"child": "data"},
        method="GET",
        delay=0,
        url="http://example.com",
    )

    batch_request = CommandJobBatchRequest(
        batch=parent_job,
        children=[child_request],
    )

    await message_broker.send_batch(batch_request)

    assert mock_nats_client.publish.await_count == 2


def test_make_child():
    parent_job = CommandJobRequest(
        id="parent-id",
        channel="parent.command",
        data={"parent": "data"},
        method="POST",
        priority=2,
        send_at=int(datetime.now().timestamp()),
        state=JobState.IDLE.value,
        url="",
    )

    child_request = UrlJobRequest(
        command="child.command",
        data={"child": "data"},
        method="GET",
        delay=10,
        url="http://example.com",
    )

    child_job = parent_job.make_child(child_request)

    assert child_job.parent_id == "parent-id"
    assert child_job.channel == "child.command"
    assert child_job.data == {"child": "data"}
    assert child_job.method == "GET"
    assert child_job.priority == 1  # parent.priority - 1
    assert child_job.send_at == parent_job.send_at + 10
    assert child_job.state == JobState.IDLE.value
    assert child_job.url == "http://example.com"
