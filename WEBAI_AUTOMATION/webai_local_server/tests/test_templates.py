from webai_local_server.local_webai_server import build_system_prompt, extract_success_expectations

def test_navigation_template_included():
    t = "Open https://x.com and click 'Contact us'. Confirm URL contains 'contact-us'."
    e = extract_success_expectations(t)
    s = build_system_prompt(t, e)
    assert "NAVIGATION TEMPLATE" in s
    assert "Expected URL contains" in s

def test_search_template_included():
    t = "Go to google and search 'weather today' then press enter."
    e = extract_success_expectations(t)
    e["task_type"] = "search"
    s = build_system_prompt(t, e)
    assert "SEARCH TEMPLATE" in s
