from __future__ import annotations

import base64
import json
import asyncio
from typing import Any, Dict, Union, List, Optional

from playwright.async_api import Page, Frame, ElementHandle, Locator

from . import cdp

# Import fallback helper functions for automatic locator fallback
from .fallback_helpers import type_with_fallback, click_with_fallback, validate_page

ScrollType = str


DEFAULT_NAV_TIMEOUT_MS = 30000
DEFAULT_ACTION_TIMEOUT_MS = 15000


async def _post_action_wait(page: Page, settle_ms: int = 250) -> None:
    """Small, safe waits after actions to let navigation / DOM updates settle."""
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception:
        pass

    # Some pages never reach networkidle; treat as best-effort
    try:
        await page.wait_for_load_state("networkidle", timeout=3000)
    except Exception:
        pass

    await asyncio.sleep(max(0, settle_ms) / 1000.0)


async def hover_cdp_element(page: Page, element_id: str) -> bool:
    coords = await cdp._get_content_quads(page, int(element_id))
    await page.mouse.move(coords["centerX"], coords["centerY"])
    return True


async def click_cdp_element(page: Page, element_id: str) -> bool:
    coords = await cdp._get_content_quads(page, int(element_id))
    await page.mouse.click(coords["centerX"], coords["centerY"])
    return True


async def click_and_input_cdp_element(page: Page, element_id: str, value: str) -> bool:
    coords = await cdp._get_content_quads(page, int(element_id))
    await page.mouse.click(coords["centerX"], coords["centerY"])
    await page.keyboard.type(value)
    return True


async def scroll_cdp_element(page: Page, element_id: str, target: ScrollType) -> Any:
    return await cdp.scroll_element(page, int(element_id), target)


async def hover_location(page: Page, x: float, y: float) -> bool:
    await page.mouse.move(x, y)
    return True


async def click_location(page: Page, x: float, y: float) -> bool:
    await page.mouse.click(x, y)
    return True


async def click_and_input_location(page: Page, x: float, y: float, value: str) -> bool:
    await page.mouse.click(x, y)
    await page.keyboard.type(value)
    return True


async def hover(page: Page, selector: str) -> bool:
    await page.locator(selector).hover()
    return True


async def click(page: Page, selector: str) -> bool:
    await page.locator(selector).click()
    return True


async def input_text(page: Page, selector: str, value: str) -> bool:
    await page.locator(selector).fill(value)
    return True


async def keypress_enter(page: Page) -> bool:
    await page.keyboard.press("Enter")
    return True


async def keypress_select_all(page: Page) -> bool:
    await page.keyboard.press("Control+A")
    return True


async def keypress_backspace(page: Page) -> bool:
    await page.keyboard.press("Backspace")
    return True


async def navigate(page: Page, url: str) -> bool:
    url = (url or "").strip()

    # If the AI planner sends placeholders like "url", don't crash.
    if not url or url.lower() in {"url", "http://", "https://"}:
        print(f"[WARN] Skipping navigation: invalid url='{url}'")
        return False

    # If user provided domain without scheme, normalize
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=DEFAULT_NAV_TIMEOUT_MS)
        # Best-effort stabilization: networkidle may timeout on pages with long polling
        try:
            await page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        await asyncio.sleep(0.4)
        return True
    except Exception as e:
        print(f"[WARN] Navigation failed for url='{url}': {e}")
        return False


async def scroll_page_script(page: Page, target: ScrollType) -> Any:
    if target == "down":
        return await page.evaluate("window.scrollBy(0, window.innerHeight)")
    if target == "up":
        return await page.evaluate("window.scrollBy(0, -window.innerHeight)")
    if target == "top":
        return await page.evaluate("window.scrollTo(0, 0)")
    if target == "bottom":
        return await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    return None


async def get_viewport_metadata(page: Page) -> Dict[str, Any]:
    return await page.evaluate(
        """() => {
        return {
            devicePixelRatio: window.devicePixelRatio,
            innerWidth: window.innerWidth,
            innerHeight: window.innerHeight,
            outerWidth: window.outerWidth,
            outerHeight: window.outerHeight,
        };
    }"""
    )


async def get_dom_snapshot(page: Page) -> Dict[str, Any]:
    dom_snapshot = await cdp.get_dom_snapshot(page)
    return {"dom": json.dumps(dom_snapshot)}


