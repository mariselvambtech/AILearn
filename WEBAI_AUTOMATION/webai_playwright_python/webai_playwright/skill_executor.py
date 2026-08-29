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
            for field_name in ["url", "value", "name", "attribute_name"]:
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
                success = await click_with_fallback(page, locators)
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
