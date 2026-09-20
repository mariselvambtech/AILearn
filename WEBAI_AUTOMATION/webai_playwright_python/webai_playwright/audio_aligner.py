"""
Audio Aligner Utility for WebAI Playwright Recorder.

Transcribes recorded session audio using the configured active transcriber strategy
(faster-whisper or SenseVoice) and aligns spoken context to recorded browser steps
based on temporal proximity.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Union

from .audio_transcriber import ACTIVE_TRANSCRIBER, BaseTranscriber, FasterWhisperTranscriber


class AudioAligner:
    """
    Utility class for transcribing audio and aligning voice context with recorded steps.
    """

    def __init__(
        self,
        transcriber: Optional[BaseTranscriber] = None,
        model_size: Optional[str] = None,
    ) -> None:
        """
        Initialize AudioAligner with an explicit transcriber strategy, or fallback to ACTIVE_TRANSCRIBER.
        """
        self.model_size = model_size or "base.en"
        if transcriber is not None:
            self.transcriber = transcriber
        elif model_size is not None:
            self.transcriber = FasterWhisperTranscriber(model_size=model_size)
        else:
            self.transcriber = ACTIVE_TRANSCRIBER

    def _get_model(self):
        """Forwarding method to underlying strategy model for backwards compatibility."""
        if hasattr(self.transcriber, "_get_model"):
            return self.transcriber._get_model()
        return getattr(self.transcriber, "_model", None)

    @property
    def _model(self):
        """Forwarding property to underlying strategy model for backwards compatibility."""
        if hasattr(self.transcriber, "_model"):
            return self.transcriber._model
        return None

    @_model.setter
    def _model(self, val):
        if hasattr(self.transcriber, "_model"):
            self.transcriber._model = val

    def transcribe_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Transcribes the WAV audio file using the active transcriber strategy and returns
        timestamped segments in milliseconds.
        """
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 100:
            print(f" [AudioAligner] Audio file invalid or empty: {audio_path}")
            return []

        try:
            segments = self.transcriber.transcribe_segments(audio_path)
            print(f" [AudioAligner] Transcribed {len(segments)} segments from {audio_path}")
            return segments
        except Exception as e:
            print(f" [WARN] [AudioAligner] Audio transcription failed: {e}")
            return []

    def align_steps(self, steps: List[Union[Dict[str, Any], Any]], segments: List[Dict[str, Any]]) -> List[Union[Dict[str, Any], Any]]:
        """
        Aligns voice transcript segments to recorded steps based on temporal proximity.
        Matching window: segment_start_ms - 1000 <= step.timestamp_ms <= segment_end_ms + 2000
        Handles multiple overlapping segments by concatenating text cleanly.
        """
        if not segments or not steps:
            return steps

        for step in steps:
            # Extract timestamp_ms safely whether step is a dict or dataclass instance
            if isinstance(step, dict):
                step_ts = step.get("timestamp_ms", 0.0)
            else:
                step_ts = getattr(step, "timestamp_ms", 0.0)

            if not step_ts:
                continue

            matching_texts = []
            for seg in segments:
                start_ms = seg.get("start_ms", seg.get("start", 0.0))
                end_ms = seg.get("end_ms", seg.get("end", 0.0))
                start_win = start_ms - 1000.0
                end_win = end_ms + 2000.0

                if start_win <= step_ts <= end_win:
                    text = seg.get("text", "").strip()
                    if text:
                        matching_texts.append(text)

            if matching_texts:
                # Concatenate multiple overlapping spoken segments cleanly
                combined_context = " ".join(matching_texts)
                if isinstance(step, dict):
                    step["voice_context"] = combined_context
                else:
                    setattr(step, "voice_context", combined_context)

        return steps
