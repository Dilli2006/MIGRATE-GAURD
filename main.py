"""MIGRATE-GUARD - FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI

from backend.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create and tear down the database connection pool."""
    app.state.pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
    yield
    await app.state.pool.close()


app = FastAPI(
    title="MIGRATE-GUARD",
    description="The Post-Failure Resolution Engine for Database Migrations",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "migrate-guard"}


# Import and include routers
from backend.api.webhooks import router as webhook_router  # noqa: E402
from backend.api.incidents import router as incident_router  # noqa: E402
from backend.api.approvals import router as approval_router  # noqa: E402
from backend.api.notifications import router as notification_router  # noqa: E402

app.include_router(webhook_router)
app.include_router(incident_router)
app.include_router(approval_router)
app.include_router(notification_router)

