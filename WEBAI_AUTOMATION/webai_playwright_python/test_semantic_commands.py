
import importlib
import pytest

ai_mod = importlib.import_module("webai_playwright.ai")

class DummyPage:
    pass

@pytest.mark.asyncio
async def test_execute_command_semantic_dispatch(monkeypatch):
    page = DummyPage()

    called = {}

    async def fake_click_by_role(page, role, name, exact):
        called["clickByRole"] = (role, name, exact)
        return True

    async def fake_type_by_label(page, label, text, exact):
        called["typeByLabel"] = (label, text, exact)
        return True

    monkeypatch.setattr(ai_mod.pw, "click_by_role", fake_click_by_role)
    monkeypatch.setattr(ai_mod.pw, "type_by_label", fake_type_by_label)

    res = await ai_mod._execute_command(page, {"name":"clickByRole", "arguments":{"role":"button","name":"Save","exact":True}})
    assert res is True
    assert called["clickByRole"] == ("button","Save",True)

    res = await ai_mod._execute_command(page, {"name":"typeByLabel", "arguments":{"label":"Email","text":"a@b.com","exact":False}})
    assert res is True
    assert called["typeByLabel"] == ("Email","a@b.com",False)
