"""
Audio Capture Plugin for WebAI Playwright Recorder.

Provides background audio recording (16kHz Mono PCM WAV) synchronized with 
browser events emitted by the WebRecorder Event Bus.
"""
from __future__ import annotations

import os
import time
import threading
import numpy as np
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..recorder import Step, WebRecorder


class AudioCapturePlugin:
    """
    Plugin that captures background audio during WebRecorder sessions.
    Subscribes to 'recording_started' and 'recording_stopped' event bus events.
    """

    def __init__(self, output_file: str = "session_audio.wav", samplerate: int = 16000, channels: int = 1) -> None:
        self.output_file = output_file
        self.samplerate = samplerate
        self.channels = channels
        self._is_recording = False
        self._thread: Optional[threading.Thread] = None
        self._stream = None
        self._sound_file = None
        self._recorder: Optional[WebRecorder] = None
        self._last_frames_time = 0.0

    def attach(self, recorder: WebRecorder) -> None:
        """Attach to WebRecorder event bus and subscribe to lifecycle events."""
        self._recorder = recorder
        recorder.subscribe("recording_started", self._on_recording_started)
        recorder.subscribe("recording_stopped", self._on_recording_stopped)

    def _on_recording_started(self, event_name: str, step: Optional[Step], payload: Dict[str, Any]) -> None:
        """Event handler for session start."""
        if self._is_recording:
            return

        self._is_recording = True
        self._thread = threading.Thread(target=self._record_audio_loop, daemon=True)
        self._thread.start()

    def _on_recording_stopped(self, event_name: str, step: Optional[Step], payload: Dict[str, Any]) -> None:
        """Event handler for session stop."""
        self._is_recording = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)

    def _record_audio_loop(self) -> None:
        """Background thread loop recording PCM audio from default microphone."""
        try:
            import sounddevice as sd
            import soundfile as sf

            # Open SoundFile for writing WAV audio
            self._sound_file = sf.SoundFile(
                self.output_file,
                mode="w",
                samplerate=self.samplerate,
                channels=self.channels,
                subtype="PCM_16"
            )
            self._last_frames_time = time.time()

            def audio_callback(indata, frames, time_info, status):
                if status:
                    print(f" [AudioPlugin] Stream status warning: {status}")
                if self._is_recording and self._sound_file:
                    self._sound_file.write(indata)
                    self._last_frames_time = time.time()

            with sd.InputStream(
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="int16",
                callback=audio_callback
            ):
                while self._is_recording:
                    time.sleep(0.1)
                    # Fallback for silent/virtual mic streams: if no frames arrived for > 0.2s, write silence
                    now = time.time()
                    elapsed = now - self._last_frames_time
                    if elapsed >= 0.2 and self._sound_file:
                        silence_frames = int(elapsed * self.samplerate)
                        if silence_frames > 0:
                            silence_data = np.zeros((silence_frames, self.channels), dtype=np.int16)
                            self._sound_file.write(silence_data)
                            self._last_frames_time = now

        except Exception as e:
            print(f" [WARN] [AudioPlugin] Audio capture warning (recording continuing without mic audio): {e}")
            # Fallback file creation if mic stream is completely blocked/missing
            try:
                import soundfile as sf
                if self._sound_file is None:
                    self._sound_file = sf.SoundFile(
                        self.output_file,
                        mode="w",
                        samplerate=self.samplerate,
                        channels=self.channels,
                        subtype="PCM_16"
                    )
                while self._is_recording:
                    silence_data = np.zeros((int(0.1 * self.samplerate), self.channels), dtype=np.int16)
                    self._sound_file.write(silence_data)
                    time.sleep(0.1)
            except Exception:
                pass
        finally:
            if self._sound_file:
                try:
                    self._sound_file.flush()
                    self._sound_file.close()
                except Exception:
                    pass
                self._sound_file = None
