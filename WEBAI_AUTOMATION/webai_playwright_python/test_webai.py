import base64
import json
import importlib

import pytest

import webai_playwright.config as config

# NOTE: webai_playwright/__init__.py exports `ai` function which can shadow submodule name.
# Import via importlib to unambiguously load the module.
ai_mod = importlib.import_module("webai_playwright.ai")
from webai_playwright import playwright_actions as pw


class FakeMouse:
    def __init__(self):
        self.moves = []
        self.clicks = []

    async def move(self, x, y):
        self.moves.append((x, y))

    async def click(self, x, y):
        self.clicks.append((x, y))


class FakeKeyboard:
    def __init__(self):
        self.typed = []
        self.pressed = []

    async def type(self, text):
        self.typed.append(text)

    async def press(self, key):
        self.pressed.append(key)


class FakePage:
    def __init__(self):
        self.mouse = FakeMouse()
        self.keyboard = FakeKeyboard()
        self.gotos = []
        self.evals = []
        self._screenshot_bytes = b"fakepngbytes"

    async def screenshot(self, **kwargs):
        return self._screenshot_bytes

    async def goto(self, url, **kwargs):
        self.gotos.append((url, kwargs))

    async def evaluate(self, expr, *args):
        self.evals.append((expr, args))
        # Used by get_snapshot() to read visual viewport and pixel ratio
        if "visualViewport" in expr or "pixelRatio" in expr:
            return {"viewportWidth": 800, "viewportHeight": 600, "pixelRatio": 2}
        return None


@pytest.mark.asyncio
async def test_get_snapshot_base64_and_dom(monkeypatch):
    async def fake_dom_snapshot(page):
        return {"ok": True, "nodes": []}

    async def fake_layout_metrics(page):
        return {"contentSize": {"width": 800, "height": 600}}

    monkeypatch.setattr(pw.cdp, "get_dom_snapshot", fake_dom_snapshot)
    monkeypatch.setattr(pw.cdp, "get_layout_metrics", fake_layout_metrics)

    page = FakePage()
    snap = await pw.get_snapshot(page)

    assert json.loads(snap["dom"]) == {"ok": True, "nodes": []}
    assert base64.b64decode(snap["screenshot"].encode("ascii")) == page._screenshot_bytes
    assert snap["viewportWidth"] == 800
    assert snap["viewportHeight"] == 600
    assert snap["pixelRatio"] == 2
    assert "layoutMetrics" in snap


@pytest.mark.asyncio
async def test_execute_command_dispatch(monkeypatch):
    page = FakePage()

    async def fake_get_current_url(page):
        return "https://local.test/"

    monkeypatch.setattr(ai_mod.cdp, "get_current_url", fake_get_current_url)

    res = await ai_mod._execute_command(page, {"name": "getCurrentUrl", "arguments": {}})
    assert res == "https://local.test/"

    with pytest.raises(ai_mod.ClientError):
        await ai_mod._execute_command(page, {"name": "nope", "arguments": {}})


@pytest.mark.asyncio
async def test_send_command_response_formats_json(monkeypatch):
    sent = []

    async def fake_send(msg):
        sent.append(msg)

    monkeypatch.setattr(ai_mod, "send_message", fake_send)

    await ai_mod._send_command_response(3, "task123", {"a": 1})
    assert sent[-1]["type"] == "command-response"
    assert sent[-1]["index"] == 3
    assert sent[-1]["taskId"] == "task123"
    assert sent[-1]["result"] == json.dumps({"a": 1})

    await ai_mod._send_command_response(4, "task123", None)
    assert sent[-1]["result"] == "null"


@pytest.mark.asyncio
async def test_ai_requires_token(monkeypatch):
    # Force TOKEN to be empty
    monkeypatch.setattr(config, "TOKEN", "")
    monkeypatch.setattr(ai_mod, "TOKEN", "")

    with pytest.raises(ai_mod.ClientError) as e:
        await ai_mod.ai("hello", page=FakePage())

    assert "TOKEN must be defined" in str(e.value)


@pytest.mark.asyncio
async def test_ai_happy_path_with_mock_ws(monkeypatch):
    # Mock TOKEN so ai() proceeds
    monkeypatch.setattr(config, "TOKEN", "dummy")
    monkeypatch.setattr(ai_mod, "TOKEN", "dummy")

    async def fake_snapshot(page):
        return {
            "dom": "{}",
            "screenshot": base64.b64encode(b"x").decode("ascii"),
            "pixelRatio": 1,
            "viewportWidth": 800,
            "viewportHeight": 600,
        }

    monkeypatch.setattr(ai_mod.pw, "get_snapshot", fake_snapshot)

    sent = []

    async def fake_send_message(msg):
        sent.append(msg)

    monkeypatch.setattr(ai_mod, "send_message", fake_send_message)

    async def fake_listen(task_id, handler):
        cmd = {"type": "command-request", "taskId": task_id, "index": 0, "name": "getCurrentUrl", "arguments": {}}

        async def fake_get_current_url(page):
            return "https://example.local/"

        monkeypatch.setattr(ai_mod.cdp, "get_current_url", fake_get_current_url)

        stop = await handler(cmd)
        assert stop is False

        complete = {"type": "task-complete", "taskId": task_id, "value": "ok"}
        stop = await handler(complete)
        assert stop is True

    monkeypatch.setattr(ai_mod, "listen", fake_listen)

    out = await ai_mod.ai("test task", page=FakePage(), options={"type": "action"})

    assert out["type"] == "task-complete"
    assert out["value"] == "ok"

    assert any(m.get("type") == "task-start" for m in sent)
    assert any(m.get("type") == "command-response" for m in sent)


def test_websocket_url_custom_env(monkeypatch):
    monkeypatch.setenv("TOKEN", "abc")
    monkeypatch.setenv("WEBSOCKET_PROTOCOL", "ws")
    monkeypatch.setenv("WEBSOCKET_HOST", "localhost:9999")

    import importlib
    import webai_playwright.config as cfg

    importlib.reload(cfg)
    url = cfg.websocket_url()

    assert url.startswith("ws://localhost:9999/")
    assert "key=abc" in url


class FakeCDPSession:
    def __init__(self):
        self.calls = []
    async def send(self, method, params=None):
        self.calls.append((method, params))
        if method == "Browser.getWindowForTarget":
            return {"windowId": 123}
        return {}


class FakeContext:
    def __init__(self, cdp_session):
        self._cdp_session = cdp_session
    async def new_cdp_session(self, page):
        return self._cdp_session


class FakePageForWindow:
    def __init__(self):
        self._cdp = FakeCDPSession()
        self.context = FakeContext(self._cdp)


@pytest.mark.asyncio
async def test_set_window_state_maximized():
    page = FakePageForWindow()
    ok = await pw.set_window_state(page, "maximized")
    assert ok is True
    # verify CDP calls
    assert page._cdp.calls[0][0] == "Browser.getWindowForTarget"
    assert page._cdp.calls[1][0] == "Browser.setWindowBounds"
    assert page._cdp.calls[1][1]["bounds"]["windowState"] == "maximized"


@pytest.mark.asyncio
async def test_set_window_state_invalid():
    page = FakePageForWindow()
    with pytest.raises(ValueError):
        await pw.set_window_state(page, "banana")
