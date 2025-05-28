"""API Clients for Control Panel."""

from typing import Any
from typing import Dict

import httpx


class BaseClient:
    """Base API client class."""

    def __init__(self, config={}):
        self.base_url = config["url"]
        self.config = config

    async def get(self, endpoint: str) -> Dict[str, Any]:
        """GET request to API endpoint."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            return response.json()

    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request to API endpoint."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()

    async def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PUT request to API endpoint."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.put(endpoint, json=data)
            response.raise_for_status()
            return response.json()

    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE request to API endpoint."""
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            response = await client.delete(endpoint)
            response.raise_for_status()
            return response.json()


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


class ActorClient(BaseClient):
    """Client for Actor API."""

    pass


class MessageBrokerClient:
    """Client for Messages"""

    def __init__(self, config={}):
        self.config = config
