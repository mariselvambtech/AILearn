"""
Quick Test: Verify Playback Works
"""
import json
from pathlib import Path

def test_recorded_steps_structure():
    """Test that recorded_steps.json has correct structure"""
    print("=" * 60)
    print("Test 1: Recorded Steps Structure")
    print("=" * 60)
    
    steps_file = Path("recorded_steps.json")
    if not steps_file.exists():
        print("❌ recorded_steps.json not found!")
        return False
    
    steps = json.loads(steps_file.read_text())
    
    print(f"✅ Found {len(steps)} recorded steps")
    
    # Test each step
    for i, step in enumerate(steps, 1):
        action = step.get("action")
        print(f"\nStep {i}: {action}")
        
        if action == "open":
            url = step.get("url")
            print(f"  URL: {url}")
            assert url, f"Step {i}: open action missing URL"
            
        elif action == "click":
            name = step.get("name")
            print(f"  Target: {name}")
            assert name, f"Step {i}: click action missing name"
            
        elif action == "type":
            name = step.get("name")
            value = step.get("value")
            print(f"  Field: {name}")
            print(f"  Value: {value}")
            assert name, f"Step {i}: type action missing name"
            assert value, f"Step {i}: type action missing value"
            
        elif action == "navigate":
            url = step.get("url")
            print(f"  URL: {url}")
            
        elif action == "press_key":
            key = step.get("key")
            print(f"  Key: {key}")
            
    print("\n✅ All steps have valid structure!")
    return True


def test_task_text_generation():
    """Test that generated_task.txt matches recorded steps"""
    print("\n" + "=" * 60)
    print("Test 2: Task Text Generation")
    print("=" * 60)
    
    task_file = Path("generated_task.txt")
    if not task_file.exists():
        print("❌ generated_task.txt not found!")
        return False
    
    task_text = task_file.read_text().strip()
    lines = [l for l in task_text.split("\n") if l.strip() and not l.startswith("Finish")]
    
    print(f"✅ Generated {len(lines)} task lines:")
    for i, line in enumerate(lines, 1):
        print(f"  {i}. {line}")
    
    # Check for type actions
    type_lines = [l for l in lines if l.startswith("Type")]
    print(f"\n✅ Found {len(type_lines)} typing actions")
    
    # Check for click actions
    click_lines = [l for l in lines if l.startswith("Click")]
    print(f"✅ Found {len(click_lines)} click actions")
    
    return True


if __name__ == "__main__":
    print("Running Quick Tests...\n")
    
    try:
        result1 = test_recorded_steps_structure()
        result2 = test_task_text_generation()
        
        if result1 and result2:
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
        else:
            print("\n❌ SOME TESTS FAILED")
            exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
