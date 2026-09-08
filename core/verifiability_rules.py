"""Verifiability rules table — which SQL actions can be safely verified via schema delta."""

from backend.core.schemas import Action, ActionType, Verifiability

# Rules table: which action types are safe to verify by schema diff alone.
VERIFIABILITY_RULES: dict[ActionType, Verifiability] = {
    ActionType.CREATE_TABLE: Verifiability.VERIFIABLE,
    ActionType.DROP_TABLE: Verifiability.VERIFIABLE,
    ActionType.ADD_COLUMN: Verifiability.VERIFIABLE,
    ActionType.DROP_COLUMN: Verifiability.VERIFIABLE,
    ActionType.ADD_CONSTRAINT: Verifiability.VERIFIABLE,
    ActionType.DROP_CONSTRAINT: Verifiability.VERIFIABLE,
    ActionType.CREATE_INDEX: Verifiability.VERIFIABLE,
    ActionType.DROP_INDEX: Verifiability.VERIFIABLE,
    ActionType.ALTER_COLUMN_TYPE: Verifiability.NOT_VERIFIABLE,
    ActionType.ALTER_COLUMN_NULL: Verifiability.NOT_VERIFIABLE,
    ActionType.RENAME_TABLE: Verifiability.NOT_VERIFIABLE,
    ActionType.RENAME_COLUMN: Verifiability.NOT_VERIFIABLE,
    ActionType.RAW_DML: Verifiability.NOT_VERIFIABLE,
}


def classify_actions(actions: list[Action]) -> list[Action]:
    """Tag every action with its verifiability, then apply the atomic-statement rule.

    The atomic-statement rule (from the spec): if ANY action inside a single
    ALTER TABLE statement is NOT_VERIFIABLE, the entire statement — and every
    action in it — becomes NOT_VERIFIABLE.  Postgres executes all actions in
    one ALTER TABLE atomically, so we can't reason about individual pieces.
    """
    # Step 1: tag each action individually
    for action in actions:
        action.verifiability = VERIFIABILITY_RULES.get(
            action.action_type, Verifiability.NOT_VERIFIABLE
        )

    # Step 2: group by statement index
    statements: dict[int, list[Action]] = {}
    for action in actions:
        statements.setdefault(action.statement_index, []).append(action)

    # Step 3: atomic-statement rule
    for stmt_actions in statements.values():
        has_non_verifiable = any(
            a.verifiability == Verifiability.NOT_VERIFIABLE for a in stmt_actions
        )
        if has_non_verifiable:
            for a in stmt_actions:
                a.verifiability = Verifiability.NOT_VERIFIABLE

    return actions
