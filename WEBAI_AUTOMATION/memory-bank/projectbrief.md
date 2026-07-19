# Project Brief — WebAI Platform

## One-Line Summary
WebAI is a **Python-based, AI-powered web automation platform** that records browser actions, stores them in Microsoft SQL Server, and replays them on demand — like UiPath's Web Recorder, but with a local LLM brain (Llama 3.1) for self-healing automation.

## Core Purpose
Build a tool that lets users:
1. **Record** themselves using a website (clicks, typing, navigation, data extraction)
2. **Save** those recorded steps into a database for future reuse (orchestration)
3. **Replay** the automation later by selecting a project from the database
4. **Extract data** from web pages (text, attributes, tables with pagination) into Excel/Word/TXT/CSV
5. **Log everything** to SQL Server for debugging, analytics, and audit trails

## Goals
- **Primary:** Replace brittle, single-selector automation (UiPath-style) with a self-healing system that survives website redesigns
- **Secondary:** Provide database-backed orchestration so automations are reusable, shareable (templates), and schedulable (cron)
- **Tertiary:** Enable AI-driven freeform task execution from plain English ("Go to Google and search for cats")

## Project Scope

### In Scope
- ✅ Browser action recording (click, type, navigate, press_key, verify, extract, extract_table, wait)
- ✅ Multi-locator capture (10+ strategies per element) for resilient playback
- ✅ Database storage of automations, configs, execution history, logs
- ✅ Encrypted credential management (Fernet)
- ✅ Variable substitution (`{{username}}` → actual values at runtime)
- ✅ AI-guided playback using local Ollama / Llama 3.1
- ✅ Data extraction: text, attributes, tables (with pagination)
- ✅ Multi-format export: Excel (.xlsx), Word (.docx), Text (.txt), CSV
- ✅ Structured logging with batch upload + retention policy
- ✅ Cron-based scheduling for recurring automations
- ✅ User authentication (API keys, JWT, bcrypt passwords)
- ✅ Template system for sharing automations across users

### Out of Scope (Future Enhancements)
- ❌ Conditional branching based on extracted variable values (e.g., "if exchange_rate > 70, raise Jira ticket")
- ❌ Jira/incident ticket integration
- ❌ Desktop application automation (Windows apps, SAP, Citrix)
- ❌ Visual drag-and-drop workflow designer (no-code interface)
- ❌ Centralized queue management (UiPath Orchestrator-style)
- ❌ Mobile browser automation
- ❌ Cloud deployment (currently local-only)

## Key Features

### 1. Recording (UiPath Web Recorder Equivalent)
- Right-click context menu in browser → Extract Text / Extract Attribute / Extract Table / Add Delay
- Visual feedback hints for each recorded action
- Stop via button, Ctrl+Shift+S, Ctrl+Alt+S, or Esc
- Verification prompts: Ctrl+Shift+V (verify text), Ctrl+Shift+E (verify element)
- Add delay shortcut: Ctrl+Shift+W
- Captures 10+ locator strategies per element for fallback resilience

### 2. Database-Backed Orchestration
- Recorded automations stored in `automations` table as JSON
- Reusable: select project by ID → fetch steps → replay
- Per-user configs with encrypted secrets (e.g., your IRCTC password)
- Execution history tracks every run: status, duration, errors, extracted data
- Detailed logs per execution step for debugging

### 3. AI-Driven Playback
- **Guided mode:** Executes recorded steps sequentially with fallback locators (no LLM needed when locators exist)
- **Freeform mode:** LLM plans actions from page context + plain English task
- Self-healing: if locator #1 fails, tries #2, #3... up to 10+ strategies
- Confidence scoring (0-100) for task success verification

### 4. Data Extraction
- **Text extraction:** Right-click element → Extract Text → name variable
- **Attribute extraction:** Right-click → Extract Attribute → specify attribute (e.g., href)
- **Table extraction:** Right-click table → select columns → configure pagination
- Save to Excel/Word/TXT/CSV with folder, filename, and append/overwrite mode

## Target Users
- **Automation engineers** who want a free, local alternative to UiPath
- **Developers** comfortable with Python who need customizable web automation
- **QA teams** needing record-and-replay testing with resilient selectors
- **Data analysts** scraping tabular data from multi-page web tables

## Success Criteria
- Recorded automation replays successfully even after website UI changes (via fallback)
- Automations persist in database and can be re-run by ID without re-recording
- Data extraction produces correct files in chosen formats
- All execution steps are logged to database for audit/debugging
- System runs entirely locally (no cloud dependencies except optional Ollama model download)

## Project Structure
```
e:\WebAI_Project\
├── webai_api_server/          # FastAPI + MSSQL backend (port 8000)
├── webai_local_server/        # AI brain: WebSocket + Ollama (port 8765)
├── webai_playwright_python/   # Browser robot: Playwright recorder + player
├── memory-bank/               # This documentation
├── walkthrough.md             # Detailed source code analysis
└── *.docx                     # Feature notes & run guides
```

## Related Documents
- `productContext.md` — Why this project exists and user experience
- `systemPatterns.md` — Architecture and design patterns
- `techContext.md` — Technologies, dependencies, setup
- `decisionLog.md` — Key architectural decisions