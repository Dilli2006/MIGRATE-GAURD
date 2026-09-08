"""Tests for the verdict engine."""

import pytest

from backend.core.schemas import Action, ActionType, SchemaDelta, VerdictType, Verifiability
from backend.core.verdict_engine import compute_verdict


class TestVerdictEngine:
    def test_all_verifiable_applied(self):
        actions = [
            Action(statement_text="CREATE TABLE test (id INT);", action_type=ActionType.CREATE_TABLE, target_table="test", verifiability=Verifiability.VERIFIABLE, statement_index=0),
        ]
        delta = SchemaDelta(added_tables={"test"}, dropped_tables=set(), added_columns={}, dropped_columns={}, added_constraints={}, dropped_constraints={}, added_indexes={}, dropped_indexes={})
        result = compute_verdict(actions, delta)
        assert result.verdict == VerdictType.APPLIED
        assert result.confidence == 1.0

    def test_all_verifiable_rolled_back(self):
        actions = [
            Action(statement_text="CREATE TABLE test (id INT);", action_type=ActionType.CREATE_TABLE, target_table="test", verifiability=Verifiability.VERIFIABLE, statement_index=0),
        ]
        delta = SchemaDelta(added_tables=set(), dropped_tables=set(), added_columns={}, dropped_columns={}, added_constraints={}, dropped_constraints={}, added_indexes={}, dropped_indexes={})
        result = compute_verdict(actions, delta)
        assert result.verdict == VerdictType.ROLLED_BACK

    def test_non_verifiable_hard_stop(self):
        actions = [
            Action(statement_text="ALTER TABLE users ALTER COLUMN name TYPE INT;", action_type=ActionType.ALTER_COLUMN_TYPE, target_table="users", verifiability=Verifiability.NOT_VERIFIABLE, statement_index=0),
        ]
        delta = SchemaDelta(added_tables=set(), dropped_tables=set(), added_columns={}, dropped_columns={}, added_constraints={}, dropped_constraints={}, added_indexes={}, dropped_indexes={})
        result = compute_verdict(actions, delta)
        assert result.verdict == VerdictType.HARD_STOP

    def test_mixed_verifiable_hard_stop(self):
        actions = [
            Action(statement_text="CREATE TABLE test (id INT);", action_type=ActionType.CREATE_TABLE, target_table="test", verifiability=Verifiability.VERIFIABLE, statement_index=0),
            Action(statement_text="ALTER TABLE users ALTER COLUMN name TYPE INT;", action_type=ActionType.ALTER_COLUMN_TYPE, target_table="users", verifiability=Verifiability.NOT_VERIFIABLE, statement_index=1),
        ]
        delta = SchemaDelta(added_tables={"test"}, dropped_tables=set(), added_columns={}, dropped_columns={}, added_constraints={}, dropped_constraints={}, added_indexes={}, dropped_indexes={})
        result = compute_verdict(actions, delta)
        assert result.verdict == VerdictType.HARD_STOP
        assert result.non_verifiable_actions == 1

    def test_empty_actions_rolled_back(self):
        delta = SchemaDelta(added_tables=set(), dropped_tables=set(), added_columns={}, dropped_columns={}, added_constraints={}, dropped_constraints={}, added_indexes={}, dropped_indexes={})
        result = compute_verdict([], delta)
        assert result.verdict == VerdictType.ROLLED_BACK

    def test_drop_table_applied(self):
        actions = [
            Action(statement_text="DROP TABLE old_data;", action_type=ActionType.DROP_TABLE, target_table="old_data", verifiability=Verifiability.VERIFIABLE, statement_index=0),
        ]
        delta = SchemaDelta(added_tables=set(), dropped_tables={"old_data"}, added_columns={}, dropped_columns={}, added_constraints={}, dropped_constraints={}, added_indexes={}, dropped_indexes={})
        result = compute_verdict(actions, delta)
        assert result.verdict == VerdictType.APPLIED

    def test_add_column_applied(self):
        actions = [
            Action(statement_text="ALTER TABLE users ADD COLUMN email TEXT;", action_type=ActionType.ADD_COLUMN, target_table="users", verifiability=Verifiability.VERIFIABLE, statement_index=0),
        ]
        delta = SchemaDelta(added_tables=set(), dropped_tables=set(), added_columns={"users": {"email"}}, dropped_columns={}, added_constraints={}, dropped_constraints={}, added_indexes={}, dropped_indexes={})
        result = compute_verdict(actions, delta)
        assert result.verdict == VerdictType.APPLIED

