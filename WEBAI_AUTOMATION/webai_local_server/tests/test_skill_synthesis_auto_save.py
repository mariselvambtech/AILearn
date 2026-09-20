import json
import pytest
from pathlib import Path
from typing import Any, Dict, List, Optional


def test_normalize_history_step():
    """Verify action normalization extracts clean, replay-compatible step structures."""
    from webai_local_server.local_webai_server_guided import _normalize_history_step

    # 1. goto / open
    goto_act = {"action": "goto", "url": "https://sujaypublicschool.com/"}
    step1 = _normalize_history_step(goto_act, url="https://sujaypublicschool.com/")
    assert step1["action"] == "open"
    assert step1["url"] == "https://sujaypublicschool.com/"

    # 2. click with target
    click_act = {
        "action": "click",
        "target": {"by": "text", "text": "Online Admissions", "exact": False}
    }
    step2 = _normalize_history_step(click_act, url="https://sujaypublicschool.com/")
    assert step2["action"] == "click"
    assert step2["name"] == "Online Admissions"
    assert step2["url"] == "https://sujaypublicschool.com/"
    assert step2["locators"] is not None
    assert step2["locators"][0]["type"] == "text"
    assert step2["locators"][0]["value"] == "Online Admissions"

    # 3. type action
    type_act = {
        "action": "type",
        "target": {"by": "label", "label": "Student Name"},
        "text": "John Doe"
    }
    step3 = _normalize_history_step(type_act, url="https://sujaypublicschool.com/admissions")
    assert step3["action"] == "type"
    assert step3["value"] == "John Doe"
    assert step3["name"] == "Student Name"


def test_save_synthesized_skill_creates_expected_artifacts(tmp_path: Path):
    """Verify save_synthesized_skill creates slug directory, recorded_steps.json, skill JSON, and registry entry."""
    import sys
    playwright_dir = Path(__file__).resolve().parent.parent.parent / "webai_playwright_python"
    if str(playwright_dir) not in sys.path:
        sys.path.insert(0, str(playwright_dir))

    from run_autonomous import save_synthesized_skill

    sample_history = [
        {"action": "open", "url": "https://sujaypublicschool.com/"},
        {"action": "click", "name": "Online Admissions", "url": "https://sujaypublicschool.com/"},
    ]

    skill_name = "Sujay Admissions Check"
    trigger_desc = "Check if admissions are open at Sujay Public School"

    created_paths = save_synthesized_skill(
        skill_name=skill_name,
        trigger_desc=trigger_desc,
        action_history=sample_history,
        base_skills_dir=tmp_path
    )

    slug_dir = tmp_path / "sujay_admissions_check"
    recorded_steps_path = slug_dir / "recorded_steps.json"
    skill_json_path = tmp_path / "sujay_admissions_check.json"
    registry_path = tmp_path / "skills_registry.json"

    assert slug_dir.is_dir()
    assert recorded_steps_path.exists()
    assert skill_json_path.exists()
    assert registry_path.exists()

    # Verify recorded_steps.json content
    recorded_steps = json.loads(recorded_steps_path.read_text(encoding="utf-8"))
    assert len(recorded_steps) == 2
    assert recorded_steps[0]["action"] == "open"
    assert recorded_steps[1]["name"] == "Online Admissions"

    # Verify skill JSON schema
    skill_data = json.loads(skill_json_path.read_text(encoding="utf-8"))
    assert skill_data["skill_name"] == skill_name
    assert skill_data["description"] == trigger_desc
    assert trigger_desc in skill_data["trigger_phrases"]
    assert len(skill_data["parameterized_steps"]) == 2

    # Verify registry entry
    registry_data = json.loads(registry_path.read_text(encoding="utf-8"))
    assert isinstance(registry_data, list)
    assert any(entry["skill_name"] == skill_name for entry in registry_data)


def test_save_synthesized_skill_updates_existing_entry(tmp_path: Path):
    """Verify that saving an updated skill with the same name updates the existing registry entry without duplicate."""
    import sys
    playwright_dir = Path(__file__).resolve().parent.parent.parent / "webai_playwright_python"
    if str(playwright_dir) not in sys.path:
        sys.path.insert(0, str(playwright_dir))

    from run_autonomous import save_synthesized_skill

    # 1. Initial save
    save_synthesized_skill(
        skill_name="Test Workflow",
        trigger_desc="Original description",
        action_history=[{"action": "open", "url": "https://example.com"}],
        base_skills_dir=tmp_path
    )

    registry_path = tmp_path / "skills_registry.json"
    registry_data = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry_data) == 1
    assert registry_data[0]["description"] == "Original description"

    # 2. Update save
    save_synthesized_skill(
        skill_name="Test Workflow",
        trigger_desc="Updated description",
        action_history=[
            {"action": "open", "url": "https://example.com"},
            {"action": "click", "name": "Start"}
        ],
        base_skills_dir=tmp_path
    )

    updated_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(updated_registry) == 1
    assert updated_registry[0]["description"] == "Updated description"

