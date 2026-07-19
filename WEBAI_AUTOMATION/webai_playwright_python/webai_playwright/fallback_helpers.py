"""
Helper functions for fallback extraction strategies.
"""

from typing import List, Dict

# Locator priority: prefer stable selectors
LOCATOR_PRIORITY = {
    "test-id": 1,
    "id": 2,
    "name": 3,
    "placeholder": 4,
    "role": 5,
    "label": 6,
    "href": 7,
    "css": 8,
    "xpath": 9
}


async def click_with_fallback(page, locators: List[Dict]) -> bool:
    """
    Try multiple locators in priority order until one successfully clicks.
    
    Args:
        page: Playwright page
        locators: List of locator dicts like [{"type": "id", "value": "submit-btn"}, ...]
    
    Returns:
        True if any locator succeeded
        
    Raises:
        Exception if all locators failed
    """
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError

    sorted_locators = sorted(locators, key=lambda x: LOCATOR_PRIORITY.get(x.get("type"), 99))
    
    errors = []
    print(f"🔍 Attempting click with {len(sorted_locators)} locators...")
    
    for i, loc in enumerate(sorted_locators):
        loc_type = loc.get("type")
        loc_value = loc.get("value", "")
        
        try:
            print(f"  Attempt {i+1}/{len(sorted_locators)}: {loc_type}='{loc_value[:50]}'")
            
            # Create locator
            if loc_type == "test-id":
                loc_obj = page.get_by_test_id(loc_value)
            elif loc_type == "id":
                loc_obj = page.locator(f"#{loc_value}")
            elif loc_type == "name":
                loc_obj = page.locator(f"[name='{loc_value}']")
            elif loc_type == "href":
                loc_obj = page.locator(f"[href='{loc_value}']")
            elif loc_type == "placeholder":
                loc_obj = page.get_by_placeholder(loc_value)
            elif loc_type == "role":
                role_name = loc.get("name")
                if role_name:
                    loc_obj = page.get_by_role(loc_value, name=role_name)
                else:
                    loc_obj = page.get_by_role(loc_value)
            elif loc_type == "label":
                loc_obj = page.get_by_label(loc_value)
            elif loc_type == "css":
                loc_obj = page.locator(loc_value)
            elif loc_type == "xpath":
                loc_obj = page.locator(f"xpath={loc_value}")
            else:
                errors.append(f"{loc_type}: Unknown locator type")
                continue
            
            # Try clicking with timeout
            await loc_obj.click(timeout=5000)
            print(f"  ✅ Click successful with {loc_type}")
            return True
            
        except PlaywrightTimeoutError:
            error_msg = f"Element not found/clickable (timeout)"
            errors.append(f"{loc_type}: {error_msg}")
            print(f"  ❌ {error_msg}")
        except Exception as e:
            error_msg = str(e)[:100]
            errors.append(f"{loc_type}: {error_msg}")
            print(f"  ❌ {error_msg}")
    
    # All locators failed
    error_report = f"❌ All {len(sorted_locators)} locators failed for click:\\n"
    for err in errors:
        error_report += f"  • {err}\\n"
    raise Exception(error_report)


async def type_with_fallback(page, locators: List[Dict], text: str) -> bool:
    """
    Try multiple locators in priority order to type text.
    
    Args:
        page: Playwright page
        locators: List of locator dicts
        text: Text to type
    
    Returns:
        True if any locator succeeded
        
    Raises:
        Exception if all locators failed
    """
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError

    sorted_locators = sorted(locators, key=lambda x: LOCATOR_PRIORITY.get(x.get("type"), 99))
    
    errors = []
    print(f"🔍 Attempting type with {len(sorted_locators)} locators...")
    
    for i, loc in enumerate(sorted_locators):
        loc_type = loc.get("type")
        loc_value = loc.get("value", "")
        
        try:
            print(f"  Attempt {i+1}/{len(sorted_locators)}: {loc_type}='{loc_value[:50]}'")
            
            # Create locator (same as click_with_fallback)
            if loc_type == "test-id":
                loc_obj = page.get_by_test_id(loc_value)
            elif loc_type == "id":
                loc_obj = page.locator(f"#{loc_value}")
            elif loc_type == "name":
                loc_obj = page.locator(f"[name='{loc_value}']")
            elif loc_type == "placeholder":
                loc_obj = page.get_by_placeholder(loc_value)
            elif loc_type == "role":
                role_name = loc.get("name")
                if role_name:
                    loc_obj = page.get_by_role(loc_value, name=role_name)
                else:
                    loc_obj = page.get_by_role(loc_value)
            elif loc_type == "label":
                loc_obj = page.get_by_label(loc_value)
            elif loc_type == "css":
                loc_obj = page.locator(loc_value)
            elif loc_type == "xpath":
                loc_obj = page.locator(f"xpath={loc_value}")
            else:
                errors.append(f"{loc_type}: Unknown locator type")
                continue
            
            # Try typing
            await loc_obj.clear()
            await loc_obj.fill(text)
            print(f"  ✅ Type successful with {loc_type}")
            return True
            
        except PlaywrightTimeoutError:
            error_msg = f"Element not found/typeable (timeout)"
            errors.append(f"{loc_type}: {error_msg}")
            print(f"  ❌ {error_msg}")
        except Exception as e:
            error_msg = str(e)[:100]
            errors.append(f"{loc_type}: {error_msg}")
            print(f"  ❌ {error_msg}")
    
    # All locators failed
    error_report = f"❌ All {len(sorted_locators)} locators failed for type:\\n"
    for err in errors:
        error_report += f"  • {err}\\n"
    raise Exception(error_report)


