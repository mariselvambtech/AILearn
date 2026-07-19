from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

_CONFIG_CACHE: Optional[Dict[str, Any]] = None

def _load_config_file() -> Dict[str, Any]:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    cfg: Dict[str, Any] = {}
    path = Path.cwd() / "webai.config.json"
    if path.exists():
        try:
            cfg = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
    _CONFIG_CACHE = cfg
    return cfg

def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    cfg = _load_config_file()
    # Upstream commonly uses AI_TOKEN; support both.
    if key == "TOKEN" and os.environ.get("AI_TOKEN"):
        return os.environ.get("AI_TOKEN")
    if key in os.environ and os.environ[key] != "":
        return os.environ[key]
    if key in cfg and cfg[key] not in (None, ""):
        return str(cfg[key])
    return default

TOKEN = get_config_value("TOKEN")
WEBSOCKET_PROTOCOL = get_config_value("WEBSOCKET_PROTOCOL", "https")
WEBSOCKET_HOST = get_config_value("WEBSOCKET_HOST", "devai.us-east-1.reflect.run")
PACKAGE_NAME = get_config_value("PACKAGE_NAME", "webai")
LOGS_ENABLED = (get_config_value("LOGS_ENABLED", "false") or "false").lower() == "true"
MAX_TASK_CHARS = int(get_config_value("MAX_TASK_CHARS", "2000") or "2000")

WEBDRIVER_ELEMENT_KEY = "element-6066-11e4-a52e-4f735466cecf"

def websocket_url() -> str:
    # TS uses https/http but the Python websockets client expects ws/wss.
    proto = WEBSOCKET_PROTOCOL or "https"
    if proto == "https":
        ws_proto = "wss"
    elif proto == "http":
        ws_proto = "ws"
    elif proto in ("ws", "wss"):
        ws_proto = proto
    else:
        ws_proto = "wss"
    key = TOKEN or ""
    return f"{ws_proto}://{WEBSOCKET_HOST}/api?key={key}"
