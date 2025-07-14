import asyncio

import pytest
from nats.aio.client import Client as NATS
from testcontainers.core.container import DockerContainer


@pytest.fixture(scope="module")
def nats_container():
    nats = DockerContainer("nats:latest").with_exposed_ports(4222)
    nats.start()
    yield nats
    nats.stop()


@pytest.fixture
def nats_client(nats_container):
    async def _get_client():
        nc = NATS()
        port = nats_container.get_exposed_port(4222)
        await nc.connect(servers=[f"nats://localhost:{port}"])
        return nc

    return _get_client()


@pytest.mark.asyncio
async def test_nats_integration(nats_client):
    # Use a future to capture the received message
    received_msg = asyncio.Future()

    async def message_handler(msg):
        received_msg.set_result(msg)

    # Get the NATS client
    client = await nats_client

    # Subscribe with a callback
    await client.subscribe("test.subject", cb=message_handler)

    # Publish a message
    await client.publish("test.subject", b"hello")

    # Wait for the message to be received
    msg = await received_msg
    assert msg.data == b"hello"

    # Clean up
    await client.close()


@pytest.mark.asyncio
async def test_nats_integration_with_request(nats_client):
    # Use a future to capture the received message

    client = await nats_client

    async def message_responder(msg):
        await client.publish(msg.reply, b"OK")

    sub = await client.subscribe("test.subject", cb=message_responder)

    response = await client.request("test.subject", b"hello")
    assert response.data == b"OK"

    await sub.unsubscribe()
    await client.close()
