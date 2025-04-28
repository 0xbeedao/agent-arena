from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class DbBase(BaseModel):
    """
    Base model for DB-persisted objects
    """

    id: str = Field(default=None, description="Unique identifier (ULID)")
    active: bool = Field(default=True, description="Is the object active?")
    created_at: datetime = Field(default=None, description="Creation timestamp")
    updated_at: datetime = Field(default=None, description="Creation timestamp")
    deleted_at: Optional[datetime] = Field(default=None, description="Deletion timestamp")

    