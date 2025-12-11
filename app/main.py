from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.database import engine, Base
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="API Boilerplate",
    description="A FastAPI boilerplate project",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health.router)
