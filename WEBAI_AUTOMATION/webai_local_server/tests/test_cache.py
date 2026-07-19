from webai_local_server.local_webai_server import _cache_key

def test_cache_key_stable():
    k1 = _cache_key("https://example.com/a", "Click Contact Us")
    k2 = _cache_key("https://example.com/a", "Click Contact Us")
    assert k1 == k2
