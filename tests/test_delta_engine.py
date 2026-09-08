"""Tests for the schema delta computation engine."""

import pytest

from backend.core.schemas import SchemaColumn, SchemaState, SchemaTable
from backend.core.delta_engine import compute_delta


def _make_schema(tables: dict) -> SchemaState:
    schema_tables = {}
    for table_name, columns in tables.items():
        cols = {}
        for col_name, col_type in columns.items():
            cols[col_name] = SchemaColumn(name=col_name, data_type=col_type, is_nullable=False)
        schema_tables[table_name] = SchemaTable(name=table_name, columns=cols, constraints={}, indexes={})
    return SchemaState(tables=schema_tables)


class TestDeltaEngine:
    def test_added_table(self):
        baseline = _make_schema({"users": {"id": "INT", "name": "TEXT"}})
        live = _make_schema({"users": {"id": "INT", "name": "TEXT"}, "orders": {"id": "INT", "user_id": "INT"}})
        delta = compute_delta(baseline, live)
        assert "orders" in delta.added_tables
        assert len(delta.dropped_tables) == 0

    def test_dropped_table(self):
        baseline = _make_schema({"users": {"id": "INT"}, "orders": {"id": "INT"}})
        live = _make_schema({"users": {"id": "INT"}})
        delta = compute_delta(baseline, live)
        assert "orders" in delta.dropped_tables

    def test_added_column(self):
        baseline = _make_schema({"users": {"id": "INT", "name": "TEXT"}})
        live = _make_schema({"users": {"id": "INT", "name": "TEXT", "email": "TEXT"}})
        delta = compute_delta(baseline, live)
        assert "email" in delta.added_columns.get("users", set())

    def test_dropped_column(self):
        baseline = _make_schema({"users": {"id": "INT", "name": "TEXT", "email": "TEXT"}})
        live = _make_schema({"users": {"id": "INT", "name": "TEXT"}})
        delta = compute_delta(baseline, live)
        assert "email" in delta.dropped_columns.get("users", set())

    def test_no_changes(self):
        schema = _make_schema({"users": {"id": "INT", "name": "TEXT"}})
        delta = compute_delta(schema, schema)
        assert len(delta.added_tables) == 0
        assert len(delta.dropped_tables) == 0
        assert len(delta.added_columns) == 0
        assert len(delta.dropped_columns) == 0

    def test_multiple_changes(self):
        baseline = _make_schema({"users": {"id": "INT", "name": "TEXT"}, "old_table": {"id": "INT"}})
        live = _make_schema({"users": {"id": "INT", "name": "TEXT", "email": "TEXT"}, "new_table": {"id": "INT"}})
        delta = compute_delta(baseline, live)
        assert "new_table" in delta.added_tables
        assert "old_table" in delta.dropped_tables
        assert "email" in delta.added_columns.get("users", set())

