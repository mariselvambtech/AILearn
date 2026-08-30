import sys
import os
import asyncio

# Tell Python where to find the webai_playwright module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'webai_playwright_python')))

from playwright.async_api import async_playwright

async def main():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { padding: 50px; font-family: sans-serif; background: #f0f0f0; height: 100vh; margin: 0; }
            .btn { padding: 15px 25px; background: #007bff; color: white; cursor: pointer; display: inline-block; font-weight: bold; border-radius: 5px; }
            .dead-space { width: 400px; height: 150px; background: #ddd; margin-top: 20px; border: 3px dashed #999; display: flex; align-items: center; justify-content: center; color: transparent; }
            .text-box { margin-top: 20px; padding: 15px; background: white; border: 1px solid #ccc; width: 400px; }
        </style>
    </head>
    <body>
        <h2>🛡️ Smart Semantic Filter Test</h2>
        
        <p>1. Click the blue button (Should be CAPTURED):</p>
        <div class="btn" id="valid-btn" role="button">Submit Order</div>

        <p>2. Click this text box (Should be CAPTURED):</p>
        <div class="text-box" id="valid-text">This is standard text inside a div. It has no role, but it has content.</div>

        <p>3. Click anywhere inside the grey dashed box (Should be IGNORED):</p>
        <div class="dead-space" id="invalid-space"></div>
        
        <p>4. Click the grey background anywhere (Should be IGNORED)</p>
    </body>
    </html>
    """

    # This is the exact JS payload Antigravity implemented
    telemetry_js = """
    () => {
        window.__webai_telemetry = window.__webai_telemetry || [];
        if (!window.__webai_telemetry_handler) {
            window.__webai_telemetry_handler = function(e) {
                if (e.target.closest('#webai-hitl-observer-panel')) return;
                
                const target = e.target;
                const tag = (target.tagName || '').toLowerCase();
                const text = (target.innerText || target.getAttribute('aria-label') || target.getAttribute('alt') || target.getAttribute('placeholder') || target.getAttribute('title') || target.value || '').trim();
                
                const isInteractiveTag = ['a', 'button', 'input', 'select', 'textarea', 'option', 'label', 'summary'].includes(tag);
                const hasInteractiveRole = Boolean(target.closest('[role="button"], [role="link"], [role="option"], [role="checkbox"], [role="menuitem"], [role="tab"], [role="combobox"]') || target.hasAttribute('onclick') || target.getAttribute('role'));
                
                // Exclude root elements from passing the text check
                const isRoot = tag === 'body' || tag === 'html';
                const hasText = text.length > 0 && !isRoot;

                if (!isInteractiveTag && !hasInteractiveRole && !hasText) {
                    console.log('[Telemetry] Discarded noise on <' + tag + '>');
                    return;
                }

                let css = tag;
                if (target.id) css += '#' + target.id;
                
                window.__webai_telemetry.push({
                    tag: tag,
                    text: text.substring(0, 100),
                    css: css,
                    timestamp: Date.now()
                });
            };
            document.addEventListener('click', window.__webai_telemetry_handler, true);
        }
    }
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.set_content(html_content)

        # Inject the telemetry listener
        await page.evaluate(telemetry_js)
        
        print("\n" + "="*60)
        print("🚀 BROWSER READY: You have 10 seconds to click!")
        print("-> Click the blue button.")
        print("-> Click the white text box.")
        print("-> Click the grey dashed box.")
        print("-> Click the background.")
        print("="*60 + "\n")
        
        await page.wait_for_timeout(10000)
        
        # Retrieve the filtered telemetry
        telemetry = await page.evaluate("window.__webai_telemetry")
        
        print("📊 FILTERED TELEMETRY RESULTS:")
        if not telemetry:
            print("  [Empty] No valid clicks captured.")
        else:
            for i, event in enumerate(telemetry):
                print(f"  [{i+1}] Tag: <{event['tag']}> | CSS: {event['css']}")
                print(f"      Text: '{event['text']}'\n")
        
        print("✅ Test complete. Closing browser.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())