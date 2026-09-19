"""
TDVC Test Suite for Automation-to-Skill Mapping:
1. SkillSynthesizer.synthesize() accepts source_automation_id and writes it to the root dict.
2. SkillSynthesizer.save_skill() persists source_automation_id to disk in skills/*.json and mirror file.
3. dashboard_server.py list_skills() extracts source_automation_id from JSON and includes it in response.
4. dashboard_server.py POST /api/automations/{automation_id}/synthesize fetches automation, synthesizes skill with source_automation_id, and returns {"status": "success"}.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup path imports
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "webai_playwright_python"))
sys.path.insert(0, str(REPO_ROOT / "webai_local_server"))

import pytest
from webai_playwright.skill_synthesizer import SkillSynthesizer
from webai_dashboard import dashboard_server


def test_synthesizer_injects_source_automation_id():
    """Validates that synthesize() adds source_automation_id at root level of skill dict."""
    synthesizer = SkillSynthesizer()
    steps = [
        {"action": "click", "name": "Submit", "url": "https://example.com", "voice_context": "click submit button"}
    ]

    # Test with source_automation_id provided (Ollama or fallback engine)
    skill = synthesizer.synthesize(steps, source_automation_id=105)
    assert skill.get("source_automation_id") == 105
    assert "skill_name" in skill and bool(skill["skill_name"])

    # Test fallback engine explicitly
    with patch.object(synthesizer, "_synthesize_with_ollama", side_effect=Exception("offline")):
        fb_skill = synthesizer.synthesize(steps, source_automation_id=106)
        assert fb_skill.get("source_automation_id") == 106
        assert fb_skill.get("skill_name") == "Example.com Automation Skill"

    # Test with empty steps
    empty_skill = synthesizer.synthesize([], source_automation_id=200)
    assert empty_skill.get("source_automation_id") == 200

    # Test without source_automation_id (None / omitted)
    default_skill = synthesizer.synthesize(steps)
    assert default_skill.get("source_automation_id") is None


def test_save_skill_persists_source_automation_id():
    """Validates that save_skill writes source_automation_id to disk in both slug and mirror files."""
    synthesizer = SkillSynthesizer()
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_skill = {
            "skill_name": "Flipkart Order",
            "description": "Order placement",
            "trigger_phrases": ["Order items"],
            "parameters_schema": {},
            "parameterized_steps": [{"action": "click", "name": "Buy"}],
            "source_automation_id": 5030
        }
        saved_path = synthesizer.save_skill(mock_skill, base_dir=tmpdir)
        slug_file = Path(saved_path)
        mirror_file = Path(tmpdir) / "synthesized_skill.json"

        assert slug_file.exists()
        slug_data = json.loads(slug_file.read_text(encoding="utf-8"))
        assert slug_data.get("source_automation_id") == 5030

        assert mirror_file.exists()
        mirror_data = json.loads(mirror_file.read_text(encoding="utf-8"))
        assert mirror_data.get("source_automation_id") == 5030


@pytest.mark.asyncio
async def test_list_skills_extracts_source_automation_id():
    """Validates that list_skills includes source_automation_id in the response payload."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        skill_with_id = {
            "skill_name": "Mapped Skill",
            "description": "Linked to automation 42",
            "parameters_schema": {},
            "parameterized_steps": [{"action": "click"}],
            "source_automation_id": 42
        }
        skill_without_id = {
            "skill_name": "Unmapped Skill",
            "description": "Standalone skill",
            "parameters_schema": {},
            "parameterized_steps": [{"action": "type"}],
        }

        (skills_dir / "mapped_skill.json").write_text(json.dumps(skill_with_id), encoding="utf-8")
        (skills_dir / "unmapped_skill.json").write_text(json.dumps(skill_without_id), encoding="utf-8")

        with patch.object(dashboard_server, "CLIENT_DIR", Path(tmpdir)):
            skills = await dashboard_server.list_skills()
            skill_map = {s["skill_name"]: s for s in skills}

            assert "Mapped Skill" in skill_map
            assert skill_map["Mapped Skill"]["source_automation_id"] == 42

            assert "Unmapped Skill" in skill_map
            assert skill_map["Unmapped Skill"]["source_automation_id"] is None


@pytest.mark.asyncio
async def test_synthesize_endpoint():
    """Validates POST /api/automations/{automation_id}/synthesize endpoint workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_automation = {
            "id": 99,
            "name": "Test Search",
            "voice_context": "search voice memo",
            "steps_json": [
                {
                    "action": "type",
                    "name": "search_input",
                    "value": "playwright",
                    "url": "https://test.local"
                }
            ]
        }

        with patch.object(dashboard_server, "CLIENT_DIR", Path(tmpdir)), \
             patch.object(dashboard_server, "_proxy_get", return_value=mock_automation) as mock_proxy, \
             patch.object(dashboard_server, "_require_api_key", return_value="dummy_key"):

            res = await dashboard_server.synthesize_automation_skill(automation_id=99, x_api_key="dummy_key")
            assert res == {"status": "success"}

            # Verify proxy get called with correct automation endpoint
            mock_proxy.assert_called_once_with("/automations/99", "dummy_key")

            # Verify skill was saved to temporary CLIENT_DIR with source_automation_id
            skills_dir = Path(tmpdir) / "skills"
            saved_files = list(skills_dir.glob("*.json"))
            assert len(saved_files) >= 1
            saved_content = json.loads(saved_files[0].read_text(encoding="utf-8"))
            assert saved_content.get("source_automation_id") == 99
