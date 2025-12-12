from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.database import engine, Base
from app.routers import health, school, student, invoice, payment, payment_allocation


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(
    title="School Management API",
    description="API for managing schools, students, invoices, and payments",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(school.router)
app.include_router(student.router)
app.include_router(invoice.router)
app.include_router(payment.router)
app.include_router(payment_allocation.router)
