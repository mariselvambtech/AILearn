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
            .btn { padding: 15px 25px; background: #007bff; color: white; cursor: pointer; display: inline-block; font-weight: bold; border-radius: 5px; margin-bottom: 20px; }
            .fake-btn { padding: 15px 25px; background: #dc3545; color: white; cursor: pointer; display: inline-block; font-weight: bold; border-radius: 5px; margin-bottom: 20px; }
            .dead-space { width: 400px; height: 150px; background: #ddd; border: 3px dashed #999; display: flex; align-items: center; justify-content: center; color: transparent; }
        </style>
    </head>
    <body>
        <h2>🛡️ Shield 2: Mutation Observer Test</h2>
        
        <p>1. Click this button (It adds text to the screen → DOM Mutates → Should be CAPTURED):</p>
        <button class="btn" id="good-btn" onclick="let d = document.createElement('p'); d.innerText='DOM Mutated!'; document.body.appendChild(d);">Real Action Button</button>

        <br>
        <p>2. Click this red button (It has a valid role and text → Passes Shield 1 → but does NOTHING → Fails Shield 2 → Should be IGNORED):</p>
        <div class="fake-btn" id="fake-btn" role="button">Dead Button</div>

        <br>
        <p>3. Click this grey box (Fails Shield 1 immediately → Should be IGNORED):</p>
        <div class="dead-space" id="invalid-space">hidden text</div>
    </body>
    </html>
    """

    # The exact dual-shield JS payload Antigravity implemented
    telemetry_js = """
    () => {
        window.__webai_telemetry = window.__webai_telemetry || [];
        if (!window.__webai_telemetry_handler) {
            window.__webai_telemetry_handler = function(e) {
                if (e.target.closest('#webai-hitl-observer-panel')) return;
                
                const target = e.target;
                const tag = (target.tagName || '').toLowerCase();
                const isRootContainer = tag === 'body' || tag === 'html';
                const text = isRootContainer ? '' : (target.innerText || target.value || '').trim();
                
                const isInteractiveTag = ['a', 'button', 'input', 'select', 'textarea'].includes(tag);
                const hasInteractiveRole = Boolean(target.closest('[role="button"]') || target.hasAttribute('onclick'));
                const hasText = text.length > 0;

                // --- SHIELD 1: Semantic Filtering ---
                if (!isInteractiveTag && !hasInteractiveRole && !hasText) return;

                let css = tag;
                if (target.id) css += '#' + target.id;
                
                const telemetryEvent = { tag: tag, text: text.substring(0, 100), css: css, timestamp: Date.now() };

                // --- SHIELD 2: Mutation Observer ---
                const initialUrl = window.location.href;
                let stateChanged = false;

                const observer = new MutationObserver((mutations) => {
                    stateChanged = true;
                    observer.disconnect();
                });

                observer.observe(document.body, { childList: true, subtree: true, attributes: true, characterData: true });

                setTimeout(() => {
                    observer.disconnect();
                    if (stateChanged || window.location.href !== initialUrl) {
                        window.__webai_telemetry.push(telemetryEvent);
                    }
                }, 800);
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
        print("🚀 BROWSER READY: You have 12 seconds to click!")
        print("-> Click the blue 'Real Action Button'.")
        print("-> Click the red 'Dead Button' multiple times.")
        print("-> Click the grey dashed box.")
        print("="*60 + "\n")
        
        await page.wait_for_timeout(12000)
        
        # Wait an extra 1.5 seconds to ensure the final 800ms mutation timeout clears before extracting
        await page.wait_for_timeout(1500)
        
        # Retrieve the filtered telemetry
        telemetry = await page.evaluate("window.__webai_telemetry")
        
        print("📊 FILTERED TELEMETRY RESULTS (SHIELD 2):")
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