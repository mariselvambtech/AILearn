/**
 * WebAI Automation Dashboard — front-end application logic.
 *
 * Dependency-free SPA that talks to the dashboard server (same origin):
 *  - Login/register (API key persisted in localStorage)
 *  - Automation card grid with Run / View Steps / Delete actions
 *  - Import recording via multipart upload
 *  - Executions table with live status polling
 *  - Per-execution logs viewer
 */
"use strict";

// ===== State =====
const state = {
    apiKey: localStorage.getItem("webai_api_key") || null,
    username: localStorage.getItem("webai_username") || null,
    automations: [],
    pendingRunId: null,        // automation id awaiting run confirmation
    pendingDeleteId: null,    // automation id awaiting delete confirmation
    executionsTimer: null,     // polling timer for executions table
    stepsCache: {},            // automationId -> steps array (modal perf cache)
    trackedRuns: {},           // run_id -> { name, status } (live process tracker)
};

// ===== DOM helpers =====
const $ = (id) => document.getElementById(id);

function showModal(id) { $(id).classList.remove("hidden"); }
function hideModal(id) { $(id).classList.add("hidden"); }

function toast(message, kind = "info", durationMs = 4500) {
    const el = document.createElement("div");
    el.className = `toast ${kind}`;
    el.textContent = message;
    $("toastContainer").appendChild(el);
    setTimeout(() => el.remove(), durationMs);
}

function escapeHtml(value) {
    // DOM-based escaping: robust and immune to source-formatting issues
    const div = document.createElement("div");
    div.textContent = String(value ?? "");
    return div.innerHTML;
}


// ===== API client =====
async function api(path, options = {}) {
    const headers = options.headers ? { ...options.headers } : {};
    if (state.apiKey) headers["X-API-Key"] = state.apiKey;
    if (options.json !== undefined) {
        headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(options.json);
        delete options.json;
    }
    const resp = await fetch(path, { ...options, headers });
    let data = null;
    try { data = await resp.json(); } catch { /* non-JSON body */ }
    if (!resp.ok) {
        const detail = data && data.detail ? data.detail : `HTTP ${resp.status}`;
        const err = new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
        err.status = resp.status;
        throw err;
    }
    return data;
}

// ===== Health badges =====
async function refreshHealth() {
    try {
        const health = await api("/api/health");
        setBadge("badgeApi", health.api_server);
        setBadge("badgeAi", health.ai_server);
        setBadge("badgeOllama", health.ollama);
    } catch {
        setBadge("badgeApi", "offline");
        setBadge("badgeAi", "offline");
        setBadge("badgeOllama", "offline");
    }
}

function setBadge(id, status) {
    const badge = $(id);
    badge.classList.remove("online", "offline");
    badge.classList.add(status === "online" ? "online" : "offline");
}

// ===== Auth =====
function setSession(apiKey, username) {
    state.apiKey = apiKey;
    state.username = username || null;
    localStorage.setItem("webai_api_key", apiKey);
    if (username) localStorage.setItem("webai_username", username);
    renderAuthArea();
}

function clearSession() {
    state.apiKey = null;
    state.username = null;
    localStorage.removeItem("webai_api_key");
    localStorage.removeItem("webai_username");
    renderAuthArea();
}

function renderAuthArea() {
    const loggedIn = Boolean(state.apiKey);
    $("loginBtn").hidden = loggedIn;
    $("logoutBtn").hidden = !loggedIn;
    $("userChip").classList.toggle("hidden", !loggedIn);
    if (loggedIn) $("userChip").textContent = state.username ? `@${state.username}` : "API key session";
}

async function handleLogin(event) {
    event.preventDefault();
    $("authError").classList.add("hidden");
    try {
        const data = await api("/api/auth/login", {
            method: "POST",
            json: { username: $("loginUsername").value.trim(), password: $("loginPassword").value },
        });
        setSession(data.api_key, $("loginUsername").value.trim());
        hideModal("authModal");
        toast("Logged in successfully", "success");
        loadDashboard();
    } catch (err) {
        showAuthError(err.message);
    }
}

async function handleRegister(event) {
    event.preventDefault();
    $("authError").classList.add("hidden");
    try {
        await api("/api/auth/register", {
            method: "POST",
            json: {
                username: $("regUsername").value.trim(),
                email: $("regEmail").value.trim() || null,
                password: $("regPassword").value,
            },
        });
        toast("Account created — logging you in…", "success");
        const data = await api("/api/auth/login", {
            method: "POST",
            json: { username: $("regUsername").value.trim(), password: $("regPassword").value },
        });
        setSession(data.api_key, $("regUsername").value.trim());
        hideModal("authModal");
        loadDashboard();
    } catch (err) {
        showAuthError(err.message);
    }
}

