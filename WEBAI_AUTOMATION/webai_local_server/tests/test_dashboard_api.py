"""
QA suite for the WebAI Dashboard Server (webai_dashboard).

Covers two layers:

1. **Unit tests (offline, always run):** helper functions (step validation,
   base-URL derivation, task-text generation), auth enforcement, health
   endpoint shape, and upstream-failure handling. The API server is replaced
   by monkeypatched `requests` stubs — no live services required.

2. **Integration tests (auto-skipped when the API server is offline):**
   exercised against a real API server on WEBAI_API_URL (default
   http://localhost:8000) using the QA credentials from WEBAI_QA_API_KEY.
   These validate the proxy chain end-to-end without launching a browser.

Run with:
    cd webai_local_server
    ..\\webai_playwright_python\\.venv\\Scripts\\python.exe -m pytest tests/test_dashboard_api.py -v
"""
import io
import json
import os
from typing import Any, Dict, List, Optional

import pytest
import requests
from fastapi.testclient import TestClient

from webai_dashboard import dashboard_server
from webai_dashboard.dashboard_server import (
    app,
    build_task_text,
    derive_base_url,
    validate_steps_payload,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixtures & stubs
# ---------------------------------------------------------------------------

API_KEY = os.getenv("WEBAI_QA_API_KEY", "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8")
AUTH_HEADERS = {"X-API-Key": API_KEY}

SAMPLE_STEPS: List[Dict[str, Any]] = [
    {"action": "open", "url": "https://example.com/", "name": None, "value": None},
    {"action": "click", "url": "https://example.com/page", "name": "Go", "value": None},
    {"action": "type", "url": None, "name": "q", "value": "hello"},
]


class FakeResponse:
    """Minimal stand-in for `requests.Response` used by monkeypatched stubs."""

    def __init__(self, status_code: int = 200, payload: Optional[Any] = None) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = json.dumps(self._payload)

    def json(self) -> Any:
        return self._payload


# ---------------------------------------------------------------------------
# Unit tests — pure helpers
# ---------------------------------------------------------------------------

class TestValidateStepsPayload:
    """Step-payload validation for the import endpoint."""

    def test_valid_steps_pass_through(self) -> None:
        assert validate_steps_payload(SAMPLE_STEPS) == SAMPLE_STEPS

    def test_rejects_non_list(self) -> None:
        with pytest.raises(Exception) as exc_info:
            validate_steps_payload({"action": "open"})
        assert getattr(exc_info.value, "status_code", None) == 422

    def test_rejects_empty_list(self) -> None:
        with pytest.raises(Exception) as exc_info:
            validate_steps_payload([])
        assert getattr(exc_info.value, "status_code", None) == 422

    def test_rejects_step_without_action(self) -> None:
        with pytest.raises(Exception) as exc_info:
            validate_steps_payload([{"url": "https://example.com"}])
        assert getattr(exc_info.value, "status_code", None) == 422


class TestDeriveBaseUrl:
    """Base-URL derivation from recorded steps."""

    def test_first_http_url_wins(self) -> None:
        assert derive_base_url(SAMPLE_STEPS) == "https://example.com/"

    def test_returns_none_without_urls(self) -> None:
        steps = [{"action": "click", "name": "Go"}]
        assert derive_base_url(steps) is None

    def test_ignores_non_http_urls(self) -> None:
        steps = [{"action": "open", "url": "ftp://example.com"}]
        assert derive_base_url(steps) is None


class TestBuildTaskText:
    """generated_task.txt content generation for guided playback."""

    def test_includes_open_line_with_base_url(self) -> None:
        text = build_task_text("My Automation", "https://example.com")
        assert text.startswith("Open https://example.com")
        assert "My Automation" in text
        assert text.endswith("\n")

    def test_omits_open_line_without_base_url(self) -> None:
        text = build_task_text("My Automation", None)
        assert not text.startswith("Open ")
        assert "My Automation" in text


# ---------------------------------------------------------------------------
# Unit tests — HTTP layer (upstream stubbed via monkeypatch)
# ---------------------------------------------------------------------------

class TestAuthEnforcement:
    """X-API-Key header enforcement on protected endpoints."""

    def test_automations_requires_api_key(self) -> None:
        resp = client.get("/api/automations")
        assert resp.status_code == 401

    def test_executions_requires_api_key(self) -> None:
        resp = client.get("/api/executions")
        assert resp.status_code == 401

    def test_run_requires_api_key(self) -> None:
        resp = client.post("/api/automations/run", json={"automation_id": 1})
        assert resp.status_code == 401

    def test_import_requires_api_key(self) -> None:
        files = {"file": ("recorded_steps.json", io.BytesIO(b"[]"), "application/json")}
        resp = client.post("/api/automations/import", files=files, data={"name": "X"})
        assert resp.status_code == 401


class TestHealthEndpoint:
    """Health endpoint always reports dashboard status plus dependency probes."""

    def test_health_shape(self) -> None:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["dashboard"] == "online"
        assert set(body.keys()) == {"dashboard", "api_server", "ai_server", "ollama"}
        assert body["api_server"] in ("online", "offline")


class TestProxyBehavior:
    """Proxy endpoints forward auth headers and surface upstream errors."""

    def test_list_automations_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_get(url: str, **kwargs: Any) -> FakeResponse:
            assert kwargs["headers"]["X-API-Key"] == API_KEY
            return FakeResponse(200, [{"id": 1, "name": "Demo"}])

        monkeypatch.setattr(requests, "get", fake_get)
        resp = client.get("/api/automations", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert resp.json() == [{"id": 1, "name": "Demo"}]

    def test_list_automations_upstream_error_propagates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_get(url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(500, {"detail": "db down"})

        monkeypatch.setattr(requests, "get", fake_get)
        resp = client.get("/api/automations", headers=AUTH_HEADERS)
        assert resp.status_code == 500

    def test_list_automations_unreachable_upstream_gives_502(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_get(url: str, **kwargs: Any) -> Any:
            raise requests.ConnectionError("refused")

        monkeypatch.setattr(requests, "get", fake_get)
        resp = client.get("/api/automations", headers=AUTH_HEADERS)
        assert resp.status_code == 502

    def test_login_forwards_credentials(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: Dict[str, Any] = {}

        def fake_post(url: str, **kwargs: Any) -> FakeResponse:
            captured.update(kwargs.get("json") or {})
            return FakeResponse(200, {"access_token": "t", "token_type": "bearer", "api_key": "k"})

        monkeypatch.setattr(requests, "post", fake_post)
        resp = client.post("/api/auth/login", json={"username": "u", "password": "p"})
        assert resp.status_code == 200
        assert resp.json()["api_key"] == "k"
        assert captured == {"username": "u", "password": "p"}

    def test_login_failure_propagates_401(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_post(url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(401, {"detail": "Incorrect username or password"})

        monkeypatch.setattr(requests, "post", fake_post)
        resp = client.post("/api/auth/login", json={"username": "u", "password": "wrong"})
        assert resp.status_code == 401


class TestImportValidation:
    """Import endpoint rejects malformed uploads before touching the API server."""

    def test_rejects_invalid_json_file(self) -> None:
        files = {"file": ("recorded_steps.json", io.BytesIO(b"not json{"), "application/json")}
        resp = client.post(
            "/api/automations/import",
            files=files,
            data={"name": "Broken"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 422

    def test_rejects_steps_missing_action(self) -> None:
        payload = json.dumps([{"url": "https://example.com"}]).encode()
        files = {"file": ("recorded_steps.json", io.BytesIO(payload), "application/json")}
        resp = client.post(
            "/api/automations/import",
            files=files,
            data={"name": "Broken"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 422

    def test_import_success_calls_api_server(self, monkeypatch: pytest.MonkeyPatch) -> None:
        captured: Dict[str, Any] = {}

        def fake_post(url: str, **kwargs: Any) -> FakeResponse:
            captured["url"] = url
            captured["json"] = kwargs.get("json")
            return FakeResponse(201, {"id": 42})

        monkeypatch.setattr(requests, "post", fake_post)
        payload = json.dumps(SAMPLE_STEPS).encode()
        files = {"file": ("recorded_steps.json", io.BytesIO(payload), "application/json")}
        resp = client.post(
            "/api/automations/import",
            files=files,
            data={"name": "QA Import", "description": "from pytest"},
            headers=AUTH_HEADERS,
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["automation_id"] == 42
        assert body["step_count"] == len(SAMPLE_STEPS)
        assert body["base_url"] == "https://example.com/"
        assert captured["json"]["name"] == "QA Import"
        assert captured["json"]["base_url"] == "https://example.com/"


class TestRunEndpoint:
    """Run endpoint orchestration (subprocess spawn stubbed out)."""

    def test_run_unknown_automation_propagates_404(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_get(url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(404, {"detail": "Automation not found"})

        monkeypatch.setattr(requests, "get", fake_get)
        resp = client.post("/api/automations/run", json={"automation_id": 99999}, headers=AUTH_HEADERS)
        assert resp.status_code == 404

    def test_run_empty_steps_gives_422(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def fake_get(url: str, **kwargs: Any) -> FakeResponse:
            return FakeResponse(200, {"automation_id": 5, "steps": [], "base_url": None})

        monkeypatch.setattr(requests, "get", fake_get)
        resp = client.post("/api/automations/run", json={"automation_id": 5}, headers=AUTH_HEADERS)
        assert resp.status_code == 422

    def test_run_success_spawns_playback(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any) -> None:
        spawned: Dict[str, Any] = {}

        def fake_get(url: str, **kwargs: Any) -> FakeResponse:
            if url.endswith("/steps"):
                return FakeResponse(200, {
                    "automation_id": 7,
                    "steps": SAMPLE_STEPS,
                    "base_url": "https://example.com/",
                })
            return FakeResponse(200, {"id": 7, "name": "QA Run", "base_url": "https://example.com/"})

        def fake_post(url: str, **kwargs: Any) -> FakeResponse:
            if url.endswith("/execute"):
                return FakeResponse(201, {"id": 1001})
            return FakeResponse(201, {})

        class FakeRun:
            run_id = 3
            process = type("P", (), {"pid": 4321})()

        def fake_spawn(**kwargs: Any) -> FakeRun:
            spawned.update(kwargs)
            return FakeRun()

        monkeypatch.setattr(requests, "get", fake_get)
        monkeypatch.setattr(requests, "post", fake_post)
        monkeypatch.setattr(dashboard_server.process_manager, "spawn", fake_spawn)
        # Redirect playback file writes into a temp client dir
        monkeypatch.setattr(dashboard_server, "CLIENT_DIR", tmp_path)
        (tmp_path / dashboard_server.PLAYBACK_SCRIPT).write_text("# stub", encoding="utf-8")

        resp = client.post("/api/automations/run", json={"automation_id": 7}, headers=AUTH_HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "started"
        assert body["execution_id"] == 1001
        assert body["step_count"] == len(SAMPLE_STEPS)

        # Playback files were generated for the client
        written_steps = json.loads((tmp_path / "recorded_steps.json").read_text(encoding="utf-8"))
        assert written_steps == SAMPLE_STEPS
        task_text = (tmp_path / "generated_task.txt").read_text(encoding="utf-8")
        assert "Open https://example.com/" in task_text

        # Subprocess spawn received execution context via env
        assert spawned["execution_id"] == 1001
        assert spawned["env"]["WEBAI_EXECUTION_ID"] == "1001"
        assert spawned["env"]["WEBAI_API_KEY"] == API_KEY


# ---------------------------------------------------------------------------
# Integration tests — require a live API server (auto-skip otherwise)
# ---------------------------------------------------------------------------

def _api_server_online() -> bool:
    """Return True when a real API server answers on WEBAI_API_URL."""
    try:
        return requests.get(f"{dashboard_server.API_URL}/health", timeout=2).status_code == 200
    except requests.RequestException:
        return False


pytestmark_integration = pytest.mark.skipif(
    not _api_server_online(),
    reason="API server offline — start it (port 8000) to run integration tests",
)


@pytestmark_integration
class TestLiveApiServer:
    """End-to-end proxy chain against a real API server (no browser launched)."""

    def test_live_health_reports_api_online(self) -> None:
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json()["api_server"] == "online"

    def test_live_list_automations(self) -> None:
        resp = client.get("/api/automations", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_live_list_executions(self) -> None:
        resp = client.get("/api/executions", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        executions = resp.json()
        assert isinstance(executions, list)
        if executions:
            assert "live_status" in executions[0]

    def test_live_run_unknown_automation_is_404(self) -> None:
        resp = client.post("/api/automations/run", json={"automation_id": 999999}, headers=AUTH_HEADERS)
        assert resp.status_code == 404
