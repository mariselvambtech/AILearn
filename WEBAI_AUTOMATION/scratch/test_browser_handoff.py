"""
TDVC Test Suite for Phase 7: The Browser Handoff Engine (Rule 7)
Verifies:
1. Browser teardown (page.close) is safely bypassed when keep_alive=True.
2. A WebSocket 'task-start' payload is emitted with handoff_intent and current page.url.
3. SkillExecutor returns status='handoff' and keep_alive=True.
"""
import os
import sys
import asyncio
from unittest.mock import AsyncMock, patch

# Ensure local packages are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python")))

from webai_playwright.skill_executor import SkillExecutor


class MockKeyboard:
    async def press(self, key: str):
        pass


class MockPage:
    def __init__(self, url: str = "https://www.flipkart.com/search?q=shirt"):
        self.url = url
        self.keyboard = MockKeyboard()
        self.close_called = False

    async def goto(self, url: str, wait_until: str = None):
        self.url = url

    async def content(self):
        return "<html><body>Mock Page Content</body></html>"

    async def close(self):
        self.close_called = True


async def test_browser_handoff_lifecycle():
    print("\n--- Running TDVC Test: Browser Handoff Lifecycle ---")

    # 1. Mock Skill Recipe
    sample_skill = {
        "skill_name": "Flipkart Search",
        "description": "Searches for shirts on Flipkart",
        "parameters_schema": {},
        "parameterized_steps": [
            {"action": "goto", "url": "https://www.flipkart.com"}
        ]
    }

    executor = SkillExecutor(sample_skill)
    mock_page = MockPage()

    # 2. Patch WebSocket send_message
    sent_messages = []

    async def mock_send_message(msg):
        sent_messages.append(msg)

    with patch("webai_playwright.websocket_client.send_message", side_effect=mock_send_message):
        # 3. Execute skill with keep_alive=True and handoff_intent
        handoff_intent = "Add to cart and checkout"
        result = await executor.execute_skill(
            mock_page,
            keep_alive=True,
            handoff_intent=handoff_intent
        )

        print(f"Execution Result Status: {result.get('status')}")
        print(f"Keep Alive Flag: {result.get('keep_alive')}")
        print(f"Handoff Intent: {result.get('handoff_intent')}")
        print(f"Sent WS Messages Count: {len(sent_messages)}")

        # 4. Assertions
        assert mock_page.close_called is False, "page.close() MUST NOT be called when keep_alive=True!"
        assert result.get("status") == "handoff", f"Expected status 'handoff', got '{result.get('status')}'"
        assert result.get("keep_alive") is True, "Expected keep_alive=True in result!"
        assert result.get("handoff_intent") == handoff_intent, "Handoff intent mismatch in result!"

        assert len(sent_messages) == 1, f"Expected 1 WebSocket message emitted, got {len(sent_messages)}"
        ws_msg = sent_messages[0]
        assert ws_msg.get("type") == "task-start", f"Expected WS message type 'task-start', got '{ws_msg.get('type')}'"
        assert ws_msg.get("task") == handoff_intent, f"Expected task '{handoff_intent}', got '{ws_msg.get('task')}'"
        assert ws_msg.get("url") == "https://www.flipkart.com", f"Expected URL 'https://www.flipkart.com', got '{ws_msg.get('url')}'"

    print("[PASS] test_browser_handoff_lifecycle completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_browser_handoff_lifecycle())
    print("\n[SUCCESS] ALL TDVC BROWSER HANDOFF TESTS PASSED!")
