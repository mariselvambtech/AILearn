"""
TDVC Test Harness for HITLPlugin & Event Bus Interception (Phase 10 & 11).
Verifies:
1. HITLPlugin attachment to WebRecorder Event Bus.
2. Async trigger_intervention handling Continuous Observer Mode UI injection & Resume AI promise resolution.
3. Mocked TTS cue and faster-whisper transcription payload packaging.
4. Graceful error handling when audio/whisper drivers encounter exceptions.
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

# Ensure webai_playwright_python is in import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python")))

from webai_playwright.recorder import WebRecorder


def create_mock_page(mock_click_data: Dict[str, Any] | None = None) -> MagicMock:
    """Create a mocked Playwright Page object simulating Observer Mode resolution."""
    if mock_click_data is None:
        mock_click_data = {
            "status": "resolved",
            "action": "observer_mode_complete",
            "x": 150,
            "y": 300,
            "targetTag": "RESUME_AI",
            "targetId": "webai-hitl-resume-btn",
            "textContent": "Resume AI",
        }

    page = MagicMock()
    page.evaluate = AsyncMock(return_value=mock_click_data)
    page.add_init_script = AsyncMock()
    return page


def test_hitl_plugin_successful_resolution():
    """Assert HITLPlugin packages observer resolution data and transcribed voice into payload."""
    from webai_playwright.plugins.hitl_plugin import HITLPlugin

    mock_page = create_mock_page()
    plugin = HITLPlugin(tts_prompt="Test TTS Prompt", whisper_model_size="tiny")

    # Mock pyttsx3 and faster-whisper calls inside plugin
    with patch.object(plugin, "_speak_tts_cue_async") as mock_tts, \
         patch.object(plugin, "_transcribe_vocal_explanation", return_value="Mocked vocal explanation: completed login form") as mock_whisper:

        resolution = asyncio.run(plugin.trigger_intervention(mock_page, {"reason": "consecutive_spatial_mapping_failures"}))

        # Assertions
        assert resolution is not None, "Resolution payload should not be None"
        assert resolution.get("status") == "resolved", f"Expected status 'resolved', got {resolution.get('status')}"
        assert resolution.get("action") == "observer_mode_complete", f"Expected action 'observer_mode_complete', got {resolution.get('action')}"
        
        click_data = resolution.get("click", {})
        assert click_data.get("x") == 150, f"Expected x=150, got {click_data.get('x')}"
        assert click_data.get("y") == 300, f"Expected y=300, got {click_data.get('y')}"
        assert click_data.get("targetId") == "webai-hitl-resume-btn", f"Expected targetId='webai-hitl-resume-btn', got {click_data.get('targetId')}"
        assert click_data.get("targetTag") == "RESUME_AI", f"Expected targetTag='RESUME_AI', got {click_data.get('targetTag')}"
        
        transcription = resolution.get("audio_transcription")
        assert transcription == "Mocked vocal explanation: completed login form", f"Unexpected transcription: {transcription}"
        
        mock_tts.assert_called_once()
        print(" [PASS] test_hitl_plugin_successful_resolution")


def test_hitl_plugin_graceful_degradation():
    """Assert HITLPlugin handles hardware/audio transcription failures gracefully without crashing."""
    from webai_playwright.plugins.hitl_plugin import HITLPlugin

    mock_page = create_mock_page()
    plugin = HITLPlugin()

    # Simulate pyttsx3 and faster-whisper raising hardware exceptions
    with patch.object(plugin, "_speak_tts_cue_async", side_effect=RuntimeError("Audio output device missing")), \
         patch.object(plugin, "_transcribe_vocal_explanation", side_effect=RuntimeError("Whisper CUDA error")):

        # Must execute without raising exception
        resolution = asyncio.run(plugin.trigger_intervention(mock_page, {"reason": "consecutive_spatial_mapping_failures"}))

        assert resolution is not None
        assert resolution.get("status") == "resolved"
        assert resolution.get("action") == "observer_mode_complete"
        assert resolution.get("click", {}).get("x") == 150
        # Transcription should gracefully degrade to fallback string or empty message
        transcription = resolution.get("audio_transcription", "")
        assert isinstance(transcription, str)
        print(" [PASS] test_hitl_plugin_graceful_degradation")


def test_hitl_plugin_event_bus_attach():
    """Assert HITLPlugin registers correctly with WebRecorder Event Bus."""
    from webai_playwright.plugins.hitl_plugin import HITLPlugin

    recorder = WebRecorder()
    plugin = HITLPlugin()
    recorder.register_plugin(plugin)

    assert plugin in recorder.plugins, "HITLPlugin should be registered in recorder.plugins"
    assert "human_intervention_required" in recorder._subscribers, "WebRecorder should have subscriber for 'human_intervention_required'"
    print(" [PASS] test_hitl_plugin_event_bus_attach")


if __name__ == "__main__":
    print(" Running HITL Plugin TDVC Test Suite...")
    test_hitl_plugin_event_bus_attach()
    test_hitl_plugin_successful_resolution()
    test_hitl_plugin_graceful_degradation()
    print(" ALL HITL PLUGIN TESTS PASSED!")
