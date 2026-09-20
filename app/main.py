from fastapi import FastAPI

from app.database import Base, engine
from app.models import User, Category, Ticket, Comment, TicketHistory
from app.routers.auth import router as auth_router


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