from pydantic import BaseModel, Field

class ValidationResponse(BaseModel):
    """
    Validation response model for the Agent Arena application.
    
    This model is used to validate models.
    """
    valid: bool = Field(description="Is the data valid?")
    message: str = Field(description="Validation message")
    data: dict = Field(default_factory=dict, description="Additional data related to validation")

