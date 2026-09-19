"""
Skill Executor Utility for WebAI Playwright Recorder.

Parses synthesized skills (synthesized_skill.json), injects user-provided 
runtime parameters (or schema defaults), and replays actions flawlessly in 
Chromium using Playwright's multi-locator fallback engine.
"""
from __future__ import annotations

import os
import json
import re
import asyncio
import copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import Page

from .fallback_helpers import (
    click_with_fallback,
    type_with_fallback,
    extract_with_fallback,
    select_with_fallback
)


class SemanticVerificationError(Exception):
    """Raised when pre-click Rich Element Snapshot fails semantic verification against expected_context."""
    pass


RICH_SNAPSHOT_JS = """el => ({
    text: el.innerText || el.textContent || '',
    value: el.value || '',
    aria: el.getAttribute('aria-label') || '',
    title: el.getAttribute('title') || '',
    checked: Boolean(el.checked)
})"""


async def extract_rich_snapshot(locator_obj: Any) -> Dict[str, Any]:
    """
    Extracts a comprehensive state dictionary from a DOM element using locator.evaluate().
    Dictionary keys: text, value, aria, title, checked.
    """
    try:
        if hasattr(locator_obj, "first") and hasattr(locator_obj, "count"):
            if await locator_obj.count() > 0:
                res = await locator_obj.first.evaluate(RICH_SNAPSHOT_JS)
                if isinstance(res, dict):
                    return res
        if hasattr(locator_obj, "evaluate"):
            res = await locator_obj.evaluate(RICH_SNAPSHOT_JS)
            if isinstance(res, dict):
                return res
    except Exception:
        pass
    return {"text": "", "value": "", "aria": "", "title": "", "checked": False}


def verify_semantic_context(snapshot: Dict[str, Any], expected_context: Optional[str]) -> bool:
    """
    Verifies that expected_context exists within the lowercase string values of the Rich Element Snapshot.
    Inspects text, value, aria (aria-label), title, and checked state.
    Raises SemanticVerificationError on mismatch.
    """
    if not expected_context or not expected_context.strip():
        return True

    expected = expected_context.strip().lower()
    parts = [
        str(snapshot.get("text") or ""),
        str(snapshot.get("value") or ""),
        str(snapshot.get("aria") or ""),
        str(snapshot.get("title") or "")
    ]
    if snapshot.get("checked"):
        parts.append("checked selected")

    combined_text = " ".join(parts).lower()

    if expected in combined_text:
        return True

    raise SemanticVerificationError(
        f"Semantic verification failed: expected '{expected_context}' not found in element snapshot: {snapshot}"
    )


