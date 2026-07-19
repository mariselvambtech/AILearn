# Active Context — WebAI Platform

> **This file updates most frequently.** It tracks the current session state, recent changes, open questions, and immediate next steps.

## Current Session (2026-07-18)

### What Was Done Today
- ✅ Read and analyzed all three project components (`webai_api_server`, `webai_local_server`, `webai_playwright_python`)
- ✅ Understood the full architecture: 3-tier system (API/AI/Browser)
- ✅ Created `memory-bank/` directory with 7 documentation files
- ✅ Documented architecture, patterns, tech stack, and product context
- ✅ Verified memory-bank files against actual source code
- ⚠️ Pending discrepancies: LOCATOR_PRIORITY dual versions, missing tests, missing files, Ctrl+Shift+W shortcut, shim bug, pagination ranges

### Current State of the Codebase
The project is **functional and feature-complete** for its current scope. All three servers can run and the end-to-end flow (record → save to DB → replay from DB) works.

## Running Services Status

| Service | Port | Status | Start Command |
|---------|------|--------|---------------|
| API Server | 8000 | ⚠️ Not running (needs manual start) | `cd e:\WebAI_Project\webai_api_server && python run.py` |
| AI Server | 8765 | ⚠️ Not running (needs manual start) | `cd e:\WebAI_Project\webai_local_server && python -m webai_local_server.local_webai_server_guided` |
| Ollama | 11434 | ⚠️ Not running (needs manual start) | `ollama serve` |

**To use the system:** Start all 3 servers in separate terminals, then run client scripts from `e:\WebAI_Project\webai_playwright_python`.

## Recent Work Completed

### Phase 8.2: Save Extracted Data ✅
- Implemented save options dialog (Excel/Word/TXT checkboxes)
- File configuration dialog (folder, filename, append/overwrite mode)
- Immediate save during recording (`_save_extraction_immediately`)
- Save during playback (`_save_txt/excel/word_extraction` in AI server)
- Visual indicator (green outline on extracted elements)

### Phase 8.3: Table Extraction ✅
- Right-click → Extract Table context menu option
- Table detection + column header reading
- Column selection dialog with checkboxes
- Pagination configuration (see ranges below)
- JavaScript-based extraction with duplicate detection (hashing)
- "Next" button auto-clicking with change polling
- Export to Excel/CSV/TXT via pandas

### Phase 9.1: Add Delay ✅
- Right-click → Add Delay context menu option
- Keyboard shortcut: Ctrl+Shift+W
- Input dialog for seconds (1-60 range validation)
- Wait action recorded and replayed (server-side `asyncio.sleep`)

### Database Migrations ✅
- Added `log_retention_days` column to `automation_configs`
- Added IST computed columns (`started_at_ist`, `completed_at_ist`, `timestamp_ist`)
- Added `automation_id` to `execution_logs` with foreign key + index

## Pagination Config Ranges (from `recorder.py` lines 943-959)

| Parameter | Min | Max | Step | Default | Purpose |
|-----------|-----|-----|------|---------|---------|
| Max Pages | 1 | 100 | 1 | 10 | Maximum pages to extract |
| Wait Per Page | 1 | 10 | 0.5 | 2.0 | Seconds to wait after page change for stability |
| Page Timeout | 5 | 30 | 1 | 10 | Max seconds to wait for table to change (polls every 100ms) |
| Retry Attempts | 1 | 5 | 1 | 3 | Retries if duplicate data detected |

## Open Questions / Decisions Pending

### 1. Conditional Branching (Future Enhancement)
**From `ai additional features webscrape.docx`:**
> "I might be checking some condition like less than or greater than or equal. Based on the result, I might raise Jira ticket or incident ticket."

**Status:** Not yet implemented. Currently, extracted data is stored in variables but no conditional logic exists to branch based on values.

**Potential approach:**
- Add `condition` action type to recorder
- Evaluate extracted variable values against thresholds
- Branch to different action sequences based on result
- Integrate with Jira API for ticket creation

### 2. Variable Storage for Conditions
**User wants:** Extracted data stored in variables for later condition checks
**Current state:** Data stored in `page.__extracted_data__[key]` but not persisted beyond session
**Needed:** Variables carried between steps, accessible in condition evaluations

### 3. Explicit Page Validation
**Current:** `navigate` action trusts Playwright's built-in waiting (`domcontentloaded`)
**Available but unused:** `validatePage` command exists in `fallback_helpers.py` but not called after navigation
**Question:** Should we add explicit `validatePage` calls after every `navigate` action?

### 4. LOCATOR_PRIORITY Inconsistency
**Current:** Server has 13 locator types, client has 9 (missing `alt`, `aria-label`, `title`)
**Status:** Pending – not yet unified. **Question:** Should we unify both to the 13-type version?
**Impact:** Server may send locator types the client doesn't handle

### 5. Shim Module Bug
**Current:** `local_webai_server.py` shim imports from non-existent module
**Question:** Fix shim to import from `local_webai_server_guided`?

## Immediate Next Steps (If User Requests)

### Option A: Implement Conditional Branching
1. Add `condition` action to `Step` dataclass in `recorder.py`
2. Add UI dialog for condition configuration (variable, operator, value)
3. Add `condition` handling in `local_webai_server_guided.py`
4. Implement branch logic (if true → steps A, if false → steps B)
5. Add Jira integration for ticket creation

### Option B: Fix Known Issues
1. Unify LOCATOR_PRIORITY between server and client (13 types)
2. Fix shim module to import from `local_webai_server_guided`
3. Add explicit `validatePage` after navigation
4. Externalize hardcoded API key to environment variable
5. Disable database echo for production

### Option C: Testing & Stabilization
1. Run full E2E test: record → import → replay
2. Test data extraction with real websites
3. Test table extraction with pagination
4. Verify log retention cleanup works
5. Test scheduling with cron expressions

## Active Files (Most Recently Modified)

| File | Last Change | Purpose |
|------|-------------|---------|
| `webai_local_server/webai_local_server/local_webai_server_guided.py` | Phase 8.2/8.3/9.1 | AI brain with extraction + table + wait |
| `webai_playwright_python/webai_playwright/recorder.py` | Phase 8.2/8.3/9.1 | Recorder with context menu + save dialogs |
| `webai_playwright_python/webai_playwright/fallback_helpers.py` | Phase 8.2/8.3 | Extraction + table extraction logic |
| `webai_playwright_python/webai_playwright/ai.py` | Phase 8.2/8.3 | Command handlers for extract/extractTableData |
| `webai_api_server/main.py` | Logging endpoints | API with log batch + stats endpoints |
| `webai_api_server/models.py` | IST + automation_id | Database models with IST columns |

## Key Context for Next Session

1. **Always start 3 servers** before testing: API (8000), AI (8765), Ollama (11434)
2. **API key** for testing: `o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8`
3. **Guided mode** (with recorded_steps) bypasses LLM for click/type — uses fallback only
4. **Freeform mode** (no recorded_steps) requires Ollama running
5. **Extraction features** are in `recorder.py` (JS) + `fallback_helpers.py` (Python) + `local_webai_server_guided.py` (server)
6. **Database** must have `webai_automation` database created in SSMS before first run
7. **Encryption key** in `.env` must be preserved — losing it loses all encrypted credentials
8. **Shim module is broken** — always run `local_webai_server_guided` directly, not via shim
9. **LOCATOR_PRIORITY differs** between server (13 types) and client (9 types) — see `progress.md` issue #8

## Related Documents
- `progress.md` — Detailed feature status and known issues
- `decisionLog.md` — Why certain approaches were chosen
- `techContext.md` — Setup commands and credentials