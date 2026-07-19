from webai_local_server.local_webai_server import compute_confidence

def test_confidence_high_when_verified():
    c = compute_confidence(progress_ok=True, strict=True, url_ok=True, text_ok=True, failures=0)
    assert c >= 90

def test_confidence_penalizes_failures():
    c1 = compute_confidence(progress_ok=True, strict=True, url_ok=True, text_ok=True, failures=0)
    c2 = compute_confidence(progress_ok=True, strict=True, url_ok=True, text_ok=True, failures=3)
    assert c2 < c1

def test_confidence_low_when_strict_but_not_verified():
    c = compute_confidence(progress_ok=True, strict=True, url_ok=False, text_ok=False, failures=0)
    assert c <= 60
