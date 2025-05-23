from sqlmodel import Field
from sqlmodel import SQLModel


class AuditMessage(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    created_at: int = Field()
    message: str = Field()
