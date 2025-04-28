from datetime import datetime
from pydantic import BaseModel, Field

class DbBase(BaseModel):
    """
    Base model for DB-persisted objects
    """

    id: str = Field(default=None, description="Unique identifier (ULID)")
    created_at: datetime = Field(default=None, description="Creation timestamp")
    updated_at: datetime = Field(default=None, description="Creation timestamp")

    