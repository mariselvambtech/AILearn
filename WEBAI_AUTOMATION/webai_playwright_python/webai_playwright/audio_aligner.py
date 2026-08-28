"""
Audio Aligner Utility for WebAI Playwright Recorder.

Transcribes recorded session audio using faster-whisper (hardware auto-detected)
and aligns spoken context to recorded browser steps based on temporal proximity.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Union


class AudioAligner:
    """
    Utility class for transcribing audio and aligning voice context with recorded steps.
    """

    def __init__(self, model_size: str = "base") -> None:
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        """Lazy initialization of faster-whisper model with hardware auto-detection."""
        if self._model is None:
            from faster_whisper import WhisperModel
            # Automatically uses NVIDIA GPU (CUDA) if available, falling back cleanly to CPU
            self._model = WhisperModel(self.model_size, device="auto", compute_type="default")
        return self._model

    def transcribe_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Transcribes the WAV audio file and returns timestamped segments in milliseconds.
        """
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 100:
            print(f" [AudioAligner] Audio file invalid or empty: {audio_path}")
            return []

        try:
            model = self._get_model()
            segments, info = model.transcribe(audio_path, word_timestamps=False)
            
            output_segments = []
            for seg in segments:
                text = seg.text.strip()
                if not text:
                    continue
                output_segments.append({
                    "start_ms": seg.start * 1000.0,
                    "end_ms": seg.end * 1000.0,
                    "text": text
                })
            
            print(f" [AudioAligner] Transcribed {len(output_segments)} segments from {audio_path}")
            return output_segments

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
                start_win = seg["start_ms"] - 1000.0
                end_win = seg["end_ms"] + 2000.0

                if start_win <= step_ts <= end_win:
                    matching_texts.append(seg["text"])

            if matching_texts:
                # Concatenate multiple overlapping spoken segments cleanly
                combined_context = " ".join(matching_texts)
                if isinstance(step, dict):
                    step["voice_context"] = combined_context
                else:
                    setattr(step, "voice_context", combined_context)

        return steps
