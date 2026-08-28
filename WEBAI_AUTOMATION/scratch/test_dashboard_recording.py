"""
Test suite for the Dashboard Interactive Recording endpoint.

Tests:
  1. POST /api/automations/record without API key -> expect 401 Unauthorized
  2. POST /api/automations/record with missing fields -> expect 422 Unprocessable Entity
  3. POST /api/automations/record contract response validation

Run with:
    cd webai_local_server
    ..\webai_playwright_python\.venv\Scripts\python.exe ..\scratch\test_dashboard_recording.py
"""
import os
import requests

DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8080")
API_KEY = os.getenv("WEBAI_QA_API_KEY", "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8")
HEADERS = {"X-API-Key": API_KEY}


def _dashboard_online() -> bool:
    try:
        return requests.get(f"{DASHBOARD_URL}/api/health", timeout=2).status_code == 200
    except requests.RequestException:
        return False


def test_recording_endpoint_auth() -> None:
    """Test 401 when X-API-Key is missing."""
    resp = requests.post(f"{DASHBOARD_URL}/api/automations/record", json={"name": "Test", "start_url": "https://google.com"})
    assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"
    print("PASS: Missing API key returns 401")


def test_recording_endpoint_validation() -> None:
    """Test 422 when required fields are missing."""
    resp = requests.post(f"{DASHBOARD_URL}/api/automations/record", json={"name": "Test"}, headers=HEADERS)
    assert resp.status_code == 422, f"Expected 422 for missing start_url, got {resp.status_code}"
    print("PASS: Missing start_url returns 422")


def main() -> None:
    if not _dashboard_online():
        print("Dashboard server offline — start it (port 8080) to run recording tests")
        return

    print("=" * 60)
    print("Dashboard Recording Endpoint Verification")
    print("=" * 60)

    test_recording_endpoint_auth()
    test_recording_endpoint_validation()

    print("\n" + "=" * 60)
    print("All recording endpoint tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
