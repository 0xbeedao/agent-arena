"""
Player models for the Agent Arena application.
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from sqlmodel import Field

from .dbbase import DbBase


class PlayerStateDTO(DbBase, table=True):
    """
    Represents the state of a player.

    Maps to the PLAYER_STATE entity in the ER diagram.
    """

    agent_id: str = Field(description="Agent identifier")
    position: str = Field(
        description="Grid coordinate as 'x,y'", pattern=r"^-?\d+,-?\d+$"
    )
    inventory: Optional[List[str]] = Field(default=None, description="Player inventory")
    health_state: str = Field(description="Health state")
    custom_state: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom state data"
    )

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [("agent_id", "agents", "id")]


class PlayerAction(DbBase, table=True):
    """
    Represents an action taken by a player.

    Maps to the PLAYER_ACTION entity in the ER diagram.
    """

    agent_id: str = Field(description="Agent identifier")
    action: str = Field(description="Action description")
    target: Optional[str] = Field(
        default=None, description="Target coordinate as 'x,y'", pattern=r"^-?\d+,-?\d+$"
    )

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [("agent_id", "agents", "id")]
