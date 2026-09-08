"""MIGRATE-GUARD - FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import settings

FRONTEND_DIR = Path(__file__).parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create and tear down the database connection pool."""
    try:
        app.state.pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL, timeout=2)
    except Exception:
        app.state.pool = None
    yield
    if getattr(app.state, "pool", None):
        try:
            await app.state.pool.close()
        except Exception:
            pass


app = FastAPI(
    title="MIGRATE-GUARD",
    description="The Post-Failure Resolution Engine for Database Migrations",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow browser fetch from any origin (development-friendly)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Serve the dashboard UI — mount AFTER API routes so /docs, /health, /incidents/
# are handled first.
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