async def get_page_screenshot(page: Page) -> Dict[str, Any]:
    data = await page.screenshot(type="png", full_page=True)
    return {"imageBase64": base64.b64encode(data).decode("utf-8")}


async def get_page_title(page: Page) -> str:
    return await page.title()


async def get_page_url(page: Page) -> str:
    return page.url


async def _target_locator(page: Page, target: Dict[str, Any]) -> Locator:
    by = (target.get("by") or "").strip().lower()
    exact = bool(target.get("exact", False))

    if by == "label":
        return page.get_by_label(target.get("label", ""), exact=exact)

    if by == "placeholder":
        return page.get_by_placeholder(target.get("placeholder", ""), exact=exact)

    if by == "text":
        return page.get_by_text(target.get("text", ""), exact=exact)

    if by == "role":
        role = target.get("role", "")
        name = target.get("name", "")
        return page.get_by_role(role, name=name, exact=exact)

    # fallback
    return page.get_by_text(target.get("text", ""), exact=exact)


async def cdp_element_to_playwright_handle(page: Page, element: Dict[str, Any]) -> Optional[ElementHandle]:
    # Converts a CDP node into a playwright handle using backendNodeId.
    try:
        backend_node_id = element.get("backendNodeId")
        if backend_node_id is None:
            return None
        resolved = await cdp.resolve_node(page, backend_node_id=int(backend_node_id))
        object_id = resolved.get("object", {}).get("objectId")
        if not object_id:
            return None
        handle = await page.context.new_cdp_session(page).send("Runtime.callFunctionOn", {
            "functionDeclaration": "function() { return this; }",
            "objectId": object_id,
            "returnByValue": False,
        })
        # If the above fails in some environments, you may already have alternate helpers in cdp.py.
        return None
    except Exception:
        return None


async def get_element_at_location(page: Page, x: float, y: float) -> Optional[Dict[str, Any]]:
    return await cdp.get_element_at_point(page, x, y)


async def set_window_state(page: Page, state: str) -> bool:
    # state: normal|minimized|maximized|fullscreen
    await cdp.set_window_state(page, state)
    return True


async def get_interactive_elements(page: Page) -> List[Dict[str, Any]]:
    return await cdp.get_interactive_elements(page)


async def click_by_role(page: Page, role: str, name: str, exact: bool = False) -> bool:
    loc = page.get_by_role(role, name=name, exact=exact)
    await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await _post_action_wait(page)
    return True


async def click_by_text(page: Page, text: str, exact: bool = False) -> bool:
    loc = page.get_by_text(text, exact=exact)
    await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await _post_action_wait(page)
    return True


async def click_by_label(page: Page, label: str, exact: bool = False) -> bool:
    """
    Labels are for inputs/controls. If the model tries label for a link/button,
    fallback to text to avoid timeouts.
    """
    # Try label with full timeout (not 4s which is too short!)
    try:
        loc = page.get_by_label(label, exact=exact)
        await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)  # Use full 15s timeout
        await _post_action_wait(page)
        return True
    except Exception:
        pass

    # Fallback: visible text
    loc2 = page.get_by_text(label, exact=exact)
    await loc2.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await _post_action_wait(page)
    return True


async def type_by_label(page: Page, label: str, text: str, exact: bool = False) -> bool:
    loc = page.get_by_label(label, exact=exact)
    await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await loc.first.fill(text)
    await _post_action_wait(page)
    return True


async def type_by_placeholder(page: Page, placeholder: str, text: str, exact: bool = False) -> bool:
    loc = page.get_by_placeholder(placeholder, exact=exact)
    await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await loc.first.fill(text)
    await _post_action_wait(page)
    return True


async def type_by_role(page: Page, role: str, name: str, text: str, exact: bool = False) -> bool:
    loc = page.get_by_role(role, name=name, exact=exact)
    await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await loc.first.fill(text)
    await _post_action_wait(page)
    return True


# NEW: Multi-locator strategy type functions
async def type_by_id(page: Page, element_id: str, text: str) -> bool:
    """Type into element by ID"""
    loc = page.locator(f"#{element_id}")
    await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await loc.first.fill(text)
    await _post_action_wait(page)
    return True


async def type_by_name(page: Page, name: str, text: str) -> bool:
    """Type into element by name attribute"""
    loc = page.locator(f"[name='{name}']")
    await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await loc.first.fill(text)
    await _post_action_wait(page)
    return True


