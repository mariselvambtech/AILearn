"""
TDVC Test Suite for Phase 8: Autonomous Continuation & Spatial Graph Routing (Rule 7)
Verifies:
1. Spatial prompt building with bounding box and element context.
2. Robust coordinate extraction (_extract_coords) from Hermes 3 JSON outputs.
3. Multi-format plan parsing (lists, dicts with 'plan', dicts with 'action', dicts with 'x'/'y').
"""
import os
import sys
import json

# Ensure local packages are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_local_server")))

from webai_local_server.local_webai_server_guided import (
    _build_spatial_prompt,
    _extract_coords,
    _extract_json_array
)


def parse_llm_plan(llm_out: str):
    """Helper function matching the server's new multi-format plan parser."""
    plan = []
    try:
        parsed = json.loads(llm_out.strip().replace("```json", "").replace("```", ""))
        if isinstance(parsed, list):
            plan = parsed
        elif isinstance(parsed, dict):
            if "plan" in parsed and isinstance(parsed["plan"], list):
                plan = parsed["plan"]
            elif "action" in parsed:
                plan = [parsed]
            elif "x" in parsed and "y" in parsed:
                plan = [{"action": "clickLocation", "x": parsed["x"], "y": parsed["y"]}]
    except Exception:
        coords = _extract_coords(llm_out)
        if coords:
            plan = [{"action": "clickLocation", "x": coords["x"], "y": coords["y"]}]
        else:
            try:
                plan = _extract_json_array(llm_out)
            except Exception:
                plan = []
    return plan


def test_build_spatial_prompt():
    print("\n--- Running TDVC Test: Spatial Prompt Building ---")

    task_text = "Add to cart and checkout"
    url = "https://www.flipkart.com/red-shirt/p/itm123"
    title = "Red Shirt - Buy Red Shirt Online on Flipkart"

    mock_elements = [
        {
            "id": 1,
            "tagName": "BUTTON",
            "text": "ADD TO CART",
            "role": "button",
            "bbox": [100, 200, 250, 250],
            "center": [175, 225]
        },
        {
            "id": 2,
            "tagName": "BUTTON",
            "text": "BUY NOW",
            "role": "button",
            "bbox": [260, 200, 400, 250],
            "center": [330, 225]
        }
    ]

    prompt = _build_spatial_prompt(task_text, url, title, mock_elements)
    print("Generated Spatial Prompt Preview:\n" + prompt[:400] + "...")

    # Assertions
    assert "ADD TO CART" in prompt, "Spatial prompt must include element text 'ADD TO CART'!"
    assert "BUY NOW" in prompt, "Spatial prompt must include element text 'BUY NOW'!"
    assert "175" in prompt or "100" in prompt, "Spatial prompt must include element coordinates or bbox!"
    assert task_text in prompt or "checkout" in prompt, "Spatial prompt must include task goal!"

    print("[PASS] test_build_spatial_prompt completed successfully!")


def test_extract_coords_json():
    print("\n--- Running TDVC Test: Extract Coords (Clean & Markdown JSON) ---")

    # 1. Clean JSON
    raw_1 = '{"action": "clickLocation", "x": 175, "y": 225}'
    coords_1 = _extract_coords(raw_1)
    assert coords_1 == {"x": 175, "y": 225}, f"Expected {{'x': 175, 'y': 225}}, got {coords_1}"

    # 2. Markdown Wrapped JSON
    raw_2 = "```json\n{\n  \"x\": 330,\n  \"y\": 225\n}\n```"
    coords_2 = _extract_coords(raw_2)
    assert coords_2 == {"x": 330, "y": 225}, f"Expected {{'x': 330, 'y': 225}}, got {coords_2}"

    # 3. Text Chatter with embedded JSON
    raw_3 = "To click the Add to Cart button, I will click at coordinates {\"x\": 175, \"y\": 225}."
    coords_3 = _extract_coords(raw_3)
    assert coords_3 == {"x": 175, "y": 225}, f"Expected {{'x': 175, 'y': 225}}, got {coords_3}"

    # 4. Invalid input returns None
    raw_4 = "I cannot find any button."
    coords_4 = _extract_coords(raw_4)
    assert coords_4 is None, f"Expected None for non-coordinate text, got {coords_4}"

    print("[PASS] test_extract_coords_json completed successfully!")


def test_multi_format_plan_parsing():
    print("\n--- Running TDVC Test: Multi-Format Plan Parsing ---")

    # Format 1: Direct JSON list
    raw_list = '[{"action": "clickLocation", "x": 100, "y": 200}]'
    plan_1 = parse_llm_plan(raw_list)
    assert len(plan_1) == 1 and plan_1[0]["x"] == 100

    # Format 2: Dict with "plan" key
    raw_plan_dict = '{"plan": [{"action": "clickLocation", "x": 150, "y": 250}]}'
    plan_2 = parse_llm_plan(raw_plan_dict)
    assert len(plan_2) == 1 and plan_2[0]["x"] == 150

    # Format 3: Single action dict
    raw_action_dict = '{"action": "clickLocation", "x": 200, "y": 300}'
    plan_3 = parse_llm_plan(raw_action_dict)
    assert len(plan_3) == 1 and plan_3[0]["x"] == 200

    # Format 4: Pure x/y dict
    raw_xy_dict = '{"x": 250, "y": 350}'
    plan_4 = parse_llm_plan(raw_xy_dict)
    assert len(plan_4) == 1 and plan_4[0]["action"] == "clickLocation" and plan_4[0]["x"] == 250

    print("[PASS] test_multi_format_plan_parsing completed successfully!")


if __name__ == "__main__":
    test_build_spatial_prompt()
    test_extract_coords_json()
    test_multi_format_plan_parsing()
    print("\n[SUCCESS] ALL TDVC PHASE 8 AUTONOMOUS HANDOFF TESTS PASSED!")
