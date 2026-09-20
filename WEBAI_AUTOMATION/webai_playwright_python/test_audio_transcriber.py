"""
Unit and integration tests for Audio Transcriber Strategy Pattern & Factory.
Tests FasterWhisperTranscriber, SenseVoiceTranscriber, get_transcriber(),
AudioAligner integration, and HITLPlugin integration.
"""
import os
import sys
from unittest.mock import MagicMock, patch
import pytest

# Ensure webai_playwright_python is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from webai_playwright.audio_transcriber import (
    BaseTranscriber,
    FasterWhisperTranscriber,
    SenseVoiceTranscriber,
    get_transcriber,
    ACTIVE_TRANSCRIBER,
)
from webai_playwright.audio_aligner import AudioAligner
from webai_playwright.plugins.hitl_plugin import HITLPlugin


@pytest.fixture
def dummy_wav(tmp_path):
    """Creates a valid dummy WAV file >= 100 bytes."""
    wav_file = tmp_path / "test_audio.wav"
    wav_file.write_bytes(b"RIFF" + b"\x00" * 150)
    return str(wav_file)


class DummySegment:
    def __init__(self, start, end, text):
        self.start = start
        self.end = end
        self.text = text


def test_factory_model_selection(monkeypatch):
    """Verify get_transcriber factory returns expected strategy based on argument and env."""
    # 1. Direct arguments
    whisper_t = get_transcriber("whisper")
    assert isinstance(whisper_t, FasterWhisperTranscriber)

    sense_t = get_transcriber("sensevoice")
    assert isinstance(sense_t, SenseVoiceTranscriber)

    # 2. Environment variable
    monkeypatch.setenv("VOICE_MODEL", "sensevoice")
    assert isinstance(get_transcriber(), SenseVoiceTranscriber)

    monkeypatch.setenv("VOICE_MODEL", "whisper")
    assert isinstance(get_transcriber(), FasterWhisperTranscriber)


def test_faster_whisper_transcriber(dummy_wav):
    """Verify FasterWhisperTranscriber segments and text transcription."""
    transcriber = FasterWhisperTranscriber()
    
    mock_model = MagicMock()
    mock_model.transcribe.return_value = (
        [
            DummySegment(start=1.2, end=3.5, text="Click the login button"),
            DummySegment(start=4.0, end=5.8, text="Type admin password"),
        ],
        MagicMock()
    )
    transcriber._model = mock_model

    # 1. Segments
    segments = transcriber.transcribe_segments(dummy_wav)
    assert len(segments) == 2
    assert segments[0]["start"] == 1200.0
    assert segments[0]["end"] == 3500.0
    assert segments[0]["start_ms"] == 1200.0
    assert segments[0]["end_ms"] == 3500.0
    assert segments[0]["text"] == "Click the login button"

    # 2. Plain Text
    text = transcriber.transcribe_text(dummy_wav)
    assert text == "Click the login button Type admin password"


def test_sense_voice_transcriber(dummy_wav):
    """Verify SenseVoiceTranscriber generation, postprocessing, and 0..999999ms segment."""
    transcriber = SenseVoiceTranscriber()

    mock_model = MagicMock()
    mock_model.generate.return_value = [{"text": "<|en|>Open settings page<|NEUTRAL|>"}]
    transcriber._model = mock_model

    # Mock rich_transcription_postprocess in postprocess_utils
    mock_postprocess = MagicMock(return_value="Open settings page")
    with patch.dict("sys.modules", {"funasr.utils.postprocess_utils": MagicMock(rich_transcription_postprocess=mock_postprocess)}):
        # 1. Plain text
        text = transcriber.transcribe_text(dummy_wav)
        assert text == "Open settings page"

        # 2. Segments
        segments = transcriber.transcribe_segments(dummy_wav)
        assert len(segments) == 1
        assert segments[0]["start"] == 0.0
        assert segments[0]["end"] == 999999.0
        assert segments[0]["text"] == "Open settings page"


def test_sense_voice_missing_dependency_warning():
    """Verify SenseVoiceTranscriber raises ImportError with pip instructions when funasr is missing."""
    transcriber = SenseVoiceTranscriber()
    
    with patch.dict("sys.modules", {"funasr": None}):
        with pytest.raises(ImportError) as exc_info:
            transcriber._get_model()
        assert "pip install funasr modelscope" in str(exc_info.value)


def test_audio_aligner_integration(dummy_wav):
    """Verify AudioAligner integrates with transcriber strategy and aligns steps."""
    mock_transcriber = MagicMock(spec=BaseTranscriber)
    mock_transcriber.transcribe_segments.return_value = [
        {"start_ms": 2000.0, "end_ms": 4000.0, "text": "Select blue shirt"}
    ]

    aligner = AudioAligner(transcriber=mock_transcriber)
    segments = aligner.transcribe_audio(dummy_wav)
    assert len(segments) == 1
    assert segments[0]["text"] == "Select blue shirt"

    steps = [
        {"action": "click", "name": "Shirt", "timestamp_ms": 2500.0}
    ]
    aligned = aligner.align_steps(steps, segments)
    assert aligned[0]["voice_context"] == "Select blue shirt"


def test_hitl_plugin_integration(dummy_wav, monkeypatch):
    """Verify HITLPlugin uses ACTIVE_TRANSCRIBER to transcribe vocal explanations."""
    mock_transcriber = MagicMock(spec=BaseTranscriber)
    mock_transcriber.transcribe_text.return_value = "User clicked the search button"
    
    import webai_playwright.plugins.hitl_plugin as hp
    monkeypatch.setattr(hp, "ACTIVE_TRANSCRIBER", mock_transcriber)

    plugin = HITLPlugin()
    result = plugin._transcribe_vocal_explanation(dummy_wav)
    assert result == "User clicked the search button"
    mock_transcriber.transcribe_text.assert_called_once_with(dummy_wav)
