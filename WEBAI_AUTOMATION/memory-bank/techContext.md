# Tech Context — WebAI Platform

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| Language | Python | ≥3.9 | All components |
| Web Framework | FastAPI | 0.109.0 | REST API server |
| ASGI Server | Uvicorn | 0.27.0 | Runs FastAPI |
| Database | Microsoft SQL Server | — | Data persistence |
| DB Driver | pyodbc | 5.0.1 | ODBC connection to MSSQL |
| ORM | SQLAlchemy | 2.0.25 | Database models + queries |
| Browser Automation | Playwright | ≥1.40.0 | Chromium control |
| AI/LLM | Ollama | — | Local LLM inference |
| LLM Model | Llama 3.1 | — | Default model |
| WebSocket | websockets | ≥11.0 | AI server ↔ browser communication |
| Auth | python-jose | 3.3.0 | JWT tokens |
| Password Hashing | passlib + bcrypt | 1.7.4 / 4.1.2 | Secure password storage |
| Encryption | cryptography (Fernet) | 42.0.0 | Credential encryption |
| Data Validation | Pydantic | 2.5.3 | API request/response schemas |
| Env Config | python-dotenv | 1.0.0 | .env file loading |
| Scheduling | croniter | 2.0.1 | Cron expression parsing |
| Excel Export | openpyxl | — | .xlsx file generation |
| Word Export | python-docx | — | .docx file generation |
| Data Analysis | pandas | — | Table data → Excel/CSV |
| HTTP Client | requests | — | API calls from client scripts |

## Ports & Services

| Service | Port | Command to Start |
|---------|------|-----------------|
| API Server (FastAPI) | 8000 | `cd e:\WebAI_Project\webai_api_server && python run.py` |
| AI Server (WebSocket) | 8765 | `cd e:\WebAI_Project\webai_local_server && python -m webai_local_server.local_webai_server_guided` |
| Ollama (LLM) | 11434 | `ollama serve` |
| MSSQL | 1433 (default) | SQL Server service |

> ⚠️ **Note:** The shim file `webai_local_server/local_webai_server.py` imports from `webai_local_server.local_webai_server` (a non-existent module). The actual implementation is in `local_webai_server_guided.py`. Always run the guided module directly as shown above.

## Environment Variables

### `webai_api_server/.env`
```ini
# Database (ODBC connection string format)
DATABASE_URL=DRIVER={ODBC Driver 17 for SQL Server};SERVER=sweet\MSSQL;DATABASE=webai_automation;UID=sa;PWD=mariselvam;TrustServerCertificate=yes

# Security
SECRET_KEY=your-secret-key-change-this-in-production-32-chars-min-abcdef1234567890
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Encryption (Fernet key - KEEP SECRET!)
ENCRYPTION_KEY=f1HDOevt9N9oTVaTRjH21CtQjasFCjuvBCd9-vkNvAo=
```

### `webai_playwright_python/webai.config.json`
```json
{
  "TOKEN": "local-dev",
  "WEBSOCKET_PROTOCOL": "ws",
  "WEBSOCKET_HOST": "localhost:8765"
}
```

### AI Server (optional env vars, with defaults)
| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_URL` | `http://localhost:11434/api/chat` | Ollama chat endpoint |
| `OLLAMA_MODEL` | `llama3.1` | LLM model name |
| `OLLAMA_TEMPERATURE` | `0.2` | LLM creativity (low = deterministic) |
| `HOST` | `localhost` | WebSocket bind host |
| `PORT` | `8765` | WebSocket port |
| `WS_PATH` | `/api` | WebSocket path |
| `MAX_ROUNDS` | `12` | Max LLM planning rounds |
| `MAX_ACTIONS_PER_ROUND` | `6` | Max actions per LLM plan |
| `MAX_FAILURES` | `10` | Max failures before abort |
| `TASK_NORMALIZATION` | `1` | Enable task normalization |
| `PLAN_CACHE_FILE` | `plan_cache.json` | Plan cache location |

## Dependencies

### `webai_api_server/requirements.txt`
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pyodbc==5.0.1
python-multipart==0.0.6
pydantic==2.5.3
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
cryptography==42.0.0
python-dotenv==1.0.0
bcrypt==4.1.2
aiohttp==3.9.1
croniter==2.0.1
```

### `webai_playwright_python/requirements.txt`
```
playwright>=1.40.0
websockets>=11.0
```

### Additional (for data extraction features)
```
openpyxl        # Excel export
python-docx     # Word export
pandas          # Table data handling
requests        # HTTP client for API calls
```

## Development Setup

### One-Time Setup

#### 1. Install ODBC Driver 17 for SQL Server
- Download: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
- Or: `choco install sql-server-odbc-driver`

#### 2. Create Database
Open SQL Server Management Studio (SSMS):
```sql
CREATE DATABASE webai_automation;
GO
USE webai_automation;
GO
```

#### 3. Install Python Dependencies
```powershell
# API server
cd e:\WebAI_Project\webai_api_server
pip install -r requirements.txt

# Playwright client
cd e:\WebAI_Project\webai_playwright_python
pip install -r requirements.txt
pip install openpyxl python-docx pandas requests

