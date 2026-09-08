"""Tests for the Prisma adapter."""

import pytest

from backend.adapters.prisma_adapter import PrismaAdapter


class TestPrismaAdapter:
    def test_adapter_is_instantiable(self):
        adapter = PrismaAdapter()
        assert adapter is not None

    def test_parse_webhook_github_failure(self):
        adapter = PrismaAdapter()
        payload = {
            "workflow_run": {"conclusion": "failure", "display_title": "Deploy migration"},
            "commits": [{"message": "chore: migrate add users table\n\nPrisma migration: 20240101_add_users_table"}],
        }
        incident = adapter._parse_webhook_payload(payload)
        assert incident is not None
        assert incident.migration_name == "20240101_add_users_table"

