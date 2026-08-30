"""
Test suite for Phase 12 - JS Telemetry Injector with Smart Semantic Filtering.

Verifies that the capture-phase click listener correctly captures interactive elements,
role-based elements, and text-bearing containers while filtering out dead/empty spaces.
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
<head><title>Telemetry Test Page</title></head>
<body>
    <h2>Telemetry Test</h2>

    <!-- 1. Interactive Tag (Mutating) -->
    <button id="btn1" onclick="this.dataset.clicked='true'">Add to Cart</button>

    <!-- 2. Interactive Role (Mutating) -->
    <div role="button" id="btn2" onclick="this.dataset.clicked='true'">Custom Role Button</div>

    <!-- 3. Non-interactive Tag WITH Text (Mutating) -->
    <div id="div1" onclick="this.dataset.clicked='true'">Some readable text in container</div>

    <!-- 4. Dead/Empty Space -->
    <div id="dead-box" style="width: 100px; height: 100px; border: 1px solid red;"></div>

    <!-- 5. Blank Body Area -->
</body>
</html>
"""


@pytest.mark.asyncio
async def test_smart_semantic_filtering_telemetry():
    """Verify JS telemetry listener captures valid clicks and filters dead spaces."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(HTML_CONTENT)

        hitl = HITLPlugin()

        # Start observer mode in background task
        observer_task = asyncio.create_task(hitl._inject_and_await_observer_mode(page, timeout_sec=5.0))

        # Give observer mode a moment to inject panel and JS listener
        await page.wait_for_selector("#webai-hitl-observer-panel", timeout=2000)

        # Perform 5 test clicks
        # Click 1: Button (Interactive tag)
        await page.locator("#btn1").click()

        # Click 2: Role button (Interactive role)
        await page.locator("#btn2").click()

        # Click 3: Text container (Has text)
        await page.locator("#div1").click()

        # Click 4: Dead box (No tag, no role, no text -> SHOULD BE DISCARDED)
        await page.locator("#dead-box").click()

        # Click 5: Blank body click (No tag, no role, no text -> SHOULD BE DISCARDED)
        await page.mouse.click(10, 10)

        # Wait 1.2s for 800ms Shield 2 DOM mutation verification timeout
        await asyncio.sleep(1.2)

        # Inspect window.__webai_telemetry
        telemetry = await page.evaluate("() => window.__webai_telemetry || []")

        print(f"\n[TEST LOG] Captured Telemetry Events ({len(telemetry)}):")
        for idx, event in enumerate(telemetry):
            print(f"  {idx+1}. Tag: {event.get('tag')}, CSS: {event.get('css')}, Text: '{event.get('text')}'")

        # Assert length is exactly 3 (btn1, btn2, div1 captured; dead-box & body discarded)
        assert len(telemetry) == 3, f"Expected 3 valid telemetry events, got {len(telemetry)}"

        # Assert captured elements
        tags = [e["tag"] for e in telemetry]
        css_list = [e["css"] for e in telemetry]

        assert "button" in tags
        assert any("btn1" in c for c in css_list)
        assert any("btn2" in c for c in css_list)
        assert any("div1" in c for c in css_list)

        # Click Resume AI to finish observer mode cleanly
        await page.locator("#webai-hitl-resume-btn").click()
        result = await observer_task
        assert result.get("status") == "resolved"

        # Verify telemetry was attached to resolution payload
        assert "telemetry" in result.get("click", {}) or "telemetry" in result
        captured_in_result = result.get("click", {}).get("telemetry") or result.get("telemetry")
        assert len(captured_in_result) == 3

        await browser.close()
