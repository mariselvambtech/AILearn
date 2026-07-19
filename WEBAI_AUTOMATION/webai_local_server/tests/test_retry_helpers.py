from webai_local_server.local_webai_server import _looks_like_not_found, _looks_like_navigation_issue

def test_not_found_patterns():
    assert _looks_like_not_found("TimeoutError: locator not found") is True
    assert _looks_like_not_found("No node found for selector") is True
    assert _looks_like_not_found("random error") is False

def test_navigation_patterns():
    assert _looks_like_navigation_issue("Navigation failed because net::ERR_NAME_NOT_RESOLVED") is True
    assert _looks_like_navigation_issue("Frame was detached") is True
    assert _looks_like_navigation_issue("element not found") is False
