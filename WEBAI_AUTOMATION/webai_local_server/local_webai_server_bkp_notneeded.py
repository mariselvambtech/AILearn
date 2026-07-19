import asyncio
import json
import urllib.parse
from typing import Any, Dict, Optional

import websockets


def jdump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False)


def get_request_path(ws: Any) -> str:
    """
    websockets API differs:
    - older: ws.path
    - newer: ws.request.path
    """
    if hasattr(ws, "path"):
        return ws.path
    req = getattr(ws, "request", None)
    if req and hasattr(req, "path"):
        return req.path
    return "/api"


def get_query_param(path: str, key: str) -> Optional[str]:
    parsed = urllib.parse.urlparse(path)
    qs = urllib.parse.parse_qs(parsed.query)
    vals = qs.get(key)
    return vals[0] if vals else None


async def handle_client(ws: Any):
    path = get_request_path(ws)
    client_key = get_query_param(path, "key")
    print(f"✅ Client connected: {path} | key={'(none)' if not client_key else client_key}")

    task_id = None
    command_index = 0

    async def recv_json() -> Dict[str, Any]:
        raw = await ws.recv()
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", errors="replace")
        return json.loads(raw)

    async def send_json(msg: Dict[str, Any]) -> None:
        await ws.send(jdump(msg))

    async def send_command(name: str, arguments: Dict[str, Any]) -> Any:
        nonlocal command_index, task_id

        await send_json({
            "type": "command-request",
            "taskId": task_id,
            "index": command_index,
            "name": name,
            "arguments": arguments,
        })
        command_index += 1

        # Wait for matching command-response
        while True:
            resp = await recv_json()
            if resp.get("type") == "command-response" and resp.get("taskId") == task_id:
                result = resp.get("result")
                if result and result != "null":
                    try:
                        return json.loads(result)
                    except Exception:
                        return result
                return None

    try:
        # 1) Expect task-start first
        start_msg = await recv_json()
        if start_msg.get("type") != "task-start":
            await send_json({
                "type": "task-complete",
                "taskId": start_msg.get("taskId", "unknown"),
                "success": False,
                "error": "Expected task-start first"
            })
            return

        task_id = start_msg["taskId"]
        task_text = start_msg.get("task", "")
        print(f"📩 task-start taskId={task_id}")
        print(f"📝 task: {task_text}")

        # --- Google search workflow (deterministic baseline) ---
        # Find the search box
        elements = await send_command("findElements", {
            "using": "css selector",
            "value": 'textarea[name="q"], input[name="q"]'
        })

        if not elements:
            await send_json({
                "type": "task-complete",
                "taskId": task_id,
                "success": False,
                "error": "Could not find Google search box"
            })
            return

        # element id is stored under a webdriver key: {"element-6066-...": "<id>"}
        first = elements[0]
        element_key = next(iter(first.keys()))
        element_id = first[element_key]

        # Click box, type, press Enter
        await send_command("clickElement", {"id": element_id})
        await send_command("sendKeysToElement", {"id": element_id, "text": "weather today"})
        await send_command("keypressEnter", {})

        await send_json({
            "type": "task-complete",
            "taskId": task_id,
            "success": True,
            "summary": "Searched 'weather today' on Google"
        })
        print("✅ task-complete sent")

    except Exception as e:
        # THIS is what was likely causing your 1011 error previously
        print("❌ Server crashed with error:", repr(e))
        try:
            if task_id:
                await send_json({
                    "type": "task-complete",
                    "taskId": task_id,
                    "success": False,
                    "error": str(e),
                })
        except Exception:
            pass


async def main():
    host = "localhost"
    port = 8765
    print(f"✅ Local AI WebSocket server: ws://{host}:{port}/api")

    # max_size=None avoids disconnects if the client sends a big snapshot
    async with websockets.serve(handle_client, host, port, max_size=None):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
