import asyncio
import sys
import os
import json
from playwright.async_api import async_playwright

# Ensure we can import from the playwright client directory
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'webai_playwright_python'))

try:
    from webai_playwright.plugins.hitl_plugin import HITLPlugin
except ImportError:
    print("❌ HITLPlugin not found. Make sure Phase 10 is fully implemented.")
    sys.exit(1)

async def main():
    print("🚀 Starting HITL Live Confidence Test (Async Mode)...")
    
    # We now use async_playwright to perfectly match the real WebAI environment
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🌐 Loading example.com...")
        await page.goto("https://example.com")

        print("🔌 Initializing HITL Plugin...")
        hitl = HITLPlugin()

        print("\n" + "="*50)
        print("🎧 TRIGGERING INTERVENTION!")
        print("1. Listen for the TTS audio cue.")
        print("2. Speak a brief instruction into your microphone.")
        print("3. Click anywhere on the webpage (e.g., the 'More information' link).")
        print("="*50 + "\n")
        
        payload = {"reason": "manual_confidence_test"}

        try:
            # Since everything is async, we can just await the intervention naturally! No deadlocks.
            result = await hitl.trigger_intervention(page, payload)

            print("\n✅ HITL Resolution Successfully Captured:")
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"\n❌ Error during HITL intervention: {e}")

        finally:
            print("\nClosing browser in 5 seconds...")
            await page.wait_for_timeout(5000)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())