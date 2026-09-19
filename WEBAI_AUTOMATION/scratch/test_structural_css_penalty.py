"""
TDVC Test Suite: Verifying Structural CSS Demotion (:nth-child / :nth-of-type)
in fallback_helpers.py to prevent false-positive clicks over semantic text matches.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest
from playwright.async_api import async_playwright

# Ensure webai_playwright_python is in sys.path
client_dir = Path(__file__).resolve().parent.parent / "webai_playwright_python"
if str(client_dir) not in sys.path:
    sys.path.insert(0, str(client_dir))

from webai_playwright.fallback_helpers import click_with_fallback, LOCATOR_PRIORITY


@pytest.mark.asyncio
async def test_structural_css_demoted_behind_semantic_text():
    """
    DOM Scenario:
    - Container with 3 children:
      1. Header
      2. <div class="buvtMR">Brand A</div> (matches div.buvtMR:nth-child(2))
      3. <div class="buvtMR">Blue</div> (matches text='Blue')
    Input Locators:
      - [{'type': 'css', 'value': 'div.buvtMR:nth-child(2)'}, {'type': 'text', 'value': 'Blue'}]

    Assert:
      click_with_fallback must execute semantic text='Blue' ahead of structural :nth-child(2).
      window.clickedTarget must equal 'Blue' (Element B), NOT 'Brand A' (Element A).
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Structural CSS Test</title></head>
    <body>
        <div id="parent">
            <div>Header</div>
            <div class="buvtMR" id="elemA" onclick="window.clickedTarget = 'Brand A'">Brand A</div>
            <div class="buvtMR" id="elemB" onclick="window.clickedTarget = 'Blue'">Blue</div>
        </div>
    </body>
    </html>
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html)

        locators = [
            {"type": "css", "value": "div.buvtMR:nth-child(2)"},
            {"type": "text", "value": "Blue"}
        ]

        success = await click_with_fallback(page, locators)
        assert success is True, "click_with_fallback returned False"

        clicked_target = await page.evaluate("() => window.clickedTarget")
        print(f"Clicked target: {clicked_target}")

        await browser.close()

        # Without the fix, :nth-child(2) (CSS priority 9) clicks 'Brand A'.
        # With the fix, :nth-child(2) is penalized to 11.5, so 'Blue' (Text priority 11) is clicked first.
        assert clicked_target == "Blue", f"Expected 'Blue' to be clicked, but got '{clicked_target}'"


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_structural_css_demoted_behind_semantic_text())
