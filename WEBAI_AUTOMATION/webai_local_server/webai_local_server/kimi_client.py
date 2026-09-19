"""
Kimi K3 Provider Client Module.

Provides an OpenAI-compatible async HTTP client for Kimi K3 / Moonshot AI
supporting text, multi-turn reasoning traces (reasoning_content), tool-calls,
and multimodal visual-DOM screenshot payloads using httpx.AsyncClient.
"""

import os
import logging
from typing import Any, Dict, List, Optional
import httpx

logger = logging.getLogger("webai_kimi")


def _get_env(name: str, default: str = "") -> str:
    """Read an environment variable with a default fallback."""
    val = os.getenv(name)
    return default if val is None or val == "" else val


def format_vision_message(
    text: str,
    image_base64: Optional[str] = None,
    mime_type: str = "image/jpeg"
) -> Dict[str, Any]:
    """
    Construct an OpenAI-compatible user message dictionary.
    
    If image_base64 is provided, formats as multimodal content containing
    both text and image_url blocks. Otherwise returns a standard text content message.
    """
    if not image_base64:
        return {"role": "user", "content": text}

    # Normalize data URI if prefix was already present
    clean_b64 = image_base64
    if clean_b64.startswith("data:"):
        # already full data uri
        img_url = clean_b64
    else:
        img_url = f"data:{mime_type};base64,{clean_b64}"

    return {
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {
                "type": "image_url",
                "image_url": {
                    "url": img_url
                }
            }
        ]
    }


def preserve_reasoning_envelope(response_message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preserve reasoning content and tool calls from an assistant response for multi-turn chat.
    
    Kimi K3 and OpenAI-compatible reasoning models emit reasoning_content and tool_calls
    which must be preserved in conversational turns to maintain contextual reasoning fidelity.
    """
    envelope: Dict[str, Any] = {
        "role": response_message.get("role", "assistant"),
        "content": response_message.get("content") or "",
    }
    reasoning = response_message.get("reasoning_content") or response_message.get("reasoning")
    if reasoning is not None:
        envelope["reasoning_content"] = reasoning
    if "tool_calls" in response_message and response_message["tool_calls"] is not None:
        envelope["tool_calls"] = response_message["tool_calls"]
    return envelope


async def kimi_chat(
    system: str,
    user: str,
    screenshot_base64: Optional[str] = None,
    history: Optional[List[Dict[str, Any]]] = None
) -> str:
    """
    Perform an asynchronous chat completion against the Kimi K3 provider.
    
    Args:
        system: System instructions or base prompt.
        user: User prompt text.
        screenshot_base64: Optional base64-encoded image string for visual reasoning.
        history: Optional list of previous conversation turns (with envelopes preserved).
        
    Returns:
        The content string produced by the assistant.
    """
    api_key = _get_env("KIMI_API_KEY") or _get_env("MOONSHOT_API_KEY")
    base_url = _get_env("KIMI_BASE_URL", "https://api.moonshot.cn/v1").rstrip("/")
    model = _get_env("KIMI_MODEL", "kimi-k3")
    temperature = float(_get_env("KIMI_TEMPERATURE", "0.2"))
    timeout = float(_get_env("KIMI_TIMEOUT", "60.0"))
    max_tokens = int(_get_env("KIMI_MAX_TOKENS", "2048"))

    endpoint = f"{base_url}/chat/completions"

    headers: Dict[str, str] = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    else:
        logger.warning("⚠️ KIMI_API_KEY is not set. Requests to Kimi K3 may fail authentication.")

    messages: List[Dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})

    if history:
        for turn in history:
            messages.append(turn)

    # Format user message with vision attachment if screenshot is supplied
    messages.append(format_vision_message(user, image_base64=screenshot_base64))

    payload: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(endpoint, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        choices = data.get("choices") or []
        if not choices:
            logger.error("❌ Kimi K3 returned no choices in response.")
            return ""

        first_choice = choices[0].get("message") or {}
        content = first_choice.get("content") or ""
        reasoning = first_choice.get("reasoning_content") or first_choice.get("reasoning")

        if reasoning:
            logger.info(f"🧠 [Kimi K3 Reasoning Trace]: {str(reasoning)[:250]}...")

        return content

    except httpx.HTTPStatusError as err:
        logger.error(f"❌ Kimi K3 HTTP error {err.response.status_code}: {err.response.text}")
        raise
    except Exception as exc:
        logger.error(f"❌ Kimi K3 request failed: {exc}")
        raise