async def select_with_fallback(page, locators: List[Dict], value: str) -> bool:
    """
    Try multiple locators in priority order to select a dropdown value.
    
    Args:
        page: Playwright page
        locators: List of locator dicts
        value: Value to select
    
    Returns:
        True if any locator succeeded
        
    Raises:
        Exception if all locators failed
    """
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError

    sorted_locators = sorted(locators, key=lambda x: LOCATOR_PRIORITY.get(x.get("type"), 99))
    
    errors = []
    print(f"🔍 Attempting select with {len(sorted_locators)} locators...")
    
    for i, loc in enumerate(sorted_locators):
        loc_type = loc.get("type")
        loc_value = loc.get("value", "")
        
        try:
            print(f"  Attempt {i+1}/{len(sorted_locators)}: {loc_type}='{loc_value[:50]}'")
            
            # Create locator
            if loc_type == "id":
                loc_obj = page.locator(f"#{loc_value}")
            elif loc_type == "name":
                loc_obj = page.locator(f"[name='{loc_value}']")
            elif loc_type == "css":
                loc_obj = page.locator(loc_value)
            elif loc_type == "xpath":
                loc_obj = page.locator(f"xpath={loc_value}")
            else:
                errors.append(f"{loc_type}: Unsupported locator for select")
                continue
            
            # Try selecting
            await loc_obj.select_option(value)
            print(f"  ✅ Select successful with {loc_type}")
            return True
            
        except PlaywrightTimeoutError:
            error_msg = f"Element not found (timeout)"
            errors.append(f"{loc_type}: {error_msg}")
            print(f"  ❌ {error_msg}")
        except Exception as e:
            error_msg = str(e)[:100]
            errors.append(f"{loc_type}: {error_msg}")
            print(f"  ❌ {error_msg}")
    
    # All locators failed
    error_report = f"❌ All {len(sorted_locators)} locators failed for select:\\n"
    for err in errors:
        error_report += f"  • {err}\\n"
    raise Exception(error_report)


