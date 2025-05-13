from typing import List
from pydantic import BaseModel, Field
from agentarena.models.participant import ParticipantRole


class ArenaFeatureRequest(BaseModel):
    name: str
    description: str
    position: str = Field(description="Comma-separated x,y coordinates, e.g., '5,5'")
    # Add other fields from FeatureDTO if they can be set on creation, excluding id, arena_config_id


class ArenaParticipantRequest(BaseModel):
    role: ParticipantRole
    agent_id: str = Field(description="ID of an existing Agent model")
    # Add other fields from ParticipantDTO if they can be set on creation, excluding id, arena_config_id


class ArenaDefinitionRequest(BaseModel):
    name: str
    description: str
    height: int
    width: int
    rules: str
    max_random_features: int
    features: List[ArenaFeatureRequest] = Field(default_factory=list)
    participants: List[ArenaParticipantRequest] = Field(
        default_factory=list
    )  # Changed from 'agents' in user JSON to 'participants' for clarity
