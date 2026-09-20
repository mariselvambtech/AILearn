# Graph Report - AILearn  (2026-09-20)

## Corpus Check
- 286 files · ~280,375 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1469 nodes · 2215 edges · 128 communities (113 shown, 15 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 32 edges (avg confidence: 0.68)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fe359f72`
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
- test_circuit_breaker_anti_loop.py
- Any
- Page
- MockPage
- dashboard_health
- save_synthesized_skill
- TaskDone
- _prune_dom_snapshot
- .json
- test_skill_mapping.py
- test_run_hybrid.py
- test_unified_13_locators.py
- skill_executor.py
- Any
- skill_synthesizer.py
- synthesize_automation_skill
- execute_skill_endpoint
- test_dashboard_skill_delete.py
- activeContext.md
- run_skill.py
- Exception
- Page
- Previous Session (2026-08-29)
- MockLocator
- tests/test_dashboard_api.py
- validate_steps_payload
- Previous Session (2026-08-27)
- _execute_command
- dash_synthesize.py
- .save_skill
- normalize_task
- build_task_text
- TestAuthEnforcement
- _env
- recorder.py
- Active Context  WebAI Platform
- Previous Session (2026-09-09)
- test_dynamic_popup_handling.py
- TestImportValidation
- Previous Session (2026-08-03)
- Decision 14: Semantic Verification & Conditional Assertions
- Decision 16: Read-First System Prompting & Anti-Loop Directives
- Decision 17: Action Deduplication Circuit Breaker & Proactive HITL Escalation
- Decision 18: Skill Synthesis (Auto-Saving Successful Agentic Workflows)
- Decision 19: Dashboard Skill Management (Delete Functionality)
- _buffer_log
- Path

## God Nodes (most connected - your core abstractions)
1. `Step` - 28 edges
2. `handle_client()` - 27 edges
3. `WebRecorder` - 27 edges
4. `SkillSynthesizer` - 26 edges
5. `Decision Log — WebAI Platform` - 24 edges
6. `get_cdp()` - 21 edges
7. `Recent Work Completed` - 20 edges
8. `SkillExecutor` - 20 edges
9. `click()` - 19 edges
10. `api()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `test_skill_synthesizer_expected_context()` --calls--> `SkillSynthesizer`  [INFERRED]
  WEBAI_AUTOMATION/scratch/test_semantic_verification.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/skill_synthesizer.py
- `test_click_with_fallback_semantic_guard()` --calls--> `click_with_fallback()`  [INFERRED]
  WEBAI_AUTOMATION/scratch/test_semantic_verification.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/fallback_helpers.py
- `run_e2e_test()` --indirect_call--> `handle_client()`  [INFERRED]
  WEBAI_AUTOMATION/scratch/test_e2e_server_kimi.py → WEBAI_AUTOMATION/webai_local_server/webai_local_server/local_webai_server_guided.py
- `test_semantic_verification_triggers_hitl_and_resumes()` --calls--> `SkillExecutor`  [EXTRACTED]
  WEBAI_AUTOMATION/scratch/test_hitl_interception.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/skill_executor.py
- `MockKeyboard` --uses--> `SkillExecutor`  [INFERRED]
  WEBAI_AUTOMATION/scratch/test_browser_handoff.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/skill_executor.py

## Import Cycles
- None detected.

## Communities (128 total, 15 thin omitted)

### Community 0 - "Recent Work Completed"
Cohesion: 0.05
Nodes (40): 1. Conditional Branching (Future Enhancement), 2. Variable Storage for Conditions, 3. Explicit Page Validation, 4. LOCATOR_PRIORITY Inconsistency, 5. Shim Module Bug, 7 Web Failure Scenario Fortification & Test Suite Verification ✅, Active Context — WebAI Platform, Active Files (Most Recently Modified) (+32 more)

### Community 1 - "Active Context — WebAI Platform"
Cohesion: 0.17
Nodes (12): Current Session (2026-09-20), Phase 17: Distil-Whisper Transcription & Vocabulary Priming Upgrade (`audio_aligner.py`) ✅, Phase 18: Semantic Verification & Conditional Assertions (Decision 14, Rule 7 TDVC) ✅, Phase 19: New Tab Automatic Context Switching (`skill_executor.py`) (Rule 7 TDVC) ✅, Phase 20: Semantic Verification HITL Interception & Auto-Resumption (Rule 7 TDVC, Rule 9) ✅, Phase 21: Automation-to-Skill Mapping & Nested Dashboard Rendering (Rule 7 TDVC, Rule 3) ✅, Phase 22: Decoupled Skill Synthesis Subprocess Execution (`dash_synthesize.py`) (Rule 3, Rule 7 TDVC) ✅, Phase 23: Windows Console UTF-8 & Global `safe_print` Wrapper (`skill_executor.py`, `dashboard_server.py`) (Rule 3) ✅ (+4 more)

### Community 2 - "Open Questions / Decisions Pending"
Cohesion: 0.12
Nodes (19): Phase 1 Test Suite: test_event_bus_core.py  Tests the WebRecorder Event Bus pub/, Tests that WebRecorder correctly broadcasts click and type events     with full, Tests that if a subscriber plugin raises an exception during execution,     the, Tests that DataExtractionPlugin subscribes to extract channel and safely handles, test_data_extraction_plugin_subscription(), test_event_bus_click_and_type_events(), test_plugin_exception_isolation(), DataExtractionPlugin (+11 more)

### Community 3 - "Immediate Next Steps (If User Requests)"
Cohesion: 0.15
Nodes (11): extract_table_data(), _get_active_page(), Helper functions for fallback extraction strategies.  This module provides heu, Try multiple locators in priority order to type text.          Args:, Try multiple locators in priority order to select a dropdown value.          A, Returns the active Playwright page/tab from context if multiple tabs exist., Extract table data with pagination support and robust change detection., Validate that the page URL contains the expected URL substring.          Args: (+3 more)

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
Cohesion: 0.06
Nodes (31): 1. Browser Robot ↔ AI Brain (WebSocket), 2. Browser Robot ↔ API Server (HTTP REST), 3. AI Brain ↔ API Server (HTTP REST), 4. AI Brain ↔ Ollama (HTTP), Action Deduplication Circuit Breaker Pattern (Decision 17), Autonomous Navigation Hardening Patterns, Component Relationships, Critical Implementation Paths (+23 more)

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
Cohesion: 0.18
Nodes (38): api(), automationNameFor(), bindEvents(), clearSession(), confirmDelete(), confirmRun(), deleteSkill(), escapeHtml() (+30 more)

### Community 24 - "Tech Context — WebAI Platform"
Cohesion: 0.06
Nodes (32): 1. Install ODBC Driver 17 for SQL Server, 2. Create Database, 3. Install Python Dependencies, 4. Initialize Database Tables, 5. Pull Ollama Model, Additional (for data extraction features), AI Server (optional env vars, with defaults), Dashboard Server (optional env vars, with defaults) (+24 more)

### Community 25 - "PlaybackProcessManager"
Cohesion: 0.09
Nodes (17): Popen, PlaybackProcessManager, PlaybackRun, Path, Playback subprocess lifecycle manager for the WebAI dashboard server.  The das, Return True while at least one playback subprocess is still alive., Return execution IDs of all currently-running playback subprocesses., Mark orphan RUNNING executions as FAILED.          Historical executions stay (+9 more)

### Community 26 - "Any"
Cohesion: 0.20
Nodes (15): delete_skill_endpoint(), get_automation(), get_execution_logs(), list_automations(), list_executions(), _proxy_get(), Any, List recent executions, annotated with live subprocess status.      When an ex (+7 more)

### Community 27 - "run_automation_endpoint"
Cohesion: 0.25
Nodes (9): BaseModel, LoginPayload, Result of a successfully dispatched automation run., Trigger browser playback of a database-backed automation.      Replaces the in, Credentials forwarded to the API server's /auth/login endpoint., Payload for triggering an automation run from the dashboard., run_automation_endpoint(), RunRequest (+1 more)

### Community 28 - "dashboard_server.py"
Cohesion: 0.16
Nodes (13): dashboard_health(), list_runs(), list_skills(), _probe_http(), _probe_tcp(), _probe_ws(), WebAI Dashboard Server — web UI + orchestration API.  This FastAPI server is t, List playback subprocesses spawned by this dashboard (live diagnostics). (+5 more)

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
Nodes (13): ai(), ai_sync(), ClientError, _dispatch_command(), _make_error_message(), Any, Page, High-level AI Integration Module for the Playwright Client.  This module expos (+5 more)

### Community 33 - "Implementation Plan — WebAI Front-End Automation Dashboard"
Cohesion: 0.18
Nodes (10): 1. Objective, 2. Architecture, 3. API Contract (Dashboard Server), 4. CLI Refactoring (Workflow Requirement), 5. Front-End, 6. Environment & Dependencies, 7. QA Plan, 8. Documentation Plan (Doc Agent) (+2 more)

### Community 34 - "benchmark_modal_speed.py"
Cohesion: 0.28
Nodes (8): _api_online(), main(), Any, Benchmark: Modal rendering response time.  Measures the latency of the endpoin, Return the response time in milliseconds for a GET request., Check if the API server is reachable., Run the benchmark and print results., _time_get()

### Community 35 - "_safe_detail"
Cohesion: 0.17
Nodes (12): Response, UploadFile, import_automation(), login(), Extract an error detail payload from an upstream API response.      Args:, Proxy login to the API server and return the user's API key.      The front-en, Proxy user registration to the API server., Registration details forwarded to the API server's /auth/register endpoint. (+4 more)

### Community 36 - "test_dashboard_recording.py"
Cohesion: 0.36
Nodes (7): _dashboard_online(), main(), Test suite for the Dashboard Interactive Recording endpoint.  Tests:   1. POST /, Test 401 when X-API-Key is missing., Test 422 when required fields are missing., test_recording_endpoint_auth(), test_recording_endpoint_validation()

### Community 37 - "test_dashboard_api.py"
Cohesion: 0.14
Nodes (14): TDVC Test Suite for Phase 6: Semantic Intent Router & Agentic Handoff Engine (Ru, test_intent_routing_and_variable_extraction(), test_no_matching_skill_fallback(), IntentRouter, load_local_skills(), Any, Semantic Intent Router & Agentic Handoff Module for WebAI Local AI Server.  Anal, Extracts and binds JSON classification output from Ollama to full skill dict. (+6 more)

### Community 38 - "validate_steps_payload"
Cohesion: 0.20
Nodes (10): TDVC Test Harness for Semantic Verification & Conditional Assertions (Decision 1, test_click_with_fallback_semantic_guard(), test_rich_snapshot_semantic_matching(), test_semantic_mismatch_raises_error(), test_skill_executor_assert_handler(), test_skill_executor_template_resolution(), test_skill_synthesizer_expected_context(), test_step_schema_extension() (+2 more)

### Community 39 - "Decision Log — WebAI Platform"
Cohesion: 0.20
Nodes (9): Context, Decision, Decision 20: Jira Integration Approach (Pending), Decision 21: Variable Persistence Model (Pending), Decision Log — WebAI Platform, Decision: Refactoring `recorder.py` to Event Bus & Plugin Isolation, Future Decisions Pending, Impact (+1 more)

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
Cohesion: 0.20
Nodes (9): TDVC Test Suite: Verifying Structural CSS Demotion (:nth-child / :nth-of-type) i, DOM Scenario:     - Container with 3 children:       1. Header       2. <div cla, test_structural_css_demoted_behind_semantic_text(), Verify click_with_fallback works with all 13 locator types including alt, aria-l, test_click_with_fallback_all_13_types(), click_with_fallback(), Try multiple locators in priority order until one successfully clicks.     Fort, extract_rich_snapshot() (+1 more)

### Community 65 - "HITLPlugin"
Cohesion: 0.06
Nodes (36): Any, Page, Step, action_listener_loop(), load_local_skills(), main(), End-to-End Hybrid Test Orchestrator for WebAI Platform.  1. Accepts hardcoded pr, Discovers and loads synthesized skills from JSON files in the workspace. (+28 more)

### Community 66 - "Step"
Cohesion: 0.18
Nodes (10): Any, Converts Step dataclasses or dicts into uniform dictionaries., Queries local Ollama hermes3 model for skill synthesis and auto-parameterization, Extracts JSON payload from LLM response content and preserves locators on matchi, Synthesizes recorded browser steps and voice context into reusable AI Skill reci, Extracts core semantic keyword from voice context or step name for pre-click ver, Rule-based fallback synthesizer when Ollama is offline.         Detects typed te, Converts text into a clean snake_case variable name. (+2 more)

### Community 67 - "handle_client"
Cohesion: 0.10
Nodes (25): run_e2e_test(), build_subgoal_prompt(), extract_primary_open_url(), extract_success_expectations(), _fmt_target(), _format_last_errors(), get_query_param(), get_request_path() (+17 more)

### Community 68 - "ai.py"
Cohesion: 0.17
Nodes (32): CDPSession, RuntimeError, clear_element(), click_element(), detach(), execute_script(), find_elements(), focus_element() (+24 more)

### Community 69 - "HITLPlugin"
Cohesion: 0.16
Nodes (10): HITLPlugin, Any, Page, Transcribe PCM WAV audio using faster-whisper., Main entrypoint called when human intervention is required.         1. Speaks TT, Plugin that manages Human-in-the-Loop (HITL) fallback interventions., Attach to WebRecorder event bus and subscribe to intervention requests., Event bus handler when human intervention is triggered. (+2 more)

### Community 70 - "Any"
Cohesion: 0.13
Nodes (19): cache_get_plan(), _cache_key(), cache_put_plan(), _load_cache(), _normalize_history_step(), Any, Normalizes an action dictionary executed during an autonomous session     into, Save the extracted data to a Microsoft Word document using python-docx. (+11 more)

### Community 71 - "_compact_context"
Cohesion: 0.25
Nodes (7): LogRecord, _EmptyProbeNoiseFilter, _http_health_response(), main(), Downgrade 'opening handshake failed' tracebacks caused by bare TCP probes., Answer plain HTTP requests cleanly instead of failing the WS handshake.      R, Entrypoint for the Local WebAI Server.          Starts a WebSocket server that

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
Cohesion: 0.33
Nodes (6): _flush_orchestration_logs(), Payload for starting a new interactive recording session from the dashboard., Best-effort batch upload of dashboard orchestration logs to the API server., Launch an interactive browser session to record a new automation.      Spawns, record_automation_endpoint(), RecordRequest

### Community 78 - "test_circuit_breaker_anti_loop.py"
Cohesion: 0.12
Nodes (23): Any, Verify circuit breaker resets repeat_action_count when URL changes., Verify circuit breaker resets repeat_action_count when action signature changes., Verify that an early done action with summary is accepted for informational quer, Simulates the circuit breaker logic implemented in handle_client loop.     Retur, Verify BASE_PROMPT includes read-first, dropdown toggle, and anti-loop directive, Verify informational queries ('check', 'find out', 'what is') are inferred corre, Verify build_system_prompt injects informational template when task_type is info (+15 more)

### Community 83 - "MockPage"
Cohesion: 0.24
Nodes (4): MockKeyboard, MockPage, TDVC Test Suite for Phase 7: The Browser Handoff Engine (Rule 7) Verifies: 1. Br, test_browser_handoff_lifecycle()

### Community 84 - "dashboard_health"
Cohesion: 0.25
Nodes (7): TDVC Test Harness for New Tab Context Switching in SkillExecutor. Tests: 1. Sing, test_new_tab_context_switch(), test_single_tab_invariant(), TDVC Test Harness for SkillExecutor Parameter Injection & Schema Resolution. Ver, test_skill_executor_resolution(), Executes synthesized AI skill recipes with dynamic runtime parameter injection., SkillExecutor

### Community 85 - "save_synthesized_skill"
Cohesion: 0.11
Nodes (21): Path, Verify save_synthesized_skill creates slug directory, recorded_steps.json, skill, Verify action normalization extracts clean, replay-compatible step structures., Verify that saving an updated skill with the same name updates the existing regi, test_normalize_history_step(), test_save_synthesized_skill_creates_expected_artifacts(), test_save_synthesized_skill_updates_existing_entry(), main() (+13 more)

### Community 86 - "TaskDone"
Cohesion: 0.67
Nodes (3): Exception, Exception raised internally when the LLM outputs `action=done`.          This, TaskDone

### Community 88 - "_prune_dom_snapshot"
Cohesion: 0.17
Nodes (11): TDVC Test Suite for Multi-Skill Library Architecture with Mandatory Safeguards:, Validates run_skill path resolution supports explicit sys.argv[1] or default fal, Validates that save_skill creates skills/ directory, saves skills/{slug}.json, a, Validates that sanitize_skill_filename strips directory traversal characters., Validates that skills/*.json takes precedence and mirror synthesized_skill.json, Validates that SkillExecutePayload accepts and validates a filename string., test_run_skill_cli_resolution(), test_safeguard_deduplication_in_scanner() (+3 more)

### Community 89 - ".json"
Cohesion: 0.23
Nodes (5): FakeResponse, Any, End-to-end proxy chain against a real API server (no browser launched)., Minimal stand-in for `requests.Response` used by monkeypatched stubs., TestLiveApiServer

### Community 90 - "test_skill_mapping.py"
Cohesion: 0.18
Nodes (10): Exception, TDVC Test Suite for Automation-to-Skill Mapping: 1. SkillSynthesizer.synthesize(, Validates POST /api/automations/{automation_id}/synthesize endpoint workflow., Validates that synthesize() adds source_automation_id at root level of skill dic, Validates that save_skill writes source_automation_id to disk in both slug and m, Validates that list_skills includes source_automation_id in the response payload, test_list_skills_extracts_source_automation_id(), test_save_skill_persists_source_automation_id() (+2 more)

### Community 91 - "test_run_hybrid.py"
Cohesion: 0.20
Nodes (3): MockKeyboard, MockPage, TDVC Test Suite for run_hybrid.py & TaskId Handoff Fix (Rule 7) Verifies: 1. tas

### Community 92 - "test_unified_13_locators.py"
Cohesion: 0.15
Nodes (13): Test suite for verifying all 13 locator strategies in fallback_helpers.py.  This, Verify _create_locator_obj constructs valid locators for all 13 types., Verify type_with_fallback works with input locators including aria-label, title,, Verify extract_with_fallback extracts text/attribute for aria-label, alt, title,, Verify LOCATOR_PRIORITY is exact 13-key 0-indexed dict matching server., test_create_locator_obj_all_13_types(), test_extract_with_fallback_all_types(), test_locator_priority_structure() (+5 more)

### Community 93 - "skill_executor.py"
Cohesion: 0.20
Nodes (7): Headless E2E Test for SkillExecutor Playwright Execution. Verifies loading synth, test_e2e_skill_playback(), TDVC Test Harness for SemanticVerificationError HITL Interception in SkillExecut, test_semantic_verification_triggers_hitl_and_resumes(), Skill Executor Utility for WebAI Playwright Recorder.  Parses synthesized skills, Raised when pre-click Rich Element Snapshot fails semantic verification against, SemanticVerificationError

### Community 94 - "Any"
Cohesion: 0.28
Nodes (6): Any, Path, Injects runtime parameters (or schema defaults) into step template placeholders, Replays resolved skill steps sequentially in Playwright with multi-locator fallb, Safely print to stdout, catching any encoding or I/O exceptions.     Prevents cr, safe_print()

### Community 95 - "skill_synthesizer.py"
Cohesion: 0.29
Nodes (5): TDVC Test Harness for SkillSynthesizer. Verifies Ollama synthesis, JSON parsing,, test_skill_synthesis(), fetch_steps_from_api(), main(), Skill Synthesizer Utility for WebAI Playwright Recorder.  Processes time-aligned

### Community 96 - "synthesize_automation_skill"
Cohesion: 0.32
Nodes (7): Tests for decoupled skill synthesis execution.  Validates that: 1. dash_synthesi, Verify that synthesize_automation_skill spawns dash_synthesize.py with the corre, Verify that CalledProcessError from subprocess.run is mapped to HTTPException(50, test_synthesize_endpoint_handles_called_process_error(), test_synthesize_endpoint_spawns_subprocess(), Synthesize an AI Skill recipe from database automation steps.      Spawns `das, synthesize_automation_skill()

### Community 97 - "execute_skill_endpoint"
Cohesion: 0.22
Nodes (9): execute_skill_endpoint(), Path, Sanitize a skill filename using os.path.basename to guard against directory trav, Payload for triggering dynamic execution of a synthesized AI skill., Choose the Python interpreter for the playback subprocess.      Prefers the Pl, Execute a synthesized AI Skill asynchronously via SkillExecutor in Playwright ve, sanitize_skill_filename(), _select_playback_python() (+1 more)

### Community 98 - "test_dashboard_skill_delete.py"
Cohesion: 0.20
Nodes (9): mock_skill_environment(), Unit and integration tests for DELETE /api/skills/{slug} endpoint in dashboard_s, Verify deleting a non-existent skill returns 404., Verify invalid slugs with illegal characters are rejected with 400., Sets up a temporary skills directory and points CLIENT_DIR to tmp_path., Verify DELETE /api/skills/{slug} removes files, directory, and registry entry., test_delete_skill_invalid_slug(), test_delete_skill_not_found() (+1 more)

### Community 99 - "activeContext.md"
Cohesion: 0.22
Nodes (8): Active Context  WebAI Platform, Active Context  WebAI Platform, Current Session (2026-07-29), Current Session (2026-07-29), Dashboard Enhancements & Performance Optimization, Dashboard Enhancements & Performance Optimization, Previous Session (2026-07-18), Previous Session (2026-07-18)

### Community 100 - "run_skill.py"
Cohesion: 0.50
Nodes (4): main(), CLI Runner for Executing Synthesized AI Skills.  Loads synthesized_skill.json, p, Resolves skill file path supporting direct path, skills/ filename, or default fa, resolve_skill_path()

### Community 103 - "Previous Session (2026-08-29)"
Cohesion: 0.25
Nodes (8): Hybrid E2E Test Orchestrator (`run_hybrid.py`) & Handoff Fix ✅, Phase 10: Human-in-the-Loop (HITL) Interactive Learning & Execution Fixes ✅, Phase 11: Continuous Observer Mode & Advanced HITL Control ✅, Phase 6: Semantic Intent Router & Agentic Handoff Engine ✅, Phase 7: The Browser Handoff Engine (The Bridge) ✅, Phase 8: Autonomous Continuation & Spatial Graph Routing ✅, Previous Session (2026-08-29), System Architecture & Workflow Documentation Generated ✅

### Community 105 - "tests/test_dashboard_api.py"
Cohesion: 0.25
Nodes (5): _api_server_online(), QA suite for the WebAI Dashboard Server (webai_dashboard).  Covers two layers:, Health endpoint always reports dashboard status plus dependency probes., Return True when a real API server answers on WEBAI_API_URL., TestHealthEndpoint

### Community 106 - "validate_steps_payload"
Cohesion: 0.36
Nodes (4): Step-payload validation for the import endpoint., TestValidateStepsPayload, Validate an uploaded recording payload.      Args:         steps: Parsed JSON, validate_steps_payload()

### Community 107 - "Previous Session (2026-08-27)"
Cohesion: 0.29
Nodes (7): Documentation Update: Virtual Environment Activation in `how_to_run.md` ✅, Phase 1: Audio Capture & Event Synchronization ✅, Phase 2: Local Transcription & Alignment ✅, Phase 3: AI Skill Synthesis & Auto-Parameterization ✅, Phase 4: Skill Execution Engine & Dynamic Replay ✅, Phase 5: Dashboard UI Integration & Skill Management ✅, Previous Session (2026-08-27)

### Community 108 - "_execute_command"
Cohesion: 0.38
Nodes (6): test_action_listener_loop_mock(), test_execute_command_fallback_single_page(), test_execute_command_uses_active_page_from_context(), _execute_command(), Execute a single AI command against the active Playwright page with timeout safe, _send_command_response()

### Community 109 - "dash_synthesize.py"
Cohesion: 0.33
Nodes (6): fetch_automation(), main(), Any, CLI script to synthesize an AI Skill recipe from database automation steps.  Thi, Fetch an automation record and its recorded steps from the API server.      Args, Parse arguments, retrieve automation steps, synthesize the skill, and save it.

### Community 110 - ".save_skill"
Cohesion: 0.33
Nodes (4): Validates dependency-free slugification of human-readable skill names into safe, test_slugify_filename(), Converts a human-readable skill name into a safe, alphanumeric filename slug., Saves the synthesized skill recipe to skills/{slug}.json and mirrors to synthesi

### Community 111 - "normalize_task"
Cohesion: 0.33
Nodes (6): Verify normalize_task injects read-first, anti-loop, and dropdown requirements., test_normalize_task_read_first_guidance(), _extract_urls(), _is_already_structured(), normalize_task(), Convert a short task into Goal/Requirements/Success Criteria form.

### Community 112 - "build_task_text"
Cohesion: 0.40
Nodes (4): generated_task.txt content generation for guided playback., TestBuildTaskText, build_task_text(), Build the `generated_task.txt` content consumed by the guided playback client.

### Community 114 - "_env"
Cohesion: 0.40
Nodes (6): _env(), jdump(), llm_plan_chat(), ollama_chat(), Calls local Ollama chat API.     Default endpoint: http://localhost:11434/api/c, Route planning chat requests to the configured LLM provider.      Defaults to

### Community 115 - "recorder.py"
Cohesion: 0.33
Nodes (3): main(), Human-in-the-Loop (HITL) Interactive Learning Plugin for WebAI Playwright Record, Browser Interaction Recorder utilizing Chrome DevTools Protocol (CDP).  This mod

### Community 116 - "Active Context  WebAI Platform"
Cohesion: 0.40
Nodes (5): Active Context  WebAI Platform, Phase 15: Kimi K3 Provider Integration & Multimodal Visual-DOM Planning (Rule 7 TDVC) ✅, Phase 16: Multi-Skill Library Integration & Catalog Scanner (Rule 7 TDVC) ✅, Previous Session (2026-07-18), Previous Session (2026-09-18)

### Community 117 - "Previous Session (2026-09-09)"
Cohesion: 0.40
Nodes (5): Client & Server Multi-Locator Priority Unification (13 Strategies) ✅, Phase 12: JS Telemetry Injector (Shield 1: Smart Filtering & Shield 2: Mutation Verification) ✅, Phase 13: Dynamic Popup & Delayed DOM Re-hydration (Rule 7 TDVC) ✅, Phase 14: Audio Transcription VAD & Anti-Hallucination Upgrade (Rule 7 TDVC) ✅, Previous Session (2026-09-09)

### Community 118 - "test_dynamic_popup_handling.py"
Cohesion: 0.40
Nodes (4): TDVC Assertion:     Assert that when Playwright throws a TimeoutError during com, Mock an AI server loop where an injected Playwright TimeoutError is simulated, test_client_handles_playwright_timeout(), test_server_dynamic_popup_retry_on_timeout()

### Community 120 - "Previous Session (2026-08-03)"
Cohesion: 0.50
Nodes (4): Dashboard Enhancements & Performance Optimization, Plugin Architecture Refactoring: `recorder.py` & `DataExtractionPlugin` ✅, Previous Session (2026-08-03), WebSocket Handshake Error Fix (AI Server :8765) ✅

### Community 121 - "Decision 14: Semantic Verification & Conditional Assertions"
Cohesion: 0.50
Nodes (4): Context, Decision 14: Semantic Verification & Conditional Assertions, Decision, Impact

### Community 122 - "Decision 16: Read-First System Prompting & Anti-Loop Directives"
Cohesion: 0.50
Nodes (4): Context, Decision 16: Read-First System Prompting & Anti-Loop Directives, Decision, Impact

### Community 123 - "Decision 17: Action Deduplication Circuit Breaker & Proactive HITL Escalation"
Cohesion: 0.50
Nodes (4): Context, Decision 17: Action Deduplication Circuit Breaker & Proactive HITL Escalation, Decision, Impact

### Community 124 - "Decision 18: Skill Synthesis (Auto-Saving Successful Agentic Workflows)"
Cohesion: 0.50
Nodes (4): Context, Decision 18: Skill Synthesis (Auto-Saving Successful Agentic Workflows), Decision, Impact

### Community 125 - "Decision 19: Dashboard Skill Management (Delete Functionality)"
Cohesion: 0.50
Nodes (4): Context, Decision 19: Dashboard Skill Management (Delete Functionality), Decision, Impact

### Community 126 - "_buffer_log"
Cohesion: 0.50
Nodes (4): _buffer_log(), delete_automation(), Append one orchestration log entry to the buffer (source='api')., Delete an automation and its dependent records via the API server.      Proxie

## Knowledge Gaps
- **280 isolated node(s):** `Phase 27: Dashboard Skill Management (Delete Functionality) (Decision 19, Rule 7 TDVC) ✅`, `Phase 26: Skill Synthesis (Auto-Saving Successful Agentic Workflows) (Decision 18, Rule 7 TDVC) ✅`, `Phase 25: Autonomous Navigation Engine Hardening (Decision 16, Decision 17, Rule 7 TDVC) ✅`, `Phase 24: Pure Autonomous AI Navigation Entry Point (`run_autonomous.py`) (Rule 3) ✅`, `Phase 23: Windows Console UTF-8 & Global `safe_print` Wrapper (`skill_executor.py`, `dashboard_server.py`) (Rule 3) ✅` (+275 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Step` connect `Open Questions / Decisions Pending` to `HITLPlugin`, `validate_steps_payload`, `AudioCapturePlugin`, `recorder.py`, `Page`, `Page`, `skill_synthesizer.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `SkillSynthesizer` connect `Step` to `validate_steps_payload`, `dash_synthesize.py`, `.save_skill`, `recorder.py`, `Page`, `_prune_dom_snapshot`, `test_skill_mapping.py`, `skill_synthesizer.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `SkillExecutor` connect `dashboard_health` to `run_skill.py`, `validate_steps_payload`, `MockLocator`, `MockPage`, `test_run_hybrid.py`, `skill_executor.py`, `Any`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **What connects `Phase 27: Dashboard Skill Management (Delete Functionality) (Decision 19, Rule 7 TDVC) ✅`, `Phase 26: Skill Synthesis (Auto-Saving Successful Agentic Workflows) (Decision 18, Rule 7 TDVC) ✅`, `Phase 25: Autonomous Navigation Engine Hardening (Decision 16, Decision 17, Rule 7 TDVC) ✅` to the rest of the system?**
  _280 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Recent Work Completed` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Open Questions / Decisions Pending` be split into smaller, more focused modules?**
  _Cohesion score 0.12433862433862433 - nodes in this community are weakly interconnected._
- **Should `Project Milestones` be split into smaller, more focused modules?**
  _Cohesion score 0.05555555555555555 - nodes in this community are weakly interconnected._