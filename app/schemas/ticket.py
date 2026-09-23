from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class TicketCreate(BaseModel):
    title: str = Field(
        min_length=5,
        max_length=255
    )
    description: str = Field(
        min_length=10
    )
    priority: str = Field(
        default="MEDIUM"
    )
    category_id: int


class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    priority: str
    created_by: int
    assigned_to: int | None
    category_id: int
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

class TicketUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None