from datetime import datetime
from typing import List
from typing import Optional
from typing import Tuple

from pydantic import BaseModel
from pydantic import Field
from ulid import ULID

from .validation import ValidationResponse


class DbBase(BaseModel):
    """
    Base model for DB-persisted objects
    """

    id: str = Field(default=None, description="Unique identifier (ULID)")
    active: bool = Field(default=True, description="Is the object active?")
    created_at: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Creation timestamp"
    )
    deleted_at: Optional[datetime] = Field(
        default=None, description="Deletion timestamp"
    )

    def fill_defaults(self):
        if self.id is None or self.id.strip() == "":
            self.id = ULID().hex

        if self.created_at is None:
            self.created_at = datetime.now()

        return self

    def touch(self):
        self.fill_defaults()
        self.updated_at = datetime.now()
        return self

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        return []

    def validateDTO(self) -> ValidationResponse:
        """
        Validate the model.

        Returns:
            ValidationResponse: The validation response.
        """
        self.fill_defaults()
        return ValidationResponse(
            success=True,
            message="Validation successful.",
            data={},
        )

    @staticmethod
    def validate_list(obj_list: List[BaseModel]) -> List[ValidationResponse]:
        """
        Validate a list of models.

        Args:
            obj_list: The list of models to validate.

        Returns:
            ValidationResponse: The validation response for errors.
        """
        messages = []
        for obj in obj_list:
            validation = obj.validateDTO()
            if not validation.success:
                messages.extend(validation)

        return messages
