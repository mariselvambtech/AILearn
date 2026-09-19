"""
Proxy module providing backwards compatibility for tests importing local_webai_server.
Forwards all public and internal helper symbols from local_webai_server_guided.
"""
from .local_webai_server_guided import *
from .local_webai_server_guided import (
    _cache_key,
    _looks_like_not_found,
    _looks_like_navigation_issue,
    _compact_context,
    _extract_json_array,
)
