from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.database import Base, engine
from app.models import User, Category, Ticket, Comment, TicketHistory
from app.routers.auth import router as auth_router
from app.core.dependencies import (
    get_current_user,
    require_role
)
from app.models.user import User
from app.routers.tickets import router as tickets_router
from app.routers.users import router as users_router
from app.routers.categories import router as categories_router
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="IT Help Desk System",
    description="Backend API for an IT Help Desk System",
    version="1.0.0"
)

WEB_DIR = Path(__file__).parent / "web"
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(users_router)
app.include_router(categories_router)

@app.get("/")
def root():
    return FileResponse(WEB_DIR / "index.html")

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