function handleApiKeySubmit(event) {
    event.preventDefault();
    const key = $("apiKeyInput").value.trim();
    if (!key) return showAuthError("API key cannot be empty.");
    setSession(key, null);
    hideModal("authModal");
    toast("API key saved", "success");
    loadDashboard();
}

function showAuthError(message) {
    const el = $("authError");
    el.textContent = message;
    el.classList.remove("hidden");
}

// ===== Automations =====
async function loadAutomations() {
    const grid = $("automationGrid");
    try {
        state.automations = await api("/api/automations");
        renderAutomations();
    } catch (err) {
        if (err.status === 401) {
            clearSession();
            grid.innerHTML = `<div class="empty-state">Session expired. Please log in again.</div>`;
            showModal("authModal");
        } else {
            grid.innerHTML = `<div class="empty-state">Failed to load automations: ${escapeHtml(err.message)}</div>`;
        }
    }
}

function renderAutomations() {
    const grid = $("automationGrid");
    if (!state.automations.length) {
        grid.innerHTML = `<div class="empty-state">No automations yet. Record one, then use “Import Recording”.</div>`;
        return;
    }
    grid.innerHTML = state.automations.map((a) => `
    <div class="card">
      <div class="card-title">${escapeHtml(a.name)}</div>
      <div class="card-desc">${escapeHtml(a.description || "No description")}</div>
      <div class="card-meta">
        <span class="card-id">ID ${a.id}</span>
        ${a.base_url ? `<span>${escapeHtml(safeHostname(a.base_url))}</span>` : ""}

        <span>${a.created_at ? new Date(a.created_at).toLocaleDateString() : ""}</span>
      </div>
      <div class="card-actions">
        <button class="btn btn-success btn-sm" data-run="${a.id}">▶ Run</button>
        <button class="btn btn-ghost btn-sm" data-steps="${a.id}">View steps</button>
        <button class="btn btn-danger btn-sm" data-delete="${a.id}" title="Delete automation">🗑 Delete</button>
      </div>
    </div>
  `).join("");

    grid.querySelectorAll("[data-run]").forEach((btn) =>
        btn.addEventListener("click", () => openRunModal(Number(btn.dataset.run))));
    grid.querySelectorAll("[data-steps]").forEach((btn) =>
        btn.addEventListener("click", () => openStepsModal(Number(btn.dataset.steps))));
    grid.querySelectorAll("[data-delete]").forEach((btn) =>
        btn.addEventListener("click", () => openDeleteModal(Number(btn.dataset.delete))));
}

// Safe URL display helper (avoids exceptions on malformed URLs)
function safeHostname(url) {
    try { return new URL(url).hostname; } catch { return url; }
}


// ===== Run flow =====
async function openRunModal(automationId) {
    state.pendingRunId = automationId;
    $("runModalTitle").textContent = `Run Automation #${automationId}`;
    $("runModalDesc").textContent = "Loading step preview…";
    $("runStepsPreview").innerHTML = "";
    showModal("runModal");
    try {
        const automation = await api(`/api/automations/${automationId}`);
        $("runModalTitle").textContent = `Run: ${automation.name}`;
        $("runModalDesc").textContent = automation.description || "";
        const steps = automation.steps_json || [];
        state.stepsCache[automationId] = steps;
        const preview = steps.slice(0, 5).map((s, i) =>
            `<li><b>${escapeHtml(s.action || "unknown")}</b> ${escapeHtml(s.value || s.url || s.name || "")}</li>`
        ).join("");
        $("runStepsPreview").innerHTML =
            `<b>${steps.length} steps</b><ol>${preview}</ol>` +
            (steps.length > 5 ? `<p class="muted">…and ${steps.length - 5} more</p>` : "");
    } catch (err) {
        $("runModalDesc").textContent = `Could not load preview: ${err.message}`;
    }
}

