# How to Run the WebAI Automation Project

To run the WebAI Automation project successfully, you need to run **three separate servers** simultaneously, plus the **client script**. You will need a total of four terminal windows.

> 🖥️ **No-terminal alternative (Dashboard):** Instead of running client scripts from a terminal, you can start the **Web UI Dashboard** (see Section 5 below) and drive run/import/monitor flows entirely from your browser at `http://localhost:8080`.

---

## 1. Start the API Server (Terminal 1)
This server handles the database, REST API endpoints, and execution logging.

1. Open Terminal 1
2. Navigate to the `webai_api_server` directory:
   ```bash
   cd webai_api_server
   ```
3. Start the server:
   ```bash
   python run.py
   ```
   *(Note: This runs on **Port 8000**)*

---

## 2. Start the AI Server (Terminal 2)
This server handles the WebSockets and AI communication/logic for guided automations.

1. Open Terminal 2
2. Navigate to the `webai_local_server` directory:
   ```bash
   cd webai_local_server
   ```
3. Activate the virtual environment (if you are using one):
   ```bash
   .\.venv\Scripts\Activate.ps1
   ```
4. Start the server:
   ```bash
   python -m webai_local_server.local_webai_server_guided
   ```
   *(Note: This runs on **Port 8765**)*

---

## 3. Start the Ollama Server (Terminal 3)
This runs the local LLM used by the AI server.

1. Open Terminal 3
2. Start the Ollama server:
   ```bash
   ollama serve
   ```
   *(Note: This runs on **Port 11434**. If you get a "bind: Only one usage of each socket address" error, it means Ollama is already running in the background and you can skip this step!)*

---

## 4. Run the Client Script (Terminal 4)
Once all three servers are running, you can run the actual automation client scripts.

1. Open Terminal 4
2. Navigate to the `webai_playwright_python` directory:
   ```bash
   cd webai_playwright_python
   ```
3. Activate the virtual environment (if you are using one):
   ```bash
   .\.venv\Scripts\Activate.ps1
   ```
4. Run your desired script. For example, to run an automation from the database:
   ```bash
   python run_from_database.py
   ```

### Available Client Scripts:
- `record_then_run.py`: Opens an interactive browser to record steps, saves them locally, and prompts to automatically upload/import the recording into the SQL Database.
- `import_to_database.py`: Imports a previously recorded `recorded_steps.json` into the API Server and MSSQL Database.
- `run_from_database.py`: Fetches and runs a previously recorded automation from the database using its Automation ID.
- `run_from_task_txt_guided.py`: Runs a guided AI automation based on a natural language task description.

---

## 5. (Optional) Start the Web UI Dashboard (Terminal 5)
The dashboard replaces the terminal for run/import/monitor flows — a browser-based front end for `run_from_database.py` and `import_to_database.py`.

1. Open Terminal 5
2. Navigate to the `webai_local_server` directory:
   ```bash
   cd webai_local_server
   ```
3. Start the dashboard server:
   ```bash
   python -m webai_dashboard.dashboard_server
   ```
   *(Note: This runs on **Port 8080**. Open `http://localhost:8080` in your browser, log in with your API username/password, and you can run automations, import `recorded_steps.json` files, watch execution status live, and view logs — no terminal needed for those flows.)*
> The dashboard still requires the **API Server (8000)** and **AI Server (8765)** to be running. Ollama (11434) is only needed for freeform (non-recorded) tasks.
