"""
WebAI Dashboard Server — web UI + orchestration API.

This FastAPI server is the fourth tier of the WebAI platform: it serves the
front-end dashboard (static SPA) and exposes an orchestration API that lets
users run and import database-backed automations without touching a terminal.

It replaces the interactive CLI flows of:
  - `run_from_database.py`   -> POST /api/automations/run
  - `import_to_database.py`  -> POST /api/automations/import (+ auth modals)

The dashboard never talks to MSSQL directly; it proxies authenticated calls
to the existing API server (port 8000) and owns the Playwright playback
subprocess lifecycle via `PlaybackProcessManager`.

Run with:
    cd webai_local_server
    python -m webai_dashboard.dashboard_server
"""
import json
import os
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import uvicorn
from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from webai_dashboard.process_manager import PlaybackProcessManager

# ---------------------------------------------------------------------------
# Paths & configuration
# ---------------------------------------------------------------------------

PACKAGE_DIR = Path(__file__).resolve().parent          # webai_dashboard/
REPO_ROOT = PACKAGE_DIR.parent.parent                  # repository root
CLIENT_DIR = REPO_ROOT / "webai_playwright_python"     # Playwright client dir
STATIC_DIR = PACKAGE_DIR / "static"                    # front-end assets
PLAYBACK_SCRIPT = "run_from_task_txt_guided.py"        # guided playback entry
VENV_PYTHON = CLIENT_DIR / ".venv" / "Scripts" / "python.exe"

API_URL = os.getenv("WEBAI_API_URL", "http://localhost:8000")
OLLAMA_URL = os.getenv("WEBAI_OLLAMA_URL", "http://localhost:11434")
AI_SERVER_HOST = os.getenv("AI_SERVER_HOST", "localhost")
AI_SERVER_PORT = int(os.getenv("AI_SERVER_PORT", "8765"))
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "127.0.0.1")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8080"))

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="WebAI Dashboard Server",
    description="Web UI + orchestration API for running WebAI automations without a terminal",
    version="1.0.0",
)

# Local-only tool: allow the browser SPA (served by this same app) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

process_manager = PlaybackProcessManager()


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

class LoginPayload(BaseModel):
    """Credentials forwarded to the API server's /auth/login endpoint."""
    username: str
    password: str


class RegisterPayload(BaseModel):
    """Registration details forwarded to the API server's /auth/register endpoint."""
    username: str
    email: Optional[str] = None
    password: str


class RunRequest(BaseModel):
    """Payload for triggering an automation run from the dashboard."""
    automation_id: int


class RecordRequest(BaseModel):
    """Payload for starting a new interactive recording session from the dashboard."""
    name: str
    start_url: str
    description: Optional[str] = None


class RunResponse(BaseModel):
    """Result of a successfully dispatched automation run."""
    execution_id: Optional[int]
    run_id: int
    automation_id: int
    step_count: int
    status: str
    message: str


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _require_api_key(x_api_key: Optional[str]) -> str:
    """
    Validate that the caller supplied an X-API-Key header.

    Args:
        x_api_key: Raw header value (may be None).

    Returns:
        The API key string.

    Raises:
        HTTPException: 401 when the header is missing or empty.
    """
    if not x_api_key or not x_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header. Log in via the dashboard first.",
        )
    return x_api_key.strip()


def _safe_detail(response: requests.Response) -> Any:
    """
    Extract an error detail payload from an upstream API response.

    Args:
        response: The upstream `requests.Response`.

    Returns:
        Parsed JSON body when possible, otherwise truncated raw text.
    """
    try:
        return response.json()
    except ValueError:
        return response.text[:300]


