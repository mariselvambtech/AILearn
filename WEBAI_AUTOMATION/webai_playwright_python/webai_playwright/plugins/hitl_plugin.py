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

from ..audio_transcriber import ACTIVE_TRANSCRIBER

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
        self._active_resolution_event: Optional[asyncio.Event] = None
        self._active_resolved_payload: Dict[str, Any] = {}

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

    async def _inject_and_await_observer_mode(self, page: Page, timeout_sec: float = 120.0) -> Dict[str, Any]:
        """Injects floating UI panel in Observer Mode across all context tabs and awaits user clicking 'Resume AI'."""
        context: Optional[BrowserContext] = getattr(page, "context", None)

        resolution_event = asyncio.Event()
        resolved_payload: Dict[str, Any] = {}

        self._active_resolution_event = resolution_event
        self._active_resolved_payload = resolved_payload

        # Expose binding globally on context if available, or page
        target_obj = context if context else page

        # Attach active state dict directly onto target_obj so existing exposed binding references latest invocation
        start_ms = int(time.time() * 1000)
        target_state = {
            "event": resolution_event,
            "payload": resolved_payload,
            "telemetry": [],
            "start_ms": start_ms,
        }
        setattr(target_obj, "_webai_hitl_state", target_state)

        def on_resume_webai(source, payload=None):
            nonlocal resolved_payload
            if isinstance(payload, dict):
                p = payload
            elif isinstance(source, dict):
                p = source
            else:
                p = {
                    "status": "resolved",
                    "action": "observer_mode_complete",
                    "x": 0, "y": 0,
                    "targetTag": "RESUME_AI",
                    "targetId": "webai-hitl-resume-btn",
                    "textContent": "Resume AI",
                    "timestamp": time.time()
                }

            resolved_payload = p
            self._active_resolved_payload = p

            # Update target_obj._webai_hitl_state dynamically
            state = getattr(target_obj, "_webai_hitl_state", None)
            if state and isinstance(state, dict):
                state["payload"] = p
                ev = state.get("event")
                if ev and isinstance(ev, asyncio.Event):
                    ev.set()

            resolution_event.set()

        def on_record_telemetry(source, payload=None):
            ev_data = payload if isinstance(payload, dict) else (source if isinstance(source, dict) else None)
            if not ev_data or not isinstance(ev_data, dict):
                return
            state = getattr(target_obj, "_webai_hitl_state", None)
            if state and isinstance(state.get("telemetry"), list):
                # Safeguard 1: Normalize timestamp_ms against Python session start_ms
                now_ms = int(time.time() * 1000)
                st_ms = state.get("start_ms", now_ms)
                ev_data["timestamp_ms"] = max(0, now_ms - st_ms)
                
                # Deduplicate by action, name, timestamp within 250ms window
                t_list = state["telemetry"]
                is_dup = any(
                    existing.get("action") == ev_data.get("action")
                    and existing.get("name") == ev_data.get("name")
                    and abs(existing.get("timestamp_ms", 0) - ev_data["timestamp_ms"]) < 250
                    for existing in t_list
                )
                if not is_dup:
                    t_list.append(ev_data)

        try:
            if hasattr(target_obj, "expose_binding"):
                await target_obj.expose_binding("resumeWebAI", on_resume_webai)
            elif hasattr(page, "expose_binding"):
                await page.expose_binding("resumeWebAI", on_resume_webai)
        except Exception:
            pass  # Already exposed; on_resume_webai closure or target_state dispatches cleanly

        try:
            if hasattr(target_obj, "expose_binding"):
                await target_obj.expose_binding("recordHITLTelemetry", on_record_telemetry)
            elif hasattr(page, "expose_binding"):
                await page.expose_binding("recordHITLTelemetry", on_record_telemetry)
        except Exception:
            pass

        js_inject_code = r"""() => {
            window.__webai_observer_start = window.__webai_observer_start || Date.now();
            window.__webai_telemetry = window.__webai_telemetry || [];

            const existingPanel = document.getElementById('webai-hitl-observer-panel');
            if (existingPanel) {
                try { existingPanel.remove(); } catch (_) {}
            }


            function extract13Locators(el) {
                if (!el || !el.getAttribute) return [];
                const locs = [];
                const clean = (s) => (s || '').replace(/[\r\n\t]+/g, ' ').trim();

                // 1. test-id
                const testId = el.getAttribute('data-testid') || el.getAttribute('data-test-id') || el.getAttribute('data-test');
                if (testId) locs.push({ type: 'test-id', value: testId });

                // 2. id
                const isDynamicId = /^[0-9]/.test(el.id || '') || /^modal-[A-Za-z0-9]{4,}$/.test(el.id || '') || /^:[a-zA-Z0-9_-]+:$/.test(el.id || '') || /ember\d+/i.test(el.id || '') || /^id-\d+/i.test(el.id || '');
                if (el.id && !isDynamicId) locs.push({ type: 'id', value: el.id });

                // 3. name
                const nameAttr = el.getAttribute('name');
                if (nameAttr) locs.push({ type: 'name', value: nameAttr });

                // 4. href
                const href = (el.tagName && el.tagName.toLowerCase() === 'a') ? el.getAttribute('href') : null;
                if (href && href.trim() && !href.startsWith('javascript:')) locs.push({ type: 'href', value: href.trim() });

                // 5. placeholder
                const ph = el.getAttribute('placeholder');
                if (ph && clean(ph)) locs.push({ type: 'placeholder', value: clean(ph) });

                // 6. alt
                const alt = el.getAttribute('alt');
                if (alt && clean(alt)) locs.push({ type: 'alt', value: clean(alt) });

                // 7. aria-label
                const aria = el.getAttribute('aria-label');
                if (aria && clean(aria)) locs.push({ type: 'aria-label', value: clean(aria) });

                // 8. title
                const title = el.getAttribute('title');
                if (title && clean(title)) locs.push({ type: 'title', value: clean(title) });

                // 9. label
                if (el.id) {
                    try {
                        const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
                        if (lbl && clean(lbl.innerText)) locs.push({ type: 'label', value: clean(lbl.innerText) });
                    } catch (_) {}
                }

                // 10. css
                let css = (el.tagName || '').toLowerCase();
                if (el.id && !isDynamicId) {
                    css += '#' + el.id;
                } else if (el.className && typeof el.className === 'string') {
                    const classes = el.className.trim().split(/\s+/).filter(Boolean).slice(0, 2).join('.');
                    if (classes) css += '.' + classes;
                }
                if (css) locs.push({ type: 'css', value: css });

                // 11. role
                const explicitRole = el.getAttribute('role');
                const tag = (el.tagName || '').toLowerCase();
                const role = explicitRole || (tag === 'button' ? 'button' : (tag === 'input' ? 'textbox' : (tag === 'a' ? 'link' : null)));
                const textVal = clean(el.innerText || el.textContent || '');
                if (role) locs.push({ type: 'role', value: role, name: textVal || aria || null });

                // 12. text
                if (textVal && textVal.length < 80) locs.push({ type: 'text', value: textVal });

                // 13. xpath
                function getXPath(node) {
                    if (!node || node.nodeType !== 1) return '';
                    if (node.id && !isDynamicId) return `//*[@id="${node.id}"]`;
                    const sameTagSiblings = node.parentNode ? Array.from(node.parentNode.children).filter(c => c.tagName === node.tagName) : [];
                    const idx = sameTagSiblings.length > 1 ? `[${sameTagSiblings.indexOf(node) + 1}]` : '';
                    return `${node.parentNode ? getXPath(node.parentNode) : ''}/${node.tagName.toLowerCase()}${idx}`;
                }
                try {
                    const xp = getXPath(el);
                    if (xp) locs.push({ type: 'xpath', value: xp });
                } catch (_) {}

                return locs;
            }

            if (!document.getElementById('webai-hitl-observer-panel')) {
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

                        // Flush active element input/type before resolving
                        try {
                            const activeEl = document.activeElement;
                            if (activeEl && !activeEl.closest('#webai-hitl-observer-panel')) {
                                const activeTag = (activeEl.tagName || '').toLowerCase();
                                if (activeTag === 'input' || activeTag === 'textarea' || activeEl.isContentEditable) {
                                    const val = activeEl.value || activeEl.innerText || '';
                                    if (val) {
                                        const lastTel = window.__webai_telemetry[window.__webai_telemetry.length - 1];
                                        if (!lastTel || lastTel.action !== 'type' || lastTel.value !== val) {
                                            window.__webai_telemetry.push({
                                                action: 'type',
                                                tag: activeTag,
                                                name: (activeEl.getAttribute('name') || activeEl.getAttribute('aria-label') || activeEl.placeholder || activeTag).substring(0, 100),
                                                value: val,
                                                url: window.location.href,
                                                locators: extract13Locators(activeEl),
                                                timestamp_ms: Date.now() - window.__webai_observer_start
                                            });
                                        }
                                    }
                                }
                            }
                        } catch (_) {}

                        if (window.resumeWebAI) {
                            window.resumeWebAI({
                                status: "resolved",
                                action: "observer_mode_complete",
                                x: e.clientX,
                                y: e.clientY,
                                targetTag: "RESUME_AI",
                                targetId: "webai-hitl-resume-btn",
                                textContent: "Resume AI",
                                telemetry: window.__webai_telemetry || [],
                                timestamp: Date.now()
                            });
                        }
                    });
                }
            }

            // 1. Click Listener with Semantic Filter & Shield 2 MutationObserver
            if (!window.__webai_click_handler) {
                window.__webai_click_handler = function(e) {
                    if (e.target && e.target.closest && e.target.closest('#webai-hitl-observer-panel')) return;

                    const target = e.target;
                    const tag = (target.tagName || '').toLowerCase();
                    const isRootContainer = tag === 'body' || tag === 'html';

                    const text = isRootContainer ? '' : (
                        target.innerText ||
                        target.getAttribute('aria-label') ||
                        target.getAttribute('alt') ||
                        target.getAttribute('placeholder') ||
                        target.getAttribute('title') ||
                        target.value ||
                        ''
                    ).trim();

                    const isInteractiveTag = [
                        'a', 'button', 'input', 'select', 'textarea', 'option', 'label', 'summary'
                    ].includes(tag);

                    const hasInteractiveRole = Boolean(
                        target.closest('[role="button"], [role="link"], [role="option"], [role="checkbox"], [role="menuitem"], [role="tab"], [role="combobox"]') ||
                        target.hasAttribute('onclick') ||
                        target.getAttribute('role')
                    );

                    const hasText = text.length > 0;
                    if (!isInteractiveTag && !hasInteractiveRole && !hasText) {
                        return;
                    }

                    let css = tag;
                    if (target.id) {
                        css += '#' + target.id;
                    } else if (target.className && typeof target.className === 'string') {
                        const classes = target.className.trim().split(/\s+/).filter(Boolean).slice(0, 2).join('.');
                        if (classes) css += '.' + classes;
                    }

                    const telemetryEvent = {
                        action: 'click',
                        tag: tag,
                        name: text.substring(0, 100),
                        text: text.substring(0, 100),
                        css: css,
                        x: e.clientX,
                        y: e.clientY,
                        url: window.location.href,
                        locators: extract13Locators(target),
                        timestamp_ms: Date.now() - window.__webai_observer_start
                    };

                    const initialUrl = window.location.href;
                    const isNavigational = Boolean(target.closest('a[href], button, [type="submit"]'));
                    if (isNavigational) {
                        window.__webai_telemetry.push(telemetryEvent);
                        if (window.recordHITLTelemetry) {
                            try { window.recordHITLTelemetry(telemetryEvent); } catch (_) {}
                        }
                    } else {
                        let stateChanged = false;
                        let observer = null;
                        try {
                            observer = new MutationObserver(function(mutations) {
                                for (const mutation of mutations) {
                                    if (mutation.target && mutation.target.closest && mutation.target.closest('#webai-hitl-observer-panel')) {
                                        continue;
                                    }
                                    stateChanged = true;
                                    if (observer) observer.disconnect();
                                    break;
                                }
                            });
                            observer.observe(document.body || document.documentElement, {
                                childList: true,
                                subtree: true,
                                attributes: true,
                                characterData: true
                            });
                        } catch (err) {
                            stateChanged = true;
                        }

                        setTimeout(function() {
                            if (observer) observer.disconnect();
                            const urlChanged = window.location.href !== initialUrl;
                            if (stateChanged || urlChanged) {
                                window.__webai_telemetry.push(telemetryEvent);
                                if (window.recordHITLTelemetry) {
                                    try { window.recordHITLTelemetry(telemetryEvent); } catch (_) {}
                                }
                            }
                        }, 800);
                    }
                };
                document.addEventListener('click', window.__webai_click_handler, true);
            }

            // 2. Type Listener (Debounced input & change)
            let inputDebounceTimer = null;
            if (!window.__webai_type_handler) {
                window.__webai_type_handler = function(e) {
                    if (e.target && e.target.closest && e.target.closest('#webai-hitl-observer-panel')) return;
                    const target = e.target;
                    const tag = (target.tagName || '').toLowerCase();
                    if (tag !== 'input' && tag !== 'textarea' && !target.isContentEditable) return;

                    if (inputDebounceTimer) clearTimeout(inputDebounceTimer);
                    inputDebounceTimer = setTimeout(function() {
                        const val = target.value || target.innerText || '';
                        const typeEvent = {
                            action: 'type',
                            tag: tag,
                            name: (target.getAttribute('name') || target.getAttribute('aria-label') || target.placeholder || tag).substring(0, 100),
                            value: val,
                            url: window.location.href,
                            locators: extract13Locators(target),
                            timestamp_ms: Date.now() - window.__webai_observer_start
                        };
                        window.__webai_telemetry.push(typeEvent);
                        if (window.recordHITLTelemetry) {
                            try { window.recordHITLTelemetry(typeEvent); } catch (_) {}
                        }
                    }, 400);
                };
                document.addEventListener('input', window.__webai_type_handler, true);
                document.addEventListener('change', window.__webai_type_handler, true);
            }

            // 3. Drag and Drop Listener (dragstart + drop & mousedown/mouseup > 20px)
            let dragSourceEl = null;
            let mouseDownInfo = null;

            if (!window.__webai_dragstart_handler) {
                window.__webai_dragstart_handler = function(e) {
                    if (e.target && e.target.closest && e.target.closest('#webai-hitl-observer-panel')) return;
                    dragSourceEl = e.target;
                };
                window.__webai_drop_handler = function(e) {
                    if (e.target && e.target.closest && e.target.closest('#webai-hitl-observer-panel')) return;
                    const dropTargetEl = e.target;
                    if (dragSourceEl) {
                        const dragEvent = {
                            action: 'drag_and_drop',
                            name: (dragSourceEl.getAttribute('aria-label') || dragSourceEl.id || dragSourceEl.tagName || 'drag').substring(0, 100),
                            source_locators: extract13Locators(dragSourceEl),
                            target_locators: extract13Locators(dropTargetEl),
                            source_coords: { x: 0, y: 0 },
                            target_coords: { x: e.clientX, y: e.clientY },
                            url: window.location.href,
                            timestamp_ms: Date.now() - window.__webai_observer_start
                        };
                        window.__webai_telemetry.push(dragEvent);
                        if (window.recordHITLTelemetry) {
                            try { window.recordHITLTelemetry(dragEvent); } catch (_) {}
                        }
                        dragSourceEl = null;
                    }
                };
                window.__webai_mousedown_handler = function(e) {
                    if (e.target && e.target.closest && e.target.closest('#webai-hitl-observer-panel')) return;
                    mouseDownInfo = { x: e.clientX, y: e.clientY, target: e.target, time: Date.now() };
                };
                window.__webai_mouseup_handler = function(e) {
                    if (!mouseDownInfo) return;
                    const dx = e.clientX - mouseDownInfo.x;
                    const dy = e.clientY - mouseDownInfo.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist > 20) {
                        const srcEl = mouseDownInfo.target;
                        const tgtEl = e.target;
                        const pointerDragEvent = {
                            action: 'drag_and_drop',
                            name: (srcEl.getAttribute('aria-label') || srcEl.id || srcEl.tagName || 'pointer_drag').substring(0, 100),
                            source_locators: extract13Locators(srcEl),
                            target_locators: extract13Locators(tgtEl),
                            source_coords: { x: mouseDownInfo.x, y: mouseDownInfo.y },
                            target_coords: { x: e.clientX, y: e.clientY },
                            url: window.location.href,
                            timestamp_ms: Date.now() - window.__webai_observer_start
                        };
                        window.__webai_telemetry.push(pointerDragEvent);
                        if (window.recordHITLTelemetry) {
                            try { window.recordHITLTelemetry(pointerDragEvent); } catch (_) {}
                        }
                    }
                    mouseDownInfo = null;
                };
                document.addEventListener('dragstart', window.__webai_dragstart_handler, true);
                document.addEventListener('drop', window.__webai_drop_handler, true);
                document.addEventListener('mousedown', window.__webai_mousedown_handler, true);
                document.addEventListener('mouseup', window.__webai_mouseup_handler, true);
            }

            // 4. Scroll Page Listener (Accumulated wheel delta over 350ms window)
            let wheelTimeout = null;
            let wheelAccumX = 0;
            let wheelAccumY = 0;

            if (!window.__webai_wheel_handler) {
                window.__webai_wheel_handler = function(e) {
                    if (e.target && e.target.closest && e.target.closest('#webai-hitl-observer-panel')) return;
                    wheelAccumX += e.deltaX;
                    wheelAccumY += e.deltaY;

                    if (wheelTimeout) clearTimeout(wheelTimeout);
                    wheelTimeout = setTimeout(function() {
                        const totalX = Math.round(wheelAccumX);
                        const totalY = Math.round(wheelAccumY);
                        wheelAccumX = 0;
                        wheelAccumY = 0;
                        const scrollEvent = {
                            action: 'scroll_page',
                            target: totalY >= 0 ? 'down' : 'up',
                            delta_x: totalX,
                            delta_y: totalY,
                            url: window.location.href,
                            timestamp_ms: Date.now() - window.__webai_observer_start
                        };
                        window.__webai_telemetry.push(scrollEvent);
                        if (window.recordHITLTelemetry) {
                            try { window.recordHITLTelemetry(scrollEvent); } catch (_) {}
                        }
                    }, 350);
                };
                document.addEventListener('wheel', window.__webai_wheel_handler, { capture: true, passive: true });
            }

            // 5. Unload Flush Listener for active inputs
            if (!window.__webai_unload_handler) {
                window.__webai_unload_handler = function() {
                    try {
                        const activeEl = document.activeElement;
                        if (activeEl && !activeEl.closest('#webai-hitl-observer-panel')) {
                            const activeTag = (activeEl.tagName || '').toLowerCase();
                            if (activeTag === 'input' || activeTag === 'textarea' || activeEl.isContentEditable) {
                                const val = activeEl.value || activeEl.innerText || '';
                                if (val && window.recordHITLTelemetry) {
                                    window.recordHITLTelemetry({
                                        action: 'type',
                                        tag: activeTag,
                                        name: (activeEl.getAttribute('name') || activeEl.getAttribute('aria-label') || activeEl.placeholder || activeTag).substring(0, 100),
                                        value: val,
                                        url: window.location.href,
                                        locators: extract13Locators(activeEl),
                                        timestamp_ms: Date.now() - window.__webai_observer_start
                                    });
                                }
                            }
                        }
                    } catch (_) {}
                };
                window.addEventListener('beforeunload', window.__webai_unload_handler, true);
            }
        }"""

        js_remove_code = """() => {
            const panel = document.getElementById('webai-hitl-observer-panel');
            if (panel) { panel.remove(); }
            if (window.__webai_click_handler) {
                document.removeEventListener('click', window.__webai_click_handler, true);
                delete window.__webai_click_handler;
            }
            if (window.__webai_type_handler) {
                document.removeEventListener('input', window.__webai_type_handler, true);
                document.removeEventListener('change', window.__webai_type_handler, true);
                delete window.__webai_type_handler;
            }
            if (window.__webai_dragstart_handler) {
                document.removeEventListener('dragstart', window.__webai_dragstart_handler, true);
                delete window.__webai_dragstart_handler;
            }
            if (window.__webai_drop_handler) {
                document.removeEventListener('drop', window.__webai_drop_handler, true);
                delete window.__webai_drop_handler;
            }
            if (window.__webai_mousedown_handler) {
                document.removeEventListener('mousedown', window.__webai_mousedown_handler, true);
                delete window.__webai_mousedown_handler;
            }
            if (window.__webai_mouseup_handler) {
                document.removeEventListener('mouseup', window.__webai_mouseup_handler, true);
                delete window.__webai_mouseup_handler;
            }
            if (window.__webai_wheel_handler) {
                document.removeEventListener('wheel', window.__webai_wheel_handler, true);
                delete window.__webai_wheel_handler;
            }
            if (window.__webai_unload_handler) {
                window.removeEventListener('beforeunload', window.__webai_unload_handler, true);
                delete window.__webai_unload_handler;
            }
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

        # Attach domcontentloaded listener to re-inject panel on same-tab navigations
        page_dom_listeners = []
        def _attach_dom_listener(p_target: Page):
            if hasattr(p_target, "on"):
                def _on_dom_ready():
                    asyncio.create_task(inject_into_page(p_target))
                try:
                    p_target.on("domcontentloaded", _on_dom_ready)
                    page_dom_listeners.append((p_target, _on_dom_ready))
                except Exception:
                    pass

        # Inject into all existing pages in context
        pages_list = context.pages if context and hasattr(context, "pages") and isinstance(context.pages, (list, tuple)) else [page]
        for p in pages_list:
            _attach_dom_listener(p)
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
                _attach_dom_listener(new_p)
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

        # Heartbeat loop to keep panel injected across same-tab navigations
        async def _heartbeat_loop():
            while not resolution_event.is_set():
                try:
                    all_pages = context.pages if context and hasattr(context, "pages") and isinstance(context.pages, (list, tuple)) else [page]
                    for p in all_pages:
                        if not p.is_closed():
                            p_url = getattr(p, "url", "") or ""
                            if p_url and p_url != "about:blank":
                                has_panel = False
                                try:
                                    has_panel = await p.evaluate("() => Boolean(document.getElementById('webai-hitl-observer-panel'))")
                                except Exception:
                                    pass
                                if not has_panel:
                                    await inject_into_page(p)
                except Exception:
                    pass
                await asyncio.sleep(1.0)

        heartbeat_task = asyncio.create_task(_heartbeat_loop())

        try:
            await asyncio.wait_for(resolution_event.wait(), timeout=timeout_sec)
            target_state = getattr(target_obj, "_webai_hitl_state", {})
            res_dict = (
                target_state.get("payload")
                or self._active_resolved_payload
                or resolved_payload
                or {
                    "status": "resolved",
                    "action": "observer_mode_complete",
                    "x": 0, "y": 0,
                    "targetTag": "RESUME_AI",
                    "targetId": "webai-hitl-resume-btn",
                    "textContent": "Resume AI",
                    "telemetry": [],
                    "timestamp": time.time()
                }
            )
            # Merge Python-side sink telemetry with browser payload telemetry
            py_telemetry = target_state.get("telemetry") or []
            browser_telemetry = res_dict.get("telemetry") or []
            combined_telemetry = list(py_telemetry)
            for b_step in browser_telemetry:
                if not any(
                    c.get("action") == b_step.get("action")
                    and c.get("name") == b_step.get("name")
                    and abs(c.get("timestamp_ms", 0) - b_step.get("timestamp_ms", 0)) < 250
                    for c in combined_telemetry
                ):
                    combined_telemetry.append(b_step)
            combined_telemetry.sort(key=lambda s: s.get("timestamp_ms", 0))
            res_dict["telemetry"] = combined_telemetry
            return res_dict
        except asyncio.TimeoutError:
            print(" [HITLPlugin] Timeout waiting for Resume AI click.")
            return {
                "status": "resolved",
                "action": "observer_mode_complete",
                "x": 0, "y": 0,
                "targetTag": "TIMEOUT", "targetId": "",
                "textContent": "Timeout waiting for Resume AI click",
                "telemetry": [],
                "timestamp": time.time()
            }
        except Exception as e:
            print(f" [HITLPlugin] Failed to inject/await Observer Mode panel: {e}")
            return {
                "status": "resolved",
                "action": "observer_mode_complete",
                "x": 0, "y": 0,
                "targetTag": "ERROR", "targetId": "",
                "textContent": str(e),
                "telemetry": [],
                "timestamp": time.time()
            }
        finally:
            if heartbeat_task and not heartbeat_task.done():
                heartbeat_task.cancel()
            # Safeguard 2: Remove domcontentloaded listeners so panels are never re-injected after Observer Mode finishes
            for p_item, fn in page_dom_listeners:
                try:
                    if hasattr(p_item, "remove_listener"):
                        p_item.remove_listener("domcontentloaded", fn)
                except Exception:
                    pass
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
        """Transcribe PCM WAV audio using active transcriber strategy."""
        try:
            if not os.path.exists(audio_filepath) or os.path.getsize(audio_filepath) == 0:
                return ""
            transcription = ACTIVE_TRANSCRIBER.transcribe_text(audio_filepath)
            return transcription
        except Exception as e:
            print(f" [HITLPlugin] Audio transcription fallback: {e}")
            return "User manually intervened in Observer Mode"

    async def trigger_intervention(self, page: Page, payload: Optional[Dict[str, Any]] = None, timeout_sec: float = 120.0) -> Dict[str, Any]:
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
        click_data = await self._inject_and_await_observer_mode(page, timeout_sec=timeout_sec)

        # Stop audio recording
        is_recording_audio = False
        if audio_recorder_thread and audio_recorder_thread.is_alive():
            audio_recorder_thread.join(timeout=1.0)

        # Step 4: Transcribe voice (segments & full text)
        transcription = ""
        segments = []
        try:
            if os.path.exists(temp_audio_file) and os.path.getsize(temp_audio_file) > 0:
                try:
                    if hasattr(ACTIVE_TRANSCRIBER, "transcribe_segments"):
                        segments = ACTIVE_TRANSCRIBER.transcribe_segments(temp_audio_file)
                except Exception as seg_err:
                    print(f" [HITLPlugin] Segment transcription warning: {seg_err}")
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

        # Extract and align telemetry steps
        raw_telemetry = []
        if isinstance(click_data, dict):
            raw_telemetry = click_data.get("telemetry") or []

        aligned_telemetry = [dict(step) for step in raw_telemetry]
        if segments and aligned_telemetry:
            try:
                from ..audio_aligner import AudioAligner
                aligner = AudioAligner(transcriber=ACTIVE_TRANSCRIBER)
                aligned_telemetry = aligner.align_steps(aligned_telemetry, segments)
            except Exception as align_err:
                print(f" [HITLPlugin] AudioAligner alignment error: {align_err}")

        # Attach vocal context so no instruction is lost
        for step in aligned_telemetry:
            if not step.get("voice_context") and transcription:
                step["voice_context"] = transcription
            step["full_voice_context"] = transcription

        resolution = {
            "status": "resolved",
            "action": "observer_mode_complete",
            "click": click_data,
            "telemetry": aligned_telemetry,
            "audio_transcription": transcription,
            "timestamp": time.time(),
        }

        print(f" [HITLPlugin] INTERVENTION RESOLVED: {resolution}\n")
        return resolution
