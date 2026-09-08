"""Adapter registry -- lookup and register migration tool adapters."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.adapters.base import MigrationAdapter

_ADAPTERS: dict[str, type[MigrationAdapter]] = {}


def _lazy_load():
    from backend.adapters.prisma_adapter import PrismaAdapter
    _ADAPTERS["prisma"] = PrismaAdapter


def get_adapter(name: str) -> MigrationAdapter:
    """Return a new adapter instance by name."""
    if not _ADAPTERS:
        _lazy_load()
    cls = _ADAPTERS.get(name)
    if not cls:
        raise ValueError(f"Unknown adapter: {name}. Available: {list(_ADAPTERS.keys())}")
    return cls()


def register_adapter(name: str, adapter_cls: type[MigrationAdapter]):
    """Register a new adapter for a migration tool."""
    _ADAPTERS[name] = adapter_cls
