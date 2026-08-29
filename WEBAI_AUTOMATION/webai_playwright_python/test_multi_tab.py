import pytest
from unittest.mock import AsyncMock, MagicMock
from webai_playwright.ai import _execute_command

@pytest.mark.asyncio
async def test_execute_command_uses_active_page_from_context():
    # Setup initial page and second tab
    page1 = MagicMock()
    page1.url = "https://example.com/tab1"

    page2 = MagicMock()
    page2.url = "https://example.com/tab2"

    cdp_session = AsyncMock()
    context = MagicMock()
    context.new_cdp_session = AsyncMock(return_value=cdp_session)
    context.pages = [page1, page2]

    page1.context = context
    page2.context = context

    # Test verifyUrl command which checks active_page.url
    command = {"name": "verifyUrl", "arguments": {"contains": "tab2"}}
    res = await _execute_command(page1, command)

    # Should return True because page2's URL contains 'tab2'
    assert res is True

@pytest.mark.asyncio
async def test_execute_command_fallback_single_page():
    page = MagicMock()
    page.url = "https://example.com/single"
    page.context = None

    command = {"name": "verifyUrl", "arguments": {"contains": "single"}}
    res = await _execute_command(page, command)

    assert res is True