async function confirmRun() {
    const automationId = state.pendingRunId;
    if (!automationId) return;
    const btn = $("confirmRunBtn");
    btn.disabled = true;
    btn.textContent = "Starting…";
    try {
        const result = await api("/api/automations/run", { method: "POST", json: { automation_id: automationId } });
        hideModal("runModal");
        toast(`▶ ${result.message}${result.execution_id ? ` (execution #${result.execution_id})` : ""}`, "success", 6000);
        startExecutionsPolling(true);
    } catch (err) {
        toast(`Run failed: ${err.message}`, "error", 7000);
    } finally {
        btn.disabled = false;
        btn.textContent = "▶ Run now";
    }
}

// ===== Steps viewer =====
async function openStepsModal(automationId) {
    $("stepsModalTitle").textContent = `Steps — Automation #${automationId}`;
    $("stepsList").innerHTML = `<div class="empty-state">Loading…</div>`;
    showModal("stepsModal");
    try {
        const automation = await api(`/api/automations/${automationId}`);
        $("stepsModalTitle").textContent = `Steps — ${automation.name}`;
        const steps = automation.steps_json || [];
        state.stepsCache[automationId] = steps;
        $("stepsList").innerHTML = steps.length ? steps.map((s, i) => `
      <div class="step-item">
        <span class="step-action">${i + 1}. ${escapeHtml(s.action || "unknown")}</span>
        <span class="step-detail">${escapeHtml(s.value || s.url || s.name || "")}</span>
        ${Array.isArray(s.locators) && s.locators.length
                ? `<div class="step-locators">${s.locators.length} locator strategies captured</div>` : ""}
      </div>
    `).join("") : `<div class="empty-state">No steps recorded.</div>`;
    } catch (err) {
        $("stepsList").innerHTML = `<div class="empty-state">Failed: ${escapeHtml(err.message)}</div>`;
    }
}

// ===== Delete flow =====
async function openDeleteModal(automationId) {
    state.pendingDeleteId = automationId;
    const found = state.automations.find((a) => a.id === automationId);
    const name = found ? found.name : `#${automationId}`;
    $("deleteModalTitle").textContent = `Delete Automation #${automationId}`;
    $("deleteModalDesc").textContent = `Are you sure you want to delete automation '${name}'?`;
    showModal("deleteModal");
}

async function confirmDelete() {
    const automationId = state.pendingDeleteId;
    if (!automationId) return;
    const btn = $("confirmDeleteBtn");
    btn.disabled = true;
    btn.textContent = "Deleting…";
    try {
        const result = await api(`/api/automations/${automationId}`, { method: "DELETE" });
        hideModal("deleteModal");
        toast(result.message || `Automation ${automationId} deleted`, "success", 5000);
        // Invalidate steps cache for the deleted automation
        delete state.stepsCache[automationId];
        loadAutomations();
    } catch (err) {
        toast(`Delete failed: ${err.message}`, "error", 7000);
    } finally {
        btn.disabled = false;
        btn.textContent = "Delete";
    }
}

// ===== Import flow =====
async function handleImport(event) {
    event.preventDefault();
    $("importError").classList.add("hidden");
    const fileInput = $("importFile");
    if (!fileInput.files.length) return;

    const submitBtn = $("importSubmitBtn");
    submitBtn.disabled = true;
    submitBtn.textContent = "Importing…";
    try {
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);
        formData.append("name", $("importName").value.trim());
        formData.append("description", $("importDesc").value.trim());
        const result = await api("/api/automations/import", { method: "POST", body: formData });
        hideModal("importModal");
        toast(`Imported '${result.name}' (${result.step_count} steps) as automation #${result.automation_id}`, "success", 6000);
        $("importForm").reset();
        loadAutomations();
    } catch (err) {
        const el = $("importError");
        el.textContent = err.message;
        el.classList.remove("hidden");
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Import to database";
    }
}

// ===== Record flow =====
async function handleRecord(event) {
    event.preventDefault();
    $("recordError").classList.add("hidden");

    const submitBtn = $("recordSubmitBtn");
    submitBtn.disabled = true;
    submitBtn.textContent = "Launching…";
    try {
        const payload = {
            name: $("recordName").value.trim(),
            start_url: $("recordUrl").value.trim(),
            description: $("recordDesc").value.trim() || undefined,
        };
        const result = await api("/api/automations/record", { method: "POST", json: payload });
        hideModal("recordModal");
        toast(`Recording window launched in Chromium for '${payload.name}'! Complete actions & click Stop Recording.`, "info", 8000);
        $("recordForm").reset();

        if (result && result.run_id) {
            state.trackedRuns[result.run_id] = { name: payload.name, status: "running" };
        }
        startExecutionsPolling(true);
    } catch (err) {
        const el = $("recordError");
        el.textContent = err.message;
        el.classList.remove("hidden");
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "🔴 Launch Recorder";
    }
}

// ===== Executions & Subprocess Runs =====
async function loadExecutions() {
    let anyLive = false;
    try {
        const executions = await api("/api/executions?limit=15");
        renderExecutions(executions);
        if (executions.some((e) => e.live_status === "running" || e.status === "running")) {
            anyLive = true;
        }
    } catch {
        /* ignore execution fetch error */
    }

    try {
        const runs = await api("/api/runs");
        if (runs.some((r) => r.status === "running")) {
            anyLive = true;
        }

        for (const run of runs) {
            const tracked = state.trackedRuns[run.run_id];
            if (tracked) {
                if (run.status === "success") {
                    delete state.trackedRuns[run.run_id];
                    toast(`🎉 Automation '${tracked.name}' recorded & imported to database successfully!`, "success", 7000);
                    loadAutomations();
                } else if (run.status === "failed") {
                    delete state.trackedRuns[run.run_id];
                    toast(`❌ Recording session for '${tracked.name}' failed or exited.`, "error", 7000);
                }
            }
        }
    } catch {
        /* ignore runs fetch error */
    }

    if (Object.keys(state.trackedRuns).length > 0) {
        anyLive = true;
    }

    $("liveIndicator").classList.toggle("hidden", !anyLive);
    return anyLive;
}

function renderExecutions(executions) {
    const body = $("executionsBody");
    if (!executions.length) {
        body.innerHTML = `<tr><td colspan="6" class="empty-state">No executions yet.</td></tr>`;
        return;
    }
    body.innerHTML = executions.map((e) => {
        const effective = e.live_status || e.status || "unknown";
        const duration = e.duration_seconds != null ? `${Number(e.duration_seconds).toFixed(1)}s` : "—";
        return `
      <tr>
        <td>#${e.id}</td>
        <td>${escapeHtml(automationNameFor(e.automation_id))}</td>
        <td><span class="status-pill ${escapeHtml(effective)}">${escapeHtml(effective)}</span></td>
        <td>${e.started_at ? new Date(e.started_at).toLocaleString() : "—"}</td>
        <td>${duration}</td>
        <td><button class="btn btn-ghost btn-sm" data-logs="${e.id}">Logs</button></td>
      </tr>
    `;
    }).join("");
    body.querySelectorAll("[data-logs]").forEach((btn) =>
        btn.addEventListener("click", () => openLogsModal(Number(btn.dataset.logs))));
}

function automationNameFor(automationId) {
    const found = state.automations.find((a) => a.id === automationId);
    return found ? found.name : `Automation #${automationId}`;
}

async function openLogsModal(executionId) {
    $("logsModalTitle").textContent = `Logs — Execution #${executionId}`;
    $("logsList").innerHTML = `<div class="empty-state">Loading…</div>`;
    showModal("logsModal");
    try {
        const logs = await api(`/api/executions/${executionId}/logs`);
        $("logsList").innerHTML = logs.length ? logs.map((log) => `
      <div class="log-entry ${escapeHtml(log.level || "INFO")}">
        <span class="log-meta">${log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ""} [${escapeHtml(log.level)}] ${escapeHtml(log.source || "")}</span>
        ${escapeHtml(log.message)}
      </div>
    `).join("") : `<div class="empty-state">No logs recorded for this execution.</div>`;
    } catch (err) {
        $("logsList").innerHTML = `<div class="empty-state">Failed: ${escapeHtml(err.message)}</div>`;
    }
}

// ===== Polling =====
function startExecutionsPolling(fast) {
    if (state.executionsTimer) clearInterval(state.executionsTimer);
    const tick = async () => {
        const anyLive = await loadExecutions();
        // Poll fast (5s) while a run is live, slow (30s) otherwise
        if (anyLive !== fast) startExecutionsPolling(anyLive);
    };
    state.executionsTimer = setInterval(tick, fast ? 5000 : 30000);
    loadExecutions();
}

// ===== Boot =====
function loadDashboard() {
    loadAutomations();
    loadSkills();
    startExecutionsPolling(false);
}

// ===== AI Skills =====
async function loadSkills() {
    const grid = $("skillsGrid");
    if (!grid) return;
    try {
        const skills = await api("/api/skills");
        renderSkills(skills);
    } catch (err) {
        grid.innerHTML = `<div class="empty-state">Failed to load AI skills: ${escapeHtml(err.message)}</div>`;
    }
}

function renderSkills(skills) {
    const grid = $("skillsGrid");
    if (!grid) return;
    if (!skills || skills.length === 0) {
        grid.innerHTML = `<div class="empty-state">No synthesized AI skills found. Record a skill using record_then_run.py!</div>`;
        return;
    }

    grid.innerHTML = skills.map(skill => {
        const params = skill.parameters_schema || {};
        const paramFields = Object.keys(params).map(pKey => {
            const pInfo = params[pKey] || {};
            const desc = typeof pInfo === 'object' ? (pInfo.description || pKey) : pKey;
            const defVal = typeof pInfo === 'object' ? (pInfo.default || '') : pInfo;
            return `
                <div class="form-group" style="margin-top: 8px;">
                    <label style="font-size: 0.85rem; color: var(--text-muted);">${escapeHtml(desc)}</label>
                    <input type="text" class="input skill-param-input" data-skill-id="${escapeHtml(skill.id)}" data-param-key="${escapeHtml(pKey)}" value="${escapeHtml(defVal)}" placeholder="${escapeHtml(defVal)}" style="padding: 6px 10px; font-size: 0.9rem;" />
                </div>
            `;
        }).join("");

        return `
            <div class="card skill-card" id="skill-card-${escapeHtml(skill.id)}">
                <div class="card-header">
                    <h3 class="card-title">⚡ ${escapeHtml(skill.skill_name)}</h3>
                    <span class="badge badge-accent">${skill.step_count} steps</span>
                </div>
                <p class="card-desc" style="font-size: 0.9rem; color: var(--text-muted); margin: 8px 0;">${escapeHtml(skill.description)}</p>
                <div class="trigger-phrases" style="font-size: 0.8rem; font-style: italic; opacity: 0.8; margin-bottom: 10px;">
                    Triggers: ${escapeHtml((skill.trigger_phrases || []).join(", "))}
                </div>
                <form onsubmit="handleSkillExecute(event, '${escapeHtml(skill.id)}', '${escapeHtml(skill.filename)}')">
                    ${paramFields}
                    <button type="submit" class="btn btn-accent" style="width: 100%; margin-top: 12px;">▶ Run Skill</button>
                </form>
            </div>
        `;
    }).join("");
}

async function handleSkillExecute(event, skillId, filename) {
    event.preventDefault();
    const inputs = document.querySelectorAll(`.skill-param-input[data-skill-id="${skillId}"]`);
    const parameters = {};
    inputs.forEach(input => {
        const key = input.dataset.paramKey;
        parameters[key] = input.value;
    });

    toast(`Starting execution for skill '${skillId}'...`, "info");
    try {
        const res = await api("/api/skills/execute", {
            method: "POST",
            json: { skill_id: skillId, filename: filename, parameters: parameters }
        });
        if (res.status === "success") {
            toast(`Skill '${res.skill_name || skillId}' completed successfully! (${res.steps_executed} steps)`, "success");
        } else {
            toast(`Skill execution status: ${res.status}`, "warning");
        }
    } catch (err) {
        toast(`Skill execution failed: ${err.message}`, "danger");
    }
}

function bindEvents() {
    $("loginBtn").addEventListener("click", () => showModal("authModal"));
    $("logoutBtn").addEventListener("click", () => { clearSession(); location.reload(); });
    $("loginForm").addEventListener("submit", handleLogin);
    $("registerForm").addEventListener("submit", handleRegister);
    $("apiKeyForm").addEventListener("submit", handleApiKeySubmit);
    $("tabLogin").addEventListener("click", () => switchTab(true));
    $("tabRegister").addEventListener("click", () => switchTab(false));
    $("refreshBtn").addEventListener("click", () => { loadAutomations(); loadSkills(); loadExecutions(); refreshHealth(); });
    $("refreshSkillsBtn")?.addEventListener("click", () => { loadSkills(); toast("Refreshed AI Skills", "info"); });
    $("importBtn").addEventListener("click", () => {
        if (!state.apiKey) return showModal("authModal");
        showModal("importModal");
    });
    $("importForm").addEventListener("submit", handleImport);
    $("recordBtn").addEventListener("click", () => {
        if (!state.apiKey) return showModal("authModal");
        showModal("recordModal");
    });
    $("recordForm").addEventListener("submit", handleRecord);
    $("confirmRunBtn").addEventListener("click", confirmRun);
    $("confirmDeleteBtn").addEventListener("click", confirmDelete);
    document.querySelectorAll("[data-close]").forEach((btn) =>
        btn.addEventListener("click", () => hideModal(btn.dataset.close)));
    document.querySelectorAll(".modal-backdrop").forEach((backdrop) =>
        backdrop.addEventListener("click", (e) => { if (e.target === backdrop) backdrop.classList.add("hidden"); }));
}

function switchTab(isLogin) {
    $("tabLogin").classList.toggle("active", isLogin);
    $("tabRegister").classList.toggle("active", !isLogin);
    $("loginForm").classList.toggle("hidden", !isLogin);
    $("registerForm").classList.toggle("hidden", isLogin);
}

document.addEventListener("DOMContentLoaded", () => {
    bindEvents();
    renderAuthArea();
    refreshHealth();
    setInterval(refreshHealth, 30000);
    if (state.apiKey) {
        loadDashboard();
    } else {
        showModal("authModal");
    }
});