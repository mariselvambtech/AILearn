import asyncio
import json
from pathlib import Path
import sys
from playwright.async_api import async_playwright

# ensure local project root used
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from webai_playwright import ai


def _load_recorded_steps() -> list:
    p = Path("recorded_steps.json")
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


async def main():
    task_text = Path("generated_task.txt").read_text(encoding="utf-8").strip()
    recorded_steps = _load_recorded_steps()

    # Preload first URL from the task, if present
    first_url = None
    for line in task_text.splitlines():
        line = line.strip()
        if line.lower().startswith("open "):
            first_url = line[5:].strip()
            break

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        if first_url:
            print(f"[run_from_task_txt] Preloading: {first_url}")
            await page.goto(first_url)

        options = {"recorded_steps": recorded_steps, "mode": "guided"}
        result = await ai(task_text, page=page, options=options)
        print(result)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
