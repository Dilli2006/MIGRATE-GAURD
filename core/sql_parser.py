"""
Parse migration SQL into individual actions using sqlparse.

Handles DDL (CREATE/ALTER/DROP TABLE, CREATE/DROP INDEX) and raw DML.
For ALTER TABLE, extracts individual sub-actions from comma-separated lists.
"""

from __future__ import annotations

import re

import sqlparse
from sqlparse.sql import Statement, Identifier, IdentifierList, Parenthesis
from sqlparse.tokens import Keyword, DML

from backend.core.schemas import Action, ActionType

_CREATE_TABLE_RE = re.compile(
    """CREATE\s+(?:TEMPORARY\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?['"]?(\w+)['"]?""",
    re.IGNORECASE,
)

_DROP_TABLE_RE = re.compile(
    """DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?['"]?(\w+)['"]?""",
    re.IGNORECASE,
)

_CREATE_INDEX_RE = re.compile(
    """CREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:IF\s+NOT\s+EXISTS\s+)?['"]?(\w+)['"]?\s+ON\s+['"]?(\w+)['"]?""",
    re.IGNORECASE,
)

_DROP_INDEX_RE = re.compile(
    """DROP\s+INDEX\s+(?:IF\s+EXISTS\s+)?['"]?(\w+)['"]?""",
    re.IGNORECASE,
)

_ALTER_TABLE_RE = re.compile(
    """ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?['"]?(\w+)['"]?""",
    re.IGNORECASE,
)

_RENAME_RE = re.compile(
    """RENAME\s+(?:TO\s+|COLUMN\s+)?['"]?(\w+)['"]?\s+TO\s+['"]?(\w+)['"]?""",
    re.IGNORECASE,
)

_ADD_COLUMN_RE = re.compile(
    """ADD\s+(?:COLUMN\s+)?(?:IF\s+NOT\s+EXISTS\s+)?['"]?(\w+)['"]?""",
    re.IGNORECASE,
)

_DROP_COLUMN_RE = re.compile(
    """DROP\s+(?:COLUMN\s+)?(?:IF\s+EXISTS\s+)?['"]?(\w+)['"]?""",
    re.IGNORECASE,
)

_ALTER_COLUMN_TYPE_RE = re.compile(
    """(?:ALTER|MODIFY)\s+(?:COLUMN\s+)?['"]?(\w+)['"]?\s+(?:SET\s+DATA\s+)?TYPE\s+""",
    re.IGNORECASE,
)

_ALTER_COLUMN_NULL_RE = re.compile(
    """(?:ALTER|MODIFY)\s+(?:COLUMN\s+)?['"]?(\w+)['"]?\s+(?:SET\s+(?:NOT\s+)?NULL|DROP\s+NOT\s+NULL)""",
    re.IGNORECASE,
)

_DML_RE = re.compile(
    """^\s*(INSERT|UPDATE|DELETE|MERGE)\s""",
    re.IGNORECASE,
)



def _extract_table_name_from_create(sql: str) -> str:
    m = _CREATE_TABLE_RE.search(sql)
    return m.group(1) if m else "unknown"


def _extract_table_name_from_drop(sql: str) -> str:
    m = _DROP_TABLE_RE.search(sql)
    return m.group(1) if m else "unknown"


def _extract_table_name_from_alter(sql: str) -> str:
    m = _ALTER_TABLE_RE.search(sql)
    return m.group(1) if m else "unknown"


