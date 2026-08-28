"""
Skill Synthesizer Utility for WebAI Playwright Recorder.

Processes time-aligned recorded steps enriched with voice context to:
1. Synthesize natural language intent and step descriptions.
2. Auto-detect literal values and parameterize them into dynamic variables ({{variable_name}}).
3. Generate structured skill metadata (skill_name, description, trigger_phrases, parameters_schema).
Uses local Ollama (hermes3 model) with a deterministic fallback engine.
"""
from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Optional, Union


class SkillSynthesizer:
    """
    Synthesizes recorded browser steps and voice context into reusable AI Skill recipes.
    """

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "hermes3") -> None:
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model

    def synthesize(self, steps: List[Union[Dict[str, Any], Any]]) -> Dict[str, Any]:
        """
        Main synthesis entry point. Passes steps to Ollama hermes3 or falls back if offline.
        """
        clean_steps = self._normalize_steps(steps)
        if not clean_steps:
            return self._empty_skill()

        try:
            skill = self._synthesize_with_ollama(clean_steps)
            if skill and "parameterized_steps" in skill and "skill_name" in skill:
                print(f" [SkillSynthesizer] Synthesized skill '{skill.get('skill_name')}' via Ollama ({self.model})")
                return skill
        except Exception as e:
            print(f" [WARN] [SkillSynthesizer] Ollama synthesis unavailable ({e}). Using rule-based fallback synthesizer.")

        return self._fallback_synthesis(clean_steps)

    def _normalize_steps(self, steps: List[Union[Dict[str, Any], Any]]) -> List[Dict[str, Any]]:
        """Converts Step dataclasses or dicts into uniform dictionaries."""
        normalized = []
        for s in steps:
            if is_dataclass(s):
                normalized.append(asdict(s))
            elif isinstance(s, dict):
                normalized.append(dict(s))
        return normalized

    def _empty_skill(self) -> Dict[str, Any]:
        return {
            "skill_name": "Empty Recording",
            "description": "No recorded steps found.",
            "trigger_phrases": [],
            "parameters_schema": {},
            "parameterized_steps": []
        }

    def _synthesize_with_ollama(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Queries local Ollama hermes3 model for skill synthesis and auto-parameterization."""
        step_summaries = []
        for idx, s in enumerate(steps, 1):
            summary = {
                "step_index": idx,
                "action": s.get("action"),
                "url": s.get("url"),
                "name": s.get("name"),
                "value": s.get("value"),
                "voice_context": s.get("voice_context")
            }
            step_summaries.append(summary)

        system_prompt = (
            "You are an AI Web Automation Skill Synthesizer. "
            "Analyze a sequence of recorded web browser steps with optional spoken voice context. "
            "Your tasks:\n"
            "1. Synthesize a concise skill_name, description, and list of 3-4 natural language trigger_phrases.\n"
            "2. Identify literal values (e.g. typed text, search queries) that should be dynamic parameters.\n"
            "3. Create parameters_schema mapping parameter keys to {type, description, default}.\n"
            "4. Return parameterized_steps where literal inputs are replaced by '{{parameter_key}}'.\n\n"
            "You MUST respond ONLY with valid JSON matching this exact structure:\n"
            "{\n"
            '  "skill_name": "String",\n'
            '  "description": "String",\n'
            '  "trigger_phrases": ["phrase 1", "phrase 2"],\n'
            '  "parameters_schema": {\n'
            '    "param_name": {"type": "string", "description": "String", "default": "value"}\n'
            "  },\n"
            '  "parameterized_steps": [ ... array of steps with {{param_name}} in value ... ]\n'
            "}"
        )

        user_prompt = f"Recorded Steps:\n{json.dumps(step_summaries, indent=2)}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.2}
        }

        req = urllib.request.Request(
            f"{self.ollama_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("message", {}).get("content", "")
            return self._parse_json_response(content, steps)

    def _parse_json_response(self, content: str, original_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extracts JSON payload from LLM response content."""
        content = content.strip()
        # Remove markdown ```json code block wrappers if present
        if "```" in content:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            if match:
                content = match.group(1)
            else:
                content = re.sub(r"```(?:json)?|```", "", content).strip()

        parsed = json.loads(content)
        
        # Ensure parameterized_steps retain locators and metadata from original steps
        param_steps = parsed.get("parameterized_steps", [])
        if len(param_steps) == len(original_steps):
            for orig, param in zip(original_steps, param_steps):
                if isinstance(param, dict) and "locators" not in param and "locators" in orig:
                    param["locators"] = orig["locators"]
                if isinstance(param, dict) and "timestamp_ms" not in param and "timestamp_ms" in orig:
                    param["timestamp_ms"] = orig["timestamp_ms"]

        return parsed

    def _fallback_synthesis(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Rule-based fallback synthesizer when Ollama is offline.
        Detects typed text inputs and extracts parameter candidates.
        """
        parameters_schema: Dict[str, Dict[str, Any]] = {}
        parameterized_steps: List[Dict[str, Any]] = []

        first_url = ""
        for s in steps:
            if s.get("url") and not first_url:
                first_url = s["url"]

        for idx, s in enumerate(steps):
            step_copy = dict(s)
            action = step_copy.get("action")
            val = step_copy.get("value")
            name = step_copy.get("name") or f"input_{idx+1}"
            voice = step_copy.get("voice_context") or ""

            if action == "type" and val:
                # Infer param_name from voice context or step name
                clean_name = self._sanitize_param_name(voice or name)
                param_key = clean_name or f"param_{idx+1}"
                
                parameters_schema[param_key] = {
                    "type": "string",
                    "description": f"Input value for {name}",
                    "default": val
                }
                step_copy["value"] = f"{{{{{param_key}}}}}"

            parameterized_steps.append(step_copy)

        skill_title = "Web Automation Skill"
        if first_url:
            domain = re.sub(r"https?://(www\.)?", "", first_url).split("/")[0]
            skill_title = f"{domain.capitalize()} Automation Skill"

        return {
            "skill_name": skill_title,
            "description": f"Automated sequence with {len(steps)} steps.",
            "trigger_phrases": [
                f"Run {skill_title}",
                f"Execute automation on {first_url}" if first_url else "Run web task"
            ],
            "parameters_schema": parameters_schema,
            "parameterized_steps": parameterized_steps
        }

    def _sanitize_param_name(self, text: str) -> str:
        """Converts text into a clean snake_case variable name."""
        text = text.lower()
        # Strip common action phrases from voice context
        for prefix in ["now typing", "type", "enter", "input", "typing", "fill"]:
            text = text.replace(prefix, "")
        text = re.sub(r"[^\w\s]", "", text).strip()
        words = text.split()[:3]
        return "_".join(words) if words else ""
