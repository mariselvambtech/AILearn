"""
Browser Interaction Recorder utilizing Chrome DevTools Protocol (CDP).

This module intercepts raw user interactions (mouse clicks, keystrokes, scrolling) 
directly from the browser using CDP and synthesizes them into structured JSON 
steps (`recorded_steps.json`). These steps act as the ground-truth automation 
that can later be replayed locally or uploaded to the API Server.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, asdict, field
from typing import Any, Callable, Dict, List, Optional
import json

from playwright.async_api import Page


@dataclass
class Step:
    action: str  # open | navigate | click | type | press_key | verify_text | verify_visible | extract | extract_table | wait
    url: Optional[str] = None
    name: Optional[str] = None     # click name OR confirmed label anchor OR key press context OR extraction variable name
    value: Optional[str] = None    # typed value OR verify text OR extraction sample value
    key: Optional[str] = None      # pressed key (for press_key action) OR extract_type ('text'/'attribute')
    ts: float = 0.0
    locators: Optional[List[Dict[str, str]]] = None  # Multiple locator strategies
    extract_type: Optional[str] = None  # For extract action - 'text' or 'attribute'
    attribute_name: Optional[str] = None  # For extract action with type='attribute'
    save_options: Optional[Dict[str, Any]] = None  # Save configuration for extract action
    table_config: Optional[Dict[str, Any]] = None  # Table extraction configuration
    page_summary: Optional[str] = None  # Crawl4AI LLM page summary
    element_intent: Optional[str] = None  # Semantic action intent
    fingerprint: Optional[Dict[str, Any]] = None  # Structural DOM fingerprint
    timestamp_ms: float = 0.0  # Milliseconds elapsed since recording session start
    voice_context: Optional[str] = None  # Aligned transcript spoken context


RECORDER_INIT_SCRIPT = r"""
(() => {
  let __RECORDER_STOPPED__ = false;
  let verifyVisibleArmed = false;

  const lastSentValue = new WeakMap();
  const suggestedLabel = new WeakMap();
  const labelDecision = new WeakMap();
  const userInteracted = new WeakMap();

  const MAX_CLICK_TEXT = 60;
  const MAX_LABEL_TEXT = 60;

  function isRecorderUi(el) {
    if (!el || !el.closest) return false;
    return Boolean(
      el.closest("#__webai_recorder_modal__") ||
      el.closest("#__webai_recorder_hint__") ||
      el.closest("#__webai_recorder_stopped__") ||
      el.closest("#__webai_recorder_stopbtn__") ||
      el.closest("#__extraction_menu__") ||
      el.closest("#__extraction_input__") ||
      el.closest("[data-webai-dialog='true']")
    );
  }

  function isVisible(el) {
    if (!el) return false;
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return false;
    const style = window.getComputedStyle(el);
    if (style.visibility === "hidden" || style.display === "none" || style.opacity === "0") return false;
    return true;
  }

  function cleanText(s) {
    return (s || "").replace(/\s+/g, " ").trim();
  }

  function truncate(s, n) {
    s = cleanText(s);
    if (!s) return "";
    return s.length <= n ? s : s.slice(0, n) + "…";
  }

  function getClickableTarget(el) {
    if (!el) return null;
    const target = el.closest?.("a,button,[role='button'],input[type='submit'],input[type='button'],[onclick],[class*='btn'],[class*='close'],[class*='modal'],[class*='card']");
    return target || el;
  }

  function bestStableName(el, maxLen) {
    if (!el) return null;

    const aria = el.getAttribute && el.getAttribute("aria-label");
    if (aria && cleanText(aria)) return truncate(aria, maxLen);

    const title = el.getAttribute && el.getAttribute("title");
    if (title && cleanText(title)) return truncate(title, maxLen);

    if (el.id) {
      const lbl = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (lbl && isVisible(lbl)) {
        const t = cleanText(lbl.innerText);
        if (t) return truncate(t, maxLen);
      }
    }

    const ph = el.getAttribute && el.getAttribute("placeholder");
    if (ph && cleanText(ph)) return truncate(ph, maxLen);

    const txt = cleanText(el.innerText || el.textContent || "");
    if (txt) {
      if (txt === "×" || txt === "x" || txt === "X") return "Close";
      return truncate(txt, maxLen);
    }

    const cls = (el.className && typeof el.className === "string") ? el.className.toLowerCase() : "";
    if (cls.includes("close") || cls.includes("modal-close") || cls.includes("btn-close")) {
      return "Close";
    }

    const nm = el.getAttribute && el.getAttribute("name");
    if (nm && cleanText(nm)) return truncate(nm, maxLen);
    
    const alt = el.getAttribute && el.getAttribute("alt");
    if (alt && cleanText(alt)) return truncate(alt, maxLen);

    const tag = el.tagName ? el.tagName.toLowerCase() : "";
    const type = el.getAttribute && el.getAttribute("type");
    const role = el.getAttribute && el.getAttribute("role");
    
    if (tag === "button" || role === "button" || type === "submit") {
      const parent = el.closest("form") || el.parentElement;
      if (parent) {
        const searchInput = parent.querySelector("input[type='search']") || 
                          parent.querySelector("input[placeholder*='search' i]") ||
                          parent.querySelector("input[placeholder*='Search' i]") ||
                          parent.querySelector("input[aria-label*='search' i]") ||
                          parent.querySelector("input[aria-label*='Search' i]");
        if (searchInput) {
          return "Search";
        }
      }
      return "Button";
    }
    
    if (tag === "a") {
      return "Link";
    }

    return null;
  }

  // ============================================================================
  // Multi-Locator Strategy System (13-Strategy Hierarchy)
  // ============================================================================

  function getImplicitRole(el) {
    if (!el || !el.tagName) return null;
    const tag = el.tagName.toLowerCase();
    const type = el.getAttribute && el.getAttribute('type');
    
    const roleMap = {
      'button': 'button',
      'a': 'link',
      'img': 'img',
      'input': type === 'text' ? 'textbox' : type === 'submit' ? 'button' : 'textbox',
      'textarea': 'textbox',
      'select': 'combobox',
      'nav': 'navigation',
      'header': 'banner',
      'footer': 'contentinfo',
      'main': 'main',
      'h1': 'heading',
      'h2': 'heading',
      'h3': 'heading',
      'h4': 'heading',
      'h5': 'heading',
      'h6': 'heading',
    };
    
    return roleMap[tag] || null;
  }

  function generateStableCSS(el) {
    if (!el || !el.tagName) return null;
    
    const parts = [];
    const tag = el.tagName.toLowerCase();
    parts.push(tag);
    
    if (el.id) {
      return `#${CSS.escape(el.id)}`;
    }
    
    const dynamicClassPatterns = /active|selected|hover|focus|disabled|loading|open|closed|visible|hidden/i;
    const classes = Array.from(el.classList || [])
      .filter(c => !dynamicClassPatterns.test(c))
      .slice(0, 2);
    
    if (classes.length > 0) {
      parts[0] += '.' + classes.map(c => CSS.escape(c)).join('.');
    }
    
    const stableAttrs = ['type', 'name', 'data-testid'];
    for (const attr of stableAttrs) {
      const val = el.getAttribute(attr);
      if (val) {
        parts[0] += `[${attr}="${CSS.escape(val)}"]`;
        break;
      }
    }
    
    const selector = parts.join('');
    
    try {
      const matches = document.querySelectorAll(selector);
      if (matches.length === 1) {
        return selector;
      }
      
      let index = 1;
      let sibling = el.previousElementSibling;
      while (sibling) {
        if (sibling.tagName === el.tagName) index++;
        sibling = sibling.previousElementSibling;
      }
      
      return `${selector}:nth-child(${index})`;
    } catch (e) {
      return selector;
    }
  }

  function generateXPath(el) {
    if (!el || el.nodeType !== 1) return null;
    
    if (el.id) {
      return `//*[@id="${el.id}"]`;
    }
    
    const parts = [];
    let current = el;
    let depth = 0;
    
    while (current && current.nodeType === Node.ELEMENT_NODE && current.tagName !== 'BODY') {
      const tag = current.nodeName.toLowerCase();
      
      let index = 1;
      let sibling = current.previousSibling;
      while (sibling) {
        if (sibling.nodeType === Node.ELEMENT_NODE && sibling.nodeName === current.nodeName) {
          index++;
        }
        sibling = sibling.previousSibling;
      }
      
      const totalSiblings = Array.from(current.parentNode?.children || [])
        .filter(s => s.nodeName === current.nodeName).length;
      
      const part = totalSiblings > 1 ? `${tag}[${index}]` : tag;
      parts.unshift(part);
      
      current = current.parentElement;
      depth++;
      
      if (depth >= 5) break;
    }
    
    return '//' + parts.join('/');
  }

  function getLocatorCandidates(el) {
    if (!el) return [];
    
    const candidates = [];
    
    // 1. Test ID
    const testId = el.getAttribute && (
      el.getAttribute('data-testid') ||
      el.getAttribute('data-test-id') ||
      el.getAttribute('data-test')
    );
    if (testId) {
      candidates.push({type: 'test-id', value: testId});
    }
    
    // 2. ID
    const isDynamicId = /^[0-9]/.test(el.id) || /^modal-[A-Za-z0-9]{4,}$/.test(el.id) || /^:[a-zA-Z0-9_-]+:$/.test(el.id) || /ember\d+/i.test(el.id) || /^id-\d+/i.test(el.id);
    if (el.id && !isDynamicId) {
      candidates.push({type: 'id', value: el.id});
    }
    
    // 3. Name attribute
    const name = el.getAttribute && el.getAttribute('name');
    if (name) {
      candidates.push({type: 'name', value: name});
    }
    
    // 4. Aria-label
    const ariaLabel = el.getAttribute && el.getAttribute('aria-label');
    if (ariaLabel && cleanText(ariaLabel)) {
      candidates.push({type: 'aria-label', value: cleanText(ariaLabel)});
    }
    
    // 5. Placeholder
    const placeholder = el.getAttribute && el.getAttribute('placeholder');
    if (placeholder && cleanText(placeholder)) {
      candidates.push({type: 'placeholder', value: cleanText(placeholder)});
    }
    
    // 5a. Title attribute
    const title = el.getAttribute && el.getAttribute('title');
    if (title && cleanText(title)) {
      candidates.push({type: 'title', value: cleanText(title)});
    }
    
    // 5b. Alt attribute
    const alt = el.getAttribute && el.getAttribute('alt');
    if (alt && cleanText(alt)) {
      candidates.push({type: 'alt', value: cleanText(alt)});
    }
    
    // 5c. Href attribute
    if (el.tagName && el.tagName.toLowerCase() === 'a') {
      const href = el.getAttribute && el.getAttribute('href');
      if (href && href.trim() && !href.startsWith('javascript:')) {
        candidates.push({type: 'href', value: href.trim()});
      }
    }
    
    // 6. Label
    if (el.id) {
      const label = document.querySelector(`label[for="${CSS.escape(el.id)}"]`);
      if (label) {
        const labelText = cleanText(label.innerText);
        if (labelText) {
          candidates.push({type: 'label', value: labelText});
        }
      }
    }
    
    // 7. CSS Selector
    const css = generateStableCSS(el);
    if (css) {
      candidates.push({type: 'css', value: css});
    }
    
    // 8. Text content
    const text = cleanText(el.innerText || el.textContent || '');
    if (text && text.length < 50) {
      candidates.push({type: 'text', value: text});
    }
    
    // 9. Role + Name
    const explicitRole = el.getAttribute && el.getAttribute('role');
    const role = explicitRole || getImplicitRole(el);
    if (role) {
      candidates.push({
        type: 'role',
        value: role,
        name: text || ariaLabel || null
      });
    }
    
    // 10. XPath
    const xpath = generateXPath(el);
    if (xpath) {
      candidates.push({type: 'xpath', value: xpath});
    }
    
    return candidates;
  }

  function send(kind, payload) {
    if (__RECORDER_STOPPED__) return;
    try { if (window.__recordEvent) window.__recordEvent({ kind, ...payload }); } catch {}
  }

  window.__recordSend = send;
  window.getLocatorCandidates = getLocatorCandidates;
  window.generateStableCSS = generateStableCSS;
  window.showHint = showHint;

  function showHint(msg, id="__webai_recorder_hint__") {
    const old = document.getElementById(id);
    if (old) old.remove();
    const d = document.createElement("div");
    d.id = id;
    d.textContent = msg;
    d.style.position = "fixed";
    d.style.bottom = "15px";
    d.style.left = "15px";
    d.style.background = "rgba(0,0,0,0.85)";
    d.style.color = "white";
    d.style.padding = "8px 12px";
    d.style.borderRadius = "8px";
    d.style.zIndex = "2147483647";
    d.style.fontFamily = "Arial, sans-serif";
    document.body.appendChild(d);
    setTimeout(() => d.remove(), 2500);
  }

  function showPrompt(title, placeholder) {
    return new Promise((resolve) => {
      const old = document.getElementById("__webai_recorder_modal__");
      if (old) old.remove();

      const wrap = document.createElement("div");
      wrap.id = "__webai_recorder_modal__";
      wrap.style.position = "fixed";
      wrap.style.inset = "0";
      wrap.style.background = "rgba(0,0,0,0.45)";
      wrap.style.zIndex = "2147483647";
      wrap.style.display = "flex";
      wrap.style.alignItems = "center";
      wrap.style.justifyContent = "center";

      const box = document.createElement("div");
      box.style.background = "white";
      box.style.padding = "16px";
      box.style.borderRadius = "10px";
      box.style.width = "540px";
      box.style.maxWidth = "92vw";
      box.style.fontFamily = "Arial, sans-serif";
      box.style.boxShadow = "0 10px 30px rgba(0,0,0,0.35)";

      const h = document.createElement("div");
      h.textContent = title;
      h.style.fontWeight = "700";
      h.style.marginBottom = "8px";

      const input = document.createElement("input");
      input.placeholder = placeholder || "";
      input.style.width = "100%";
      input.style.padding = "10px";
      input.style.border = "1px solid #ccc";
      input.style.borderRadius = "8px";
      input.style.outline = "none";

      const row = document.createElement("div");
      row.style.display = "flex";
      row.style.justifyContent = "flex-end";
      row.style.gap = "10px";
      row.style.marginTop = "12px";

      const cancel = document.createElement("button");
      cancel.textContent = "Cancel";
      cancel.style.padding = "8px 12px";
      cancel.style.borderRadius = "8px";
      cancel.style.border = "1px solid #ccc";
      cancel.style.background = "#f7f7f7";
      cancel.style.cursor = "pointer";

      const ok = document.createElement("button");
      ok.textContent = "OK";
      ok.style.padding = "8px 12px";
      ok.style.borderRadius = "8px";
      ok.style.border = "1px solid #0a66ff";
      ok.style.background = "#0a66ff";
      ok.style.color = "white";
      ok.style.cursor = "pointer";

      function cleanup(val) { wrap.remove(); resolve(val); }

      cancel.onclick = () => cleanup(null);
      ok.onclick = () => cleanup(cleanText(input.value) || null);

      wrap.addEventListener("keydown", (e) => {
        if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); cleanup(null); }
        if (e.key === "Enter")  { e.preventDefault(); e.stopPropagation(); cleanup(cleanText(input.value) || null); }
      }, true);

      row.appendChild(cancel);
      row.appendChild(ok);

      box.appendChild(h);
      box.appendChild(input);
      box.appendChild(row);

      wrap.appendChild(box);
      document.body.appendChild(wrap);
      setTimeout(() => input.focus(), 0);
    });
  }

  function findNearbyLabel(inputEl) {
    if (!inputEl) return null;

    const direct = bestStableName(inputEl, MAX_LABEL_TEXT);
    if (direct) return direct;

    const r = inputEl.getBoundingClientRect();
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;

    const candidates = Array.from(document.querySelectorAll("label, span, div, p, strong, b, small"));

    let best = null;
    let bestScore = 1e9;

    for (const el of candidates) {
      if (!el || el === inputEl) continue;
      if (!isVisible(el)) continue;
      if (isRecorderUi(el)) continue;

      const t = cleanText(el.innerText || "");
      if (!t) continue;
      if (t.length < 2 || t.length > 40) continue;

      const rr = el.getBoundingClientRect();
      const ex = rr.left + rr.width / 2;
      const ey = rr.top + rr.height / 2;

      const dx = ex - cx;
      const dy = ey - cy;
      const dist = Math.sqrt(dx*dx + dy*dy);

      if (dist > 220) continue;

      let penalty = 0;
      if (ey > cy + 10) penalty += 50;
      if (ex > cx + 10) penalty += 30;

      const score = dist + penalty;
      if (score < bestScore) {
        bestScore = score;
        best = t;
      }
    }
    return best ? truncate(best, MAX_LABEL_TEXT) : null;
  }

  async function finalizeTypeFor(el) {
    if (__RECORDER_STOPPED__) return;
    if (!el || isRecorderUi(el)) return;
    if (!("value" in el)) return;

    const value = cleanText(String(el.value ?? ""));
    if (!value) return;

    const last = lastSentValue.get(el);
    if (value === last) return;
    
    const hasInteraction = userInteracted.has(el);
    if (!hasInteraction) return;

    lastSentValue.set(el, value);

    let label = labelDecision.get(el);
    if (label === undefined) {
      const suggested = suggestedLabel.get(el);
      label = suggested || "(unknown)";
      labelDecision.set(el, label);
    }

    const locators = getLocatorCandidates(el);

    send("type_final", { 
      url: location.href, 
      value, 
      label,
      locators
    });
  }

  document.addEventListener("focusin", (e) => {
    const el = e.target;
    if (!el || isRecorderUi(el)) return;
    const tag = (el.tagName || "").toLowerCase();
    if (!(tag === "input" || tag === "textarea")) return;
    if (!suggestedLabel.has(el)) {
      suggestedLabel.set(el, findNearbyLabel(el));
    }
  }, true);

  document.addEventListener("input", (e) => {
    const el = e.target;
    if (!el || isRecorderUi(el)) return;
    const tag = (el.tagName || "").toLowerCase();
    if (!(tag === "input" || tag === "textarea")) return;
    userInteracted.set(el, true);
  }, true);

  document.addEventListener("focusout", (e) => {
    const el = e.target;
    if (!el || isRecorderUi(el)) return;
    const tag = (el.tagName || "").toLowerCase();
    if (!(tag === "input" || tag === "textarea")) return;
    finalizeTypeFor(el);
  }, true);

  document.addEventListener("keydown", (e) => {
    if (__RECORDER_STOPPED__) return;
    
    const el = e.target;
    if (!el || isRecorderUi(el)) return;
    
    if (e.key === "Tab" || e.key === "Enter") {
      const tag = (el.tagName || "").toLowerCase();
      if (tag === "input" || tag === "textarea") finalizeTypeFor(el);
    }
    
    const RECORDABLE_KEYS = ["Enter", "Escape", "Tab", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"];
    if (RECORDABLE_KEYS.includes(e.key)) {
      const context = bestStableName(el, MAX_LABEL_TEXT) || null;
      send("press_key", {
        url: window.location.href,
        key: e.key,
        name: context,
        value: null
      });
    }
  }, true);

  document.addEventListener("click", (e) => {
    if (__RECORDER_STOPPED__) return;

    const raw = e.target;
    if (!raw || isRecorderUi(raw)) return;

    if (verifyVisibleArmed) {
      const t = cleanText(raw.innerText || "");
      if (t) {
        try { window.__recordVerifyVisible({ url: location.href, text: truncate(t, MAX_CLICK_TEXT) }); } catch {}
      }
      verifyVisibleArmed = false;
      return;
    }

    const clickable = getClickableTarget(raw);
    if (!clickable) return;

    const name = bestStableName(clickable, MAX_CLICK_TEXT);
    if (!name) return;

    if (cleanText(name).length > MAX_CLICK_TEXT) return;

    const locators = getLocatorCandidates(clickable);

    send("click", { 
      url: location.href, 
      name,
      locators
    });
  }, true);

  async function stopNow() {
    if (__RECORDER_STOPPED__) return;
    const active = document.activeElement;
    if (active && active.tagName) {
      const t = active.tagName.toLowerCase();
      if (t === "input" || t === "textarea") await finalizeTypeFor(active);
    }
    __RECORDER_STOPPED__ = true;
    showHint("Recorder: Stopping…", "__webai_recorder_stopped__");
    try { if (window.__stopRecording) await window.__stopRecording(); } catch {}
  }

  function ensureStopButton() {
    if (document.getElementById("__webai_recorder_stopbtn__")) return;
    const btn = document.createElement("button");
    btn.id = "__webai_recorder_stopbtn__";
    btn.textContent = "Stop Recording";
    btn.style.position = "fixed";
    btn.style.right = "16px";
    btn.style.bottom = "16px";
    btn.style.zIndex = "2147483647";
    btn.style.padding = "10px 12px";
    btn.style.borderRadius = "10px";
    btn.style.border = "1px solid #c00";
    btn.style.background = "#fff";
    btn.style.color = "#c00";
    btn.style.fontFamily = "Arial, sans-serif";
    btn.style.cursor = "pointer";
    btn.onclick = () => stopNow();
    document.body.appendChild(btn);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ensureStopButton, { once: true });
  } else {
    ensureStopButton();
  }

  document.addEventListener("keydown", async (e) => {
    if (__RECORDER_STOPPED__) return;

    const stopCombo = (e.ctrlKey && e.shiftKey && e.code === "KeyS") ||
                      (e.ctrlKey && e.altKey && e.code === "KeyS") ||
                      (e.code === "Escape");
    if (stopCombo) {
      e.preventDefault();
      e.stopPropagation();
      await stopNow();
      return;
    }

    if (e.ctrlKey && e.shiftKey && e.code === "KeyV") {
      e.preventDefault();
      e.stopPropagation();
      const t = await showPrompt("Verify page contains text", "Example: Get in touch");
      if (t) {
        try { window.__recordVerifyText({ url: location.href, text: t }); } catch {}
      }
      return;
    }

    if (e.ctrlKey && e.shiftKey && e.code === "KeyE") {
      e.preventDefault();
      e.stopPropagation();
      verifyVisibleArmed = true;
      showHint("Recorder: Click element to verify visible");
      return;
    }

    if (e.ctrlKey && e.shiftKey && e.code === "KeyW") {
      e.preventDefault();
      e.stopPropagation();
      if (typeof window.__addDelay === "function") {
        window.__addDelay();
      }
      return;
    }
  }, true);
})();
"""


class WebRecorder:
    """
    Event Bus Core Engine for Browser Recording.
    Intercepts raw CDP user interactions and broadcasts recorded steps to registered plugins.
    """

    def __init__(self) -> None:
        self.steps: List[Step] = []
        self._stop_event = asyncio.Event()
        self._last_url: Optional[str] = None
        self._opened_once = False
        self._attached_pages = set()
        self._subscribers: Dict[str, List[Callable[[str, Optional[Step], Dict[str, Any]], None]]] = {}
        self._plugin_scripts: List[str] = []
        self.plugins: List[Any] = []
        self.master_start_epoch: float = time.time()
        self._is_recording = False

        # Register default DataExtractionPlugin for backward compatibility
        from .plugins.data_extraction_plugin import DataExtractionPlugin, EXTRACTION_INIT_SCRIPT
        self.register_plugin(DataExtractionPlugin(), init_script=EXTRACTION_INIT_SCRIPT)

        # Register default AudioCapturePlugin safely
        try:
            from .plugins.audio_plugin import AudioCapturePlugin
            self.register_plugin(AudioCapturePlugin())
        except Exception as e:
            print(f" [WARN] [WebRecorder] AudioCapturePlugin auto-attachment skipped: {e}")

        # Register default HITLPlugin safely
        try:
            from .plugins.hitl_plugin import HITLPlugin
            self.register_plugin(HITLPlugin())
        except Exception as e:
            print(f" [WARN] [WebRecorder] HITLPlugin auto-attachment skipped: {e}")

    def start_recording(self) -> None:
        """Start recording session and broadcast recording_started event to plugins."""
        self.master_start_epoch = time.time()
        self._is_recording = True
        self.emit("recording_started", None, {"timestamp": self.master_start_epoch})

    def _calc_ts_ms(self, now: Optional[float] = None) -> float:
        t = now if now is not None else time.time()
        return (t - self.master_start_epoch) * 1000.0

    def register_plugin(self, plugin: Any, init_script: Optional[str] = None) -> None:
        """Register and attach a plugin to this recorder event bus."""
        for i, existing in enumerate(self.plugins):
            if type(existing) is type(plugin):
                self.plugins[i] = plugin
                if hasattr(plugin, "attach"):
                    plugin.attach(self)
                return
        self.plugins.append(plugin)
        if hasattr(plugin, "attach"):
            plugin.attach(self)
        if init_script and init_script not in self._plugin_scripts:
            self._plugin_scripts.append(init_script)

    def subscribe(self, event_name: str, handler: Callable[[str, Optional[Step], Dict[str, Any]], None]) -> None:
        """Subscribe a listener callback to a specific event or '*' for all events."""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        if handler not in self._subscribers[event_name]:
            self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Callable[[str, Optional[Step], Dict[str, Any]], None]) -> None:
        """Unsubscribe a listener callback."""
        if event_name in self._subscribers and handler in self._subscribers[event_name]:
            self._subscribers[event_name].remove(handler)

    def emit(self, event_name: str, step: Optional[Step], payload: Dict[str, Any]) -> None:
        """Broadcast recorded step to all registered subscribers."""
        handlers = self._subscribers.get(event_name, []) + self._subscribers.get("*", [])
        for handler in handlers:
            try:
                handler(event_name, step, payload)
            except Exception as e:
                print(f" [EventBus] Error in subscriber for '{event_name}': {e}")

    async def attach_context(self, context) -> None:
        """
        Attaches the recorder to the BrowserContext and all current / newly opened tabs automatically.
        """
        if not self._is_recording:
            self.start_recording()
        try:
            await context.add_init_script(RECORDER_INIT_SCRIPT)
            for script in self._plugin_scripts:
                await context.add_init_script(script)
        except Exception:
            pass

        for p in context.pages:
            if p not in self._attached_pages:
                self._attached_pages.add(p)
                await self.attach(p)

        async def _on_new_page(new_page: Page):
            if new_page not in self._attached_pages:
                self._attached_pages.add(new_page)
                try:
                    await new_page.wait_for_load_state("domcontentloaded", timeout=3000)
                except Exception:
                    pass
                await self.attach(new_page)

        context.on("page", lambda p: asyncio.create_task(_on_new_page(p)))

    async def attach(self, page: Page) -> None:
        async def on_event(source, payload: Dict[str, Any]) -> None:
            kind = payload.get("kind")
            url = payload.get("url")

            if url and url != self._last_url:
                self._last_url = url
                action = "open" if not self._opened_once else "navigate"
                self._opened_once = True
                now = time.time()
                nav_step = Step(action=action, url=url, ts=now, timestamp_ms=self._calc_ts_ms(now))
                self.steps.append(nav_step)
                self.emit(action, nav_step, payload)

            if kind == "click":
                name = payload.get("name")
                locators = payload.get("locators")
                if name:
                    if self.steps and self.steps[-1].action == "click" and self.steps[-1].url == url and self.steps[-1].name == name:
                        return
                    now = time.time()
                    step = Step(action="click", url=url, name=name, locators=locators, ts=now, timestamp_ms=self._calc_ts_ms(now))
                    self.steps.append(step)
                    self.emit("click", step, payload)

            elif kind == "type_final":
                label = payload.get("label")
                value = payload.get("value")
                locators = payload.get("locators")
                now = time.time()
                if self.steps and self.steps[-1].action == "type" and self.steps[-1].url == url and self.steps[-1].name == label:
                    self.steps[-1].value = value
                    self.steps[-1].locators = locators
                    self.steps[-1].ts = now
                    self.steps[-1].timestamp_ms = self._calc_ts_ms(now)
                    self.emit("type", self.steps[-1], payload)
                    return
                step = Step(action="type", url=url, name=label, value=value, locators=locators, ts=now, timestamp_ms=self._calc_ts_ms(now))
                self.steps.append(step)
                self.emit("type", step, payload)

            elif kind == "press_key":
                key = payload.get("key")
                name = payload.get("name")
                now = time.time()
                step = Step(action="press_key", url=url, key=key, name=name, ts=now, timestamp_ms=self._calc_ts_ms(now))
                self.steps.append(step)
                self.emit("press_key", step, payload)

            elif kind == "extract":
                key = payload.get("key")
                extract_type = payload.get("extract_type")
                locators = payload.get("locators")
                sample_value = payload.get("sample_value")
                attribute_name = payload.get("attribute_name")
                save_options = payload.get("save_options")
                now = time.time()
                
                step = Step(
                    action="extract",
                    url=url,
                    name=key,
                    value=sample_value,
                    locators=locators,
                    extract_type=extract_type,
                    attribute_name=attribute_name,
                    save_options=save_options,
                    ts=now,
                    timestamp_ms=self._calc_ts_ms(now)
                )
                
                self.steps.append(step)
                print(f" Recorded extraction: {key} = '{sample_value[:50] if sample_value else 'N/A'}'")
                self.emit("extract", step, payload)

            elif kind == "extract_table":
                key = payload.get("key")
                locators = payload.get("locators")
                table_config = payload.get("table_config")
                save_options = payload.get("save_options")
                now = time.time()
                
                step = Step(
                    action="extract_table",
                    url=url,
                    name=key,
                    locators=locators,
                    table_config=table_config,
                    save_options=save_options,
                    ts=now,
                    timestamp_ms=self._calc_ts_ms(now)
                )
                
                self.steps.append(step)
                cols_count = len(table_config.get('columns', [])) if table_config else 0
                print(f" Recorded table extraction: {key} ({cols_count} columns)")
                self.emit("extract_table", step, payload)

            elif kind == "wait":
                seconds = payload.get("value")
                name = payload.get("name")
                
                try:
                    wait_time = float(seconds)
                    if wait_time < 1 or wait_time > 60:
                        print(f" Invalid wait time: {wait_time}s (must be 1-60)")
                        return
                    now = time.time()
                    step = Step(
                        action="wait",
                        url=url,
                        name=name,
                        value=str(wait_time),
                        ts=now,
                        timestamp_ms=self._calc_ts_ms(now)
                    )
                    
                    self.steps.append(step)
                    print(f" Recorded delay: {wait_time}s")
                    self.emit("wait", step, payload)
                except (ValueError, TypeError):
                    print(f" Invalid wait value: {seconds}")

        async def stop(source, payload=None) -> None:
            self._stop_event.set()

        async def verify_text(source, payload: Dict[str, Any]) -> None:
            now = time.time()
            step = Step(action="verify_text", url=payload.get("url"), value=payload.get("text"), ts=now, timestamp_ms=self._calc_ts_ms(now))
            self.steps.append(step)
            self.emit("verify_text", step, payload)

        async def verify_visible(source, payload: Dict[str, Any]) -> None:
            now = time.time()
            step = Step(action="verify_visible", url=payload.get("url"), value=payload.get("text"), ts=now, timestamp_ms=self._calc_ts_ms(now))
            self.steps.append(step)
            self.emit("verify_visible", step, payload)

        try:
            await page.expose_binding("__recordEvent", on_event)
            await page.expose_binding("__stopRecording", stop)
            await page.expose_binding("__recordVerifyText", verify_text)
            await page.expose_binding("__recordVerifyVisible", verify_visible)
        except Exception:
            pass

        try:
            await page.add_init_script(RECORDER_INIT_SCRIPT)
            for script in self._plugin_scripts:
                await page.add_init_script(script)
        except Exception:
            pass

        try:
            await page.evaluate(RECORDER_INIT_SCRIPT)
            for script in self._plugin_scripts:
                await page.evaluate(script)
        except Exception:
            pass

    async def wait_for_stop(self) -> None:
        await self._stop_event.wait()
        self.emit("recording_stopped", None, {"timestamp": time.time()})

    def to_json(self) -> List[Dict[str, Any]]:
        return [asdict(s) for s in self.steps]

    def to_task_text(self) -> str:
        lines: List[str] = []
        for s in self.steps:
            if s.action == "open" and s.url:
                lines.append(f"Open {s.url}")
            elif s.action == "navigate" and s.url:
                lines.append(f"Navigate to {s.url}")
            elif s.action == "click" and s.name:
                lines.append(f'Click "{s.name}"')
            elif s.action == "type":
                if s.name:
                    lines.append(f'Type "{s.value}" into "{s.name}"')
                else:
                    lines.append(f'Type "{s.value}"')
            elif s.action == "press_key":
                key = s.key or "Enter"
                context = s.name
                if context:
                    lines.append(f'Press {key} in "{context}"')
                else:
                    lines.append(f'Press {key}')
            elif s.action == "verify_text":
                lines.append(f'Verify the page contains text "{s.value}"')
            elif s.action == "verify_visible":
                lines.append(f'Verify element "{s.value}" is visible')
            elif s.action == "extract":
                element_context = ""
                if s.locators:
                    for loc in s.locators:
                        if loc.get("type") == "text" and loc.get("value"):
                            element_context = f" from '{loc['value']}' element"
                            break
                        elif loc.get("type") == "aria-label" and loc.get("value"):
                            element_context = f" from '{loc['value']}' element"
                            break
                        elif loc.get("type") == "role" and loc.get("name"):
                            element_context = f" from '{loc['name']}' {loc['value']}"
                            break
                
                if s.extract_type == "attribute" and s.attribute_name:
                    lines.append(f'Extract attribute "{s.attribute_name}"{element_context} into variable "{s.name}"')
                else:
                    lines.append(f'Extract text{element_context} into variable "{s.name}"')
            elif s.action == "wait":
                seconds = s.value
                if s.name:
                    lines.append(f'Wait {seconds} seconds ({s.name})')
                else:
                    lines.append(f'Wait {seconds} seconds')

        lines.append("Finish with done only after verification.")

        seen = set()
        out = []
        for ln in lines:
            if ln not in seen:
                seen.add(ln)
                out.append(ln)
        return "\n".join(out)
