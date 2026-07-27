# Graph Report - AILearn  (2026-07-26)

## Corpus Check
- 214 files · ~215,528 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 142 nodes · 172 edges · 16 communities (11 shown, 5 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0f24dba2`
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

## God Nodes (most connected - your core abstractions)
1. `WebRecorder` - 12 edges
2. `Active Context — WebAI Platform` - 10 edges
3. `Recent Work Completed` - 10 edges
4. `ai()` - 9 edges
5. `log()` - 7 edges
6. `Open Questions / Decisions Pending` - 6 edges
7. `buffer_log()` - 6 edges
8. `main()` - 6 edges
9. `_execute_command()` - 6 edges
10. `How to Run the WebAI Automation Project` - 5 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `ai()`  [EXTRACTED]
  WEBAI_AUTOMATION/webai_playwright_python/record_then_run.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/ai.py
- `main()` --calls--> `WebRecorder`  [EXTRACTED]
  WEBAI_AUTOMATION/webai_playwright_python/record_then_run.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/recorder.py
- `_execute_command()` --calls--> `extract_table_data()`  [EXTRACTED]
  WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/ai.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/fallback_helpers.py
- `_execute_command()` --calls--> `extract_with_fallback()`  [EXTRACTED]
  WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/ai.py → WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/fallback_helpers.py

## Import Cycles
- None detected.

## Communities (16 total, 5 thin omitted)

### Community 0 - "Recent Work Completed"
Cohesion: 0.20
Nodes (10): API Server Startup Bug Fixes ✅, Auto SQL Upload in `record_then_run.py` ✅, Database Migrations ✅, Graphify Knowledge Graph Integration ✅, Hermes 3 Model Integration ✅, Phase 8.2: Save Extracted Data ✅, Phase 8.3: Table Extraction ✅, Phase 9.1: Add Delay ✅ (+2 more)

### Community 1 - "Active Context — WebAI Platform"
Cohesion: 0.10
Nodes (19): 1. Conditional Branching (Future Enhancement), 2. Variable Storage for Conditions, 3. Explicit Page Validation, 4. LOCATOR_PRIORITY Inconsistency, 5. Shim Module Bug, Active Context — WebAI Platform, Active Files (Most Recently Modified), Current Session (2026-07-18) (+11 more)

### Community 2 - "Open Questions / Decisions Pending"
Cohesion: 0.14
Nodes (11): ask_yes_no(), main(), Any, Page, Browser Interaction Recorder utilizing Chrome DevTools Protocol (CDP).  This m, Save single extraction to files immediately, Save extraction to Excel file, Save extraction to Word file (+3 more)

### Community 3 - "Immediate Next Steps (If User Requests)"
Cohesion: 0.17
Nodes (18): RuntimeError, ai(), ai_sync(), ClientError, _execute_command(), _make_error_message(), Any, Page (+10 more)

### Community 4 - "Current Session (2026-07-18)"
Cohesion: 0.22
Nodes (16): buffer_log(), create_execution_record(), fetch_automation_steps(), flush_logs(), log(), main(), Run automation from API database - Simple file-based approach.  This script de, Save steps to JSON file (+8 more)

### Community 8 - "test_cdp_fixes.py"
Cohesion: 0.17
Nodes (11): Test suite for verifying CDP and Playwright Actions fixes, Test that cdp.get_dom_snapshot works correctly, Test that playwright_actions.get_snapshot works correctly, Test that cdp.get_interactive_elements works correctly, Test that playwright_actions.get_dom_snapshot works correctly, Test that playwright_actions.get_interactive_elements works correctly, test_cdp_get_dom_snapshot(), test_cdp_get_interactive_elements() (+3 more)

### Community 9 - "fallback_helpers.py"
Cohesion: 0.20
Nodes (9): click_with_fallback(), Helper functions for fallback extraction strategies.  This module provides heu, Try multiple locators in priority order to type text.          Args:, Try multiple locators in priority order to select a dropdown value.          A, Try multiple locators in priority order until one successfully clicks., Validate that the page URL contains the expected URL substring.          Args:, select_with_fallback(), type_with_fallback() (+1 more)

### Community 10 - "How to Run the WebAI Automation Project"
Cohesion: 0.29
Nodes (6): 1. Start the API Server (Terminal 1), 2. Start the AI Server (Terminal 2), 3. Start the Ollama Server (Terminal 3), 4. Run the Client Script (Terminal 4), Available Client Scripts:, How to Run the WebAI Automation Project

### Community 11 - "test_quick.py"
Cohesion: 0.33
Nodes (5): Quick Test: Verify Playback Works, Test that generated_task.txt matches recorded steps, Test that recorded_steps.json has correct structure, test_recorded_steps_structure(), test_task_text_generation()

### Community 12 - "test_error_logging.py"
Cohesion: 0.50
Nodes (3): Test error logging with stacktrace capture Forces an error scenario to verify s, Test that errors are logged with full stacktraces, test_error_logging()

## Knowledge Gaps
- **31 isolated node(s):** `What Was Done Today`, `Current State of the Codebase`, `Running Services Status`, `Auto SQL Upload in `record_then_run.py` ✅`, `Playwright Strict Mode Resilience & E2E Verification ✅` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Active Context — WebAI Platform` connect `Active Context — WebAI Platform` to `Recent Work Completed`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `extract_with_fallback()` connect `Immediate Next Steps (If User Requests)` to `fallback_helpers.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **What connects `What Was Done Today`, `Current State of the Codebase`, `Running Services Status` to the rest of the system?**
  _31 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Active Context — WebAI Platform` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `Open Questions / Decisions Pending` be split into smaller, more focused modules?**
  _Cohesion score 0.13852813852813853 - nodes in this community are weakly interconnected._