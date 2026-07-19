"""
Metadata definitions for the WebAI Playwright Client.

Maintains versioning, authorship, and licensing information for the 
`webai_playwright` package.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

_meta_cache: Optional[Dict[str, Any]] = None

def _load_meta() -> Optional[Dict[str, Any]]:
    global _meta_cache
    if _meta_cache is not None:
        return _meta_cache
    # Try to find pyproject or package metadata; fall back to None.
    # This port sets version in pyproject.toml.
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        # crude parse for version = "x"
        import re
        m = re.search(r'version\s*=\s*"([^"]+)"', text)
        if m:
            _meta_cache = {"version": m.group(1)}
            return _meta_cache
    _meta_cache = None
    return None

def get_version() -> str:
    meta = _load_meta()
    return (meta or {}).get("version", "0.0.1")
