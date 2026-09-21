from fastapi import FastAPI, Depends

from app.database import Base, engine
from app.models import User, Category, Ticket, Comment, TicketHistory
from app.routers.auth import router as auth_router
from app.core.dependencies import get_current_user
from app.models.user import User

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="IT Help Desk System",
    description="Backend API for an IT Help Desk System",
    version="1.0.0"
)


app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "message": "IT Help Desk API is running"
    }

@app.get("/me")
def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "email": current_user.email,
        "role": current_user.role
    }