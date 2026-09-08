"""Classify migration SQL — parse into actions then tag verifiability."""

from backend.core.schemas import Action
from backend.core.sql_parser import parse_migration_sql
from backend.core.verifiability_rules import classify_actions


def classify_migration(sql: str) -> list[Action]:
    """Parse a migration SQL string and classify each action's verifiability.

    Returns a list of Action objects with verifiability tags applied,
    including the atomic-statement rule.
    """
    actions = parse_migration_sql(sql)
    return classify_actions(actions)
