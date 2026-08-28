"""
TDVC Test Harness for SkillSynthesizer.
Verifies Ollama synthesis, JSON parsing, parameter substitution ({{param_name}}),
and deterministic fallback execution.
"""
from __future__ import annotations

import os
import sys

# Ensure import paths for webai_playwright_python modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python")))

from webai_playwright.recorder import Step
from webai_playwright.skill_synthesizer import SkillSynthesizer


def test_skill_synthesis():
    print(" [1/3] Setting up mock steps with typed values and voice context...")
    
    mock_steps = [
        Step(action="open", url="https://example.com/search", timestamp_ms=500.0),
        Step(
            action="type",
            name="State Search",
            value="tamilnadu",
            timestamp_ms=2500.0,
            voice_context="now typing state name"
        ),
        Step(
            action="click",
            name="Search Button",
            timestamp_ms=5000.0,
            voice_context="clicking search icon to submit"
        )
    ]

    print(" [2/3] Testing Fallback Synthesizer (Simulated Offline Ollama)...")
    offline_synthesizer = SkillSynthesizer(ollama_url="http://localhost:59999")
    fallback_skill = offline_synthesizer.synthesize(mock_steps)

    print(f"   Fallback Skill Title: '{fallback_skill.get('skill_name')}'")
    print(f"   Fallback Parameters: {list(fallback_skill.get('parameters_schema', {}).keys())}")
    
    assert fallback_skill.get("skill_name"), "Skill name missing in fallback output"
    assert len(fallback_skill.get("parameters_schema", {})) > 0, "parameters_schema should contain at least 1 parameterized variable"
    
    # Check that typed value "tamilnadu" was parameterized to {{state_name}}
    param_keys = list(fallback_skill["parameters_schema"].keys())
    first_key = param_keys[0]
    assert fallback_skill["parameters_schema"][first_key]["default"] == "tamilnadu", "Default parameter value mismatch"
    assert f"{{{{{first_key}}}}}" in fallback_skill["parameterized_steps"][1]["value"], "Step value was not parameterized with {{param}}"

    print(" [3/3] Testing Live or Mocked SkillSynthesizer Engine...")
    synthesizer = SkillSynthesizer()
    skill = synthesizer.synthesize(mock_steps)

    print(f"   Synthesized Skill Name: '{skill.get('skill_name')}'")
    print(f"   Description: '{skill.get('description')}'")
    print(f"   Trigger Phrases: {skill.get('trigger_phrases')}")
    print(f"   Parameters: {list(skill.get('parameters_schema', {}).keys())}")

    assert "skill_name" in skill and skill["skill_name"], "Synthesized skill_name missing"
    assert "parameters_schema" in skill, "parameters_schema missing"
    assert "parameterized_steps" in skill, "parameterized_steps missing"

    print(" SUCCESS: All SkillSynthesizer unit test assertions PASSED!")


if __name__ == "__main__":
    test_skill_synthesis()
