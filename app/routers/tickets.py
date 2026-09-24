from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_user,
    require_role
)
from app.database import SessionLocal
from app.models.ticket import Ticket
from app.models.user import User
from app.models.category import Category
from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketUpdate,
    TicketAssign,
    CommentCreate,
    CommentResponse
)
from app.models.comment import Comment
from app.models.ticket_history import TicketHistory
router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


# =========================
# Database Dependency
# =========================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

def create_ticket_history(
    db: Session,
    ticket_id: int,
    user_id: int,
    action: str,
    old_value: str | None = None,
    new_value: str | None = None
):
    history = TicketHistory(
        ticket_id=ticket_id,
        user_id=user_id,
        action=action,
        old_value=old_value,
        new_value=new_value
    )

    db.add(history)

# =========================
# Status Workflow
# =========================

ALLOWED_STATUS_TRANSITIONS = {
    "OPEN": ["IN_PROGRESS"],
    "IN_PROGRESS": [
        "WAITING_FOR_USER",
        "RESOLVED"
    ],
    "WAITING_FOR_USER": [
        "IN_PROGRESS"
    ],
    "RESOLVED": [
        "CLOSED",
        "IN_PROGRESS"
    ],
    "CLOSED": []
}


# =========================
# Create Ticket
# =========================

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


# =========================
# Get My Tickets
# =========================

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


# =========================
# Update Ticket
# =========================

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

    # Only the ticket creator can update their ticket
    if ticket.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own tickets"
        )

    # Closed tickets cannot be updated
    if ticket.status == "CLOSED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Closed tickets cannot be updated"
        )

    # Update status
    if ticket_data.status is not None:

        allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(
            ticket.status,
            []
        )

        if ticket_data.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot change status from "
                    f"{ticket.status} to "
                    f"{ticket_data.status}"
                )
            )

        old_status = ticket.status

        ticket.status = ticket_data.status

        create_ticket_history(
            db=db,
            ticket_id=ticket.id,
            user_id=current_user.id,
            action="STATUS_CHANGED",
            old_value=old_status,
            new_value=ticket_data.status
        )

    # Update priority
    if ticket_data.priority is not None:
        old_priority = ticket.priority

        ticket.priority = ticket_data.priority

        create_ticket_history(
            db=db,
            ticket_id=ticket.id,
            user_id=current_user.id,
            action="PRIORITY_CHANGED",
            old_value=old_priority,
            new_value=ticket_data.priority
        )

    db.commit()
    db.refresh(ticket)

    return ticket


# =========================
# Assign Ticket
# =========================

@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse
)
def assign_ticket(
    ticket_id: int,
    assignment: TicketAssign,
    current_user: User = Depends(
        require_role("analyst", "admin")
    ),
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

    analyst = (
        db.query(User)
        .filter(User.id == assignment.assigned_to)
        .first()
    )

    if not analyst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned user not found"
        )

    if analyst.role not in ["analyst", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Ticket can only be assigned "
                "to an analyst or admin"
            )
        )

    old_assignee = ticket.assigned_to

    ticket.assigned_to = analyst.id

    create_ticket_history(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id,
        action="TICKET_ASSIGNED",
        old_value=(
            str(old_assignee)
            if old_assignee is not None
            else None
        ),
        new_value=str(analyst.id)
    )



    db.commit()
    db.refresh(ticket)

    return ticket

@router.post(
    "/{ticket_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_comment(
    ticket_id: int,
    comment_data: CommentCreate,
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

    # Only users involved with the ticket can comment
    if (
        ticket.created_by != current_user.id
        and ticket.assigned_to != current_user.id
        and current_user.role not in ["admin"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to comment on this ticket"
        )

    new_comment = Comment(
        ticket_id=ticket.id,
        user_id=current_user.id,
        message=comment_data.message
    )

    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)

    return new_comment

@router.get(
    "/{ticket_id}/comments",
    response_model=list[CommentResponse]
)
def get_comments(
    ticket_id: int,
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

    if (
        ticket.created_by != current_user.id
        and ticket.assigned_to != current_user.id
        and current_user.role not in ["admin"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view these comments"
        )

    comments = (
        db.query(Comment)
        .filter(Comment.ticket_id == ticket_id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    return comments

@router.get(
    "/{ticket_id}/history"
)
def get_ticket_history(
    ticket_id: int,
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

    if (
        ticket.created_by != current_user.id
        and ticket.assigned_to != current_user.id
        and current_user.role not in ["admin"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this history"
        )

    history = (
        db.query(TicketHistory)
        .filter(TicketHistory.ticket_id == ticket_id)
        .order_by(TicketHistory.created_at.asc())
        .all()
    )

    return history