"""
TDVC Test Harness for SkillExecutor Parameter Injection & Schema Resolution.
Verifies variable template substitution ({{variable}} -> custom value or schema default)
in a sterile environment before executing browser playback.
"""
from __future__ import annotations

import os
import sys

# Ensure import paths for webai_playwright_python modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python")))

from webai_playwright.skill_executor import SkillExecutor


def test_skill_executor_resolution():
    print(" [1/3] Setting up mock synthesized_skill.json payload...")
    mock_skill_recipe = {
        "skill_name": "Test Search Automation",
        "description": "Mock skill for testing parameter resolution",
        "trigger_phrases": ["Run test search"],
        "parameters_schema": {
            "search_query": {
                "type": "string",
                "description": "The search term",
                "default": "tamilnadu"
            },
            "page_num": {
                "type": "string",
                "description": "Target page number",
                "default": "1"
            }
        },
        "parameterized_steps": [
            {
                "step_index": 1,
                "action": "open",
                "url": "https://example.com/search?p={{page_num}}",
                "value": None
            },
            {
                "step_index": 2,
                "action": "type",
                "name": "search",
                "value": "{{search_query}}",
                "locators": [{"type": "id", "value": "searchInput"}]
            }
        ]
    }

    executor = SkillExecutor(mock_skill_recipe)

    print(" [2/3] Testing Custom Runtime Argument Injection (search_query = 'Kerala', page_num = '2')...")
    custom_params = {"search_query": "Kerala", "page_num": "2"}
    resolved_custom = executor.resolve_steps(custom_params)

    assert resolved_custom[0]["url"] == "https://example.com/search?p=2", f"URL resolution failed: {resolved_custom[0]['url']}"
    assert resolved_custom[1]["value"] == "Kerala", f"Step value resolution failed: {resolved_custom[1]['value']}"
    print("   Custom parameter injection PASSED!")

    print(" [3/3] Testing Default Schema Fallback (empty runtime params {})...")
    resolved_defaults = executor.resolve_steps({})

    assert resolved_defaults[0]["url"] == "https://example.com/search?p=1", f"URL default resolution failed: {resolved_defaults[0]['url']}"
    assert resolved_defaults[1]["value"] == "tamilnadu", f"Step default value resolution failed: {resolved_defaults[1]['value']}"
    print("   Default schema fallback PASSED!")

    print(" SUCCESS: All SkillExecutor parameter resolution assertions PASSED!")


if __name__ == "__main__":
    test_skill_executor_resolution()
