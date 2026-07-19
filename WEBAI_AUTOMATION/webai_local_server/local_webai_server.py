"""
Shim module for the WebAI Local Server.

This file acts as a top-level export module (shim) for the local WebSocket AI server. 
It exists to facilitate testing and package structuring, allowing external scripts and 
tests to import components directly from `local_webai_server` instead of dealing 
with the nested directory structure `webai_local_server/local_webai_server`.

Example:
    `from local_webai_server import normalize_task`
    
    while the real implementation lives in:
    `webai_local_server/local_webai_server.py`
"""

from webai_local_server.local_webai_server import *  # noqa: F401,F403