async def extract_with_fallback(page, locators: List[Dict], extract_type: str, 
                                attribute_name: str = None) -> str:
    """
    Extract data using fallback locator strategy.
    
    Args:
        page: Playwright page
        locators: List of locators to try
        extract_type: 'text' or 'attribute'
        attribute_name: Attribute to extract (if extract_type='attribute')
    
    Returns:
        Extracted value as string
        
    Raises:
        Exception if all locators failed
    """
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError

    sorted_locators = sorted(locators, key=lambda x: LOCATOR_PRIORITY.get(x.get("type"), 99))
    
    errors = []
    print(f"🔍 Extracting using {len(sorted_locators)} locators...")
    
    for i, loc in enumerate(sorted_locators):
        loc_type = loc.get("type")
        loc_value = loc.get("value", "")
        
        try:
            print(f"  Attempt {i+1}/{len(sorted_locators)}: {loc_type}='{loc_value[:50]}'")
            
            # Create locator (reuse logic from click_with_fallback)
            if loc_type == "test-id":
                loc_obj = page.get_by_test_id(loc_value)
            elif loc_type == "id":
                loc_obj = page.locator(f"#{loc_value}")
            elif loc_type == "name":
                loc_obj = page.locator(f"[name='{loc_value}']")
            elif loc_type == "href":
                loc_obj = page.locator(f"[href='{loc_value}']")
            elif loc_type == "placeholder":
                loc_obj = page.get_by_placeholder(loc_value)
            elif loc_type == "role":
                role_name = loc.get("name")
                if role_name:
                    loc_obj = page.get_by_role(loc_value, name=role_name)
                else:
                    loc_obj = page.get_by_role(loc_value)
            elif loc_type == "label":
                loc_obj = page.get_by_label(loc_value)
            elif loc_type == "css":
                loc_obj = page.locator(loc_value)
            elif loc_type == "xpath":
                loc_obj = page.locator(f"xpath={loc_value}")
            else:
                errors.append(f"{loc_type}: Unknown locator type")
                continue
            
            # Extract data
            if extract_type == "text":
                value = await loc_obj.inner_text(timeout=5000)
            else:  # attribute
                value = await loc_obj.get_attribute(attribute_name, timeout=5000)
                if value is None:
                    value = ""
            
            print(f"  ✅ Extraction successful: '{value[:100]}'")
            return value
            
        except PlaywrightTimeoutError:
            error_msg = f"Element not found (timeout)"
            errors.append(f"{loc_type}: {error_msg}")
            print(f"  ❌ {error_msg}")
        except Exception as e:
            error_msg = str(e)[:100]
            errors.append(f"{loc_type}: {error_msg}")
            print(f"  ❌ {error_msg}")
    
    # All locators failed
    error_report = f"❌ All {len(sorted_locators)} locators failed for extraction:\\n"
    for err in errors:
        error_report += f"  • {err}\\n"
    raise Exception(error_report)


