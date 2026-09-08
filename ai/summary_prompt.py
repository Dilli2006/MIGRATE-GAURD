"""Plain-English incident narration - template-based (no LLM needed for demo)."""

from __future__ import annotations

from backend.core.schemas import Incident, VerdictResult


def summarize(incident: Incident, verdict: VerdictResult) -> str:
    """Generate a human-readable summary of what happened."""
    verdict_text = verdict.verdict.value
    confidence = verdict.confidence

    parts = [
        f"Migration {incident.migration_name} was diagnosed as {verdict_text}."
    ]

    if verdict.delta_summary:
        added = verdict.delta_summary.get("added_tables", set())
        dropped = verdict.delta_summary.get("dropped_tables", set())
        if added:
            parts.append(f"Tables added: {', '.join(sorted(added))}.")
        if dropped:
            parts.append(f"Tables dropped: {', '.join(sorted(dropped))}.")

    parts.append(f"Confidence: {confidence:.0%}.")

    if verdict.verdict.value == "HARD_STOP":
        parts.append(
            "Manual review required - non-verifiable actions detected in the migration."
        )
    elif verdict.verdict.value == "APPLIED":
        parts.append(
            "All changes verified as applied. Approve to mark migration as applied."
        )
    else:
        parts.append(
            "No changes detected in the live schema. Approve to mark migration as rolled back."
        )

    return " ".join(parts)

