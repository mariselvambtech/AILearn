# record_then_run.py
# Ready-to-paste
# - Records user actions
# - Stops via: Stop button (bottom-right) OR Ctrl+Shift+S OR Ctrl+Alt+S OR Esc
# - After recording, asks: "Run AI after recording? (y/n)"
# - Saves: recorded_steps.json, generated_task.txt

"""
Dual-phase script: Record actions and immediately replay them.

This script launches an interactive browser where user actions are intercepted 
via the Chrome DevTools Protocol (CDP) and recorded into `recorded_steps.json`.
Once the user closes the browser, it immediately launches a new instance to 
replay the recorded JSON sequence.
"""
import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

# Robust imports even if you run from another folder
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from webai_playwright.recorder import WebRecorder
from webai_playwright import ai

OUTPUT_JSON = "recorded_steps.json"
OUTPUT_TASK = "generated_task.txt"
START_URL = "about:blank"


def ask_yes_no(prompt: str, default: str = "n") -> bool:
    default = default.lower().strip()
    while True:
        ans = input(f"{prompt} (y/n) [default: {default}]: ").strip().lower()
        if not ans:
            ans = default
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("Please enter y or n.")


async def main():
    recorder = WebRecorder()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await recorder.attach(page)
        await page.goto(START_URL)

        print("\n=== Web Recorder Started ===")
        print("Do actions in the browser.")
        print("Stop options:")
        print("  - Click Stop Recording button (bottom-right)")
        print("  - Ctrl+Shift+S or Ctrl+Alt+S or Esc")
        print("Verify options:")
        print("  - Ctrl+Shift+V -> Verify page contains text")
        print("  - Ctrl+Shift+E -> Verify element visible (then click element)")
        print("============================\n")

        # Wait until stopped from inside the browser
        await recorder.wait_for_stop()

        # Save outputs
        steps_json = recorder.to_json()
        task_text = recorder.to_task_text()

        Path(OUTPUT_JSON).write_text(json.dumps(steps_json, indent=2), encoding="utf-8")
        Path(OUTPUT_TASK).write_text(task_text, encoding="utf-8")

        print(f"\nSaved: {OUTPUT_JSON}")
        print(f"Saved: {OUTPUT_TASK}")
        print("\n=== GENERATED TASK ===\n")
        print(task_text)
        print("\n======================\n")

        run_ai = ask_yes_no("Run AI after recording?", default="n")

        if run_ai:
            print("\nRunning AI health-check with generated TASK...\n")
            result = await ai(task_text, page=page)
            print("\n=== AI RESULT ===")
            print(result)
            print("=================\n")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
