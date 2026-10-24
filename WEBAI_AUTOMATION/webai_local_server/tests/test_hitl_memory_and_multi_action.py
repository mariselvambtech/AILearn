"""
Test suite for Phase 29: Simultaneous Voice + Multi-Action HITL Recording,
MSSQL HITL Learned Memory Store & Voice+DOM Self-Healing.
"""
import os
import sys
import json
import time
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

# Setup paths
SERVER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
API_SERVER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../webai_api_server"))
PLAYWRIGHT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../webai_playwright_python"))

for p in (SERVER_ROOT, API_SERVER_ROOT, PLAYWRIGHT_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)


# ==============================================================================
# 1. Multi-Action Normalization & 13-Locator Step Preservation
# ==============================================================================

def test_normalize_history_step_multi_action_and_voice():
    """Verify _normalize_history_step preserves multi-actions (drag_and_drop, scroll_page),
    coordinates, 13-rank locators, and voice_context without duplicates."""
    from webai_local_server.local_webai_server_guided import _normalize_history_step

    # Test drag_and_drop
    drag_act = {
        "action": "drag_and_drop",
        "name": "slider-handle",
        "source_locators": [{"type": "css", "value": "#slider-thumb"}],
        "target_locators": [{"type": "css", "value": "#slider-track"}],
        "source_coords": {"x": 100, "y": 200},
        "target_coords": {"x": 300, "y": 200},
        "voice_context": "Drag the slider to 300px",
        "url": "https://example.com/slider",
        "timestamp_ms": 1200
    }
    norm_drag = _normalize_history_step(drag_act)
    assert norm_drag["action"] == "drag_and_drop"
    assert norm_drag["name"] == "slider-handle"
    assert norm_drag["source_locators"] == [{"type": "css", "value": "#slider-thumb"}]
    assert norm_drag["target_locators"] == [{"type": "css", "value": "#slider-track"}]
    assert norm_drag["source_coords"] == {"x": 100, "y": 200}
    assert norm_drag["target_coords"] == {"x": 300, "y": 200}
    assert norm_drag["voice_context"] == "Drag the slider to 300px"

    # Test scroll_page
    scroll_act = {
        "action": "scroll_page",
        "target": "down",
        "delta_x": 0,
        "delta_y": 500,
        "voice_context": "Scroll down to footer",
        "url": "https://example.com/page",
        "timestamp_ms": 2500
    }
    norm_scroll = _normalize_history_step(scroll_act)
    assert norm_scroll["action"] == "scroll_page"
    assert norm_scroll["target"] == "down"
    assert norm_scroll["delta_y"] == 500
    assert norm_scroll["voice_context"] == "Scroll down to footer"

    # Test type with locators and voice_context
    type_act = {
        "action": "type",
        "name": "search",
        "value": "playwright",
        "locators": [
            {"type": "test-id", "value": "search-input"},
            {"type": "id", "value": "search"},
            {"type": "placeholder", "value": "Search here"}
        ],
        "voice_context": "Type playwright into search",
        "url": "https://example.com"
    }
    norm_type = _normalize_history_step(type_act)
    assert norm_type["action"] == "type"
    assert norm_type["value"] == "playwright"
    assert len(norm_type["locators"]) == 3
    assert norm_type["voice_context"] == "Type playwright into search"


# ==============================================================================
# 2. Simultaneous Voice Segment Alignment in HITLPlugin
# ==============================================================================

