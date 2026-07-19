"""
Test suite for the WebAI Playwright Client.

This module contains tests verifying the functionality of the Playwright 
integration, CDP accessibility tree extraction, and AI command execution.
"""

import pytest
from webai_playwright import playwright_actions as pw

class FakePage:
    def __init__(self):
        self.called = False
        self.expr = None
    async def evaluate(self, expr):
        self.called = True
        self.expr = expr
        return [{"tag":"input","role":"textbox","placeholder":"Search","text":""}]

@pytest.mark.asyncio
async def test_get_interactive_elements_calls_evaluate():
    page = FakePage()
    out = await pw.get_interactive_elements(page)
    assert page.called is True
    assert isinstance(out, list)
    assert out[0]["tag"] == "input"
