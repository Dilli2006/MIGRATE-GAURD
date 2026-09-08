"""Combine classifier results + delta to produce the final verdict."""

from backend.core.schemas import (
    Action, ActionType, SchemaDelta, VerdictResult, VerdictType, Verifiability,
)


def _check_action_against_delta(action: Action, delta: SchemaDelta) -> bool:
    """Return True if the action's effect is visible in the delta."""
    t = action.target_table

    match action.action_type:
        case ActionType.CREATE_TABLE:
            return t in delta.added_tables
        case ActionType.DROP_TABLE:
            return t in delta.dropped_tables
        case ActionType.ADD_COLUMN:
            return t in delta.added_columns and len(delta.added_columns[t]) > 0
        case ActionType.DROP_COLUMN:
            return t in delta.dropped_columns and len(delta.dropped_columns[t]) > 0
        case ActionType.ADD_CONSTRAINT:
            return t in delta.added_constraints and len(delta.added_constraints[t]) > 0
        case ActionType.DROP_CONSTRAINT:
            return t in delta.dropped_constraints and len(delta.dropped_constraints[t]) > 0
        case ActionType.CREATE_INDEX:
            return t in delta.added_indexes and len(delta.added_indexes[t]) > 0
        case ActionType.DROP_INDEX:
            return t in delta.dropped_indexes and len(delta.dropped_indexes[t]) > 0
        case _:
            return False


def compute_verdict(actions: list[Action], delta: SchemaDelta) -> VerdictResult:
    """Produce a VerdictResult from classified actions and a schema delta.

    Rules (from the spec):
      - All verifiable actions match delta  -> APPLIED
      - All verifiable actions absent from delta -> ROLLED_BACK
      - Any NOT_VERIFIABLE action present -> HARD_STOP
    """
    if not actions:
        return VerdictResult(
            verdict=VerdictType.ROLLED_BACK,
            total_actions=0,
            confidence=1.0,
            evidence="No actions found in migration SQL.",
        )

    verifiable = [a for a in actions if a.verifiability == Verifiability.VERIFIABLE]
    non_verifiable = [a for a in actions if a.verifiability == Verifiability.NOT_VERIFIABLE]

    # Hard stop if any non-verifiable action exists
    if non_verifiable:
        return VerdictResult(
            verdict=VerdictType.HARD_STOP,
            total_actions=len(actions),
            verifiable_actions=len(verifiable),
            non_verifiable_actions=len(non_verifiable),
            applied_actions=[],
            unverifiable_actions=non_verifiable,
            delta_summary={
                "added_tables": delta.added_tables,
                "dropped_tables": delta.dropped_tables,
            },
            confidence=0.0,
            evidence=(
                f"{len(non_verifiable)} non-verifiable action(s) detected. "
                f"Manual review required. Non-verifiable: "
                + "; ".join(f"{a.action_type.value} on {a.target_table}" for a in non_verifiable)
            ),
        )

    if not verifiable:
        return VerdictResult(
            verdict=VerdictType.ROLLED_BACK,
            total_actions=len(actions),
            confidence=1.0,
            evidence="No verifiable actions found.",
        )

    # Check each verifiable action against delta
    matched = [a for a in verifiable if _check_action_against_delta(a, delta)]
    unmatched = [a for a in verifiable if not _check_action_against_delta(a, delta)]

    if len(matched) == len(verifiable):
        # All verifiable actions found in delta -> APPLIED
        return VerdictResult(
            verdict=VerdictType.APPLIED,
            total_actions=len(actions),
            verifiable_actions=len(verifiable),
            applied_actions=matched,
            delta_summary={
                "added_tables": delta.added_tables,
                "dropped_tables": delta.dropped_tables,
            },
            confidence=1.0,
            evidence=(
                f"All {len(verifiable)} verifiable action(s) confirmed in schema delta. "
                f"Migration fully applied."
            ),
        )
    elif len(matched) == 0:
        # No verifiable actions found in delta -> ROLLED_BACK
        return VerdictResult(
            verdict=VerdictType.ROLLED_BACK,
            total_actions=len(actions),
            verifiable_actions=len(verifiable),
            delta_summary={
                "added_tables": delta.added_tables,
                "dropped_tables": delta.dropped_tables,
            },
            confidence=1.0,
            evidence=(
                f"None of the {len(verifiable)} verifiable action(s) found in schema delta. "
                f"Migration was rolled back."
            ),
        )
    else:
        # Partial match -> HARD_STOP (shouldn't happen in practice)
        return VerdictResult(
            verdict=VerdictType.HARD_STOP,
            total_actions=len(actions),
            verifiable_actions=len(verifiable),
            applied_actions=matched,
            unverifiable_actions=unmatched,
            delta_summary={
                "added_tables": delta.added_tables,
                "dropped_tables": delta.dropped_tables,
            },
            confidence=0.0,
            evidence=(
                f"Partial match: {len(matched)}/{len(verifiable)} verifiable actions "
                f"found in delta. Inconsistent state -- manual review required."
            ),
        )
