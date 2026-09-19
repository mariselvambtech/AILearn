"""
TDVC Test Harness for AudioAligner VAD & Anti-Hallucination Configuration.
Verifies that WhisperModel.transcribe() is called with required anti-hallucination kwargs:
vad_filter=True, condition_on_previous_text=False, beam_size=5,
vad_parameters={'min_silence_duration_ms': 500}, initial_prompt="User instructing an automated web browser."
Also verifies model upgrade to 'base.en' with graceful fallback.
"""
from __future__ import annotations

import os
import sys
from unittest.mock import MagicMock, patch

# Ensure import paths for webai_playwright_python modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python")))

from webai_playwright.audio_aligner import AudioAligner


def test_audio_vad_transcribe_kwargs(tmp_path=None):
    """
    Assert that AudioAligner.transcribe_audio calls model.transcribe with:
    - vad_filter=True
    - condition_on_previous_text=False
    - beam_size=5
    - vad_parameters=dict(min_silence_duration_ms=500)
    - initial_prompt="User instructing an automated web browser."
    """
    aligner = AudioAligner()
    
    mock_model = MagicMock()
    # transcribe returns (generator_or_list_of_segments, info)
    mock_model.transcribe.return_value = ([], MagicMock())
    aligner._model = mock_model

    # Create dummy audio file >= 100 bytes
    dummy_audio = os.path.join(os.path.dirname(__file__), "dummy_audio.wav")
    with open(dummy_audio, "wb") as f:
        f.write(b"RIFF" + b"\x00" * 120)

    try:
        aligner.transcribe_audio(dummy_audio)

        assert mock_model.transcribe.called, "model.transcribe was not called"
        _, kwargs = mock_model.transcribe.call_args

        print("Captured kwargs:", kwargs)
        assert kwargs.get("vad_filter") is True, f"Expected vad_filter=True, got {kwargs.get('vad_filter')}"
        assert kwargs.get("condition_on_previous_text") is False, f"Expected condition_on_previous_text=False, got {kwargs.get('condition_on_previous_text')}"
        assert kwargs.get("beam_size") == 5, f"Expected beam_size=5, got {kwargs.get('beam_size')}"
        assert kwargs.get("vad_parameters") == {"min_silence_duration_ms": 500}, f"Expected vad_parameters={{'min_silence_duration_ms': 500}}, got {kwargs.get('vad_parameters')}"
        assert kwargs.get("initial_prompt") == "User instructing an automated web browser.", f"Expected initial_prompt='User instructing an automated web browser.', got {kwargs.get('initial_prompt')}"
        print(" SUCCESS: All transcription VAD & anti-hallucination kwargs PASSED!")
    finally:
        if os.path.exists(dummy_audio):
            os.remove(dummy_audio)


def test_model_upgrade_and_fallback():
    """
    Assert that AudioAligner defaults to 'base.en' and falls back gracefully to 'base'.
    """
    aligner_default = AudioAligner()
    assert aligner_default.model_size == "base.en", f"Expected default model_size to be 'base.en', got {aligner_default.model_size}"

    # Test fallback mechanism when faster_whisper raises an exception on base.en
    mock_whisper_cls = MagicMock()
    def side_effect(model_name, **kwargs):
        if model_name == "base.en":
            raise RuntimeError("Model 'base.en' not available")
        return MagicMock(name=f"MockWhisper-{model_name}")

    mock_whisper_cls.side_effect = side_effect

    with patch.dict("sys.modules", {"faster_whisper": MagicMock(WhisperModel=mock_whisper_cls)}):
        aligner = AudioAligner(model_size="base.en")
        model = aligner._get_model()
        assert model is not None
        assert mock_whisper_cls.call_count == 2
        # First attempt with base.en, second fallback with base
        calls = [call[0][0] for call in mock_whisper_cls.call_args_list]
        assert calls == ["base.en", "base"], f"Expected calls ['base.en', 'base'], got {calls}"
        print(" SUCCESS: Model upgrade and fallback PASSED!")


if __name__ == "__main__":
    test_audio_vad_transcribe_kwargs()
    test_model_upgrade_and_fallback()
