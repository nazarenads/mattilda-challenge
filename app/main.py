import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.database import engine, Base, SessionLocal
from app.logging_config import setup_logging, get_logger
from app.routers import health, school, student, invoice, payment, payment_allocation, auth, user
from app.schemas import UserCreate
from app.services import user as user_service

logger = get_logger(__name__)


def create_admin_user_if_not_exists():
    """Create admin user from environment variables if it doesn't exist."""
    # Skip admin creation during tests
    if os.environ.get("TESTING") == "true":
        return
    
    db = SessionLocal()
    try:
        existing_admin = user_service.get_user_by_email(db, settings.admin_email)
        if not existing_admin:
            admin_data = UserCreate(
                email=settings.admin_email,
                password=settings.admin_password,
                school_id=None,
                is_admin=True,
            )
            user_service.create_user(db, admin_data)
            logger.info("Admin user created: %s", settings.admin_email)
        else:
            logger.info("Admin user already exists: %s", settings.admin_email)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    Base.metadata.create_all(bind=engine)
    create_admin_user_if_not_exists()
    yield
    engine.dispose()


app = FastAPI(
    title="School Management API",
    description="API for managing schools, students, invoices, and payments",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://v0-school-finance-application.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(school.router)
app.include_router(student.router)
app.include_router(invoice.router)
app.include_router(payment.router)
app.include_router(payment_allocation.router)
app.include_router(user.router)
