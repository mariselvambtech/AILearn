"""
Modular Client/Server HITL Learned Memory Store.

Provides persistent saving and querying of human-in-the-loop recovery memories
via the WebAI API Server (MSSQL), with automatic local JSON fallback (skills/hitl_memory.json).
"""
from __future__ import annotations

import json
import os
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

DEFAULT_API_URL = os.getenv("WEBAI_API_URL", "http://localhost:8000")
LOCAL_MEMORY_FILE = Path(__file__).resolve().parent.parent / "skills" / "hitl_memory.json"


def _extract_domain_and_pattern(raw_url: str):
    """Normalize URL and extract domain and path pattern."""
    if not raw_url:
        return "", ""
    parsed = urllib.parse.urlparse(raw_url)
    domain = (parsed.netloc or "").lower().split(":")[0]
    pattern = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/") if parsed.netloc else raw_url.rstrip("/")
    return domain, pattern


def _save_to_local_file(record: Dict[str, Any]) -> None:
    """Save memory record to local JSON fallback store."""
    try:
        LOCAL_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        records = []
        if LOCAL_MEMORY_FILE.exists():
            try:
                records = json.loads(LOCAL_MEMORY_FILE.read_text(encoding="utf-8"))
                if not isinstance(records, list):
                    records = []
            except Exception:
                records = []

        records.insert(0, record)
        # Keep latest 200 memories
        records = records[:200]
        LOCAL_MEMORY_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f" [HITLMemoryStore] Local file save warning: {e}")


def _lookup_from_local_file(
    url: str,
    automation_id: Optional[int] = None,
    skill_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Look up memories from local JSON fallback store."""
    if not LOCAL_MEMORY_FILE.exists():
        return []
    try:
        records = json.loads(LOCAL_MEMORY_FILE.read_text(encoding="utf-8"))
        if not isinstance(records, list):
            return []
    except Exception:
        return []

    domain, pattern = _extract_domain_and_pattern(url)

    # 1. Exact pattern match
    exact_matches = []
    for r in records:
        if r.get("url_pattern") == pattern:
            if automation_id and r.get("automation_id") != automation_id:
                continue
            if skill_name and r.get("skill_name") != skill_name:
                continue
            exact_matches.append(r)
    if exact_matches:
        return exact_matches

    # 2. Domain fallback match
    domain_matches = []
    if domain:
        for r in records:
            if r.get("domain") == domain:
                if automation_id and r.get("automation_id") != automation_id:
                    continue
                if skill_name and r.get("skill_name") != skill_name:
                    continue
                domain_matches.append(r)

    return domain_matches


def save_hitl_memory(
    url: str,
    voice_context: str,
    learned_steps: List[Dict[str, Any]],
    dom_excerpt: str = "",
    blocker_context: str = "",
    automation_id: Optional[int] = None,
    skill_name: Optional[str] = None
) -> bool:
    """
    Saves a HITL learned memory record to the central API server (MSSQL)
    and mirrors to local JSON fallback (skills/hitl_memory.json).
    """
    domain, pattern = _extract_domain_and_pattern(url)
    payload = {
        "url_pattern": pattern,
        "domain": domain,
        "automation_id": automation_id,
        "skill_name": skill_name,
        "blocker_context": blocker_context,
        "voice_context": voice_context,
        "dom_excerpt": dom_excerpt,
        "learned_steps_json": learned_steps
    }

    # Always mirror to local file
    _save_to_local_file(payload)

    # Attempt API server POST
    try:
        endpoint = f"{DEFAULT_API_URL.rstrip('/')}/hitl-memory"
        resp = requests.post(endpoint, json=payload, timeout=3.0)
        if resp.status_code in (200, 201):
            return True
        else:
            print(f" [HITLMemoryStore] API server returned {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f" [HITLMemoryStore] API server save unreachable ({e}); mirrored to local JSON.")

    return True


def lookup_hitl_memory(
    url: str,
    automation_id: Optional[int] = None,
    skill_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Queries learned HITL memories from API server with fallback to local JSON.
    """
    # Attempt API query first
    try:
        endpoint = f"{DEFAULT_API_URL.rstrip('/')}/hitl-memory"
        params: Dict[str, Any] = {"url": url}
        if automation_id is not None:
            params["automation_id"] = automation_id
        if skill_name is not None:
            params["skill_name"] = skill_name

        resp = requests.get(endpoint, params=params, timeout=3.0)
        if resp.status_code == 200:
            results = resp.json()
            if isinstance(results, list) and len(results) > 0:
                return results
    except Exception as e:
        print(f" [HITLMemoryStore] API server query unreachable ({e}); falling back to local JSON.")

    # Fallback to local file lookup
    return _lookup_from_local_file(url, automation_id=automation_id, skill_name=skill_name)
