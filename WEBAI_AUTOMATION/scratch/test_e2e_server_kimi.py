# scratch/test_e2e_server_kimi.py
import asyncio
import sys
import os
import json
import websockets
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, "webai_local_server")

load_dotenv(".env", override=True)
load_dotenv("webai_local_server/.env", override=True)

# Force provider to kimi_k3
os.environ["LLM_PROVIDER"] = "kimi_k3"

from webai_local_server.local_webai_server_guided import handle_client


async def run_e2e_test():
    test_port = 8799
    server = await websockets.serve(handle_client, "127.0.0.1", test_port)
    print(f"🚀 Started ephemeral WebAI server on ws://127.0.0.1:{test_port} (LLM_PROVIDER={os.getenv('LLM_PROVIDER')})")

    uri = f"ws://127.0.0.1:{test_port}/api?key=local-dev"
    try:
        async with websockets.connect(uri) as ws:
            tiny_jpg_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
            task_id = "test_kimi_e2e_task"

            task_payload = {
                "type": "task-start",
                "taskId": task_id,
                "task": "Click on the Login button",
                "snapshot": {
                    "url": "https://example.com",
                    "title": "Example Domain",
                    "screenshot": tiny_jpg_b64,
                    "interactiveElements": [
                        {"tag": "button", "text": "Login", "role": "button"}
                    ]
                },
                "options": {
                    "recorded_steps": []  # Freeform mode: forces LLM planning
                }
            }

            print("📤 Sending task-start to server...")
            await ws.send(json.dumps(task_payload))

            for round_i in range(8):
                raw = await asyncio.wait_for(ws.recv(), timeout=30.0)
                msg = json.loads(raw)
                msg_type = msg.get("type")
                name = msg.get("name")
                print(f"📥 Client received: {msg_type} -> name={name}")

                if msg_type == "command-request":
                    if name == "getCurrentUrl":
                        res = "https://example.com"
                    elif name == "getTitle":
                        res = "Example Domain"
                    elif name == "getInteractiveElements":
                        res = [
                            {"tag": "button", "text": "Login", "role": "button", "box": {"x": 100, "y": 200, "width": 80, "height": 30}}
                        ]
                    else:
                        print(f"\n🎉 SUCCESS! Kimi K3 planned and dispatched browser action: '{name}'")
                        print(f"   Action arguments: {msg.get('arguments')}")
                        res = {"success": True}

                    await ws.send(json.dumps({
                        "type": "command-response",
                        "taskId": task_id,
                        "index": msg.get("index", 0),
                        "result": res
                    }))

                    if name not in ("getCurrentUrl", "getTitle", "getInteractiveElements"):
                        print("✅ End-to-end Kimi K3 planning verified successfully!")
                        break

                elif msg_type == "task-complete":
                    print(f"🏁 Task complete: {msg}")
                    break

    finally:
        server.close()
        await server.wait_closed()
        print("🛑 Server closed.")


if __name__ == "__main__":
    asyncio.run(run_e2e_test())
