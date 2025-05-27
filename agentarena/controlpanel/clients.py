"""API Clients for Control Panel."""

from typing import Any
from typing import Dict

import httpx


class BaseClient:
    """Base API client class."""

    def __init__(self, config={}):
        self.base_url = config["url"]
        self.client = httpx.Client(base_url=self.base_url)
        self.config = config

    def get(self, endpoint: str) -> Dict[str, Any]:
        """GET request to API endpoint."""
        response = self.client.get(endpoint)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request to API endpoint."""
        response = self.client.post(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    def put(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """PUT request to API endpoint."""
        response = self.client.put(endpoint, json=data)
        response.raise_for_status()
        return response.json()

    def delete(self, endpoint: str) -> Dict[str, Any]:
        """DELETE request to API endpoint."""
        response = self.client.delete(endpoint)
        response.raise_for_status()
        return response.json()


class ArenaClient(BaseClient):
    """Client for Arena API."""

    # Arena-specific methods will be added here


class SchedulerClient(BaseClient):
    """Client for Scheduler API."""

    # Scheduler-specific methods will be added here


class ActorClient(BaseClient):
    """Client for Actor API."""

    # Actor-specific methods will be added here


class MessageBrokerClient:
    """Client for Messages"""

    def __init__(self, config={}):
        self.config = config
