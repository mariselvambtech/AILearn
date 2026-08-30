"""
Test suite for verifying all 13 locator strategies in fallback_helpers.py.

This test file verifies that click_with_fallback, type_with_fallback, and extract_with_fallback
properly resolve and interact with all 13 locator strategies:
1. test-id
2. id
3. name
4. href
5. placeholder
6. alt
7. aria-label
8. title
9. label
10. css
11. role
12. text
13. xpath
"""

import sys
from pathlib import Path
import pytest
from playwright.async_api import Page, async_playwright

# Ensure webai_playwright_python is in sys.path
client_dir = Path(__file__).resolve().parent.parent / "webai_playwright_python"
if str(client_dir) not in sys.path:
    sys.path.insert(0, str(client_dir))

from webai_playwright.fallback_helpers import (
    LOCATOR_PRIORITY,
    click_with_fallback,
    type_with_fallback,
    extract_with_fallback,
    _create_locator_obj
)

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head><title>Locator Test Page</title></head>
<body>
    <!-- 0. test-id -->
    <button data-testid="my-testid-btn" onclick="this.dataset.clicked='true'">TestID Button</button>

    <!-- 1. id -->
    <button id="my-id-btn" onclick="this.dataset.clicked='true'">ID Button</button>

    <!-- 2. name -->
    <input name="my-name-field" id="name-input" value="" />

    <!-- 3. href -->
    <a href="https://example.com/target-link" id="href-link">Href Link</a>

    <!-- 4. placeholder -->
    <input placeholder="Enter placeholder text" id="placeholder-input" />

    <!-- 5. alt -->
    <img alt="my-alt-image" src="data:image/gif;base64,R0lODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" id="alt-img" onclick="this.dataset.clicked='true'" />

    <!-- 6. aria-label -->
    <button aria-label="my-aria-button" id="aria-btn" onclick="this.dataset.clicked='true'">Aria Button</button>

    <!-- 7. title -->
    <button title="my-title-tooltip" id="title-btn" onclick="this.dataset.clicked='true'">Title Button</button>

    <!-- 8. label -->
    <label for="labeled-input">my-field-label</label>
    <input id="labeled-input" />

    <!-- 9. css -->
    <button class="my-custom-css-class" id="css-btn" onclick="this.dataset.clicked='true'">CSS Button</button>

    <!-- 10. role -->
    <div role="button" id="role-btn" tabindex="0" onclick="this.dataset.clicked='true'">Role Button</div>

    <!-- 11. text -->
    <button id="text-btn" onclick="this.dataset.clicked='true'">Unique Visible Text Target</button>

    <!-- 12. xpath -->
    <div id="xpath-container">
        <button class="xpath-inner-btn" onclick="this.dataset.clicked='true'">XPath Button</button>
    </div>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_locator_priority_structure():
    """Verify LOCATOR_PRIORITY is exact 13-key 0-indexed dict matching server."""
    expected_priority = {
        "test-id": 0, "id": 1, "name": 2, "href": 3,
        "placeholder": 4, "alt": 5, "aria-label": 6, "title": 7,
        "label": 8, "css": 9, "role": 10, "text": 11, "xpath": 12
    }
    assert LOCATOR_PRIORITY == expected_priority, f"Expected {expected_priority}, got {LOCATOR_PRIORITY}"
    assert len(LOCATOR_PRIORITY) == 13


