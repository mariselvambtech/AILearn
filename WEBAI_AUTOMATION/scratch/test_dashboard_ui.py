"""
Browser-driven UI test for the WebAI Dashboard front-end (scratch QA tool).

Drives the real SPA at http://localhost:8080 with Playwright (headless) and
asserts the user-facing flows work end to end against the live servers:
  1. Page loads, health badges reflect live services
  2. Auth modal appears when logged out
  3. Login via the UI persists a session (user chip + logout)
  4. Automation grid renders cards from the API
  5. "View steps" modal opens and lists recorded steps
  6. "Run" modal opens with a step preview (does NOT actually run playback)
  7. Executions table renders rows; Logs modal opens

Run with the Playwright venv while API (8000), AI (8765) and Dashboard (8080)
are up:
    .\\webai_playwright_python\\.venv\\Scripts\\python.exe scratch\\test_dashboard_ui.py
"""
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8080"
USERNAME = "mariselvam"
PASSWORD = "mariselvam"

results = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        console_errors = []
        page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: console_errors.append(str(e)))

        # Start logged out
        page.goto(BASE, wait_until="networkidle")
        page.evaluate("localStorage.clear()")
        page.reload(wait_until="networkidle")
        # Wait for app boot: auth modal should auto-open and health poll should run
        page.wait_for_selector("#authModal:not(.hidden)", timeout=8000)
        page.wait_for_timeout(1500)

        # 1. Page + title
        check("page loads with correct title", "WebAI" in page.title())

        # 2. Health badges eventually reflect live services (API/AI online)
        page.wait_for_function(
            "document.getElementById('badgeApi').classList.contains('online')",
            timeout=8000)
        api_badge = page.locator("#badgeApi").get_attribute("class") or ""
        ai_badge = page.locator("#badgeAi").get_attribute("class") or ""
        check("API health badge shows online", "online" in api_badge, api_badge)
        check("AI health badge shows online", "online" in ai_badge, ai_badge)

        # 3. Auth modal visible when logged out
        auth_visible = page.locator("#authModal").is_visible()
        check("auth modal shown when logged out", auth_visible)

        # 4. Login via the UI form
        page.fill("#loginUsername", USERNAME)
        page.fill("#loginPassword", PASSWORD)
        page.click("#loginForm button[type=submit]")
        # Wait for the session to be persisted (proves login handler completed)
        page.wait_for_function(
            "Boolean(localStorage.getItem('webai_api_key'))", timeout=8000)
        page.wait_for_timeout(1200)
        user_chip_visible = page.locator("#userChip").is_visible()
        logout_visible = page.locator("#logoutBtn").is_visible()
        check("login succeeds → user chip visible", user_chip_visible)
        check("logout button visible after login", logout_visible)
        stored_key = page.evaluate("localStorage.getItem('webai_api_key')")
        check("api key persisted to localStorage", bool(stored_key))

        # 5. Automation grid renders cards
        page.wait_for_timeout(1500)
        card_count = page.locator("#automationGrid .card").count()
        check("automation grid renders cards", card_count > 0, f"{card_count} card(s)")

        # 6. View steps modal
        if card_count > 0:
            page.locator("#automationGrid .card [data-steps]").first.click()
            # Wait for the async fetch to populate the steps list
            page.wait_for_selector("#stepsList .step-item", timeout=8000)
            steps_visible = page.locator("#stepsModal").is_visible()
            step_items = page.locator("#stepsList .step-item").count()
            check("view-steps modal opens", steps_visible)
            check("steps list populated", step_items > 0, f"{step_items} step(s)")
            page.locator("#stepsModal [data-close]").first.click()
            page.wait_for_timeout(400)

        # 7. Run modal opens with preview (do NOT confirm an actual run)
        if card_count > 0:
            page.locator("#automationGrid .card [data-run]").first.click()
            # Wait for the async fetch to populate the step preview
            page.wait_for_function(
                "document.getElementById('runStepsPreview').innerText.toLowerCase().includes('step')",
                timeout=8000)
            run_visible = page.locator("#runModal").is_visible()
            preview_text = page.locator("#runStepsPreview").inner_text()
            check("run modal opens", run_visible)
            check("run modal shows step preview", "step" in preview_text.lower(), preview_text[:60])
            page.locator("#runModal .modal-footer [data-close]").first.click()
            page.wait_for_timeout(400)

        # 8. Executions table renders and Logs modal opens
        page.wait_for_timeout(1500)
        exec_rows = page.locator("#executionsBody tr").count()
        exec_has_data = page.locator("#executionsBody [data-logs]").count() > 0
        check("executions table renders rows", exec_rows > 0, f"{exec_rows} row(s)")
        if exec_has_data:
            page.locator("#executionsBody [data-logs]").first.click()
            page.wait_for_timeout(1500)
            logs_visible = page.locator("#logsModal").is_visible()
            check("logs modal opens", logs_visible)
            page.locator("#logsModal [data-close]").first.click()
        else:
            check("logs modal opens", True, "no executions yet — skipped (ok)")

        # 9. No fatal JS console errors
        fatal = [e for e in console_errors if "favicon" not in e.lower()]
        check("no JS console/page errors", len(fatal) == 0, "; ".join(fatal[:3]))

        browser.close()

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"\n=== UI TEST SUMMARY: {passed}/{total} passed ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