async def extract_table_data(page, table_selector: str, column_indices: List[int], 
                             columns: List[str], max_pages: int = 1, 
                             wait_per_page: float = 2.0, page_timeout: float = 10.0,
                             retry_attempts: int = 3) -> Dict:
    """
    Extract table data with pagination support and robust change detection.
    
    Args:
        page: Playwright page
        table_selector: CSS selector for the table
        column_indices: List of column indices to extract
        columns: List of column names corresponding to indices
        max_pages: Maximum number of pages to extract (pagination)
        wait_per_page: Seconds to wait after page change for stability (default: 2.0)
        page_timeout: Max seconds to wait for table to change (default: 10.0)
        retry_attempts: Number of retry attempts if duplicate data detected (default: 3)
    
    Returns:
        Dict with success, data (list of row dicts), and row_count
    """
    print(f"📊 Extracting table: {table_selector}")
    print(f"   Columns: {columns}")
    print(f"   Max pages: {max_pages}, Wait: {wait_per_page}s, Timeout: {page_timeout}s, Retries: {retry_attempts}")
    
    try:
        # JavaScript to extract table data with enhanced pagination
        result = await page.evaluate("""
            async (config) => {
                const { tableSelector, columnIndices, columns, maxPages, 
                        waitPerPage, pageTimeout, retryAttempts } = config;
                
                // Helper: Extract rows from current table state
                function extractPageRows(table, indices, colNames) {
                    const rows = Array.from(table.querySelectorAll('tbody tr'));
                    return rows.map(row => {
                        const cells = Array.from(row.querySelectorAll('td, th'));
                        const rowData = {};
                        indices.forEach((idx, i) => {
                            if (idx < cells.length) {
                                rowData[colNames[i]] = cells[idx].innerText.trim();
                            }
                        });
                        return rowData;
                    }).filter(row => Object.keys(row).length > 0);
                }
                
                // Helper: Create hash from rows to detect changes
                function hashRows(rows) {
                    if (rows.length === 0) return '';
                    const first = JSON.stringify(rows[0]);
                    const last = JSON.stringify(rows[rows.length - 1]);
                    return first + '|' + last + '|' + rows.length;
                }
                
                // Helper: Find Next button
                function findNextButton() {
                    const buttons = document.querySelectorAll('button, a');
                    for (const btn of buttons) {
                        const text = btn.innerText.toLowerCase();
                        if (text.includes('next') || text === '>' || 
                            btn.getAttribute('aria-label')?.toLowerCase().includes('next')) {
                            return btn;
                        }
                    }
                    return null;
                }
                
                // Main extraction logic
                const table = document.querySelector(tableSelector);
                if (!table) {
                    console.error('❌ Table not found:', tableSelector);
                    return { success: false, data: [], row_count: 0, error: 'Table not found' };
                }
                
                console.log('📊 Table found:', table);
                
                let allData = [];
                let currentPage = 1;
                const extractedHashes = new Set();
                
                while (currentPage <= maxPages) {
                    console.log(`📄 Page ${currentPage}/${maxPages}...`);
                    
                    // STEP 1: Extract current page data
                    let pageData = extractPageRows(table, columnIndices, columns);
                    let pageHash = hashRows(pageData);
                    
                    console.log(`  Extracted ${pageData.length} rows, hash: ${pageHash.substring(0, 30)}...`);
                    
                    // STEP 2: Retry if duplicate detected
                    let retryCount = 0;
                    while (extractedHashes.has(pageHash) && retryCount < retryAttempts) {
                        console.log(`  ⚠️ Duplicate data detected, retry ${retryCount + 1}/${retryAttempts}...`);
                        await new Promise(resolve => setTimeout(resolve, waitPerPage * 1000));
                        pageData = extractPageRows(table, columnIndices, columns);
                        pageHash = hashRows(pageData);
                        retryCount++;
                    }
                    
                    if (extractedHashes.has(pageHash)) {
                        console.log(`  ❌ Still duplicate after ${retryAttempts} retries, stopping pagination`);
                        break;
                    }
                    
                    // STEP 3: Store unique data
                    extractedHashes.add(pageHash);
                    allData.push(...pageData);
                    console.log(`  ✅ Added ${pageData.length} unique rows (total: ${allData.length})`);
                    
                    if (currentPage >= maxPages) break;
                    
                    // STEP 4: Find Next button
                    const nextBtn = findNextButton();
                    if (!nextBtn || nextBtn.disabled) {
                        console.log('  ℹ️ No more pages (Next button not found or disabled)');
                        break;
                    }
                    
                    // STEP 5: Store reference for change detection
                    const oldHash = pageHash;
                    
                    // STEP 6: Click Next
                    console.log('  🔄 Navigating to next page...');
                    nextBtn.click();
                    
                    // STEP 7: Wait for table to change (with timeout)
                    const startTime = Date.now();
                    let changed = false;
                    
                    while ((Date.now() - startTime) < (pageTimeout * 1000)) {
                        await new Promise(resolve => setTimeout(resolve, 100));
                        
                        const currentData = extractPageRows(table, columnIndices, columns);
                        const currentHash = hashRows(currentData);
                        
                        if (currentHash !== oldHash) {
                            const elapsedMs = Date.now() - startTime;
                            console.log(`  ✅ Table updated after ${elapsedMs}ms`);
                            changed = true;
                            break;
                        }
                    }
                    
                    if (!changed) {
                        console.log(`  ⚠️ Timeout: Table didn't change after ${pageTimeout}s, stopping pagination`);
                        break;
                    }
                    
                    // STEP 8: Additional wait for stability
                    await new Promise(resolve => setTimeout(resolve, waitPerPage * 1000));
                    currentPage++;
                }
                
                console.log(`✅ Extraction complete: ${allData.length} total rows from ${currentPage} pages`);
                return { success: true, data: allData, row_count: allData.length };
            }
        """, {
            "tableSelector": table_selector,
            "columnIndices": column_indices,
            "columns": columns,
            "maxPages": max_pages,
            "waitPerPage": wait_per_page,
            "pageTimeout": page_timeout,
            "retryAttempts": retry_attempts
        })
        
        print(f"✅ Table extraction complete: {result.get('row_count', 0)} rows")
        return result
        
    except Exception as e:
        print(f"❌ Table extraction failed: {e}")
        return {"success": False, "data": [], "row_count": 0, "error": str(e)}


async def validate_page(page, expected_url: str, timeout_ms: int = 10000):
    """
    Validate that the page URL contains the expected URL substring.
    
    Args:
        page: Playwright page
        expected_url: Expected URL substring
        timeout_ms: Timeout in milliseconds
    
    Returns:
        True if valid, raises exception if not
    """
    import asyncio
    
    start_time = asyncio.get_event_loop().time()
    timeout_seconds = timeout_ms / 1000
    
    while True:
        current_url = page.url
        if expected_url in current_url:
            print(f"✅ Page URL validated: {current_url}")
            return True
        
        elapsed = asyncio.get_event_loop().time() - start_time
        if elapsed >= timeout_seconds:
            raise Exception(f"Page validation failed: expected '{expected_url}' in URL, got '{current_url}'")
        
        await asyncio.sleep(0.1)
