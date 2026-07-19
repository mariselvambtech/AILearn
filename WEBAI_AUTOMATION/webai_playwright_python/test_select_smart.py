"""
Test suite for the WebAI Playwright Client.

This module contains tests verifying the functionality of the Playwright 
integration, CDP accessibility tree extraction, and AI command execution.
"""

import pytest

from webai_playwright.playwright_actions import select_smart


class FakeLocator:
    def __init__(self, name, *, count=0, tag=None, calls=None, children=None):
        self._count = count
        self._tag = tag
        self._calls = calls if calls is not None else []
        self._children = children if children is not None else {}

    async def count(self):
        self._calls.append(("count", self._tag, self._count))
        return self._count

    @property
    def first(self):
        self._calls.append(("first", self._tag))
        return self

    async def click(self, timeout=None):
        self._calls.append(("click", self._tag, timeout))
        return True

    async def evaluate(self, script):
        self._calls.append(("evaluate", self._tag, script))
        if self._tag is None:
            raise RuntimeError("no tag")
        return self._tag

    async def select_option(self, label=None):
        self._calls.append(("select_option", self._tag, label))
        return True

    def get_by_role(self, role, **kwargs):
        key = ("role", role, kwargs.get("name"), kwargs.get("exact"))
        return self._children.get(key, FakeLocator("missing", count=0, tag=None, calls=self._calls))

    def get_by_text(self, text, **kwargs):
        key = ("text", text, kwargs.get("exact"))
        return self._children.get(key, FakeLocator("missing", count=0, tag=None, calls=self._calls))


class FakeKeyboard:
    def __init__(self, calls):
        self._calls = calls

    async def press(self, key):
        self._calls.append(("press", key))
        return True


class FakePage:
    def __init__(self, calls, *, trigger: FakeLocator, roles=None, labels=None, placeholders=None, texts=None, root_popup=None):
        self._calls = calls
        self._trigger = trigger
        self._roles = roles if roles is not None else {}
        self._labels = labels if labels is not None else {}
        self._placeholders = placeholders if placeholders is not None else {}
        self._texts = texts if texts is not None else {}
        self._root_popup = root_popup
        self.keyboard = FakeKeyboard(calls)

    def get_by_role(self, role, **kwargs):
        key = (role, kwargs.get("name"), kwargs.get("exact"))
        loc = self._roles.get(key)
        if loc is None:
            # listbox/menu/dialog are also queried without name
            key2 = (role, None, None)
            loc = self._roles.get(key2)
        return loc if loc is not None else FakeLocator("missing-role", count=0, tag=None, calls=self._calls)

    def get_by_label(self, label, **kwargs):
        key = (label, kwargs.get("exact"))
        return self._labels.get(key, FakeLocator("missing-label", count=0, tag=None, calls=self._calls))

    def get_by_placeholder(self, placeholder, **kwargs):
        key = (placeholder, kwargs.get("exact"))
        return self._placeholders.get(key, FakeLocator("missing-ph", count=0, tag=None, calls=self._calls))

    def get_by_text(self, text, **kwargs):
        key = (text, kwargs.get("exact"))
        return self._texts.get(key, FakeLocator("missing-text", count=0, tag=None, calls=self._calls))

    def locator(self, sel):
        self._calls.append(("locator", sel))
        return self._root_popup if self._root_popup is not None else FakeLocator("root", count=0, tag=None, calls=self._calls)

    async def wait_for_timeout(self, ms):
        self._calls.append(("wait_for_timeout", ms))
        return True


@pytest.mark.asyncio
async def test_select_smart_native_select_by_label():
    calls = []
    trigger = FakeLocator("trigger", count=1, tag="select", calls=calls)
    page = FakePage(
        calls,
        trigger=trigger,
        labels={("Country", False): trigger},
    )

    ok = await select_smart(page, option_text="India", label="Country", exact=False)
    assert ok is True
    assert ("select_option", "select", "India") in calls


@pytest.mark.asyncio
async def test_select_smart_custom_listbox_by_role():
    calls = []

    # Trigger is not <select>
    trigger = FakeLocator("trigger", count=1, tag="div", calls=calls)

    # Popup has option role
    popup_calls = calls
    option_loc = FakeLocator("opt", count=1, tag="opt", calls=popup_calls)
    popup = FakeLocator(
        "popup",
        count=1,
        tag="popup",
        calls=popup_calls,
        children={
            ("role", "option", "India", True): option_loc,
        },
    )

    listbox_loc = FakeLocator("listbox", count=1, tag="listbox", calls=calls)
    # listbox.first should behave like popup. For simplicity, map listbox.first calls to itself and use popup as returned by page.get_by_role("listbox")
    # We'll just return popup directly for listbox role queries:
    page = FakePage(
        calls,
        trigger=trigger,
        roles={
            ("combobox", "Country", False): trigger,
            ("listbox", None, None): popup,
            ("menu", None, None): FakeLocator("menu-missing", count=0, tag=None, calls=calls),
            ("dialog", None, None): FakeLocator("dlg-missing", count=0, tag=None, calls=calls),
        },
        texts={
            ("India", True): option_loc,
        },
        root_popup=popup,
    )

    ok = await select_smart(page, option_text="India", role="combobox", name="Country", exact=False)
    assert ok is True
    # should click trigger and then click option
    assert any(c[0] == "click" and c[1] == "div" for c in calls)
    assert any(c[0] == "click" and c[1] == "opt" for c in calls)