@pytest.mark.asyncio
async def test_hitl_simultaneous_voice_segment_alignment():
    """Verify that HITLPlugin aligns spoken segments to multi-action telemetry steps."""
    from webai_playwright.plugins.hitl_plugin import HITLPlugin

    plugin = HITLPlugin(tts_prompt="Test Prompt")

    # Mock audio segments returned by transcribe_segments
    mock_segments = [
        {"start_ms": 500, "end_ms": 2000, "text": "Click on the search box"},
        {"start_ms": 2500, "end_ms": 4500, "text": "Type headphones and press enter"}
    ]

    mock_transcriber = MagicMock()
    mock_transcriber.transcribe_segments.return_value = mock_segments
    mock_transcriber.transcribe_text.return_value = "Click on the search box. Type headphones and press enter."

    telemetry_raw = [
        {"action": "click", "name": "search", "timestamp_ms": 1000, "locators": [{"type": "id", "value": "search"}]},
        {"action": "type", "name": "search", "value": "headphones", "timestamp_ms": 5000, "locators": [{"type": "id", "value": "search"}]}
    ]

    with patch("webai_playwright.plugins.hitl_plugin.ACTIVE_TRANSCRIBER", mock_transcriber), \
         patch.object(plugin, "_speak_tts_cue_async", return_value=None), \
         patch.object(plugin, "_inject_and_await_observer_mode", new_callable=AsyncMock) as mock_observer:

        mock_observer.return_value = {
            "status": "resolved",
            "action": "observer_mode_complete",
            "telemetry": telemetry_raw,
            "targetTag": "RESUME_AI"
        }

        mock_page = AsyncMock()
        resolution = await plugin.trigger_intervention(mock_page, {"reason": "test"})

        assert resolution["status"] == "resolved"
        assert "telemetry" in resolution
        telemetry = resolution["telemetry"]
        assert len(telemetry) == 2
        # Verify temporal voice context alignment
        assert telemetry[0]["voice_context"] == "Click on the search box"
        assert telemetry[1]["voice_context"] == "Type headphones and press enter"


# ==============================================================================
# 3. MSSQL Model, Schemas, CRUD & Endpoints
# ==============================================================================

