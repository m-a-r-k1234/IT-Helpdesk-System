from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.user import User
from app.core.dependencies import require_role
from app.models.ticket import Ticket

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


class RoleUpdate(BaseModel):
    role: str


class StatusUpdate(BaseModel):
    is_active: bool


# =========================
# Get All Users
# =========================

@router.get("/")
def get_all_users(
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):
    users = (
        db.query(User)
        .order_by(User.id.asc())
        .all()
    )

    return users

@router.get("/analysts/workload")
def get_analyst_workload(
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):
    analysts = (
        db.query(User)
        .filter(User.role == "analyst")
        .order_by(User.id.asc())
        .all()
    )

    results = []

    for analyst in analysts:
        total = (
            db.query(Ticket)
            .filter(Ticket.assigned_to == analyst.id)
            .count()
        )

        open_tickets = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_to == analyst.id,
                Ticket.status == "OPEN"
            )
            .count()
        )

        in_progress = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_to == analyst.id,
                Ticket.status == "IN_PROGRESS"
            )
            .count()
        )

        waiting_for_user = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_to == analyst.id,
                Ticket.status == "WAITING_FOR_USER"
            )
            .count()
        )

        resolved = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_to == analyst.id,
                Ticket.status == "RESOLVED"
            )
            .count()
        )

        closed = (
            db.query(Ticket)
            .filter(
                Ticket.assigned_to == analyst.id,
                Ticket.status == "CLOSED"
            )
            .count()
        )

        results.append({
            "user_id": analyst.id,
            "name": f"{analyst.first_name} {analyst.last_name}",
            "email": analyst.email,
            "total_assigned": total,
            "open": open_tickets,
            "in_progress": in_progress,
            "waiting_for_user": waiting_for_user,
            "resolved": resolved,
            "closed": closed
        })

    return results

@router.get("/{user_id}")
def get_user(
    user_id: int,
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user

@router.get("/{user_id}/tickets")
def get_user_tickets(
    user_id: int,
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    tickets = (
        db.query(Ticket)
        .filter(Ticket.assigned_to == user_id)
        .order_by(Ticket.created_at.desc())
        .all()
    )

    return {
        "user_id": user.id,
        "user_name": f"{user.first_name} {user.last_name}",
        "role": user.role,
        "ticket_count": len(tickets),
        "tickets": tickets
    }

@router.get("/{user_id}/ticket-stats")
def get_user_ticket_stats(
    user_id: int,
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    total = (
        db.query(Ticket)
        .filter(Ticket.assigned_to == user_id)
        .count()
    )

    open_tickets = (
        db.query(Ticket)
        .filter(
            Ticket.assigned_to == user_id,
            Ticket.status == "OPEN"
        )
        .count()
    )

    in_progress = (
        db.query(Ticket)
        .filter(
            Ticket.assigned_to == user_id,
            Ticket.status == "IN_PROGRESS"
        )
        .count()
    )

    waiting_for_user = (
        db.query(Ticket)
        .filter(
            Ticket.assigned_to == user_id,
            Ticket.status == "WAITING_FOR_USER"
        )
        .count()
    )

    resolved = (
        db.query(Ticket)
        .filter(
            Ticket.assigned_to == user_id,
            Ticket.status == "RESOLVED"
        )
        .count()
    )

    closed = (
        db.query(Ticket)
        .filter(
            Ticket.assigned_to == user_id,
            Ticket.status == "CLOSED"
        )
        .count()
    )

    return {
        "user_id": user.id,
        "user_name": f"{user.first_name} {user.last_name}",
        "role": user.role,
        "total_assigned": total,
        "open": open_tickets,
        "in_progress": in_progress,
        "waiting_for_user": waiting_for_user,
        "resolved": resolved,
        "closed": closed
    }


# =========================
# Change User Role
# =========================

@router.patch("/{user_id}/role")
def update_user_role(
    user_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    allowed_roles = [
        "employee",
        "analyst",
        "admin"
    ]

    if role_data.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )

    user.role = role_data.role

    db.commit()
    db.refresh(user)

    return {
        "message": "User role updated successfully",
        "user_id": user.id,
        "role": user.role
    }


# =========================
# Activate / Deactivate User
# =========================

@router.patch("/{user_id}/status")
def update_user_status(
    user_id: int,
    status_data: StatusUpdate,
    current_user: User = Depends(
        require_role("admin")
    ),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own account status"
        )

    user.is_active = status_data.is_active

    db.commit()
    db.refresh(user)

    return {
        "message": "User status updated successfully",
        "user_id": user.id,
        "is_active": user.is_active
    }