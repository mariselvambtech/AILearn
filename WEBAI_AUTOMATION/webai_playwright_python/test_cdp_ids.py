"""
Test suite for the WebAI Playwright Client.

This module contains tests verifying the functionality of the Playwright 
integration, CDP accessibility tree extraction, and AI command execution.
"""

import pytest
import importlib

cdp = importlib.import_module("webai_playwright.cdp")

class FakeCDP:
    def __init__(self):
        self.calls = []
        self._object_id = "obj-1"

    async def send(self, method, params=None):
        params = params or {}
        self.calls.append((method, params))
        if method == "DOM.resolveNode":
            # backendNodeId -> objectId
            return {"object": {"objectId": self._object_id}}
        if method == "DOM.getContentQuads":
            # Return a simple quad box: 0,0 10,0 10,10 0,10
            return {"quads": [[0,0, 10,0, 10,10, 0,10]]}
        if method == "Runtime.callFunctionOn":
            return {"result": {"value": True}}
        return {}

@pytest.mark.asyncio
async def test_run_function_on_object_id_no_resolve(monkeypatch):
    fake = FakeCDP()
    async def fake_get_cdp(page):
        return fake
    monkeypatch.setattr(cdp, "get_cdp", fake_get_cdp)

    await cdp.run_function_on(page=None, function_declaration="function(){return 1}", element_id="-1.2.3")
    methods = [m for m,_ in fake.calls]
    assert "DOM.resolveNode" not in methods
    assert ("Runtime.callFunctionOn" in methods)

@pytest.mark.asyncio
async def test_run_function_on_backend_node_id_resolves(monkeypatch):
    fake = FakeCDP()
    async def fake_get_cdp(page):
        return fake
    monkeypatch.setattr(cdp, "get_cdp", fake_get_cdp)

    await cdp.run_function_on(page=None, function_declaration="function(){return 1}", element_id="123")
    methods = [m for m,_ in fake.calls]
    assert "DOM.resolveNode" in methods
    # ensure resolve called with backendNodeId int
    resolve_call = next(p for (m,p) in fake.calls if m=="DOM.resolveNode")
    assert resolve_call["backendNodeId"] == 123

@pytest.mark.asyncio
async def test_clear_element_object_id(monkeypatch):
    fake = FakeCDP()
    async def fake_get_cdp(page):
        return fake
    monkeypatch.setattr(cdp, "get_cdp", fake_get_cdp)
    await cdp.clear_element(page=None, element_id="-9.9.9")
    methods = [m for m,_ in fake.calls]
    assert "Runtime.callFunctionOn" in methods

@pytest.mark.asyncio
async def test_click_element_object_id_uses_content_quads(monkeypatch):
    fake = FakeCDP()
    async def fake_get_cdp(page):
        return fake
    monkeypatch.setattr(cp:=cdp, "get_cdp", fake_get_cdp)

    ok = await cdp.click_element(page=None, element_id="-9.9.9")
    assert ok is True
    assert any(m=="DOM.getContentQuads" for m,_ in fake.calls)
