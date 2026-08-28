"""Capture UI screenshots + exercise the Import flow end to end."""
import json
import sys
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8080"

# A tiny valid recording payload for the import test
IMPORT_STEPS = [
    {"action": "open", "url": "https://example.com/", "name": None, "value": None},
    {"action": "click", "url": "https://example.com/", "name": "More info", "value": None},
]

results = []

def check(name, ok, detail=""):
    results.append((name, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900})
    page.goto(BASE, wait_until="networkidle")
    page.evaluate("localStorage.clear()")
    page.reload(wait_until="networkidle")
    page.wait_for_selector("#authModal:not(.hidden)", timeout=8000)
    page.wait_for_timeout(1000)

    # Login
    page.fill("#loginUsername", "mariselvam")
    page.fill("#loginPassword", "mariselvam")
    page.click("#loginForm button[type=submit]")
    page.wait_for_function("Boolean(localStorage.getItem('webai_api_key'))", timeout=8000)
    page.wait_for_timeout(1500)

    # Screenshot: main dashboard with cards
    page.screenshot(path="scratch/ui_dashboard.png", full_page=True)
    check("screenshot: dashboard grid", True, "scratch/ui_dashboard.png")

    # Screenshot: steps modal
    page.locator("#automationGrid .card [data-steps]").first.click()
    page.wait_for_selector("#stepsList .step-item", state="attached", timeout=8000)
    page.wait_for_timeout(400)
    page.screenshot(path="scratch/ui_steps_modal.png")
    check("screenshot: steps modal", True, "scratch/ui_steps_modal.png")
    page.locator("#stepsModal [data-close]").first.click()
    page.wait_for_timeout(400)

    # --- Import flow (real, end to end) ---
    # Write a temp recording file and import it via the UI file picker
    tmp_file = "scratch/_ui_import_steps.json"
    with open(tmp_file, "w", encoding="utf-8") as f:
        json.dump(IMPORT_STEPS, f)

    cards_before = page.locator("#automationGrid .card").count()
    page.click("#importBtn")
    page.wait_for_selector("#importModal:not(.hidden)", timeout=5000)
    page.set_input_files("#importFile", tmp_file)
    page.fill("#importName", "UI Import Test Automation")
    page.fill("#importDesc", "Imported by Playwright UI test")
    page.click("#importForm button[type=submit]")
    # Import succeeds -> modal hides + automations reload
    page.wait_for_selector("#importModal", state="hidden", timeout=10000)
    page.wait_for_timeout(1500)
    cards_after = page.locator("#automationGrid .card").count()
    check("import flow adds a new automation card", cards_after == cards_before + 1,
          f"{cards_before} -> {cards_after}")
    names = page.locator("#automationGrid .card .card-title").all_inner_texts()
    check("imported automation appears by name", any("UI Import Test" in n for n in names),
          "; ".join(names))
    page.screenshot(path="scratch/ui_after_import.png", full_page=True)

    browser.close()

passed = sum(1 for _, ok in results if ok)
print(f"\n=== VISUAL/IMPORT SUMMARY: {passed}/{len(results)} passed ===")
sys.exit(0 if passed == len(results) else 1)
