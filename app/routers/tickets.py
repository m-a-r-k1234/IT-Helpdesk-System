from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import SessionLocal
from app.models.ticket import Ticket
from app.models.user import User
from app.models.category import Category
from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketUpdate
)


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED
)
def create_ticket(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    category = (
        db.query(Category)
        .filter(Category.id == ticket_data.category_id)
        .first()
    )

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    new_ticket = Ticket(
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        created_by=current_user.id,
        category_id=ticket_data.category_id
    )

    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    return {
        "message": "Ticket created successfully",
        "ticket_id": new_ticket.id,
        "title": new_ticket.title,
        "status": new_ticket.status,
        "priority": new_ticket.priority,
        "created_by": new_ticket.created_by,
        "category_id": new_ticket.category_id
    }

@router.get(
    "/",
    response_model=list[TicketResponse]
)
def get_my_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.created_by == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return tickets

@router.patch(
    "/{ticket_id}",
    response_model=TicketResponse
)
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Only the person who created the ticket can update it
    if ticket.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own tickets"
        )

    # Do not allow changes to closed tickets
    if ticket.status == "CLOSED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Closed tickets cannot be updated"
        )

    if ticket_data.status is not None:
        ticket.status = ticket_data.status

    if ticket_data.priority is not None:
        ticket.priority = ticket_data.priority

    db.commit()
    db.refresh(ticket)

    return ticket