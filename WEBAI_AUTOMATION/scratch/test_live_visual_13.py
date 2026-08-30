import sys
import os
import asyncio

# --- FIX: Tell Python to look in the webai_playwright_python folder ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'webai_playwright_python')))
# ----------------------------------------------------------------------

from playwright.async_api import async_playwright
from webai_playwright.fallback_helpers import click_with_fallback

async def main():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: sans-serif; padding: 40px; }
            .btn { display: inline-block; padding: 10px 20px; margin: 10px; cursor: pointer; border: 2px solid #333; }
            .clicked { background-color: #4CAF50; color: white; border-color: #4CAF50; }
        </style>
    </head>
    <body>
        <h2>13-Locator Visual Verification</h2>
        
        <!-- Target 1: Alt text on image button -->
        <img id="btn-alt" class="btn" alt="Submit Purchase Order" src="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='100' height='30'><text y='20'>[Alt Button]</text></svg>" onclick="this.classList.add('clicked')" />
        
        <!-- Target 2: Aria-label on icon/div button -->
        <div id="btn-aria" class="btn" role="button" aria-label="Add Item to Cart" onclick="this.classList.add('clicked')">Add to Cart</div>
        
        <!-- Target 3: Title attribute on tooltip button -->
        <button id="btn-title" class="btn" title="View Extended Product Details" onclick="this.classList.add('clicked')">Details</button>
    </body>
    </html>
    """
    
    async with async_playwright() as p:
        # Launch visible Chromium browser
        browser = await p.chromium.launch(headless=False, slow_mo=700)
        page = await browser.new_page()
        await page.set_content(html_content)
        
        print("\nTesting 'alt' locator resolution...")
        res1 = await click_with_fallback(page, [{"type": "alt", "value": "Submit Purchase Order"}])
        print(f"-> Alt Click Result: {res1}")

        print("Testing 'aria-label' locator resolution...")
        res2 = await click_with_fallback(page, [{"type": "aria-label", "value": "Add Item to Cart"}])
        print(f"-> Aria-Label Click Result: {res2}")

        print("Testing 'title' locator resolution...")
        res3 = await click_with_fallback(page, [{"type": "title", "value": "View Extended Product Details"}])
        print(f"-> Title Click Result: {res3}")

        # Verify all buttons turned green (class="clicked")
        alt_clicked = await page.locator("#btn-alt.clicked").count() > 0
        aria_clicked = await page.locator("#btn-aria.clicked").count() > 0
        title_clicked = await page.locator("#btn-title.clicked").count() > 0

        assert alt_clicked and aria_clicked and title_clicked, "One or more locator types failed to trigger the click!"
        print("\n✅ All 3 new locator types clicked successfully in a live browser session!")

        await page.wait_for_timeout(1500)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())