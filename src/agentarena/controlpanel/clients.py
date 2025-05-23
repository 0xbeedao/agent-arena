"""API Clients for Control Panel."""

import httpx
from typing import Dict, Any, Optional
import typer


class BaseClient:
    """Base API client class."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(base_url=base_url)

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

    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(f"{base_url}/arena")

    # Arena-specific methods will be added here


class SchedulerClient(BaseClient):
    """Client for Scheduler API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(f"{base_url}/scheduler")

    # Scheduler-specific methods will be added here


class ActorClient(BaseClient):
    """Client for Actor API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(f"{base_url}/actor")

    # Actor-specific methods will be added here