def test_hitl_memory_model_and_crud():
    """Test creating and retrieving HITL learned memory via SQLAlchemy Session and CRUD."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import models
    import schemas
    import crud
    from database import Base

    # In-memory SQLite for testing model & CRUD mechanics
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        mem_in = schemas.HITLMemoryCreate(
            url_pattern="https://example.com/checkout",
            domain="example.com",
            skill_name="checkout_flow",
            blocker_context="Failed to click submit button",
            voice_context="Click the place order button after checking the checkbox",
            dom_excerpt="<button id='place-order'>Place Order</button>",
            learned_steps_json=[
                {"action": "click", "name": "agree-terms", "locators": [{"type": "id", "value": "terms"}]},
                {"action": "click", "name": "place-order", "locators": [{"type": "id", "value": "place-order"}]}
            ]
        )

        created = crud.create_hitl_memory(db, mem_in)
        assert created.id is not None
        assert created.url_pattern == "https://example.com/checkout"
        assert created.domain == "example.com"
        assert len(created.learned_steps_json) == 2

        # Query exact URL
        exact_results = crud.get_hitl_memories(db, url="https://example.com/checkout")
        assert len(exact_results) == 1
        assert exact_results[0].skill_name == "checkout_flow"

        # Query domain fallback
        domain_results = crud.get_hitl_memories(db, url="https://example.com/cart")
        assert len(domain_results) == 1
        assert domain_results[0].domain == "example.com"

        # Query completely different domain
        empty_results = crud.get_hitl_memories(db, url="https://other.com/page")
        assert len(empty_results) == 0

    finally:
        db.close()


def test_hitl_memory_store_helper(tmp_path):
    """Test hitl_memory_store.py save and lookup with local JSON fallback."""
    from webai_playwright import hitl_memory_store

    json_fallback = tmp_path / "hitl_memory.json"
    with patch.object(hitl_memory_store, "LOCAL_MEMORY_FILE", json_fallback):
        # Mock requests.post to fail (forcing local JSON fallback)
        with patch("requests.post", side_effect=Exception("Connection refused")), \
             patch("requests.get", side_effect=Exception("Connection refused")):

            saved = hitl_memory_store.save_hitl_memory(
                url="https://store.com/cart",
                voice_context="Click proceed to checkout",
                learned_steps=[{"action": "click", "locators": [{"type": "id", "value": "checkout"}]}],
                blocker_context="Button not found",
                skill_name="cart_checkout"
            )
            assert saved is True
            assert json_fallback.exists()

            # Lookup from local fallback
            memories = hitl_memory_store.lookup_hitl_memory("https://store.com/cart")
            assert len(memories) >= 1
            assert memories[0]["voice_context"] == "Click proceed to checkout"
            assert memories[0]["domain"] == "store.com"


# ==============================================================================
# 4. Drag and Drop with Fallback Helper
# ==============================================================================

@pytest.mark.asyncio
async def test_drag_and_drop_with_fallback():
    """Verify drag_and_drop_with_fallback executes locator drag_to and coordinate fallback."""
    from webai_playwright.fallback_helpers import drag_and_drop_with_fallback

    mock_page = MagicMock()
    mock_src_loc = AsyncMock()
    mock_tgt_loc = AsyncMock()

    # Case 1: Locator drag_to succeeds
    with patch("webai_playwright.fallback_helpers._create_locator_obj") as mock_create_loc:
        mock_create_loc.side_effect = [mock_src_loc, mock_tgt_loc]
        success = await drag_and_drop_with_fallback(
            mock_page,
            source_locators=[{"type": "id", "value": "src"}],
            target_locators=[{"type": "id", "value": "tgt"}]
        )
        assert success is True
        mock_src_loc.drag_to.assert_called_once_with(mock_tgt_loc, timeout=4000)

    # Case 2: Mouse coordinate fallback when locators fail
    mock_page.mouse = AsyncMock()
    with patch("webai_playwright.fallback_helpers._create_locator_obj", return_value=None):
        success = await drag_and_drop_with_fallback(
            mock_page,
            source_locators=[],
            target_locators=[],
            source_coords={"x": 50, "y": 60},
            target_coords={"x": 200, "y": 250}
        )
        assert success is True
        mock_page.mouse.move.assert_any_call(50, 60)
        mock_page.mouse.down.assert_called_once()
        mock_page.mouse.up.assert_called_once()


# ==============================================================================
# 5. SkillExecutor Stuck-State Self-Healing with Learned Memory
# ==============================================================================

@pytest.mark.asyncio
async def test_skill_executor_recovers_with_hitl_memory():
    """Verify that when SkillExecutor action fails, it looks up learned memory and replays learned steps."""
    from webai_playwright.skill_executor import SkillExecutor

    recipe = {
        "skill_name": "checkout_skill",
        "parameterized_steps": [
            {"action": "click", "name": "submit_btn", "locators": [{"type": "id", "value": "submit"}]}
        ]
    }

    executor = SkillExecutor(skill_recipe=recipe)

    mock_page = AsyncMock()
    mock_page.url = "https://shop.com/checkout"
    mock_page.content.return_value = "<html><body><button id='pay'>Pay Now</button></body></html>"

    learned_memory = [{
        "voice_context": "The submit button was renamed to Pay Now",
        "learned_steps_json": [
            {"action": "click", "name": "pay_btn", "locators": [{"type": "id", "value": "pay"}]}
        ]
    }]

    # Simulate click failure on initial step, then success on learned recovery step
    with patch("webai_playwright.skill_executor.click_with_fallback", side_effect=[False, True]), \
         patch("webai_playwright.hitl_memory_store.lookup_hitl_memory", return_value=learned_memory), \
         patch("webai_playwright.hitl_memory_store.save_hitl_memory", return_value=True):

        result = await executor.execute_skill(mock_page)
        assert result["status"] == "success"
        assert result["steps_executed"] >= 1


# ==============================================================================
# 6. Phase 29 Hotfix Tests: 2nd HITL Popup, Cross-Venv Import, Pruned DOM Text
# ==============================================================================

@pytest.mark.asyncio
async def test_hitl_second_popup_resumes_cleanly():
    """Verify that a second HITL intervention on the same page/context resolves cleanly
    even when Playwright's expose_binding throws an error on duplicate registration."""
    from webai_playwright.plugins.hitl_plugin import HITLPlugin

    plugin = HITLPlugin(tts_prompt="Test")
    registered_bindings = {}

    class MockContext:
        def __init__(self):
            self.pages = []
        async def expose_binding(self, name, callback):
            if name in registered_bindings:
                raise Exception(f'Function "{name}" has been already registered')
            registered_bindings[name] = callback

    mock_context = MockContext()
    mock_page = AsyncMock()
    mock_page.context = mock_context
    mock_page.is_closed = MagicMock(return_value=False)
    mock_page.on = MagicMock()
    mock_page.remove_listener = MagicMock()
    mock_page.url = "https://example.com"
    mock_context.pages.append(mock_page)

    with patch.object(plugin, "_speak_tts_cue_async", return_value=None), \
         patch("webai_playwright.plugins.hitl_plugin.ACTIVE_TRANSCRIBER") as mock_tr:
        mock_tr.transcribe_text.return_value = "Proceed"
        mock_tr.transcribe_segments.return_value = []

        # 1st HITL intervention
        async def resolve_first():
            await asyncio.sleep(0.05)
            # Invoke the exposed binding
            cb = registered_bindings["resumeWebAI"]
            cb(None, {
                "status": "resolved",
                "action": "observer_mode_complete",
                "telemetry": [{"action": "click", "name": "btn1", "timestamp_ms": 100}]
            })

        t1 = asyncio.create_task(resolve_first())
        res1 = await plugin.trigger_intervention(mock_page, {"reason": "test1"}, timeout_sec=5.0)
        await t1

        assert res1["status"] == "resolved"
        assert res1["telemetry"][0]["name"] == "btn1"

        # 2nd HITL intervention on SAME context (expose_binding will throw and be caught)
        async def resolve_second():
            await asyncio.sleep(0.05)
            # Invoke the same original binding - it must resolve the 2nd active event!
            cb = registered_bindings["resumeWebAI"]
            cb(None, {
                "status": "resolved",
                "action": "observer_mode_complete",
                "telemetry": [{"action": "click", "name": "btn2", "timestamp_ms": 200}]
            })

        t2 = asyncio.create_task(resolve_second())
        res2 = await plugin.trigger_intervention(mock_page, {"reason": "test2"}, timeout_sec=5.0)
        await t2

        assert res2["status"] == "resolved"
        assert res2["telemetry"][0]["name"] == "btn2"