class SkillExecutor:
    """
    Executes synthesized AI skill recipes with dynamic runtime parameter injection.
    """

    def __init__(self, skill_recipe: Union[Dict[str, Any], str, Path]) -> None:
        if isinstance(skill_recipe, (str, Path)):
            recipe_path = Path(skill_recipe)
            if recipe_path.exists():
                self.recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            else:
                self.recipe = json.loads(str(skill_recipe))
        else:
            self.recipe = dict(skill_recipe)

        self.skill_name = self.recipe.get("skill_name", "Unnamed Skill")
        self.description = self.recipe.get("description", "")
        self.trigger_phrases = self.recipe.get("trigger_phrases", [])
        self.parameters_schema = self.recipe.get("parameters_schema", {})
        self.parameterized_steps = self.recipe.get("parameterized_steps", [])

    def resolve_steps(self, runtime_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Injects runtime parameters (or schema defaults) into step template placeholders ({{variable}}).
        """
        # Step 1: Gather defaults from schema
        resolved_params: Dict[str, str] = {}
        for param_key, param_info in self.parameters_schema.items():
            if isinstance(param_info, dict):
                resolved_params[param_key] = str(param_info.get("default", ""))
            else:
                resolved_params[param_key] = str(param_info)

        # Step 2: Override defaults with user-provided runtime arguments
        if runtime_params:
            for k, v in runtime_params.items():
                if v is not None and str(v).strip() != "":
                    resolved_params[k] = str(v)

        # Step 3: Template replacement in step fields
        resolved_steps = copy.deepcopy(self.parameterized_steps)
        for step in resolved_steps:
            for field_name in ["url", "value", "name", "attribute_name", "expected_context", "target"]:
                field_val = step.get(field_name)
                if field_val and isinstance(field_val, str) and "{{" in field_val:
                    for p_key, p_val in resolved_params.items():
                        placeholder = f"{{{{{p_key}}}}}"
                        if placeholder in field_val:
                            field_val = field_val.replace(placeholder, p_val)
                    step[field_name] = field_val

        return resolved_steps

    async def execute_skill(
        self,
        page: Page,
        runtime_params: Optional[Dict[str, Any]] = None,
        keep_alive: bool = False,
        handoff_intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Replays resolved skill steps sequentially in Playwright with multi-locator fallbacks.
        If keep_alive=True and handoff_intent is provided, skips browser closing and hands off
        live page context to the AI Brain server via a WebSocket task-start message.
        """
        steps = self.resolve_steps(runtime_params)
        print(f"\n=== Executing Skill: '{self.skill_name}' ({len(steps)} steps) ===")
        
        executed_count = 0
        extracted_data: Dict[str, Any] = {}

        for idx, step in enumerate(steps, 1):
            action = step.get("action")
            url = step.get("url")
            name = step.get("name") or f"step_{idx}"
            value = step.get("value")
            locators = step.get("locators") or []

            print(f" [Step {idx}/{len(steps)}] {action.upper()}: name='{name}', val='{value or url or ''}'")

            if action in ("goto", "open", "navigate"):
                if url:
                    await page.goto(url, wait_until="domcontentloaded")
            
            elif action == "click":
                expected_ctx = step.get("expected_context")
                success = await click_with_fallback(page, locators, expected_context=expected_ctx)
                if not success:
                    print(f" ⚠️ Step {idx} click failed for '{name}'")

            elif action == "type":
                typed_text = value or ""
                success = await type_with_fallback(page, locators, typed_text)
                if not success:
                    print(f" ⚠️ Step {idx} type failed for '{name}'")

            elif action == "press_key":
                key = step.get("key") or "Enter"
                await page.keyboard.press(key)

            elif action == "wait":
                try:
                    delay_sec = float(value or 1.0)
                    await asyncio.sleep(delay_sec)
                except ValueError:
                    await asyncio.sleep(1.0)

            elif action in ("extract", "extract_table"):
                val = await extract_with_fallback(page, locators, step)
                if val is not None:
                    extracted_data[name] = val
                    print(f" Extracted data for '{name}': {val[:60] if isinstance(val, str) else val}")

            elif action == "verify_text":
                target_text = value or ""
                content = await page.content()
                assert target_text.lower() in content.lower(), f"Verification failed: '{target_text}' not in page"

            elif action == "verify_visible":
                target_text = value or ""
                assert await page.get_by_text(target_text).first.is_visible(), f"Verification failed: '{target_text}' not visible"

            elif action == "assert":
                target = step.get("target") or "url_contains"
                expected_val = str(value or "")
                print(f" [ASSERT] target='{target}', expected='{expected_val}'")

                if target == "url_contains":
                    current_url = page.url or ""
                    assert expected_val.lower() in current_url.lower(), (
                        f"Assertion failed: URL '{current_url}' does not contain expected '{expected_val}'"
                    )
                elif target == "url_equals":
                    current_url = page.url or ""
                    assert current_url == expected_val, (
                        f"Assertion failed: URL '{current_url}' != '{expected_val}'"
                    )
                elif target == "title_contains":
                    title = await page.title() if hasattr(page, "title") else ""
                    assert expected_val.lower() in str(title).lower(), (
                        f"Assertion failed: Page title '{title}' does not contain expected '{expected_val}'"
                    )
                elif target in ("visible", "element_visible", "text_visible"):
                    is_vis = False
                    if locators:
                        from .fallback_helpers import _create_locator_obj
                        loc_obj = await _create_locator_obj(page, locators[0])
                        is_vis = await loc_obj.first.is_visible() if loc_obj and await loc_obj.count() > 0 else False
                    elif expected_val and hasattr(page, "get_by_text"):
                        loc_by_text = page.get_by_text(expected_val)
                        is_vis = await loc_by_text.first.is_visible() if hasattr(loc_by_text, "first") else False
                    assert is_vis, f"Assertion failed: Element with '{expected_val}' is not visible"
                elif target in ("not_visible", "hidden"):
                    is_vis = True
                    if locators:
                        from .fallback_helpers import _create_locator_obj
                        loc_obj = await _create_locator_obj(page, locators[0])
                        is_vis = await loc_obj.first.is_visible() if loc_obj and await loc_obj.count() > 0 else False
                    elif expected_val and hasattr(page, "get_by_text"):
                        loc_by_text = page.get_by_text(expected_val)
                        is_vis = await loc_by_text.first.is_visible() if hasattr(loc_by_text, "first") else False
                    assert not is_vis, f"Assertion failed: Element with '{expected_val}' is still visible"
                else:
                    # Fallback to general page text / URL check
                    current_url = page.url or ""
                    if expected_val.lower() in current_url.lower():
                        pass
                    elif hasattr(page, "content"):
                        content = await page.content()
                        assert expected_val.lower() in content.lower(), (
                            f"Assertion failed: '{expected_val}' not found in URL or page content"
                        )
                print(f"  [OK] Assertion PASSED for '{target}' -> '{expected_val}'")

            executed_count += 1

        print(f"=== Skill Execution Finished Successfully ({executed_count}/{len(steps)} steps) ===\n")

        status = "success"
        if keep_alive and handoff_intent:
            status = "handoff"
            print(f" [SkillExecutor] Handing off live browser session for task: '{handoff_intent}'")
            try:
                from .websocket_client import send_message
                payload = {
                    "type": "task-start",
                    "taskId": "handoff_session",
                    "task": handoff_intent,
                    "url": page.url,
                    "options": {
                        "keep_alive": True,
                        "from_skill": self.skill_name
                    }
                }
                await send_message(payload)
                print(" [SkillExecutor] WebSocket 'task-start' message emitted successfully.")
            except Exception as e:
                print(f" [WARN] [SkillExecutor] WebSocket handoff dispatch failed: {e}")

        return {
            "status": status,
            "skill_name": self.skill_name,
            "steps_executed": executed_count,
            "extracted_data": extracted_data,
            "keep_alive": keep_alive,
            "handoff_intent": handoff_intent
        }
