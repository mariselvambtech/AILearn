from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Page, CDPSession

from .config import WEBDRIVER_ELEMENT_KEY

_cdp_by_page: Dict[int, CDPSession] = {}

async def get_cdp(page: Page) -> CDPSession:
    key = id(page)
    if key in _cdp_by_page:
        return _cdp_by_page[key]
    try:
        session = await page.context.new_cdp_session(page)
    except Exception as e:
        raise RuntimeError("The ai() function can only be run against Chromium browsers.") from e
    _cdp_by_page[key] = session
    return session

async def detach(page: Page) -> None:
    key = id(page)
    if key in _cdp_by_page:
        try:
            await _cdp_by_page[key].detach()
        finally:
            _cdp_by_page.pop(key, None)

async def get_screenshot(page: Page) -> str:
    cdp = await get_cdp(page)
    res = await cdp.send("Page.captureScreenshot")
    return res["data"]

async def get_dom_snapshot(page: Page) -> Dict[str, Any]:
    cdp = await get_cdp(page)
    return await cdp.send("DOMSnapshot.captureSnapshot", {
        "computedStyles": ["background-color", "visibility", "opacity", "z-index", "overflow"],
        "includePaintOrder": True,
        "includeDOMRects": True,
    })

async def get_layout_metrics(page: Page) -> Dict[str, Any]:
    cdp = await get_cdp(page)
    return await cdp.send("Page.getLayoutMetrics")

async def get(page: Page, url: str) -> None:
    cdp = await get_cdp(page)
    await cdp.send("Page.navigate", {"url": url})

async def get_title(page: Page) -> str:
    cdp = await get_cdp(page)
    returned = await cdp.send("Runtime.evaluate", {"expression": "document.title", "returnByValue": True})
    return returned["result"].get("value")

async def get_current_url(page: Page) -> str:
    cdp = await get_cdp(page)
    returned = await cdp.send("Page.getNavigationHistory")
    return returned["entries"][returned["currentIndex"]]["url"]

async def execute_script(page: Page, script: str, args: List[Any]) -> Any:
    # Execute a function wrapper like the TS version
    function_declaration = f"function() {{ {script} }}"
    function_args = []
    for arg in args:
        if isinstance(arg, (bool, str, int, float)) or arg is None:
            function_args.append({"value": arg})
        elif isinstance(arg, dict) and WEBDRIVER_ELEMENT_KEY in arg:
            function_args.append({"objectId": arg[WEBDRIVER_ELEMENT_KEY]})
        else:
            function_args.append({"value": None})
    cdp = await get_cdp(page)
    returned = await cdp.send("Runtime.callFunctionOn", {
        "functionDeclaration": function_declaration,
        "arguments": function_args,
        "awaitPromise": True,
        "returnByValue": True,
    })
    return returned["result"].get("value")

async def run_function_on(page: Page, function_declaration: str, backend_node_id: int, args: Optional[List[Any]] = None) -> Any:
    cdp = await get_cdp(page)
    resolved = await cdp.send("DOM.resolveNode", {"backendNodeId": backend_node_id})
    object_id = resolved["object"]["objectId"]
    function_args = []
    if args:
        for a in args:
            if isinstance(a, (bool, str, int, float)) or a is None:
                function_args.append({"value": a})
            elif isinstance(a, dict) and WEBDRIVER_ELEMENT_KEY in a:
                function_args.append({"objectId": a[WEBDRIVER_ELEMENT_KEY]})
            else:
                function_args.append({"value": None})
    returned = await cdp.send("Runtime.callFunctionOn", {
        "functionDeclaration": function_declaration,
        "objectId": object_id,
        "arguments": function_args,
        "awaitPromise": True,
    })
    # if returnByValue wasn't requested, just return the raw.
    return returned

async def clear_element(page: Page, element_id: str) -> Any:
    # TS expects backendNodeId string for clearElement
    return await run_function_on(page, "function() { this.value = '' }", int(element_id))

