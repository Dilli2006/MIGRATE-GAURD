/* ============================================================
   MIGRATE-GUARD — Dashboard Client  (app.js)
   Talks to FastAPI backend · handles all UI state
   ============================================================ */

const API = 'http://localhost:8000';
let _incidents = [
  {
    id: "inc-001-applied",
    migration_name: "202609080010_add_teams_table",
    migration_sql: `CREATE TABLE "teams" (\n  "id" SERIAL NOT NULL PRIMARY KEY,\n  "name" TEXT NOT NULL,\n  "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP\n);\nALTER TABLE "users" ADD COLUMN "team_id" INTEGER;\nALTER TABLE "users" ADD CONSTRAINT "fk_users_team_id" FOREIGN KEY ("team_id") REFERENCES "teams"("id");\nCREATE INDEX "idx_users_team_id" ON "users"("team_id");`,
    detected_at: new Date().toISOString(),
    status: "AWAITING_APPROVAL",
    raw_logs: "Error: P3009\nMigration '202609080010_add_teams_table' failed.\nPost-migration health check timed out after 30s.\nConnection string: postgres://admin:s3cr3t_p@ss@prod.db.internal:5432/main",
    redacted_logs: "Error: P3009\nMigration '202609080010_add_teams_table' failed.\nPost-migration health check timed out after 30s.\nConnection string: postgres://admin:[REDACTED]@prod.db.internal:5432/main",
    summary: "Migration 202609080010_add_teams_table was diagnosed as APPLIED. Tables added: teams. Confidence: 100%. All changes verified as applied. Approve to mark migration as applied.",
    verdict: {
      verdict: "APPLIED",
      total_actions: 4,
      verifiable_actions: 4,
      non_verifiable_actions: 0,
      confidence: 1.0,
      evidence: "All 4 verifiable DDL actions were found present in the live database schema (S1). Zero missing changes.",
      delta_summary: {
        added_tables: ["teams"],
        dropped_tables: [],
        added_columns: { users: ["team_id"] },
        dropped_columns: {},
        added_indexes: { users: ["idx_users_team_id"] },
        dropped_indexes: {}
      },
      applied_actions: [
        { statement_text: 'CREATE TABLE "teams" (...)', action_type: "CREATE_TABLE", target_table: "teams", verifiability: "VERIFIABLE", statement_index: 1 },
        { statement_text: 'ALTER TABLE "users" ADD COLUMN "team_id" INTEGER', action_type: "ADD_COLUMN", target_table: "users", verifiability: "VERIFIABLE", statement_index: 2 },
        { statement_text: 'ALTER TABLE "users" ADD CONSTRAINT "fk_users_team_id"...', action_type: "ADD_CONSTRAINT", target_table: "users", verifiability: "VERIFIABLE", statement_index: 3 },
        { statement_text: 'CREATE INDEX "idx_users_team_id" ON "users"("team_id")', action_type: "CREATE_INDEX", target_table: "users", verifiability: "VERIFIABLE", statement_index: 4 }
      ],
      unverifiable_actions: []
    }
  },
  {
    id: "inc-002-rollback",
    migration_name: "202609080020_add_audit_logs",
    migration_sql: `CREATE TABLE "audit_logs" (\n  "id" SERIAL NOT NULL PRIMARY KEY,\n  "user_id" INTEGER NOT NULL,\n  "action" TEXT NOT NULL,\n  "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP\n);\nCREATE INDEX "idx_audit_logs_user_id" ON "audit_logs"("user_id");\nCREATE INDEX "idx_audit_logs_created" ON "audit_logs"("created_at");`,
    detected_at: new Date(Date.now() - 3600000).toISOString(),
    status: "AWAITING_APPROVAL",
    raw_logs: "Error: P3009\nDisk quota exceeded during DDL execution. Transaction aborted by PostgreSQL.",
    redacted_logs: "Error: P3009\nDisk quota exceeded during DDL execution. Transaction aborted by PostgreSQL.",
    summary: "Migration 202609080020_add_audit_logs was diagnosed as ROLLED_BACK. Confidence: 100%. No changes detected in the live schema. Approve to mark migration as rolled back.",
    verdict: {
      verdict: "ROLLED_BACK",
      total_actions: 3,
      verifiable_actions: 3,
      non_verifiable_actions: 0,
      confidence: 1.0,
      evidence: "No schema changes from this migration were detected in the live database schema. PostgreSQL rolled back the transaction cleanly.",
      delta_summary: {
        added_tables: [],
        dropped_tables: [],
        added_columns: {},
        dropped_columns: {},
        added_indexes: {},
        dropped_indexes: {}
      },
      applied_actions: [],
      unverifiable_actions: [
        { statement_text: 'CREATE TABLE "audit_logs" (...)', action_type: "CREATE_TABLE", target_table: "audit_logs", verifiability: "VERIFIABLE", statement_index: 1 },
        { statement_text: 'CREATE INDEX "idx_audit_logs_user_id" ON "audit_logs"("user_id")', action_type: "CREATE_INDEX", target_table: "audit_logs", verifiability: "VERIFIABLE", statement_index: 2 },
        { statement_text: 'CREATE INDEX "idx_audit_logs_created" ON "audit_logs"("created_at")', action_type: "CREATE_INDEX", target_table: "audit_logs", verifiability: "VERIFIABLE", statement_index: 3 }
      ]
    }
  },
  {
    id: "inc-003-hardstop",
    migration_name: "202609080030_backfill_and_alter_types",
    migration_sql: `ALTER TABLE "accounts" ALTER COLUMN "status" TYPE text;\nUPDATE "accounts" SET "balance" = "balance" * 1.05 WHERE "active" = true;\nALTER TABLE "accounts" ALTER COLUMN "email" SET NOT NULL;`,
    detected_at: new Date(Date.now() - 7200000).toISOString(),
    status: "AWAITING_APPROVAL",
    raw_logs: "Error: P3009\nMigration crashed mid-flight. Lock timeout on accounts table.",
    redacted_logs: "Error: P3009\nMigration crashed mid-flight. Lock timeout on accounts table.",
    summary: "Migration 202609080030_backfill_and_alter_types was diagnosed as HARD_STOP. Confidence: 33%. Manual review required - non-verifiable actions detected in the migration.",
    verdict: {
      verdict: "HARD_STOP",
      total_actions: 3,
      verifiable_actions: 1,
      non_verifiable_actions: 2,
      confidence: 0.33,
      evidence: "Migration contains 2 non-verifiable actions (ALTER_COLUMN_TYPE, RAW_DML). Safety threshold requires manual DBA intervention.",
      delta_summary: {
        added_tables: [],
        dropped_tables: [],
        added_columns: {},
        dropped_columns: {},
        added_indexes: {},
        dropped_indexes: {}
      },
      applied_actions: [
        { statement_text: 'ALTER TABLE "accounts" ALTER COLUMN "email" SET NOT NULL', action_type: "ALTER_COLUMN_NULL", target_table: "accounts", verifiability: "VERIFIABLE", statement_index: 3 }
      ],
      unverifiable_actions: [
        { statement_text: 'ALTER TABLE "accounts" ALTER COLUMN "status" TYPE text', action_type: "ALTER_COLUMN_TYPE", target_table: "accounts", verifiability: "NOT_VERIFIABLE", statement_index: 1 },
        { statement_text: 'UPDATE "accounts" SET "balance" = "balance" * 1.05', action_type: "RAW_DML", target_table: "accounts", verifiability: "NOT_VERIFIABLE", statement_index: 2 }
      ]
    }
  }
];
let _activeFilter = 'ALL';
let _pollTimer = null;

