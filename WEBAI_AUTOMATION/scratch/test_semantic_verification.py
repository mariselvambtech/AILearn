"""
TDVC Test Harness for Semantic Verification & Conditional Assertions (Decision 14).
Tests:
1. Mock DOM element dictionary (Rich Snapshot) verification.
2. verify_semantic_context returns True when expected_context matches aria-label or value even if innerText is empty.
3. verify_semantic_context raises SemanticVerificationError on mismatch.
4. Step schema accepts expected_context, target, and 'assert' action.
5. SkillExecutor resolves {{param}} in expected_context.
6. SkillExecutor evaluates 'assert' actions (url_contains, title_contains, visible).
"""
from __future__ import annotations

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure webai_playwright_python is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python")))

from webai_playwright.recorder import Step
from webai_playwright.skill_executor import (
    SemanticVerificationError,
    SkillExecutor,
    verify_semantic_context
)


def test_rich_snapshot_semantic_matching():
    print(" [1/5] Testing Rich Snapshot semantic context matching...")

    # Case 1: Match on aria-label with empty text and value
    snapshot_aria = {
        "text": "",
        "value": "",
        "aria": "Filter by Blue Color",
        "title": "",
        "checked": False
    }
    assert verify_semantic_context(snapshot_aria, "blue") is True
    assert verify_semantic_context(snapshot_aria, "Blue Color") is True

    # Case 2: Match on input value with empty text and aria
    snapshot_value = {
        "text": "",
        "value": "Pepe Jeans Slim Fit",
        "aria": "",
        "title": "",
        "checked": True
    }
    assert verify_semantic_context(snapshot_value, "pepe jeans") is True

    # Case 3: Match on title
    snapshot_title = {
        "text": "",
        "value": "",
        "aria": "",
        "title": "Select Large Size",
        "checked": False
    }
    assert verify_semantic_context(snapshot_title, "large") is True

    # Case 4: None or empty expected_context always passes
    assert verify_semantic_context(snapshot_aria, None) is True
    assert verify_semantic_context(snapshot_aria, "   ") is True

    print("  SUCCESS: Rich Snapshot matching on aria, value, and title PASSED!")


def test_semantic_mismatch_raises_error():
    print(" [2/5] Testing semantic mismatch raises SemanticVerificationError...")

    snapshot = {
        "text": "Red Casual Shirt",
        "value": "",
        "aria": "Red Shirt",
        "title": "",
        "checked": False
    }

    try:
        verify_semantic_context(snapshot, "blue")
        assert False, "Should have raised SemanticVerificationError for 'blue'"
    except SemanticVerificationError as e:
        print(f"  Captured expected exception: {e}")

    print("  SUCCESS: SemanticVerificationError raised on mismatch PASSED!")


def test_step_schema_extension():
    print(" [3/5] Testing Step schema accepts expected_context, target, and assert action...")

    click_step = Step(
        action="click",
        name="Color Filter",
        expected_context="blue",
        locators=[{"type": "css", "value": "div.color-blue"}]
    )
    assert click_step.expected_context == "blue"
    assert click_step.action == "click"

    assert_step = Step(
        action="assert",
        target="url_contains",
        value="color=blue"
    )
    assert assert_step.action == "assert"
    assert assert_step.target == "url_contains"
    assert assert_step.value == "color=blue"

    print("  SUCCESS: Step schema extensions verified PASSED!")


def test_skill_executor_template_resolution():
    print(" [4/5] Testing SkillExecutor template resolution in expected_context...")

    recipe = {
        "skill_name": "Filter Test",
        "parameters_schema": {
            "selected_brand": {"type": "string", "default": "Levis"}
        },
        "parameterized_steps": [
            {
                "action": "click",
                "name": "Brand Checkbox",
                "expected_context": "{{selected_brand}}",
                "locators": [{"type": "text", "value": "Brand"}]
            }
        ]
    }

    executor = SkillExecutor(recipe)
    # Default resolution
    resolved_default = executor.resolve_steps()
    assert resolved_default[0]["expected_context"] == "Levis"

    # Runtime override
    resolved_runtime = executor.resolve_steps({"selected_brand": "Pepe Jeans"})
    assert resolved_runtime[0]["expected_context"] == "Pepe Jeans"

    print("  SUCCESS: Template resolution on expected_context PASSED!")