async def get_element_attribute(page: Page, object_id: str, name: str) -> Optional[str]:
    cdp = await get_cdp(page)
    node = await cdp.send("DOM.requestNode", {"objectId": object_id})
    attrs = await cdp.send("DOM.getAttributes", {"nodeId": node["nodeId"]})
    attributes = attrs.get("attributes", [])
    for i in range(0, len(attributes), 2):
        if attributes[i] == name:
            return attributes[i+1] if i+1 < len(attributes) else None
    return None

async def get_element_tag_name(page: Page, object_id: str) -> str:
    cdp = await get_cdp(page)
    returned = await cdp.send("Runtime.callFunctionOn", {
        "functionDeclaration": "function() { return this.tagName }",
        "objectId": object_id,
        "returnByValue": True,
    })
    return returned["result"].get("value")

async def get_element_rect(page: Page, object_id: str) -> Dict[str, Any]:
    cdp = await get_cdp(page)
    returned = await cdp.send("Runtime.callFunctionOn", {
        "functionDeclaration": "function() { return JSON.parse(JSON.stringify(this.getBoundingClientRect())) }",
        "objectId": object_id,
        "returnByValue": True,
    })
    return returned["result"]["value"]

async def scroll_into_view(page: Page, element_id: str) -> Any:
    return await run_function_on(page, "function() { this.scrollIntoView({block: 'center', inline: 'center'}) }", int(element_id))


async def _get_content_quads(page: Page, *, backend_node_id: int | None = None, object_id: str | None = None) -> Dict[str, float]:
    """
    Get element quad coordinates.
    Supports either backendNodeId (int) OR objectId (str).
    """
    cdp = await get_cdp(page)

    params = {}
    if backend_node_id is not None:
        params["backendNodeId"] = backend_node_id
    elif object_id is not None:
        params["objectId"] = object_id
    else:
        raise ValueError("Either backend_node_id or object_id must be provided")

    quads = await cdp.send("DOM.getContentQuads", params)
    quad = quads["quads"][0]  # [x1,y1,x2,y2,x3,y3,x4,y4]

    top_left_x, top_left_y, top_right_x, top_right_y, bottom_right_x, bottom_right_y, bottom_left_x, bottom_left_y = quad
    width = bottom_right_x - top_right_x
    height = bottom_right_y - top_right_y
    center_x = top_left_x + (width / 2)
    center_y = top_right_y + (height / 2)

    return {
        "topLeftX": top_left_x, "topLeftY": top_left_y,
        "topRightX": top_right_x, "topRightY": top_right_y,
        "bottomRightX": bottom_right_x, "bottomRightY": bottom_right_y,
        "bottomLeftX": bottom_left_x, "bottomLeftY": bottom_left_y,
        "width": width, "height": height,
        "centerX": center_x, "centerY": center_y,
    }


async def click_element(page: Page, element_id: str) -> bool:
    """
    element_id can be either:
    - backendNodeId as a numeric string (e.g. "12345")
    - objectId (e.g. "-9006703651747481782.1.1") returned by DOM.resolveNode
    """
    cdp = await get_cdp(page)

    # Try backendNodeId first (old behavior)
    backend_node_id: int | None = None
    object_id: str | None = None

    try:
        backend_node_id = int(element_id)
    except Exception:
        object_id = element_id  # objectId string

    coords = await _get_content_quads(page, backend_node_id=backend_node_id, object_id=object_id)
    x, y = coords["centerX"], coords["centerY"]

    await cdp.send("Input.dispatchMouseEvent", {
        "type": "mousePressed",
        "x": x,
        "y": y,
        "button": "left",
        "clickCount": 1,
        "buttons": 1
    })
    await cdp.send("Input.dispatchMouseEvent", {
        "type": "mouseReleased",
        "x": x,
        "y": y,
        "button": "left",
        "clickCount": 1,
        "buttons": 1
    })
    return True


async def focus_element(page: Page, backend_node_id: int) -> None:
    cdp = await get_cdp(page)
    await cdp.send("DOM.focus", {"backendNodeId": backend_node_id})