/* ══════════════════════════════════════════
   BOOTSTRAP
══════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', () => {
  renderIncidentTable();
  updateStats();
  renderRulesTable();
  const cfgBase = document.getElementById('cfg-base');
  if (cfgBase) cfgBase.textContent = API;

  const dot  = document.getElementById('apiDot');
  const text = document.getElementById('apiStatusText');
  if (dot) dot.classList.add('online');
  if (text) text.textContent = 'Engine Active';

  const params = new URLSearchParams(window.location.search);
  const p = params.get('page');
  const sc = params.get('scenario');
  const m = params.get('modal');
  if (p) showPage(p);
  if (sc) loadScenario(sc);
  if (m) openIncident(m);

  checkApiHealth();
  loadIncidents();
  startPolling();
});

/* ══════════════════════════════════════════
   NAVIGATION
══════════════════════════════════════════ */
const PAGE_TITLES = {
  dashboard: '<span>Dashboard</span> — Incident Feed',
  create:    '<span>New Incident</span> — Manual Trigger',
  simulate:  '<span>Simulation</span> — Scenario Playground',
  settings:  '<span>Settings</span> — Configuration',
};

function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  document.getElementById('nav-' + name).classList.add('active');
  document.getElementById('pageTitle').innerHTML = PAGE_TITLES[name] || name;
  if (name === 'dashboard') loadIncidents();
}

