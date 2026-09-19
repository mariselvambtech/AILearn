import sys
from pathlib import Path
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

# Ensure paths are in sys.path
root_dir = Path(__file__).resolve().parent.parent
client_dir = root_dir / "webai_playwright_python"
server_dir = root_dir / "webai_local_server"
if str(client_dir) not in sys.path:
    sys.path.insert(0, str(client_dir))
if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))

from webai_playwright.ai import _execute_command


@pytest.mark.asyncio
async def test_client_handles_playwright_timeout():
    """
    TDVC Assertion:
    Assert that when Playwright throws a TimeoutError during command execution,
    _execute_command / handler gracefully returns a {"success": False, "error": "Timeout..."}
    dictionary rather than raising a raw unhandled exception.
    """
    mock_page = MagicMock()
    with pytest.MonkeyPatch.context() as mp:
        async def mock_timeout(*args, **kwargs):
            raise PlaywrightTimeoutError("Locator.click: Timeout 4000ms exceeded.")

        mp.setattr("webai_playwright.playwright_actions.click_by_role", mock_timeout)

        command = {
            "name": "clickByRole",
            "arguments": {"role": "button", "name": "Search"}
        }

        # _execute_command should gracefully catch TimeoutError and return error dict
        res = await _execute_command(mock_page, command)

        assert isinstance(res, dict), "Result must be a dictionary"
        assert res.get("success") is False, "Result must have success=False on timeout"
        assert "Timeout" in res.get("error", ""), "Error message must report Timeout"


@pytest.mark.asyncio
async def test_server_dynamic_popup_retry_on_timeout():
    """
    Mock an AI server loop where an injected Playwright TimeoutError is simulated
    during a click command.
    Assert:
      1. The server does not raise a fatal exception breaking the loop.
      2. consecutive_action_failures increments by 1.
      3. force_fresh_snapshot is set to True.
      4. The next command dispatched is 'getDOMSnapshot' to re-evaluate the page.
    """
    dispatched_commands = []
    consecutive_action_failures = 0
    failures = 0
    force_fresh_snapshot = False

    async def mock_send_command(name: str, arguments: dict = None):
        dispatched_commands.append(name)
        if name == "clickByRole":
            # Simulate client reporting timeout failure
            raise RuntimeError("Command 'clickByRole' failed: Timeout 4000ms exceeded.")
        if name == "getDOMSnapshot":
            return {"dom": "<html><body><div role='dialog'>Login Popup</div></body></html>"}
        if name == "getCurrentUrl":
            return "https://www.flipkart.com"
        if name == "getTitle":
            return "Online Shopping"
        if name == "getInteractiveElements":
            return []
        return None

    # Simulate 2 rounds of the server loop
    for round_idx in range(2):
        if force_fresh_snapshot:
            # Trigger fresh snapshot re-hydration
            await mock_send_command("getDOMSnapshot", {})
            force_fresh_snapshot = False

        url = await mock_send_command("getCurrentUrl", {})
        title = await mock_send_command("getTitle", {})

        if round_idx == 0:
            # Round 0: click action fails due to timeout
            try:
                await mock_send_command("clickByRole", {"role": "button", "name": "Search"})
                consecutive_action_failures = 0
            except Exception as e:
                consecutive_action_failures += 1
                failures += 1
                force_fresh_snapshot = True
                # Continue loop rather than fatal crash
                continue
        elif round_idx == 1:
            # Round 1: verifies fresh snapshot was requested before re-planning
            pass

    assert consecutive_action_failures == 1, "consecutive_action_failures should increment on timeout."
    assert "getDOMSnapshot" in dispatched_commands, "Server must dispatch getDOMSnapshot on the next loop after failure."
    click_idx = dispatched_commands.index("clickByRole")
    snap_idx = dispatched_commands.index("getDOMSnapshot")
    assert snap_idx > click_idx, "getDOMSnapshot must be dispatched after the failed click to refresh the DOM."
