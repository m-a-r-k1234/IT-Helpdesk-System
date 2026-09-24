from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

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
    status: Literal[
        "OPEN",
        "IN_PROGRESS",
        "WAITING_FOR_USER",
        "RESOLVED",
        "CLOSED"
    ] | None = None

    priority: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ] | None = None

class TicketAssign(BaseModel):
    assigned_to: int

class CommentCreate(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000
    )

class CommentResponse(BaseModel):
    id: int
    ticket_id: int
    user_id: int
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)