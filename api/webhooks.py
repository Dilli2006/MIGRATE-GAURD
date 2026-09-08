"""Webhook receiver - catches failure signals from GitHub/GitLab CI."""

from __future__ import annotations

from fastapi import APIRouter, Request

from backend.adapters.registry import get_adapter

router = APIRouter(prefix="/webhook", tags=["webhooks"])

# In-memory incident store (for demo; swap for a real DB in production)
_incidents: dict[str, "Incident"] = {}


@router.post("/github")
async def github_webhook(request: Request):
    """Receive a GitHub Actions failure webhook."""
    payload = await request.json()
    adapter = get_adapter("prisma")
    incident = await adapter.detect_failure(payload)
    if not incident:
        return {"status": "no_failure_detected"}

    from backend.api.incidents import run_analysis
    await run_analysis(incident)
    _incidents[incident.id] = incident
    return {"status": "incident_created", "incident_id": incident.id}


@router.post("/gitlab")
async def gitlab_webhook(request: Request):
    """Receive a GitLab CI failure webhook."""
    payload = await request.json()
    adapter = get_adapter("prisma")
    incident = await adapter.detect_failure(payload)
    if not incident:
        return {"status": "no_failure_detected"}

    from backend.api.incidents import run_analysis
    await run_analysis(incident)
    _incidents[incident.id] = incident
    return {"status": "incident_created", "incident_id": incident.id}
