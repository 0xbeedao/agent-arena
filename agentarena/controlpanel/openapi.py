"""OpenAPI Specification Parser for Control Panel."""

import json
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


class OpenAPIParser:
    """Parse OpenAPI specs from FastAPI servers."""

    def __init__(self):
        self.specs: Dict[str, Dict[str, Any]] = {
            "arena": {},
            "scheduler": {},
            "actor": {},
        }

    def load_from_file(self, server: str, path: Path) -> None:
        """Load OpenAPI spec from JSON file."""
        with open(path) as f:
            self.specs[server] = json.load(f)

    def load_from_url(self, server: str, url: str) -> None:
        """Load OpenAPI spec from URL."""
        # Implementation will use httpx to fetch from /openapi.json

    def get_endpoints(self, server: str) -> List[Dict[str, Any]]:
        """Get all endpoints for a server."""
        paths = self.specs[server].get("paths", {})
        return [
            {
                "path": path,
                "methods": list(methods.keys()),
                "description": methods.get("description", ""),
            }
            for path, methods in paths.items()
        ]

    def get_schema(self, server: str, model_name: str) -> Optional[Dict[str, Any]]:
        """Get schema definition for a model."""
        return (
            self.specs[server].get("components", {}).get("schemas", {}).get(model_name)
        )
