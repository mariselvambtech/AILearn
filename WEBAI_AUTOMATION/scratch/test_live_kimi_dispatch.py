# scratch/test_live_kimi_dispatch.py
import asyncio
import sys
import websockets
import json

# Force UTF-8 stream output to prevent Windows cp1252 emoji crash
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")


async def test_freeform_kimi_dispatch():
    uri = "ws://localhost:8765/api?key=local-dev"
    print(f"Connecting to AI Server at {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            # 1x1 dummy jpeg base64
            tiny_jpg_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
            task_id = "diag_kimi_test_01"

            task_payload = {
                "type": "task-start",
                "taskId": task_id,
                "task": "Freeform test: click on the Login button",
                "snapshot": {
                    "url": "https://example.com",
                    "title": "Example Domain",
                    "screenshot": tiny_jpg_b64,
                    "interactiveElements": [
                        {"tag": "button", "text": "Login", "type": "button", "role": "button"}
                    ]
                },
                "options": {
                    "recorded_steps": []  # Empty forces freeform LLM planning loop!
                }
            }

            print("📤 Sending freeform task-start payload to AI server (port 8765)...")
            await ws.send(json.dumps(task_payload))

            # Simulate client event loop: respond to inspect commands (getCurrentUrl, getTitle, getInteractiveElements)
            for round_num in range(10):
                try:
                    raw_msg = await asyncio.wait_for(ws.recv(), timeout=25.0)
                    msg = json.loads(raw_msg)
                    msg_type = msg.get("type")
                    cmd_name = msg.get("name")
                    print(f"📥 Received: type={msg_type} name={cmd_name}")

                    if msg_type == "command-request":
                        # Respond to browser inspection commands
                        if cmd_name == "getCurrentUrl":
                            result = "https://example.com"
                        elif cmd_name == "getTitle":
                            result = "Example Domain"
                        elif cmd_name == "getInteractiveElements":
                            result = [
                                {"tag": "button", "text": "Login", "role": "button", "box": {"x": 100, "y": 200, "width": 80, "height": 30}}
                            ]
                        else:
                            # Planned action dispatched by AI server (e.g. clickByRole, clickByText, clickLocation)!
                            print(f"\n🎉 AI Server Planned and Executed Command: '{cmd_name}' args={msg.get('arguments')}")
                            result = {"success": True}

                        resp_payload = {
                            "type": "command-response",
                            "taskId": task_id,
                            "index": msg.get("index", 0),
                            "result": result
                        }
                        await ws.send(json.dumps(resp_payload))

                    elif msg_type == "task-complete":
                        print(f"\n🏁 Task Completed: success={msg.get('success')}")
                        break

                except asyncio.TimeoutError:
                    print("⏱️ Timed out waiting for server response.")
                    break

    except Exception as err:
        print(f"❌ Connection or dispatch error: {err}")


if __name__ == "__main__":
    asyncio.run(test_freeform_kimi_dispatch())