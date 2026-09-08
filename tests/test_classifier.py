"""Tests for the SQL classifier - parsing + verifiability tagging."""

import pytest

from backend.core.classifier import classify_migration
from backend.core.schemas import ActionType, Verifiability


class TestClassifier:
    def test_create_table_is_verifiable(self):
        sql = "CREATE TABLE users (id SERIAL PRIMARY KEY, name TEXT NOT NULL);"
        actions = classify_migration(sql)
        assert len(actions) >= 1
        assert actions[0].action_type == ActionType.CREATE_TABLE
        assert actions[0].verifiability == Verifiability.VERIFIABLE

    def test_drop_table_is_verifiable(self):
        sql = "DROP TABLE users;"
        actions = classify_migration(sql)
        assert len(actions) == 1
        assert actions[0].action_type == ActionType.DROP_TABLE
        assert actions[0].verifiability == Verifiability.VERIFIABLE

    def test_add_column_is_verifiable(self):
        sql = "ALTER TABLE users ADD COLUMN email TEXT;"
        actions = classify_migration(sql)
        assert any(a.action_type == ActionType.ADD_COLUMN for a in actions)
        assert all(a.verifiability == Verifiability.VERIFIABLE for a in actions)

    def test_alter_column_type_is_not_verifiable(self):
        sql = "ALTER TABLE users ALTER COLUMN name TYPE VARCHAR(255);"
        actions = classify_migration(sql)
        assert any(a.action_type == ActionType.ALTER_COLUMN_TYPE for a in actions)
        assert any(a.verifiability == Verifiability.NOT_VERIFIABLE for a in actions)

    def test_rename_table_not_verifiable(self):
        sql = "ALTER TABLE users RENAME TO customers;"
        actions = classify_migration(sql)
        assert any(a.verifiability == Verifiability.NOT_VERIFIABLE for a in actions)

    def test_raw_dml_not_verifiable(self):
        sql = "UPDATE users SET name = 'test' WHERE id = 1;"
        actions = classify_migration(sql)
        assert actions[0].action_type == ActionType.RAW_DML
        assert actions[0].verifiability == Verifiability.NOT_VERIFIABLE

    def test_create_index_verifiable(self):
        sql = "CREATE INDEX idx_users_email ON users (email);"
        actions = classify_migration(sql)
        assert actions[0].action_type == ActionType.CREATE_INDEX
        assert actions[0].verifiability == Verifiability.VERIFIABLE

    def test_drop_index_verifiable(self):
        sql = "DROP INDEX idx_users_email;"
        actions = classify_migration(sql)
        assert actions[0].action_type == ActionType.DROP_INDEX
        assert actions[0].verifiability == Verifiability.VERIFIABLE

    def test_empty_sql_returns_empty(self):
        actions = classify_migration("")
        assert actions == []

    def test_multiple_statements(self):
        sql = "CREATE TABLE users (id SERIAL PRIMARY KEY); CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT);"
        actions = classify_migration(sql)
        assert len(actions) == 2
        assert all(a.verifiability == Verifiability.VERIFIABLE for a in actions)
