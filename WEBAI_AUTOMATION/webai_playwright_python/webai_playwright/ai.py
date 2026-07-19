"""
High-level AI Integration Module for the Playwright Client.

This module exposes the `ai()` function, which acts as the main entrypoint 
for executing natural language tasks. It handles connecting to the Local 
AI Server via WebSocket, extracting the accessibility tree, sending it for 
analysis, and translating the returned AI commands into Playwright actions.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Union

from .config import LOGS_ENABLED

from playwright.async_api import Page

from .config import PACKAGE_NAME, MAX_TASK_CHARS, TOKEN, WEBDRIVER_ELEMENT_KEY
from .websocket_client import send_message, listen, close_ws
from . import meta
from . import cdp
from . import playwright_actions as pw

class ClientError(RuntimeError):
    pass

def _make_error_message(msg: str) -> ClientError:
    return ClientError(f"{PACKAGE_NAME}: {msg}")

def _pretty_command_name(name: str) -> str:
    # Matches TS getPrettyCommandName() intent for logs
    return name.replace("CDP", "").replace("_", " ")

async def _send_task_start(page: Page, task_id: str, task: str, options: Optional[Dict[str, Any]]) -> None:
    snapshot = await pw.get_snapshot(page)
    if LOGS_ENABLED:
        try:
            snap_json = json.dumps(snapshot)
            print(f"[client] snapshot bytes={len(snap_json.encode('utf-8'))}")
        except Exception:
            pass
    
    message = {
        "type": "task-start",
        "packageVersion": meta.get_version(),
        "taskId": task_id,
        "task": task,
        "snapshot": {
            "dom": snapshot["dom"],
            "screenshot": snapshot["screenshot"],
            "pixelRatio": snapshot["pixelRatio"],
            "viewportWidth": snapshot["viewportWidth"],
            "viewportHeight": snapshot["viewportHeight"],
        },
        "options": options or {},
    }
    await send_message(message)

async def _send_command_response(index: int, task_id: str, result: Any) -> None:
    # TS sends stringified JSON or "null"
    if result is None:
        res_str = "null"
    else:
        try:
            res_str = json.dumps(result)
        except TypeError:
            res_str = json.dumps(str(result))
    message = {
        "type": "command-response",
        "packageVersion": meta.get_version(),
        "taskId": task_id,
        "index": index,
        "result": res_str,
    }
    await send_message(message)

async def _execute_command(page: Page, command: Dict[str, Any]) -> Any:
    name = command.get("name")
    args = command.get("arguments") or {}
    if LOGS_ENABLED:
        print(f"[client] cmd -> {name} args={str(args)[:200]}")

    # CDP (ported from src/index.ts switch)
    if name == "getDOMSnapshot":
        return await cdp.get_dom_snapshot(page)
    if name == "executeScript":
        return await cdp.execute_script(page, args.get("script", ""), args.get("args", []))
    if name == "getCurrentUrl":
        return await cdp.get_current_url(page)
    if name == "findElements":
        return await cdp.find_elements(page, args.get("using", ""), args.get("value", ""))
    if name == "getElementTagName":
        return await cdp.get_element_tag_name(page, args.get("id"))
    if name == "getElementRect":
        return await cdp.get_element_rect(page, args.get("id"))
    if name == "getElementAttribute":
        return await cdp.get_element_attribute(page, args.get("id"), args.get("name"))
    if name == "clearElement":
        return await cdp.clear_element(page, args.get("id"))
    if name == "get":
        await cdp.get(page, args.get("url", ""))
        return True
    if name == "getTitle":
        return await cdp.get_title(page)
    if name == "getCurrentUrl":
        return page.url

    if name == "scrollIntoView":
        return await cdp.scroll_into_view(page, args.get("id"))
    if name == "scrollElement":
        return await cdp.scroll_element(page, args.get("id"), args.get("target"))
    if name == "setWindowState":
        return await pw.set_window_state(page, args.get("state", "maximized"))

    # Actions using CDP element
    if name == "clickElement":
        return await pw.click_cdp_element(page, args.get("id"))
    if name == "sendKeysToElement":
        # Note: CDP sendKeysToElement expects objectId and value as [string]
        return await cdp.send_keys_to_element(page, args.get("id"), args.get("value", [""]))
    if name == "hoverElement":
        return await pw.hover_cdp_element(page, args.get("id"))

    # Actions using location
    if name == "clickLocation":
        return await pw.click_location(page, float(args.get("x")), float(args.get("y")))
    if name == "hoverLocation":
        return await pw.hover_location(page, float(args.get("x")), float(args.get("y")))
    if name == "clickAndInputLocation":
        return await pw.click_and_input_location(page, float(args.get("x")), float(args.get("y")), args.get("value", ""))
    if name == "getElementAtLocation":
        return await cdp.get_element_at_location(
            page,
            float(args.get("x")),
            float(args.get("y")),
            bool(args.get("isShadowRoot", False)),
        )

    # Device actions
    if name == "sendKeys":
        return await pw.input_text(page, args.get("value", ""))
    if name == "keypressEnter":
        return await pw.keypress_enter(page)
    if name == "navigate":
        return await pw.navigate(page, args.get("url", ""))

    # Script actions
    if name == "scrollPage":
        return await pw.scroll_page_script(page, args.get("target"))


    # ===== Commands used by latest upgraded  server =====
    if name == "getInteractiveElements":
        return await pw.get_interactive_elements(page)

    if name == "clickByRole":
        return await pw.click_by_role(
            page,
            args.get("role", ""),
            args.get("name", "") or "",
            bool(args.get("exact", False)),
        )

    if name == "clickByText":
        return await pw.click_by_text(
            page,
            args.get("text", "") or "",
            bool(args.get("exact", False)),
        )

    if name == "clickByLabel":
        return await pw.click_by_label(
            page,
            args.get("label", "") or "",
            bool(args.get("exact", False)),
        )

    if name == "typeByLabel":
        return await pw.type_by_label(
            page,
            args.get("label", "") or "",
            args.get("text", "") or "",
            bool(args.get("exact", False)),
        )

    if name == "typeByPlaceholder":
        return await pw.type_by_placeholder(
            page,
            args.get("placeholder", "") or "",
            args.get("text", "") or "",
            bool(args.get("exact", False)),
        )

    if name == "typeByRole":
        return await pw.type_by_role(
            page,
            args.get("role", "") or "",
            args.get("name", "") or "",
            args.get("text", "") or "",
            bool(args.get("exact", False)),
        )

    if name == "waitForText":
        return await pw.wait_for_text(
            page,
            args.get("text", "") or "",
            int(args.get("timeoutMs", 10000)),
        )

    if name == "waitForRole":
        return await pw.wait_for_role(
            page,
            args.get("role", "") or "",
            args.get("name", "") or "",
            bool(args.get("exact", False)),
            int(args.get("timeoutMs", 10000)),
        )

    if name == "pressKey":
        return await pw.press_key(page, args.get("key", "Enter") or "Enter")

    if name == "selectSmart":
        return await pw.select_smart(
            page,
            args.get("target") or {},
            args.get("optionText", "") or "",
        )

    if name == "selectSearchSmart":
        return await pw.select_search_smart(
            page,
            args.get("target") or {},
            args.get("query", "") or "",
            args.get("optionText", "") or "",
        )
    
    
    if name == "verifyUrl":
        current = page.url
        expected = args.get("contains", "")
        if expected not in current:
            raise ClientError(f"URL verification failed: '{expected}' not in '{current}'")
        return True

    # ================================================
    # NEW: Multi-locator type command handlers
    # ================================================
    if name == "typeById":
        return await pw.type_by_id(
            page,
            args.get("id", ""),
            args.get("text", ""),
        )

    if name == "typeByName":
        return await pw.type_by_name(
            page,
            args.get("name", ""),
            args.get("text", ""),
        )

    if name == "typeByCSS":
        return await pw.type_by_css(
            page,
            args.get("css", ""),
            args.get("text", ""),
        )

    if name == "typeByXPath":
        return await pw.type_by_xpath(
            page,
            args.get("xpath", ""),
            args.get("text", ""),
        )

    if name == "typeByAriaLabel":
        return await pw.type_by_aria_label(
            page,
            args.get("aria_label", ""),
            args.get("text", ""),
        )

    # ================================================
    # Fallback Strategy Commands
    # ================================================
    if name == "typeWithFallback":
        return await pw.type_with_fallback(
            page,
            args.get("locators", []),
            args.get("text", ""),
        )

    if name == "clickWithFallback":
        return await pw.click_with_fallback(
            page,
            args.get("locators", []),
        )

    if name == "validatePage":
        return await pw.validate_page(
            page,
            args.get("expected_url", ""),
            int(args.get("timeout_ms", 10000)),
        )

    if name == "extractData":
        from datetime import datetime
        from .fallback_helpers import extract_with_fallback  # NEW: Import from correct module
        
        key = args.get("key", "extracted_value")
        locators = args.get("locators", [])
        extract_type = args.get("extractType", "text")
        attribute_name = args.get("attributeName")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] 🔍 EXTRACTING DATA:")
        print(f"   Variable: '{key}'")
        print(f"   Type: {extract_type}")
        if attribute_name:
            print(f"   Attribute: '{attribute_name}'")
        print(f"   Trying {len(locators)} locator(s)...")
        
        value = await extract_with_fallback(
            page, locators, extract_type, attribute_name
        )
        
        # Store in session
        if not hasattr(page, '__extracted_data__'):
            page.__extracted_data__ = {}
        page.__extracted_data__[key] = value
        
        print(f"\n[{timestamp}] ✅ EXTRACTED: {key} = '{value[:100] if len(value) > 100 else value}'")
        print(f"   Stored in page.__extracted_data__['{key}']\n")
        
        return True

    if name == "extractTableData":
        # NEW: Phase 8.3 - Table extraction with pagination
        from datetime import datetime
        from .fallback_helpers import extract_table_data
        
        table_selector = args.get("tableSelector", "")
        column_indices = args.get("columnIndices", [])
        columns = args.get("columns", [])
        max_pages = args.get("maxPages", 1)
        wait_per_page = args.get("waitPerPage", 2.0)
        page_timeout = args.get("pageTimeout", 10.0)
        retry_attempts = args.get("retryAttempts", 3)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] 📊 EXTRACTING TABLE:")
        print(f"   Selector: '{table_selector}'")
        print(f"   Columns: {columns}")
        print(f"   Max Pages: {max_pages}")
        print(f"   Wait: {wait_per_page}s, Timeout: {page_timeout}s, Retries: {retry_attempts}")
        
        result = await extract_table_data(
            page, table_selector, column_indices, columns, max_pages,
            wait_per_page, page_timeout, retry_attempts
        )
        
        print(f"\n[{timestamp}] ✅ TABLE EXTRACTED: {result.get('row_count', 0)} rows")
        
        return result

    # ================================================


    raise ClientError(f"Unsupported command: {name}")

async def ai(task: Union[str, Sequence[str]], *, page: Page, options: Optional[Dict[str, Any]] = None,
             parallelism: int = 10, fail_immediately: bool = False) -> Any:
    """
    Run a Zerostep AI step.

    Args:
      task: a prompt string or a list/tuple of prompts
      page: Playwright Page (Chromium recommended)
      options: dict supports keys: debug, model, type ('action'|'assert'|'query'), disableScroll
      parallelism: when task is a list, how many to run in parallel
      fail_immediately: when task is a list, fail as soon as any task fails

    Returns:
      The full task-complete message from Zerostep (dict)
    """
    if page is None:
        raise _make_error_message("Missing required 'page' argument.")
    if isinstance(task, (list, tuple)):
        return await _run_in_parallel(list(task), page=page, options=options, parallelism=parallelism, fail_immediately=fail_immediately)

    if not TOKEN:
        raise _make_error_message(
            "TOKEN must be defined via environment (TOKEN or AI_TOKEN) or a webai.config.json file. "
            "Find your token or sign up at https://app.zerostep.com"
        )
    if len(task) > MAX_TASK_CHARS:
        raise _make_error_message(f"Provided task string is too long, max length is {MAX_TASK_CHARS} chars")

    task_id = str(uuid.uuid4())

    await _send_task_start(page, task_id, task, options)

    completion: Dict[str, Any] = {}

    async def handler(message: Dict[str, Any]) -> bool:
        nonlocal completion
        if message.get("taskId") != task_id:
            return False
        msg_type = message.get("type")
        if msg_type == "command-request":
            idx = int(message.get("index", 0))
            result = await _execute_command(page, message)
            await _send_command_response(idx, task_id, result)
            return False
        if msg_type == "task-complete":
            completion = message
            if LOGS_ENABLED:
                print(f"[client] task-complete success={message.get('success')} error={message.get('error')}")
            return True
        return False

    await listen(task_id, handler)
    return completion

async def _run_in_parallel(tasks: List[str], *, page: Page, options: Optional[Dict[str, Any]],
                           parallelism: int, fail_immediately: bool) -> List[Any]:
    all_values: List[Any] = []
    for i in range(0, len(tasks), max(1, parallelism)):
        batch = tasks[i:i+parallelism]
        if fail_immediately:
            vals = await asyncio.gather(*[ai(t, page=page, options=options) for t in batch])
            all_values.extend(vals)
        else:
            results = await asyncio.gather(*[ai(t, page=page, options=options) for t in batch], return_exceptions=True)
            all_values.extend(results)
    return all_values

def ai_sync(task: Union[str, Sequence[str]], *, page, options: Optional[Dict[str, Any]] = None,
            parallelism: int = 10, fail_immediately: bool = False) -> Any:
    """Synchronous wrapper around ai() for Playwright sync API users."""
    return asyncio.get_event_loop().run_until_complete(
        ai(task, page=page, options=options, parallelism=parallelism, fail_immediately=fail_immediately)
    )

async def close() -> None:
    await close_ws()
