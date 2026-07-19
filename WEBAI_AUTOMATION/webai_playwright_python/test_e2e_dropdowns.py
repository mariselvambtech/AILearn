
import os
import pathlib
import pytest
from playwright.async_api import async_playwright

from webai_playwright.playwright_actions import select_smart


pytestmark = pytest.mark.asyncio

RUN_E2E = os.environ.get("RUN_E2E", "0") == "1"


@pytest.mark.skipif(not RUN_E2E, reason="Set RUN_E2E=1 to run Playwright E2E tests.")
async def test_e2e_native_and_custom_dropdowns():
    here = pathlib.Path(__file__).parent
    page_path = (here / "tests_e2e_page.html").resolve().as_uri()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(page_path)

        # Native <select> by label
        ok = await select_smart(page, option_text="India", label="Country")
        assert ok is True
        native_value = await page.locator("#native").input_value()
        assert native_value == "India"

        # Custom listbox by role+name (combobox name comes from aria-labelledby "City")
        ok = await select_smart(page, option_text="Chennai", role="combobox", name="City")
        assert ok is True
        assert await page.locator("#combo").inner_text() == "Chennai"

        await browser.close()
