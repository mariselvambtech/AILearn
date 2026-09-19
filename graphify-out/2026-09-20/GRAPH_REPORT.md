# Graph Report - AILearn  (2026-09-19)

## Corpus Check
- 276 files · ~270,440 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1343 nodes · 2052 edges · 91 communities (80 shown, 11 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 28 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a36a3217`
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
- Page
- Path
- HITLPlugin
- Step
- handle_client
- ai.py
- HITLPlugin
- Any
- _compact_context
- AudioCapturePlugin
- test_hitl_plugin.py
- test_phase8_autonomous_handoff.py
- test_run_hybrid.py
- MockPage
- _compact_context
- recorder.py
- Any
- Page
- MockPage
- dashboard_health
- test_dynamic_popup_handling.py
- TaskDone
- _prune_dom_snapshot
- Exception
- Path

## God Nodes (most connected - your core abstractions)
1. `Step` - 28 edges
2. `WebRecorder` - 27 edges
3. `handle_client()` - 26 edges
4. `SkillSynthesizer` - 22 edges
5. `get_cdp()` - 21 edges
6. `Recent Work Completed` - 20 edges
7. `Decision Log — WebAI Platform` - 20 edges
8. `click()` - 19 edges
9. `SkillExecutor` - 18 edges
10. `bindEvents()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `test_skill_synthesizer_expected_context()` --calls--> `SkillSynthesizer`  [INFERRED]
  WEBAI_AUTOMATION/scratch/test_semantic_verification.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/skill_synthesizer.py
- `run_e2e_test()` --indirect_call--> `handle_client()`  [INFERRED]
  WEBAI_AUTOMATION/scratch/test_e2e_server_kimi.py → WEBAI_AUTOMATION/webai_local_server/webai_local_server/local_webai_server_guided.py
- `test_run_skill_cli_resolution()` --calls--> `resolve_skill_path()`  [INFERRED]
  WEBAI_AUTOMATION/scratch/test_multi_skill_library.py → WEBAI_AUTOMATION/webai_playwright_python/run_skill.py
- `test_step_schema_extension()` --calls--> `Step`  [EXTRACTED]
  WEBAI_AUTOMATION/scratch/test_semantic_verification.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/recorder.py
- `test_click_with_fallback_semantic_guard()` --calls--> `click_with_fallback()`  [INFERRED]
  WEBAI_AUTOMATION/scratch/test_semantic_verification.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/fallback_helpers.py

## Import Cycles
- None detected.

## Communities (91 total, 11 thin omitted)

### Community 0 - "Recent Work Completed"
Cohesion: 0.05
Nodes (40): 1. Conditional Branching (Future Enhancement), 2. Variable Storage for Conditions, 3. Explicit Page Validation, 4. LOCATOR_PRIORITY Inconsistency, 5. Shim Module Bug, 7 Web Failure Scenario Fortification & Test Suite Verification ✅, Active Context — WebAI Platform, Active Files (Most Recently Modified) (+32 more)

### Community 1 - "Active Context — WebAI Platform"
Cohesion: 0.05
Nodes (40): Active Context  WebAI Platform, Active Context  WebAI Platform, Active Context  WebAI Platform, Client & Server Multi-Locator Priority Unification (13 Strategies) ✅, Current Session (2026-07-29), Current Session (2026-07-29), Current Session (2026-09-19), Dashboard Enhancements & Performance Optimization (+32 more)

### Community 2 - "Open Questions / Decisions Pending"
Cohesion: 0.12
Nodes (19): Phase 1 Test Suite: test_event_bus_core.py  Tests the WebRecorder Event Bus pub/, Tests that WebRecorder correctly broadcasts click and type events     with full, Tests that if a subscriber plugin raises an exception during execution,     the, Tests that DataExtractionPlugin subscribes to extract channel and safely handles, test_data_extraction_plugin_subscription(), test_event_bus_click_and_type_events(), test_plugin_exception_isolation(), DataExtractionPlugin (+11 more)

### Community 3 - "Immediate Next Steps (If User Requests)"
Cohesion: 0.09
Nodes (24): Test suite for verifying all 13 locator strategies in fallback_helpers.py.  This, Verify _create_locator_obj constructs valid locators for all 13 types., Verify click_with_fallback works with all 13 locator types including alt, aria-l, Verify type_with_fallback works with input locators including aria-label, title,, Verify extract_with_fallback extracts text/attribute for aria-label, alt, title,, Verify LOCATOR_PRIORITY is exact 13-key 0-indexed dict matching server., test_click_with_fallback_all_13_types(), test_create_locator_obj_all_13_types() (+16 more)

### Community 4 - "Current Session (2026-07-18)"
Cohesion: 0.18
Nodes (19): buffer_log(), create_execution_record(), fetch_automation_steps(), flush_logs(), log(), main(), Run automation from API database - Simple file-based approach.  This script de, Save steps to JSON file (+11 more)

### Community 8 - "test_cdp_fixes.py"
Cohesion: 0.17
Nodes (11): Test suite for verifying CDP and Playwright Actions fixes, Test that cdp.get_dom_snapshot works correctly, Test that playwright_actions.get_snapshot works correctly, Test that cdp.get_interactive_elements works correctly, Test that playwright_actions.get_dom_snapshot works correctly, Test that playwright_actions.get_interactive_elements works correctly, test_cdp_get_dom_snapshot(), test_cdp_get_interactive_elements() (+3 more)

### Community 9 - "fallback_helpers.py"
Cohesion: 0.25
Nodes (7): _compact_context(), _extract_json_array(), _looks_like_navigation_issue(), _looks_like_not_found(), Compact “UI inventory” to reduce hallucinations., Strict parser: expects a JSON array; extracts first [...] if extra text exists., Proxy module providing backwards compatibility for tests importing local_webai_s

### Community 10 - "How to Run the WebAI Automation Project"
Cohesion: 0.20
Nodes (9): 1. Start the API Server (Terminal 1), 2. Start the AI Server (Terminal 2), 3. Start the Ollama Server (Terminal 3), 4. Run the Client Script (Terminal 4), 5. (Optional) Start the Web UI Dashboard (Terminal 5), 6. (Optional) Graphify update and mermaid diagram update, Available Client Scripts:, How to Run the WebAI Automation Project (+1 more)

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
Nodes (28): 1. Browser Robot ↔ AI Brain (WebSocket), 2. Browser Robot ↔ API Server (HTTP REST), 3. AI Brain ↔ API Server (HTTP REST), 4. AI Brain ↔ Ollama (HTTP), Component Relationships, Critical Implementation Paths, Database Schema, Design Patterns (+20 more)

### Community 18 - "graphify_to_mermaid.py"
Cohesion: 0.27
Nodes (11): generate_community_mermaid(), generate_god_nodes_mermaid(), main(), Any, Graphify to Mermaid Exporter  Reads graphify-out/graph.json and generates clean,, Sanitize node IDs for Mermaid compatibility., Sanitize labels for Mermaid node boxes., Generate Mermaid flowchart grouped by communities (filtering to code nodes only) (+3 more)

### Community 19 - "crawl_helper.py"
Cohesion: 0.22
Nodes (8): build_element_fingerprint(), generate_page_summary(), html_to_llm_markdown(), Any, Crawl4AI Helper Module for LLM Markdown Page Understanding & Semantic Fingerprin, Convert raw HTML DOM into clean, noise-free LLM Markdown.     Strips scripts, st, Extract a concise 1-2 sentence page summary from LLM Markdown content., Build a rich semantic fingerprint for recorded elements.     Includes tag, role,

### Community 20 - "AI Assistant Core Rules"
Cohesion: 0.14
Nodes (13): 10. Strict Prompting Contracts, 11. Autonomous E2E Validation Loop (Self-Healing), 1. Documentation & Code Synchronization, 2. Memory Bank Maintenance, 3. Code Quality & Style, 4. Testing & Verification, 5. Dependency Management, 6. Safety & Permissions (+5 more)

### Community 21 - "Page"
Cohesion: 0.10
Nodes (17): TDVC Test Harness for AudioAligner Temporal Alignment Logic. Verifies time windo, test_audio_alignment_math(), TDVC Test Harness for AudioAligner VAD & Anti-Hallucination Configuration. Verif, Assert that AudioAligner.transcribe_audio calls model.transcribe with:     - vad, Assert that AudioAligner defaults to 'base.en' and falls back gracefully to 'bas, test_audio_vad_transcribe_kwargs(), test_model_upgrade_and_fallback(), ask_yes_no() (+9 more)

### Community 22 - "crud.py"
Cohesion: 0.06
Nodes (52): Automation, AutomationConfig, AutomationCreate, AutomationUpdate, ConfigCreate, ConfigUpdate, ExecutionHistory, ScheduleCreate (+44 more)

### Community 23 - "app.js"
Cohesion: 0.19
Nodes (36): api(), automationNameFor(), bindEvents(), clearSession(), confirmDelete(), confirmRun(), escapeHtml(), handleApiKeySubmit() (+28 more)

### Community 24 - "Tech Context — WebAI Platform"
Cohesion: 0.06
Nodes (32): 1. Install ODBC Driver 17 for SQL Server, 2. Create Database, 3. Install Python Dependencies, 4. Initialize Database Tables, 5. Pull Ollama Model, Additional (for data extraction features), AI Server (optional env vars, with defaults), Dashboard Server (optional env vars, with defaults) (+24 more)

### Community 25 - "PlaybackProcessManager"
Cohesion: 0.09
Nodes (17): Popen, PlaybackProcessManager, PlaybackRun, Path, Playback subprocess lifecycle manager for the WebAI dashboard server.  The das, Return True while at least one playback subprocess is still alive., Return execution IDs of all currently-running playback subprocesses., Mark orphan RUNNING executions as FAILED.          Historical executions stay (+9 more)

### Community 26 - "Any"
Cohesion: 0.20
Nodes (15): get_automation(), get_execution_logs(), list_automations(), list_executions(), list_runs(), _proxy_get(), Any, Validate that the caller supplied an X-API-Key header.      Args:         x_a (+7 more)

### Community 27 - "run_automation_endpoint"
Cohesion: 0.22
Nodes (9): BaseModel, LoginPayload, Payload for starting a new interactive recording session from the dashboard., Result of a successfully dispatched automation run., Credentials forwarded to the API server's /auth/login endpoint., Payload for triggering an automation run from the dashboard., RecordRequest, RunRequest (+1 more)

### Community 28 - "dashboard_server.py"
Cohesion: 0.20
Nodes (11): execute_skill_endpoint(), list_skills(), _probe_tcp(), WebAI Dashboard Server — web UI + orchestration API.  This FastAPI server is t, Sanitize a skill filename using os.path.basename to guard against directory trav, Payload for triggering dynamic execution of a synthesized AI skill., Return True when a TCP connection to host:port succeeds., List all synthesized AI skills available in skills/ directory and legacy root. (+3 more)

### Community 29 - "MonkeyPatch"
Cohesion: 0.05
Nodes (27): MonkeyPatch, _api_server_online(), FakeResponse, Any, QA suite for the WebAI Dashboard Server (webai_dashboard).  Covers two layers:, generated_task.txt content generation for guided playback., X-API-Key header enforcement on protected endpoints., Health endpoint always reports dashboard status plus dependency probes. (+19 more)

### Community 30 - "test_dashboard_enhancements.py"
Cohesion: 0.23
Nodes (11): _api_online(), _dashboard_online(), main(), E2E test: Dashboard enhancements (delete + stale reconciliation).  Playwright, Run all enhancement tests., Check if the dashboard server is reachable., Check if the API server is reachable., Test that the delete button appears and opens a confirmation modal. (+3 more)

### Community 31 - "test_ws_probe_fix.py"
Cohesion: 0.24
Nodes (11): bare_tcp_probe(), garbage_probe(), http_get_probe(), main(), E2E verification for the WebSocket probe-tolerance fix in webai_local_server/lo, Connect and close without sending a single byte (old _probe_tcp)., Send a plain HTTP/1.1 GET (dashboard _probe_ws) and return the response., Send non-HTTP garbage bytes (genuine malformed request). (+3 more)

### Community 32 - ".json"
Cohesion: 0.12
Nodes (5): MockKeyboard, MockLocator, MockPage, TDVC Test Suite for run_hybrid.py & TaskId Handoff Fix (Rule 7) Verifies: 1. tas, test_action_listener_loop_mock()

### Community 33 - "Implementation Plan — WebAI Front-End Automation Dashboard"
Cohesion: 0.18
Nodes (10): 1. Objective, 2. Architecture, 3. API Contract (Dashboard Server), 4. CLI Refactoring (Workflow Requirement), 5. Front-End, 6. Environment & Dependencies, 7. QA Plan, 8. Documentation Plan (Doc Agent) (+2 more)

### Community 34 - "benchmark_modal_speed.py"
Cohesion: 0.28
Nodes (8): _api_online(), main(), Any, Benchmark: Modal rendering response time.  Measures the latency of the endpoin, Return the response time in milliseconds for a GET request., Check if the API server is reachable., Run the benchmark and print results., _time_get()

### Community 35 - "_safe_detail"
Cohesion: 0.18
Nodes (11): Response, delete_automation(), login(), Extract an error detail payload from an upstream API response.      Args:, Proxy login to the API server and return the user's API key.      The front-en, Proxy user registration to the API server., Delete an automation and its dependent records via the API server.      Proxie, Registration details forwarded to the API server's /auth/register endpoint. (+3 more)

### Community 36 - "test_dashboard_recording.py"
Cohesion: 0.36
Nodes (7): _dashboard_online(), main(), Test suite for the Dashboard Interactive Recording endpoint.  Tests:   1. POST /, Test 401 when X-API-Key is missing., Test 422 when required fields are missing., test_recording_endpoint_auth(), test_recording_endpoint_validation()

### Community 37 - "test_dashboard_api.py"
Cohesion: 0.10
Nodes (21): action_listener_loop(), load_local_skills(), main(), Any, End-to-End Hybrid Test Orchestrator for WebAI Platform.  1. Accepts hardcoded pr, Listens for incoming AI action commands (command-request) from local_webai_serve, Discovers and loads synthesized skills from JSON files in the workspace., TDVC Test Suite for Phase 6: Semantic Intent Router & Agentic Handoff Engine (Ru (+13 more)

### Community 38 - "validate_steps_payload"
Cohesion: 0.10
Nodes (23): Headless E2E Test for SkillExecutor Playwright Execution. Verifies loading synth, test_e2e_skill_playback(), TDVC Test Harness for Semantic Verification & Conditional Assertions (Decision 1, test_rich_snapshot_semantic_matching(), test_semantic_mismatch_raises_error(), test_skill_executor_assert_handler(), test_skill_executor_template_resolution(), test_skill_synthesizer_expected_context() (+15 more)

### Community 39 - "Decision Log — WebAI Platform"
Cohesion: 0.14
Nodes (13): Context, Context, Decision, Decision 14: Semantic Verification & Conditional Assertions, Decision 15: Jira Integration Approach (Pending), Decision 16: Variable Persistence Model (Pending), Decision, Decision Log — WebAI Platform (+5 more)

### Community 40 - "Decision 1: Multi-Locator Fallback vs Single Selector"
Cohesion: 0.29
Nodes (7): Alternatives Considered, Context, Decision 1: Multi-Locator Fallback vs Single Selector, Decision, Impact, Implementation, Rationale

### Community 41 - "Decision 2: LLM Bypass for Click/Type When Locators Exist"
Cohesion: 0.29
Nodes (7): Alternatives Considered, Code Location, Context, Decision 2: LLM Bypass for Click/Type When Locators Exist, Decision, Impact, Rationale

### Community 42 - "test_e2e_recording_full.py"
Cohesion: 0.48
Nodes (6): _check_servers(), main(), _obtain_api_key(), Full E2E Verification for Dashboard Recording Feature.  Prerequisites:   API Ser, test_api_e2e_record_dispatch(), test_ui_e2e_recording_modal()

### Community 43 - "derive_base_url"
Cohesion: 0.24
Nodes (7): UploadFile, Base-URL derivation from recorded steps., TestDeriveBaseUrl, derive_base_url(), import_automation(), Derive an automation's starting URL from its recorded steps.      Args:, Import a recorded_steps.json file as a new database automation.      Replaces

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
Nodes (6): Alternatives Considered, Context, Decision, Decision 3: Local Ollama vs Cloud LLM API, Impact, Rationale

### Community 56 - "build_task_text"
Cohesion: 0.08
Nodes (60): ElementHandle, Locator, ScrollType, cdp_element_to_playwright_handle(), click(), click_and_input_cdp_element(), click_and_input_location(), click_by_label() (+52 more)

### Community 58 - "Decision 18: Probe-Tolerant WebSocket Server (process_request + logging filter)"
Cohesion: 0.40
Nodes (5): Alternatives Considered, Context, Decision 18: Probe-Tolerant WebSocket Server (process_request + logging filter), Decision, Impact

### Community 59 - "TestImportValidation"
Cohesion: 0.07
Nodes (18): FakeCDPSession, FakeContext, FakeKeyboard, FakeMouse, FakePage, FakePageForWindow, Test suite for the WebAI Playwright Client.  This module contains tests verify, # NOTE: webai_playwright/__init__.py exports `ai` function which can shadow subm (+10 more)

### Community 60 - "test_dashboard_ui.py"
Cohesion: 0.67
Nodes (3): check(), main(), Browser-driven UI test for the WebAI Dashboard front-end (scratch QA tool).  D

### Community 61 - "migrate_indexes.py"
Cohesion: 0.50
Nodes (3): migrate_indexes(), Database Migration: Add performance indexes for modal rendering.  Creates explic, Create missing performance indexes on execution_logs and execution_history.

### Community 63 - "Page"
Cohesion: 0.12
Nodes (11): Attach plugin to WebRecorder instance by subscribing to event bus., Any, Page, Event Bus Core Engine for Browser Recording.     Intercepts raw CDP user interac, Start recording session and broadcast recording_started event to plugins., Register and attach a plugin to this recorder event bus., Subscribe a listener callback to a specific event or '*' for all events., Unsubscribe a listener callback. (+3 more)

### Community 64 - "Path"
Cohesion: 0.13
Nodes (13): test_click_with_fallback_semantic_guard(), TDVC Test Suite: Verifying Structural CSS Demotion (:nth-child / :nth-of-type) i, DOM Scenario:     - Container with 3 children:       1. Header       2. <div cla, test_structural_css_demoted_behind_semantic_text(), click_with_fallback(), Try multiple locators in priority order until one successfully clicks.     Fort, extract_rich_snapshot(), Any (+5 more)

### Community 65 - "HITLPlugin"
Cohesion: 0.06
Nodes (30): Any, Page, Step, create_mock_page(), Any, TDVC Test Harness for HITLPlugin & Event Bus Interception (Phase 10 & 11). Verif, Create a mocked Playwright Page object simulating Observer Mode resolution., Assert HITLPlugin packages observer resolution data and transcribed voice into p (+22 more)

### Community 66 - "Step"
Cohesion: 0.06
Nodes (30): TDVC Test Suite for Multi-Skill Library Architecture with Mandatory Safeguards:, Validates run_skill path resolution supports explicit sys.argv[1] or default fal, Validates dependency-free slugification of human-readable skill names into safe, Validates that save_skill creates skills/ directory, saves skills/{slug}.json, a, Validates that sanitize_skill_filename strips directory traversal characters., Validates that skills/*.json takes precedence and mirror synthesized_skill.json, Validates that SkillExecutePayload accepts and validates a filename string., test_run_skill_cli_resolution() (+22 more)

### Community 67 - "handle_client"
Cohesion: 0.09
Nodes (28): run_e2e_test(), build_subgoal_prompt(), extract_primary_open_url(), extract_success_expectations(), _extract_urls(), _fmt_target(), _format_last_errors(), get_query_param() (+20 more)

### Community 68 - "ai.py"
Cohesion: 0.17
Nodes (32): CDPSession, RuntimeError, clear_element(), click_element(), detach(), execute_script(), find_elements(), focus_element() (+24 more)

### Community 69 - "HITLPlugin"
Cohesion: 0.16
Nodes (10): HITLPlugin, Any, Page, Transcribe PCM WAV audio using faster-whisper., Main entrypoint called when human intervention is required.         1. Speaks TT, Plugin that manages Human-in-the-Loop (HITL) fallback interventions., Attach to WebRecorder event bus and subscribe to intervention requests., Event bus handler when human intervention is triggered. (+2 more)

### Community 70 - "Any"
Cohesion: 0.15
Nodes (17): build_system_prompt(), cache_get_plan(), _cache_key(), cache_put_plan(), _load_cache(), Any, Save the extracted data to a Microsoft Word document using python-docx., Save the extracted data to a simple text file.          This fulfills the extr (+9 more)

### Community 71 - "_compact_context"
Cohesion: 0.15
Nodes (13): LogRecord, _EmptyProbeNoiseFilter, _env(), _http_health_response(), jdump(), llm_plan_chat(), main(), ollama_chat() (+5 more)

### Community 72 - "AudioCapturePlugin"
Cohesion: 0.13
Nodes (10): TDVC Test Harness for AudioCapturePlugin & WebRecorder Synchronization. Verifies, test_audio_plugin_synchronization(), AudioCapturePlugin, Any, Audio Capture Plugin for WebAI Playwright Recorder.  Provides background audio r, Plugin that captures background audio during WebRecorder sessions.     Subscribe, Attach to WebRecorder event bus and subscribe to lifecycle events., Event handler for session start. (+2 more)

### Community 73 - "test_hitl_plugin.py"
Cohesion: 0.10
Nodes (23): TDVC Test Suite for Phase 15: Kimi K3 Provider Integration.  Covers: 1. Provider, llm_plan_chat routes to kimi_chat when LLM_PROVIDER is 'kimi_k3', else to ollama, When a recorded step has locators, guided execution must NEVER invoke LLM (Ollam, Text-only message should produce a clean user message., Multimodal message must include OpenAI-compatible text and image_url blocks., Reasoning content and tool calls must be preserved in assistant envelopes for mu, kimi_chat must call OpenAI-compatible /chat/completions via httpx.AsyncClient an, test_format_vision_message_text_only() (+15 more)

### Community 74 - "test_phase8_autonomous_handoff.py"
Cohesion: 0.22
Nodes (10): parse_llm_plan(), TDVC Test Suite for Phase 8: Autonomous Continuation & Spatial Graph Routing (Ru, Helper function matching the server's new multi-format plan parser., test_build_spatial_prompt(), test_extract_coords_json(), test_multi_format_plan_parsing(), _build_spatial_prompt(), _extract_coords() (+2 more)

### Community 75 - "test_run_hybrid.py"
Cohesion: 0.53
Nodes (5): _evaluate_plan_reset(), Evaluates if the LLM action plan queue should be flushed based on execution stat, test_plan_flushed_on_hitl_resolution(), test_plan_flushed_on_max_failures(), test_plan_retained_on_normal_success()

### Community 76 - "MockPage"
Cohesion: 0.22
Nodes (11): _buffer_log(), _flush_orchestration_logs(), Path, Choose the Python interpreter for the playback subprocess.      Prefers the Pl, Best-effort batch upload of dashboard orchestration logs to the API server., Append one orchestration log entry to the buffer (source='api')., Trigger browser playback of a database-backed automation.      Replaces the in, Launch an interactive browser session to record a new automation.      Spawns (+3 more)

### Community 77 - "_compact_context"
Cohesion: 0.16
Nodes (20): test_execute_command_fallback_single_page(), test_execute_command_uses_active_page_from_context(), ai(), ai_sync(), ClientError, _dispatch_command(), _execute_command(), _make_error_message() (+12 more)

### Community 78 - "recorder.py"
Cohesion: 0.33
Nodes (3): main(), Human-in-the-Loop (HITL) Interactive Learning Plugin for WebAI Playwright Record, Browser Interaction Recorder utilizing Chrome DevTools Protocol (CDP).  This mod

### Community 83 - "MockPage"
Cohesion: 0.24
Nodes (4): MockKeyboard, MockPage, TDVC Test Suite for Phase 7: The Browser Handoff Engine (Rule 7) Verifies: 1. Br, test_browser_handoff_lifecycle()

### Community 84 - "dashboard_health"
Cohesion: 0.33
Nodes (6): dashboard_health(), _probe_http(), _probe_ws(), Probe a WebSocket server by sending a minimal HTTP request.      Unlike a raw, Return True when an HTTP GET to url returns any non-server-error status., Report the health of the dashboard itself and its upstream dependencies.

### Community 85 - "test_dynamic_popup_handling.py"
Cohesion: 0.40
Nodes (4): TDVC Assertion:     Assert that when Playwright throws a TimeoutError during com, Mock an AI server loop where an injected Playwright TimeoutError is simulated, test_client_handles_playwright_timeout(), test_server_dynamic_popup_retry_on_timeout()

### Community 86 - "TaskDone"
Cohesion: 0.67
Nodes (3): Exception, Exception raised internally when the LLM outputs `action=done`.          This, TaskDone

## Knowledge Gaps
- **257 isolated node(s):** `Phase 18: Semantic Verification & Conditional Assertions (Decision 14, Rule 7 TDVC) ✅`, `Phase 17: Distil-Whisper Transcription & Vocabulary Priming Upgrade (`audio_aligner.py`) ✅`, `Phase 16: Multi-Skill Library Integration & Catalog Scanner (Rule 7 TDVC) ✅`, `Phase 15: Kimi K3 Provider Integration & Multimodal Visual-DOM Planning (Rule 7 TDVC) ✅`, `Phase 14: Audio Transcription VAD & Anti-Hallucination Upgrade (Rule 7 TDVC) ✅` (+252 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `handle_client()` connect `handle_client` to `ai.py`, `Any`, `_compact_context`, `fallback_helpers.py`, `test_phase8_autonomous_handoff.py`?**
  _High betweenness centrality (0.071) - this node is a cross-community bridge._
- **Why does `ClientError` connect `_compact_context` to `ai.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `test_hitl_plugin_graceful_degradation()` connect `HITLPlugin` to `ai.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `handle_client()` (e.g. with `run_e2e_test()` and `RuntimeError`) actually correct?**
  _`handle_client()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Phase 18: Semantic Verification & Conditional Assertions (Decision 14, Rule 7 TDVC) ✅`, `Phase 17: Distil-Whisper Transcription & Vocabulary Priming Upgrade (`audio_aligner.py`) ✅`, `Phase 16: Multi-Skill Library Integration & Catalog Scanner (Rule 7 TDVC) ✅` to the rest of the system?**
  _257 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Recent Work Completed` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Active Context — WebAI Platform` be split into smaller, more focused modules?**
  _Cohesion score 0.04878048780487805 - nodes in this community are weakly interconnected._