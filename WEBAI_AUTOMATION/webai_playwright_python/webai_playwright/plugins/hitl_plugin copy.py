"""
Human-in-the-Loop (HITL) Interactive Learning Plugin for WebAI Playwright Recorder.

Subscribes to 'human_intervention_required' event on WebRecorder Event Bus.
Fires a non-blocking TTS audio cue using pyttsx3, injects DOM click listener via Playwright,
records vocal explanation and transcribes via faster-whisper, and returns a resolution payload.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import threading
import time
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page
    from ..recorder import Step, WebRecorder


HITL_CLICK_SCRIPT = """
(() => {
    window.__hitl_click__ = null;
    const handler = (e) => {
        const target = e.target || {};
        window.__hitl_click__ = {
            x: e.clientX,
            y: e.clientY,
            targetTag: (target.tagName || '').toUpperCase(),
            targetId: target.id || '',
            textContent: (target.textContent || '').trim().substring(0, 100)
        };
    };
    document.addEventListener('click', handler, { once: true, capture: true });
})();
"""


class HITLPlugin:
    """
    Plugin that manages Human-in-the-Loop (HITL) fallback interventions.
    """

    def __init__(
        self,
        tts_prompt: str = "I am unable to proceed. Please click the target for me",
        whisper_model_size: str = "tiny",
    ) -> None:
        self.tts_prompt = tts_prompt
        self.whisper_model_size = whisper_model_size
        self._recorder: Optional[WebRecorder] = None
        self._is_intervening = False

    def attach(self, recorder: WebRecorder) -> None:
        """Attach to WebRecorder event bus and subscribe to intervention requests."""
        self._recorder = recorder
        recorder.subscribe("human_intervention_required", self._on_human_intervention_required)

    def _on_human_intervention_required(
        self, event_name: str, step: Optional[Step], payload: Dict[str, Any]
    ) -> None:
        """Event bus handler when human intervention is triggered."""
        self._is_intervening = True
        print(f" 🤝 [HITLPlugin] Human intervention event received: {payload}")

    def _speak_tts_cue_async(self, prompt: str) -> None:
        """Spawns background daemon thread to run pyttsx3 TTS audio cue."""
        def tts_thread():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.say(prompt)
                engine.runAndWait()
            except Exception as e:
                print(f" ⚠️ [HITLPlugin] Audio TTS cue skipped: {e}")

        thread = threading.Thread(target=tts_thread, daemon=True)
        thread.start()

    async def _inject_and_await_click(self, page: Page, timeout_sec: float = 30.0) -> Dict[str, Any]:
        """Injects JS click listener into DOM and polls page.evaluate for window.__hitl_click__."""
        try:
            await page.evaluate(HITL_CLICK_SCRIPT)
        except Exception as e:
            print(f" ⚠️ [HITLPlugin] Failed to inject JS click listener: {e}")

        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            try:
                click_data = await page.evaluate("window.__hitl_click__")
                if click_data:
                    return click_data
            except Exception:
                pass
            await asyncio.sleep(0.2)

        # Fallback if timeout reached
        return {
            "x": 0,
            "y": 0,
            "targetTag": "UNKNOWN",
            "targetId": "",
            "textContent": "Timeout waiting for manual click",
        }

    def _transcribe_vocal_explanation(self, audio_filepath: str) -> str:
        """Transcribe PCM WAV audio using faster-whisper."""
        try:
            if not os.path.exists(audio_filepath) or os.path.getsize(audio_filepath) == 0:
                return ""
            from faster_whisper import WhisperModel
            model = WhisperModel(self.whisper_model_size, device="cpu", compute_type="int8")
            segments, _ = model.transcribe(audio_filepath, beam_size=5)
            transcription = " ".join([segment.text for segment in segments]).strip()
            return transcription
        except Exception as e:
            print(f" ⚠️ [HITLPlugin] Audio transcription fallback: {e}")
            return "User manually intervened via click"

    async def trigger_intervention(self, page: Page, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entrypoint called when human intervention is required.
        1. Speaks TTS audio cue asynchronously.
        2. Injects JS click listener and awaits manual click.
        3. Attempts background audio recording and vocal transcription.
        4. Packages resolution payload.
        """
        payload = payload or {}
        reason = payload.get("reason", "consecutive_failures")
        print(f"\n 🚨 [HITLPlugin] INTERVENTION TRIGGERED (Reason: {reason})")

        # Step 1: Speak TTS Audio Cue (Non-blocking daemon thread)
        try:
            self._speak_tts_cue_async(self.tts_prompt)
        except Exception as e:
            print(f" ⚠️ [HITLPlugin] TTS triggering warning: {e}")

        # Step 2 & 3: Listen for click and record vocal explanation
        temp_audio_file = os.path.join(tempfile.gettempdir(), f"hitl_voice_{int(time.time())}.wav")
        audio_recorder_thread = None
        is_recording_audio = False

        # Attempt microphone recording on background thread
        def record_voice():
            nonlocal is_recording_audio
            try:
                import sounddevice as sd
                import soundfile as sf
                samplerate = 16000
                channels = 1
                is_recording_audio = True
                with sf.SoundFile(temp_audio_file, mode="w", samplerate=samplerate, channels=channels, subtype="PCM_16") as sound_file:
                    def audio_callback(indata, frames, time_info, status):
                        if is_recording_audio:
                            sound_file.write(indata)
                    with sd.InputStream(samplerate=samplerate, channels=channels, dtype="int16", callback=audio_callback):
                        while is_recording_audio:
                            time.sleep(0.1)
            except Exception as e:
                print(f" ⚠️ [HITLPlugin] Voice recording warning: {e}")

        try:
            audio_recorder_thread = threading.Thread(target=record_voice, daemon=True)
            audio_recorder_thread.start()
        except Exception:
            pass

        # Await manual DOM click
        click_data = await self._inject_and_await_click(page, timeout_sec=30.0)

        # Stop audio recording
        is_recording_audio = False
        if audio_recorder_thread and audio_recorder_thread.is_alive():
            audio_recorder_thread.join(timeout=1.0)

        # Step 4: Transcribe voice
        transcription = ""
        try:
            transcription = self._transcribe_vocal_explanation(temp_audio_file)
        except Exception as e:
            print(f" ⚠️ [HITLPlugin] Voice transcription error: {e}")

        if not transcription:
            transcription = f"User clicked {click_data.get('targetTag', 'element')} at ({click_data.get('x')}, {click_data.get('y')})"

        # Clean up temporary audio file
        if os.path.exists(temp_audio_file):
            try:
                os.remove(temp_audio_file)
            except Exception:
                pass

        resolution = {
            "status": "resolved",
            "click": click_data,
            "audio_transcription": transcription,
            "timestamp": time.time(),
        }

        print(f" ✅ [HITLPlugin] INTERVENTION RESOLVED: {resolution}\n")
        return resolution
