"""
Audio Transcriber Strategy & Factory Module for WebAI Playwright.

Provides an extensible strategy pattern for dynamic voice model switching
between faster-whisper and Alibaba SenseVoice, controlled via the VOICE_MODEL
environment variable.
"""
from __future__ import annotations

import abc
import os
from typing import Any, Dict, List, Optional


class BaseTranscriber(abc.ABC):
    """Abstract Base Class for voice model transcription strategies."""

    @abc.abstractmethod
    def transcribe_text(self, file_path: str) -> str:
        """
        Transcribe the audio file directly into a clean, plain text string.

        Args:
            file_path: Absolute or relative path to the PCM WAV audio file.

        Returns:
            The complete transcribed text as a single string.
        """
        pass

    @abc.abstractmethod
    def transcribe_segments(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Transcribe the audio file into timestamped segments.

        Args:
            file_path: Absolute or relative path to the PCM WAV audio file.

        Returns:
            A list of segment dictionaries in milliseconds:
            [{"start": float, "end": float, "start_ms": float, "end_ms": float, "text": str}, ...]
        """
        pass


class FasterWhisperTranscriber(BaseTranscriber):
    """
    faster-whisper transcription strategy utilizing hardware auto-detection (CUDA/CPU),
    VAD filtering, and hallucination reduction parameters.
    """

    def __init__(
        self,
        model_size: str = "Systran/faster-distil-whisper-large-v3",
        device: str = "auto",
        compute_type: str = "default",
    ) -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _get_model(self):
        """Lazy initialization of faster-whisper model."""
        if self._model is None:
            from faster_whisper import WhisperModel
            try:
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
            except Exception as e:
                if self.model_size == "base.en":
                    print(f" [WARN] [FasterWhisperTranscriber] Failed to load '{self.model_size}', falling back to 'base': {e}")
                    self._model = WhisperModel("base", device=self.device, compute_type=self.compute_type)
                elif self.model_size != "base":
                    print(f" [WARN] [FasterWhisperTranscriber] Failed to load '{self.model_size}', falling back to 'base.en': {e}")
                    self._model = WhisperModel("base.en", device=self.device, compute_type=self.compute_type)
                else:
                    raise
        return self._model

    def transcribe_text(self, file_path: str) -> str:
        """Transcribe WAV audio into joined text."""
        segments = self.transcribe_segments(file_path)
        return " ".join(seg["text"] for seg in segments if seg.get("text")).strip()

    def transcribe_segments(self, file_path: str) -> List[Dict[str, Any]]:
        """Transcribe WAV audio into timestamped segments in milliseconds."""
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 100:
            return []

        try:
            model = self._get_model()
            segments, _ = model.transcribe(
                file_path,
                word_timestamps=False,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                condition_on_previous_text=False,
                beam_size=5,
                initial_prompt="User instructing an automated web browser.",
            )

            output_segments: List[Dict[str, Any]] = []
            for seg in segments:
                text = (seg.text or "").strip()
                if not text:
                    continue
                start_ms = float(seg.start * 1000.0)
                end_ms = float(seg.end * 1000.0)
                output_segments.append({
                    "start": start_ms,
                    "end": end_ms,
                    "start_ms": start_ms,
                    "end_ms": end_ms,
                    "text": text,
                })
            return output_segments
        except Exception as e:
            print(f" [WARN] [FasterWhisperTranscriber] Transcription failed: {e}")
            return []


class SenseVoiceTranscriber(BaseTranscriber):
    """
    Alibaba SenseVoice transcription strategy utilizing FunASR with rich transcription
    post-processing and full-range segment mapping for step alignment.
    """

    def __init__(
        self,
        model_name: str = "iic/SenseVoiceSmall",
        vad_model: str = "fsmn-vad",
        device: str = "cuda:0",
    ) -> None:
        self.model_name = model_name
        self.vad_model = vad_model
        self.device = device
        self._model = None

    def _get_model(self):
        """Lazy initialization of FunASR SenseVoice model with graceful dependency warning."""
        if self._model is None:
            try:
                from funasr import AutoModel
            except ImportError as e:
                err_msg = str(e)
                if "PyTorch" in err_msg or "torch" in err_msg:
                    print(f" [WARN] [SenseVoiceTranscriber] PyTorch is required by FunASR: {err_msg}")
                    raise ImportError(f"SenseVoice requires PyTorch. {err_msg}") from e
                print(" [WARN] [SenseVoiceTranscriber] 'funasr' is not installed. To use SenseVoice, run: pip install funasr modelscope")
                raise ImportError(
                    "funasr is not installed. To use SenseVoice, please run: pip install funasr modelscope"
                ) from e
            try:
                self._model = AutoModel(model=self.model_name, vad_model=self.vad_model, device=self.device)
            except Exception as e:
                if self.device != "cpu":
                    print(f" [WARN] [SenseVoiceTranscriber] Failed on '{self.device}', falling back to 'cpu': {e}")
                    self._model = AutoModel(model=self.model_name, vad_model=self.vad_model, device="cpu")
                else:
                    raise
        return self._model

    def transcribe_text(self, file_path: str) -> str:
        """Transcribe audio using SenseVoice and clean rich tags with postprocess_utils."""
        if not os.path.exists(file_path) or os.path.getsize(file_path) < 100:
            return ""

        try:
            model = self._get_model()
            res = model.generate(input=file_path, language="en", use_itn=True, batch_size_s=60,)
            if not res or not isinstance(res, list):
                return ""
            raw_text = res[0].get("text", "")
            try:
                from funasr.utils.postprocess_utils import rich_transcription_postprocess
                clean_text = rich_transcription_postprocess(raw_text).strip()
            except Exception:
                clean_text = raw_text.strip()
            return clean_text
        except Exception as e:
            print(f" [WARN] [SenseVoiceTranscriber] Text transcription failed: {e}")
            return ""

    def transcribe_segments(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Returns a single segment spanning the entire audio session (0..999999 ms)
        to safely align SenseVoice transcriptions with recorded browser steps.
        """
        text = self.transcribe_text(file_path)
        if not text:
            return []
        return [{
            "start": 0.0,
            "end": 999999.0,
            "start_ms": 0.0,
            "end_ms": 999999.0,
            "text": text,
        }]


def get_transcriber(voice_model: Optional[str] = None) -> BaseTranscriber:
    """
    Factory function returning the active transcriber strategy.

    Reads the provided argument or the VOICE_MODEL environment variable:
      - 'sensevoice' -> SenseVoiceTranscriber
      - 'whisper' (default) -> FasterWhisperTranscriber
    """
    model_choice = (voice_model or os.getenv("VOICE_MODEL", "whisper")).strip().lower()
    if "sense" in model_choice:
        return SenseVoiceTranscriber()
    return FasterWhisperTranscriber()


# Global singleton instance (lazily initialized on first transcribe call)
ACTIVE_TRANSCRIBER: BaseTranscriber = get_transcriber()
