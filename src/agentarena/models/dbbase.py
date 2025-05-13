from typing import List
from typing import Optional
from typing import Tuple

from pydantic import BaseModel
from pydantic import Field

from .validation import ValidationResponse


class DbBase(BaseModel):
    """
    Base model for DB-persisted objects
    """

    id: str = Field(default=None, description="Unique identifier")
    active: bool = Field(default=True, description="Is the object active?")
    created_at: Optional[int] = Field(default=0, description="Creation timestamp")
    updated_at: Optional[int] = Field(default=0, description="Creation timestamp")
    deleted_at: Optional[int] = Field(default=0, description="Deletion timestamp")

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        return []

    def validateDTO(self) -> ValidationResponse:
        """
        Validate the model. To be overridden by validating models

        Returns:
            ValidationResponse: The validation response.
        """
        return ValidationResponse(
            success=True,
            message="Validation successful.",
            data={},
        )
