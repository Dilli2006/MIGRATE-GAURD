"""Approval flow - engineer reviews and resolves incidents."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.adapters.registry import get_adapter
from backend.core.schemas import IncidentStatus, VerdictType

router = APIRouter(prefix="/incidents", tags=["approvals"])


def _get_incidents():
    from backend.api.webhooks import _incidents
    return _incidents


@router.post("/{incident_id}/approve")
async def approve_incident(incident_id: str):
    """Engineer approves the verdict. Execute the native resolve command."""
    incidents = _get_incidents()
    if incident_id not in incidents:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident = incidents[incident_id]
    if incident.status != IncidentStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=400,
            detail=f"Incident is in status {incident.status.value}, expected AWAITING_APPROVAL",
        )

    adapter = get_adapter("prisma")
    verdict_type = incident.verdict.verdict if incident.verdict else VerdictType.APPLIED
    success = await adapter.resolve(incident, verdict_type)

    if success:
        incident.status = IncidentStatus.RESOLVED
        incident.resolution = f"Resolved as {verdict_type.value}"
    else:
        incident.status = IncidentStatus.FAILED
        incident.resolution = "Resolution command failed"

    return {"status": incident.status.value, "resolution": incident.resolution}


@router.post("/{incident_id}/reject")
async def reject_incident(incident_id: str):
    """Engineer rejects the verdict. Mark as rolled back."""
    incidents = _get_incidents()
    if incident_id not in incidents:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident = incidents[incident_id]
    adapter = get_adapter("prisma")
    success = await adapter.resolve(incident, VerdictType.ROLLED_BACK)

    if success:
        incident.status = IncidentStatus.RESOLVED
        incident.resolution = "Resolved as ROLLED_BACK"
    else:
        incident.status = IncidentStatus.FAILED
        incident.resolution = "Rollback command failed"

    return {"status": incident.status.value, "resolution": incident.resolution}


@router.post("/{incident_id}/escalate")
async def escalate_incident(incident_id: str):
    """Escalate for manual review."""
    incidents = _get_incidents()
    if incident_id not in incidents:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident = incidents[incident_id]
    incident.status = IncidentStatus.FAILED
    incident.resolution = "Escalated for manual review - non-verifiable actions detected"
    return {"status": "escalated", "resolution": incident.resolution}
