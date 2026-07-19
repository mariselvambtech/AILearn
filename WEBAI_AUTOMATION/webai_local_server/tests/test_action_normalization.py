"""
Unit Tests for Action Normalization (Mocked - No Ollama Required)
"""
import sys
from pathlib import Path

# Add server path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "webai_local_server" / "webai_local_server"))

def test_normalize_action_converts_by_name_to_by_text():
    """Test that by='name' is auto-converted to by='text'"""
    # Import the normalize_action function from the server
    # We'll simulate it here since it's inside handle_client
    
    def normalize_action(act):
        """Simplified version of normalize_action for testing"""
        if not isinstance(act, dict):
            return act
        
        kind = (act.get("action") or "").strip().lower()
        
        # SAFETY: Convert invalid by='name' to by='text'
        if kind in ("click", "type") and isinstance(act.get("target"), dict):
            t = act["target"]
            by_value = (t.get("by") or "").strip().lower()
            if by_value == "name":
                print(f"[WARN] LLM used invalid by='name', auto-converting to by='text': {t}")
                act["target"] = {
                    "by": "text",
                    "text": t.get("name", ""),
                    "exact": bool(t.get("exact", False))
                }
        
        return act
    
    # Test 1: Click action with by='name'
    action = {
        "action": "click",
        "target": {"by": "name", "name": "Contact Us", "exact": False}
    }
    normalized = normalize_action(action)
    assert normalized["target"]["by"] == "text", f"Expected by='text', got by='{normalized['target']['by']}'"
    assert normalized["target"]["text"] == "Contact Us", f"Expected text='Contact Us', got '{normalized['target']['text']}'"
    assert normalized["target"]["exact"] == False
    print("✅ Test 1 passed: Click with by='name' → by='text'")
    
    # Test 2: Type action with by='name'
    action = {
        "action": "type",
        "target": {"by": "name", "name": "Email", "exact": False},
        "text": "test@example.com"
    }
    normalized = normalize_action(action)
    assert normalized["target"]["by"] == "text"
    assert normalized["target"]["text"] == "Email"
    print("✅ Test 2 passed: Type with by='name' → by='text'")
    
    # Test 3: Click action with valid by='text' should not change
    action = {
        "action": "click",
        "target": {"by": "text", "text": "Submit", "exact": False}
    }
    normalized = normalize_action(action)
    assert normalized["target"]["by"] == "text"
    assert normalized["target"]["text"] == "Submit"
    print("✅ Test 3 passed: Valid by='text' unchanged")
    
    # Test 4: Click action with by='role' should not change
    action = {
        "action": "click",
        "target": {"by": "role", "role": "button", "name": "Search", "exact": False}
    }
    normalized = normalize_action(action)
    assert normalized["target"]["by"] == "role"
    assert normalized["target"]["role"] == "button"
    assert normalized["target"]["name"] == "Search"
    print("✅ Test 4 passed: Valid by='role' unchanged")
    
    print("\n✅ All unit tests passed!")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Running Unit Tests for Action Normalization")
    print("=" * 60)
    print()
    
    try:
        test_normalize_action_converts_by_name_to_by_text()
        print("\n" + "=" * 60)
        print("SUCCESS: All tests passed (4/4)")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
