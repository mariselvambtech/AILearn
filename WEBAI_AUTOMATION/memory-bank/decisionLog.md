# Decision Log — WebAI Platform

> **Records important architectural choices, technical decisions, and alternative approaches that were considered.**

## Decision: Refactoring `recorder.py` to Event Bus & Plugin Isolation

**Date:** 2026-08-03
**Status:** Implemented ✅

### Context
`recorder.py` previously mixed browser recording, event handling, context menu UI dialog generation, and file IO (Excel, Word, TXT saving) inside a single class, violating Section 9 of `AI_RULES.md`.

### Decision
Converted `WebRecorder` into a pure **Event Bus** core engine exposing pub/sub methods (`subscribe`, `unsubscribe`, `emit`). Extracted all data extraction dialogs and background file persistence logic into an isolated plugin ([data_extraction_plugin.py](file:///d:/AI/AILearn/WEBAI_AUTOMATION/webai_playwright_python/webai_playwright/plugins/data_extraction_plugin.py)).

### Impact
- Core recorder loop is lightweight and immutable.
- `DataExtractionPlugin` handles text/attribute/table extraction and file persistence independently.
- Plugin IO exceptions are isolated in `try/except` blocks, ensuring the main browser event loop never crashes.

---

## Decision 1: Multi-Locator Fallback vs Single Selector

**Date:** Phase 6
**Status:** Implemented ✅

### Context
Traditional web automation (UiPath) uses a single selector per element. When websites redesign, these selectors break, requiring manual fixes.

### Decision
Capture **10+ locator strategies** per element during recording and try them in priority order during playback.

### Alternatives Considered
1. **Single best selector** (UiPath approach) — Rejected: too brittle, breaks on changes
2. **LLM chooses selector at runtime** — Rejected: slow (LLM call per action), non-deterministic, expensive
3. **Anchor-based selectors** (UiPath newer) — Rejected: still limited, rule-based
4. **Multi-locator with priority fallback** ✅ — Chosen: deterministic, fast, self-healing

### Rationale
- `test-id` and `id` rarely change (developer-intended)
- `name` stable for forms
- `href` stable for links
- `xpath` is last resort (structure-dependent, breaks easily)
- By trying all in order, if one breaks, next works — no human intervention

### Impact
- **Positive:** Automations survive website redesigns; no manual selector fixes
- **Negative:** Slightly more data stored per step (locator array vs single string)
- **Trade-off:** Worth it for resilience

### Implementation
- `recorder.py` → `getLocatorCandidates(el)` collects all locators
- `fallback_helpers.py` → `click_with_fallback()` / `type_with_fallback()` tries in sorted order
- `local_webai_server_guided.py` → sorts by `LOCATOR_PRIORITY` dict, sends `clickWithFallback`/`typeWithFallback`

---

## Decision 2: LLM Bypass for Click/Type When Locators Exist

**Date:** Phase 6
**Status:** Implemented ✅

### Context
When recorded steps include locators, should we still ask the LLM to plan the action, or execute directly?

### Decision
**Bypass LLM entirely** for click/type when locators are available. Send `clickWithFallback`/`typeWithFallback` directly.

### Alternatives Considered
1. **Always use LLM** — Rejected: slow (1-3 seconds per action), non-deterministic, can make wrong choices
2. **Never use LLM** — Rejected: freeform mode needs LLM for arbitrary tasks
3. **Bypass LLM when locators exist, use LLM otherwise** ✅ — Chosen: best of both worlds

### Rationale
- Guided mode (recorded steps) should be fast and predictable
- LLM adds latency and unpredictability for no benefit when locators exist
- Freeform mode (no recorded steps) still needs LLM for planning

### Impact
- **Positive:** Guided mode is ~10x faster (no LLM call per action)
- **Positive:** Deterministic — same input always produces same output
- **Negative:** Less "intelligent" adaptation in guided mode (but fallback handles changes)

### Code Location
`local_webai_server_guided.py` lines ~1345-1422:
```python
if locators:
    sorted_locators = sorted(locators, key=lambda x: LOCATOR_PRIORITY.get(x.get("type"), 99))
    plan = [{"action": "clickWithFallback", "locators": sorted_locators}]
    return plan  # Skip LLM entirely
```

---

## Decision 3: Local Ollama vs Cloud LLM API

**Date:** Phase 5
**Status:** Implemented ✅

### Context
The AI server needs an LLM for freeform task planning. Cloud APIs (OpenAI, Anthropic) are powerful but require internet + API keys + cost money.

### Decision
Use **local Ollama with Llama 3.1** as the default LLM.

### Alternatives Considered
1. **OpenAI GPT-4 API** — Rejected: requires internet, API key, costs money per call, data leaves machine
2. **Anthropic Claude API** — Rejected: same issues as OpenAI
3. **Local Ollama + Llama 3.1** ✅ — Chosen: free, offline, private, customizable
4. **HuggingFace transformers** — Rejected: more complex setup, less optimized than Ollama

### Rationale
- Project goal is "free, local alternative to UiPath"
- Privacy: automation may involve credentials, sensitive data
- Cost: $0 for local inference
- Customizable: can swap models via `OLLAMA_MODEL` env var

### Impact
- **Positive:** Free, private, offline-capable
- **Negative:** Llama 3.1 less capable than GPT-4 for complex reasoning
- **Negative:** Requires local GPU/CPU resources for inference
- **Mitigation:** Guided mode doesn't need LLM at all

---

## Decision 4: Fernet Symmetric Encryption for Credentials

**Date:** Phase 2
**Status:** Implemented ✅

### Context
User credentials (passwords for automated sites) need secure storage in the database.

### Decision
Use **Fernet symmetric encryption** (from `cryptography` library).

### Alternatives Considered
1. **Plain text storage** — Rejected: extremely insecure
2. **AES-256 with manual key management** — Rejected: complex, error-prone
3. **Hashing (one-way)** — Rejected: need to decrypt to use credentials
4. **Fernet symmetric encryption** ✅ — Chosen: simple, secure, built-in key rotation support
5. **AWS KMS / Azure Key Vault** — Rejected: cloud dependency, project is local-only

### Rationale
- Fernet is AES-128-CBC with HMAC authentication — secure and simple
- Key stored in `.env` file (not in database)
- If database is compromised, credentials remain encrypted
- Simple API: `encrypt()` and `decrypt()`

### Impact
- **Positive:** Credentials secure at rest
- **Positive:** Simple implementation
- **Negative:** If `ENCRYPTION_KEY` lost, all credentials unrecoverable
- **Mitigation:** Documented warning in setup guide

---

## Decision 5: IST Timezone Computed Columns

**Date:** Migration
**Status:** Implemented ✅

### Context
Database stores UTC times, but user (in India) wants to see IST (UTC+5:30) times.

### Decision
Add **computed columns** (`started_at_ist`, `completed_at_ist`, `timestamp_ist`) using `DATEADD(MINUTE, 330, ...)`.

### Alternatives Considered
1. **Store IST directly** — Rejected: bad practice, breaks if server timezone changes
2. **Convert in application code** — Rejected: every query needs conversion logic
3. **Computed columns in DB** ✅ — Chosen: automatic, always correct, queryable
4. **Use Python `pytz` at query time** — Rejected: adds complexity to every query

### Rationale
- Computed columns are maintained by SQL Server automatically
- No application code changes needed for display
- Can query directly: `WHERE timestamp_ist > '2026-07-18'`

### Impact
- **Positive:** IST times always available without application logic
- **Negative:** Slightly more storage (computed columns)
- **Migration:** `migrate_ist_and_automation_id.py` script adds columns

---

## Decision 6: Batch Logging vs Individual Log Entries

**Date:** Phase 3
**Status:** Implemented ✅

### Context
Each execution generates many log entries (one per action). Sending each individually is slow and chatty.

### Decision
**Buffer logs and send in batches** via `POST /logs/batch`.

### Alternatives Considered
1. **Individual POST per log** — Rejected: too many HTTP requests, slow, network overhead
2. **WebSocket for logs** — Rejected: adds complexity, logs are not real-time critical
3. **Batch upload** ✅ — Chosen: efficient, simple, reduces network calls
4. **Write logs to file, import later** — Rejected: not real-time, manual import needed

### Rationale
- 50+ log entries per execution → 1 batch request instead of 50 individual
- Reduces API server load
- Client buffers and flushes at end (or when buffer full)

### Impact
- **Positive:** ~50x fewer HTTP requests
- **Positive:** Faster execution (less network overhead)
- **Negative:** Logs not visible in DB until flush (minor delay)
- **Implementation:** `logs_buffer` in `run_from_database.py`, `ServerLogger` in `server_logger.py`

---

## Decision 7: WebSocket for AI Server vs HTTP Polling

**Date:** Phase 5
**Status:** Implemented ✅

### Context
The AI server needs to send commands to the browser and receive results. This is a bidirectional, real-time conversation.

### Decision
Use **WebSocket** for AI server ↔ browser communication.

### Alternatives Considered
1. **HTTP polling** — Rejected: high latency, wasteful requests, not real-time
2. **Server-Sent Events (SSE)** — Rejected: one-directional (server → client only)
3. **WebSocket** ✅ — Chosen: bidirectional, real-time, efficient
4. **gRPC** — Rejected: overkill for this use case, more complex setup

### Rationale
- AI server sends command → browser executes → browser sends result → AI server processes
- This loop needs low latency and bidirectional communication
- WebSocket is the standard for real-time bidirectional communication

### Impact
- **Positive:** Real-time command/response, efficient
- **Positive:** Persistent connection (no reconnect per action)
- **Negative:** Requires WebSocket server management
- **Config:** `ws://localhost:8765/api?key=local-dev`

---

## Decision 8: Task Normalization Before LLM

**Date:** Phase 5
**Status:** Implemented ✅

### Context
Users write vague tasks like "search Google for cats." The LLM performs better with structured input.

### Decision
**Normalize tasks** into Goal/Requirements/Success Criteria format before sending to LLM.

### Alternatives Considered
1. **Send raw task to LLM** — Rejected: LLM may misunderstand vague instructions
2. **Require structured input from user** — Rejected: poor UX, users want to write naturally
3. **Auto-normalize with heuristics** ✅ — Chosen: best UX, improves LLM performance
4. **Use a separate LLM call to normalize** — Rejected: adds latency, overkill

### Rationale
- Heuristic normalization is fast (no LLM call)
- Detects intent: search, click, navigate, form, dropdown
- Extracts URLs automatically
- Adds constraints ("wait for page load", "prefer stable targeting")
- Adds success criteria for verification

### Impact
- **Positive:** Better LLM performance (structured input)
- **Positive:** Users can write naturally
- **Negative:** Heuristics may misclassify edge cases
- **Mitigation:** If task already structured (`_is_already_structured()`), skip normalization

---

## Decision 9: Action Normalization (LLM Tolerance)

**Date:** Phase 5
**Status:** Implemented ✅

### Context
LLMs sometimes return invalid field names (e.g., `by='name'` which isn't supported by Playwright locators).

### Decision
**Auto-fix common LLM mistakes** via `normalize_action()` function.

### Alternatives Considered
1. **Reject invalid actions** — Rejected: poor UX, automation fails on minor LLM errors
2. **Retry LLM with error feedback** — Rejected: slow, may repeat same mistake
3. **Auto-fix common mistakes** ✅ — Chosen: fast, tolerant, keeps automation running
4. **Strict prompt engineering only** — Rejected: LLMs are probabilistic, can't guarantee compliance

### Rationale
- LLMs are probabilistic — they will sometimes make mistakes
- Auto-fixing is faster than retrying
- Common fixes: `by='name'` → `by='text'`, `target` → `url` for goto, etc.

### Impact
- **Positive:** Fewer failures from LLM mistakes
- **Positive:** Faster (no retry needed)
- **Negative:** May mask real issues (invalid action silently "fixed")
- **Mitigation:** Logs warning when auto-fixing: `[WARN] LLM used invalid by='name', auto-converting`

---

## Decision 10: Plan Caching Disabled

**Date:** Phase 5
**Status:** Disabled by design ⚠️

### Context
Caching successful LLM plans would speed up repeated freeform tasks. Should we enable it?

### Decision
**Disable plan caching** (`replay_enabled = False`, `record_enabled = False`).

### Alternatives Considered
1. **Enable caching** — Rejected: cached plans may become stale if website changes
2. **Disable caching** ✅ — Chosen: fresh LLM planning each run ensures adaptability
3. **Cache with TTL** — Considered: adds complexity, not yet needed

### Rationale
- Freeform mode is for arbitrary tasks — caching may use stale plans
- Guided mode (recorded steps) already provides fast replay without LLM
- If needed later, caching can be re-enabled via env vars

### Impact
- **Positive:** Always fresh plans, adapts to website changes
- **Negative:** Slower for repeated freeform tasks (LLM call each time)
- **Workaround:** Use guided mode for repeated tasks

---

## Decision 11: Right-Click Context Menu for Extraction

**Date:** Phase 8.1
**Status:** Implemented ✅

### Context
How should users trigger data extraction during recording?

### Decision
Use **right-click context menu** with options: Extract Text, Extract Attribute, Extract Table, Add Delay.

### Alternatives Considered
1. **Toolbar button** — Rejected: takes screen space, less intuitive
2. **Keyboard shortcut** — Rejected: hard to discover, conflicts with browser shortcuts
3. **Right-click context menu** ✅ — Chosen: intuitive, discoverable, doesn't interfere with page
4. **Floating action button** — Rejected: may overlap page content

### Rationale
- Right-click is natural for "interact with this element" actions
- Context menu appears at cursor position (near target element)
- Doesn't interfere with normal page interactions
- Easy to add new options (Add Delay was added later)

### Impact
- **Positive:** Intuitive UX, element-targeted
- **Positive:** Extensible (can add more options)
- **Negative:** Overrides browser's native context menu during recording
- **Implementation:** `contextmenu` event listener in `recorder.py` JS

---

## Decision 12: Table Extraction via Injected JavaScript

**Date:** Phase 8.3
**Status:** Implemented ✅

### Context
Table extraction with pagination needs to read DOM, click "Next", wait for changes, and detect duplicates.

### Decision
Use **`page.evaluate()` with injected JavaScript** for the entire extraction loop.

### Alternatives Considered
1. **Python-side loop with Playwright calls** — Rejected: slow (round-trips per action), complex
2. **Injected JavaScript for entire loop** ✅ — Chosen: fast, single round-trip, handles pagination
3. **Hybrid (JS for extraction, Python for pagination)** — Rejected: more complex, no benefit

### Rationale
- JavaScript runs in page context — direct DOM access, no round-trips
- Pagination loop (extract → click Next → wait → repeat) is faster in JS
- Duplicate detection via hashing (first row + last row + count)
- Change detection via polling (every 100ms)

### Impact
- **Positive:** Fast, efficient table extraction
- **Positive:** Handles complex pagination scenarios
- **Negative:** Large JS block in Python string (harder to maintain)
- **Mitigation:** Well-commented JS code in `fallback_helpers.py`

---

## Decision 13: Database-Backed Orchestration vs File-Based

**Date:** Phase 2
**Status:** Implemented ✅

### Context
Should automations be stored as files (`recorded_steps.json`) or in a database?

### Decision
**Store in MSSQL database** with full CRUD API, but keep file-based as fallback.

### Alternatives Considered
1. **File-based only** — Rejected: hard to share, version, query, schedule
2. **Database only** — Rejected: harder to debug, no offline access
3. **Database primary, file fallback** ✅ — Chosen: best of both worlds
4. **Git-based versioning** — Rejected: no runtime API, no scheduling

### Rationale
- Database enables: orchestration by ID, multi-user, scheduling, templates, execution history
- File fallback: `run_from_database.py` saves to `recorded_steps.json` for playback compatibility
- User's use case: "select project from database and reuse" → requires database

### Impact
- **Positive:** Reusable automations, orchestration, scheduling
- **Positive:** Multi-user support with encrypted credentials
- **Negative:** Requires MSSQL setup (ODBC driver, database creation)
- **Migration path:** `import_to_database.py` uploads existing JSON files

---

## Decision 17: Front-End Dashboard as Orchestration Layer (Not API Server Extension)

**Date:** 2026-07-28
**Status:** Implemented ✅

### Context
The Enterprise Frontend Fleet workflow required a Web UI to run/import automations
without a terminal. The API server (port 8000) already exposes every required
endpoint — where should the dashboard live?

### Decision
Build the dashboard as a **separate orchestration tier** (`webai_local_server/webai_dashboard/`,
port 8080) that proxies the API server and owns the Playwright playback subprocess
lifecycle. The API server remains untouched.

### Alternatives Considered
1. **Extend `webai_api_server` with UI + run endpoints** — Rejected: couples the stable
   Warehouse DB layer to process management; workflow mandates the web server under
   `webai_local_server/`; higher regression risk.
2. **Static SPA calling the API server directly** — Rejected: the browser cannot spawn
   the local Playwright playback process; a server-side orchestrator is required.
3. **Dashboard as orchestration proxy** ✅ — Chosen: zero API-server changes, clear
   separation of concerns, dashboard owns subprocess + status finalization.

### Rationale
- Browser playback must run on the host machine (visible Chromium) — only a local
  server-side component can spawn it.
- A watcher thread finalizing `PUT /executions/{id}` closes the pre-existing gap
  where executions stayed "running" forever.
- Import uses `POST /automations` (not `/migrate/import-recording`) so `base_url`
  is derived from the first recorded step and stored.

### Impact
- **Positive:** Terminal-free run/import/monitor; executions finalize correctly;
  audit logs preserved (source="api").
- **Negative:** Orchestration logic partially duplicates `run_from_database.py`
  (accepted; CLI remains the canonical file-based fallback).
- **Note:** CLI scripts were refactored into programmatic functions
  (`run_automation`, `import_recording`) keeping both entry points in parity.

---

## Decision 18: Probe-Tolerant WebSocket Server (process_request + logging filter)

**Date:** 2026-07-29
**Status:** Implemented ✅

### Context
The AI WebSocket server (port 8765) terminal flooded with repeating
`EOFError: stream ends after 0 bytes` → `InvalidMessage` tracebacks. Health-check
probes (dashboard `/api/health` → `_probe_tcp`, port monitors) open a TCP
connection and close it without sending bytes; the `websockets` library
(`asyncio/server.py:365`) logs `logger.error("opening handshake failed",
exc_info=True)` for every such connection. Even a *valid* plain-HTTP GET is
rejected by `accept()` with `InvalidUpgrade` and still logged at ERROR.

### Decision
Harden the server itself, two layers, in `local_webai_server_guided.py`:
1. **`process_request=_http_health_response`** in `websockets.serve()` — plain
   HTTP requests (health checks, browsers, curl) get a clean `200 OK` response;
   genuine `Upgrade: websocket` requests return `None` and continue the normal
   handshake. When `process_request` returns a response, the library skips
   `accept()`, so no `handshake_exc` is set and nothing is logged.
2. **`_EmptyProbeNoiseFilter`** on the `websockets.server` logger — downgrades
   `opening handshake failed` records whose exception chain contains
   `EOFError ... "0 bytes"` (definitively an empty probe: no data was ever sent)
   from ERROR to DEBUG. Genuine failures (malformed bytes, bad headers) remain
   at ERROR.

Client side: dashboard `dashboard_health()` switched from `_probe_tcp()` to
`_probe_ws()` (sends a valid `GET / HTTP/1.1` request line).

### Alternatives Considered
1. **Only fix the dashboard probe** — Rejected: insufficient; the old dashboard
   process keeps probing until restarted, other tools (port monitors, IDEs) can
   probe too, and even `_probe_ws`'s plain GET triggers `InvalidUpgrade` ERROR
   logs without layer 1.
2. **Suppress ALL 'opening handshake failed' records** — Rejected: hides genuine
   handshake failures (malformed clients, config mistakes) that should stay visible.
3. **`process_request` + targeted empty-probe downgrade** ✅ — Chosen: clean HTTP
   semantics for health checks, silent for empty probes, loud for real errors.

### Impact
- **Positive:** Terminal stays clean regardless of which client probes the port;
  HTTP health checks get a meaningful 200 response; real WebSocket clients and
  genuine error visibility unaffected.
- **Negative:** Empty-probe events only visible at DEBUG (acceptable — they carry
  no actionable information).
- **Verification:** `scratch/test_ws_probe_fix.py` E2E (4 scenarios) + 34/34 pytest.

---

## Future Decisions Pending


### Decision 14: Conditional Branching Implementation (Pending)
**Question:** How to implement if/else logic based on extracted variable values?
**Options:**
1. New `condition` action type in recorder
2. LLM-based conditional evaluation
3. Rule-based condition engine in AI server
**Status:** Awaiting user direction

### Decision 15: Jira Integration Approach (Pending)
**Question:** How to integrate with Jira for ticket creation?
**Options:**
1. Direct Jira REST API calls from AI server
2. Webhook to external integration service
3. Store condition results in DB, separate worker creates tickets
**Status:** Awaiting user direction

### Decision 16: Variable Persistence Model (Pending)
**Question:** How should extracted variables persist across steps for condition checks?
**Options:**
1. In-memory dict (current: `page.__extracted_data__`)
2. Server-side variable context (sent with each command)
3. Database-backed variable store
**Status:** Awaiting user direction

## Related Documents
- `systemPatterns.md` — How these decisions manifest in code
- `progress.md` — Which decisions are implemented vs pending
- `activeContext.md` — Current open questions