"""
Test suite for Phase 12 - Shield 2: DOM Mutation Verification.

Verifies that clicks passing Shield 1 (Semantic Filtering) are only recorded
if they trigger a measurable state change (DOM mutation or URL change) within 800ms.
Unresponsive/dead buttons are discarded by Shield 2.
"""

import sys
import asyncio
from pathlib import Path
import pytest
from playwright.async_api import async_playwright

# Ensure webai_playwright_python is in sys.path
client_dir = Path(__file__).resolve().parent.parent / "webai_playwright_python"
if str(client_dir) not in sys.path:
    sys.path.insert(0, str(client_dir))

from webai_playwright.plugins.hitl_plugin import HITLPlugin

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head><title>Mutation Observer Test</title></head>
<body>
    <h2>Shield 2 Test Page</h2>

    <!-- Button A: Mutates DOM on click -->
    <button id="btn-a" onclick="const d = document.createElement('div'); d.innerText='New Content'; document.body.appendChild(d);">
        Button A (Mutates DOM)
    </button>

    <!-- Button B: Dead/Unresponsive (passes Shield 1, but triggers NO mutation or URL change) -->
    <button id="btn-b">
        Button B (Dead Button)
    </button>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_shield_2_dom_mutation_verification():
    """Verify Shield 2 captures Button A (DOM mutation) and discards Button B (unresponsive)."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(HTML_CONTENT)

        hitl = HITLPlugin()

        # Start observer mode in background task
        observer_task = asyncio.create_task(hitl._inject_and_await_observer_mode(page, timeout_sec=5.0))

        # Wait for observer panel to inject
        await page.wait_for_selector("#webai-hitl-observer-panel", timeout=2000)

        # Click Button A (Mutating DOM)
        await page.locator("#btn-a").click()

        # Click Button B (Dead button)
        await page.locator("#btn-b").click()

        # Wait 1.2 seconds for the 800ms mutation verification timeout to complete
        await asyncio.sleep(1.2)

        # Inspect window.__webai_telemetry
        telemetry = await page.evaluate("() => window.__webai_telemetry || []")

        print(f"\n[TEST LOG] Captured Telemetry Events ({len(telemetry)}):")
        for idx, event in enumerate(telemetry):
            print(f"  {idx+1}. Tag: {event.get('tag')}, CSS: {event.get('css')}, Text: '{event.get('text')}'")

        # Assert exactly 1 telemetry event (Button A captured; Button B discarded by Shield 2)
        assert len(telemetry) == 1, f"Expected 1 verified telemetry event, got {len(telemetry)}"
        assert telemetry[0]["css"] == "button#btn-a"
        assert "Button A" in telemetry[0]["text"]

        # Click Resume AI to resolve cleanly
        await page.locator("#webai-hitl-resume-btn").click()
        result = await observer_task
        assert result.get("status") == "resolved"

        await browser.close()