/* ══════════════════════════════════════════
   API HELPERS
══════════════════════════════════════════ */
async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

/* ══════════════════════════════════════════
   HEALTH CHECK
══════════════════════════════════════════ */
async function checkApiHealth() {
  const dot  = document.getElementById('apiDot');
  const text = document.getElementById('apiStatusText');
  const cfg  = document.getElementById('cfg-status');
  try {
    const data = await apiFetch('/health');
    dot.classList.add('online');
    text.textContent = 'API Online';
    if (cfg) cfg.textContent = '✅ ' + (data.service || 'ok');
  } catch {
    dot.classList.remove('online');
    dot.classList.add('offline');
    text.textContent = 'API Offline';
    if (cfg) cfg.textContent = '❌ Unreachable';
  }
}

/* ══════════════════════════════════════════
   POLLING
══════════════════════════════════════════ */
function startPolling() {
  if (_pollTimer) clearInterval(_pollTimer);
  _pollTimer = setInterval(() => {
    checkApiHealth();
    const activePage = document.querySelector('.page.active');
    if (activePage && activePage.id === 'page-dashboard') loadIncidents();
  }, 15000);
}

/* ══════════════════════════════════════════
   INCIDENT LIST
══════════════════════════════════════════ */
async function loadIncidents() {
  const spinner = document.getElementById('refreshSpinner');
  const last    = document.getElementById('lastRefresh');
  spinner.style.display = 'inline-block';
  try {
    _incidents = await apiFetch('/incidents/');
    renderIncidentTable();
    updateStats();
    const badge = document.getElementById('awaitingBadge');
    const waiting = _incidents.filter(i => i.status === 'AWAITING_APPROVAL').length;
    badge.style.display = waiting ? 'inline' : 'none';
    badge.textContent = waiting;
  } catch (e) {
    renderErrorState(e.message);
  } finally {
    spinner.style.display = 'none';
    last.textContent = 'Updated ' + new Date().toLocaleTimeString();
  }
}

function updateStats() {
  document.getElementById('statTotal').textContent    = _incidents.length;
  document.getElementById('statAwaiting').textContent = _incidents.filter(i => i.status === 'AWAITING_APPROVAL').length;
  document.getElementById('statResolved').textContent = _incidents.filter(i => i.status === 'RESOLVED').length;
  document.getElementById('statHardStop').textContent = _incidents.filter(i => i.verdict?.verdict === 'HARD_STOP').length;
}

function setFilter(filter, el) {
  _activeFilter = filter;
  document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  renderIncidentTable();
}

function getFiltered() {
  if (_activeFilter === 'ALL') return _incidents;
  return _incidents.filter(i => i.status === _activeFilter);
}

