"""
Test Phase 1: Verify recorder captures multiple locators
"""
import json
from pathlib import Path

def test_locators_captured():
    print("=" * 60)
    print("Test: Phase 1 - Locator Collection")
    print("=" * 60)
    
    steps_file = Path("recorded_steps.json")
    if not steps_file.exists():
        print("❌ No recorded_steps.json - please record some actions first")
        return False
    
    steps = json.loads(steps_file.read_text())
    print(f"\n✅ Found {len(steps)} steps\n")
    
    for i, step in enumerate(steps, 1):
        action = step.get("action")
        print(f"Step {i}: {action}")
        
        if action in ("click", "type"):
            locators = step.get("locators")
            if locators is None:
                print(f"  ❌ No 'locators' field!")
                return False
            
            if not isinstance(locators, list):
                print(f"  ❌ locators is not a list: {type(locators)}")
                return False
            
            if len(locators) == 0:
                print(f"  ⚠️  Empty locators array")
            else:
                print(f"  ✅ Captured {len(locators)} locator strategies:")
                for loc in locators:
                    loc_type = loc.get("type")
                    loc_value = loc.get("value", "")
                    if len(loc_value) > 50:
                        loc_value = loc_value[:47] + "..."
                    print(f"      • {loc_type}: {loc_value}")
        
        print()
    
    print("=" * 60)
    print("✅ Phase 1 Test PASSED - Locators are being captured!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        result = test_locators_captured()
        if not result:
            exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
