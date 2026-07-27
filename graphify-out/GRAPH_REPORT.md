# Graph Report - AILearn  (2026-07-27)

## Corpus Check
- 216 files · ~218,184 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 312 nodes · 396 edges · 22 communities (16 shown, 6 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 5 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `bc775fb6`
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

## God Nodes (most connected - your core abstractions)
1. `handle_client()` - 22 edges
2. `Recent Work Completed` - 18 edges
3. `WebRecorder` - 13 edges
4. `Active Context — WebAI Platform` - 10 edges
5. `Project Milestones` - 10 edges
6. `Design Patterns` - 10 edges
7. `Progress — WebAI Platform` - 9 edges
8. `System Patterns — WebAI Platform` - 9 edges
9. `Known Issues` - 8 edges
10. `ai()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `WebRecorder`  [EXTRACTED]
  WEBAI_AUTOMATION/webai_playwright_python/record_then_run.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/recorder.py
- `_execute_command()` --calls--> `extract_with_fallback()`  [EXTRACTED]
  WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/ai.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/fallback_helpers.py
- `_execute_command()` --calls--> `extract_table_data()`  [EXTRACTED]
  WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/ai.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/fallback_helpers.py

## Import Cycles
- None detected.

## Communities (22 total, 6 thin omitted)

### Community 0 - "Recent Work Completed"
Cohesion: 0.11
Nodes (18): 7 Web Failure Scenario Fortification & Test Suite Verification ✅, API Server Startup Bug Fixes ✅, Auto SQL Upload in `record_then_run.py` ✅, Crawl4AI Integration & Semantic DOM Fingerprinting ✅, Database Migrations ✅, Graphify Knowledge Graph Integration ✅, Hermes 3 Model Integration ✅, `<label>` Button Click Locator Fix & Hermes 3 Self-Healing ✅ (+10 more)

### Community 1 - "Active Context — WebAI Platform"
Cohesion: 0.10
Nodes (19): 1. Conditional Branching (Future Enhancement), 2. Variable Storage for Conditions, 3. Explicit Page Validation, 4. LOCATOR_PRIORITY Inconsistency, 5. Shim Module Bug, Active Context — WebAI Platform, Active Files (Most Recently Modified), Current Session (2026-07-18) (+11 more)

### Community 2 - "Open Questions / Decisions Pending"
Cohesion: 0.13
Nodes (12): Page, ask_yes_no(), main(), Any, Browser Interaction Recorder utilizing Chrome DevTools Protocol (CDP).  This m, Attaches the recorder to the BrowserContext and all current / newly opened tabs, Save single extraction to files immediately, Save extraction to Excel file (+4 more)

### Community 3 - "Immediate Next Steps (If User Requests)"
Cohesion: 0.09
Nodes (34): Exception, RuntimeError, Exception raised internally when the LLM outputs `action=done`.          This si, TaskDone, ai(), ai_sync(), ClientError, _execute_command() (+26 more)

### Community 4 - "Current Session (2026-07-18)"
Cohesion: 0.22
Nodes (16): buffer_log(), create_execution_record(), fetch_automation_steps(), flush_logs(), log(), main(), Run automation from API database - Simple file-based approach.  This script de, Save steps to JSON file (+8 more)

### Community 8 - "test_cdp_fixes.py"
Cohesion: 0.17
Nodes (11): Test suite for verifying CDP and Playwright Actions fixes, Test that cdp.get_dom_snapshot works correctly, Test that playwright_actions.get_snapshot works correctly, Test that cdp.get_interactive_elements works correctly, Test that playwright_actions.get_dom_snapshot works correctly, Test that playwright_actions.get_interactive_elements works correctly, test_cdp_get_dom_snapshot(), test_cdp_get_interactive_elements() (+3 more)

### Community 9 - "fallback_helpers.py"
Cohesion: 0.06
Nodes (56): build_subgoal_prompt(), build_system_prompt(), cache_get_plan(), _cache_key(), cache_put_plan(), _compact_context(), _env(), _extract_json_array() (+48 more)

### Community 10 - "How to Run the WebAI Automation Project"
Cohesion: 0.29
Nodes (6): 1. Start the API Server (Terminal 1), 2. Start the AI Server (Terminal 2), 3. Start the Ollama Server (Terminal 3), 4. Run the Client Script (Terminal 4), Available Client Scripts:, How to Run the WebAI Automation Project

### Community 11 - "test_quick.py"
Cohesion: 0.33
Nodes (5): Quick Test: Verify Playback Works, Test that generated_task.txt matches recorded steps, Test that recorded_steps.json has correct structure, test_recorded_steps_structure(), test_task_text_generation()

### Community 12 - "test_error_logging.py"
Cohesion: 0.50
Nodes (3): Test error logging with stacktrace capture Forces an error scenario to verify s, Test that errors are logged with full stacktraces, test_error_logging()

### Community 16 - "Project Milestones"
Cohesion: 0.06
Nodes (34): 1. Plan Caching Disabled, 2. No Explicit Navigation Validation, 3. Variable Persistence Limited, 4. LLM Sometimes Returns Invalid Actions, 5. Hardcoded API Key in Scripts, 6. Database Echo Enabled, 7. CORS Wide Open, API Server Tests ✅ (+26 more)

### Community 17 - "Design Patterns"
Cohesion: 0.07
Nodes (26): 1. Browser Robot ↔ AI Brain (WebSocket), 2. Browser Robot ↔ API Server (HTTP REST), 3. AI Brain ↔ API Server (HTTP REST), 4. AI Brain ↔ Ollama (HTTP), Component Relationships, Critical Implementation Paths, Database Schema, Design Patterns (+18 more)

### Community 18 - "graphify_to_mermaid.py"
Cohesion: 0.27
Nodes (11): generate_community_mermaid(), generate_god_nodes_mermaid(), main(), Any, Graphify to Mermaid Exporter  Reads graphify-out/graph.json and generates clean,, Sanitize node IDs for Mermaid compatibility., Sanitize labels for Mermaid node boxes., Generate Mermaid flowchart grouped by communities (filtering to code nodes only) (+3 more)

### Community 19 - "crawl_helper.py"
Cohesion: 0.22
Nodes (8): build_element_fingerprint(), generate_page_summary(), html_to_llm_markdown(), Any, Crawl4AI Helper Module for LLM Markdown Page Understanding & Semantic Fingerprin, Convert raw HTML DOM into clean, noise-free LLM Markdown.     Strips scripts, st, Extract a concise 1-2 sentence page summary from LLM Markdown content., Build a rich semantic fingerprint for recorded elements.     Includes tag, role,

### Community 20 - "AI Assistant Core Rules"
Cohesion: 0.25
Nodes (7): 1. Documentation & Code Synchronization, 2. Memory Bank Maintenance, 3. Code Quality & Style, 4. Testing & Verification, 5. Dependency Management, 6. Safety & Permissions, AI Assistant Core Rules

## Knowledge Gaps
- **95 isolated node(s):** `graphify`, `1. Documentation & Code Synchronization`, `2. Memory Bank Maintenance`, `3. Code Quality & Style`, `4. Testing & Verification` (+90 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TaskDone` connect `Immediate Next Steps (If User Requests)` to `fallback_helpers.py`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **What connects `graphify`, `1. Documentation & Code Synchronization`, `2. Memory Bank Maintenance` to the rest of the system?**
  _95 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Recent Work Completed` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._
- **Should `Active Context — WebAI Platform` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `Open Questions / Decisions Pending` be split into smaller, more focused modules?**
  _Cohesion score 0.12681159420289856 - nodes in this community are weakly interconnected._
- **Should `Immediate Next Steps (If User Requests)` be split into smaller, more focused modules?**
  _Cohesion score 0.08677098150782361 - nodes in this community are weakly interconnected._
- **Should `fallback_helpers.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05792349726775956 - nodes in this community are weakly interconnected._