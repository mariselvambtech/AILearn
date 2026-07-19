from __future__ import annotations

import asyncio
import json
from typing import Any, Awaitable, Callable, Dict, Optional

import websockets

from .config import LOGS_ENABLED, websocket_url

_ws: Optional[Any] = None
_ws_lock = asyncio.Lock()


class WebAIAuthError(RuntimeError):
    """Raised when the WebSocket server rejects authentication."""
    pass


def _is_ws_closed(ws: Any) -> bool:
    """
    websockets API varies by version:
    - older: ws.closed (bool)
    - newer: ws.close_code (None if open) and/or ws.state
    This function normalizes "is closed?" across versions.
    """
    if ws is None:
        return True

    # websockets <= 11
    if hasattr(ws, "closed"):
        try:
            return bool(ws.closed)
        except Exception:
            pass

    # websockets >= 12 typically has close_code
    if hasattr(ws, "close_code"):
        try:
            return ws.close_code is not None
        except Exception:
            pass

    # some versions expose state
    if hasattr(ws, "state"):
        try:
            # state may be an enum with name "OPEN"/"CLOSED"
            name = getattr(ws.state, "name", str(ws.state))
            return str(name).upper() == "CLOSED"
        except Exception:
            pass

    # fallback: assume it's open if we can't prove it's closed
    return False


async def get_ws() -> Any:
    global _ws
    async with _ws_lock:
        if _ws and not _is_ws_closed(_ws):
            return _ws

        url = websocket_url()

        try:
            _ws = await websockets.connect(url, max_size=None)
        except websockets.exceptions.InvalidStatusCode as e:
            if getattr(e, "status_code", None) == 401:
                raise WebAIAuthError(
                    "Authentication failed. Make sure TOKEN / AI_TOKEN is set correctly."
                ) from e
            raise

        return _ws


async def close_ws() -> None:
    global _ws
    async with _ws_lock:
        if _ws and not _is_ws_closed(_ws):
            await _ws.close()
        _ws = None


async def send_message(message: Dict[str, Any]) -> None:
    ws = await get_ws()
    data = json.dumps(message)
    if LOGS_ENABLED:
        print("> ws send:", data[:250])
    await ws.send(data)


async def listen(task_id: str, handler: Callable[[Dict[str, Any]], Awaitable[bool]]) -> None:
    """
    Listen for messages, passing each message to handler.
    If handler returns True, stop listening.
    """
    ws = await get_ws()
    async for raw in ws:
        parsed = json.loads(raw)
        if LOGS_ENABLED and parsed.get("taskId") == task_id:
            print("< ws recv:", json.dumps(parsed)[:250])
        stop = await handler(parsed)
        if stop:
            break
