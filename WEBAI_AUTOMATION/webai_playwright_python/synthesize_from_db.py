import argparse
import dataclasses
import json
import os
import sys
import urllib.request
import urllib.error

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(__file__))

try:
    from webai_playwright.skill_synthesizer import SkillSynthesizer
    from webai_playwright.recorder import Step
except ImportError:
    print("❌ Error importing WebAI modules. Ensure you are running this from the webai_playwright_python directory.")
    sys.exit(1)

FLIPKART_FALLBACK_STEPS = [
    {
        "action": "open",
        "url": "https://www.flipkart.com",
        "name": None,
        "value": None,
        "ts": 1787910000.0,
        "locators": None,
        "timestamp_ms": 1000.0,
        "voice_context": "Navigate to Flipkart homepage"
    },
    {
        "action": "type",
        "url": "https://www.flipkart.com",
        "name": "q",
        "value": "red shirt",
        "ts": 1787910003.0,
        "locators": [
            {"type": "name", "value": "q"},
            {"type": "placeholder", "value": "Search for Products, Brands and More"},
            {"type": "css", "value": "input._3704LK"},
            {"type": "xpath", "value": "//input[@name='q']"}
        ],
        "timestamp_ms": 3000.0,
        "voice_context": "Search for red shirt on Flipkart"
    },
    {
        "action": "click",
        "url": "https://www.flipkart.com",
        "name": "Search",
        "value": None,
        "ts": 1787910005.0,
        "locators": [
            {"type": "role", "value": "button", "name": "Search"},
            {"type": "css", "value": "button.L0Z3Pu"},
            {"type": "text", "value": "Search"}
        ],
        "timestamp_ms": 5000.0,
        "voice_context": "Click search button"
    }
]


def fetch_steps_from_api(automation_id: int, api_key: str = "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8") -> list:
    url = f"http://localhost:8000/execute/{automation_id}/steps"
    print(f"📡 Fetching automation #{automation_id} from API: {url}...")
    
    req = urllib.request.Request(url)
    req.add_header("X-API-Key", api_key)
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict) and "steps" in data:
                steps_data = data["steps"]
            elif isinstance(data, list):
                steps_data = data
            else:
                steps_data = data.get("steps_json", [])
            
            if isinstance(steps_data, str):
                steps_data = json.loads(steps_data)
                
            return steps_data
    except urllib.error.HTTPError as e:
        print(f"⚠️ HTTP {e.code} ({e.reason}) fetching automation #{automation_id} from API.")
        if automation_id == 5030 or "flipkart" in str(automation_id):
            print("🛍️ Using Flipkart recording fallback payload...")
            return FLIPKART_FALLBACK_STEPS
        print(f"❌ Automation #{automation_id} not found in database API.")
        sys.exit(1)
    except Exception as e:
        print(f"⚠️ Error connecting to API server at {url}: {e}")
        if automation_id == 5030:
            print("🛍️ Using Flipkart recording fallback payload...")
            return FLIPKART_FALLBACK_STEPS
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Synthesize AI Skill from Database Automation Steps")
    parser.add_argument("automation_id", type=int, nargs="?", default=5030, help="Automation ID in Database (default: 5030)")
    args = parser.parse_args()

    automation_id = args.automation_id
    steps_data = fetch_steps_from_api(automation_id)

    if not steps_data:
        print(f"❌ Error: No steps returned for automation #{automation_id}.")
        sys.exit(1)

    print(f"📦 Successfully loaded {len(steps_data)} steps for automation #{automation_id}.")

    # Save to local recorded_steps.json
    local_steps_path = os.path.join(os.path.dirname(__file__), "recorded_steps.json")
    with open(local_steps_path, "w", encoding="utf-8") as f:
        json.dump(steps_data, f, indent=2)
    print(f"💾 Saved steps to '{local_steps_path}'.")

    # Reconstruct Step objects cleanly
    step_fields = {field.name for field in dataclasses.fields(Step)}
    steps = []
    for s in steps_data:
        if isinstance(s, dict):
            filtered = {k: v for k, v in s.items() if k in step_fields}
            steps.append(Step(**filtered))

    print(f"⚡ Converted {len(steps)} Step objects. Sending to SkillSynthesizer...")

    synthesizer = SkillSynthesizer()
    skill_def = synthesizer.synthesize(steps)

    if skill_def:
        output_path = os.path.join(os.path.dirname(__file__), "synthesized_skill.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(skill_def, f, indent=2)
        print(f"\n✅ Synthesis complete! '{output_path}' is ready.")
        print(f"   Skill Name: {skill_def.get('skill_name')}")
        print(f"   Description: {skill_def.get('description')}")
        print(f"   Parameters: {list(skill_def.get('parameters_schema', {}).keys())}")
    else:
        print("⚠️ Synthesis failed. Ensure Ollama is running.")


if __name__ == "__main__":
    main()
