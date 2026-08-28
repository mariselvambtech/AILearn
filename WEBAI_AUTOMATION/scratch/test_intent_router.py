"""
TDVC Test Suite for Phase 6: Semantic Intent Router & Agentic Handoff Engine (Rule 7)
Verifies:
1. Semantic matching of user prompts to available synthesized skills.
2. Parameter & variable extraction from natural language prompts.
3. Gap analysis returning requires_agentic_handoff=True for prompts extending beyond skill scope.
"""
import os
import sys

# Ensure local packages are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_local_server")))

from webai_local_server.intent_router import IntentRouter


def test_intent_routing_and_variable_extraction():
    print("\n--- Running TDVC Test: Intent Router & Variable Extraction ---")

    # 1. Mock Skill Registry
    mock_skills = [
        {
            "skill_name": "Flipkart Search",
            "description": "Searches for clothing and products on Flipkart with color and category filters.",
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
                    "default": "blue"
                }
            },
            "parameterized_steps": [
                {"action": "goto", "url": "https://www.flipkart.com"},
                {"action": "type", "value": "{{search_query}}"},
                {"action": "click", "name": "Search Button"}
            ]
        },
        {
            "skill_name": "Wikipedia Article Search",
            "description": "Searches Wikipedia for an article topic.",
            "trigger_phrases": ["Search Wikipedia for topic", "Look up article on Wikipedia"],
            "parameters_schema": {
                "search_query": {"type": "string", "description": "Topic to search", "default": "Python"}
            },
            "parameterized_steps": [
                {"action": "goto", "url": "https://www.wikipedia.org"},
                {"action": "type", "value": "{{search_query}}"}
            ]
        }
    ]

    router = IntentRouter()

    # 2. Test Prompt requiring variable extraction & handoff
    user_prompt = "Buy a red shirt on Flipkart"
    result = router.route_intent(user_prompt, mock_skills)

    print(f"User Prompt: '{user_prompt}'")
    print(f"Matched Skill: {result.get('matched_skill', {}).get('skill_name')}")
    print(f"Extracted Variables: {result.get('extracted_variables')}")
    print(f"Requires Agentic Handoff: {result.get('requires_agentic_handoff')}")
    print(f"Confidence: {result.get('confidence')}")

    # 3. Assertions (Strict Rule 7 Requirements)
    assert result["matched_skill"] is not None, "Failed to match skill!"
    assert result["matched_skill"]["skill_name"] == "Flipkart Search", f"Expected 'Flipkart Search', got '{result['matched_skill']['skill_name']}'"
    
    extracted_vars = result.get("extracted_variables", {})
    assert "color_filter" in extracted_vars, "Failed to extract 'color_filter' parameter!"
    assert extracted_vars["color_filter"].lower() == "red", f"Expected 'red', got '{extracted_vars.get('color_filter')}'"
    
    assert result.get("requires_agentic_handoff") is True, "Expected requires_agentic_handoff=True for 'Buy' prompt!"
    assert result.get("confidence", 0) >= 0.7, "Expected high confidence score for matching prompt!"

    print("[PASS] test_intent_routing_and_variable_extraction completed successfully!")


def test_no_matching_skill_fallback():
    print("\n--- Running TDVC Test: No Matching Skill Fallback ---")
    mock_skills = [
        {
            "skill_name": "Wikipedia Article Search",
            "description": "Searches Wikipedia for an article topic.",
            "trigger_phrases": ["Search Wikipedia"],
            "parameters_schema": {},
            "parameterized_steps": []
        }
    ]

    router = IntentRouter()
    user_prompt = "Order pizza on Dominoes"
    result = router.route_intent(user_prompt, mock_skills)

    assert result["matched_skill"] is None, "Should not match any skill!"
    assert result["requires_agentic_handoff"] is True, "Unmatched prompt must require full agentic execution!"
    print("[PASS] test_no_matching_skill_fallback completed successfully!")


if __name__ == "__main__":
    test_intent_routing_and_variable_extraction()
    test_no_matching_skill_fallback()
    print("\n[SUCCESS] ALL TDVC INTENT ROUTER TESTS PASSED!")
