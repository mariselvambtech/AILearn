import os
import json
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.append(os.path.dirname(__file__))

try:
    from webai_playwright.skill_synthesizer import SkillSynthesizer
    from webai_playwright.recorder import Step
except ImportError:
    print("❌ Error importing WebAI modules. Ensure you are running this from the webai_playwright_python directory.")
    sys.exit(1)

def main():
    print("🚀 Starting auto-synthesis of the latest recording...")
    steps_file = "recorded_steps.json"
    
    if not os.path.exists(steps_file) or os.path.getsize(steps_file) <= 2:
        parent_steps = os.path.join("..", "recorded_steps.json")
        if os.path.exists(parent_steps) and os.path.getsize(parent_steps) > 2:
            print(f"ℹ️ Found recording in parent directory ({parent_steps}), using it...")
            steps_file = parent_steps

    if not os.path.exists(steps_file) or os.path.getsize(steps_file) <= 2:
        print(f"❌ Error: {steps_file} not found or is empty.")
        sys.exit(1)
        
    with open(steps_file, "r", encoding="utf-8") as f:
        steps_data = json.load(f)
        
    # Reconstruct Step objects
    steps = [Step(**s) for s in steps_data]
    print(f"📦 Loaded {len(steps)} steps. Sending to SkillSynthesizer...")
    
    synthesizer = SkillSynthesizer()
    skill_def = synthesizer.synthesize(steps)
    
    if skill_def:
        print("✅ Synthesis complete! 'synthesized_skill.json' is ready.")
    else:
        print("⚠️ Synthesis failed. Ensure Ollama is running.")

if __name__ == "__main__":
    main()
