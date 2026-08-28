# Graph Report - AILearn  (2026-07-29)

## Corpus Check
- 229 files · ~242,008 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 789 nodes · 1098 edges · 63 communities (55 shown, 8 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ba11a0ae`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Recent Work Completed
- Active Context — WebAI Platform
- Open Questions / Decisions Pending
- Immediate Next Steps (If User Requests)
- Current Session (2026-07-18)
- AGENTS.md
- rules/graphify.md
- workflows/graphify.md
- test_cdp_fixes.py
- fallback_helpers.py
- How to Run the WebAI Automation Project
- test_quick.py
- test_error_logging.py
- import_to_database.py
- test_phase1_locators.py
- Project Milestones
- Design Patterns
- graphify_to_mermaid.py
- crawl_helper.py
- AI Assistant Core Rules
- Page
- crud.py
- app.js
- Tech Context — WebAI Platform
- PlaybackProcessManager
- Any
- run_automation_endpoint
- dashboard_server.py
- MonkeyPatch
- test_dashboard_enhancements.py
- test_ws_probe_fix.py
- .json
- Implementation Plan — WebAI Front-End Automation Dashboard
- benchmark_modal_speed.py
- _safe_detail
- test_dashboard_recording.py
- test_dashboard_api.py
- validate_steps_payload
- Decision Log — WebAI Platform
- Decision 1: Multi-Locator Fallback vs Single Selector
- Decision 2: LLM Bypass for Click/Type When Locators Exist
- test_e2e_recording_full.py
- derive_base_url
- Decision 4: Fernet Symmetric Encryption for Credentials
- Decision 5: IST Timezone Computed Columns
- Decision 6: Batch Logging vs Individual Log Entries
- Decision 7: WebSocket for AI Server vs HTTP Polling
- Decision 8: Task Normalization Before LLM
- Decision 9: Action Normalization (LLM Tolerance)
- Decision 10: Plan Caching Disabled
- Decision 11: Right-Click Context Menu for Extraction
- Decision 12: Table Extraction via Injected JavaScript
- Decision 13: Database-Backed Orchestration vs File-Based
- Decision 17: Front-End Dashboard as Orchestration Layer (Not API Server Extension)
- Decision 3: Local Ollama vs Cloud LLM API
- build_task_text
- TestAuthEnforcement
- Decision 18: Probe-Tolerant WebSocket Server (process_request + logging filter)
- TestImportValidation
- test_dashboard_ui.py
- migrate_indexes.py
- test_dashboard_visual.py

## God Nodes (most connected - your core abstractions)
1. `handle_client()` - 22 edges
2. `Recent Work Completed` - 20 edges
3. `Decision Log — WebAI Platform` - 18 edges
4. `PlaybackProcessManager` - 17 edges
5. `bindEvents()` - 15 edges
6. `api()` - 13 edges
7. `Tech Context — WebAI Platform` - 12 edges
8. `Project Milestones` - 11 edges
9. `Design Patterns` - 11 edges
10. `run_automation_endpoint()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `LoginPayload` --uses--> `PlaybackProcessManager`  [INFERRED]
  WEBAI_AUTOMATION/webai_local_server/webai_dashboard/dashboard_server.py → WEBAI_AUTOMATION/webai_local_server/webai_dashboard/process_manager.py
- `RegisterPayload` --uses--> `PlaybackProcessManager`  [INFERRED]
  WEBAI_AUTOMATION/webai_local_server/webai_dashboard/dashboard_server.py → WEBAI_AUTOMATION/webai_local_server/webai_dashboard/process_manager.py
- `RunRequest` --uses--> `PlaybackProcessManager`  [INFERRED]
  WEBAI_AUTOMATION/webai_local_server/webai_dashboard/dashboard_server.py → WEBAI_AUTOMATION/webai_local_server/webai_dashboard/process_manager.py
- `RecordRequest` --uses--> `PlaybackProcessManager`  [INFERRED]
  WEBAI_AUTOMATION/webai_local_server/webai_dashboard/dashboard_server.py → WEBAI_AUTOMATION/webai_local_server/webai_dashboard/process_manager.py
- `RunResponse` --uses--> `PlaybackProcessManager`  [INFERRED]
  WEBAI_AUTOMATION/webai_local_server/webai_dashboard/dashboard_server.py → WEBAI_AUTOMATION/webai_local_server/webai_dashboard/process_manager.py

## Import Cycles
- None detected.

## Communities (63 total, 8 thin omitted)

### Community 0 - "Recent Work Completed"
Cohesion: 0.10
Nodes (21): 7 Web Failure Scenario Fortification & Test Suite Verification ✅, API Server Startup Bug Fixes ✅, Auto SQL Upload in `record_then_run.py` ✅, Browser-driven UI verification (2026-07-29) ✅, Crawl4AI Integration & Semantic DOM Fingerprinting ✅, Database Migrations ✅, Graphify Knowledge Graph Integration ✅, Hermes 3 Model Integration ✅ (+13 more)

### Community 1 - "Active Context — WebAI Platform"
Cohesion: 0.06
Nodes (32): 1. Conditional Branching (Future Enhancement), 2. Variable Storage for Conditions, 3. Explicit Page Validation, 4. LOCATOR_PRIORITY Inconsistency, 5. Shim Module Bug, Active Context  WebAI Platform, Active Context  WebAI Platform, Active Context  WebAI Platform (+24 more)

### Community 2 - "Open Questions / Decisions Pending"
Cohesion: 0.12
Nodes (12): Page, ask_yes_no(), main(), Any, Browser Interaction Recorder utilizing Chrome DevTools Protocol (CDP).  This m, Attaches the recorder to the BrowserContext and all current / newly opened tabs, Save single extraction to files immediately, Save extraction to Excel file (+4 more)

### Community 3 - "Immediate Next Steps (If User Requests)"
Cohesion: 0.09
Nodes (34): Exception, RuntimeError, Exception raised internally when the LLM outputs `action=done`.          This, TaskDone, ai(), ai_sync(), ClientError, _execute_command() (+26 more)

### Community 4 - "Current Session (2026-07-18)"
Cohesion: 0.18
Nodes (19): buffer_log(), create_execution_record(), fetch_automation_steps(), flush_logs(), log(), main(), Run automation from API database - Simple file-based approach.  This script de, Save steps to JSON file (+11 more)

### Community 8 - "test_cdp_fixes.py"
Cohesion: 0.17
Nodes (11): Test suite for verifying CDP and Playwright Actions fixes, Test that cdp.get_dom_snapshot works correctly, Test that playwright_actions.get_snapshot works correctly, Test that cdp.get_interactive_elements works correctly, Test that playwright_actions.get_dom_snapshot works correctly, Test that playwright_actions.get_interactive_elements works correctly, test_cdp_get_dom_snapshot(), test_cdp_get_interactive_elements() (+3 more)

### Community 9 - "fallback_helpers.py"
Cohesion: 0.05
Nodes (61): LogRecord, build_subgoal_prompt(), build_system_prompt(), cache_get_plan(), _cache_key(), cache_put_plan(), _compact_context(), _EmptyProbeNoiseFilter (+53 more)

### Community 10 - "How to Run the WebAI Automation Project"
Cohesion: 0.25
Nodes (7): 1. Start the API Server (Terminal 1), 2. Start the AI Server (Terminal 2), 3. Start the Ollama Server (Terminal 3), 4. Run the Client Script (Terminal 4), 5. (Optional) Start the Web UI Dashboard (Terminal 5), Available Client Scripts:, How to Run the WebAI Automation Project

### Community 11 - "test_quick.py"
Cohesion: 0.33
Nodes (5): Quick Test: Verify Playback Works, Test that generated_task.txt matches recorded steps, Test that recorded_steps.json has correct structure, test_recorded_steps_structure(), test_task_text_generation()

### Community 12 - "test_error_logging.py"
Cohesion: 0.50
Nodes (3): Test error logging with stacktrace capture Forces an error scenario to verify s, Test that errors are logged with full stacktraces, test_error_logging()

### Community 13 - "import_to_database.py"
Cohesion: 0.24
Nodes (10): import_recording(), login_user(), main(), Any, Import recorded_steps.json into the WebAI API database.  This script bridges t, Interactive CLI wrapper for importing `recorded_steps.json` into the database., Register a new user account via the API server.      Args:         username:, Authenticate a user and retrieve their API key.      Args:         username: (+2 more)

### Community 16 - "Project Milestones"
Cohesion: 0.06
Nodes (35): 1. Plan Caching Disabled, 2. No Explicit Navigation Validation, 3. Variable Persistence Limited, 4. LLM Sometimes Returns Invalid Actions, 5. Hardcoded API Key in Scripts, 6. Database Echo Enabled, 7. CORS Wide Open, API Server Tests ✅ (+27 more)

### Community 17 - "Design Patterns"
Cohesion: 0.07
Nodes (27): 1. Browser Robot ↔ AI Brain (WebSocket), 2. Browser Robot ↔ API Server (HTTP REST), 3. AI Brain ↔ API Server (HTTP REST), 4. AI Brain ↔ Ollama (HTTP), Component Relationships, Critical Implementation Paths, Database Schema, Design Patterns (+19 more)

### Community 18 - "graphify_to_mermaid.py"
Cohesion: 0.27
Nodes (11): generate_community_mermaid(), generate_god_nodes_mermaid(), main(), Any, Graphify to Mermaid Exporter  Reads graphify-out/graph.json and generates clean,, Sanitize node IDs for Mermaid compatibility., Sanitize labels for Mermaid node boxes., Generate Mermaid flowchart grouped by communities (filtering to code nodes only) (+3 more)

### Community 19 - "crawl_helper.py"
Cohesion: 0.22
Nodes (8): build_element_fingerprint(), generate_page_summary(), html_to_llm_markdown(), Any, Crawl4AI Helper Module for LLM Markdown Page Understanding & Semantic Fingerprin, Convert raw HTML DOM into clean, noise-free LLM Markdown.     Strips scripts, st, Extract a concise 1-2 sentence page summary from LLM Markdown content., Build a rich semantic fingerprint for recorded elements.     Includes tag, role,

### Community 20 - "AI Assistant Core Rules"
Cohesion: 0.25
Nodes (7): 1. Documentation & Code Synchronization, 2. Memory Bank Maintenance, 3. Code Quality & Style, 4. Testing & Verification, 5. Dependency Management, 6. Safety & Permissions, AI Assistant Core Rules

### Community 22 - "crud.py"
Cohesion: 0.06
Nodes (52): Automation, AutomationConfig, AutomationCreate, AutomationUpdate, ConfigCreate, ConfigUpdate, ExecutionHistory, ScheduleCreate (+44 more)

### Community 23 - "app.js"
Cohesion: 0.20
Nodes (33): api(), automationNameFor(), bindEvents(), clearSession(), confirmDelete(), confirmRun(), escapeHtml(), handleApiKeySubmit() (+25 more)

### Community 24 - "Tech Context — WebAI Platform"
Cohesion: 0.06
Nodes (32): 1. Install ODBC Driver 17 for SQL Server, 2. Create Database, 3. Install Python Dependencies, 4. Initialize Database Tables, 5. Pull Ollama Model, Additional (for data extraction features), AI Server (optional env vars, with defaults), Dashboard Server (optional env vars, with defaults) (+24 more)

### Community 25 - "PlaybackProcessManager"
Cohesion: 0.09
Nodes (17): Popen, PlaybackProcessManager, PlaybackRun, Path, Playback subprocess lifecycle manager for the WebAI dashboard server.  The das, Return True while at least one playback subprocess is still alive., Return execution IDs of all currently-running playback subprocesses., Mark orphan RUNNING executions as FAILED.          Historical executions stay (+9 more)

### Community 26 - "Any"
Cohesion: 0.16
Nodes (19): _buffer_log(), delete_automation(), get_automation(), get_execution_logs(), list_automations(), list_executions(), list_runs(), _proxy_get() (+11 more)

### Community 27 - "run_automation_endpoint"
Cohesion: 0.13
Nodes (18): BaseModel, _flush_orchestration_logs(), LoginPayload, Path, Payload for starting a new interactive recording session from the dashboard., Result of a successfully dispatched automation run., Choose the Python interpreter for the playback subprocess.      Prefers the Pl, Best-effort batch upload of dashboard orchestration logs to the API server. (+10 more)

### Community 28 - "dashboard_server.py"
Cohesion: 0.18
Nodes (13): dashboard_health(), _probe_http(), _probe_tcp(), _probe_ws(), WebAI Dashboard Server — web UI + orchestration API.  This FastAPI server is t, Return True when a TCP connection to host:port succeeds., Probe a WebSocket server by sending a minimal HTTP request.      Unlike a raw, Return True when an HTTP GET to url returns any non-server-error status. (+5 more)

### Community 29 - "MonkeyPatch"
Cohesion: 0.24
Nodes (5): MonkeyPatch, Proxy endpoints forward auth headers and surface upstream errors., Run endpoint orchestration (subprocess spawn stubbed out)., TestProxyBehavior, TestRunEndpoint

### Community 30 - "test_dashboard_enhancements.py"
Cohesion: 0.23
Nodes (11): _api_online(), _dashboard_online(), main(), E2E test: Dashboard enhancements (delete + stale reconciliation).  Playwright, Run all enhancement tests., Check if the dashboard server is reachable., Check if the API server is reachable., Test that the delete button appears and opens a confirmation modal. (+3 more)

### Community 31 - "test_ws_probe_fix.py"
Cohesion: 0.24
Nodes (11): bare_tcp_probe(), garbage_probe(), http_get_probe(), main(), E2E verification for the WebSocket probe-tolerance fix in webai_local_server/lo, Connect and close without sending a single byte (old _probe_tcp)., Send a plain HTTP/1.1 GET (dashboard _probe_ws) and return the response., Send non-HTTP garbage bytes (genuine malformed request). (+3 more)

### Community 32 - ".json"
Cohesion: 0.23
Nodes (5): FakeResponse, Any, End-to-end proxy chain against a real API server (no browser launched)., Minimal stand-in for `requests.Response` used by monkeypatched stubs., TestLiveApiServer

### Community 33 - "Implementation Plan — WebAI Front-End Automation Dashboard"
Cohesion: 0.18
Nodes (10): 1. Objective, 2. Architecture, 3. API Contract (Dashboard Server), 4. CLI Refactoring (Workflow Requirement), 5. Front-End, 6. Environment & Dependencies, 7. QA Plan, 8. Documentation Plan (Doc Agent) (+2 more)

### Community 34 - "benchmark_modal_speed.py"
Cohesion: 0.28
Nodes (8): _api_online(), main(), Any, Benchmark: Modal rendering response time.  Measures the latency of the endpoin, Return the response time in milliseconds for a GET request., Check if the API server is reachable., Run the benchmark and print results., _time_get()

### Community 35 - "_safe_detail"
Cohesion: 0.25
Nodes (8): Response, UploadFile, import_automation(), login(), Extract an error detail payload from an upstream API response.      Args:, Proxy login to the API server and return the user's API key.      The front-en, Import a recorded_steps.json file as a new database automation.      Replaces, _safe_detail()

### Community 36 - "test_dashboard_recording.py"
Cohesion: 0.36
Nodes (7): _dashboard_online(), main(), Test suite for the Dashboard Interactive Recording endpoint.  Tests:   1. POST /, Test 401 when X-API-Key is missing., Test 422 when required fields are missing., test_recording_endpoint_auth(), test_recording_endpoint_validation()

### Community 37 - "test_dashboard_api.py"
Cohesion: 0.25
Nodes (5): _api_server_online(), QA suite for the WebAI Dashboard Server (webai_dashboard).  Covers two layers:, Health endpoint always reports dashboard status plus dependency probes., Return True when a real API server answers on WEBAI_API_URL., TestHealthEndpoint

### Community 38 - "validate_steps_payload"
Cohesion: 0.36
Nodes (4): Step-payload validation for the import endpoint., TestValidateStepsPayload, Validate an uploaded recording payload.      Args:         steps: Parsed JSON, validate_steps_payload()

### Community 39 - "Decision Log — WebAI Platform"
Cohesion: 0.29
Nodes (6): Decision 14: Conditional Branching Implementation (Pending), Decision 15: Jira Integration Approach (Pending), Decision 16: Variable Persistence Model (Pending), Decision Log — WebAI Platform, Future Decisions Pending, Related Documents

### Community 40 - "Decision 1: Multi-Locator Fallback vs Single Selector"
Cohesion: 0.29
Nodes (7): Alternatives Considered, Context, Decision, Decision 1: Multi-Locator Fallback vs Single Selector, Impact, Implementation, Rationale

### Community 41 - "Decision 2: LLM Bypass for Click/Type When Locators Exist"
Cohesion: 0.29
Nodes (7): Alternatives Considered, Code Location, Context, Decision 2: LLM Bypass for Click/Type When Locators Exist, Decision, Impact, Rationale

### Community 42 - "test_e2e_recording_full.py"
Cohesion: 0.48
Nodes (6): _check_servers(), main(), _obtain_api_key(), Full E2E Verification for Dashboard Recording Feature.  Prerequisites:   API Ser, test_api_e2e_record_dispatch(), test_ui_e2e_recording_modal()

### Community 43 - "derive_base_url"
Cohesion: 0.38
Nodes (4): Base-URL derivation from recorded steps., TestDeriveBaseUrl, derive_base_url(), Derive an automation's starting URL from its recorded steps.      Args:

### Community 44 - "Decision 4: Fernet Symmetric Encryption for Credentials"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision, Decision 4: Fernet Symmetric Encryption for Credentials, Impact, Rationale

### Community 45 - "Decision 5: IST Timezone Computed Columns"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision, Decision 5: IST Timezone Computed Columns, Impact, Rationale

### Community 46 - "Decision 6: Batch Logging vs Individual Log Entries"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision, Decision 6: Batch Logging vs Individual Log Entries, Impact, Rationale

### Community 47 - "Decision 7: WebSocket for AI Server vs HTTP Polling"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision, Decision 7: WebSocket for AI Server vs HTTP Polling, Impact, Rationale

### Community 48 - "Decision 8: Task Normalization Before LLM"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision, Decision 8: Task Normalization Before LLM, Impact, Rationale

### Community 49 - "Decision 9: Action Normalization (LLM Tolerance)"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision, Decision 9: Action Normalization (LLM Tolerance), Impact, Rationale

### Community 50 - "Decision 10: Plan Caching Disabled"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision 10: Plan Caching Disabled, Decision, Impact, Rationale

### Community 51 - "Decision 11: Right-Click Context Menu for Extraction"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision 11: Right-Click Context Menu for Extraction, Decision, Impact, Rationale

### Community 52 - "Decision 12: Table Extraction via Injected JavaScript"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision 12: Table Extraction via Injected JavaScript, Decision, Impact, Rationale

### Community 53 - "Decision 13: Database-Backed Orchestration vs File-Based"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision 13: Database-Backed Orchestration vs File-Based, Decision, Impact, Rationale

### Community 54 - "Decision 17: Front-End Dashboard as Orchestration Layer (Not API Server Extension)"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision 17: Front-End Dashboard as Orchestration Layer (Not API Server Extension), Decision, Impact, Rationale

### Community 55 - "Decision 3: Local Ollama vs Cloud LLM API"
Cohesion: 0.33
Nodes (6): Alternatives Considered, Context, Decision 3: Local Ollama vs Cloud LLM API, Decision, Impact, Rationale

### Community 56 - "build_task_text"
Cohesion: 0.40
Nodes (4): generated_task.txt content generation for guided playback., TestBuildTaskText, build_task_text(), Build the `generated_task.txt` content consumed by the guided playback client.

### Community 58 - "Decision 18: Probe-Tolerant WebSocket Server (process_request + logging filter)"
Cohesion: 0.40
Nodes (5): Alternatives Considered, Context, Decision 18: Probe-Tolerant WebSocket Server (process_request + logging filter), Decision, Impact

### Community 60 - "test_dashboard_ui.py"
Cohesion: 0.67
Nodes (3): check(), main(), Browser-driven UI test for the WebAI Dashboard front-end (scratch QA tool).  D

### Community 61 - "migrate_indexes.py"
Cohesion: 0.50
Nodes (3): migrate_indexes(), Database Migration: Add performance indexes for modal rendering.  Creates explic, Create missing performance indexes on execution_logs and execution_history.

## Knowledge Gaps
- **222 isolated node(s):** `1. Objective`, `2. Architecture`, `3. API Contract (Dashboard Server)`, `4. CLI Refactoring (Workflow Requirement)`, `5. Front-End` (+217 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Decision Log — WebAI Platform` connect `Decision Log — WebAI Platform` to `Decision 1: Multi-Locator Fallback vs Single Selector`, `Decision 2: LLM Bypass for Click/Type When Locators Exist`, `Decision 4: Fernet Symmetric Encryption for Credentials`, `Decision 5: IST Timezone Computed Columns`, `Decision 6: Batch Logging vs Individual Log Entries`, `Decision 7: WebSocket for AI Server vs HTTP Polling`, `Decision 8: Task Normalization Before LLM`, `Decision 9: Action Normalization (LLM Tolerance)`, `Decision 10: Plan Caching Disabled`, `Decision 11: Right-Click Context Menu for Extraction`, `Decision 12: Table Extraction via Injected JavaScript`, `Decision 13: Database-Backed Orchestration vs File-Based`, `Decision 17: Front-End Dashboard as Orchestration Layer (Not API Server Extension)`, `Decision 3: Local Ollama vs Cloud LLM API`, `Decision 18: Probe-Tolerant WebSocket Server (process_request + logging filter)`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `TaskDone` connect `Immediate Next Steps (If User Requests)` to `fallback_helpers.py`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **What connects `1. Objective`, `2. Architecture`, `3. API Contract (Dashboard Server)` to the rest of the system?**
  _222 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Recent Work Completed` be split into smaller, more focused modules?**
  _Cohesion score 0.09523809523809523 - nodes in this community are weakly interconnected._
- **Should `Active Context — WebAI Platform` be split into smaller, more focused modules?**
  _Cohesion score 0.06060606060606061 - nodes in this community are weakly interconnected._
- **Should `Open Questions / Decisions Pending` be split into smaller, more focused modules?**
  _Cohesion score 0.11956521739130435 - nodes in this community are weakly interconnected._
- **Should `Immediate Next Steps (If User Requests)` be split into smaller, more focused modules?**
  _Cohesion score 0.08677098150782361 - nodes in this community are weakly interconnected._