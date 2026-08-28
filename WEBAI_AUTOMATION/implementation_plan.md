# Implementation Plan — WebAI Front-End Automation Dashboard

> **Author:** CTO / Architect Agent (Enterprise Multi-Agent Fleet Workflow)
> **Date:** 2026-07-28
> **Status:** ✅ Completed (2026-07-29) — Developer/QA/Doc stages all delivered; 29/29 tests pass; live E2E verified (execution 2016)
> **Workflow:** `.agents/workflows/enterprise_frontend_fleet.md`

---

## 1. Objective

Replace all terminal interaction for `run_from_database.py` and `import_to_database.py`
with a modern Web UI dashboard. Users can list automations stored in MSSQL, trigger
browser playback with one click, import new recordings via file upload, and inspect
execution history/logs — without opening a terminal.

## 2. Architecture

New component: **`webai_local_server/webai_dashboard/`** — a FastAPI dashboard server
(port **8080**) acting as an orchestration/UI layer. The existing API server (port 8000)
remains **unchanged**; the dashboard proxies authenticated calls to it and owns the
Playwright playback subprocess lifecycle.

```
Browser UI (static SPA)  -->  Dashboard Server :8080  -->  API Server :8000 (unchanged)
                                     |
                                     +-- spawns --> run_from_task_txt_guided.py
                                                     (webai_playwright_python/.venv)
                                                     --> AI Server :8765 (WebSocket brain)
```

**Why a separate orchestrator instead of extending `webai_api_server`:**
- Workflow mandates the web server live under `webai_local_server/`.
- Keeps the Warehouse (DB API) stable and untouched — zero regression risk.
- Playback subprocess must run with the Playwright venv; the dashboard owns process lifecycle.

## 3. API Contract (Dashboard Server)

| Method | Endpoint | Auth | Behavior |
|---|---|---|---|
| GET | `/` | — | Serves the dashboard SPA (static files) |
| GET | `/api/health` | — | Probes API server (8000), AI server (8765), Ollama (11434) |
| POST | `/api/auth/login` | — | Proxy → `POST /auth/login`; returns `api_key` (stored in browser localStorage) |
| POST | `/api/auth/register` | — | Proxy → `POST /auth/register` |
| GET | `/api/automations` | X-API-Key | Proxy → `GET /automations` (dashboard card grid) |
| GET | `/api/automations/{id}` | X-API-Key | Proxy → `GET /automations/{id}` (View Steps modal) |
| POST | `/api/automations/run` | X-API-Key | **Replaces `run_from_database.py`**: fetch substituted steps → write `recorded_steps.json` + generate `generated_task.txt` → create execution record → spawn playback subprocess → return `execution_id` |
| POST | `/api/automations/import` | X-API-Key | **Replaces `import_to_database.py`**: multipart upload of `recorded_steps.json` + name/description → derive `base_url` → `POST /automations` |
| GET | `/api/executions` | X-API-Key | Proxy → `GET /executions`, merged with live subprocess states |
| GET | `/api/executions/{id}/logs` | X-API-Key | Proxy → `GET /executions/{id}/logs` (logs viewer modal) |

**Process watcher (new capability):** a background thread waits on each spawned playback
process and calls `PUT /executions/{id}` (`success`/`failed`) on exit — closing the
existing gap where CLI-triggered executions stayed `running` forever. Orchestration
events are also flushed to `POST /logs/batch` for audit parity with the CLI flow.

## 4. CLI Refactoring (Workflow Requirement)

| File | Change |
|---|---|
| `run_from_database.py` | Extract `run_automation(automation_id, api_key, api_url, auto_confirm) -> bool` (no `input()`); `main()` remains a thin interactive wrapper |
| `import_to_database.py` | Extract `register_user()`, `login_user()`, `import_recording()` programmatic functions; `main()` remains interactive wrapper |

Both keep 100% backward-compatible CLI behavior.

## 5. Front-End

`webai_dashboard/static/` — dependency-free SPA (vanilla HTML/CSS/JS, offline-friendly,
consistent with the project's local-only philosophy):

- **Header:** service health badges (API / AI / Ollama), login chip
- **Automation grid:** cards with name, description, ID, Run + View Steps buttons
- **Run modal:** step preview + confirm (replaces the `y/n` terminal prompt)
- **Import modal:** file picker for `recorded_steps.json`, name/description fields
- **Login/Register modal:** username/password → API key persisted in localStorage
- **Executions panel:** live status polling (3s) while runs are active
- **Logs modal:** per-execution log viewer

## 6. Environment & Dependencies

- Dashboard server runs with `webai_playwright_python/.venv` (already has `fastapi`,
  `requests`; **`uvicorn`, `pytest`, `httpx` to be installed — approved at HITL gate**)
- Config via env vars: `WEBAI_API_URL` (default `http://localhost:8000`),
  `WEBAI_OLLAMA_URL` (default `http://localhost:11434`), `AI_SERVER_HOST`/`AI_SERVER_PORT`
  (defaults `localhost`/`8765`), `DASHBOARD_PORT` (default `8080`)

## 7. QA Plan

1. **Unit tests** (`webai_local_server/tests/test_dashboard_api.py`): step-payload
   validation, base-URL derivation, task-file generation, health endpoint, auth proxy
   error handling (mocked upstream via `monkeypatch` + FastAPI `TestClient`).
2. **Integration tests** (auto-skip if API server offline): list automations,
   import → appears in list, run endpoint validation (404 on unknown automation).
3. **Live E2E proof:** start API (8000) + AI (8765) + Dashboard (8080); trigger
   automation ID 1 via `POST /api/automations/run`; verify execution record,
   subprocess spawn, and final status update.

**Quality gate:** 100% pass; failures bounce to Developer Agent (max 3 iterations).

## 8. Documentation Plan (Doc Agent)

- `memory-bank/activeContext.md`, `progress.md` — feature entry
- `memory-bank/decisionLog.md` — Decision 14: dashboard-as-orchestrator + execution status gap fix
- `memory-bank/systemPatterns.md` — Mermaid diagram with dashboard tier
- `memory-bank/techContext.md`, `how_to_run.md` — port 8080, run commands
- `graphify update .` + `python scripts/graphify_to_mermaid.py`

## 9. Safety

- No destructive actions (no DB drops, no file deletions).
- No git commits — user commits manually.
- Dashboard stores no credentials server-side; API key lives only in browser localStorage.
