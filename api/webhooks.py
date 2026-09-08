"""Webhook receiver - catches failure signals from GitHub/GitLab CI."""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Request

from backend.adapters.registry import get_adapter

router = APIRouter(prefix="/webhook", tags=["webhooks"])

from backend.core.schemas import (
    Action,
    ActionType,
    Incident,
    IncidentStatus,
    Verifiability,
    VerdictResult,
    VerdictType,
)

# In-memory incident store seeded with demo incidents
_incidents: dict[str, Incident] = {
    "inc-001-applied": Incident(
        id="inc-001-applied",
        migration_name="202609080010_add_teams_table",
        migration_sql="CREATE TABLE \"teams\" (\n  \"id\" SERIAL NOT NULL PRIMARY KEY,\n  \"name\" TEXT NOT NULL,\n  \"created_at\" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP\n);\nALTER TABLE \"users\" ADD COLUMN \"team_id\" INTEGER;\nALTER TABLE \"users\" ADD CONSTRAINT \"fk_users_team_id\" FOREIGN KEY (\"team_id\") REFERENCES \"teams\"(\"id\");\nCREATE INDEX \"idx_users_team_id\" ON \"users\"(\"team_id\");",
        detected_at=datetime.now(timezone.utc),
        status=IncidentStatus.AWAITING_APPROVAL,
        raw_logs="Error: P3009\nMigration '202609080010_add_teams_table' failed.\nPost-migration health check timed out after 30s.\nConnection string: postgres://admin:s3cr3t_p@ss@prod.db.internal:5432/main",
        redacted_logs="Error: P3009\nMigration '202609080010_add_teams_table' failed.\nPost-migration health check timed out after 30s.\nConnection string: postgres://admin:[REDACTED]@prod.db.internal:5432/main",
        summary="Migration 202609080010_add_teams_table was diagnosed as APPLIED. Tables added: teams. Confidence: 100%. All changes verified as applied. Approve to mark migration as applied.",
        verdict=VerdictResult(
            verdict=VerdictType.APPLIED,
            total_actions=4,
            verifiable_actions=4,
            non_verifiable_actions=0,
            confidence=1.0,
            evidence="All 4 verifiable DDL actions were found present in the live database schema (S1). Zero missing changes.",
            delta_summary={
                "added_tables": ["teams"],
                "dropped_tables": [],
                "added_columns": {"users": ["team_id"]},
                "dropped_columns": {},
                "added_indexes": {"users": ["idx_users_team_id"]},
                "dropped_indexes": {},
            },
            applied_actions=[
                Action(statement_text="CREATE TABLE \"teams\" (...)", action_type=ActionType.CREATE_TABLE, target_table="teams", verifiability=Verifiability.VERIFIABLE, statement_index=1),
                Action(statement_text="ALTER TABLE \"users\" ADD COLUMN \"team_id\" INTEGER", action_type=ActionType.ADD_COLUMN, target_table="users", verifiability=Verifiability.VERIFIABLE, statement_index=2),
                Action(statement_text="ALTER TABLE \"users\" ADD CONSTRAINT \"fk_users_team_id\"...", action_type=ActionType.ADD_CONSTRAINT, target_table="users", verifiability=Verifiability.VERIFIABLE, statement_index=3),
                Action(statement_text="CREATE INDEX \"idx_users_team_id\" ON \"users\"(\"team_id\")", action_type=ActionType.CREATE_INDEX, target_table="users", verifiability=Verifiability.VERIFIABLE, statement_index=4),
            ],
            unverifiable_actions=[],
        ),
    ),
    "inc-002-rollback": Incident(
        id="inc-002-rollback",
        migration_name="202609080020_add_audit_logs",
        migration_sql="CREATE TABLE \"audit_logs\" (\n  \"id\" SERIAL NOT NULL PRIMARY KEY,\n  \"user_id\" INTEGER NOT NULL,\n  \"action\" TEXT NOT NULL,\n  \"created_at\" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP\n);\nCREATE INDEX \"idx_audit_logs_user_id\" ON \"audit_logs\"(\"user_id\");\nCREATE INDEX \"idx_audit_logs_created\" ON \"audit_logs\"(\"created_at\");",
        detected_at=datetime.now(timezone.utc),
        status=IncidentStatus.AWAITING_APPROVAL,
        raw_logs="Error: P3009\nDisk quota exceeded during DDL execution. Transaction aborted by PostgreSQL.",
        redacted_logs="Error: P3009\nDisk quota exceeded during DDL execution. Transaction aborted by PostgreSQL.",
        summary="Migration 202609080020_add_audit_logs was diagnosed as ROLLED_BACK. Confidence: 100%. No changes detected in the live schema. Approve to mark migration as rolled back.",
        verdict=VerdictResult(
            verdict=VerdictType.ROLLED_BACK,
            total_actions=3,
            verifiable_actions=3,
            non_verifiable_actions=0,
            confidence=1.0,
            evidence="No schema changes from this migration were detected in the live database schema. PostgreSQL rolled back the transaction cleanly.",
            delta_summary={
                "added_tables": [],
                "dropped_tables": [],
                "added_columns": {},
                "dropped_columns": {},
                "added_indexes": {},
                "dropped_indexes": {},
            },
            applied_actions=[],
            unverifiable_actions=[
                Action(statement_text="CREATE TABLE \"audit_logs\" (...)", action_type=ActionType.CREATE_TABLE, target_table="audit_logs", verifiability=Verifiability.VERIFIABLE, statement_index=1),
                Action(statement_text="CREATE INDEX \"idx_audit_logs_user_id\" ON \"audit_logs\"(\"user_id\")", action_type=ActionType.CREATE_INDEX, target_table="audit_logs", verifiability=Verifiability.VERIFIABLE, statement_index=2),
                Action(statement_text="CREATE INDEX \"idx_audit_logs_created\" ON \"audit_logs\"(\"created_at\")", action_type=ActionType.CREATE_INDEX, target_table="audit_logs", verifiability=Verifiability.VERIFIABLE, statement_index=3),
            ],
        ),
    ),
    "inc-003-hardstop": Incident(
        id="inc-003-hardstop",
        migration_name="202609080030_backfill_and_alter_types",
        migration_sql="ALTER TABLE \"accounts\" ALTER COLUMN \"status\" TYPE text;\nUPDATE \"accounts\" SET \"balance\" = \"balance\" * 1.05 WHERE \"active\" = true;\nALTER TABLE \"accounts\" ALTER COLUMN \"email\" SET NOT NULL;",
        detected_at=datetime.now(timezone.utc),
        status=IncidentStatus.AWAITING_APPROVAL,
        raw_logs="Error: P3009\nMigration crashed mid-flight. Lock timeout on accounts table.",
        redacted_logs="Error: P3009\nMigration crashed mid-flight. Lock timeout on accounts table.",
        summary="Migration 202609080030_backfill_and_alter_types was diagnosed as HARD_STOP. Confidence: 33%. Manual review required - non-verifiable actions detected in the migration.",
        verdict=VerdictResult(
            verdict=VerdictType.HARD_STOP,
            total_actions=3,
            verifiable_actions=1,
            non_verifiable_actions=2,
            confidence=0.33,
            evidence="Migration contains 2 non-verifiable actions (ALTER_COLUMN_TYPE, RAW_DML). Safety threshold requires manual DBA intervention.",
            delta_summary={
                "added_tables": [],
                "dropped_tables": [],
                "added_columns": {},
                "dropped_columns": {},
                "added_indexes": {},
                "dropped_indexes": {},
            },
            applied_actions=[
                Action(statement_text="ALTER TABLE \"accounts\" ALTER COLUMN \"email\" SET NOT NULL", action_type=ActionType.ALTER_COLUMN_NULL, target_table="accounts", verifiability=Verifiability.VERIFIABLE, statement_index=3),
            ],
            unverifiable_actions=[
                Action(statement_text="ALTER TABLE \"accounts\" ALTER COLUMN \"status\" TYPE text", action_type=ActionType.ALTER_COLUMN_TYPE, target_table="accounts", verifiability=Verifiability.NOT_VERIFIABLE, statement_index=1),
                Action(statement_text="UPDATE \"accounts\" SET \"balance\" = \"balance\" * 1.05", action_type=ActionType.RAW_DML, target_table="accounts", verifiability=Verifiability.NOT_VERIFIABLE, statement_index=2),
            ],
        ),
    ),
}


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