function renderIncidentTable() {
  const container = document.getElementById('incidentTableContainer');
  const list = getFiltered();
  if (!list.length) {
    container.innerHTML = `<div class="empty-state">
      <div class="empty-icon">🔍</div>
      <p>${_activeFilter === 'ALL' ? 'No incidents yet. Create one or trigger a webhook.' : 'No incidents match this filter.'}</p>
    </div>`;
    return;
  }

  const rows = list.map(inc => {
    const verdict = inc.verdict?.verdict || '—';
    const vBadge  = verdictBadge(verdict);
    const sBadge  = statusBadge(inc.status);
    const time    = inc.detected_at ? new Date(inc.detected_at).toLocaleString() : '—';
    return `<tr onclick="openIncident('${inc.id}')">
      <td><div class="incident-name">${escHtml(inc.migration_name)}</div><div class="incident-time">${time}</div></td>
      <td>${sBadge}</td>
      <td>${vBadge}</td>
      <td style="font-size:12px;color:var(--slate-500)">${inc.verdict ? inc.verdict.total_actions + ' actions' : '—'}</td>
      <td style="font-size:12px;color:var(--slate-500)">${inc.verdict ? Math.round(inc.verdict.confidence * 100) + '%' : '—'}</td>
      <td><button class="btn btn-ghost btn-sm" onclick="event.stopPropagation();openIncident('${inc.id}')">View →</button></td>
    </tr>`;
  }).join('');

  container.innerHTML = `<table class="incident-table">
    <thead><tr>
      <th>Migration</th><th>Status</th><th>Verdict</th><th>Actions</th><th>Confidence</th><th></th>
    </tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function renderErrorState(msg) {
  document.getElementById('incidentTableContainer').innerHTML = `<div class="empty-state">
    <div class="empty-icon">⚠️</div>
    <p style="color:var(--red-400)">Failed to load: ${escHtml(msg)}</p>
    <p style="font-size:12px">Is the FastAPI server running on port 8000?</p>
  </div>`;
}

/* ══════════════════════════════════════════
   INCIDENT DETAIL MODAL
══════════════════════════════════════════ */
async function openIncident(id) {
  const modal = document.getElementById('incidentModal');
  modal.classList.add('open');
  const local = _incidents.find(i => i.id === id);
  if (local) {
    renderModalContent(local);
  } else {
    document.getElementById('modalBody').innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:200px"><span class="spinner" style="width:36px;height:36px;border-width:3px"></span></div>`;
    document.getElementById('modalFooter').innerHTML = '';
  }

  try {
    const inc = await apiFetch('/incidents/' + id);
    renderModalContent(inc);
  } catch (e) {
    if (!local) {
      document.getElementById('modalBody').innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p style="color:var(--red-400)">${escHtml(e.message)}</p></div>`;
    }
  }
}

function renderModalContent(inc) {
  const verdict  = inc.verdict;
  const vtype    = verdict?.verdict || 'UNKNOWN';
  const heroClass = { APPLIED: 'applied', ROLLED_BACK: 'rolled-back', HARD_STOP: 'hard-stop' }[vtype] || 'rolled-back';
  const heroEmoji = { APPLIED: '✅', ROLLED_BACK: '🔄', HARD_STOP: '🛑' }[vtype] || '❓';
  const confidence = verdict ? Math.round(verdict.confidence * 100) : 0;

  document.getElementById('modalTitle').textContent = inc.migration_name;
  document.getElementById('modalSubtitle').textContent = `ID: ${inc.id}  •  Detected: ${inc.detected_at ? new Date(inc.detected_at).toLocaleString() : '—'}`;

  /* Summary card */
  const summaryHTML = inc.summary
    ? `<div style="background:var(--bg-glass-light);border:1px solid rgba(255,255,255,0.06);border-radius:var(--radius-md);padding:14px 16px;font-size:13px;color:var(--slate-300);line-height:1.6">${escHtml(inc.summary)}</div>`
    : '';

  /* Verdict hero */
  const verdictHTML = verdict ? `
    <div class="verdict-hero ${heroClass}">
      <div class="verdict-emoji">${heroEmoji}</div>
      <div>
        <div class="verdict-type">${vtype.replace('_', ' ')}</div>
        <div class="verdict-evidence">${escHtml(verdict.evidence || '')}</div>
        <div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">
          <span style="font-size:12px;color:var(--slate-500)">Total: <b style="color:var(--white)">${verdict.total_actions}</b></span>
          <span style="font-size:12px;color:var(--slate-500)">Verifiable: <b style="color:var(--emerald-400)">${verdict.verifiable_actions}</b></span>
          <span style="font-size:12px;color:var(--slate-500)">Non-Verifiable: <b style="color:var(--red-400)">${verdict.non_verifiable_actions}</b></span>
        </div>
      </div>
      <div class="verdict-confidence">
        <div class="confidence-value">${confidence}%</div>
        <div class="confidence-label">Confidence</div>
      </div>
    </div>` : '';

  /* Status badges row */
  const statusRow = `<div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
    ${statusBadge(inc.status)}
    ${verdictBadge(vtype)}
    <span style="font-size:11px;color:var(--slate-600);margin-left:auto">${statusBadge(inc.status)}</span>
  </div>`;

  /* Delta diff */
  const delta = verdict?.delta_summary || {};
  const addedTables    = delta.added_tables    || [];
  const droppedTables  = delta.dropped_tables  || [];
  const addedCols      = Object.entries(delta.added_columns    || {}).flatMap(([t,cs]) => [...cs].map(c => `${t}.${c}`));
  const droppedCols    = Object.entries(delta.dropped_columns  || {}).flatMap(([t,cs]) => [...cs].map(c => `${t}.${c}`));
  const addedIdx       = Object.entries(delta.added_indexes    || {}).flatMap(([t,is]) => [...is]);
  const droppedIdx     = Object.entries(delta.dropped_indexes  || {}).flatMap(([t,is]) => [...is]);

  const allAdded   = [...addedTables.map(t => '🟢 Table: ' + t), ...addedCols.map(c => '🔵 Column: ' + c), ...addedIdx.map(i => '🔷 Index: ' + i)];
  const allDropped = [...droppedTables.map(t => '🔴 Table: ' + t), ...droppedCols.map(c => '🟠 Column: ' + c), ...droppedIdx.map(i => '🔸 Index: ' + i)];

  const deltaHTML = verdict ? `
    <div>
      <div class="section-label">📐 Schema Delta (Δ = S1 − S0)</div>
      <div class="delta-grid">
        <div class="delta-box added">
          <div class="delta-label">➕ Added to Live Schema</div>
          ${allAdded.length ? allAdded.map(x => `<div class="delta-item">${escHtml(x)}</div>`).join('') : '<div class="delta-empty">No additions detected</div>'}
        </div>
        <div class="delta-box dropped">
          <div class="delta-label">➖ Removed from Live Schema</div>
          ${allDropped.length ? allDropped.map(x => `<div class="delta-item">${escHtml(x)}</div>`).join('') : '<div class="delta-empty">No removals detected</div>'}
        </div>
      </div>
    </div>` : '';

  /* AST Actions table */
  const actions = [...(verdict?.applied_actions || []), ...(verdict?.unverifiable_actions || [])];
  const astHTML = actions.length ? `
    <div>
      <div class="section-label">🔬 AST Actions Classification</div>
      <div style="overflow-x:auto;border:1px solid rgba(255,255,255,0.05);border-radius:var(--radius-md)">
        <table class="ast-table">
          <thead><tr><th>#</th><th>Action Type</th><th>Target Table</th><th>Verifiability</th></tr></thead>
          <tbody>
            ${actions.map((a, i) => `<tr>
              <td style="color:var(--slate-600)">${i+1}</td>
              <td class="action-type">${escHtml(a.action_type || '—')}</td>
              <td class="target-tbl">${escHtml(a.target_table || '—')}</td>
              <td>${a.verifiability === 'VERIFIABLE'
                ? '<span class="badge badge-verifiable">✅ Verifiable</span>'
                : '<span class="badge badge-not-verifiable">❌ Not Verifiable</span>'}</td>
            </tr>`).join('')}
          </tbody>
        </table>
      </div>
    </div>` : '';

  /* Resolution command */
  const resCmd = buildResolutionCmd(inc);
  const safeCmd = resCmd ? encodeURIComponent(resCmd) : '';
  const resCmdHTML = resCmd ? `
    <div>
      <div class="section-label">⚡ Resolution Command</div>
      <div class="resolution-cmd">
        <div><span class="cmd-prompt">$</span>${escHtml(resCmd)}</div>
        <button class="copy-btn" onclick="copyCmd(decodeURIComponent('${safeCmd}'))">📋 Copy</button>
      </div>
    </div>` : '';

  /* Migration SQL */
  const sqlHTML = inc.migration_sql ? `
    <div>
      <div class="section-label">📄 Migration SQL</div>
      <div class="log-viewer">${escHtml(inc.migration_sql)}</div>
    </div>` : '';

  /* Redacted logs */
  const logsHTML = inc.redacted_logs ? `
    <div>
      <div class="section-label">📋 Redacted CI/CD Logs</div>
      <div class="log-viewer">${escHtml(inc.redacted_logs)}</div>
    </div>` : '';

  document.getElementById('modalBody').innerHTML = [
    summaryHTML, verdictHTML, deltaHTML, astHTML, resCmdHTML, sqlHTML, logsHTML
  ].filter(Boolean).join('');

  /* Footer action buttons */
  const canApprove = inc.status === 'AWAITING_APPROVAL';
  document.getElementById('modalFooter').innerHTML = canApprove ? `
    <button class="btn btn-success" onclick="doApprove('${inc.id}')">✅ Approve &amp; Resolve</button>
    <button class="btn btn-danger" onclick="doReject('${inc.id}')">❌ Reject</button>
    <button class="btn btn-purple" onclick="doEscalate('${inc.id}')">🔺 Escalate to DBA</button>
    <button class="btn btn-ghost" onclick="closeModalDirect()" style="margin-left:auto">Close</button>
  ` : `
    <div style="font-size:12px;color:var(--slate-500);display:flex;align-items:center;gap:8px">
      ${statusBadge(inc.status)}
      <span>${inc.resolution || 'No further action available.'}</span>
    </div>
    <button class="btn btn-ghost" onclick="closeModalDirect()" style="margin-left:auto">Close</button>
  `;
}

function buildResolutionCmd(inc) {
  const v = inc.verdict?.verdict;
  const name = inc.migration_name;
  if (!v || !name || v === 'HARD_STOP') return null;
  const flag = v === 'APPLIED' ? '--applied' : '--rolled-back';
  return `prisma migrate resolve ${flag} "${name}"`;
}

function copyCmd(cmd) {
  navigator.clipboard.writeText(cmd).then(() => toast('📋 Command copied to clipboard!', 'success'));
}

/* ══════════════════════════════════════════
   APPROVE / REJECT / ESCALATE
══════════════════════════════════════════ */
async function doApprove(id) {
  if (!confirm('Approve this verdict and execute the native resolution command?')) return;
  await doAction(id, '/approve', 'POST', '✅ Incident approved and resolved!', 'success');
}
async function doReject(id) {
  if (!confirm('Reject this verdict? No action will be taken on the database.')) return;
  await doAction(id, '/reject', 'POST', '❌ Incident rejected.', 'info');
}
async function doEscalate(id) {
  await doAction(id, '/escalate', 'POST', '🔺 Escalated to senior DBA.', 'info');
}

async function doAction(id, path, method, successMsg, toastType) {
  try {
    await apiFetch('/incidents/' + id + path, { method });
    toast(successMsg, toastType);
    closeModalDirect();
    await loadIncidents();
  } catch (e) {
    toast('⚠️ ' + e.message, 'error');
  }
}

/* ══════════════════════════════════════════
   CREATE INCIDENT
══════════════════════════════════════════ */
async function handleCreateSubmit(e) {
  e.preventDefault();
  const btn = document.getElementById('createSubmitBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Analyzing…';

  const body = {
    migration_name: document.getElementById('f-name').value.trim(),
    migration_sql:  document.getElementById('f-sql').value.trim(),
    raw_logs:       document.getElementById('f-logs').value.trim() || null,
    prisma_dir:     document.getElementById('f-dir').value.trim() || './prisma/migrations',
  };

  try {
    const inc = await apiFetch('/incidents/', { method: 'POST', body: JSON.stringify(body) });
    toast('🔬 Forensic analysis complete! Opening incident…', 'success');
    clearCreateForm();
    showPage('dashboard');
    await loadIncidents();
    openIncident(inc.id);
  } catch (e) {
    toast('⚠️ ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '🔬 Run Forensic Analysis';
  }
}

function clearCreateForm() {
  document.getElementById('createForm').reset();
}

/* ══════════════════════════════════════════
   SCENARIO PLAYGROUND
══════════════════════════════════════════ */
const SCENARIOS = {
  A: {
    name: '202609080010_add_teams_table',
    sql: `CREATE TABLE "teams" (
  "id" SERIAL NOT NULL,
  "name" TEXT NOT NULL,
  "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "teams_pkey" PRIMARY KEY ("id")
);

ALTER TABLE "users" ADD COLUMN "team_id" INTEGER;
ALTER TABLE "users" ADD CONSTRAINT "fk_users_team_id" FOREIGN KEY ("team_id") REFERENCES "teams"("id");
CREATE INDEX "idx_users_team_id" ON "users"("team_id");`,
    logs: `Error: P3009\nMigration '202609080010_add_teams_table' failed.\nPost-migration health check timed out after 30s.\nConnection string: postgres://admin:s3cr3t@prod.db.internal:5432/main`,
    label: 'Scenario A — Expected: APPLIED',
  },
  B: {
    name: '202609080020_add_audit_logs',
    sql: `CREATE TABLE "audit_logs" (
  "id" SERIAL NOT NULL,
  "user_id" INTEGER NOT NULL,
  "action" TEXT NOT NULL,
  "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "audit_logs_pkey" PRIMARY KEY ("id")
);

ALTER TABLE "audit_logs" ADD CONSTRAINT "fk_audit_user_id" FOREIGN KEY ("user_id") REFERENCES "users"("id");
CREATE INDEX "idx_audit_logs_user_id" ON "audit_logs"("user_id");
CREATE INDEX "idx_audit_logs_created" ON "audit_logs"("created_at");`,
    logs: `Error: P3009\nDisk quota exceeded during DDL execution. Transaction aborted by PostgreSQL.`,
    label: 'Scenario B — Expected: ROLLED_BACK',
  },
  C: {
    name: '202609080030_backfill_and_alter_types',
    sql: `ALTER TABLE "accounts" ALTER COLUMN "status" TYPE text;
UPDATE "accounts" SET "balance" = "balance" * 1.05 WHERE "active" = true;
ALTER TABLE "accounts" ALTER COLUMN "email" SET NOT NULL;`,
    logs: `Error: P3009\nMigration crashed mid-flight. Lock timeout on accounts table.`,
    label: 'Scenario C — Expected: HARD_STOP',
  },
};

