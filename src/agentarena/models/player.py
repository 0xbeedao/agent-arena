"""
Player models for the Agent Arena application.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ulid import ULID

class PlayerState(BaseModel):
    """
    Represents the state of a player.
    
    Maps to the PLAYER_STATE entity in the ER diagram.
    """
    agent_id: ULID = Field(description="Agent identifier")
    position: str = Field(description="Grid coordinate as 'x,y'", pattern=r"^-?\d+,-?\d+$")
    inventory: Optional[List[str]] = Field(default=None, description="Player inventory")
    health_state: str = Field(description="Health state")
    custom_state: Optional[Dict[str, Any]] = Field(default=None, description="Custom state data")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Creation timestamp")


class PlayerAction(BaseModel):
    """
    Represents an action taken by a player.
    
    Maps to the PLAYER_ACTION entity in the ER diagram.
    """
    agent_id: ULID = Field(description="Agent identifier")
    action: str = Field(description="Action description")
    target: Optional[str] = Field(
        default=None, 
        description="Target coordinate as 'x,y'",
        pattern=r"^-?\d+,-?\d+$"
    )