"""
Purely autonomous, blank-slate AI browser navigation entry point.

This script reads a natural language prompt from `generated_task.txt` and relies
entirely on the local WebAI server for intelligent navigation without using any
pre-recorded JSON files (e.g., `recorded_steps.json`).
"""
import asyncio
import os
import re
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# Ensure standard output uses UTF-8 to prevent Windows console crashes
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Ensure client directory is in sys.path
CLIENT_DIR = Path(__file__).resolve().parent
if str(CLIENT_DIR) not in sys.path:
    sys.path.insert(0, str(CLIENT_DIR))

from webai_playwright.ai import ai, ClientError


class TaskComplete(Exception):
    """Exception or signal representing autonomous task completion."""
    pass


def _resolve_task_file() -> Path:
    """Find the task prompt file, checking local and parent directories."""
    candidates = [
        CLIENT_DIR / "generated_task.txt",
        Path("generated_task.txt"),
        CLIENT_DIR.parent / "generated_task.txt",
    ]
    for p in candidates:
        if p.exists():
            return p
    return CLIENT_DIR / "generated_task.txt"


async def main() -> None:
    """Main execution loop for purely autonomous AI navigation."""
    task_file = _resolve_task_file()
    if not task_file.exists():
        raise FileNotFoundError(f"Task file not found at: {task_file}")

    task_text = task_file.read_text(encoding="utf-8").strip()
    if not task_text:
        raise ValueError(f"Task file is empty: {task_file}")

    print(f"[run_autonomous] Loaded task from {task_file}:")
    print(f"  '{task_text}'\n")

    # Check for optional initial URL command (e.g. 'Open https://...')
    first_url = None
    open_re = re.compile(r"^\s*Open\s+(https?://\S+)\s*$", re.IGNORECASE | re.MULTILINE)
    m = open_re.search(task_text)
    if m:
        first_url = m.group(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            if first_url:
                print(f"[run_autonomous] Preloading initial URL: {first_url}")
                await page.goto(first_url, wait_until="domcontentloaded")
            else:
                print("[run_autonomous] Starting with blank slate (about:blank)")
                await page.goto("about:blank")

            print("[run_autonomous] Delegating navigation to local AI server...")
            # Pure autonomous execution: No recorded_steps loaded or passed
            result = await ai(task_text, page=page)

            print("\n=== AI RESULT ===")
            print(result)
            print("=================\n")

        except ClientError as ce:
            print(f"\n[ClientError] WebAI client error occurred: {ce}")
        except TaskComplete as tc:
            print(f"\n[TaskComplete] Task completed successfully: {tc}")
        except Exception as e:
            print(f"\n[Error] Unexpected error during autonomous execution: {e}")
        finally:
            print("[run_autonomous] Cleaning up browser resources...")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
