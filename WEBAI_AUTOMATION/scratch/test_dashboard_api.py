"""
TDVC Test Harness for WebAI Dashboard Skill Management API Endpoints.
Uses FastAPI's TestClient to verify GET /api/skills and POST /api/skills/execute
before updating server routes or UI assets.
"""
from __future__ import annotations

import os
import sys

# Ensure import paths for webai_local_server and webai_playwright_python modules
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOCAL_SERVER_DIR = os.path.join(REPO_ROOT, "webai_local_server")
PLAYWRIGHT_DIR = os.path.join(REPO_ROOT, "webai_playwright_python")

for p in [LOCAL_SERVER_DIR, PLAYWRIGHT_DIR, REPO_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient
from webai_dashboard.dashboard_server import app

client = TestClient(app)


def test_list_skills_endpoint():
    print(" [1/2] Testing GET /api/skills endpoint...")
    response = client.get("/api/skills")
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    skills = response.json()
    assert isinstance(skills, list), f"Expected list of skills, got {type(skills)}"
    assert len(skills) > 0, "No skills returned from GET /api/skills"
    
    first_skill = skills[0]
    assert "skill_name" in first_skill, "Missing 'skill_name' in skill record"
    assert "parameters_schema" in first_skill, "Missing 'parameters_schema' in skill record"
    print(f"   GET /api/skills PASSED: Found {len(skills)} skill(s). Skill name: '{first_skill['skill_name']}'")


def test_execute_skill_endpoint():
    print(" [2/2] Testing POST /api/skills/execute endpoint...")
    payload = {
        "skill_id": "synthesized_skill",
        "parameters": {"search_query": "Kerala"}
    }
    response = client.post("/api/skills/execute", json=payload)
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    result = response.json()
    assert "status" in result, "Missing 'status' in execute response"
    assert result["status"] in ("success", "running"), f"Unexpected status: {result['status']}"
    print(f"   POST /api/skills/execute PASSED: Status = '{result['status']}'")


if __name__ == "__main__":
    test_list_skills_endpoint()
    test_execute_skill_endpoint()
    print("\n SUCCESS: All Dashboard API endpoint assertions PASSED!")