def test_ai_server_imports_hitl_memory_store():
    """Verify that hitl_memory_store can be imported and executed from AI server context
    without failing on missing playwright module."""
    # Ensure sys.path includes webai_playwright_python
    pw_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../webai_playwright_python"))
    if pw_dir not in sys.path:
        sys.path.insert(0, pw_dir)

    from webai_playwright.hitl_memory_store import save_hitl_memory, lookup_hitl_memory
    assert callable(save_hitl_memory)
    assert callable(lookup_hitl_memory)


def test_informational_and_post_hitl_includes_pruned_dom_text():
    """Verify that _prune_dom_snapshot extracts readable text from tables, lists, and headings,
    and fallback stripping preserves static course lists."""
    from webai_local_server.local_webai_server_guided import _prune_dom_snapshot

    sample_html = """
    <html>
      <head><title>Courses</title></head>
      <body>
        <script>console.log("ignore");</script>
        <style>.hide { display: none; }</style>
        <h1>Offered Courses at Thanjavur Campus</h1>
        <table border="1">
          <thead>
            <tr><th>Course Code</th><th>Course Title</th><th>Department</th></tr>
          </thead>
          <tbody>
            <tr><td>CS101</td><td>Data Structures & Algorithms</td><td>Computer Science</td></tr>
            <tr><td>ME202</td><td>Thermal Engineering</td><td>Mechanical</td></tr>
          </tbody>
        </table>
        <ul>
          <li>B.Tech Computer Science and Engineering</li>
          <li>B.Tech Artificial Intelligence and Data Science</li>
        </ul>
      </body>
    </html>
    """
    pruned = _prune_dom_snapshot(sample_html)
    assert "Data Structures" in pruned
    assert "Thanjavur Campus" in pruned
    assert "Artificial Intelligence" in pruned
    assert "<script>" not in pruned
    assert "console.log" not in pruned


