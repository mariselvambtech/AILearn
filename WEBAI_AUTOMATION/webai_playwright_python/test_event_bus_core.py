"""
Phase 1 Test Suite: test_event_bus_core.py

Tests the WebRecorder Event Bus pub/sub mechanism, 13-locator strategy preservation,
and DataExtractionPlugin exception-trapping isolation.
"""
import sys
import types
import pytest

# Mock optional dependencies if missing in test runner environment
if "websockets" not in sys.modules:
    mock_ws = types.ModuleType("websockets")
    sys.modules["websockets"] = mock_ws

sys.path.insert(0, "webai_playwright_python")

from webai_playwright.recorder import WebRecorder, Step
from webai_playwright.plugins.data_extraction_plugin import DataExtractionPlugin


def test_event_bus_click_and_type_events():
    """
    Tests that WebRecorder correctly broadcasts click and type events
    with full 13-locator arrays intact to registered subscribers.
    """
    recorder = WebRecorder()
    received_events = []

    def mock_subscriber(event_name: str, step: Step, payload: dict):
        received_events.append((event_name, step, payload))

    recorder.subscribe("click", mock_subscriber)
    recorder.subscribe("type", mock_subscriber)

    locators_13_types = [
        {"type": "test-id", "value": "btn-submit"},
        {"type": "id", "value": "submit_button_1"},
        {"type": "name", "value": "submitBtn"},
        {"type": "aria-label", "value": "Submit Form"},
        {"type": "placeholder", "value": "Click to submit"},
        {"type": "title", "value": "Submit Title"},
        {"type": "alt", "value": "Submit Icon"},
        {"type": "href", "value": "https://example.com/submit"},
        {"type": "label", "value": "Submit Label"},
        {"type": "css", "value": "button#submit_button_1"},
        {"type": "text", "value": "Submit"},
        {"type": "role", "value": "button", "name": "Submit"},
        {"type": "xpath", "value": "//*[@id='submit_button_1']"}
    ]

    click_step = Step(action="click", url="https://example.com", name="Submit", locators=locators_13_types)
    type_step = Step(action="type", url="https://example.com", name="username", value="admin", locators=locators_13_types)

    recorder.emit("click", click_step, {"kind": "click", "url": "https://example.com", "name": "Submit", "locators": locators_13_types})
    recorder.emit("type", type_step, {"kind": "type_final", "url": "https://example.com", "label": "username", "value": "admin", "locators": locators_13_types})

    assert len(received_events) == 2
    assert received_events[0][0] == "click"
    assert len(received_events[0][1].locators) == 13
    assert received_events[0][1].locators[3]["type"] == "aria-label"

    assert received_events[1][0] == "type"
    assert received_events[1][1].value == "admin"
    print(" test_event_bus_click_and_type_events: PASSED (13 locators preserved)")


def test_plugin_exception_isolation():
    """
    Tests that if a subscriber plugin raises an exception during execution,
    the WebRecorder Event Bus traps the error and main event loop survives cleanly.
    """
    recorder = WebRecorder()

    def faulty_plugin_subscriber(event_name: str, step: Step, payload: dict):
        raise ValueError("Simulated Plugin IO Exception")

    recorder.subscribe("click", faulty_plugin_subscriber)

    step = Step(action="click", url="https://example.com", name="Test")
    
    try:
        recorder.emit("click", step, {})
        print(" test_plugin_exception_isolation: PASSED (Core loop survived subscriber exception)")
    except Exception as e:
        pytest.fail(f"Event bus failed to isolate subscriber exception: {e}")


def test_data_extraction_plugin_subscription():
    """
    Tests that DataExtractionPlugin subscribes to extract channel and safely handles file persistence calls.
    """
    recorder = WebRecorder()
    plugin = DataExtractionPlugin()
    
    saved_calls = []
    plugin._save_extraction_immediately = lambda step, options: saved_calls.append((step, options))
    
    plugin.attach(recorder)

    extract_step = Step(
        action="extract",
        url="https://example.com",
        name="price",
        value="$99.99",
        save_options={"formats": {"txt": True}, "folder": ".", "filename": "test_output"}
    )

    recorder.emit("extract", extract_step, {"save_options": extract_step.save_options})

    assert len(saved_calls) == 1
    assert saved_calls[0][0].name == "price"
    print(" test_data_extraction_plugin_subscription: PASSED")


if __name__ == "__main__":
    test_event_bus_click_and_type_events()
    test_plugin_exception_isolation()
    test_data_extraction_plugin_subscription()
    print("\n============================================================")
    print(" PHASE 1 TEST SUITE PASSED 100%")
    print("============================================================")
