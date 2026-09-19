"""
TDVC Test Harness for SemanticVerificationError HITL Interception in SkillExecutor.
Tests:
1. When click_with_fallback raises SemanticVerificationError, SkillExecutor intercepts it.
2. SkillExecutor invokes HITLPlugin.trigger_intervention(page, payload=...).
3. SkillExecutor awaits the resolution payload and safely continues the step loop.
4. Subsequent steps execute without raising the intercepted SemanticVerificationError.
"""
from __future__ import annotations

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

# Ensure webai_playwright_python is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python")))

from webai_playwright.skill_executor import SemanticVerificationError, SkillExecutor


@pytest.mark.asyncio
async def test_semantic_verification_triggers_hitl_and_resumes():
    # Setup mock Page
    page = MagicMock()
    page.url = "https://www.flipkart.com/search?q=shirts"
    page.bring_to_front = AsyncMock()
    page.wait_for_load_state = AsyncMock()

    mock_context = MagicMock()
    mock_context.pages = [page]
    page.context = mock_context

    recipe = {
        "skill_name": "Semantic Failure HITL Test",
        "parameterized_steps": [
            {
                "action": "click",
                "name": "Blue Shirt Option",
                "expected_context": "blue",
                "locators": [{"type": "css", "value": "div.red-shirt"}]
            },
            {
                "action": "assert",
                "target": "url_contains",
                "value": "search"
            }
        ]
    }

    # Mock HITLPlugin
    mock_hitl = MagicMock()
    mock_hitl.trigger_intervention = AsyncMock(return_value={
        "status": "resolved",
        "action": "observer_mode_complete",
        "telemetry": [{"tag": "button", "text": "Blue Shirt"}],
        "audio_transcription": "User selected blue shirt manually"
    })

    executor = SkillExecutor(recipe, hitl_plugin=mock_hitl)

    # Simulate click_with_fallback raising SemanticVerificationError on step 1
    async def mock_click_semantic_fail(page_arg, locators, expected_context=None):
        raise SemanticVerificationError(f"expected '{expected_context}' not found in element")

    with patch("webai_playwright.skill_executor.click_with_fallback", side_effect=mock_click_semantic_fail):
        result = await executor.execute_skill(page)

    # 1. Assert executor caught the error and completed skill execution
    assert result["status"] == "success"
    assert result["steps_executed"] == 2

    # 2. Assert HITL trigger_intervention was called with page and payload
    assert mock_hitl.trigger_intervention.called, "Expected HITLPlugin.trigger_intervention to be called"
    assert mock_hitl.trigger_intervention.call_count == 1
    called_page, called_payload = mock_hitl.trigger_intervention.call_args[0][:2] if len(mock_hitl.trigger_intervention.call_args[0]) >= 2 else (mock_hitl.trigger_intervention.call_args[0][0], mock_hitl.trigger_intervention.call_args[1].get("payload", {}))
    assert called_page == page
    assert "semantic" in str(called_payload).lower() or "blue" in str(called_payload).lower()


if __name__ == "__main__":
    asyncio.run(test_semantic_verification_triggers_hitl_and_resumes())
    print("Test passed successfully!")