def _proxy_get(path: str, api_key: str, params: Optional[Dict[str, Any]] = None) -> Any:
    """
    Proxy an authenticated GET request to the API server.

    Args:
        path: API server path (e.g. "/automations").
        api_key: Caller's X-API-Key.
        params: Optional query parameters.

    Returns:
        Parsed JSON response body.

    Raises:
        HTTPException: 502 when the API server is unreachable, or the upstream
            status code when it returns an error.
    """
    try:
        resp = requests.get(
            f"{API_URL}{path}",
            headers={"X-API-Key": api_key},
            params=params,
            timeout=15,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"API server unreachable at {API_URL}: {exc}",
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=_safe_detail(resp))
    return resp.json()


def _probe_tcp(host: str, port: int, timeout: float = 1.5) -> bool:
    """Return True when a TCP connection to host:port succeeds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _probe_ws(host: str, port: int, timeout: float = 2.0) -> bool:
    """
    Probe a WebSocket server by sending a minimal HTTP request.

    Unlike a raw TCP probe (which causes ``EOFError`` noise in the
    ``websockets`` server logs because it sends 0 bytes and closes),
    this sends a valid HTTP/1.1 request line so the server can respond
    with a proper HTTP status (e.g. 426 Upgrade Required) instead of
    logging a handshake failure.

    Args:
        host: WebSocket server hostname.
        port: WebSocket server port.
        timeout: Socket timeout in seconds.

    Returns:
        True when the server responds with any HTTP data.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            # Send a minimal HTTP/1.1 GET request. The websockets server
            # parses the request line successfully and responds with an HTTP
            # error (426 Upgrade Required) since this is not a valid WebSocket
            # upgrade request — a clean exchange with no error logging.
            sock.sendall(
                b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n"
            )
            data = sock.recv(128)
            return bool(data)
    except OSError:
        return False


def _probe_http(url: str, timeout: float = 2.0) -> bool:
    """Return True when an HTTP GET to url returns any non-server-error status."""
    try:
        return requests.get(url, timeout=timeout).status_code < 500
    except requests.RequestException:
        return False


def validate_steps_payload(steps: Any) -> List[Dict[str, Any]]:
    """
    Validate an uploaded recording payload.

    Args:
        steps: Parsed JSON from the uploaded file.

    Returns:
        The steps list when valid.

    Raises:
        HTTPException: 422 when the payload is not a non-empty list of step
            objects each containing an "action" field.
    """
    if not isinstance(steps, list) or not steps:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Recording must be a non-empty JSON array of steps.",
        )
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or "action" not in step:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Step {index} is invalid: each step must be an object with an 'action' field.",
            )
    return steps


def derive_base_url(steps: List[Dict[str, Any]]) -> Optional[str]:
    """
    Derive an automation's starting URL from its recorded steps.

    Args:
        steps: Validated recorded steps.

    Returns:
        The first http(s) URL found in the steps, or None.
    """
    for step in steps:
        url = step.get("url")
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            return url
    return None


def build_task_text(automation_name: str, base_url: Optional[str]) -> str:
    """
    Build the `generated_task.txt` content consumed by the guided playback client.

    Guided mode follows the recorded steps, so the task text only needs to
    prime the starting URL and set generic success criteria.

    Args:
        automation_name: Name of the automation being run.
        base_url: Starting URL (first recorded URL), if any.

    Returns:
        Task text (multi-line string) to write into `generated_task.txt`.
    """
    lines: List[str] = []
    if base_url:
        lines.append(f"Open {base_url}")
    lines.append(f"Execute the recorded automation '{automation_name}' step by step.")
    lines.append("Finish with done only after verification.")
    return "\n".join(lines) + "\n"


def _select_playback_python() -> Path:
    """
    Choose the Python interpreter for the playback subprocess.

    Prefers the Playwright client virtual environment (which has Playwright
    installed); falls back to the interpreter running this dashboard.

    Returns:
        Path to the Python executable.
    """
    if VENV_PYTHON.exists():
        return VENV_PYTHON
    return Path(sys.executable)


