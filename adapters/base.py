"""Abstract adapter contract -- every migration tool plugin must answer 4 questions."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core.schemas import Incident, SchemaState, VerdictType


class MigrationAdapter(ABC):
    """The fixed 4-question contract that every adapter must implement."""

    @abstractmethod
    async def detect_failure(self, payload: dict) -> Incident | None:
        """Q1 DETECT -- did a migration fail? Parse the webhook/CI payload."""

    @abstractmethod
    async def get_baseline(self, incident: Incident) -> SchemaState:
        """Q2 BASELINE -- reconstruct the schema state before the failure."""

    @abstractmethod
    async def get_live_schema(self) -> SchemaState:
        """Q3 LIVE -- introspect the actual live database schema right now."""

    @abstractmethod
    async def resolve(self, incident: Incident, verdict: VerdictType) -> bool:
        """Q4 RESOLVE -- call the migration tool's own native recovery command."""
