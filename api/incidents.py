"""Incident CRUD - list, detail, manual trigger, and analysis pipeline."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from backend.adapters.registry import get_adapter
from backend.ai.redaction_prompt import redact
from backend.ai.summary_prompt import summarize
from backend.core.classifier import classify_migration
from backend.core.delta_engine import compute_delta
from backend.core.schemas import Incident, IncidentStatus
from backend.core.verdict_engine import compute_verdict

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _get_incidents() -> dict[str, Incident]:
    from backend.api.webhooks import _incidents
    return _incidents


async def run_analysis(incident: Incident) -> None:
    """Run the full forensic pipeline on an incident."""
    adapter = get_adapter("prisma")
    incident.status = IncidentStatus.ANALYZING

    # Step 1: Get baseline (S0) and live (S1)
    baseline = await adapter.get_baseline(incident)
    live = await adapter.get_live_schema()

    # Step 2: Compute delta
    delta = compute_delta(baseline, live)

    # Step 3: Parse and classify migration SQL
    actions = classify_migration(incident.migration_sql)

    # Step 4: Compute verdict
    verdict = compute_verdict(actions, delta)
    incident.verdict = verdict

    # Step 5: AI narration (redact + summarize)
    incident.redacted_logs = redact(incident.raw_logs or "")
    incident.summary = summarize(incident, verdict)

    incident.status = IncidentStatus.AWAITING_APPROVAL


@router.get("/")
async def list_incidents():
    """List all known incidents."""
    return list(_get_incidents().values())


@router.get("/{incident_id}")
async def get_incident(incident_id: str):
    """Get a single incident with full evidence."""
    incidents = _get_incidents()
    if incident_id not in incidents:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incidents[incident_id]


@router.post("/")
async def create_incident(request: Request):
    """Manually trigger an incident for testing.

    Accepts: { "migration_name": "...", "migration_sql": "...", "prisma_dir": "..." }
    """
    body = await request.json()
    incident = Incident(
        id=str(uuid.uuid4()),
        migration_name=body.get("migration_name", "unknown"),
        migration_sql=body.get("migration_sql", ""),
        detected_at=datetime.now(timezone.utc),
        status=IncidentStatus.DETECTED,
        prisma_dir=body.get("prisma_dir", "./prisma/migrations"),
    )

    await run_analysis(incident)
    _get_incidents()[incident.id] = incident
    return incident
