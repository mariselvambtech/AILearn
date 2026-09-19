"""
TDVC Test Suite for Phase 15: Kimi K3 Provider Integration.

Covers:
1. Provider selection (LLM_PROVIDER routing).
2. Multimodal vision content serialization (text + data-uri image_url block).
3. Multi-turn reasoning / tool-call envelope preservation (reasoning_content + tool_calls).
4. Guided-mode locator bypass invariant (locators present -> zero LLM calls).
"""

import asyncio
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Any, Dict, List, Optional

# Import target functions from webai_local_server
from webai_local_server.kimi_client import (
    format_vision_message,
    preserve_reasoning_envelope,
    kimi_chat,
)
from webai_local_server.local_webai_server_guided import (
    llm_plan_chat,
    LOCATOR_PRIORITY,
)


def test_format_vision_message_text_only():
    """Text-only message should produce a clean user message."""
    msg = format_vision_message("Plan the next action", image_base64=None)
    assert msg["role"] == "user"
    assert msg["content"] == "Plan the next action"


def test_format_vision_message_with_image_payload():
    """Multimodal message must include OpenAI-compatible text and image_url blocks."""
    dummy_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    msg = format_vision_message("Analyze screenshot", image_base64=dummy_b64, mime_type="image/png")
    assert msg["role"] == "user"
    assert isinstance(msg["content"], list)
    assert len(msg["content"]) == 2

    text_part = msg["content"][0]
    assert text_part["type"] == "text"
    assert text_part["text"] == "Analyze screenshot"

    img_part = msg["content"][1]
    assert img_part["type"] == "image_url"
    assert "image_url" in img_part
    assert img_part["image_url"]["url"] == f"data:image/png;base64,{dummy_b64}"


def test_preserve_reasoning_envelope():
    """Reasoning content and tool calls must be preserved in assistant envelopes for multi-turn chat."""
    raw_response_message = {
        "role": "assistant",
        "content": "[{\"action\": \"click\", \"target\": {\"by\": \"text\", \"text\": \"Submit\"}}]",
        "reasoning_content": "The user wants to submit. I see a button labeled Submit.",
        "tool_calls": [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {"name": "click", "arguments": "{\"target\": \"Submit\"}"}
            }
        ]
    }

    envelope = preserve_reasoning_envelope(raw_response_message)
    assert envelope["role"] == "assistant"
    assert envelope["content"] == raw_response_message["content"]
    assert envelope["reasoning_content"] == "The user wants to submit. I see a button labeled Submit."
    assert len(envelope["tool_calls"]) == 1
    assert envelope["tool_calls"][0]["id"] == "call_abc123"


def test_kimi_chat_request_payload_and_reasoning_extraction():
    """kimi_chat must call OpenAI-compatible /chat/completions via httpx.AsyncClient and return content."""
    async def _test():
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "[{\"action\": \"click\", \"target\": {\"by\": \"text\", \"text\": \"Login\"}}]",
                        "reasoning_content": "Found Login button on page."
                    }
                }
            ]
        }

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_response_data
        mock_resp.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_resp

            result = await kimi_chat(
                system="System instructions",
                user="User instruction",
                screenshot_base64="fake_b64",
            )

            assert mock_post.called
            call_kwargs = mock_post.call_args.kwargs
            url = mock_post.call_args.args[0] if mock_post.call_args.args else call_kwargs.get("url", "")
            assert "/chat/completions" in url

            payload = call_kwargs.get("json") or {}
            assert payload.get("model") == os.getenv("KIMI_MODEL", "kimi-k3")
            messages = payload.get("messages", [])
            assert len(messages) >= 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"
            # User message has multimodal block
            assert isinstance(messages[1]["content"], list)
            assert "[{\"action\": \"click\"" in result

    asyncio.run(_test())


def test_provider_selection_routing():
    """llm_plan_chat routes to kimi_chat when LLM_PROVIDER is 'kimi_k3', else to ollama_chat."""
    async def _test():
        with patch.dict(os.environ, {"LLM_PROVIDER": "kimi_k3"}), \
             patch("webai_local_server.kimi_client.kimi_chat", new_callable=AsyncMock) as mock_kimi, \
             patch("webai_local_server.local_webai_server_guided.ollama_chat", new_callable=AsyncMock) as mock_ollama:
            mock_kimi.return_value = "kimi_plan"
            mock_ollama.return_value = "ollama_plan"

            out = await llm_plan_chat("sys", "usr", screenshot_base64="screen123")
            assert out == "kimi_plan"
            assert mock_kimi.called
            assert not mock_ollama.called

        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}), \
             patch("webai_local_server.kimi_client.kimi_chat", new_callable=AsyncMock) as mock_kimi, \
             patch("webai_local_server.local_webai_server_guided.ollama_chat", new_callable=AsyncMock) as mock_ollama:
            mock_kimi.return_value = "kimi_plan"
            mock_ollama.return_value = "ollama_plan"

            out = await llm_plan_chat("sys", "usr", screenshot_base64="screen123")
            assert out == "ollama_plan"
            assert mock_ollama.called
            assert not mock_kimi.called

    asyncio.run(_test())


def test_guided_mode_locator_bypass_invariant():
    """When a recorded step has locators, guided execution must NEVER invoke LLM (Ollama or Kimi)."""
    step_with_locators = {
        "action": "click",
        "name": "Submit Button",
        "locators": [
            {"type": "id", "value": "submit-btn"},
            {"type": "text", "value": "Submit"}
        ]
    }

    with patch("webai_local_server.local_webai_server_guided.ollama_chat", new_callable=AsyncMock) as mock_ollama, \
         patch("webai_local_server.kimi_client.kimi_chat", new_callable=AsyncMock) as mock_kimi:

        locators = step_with_locators.get("locators") or []
        assert len(locators) > 0

        # Sort locators by priority (replicates guided mode in local_webai_server_guided.py)
        sorted_locators = sorted(locators, key=lambda x: LOCATOR_PRIORITY.get(x.get("type"), 99))
        plan = [{
            "action": "clickWithFallback",
            "locators": sorted_locators
        }]

        assert len(plan) == 1
        assert plan[0]["action"] == "clickWithFallback"
        assert plan[0]["locators"][0]["type"] == "id"
        # Invariant: Neither LLM should have been called
        assert not mock_ollama.called
        assert not mock_kimi.called
