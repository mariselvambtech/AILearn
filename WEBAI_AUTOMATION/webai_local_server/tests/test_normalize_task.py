from webai_local_server.local_webai_server import normalize_task

def test_short_task_normalizes():
    t = 'launch https://sujaypublicschool.com and click contact us'
    out = normalize_task(t)
    assert "Goal:" in out
    assert "Requirements:" in out
    assert "Success criteria:" in out
    assert "https://sujaypublicschool.com" in out

def test_structured_task_unchanged():
    t = "Goal:\n- Do X\n\nRequirements:\n- Do Y\n\nSuccess criteria:\n- Do Z"
    out = normalize_task(t)
    assert out == t
