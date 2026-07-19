"""
Test suite for verifying CDP and Playwright Actions fixes
"""
import asyncio
import pytest
from playwright.async_api import async_playwright


@pytest.mark.asyncio
async def test_cdp_get_dom_snapshot():
    """Test that cdp.get_dom_snapshot works correctly"""
    from webai_playwright import cdp
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("about:blank")
        
        # Test get_dom_snapshot
        result = await cdp.get_dom_snapshot(page)
        assert result is not None
        assert isinstance(result, dict)
        
        await browser.close()


@pytest.mark.asyncio
async def test_cdp_get_interactive_elements():
    """Test that cdp.get_interactive_elements works correctly"""
    from webai_playwright import cdp
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Create a simple HTML page with interactive elements
        await page.set_content("""
            <html>
                <body>
                    <button id="btn1">Click Me</button>
                    <a href="#">Link</a>
                    <input type="text" placeholder="Enter text" />
                    <select><option>Option 1</option></select>
                </body>
            </html>
        """)
        
        # Test get_interactive_elements
        elements = await cdp.get_interactive_elements(page)
        assert elements is not None
        assert isinstance(elements, list)
        assert len(elements) > 0
        
        # Verify structure
        for element in elements:
            assert isinstance(element, dict)
            assert 'tag' in element
            assert 'type' in element
            
        await browser.close()


@pytest.mark.asyncio
async def test_playwright_actions_get_dom_snapshot():
    """Test that playwright_actions.get_dom_snapshot works correctly"""
    from webai_playwright import playwright_actions as pw
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("about:blank")
        
        # Test get_dom_snapshot
        result = await pw.get_dom_snapshot(page)
        assert result is not None
        assert isinstance(result, dict)
        assert 'dom' in result
        
        await browser.close()


@pytest.mark.asyncio
async def test_playwright_actions_get_interactive_elements():
    """Test that playwright_actions.get_interactive_elements works correctly"""
    from webai_playwright import playwright_actions as pw
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Create a simple HTML page with interactive elements
        await page.set_content("""
            <html>
                <body>
                    <button id="btn1">Click Me</button>
                    <a href="#">Link</a>
                    <input type="text" placeholder="Enter text" />
                </body>
            </html>
        """)
        
        # Test get_interactive_elements
        elements = await pw.get_interactive_elements(page)
        assert elements is not None
        assert isinstance(elements, list)
        assert len(elements) >= 3  # button, link, input
        
        await browser.close()


@pytest.mark.asyncio
async def test_playwright_actions_get_snapshot():
    """Test that playwright_actions.get_snapshot works correctly"""
    from webai_playwright import playwright_actions as pw
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("about:blank")
        
        # Test get_snapshot
        result = await pw.get_snapshot(page)
        assert result is not None
        assert isinstance(result, dict)
        assert 'dom' in result
        assert 'screenshot' in result
        assert 'pixelRatio' in result
        assert 'viewportWidth' in result
        assert 'viewportHeight' in result
        
        await browser.close()


if __name__ == "__main__":
    # Run tests manually
    print("Running CDP and Playwright Actions tests...")
    
    asyncio.run(test_cdp_get_dom_snapshot())
    print("✅ test_cdp_get_dom_snapshot passed")
    
    asyncio.run(test_cdp_get_interactive_elements())
    print("✅ test_cdp_get_interactive_elements passed")
    
    asyncio.run(test_playwright_actions_get_dom_snapshot())
    print("✅ test_playwright_actions_get_dom_snapshot passed")
    
    asyncio.run(test_playwright_actions_get_interactive_elements())
    print("✅ test_playwright_actions_get_interactive_elements passed")
    
    asyncio.run(test_playwright_actions_get_snapshot())
    print("✅ test_playwright_actions_get_snapshot passed")
    
    print("\n✅ All tests passed!")
