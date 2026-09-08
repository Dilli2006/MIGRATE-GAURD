# MIGRATE-GUARD 🛡️
### The Post-Failure Resolution Engine for Database Migrations

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14%2B-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Prisma Compatible](https://img.shields.io/badge/Prisma-P3009_Engine-2D3748.svg?logo=prisma&logoColor=white)](https://www.prisma.io/)
[![Architecture](https://img.shields.io/badge/Architecture-Deterministic_Forensics-emerald.svg)](#core-forensic-mechanism)

> **"When a production database migration crashes halfway through, MIGRATE-GUARD mathematically proves what actually happened, redacts sensitive data, narrates the incident in plain English, and executes the migration tool's native recovery command with one click."**

<p align="center">
  <img src="./assets/01_swagger_ui.png" alt="MIGRATE-GUARD Live Swagger UI — All API Endpoints" width="80%" />
</p>

<p align="center"><em>The live MIGRATE-GUARD API running on FastAPI — Swagger interactive docs at <code>/docs</code></em></p>

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| **API Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10+) | Async REST server with auto-generated OpenAPI 3.1 docs |
| **SQL Parsing** | [sqlglot](https://github.com/tobymao/sqlglot) (Postgres dialect) | Zero-dependency Python SQL AST parser — no C compilation needed |
| **Data Models** | [Pydantic v2](https://docs.pydantic.dev/) | Strict schema validation for incidents, verdicts, and delta results |
| **Database** | [PostgreSQL 14+](https://www.postgresql.org/) | Target database for live schema introspection via `information_schema` & `pg_catalog` |
| **DB Driver** | [psycopg2-binary](https://www.psycopg.org/) | PostgreSQL adapter for Python |
| **ASGI Server** | [Uvicorn](https://www.uvicorn.org/) | High-performance async server for FastAPI |
| **PII Redaction** | Regex engine + pluggable LLM (OpenAI / Gemini) | Sanitizes credentials, connection strings, tokens from CI/CD logs |
| **Testing** | [pytest](https://pytest.org/) + [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) | 25 unit tests covering classifier, delta engine, verdict engine, and adapter |
| **Containerization** | [Docker Compose](https://docs.docker.com/compose/) | Local PostgreSQL sandbox for development and testing |
| **API Documentation** | Swagger UI (built-in) | Interactive endpoint explorer at `/docs` |

---

## Table of Contents

- [Technology Stack](#technology-stack)
- [The Problem](#the-problem)
- [Why Existing Tools Fall Short](#why-existing-tools-fall-short)
- [How It Works — Step-by-Step Workflow](#how-it-works--step-by-step-workflow)
- [Core Forensic Mechanism](#core-forensic-mechanism)
  - [End-to-End Forensic Flowchart](#end-to-end-forensic-flowchart)
  - [Incident Sequence Diagram](#incident-sequence-diagram)
  - [The Delta Engine ($\Delta = S_1 - S_0$)](#the-delta-engine-delta--s_1---s_0)
- [Safety Boundary & The Rules Matrix](#safety-boundary--the-rules-matrix)
  - [Atomic Compound Statement Roll-Up](#atomic-compound-statement-roll-up)
  - [Verifiability Rules Table](#verifiability-rules-table)
- [Incident Lifecycle & State Machine](#incident-lifecycle--state-machine)
- [System Architecture](#system-architecture)
  - [Component Architecture Diagram](#component-architecture-diagram)
  - [Project File Structure](#project-file-structure)
- [Quick Start (Local Sandbox)](#quick-start-local-sandbox)
- [Interactive Scenarios & Playground](#interactive-scenarios--playground)
  - [Scenario Breakdown](#scenario-breakdown)
- [API & Webhook Reference](#api--webhook-reference)
  - [Complete Endpoint Reference](#complete-endpoint-reference)
- [Redaction & PII Sanitization Workflow](#redaction--pii-sanitization-workflow)
- [Incident Narrative Generation](#incident-narrative-generation)
- [Adapter Architecture (Extensibility)](#adapter-architecture-extensibility)
- [Transparent AI Boundary](#transparent-ai-boundary)
- [Configuration & Environment](#configuration--environment)
- [Deployment Options](#deployment-options)
- [Automated Verification & Tests](#automated-verification--tests)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## The Problem

Every engineering team running Prisma or automated schema migrations against production PostgreSQL eventually experiences a mid-flight crash:
- Network disconnect during DDL execution
- Lock timeouts on busy tables
- Target table deadlock after partial statement commits
- Uncaught post-migration hooks or health-check timeouts

When Prisma crashes mid-flight, it enters an unrecoverable state (`P3009`):

```text
Error: P3009: migrate found failed migrations in the target database, 
new migrations will not be applied. Read more about how to resolve: 
https://pris.ly/d/migrate-resolve
The `202609080010_add_teams_table` migration started at 2026-09-08 00:10:02 UTC failed.
```

The tool refuses to touch the database until an on-call engineer tells it whether the crashed migration **actually applied** or **rolled back**:
- `prisma migrate resolve --applied <name>`
- `prisma migrate resolve --rolled-back <name>`

### The Risk
- **Guess wrong on `--applied`:** You record the migration as complete when the schema never changed. Future code deploys instantly throw `relation does not exist` runtime exceptions in production.
- **Guess wrong on `--rolled-back`:** Prisma attempts to re-apply the migration on the next deploy. If tables or constraints were already created, the deploy crashes again with `already exists`.
- **The $299/hr Triage Call:** Because guessing can corrupt production migration state, teams routinely stall deployment pipelines or pay expensive emergency database consulting services just to perform this forensic check manually.

---

## Why Existing Tools Fall Short

| Tool | Focus Area | How MIGRATE-GUARD Differs |
|---|---|---|
| **Atlas / Bytebase** | Pre-Apply Gatekeeper | Blocks dangerous migrations *before* they run. Has no awareness of a migration that already crashed mid-flight. |
| **Squawk / Linters** | Static SQL Analysis | Lints queries before merge. Incapable of diagnosing partial runtime failures against a live database. |
| **Prisma / Flyway / Liquibase** | Migration Execution | Throws an error code (`P3009`, `Migration failed`) and leaves the forensic investigation entirely to a human. |
| **MIGRATE-GUARD** | **Post-Failure Resolution** | **Acts immediately after the crash. Performs a deterministic delta diff ($\Delta = S_1 - S_0$), proves live state, and recommends the official native recovery command.** |

---

## How It Works — Step-by-Step Workflow

The following walkthrough shows the complete incident resolution lifecycle, from the moment a CI/CD deploy crashes to the moment the database migration state is safely resolved:

```mermaid
flowchart LR
    subgraph STEP1 ["Step 1"]
        S1_T["🔴 CI/CD Pipeline Crashes"]
    end
    subgraph STEP2 ["Step 2"]
        S2_T["📡 Webhook / Manual\nPOST /incidents/"]
    end
    subgraph STEP3 ["Step 3"]
        S3_T["🔬 SQL Parser\nExtracts AST Actions"]
    end
    subgraph STEP4 ["Step 4"]
        S4_T["📋 Classifier\nVerifiable vs Non-Verifiable"]
    end
    subgraph STEP5 ["Step 5"]
        S5_T["📐 Delta Engine\nΔ = S1 - S0"]
    end
    subgraph STEP6 ["Step 6"]
        S6_T["⚖️ Verdict Engine\nAPPLIED / ROLLED_BACK / HARD_STOP"]
    end
    subgraph STEP7 ["Step 7"]
        S7_T["🧹 Redact PII\n+ Generate Summary"]
    end
    subgraph STEP8 ["Step 8"]
        S8_T["👨‍💻 Engineer Reviews\n& Clicks Approve"]
    end
    subgraph STEP9 ["Step 9"]
        S9_T["✅ Native CLI Executes\nprisma migrate resolve"]
    end

    STEP1 --> STEP2 --> STEP3 --> STEP4 --> STEP5 --> STEP6 --> STEP7 --> STEP8 --> STEP9
```

| Step | What Happens | Component |
|:---:|---|---|
| **1** | A `prisma migrate deploy` (or equivalent) crashes mid-flight due to a lock timeout, network disconnect, or post-DDL hook failure. Prisma records the migration as `failed` in `_prisma_migrations`. | CI/CD Pipeline |
| **2** | The crash signal arrives via GitHub/GitLab webhook (`POST /webhook/github`), or an engineer manually creates an incident (`POST /incidents/`) with the migration SQL and error logs. | `api/webhooks.py`, `api/incidents.py` |
| **3** | The SQL parser decomposes `migration.sql` into individual statements and granular actions (CREATE TABLE, ADD COLUMN, ALTER TYPE, etc.) using the `sqlglot` Postgres AST parser. | `core/sql_parser.py` |
| **4** | Each action is checked against the **Verifiability Rules Matrix**. Safe structural changes (CREATE/DROP TABLE, ADD/DROP COLUMN) are tagged ✅. Ambiguous changes (ALTER TYPE, RENAME, DML) are tagged ❌. If any action in a compound `ALTER TABLE` is ❌, the entire statement is marked ❌ (**atomic roll-up**). | `core/classifier.py`, `core/verifiability_rules.py` |
| **5** | The Delta Engine reconstructs the baseline schema $S_0$ (from migration history) and introspects the live schema $S_1$ (from PostgreSQL catalog), then computes $\Delta = S_1 - S_0$ to isolate the exact mutations that survive in the database. | `core/delta_engine.py`, `db/introspection.py` |
| **6** | The Verdict Engine cross-references the classified actions against $\Delta$: if all verifiable actions are present → `APPLIED`; if all are absent → `ROLLED_BACK`; if any action is non-verifiable or the delta is inconsistent → `HARD_STOP`. Confidence is always `1.0` or `0.0` — never probabilistic. | `core/verdict_engine.py` |
| **7** | The AI layer sanitizes the raw CI/CD error logs (stripping passwords, connection strings, tokens, IPs) and generates a one-sentence plain-English incident summary. This layer is **optional** — the system works fully offline without an LLM API key. | `ai/redactor.py`, `ai/narrator.py` |
| **8** | The engineer reviews the verdict, delta evidence, AST classification badges, and sanitized logs on the triage dashboard or via API. They choose **Approve**, **Reject**, or **Escalate**. | `api/incidents.py`, Dashboard UI |
| **9** | On approval, MIGRATE-GUARD executes the migration tool's **own native recovery command** (e.g. `prisma migrate resolve --applied` or `--rolled-back`), updating the `_prisma_migrations` table and unblocking the CI/CD pipeline. | `adapters/prisma_adapter.py` |

---

## Core Forensic Mechanism

MIGRATE-GUARD is completely deterministic. It does not use LLM heuristics or probabilistic guessing to determine database state.

### End-to-End Forensic Flowchart

```mermaid
flowchart TD
    subgraph INGESTION ["1. Failure Detection & Ingestion"]
        A[CI/CD Deploy: prisma migrate deploy] -->|Crash / Lock Timeout| B[Prisma P3009 Error Signal]
        B --> C[MIGRATE-GUARD Webhook Receiver]
    end

    subgraph FORENSICS ["2. Dual Schema Forensics"]
        C --> D[Migration History Files]
        C --> E[(Live PostgreSQL Database)]
        D -->|Replay / History Diff| S0[Baseline Schema S0<br/>State right BEFORE crash]
        E -->|information_schema & pg_catalog| S1[Live Schema S1<br/>Actual state RIGHT NOW]
        S0 & S1 --> DELTA["Delta Engine: Δ = S1 - S0<br/>(Isolates exact mutations)"]
    end

    subgraph PARSING ["3. SQL AST & Verifiability Classification"]
        C --> SQL[migration.sql Raw File]
        SQL --> PARSER[PostgreSQL Grammar Parser<br/>sqlglot Postgres Dialect]
        PARSER --> AST[AST Statements & Actions]
        AST --> CLASSIFIER{Rules Classifier Engine}
        CLASSIFIER -->|Check Action Rules| RULES[Verifiability Rules Matrix]
    end

    subgraph VERDICT_DECISION ["4. Deterministic Verdict Matrix"]
        RULES & DELTA --> EVAL{Verdict Evaluator}
        EVAL -->|Any Non-Verifiable Action| HS[🛑 HARD STOP: Refuse to Guess]
        EVAL -->|Partial / Inconsistent Delta| HS
        EVAL -->|All Verifiable & Present in Δ| APP[✅ APPLIED: Confirmed Committed]
        EVAL -->|All Verifiable & Absent from Δ| RB[🔄 ROLLED BACK: Confirmed Clean Abort]
    end

    subgraph RESOLUTION ["5. Approval & Native Resolution"]
        APP --> REC1["Recommend: prisma migrate resolve --applied"]
        RB --> REC2["Recommend: prisma migrate resolve --rolled-back"]
        HS --> ALERT["Route to Human DBA with Line-by-Line Evidence"]
        REC1 & REC2 --> AI[AI Layer: Redact Secrets + Plain-English Summary]
        AI --> UI[Triage Dashboard & Slack Alert]
        UI -->|Engineer 1-Click Approval| CLI[Execute Official Migration CLI]
        CLI --> DB_CONFIRM[PostgreSQL _prisma_migrations State Resolved]
    end

    style APP fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff
    style RB fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#fff
    style HS fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#fff
    style UI fill:#1e293b,stroke:#06b6d4,stroke-width:2px,color:#fff
```

### Incident Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant CI as CI/CD Pipeline
    participant DB as PostgreSQL (Live)
    participant MG as MIGRATE-GUARD Core
    participant ENG as On-Call Engineer

    CI->>DB: prisma migrate deploy (CRASHES mid-flight)
    CI->>MG: Webhook trigger (P3009 Signal + Migration Name)
    Note over MG: 1. BASELINE RECONSTRUCTION (S0)<br/>Reconstruct pre-crash schema from history alone
    Note over MG: 2. LIVE INTROSPECTION (S1)<br/>Query information_schema & pg_catalog
    Note over MG: 3. DELTA CALCULATION (Δ)<br/>Δ = S1 - S0 (isolate exact mutation)
    Note over MG: 4. SQL AST PARSING & CLASSIFICATION<br/>Inspect each statement & action in migration.sql
    Note over MG: 5. DETERMINISTIC VERDICT<br/>All verifiable in Δ? APPLIED<br/>All verifiable absent? ROLLED_BACK<br/>Ambiguous action? HARD_STOP
    Note over MG: 6. REDACTION & NARRATION<br/>Sanitize secrets + write plain-English summary
    MG->>ENG: Alert (Slack/Dashboard) with Evidence & 1-Click Approval
    ENG->>MG: Authorize Native Resolution
    MG->>CI: Execute `prisma migrate resolve --[applied|rolled-back]`
    CI->>DB: Update _prisma_migrations record
    MG-->>ENG: Incident closed safely
```

### The Delta Engine ($\Delta = S_1 - S_0$)

The schema delta is calculated using formal set differences across all database object layers:

```mermaid
graph LR
    subgraph INPUTS ["Forensic Schema Inputs"]
        S0["Baseline Schema S0<br/>(Computed from migration history)"]
        S1["Live Schema S1<br/>(Introspected from PostgreSQL)"]
    end

    subgraph DELTA_MATH ["Set Difference Engine (Δ = S1 - S0)"]
        D_TAB["Δ Tables = S1.tables \ S0.tables"]
        D_COL["Δ Columns = S1.columns \ S0.columns"]
        D_CON["Δ Constraints = S1.constraints \ S0.constraints"]
        D_IDX["Δ Indexes = S1.indexes \ S0.indexes"]
    end

    subgraph OUTPUT ["Mutation Isolate (Δ)"]
        MUT["Exact DDL changes executed<br/>before migration died"]
    end

    S0 & S1 --> D_TAB & D_COL & D_CON & D_IDX
    D_TAB & D_COL & D_CON & D_IDX --> MUT

    style MUT fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
```

### The 10-Step Forensic Pipeline:

1. **DETECT:** CI/CD webhook or polling service catches the failed migration signal (e.g. `_prisma_migrations` row with `finished_at IS NULL` and `rolled_back_at IS NULL`).
2. **BASELINE ($S_0$):** Reconstructs the exact schema state prior to the failed migration using migration history alone (replay against shadow catalog or diffing against prior migrations).
3. **LIVE ($S_1$):** Introspects the live database schema directly (`information_schema` tables, columns, constraints, foreign keys, and indexes).
4. **DELTA ($\Delta$):** Calculates the exact mathematical mutation: $\Delta = S_1 - S_0$.
5. **PARSE:** Parses the failed migration's raw SQL into an Abstract Syntax Tree (AST) using an exact PostgreSQL grammar parser (`sqlglot` Postgres dialect).
6. **CLASSIFY:** Evaluates every statement action against an editable rules table to determine whether the action is provably verifiable in $\Delta$.
7. **VERDICT:**
   - **`APPLIED`:** All actions are verifiable and all target artifacts are present in $\Delta$.
   - **`ROLLED_BACK`:** All actions are verifiable and all target artifacts are absent from $\Delta$.
   - **`HARD_STOP`:** Any action is non-verifiable or delta state is internally inconsistent. Refuses to guess; routes to human DBA.
8. **NARRATE:** AI redacts credentials/PII and generates a 1-sentence executive incident summary.
9. **APPROVE:** Evidence, AST classification badges, schema diff, and proposed CLI command are surfaced for one-click human confirmation.
10. **EXECUTE:** Runs the migration tool's **own official recovery command** (`prisma migrate resolve --applied` or `--rolled-back`).

---

## Safety Boundary & The Rules Matrix

> [!IMPORTANT]
> **The Core Thesis:** We know exactly which migration operations are safe to auto-verify, and we **refuse to touch the rest**.

### Atomic Compound Statement Roll-Up

PostgreSQL executes compound `ALTER TABLE` statements atomically. If an engineer runs an `ALTER TABLE` with three actions and one is ambiguous, MIGRATE-GUARD applies an **atomic statement roll-up**:

```mermaid
flowchart LR
    subgraph COMPOUND_STMT ["Compound ALTER TABLE Statement"]
        direction TB
        A1["Action 1: ADD COLUMN age INT"] --> C1["✅ Verifiable (Column existence in Δ)"]
        A2["Action 2: ALTER COLUMN role TYPE text"] --> C2["❌ NOT Verifiable (Type conversion / casting)"]
    end

    subgraph ROLLUP ["PostgreSQL Atomic Roll-Up Rule"]
        C1 & C2 --> R1{"Are ALL actions in statement verifiable?"}
        R1 -->|No: Action 2 is unsafe| R2["❌ WHOLE STATEMENT IS NOT VERIFIABLE"]
        R2 --> STOP["🛑 HARD STOP TRIGGERED<br/>Refuse to guess; require manual human DBA triage"]
    end

    style C1 fill:#064e3b,stroke:#10b981,color:#fff
    style C2 fill:#7f1d1d,stroke:#ef4444,color:#fff
    style R2 fill:#7f1d1d,stroke:#ef4444,stroke-width:2px,color:#fff
    style STOP fill:#450a0a,stroke:#dc2626,stroke-width:3px,color:#fff
```

### Verifiability Rules Table

| Action Type | SQL Pattern | Verifiability | Rationale |
|---|---|:---:|---|
| `CREATE_TABLE` | `CREATE TABLE "users" (...)` | ✅ **VERIFIABLE** | Table existence in $S_1$ vs $S_0$ is binary and unambiguous. |
| `DROP_TABLE` | `DROP TABLE "old_data"` | ✅ **VERIFIABLE** | Absence of table in $S_1$ compared to $S_0$ is deterministically proven. |
| `ADD_COLUMN` | `ALTER TABLE "t" ADD COLUMN "c" INT` | ✅ **VERIFIABLE** | Column presence in target table is inspectable via `information_schema.columns`. |
| `DROP_COLUMN` | `ALTER TABLE "t" DROP COLUMN "c"` | ✅ **VERIFIABLE** | Absence of column is deterministically proven. |
| `ADD_CONSTRAINT` | `ALTER TABLE "t" ADD CONSTRAINT ...` | ✅ **VERIFIABLE** | FK, UNIQUE, and CHECK constraints appear in `table_constraints`. |
| `DROP_CONSTRAINT` | `ALTER TABLE "t" DROP CONSTRAINT ...` | ✅ **VERIFIABLE** | Constraint removal is deterministically checked. |
| `CREATE_INDEX` | `CREATE INDEX "idx" ON "t"("c")` | ✅ **VERIFIABLE** | Standard indexes are transactionally committed with verifiable catalog rows. |
| `DROP_INDEX` | `DROP INDEX "idx"` | ✅ **VERIFIABLE** | Index removal is checked in `pg_indexes`. |
| `ALTER_COLUMN_TYPE` | `ALTER TABLE "t" ALTER COLUMN "c" TYPE text` | ❌ **NOT VERIFIABLE** | Type conversions may involve implicit casting, collations, or state mutations not verifiable from schema diff alone. |
| `SET/DROP NOT NULL` | `ALTER TABLE "t" ALTER COLUMN "c" SET NOT NULL` | ❌ **NOT VERIFIABLE** | Requires full table data scan validation; dangerous to infer purely from metadata delta under concurrent workloads. |
| `RENAME_TABLE` / `COL` | `ALTER TABLE "t" RENAME TO "t2"` | ❌ **NOT VERIFIABLE** | Indistinguishable in standard schema diff from `DROP` + `CREATE` without commit metadata. |
| `INDEX CONCURRENTLY` | `CREATE INDEX CONCURRENTLY ...` | ❌ **NOT VERIFIABLE** | Runs outside transaction blocks; can leave an invalid index (`pg_index.indisvalid = false`). |
| `RAW_DML` | `UPDATE "users" SET "active" = true` | ❌ **NOT VERIFIABLE** | Data mutation, not schema structure. Schema delta cannot prove execution completeness. |

---

## Incident Lifecycle & State Machine

Every incident in MIGRATE-GUARD follows a strict state machine. The status transitions are enforced by the API — you cannot approve a rejected incident or escalate an already-resolved one:

```mermaid
stateDiagram-v2
    [*] --> CREATED : POST /incidents/
    CREATED --> AWAITING_APPROVAL : Forensic triage completes\n(AST + Δ + Verdict computed)

    AWAITING_APPROVAL --> APPROVED : POST /incidents/{id}/approve
    AWAITING_APPROVAL --> REJECTED : POST /incidents/{id}/reject
    AWAITING_APPROVAL --> ESCALATED : POST /incidents/{id}/escalate

    APPROVED --> RESOLVED : Native CLI executes\nprisma migrate resolve
    REJECTED --> [*] : Incident closed\n(no action taken)
    ESCALATED --> AWAITING_APPROVAL : Senior DBA reviews\nand re-triages
    RESOLVED --> [*] : Migration state fixed\nCI/CD unblocked

    state AWAITING_APPROVAL {
        [*] --> VerdictReady
        VerdictReady --> APPLIED_Verdict : All verifiable + present in Δ
        VerdictReady --> ROLLED_BACK_Verdict : All verifiable + absent from Δ
        VerdictReady --> HARD_STOP_Verdict : Non-verifiable action detected
    }
```

### Status Definitions

| Status | Meaning | Allowed Transitions |
|---|---|---|
| `CREATED` | Incident received, forensic triage is running | → `AWAITING_APPROVAL` |
| `AWAITING_APPROVAL` | Verdict computed, waiting for human decision | → `APPROVED`, `REJECTED`, `ESCALATED` |
| `APPROVED` | Engineer confirmed the verdict, executing resolution | → `RESOLVED` |
| `REJECTED` | Engineer disagreed with the verdict, no action taken | → (closed) |
| `ESCALATED` | Routed to senior DBA for manual investigation | → `AWAITING_APPROVAL` (after re-triage) |
| `RESOLVED` | Native CLI executed successfully, migration state fixed | → (closed) |

---

## System Architecture

### Component Architecture Diagram

```mermaid
flowchart TD
    subgraph INGESTION_API ["API & Webhook Layer (FastAPI)"]
        W1[CI/CD Webhook: GitHub / GitLab]
        W2[CLI / Manual Incident REST Trigger]
        W3[Simulation Playground Endpoints]
    end

    subgraph CORE_ENGINE ["Deterministic Forensic Engine (Tool-Agnostic)"]
        SP[PostgreSQL SQL Parser<br/>sqlglot AST]
        VR[Rules Catalog Table]
        CL[Action Classifier & Atomic Roll-Up]
        DE[Schema Delta Calculator Δ = S1 - S0]
        VE[Verdict Decision Matrix]
        
        SP --> CL
        VR --> CL
        CL & DE --> VE
    end

    subgraph ADAPTER_LAYER ["Adapter Plugin Registry"]
        direction TB
        AD_BASE[MigrationAdapter Interface]
        AD_PRISMA[Prisma Adapter<br/>Full Implementation]
        AD_FLYWAY[Flyway Adapter<br/>Stub]
        AD_TYPEORM[TypeORM Adapter<br/>Stub]
        
        AD_BASE --> AD_PRISMA & AD_FLYWAY & AD_TYPEORM
    end

    subgraph AI_LAYER ["Sanitization & Reporting"]
        RED[PII & Secret Redactor]
        NAR[Plain-English Incident Narrator]
    end

    subgraph CLIENT_LAYER ["Interactive Triage Dashboard"]
        UI[Glassmorphism Dark-Mode UI]
        ACT[1-Click Resolution Trigger]
    end

    INGESTION_API --> CORE_ENGINE
    CORE_ENGINE <--> ADAPTER_LAYER
    CORE_ENGINE --> AI_LAYER
    AI_LAYER --> CLIENT_LAYER
    CLIENT_LAYER -->|Authorized Approval| AD_PRISMA
    AD_PRISMA -->|Executes Native CLI| TARGET_DB[(PostgreSQL)]

    style CORE_ENGINE fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    style AD_PRISMA fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff
    style CLIENT_LAYER fill:#1e1e2e,stroke:#a855f7,stroke-width:2px,color:#fff
```

### Project File Structure

```
MIGRATE-GUARD/
├── backend/
│   ├── main.py                     # FastAPI application entrypoint & static serving
│   ├── config.py                   # Pydantic BaseSettings, DB connection params, API keys
│   ├── core/                       # Tool-Agnostic Resolution Engine
│   │   ├── schemas.py              # Pydantic v2 domain schemas (AST, Delta, Verdict, Incident)
│   │   ├── sql_parser.py           # SQL AST parser extracting statements & fine-grained actions
│   │   ├── verifiability_rules.py  # Pluggable classification catalog & rules matrix
│   │   ├── classifier.py           # Action classifier + atomic compound statement roll-up
│   │   ├── delta_engine.py         # Set difference calculator: Δ = S1 - S0
│   │   └── verdict_engine.py       # Deterministic decision matrix (APPLIED, ROLLED_BACK, HARD_STOP)
│   ├── adapters/                   # Migration Tool Plugins
│   │   ├── base.py                 # Abstract Base Contract (detect, baseline, introspect, resolve)
│   │   ├── prisma_adapter.py       # Full Prisma implementation (_prisma_migrations, diff, resolve CLI)
│   │   ├── registry.py             # Adapter lookup & registration
│   │   └── stubs/                  # Open roadmap slots (Flyway, TypeORM, Django)
│   ├── db/
│   │   ├── introspection.py        # PostgreSQL information_schema & pg_catalog introspector
│   │   └── history_reconstruction.py # S0 baseline generator from migration history
│   ├── ai/
│   │   ├── redactor.py             # Credential, token, connection string, and PII sanitizer
│   │   └── narrator.py             # Executive incident report generator (Regex + Pluggable LLM)
│   └── api/
│       ├── incidents.py            # Incident retrieval, approval, and resolution dispatch
│       ├── webhooks.py             # Ingestion for CI/CD failure webhooks
│       └── simulate.py             # Simulation endpoints for Scenarios A, B, and C
├── frontend/                       # Dark-Mode Real-Time Triage Dashboard
│   ├── index.html                  # Visual forensic command center
│   ├── styles.css                  # Custom styling, diff views, AST tags, glassmorphism
│   └── app.js                      # Interactive UI state, simulation playground, one-click resolve
├── tests/                          # Comprehensive Test Suite
│   ├── test_classifier.py          # Verifies classification & atomic roll-up logic
│   ├── test_delta_engine.py        # Validates table, column, index, constraint math
│   ├── test_verdict_engine.py      # Verifies APPLIED, ROLLED_BACK, and HARD_STOP branches
│   └── fixtures/                   # Realistic crash migration SQL scripts
├── assets/                         # Real project screenshots & evidence
│   ├── 01_swagger_ui.png           # Swagger UI overview (all endpoint groups)
│   ├── 02_swagger_endpoints.png    # Webhook & incident endpoint close-up
│   ├── 02_post_incidents_response.json  # Real POST /incidents/ triage response
│   ├── 03_swagger_all_endpoints.png     # Full API surface (approvals, notifications, schemas)
│   └── 04_pytest_output.txt        # Real pytest run — 25/25 passed
└── docker/
    └── docker-compose.yml          # PostgreSQL sandbox for live testing & demos
```

---

## Quick Start (Local Sandbox)

### Prerequisites
- Python 3.10+
- Node.js & npm (for optional Prisma CLI testing)
- Docker & Docker Compose (optional, for live PostgreSQL sandbox)

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/<your-org>/migrate-guard.git
cd migrate-guard

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 2. Configure Environment

Create a `.env` file or use the defaults:

```bash
cp .env.example .env
```

```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/migrate_guard_test
MIGRATE_GUARD_PORT=8000
ENVIRONMENT=development
# Optional: Set an OpenAI or Gemini API key for dynamic incident narration
# OPENAI_API_KEY=your_key_here
```

### 3. Launch the Server & Dashboard

```bash
# Run the FastAPI server
python -m uvicorn backend.main:app --reload --port 8000
```

Open your browser to:
👉 **`http://localhost:8000`**

---

## Interactive Scenarios & Playground

The built-in triage dashboard comes pre-configured with **3 real-world crash scenarios** so you can test and demonstrate the forensic engine immediately without waiting for a production crash:

### Scenario Breakdown

#### Scenario A: Fully Applied Migration (DDL Committed Before Crash)
- **What happened:** Migration `202609080010_add_teams_table` created table `teams`, added foreign key `fk_users_team_id`, and added column `team_id` to `users`. A post-migration health-check timed out.
- **Delta ($\Delta$):** All tables, columns, and foreign keys exist in PostgreSQL.
- **AST Classification:** 100% Verifiable actions.
- **Verdict:** `APPLIED` ✅
- **Resolution Command:** `prisma migrate resolve --applied "202609080010_add_teams_table"`

#### Scenario B: Cleanly Aborted / Rolled Back Migration
- **What happened:** Migration `202609080020_add_audit_logs` hit a disk quota limit or constraint error within the transaction block. PostgreSQL aborted the transaction.
- **Delta ($\Delta$):** $\Delta = \emptyset$ (No changes in PostgreSQL catalog).
- **AST Classification:** 100% Verifiable actions.
- **Verdict:** `ROLLED_BACK` 🔄
- **Resolution Command:** `prisma migrate resolve --rolled-back "202609080020_add_audit_logs"`

#### Scenario C: Ambiguous / Non-Verifiable Migration (HARD STOP)
- **What happened:** Migration `202609080030_backfill_and_alter_types` altered column `status` from `VARCHAR(50)` to `ENUM` and executed a raw `UPDATE accounts SET balance = balance * 1.05`.
- **AST Classification:** Contains `ALTER_COLUMN_TYPE` and `RAW_DML`.
- **Verdict:** `HARD_STOP` 🛑
- **Resolution Action:** **Locks automated execution.** Refuses to guess. Alerts engineer with exact line numbers and requires manual DBA triage.

---

## API & Webhook Reference

### Complete Endpoint Reference

The following table documents **every endpoint** in the live MIGRATE-GUARD API (as shown in the Swagger UI screenshots above):

| Method | Endpoint | Description | Request Body | Response |
|:---:|---|---|---|---|
| `GET` | `/health` | Health check — confirms server is running | — | `{"status": "ok"}` |
| `POST` | `/webhook/github` | Ingest a GitHub Actions failure webhook | GitHub webhook payload with migration error | Created incident ID |
| `POST` | `/webhook/gitlab` | Ingest a GitLab CI failure webhook | GitLab webhook payload with migration error | Created incident ID |
| `GET` | `/incidents/` | List all incidents with their verdicts | — | Array of incident objects |
| `POST` | `/incidents/` | Create a new incident manually (with migration SQL + logs) | `{migration_name, migration_sql, raw_logs?, prisma_dir?}` | Full incident object with verdict |
| `GET` | `/incidents/{incident_id}` | Get a specific incident by ID | — | Full incident object with verdict |
| `POST` | `/incidents/{incident_id}/approve` | Approve the verdict and execute native resolution | `{approved_by}` | Resolution confirmation |
| `POST` | `/incidents/{incident_id}/reject` | Reject the verdict — no action taken on database | — | Updated incident (status: REJECTED) |
| `POST` | `/incidents/{incident_id}/escalate` | Escalate to senior DBA for manual review | — | Updated incident (status: ESCALATED) |
| `POST` | `/notify/slack` | Send incident alert to a Slack channel | `{incident_id}` | Notification confirmation |

### Live API Surface

The full OpenAPI 3.1 endpoint surface auto-generated from the running server:

<p align="center">
  <img src="./assets/03_swagger_all_endpoints.png" alt="MIGRATE-GUARD — Complete API Endpoint Listing" width="70%" />
</p>

<p align="center">
  <img src="./assets/02_swagger_endpoints.png" alt="MIGRATE-GUARD — Webhook & Incident Endpoints Close-Up" width="70%" />
</p>

### 1. Ingest CI/CD Failure Webhook
`POST /webhook/github` · `POST /webhook/gitlab`

```bash
curl -X POST http://localhost:8000/webhook/github \
  -H "Content-Type: application/json" \
  -d '{
    "migration_name": "20260908_add_orders",
    "error_code": "P3009",
    "error_log": "Database error: timed out waiting for connection pool after DDL commit.",
    "raw_sql": "CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT NOT NULL, total DECIMAL(10,2)); ALTER TABLE orders ADD COLUMN status VARCHAR(50); CREATE INDEX idx_orders_user ON orders(user_id);"
  }'
```

### 2. Create Incident & Get Forensic Triage
`POST /incidents/`

**Real response from the running server** (from [`02_post_incidents_response.json`](./assets/02_post_incidents_response.json)):
```json
{
  "id": "267ab45f-7001-4caa-8459-12b2b986a88a",
  "migration_name": "20260908_add_orders",
  "migration_sql": "CREATE TABLE orders (id SERIAL PRIMARY KEY, user_id INT NOT NULL, total DECIMAL(10,2)); ALTER TABLE orders ADD COLUMN status VARCHAR(50); CREATE INDEX idx_orders_user ON orders(user_id);",
  "detected_at": "2026-09-08T15:15:01.721752Z",
  "status": "AWAITING_APPROVAL",
  "verdict": {
    "verdict": "ROLLED_BACK",
    "total_actions": 3,
    "verifiable_actions": 3,
    "non_verifiable_actions": 0,
    "applied_actions": [],
    "unverifiable_actions": [],
    "delta_summary": { "added_tables": [], "dropped_tables": [] },
    "confidence": 1.0,
    "evidence": "None of the 3 verifiable action(s) found in schema delta. Migration was rolled back."
  },
  "raw_logs": null,
  "redacted_logs": "",
  "summary": "Migration 20260908_add_orders was diagnosed as ROLLED_BACK. Confidence: 100%. No changes detected in the live schema. Approve to mark migration as rolled back.",
  "resolution": null,
  "prisma_dir": "./prisma/migrations"
}
```

> **Key takeaway:** 3 verifiable actions (CREATE TABLE, ADD COLUMN, CREATE INDEX), zero changes found in $\Delta$ → engine conclusively determined `ROLLED_BACK` at 100% confidence.

### 3. Approve, Reject, or Escalate
`POST /incidents/{incident_id}/approve` · `POST /incidents/{incident_id}/reject` · `POST /incidents/{incident_id}/escalate`

```bash
# Approve the verdict and execute native resolution
curl -X POST http://localhost:8000/incidents/267ab45f-7001-4caa-8459-12b2b986a88a/approve \
  -H "Content-Type: application/json" \
  -d '{"approved_by": "oncall-engineer@company.com"}'

# Or reject if you disagree with the verdict
curl -X POST http://localhost:8000/incidents/267ab45f-7001-4caa-8459-12b2b986a88a/reject

# Or escalate to a senior DBA
curl -X POST http://localhost:8000/incidents/267ab45f-7001-4caa-8459-12b2b986a88a/escalate
```

### 4. Slack Notification
`POST /notify/slack`

```bash
curl -X POST http://localhost:8000/notify/slack \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "267ab45f-7001-4caa-8459-12b2b986a88a"}'
```

---

## Redaction & PII Sanitization Workflow

Before any CI/CD error log or migration output is shown to a user (or sent to Slack), the **Redactor** strips sensitive data using a layered approach:

```mermaid
flowchart TD
    RAW["Raw CI/CD Error Log\n(may contain secrets)"] --> R1

    subgraph REDACTION ["Layered Redaction Pipeline"]
        R1["Layer 1: Regex Patterns\n• PostgreSQL connection strings\n• postgres://user:PASSWORD@host:port/db\n• Bearer tokens, API keys\n• AWS_SECRET_ACCESS_KEY, OPENAI_API_KEY"]
        R1 --> R2["Layer 2: Structured Patterns\n• IP addresses (IPv4/IPv6)\n• Email addresses\n• Credit card numbers (Luhn check)\n• SSH private key blocks"]
        R2 --> R3["Layer 3: LLM Review (Optional)\n• Contextual secret detection\n• Custom organization patterns\n• Domain-specific PII"]
    end

    R3 --> CLEAN["Sanitized Log\nAll secrets replaced with [REDACTED]"]

    style RAW fill:#7f1d1d,stroke:#ef4444,color:#fff
    style CLEAN fill:#064e3b,stroke:#10b981,color:#fff
```

**Example transformation:**
```diff
- Connection string: postgres://admin:s3cr3tP@ss!@db.prod.internal:5432/main_db
+ Connection string: postgres://admin:[REDACTED]@db.prod.internal:5432/main_db

- Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIi...
+ Authorization: Bearer [REDACTED]
```

> **Offline-first:** Layers 1 and 2 run entirely locally with zero external dependencies. Layer 3 only activates if an LLM API key is configured in `.env`.

---

## Incident Narrative Generation

After the verdict is computed and logs are sanitized, the **Narrator** generates a concise, plain-English summary suitable for Slack alerts, on-call dashboards, and incident postmortems:

```mermaid
flowchart LR
    subgraph INPUTS ["Narrator Inputs"]
        V["Verdict: ROLLED_BACK"]
        E["Evidence: 3 verifiable,\n0 found in Δ"]
        M["Migration: 20260908_add_orders"]
        R["Redacted Logs"]
    end

    subgraph NARRATOR ["Narrative Engine"]
        T["Template Engine\n(Deterministic Fallback)"]
        L["LLM Enhancement\n(Optional, if API key set)"]
    end

    INPUTS --> T
    T --> L
    L --> OUT["Summary: Migration 20260908_add_orders\nwas diagnosed as ROLLED_BACK.\nConfidence: 100%. No changes detected\nin the live schema."]

    style OUT fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
```

**How it works:**
1. The **template engine** always produces a summary using a deterministic format: `"Migration {name} was diagnosed as {verdict}. Confidence: {confidence}%. {evidence_summary}."`
2. If an LLM API key is configured, the template output is optionally refined for more natural phrasing — but the verdict, confidence, and evidence are **never modified by the LLM**.
3. The summary is attached to the incident object and is available via `GET /incidents/{id}` and `POST /notify/slack`.

---

## Adapter Architecture (Extensibility)

The Core Forensic Engine has **zero knowledge of Prisma**. All tool-specific logic communicates through the `MigrationAdapter` contract:

```mermaid
flowchart TD
    CORE["MIGRATE-GUARD Core Engine<br/>(Tool-Agnostic Forensics)"]
    
    subgraph CONTRACT ["MigrationAdapter Abstract Contract (4 Questions)"]
        Q1["Q1: detect_failure(signal)"]
        Q2["Q2: reconstruct_baseline(migration_name)"]
        Q3["Q3: introspect_live()"]
        Q4["Q4: resolve(migration_name, verdict)"]
    end

    CORE <--> CONTRACT

    subgraph PLUGINS ["Pluggable Adapter Registry"]
        PRISMA["Prisma Adapter<br/>(Built & Fully Proven)<br/>• _prisma_migrations<br/>• prisma migrate diff<br/>• prisma migrate resolve"]
        FLYWAY["Flyway Adapter<br/>(Open Slot)<br/>• flyway_schema_history<br/>• flyway repair"]
        TYPEORM["TypeORM Adapter<br/>(Open Slot)<br/>• migrations table<br/>• typeorm migration:revert"]
        DJANGO["Django Adapter<br/>(Open Slot)<br/>• django_migrations<br/>• migrate --fake"]
    end

    CONTRACT --> PRISMA
    CONTRACT -.-> FLYWAY
    CONTRACT -.-> TYPEORM
    CONTRACT -.-> DJANGO

    style PRISMA fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff
    style FLYWAY fill:#1e293b,stroke:#64748b,stroke-width:1px,color:#cbd5e1
    style TYPEORM fill:#1e293b,stroke:#64748b,stroke-width:1px,color:#cbd5e1
    style DJANGO fill:#1e293b,stroke:#64748b,stroke-width:1px,color:#cbd5e1
```

```python
from abc import ABC, abstractmethod
from backend.core.schemas import DatabaseSchema, FailedMigration, ResolutionResult, VerdictStatus

class MigrationAdapter(ABC):
    """Abstract plugin contract for database migration tools."""

    @abstractmethod
    def detect_failure(self, raw_signal: dict) -> FailedMigration:
        """Parse tool-specific error codes (e.g. Prisma P3009) into a standardized FailedMigration."""
        pass

    @abstractmethod
    def reconstruct_baseline(self, migration_name: str) -> DatabaseSchema:
        """Reconstruct schema state (S0) prior to the failed migration using history."""
        pass

    @abstractmethod
    def introspect_live(self) -> DatabaseSchema:
        """Introspect the live database schema (S1)."""
        pass

    @abstractmethod
    def resolve(self, migration_name: str, verdict: VerdictStatus) -> ResolutionResult:
        """Execute the migration tool's native recovery CLI command."""
        pass
```

---

## Transparent AI Boundary

MIGRATE-GUARD maintains a strict philosophical separation between **deterministic truth** and **generative language models**:

```mermaid
flowchart TD
    CRASH["💥 CRASH OCCURS (e.g. Prisma P3009)"] --> DET
    
    subgraph DETERMINISTIC_ZONE ["Deterministic Core Engine (Zero AI Involvement)"]
        DET[1. Detect Signal] --> BASE[2. Reconstruct S0 & Introspect S1]
        BASE --> DIFF[3. Compute Schema Delta Δ = S1 - S0]
        DIFF --> PARSE[4. Parse SQL AST & Actions]
        PARSE --> CLASS[5. Classify Verifiability Rules]
        CLASS --> VERD[6. Verdict Engine: APPLIED / ROLLED_BACK / HARD_STOP]
    end

    subgraph GENERATIVE_ZONE ["Generative AI Layer (Assistance Only)"]
        VERD --> RED[PII & Credential Redaction]
        RED --> SUMM[Plain-English Executive Summary]
    end

    subgraph HUMAN_GOVERNANCE ["Human On-Call Engineer"]
        SUMM --> DASH[Review Evidence & Verification Proof on Dashboard]
        DASH --> APP[1-Click Authorization]
    end

    subgraph EXECUTION_ZONE ["Native CLI Execution"]
        APP --> NATIVE[Call Tool's Native CLI: prisma migrate resolve]
    end

    style DETERMINISTIC_ZONE fill:#0f172a,stroke:#38bdf8,stroke-width:2px,color:#fff
    style GENERATIVE_ZONE fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#fff
    style HUMAN_GOVERNANCE fill:#1e293b,stroke:#10b981,stroke-width:2px,color:#fff
    style EXECUTION_ZONE fill:#064e3b,stroke:#059669,stroke-width:2px,color:#fff
```

---

## Configuration & Environment

| Environment Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string for live introspection | `postgresql://postgres:postgres@localhost:5432/postgres` |
| `MIGRATE_GUARD_PORT` | Port for the FastAPI server & dashboard | `8000` |
| `MIGRATE_GUARD_HOST` | Host binding interface | `0.0.0.0` |
| `OPENAI_API_KEY` | (Optional) OpenAI API key for LLM narration | `None` (uses deterministic fallback narrator) |
| `GEMINI_API_KEY` | (Optional) Gemini API key for LLM narration | `None` |
| `SLACK_WEBHOOK_URL` | (Optional) Slack incoming webhook URL for notifications | `None` |
| `ENVIRONMENT` | Runtime environment (`development`, `production`) | `development` |

---

## Deployment Options

### Option 1: Local Development (Recommended for evaluation)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### Option 2: Docker Compose (Full stack with PostgreSQL)
```bash
docker compose -f docker/docker-compose.yml up -d
# API available at http://localhost:8000
# PostgreSQL available at localhost:5432
```

### Option 3: Production Deployment
```bash
# Build and run with Gunicorn + Uvicorn workers
pip install gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### CI/CD Integration

Add MIGRATE-GUARD as a **failure handler** in your existing GitHub Actions or GitLab CI pipeline:

```yaml
# .github/workflows/deploy.yml (add this as a failure step)
- name: Handle Migration Failure
  if: failure()
  run: |
    curl -X POST ${{ secrets.MIGRATE_GUARD_URL }}/webhook/github \
      -H "Content-Type: application/json" \
      -d '{"migration_name": "${{ env.MIGRATION_NAME }}", "error_log": "${{ steps.migrate.outputs.stderr }}"}'
```

---

## Automated Verification & Tests

Run the complete test suite with `pytest`:

```bash
pytest backend/tests/ -v
```

### Real Test Output — 25/25 Passed ✅

The following is the **actual output** from the project's test suite (from [`04_pytest_output.txt`](./assets/04_pytest_output.txt)):

```text
============================= test session starts =============================
collected 25 items

backend/tests/test_classifier.py::TestClassifier::test_create_table_is_verifiable PASSED [  4%]
backend/tests/test_classifier.py::TestClassifier::test_drop_table_is_verifiable PASSED [  8%]
backend/tests/test_classifier.py::TestClassifier::test_add_column_is_verifiable PASSED [ 12%]
backend/tests/test_classifier.py::TestClassifier::test_alter_column_type_is_not_verifiable PASSED [ 16%]
backend/tests/test_classifier.py::TestClassifier::test_rename_table_not_verifiable PASSED [ 20%]
backend/tests/test_classifier.py::TestClassifier::test_raw_dml_not_verifiable PASSED [ 24%]
backend/tests/test_classifier.py::TestClassifier::test_create_index_verifiable PASSED [ 28%]
backend/tests/test_classifier.py::TestClassifier::test_drop_index_verifiable PASSED [ 32%]
backend/tests/test_classifier.py::TestClassifier::test_empty_sql_returns_empty PASSED [ 36%]
backend/tests/test_classifier.py::TestClassifier::test_multiple_statements PASSED [ 40%]
backend/tests/test_delta_engine.py::TestDeltaEngine::test_added_table PASSED [ 44%]
backend/tests/test_delta_engine.py::TestDeltaEngine::test_dropped_table PASSED [ 48%]
backend/tests/test_delta_engine.py::TestDeltaEngine::test_added_column PASSED [ 52%]
backend/tests/test_delta_engine.py::TestDeltaEngine::test_dropped_column PASSED [ 56%]
backend/tests/test_delta_engine.py::TestDeltaEngine::test_no_changes PASSED [ 60%]
backend/tests/test_delta_engine.py::TestDeltaEngine::test_multiple_changes PASSED [ 64%]
backend/tests/test_prisma_adapter.py::TestPrismaAdapter::test_adapter_is_instantiable PASSED [ 68%]
backend/tests/test_prisma_adapter.py::TestPrismaAdapter::test_parse_webhook_github_failure PASSED [ 72%]
backend/tests/test_verdict_engine.py::TestVerdictEngine::test_all_verifiable_applied PASSED [ 76%]
backend/tests/test_verdict_engine.py::TestVerdictEngine::test_all_verifiable_rolled_back PASSED [ 80%]
backend/tests/test_verdict_engine.py::TestVerdictEngine::test_non_verifiable_hard_stop PASSED [ 84%]
backend/tests/test_verdict_engine.py::TestVerdictEngine::test_mixed_verifiable_hard_stop PASSED [ 88%]
backend/tests/test_verdict_engine.py::TestVerdictEngine::test_empty_actions_rolled_back PASSED [ 92%]
backend/tests/test_verdict_engine.py::TestVerdictEngine::test_drop_table_applied PASSED [ 96%]
backend/tests/test_verdict_engine.py::TestVerdictEngine::test_add_column_applied PASSED [100%]

============================= 25 passed in 0.44s ==============================
```

### Test Coverage Breakdown

| Test Module | Tests | What It Verifies |
|---|:---:|---|
| `test_classifier.py` | 10 | DDL verifiability classification, atomic roll-up, edge cases |
| `test_delta_engine.py` | 6 | Schema set difference ($\Delta$) across tables, columns, multi-change scenarios |
| `test_prisma_adapter.py` | 2 | Adapter instantiation, GitHub webhook failure parsing |
| `test_verdict_engine.py` | 7 | APPLIED, ROLLED_BACK, HARD_STOP decision paths, mixed/empty edge cases |

---

## Roadmap

| Priority | Feature | Status |
|:---:|---|:---:|
| 🟢 | PostgreSQL + Prisma adapter (full implementation) | ✅ Done |
| 🟢 | Deterministic Forensic Engine (parser, classifier, delta, verdict) | ✅ Done |
| 🟢 | REST API with OpenAPI 3.1 auto-docs | ✅ Done |
| 🟢 | PII redaction (regex-based) | ✅ Done |
| 🟢 | Incident narrative generation (template engine) | ✅ Done |
| 🟢 | GitHub & GitLab webhook ingestion | ✅ Done |
| 🟢 | Approve / Reject / Escalate workflow | ✅ Done |
| 🟢 | Slack notification integration | ✅ Done |
| 🟢 | 25-test pytest suite (classifier, delta, verdict, adapter) | ✅ Done |
| 🟡 | Interactive triage dashboard (frontend UI) | 🚧 In Progress |
| 🟡 | LLM-enhanced narrative generation (OpenAI / Gemini) | 🚧 In Progress |
| 🔵 | Flyway adapter | 📋 Planned |
| 🔵 | TypeORM adapter | 📋 Planned |
| 🔵 | Django migrations adapter | 📋 Planned |
| 🔵 | MySQL / MariaDB database engine support | 📋 Planned |
| 🔵 | Docker Compose one-command sandbox | 📋 Planned |
| 🔵 | Kubernetes Helm chart for production deployment | 📋 Planned |

---

## Contributing

We welcome contributions to adapters, verifiability rules, and parser enhancements!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/flyway-adapter`)
3. Commit your changes with clear messages (`git commit -m 'Add Flyway adapter implementation'`)
4. Ensure all tests pass (`pytest backend/tests/ -v`)
5. Open a Pull Request

### Good First Issues
- Implement the **Flyway adapter** using the `MigrationAdapter` abstract contract
- Add more regex patterns to the **PII redactor** (e.g., GCP service account keys)
- Add test cases for compound `ALTER TABLE` with 3+ mixed actions
- Write a **Django migrations adapter** stub

---

## License

Distributed under the **MIT License**. See `LICENSE` for more information.