def _flush_orchestration_logs(logs: List[Dict[str, Any]], execution_id: Optional[int], api_key: str) -> None:
    """
    Best-effort batch upload of dashboard orchestration logs to the API server.

    Mirrors the client-side logging behavior of `run_from_database.py` so
    dashboard-triggered runs keep the same audit trail. Never raises.

    Args:
        logs: Buffered log entries (cleared after the attempt).
        execution_id: Execution record to attach logs to (None skips upload).
        api_key: Caller's X-API-Key.
    """
    if not logs or execution_id is None:
        return
    try:
        requests.post(
            f"{API_URL}/logs/batch",
            json={"execution_id": execution_id, "logs": logs},
            headers={"X-API-Key": api_key},
            timeout=5,
        )
    except requests.RequestException as exc:
        print(f"[WARN] Dashboard log flush failed: {exc}")
    finally:
        logs.clear()


def _buffer_log(logs: List[Dict[str, Any]], level: str, message: str,
                metadata: Optional[Dict[str, Any]] = None) -> None:
    """Append one orchestration log entry to the buffer (source='api')."""
    logs.append({
        "timestamp": datetime.now().isoformat(),
        "level": level,
        "source": "api",
        "message": message,
        "metadata": metadata or {},
    })


# ---------------------------------------------------------------------------
# Health & auth endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def dashboard_health() -> Dict[str, Any]:
    """
    Report the health of the dashboard itself and its upstream dependencies.

    Probes the API server (HTTP :8000), AI server (TCP :8765) and Ollama
    (HTTP :11434) so the front-end can show live status badges.
    """
    return {
        "dashboard": "online",
        "api_server": "online" if _probe_http(f"{API_URL}/health") else "offline",
        # Use _probe_ws (not _probe_tcp) so the websockets AI server gets a
        # valid HTTP request line and responds cleanly instead of logging
        # "EOFError: stream ends after 0 bytes" handshake failures.
        "ai_server": "online" if _probe_ws(AI_SERVER_HOST, AI_SERVER_PORT) else "offline",
        "ollama": "online" if _probe_http(f"{OLLAMA_URL}/api/tags") else "offline",
    }


@app.post("/api/auth/login")
async def login(payload: LoginPayload) -> Dict[str, Any]:
    """
    Proxy login to the API server and return the user's API key.

    The front-end stores the returned `api_key` in localStorage and sends it
    as the X-API-Key header on subsequent dashboard API calls. The dashboard
    itself never persists credentials.
    """
    try:
        resp = requests.post(
            f"{API_URL}/auth/login",
            json={"username": payload.username, "password": payload.password},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"API server unreachable at {API_URL}: {exc}",
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=_safe_detail(resp))
    return resp.json()


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterPayload) -> Dict[str, Any]:
    """Proxy user registration to the API server."""
    try:
        resp = requests.post(
            f"{API_URL}/auth/register",
            json={
                "username": payload.username,
                "email": payload.email,
                "password": payload.password,
            },
            timeout=15,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"API server unreachable at {API_URL}: {exc}",
        )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=_safe_detail(resp))
    return resp.json()


# ---------------------------------------------------------------------------
# Automation endpoints
# ---------------------------------------------------------------------------

@app.get("/api/automations")
async def list_automations(x_api_key: Optional[str] = Header(default=None)) -> Any:
    """List the caller's automations (dashboard card grid data source)."""
    api_key = _require_api_key(x_api_key)
    return _proxy_get("/automations", api_key)


@app.get("/api/automations/{automation_id}")
async def get_automation(automation_id: int,
                         x_api_key: Optional[str] = Header(default=None)) -> Any:
    """Fetch one automation including its recorded steps (View Steps modal)."""
    api_key = _require_api_key(x_api_key)
    return _proxy_get(f"/automations/{automation_id}", api_key)


