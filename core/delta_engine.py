"""Compute the schema delta (Delta = S1 - S0) between two schema states."""

from backend.core.schemas import SchemaDelta, SchemaState


def compute_delta(baseline: SchemaState, live: SchemaState) -> SchemaDelta:
    """Pure set-difference between two schema states.

    Added = in live but not in baseline.
    Dropped = in baseline but not in live.
    """
    baseline_tables = set(baseline.tables.keys())
    live_tables = set(live.tables.keys())

    delta = SchemaDelta(
        added_tables=live_tables - baseline_tables,
        dropped_tables=baseline_tables - live_tables,
    )

    # Column-level diff for tables present in both
    common_tables = baseline_tables & live_tables
    for table_name in common_tables:
        baseline_cols = set(baseline.tables[table_name].columns.keys())
        live_cols = set(live.tables[table_name].columns.keys())

        added_cols = live_cols - baseline_cols
        dropped_cols = baseline_cols - live_cols

        if added_cols:
            delta.added_columns[table_name] = added_cols
        if dropped_cols:
            delta.dropped_columns[table_name] = dropped_cols

        # Constraint-level diff
        baseline_constraints = set(baseline.tables[table_name].constraints.keys())
        live_constraints = set(live.tables[table_name].constraints.keys())
        added_c = live_constraints - baseline_constraints
        dropped_c = baseline_constraints - live_constraints
        if added_c:
            delta.added_constraints[table_name] = added_c
        if dropped_c:
            delta.dropped_constraints[table_name] = dropped_c

        # Index-level diff
        baseline_indexes = set(baseline.tables[table_name].indexes.keys())
        live_indexes = set(live.tables[table_name].indexes.keys())
        added_i = live_indexes - baseline_indexes
        dropped_i = baseline_indexes - live_indexes
        if added_i:
            delta.added_indexes[table_name] = added_i
        if dropped_i:
            delta.dropped_indexes[table_name] = dropped_i

    return delta
