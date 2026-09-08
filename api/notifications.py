"""Notification delivery - Slack webhook integration."""

from __future__ import annotations

import httpx
from fastapi import APIRouter

from backend.config import settings

router = APIRouter(tags=["notifications"])


@router.post("/notify/slack")
async def notify_slack(incident_id: str, verdict: str, summary: str, evidence: str):
    """Send verdict + evidence to Slack webhook."""
    if not settings.SLACK_WEBHOOK_URL:
        return {"status": "skipped", "reason": "No SLACK_WEBHOOK_URL configured"}

    color_map = {
        "APPLIED": "#36a64f",
        "ROLLED_BACK": "#ff9900",
        "HARD_STOP": "#ff0000",
    }

    payload = {
        "attachments": [
            {
                "color": color_map.get(verdict, "#cccccc"),
                "title": f"MIGRATE-GUARD: {verdict}",
                "text": summary,
                "fields": [
                    {"title": "Incident ID", "value": incident_id, "short": True},
                    {"title": "Verdict", "value": verdict, "short": True},
                    {"title": "Evidence", "value": evidence[:500], "short": False},
                ],
            }
        ]
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(settings.SLACK_WEBHOOK_URL, json=payload)
        return {"status": "sent", "slack_status": resp.status_code}
