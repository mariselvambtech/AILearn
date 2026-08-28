# record_then_run.py
# Ready-to-paste
# - Records user actions
# - Stops via: Stop button (bottom-right) OR Ctrl+Shift+S OR Ctrl+Alt+S OR Esc
# - After recording, asks: "Run AI after recording? (y/n)"
# - Saves: recorded_steps.json, generated_task.txt

"""
Dual-phase script: Record actions and immediately replay them.

This script launches an interactive browser where user actions are intercepted 
via the Chrome DevTools Protocol (CDP) and recorded into `recorded_steps.json`.
Once the user closes the browser, it immediately launches a new instance to 
replay the recorded JSON sequence.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

from playwright.async_api import async_playwright

# Robust imports even if you run from another folder
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from webai_playwright.recorder import WebRecorder
from webai_playwright import ai

OUTPUT_JSON = "recorded_steps.json"
OUTPUT_TASK = "generated_task.txt"
START_URL = os.environ.get("WEBAI_START_URL", "about:blank")


def ask_yes_no(prompt: str, default: str = "n") -> bool:
    default = default.lower().strip()
    while True:
        ans = input(f"{prompt} (y/n) [default: {default}]: ").strip().lower()
        if not ans:
            ans = default
        if ans in ("y", "yes"):
            return True
        if ans in ("n", "no"):
            return False
        print("Please enter y or n.")


async def main():
    recorder = WebRecorder()
    auto_import = os.environ.get("WEBAI_AUTO_IMPORT") == "1"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await recorder.attach_context(context)
        await page.goto(START_URL)

        print("\n=== Web Recorder Started ===")
        print(f"Target URL: {START_URL}")
        print("Do actions in the browser.")
        print("Stop options:")
        print("  - Click Stop Recording button (bottom-right)")
        print("  - Ctrl+Shift+S or Ctrl+Alt+S or Esc")
        print("Verify options:")
        print("  - Ctrl+Shift+V -> Verify page contains text")
        print("  - Ctrl+Shift+E -> Verify element visible (then click element)")
        print("============================\n")

        # Wait until stopped from inside the browser
        await recorder.wait_for_stop()

        # Save outputs
        steps_json = recorder.to_json()
        task_text = recorder.to_task_text()

        Path(OUTPUT_JSON).write_text(json.dumps(steps_json, indent=2), encoding="utf-8")
        Path(OUTPUT_TASK).write_text(task_text, encoding="utf-8")

        # Phase 2: Post-recording audio transcription & spoken context alignment
        audio_file = "session_audio.wav"
        if os.path.exists(audio_file) and os.path.getsize(audio_file) > 100:
            try:
                print("\n[AudioAligner] Transcribing recorded audio session...")
                from webai_playwright.audio_aligner import AudioAligner
                aligner = AudioAligner()
                segments = aligner.transcribe_audio(audio_file)
                if segments:
                    steps_json = aligner.align_steps(steps_json, segments)
                    Path(OUTPUT_JSON).write_text(json.dumps(steps_json, indent=2), encoding="utf-8")
                    print(f" [AudioAligner] Enriched {OUTPUT_JSON} with voice_context tags.")
            except Exception as e:
                print(f" [WARN] [AudioAligner] Audio transcription skipped: {e}")

        # Phase 3: AI Skill Synthesis & Auto-Parameterization
        synthesize_skill = False if auto_import else ask_yes_no("Synthesize into AI Skill?", default="y")
        if synthesize_skill:
            try:
                print("\n[SkillSynthesizer] Synthesizing recorded steps into reusable AI Skill...")
                from webai_playwright.skill_synthesizer import SkillSynthesizer
                synthesizer = SkillSynthesizer()
                skill_recipe = synthesizer.synthesize(steps_json)
                output_skill = "synthesized_skill.json"
                Path(output_skill).write_text(json.dumps(skill_recipe, indent=2), encoding="utf-8")
                print(f" [SkillSynthesizer] Saved skill recipe: {output_skill}")
                print(f" Skill Name: {skill_recipe.get('skill_name')}")
                print(f" Parameters: {list(skill_recipe.get('parameters_schema', {}).keys())}")
            except Exception as e:
                print(f" [WARN] [SkillSynthesizer] Skill synthesis skipped: {e}")

        print(f"\nSaved: {OUTPUT_JSON}")
        print(f"Saved: {OUTPUT_TASK}")
        print("\n=== GENERATED TASK ===\n")
        print(task_text)
        print("\n======================\n")

        run_ai = False if auto_import else ask_yes_no("Run AI after recording?", default="n")

        if run_ai:
            print("\nRunning AI health-check with generated TASK...\n")
            result = await ai(task_text, page=page)
            print("\n=== AI RESULT ===")
            print(result)
            print("=================\n")

        await browser.close()

        # Upload recording to SQL database
        save_db = True if auto_import else ask_yes_no("Save this recording to SQL database?", default="y")
        if save_db:
            try:
                import import_to_database
                print("\n=== Uploading Recording to SQL Database ===")
                if auto_import:
                    rec_name = os.environ.get("WEBAI_AUTOMATION_NAME", "Recorded Automation")
                    rec_desc = os.environ.get("WEBAI_AUTOMATION_DESC", "Recorded via Dashboard")
                    api_key = os.environ.get("WEBAI_API_KEY")
                    api_url = os.environ.get("WEBAI_API_URL", "http://localhost:8000")
                    if api_key:
                        import_to_database.import_recording(steps_json, rec_name, rec_desc, api_key, api_url)
                    else:
                        import_to_database.main()
                else:
                    import_to_database.main()
            except Exception as db_err:
                print(f"Failed to upload to SQL database: {db_err}")


if __name__ == "__main__":
    asyncio.run(main())