def test_skill_executor_assert_handler():
    print(" [5/5] Testing SkillExecutor assert action execution with mock Page...")

    recipe = {
        "skill_name": "Assert Test",
        "parameterized_steps": [
            {
                "action": "assert",
                "target": "url_contains",
                "value": "flipkart.com/clothing"
            },
            {
                "action": "assert",
                "target": "title_contains",
                "value": "Flipkart"
            },
            {
                "action": "assert",
                "target": "visible",
                "value": "Filters Applied"
            }
        ]
    }

    executor = SkillExecutor(recipe)

    # Mock Playwright Page
    mock_page = MagicMock()
    mock_page.url = "https://www.flipkart.com/clothing-and-accessories/bottomwear"
    mock_page.title = AsyncMock(return_value="Online Shopping Site - Flipkart")
    
    mock_first = MagicMock()
    mock_first.is_visible = AsyncMock(return_value=True)
    mock_locator = MagicMock()
    mock_locator.first = mock_first
    mock_page.get_by_text.return_value = mock_locator

    result = asyncio.run(executor.execute_skill(mock_page))
    assert result["status"] == "success"
    assert result["steps_executed"] == 3

    # Verify failure condition on assert
    failing_recipe = {
        "skill_name": "Failing Assert",
        "parameterized_steps": [
            {
                "action": "assert",
                "target": "url_contains",
                "value": "amazon.com"
            }
        ]
    }
    failing_executor = SkillExecutor(failing_recipe)
    try:
        asyncio.run(failing_executor.execute_skill(mock_page))
        assert False, "Should have failed URL assert"
    except AssertionError as ae:
        print(f"  Captured expected assertion failure: {ae}")

    print("  SUCCESS: SkillExecutor assert action execution PASSED!")


def test_skill_synthesizer_expected_context():
    print(" [6/7] Testing SkillSynthesizer fallback populates expected_context...")
    from webai_playwright.skill_synthesizer import SkillSynthesizer

    synthesizer = SkillSynthesizer()
    sample_steps = [
        {
            "action": "click",
            "name": "COLOR",
            "voice_context": "in the color section I'm just selecting the blue",
            "locators": [{"type": "css", "value": "div.color"}]
        },
        {
            "action": "click",
            "name": "BRAND",
            "voice_context": "filtering the jeans with brand pepe jeans",
            "locators": [{"type": "text", "value": "BRAND"}]
        }
    ]

    skill = synthesizer.synthesize(sample_steps)
    param_steps = skill.get("parameterized_steps", [])
    assert len(param_steps) == 2
    assert "blue" in param_steps[0].get("expected_context", "").lower()
    assert "pepe jeans" in param_steps[1].get("expected_context", "").lower()
    print("  SUCCESS: SkillSynthesizer extracted expected_context from voice_context PASSED!")


def test_click_with_fallback_semantic_guard():
    print(" [7/7] Testing click_with_fallback semantic guard skips mismatched locators...")
    from webai_playwright.fallback_helpers import click_with_fallback

    # Mock Page and Locators
    mock_page = MagicMock()
    mock_page.wait_for_load_state = AsyncMock()

    # Locator 1 (CSS): text="Red Shirt", fails verification for "blue"
    mock_loc1 = MagicMock()
    mock_loc1.count = AsyncMock(return_value=1)
    mock_loc1.first.scroll_into_view_if_needed = AsyncMock()
    snap1 = {"text": "Red Shirt", "value": "", "aria": "", "title": "", "checked": False}
    mock_loc1.first.evaluate = AsyncMock(return_value=snap1)
    mock_loc1.evaluate = AsyncMock(return_value=snap1)
    mock_loc1.click = AsyncMock()

    # Locator 2 (Text): aria="Blue Shirt", passes verification for "blue"
    mock_loc2 = MagicMock()
    mock_loc2.count = AsyncMock(return_value=1)
    mock_loc2.first.scroll_into_view_if_needed = AsyncMock()
    snap2 = {"text": "", "value": "", "aria": "Select Blue Shirt", "title": "", "checked": False}
    mock_loc2.first.evaluate = AsyncMock(return_value=snap2)
    mock_loc2.evaluate = AsyncMock(return_value=snap2)
    mock_loc2.click = AsyncMock()

    async def mock_create_loc(target_page, loc):
        if loc.get("type") == "css":
            return mock_loc1
        elif loc.get("type") == "text":
            return mock_loc2
        return None

    locators = [
        {"type": "css", "value": "div.item"},
        {"type": "text", "value": "Blue"}
    ]

    with patch("webai_playwright.fallback_helpers._create_locator_obj", side_effect=mock_create_loc):
        res = asyncio.run(click_with_fallback(mock_page, locators, expected_context="blue"))
        assert res is True
        # mock_loc1 click should NOT have been called due to semantic mismatch
        assert not mock_loc1.click.called
        # mock_loc2 click SHOULD have been called
        assert mock_loc2.click.called

    print("  SUCCESS: click_with_fallback skipped mismatched locator and clicked matching locator PASSED!")


if __name__ == "__main__":
    test_rich_snapshot_semantic_matching()
    test_semantic_mismatch_raises_error()
    test_step_schema_extension()
    test_skill_executor_template_resolution()
    test_skill_executor_assert_handler()
    test_skill_synthesizer_expected_context()
    test_click_with_fallback_semantic_guard()
    print("\nALL SEMANTIC VERIFICATION & CONDITIONAL ASSERTION TESTS PASSED (7/7)!")
