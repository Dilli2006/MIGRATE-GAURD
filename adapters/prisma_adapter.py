"""Prisma adapter -- fully implemented, production-ready."""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Any

import asyncpg

from backend.adapters.base import MigrationAdapter
from backend.core.schemas import Incident, IncidentStatus, SchemaState, VerdictType
from backend.db.history_reconstruction import get_baseline_schema
from backend.db.introspection import get_live_schema
from backend.config import settings


class PrismaAdapter(MigrationAdapter):
    """Prisma-specific adapter implementing the 4-question contract."""

    def __init__(self, pool: asyncpg.Pool | None = None):
        self._pool = pool

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
        return self._pool

    async def detect_failure(self, payload: dict) -> Incident | None:
        """Parse GitHub/GitLab webhook for migration failure signal.

        Checks _prisma_migrations table for unfinished migrations.
        """
        pool = await self._get_pool()

        try:
            rows = await pool.fetch(
                """
                SELECT id, migration_name, started_at, applied_steps_at
                FROM _prisma_migrations
                WHERE finished_at IS NULL
                ORDER BY started_at DESC
                LIMIT 1
                """
            )
        except Exception:
            # Table might not exist yet -- try to extract from payload
            rows = []

        if rows:
            row = rows[0]
            return Incident(
                id=str(uuid.uuid4()),
                migration_name=row["migration_name"],
                migration_sql=await self._read_migration_sql(row["migration_name"]),
                detected_at=datetime.now(timezone.utc),
                status=IncidentStatus.DETECTED,
                raw_logs=f"Detected unfinished migration: {row['migration_name']}",
                prisma_dir=settings.PRISMA_MIGRATIONS_DIR,
            )

        # Fallback: try to extract from webhook payload
        return self._parse_webhook_payload(payload)

    def _parse_webhook_payload(self, payload: dict) -> Incident | None:
        """Extract migration failure info from GitHub/GitLab webhook payload."""
        # GitHub Actions
        if "workflow_run" in payload:
            wr = payload["workflow_run"]
            if wr.get("conclusion") == "failure":
                msg = wr.get("display_title", "")
                # Try to find migration name in commit messages
                commits = payload.get("commits", [])
                for c in commits:
                    msg = c.get("message", "")
                    # Prefer Prisma migration marker
                    m = re.search(r"Prisma migration:\s*(.+)", msg, re.IGNORECASE)
                    if not m:
                        m = re.search(r"(?:chore|migrate|migration):\s*(.+)", msg, re.IGNORECASE)
                    if m:
                        return Incident(
                            id=str(uuid.uuid4()),
                            migration_name=m.group(1).strip(),
                            migration_sql="",
                            detected_at=datetime.now(timezone.utc),
                            status=IncidentStatus.DETECTED,
                            raw_logs=msg,
                            prisma_dir=settings.PRISMA_MIGRATIONS_DIR,
                        )

        # GitLab CI
        if "build_status" in payload:
            if payload["build_status"] == "failed":
                return Incident(
                    id=str(uuid.uuid4()),
                    migration_name=str(payload.get("id", "unknown")),
                    migration_sql="",
                    detected_at=datetime.now(timezone.utc),
                    status=IncidentStatus.DETECTED,
                    raw_logs=payload.get("build_log", ""),
                    prisma_dir=settings.PRISMA_MIGRATIONS_DIR,
                )

        return None

    async def _read_migration_sql(self, migration_name: str) -> str:
        """Read the migration.sql file from the Prisma migrations directory."""
        migrations_dir = settings.PRISMA_MIGRATIONS_DIR
        sql_path = os.path.join(migrations_dir, migration_name, "migration.sql")
        if os.path.isfile(sql_path):
            with open(sql_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    async def get_baseline(self, incident: Incident) -> SchemaState:
        """Reconstruct schema state before the failed migration."""
        prisma_dir = incident.prisma_dir or settings.PRISMA_MIGRATIONS_DIR
        return await get_baseline_schema(prisma_dir, incident.migration_name)

    async def get_live_schema(self) -> SchemaState:
        """Introspect the actual live database schema."""
        pool = await self._get_pool()
        return await get_live_schema(pool)

    async def resolve(self, incident: Incident, verdict: VerdictType) -> bool:
        """Execute Prisma's own native resolve command."""
        cmd_map = {
            VerdictType.APPLIED: "--applied",
            VerdictType.ROLLED_BACK: "--rolled-back",
        }
        flag = cmd_map.get(verdict)
        if not flag:
            return False

        cmd = [
            "npx", "prisma", "migrate", "resolve",
            flag, incident.migration_name,
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(settings.PRISMA_SCHEMA_PATH) or ".",
            )
            stdout, stderr = await proc.communicate()
            return proc.returncode == 0
        except Exception:
            return False
