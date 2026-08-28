"""
CLI Runner for Executing Synthesized AI Skills.

Loads synthesized_skill.json, prompts the user for runtime parameters (with schema defaults),
and executes the automation live in Chromium via SkillExecutor.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

# Ensure imports work regardless of execution CWD
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from webai_playwright.skill_executor import SkillExecutor


async def main():
    skill_file = sys.argv[1] if len(sys.argv) > 1 else "synthesized_skill.json"
    
    if not os.path.exists(skill_file):
        print(f" ❌ Skill file not found: {skill_file}")
        print("Please record and synthesize a skill first using record_then_run.py!")
        sys.exit(1)

    print(f"\nLoading Skill Recipe: {skill_file}")
    executor = SkillExecutor(skill_file)

    print("\n==================================================")
    print(f" SKILL NAME: {executor.skill_name}")
    print(f" DESCRIPTION: {executor.description}")
    print(f" TRIGGERS: {', '.join(executor.trigger_phrases)}")
    print("==================================================\n")

    runtime_params = {}
    if executor.parameters_schema:
        print("--- Parameter Configuration ---")
        for param_key, param_info in executor.parameters_schema.items():
            if isinstance(param_info, dict):
                default_val = param_info.get("default", "")
                desc = param_info.get("description", "")
            else:
                default_val = str(param_info)
                desc = ""

            prompt_str = f"Enter value for '{param_key}'"
            if desc:
                prompt_str += f" ({desc})"
            prompt_str += f" [default: {default_val}]: "

            user_val = input(prompt_str).strip()
            runtime_params[param_key] = user_val if user_val else default_val
        print("-------------------------------\n")

    print(f"Starting Playwright Browser for '{executor.skill_name}'...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            result = await executor.execute_skill(page, runtime_params)
            print("\n=== EXECUTION COMPLETED ===")
            print(f"Status: {result.get('status')}")
            print(f"Steps Executed: {result.get('steps_executed')}")
            if result.get("extracted_data"):
                print(f"Extracted Data: {json.dumps(result['extracted_data'], indent=2)}")
            print("===========================\n")
        except Exception as e:
            print(f"\n ❌ Execution Error: {e}\n")

        print("Closing browser in 3 seconds...")
        await asyncio.sleep(3.0)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
