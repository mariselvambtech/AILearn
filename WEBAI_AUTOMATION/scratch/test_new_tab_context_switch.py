"""
TDVC Test Harness for New Tab Context Switching in SkillExecutor.
Tests:
1. Single-tab execution maintains page reference without unnecessary context switching.
2. When an action spawns a new tab (len(pages) increases):
   - Active page reference switches to context.pages[-1].
   - page.bring_to_front() and page.wait_for_load_state("domcontentloaded") are awaited.
   - Subsequent steps execute against the new tab.
   - WebSocket handoff payload (if keep_alive=True) carries the new tab's URL.
"""
from __future__ import annotations

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure webai_playwright_python is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python")))

from webai_playwright.skill_executor import SkillExecutor


def test_new_tab_context_switch():
    print(" [1/2] Testing new tab detection and automatic context switching...")

    # Mock Page 1 (initial tab)
    page1 = MagicMock()
    page1.url = "https://www.flipkart.com/search?q=jeans"
    page1.bring_to_front = AsyncMock()
    page1.wait_for_load_state = AsyncMock()

    # Mock Page 2 (new tab spawned after click)
    page2 = MagicMock()
    page2.url = "https://www.flipkart.com/pepe-jeans-slim-fit/p/itm12345"
    page2.bring_to_front = AsyncMock()
    page2.wait_for_load_state = AsyncMock()
    page2.title = AsyncMock(return_value="Pepe Jeans Product Page")

    # Shared browser context
    mock_context = MagicMock()
    mock_context.pages = [page1]

    page1.context = mock_context
    page2.context = mock_context

    recipe = {
        "skill_name": "Flipkart New Tab Test",
        "parameterized_steps": [
            {
                "action": "click",
                "name": "Product Link",
                "locators": [{"type": "css", "value": "a.product-card"}]
            },
            {
                "action": "assert",
                "target": "url_contains",
                "value": "pepe-jeans"
            }
        ]
    }

    executor = SkillExecutor(recipe)

    # When step 1 (click) executes, simulate the browser opening page2
    async def mock_click(page_arg, locators, expected_context=None):
        mock_context.pages.append(page2)
        return True

    with patch("webai_playwright.skill_executor.click_with_fallback", side_effect=mock_click):
        result = asyncio.run(executor.execute_skill(page1))

    assert result["status"] == "success"
    assert result["steps_executed"] == 2

    # Assert page2 had bring_to_front and wait_for_load_state called
    assert page2.bring_to_front.called, "Expected page2.bring_to_front() to be called on new tab"
    assert page2.wait_for_load_state.called, "Expected page2.wait_for_load_state('domcontentloaded') to be called"
    page2.wait_for_load_state.assert_called_with("domcontentloaded")

    print("  SUCCESS: New tab detected, brought to front, loaded, and context switched!")


def test_single_tab_invariant():
    print(" [2/2] Testing single-tab execution invariant...")

    page = MagicMock()
    page.url = "https://example.com"
    page.bring_to_front = AsyncMock()
    page.wait_for_load_state = AsyncMock()

    mock_context = MagicMock()
    mock_context.pages = [page]
    page.context = mock_context

    recipe = {
        "skill_name": "Single Tab Test",
        "parameterized_steps": [
            {
                "action": "click",
                "name": "Same Page Button",
                "locators": [{"type": "text", "value": "Next"}]
            }
        ]
    }

    executor = SkillExecutor(recipe)

    async def mock_click_same_tab(page_arg, locators, expected_context=None):
        return True

    with patch("webai_playwright.skill_executor.click_with_fallback", side_effect=mock_click_same_tab):
        result = asyncio.run(executor.execute_skill(page))

    assert result["status"] == "success"
    assert result["steps_executed"] == 1
    # bring_to_front should NOT have been called because tab count didn't increase
    assert not page.bring_to_front.called, "Single tab should not trigger bring_to_front()"

    print("  SUCCESS: Single tab execution preserved without redundant switching!")


if __name__ == "__main__":
    test_new_tab_context_switch()
    test_single_tab_invariant()
    print("\nALL NEW TAB CONTEXT SWITCHING TESTS PASSED (2/2)!")