function loadScenario(key) {
  const s = SCENARIOS[key];
  document.getElementById('scenarioLabel').textContent = s.label;
  document.getElementById('scenarioPreview').innerHTML = `
    <div>
      <div class="section-label">Migration Name</div>
      <code style="font-family:var(--font-mono);font-size:13px;color:var(--cyan-300)">${escHtml(s.name)}</code>
    </div>
    <div>
      <div class="section-label">SQL Preview</div>
      <div class="log-viewer">${escHtml(s.sql)}</div>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap">
      <button class="btn btn-primary" onclick="submitScenario('${key}')">🔬 Submit &amp; Analyze</button>
      <button class="btn btn-ghost" onclick="prefillCreate('${key}')">✏️ Edit Before Submit</button>
    </div>
  `;
}

async function submitScenario(key) {
  const s = SCENARIOS[key];
  const body = { migration_name: s.name, migration_sql: s.sql, raw_logs: s.logs };
  try {
    const btn = event.target;
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span> Analyzing…';
    const inc = await apiFetch('/incidents/', { method: 'POST', body: JSON.stringify(body) });
    toast('🧪 Scenario submitted! Opening result…', 'success');
    showPage('dashboard');
    await loadIncidents();
    openIncident(inc.id);
  } catch (e) {
    toast('⚠️ ' + e.message, 'error');
  }
}

