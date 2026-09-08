"""Pydantic v2 models for MIGRATE-GUARD — the forensic engine for crashed migrations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    CREATE_TABLE = "CREATE_TABLE"
    DROP_TABLE = "DROP_TABLE"
    ADD_COLUMN = "ADD_COLUMN"
    DROP_COLUMN = "DROP_COLUMN"
    ADD_CONSTRAINT = "ADD_CONSTRAINT"
    DROP_CONSTRAINT = "DROP_CONSTRAINT"
    CREATE_INDEX = "CREATE_INDEX"
    DROP_INDEX = "DROP_INDEX"
    ALTER_COLUMN_TYPE = "ALTER_COLUMN_TYPE"
    ALTER_COLUMN_NULL = "ALTER_COLUMN_NULL"
    RENAME_TABLE = "RENAME_TABLE"
    RENAME_COLUMN = "RENAME_COLUMN"
    RAW_DML = "RAW_DML"


class Verifiability(str, Enum):
    VERIFIABLE = "VERIFIABLE"
    NOT_VERIFIABLE = "NOT_VERIFIABLE"


class Action(BaseModel):
    statement_text: str
    action_type: ActionType
    target_table: str
    verifiability: Verifiability | None = None
    statement_index: int = 0


class SchemaColumn(BaseModel):
    name: str
    data_type: str
    is_nullable: bool = False
    column_default: str | None = None
    constraints: list[str] = Field(default_factory=list)


class SchemaTable(BaseModel):
    name: str
    columns: dict[str, SchemaColumn] = Field(default_factory=dict)
    constraints: dict[str, dict] = Field(default_factory=dict)
    indexes: dict[str, dict] = Field(default_factory=dict)


class SchemaState(BaseModel):
    tables: dict[str, SchemaTable] = Field(default_factory=dict)


class SchemaDelta(BaseModel):
    added_tables: set[str] = Field(default_factory=set)
    dropped_tables: set[str] = Field(default_factory=set)
    added_columns: dict[str, set[str]] = Field(default_factory=dict)
    dropped_columns: dict[str, set[str]] = Field(default_factory=dict)
    added_constraints: dict[str, set[str]] = Field(default_factory=dict)
    dropped_constraints: dict[str, set[str]] = Field(default_factory=dict)
    added_indexes: dict[str, set[str]] = Field(default_factory=dict)
    dropped_indexes: dict[str, set[str]] = Field(default_factory=dict)


class VerdictType(str, Enum):
    APPLIED = "APPLIED"
    ROLLED_BACK = "ROLLED_BACK"
    HARD_STOP = "HARD_STOP"


class VerdictResult(BaseModel):
    verdict: VerdictType
    total_actions: int = 0
    verifiable_actions: int = 0
    non_verifiable_actions: int = 0
    applied_actions: list[Action] = Field(default_factory=list)
    unverifiable_actions: list[Action] = Field(default_factory=list)
    delta_summary: dict = Field(default_factory=dict)
    confidence: float = 1.0
    evidence: str = ""


class IncidentStatus(str, Enum):
    DETECTED = "DETECTED"
    ANALYZING = "ANALYZING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    RESOLVED = "RESOLVED"
    FAILED = "FAILED"


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    migration_name: str
    migration_sql: str = ""
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: IncidentStatus = IncidentStatus.DETECTED
    verdict: VerdictResult | None = None
    raw_logs: str | None = None
    redacted_logs: str | None = None
    summary: str | None = None
    resolution: str | None = None
    prisma_dir: str | None = None
