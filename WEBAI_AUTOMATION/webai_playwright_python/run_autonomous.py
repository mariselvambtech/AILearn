"""
Purely autonomous, blank-slate AI browser navigation entry point.

This script reads a natural language prompt from `generated_task.txt` and relies
entirely on the local WebAI server for intelligent navigation without using any
pre-recorded JSON files (e.g., `recorded_steps.json`).
"""
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Ensure standard output uses UTF-8 to prevent Windows console crashes
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Ensure client directory is in sys.path
CLIENT_DIR = Path(__file__).resolve().parent
if str(CLIENT_DIR) not in sys.path:
    sys.path.insert(0, str(CLIENT_DIR))


class TaskComplete(Exception):
    """Exception or signal representing autonomous task completion."""
    pass


def slugify(name: str) -> str:
    """Converts a human-readable skill name into a safe, alphanumeric filename slug."""
    s = re.sub(r"[^\w\s-]", "", (name or "").lower()).strip()
    return re.sub(r"[-\s]+", "_", s) or "skill"


def save_synthesized_skill(
    skill_name: str,
    trigger_desc: str,
    action_history: List[Dict[str, Any]],
    base_skills_dir: Optional[Union[str, Path]] = None,
) -> Dict[str, Path]:
    """
    Saves the executed action history as a synthesized skill and updates the skill registry.

    Creates:
      1. {base_skills_dir}/{slug}/recorded_steps.json
      2. {base_skills_dir}/{slug}.json
      3. {base_skills_dir}/skills_registry.json (updated/appended)
    """
    if base_skills_dir is None:
        base_dir = CLIENT_DIR / "skills"
    else:
        base_dir = Path(base_skills_dir)

    base_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(skill_name)

    # 1. Directory and recorded_steps.json
    slug_dir = base_dir / slug
    slug_dir.mkdir(parents=True, exist_ok=True)
    recorded_steps_file = slug_dir / "recorded_steps.json"
    recorded_steps_file.write_text(json.dumps(action_history, indent=2, ensure_ascii=False), encoding="utf-8")

    # 2. Build parameterized steps and skill schema
    parameterized_steps = []
    for step in action_history:
        st_copy = dict(step)
        parameterized_steps.append(st_copy)

    skill_schema: Dict[str, Any] = {
        "skill_name": skill_name,
        "description": trigger_desc,
        "trigger_phrases": [
            trigger_desc,
            skill_name,
        ],
        "parameters_schema": {},
        "parameterized_steps": parameterized_steps,
        "recorded_steps_path": f"{slug}/recorded_steps.json",
    }
    skill_file = base_dir / f"{slug}.json"
    skill_file.write_text(json.dumps(skill_schema, indent=2, ensure_ascii=False), encoding="utf-8")

    # 3. Update skills_registry.json
    registry_file = base_dir / "skills_registry.json"
    registry_entries: List[Dict[str, Any]] = []
    if registry_file.exists():
        try:
            loaded = json.loads(registry_file.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                registry_entries = loaded
        except Exception:
            registry_entries = []

    # Update existing entry or append
    new_entry = {
        "skill_name": skill_name,
        "slug": slug,
        "description": trigger_desc,
        "skill_file": f"{slug}.json",
        "recorded_steps": f"{slug}/recorded_steps.json",
    }
    updated = False
    for i, entry in enumerate(registry_entries):
        if entry.get("slug") == slug or entry.get("skill_name") == skill_name:
            registry_entries[i] = new_entry
            updated = True
            break
    if not updated:
        registry_entries.append(new_entry)

    registry_file.write_text(json.dumps(registry_entries, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "slug_dir": slug_dir,
        "recorded_steps_path": recorded_steps_file,
        "skill_json_path": skill_file,
        "registry_path": registry_file,
    }


def _resolve_task_file() -> Path:
    """Find the task prompt file, checking local and parent directories."""
    candidates = [
        CLIENT_DIR / "generated_task.txt",
        Path("generated_task.txt"),
        CLIENT_DIR.parent / "generated_task.txt",
    ]
    for p in candidates:
        if p.exists():
            return p
    return CLIENT_DIR / "generated_task.txt"


async def main() -> None:
    """Main execution loop for purely autonomous AI navigation."""
    from playwright.async_api import async_playwright
    from webai_playwright.ai import ai, ClientError

    task_file = _resolve_task_file()
    if not task_file.exists():
        raise FileNotFoundError(f"Task file not found at: {task_file}")

    task_text = task_file.read_text(encoding="utf-8").strip()
    if not task_text:
        raise ValueError(f"Task file is empty: {task_file}")

    print(f"[run_autonomous] Loaded task from {task_file}:")
    print(f"  '{task_text}'\n")

    # Check for optional initial URL command (e.g. 'Open https://...')
    first_url = None
    open_re = re.compile(r"^\s*Open\s+(https?://\S+)\s*$", re.IGNORECASE | re.MULTILINE)
    m = open_re.search(task_text)
    if m:
        first_url = m.group(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            if first_url:
                print(f"[run_autonomous] Preloading initial URL: {first_url}")
                await page.goto(first_url, wait_until="domcontentloaded")
            else:
                print("[run_autonomous] Starting with blank slate (about:blank)")
                await page.goto("about:blank")

            print("[run_autonomous] Delegating navigation to local AI server...")
            # Pure autonomous execution: No recorded_steps loaded or passed
            result = await ai(task_text, page=page, options={"max_rounds": 25})

            print("\n=== AI RESULT ===")
            print(result)
            print("=================\n")

            # Skill Synthesis Prompt
            if result and result.get("success") and result.get("action_history"):
                try:
                    save_prompt = "✨ Task completed successfully! Would you like to save this workflow as a reusable skill? (y/n): "
                    save_choice = input(save_prompt).strip().lower()
                except (EOFError, KeyboardInterrupt):
                    save_choice = "n"

                if save_choice in ("y", "yes"):
                    try:
                        s_name = input("Skill Name: ").strip()
                        t_desc = input("Trigger Description: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        s_name = ""
                        t_desc = ""

                    if s_name:
                        save_synthesized_skill(
                            skill_name=s_name,
                            trigger_desc=t_desc or s_name,
                            action_history=result["action_history"],
                        )
                        print(f"\n[run_autonomous] ✅ Successfully saved synthesized skill '{s_name}'!\n")

        except ClientError as ce:
            print(f"\n[ClientError] WebAI client error occurred: {ce}")
        except TaskComplete as tc:
            print(f"\n[TaskComplete] Task completed successfully: {tc}")
        except Exception as e:
            print(f"\n[Error] Unexpected error during autonomous execution: {e}")
        finally:
            print("[run_autonomous] Cleaning up browser resources...")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
