"""
TDVC Test Suite for Multi-Skill Library Architecture with Mandatory Safeguards:
1. Regex slugification (dependency-free).
2. SkillSynthesizer save_skill() dual-write logic (skills/{slug}.json + synthesized_skill.json).
3. Dashboard Server multi-file directory scanning and filename injection in GET /api/skills.
4. Safeguard 1: Deduplication (skills/*.json loaded first; synthesized_skill.json deduplicated if identical skill_name).
5. Safeguard 2: Path Traversal Guard (os.path.basename sanitization).
6. Safeguard 3: CLI Runner Support in run_skill.py (sys.argv[1] fallback).
7. SkillExecutePayload schema validation accepting a filename string.
8. IntentRouter load_local_skills() discovering all skill JSON files in skills/ directory.
"""

import os
import json
import tempfile
from pathlib import Path
import pytest

# Target imports
from webai_playwright.skill_synthesizer import SkillSynthesizer
from webai_dashboard.dashboard_server import SkillExecutePayload, sanitize_skill_filename
from webai_local_server.intent_router import load_local_skills


def test_slugify_filename():
    """Validates dependency-free slugification of human-readable skill names into safe filenames."""
    assert SkillSynthesizer.slugify("Flipkart Product Search") == "flipkart_product_search"
    assert SkillSynthesizer.slugify("Amazon - Add to Cart! (2026)") == "amazon_add_to_cart_2026"
    assert SkillSynthesizer.slugify("  Multiple   Spaces  And---Dashes  ") == "multiple_spaces_and_dashes"
    assert SkillSynthesizer.slugify("") == "skill"


def test_skill_synthesizer_save_skill_dual_write():
    """Validates that save_skill creates skills/ directory, saves skills/{slug}.json, and mirrors synthesized_skill.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        synthesizer = SkillSynthesizer()
        mock_skill = {
            "skill_name": "Flipkart Shoe Search",
            "description": "Searches for shoes on Flipkart",
            "trigger_phrases": ["Search shoes on Flipkart"],
            "parameters_schema": {"search_query": {"type": "string", "default": "shoes"}},
            "parameterized_steps": [{"action": "click", "name": "Search"}]
        }

        saved_path = synthesizer.save_skill(mock_skill, base_dir=tmpdir)
        slug_file = Path(saved_path)
        mirror_file = Path(tmpdir) / "synthesized_skill.json"

        # Check slug file exists in skills/
        assert slug_file.exists()
        assert slug_file.name == "flipkart_shoe_search.json"
        assert slug_file.parent.name == "skills"

        data = json.loads(slug_file.read_text(encoding="utf-8"))
        assert data["skill_name"] == "Flipkart Shoe Search"

        # Check mirror file exists
        assert mirror_file.exists()
        mirror_data = json.loads(mirror_file.read_text(encoding="utf-8"))
        assert mirror_data["skill_name"] == "Flipkart Shoe Search"


def test_safeguard_path_traversal_sanitization():
    """Validates that sanitize_skill_filename strips directory traversal characters."""
    assert sanitize_skill_filename("../../etc/passwd") == "passwd"
    assert sanitize_skill_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert sanitize_skill_filename("skills/flipkart.json") == "flipkart.json"
    assert sanitize_skill_filename("amazon_search.json") == "amazon_search.json"


def test_safeguard_deduplication_in_scanner():
    """Validates that skills/*.json takes precedence and mirror synthesized_skill.json is deduplicated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        skill_primary = {
            "skill_name": "Flipkart Search",
            "description": "Primary library skill",
            "parameters_schema": {},
            "parameterized_steps": [{"action": "click"}]
        }
        # Mirror copy at root
        mirror_file = Path(tmpdir) / "synthesized_skill.json"
        mirror_file.write_text(json.dumps(skill_primary), encoding="utf-8")
        (skills_dir / "flipkart_search.json").write_text(json.dumps(skill_primary), encoding="utf-8")

        # Load skills
        loaded = load_local_skills(skills_dir=skills_dir, root_dir=Path(tmpdir))
        # Should only contain 1 copy of "Flipkart Search"
        names = [s.get("skill_name") for s in loaded]
        assert names.count("Flipkart Search") == 1


def test_skill_execute_payload_schema():
    """Validates that SkillExecutePayload accepts and validates a filename string."""
    payload = SkillExecutePayload(filename="flipkart_search.json", parameters={"query": "shoes"})
    assert payload.filename == "flipkart_search.json"
    assert payload.parameters == {"query": "shoes"}

    # Default fallback
    default_payload = SkillExecutePayload()
    assert default_payload.filename == "synthesized_skill.json"


def test_run_skill_cli_resolution():
    """Validates run_skill path resolution supports explicit sys.argv[1] or default fallback."""
    import sys
    playwright_dir = str(Path(__file__).resolve().parent.parent / "webai_playwright_python")
    if playwright_dir not in sys.path:
        sys.path.insert(0, playwright_dir)
    from run_skill import resolve_skill_path
    
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        custom_file = skills_dir / "custom.json"
        custom_file.write_text("{}", encoding="utf-8")
        default_file = Path(tmpdir) / "synthesized_skill.json"
        default_file.write_text("{}", encoding="utf-8")

        # Explicit path
        assert resolve_skill_path(str(custom_file), base_dir=tmpdir) == str(custom_file)
        # Basename in skills/
        assert resolve_skill_path("custom.json", base_dir=tmpdir) == str(custom_file)
        # Omitted / None falls back to default synthesized_skill.json
        assert resolve_skill_path(None, base_dir=tmpdir) == str(default_file)
