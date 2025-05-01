from datetime import datetime
from typing import Optional,  List, Tuple
from pydantic import BaseModel, Field
from .validation import ValidationResponse

class DbBase(BaseModel):
    """
    Base model for DB-persisted objects
    """

    id: str = Field(default=None, description="Unique identifier (ULID)")
    active: bool = Field(default=True, description="Is the object active?")
    created_at: datetime = Field(default=None, description="Creation timestamp")
    updated_at: datetime = Field(default=None, description="Creation timestamp")
    deleted_at: Optional[datetime] = Field(default=None, description="Deletion timestamp")

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        return []
    
    def validateDTO(self) -> ValidationResponse:
        """
        Validate the model.
                    
        Returns:
            ValidationResponse: The validation response.
        """
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
        
    
