# Product Context — WebAI Platform

## Why This Project Exists

### The Problem with Traditional Web Automation (UiPath)
Traditional web automation tools like UiPath rely on **single, brittle selectors**. When a website redesigns:
- A button's `id="btn-login"` changes to `id="btn-auth"` → automation **breaks immediately**
- A developer must manually: open Studio → edit selector → re-test → re-deploy
- Cost: ~4 hours of human work per broken automation
- Result: Automations are fragile and require constant maintenance

### The WebAI Solution
WebAI solves this by capturing **10+ locator strategies** per element during recording and using a **fallback system** during playback:
- If `id` fails → try `name` → try `aria-label` → try `placeholder` → try `css` → try `text` → try `xpath`...
- If a website changes one locator, the automation **still works** by falling back to another
- An **AI brain (Llama 3.1)** can also reason about failures and adapt (scroll, retry, choose alternative)

## Problems Solved

### 1. Brittle Selectors → Self-Healing Automation
**Before:** One selector breaks → entire automation fails → human fixes it
**After:** 10+ locators captured → if one breaks, next one works → no human intervention needed

### 2. File-Based Recordings → Database Orchestration
**Before:** `recorded_steps.json` saved locally → hard to share, version, or reuse across machines
**After:** Automations stored in MSSQL → reusable by ID, shareable as templates, schedulable via cron

**Example use case (currency converter):**
1. User records a currency exchange rate converter automation
2. Automation saved to database with name "USD to INR Converter"
3. Weeks later, user runs `run_from_database.py`, enters automation ID
4. System fetches steps from DB, substitutes variables, replays in browser
5. Execution logged with status, timing, and extracted data

### 3. Hardcoded Credentials → Encrypted Secret Management
**Before:** Passwords hardcoded in scripts or plain text files
**After:** Credentials encrypted with Fernet symmetric encryption, stored per-user in database, decrypted only at runtime

### 4. No Audit Trail → Full Execution Logging
**Before:** "Why did my automation fail at 3 AM?" — no way to know
**After:** Every execution creates a record with:
- Start/end time, duration
- Success/failure status + error messages
- Step-by-step logs (INFO/WARN/ERROR/DEBUG)
- Extracted data stored for review
- IST timezone columns for local readability

### 5. Manual Repetition → Scheduling
**Before:** Human must manually trigger automations
**After:** Cron-based scheduling ("run this every day at 9 AM") with automatic execution tracking

## Intended User Experience

### Flow 1: Record → Save → Replay (Primary Use Case)
```
User runs: python record_then_run.py
  → Browser opens (Chromium, non-headless)
  → User navigates to target website
  → User performs actions (clicks, types, navigates)
  → Optional: Right-click → Extract data (text/attribute/table)
  → User stops recording (Stop button / Ctrl+Shift+S / Esc)
  → Steps saved to recorded_steps.json + generated_task.txt
  → User runs: python import_to_database.py
  → Steps uploaded to MSSQL via POST /automations
  → Later: python run_from_database.py
  → User enters automation ID
  → System fetches steps, creates execution record, replays in browser
  → Logs sent to database for review
```

### Flow 2: AI-Driven Freeform Execution
```
User writes task in generated_task.txt:
  "Open https://google.com and search for 'web automation'"

User runs: python run_from_task_txt_guided.py
  → Browser opens, connects to AI server via WebSocket
  → AI server normalizes task into Goal/Requirements/Success Criteria
  → AI server asks Llama 3.1 to plan actions
  → LLM returns JSON plan: [{action: "goto", url: "..."}, {action: "type", ...}]
  → Browser executes each action
  → Server verifies success (URL change, expected text)
  → If failure: retry with scroll/alternative strategy
  → On success: task-complete sent, logs saved
```

### Flow 3: Data Extraction (Web Scraping)
```
During recording:
  → User right-clicks on data element
  → Context menu appears: Extract Text / Extract Attribute / Extract Table
  → User chooses extraction type
  → Dialog asks for variable name (e.g., "exchange_rate")
  → Save dialog: checkboxes for Excel/Word/TXT + folder/filename/mode
  → Element highlighted with green outline (visual confirmation)
  → Extraction step recorded with locators + save config

During playback:
  → Server sends extractData command
  → Client tries locators in priority order (fallback)
  → Extracted value stored in page.__extracted_data__[variable_name]
  → If save_options configured: data saved to chosen file formats
```

### Flow 4: Table Extraction with Pagination
```
During recording:
  → User right-clicks on a table
  → System detects table element + reads column headers
  → Column selection dialog: checkboxes for each column
  → Pagination config: enable, max_pages, wait_per_page, page_timeout, retry_attempts
  → Variable name prompt (e.g., "product_catalog")
  → Save options dialog (Excel/CSV/TXT)

During playback:
  → JavaScript injected to extract rows from current page
  → Hash-based duplicate detection (prevents re-extracting same page)
  → Clicks "Next" button → waits for table to change (polling every 100ms)
  → Retries on duplicate data (up to retry_attempts)
  → Stops when: max_pages reached, no Next button, or timeout
  → All rows aggregated → saved to Excel/CSV/TXT
```

## Target User Personas

### Persona 1: Mariselvam (Automation Engineer)
- Wants free, local alternative to UiPath
- Needs automations to survive website redesigns
- Values transparency (can see LLM reasoning in logs)
- Comfortable with Python + command line

### Persona 2: QA Team Member
- Needs record-and-replay testing
- Wants resilient selectors that don't break on UI updates
- Needs execution logs for bug reports

### Persona 3: Data Analyst
- Scrapes tabular data from multi-page web tables
- Wants data exported to Excel for analysis
- Needs pagination support for large datasets

## Competitive Positioning

| Feature | WebAI | UiPath |
|---------|-------|--------|
| Intelligence | LLM reasoning (Llama 3.1) | Rule-based algorithms |
| Selector resilience | 10+ fallback locators | Single selector (breaks on changes) |
| Error recovery | AI adapts (scroll, retry, alternative) | Dumb retry → fail → human fix |
| Natural language | ✅ "Click the login button" | ❌ Exact recording only |
| Cost | Free (local Ollama) | Expensive licensing |
| Desktop automation | ❌ Web only | ✅ Windows apps, SAP, Citrix |
| No-code interface | ❌ Python scripts | ✅ Drag-and-drop Studio |
| Enterprise features | Basic (scheduling, templates) | Full Orchestrator, queues, analytics |
| Open source | ✅ Fully customizable | ❌ Closed source |

## Key Differentiator
**Self-healing automation through multi-locator fallback + AI reasoning.**
While UiPath breaks when a website changes, WebAI adapts automatically — saving hours of maintenance per broken automation.

## Related Documents
- `projectbrief.md` — Core requirements and scope
- `systemPatterns.md` — How the fallback strategy works technically
- `techContext.md` — Ollama setup and local execution