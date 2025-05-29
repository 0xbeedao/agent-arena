from typing import List
from typing import Optional
from typing import Tuple

from sqlmodel import Field
from sqlmodel import SQLModel

from .validation import ValidationResponse


class DbBase(SQLModel, table=False):
    """
    Base model for DB-persisted objects
    """

    id: str = Field(default=None, description="Unique identifier", primary_key=True)
    created_at: Optional[int] = Field(default=0, description="Creation timestamp")
    updated_at: Optional[int] = Field(default=0, description="Creation timestamp")

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
            data="",
        )