async def send_keys_to_element(page: Page, object_id: str, value_list: List[str]) -> bool:
    cdp = await get_cdp(page)
    value = value_list[0] if value_list else ""
    node = await cdp.send("DOM.requestNode", {"objectId": object_id})
    await cdp.send("DOM.focus", {"nodeId": node["nodeId"]})
    for ch in value:
        await cdp.send("Input.dispatchKeyEvent", {"type": "char", "text": ch})
    return True

async def scroll_element(page: Page, element_id: str, target: str) -> Any:
    # target: up/down/top/bottom
    # We'll implement by running element.scrollBy / scrollTop.
    if target == "up":
        fn = "function() { this.scrollBy(0, -Math.max(100, this.clientHeight*0.8)); }"
    elif target == "down":
        fn = "function() { this.scrollBy(0, Math.max(100, this.clientHeight*0.8)); }"
    elif target == "top":
        fn = "function() { this.scrollTop = 0; }"
    elif target == "bottom":
        fn = "function() { this.scrollTop = this.scrollHeight; }"
    else:
        raise ValueError(f"Unsupported scroll target {target}")
    return await run_function_on(page, fn, int(element_id))

async def find_elements(page: Page, using: str, value: str) -> List[Dict[str, str]]:
    if using in ("css selector", "tag name"):
        return await query_selector_all(page, value)
    raise RuntimeError(f"Unsupported findElements strategy {using}")

async def query_selector_all(page: Page, selector: str) -> List[Dict[str, str]]:
    cdp = await get_cdp(page)
    root = await cdp.send("DOM.getDocument", {"depth": -1})
    returned = await cdp.send("DOM.querySelectorAll", {"nodeId": root["root"]["nodeId"], "selector": selector})
    node_ids = returned.get("nodeIds", [])
    resolved = await asyncio.gather(*[cdp.send("DOM.resolveNode", {"nodeId": nid}) for nid in node_ids])
    return [{WEBDRIVER_ELEMENT_KEY: r["object"]["objectId"]} for r in resolved if r.get("object", {}).get("objectId")]

async def get_element_at_location(page: Page, x: float, y: float, include_shadow_dom: bool = True) -> Dict[str, str]:
    cdp = await get_cdp(page)
    res = await cdp.send("DOM.getNodeForLocation", {
        "x": x,
        "y": y,
        "includeUserAgentShadowDOM": include_shadow_dom,
    })
    backend_node_id = res.get("backendNodeId")
    if backend_node_id is None:
        return {}
    resolved = await cdp.send("DOM.resolveNode", {"backendNodeId": backend_node_id})
    object_id = resolved.get("object", {}).get("objectId")
    if not object_id:
        return {}
    return {WEBDRIVER_ELEMENT_KEY: object_id}

async def get_interactive_elements(page: Page) -> List[Dict[str, Any]]:
    """
    Extract interactive elements from the page.
    Returns a list of dictionaries containing element metadata.
    """
    script = """
    (() => {
      const elements = [];
      const candidates = document.querySelectorAll(
        'a, button, input, textarea, select, [role="button"], [role="link"], [onclick], [contenteditable="true"]'
      );
      
      for (const el of candidates) {
        if (!el.offsetParent && el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA') continue;
        
        const rect = el.getBoundingClientRect();
        if (rect.width < 2 || rect.height < 2) continue;
        
        const style = window.getComputedStyle(el);
        if (style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0') continue;
        
        elements.push({
          tag: el.tagName.toLowerCase(),
          type: el.type || '',
          role: el.getAttribute('role') || el.getAttribute('aria-role') || '',
          name: (el.getAttribute('aria-label') || el.getAttribute('name') || el.textContent || '').trim().slice(0, 100),
          placeholder: el.getAttribute('placeholder') || '',
          ariaLabel: el.getAttribute('aria-label') || '',
          text: (el.textContent || '').trim().slice(0, 100),
          id: el.id || '',
          className: el.className || ''
        });
        
        if (elements.length >= 100) break;
      }
      
      return elements;
    })()
    """
    
    result = await page.evaluate(script)
    return result if isinstance(result, list) else []