function prefillCreate(key) {
  const s = SCENARIOS[key];
  document.getElementById('f-name').value = s.name;
  document.getElementById('f-sql').value  = s.sql;
  document.getElementById('f-logs').value = s.logs;
  showPage('create');
}

/* ══════════════════════════════════════════
   MODAL HELPERS
══════════════════════════════════════════ */
function closeModal(e) {
  if (e.target === document.getElementById('incidentModal')) closeModalDirect();
}
function closeModalDirect() {
  document.getElementById('incidentModal').classList.remove('open');
}

/* ══════════════════════════════════════════
   BADGE HELPERS
══════════════════════════════════════════ */
function verdictBadge(v) {
  const map = {
    APPLIED:      ['badge-applied',     '✅ Applied'],
    ROLLED_BACK:  ['badge-rolled-back', '🔄 Rolled Back'],
    HARD_STOP:    ['badge-hard-stop',   '🛑 Hard Stop'],
  };
  const [cls, label] = map[v] || ['badge-created', '— Unknown'];
  return `<span class="badge ${cls}">${label}</span>`;
}

function statusBadge(s) {
  const map = {
    DETECTED:         ['badge-created',   '🔵 Detected'],
    ANALYZING:        ['badge-analyzing', '⏳ Analyzing'],
    AWAITING_APPROVAL:['badge-awaiting',  '⏳ Awaiting Approval'],
    RESOLVED:         ['badge-resolved',  '✅ Resolved'],
    FAILED:           ['badge-failed',    '⚠️ Escalated'],
  };
  const [cls, label] = map[s] || ['badge-created', s];
  return `<span class="badge ${cls}">${label}</span>`;
}

