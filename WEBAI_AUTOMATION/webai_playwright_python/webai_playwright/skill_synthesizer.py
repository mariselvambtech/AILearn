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

    @staticmethod
    def slugify(name: str) -> str:
        """Converts a human-readable skill name into a safe, alphanumeric filename slug."""
        s = re.sub(r"[^\w\s-]", "", (name or "").lower()).strip()
        return re.sub(r"[-\s]+", "_", s) or "skill"

    def save_skill(self, skill: Dict[str, Any], base_dir: Optional[Union[str, Any]] = None) -> str:
        """
        Saves the synthesized skill recipe to skills/{slug}.json and mirrors to synthesized_skill.json.

        Args:
            skill: The synthesized skill definition dictionary.
            base_dir: Optional root/client directory. If None, uses workspace or cwd.

        Returns:
            The string path to the newly saved slugified skill file.
        """
        import os
        from pathlib import Path

        root = Path(base_dir) if base_dir else Path.cwd()
        skills_dir = root / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)

        skill_name = skill.get("skill_name") or "skill"
        slug = self.slugify(skill_name)
        slug_path = skills_dir / f"{slug}.json"
        mirror_path = root / "synthesized_skill.json"

        skill_json = json.dumps(skill, indent=2, ensure_ascii=False)
        slug_path.write_text(skill_json, encoding="utf-8")
        mirror_path.write_text(skill_json, encoding="utf-8")

        print(f" [SkillSynthesizer] Saved multi-skill library recipe: {slug_path}")
        print(f" [SkillSynthesizer] Mirrored legacy recipe: {mirror_path}")

        return str(slug_path)

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
            "4. Return parameterized_steps where literal inputs are replaced by '{{parameter_key}}'.\n"
            "5. Pre-Click Semantic Verification: When synthesizing 'click' or 'type' steps with voice_context, "
            "populate 'expected_context' with the core semantic target or keyword (e.g., if voice says 'clicking the blue checkbox', "
            "expected_context='blue'; if voice says 'filtering jeans with brand pepe jeans', expected_context='pepe jeans').\n"
            "6. Post-Click Conditional Assertions: Insert a new {'action': 'assert', 'target': 'url_contains'|'title_contains'|'visible', 'value': '...'} "
            "step after critical actions (e.g., form submissions, searches, navigation) when the voice context indicates an expected outcome or loaded page.\n\n"
            "You MUST respond ONLY with valid JSON matching this exact structure:\n"
            "{\n"
            '  "skill_name": "String",\n'
            '  "description": "String",\n'
            '  "trigger_phrases": ["phrase 1", "phrase 2"],\n'
            '  "parameters_schema": {\n'
            '    "param_name": {"type": "string", "description": "String", "default": "value"}\n'
            "  },\n"
            '  "parameterized_steps": [\n'
            '    {"action": "click", "name": "...", "expected_context": "...", "value": null, "locators": [...]},\n'
            '    {"action": "assert", "target": "url_contains", "value": "..."}\n'
            '  ]\n'
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
        """Extracts JSON payload from LLM response content and preserves locators on matching steps."""
        content = content.strip()
        # Remove markdown ```json code block wrappers if present
        if "```" in content:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            if match:
                content = match.group(1)
            else:
                content = re.sub(r"```(?:json)?|```", "", content).strip()

        parsed = json.loads(content)
        
        # Ensure parameterized_steps retain locators and metadata from original steps,
        # skipping newly injected 'assert' steps without throwing off index alignment.
        param_steps = parsed.get("parameterized_steps", [])
        orig_idx = 0
        for param in param_steps:
            if not isinstance(param, dict):
                continue
            if param.get("action") == "assert":
                continue
            if orig_idx < len(original_steps):
                orig = original_steps[orig_idx]
                if "locators" not in param and "locators" in orig:
                    param["locators"] = orig["locators"]
                if "timestamp_ms" not in param and "timestamp_ms" in orig:
                    param["timestamp_ms"] = orig["timestamp_ms"]
                orig_idx += 1

        return parsed

    def _extract_semantic_target(self, voice_context: str, step_name: Optional[str]) -> Optional[str]:
        """Extracts core semantic keyword from voice context or step name for pre-click verification."""
        if not voice_context and not step_name:
            return None
        text = (voice_context or "").lower()
        for phrase in [
            "selecting the", "selecting", "filtering the", "filtering with", "filtering",
            "clicking on", "clicking the", "clicking", "click on", "click the", "click"
        ]:
            if phrase in text:
                remainder = text.split(phrase, 1)[1].strip()
                words = re.sub(r"[^\w\s-]", "", remainder).split()
                if words:
                    meaningful = [w for w in words if w not in ("so", "now", "the", "a", "an", "and", "in", "to", "with")][:3]
                    if meaningful:
                        return " ".join(meaningful)
        if step_name and len(step_name) <= 30 and not step_name.startswith("step_"):
            return step_name.lower().strip()
        return None

    def _fallback_synthesis(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Rule-based fallback synthesizer when Ollama is offline.
        Detects typed text inputs, populates expected_context from voice context,
        and extracts parameter candidates.
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

            elif action == "click":
                target_kw = self._extract_semantic_target(voice, name)
                if target_kw:
                    step_copy["expected_context"] = target_kw

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
