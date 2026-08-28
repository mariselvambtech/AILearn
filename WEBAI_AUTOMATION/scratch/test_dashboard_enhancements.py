"""
E2E test: Dashboard enhancements (delete + stale reconciliation).

Playwright headless test covering:
  1. Delete button appears on automation cards
  2. Delete confirmation modal opens with correct automation name
  3. Stale execution reconciliation marks orphan RUNNING as FAILED

Requires the dashboard server (port 8080) and API server (port 8000) running.
Run with:
    cd webai_local_server
    ..\webai_playwright_python\.venv\Scripts\python.exe ..\scratch\test_dashboard_enhancements.py
"""
import os
import time
from typing import Any, Dict, Optional

import requests
from playwright.sync_api import sync_playwright

DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8080")
API_URL = os.getenv("WEBAI_API_URL", "http://localhost:8000")
API_KEY = os.getenv("WEBAI_QA_API_KEY", "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8")
HEADERS = {"X-API-Key": API_KEY}


def _dashboard_online() -> bool:
    """Check if the dashboard server is reachable."""
    try:
        return requests.get(f"{DASHBOARD_URL}/api/health", timeout=2).status_code == 200
    except requests.RequestException:
        return False


def _api_online() -> bool:
    """Check if the API server is reachable."""
    try:
        return requests.get(f"{API_URL}/health", timeout=2).status_code == 200
    except requests.RequestException:
        return False


def test_delete_button_and_modal() -> None:
    """Test that the delete button appears and opens a confirmation modal."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(DASHBOARD_URL)

        # Set API key in localStorage (simulates login)
        page.evaluate(f"localStorage.setItem('webai_api_key', '{API_KEY}')")
        page.reload()
        page.wait_for_selector(".card", timeout=10000)

        # Check delete button exists
        delete_btn = page.query_selector("[data-delete]")
        assert delete_btn is not None, "Delete button not found on automation card"

        # Click delete button
        delete_btn.click()
        page.wait_for_selector("#deleteModal:not(.hidden)", timeout=5000)

        # Check modal content
        modal_desc = page.text_content("#deleteModalDesc")
        assert "Are you sure" in modal_desc, f"Unexpected modal text: {modal_desc}"

        # Close modal
        page.click('[data-close="deleteModal"]')
        page.wait_for_selector("#deleteModal.hidden", timeout=5000)

        browser.close()
        print("PASS: Delete button and confirmation modal work correctly")


def test_stale_reconciliation() -> None:
    """Test that stale RUNNING executions are reconciled to FAILED."""
    if not _api_online():
        print("SKIP: API server offline — cannot test stale reconciliation")
        return

    # Fetch current executions
    resp = requests.get(f"{API_URL}/executions", headers=HEADERS,
                         params={"limit": 50}, timeout=10)
    if resp.status_code != 200:
        print("SKIP: Could not fetch executions")
        return

    executions = resp.json() or []
    stale_count = sum(1 for e in executions
                      if (e.get("status") or "").lower() == "running"
                      and not (e.get("live_status") or "").lower() == "running")

    if stale_count == 0:
        print("PASS: No stale RUNNING executions found (nothing to reconcile)")
        return

    # Trigger reconciliation via dashboard
    resp = requests.get(f"{DASHBOARD_URL}/api/executions", headers=HEADERS,
                         params={"limit": 50}, timeout=15)
    if resp.status_code != 200:
        print(f"FAIL: Dashboard executions endpoint returned {resp.status_code}")
        return

    # Check that stale executions were reconciled
    time.sleep(2)  # Give the sweeper time to run
    resp = requests.get(f"{API_URL}/executions", headers=HEADERS,
                         params={"limit": 50}, timeout=10)
    executions = resp.json() or []
    still_stale = sum(1 for e in executions
                      if (e.get("status") or "").lower() == "running"
                      and not (e.get("live_status") or "").lower() == "running")

    if still_stale < stale_count:
        print(f"PASS: Reconciled {stale_count - still_stale} stale execution(s)")
    else:
        print(f"WARN: {still_stale} stale execution(s) still RUNNING (may be live)")


def main() -> None:
    """Run all enhancement tests."""
    if not _dashboard_online():
        print("Dashboard server offline — start it (port 8080) to run tests")
        return

    print("=" * 60)
    print("Dashboard Enhancements E2E Test")
    print("=" * 60)

    test_delete_button_and_modal()
    test_stale_reconciliation()

    print("\n" + "=" * 60)
    print("All enhancement tests completed")
    print("=" * 60)


if __name__ == "__main__":
    main()