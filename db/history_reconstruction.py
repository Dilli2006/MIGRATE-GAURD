"""Reconstruct the schema state before a failed migration from history alone."""

from __future__ import annotations

import asyncio
import os
import re
import tempfile
from pathlib import Path

from backend.core.schemas import SchemaColumn, SchemaState, SchemaTable


def _get_prior_migration_dir(migrations_dir: str, failed_migration: str) -> str | None:
    """Find the migration directory that comes alphabetically before the failed one."""
    if not os.path.isdir(migrations_dir):
        return None

    dirs = sorted(
        d for d in os.listdir(migrations_dir)
        if os.path.isdir(os.path.join(migrations_dir, d))
    )

    try:
        idx = dirs.index(failed_migration)
        if idx > 0:
            return os.path.join(migrations_dir, dirs[idx - 1])
    except ValueError:
        pass

    return None


def _parse_sql_to_schema(sql: str) -> SchemaState:
    """Parse SQL statements to build a SchemaState.

    This is a simplified parser for migration SQL -- handles CREATE TABLE,
    ALTER TABLE ADD COLUMN, ALTER TABLE DROP TABLE, DROP TABLE.
    """
    tables: dict[str, SchemaTable] = {}
    statements = [s.strip().rstrip(";") for s in sql.split(";") if s.strip()]

    for stmt in statements:
        upper = stmt.upper()
        if not upper:
            continue

        # CREATE TABLE
        if upper.startswith("CREATE") and "TABLE" in upper:
            # Extract table name
            m = re.search(r'CREATE\s+(?:TEMPORARY\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["\']?(\w+)["\']?', stmt, re.IGNORECASE)
            if m:
                tname = m.group(1)
                tables[tname] = SchemaTable(name=tname)
                # Parse columns from parentheses
                paren_match = re.search(r'\((.*)\)', stmt, re.DOTALL)
                if paren_match:
                    body = paren_match.group(1)
                    for part in _split_outside_parens(body):
                        part = part.strip()
                        if not part or part.upper().startswith(("PRIMARY", "UNIQUE", "CHECK", "FOREIGN", "CONSTRAINT")):
                            continue
                        col_match = re.match(r'["\']?(\w+)["\']?\s+([\w()]+)', part, re.IGNORECASE)
                        if col_match:
                            col = SchemaColumn(
                                name=col_match.group(1),
                                data_type=col_match.group(2),
                                is_nullable="NOT NULL" not in part.upper(),
                            )
                            tables[tname].columns[col.name] = col

        # ALTER TABLE ... ADD COLUMN
        elif upper.startswith("ALTER") and "TABLE" in upper and "ADD" in upper:
            m = re.search(r'ALTER\s+TABLE\s+["\']?(\w+)["\']?', stmt, re.IGNORECASE)
            col_m = re.search(r'ADD\s+(?:COLUMN\s+)?(?:IF\s+NOT\s+EXISTS\s+)?["\']?(\w+)["\']?\s+([\w()]+)', stmt, re.IGNORECASE)
            if m and col_m:
                tname = m.group(1)
                if tname not in tables:
                    tables[tname] = SchemaTable(name=tname)
                col = SchemaColumn(
                    name=col_m.group(1),
                    data_type=col_m.group(2),
                    is_nullable="NOT NULL" not in stmt.upper().split("ADD")[-1],
                )
                tables[tname].columns[col.name] = col

        # ALTER TABLE ... DROP COLUMN
        elif upper.startswith("ALTER") and "TABLE" in upper and "DROP" in upper and "COLUMN" in upper:
            m = re.search(r'ALTER\s+TABLE\s+["\']?(\w+)["\']?', stmt, re.IGNORECASE)
            col_m = re.search(r'DROP\s+(?:COLUMN\s+)?(?:IF\s+EXISTS\s+)?["\']?(\w+)["\']?', stmt, re.IGNORECASE)
            if m and col_m:
                tname = m.group(1)
                if tname in tables:
                    tables[tname].columns.pop(col_m.group(1), None)

        # DROP TABLE
        elif upper.startswith("DROP") and "TABLE" in upper:
            m = re.search(r'DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?["\']?(\w+)["\']?', stmt, re.IGNORECASE)
            if m:
                tables.pop(m.group(1), None)

    return SchemaState(tables=tables)


def _split_outside_parens(sql: str) -> list[str]:
    parts, depth, current = [], 0, []
    for char in sql:
        if char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    if current:
        parts.append("".join(current))
    return parts


async def get_baseline_schema(prisma_dir: str, migration_name: str) -> SchemaState:
    """Reconstruct schema state BEFORE the failed migration.

    Strategy:
    1. Find the migration before the failed one in the migrations directory
    2. Collect all SQL from migrations up to (but not including) the failed one
    3. Replay them to build the baseline schema
    """
    migrations_dir = prisma_dir
    if not os.path.isdir(migrations_dir):
        # Try common Prisma paths
        for candidate in ["./prisma/migrations", "../prisma/migrations"]:
            if os.path.isdir(candidate):
                migrations_dir = candidate
                break

    # Get all migration dirs sorted
    if os.path.isdir(migrations_dir):
        all_migrations = sorted(
            d for d in os.listdir(migrations_dir)
            if os.path.isdir(os.path.join(migrations_dir, d))
        )

        # Find index of the failed migration
        try:
            fail_idx = all_migrations.index(migration_name)
        except ValueError:
            fail_idx = len(all_migrations)

        # Replay all migrations before the failed one
        combined_sql = ""
        for i in range(fail_idx):
            migration_path = os.path.join(migrations_dir, all_migrations[i], "migration.sql")
            if os.path.isfile(migration_path):
                with open(migration_path, "r", encoding="utf-8") as f:
                    combined_sql += f.read() + "\n"

        if combined_sql:
            return _parse_sql_to_schema(combined_sql)

    # Fallback: empty schema
    return SchemaState(tables={})
