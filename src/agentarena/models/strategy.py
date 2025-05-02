"""
Strategy model for the Agent Arena application.
"""

from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field
from .dbmodel import DbBase
from .validation import ValidationResponse

class StrategyType(str, Enum):
    """
    Enum for different strategy types.
    """
    JUDGE = "judge"
    ARENA = "arena"
    PLAYER = "player"

class StrategyDTO(DbBase):
    """
    Represents a strategy that can be used by an agent.
    
    Maps to the STRATEGY entity in the ER diagram.
    """
    name: Optional[str] = Field(default="", description="Strategy name")
    personality: Optional[str] = Field(default="", description="Personality description")
    instructions: Optional[str] = Field(default="", description="Strategy instructions")
    description: Optional[str] = Field(default="", description="Detailed description of the strategy")
    group: str = Field(default=StrategyType.PLAYER.value, description="Type of strategy")

    def validateDTO(self) -> ValidationResponse:
        """
        Validate the strategy model.
        
        Args:
            strategy: The strategy model to validate.
            
        Returns:
            ValidationResponse: The validation response.
        """
        upstream = super().validateDTO()
        messages = []

        if not upstream.success:
            # If the upstream validation fails, we need to collect the messages
            messages.extend(upstream.data.get("messages", []))
        
        if not self.name:
            messages.append("Strategy name is required.")
        
        if not self.instructions:
            messages.append("Instructions are required.")
        
        if not self.group in [StrategyType.JUDGE, StrategyType.ARENA, StrategyType.PLAYER]:
            messages.append("Group must be one of 'judge', 'arena', or 'player'.")
        
        if messages or not upstream.success:
            return ValidationResponse(
                success=False,
                message="Validation failed.",
                data={"messages": messages}
            )
        
        return ValidationResponse(
            success=True, 
            message="Validation successful.", 
            data={}
        )
    
class Strategy(BaseModel):
    """
    Strategy model for the Agent Arena application.
    """
    id: str = Field(description="Unique identifier (ULID)")
    name: str = Field(description="Strategy name")
    personality: str = Field(description="Personality description")
    instructions: str = Field(description="Strategy instructions")
    description: str = Field(description="Detailed description of the strategy")
    group: StrategyType = Field(default=StrategyType.PLAYER, description="Type of strategy")


    @staticmethod
    def from_dto(dto: StrategyDTO):
        """
        Convert the DTO to a Strategy model.
        
        Returns:
            Strategy: The converted strategy model.
        """
        return Strategy(
            id=dto.id,
            name=dto.name,
            personality=dto.personality,
            instructions=dto.instructions,
            description=dto.description,
            group=dto.group
        )