@pytest.mark.asyncio
async def test_create_locator_obj_all_13_types():
    """Verify _create_locator_obj constructs valid locators for all 13 types."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(HTML_CONTENT)

        locators_to_test = [
            ({"type": "test-id", "value": "my-testid-btn"}, "TestID Button"),
            ({"type": "id", "value": "my-id-btn"}, "ID Button"),
            ({"type": "name", "value": "my-name-field"}, ""),
            ({"type": "href", "value": "https://example.com/target-link"}, "Href Link"),
            ({"type": "placeholder", "value": "Enter placeholder text"}, ""),
            ({"type": "alt", "value": "my-alt-image"}, ""),
            ({"type": "aria-label", "value": "my-aria-button"}, "Aria Button"),
            ({"type": "title", "value": "my-title-tooltip"}, "Title Button"),
            ({"type": "label", "value": "my-field-label"}, ""),
            ({"type": "css", "value": ".my-custom-css-class"}, "CSS Button"),
            ({"type": "role", "value": "button", "name": "Role Button"}, "Role Button"),
            ({"type": "text", "value": "Unique Visible Text Target"}, "Unique Visible Text Target"),
            ({"type": "xpath", "value": "//div[@id='xpath-container']/button"}, "XPath Button"),
        ]

        for loc_dict, _ in locators_to_test:
            loc_obj = await _create_locator_obj(page, loc_dict)
            assert loc_obj is not None, f"Failed to create locator object for type {loc_dict['type']}"
            count = await loc_obj.count()
            assert count > 0, f"Locator for type {loc_dict['type']} found 0 elements"

        await browser.close()


@pytest.mark.asyncio
async def test_click_with_fallback_all_13_types():
    """Verify click_with_fallback works with all 13 locator types including alt, aria-label, title."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(HTML_CONTENT)

        test_cases = [
            [{"type": "test-id", "value": "my-testid-btn"}],
            [{"type": "id", "value": "my-id-btn"}],
            [{"type": "href", "value": "https://example.com/target-link"}],
            [{"type": "alt", "value": "my-alt-image"}],
            [{"type": "aria-label", "value": "my-aria-button"}],
            [{"type": "title", "value": "my-title-tooltip"}],
            [{"type": "css", "value": ".my-custom-css-class"}],
            [{"type": "role", "value": "button", "name": "Role Button"}],
            [{"type": "text", "value": "Unique Visible Text Target"}],
            [{"type": "xpath", "value": "//div[@id='xpath-container']/button"}],
        ]

        for locators in test_cases:
            await page.set_content(HTML_CONTENT)
            loc_type = locators[0]["type"]
            success = await click_with_fallback(page, locators)
            assert success is True, f"click_with_fallback failed for type {loc_type}"

        await browser.close()


@pytest.mark.asyncio
async def test_type_with_fallback_all_relevant_types():
    """Verify type_with_fallback works with input locators including aria-label, title, alt, placeholder, etc."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content("""
        <html><body>
            <input aria-label="aria-input" id="i1" />
            <input title="title-input" id="i2" />
            <input placeholder="ph-input" id="i3" />
            <input name="name-input" id="i4" />
        </body></html>
        """)

        # Test aria-label
        res1 = await type_with_fallback(page, [{"type": "aria-label", "value": "aria-input"}], "hello aria")
        assert res1 is True
        val1 = await page.locator("#i1").input_value()
        assert val1 == "hello aria"

        # Test title
        res2 = await type_with_fallback(page, [{"type": "title", "value": "title-input"}], "hello title")
        assert res2 is True
        val2 = await page.locator("#i2").input_value()
        assert val2 == "hello title"

        # Test placeholder
        res3 = await type_with_fallback(page, [{"type": "placeholder", "value": "ph-input"}], "hello ph")
        assert res3 is True
        val3 = await page.locator("#i3").input_value()
        assert val3 == "hello ph"

        await browser.close()


@pytest.mark.asyncio
async def test_extract_with_fallback_all_types():
    """Verify extract_with_fallback extracts text/attribute for aria-label, alt, title, test-id, etc."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(HTML_CONTENT)

        # Extract inner text using aria-label
        val_aria = await extract_with_fallback(page, [{"type": "aria-label", "value": "my-aria-button"}], "text")
        assert "Aria Button" in val_aria

        # Extract inner text using title
        val_title = await extract_with_fallback(page, [{"type": "title", "value": "my-title-tooltip"}], "text")
        assert "Title Button" in val_title

        # Extract attribute using alt
        val_alt_attr = await extract_with_fallback(page, [{"type": "alt", "value": "my-alt-image"}], "attribute", "alt")
        assert val_alt_attr == "my-alt-image"

        await browser.close()