def _parse_alter_table_actions(sql: str, stmt_idx: int) -> list[Action]:
    """Parse an ALTER TABLE statement into individual actions."""
    table_match = _ALTER_TABLE_RE.search(sql)
    table_name = table_match.group(1) if table_match else "unknown"
    actions: list[Action] = []

    alter_body = re.sub(
        """ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?['"]?\w+['"]?\s*,?\s*""",
        "", sql, count=1, flags=re.IGNORECASE,
    )

    parts = _split_outside_parens(alter_body)

    for part in parts:
        part = part.strip().rstrip(";").strip()
        if not part:
            continue

        rename_m = _RENAME_RE.search(part)
        if rename_m:
            if "COLUMN" in part.upper():
                actions.append(Action(statement_text=part, action_type=ActionType.RENAME_COLUMN, target_table=table_name, statement_index=stmt_idx))
            else:
                actions.append(Action(statement_text=part, action_type=ActionType.RENAME_TABLE, target_table=table_name, statement_index=stmt_idx))
            continue

        add_m = _ADD_COLUMN_RE.search(part)
        if add_m and ("ADD" in part.upper()):
            actions.append(Action(statement_text=part, action_type=ActionType.ADD_COLUMN, target_table=table_name, statement_index=stmt_idx))
            continue

        drop_m = _DROP_COLUMN_RE.search(part)
        if drop_m and ("DROP" in part.upper()):
            actions.append(Action(statement_text=part, action_type=ActionType.DROP_COLUMN, target_table=table_name, statement_index=stmt_idx))
            continue

        if _ALTER_COLUMN_TYPE_RE.search(part):
            actions.append(Action(statement_text=part, action_type=ActionType.ALTER_COLUMN_TYPE, target_table=table_name, statement_index=stmt_idx))
            continue

        if _ALTER_COLUMN_NULL_RE.search(part):
            actions.append(Action(statement_text=part, action_type=ActionType.ALTER_COLUMN_NULL, target_table=table_name, statement_index=stmt_idx))
            continue

        if "ADD" in part.upper() and "CONSTRAINT" in part.upper():
            actions.append(Action(statement_text=part, action_type=ActionType.ADD_CONSTRAINT, target_table=table_name, statement_index=stmt_idx))
            continue

        if "DROP" in part.upper() and "CONSTRAINT" in part.upper():
            actions.append(Action(statement_text=part, action_type=ActionType.DROP_CONSTRAINT, target_table=table_name, statement_index=stmt_idx))
            continue

        actions.append(Action(statement_text=part, action_type=ActionType.ALTER_COLUMN_TYPE, target_table=table_name, statement_index=stmt_idx))

    return actions


def _split_outside_parens(sql: str) -> list[str]:
    """Split SQL on commas that are outside parentheses."""
    parts = []
    depth = 0
    current: list[str] = []
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


def parse_migration_sql(sql: str) -> list[Action]:
    """Parse a full migration SQL file into a list of Actions."""
    if not sql or not sql.strip():
        return []

    statements = sqlparse.split(sql)
    actions: list[Action] = []

    for idx, stmt_text in enumerate(statements):
        stmt_text = stmt_text.strip()
        if not stmt_text:
            continue

        stmt_clean = stmt_text.rstrip(";").strip()

        if stmt_clean.startswith("--") or stmt_clean.startswith("/*"):
            continue

        upper = stmt_clean.upper()

        if upper.startswith("CREATE") and "TABLE" in upper:
            table = _extract_table_name_from_create(stmt_clean)
            actions.append(Action(statement_text=stmt_clean, action_type=ActionType.CREATE_TABLE, target_table=table, statement_index=idx))
            continue

        if upper.startswith("DROP") and "TABLE" in upper:
            table = _extract_table_name_from_drop(stmt_clean)
            actions.append(Action(statement_text=stmt_clean, action_type=ActionType.DROP_TABLE, target_table=table, statement_index=idx))
            continue

        if upper.startswith("CREATE") and "INDEX" in upper:
            m = _CREATE_INDEX_RE.search(stmt_clean)
            target = m.group(2) if m else "unknown"
            actions.append(Action(statement_text=stmt_clean, action_type=ActionType.CREATE_INDEX, target_table=target, statement_index=idx))
            continue

        if upper.startswith("DROP") and "INDEX" in upper:
            actions.append(Action(statement_text=stmt_clean, action_type=ActionType.DROP_INDEX, target_table="unknown", statement_index=idx))
            continue

        if upper.startswith("ALTER") and "TABLE" in upper:
            actions.extend(_parse_alter_table_actions(stmt_clean, idx))
            continue

        if _DML_RE.match(stmt_clean):
            actions.append(Action(statement_text=stmt_clean, action_type=ActionType.RAW_DML, target_table="unknown", statement_index=idx))
            continue

        actions.append(Action(statement_text=stmt_clean, action_type=ActionType.RAW_DML, target_table="unknown", statement_index=idx))

    return actions