async def type_by_css(page: Page, css: str, text: str) -> bool:
    """Type into element by CSS selector"""
    loc = page.locator(css)
    await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await loc.first.fill(text)
    await _post_action_wait(page)
    return True


async def type_by_xpath(page: Page, xpath: str, text: str) -> bool:
    """Type into element by XPath"""
    loc = page.locator(f"xpath={xpath}")
    await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await loc.first.fill(text)
    await _post_action_wait(page)
    return True


async def type_by_aria_label(page: Page, aria_label: str, text: str) -> bool:
    """Type into element by aria-label attribute"""
    loc = page.locator(f"[aria-label='{aria_label}']")
    await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await loc.first.fill(text)
    await _post_action_wait(page)
    return True
# End of multi-locator type functions


async def wait_for_text(page: Page, text: str, timeout_ms: int = 10000) -> bool:
    await page.get_by_text(text, exact=False).first.wait_for(timeout=timeout_ms)
    return True


async def wait_for_role(page: Page, role: str, name: str, exact: bool = False, timeout_ms: int = 10000) -> bool:
    await page.get_by_role(role, name=name, exact=exact).first.wait_for(timeout=timeout_ms)
    return True


async def press_key(page: Page, key: str) -> bool:
    await page.keyboard.press(key)
    await _post_action_wait(page, settle_ms=150)
    return True


async def select_smart(page: Page, target: Dict[str, Any], option_text: str) -> bool:
    """
    Works for:
    - Native <select> (uses select_option)
    - Custom dropdowns (click dropdown -> click option text)
    """
    dropdown = _target_locator(page, target).first

    # Try native select first
    try:
        tag = await dropdown.evaluate("el => (el && el.tagName ? el.tagName.toLowerCase() : '')")
        if tag == "select":
            try:
                await dropdown.select_option(label=option_text)
            except Exception:
                await dropdown.select_option(value=option_text)
            await _post_action_wait(page)
            return True
    except Exception:
        pass

    # Custom dropdown fallback
    await dropdown.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)

    # Try typical option roles first, then text fallback
    try:
        await page.get_by_role("option", name=option_text, exact=False).first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
        await _post_action_wait(page)
        return True
    except Exception:
        pass

    await page.get_by_text(option_text, exact=False).first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await _post_action_wait(page)
    return True


async def select_search_smart(page: Page, target: Dict[str, Any], query: str, option_text: str) -> bool:
    """
    For searchable dropdowns (MUI/React etc.):
    click dropdown -> type query -> click option_text
    """
    dropdown = _target_locator(page, target).first
    await dropdown.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)

    if query:
        await page.keyboard.type(query)
        # small wait for dropdown to filter options
        await asyncio.sleep(0.25)

    try:
        await page.get_by_role("option", name=option_text, exact=False).first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
        await _post_action_wait(page)
        return True
    except Exception:
        pass

    await page.get_by_text(option_text, exact=False).first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    await _post_action_wait(page)
    return True


# -----------------------------------------------------------------------------
# Compatibility shim:
# ai.py expects playwright_actions.get_snapshot(page)
# Some versions only implement get_dom_snapshot(page).
# -----------------------------------------------------------------------------

import base64
from typing import Any, Dict
from playwright.async_api import Page

async def get_snapshot(page: Page) -> Dict[str, Any]:
    """
    Returns a snapshot payload compatible with ai.py:
      {
        "dom": <dom_snapshot>,
        "screenshot": <base64 jpeg>,
        "pixelRatio": <float>,
        "viewportWidth": <int>,
        "viewportHeight": <int>,
      }
    """
    # DOM snapshot
    dom = await get_dom_snapshot(page)

    # Smaller screenshot to avoid websocket payload bloat
    screenshot_bytes = await page.screenshot(type="jpeg", quality=45, scale="css")

    # Viewport info (your file already has get_viewport_metadata in most versions)
    vp = await get_viewport_metadata(page)

    return {
        "dom": dom,
        "screenshot": base64.b64encode(screenshot_bytes).decode("utf-8"),
        "pixelRatio": vp.get("pixelRatio", 1),
        "viewportWidth": vp.get("viewportWidth", 0),
        "viewportHeight": vp.get("viewportHeight", 0),
    }