@app.post("/api/automations/run", response_model=RunResponse)
async def run_automation_endpoint(request: RunRequest,
                                  x_api_key: Optional[str] = Header(default=None)) -> RunResponse:
    """
    Trigger browser playback of a database-backed automation.

    Replaces the interactive `run_from_database.py` flow:
      1. Fetch steps (variables/secrets already substituted) from the API server.
      2. Write `recorded_steps.json` and regenerate `generated_task.txt` in the
         Playwright client directory.
      3. Create an execution record.
      4. Spawn `run_from_task_txt_guided.py` as a background subprocess; a
         watcher thread finalizes the execution status when playback exits.

    Args:
        request: Body containing the `automation_id` to run.
        x_api_key: Caller's X-API-Key header.

    Returns:
        RunResponse with the execution ID, internal run ID and step count.
    """
    api_key = _require_api_key(x_api_key)
    logs: List[Dict[str, Any]] = []

    # Pre-flight: playback client must exist on this machine
    playback_path = CLIENT_DIR / PLAYBACK_SCRIPT
    if not playback_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Playback client not found at {playback_path}",
        )

    # 1) Fetch variable-substituted steps
    _buffer_log(logs, "INFO", f"Dashboard: fetching automation {request.automation_id}",
                {"automation_id": request.automation_id})
    try:
        resp = requests.get(
            f"{API_URL}/execute/{request.automation_id}/steps",
            headers={"X-API-Key": api_key},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"API server unreachable at {API_URL}: {exc}",
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=_safe_detail(resp))

    payload = resp.json()
    steps = payload.get("steps") or []
    base_url = payload.get("base_url")
    if not steps:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Automation {request.automation_id} has no steps to execute.",
        )
    _buffer_log(logs, "INFO", f"Fetched {len(steps)} steps",
                {"step_count": len(steps), "base_url": base_url})

    # Fetch the automation name (used for the generated task file); tolerate failure
    automation_name = f"Automation {request.automation_id}"
    try:
        meta = _proxy_get(f"/automations/{request.automation_id}", api_key)
        automation_name = meta.get("name") or automation_name
        if not base_url:
            base_url = meta.get("base_url")
    except HTTPException:
        pass  # name/base_url fallback is sufficient for playback

    # 2) Write the files the playback client reads
    try:
        (CLIENT_DIR / "recorded_steps.json").write_text(
            json.dumps(steps, indent=2), encoding="utf-8"
        )
        (CLIENT_DIR / "generated_task.txt").write_text(
            build_task_text(automation_name, base_url), encoding="utf-8"
        )
    except OSError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write playback files in {CLIENT_DIR}: {exc}",
        )
    _buffer_log(logs, "INFO", "Playback files written",
                {"client_dir": str(CLIENT_DIR), "base_url": base_url})

    # 3) Create the execution record (best effort — playback can run without it)
    execution_id: Optional[int] = None
    try:
        exec_resp = requests.post(
            f"{API_URL}/execute",
            json={"automation_id": request.automation_id},
            headers={"X-API-Key": api_key},
            timeout=15,
        )
        if exec_resp.status_code == 201:
            execution_id = exec_resp.json().get("id")
            _buffer_log(logs, "INFO", "Execution record created",
                        {"execution_id": execution_id})
        else:
            _buffer_log(logs, "WARN", "Could not create execution record",
                        {"status_code": exec_resp.status_code})
    except requests.RequestException as exc:
        _buffer_log(logs, "WARN", f"Execution record request failed: {exc}")

    # 4) Spawn the playback subprocess (watcher finalizes status on exit)
    env = os.environ.copy()
    if execution_id is not None:
        env["WEBAI_EXECUTION_ID"] = str(execution_id)
        env["WEBAI_API_URL"] = API_URL
        env["WEBAI_API_KEY"] = api_key

    run = process_manager.spawn(
        automation_id=request.automation_id,
        execution_id=execution_id,
        python_exe=_select_playback_python(),
        script=PLAYBACK_SCRIPT,
        cwd=CLIENT_DIR,
        env=env,
        api_url=API_URL,
        api_key=api_key,
    )
    _buffer_log(logs, "INFO", f"Playback subprocess spawned (run_id={run.run_id})",
                {"run_id": run.run_id, "pid": run.process.pid})
    _flush_orchestration_logs(logs, execution_id, api_key)

    return RunResponse(
        execution_id=execution_id,
        run_id=run.run_id,
        automation_id=request.automation_id,
        step_count=len(steps),
        status="started",
        message=f"Playback started for '{automation_name}' ({len(steps)} steps).",
    )


