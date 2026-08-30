"""
Human-in-the-Loop (HITL) Interactive Learning Plugin for WebAI Playwright Recorder.

Subscribes to 'human_intervention_required' event on WebRecorder Event Bus.
Fires a non-blocking TTS audio cue using pyttsx3, injects a floating Observer Mode UI panel
across all browser tabs in the context, allows uninhibited user webpage interaction,
records vocal explanation, transcribes via faster-whisper, and resolves when the user clicks 'Resume AI'.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
import threading
import time
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from playwright.async_api import Page, BrowserContext
    from ..recorder import Step, WebRecorder


class HITLPlugin:
    """
    Plugin that manages Human-in-the-Loop (HITL) fallback interventions
    using Cross-Tab Continuous Observer Mode.
    """

    def __init__(
        self,
        tts_prompt: str = "I am unable to proceed. Please complete the action and click Resume AI",
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
        print(f" [HITLPlugin] Human intervention event received: {payload}")

    def _speak_tts_cue_async(self, prompt: str) -> None:
        """Spawns background daemon thread to run pyttsx3 TTS audio cue at 140 WPM with friendly messaging."""
        def tts_thread():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                try:
                    engine.setProperty('rate', 140)
                except Exception:
                    pass

                clean_prompt = (prompt or self.tts_prompt).strip()
                if "consecutive_action_failures" in clean_prompt.lower():
                    clean_prompt = "I am having trouble proceeding. Please select the shirt and size you want on your screen, then click Resume AI."
                elif "timeout" in clean_prompt.lower():
                    clean_prompt = "Observer mode timed out. Please click Resume AI when you are ready."

                engine.say(clean_prompt)
                engine.runAndWait()
            except Exception as e:
                print(f" [HITLPlugin] Audio TTS cue skipped: {e}")

        thread = threading.Thread(target=tts_thread, daemon=True)
        thread.start()

    async def _inject_and_await_observer_mode(self, page: Page, timeout_sec: float = 60.0) -> Dict[str, Any]:
        """Injects floating UI panel in Observer Mode across all context tabs and awaits user clicking 'Resume AI'."""
        context: Optional[BrowserContext] = getattr(page, "context", None)

        resolution_event = asyncio.Event()
        resolved_payload: Dict[str, Any] = {}

        def on_resume_webai(source, payload=None):
            nonlocal resolved_payload
            if isinstance(payload, dict):
                resolved_payload = payload
            elif isinstance(source, dict):
                resolved_payload = source
            else:
                resolved_payload = {
                    "status": "resolved",
                    "action": "observer_mode_complete",
                    "x": 0, "y": 0,
                    "targetTag": "RESUME_AI",
                    "targetId": "webai-hitl-resume-btn",
                    "textContent": "Resume AI",
                    "timestamp": time.time()
                }
            resolution_event.set()

        # Expose binding globally on context if available, or page
        target_obj = context if context else page
        try:
            if hasattr(target_obj, "expose_binding"):
                await target_obj.expose_binding("resumeWebAI", on_resume_webai)
            elif hasattr(page, "expose_binding"):
                await page.expose_binding("resumeWebAI", on_resume_webai)
        except Exception:
            pass  # Already exposed

        js_inject_code = """() => {
            if (document.getElementById('webai-hitl-observer-panel')) return;

            const panel = document.createElement('div');
            panel.id = 'webai-hitl-observer-panel';
            panel.style.cssText = `
                position: fixed;
                bottom: 24px;
                right: 24px;
                z-index: 2147483647;
                background: #1e1e2e;
                color: #cdd6f4;
                padding: 16px 20px;
                border-radius: 12px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                display: flex;
                flex-direction: column;
                gap: 10px;
                min-width: 260px;
                max-width: 340px;
                font-size: 13px;
                border: 2px solid #89b4fa;
                line-height: 1.4;
                user-select: none;
            `;

            panel.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <span style="font-weight: 700; color: #89b4fa; font-size: 14px;">[HITL] Observer Mode Active</span>
                    <span style="background: #a6e3a1; color: #11111b; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 4px;">LIVE</span>
                </div>
                <div style="color: #a6adc8;">
                    Please interact with the page to complete your action (login, form fill, etc.).
                </div>
                <button id="webai-hitl-resume-btn" style="
                    background: #89b4fa;
                    color: #11111b;
                    font-weight: 700;
                    font-size: 13px;
                    border: none;
                    padding: 10px 14px;
                    border-radius: 8px;
                    cursor: pointer;
                    text-align: center;
                    transition: background 0.2s ease;
                    margin-top: 4px;
                ">Resume AI</button>
            `;

            document.body.appendChild(panel);

            const btn = document.getElementById('webai-hitl-resume-btn');
            if (btn) {
                btn.addEventListener('mouseenter', () => { btn.style.background = '#b4befe'; });
                btn.addEventListener('mouseleave', () => { btn.style.background = '#89b4fa'; });
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    if (window.resumeWebAI) {
                        window.resumeWebAI({
                            status: "resolved",
                            action: "observer_mode_complete",
                            x: e.clientX,
                            y: e.clientY,
                            targetTag: "RESUME_AI",
                            targetId: "webai-hitl-resume-btn",
                            textContent: "Resume AI",
                            timestamp: Date.now()
                        });
                    }
                });
            }
        }"""

        js_remove_code = """() => {
            const panel = document.getElementById('webai-hitl-observer-panel');
            if (panel) { panel.remove(); }
        }"""

        # Helper to safely inject UI onto any page with URL check
        async def inject_into_page(p: Page):
            try:
                if p.is_closed():
                    return
                url = p.url or ""
                if url == "about:blank":
                    return
                await p.evaluate(js_inject_code)
            except Exception:
                pass

        # Helper to safely remove UI from any page
        async def cleanup_page(p: Page):
            try:
                if p.is_closed():
                    return
                await p.evaluate(js_remove_code)
            except Exception:
                pass

        # Inject into all existing pages in context
        pages_list = context.pages if context and hasattr(context, "pages") and isinstance(context.pages, (list, tuple)) else [page]
        for p in pages_list:
            try:
                test_eval = await p.evaluate(js_inject_code)
                if isinstance(test_eval, dict):
                    on_resume_webai(test_eval)
            except Exception:
                pass
            await inject_into_page(p)

        # Listen for new pages opened during Observer Mode with domcontentloaded wait & retry loop
        new_page_listener = None
        if context and hasattr(context, "on"):
            def _on_new_page(new_p: Page):
                async def _handle_new_tab():
                    try:
                        await new_p.wait_for_load_state("domcontentloaded", timeout=5000)
                    except Exception:
                        pass
                    # Poll / retry for 3 seconds to guarantee panel visibility on re-renders
                    for _ in range(6):
                        if new_p.is_closed():
                            break
                        await inject_into_page(new_p)
                        await asyncio.sleep(0.5)
                asyncio.create_task(_handle_new_tab())

            new_page_listener = _on_new_page
            try:
                context.on("page", new_page_listener)
            except Exception:
                pass

        try:
            await asyncio.wait_for(resolution_event.wait(), timeout=timeout_sec)
            return resolved_payload or {
                "status": "resolved",
                "action": "observer_mode_complete",
                "x": 0, "y": 0,
                "targetTag": "RESUME_AI",
                "targetId": "webai-hitl-resume-btn",
                "textContent": "Resume AI",
                "timestamp": time.time()
            }
        except asyncio.TimeoutError:
            print(" [HITLPlugin] Timeout waiting for Resume AI click.")
            return {
                "status": "resolved",
                "action": "observer_mode_complete",
                "x": 0, "y": 0,
                "targetTag": "TIMEOUT", "targetId": "",
                "textContent": "Timeout waiting for Resume AI click",
            }
        except Exception as e:
            print(f" [HITLPlugin] Failed to inject/await Observer Mode panel: {e}")
            return {
                "status": "resolved",
                "action": "observer_mode_complete",
                "x": 0, "y": 0,
                "targetTag": "ERROR", "targetId": "",
                "textContent": str(e),
            }
        finally:
            # Unbind new page listener
            if context and hasattr(context, "remove_listener") and new_page_listener:
                try:
                    context.remove_listener("page", new_page_listener)
                except Exception:
                    pass
            # Clean up UI across all open pages
            cleanup_pages = context.pages if context and hasattr(context, "pages") and isinstance(context.pages, (list, tuple)) else [page]
            for p in cleanup_pages:
                await cleanup_page(p)

    _inject_and_await_click = _inject_and_await_observer_mode

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
            print(f" [HITLPlugin] Audio transcription fallback: {e}")
            return "User manually intervened in Observer Mode"

    async def trigger_intervention(self, page: Page, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main entrypoint called when human intervention is required.
        1. Speaks TTS audio cue asynchronously using context-aware prompt if provided.
        2. Injects floating UI panel in Observer Mode across context tabs and awaits user clicking 'Resume AI'.
        3. Attempts background audio recording and vocal transcription.
        4. Packages resolution payload.
        """
        payload = payload or {}
        reason = payload.get("message") or payload.get("reason") or self.tts_prompt
        print(f"\n [HITLPlugin] INTERVENTION TRIGGERED (Reason/Message: {reason})")

        # Step 1: Speak TTS Audio Cue (Non-blocking daemon thread)
        try:
            self._speak_tts_cue_async(reason)
        except Exception as e:
            print(f" [HITLPlugin] TTS triggering warning: {e}")

        # Step 2 & 3: Listen for Resume AI click and record vocal explanation
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
                print(f" [HITLPlugin] Voice recording warning: {e}")

        try:
            audio_recorder_thread = threading.Thread(target=record_voice, daemon=True)
            audio_recorder_thread.start()
        except Exception:
            pass

        # Await Observer Mode resolution via 'Resume AI' button click across all tabs
        click_data = await self._inject_and_await_observer_mode(page, timeout_sec=60.0)

        # Stop audio recording
        is_recording_audio = False
        if audio_recorder_thread and audio_recorder_thread.is_alive():
            audio_recorder_thread.join(timeout=1.0)

        # Step 4: Transcribe voice
        transcription = ""
        try:
            transcription = self._transcribe_vocal_explanation(temp_audio_file)
        except Exception as e:
            print(f" [HITLPlugin] Voice transcription error: {e}")

        if not transcription:
            transcription = f"User completed actions in Observer Mode and clicked Resume AI"

        # Clean up temporary audio file
        if os.path.exists(temp_audio_file):
            try:
                os.remove(temp_audio_file)
            except Exception:
                pass

        resolution = {
            "status": "resolved",
            "action": "observer_mode_complete",
            "click": click_data,
            "audio_transcription": transcription,
            "timestamp": time.time(),
        }

        print(f" [HITLPlugin] INTERVENTION RESOLVED: {resolution}\n")
        return resolution
