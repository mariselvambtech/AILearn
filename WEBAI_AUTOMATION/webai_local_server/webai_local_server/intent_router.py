"""
Semantic Intent Router & Agentic Handoff Module for WebAI Local AI Server.

Analyzes natural language user prompts against available synthesized skills to:
1. Classify and match user intent to an existing AI skill recipe.
2. Extract dynamic parameter variable values from the prompt text.
3. Perform gap analysis to determine if an autonomous LLM hand-off is required
   to complete unrecorded steps beyond the skill's scope.
Uses local Ollama (hermes3 model) with a deterministic fallback engine.
"""
from __future__ import annotations

import json
import re
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional


class IntentRouter:
    """
    Semantic Intent Router and Agentic Handoff Manager.
    """

    KNOWN_COLOR_WORDS = {
        "red", "blue", "green", "yellow", "black", "white", "pink", "purple",
        "orange", "grey", "gray", "brown", "silver", "gold", "beige", "navy"
    }

    ACTION_VERBS_REQUIRING_HANDOFF = {
        "buy", "order", "checkout", "pay", "purchase", "add to cart",
        "subscribe", "download", "export", "delete", "remove", "sign up",
        "register", "book", "reserve"
    }

    def __init__(self, ollama_url: str = "http://localhost:11434", model: str = "hermes3") -> None:
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model

    def route_intent(
        self, prompt: str, available_skills: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Main routing entry point. Passes prompt and skills to Ollama hermes3 or falls back if offline.
        """
        if not prompt or not prompt.strip():
            return self._empty_route_result()

        if not available_skills:
            return {
                "matched_skill": None,
                "extracted_variables": {},
                "requires_agentic_handoff": True,
                "confidence": 0.0,
                "explanation": "No available skills provided."
            }

        try:
            result = self._route_with_ollama(prompt, available_skills)
            if result and "requires_agentic_handoff" in result:
                print(f" [IntentRouter] Intent routed via Ollama ({self.model}): matched='{result.get('matched_skill', {}).get('skill_name') if result.get('matched_skill') else 'None'}'")
                return result
        except Exception as e:
            print(f" [WARN] [IntentRouter] Ollama routing unavailable ({e}). Using deterministic rule-based router.")

        return self._fallback_route(prompt, available_skills)

    def _empty_route_result(self) -> Dict[str, Any]:
        return {
            "matched_skill": None,
            "extracted_variables": {},
            "requires_agentic_handoff": True,
            "confidence": 0.0,
            "explanation": "Empty prompt provided."
        }

    def _route_with_ollama(
        self, prompt: str, available_skills: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Queries local Ollama hermes3 model for semantic intent matching and variable extraction."""
        skills_summary = []
        for idx, sk in enumerate(available_skills, 1):
            skills_summary.append({
                "skill_index": idx,
                "skill_name": sk.get("skill_name"),
                "description": sk.get("description"),
                "trigger_phrases": sk.get("trigger_phrases", []),
                "parameters_schema": sk.get("parameters_schema", {})
            })

        system_prompt = (
            "You are an AI Semantic Intent Classifier and Agentic Handoff Router for web automation.\n"
            "Analyze a user prompt against available web skills to:\n"
            "1. Identify the single best matched skill (or return null if no skill fits).\n"
            "2. Extract values from the user prompt for the matched skill's parameters_schema.\n"
            "3. Perform strict gap analysis: Compare the user prompt's requested actions against the matched skill's recorded capabilities. "
            "If the user prompt asks to perform actions beyond what the recorded skill does (e.g. prompt contains 'buy', 'order', 'checkout', 'pay', 'purchase', but the skill only does 'search' or 'find'), "
            "you MUST set requires_agentic_handoff to true. Set requires_agentic_handoff to false ONLY if the skill completely satisfies all requested user actions.\n"
            "4. Assign a confidence score from 0.0 to 1.0.\n\n"
            "You MUST respond ONLY with valid JSON matching this exact structure:\n"
            "{\n"
            '  "matched_skill_name": "String or null",\n'
            '  "extracted_variables": {"param_key": "extracted_value"},\n'
            '  "requires_agentic_handoff": true/false,\n'
            '  "confidence": 0.95,\n'
            '  "explanation": "Brief explanation"\n'
            "}"
        )

        user_prompt = (
            f"User Prompt: '{prompt}'\n\n"
            f"Available Skills:\n{json.dumps(skills_summary, indent=2)}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {"temperature": 0.1}
        }

        req = urllib.request.Request(
            f"{self.ollama_url}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("message", {}).get("content", "")
            return self._parse_ollama_response(content, available_skills, prompt)

    def _parse_ollama_response(
        self, content: str, available_skills: List[Dict[str, Any]], prompt: str = ""
    ) -> Dict[str, Any]:
        """Extracts and binds JSON classification output from Ollama to full skill dict."""
        content = content.strip()
        if "```" in content:
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
            if match:
                content = match.group(1)
            else:
                content = re.sub(r"```(?:json)?|```", "", content).strip()

        parsed = json.loads(content)
        matched_name = str(parsed.get("matched_skill_name") or "")

        matched_skill = None
        if matched_name and matched_name.lower() not in {"none", "null"}:
            for sk in available_skills:
                if sk.get("skill_name", "").lower() == matched_name.lower():
                    matched_skill = sk
                    break

        requires_handoff = parsed.get("requires_agentic_handoff", True)

        # If no skill was matched, handoff is required
        if not matched_skill:
            requires_handoff = True

        # Safety override: if prompt contains explicit unrecorded action verbs, enforce handoff
        if prompt and matched_skill:
            clean_prompt = prompt.lower()
            skill_name_desc = (matched_skill.get("skill_name", "") + " " + matched_skill.get("description", "")).lower()
            for verb in self.ACTION_VERBS_REQUIRING_HANDOFF:
                if verb in clean_prompt and verb not in skill_name_desc:
                    requires_handoff = True
                    break

        return {
            "matched_skill": matched_skill,
            "extracted_variables": parsed.get("extracted_variables", {}) if matched_skill else {},
            "requires_agentic_handoff": requires_handoff,
            "confidence": float(parsed.get("confidence", 0.8 if matched_skill else 0.0)),
            "explanation": parsed.get("explanation", "")
        }

    def _fallback_route(
        self, prompt: str, available_skills: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Deterministic rule-based intent router when Ollama is offline or in test mode.
        Calculates semantic match scores, extracts variables, and performs gap analysis.
        """
        clean_prompt = prompt.strip()
        prompt_words = set(re.findall(r"\w+", clean_prompt.lower()))

        best_skill: Optional[Dict[str, Any]] = None
        best_score = 0

        # 1. Semantic Match Scoring
        for sk in available_skills:
            score = 0
            s_name = sk.get("skill_name", "").lower()
            s_desc = sk.get("description", "").lower()
            triggers = [t.lower() for t in sk.get("trigger_phrases", [])]

            # Domain/Keyword matching
            for word in prompt_words:
                if len(word) <= 2:
                    continue
                if word in s_name:
                    score += 3
                if word in s_desc:
                    score += 1
                for tr in triggers:
                    if word in tr:
                        score += 2

            # Whole phrase substring bonus
            for tr in triggers:
                if tr in clean_prompt.lower():
                    score += 5

            if score > best_score:
                best_score = score
                best_skill = sk

        if not best_skill or best_score < 2:
            return {
                "matched_skill": None,
                "extracted_variables": {},
                "requires_agentic_handoff": True,
                "confidence": 0.0,
                "explanation": "No skill met the similarity threshold."
            }

        # 2. Parameter Variable Extraction
        extracted_vars: Dict[str, Any] = {}
        schema = best_skill.get("parameters_schema", {})

        for p_name, p_info in schema.items():
            val = self._extract_variable_value(clean_prompt, p_name, p_info, prompt_words)
            if val:
                extracted_vars[p_name] = val

        # 3. Gap Analysis for Agentic Handoff
        requires_handoff = False

        # Check for unrecorded action verbs (e.g. "buy", "checkout", "order")
        for verb in self.ACTION_VERBS_REQUIRING_HANDOFF:
            if verb in clean_prompt.lower():
                requires_handoff = True
                break

        # Calculate confidence score based on match strength
        confidence = min(1.0, round(0.5 + (best_score * 0.1), 2))

        return {
            "matched_skill": best_skill,
            "extracted_variables": extracted_vars,
            "requires_agentic_handoff": requires_handoff,
            "confidence": confidence,
            "explanation": f"Matched '{best_skill.get('skill_name')}' with score {best_score}."
        }

    def _extract_variable_value(
        self, prompt: str, param_name: str, param_info: Dict[str, Any], prompt_words: set[str]
    ) -> Optional[str]:
        """Extracts parameter value from user prompt based on schema metadata and keywords."""
        p_name_lower = param_name.lower()
        desc_lower = (param_info.get("description") or "").lower()

        # Color extraction
        if "color" in p_name_lower or "color" in desc_lower:
            for color in self.KNOWN_COLOR_WORDS:
                if color in prompt_words:
                    return color

        # Search query / item extraction
        if "query" in p_name_lower or "search" in p_name_lower or "item" in p_name_lower:
            # Look for common nouns in prompt
            words_list = re.findall(r"\w+", prompt)
            filtered = [w for w in words_list if w.lower() not in {"buy", "a", "an", "the", "on", "in", "for", "search", "find", "order", "get"}]
            # Remove color words if present
            filtered = [w for w in filtered if w.lower() not in self.KNOWN_COLOR_WORDS]
            if filtered:
                # Exclude domain words like "flipkart", "wikipedia"
                domain_words = {"flipkart", "wikipedia", "amazon", "google"}
                filtered = [w for w in filtered if w.lower() not in domain_words]
                if filtered:
                    return filtered[0]

        # Default fallback
        return param_info.get("default")
