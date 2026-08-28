"""
E2E verification for the WebSocket probe-tolerance fix in
webai_local_server/local_webai_server_guided.py.

Starts the real AI server (test port 8766, so a live dev server on 8765 is
never disturbed) in a subprocess and exercises:

  1. Bare TCP probe (connect + close, 0 bytes — old dashboard ``_probe_tcp``)
     -> server must stay SILENT (no 'opening handshake failed' ERROR output).
  2. Plain HTTP GET (dashboard ``_probe_ws`` / browser / curl)
     -> server must answer HTTP 200 with NO error logging.
  3. Malformed garbage bytes
     -> genuine parse failure must STILL be logged at ERROR (no over-suppression).
  4. Genuine WebSocket client handshake + bogus first message
     -> handshake must succeed and the server must reply with a
        'task-complete' error payload (clean protocol round-trip).

Run from the repo root:
    webai_local_server\\.venv\\Scripts\\python.exe scratch\\test_ws_probe_fix.py
"""
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_PY = REPO_ROOT / "webai_local_server" / ".venv" / "Scripts" / "python.exe"
SERVER_CWD = REPO_ROOT / "webai_local_server"
PORT = 8766  # isolated test port — never clashes with a dev server on 8765


def bare_tcp_probe() -> None:
    """Connect and close without sending a single byte (old _probe_tcp)."""
    with socket.create_connection(("localhost", PORT), timeout=3):
        pass


def http_get_probe() -> str:
    """Send a plain HTTP/1.1 GET (dashboard _probe_ws) and return the response."""
    with socket.create_connection(("localhost", PORT), timeout=3) as sock:
        sock.settimeout(3)
        sock.sendall(b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n")
        return sock.recv(512).decode("latin-1", errors="replace")


def garbage_probe() -> None:
    """Send non-HTTP garbage bytes (genuine malformed request)."""
    with socket.create_connection(("localhost", PORT), timeout=3) as sock:
        sock.settimeout(3)
        sock.sendall(b"GARBAGE\r\n\r\n")
        try:
            sock.recv(128)
        except OSError:
            pass


def ws_client_probe() -> dict:
    """Genuine WebSocket handshake + bogus first message -> expect task-complete error."""
    import websockets

    async def _run() -> dict:
        async with websockets.connect(
            f"ws://localhost:{PORT}/api?key=local-dev", open_timeout=5
        ) as ws:
            await ws.send(json.dumps({"type": "bogus", "taskId": "probe-test"}))
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            return json.loads(raw)

    return asyncio.run(_run())


def wait_for_listening(timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("localhost", PORT), timeout=1):
                return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError(f"server did not start listening on port {PORT}")


def main() -> int:
    print("=" * 60)
    print(" WebSocket probe-tolerance E2E test (port %d)" % PORT)
    print("=" * 60)
    env = os.environ.copy()
    env["PORT"] = str(PORT)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"  # unbuffered stdout so prints survive terminate()
    print(f"Starting AI server: {VENV_PY} -u -m webai_local_server.local_webai_server_guided")
    proc = subprocess.Popen(
        [str(VENV_PY), "-u", "-m", "webai_local_server.local_webai_server_guided"],
        cwd=str(SERVER_CWD),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    try:
        wait_for_listening()

        print("\n[1] Bare TCP probes (0 bytes, x3) — old dashboard _probe_tcp ...")
        for _ in range(3):
            bare_tcp_probe()

        print("[2] Plain HTTP GET probe — dashboard _probe_ws / browser ...")
        resp = http_get_probe()
        status_line = resp.splitlines()[0] if resp else "(no response)"
        print(f"    server replied: {status_line}")
        assert "200" in status_line, f"expected HTTP 200, got: {resp!r}"

        print("[3] Malformed garbage probe (genuine parse failure) ...")
        garbage_probe()

        print("[4] Genuine WebSocket client handshake + bogus message ...")
        reply = ws_client_probe()
        print(f"    server replied: {reply}")
        assert reply.get("type") == "task-complete", f"unexpected reply: {reply}"
        assert reply.get("taskId") == "probe-test", f"unexpected taskId: {reply}"

        time.sleep(2.0)  # allow the server to flush any logs
    finally:
        proc.terminate()
        try:
            out, _ = proc.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()

    print("\n--- Captured server output ---")
    for line in out.splitlines():
        print(f"    {line}")
    print("--- End of server output ---\n")

    lines = out.splitlines()
    eof_noise = [l for l in lines if "stream ends after 0 bytes" in l]
    genuine_errors = [l for l in lines if "opening handshake failed" in l]
    client_connected = [l for l in lines if "Client connected" in l]

    failures = []

    # Empty probes (wait_for_listening + step 1) must be fully silent.
    if eof_noise:
        failures.append(f"empty-probe EOFError tracebacks leaked: {eof_noise[:2]}")

    # The garbage probe MUST log exactly one genuine ERROR (proves no over-suppression).
    if not genuine_errors:
        failures.append("expected the garbage probe to log one genuine 'opening handshake failed' ERROR (over-suppression?)")
    elif len(genuine_errors) > 1:
        failures.append(f"expected at most 1 genuine handshake error (garbage probe), got {len(genuine_errors)}")

    # The genuine WS client must reach the application handler.
    if not client_connected:
        failures.append("genuine WebSocket client did not reach handle_client ('Client connected' missing)")

    if failures:
        print("❌ TEST FAILED:")
        for f in failures:
            print(f"   - {f}")
        return 1

    print("✅ ALL CHECKS PASSED:")
    print("   - bare TCP probes (0 bytes) produced NO error output")
    print("   - plain HTTP GET answered with 200, no InvalidUpgrade error")
    print("   - malformed garbage still logs a genuine ERROR (no over-suppression)")
    print("   - genuine WebSocket client connected + received task-complete reply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
