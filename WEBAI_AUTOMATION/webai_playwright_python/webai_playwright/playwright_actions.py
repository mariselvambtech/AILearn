"""
Action execution layer mapping semantic AI commands to Playwright primitives.

This module is responsible for taking the structured JSON commands (like `click`, 
`type`, `hover`) emitted by the local AI Brain and translating them into robust 
Playwright interactions on the actual browser page, handling waiting and targeting.
"""
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



async def hydrate_page_dom(page: Page) -> None:
    """
    Scrolls down slightly and back up to trigger lazy-loaded React/Vue components 
    (such as product variant selectors and checkout buttons) without losing scroll position.
    """
    try:
        scroll_script = """
        () => {
            const initialY = window.scrollY;
            window.scrollBy({ top: 350, behavior: 'instant' });
            setTimeout(() => {
                window.scrollTo({ top: initialY, behavior: 'instant' });
            }, 150);
        }
        """
        await page.evaluate(scroll_script)
        await asyncio.sleep(0.2)
    except Exception:
        pass


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
            await page.wait_for_load_state("networkidle", timeout=4000)
        except Exception:
            pass

        # Trigger hydration scroll to expose dynamic buttons/variant selectors
        await hydrate_page_dom(page)
        await asyncio.sleep(0.3)
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


VALID_WINDOW_STATES = {"normal", "minimized", "maximized", "fullscreen"}

async def set_window_state(page: Page, state: str) -> bool:
    """
    Sets the browser window state.
    Allowed states: normal, minimized, maximized, fullscreen.
    """
    state_clean = (state or "").strip().lower()
    if state_clean not in VALID_WINDOW_STATES:
        raise ValueError(f"Invalid window state: '{state}'. Allowed states: {VALID_WINDOW_STATES}")

    if hasattr(cdp, "set_window_state"):
        await cdp.set_window_state(page, state_clean)
        return True

    # Fallback to direct CDP session
    try:
        session = await page.context.new_cdp_session(page)
        win = await session.send("Browser.getWindowForTarget")
        window_id = win.get("windowId")
        if window_id is not None:
            await session.send("Browser.setWindowBounds", {
                "windowId": window_id,
                "bounds": {"windowState": state_clean}
            })
    except Exception:
        pass
    return True


async def get_interactive_elements(page: Page) -> List[Dict[str, Any]]:
    return await cdp.get_interactive_elements(page)


async def click_by_role(page: Page, role: str, name: str, exact: bool = False) -> bool:
    clean_role = (role or "").strip().lower()
    if clean_role == "element" or not clean_role:
        print(f"[playwright_actions] Invalid ARIA role '{role}'. Falling back directly to click_by_text(name='{name}').")
        return await click_by_text(page, name, exact=exact)

    try:
        loc = page.get_by_role(role, name=name, exact=exact)
        try:
            await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
        except Exception as e:
            err_msg = str(e).lower()
            if any(term in err_msg for term in ["intercepts pointer events", "is receiving the click", "overlay", "covered"]):
                print(f"[playwright_actions] Pointer interception detected for click_by_role('{role}', '{name}'). Pressing Escape and retrying with force=True...")
                try:
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(0.3)
                except Exception:
                    pass
                await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS, force=True)
            else:
                raise
        await _post_action_wait(page)
        return True
    except Exception as exc:
        print(f"[playwright_actions] click_by_role('{role}', '{name}') failed: {exc}. Retrying fallback click_by_text(name='{name}')...")
        try:
            return await click_by_text(page, name, exact=False)
        except Exception:
            raise exc


async def click_by_text(page: Page, text: str, exact: bool = False) -> bool:
    loc = page.get_by_text(text, exact=exact)
    try:
        await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS)
    except Exception as e:
        err_msg = str(e).lower()
        if any(term in err_msg for term in ["intercepts pointer events", "is receiving the click", "overlay", "covered"]):
            print(f"[playwright_actions] Pointer interception detected for click_by_text('{text}'). Pressing Escape and retrying with force=True...")
            try:
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.3)
            except Exception:
                pass
            await loc.first.click(timeout=DEFAULT_ACTION_TIMEOUT_MS, force=True)
        else:
            raise
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
        "layoutMetrics": <layout_metrics>,
      }
    """
    # DOM snapshot
    dom_payload = await get_dom_snapshot(page)
    if isinstance(dom_payload, dict):
        dom_string = dom_payload.get("dom") if "dom" in dom_payload else json.dumps(dom_payload)
    else:
        dom_string = str(dom_payload or "")

    # Smaller screenshot to avoid websocket payload bloat
    screenshot_bytes = await page.screenshot(type="jpeg", quality=45, scale="css")
    if not isinstance(screenshot_bytes, (bytes, bytearray)):
        screenshot_bytes = str(screenshot_bytes or "").encode("utf-8")

    # Layout metrics (if supported by cdp)
    layout_metrics = None
    if hasattr(cdp, "get_layout_metrics"):
        try:
            layout_metrics = await cdp.get_layout_metrics(page)
        except Exception:
            pass

    # Viewport info via page evaluation
    vp = {}
    try:
        vp_eval = await page.evaluate("() => ({ viewportWidth: window.innerWidth, viewportHeight: window.innerHeight, pixelRatio: window.devicePixelRatio })")
        if isinstance(vp_eval, dict):
            vp.update(vp_eval)
    except Exception:
        pass

    if layout_metrics and isinstance(layout_metrics, dict):
        cs = layout_metrics.get("contentSize") or layout_metrics.get("cssContentSize") or {}
        if cs.get("width") and not vp.get("viewportWidth"):
            vp["viewportWidth"] = cs.get("width")
        if cs.get("height") and not vp.get("viewportHeight"):
            vp["viewportHeight"] = cs.get("height")

    res = {
        "dom": dom_string,
        "screenshot": base64.b64encode(screenshot_bytes).decode("utf-8"),
        "pixelRatio": vp.get("pixelRatio", 1),
        "viewportWidth": vp.get("viewportWidth", 0),
        "viewportHeight": vp.get("viewportHeight", 0),
    }
    if layout_metrics is not None:
        res["layoutMetrics"] = layout_metrics
    return res