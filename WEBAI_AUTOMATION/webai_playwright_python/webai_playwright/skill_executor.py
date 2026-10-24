"""
Skill Executor Utility for WebAI Playwright Recorder.

Parses synthesized skills (synthesized_skill.json), injects user-provided 
runtime parameters (or schema defaults), and replays actions flawlessly in 
Chromium using Playwright's multi-locator fallback engine.
"""
from __future__ import annotations

import os
import sys
import json
import re
import asyncio
import copy
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

from playwright.async_api import Page

logger = logging.getLogger("SkillExecutor")


def safe_print(*args: Any, **kwargs: Any) -> None:
    """
    Safely print to stdout, catching any encoding or I/O exceptions.
    Prevents crashes on Windows when printing unencodable characters (e.g. ₹, emojis, ✕).
    """
    try:
        print(*args, **kwargs)
    except Exception:
        pass

from .fallback_helpers import (
    click_with_fallback,
    type_with_fallback,
    extract_with_fallback,
    select_with_fallback,
    drag_and_drop_with_fallback
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

    def __init__(
        self,
        skill_recipe: Union[Dict[str, Any], str, Path],
        hitl_plugin: Optional[Any] = None
    ) -> None:
        if isinstance(skill_recipe, (str, Path)):
            recipe_path = Path(skill_recipe)
            self.recipe_path: Optional[Path] = recipe_path if recipe_path.exists() else None
            if recipe_path.exists():
                self.recipe = json.loads(recipe_path.read_text(encoding="utf-8"))
            else:
                self.recipe = json.loads(str(skill_recipe))
        else:
            self.recipe_path = None
            self.recipe = dict(skill_recipe)

        self.skill_name = self.recipe.get("skill_name", "Unnamed Skill")
        self.description = self.recipe.get("description", "")
        self.trigger_phrases = self.recipe.get("trigger_phrases", [])
        self.parameters_schema = self.recipe.get("parameters_schema", {})
        self.parameterized_steps = self.recipe.get("parameterized_steps", [])
        self.hitl_plugin = hitl_plugin

    async def _handle_stuck_recovery(
        self,
        page: Page,
        step: Dict[str, Any],
        step_idx: int,
        reason: str
    ) -> bool:
        """
        Attempts self-healing:
        Step 1: lookup_hitl_memory. If memories found, execute learned recovery steps.
        Step 2: If no memory or recovery failed, trigger HITLPlugin intervention.
        Step 3: Save new HITL memory and update recipe on disk.
        """
        try:
            from .hitl_memory_store import lookup_hitl_memory
            current_url = getattr(page, "url", "")
            memories = lookup_hitl_memory(current_url, skill_name=self.skill_name)
            if memories:
                mem = memories[0]
                learned_steps = mem.get("learned_steps_json") or []
                safe_print(f" 🧠 [SkillExecutor] Found learned HITL memory for '{current_url}'. Applying Voice+DOM Self-Healing...")
                if learned_steps:
                    all_learned_ok = True
                    for l_step in learned_steps:
                        l_act = l_step.get("action")
                        l_locs = l_step.get("locators") or []
                        l_val = l_step.get("value")
                        if l_act == "click":
                            ok = await click_with_fallback(page, l_locs, expected_context=l_step.get("expected_context"))
                        elif l_act == "type":
                            ok = await type_with_fallback(page, l_locs, l_val or "")
                        elif l_act in ("drag_and_drop", "drag"):
                            ok = await drag_and_drop_with_fallback(
                                page,
                                l_locs,
                                target_locators=l_step.get("target_locators") or [],
                                source_coords=l_step.get("source_coords"),
                                target_coords=l_step.get("target_coords")
                            )
                        elif l_act in ("scroll", "scroll_page", "scroll_wheel"):
                            dx = float(l_step.get("delta_x") or l_step.get("deltaX") or 0)
                            dy = float(l_step.get("delta_y") or l_step.get("deltaY") or 300)
                            if hasattr(page, "mouse") and hasattr(page.mouse, "wheel"):
                                await page.mouse.wheel(dx, dy)
                            elif hasattr(page, "evaluate"):
                                await page.evaluate(f"window.scrollBy({dx}, {dy})")
                            ok = True
                        elif l_act in ("goto", "open", "navigate"):
                            if l_step.get("url"):
                                await page.goto(l_step.get("url"), wait_until="domcontentloaded")
                            ok = True
                        else:
                            ok = True
                        if not ok:
                            all_learned_ok = False
                            break
                    if all_learned_ok:
                        safe_print(" ✅ [SkillExecutor] Successfully executed learned recovery steps!")
                        return True
        except Exception as rec_err:
            logger.warning(f"Error during learned memory recovery: {rec_err}")

        # Step 2: Fallback to HITLPlugin intervention
        safe_print(f" ⚠️ [SkillExecutor] Stuck on step {step_idx} ('{step.get('name')}'). Launching HITL Observer Mode...")
        hitl = getattr(self, "hitl_plugin", None)
        if not hitl:
            try:
                from .plugins.hitl_plugin import HITLPlugin
                hitl = HITLPlugin(
                    tts_prompt=f"Action failed for {step.get('name')}. Please complete the action and click Resume AI."
                )
            except Exception as imp_err:
                logger.error(f"Failed to instantiate HITLPlugin: {imp_err}")
                hitl = None

        if hitl and hasattr(hitl, "trigger_intervention"):
            try:
                payload = {
                    "reason": reason,
                    "message": f"Action failed for '{step.get('name')}': {reason}. Please complete the action on your screen and click Resume AI.",
                    "step": step,
                    "step_index": step_idx
                }
                resolution = await hitl.trigger_intervention(page, payload=payload)
                safe_print(f" [SkillExecutor] HITL intervention resolved: {resolution.get('action', 'complete')}.")

                telemetry = resolution.get("telemetry") or resolution.get("click", {}).get("telemetry") or []
                voice_ctx = resolution.get("audio_transcription") or resolution.get("voice_context") or ""

                # Step 3: Save new HITL memory
                try:
                    from .hitl_memory_store import save_hitl_memory
                    current_url = getattr(page, "url", "")
                    save_hitl_memory(
                        url=current_url,
                        voice_context=voice_ctx,
                        learned_steps=telemetry,
                        blocker_context=reason,
                        skill_name=self.skill_name
                    )
                except Exception as save_err:
                    logger.warning(f"Failed to save HITL memory: {save_err}")

                # Update recipe on disk if possible
                try:
                    if telemetry and hasattr(self, "recipe") and "parameterized_steps" in self.recipe:
                        first_locs = telemetry[0].get("locators")
                        if first_locs and 0 <= step_idx - 1 < len(self.recipe["parameterized_steps"]):
                            self.recipe["parameterized_steps"][step_idx - 1]["locators"] = first_locs
                            if self.recipe_path and Path(self.recipe_path).exists():
                                Path(self.recipe_path).write_text(json.dumps(self.recipe, indent=2), encoding="utf-8")
                            default_recipe = Path("skills/synthesized_skill.json")
                            if default_recipe.exists():
                                default_recipe.write_text(json.dumps(self.recipe, indent=2), encoding="utf-8")
                except Exception as recipe_save_err:
                    logger.warning(f"Failed to update recipe file: {recipe_save_err}")

                return True
            except Exception as hitl_err:
                logger.error(f"Error during HITL intervention: {hitl_err}")
                return False

        return False

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
        safe_print(f"\n=== Executing Skill: '{self.skill_name}' ({len(steps)} steps) ===")
        
        executed_count = 0
        extracted_data: Dict[str, Any] = {}

        for idx, step in enumerate(steps, 1):
            action = step.get("action")
            url = step.get("url")
            name = step.get("name") or f"step_{idx}"
            value = step.get("value")
            locators = step.get("locators") or []

            safe_print(f" [Step {idx}/{len(steps)}] {action.upper()}: name='{name}', val='{value or url or ''}'")

            # Capture open tab count before executing step action
            current_page_count = (
                len(page.context.pages)
                if hasattr(page, "context") and page.context and hasattr(page.context, "pages")
                else 1
            )

            try:
                if action in ("goto", "open", "navigate"):
                    if url:
                        await page.goto(url, wait_until="domcontentloaded")
                
                elif action == "click":
                    expected_ctx = step.get("expected_context")
                    success = await click_with_fallback(page, locators, expected_context=expected_ctx)
                    if not success:
                        safe_print(f" ⚠️ Step {idx} click failed for '{name}'")
                        recovered = await self._handle_stuck_recovery(page, step, idx, reason=f"Click failed for '{name}'")
                        if not recovered:
                            safe_print(f" ❌ Step {idx} recovery failed for '{name}'")

                elif action == "type":
                    typed_text = value or ""
                    success = await type_with_fallback(page, locators, typed_text)
                    if not success:
                        safe_print(f" ⚠️ Step {idx} type failed for '{name}'")
                        recovered = await self._handle_stuck_recovery(page, step, idx, reason=f"Type failed for '{name}'")
                        if not recovered:
                            safe_print(f" ❌ Step {idx} recovery failed for '{name}'")

                elif action in ("drag_and_drop", "drag"):
                    target_locs = step.get("target_locators") or []
                    source_coords = step.get("source_coords")
                    target_coords = step.get("target_coords")
                    success = await drag_and_drop_with_fallback(
                        page,
                        locators,
                        target_locators=target_locs,
                        source_coords=source_coords,
                        target_coords=target_coords
                    )
                    if not success:
                        safe_print(f" ⚠️ Step {idx} drag_and_drop failed for '{name}'")
                        recovered = await self._handle_stuck_recovery(page, step, idx, reason=f"Drag and drop failed for '{name}'")
                        if not recovered:
                            safe_print(f" ❌ Step {idx} recovery failed for '{name}'")

                elif action in ("scroll", "scroll_page", "scroll_wheel"):
                    delta_x = step.get("delta_x") or step.get("deltaX") or 0
                    delta_y = step.get("delta_y") or step.get("deltaY") or step.get("value") or 300
                    try:
                        delta_x = float(delta_x)
                        delta_y = float(delta_y)
                    except (ValueError, TypeError):
                        delta_x, delta_y = 0.0, 300.0
                    if hasattr(page, "mouse") and hasattr(page.mouse, "wheel"):
                        await page.mouse.wheel(delta_x, delta_y)
                    elif hasattr(page, "evaluate"):
                        await page.evaluate(f"window.scrollBy({delta_x}, {delta_y})")

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
                        safe_print(f" Extracted data for '{name}': {val[:60] if isinstance(val, str) else val}")

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
                    safe_print(f" [ASSERT] target='{target}', expected='{expected_val}'")

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
                    safe_print(f"  [OK] Assertion PASSED for '{target}' -> '{expected_val}'")

            except SemanticVerificationError as e:
                logger.warning(f"Semantic verification failed on step {idx} ('{name}'): {e}. Triggering recovery...")
                safe_print(f" ⚠️ [SkillExecutor] Semantic verification failed on step {idx} ('{name}'): {e}. Launching recovery...")
                await self._handle_stuck_recovery(page, step, idx, reason=f"Semantic verification failed: {e}")

                # Check if a new tab was opened during manual intervention
                if hasattr(page, "context") and page.context and hasattr(page.context, "pages"):
                    try:
                        if len(page.context.pages) > current_page_count:
                            page = page.context.pages[-1]
                            await page.bring_to_front()
                            await page.wait_for_load_state("domcontentloaded")
                            logger.info("New tab detected after HITL intervention. Switched active page context.")
                            safe_print(f" [SkillExecutor] New tab detected after HITL. Switched active page context to '{page.url}'.")
                    except Exception as tab_err:
                        logger.warning(f"Error handling new tab context switch after HITL: {tab_err}")

                executed_count += 1
                continue

            # Context Switching Logic for New Tabs
            if hasattr(page, "context") and page.context and hasattr(page.context, "pages"):
                try:
                    if len(page.context.pages) > current_page_count:
                        page = page.context.pages[-1]
                        await page.bring_to_front()
                        await page.wait_for_load_state("domcontentloaded")
                        logger.info("New tab detected. Switched active page context.")
                        safe_print(f" [SkillExecutor] New tab detected. Switched active page context to '{page.url}'.")
                except Exception as tab_err:
                    logger.warning(f"Error handling new tab context switch: {tab_err}")
                    safe_print(f"  [WARN] [SkillExecutor] Error handling new tab context switch: {tab_err}")

            executed_count += 1

        safe_print(f"=== Skill Execution Finished Successfully ({executed_count}/{len(steps)} steps) ===\n")

        status = "success"
        if keep_alive and handoff_intent:
            status = "handoff"
            safe_print(f" [SkillExecutor] Handing off live browser session for task: '{handoff_intent}'")
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
                safe_print(" [SkillExecutor] WebSocket 'task-start' message emitted successfully.")
            except Exception as e:
                safe_print(f" [WARN] [SkillExecutor] WebSocket handoff dispatch failed: {e}")

        return {
            "status": status,
            "skill_name": self.skill_name,
            "steps_executed": executed_count,
            "extracted_data": extracted_data,
            "keep_alive": keep_alive,
            "handoff_intent": handoff_intent
        }
