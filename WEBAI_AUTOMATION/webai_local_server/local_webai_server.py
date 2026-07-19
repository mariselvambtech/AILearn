"""
Shim module.

This allows tests to import:
    from local_webai_server import ...

while the real implementation lives in:
    webai_local_server/local_webai_server.py

Allows imports like:
    from local_webai_server import normalize_task

while real implementation lives in:
    webai_local_server/local_webai_server.py
"""

from webai_local_server.local_webai_server import *  # noqa: F401,F403
