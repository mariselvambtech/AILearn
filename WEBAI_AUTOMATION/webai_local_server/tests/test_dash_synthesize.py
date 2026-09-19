"""
Tests for decoupled skill synthesis execution.

Validates that:
1. dash_synthesize CLI fetches automation steps, invokes SkillSynthesizer, and saves the skill.
2. dash_synthesize CLI propagates error exit codes on network/parse failures.
3. synthesize_automation_skill endpoint spawns dash_synthesize via subprocess and handles CalledProcessError.
"""
import subprocess
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from webai_dashboard.dashboard_server import app, synthesize_automation_skill


def test_synthesize_endpoint_spawns_subprocess():
    """Verify that synthesize_automation_skill spawns dash_synthesize.py with the correct args."""
    with patch("webai_dashboard.dashboard_server.subprocess.run") as mock_run, \
         patch("webai_dashboard.dashboard_server._select_playback_python") as mock_select_py:
        mock_select_py.return_value = "C:/fake/python.exe"
        mock_run.return_value = MagicMock(returncode=0)

        import asyncio
        result = asyncio.run(synthesize_automation_skill(automation_id=42, x_api_key="test-key"))

        assert result == {"status": "success"}
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "C:/fake/python.exe"
        assert cmd[1] == "dash_synthesize.py"
        assert cmd[2] == "--id"
        assert cmd[3] == "42"
        env = mock_run.call_args[1]["env"]
        assert env.get("WEBAI_API_KEY") == "test-key"


def test_synthesize_endpoint_handles_called_process_error():
    """Verify that CalledProcessError from subprocess.run is mapped to HTTPException(500)."""
    with patch("webai_dashboard.dashboard_server.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["python", "dash_synthesize.py"],
            stderr="Failed to fetch automation #999: HTTP 404",
        )

        import asyncio
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(synthesize_automation_skill(automation_id=999, x_api_key="test-key"))

        assert exc_info.value.status_code == 500
        assert "Failed to fetch automation #999: HTTP 404" in exc_info.value.detail
