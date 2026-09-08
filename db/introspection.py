"""Live schema introspection via information_schema queries."""

from __future__ import annotations

import asyncpg

from backend.core.schemas import SchemaColumn, SchemaState, SchemaTable


async def get_live_schema(pool: asyncpg.Pool) -> SchemaState:
    """Introspect the actual live database schema right now.

    Queries information_schema for tables, columns, constraints, and indexes.
    Returns a complete SchemaState representing S1.
    """
    async with pool.acquire() as conn:
        # 1. Get all user tables
        tables_rows = await conn.fetch(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )

        schema_tables: dict[str, SchemaTable] = {}

        for row in tables_rows:
            table_name = row["table_name"]
            schema_tables[table_name] = SchemaTable(name=table_name)

        # 2. Get all columns
        columns_rows = await conn.fetch(
            """
            SELECT
                c.table_name,
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.character_maximum_length
            FROM information_schema.columns c
            WHERE c.table_schema = 'public'
            ORDER BY c.table_name, c.ordinal_position
            """
        )

        for row in columns_rows:
            table_name = row["table_name"]
            if table_name not in schema_tables:
                continue

            data_type = row["data_type"]
            if row["character_maximum_length"]:
                data_type = f"{data_type}({row['character_maximum_length']})"

            col = SchemaColumn(
                name=row["column_name"],
                data_type=data_type,
                is_nullable=(row["is_nullable"] == "YES"),
                column_default=row["column_default"],
            )
            schema_tables[table_name].columns[col.name] = col

        # 3. Get constraints
        constraints_rows = await conn.fetch(
            """
            SELECT
                tc.table_name,
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = 'public'
            ORDER BY tc.table_name, tc.constraint_name
            """
        )

        for row in constraints_rows:
            table_name = row["table_name"]
            if table_name not in schema_tables:
                continue
            cname = row["constraint_name"]
            if cname not in schema_tables[table_name].constraints:
                schema_tables[table_name].constraints[cname] = {
                    "type": row["constraint_type"],
                    "columns": [],
                }
            schema_tables[table_name].constraints[cname]["columns"].append(
                row["column_name"]
            )

        # 4. Get indexes
        index_rows = await conn.fetch(
            """
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
            """
        )

        for row in index_rows:
            table_name = row["tablename"]
            if table_name not in schema_tables:
                continue
            schema_tables[table_name].indexes[row["indexname"]] = {
                "definition": row["indexdef"],
            }

    return SchemaState(tables=schema_tables)
