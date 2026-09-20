from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category
    from app.models.comment import Comment
    from app.models.ticket_history import TicketHistory

class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="OPEN",
        nullable=False
    )

    priority: Mapped[str] = mapped_column(
        String(50),
        default="MEDIUM",
        nullable=False
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    assigned_to: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True
    )

    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_tickets"
)

    assignee: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[assigned_to],
        back_populates="assigned_tickets"
)

    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="tickets"
)

    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="ticket"
)

    history: Mapped[list["TicketHistory"]] = relationship(
        "TicketHistory",
        back_populates="ticket"
)