/* ══════════════════════════════════════════
   VERIFIABILITY RULES TABLE
══════════════════════════════════════════ */
const RULES = [
  ['CREATE_TABLE',       'CREATE TABLE "users" (...)',            true,  'Table existence in S1 vs S0 is binary and unambiguous.'],
  ['DROP_TABLE',         'DROP TABLE "old_data"',                 true,  'Absence of table in S1 compared to S0 is deterministically proven.'],
  ['ADD_COLUMN',         'ALTER TABLE "t" ADD COLUMN "c" INT',    true,  'Column presence in target table is inspectable via information_schema.'],
  ['DROP_COLUMN',        'ALTER TABLE "t" DROP COLUMN "c"',       true,  'Absence of column is deterministically proven.'],
  ['ADD_CONSTRAINT',     'ALTER TABLE "t" ADD CONSTRAINT …',      true,  'FK, UNIQUE, CHECK constraints appear in table_constraints.'],
  ['DROP_CONSTRAINT',    'ALTER TABLE "t" DROP CONSTRAINT …',     true,  'Constraint removal is deterministically checked.'],
  ['CREATE_INDEX',       'CREATE INDEX "idx" ON "t"("c")',         true,  'Indexes are transactionally committed with verifiable catalog rows.'],
  ['DROP_INDEX',         'DROP INDEX "idx"',                       true,  'Index removal is checked in pg_indexes.'],
  ['ALTER_COLUMN_TYPE',  'ALTER COLUMN "c" TYPE text',            false, 'Type conversions may involve casting/collations not verifiable from schema diff.'],
  ['SET/DROP NOT NULL',  'ALTER COLUMN "c" SET NOT NULL',         false, 'Requires full table data scan; dangerous to infer from metadata delta.'],
  ['RENAME_TABLE/COL',   'ALTER TABLE "t" RENAME TO "t2"',        false, 'Indistinguishable from DROP + CREATE without commit metadata.'],
  ['INDEX CONCURRENTLY', 'CREATE INDEX CONCURRENTLY …',           false, 'Runs outside transaction blocks; can leave invalid index (indisvalid=false).'],
  ['RAW_DML',            'UPDATE "users" SET "active" = true',    false, 'Data mutation — schema delta cannot prove execution completeness.'],
];

function renderRulesTable() {
  const tbody = document.getElementById('rulesTableBody');
  if (!tbody) return;
  tbody.innerHTML = RULES.map(([action, sql, ok, rationale]) => `
    <tr>
      <td class="rule-action">${action}</td>
      <td><code style="font-family:var(--font-mono);font-size:11.5px;color:var(--slate-400)">${escHtml(sql)}</code></td>
      <td>${ok ? '<span class="badge badge-verifiable">✅ Yes</span>' : '<span class="badge badge-not-verifiable">❌ No</span>'}</td>
      <td class="rule-rationale">${rationale}</td>
    </tr>`).join('');
}

/* ══════════════════════════════════════════
   TOAST
══════════════════════════════════════════ */
function toast(msg, type = 'info') {
  const container = document.getElementById('toastContainer');
  const icons = { success: '✅', error: '❌', info: '💡' };
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.innerHTML = `<span>${icons[type] || '💡'}</span><span>${escHtml(msg)}</span>`;
  container.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(30px)'; el.style.transition = '0.3s'; setTimeout(() => el.remove(), 300); }, 3500);
}

/* ══════════════════════════════════════════
   UTIL
══════════════════════════════════════════ */
function escHtml(str) {
  if (str == null) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
