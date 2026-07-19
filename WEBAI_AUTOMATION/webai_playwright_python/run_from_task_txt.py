import asyncio
import re
from pathlib import Path
from playwright.async_api import async_playwright
from webai_playwright import ai

TASK_FILE = "generated_task.txt"
OPEN_RE = re.compile(r"^\s*Open\s+(https?://\S+)\s*$", re.IGNORECASE | re.MULTILINE)

async def main():
    task_text = Path(TASK_FILE).read_text(encoding="utf-8").strip()
    if not task_text:
        raise RuntimeError(f"{TASK_FILE} is empty")

    m = OPEN_RE.search(task_text)
    first_url = m.group(1) if m else None

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        if first_url:
            print(f"[run_from_task_txt] Preloading: {first_url}")
            await page.goto(first_url, wait_until="domcontentloaded")
        else:
            await page.goto("about:blank")

        result = await ai(task_text, page=page)
        print("\n=== AI RESULT ===")
        print(result)
        print("=================\n")

        input("Press ENTER to close the browser...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
