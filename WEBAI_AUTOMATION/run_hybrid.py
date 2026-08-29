"""
End-to-End Hybrid Test Orchestrator for WebAI Platform.

1. Accepts hardcoded prompt: 'Buy a red shirt on Flipkart'.
2. Classifies intent & extracts dynamic variables via IntentRouter against local skills.
3. If a skill matches and requires_agentic_handoff is True, launches headed Chromium via Playwright.
4. Initializes SkillExecutor with the matched skill.
5. Replays recorded skill steps via execute_skill(page=page, keep_alive=True, handoff_intent=prompt),
   emitting a WebSocket 'task-start' message to port 8765.
6. Runs an action listener loop receiving AI commands (click, type, etc.) via WebSocket from port 8765
   and executing them live in Chromium without closing the browser context.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from playwright.async_api import async_playwright

# Ensure imports work from workspace root
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR / "webai_local_server") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "webai_local_server"))
if str(ROOT_DIR / "webai_playwright_python") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "webai_playwright_python"))

# Configure WebSocket target defaults to local WebAI AI Server on port 8765
os.environ.setdefault("WEBSOCKET_PROTOCOL", "ws")
os.environ.setdefault("WEBSOCKET_HOST", "localhost:8765")

from webai_local_server.intent_router import IntentRouter
from webai_playwright.skill_executor import SkillExecutor
from webai_playwright.ai import _execute_command, _send_command_response
from webai_playwright.websocket_client import listen

# Default local skill recipe fallback for Flipkart Search
DEFAULT_SKILLS: List[Dict[str, Any]] = [
    {
        "skill_name": "Flipkart Search",
        "description": "Searches for clothing, shirts, and products on Flipkart with color and category filters.",
        "trigger_phrases": [
            "Search for products on Flipkart",
            "Flipkart item search",
            "Find shirts on Flipkart",
            "Search shirts on Flipkart"
        ],
        "parameters_schema": {
            "search_query": {
                "type": "string",
                "description": "Product search item name",
                "default": "shirt"
            },
            "color_filter": {
                "type": "string",
                "description": "Color filter for the product",
                "default": "red"
            }
        },
        "parameterized_steps": [
            {"action": "goto", "url": "https://www.flipkart.com"},
            {
                "action": "type",
                "name": "search_input",
                "value": "{{color_filter}} {{search_query}}",
                "locators": [
                    {"type": "css", "value": "input[name='q']"},
                    {"type": "css", "value": "input[type='text']"},
                    {"type": "placeholder", "value": "Search for Products, Brands and More"}
                ]
            },
            {"action": "press_key", "key": "Enter"},
            {"action": "wait", "value": "3"}
        ]
    }
]


def load_local_skills() -> List[Dict[str, Any]]:
    """Discovers and loads synthesized skills from JSON files in the workspace."""
    skills: List[Dict[str, Any]] = []

    # Potential locations for skill JSONs
    skill_paths = [
        ROOT_DIR / "synthesized_skill.json",
        ROOT_DIR / "webai_playwright_python" / "synthesized_skill.json"
    ]

    for p in skill_paths:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "skill_name" in data:
                    skills.append(data)
            except Exception as e:
                print(f" ⚠️ [WARN] Could not parse skill at {p}: {e}")

    # Merge default fallback skills if not already present
    for default_sk in DEFAULT_SKILLS:
        d_name = default_sk.get("skill_name", "").lower()
        if not any(s.get("skill_name", "").lower() == d_name for s in skills):
            skills.append(default_sk)

    return skills


async def action_listener_loop(page: Any, task_id: str = "handoff_session") -> None:
    """
    Listens for incoming AI action commands (command-request) from local_webai_server_guided via WebSocket,
    executes the commands on the live Playwright page, and returns the result (command-response).
    """
    print(f"\n 🎧 [Action Listener] Connected & listening for AI commands on port 8765 (taskId='{task_id}')...")

    async def handler(message: Dict[str, Any]) -> bool:
        msg_type = message.get("type")
        msg_task_id = message.get("taskId") or message.get("task_id") or task_id

        if msg_type == "command-request":
            idx = int(message.get("index", 0))
            cmd_name = message.get("name", "unknown")
            print(f" 🤖 [AI Command Received] index={idx}, command='{cmd_name}'")
            try:
                result = await _execute_command(page, message)
                await _send_command_response(idx, msg_task_id, result)
                print(f"  ✅ [Command Executed] index={idx}, result={str(result)[:100]}")
            except Exception as e:
                print(f"  ❌ [Command Failed] index={idx}, error={e}")
                await _send_command_response(idx, msg_task_id, {"error": str(e)})
            return False

        if msg_type == "task-complete":
            print("\n==================================================")
            print(f" 🏁 AI Task Completed! Success: {message.get('success')}")
            if message.get("error"):
                print(f" ❌ Error Details: {message.get('error')}")
            print("==================================================\n")
            return True

        return False

    await listen(task_id, handler)


async def main() -> None:
    # Requirement 1: Hardcoded default prompt
    prompt = sys.argv[1] if len(sys.argv) > 1 else "Buy a red shirt on Flipkart"

    print("\n==================================================")
    print(" WebAI Hybrid E2E Test Orchestrator")
    print(f" PROMPT: '{prompt}'")
    print("==================================================\n")

    # Load local skill recipes
    available_skills = load_local_skills()
    print(f"Loaded {len(available_skills)} local skill recipe(s).")

    # Requirement 2: Initialize IntentRouter and route prompt
    router = IntentRouter()
    print("Routing intent against local skills...")
    result = router.route_intent(prompt, available_skills)

    matched_skill = result.get("matched_skill")
    requires_handoff = result.get("requires_agentic_handoff", False)
    extracted_vars = result.get("extracted_variables", {})

    print(f" -> Matched Skill : {matched_skill.get('skill_name') if matched_skill else 'None'}")
    print(f" -> Requires Handoff: {requires_handoff}")
    print(f" -> Extracted Vars  : {extracted_vars}")
    print(f" -> Confidence     : {result.get('confidence')}")
    print(f" -> Explanation    : {result.get('explanation')}\n")

    # Requirement 3 & 4: Launch headed Chromium & SkillExecutor if handoff required
    if matched_skill and requires_handoff:
        print("🚀 Agentic handoff required. Launching headed Chromium browser...")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            # Requirement 4: Initialize SkillExecutor
            executor = SkillExecutor(matched_skill)

            # Requirement 5: Execute skill with keep_alive=True and handoff_intent=prompt
            print("Executing skill steps and signaling WebSocket on port 8765...")
            exec_result = await executor.execute_skill(
                page=page,
                runtime_params=extracted_vars,
                keep_alive=True,
                handoff_intent=prompt
            )

            print("\n==================================================")
            print(f" Execution Status: {exec_result.get('status')}")
            print(f" Steps Executed  : {exec_result.get('steps_executed')}")
            print("==================================================")

            # Requirement 6: WebSocket action listener loop for AI Server takeover on port 8765
            print("\n [Orchestrator] Skill execution complete. Starting WebSocket action listener loop for AI Server takeover...")
            print(" 🔄 AI Server (local_webai_server_guided.py) can now send live browser commands.")
            print(" Press Ctrl+C to stop the orchestrator and close the browser.\n")

            try:
                await action_listener_loop(page, "handoff_session")
            except (KeyboardInterrupt, asyncio.CancelledError):
                print("\n[Orchestrator] Shutting down browser session...")
    elif matched_skill:
        print("Execute skill without handoff (determinist replay only).")
    else:
        print("❌ No matching skill found. Full agentic task initiation required.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExited.")
