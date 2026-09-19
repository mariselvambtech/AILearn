"""
CLI script to synthesize an AI Skill recipe from database automation steps.

This script is invoked by the WebAI dashboard server as a subprocess inside
the Playwright virtual environment, preventing cross-environment dependency
issues with the dashboard server.
"""
import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

import httpx

# Ensure webai_playwright_python directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from webai_playwright.skill_synthesizer import SkillSynthesizer


def fetch_automation(automation_id: int, api_url: str, api_key: str) -> Dict[str, Any]:
    """
    Fetch an automation record and its recorded steps from the API server.

    Args:
        automation_id: The ID of the database automation to fetch.
        api_url: Base URL of the WebAI API server.
        api_key: X-API-Key header token for authentication.

    Returns:
        Dict representing the automation record.
    """
    url = f"{api_url.rstrip('/')}/automations/{automation_id}"
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        response = httpx.get(url, headers=headers, timeout=15.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        sys.stderr.write(f"Failed to fetch automation #{automation_id}: HTTP {exc.response.status_code} - {exc.response.text}\n")
        sys.exit(1)
    except Exception as exc:
        sys.stderr.write(f"Network error contacting API server at {url}: {exc}\n")
        sys.exit(1)


def main() -> None:
    """
    Parse arguments, retrieve automation steps, synthesize the skill, and save it.
    """
    parser = argparse.ArgumentParser(description="Synthesize AI Skill from automation ID")
    parser.add_argument("--id", type=int, required=True, help="Automation ID to synthesize")
    parser.add_argument(
        "--api-url",
        type=str,
        default=os.getenv("WEBAI_API_URL", "http://127.0.0.1:8000"),
        help="WebAI API server base URL",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.getenv("WEBAI_API_KEY", "o3-pxCyR0eY8dqI-iCHW6AVGGwrjQU8aJw-VBIt1f-8"),
        help="X-API-Key token for authentication",
    )
    args = parser.parse_args()

    auto = fetch_automation(args.id, args.api_url, args.api_key)

    steps_raw = auto.get("steps_json") or []
    if isinstance(steps_raw, str):
        try:
            steps = json.loads(steps_raw)
        except Exception as exc:
            sys.stderr.write(f"Failed to parse steps_json for automation #{args.id}: {exc}\n")
            sys.exit(1)
    elif isinstance(steps_raw, list):
        steps = steps_raw
    else:
        steps = []

    voice_context = auto.get("voice_context")
    if voice_context and isinstance(steps, list):
        for s in steps:
            if isinstance(s, dict) and not s.get("voice_context"):
                s["voice_context"] = voice_context

    ollama_url = os.getenv("WEBAI_OLLAMA_URL", "http://localhost:11434")
    synthesizer = SkillSynthesizer(ollama_url=ollama_url)
    skill = synthesizer.synthesize(steps, source_automation_id=args.id)
    saved_path = synthesizer.save_skill(skill, base_dir=".")
    print(f"Successfully synthesized skill for automation #{args.id}: {saved_path}")


if __name__ == "__main__":
    main()