# Install Chromium browser
playwright install chromium
```

#### 4. Initialize Database Tables
```powershell
cd e:\WebAI_Project\webai_api_server
python init_db.py
```

#### 5. Pull Ollama Model
```powershell
ollama pull llama3.1
```

### Running the System (3 terminals + 1 for usage)

#### Terminal 1: API Server
```powershell
cd e:\WebAI_Project\webai_api_server
python run.py
```
- Server: http://localhost:8000
- Docs: http://localhost:8000/docs (Swagger UI)
- Health: http://localhost:8000/health

#### Terminal 2: AI Server
```powershell
cd e:\WebAI_Project\webai_local_server
python -m webai_local_server.local_webai_server_guided
```
- WebSocket: ws://localhost:8765/api

#### Terminal 3: Ollama
```powershell
ollama serve
```
- Endpoint: http://localhost:11434

#### Terminal 4: Usage
```powershell
cd e:\WebAI_Project\webai_playwright_python

python record_then_run.py            # 📹 Record actions
python import_to_database.py         # 📤 Upload to database
python run_from_database.py          # ▶️ Replay from database
python run_from_task_txt_guided.py   # 🧠 AI executes plain English task
```

## Existing Credentials

| Item | Value |
|------|-------|
| Username | `mariselvam` |
| API Key | `o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8` |
| Automation ID | 1 (Wikipedia/Sastra search) |
| WebSocket Token | `local-dev` |

**Note:** The API key was auto-generated by `secrets.token_urlsafe(32)` in `auth.py` during user registration. It's stored in the `users` table `api_key` column and sent as `X-API-Key` header for API authentication.

## Database Connection Details

- **Server:** `sweet\MSSQL` (named instance)
- **Database:** `webai_automation`
- **User:** `sa`
- **Password:** `mariselvam`
- **Driver:** ODBC Driver 17 for SQL Server
- **TrustServerCertificate:** yes (local dev only)

**Connection string format:**
```
mssql+pyodbc:///?odbc_connect=<URL-encoded ODBC string>
```

## Technical Constraints

1. **Local-only deployment:** No cloud dependencies (except initial Ollama model download)
2. **Windows-focused:** Paths use `e:\` drive, `.env` uses Windows-style connection strings
3. **Single-user per API key:** No multi-tenant isolation beyond user_id filtering
4. **Chromium only:** Playwright configured for Chromium (not Firefox/WebKit)
5. **Non-headless recording:** Browser must be visible during recording (user interacts)
6. **Ollama dependency:** Freeform mode requires Ollama running; guided mode works without LLM
7. **MSSQL-specific:** Uses JSON column type (MSSQL `NVARCHAR(MAX)` with JSON validation)
8. **IST timezone:** Computed columns add 330 minutes (5:30) for Indian Standard Time

## Testing

### Test Files

**API Server** (`webai_api_server/`):
| File | Purpose |
|------|---------|
| `test_connection.py` | Database connection test |
| `test_endpoints.py` | API endpoint tests |
| `test_full_flow.py` | Execution + logging flow test |
| `test_logging.py` | Logging endpoint tests |
| `test_schema_changes.py` | IST columns + automation_id test |

**AI Server** (`webai_local_server/tests/`):
| File | Purpose |
|------|---------|
| `test_action_normalization.py` | Action normalization tests |
| `test_cache.py` | Plan cache tests |
| `test_confidence.py` | Confidence scoring tests |
| `test_normalize_task.py` | Task normalization tests |
| `test_retry_helpers.py` | Retry helper tests |
| `test_success_rules.py` | Success rules extraction tests |
| `test_templates.py` | System prompt template tests |

**Playwright Client** (`webai_playwright_python/`):
| File | Purpose |
|------|---------|
| `test_webai.py` | Client unit tests (mocked) |
| `test_cdp_fixes.py` | CDP function tests |
| `test_cdp_ids.py` | CDP element ID handling |
| `test_context_elements.py` | Interactive element detection |
| `test_e2e_dropdowns.py` | E2E dropdown tests (set `RUN_E2E=1`) |
| `test_select_smart.py` | Select smart unit tests |
| `test_semantic_commands.py` | Semantic command dispatch |
| `test_phase1_locators.py` | Locator capture verification |
| `test_quick.py` | Recorded steps structure |
| `test_error_logging.py` | Error logging with stacktraces |

### Running Tests
```powershell
# API server tests
cd e:\WebAI_Project\webai_api_server
python -m pytest -q

# AI server tests
cd e:\WebAI_Project\webai_local_server
python -m pytest -q

# Playwright tests
cd e:\WebAI_Project\webai_playwright_python
python -m pytest -q

# E2E tests (requires browser)
set RUN_E2E=1
python -m pytest test_e2e_dropdowns.py -q
```

## Migration Scripts

| Script | Purpose |
|--------|---------|
| `init_db.py` | Create all tables |
| `add_log_retention_column.py` | Add `log_retention_days` to `automation_configs` |
| `migrate_ist_and_automation_id.py` | Add IST computed columns + `automation_id` to logs |
| `timezone_fix.py` | IST timezone helper (reference) |

## Related Documents
- `systemPatterns.md` — Architecture and design patterns
- `activeContext.md` — Current running state
- `progress.md` — What's tested and working