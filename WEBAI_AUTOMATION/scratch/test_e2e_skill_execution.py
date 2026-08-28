"""
Headless E2E Test for SkillExecutor Playwright Execution.
Verifies loading synthesized_skill.json, parameter injection (search_query = 'Kerala'),
and headless Chromium playback.
"""
from __future__ import annotations

import os
import sys
import asyncio

# Ensure import paths for webai_playwright_python modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python")))

from playwright.async_api import async_playwright
from webai_playwright.skill_executor import SkillExecutor


async def test_e2e_skill_playback():
    skill_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python", "synthesized_skill.json"))
    
    assert os.path.exists(skill_file), f"Synthesized skill file not found at {skill_file}"
    
    print(" [1/3] Loading synthesized_skill.json...")
    executor = SkillExecutor(skill_file)

    print(" [2/3] Launching headless Playwright browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print(" [3/3] Executing skill with runtime parameter 'search_query' = 'Kerala'...")
        result = await executor.execute_skill(page, {"search_query": "Kerala"})
        
        await browser.close()

    assert result.get("status") == "success", f"Skill execution status failed: {result}"
    assert result.get("steps_executed", 0) > 0, "No steps were executed"
    print(f" SUCCESS: E2E Skill Playback PASSED! ({result.get('steps_executed')} steps executed)")


if __name__ == "__main__":
    asyncio.run(test_e2e_skill_playback())
