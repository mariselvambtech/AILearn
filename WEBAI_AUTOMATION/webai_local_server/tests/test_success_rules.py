from webai_local_server.local_webai_server import extract_success_expectations, url_meets_expectations

def test_extracts_url_contains():
    task = "Confirm the page navigated to contact-us (URL contains 'contact-us')."
    e = extract_success_expectations(task)
    assert "contact-us" in e["expected_url_substrings"]

def test_extracts_quoted_text():
    task = 'look for the words "Start the conversation to established good relationship and business."'
    e = extract_success_expectations(task)
    assert any("Start the conversation" in t for t in e["expected_texts"])

def test_url_meets_expectations():
    assert url_meets_expectations("https://x.com/contact-us", ["contact-us"]) is True
    assert url_meets_expectations("https://x.com/home", ["contact-us"]) is False
