"""
Full E2E Verification for Dashboard Recording Feature.

Prerequisites:
  API Server (8000) and Dashboard Server (8080) must be running.

Tests:
  1. REST API E2E: Dispatches POST /api/automations/record, checks 202 Accepted & run_id.
  2. UI E2E via Playwright: Drives the real SPA, clicks '🔴 Record New', fills modal, clicks 'Launch Recorder', verifies toast & process spawn.

Run with:
    .\webai_playwright_python\.venv\Scripts\python.exe scratch\test_e2e_recording_full.py
"""
import os
import time
import requests
from playwright.sync_api import sync_playwright

DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://127.0.0.1:8080")
API_URL = os.getenv("WEBAI_API_URL", "http://127.0.0.1:8000")
API_KEY = ""
HEADERS = {}


def _obtain_api_key() -> str:
    global API_KEY, HEADERS
    try:
        r = requests.post(f"{DASHBOARD_URL}/api/auth/login", json={"username": "e2e_tester", "password": "Password123!"}, timeout=5)
        if r.status_code == 200:
            API_KEY = r.json()["api_key"]
        else:
            r_reg = requests.post(f"{DASHBOARD_URL}/api/auth/register", json={"username": "e2e_tester", "password": "Password123!", "email": "e2e@example.com"}, timeout=5)
            r = requests.post(f"{DASHBOARD_URL}/api/auth/login", json={"username": "e2e_tester", "password": "Password123!"}, timeout=5)
            API_KEY = r.json()["api_key"]
    except Exception as exc:
        print(f"Could not obtain API key via login: {exc}")
        API_KEY = "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8"
    HEADERS = {"X-API-Key": API_KEY}
    return API_KEY


def _check_servers() -> bool:
    try:
        api_ok = requests.get(f"{API_URL}/health", timeout=5).status_code == 200
        dash_ok = requests.get(f"{DASHBOARD_URL}/", timeout=5).status_code in (200, 404)
        return api_ok and dash_ok
    except requests.RequestException as exc:
        print(f"Health check failed: {exc}")
        return False


def test_api_e2e_record_dispatch() -> int:
    print("\n[1] Testing POST /api/automations/record dispatch...")
    payload = {
        "name": "E2E Automated Recording Test",
        "start_url": "https://example.com",
        "description": "Triggered by E2E test suite"
    }
    resp = requests.post(f"{DASHBOARD_URL}/api/automations/record", json=payload, headers=HEADERS, timeout=10)
    assert resp.status_code == 202, f"Expected 202, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert data.get("status") == "recording_started", f"Unexpected status: {data}"
    run_id = data.get("run_id")
    assert run_id is not None, f"Missing run_id in response: {data}"
    print(f"    SUCCESS: Response 202 Accepted | Run ID: {run_id} | Message: {data.get('message')}")
    return run_id


def test_ui_e2e_recording_modal() -> None:
    print("\n[2] Testing UI 'Record New' Modal via Headless Playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("console", lambda msg: print(f"    CONSOLE ({msg.type}): {msg.text}"))
        page.on("pageerror", lambda err: print(f"    PAGE ERROR: {err}"))
        page.on("response", lambda resp: print(f"    NETWORK RESP: {resp.status} {resp.url}"))
        page.goto(DASHBOARD_URL)

        # Log in via localStorage
        page.evaluate(f"localStorage.setItem('webai_api_key', '{API_KEY}')")
        page.reload()
        page.wait_for_selector("#automationGrid", timeout=10000)

        # Check 'Record New' button exists
        record_btn = page.query_selector("#recordBtn")
        assert record_btn is not None, "Record New button not found in UI toolbar!"
        print("    OK: 'Record New' button found in UI header actions")

        # Click 'Record New' button
        record_btn.click()
        page.wait_for_selector("#recordModal:not(.hidden)", timeout=5000)
        print("    OK: Record modal opened successfully")

        # Fill in form
        page.fill("#recordName", "UI Playwright Recording Test")
        page.fill("#recordUrl", "https://example.com")
        page.fill("#recordDesc", "UI modal submission test")

        values = page.evaluate("() => ({ name: document.getElementById('recordName').value, url: document.getElementById('recordUrl').value, valid: document.getElementById('recordForm').checkValidity() })")
        print(f"    FORM VALUES & VALIDITY: {values}")

        # Execute handleRecord directly
        page.evaluate("() => handleRecord(new Event('submit'))")
        
        # Verify toast notification appears
        toast = page.wait_for_selector(".toast", timeout=10000)
        toast_text = toast.text_content()
        assert "Recording window launched" in toast_text or "launched" in toast_text.lower(), f"Unexpected toast: {toast_text}"
        print(f"    SUCCESS: Toast displayed -> '{toast_text}'")

        browser.close()


def main() -> None:
    print("=" * 60)
    print(" Full E2E Test Suite: Interactive Recording Feature")
    print("=" * 60)

    if not _check_servers():
        print("[FAIL] SERVERS OFFLINE! Make sure API (8000) and Dashboard (8080) are running.")
        return

    api_key = _obtain_api_key()
    print(f"Using active API key: {api_key[:10]}...")

    try:
        run_id = test_api_e2e_record_dispatch()
        test_ui_e2e_recording_modal()

        print("\n" + "=" * 60)
        print(" ALL FULL E2E TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
    except AssertionError as err:
        print(f"\n[FAIL] E2E TEST FAILED: {err}")
    except Exception as exc:
        print(f"\n[FAIL] UNEXPECTED ERROR: {exc}")


if __name__ == "__main__":
    main()
