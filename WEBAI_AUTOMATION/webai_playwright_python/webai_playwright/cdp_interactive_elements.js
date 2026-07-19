// Script to extract interactive elements from the page
(() => {
    const elements = [];
    const candidates = document.querySelectorAll(
        'a, button, input, textarea, select, [role="button"], [role="link"], [onclick], [contenteditable="true"]'
    );

    for (const el of candidates) {
        if (!el.offsetParent && el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA') continue;

        const rect = el.getBoundingClientRect();
        if (rect.width < 2 || rect.height < 2) continue;

        const style = window.getComputedStyle(el);
        if (style.visibility === 'hidden' || style.display === 'none' || style.opacity === '0') continue;

        elements.push({
            tag: el.tagName.toLowerCase(),
            type: el.type || '',
            role: el.getAttribute('role') || el.getAttribute('aria-role') || '',
            name: (el.getAttribute('aria-label') || el.getAttribute('name') || el.textContent || '').trim().slice(0, 100),
            placeholder: el.getAttribute('placeholder') || '',
            ariaLabel: el.getAttribute('aria-label') || '',
            text: (el.textContent || '').trim().slice(0, 100),
            id: el.id || '',
            className: el.className || ''
        });

        if (elements.length >= 100) break;
    }

    return elements;
})()