@app.post("/api/automations/record", status_code=status.HTTP_202_ACCEPTED)
async def record_automation_endpoint(
    req: RecordRequest,
    x_api_key: Optional[str] = Header(default=None)
) -> Dict[str, Any]:
    """
    Launch an interactive browser session to record a new automation.

    Spawns ``record_then_run.py`` in non-headless Chromium mode. Intercepts
    user clicks, inputs, and data extractions, and automatically uploads the
    result to the API database on completion.

    Args:
        req: RecordRequest containing name, start_url, and optional description.
        x_api_key: Caller's X-API-Key header.

    Returns:
        Dict with status, run_id, and confirmation message.
    """
    api_key = _require_api_key(x_api_key)
    logs: List[Dict[str, Any]] = []
    _buffer_log(logs, "INFO", f"Dashboard: starting recording session for '{req.name}'",
                {"name": req.name, "start_url": req.start_url})

    if not _probe_http(f"{API_URL}/health"):
        _buffer_log(logs, "ERROR", "API server unreachable prior to recording launch")
        _flush_orchestration_logs(logs, None, api_key)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"API server unreachable at {API_URL}",
        )

    python_exe = _select_playback_python()
    cwd = CLIENT_DIR
    env = os.environ.copy()
    env["WEBAI_START_URL"] = req.start_url
    env["WEBAI_AUTOMATION_NAME"] = req.name
    env["WEBAI_AUTOMATION_DESC"] = req.description or ""
    env["WEBAI_AUTO_IMPORT"] = "1"
    env["WEBAI_API_URL"] = API_URL
    env["WEBAI_API_KEY"] = api_key

    run = process_manager.spawn(
        automation_id=0,
        execution_id=None,
        python_exe=python_exe,
        script="record_then_run.py",
        cwd=cwd,
        env=env,
        api_url=API_URL,
        api_key=api_key,
    )
    _buffer_log(logs, "INFO", f"Recording process spawned (run_id={run.run_id})")
    _flush_orchestration_logs(logs, None, api_key)

    return {
        "status": "recording_started",
        "run_id": run.run_id,
        "message": f"Interactive recording started for '{req.name}'. Perform your actions in the opened Chromium browser window.",
    }


