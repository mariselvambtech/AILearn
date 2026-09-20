"""
Unit and integration tests for DELETE /api/skills/{slug} endpoint in dashboard_server.py.
"""
import json
import os
import shutil
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from webai_dashboard.dashboard_server import app, CLIENT_DIR

client = TestClient(app)


@pytest.fixture
def mock_skill_environment(monkeypatch, tmp_path):
    """Sets up a temporary skills directory and points CLIENT_DIR to tmp_path."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Monkeypatch CLIENT_DIR in dashboard_server module
    import webai_dashboard.dashboard_server as ds
    monkeypatch.setattr(ds, "CLIENT_DIR", tmp_path)

    # Create dummy skill artifacts
    slug = "test_delete_skill"
    skill_file = skills_dir / f"{slug}.json"
    skill_file.write_text(
        json.dumps({
            "skill_name": "Test Delete Skill",
            "description": "A temporary skill for deletion testing",
            "parameterized_steps": [{"action": "open", "url": "https://example.com"}]
        }),
        encoding="utf-8"
    )

    slug_dir = skills_dir / slug
    slug_dir.mkdir(parents=True, exist_ok=True)
    recorded_steps_file = slug_dir / "recorded_steps.json"
    recorded_steps_file.write_text(
        json.dumps([{"action": "open", "url": "https://example.com"}]),
        encoding="utf-8"
    )

    registry_file = skills_dir / "skills_registry.json"
    registry_file.write_text(
        json.dumps([
            {
                "skill_name": "Test Delete Skill",
                "slug": slug,
                "description": "A temporary skill for deletion testing",
                "skill_file": f"{slug}.json",
                "recorded_steps": f"{slug}/recorded_steps.json"
            },
            {
                "skill_name": "Keep This Skill",
                "slug": "keep_this_skill",
                "description": "Should remain untouched",
                "skill_file": "keep_this_skill.json",
                "recorded_steps": "keep_this_skill/recorded_steps.json"
            }
        ]),
        encoding="utf-8"
    )

    return {
        "tmp_path": tmp_path,
        "skills_dir": skills_dir,
        "slug": slug,
        "skill_file": skill_file,
        "slug_dir": slug_dir,
        "registry_file": registry_file
    }


def test_delete_skill_success(mock_skill_environment):
    """Verify DELETE /api/skills/{slug} removes files, directory, and registry entry."""
    env = mock_skill_environment
    slug = env["slug"]

    assert env["skill_file"].exists()
    assert env["slug_dir"].is_dir()

    resp = client.delete(f"/api/skills/{slug}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["slug"] == slug

    # Verify disk deletions
    assert not env["skill_file"].exists()
    assert not env["slug_dir"].exists()

    # Verify registry unregistration
    registry_data = json.loads(env["registry_file"].read_text(encoding="utf-8"))
    assert len(registry_data) == 1
    assert registry_data[0]["slug"] == "keep_this_skill"


def test_delete_skill_not_found(mock_skill_environment):
    """Verify deleting a non-existent skill returns 404."""
    resp = client.delete("/api/skills/non_existent_slug_123")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_delete_skill_invalid_slug(mock_skill_environment):
    """Verify invalid slugs with illegal characters are rejected with 400."""
    resp = client.delete("/api/skills/invalid;slug!chars")
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()

