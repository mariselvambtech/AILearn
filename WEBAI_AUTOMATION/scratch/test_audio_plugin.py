"""
TDVC Test Harness for AudioCapturePlugin & WebRecorder Synchronization.
Verifies audio recording thread lifecycle, WAV file output (>1000 bytes), and Step timestamp_ms calculation.
"""
from __future__ import annotations

import os
import sys
import time
import shutil

# Ensure import paths for webai_playwright_python modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python")))

from webai_playwright.recorder import WebRecorder, Step
from webai_playwright.plugins.audio_plugin import AudioCapturePlugin


def test_audio_plugin_synchronization():
    test_audio_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "session_audio.wav"))
    
    # Cleanup previous test artifact if present
    if os.path.exists(test_audio_path):
        os.remove(test_audio_path)

    print(" [1/4] Initializing WebRecorder and AudioCapturePlugin...")
    recorder = WebRecorder()
    audio_plugin = AudioCapturePlugin(output_file=test_audio_path, samplerate=16000, channels=1)
    recorder.register_plugin(audio_plugin)
    recorder.start_recording()

    print(" [2/4] Simulating 1.5-second recording session with action steps...")
    
    # Simulate first action step ~200ms after start
    time.sleep(0.2)
    step1 = Step(action="open", url="https://example.com", ts=time.time(), timestamp_ms=recorder._calc_ts_ms())
    recorder.steps.append(step1)
    recorder.emit("open", step1, {"url": "https://example.com"})

    # Simulate second action step ~600ms after start
    time.sleep(0.4)
    step2 = Step(action="click", name="Submit Button", ts=time.time(), timestamp_ms=recorder._calc_ts_ms())
    recorder.steps.append(step2)
    recorder.emit("click", step2, {"name": "Submit Button"})

    # Wait remaining time to reach ~1.5s total recording time
    time.sleep(0.9)

    print(" [3/4] Triggering session stop event...")
    recorder.emit("recording_stopped", None, {"timestamp": time.time()})
    
    # Give background audio thread time to join and close soundfile
    if audio_plugin._thread and audio_plugin._thread.is_alive():
        audio_plugin._thread.join(timeout=3.0)

    print(" [4/4] Running assertions...")
    
    # Assertion 1: File existence
    assert os.path.exists(test_audio_path), f"Audio file was not created at {test_audio_path}"
    file_size = os.path.getsize(test_audio_path)
    print(f"   Audio file size: {file_size} bytes")

    # Assertion 2: File size > 1000 bytes (proving actual audio frames captured)
    assert file_size > 1000, f"Audio file size ({file_size} bytes) is <= 1000 bytes"

    # Assertion 3: Step timestamp_ms verification
    assert step1.timestamp_ms > 0, f"Step 1 timestamp_ms invalid: {step1.timestamp_ms}"
    assert step2.timestamp_ms > step1.timestamp_ms, f"Step 2 timestamp_ms ({step2.timestamp_ms}) not > Step 1 ({step1.timestamp_ms})"
    assert 150 <= step1.timestamp_ms <= 400, f"Step 1 timestamp_ms ({step1.timestamp_ms}) out of expected ~200ms range"
    assert 500 <= step2.timestamp_ms <= 850, f"Step 2 timestamp_ms ({step2.timestamp_ms}) out of expected ~600ms range"

    print(" SUCCESS: All AudioCapturePlugin & WebRecorder assertions PASSED!")


if __name__ == "__main__":
    test_audio_plugin_synchronization()
