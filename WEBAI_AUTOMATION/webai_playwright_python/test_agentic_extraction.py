"""
Unit tests for Agentic Tool Use Data Extraction in client layer.
Tests extract_text, extract_table, and ai._dispatch_command routing.
"""
import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Add webai_playwright_python to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import webai_playwright.playwright_actions as pw
from webai_playwright.ai import _dispatch_command


@pytest.mark.asyncio
async def test_extract_text_target_resolution():
    """Verify extract_text resolves different target shapes into locators."""
    mock_page = MagicMock()

    with patch("webai_playwright.playwright_actions.extract_with_fallback", new_callable=AsyncMock) as mock_extract:
        mock_extract.return_value = "Extracted Course Title"

        # 1. Target by text
        res = await pw.extract_text(mock_page, {"by": "text", "text": "Programmes Offered"})
        assert res == "Extracted Course Title"
        mock_extract.assert_called_once()
        locators = mock_extract.call_args[0][1]
        assert locators[0]["type"] == "text"
        assert locators[0]["value"] == "Programmes Offered"

        mock_extract.reset_mock()

        # 2. Target by role
        res2 = await pw.extract_text(mock_page, {"by": "role", "role": "heading", "name": "Admissions"})
        assert res2 == "Extracted Course Title"
        locators2 = mock_extract.call_args[0][1]
        assert locators2[0]["type"] == "role"
        assert locators2[0]["value"] == "heading"
        assert locators2[0]["name"] == "Admissions"

        mock_extract.reset_mock()

        # 3. Target as string
        res3 = await pw.extract_text(mock_page, "div.course-details")
        assert res3 == "Extracted Course Title"
        locators3 = mock_extract.call_args[0][1]
        assert locators3[0]["type"] == "css"
        assert locators3[0]["value"] == "div.course-details"


@pytest.mark.asyncio
async def test_extract_table_target_resolution():
    """Verify extract_table resolves table selector and delegates to extract_table_data."""
    mock_page = MagicMock()
    mock_locator = MagicMock()
    mock_page.locator.return_value = mock_locator

    with patch("webai_playwright.playwright_actions.extract_table_data", new_callable=AsyncMock) as mock_extract_table:
        mock_extract_table.return_value = {
            "success": True,
            "data": [{"Course": "B.Tech", "Duration": "4 Years"}],
            "row_count": 1,
        }

        # 1. Target with css selector
        res = await pw.extract_table(mock_page, {"by": "css", "selector": "table#ug-courses"})
        assert res["success"] is True
        assert res["row_count"] == 1
        mock_extract_table.assert_called_once()
        # First positional argument should be the resolved Locator
        assert mock_extract_table.call_args[0][0] == mock_locator
        assert mock_extract_table.call_args[1]["table_selector"] == "table#ug-courses"

        mock_extract_table.reset_mock()

        # 2. Target as string
        res2 = await pw.extract_table(mock_page, "table.programmes")
        assert res2["success"] is True
        assert mock_extract_table.call_args[0][0] == mock_locator
        assert mock_extract_table.call_args[1]["table_selector"] == "table.programmes"


@pytest.mark.asyncio
async def test_extract_table_data_with_locator():
    """Verify fallback_helpers.extract_table_data evaluates directly on a Locator element without document.querySelector."""
    mock_locator = MagicMock()
    del mock_locator.goto
    # Mock locator.first.evaluate
    mock_locator.first.evaluate = AsyncMock(return_value={
        "success": True,
        "data": [{"Course": "B.Tech"}],
        "row_count": 1,
    })

    from webai_playwright.fallback_helpers import extract_table_data
    result = await extract_table_data(mock_locator)
    assert result["success"] is True
    assert result["row_count"] == 1
    mock_locator.first.evaluate.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_command_extract_text_and_table():
    """Verify _dispatch_command routes extract_text and extract_table commands."""
    mock_page = MagicMock()

    with patch("webai_playwright.playwright_actions.extract_text", new_callable=AsyncMock) as mock_extract_text, \
         patch("webai_playwright.playwright_actions.extract_table", new_callable=AsyncMock) as mock_extract_table:

        mock_extract_text.return_value = "Hello World"
        mock_extract_table.return_value = {"success": True, "data": [{"col1": "val1"}], "row_count": 1}

        # Command: extract_text
        cmd_text = {
            "name": "extract_text",
            "arguments": {"target": {"by": "text", "text": "Welcome"}}
        }
        res_text = await _dispatch_command(mock_page, cmd_text)
        assert res_text == "Hello World"
        mock_extract_text.assert_called_once()

        # Command: extract_table
        cmd_table = {
            "name": "extract_table",
            "arguments": {"target": {"by": "css", "selector": "table"}}
        }
        res_table = await _dispatch_command(mock_page, cmd_table)
        assert res_table["success"] is True
        assert res_table["row_count"] == 1
        mock_extract_table.assert_called_once()
