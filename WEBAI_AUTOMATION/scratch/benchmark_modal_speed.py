"""
Benchmark: Modal rendering response time.

Measures the latency of the endpoints that power the "Logs" and "View Steps"
modals, plus the lightweight automations summary endpoint. Run against a live
API server (port 8000) with the QA API key.

Usage:
    cd webai_api_server
    ..\webai_playwright_python\.venv\Scripts\python.exe ..\scratch\benchmark_modal_speed.py
"""
import os
import time
from typing import Any, Dict, List, Optional

import requests

API_URL = os.getenv("WEBAI_API_URL", "http://localhost:8000")
API_KEY = os.getenv("WEBAI_QA_API_KEY", "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8")
HEADERS = {"X-API-Key": API_KEY}
TARGET_MS = 200


def _time_get(path: str, params: Optional[Dict[str, Any]] = None) -> float:
    """Return the response time in milliseconds for a GET request."""
    start = time.perf_counter()
    resp = requests.get(f"{API_URL}{path}", headers=HEADERS, params=params, timeout=15)
    elapsed_ms = (time.perf_counter() - start) * 1000
    if resp.status_code != 200:
        print(f"  [WARN] {path} returned {resp.status_code}")
    return elapsed_ms


def _api_online() -> bool:
    """Check if the API server is reachable."""
    try:
        return requests.get(f"{API_URL}/health", timeout=2).status_code == 200
    except requests.RequestException:
        return False


def main() -> None:
    """Run the benchmark and print results."""
    if not _api_online():
        print("API server offline — start it (port 8000) to run the benchmark")
        return

    print("=" * 60)
    print("Modal Speed Benchmark")
    print(f"  Target: < {TARGET_MS}ms per request")
    print("=" * 60)

    results: List[Dict[str, Any]] = []

    # 1) Automations summary (lightweight card grid)
    print("\n1. GET /automations/summary (lightweight card grid)")
    for i in range(3):
        ms = _time_get("/automations/summary")
        print(f"   Run {i+1}: {ms:.1f}ms")
        results.append({"endpoint": "/automations/summary", "ms": ms})

    # 2) Automations full (with steps_json — for comparison)
    print("\n2. GET /automations (full, with steps_json — for comparison)")
    for i in range(3):
        ms = _time_get("/automations")
        print(f"   Run {i+1}: {ms:.1f}ms")
        results.append({"endpoint": "/automations (full)", "ms": ms})

    # 3) Executions list
    print("\n3. GET /executions (executions table)")
    for i in range(3):
        ms = _time_get("/executions", params={"limit": 15})
        print(f"   Run {i+1}: {ms:.1f}ms")
        results.append({"endpoint": "/executions", "ms": ms})

    # 4) Logs modal — find an execution ID to test
    print("\n4. GET /executions/{id}/logs (Logs modal)")
    try:
        execs = requests.get(f"{API_URL}/executions", headers=HEADERS,
                              params={"limit": 1}, timeout=10).json()
        if execs and isinstance(execs, list) and len(execs) > 0:
            exec_id = execs[0].get("id")
            for i in range(3):
                ms = _time_get(f"/executions/{exec_id}/logs", params={"limit": 100})
                print(f"   Run {i+1}: {ms:.1f}ms (execution #{exec_id})")
                results.append({"endpoint": f"/executions/{exec_id}/logs", "ms": ms})
        else:
            print("   SKIP: No executions found to test")
    except requests.RequestException as exc:
        print(f"   SKIP: Could not fetch executions: {exc}")

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    all_pass = True
    for r in results:
        status = "PASS" if r["ms"] < TARGET_MS else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  {status} {r['endpoint']}: {r['ms']:.1f}ms")

    print("\n" + ("All requests under 200ms — PASS" if all_pass else
                  "Some requests exceeded 200ms — FAIL"))
    print("=" * 60)


if __name__ == "__main__":
    main()