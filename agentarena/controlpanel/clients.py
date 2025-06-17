"""API Clients for Control Panel."""

from typing import Any
from typing import Dict

import httpx
import nats
from nats.aio.client import Client as NatsClient


class BaseClient:
    """Base API client class."""

    def __init__(self, config={}):
        self.base_url = config["url"]
        self.config = config

    async def get(self, endpoint: str) -> httpx.Response:
        """GET request to API endpoint."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            return response

    async def post(self, endpoint: str, data: Dict[str, Any]) -> httpx.Response:
        """POST request to API endpoint."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(endpoint, json=data)
            response.raise_for_status()
            return response

    async def put(self, endpoint: str, data: Dict[str, Any]) -> httpx.Response:
        """PUT request to API endpoint."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(endpoint, json=data)
            response.raise_for_status()
            return response

    async def delete(self, endpoint: str) -> httpx.Response:
        """DELETE request to API endpoint."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.delete(endpoint)
            response.raise_for_status()
            return response


class ArenaClient(BaseClient):
    """Client for Arena API."""

    async def get_participants(self) -> Dict[str, Any]:
        """Get list of all participants."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get("/api/participant")
            response.raise_for_status()
            return response.json()


class SchedulerClient(BaseClient):
    """Client for Scheduler API."""

    # Scheduler-specific methods will be added here


class ParticipantClient(BaseClient):
    """Client for Participant API."""


class StrategyClient(BaseClient):
    """Client for Strategy API."""


class MessageBrokerClient:
    """Client for Messages"""

    def __init__(self, config={}):
        self.config = config
        self.client: NatsClient | None = None

    async def subscribe(self, subject: str, callback):
        client = await self.get_client()
        return await client.subscribe(subject, cb=callback)

    async def get_client(self) -> NatsClient:
        if self.client is None:
            self.client = await nats.connect(self.config["url"])
        return self.client
