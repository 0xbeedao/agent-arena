from typing import Optional

from pydantic import BaseModel
from pydantic import Field


class ValidationResponse(BaseModel):
    """
    Validation response model for the Agent Arena application.

    This model is used to validate models.
    """

    success: bool = Field(description="Is the data valid?")
    message: str = Field(description="Validation message")
    data: str = Field(description="Additional data related to validation")


class ModelResponse(BaseModel):
    """
    Response model for creating a new instance.

    This model is used to return the ID of the created instance.
    """

    success: bool = Field(description="Is the operation successful?")
    id: Optional[str] = Field(default=None, description="ID of the created instance")
    validation: Optional[ValidationResponse] = Field(
        default=None, description="Validation response"
    )
    error: Optional[str] = Field(default=None, description="Error message")
    data: Optional[str] = Field(default=None, description="Data")