@pytest.mark.asyncio
async def test_hitl_same_tab_navigation_preserves_telemetry_and_reinjects_panel():
    """Verify that clicking a link before same-tab navigation records telemetry via Python sink
    and keeps telemetry synchronized across same-tab reload without timing out."""
    from webai_playwright.plugins.hitl_plugin import HITLPlugin

    plugin = HITLPlugin(tts_prompt="Test")
    registered_bindings = {}
    page_event_listeners = {}

    class MockContext:
        def __init__(self):
            self.pages = []
        async def expose_binding(self, name, callback):
            registered_bindings[name] = callback

    mock_context = MockContext()
    mock_page = AsyncMock()
    mock_page.context = mock_context
    mock_page.is_closed = MagicMock(return_value=False)
    mock_page.url = "https://sastra.edu"
    mock_context.pages.append(mock_page)

    def mock_on(event, handler):
        page_event_listeners.setdefault(event, []).append(handler)

    mock_page.on = mock_on
    mock_page.remove_listener = MagicMock()

    with patch.object(plugin, "_speak_tts_cue_async", return_value=None), \
         patch("webai_playwright.plugins.hitl_plugin.ACTIVE_TRANSCRIBER") as mock_tr:
        mock_tr.transcribe_text.return_value = "Proceed"
        mock_tr.transcribe_segments.return_value = []

        async def user_workflow():
            await asyncio.sleep(0.05)
            # 1. User clicks navigation link - immediately recorded via recordHITLTelemetry
            record_cb = registered_bindings.get("recordHITLTelemetry")
            assert record_cb is not None
            record_cb(None, {
                "action": "click",
                "tag": "a",
                "name": "UG / PG Programmes",
                "text": "UG / PG Programmes",
                "url": "https://sastra.edu",
                "timestamp_ms": 150
            })

            # 2. Simulate same-tab navigation: trigger domcontentloaded event
            dom_handlers = page_event_listeners.get("domcontentloaded", [])
            for h in dom_handlers:
                h()

            await asyncio.sleep(0.05)
            # 3. User clicks Resume AI on the new page
            resume_cb = registered_bindings.get("resumeWebAI")
            assert resume_cb is not None
            resume_cb(None, {
                "status": "resolved",
                "action": "observer_mode_complete",
                "telemetry": []
            })

        workflow_task = asyncio.create_task(user_workflow())
        res = await plugin.trigger_intervention(mock_page, {"reason": "test_nav"}, timeout_sec=5.0)
        await workflow_task

        assert res["status"] == "resolved"
        assert len(res["telemetry"]) >= 1
        assert res["telemetry"][0]["name"] == "UG / PG Programmes"
        assert res["telemetry"][0]["timestamp_ms"] >= 0


def test_prune_dom_snapshot_strips_header_nav_and_preserves_tables():
    """Verify that _prune_dom_snapshot strips header, nav, and footer mega-menus
    so that table courses appear prominently at the start of the pruned output."""
    from webai_local_server.local_webai_server_guided import _prune_dom_snapshot

    # Generate a massive header with 150 links (>6000 chars)
    mega_nav = "<header><nav>" + "".join([f'<a href="/link{i}">Navigation Menu Link Item #{i}</a> ' for i in range(150)]) + "</nav></header>"
    
    courses_table = """
    <main>
      <h1>Admissions 2026 - Programmes Offered</h1>
      <table>
        <thead><tr><th>Department</th><th>Programmes</th></tr></thead>
        <tbody>
          <tr><td>School of Computing</td><td>B.Tech Computer Science & Engineering (Thanjavur Campus)</td></tr>
          <tr><td>School of Electrical</td><td>B.Tech Electronics & Communication Engineering</td></tr>
        </tbody>
      </table>
    </main>
    <footer><p>Copyright Sastra University</p></footer>
    """
    
    html = f"<html><body>{mega_nav}\n{courses_table}</body></html>"
    pruned = _prune_dom_snapshot(html, max_chars=12000)

    # Mega nav should be stripped
    assert "Navigation Menu Link Item #50" not in pruned
    assert "Copyright Sastra University" not in pruned
    # Course table must be preserved
    assert "Programmes Offered" in pruned
    assert "B.Tech Computer Science & Engineering (Thanjavur Campus)" in pruned
    # Course content should appear near the beginning of pruned text
    assert pruned.index("Programmes Offered") < 200