@app.delete("/api/automations/{automation_id}", status_code=status.HTTP_200_OK)
async def delete_automation(automation_id: int,
                           x_api_key: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    """
    Delete an automation and its dependent records via the API server.

    Proxies ``DELETE /automations/{id}`` to the API server, which cascades the
    deletion to ``automation_configs``, ``execution_history``,
    ``execution_logs`` and ``scheduled_runs``. A best-effort audit log entry
    is appended so the deletion is traceable.

    Args:
        automation_id: Database ID of the automation to delete.
        x_api_key: Caller's X-API-Key header.

    Returns:
        A summary dict with ``success``, ``automation_id`` and ``message``.
    """
    api_key = _require_api_key(x_api_key)
    logs: List[Dict[str, Any]] = []
    _buffer_log(logs, "INFO", f"Dashboard: deleting automation {automation_id}",
                {"automation_id": automation_id})

    try:
        resp = requests.delete(
            f"{API_URL}/automations/{automation_id}",
            headers={"X-API-Key": api_key},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"API server unreachable at {API_URL}: {exc}",
        )

    if resp.status_code not in (200, 204):
        raise HTTPException(status_code=resp.status_code, detail=_safe_detail(resp))

    _buffer_log(logs, "INFO", f"Automation {automation_id} deleted successfully",
                {"automation_id": automation_id})
    # Best-effort audit log — no execution_id to attach to, so skip batch upload
    # (the API server has no standalone audit endpoint; deletion is logged here only)
    return {
        "success": True,
        "automation_id": automation_id,
        "message": f"Automation {automation_id} deleted successfully.",
    }


@app.post("/api/automations/import", status_code=status.HTTP_201_CREATED)
async def import_automation(file: UploadFile = File(...),
                            name: str = Form(...),
                            description: str = Form(""),
                            x_api_key: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    """
    Import a recorded_steps.json file as a new database automation.

    Replaces the interactive `import_to_database.py` flow. The recording is
    uploaded directly from the browser; the starting URL is derived from the
    first recorded step and stored as the automation's `base_url`.

    Args:
        file: Uploaded `recorded_steps.json` file.
        name: Automation name (form field).
        description: Optional description (form field).
        x_api_key: Caller's X-API-Key header.

    Returns:
        Import summary including the new `automation_id`.
    """
    api_key = _require_api_key(x_api_key)

    raw = await file.read()
    try:
        steps_raw = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Uploaded file is not valid JSON: {exc}",
        )

    steps = validate_steps_payload(steps_raw)
    base_url = derive_base_url(steps)

    try:
        resp = requests.post(
            f"{API_URL}/automations",
            json={
                "name": name,
                "description": description or "Imported via WebAI Dashboard",
                "base_url": base_url,
                "steps_json": steps,
                "is_template": False,
            },
            headers={"X-API-Key": api_key},
            timeout=30,
        )
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"API server unreachable at {API_URL}: {exc}",
        )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=resp.status_code, detail=_safe_detail(resp))

    created = resp.json()
    return {
        "success": True,
        "automation_id": created.get("id"),
        "name": name,
        "step_count": len(steps),
        "base_url": base_url,
    }


# ---------------------------------------------------------------------------
# Execution monitoring endpoints
# ---------------------------------------------------------------------------

@app.get("/api/executions")
async def list_executions(limit: int = 20,
                          x_api_key: Optional[str] = Header(default=None)) -> Any:
    """
    List recent executions, annotated with live subprocess status.

    When an execution was launched by this dashboard and its playback process
    is still alive (or just finished), a `live_status` field is merged into
    the response so the front-end can show real-time progress.
    """
    api_key = _require_api_key(x_api_key)
    executions = _proxy_get("/executions", api_key, params={"limit": limit})
    for execution in executions:
        run = process_manager.get_by_execution(execution.get("id"))
        execution["live_status"] = run.status if run else None
    return executions


@app.get("/api/executions/{execution_id}/logs")
async def get_execution_logs(execution_id: int, limit: int = 200,
                             x_api_key: Optional[str] = Header(default=None)) -> Any:
    """Fetch logs for one execution (logs viewer modal data source)."""
    api_key = _require_api_key(x_api_key)
    return _proxy_get(f"/executions/{execution_id}/logs", api_key, params={"limit": limit})


@app.get("/api/runs")
async def list_runs() -> List[Dict[str, Any]]:
    """List playback subprocesses spawned by this dashboard (live diagnostics)."""
    return [run.to_dict() for run in process_manager.list_runs()]


# ---------------------------------------------------------------------------
# Static front-end (mounted last so /api routes take precedence)
# ---------------------------------------------------------------------------

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    print("=" * 60)
    print(" WebAI Dashboard Server")
    print("=" * 60)
    print(f" Dashboard: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print(f" API server: {API_URL}")
    print(f" AI server probe: {AI_SERVER_HOST}:{AI_SERVER_PORT}")
    print("=" * 60)
    uvicorn.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT)
