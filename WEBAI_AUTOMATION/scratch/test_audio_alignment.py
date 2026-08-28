"""
TDVC Test Harness for AudioAligner Temporal Alignment Logic.
Verifies time window calculation (segment_start_ms - 1000 <= step.timestamp_ms <= segment_end_ms + 2000)
and overlapping segment text concatenation on both Step dataclass instances and dicts.
"""
from __future__ import annotations

import os
import sys

# Ensure import paths for webai_playwright_python modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "webai_playwright_python")))

from webai_playwright.recorder import Step
from webai_playwright.audio_aligner import AudioAligner


def test_audio_alignment_math():
    print(" [1/3] Initializing mock transcript segments and step data...")
    
    mock_segments = [
        {"start_ms": 2000.0, "end_ms": 4000.0, "text": "Click the login button"},
        {"start_ms": 4500.0, "end_ms": 6000.0, "text": "Now type admin username"},
        {"start_ms": 12000.0, "end_ms": 15000.0, "text": "Wait for page load"}
    ]

    mock_steps_dataclass = [
        Step(action="open", url="https://example.com", timestamp_ms=500.0),      # Outside window (< 1000)
        Step(action="click", name="Login", timestamp_ms=2500.0),                  # Matches Segment 1
        Step(action="type", name="Username", timestamp_ms=5000.0),               # Matches Segment 1 & Segment 2
        Step(action="wait", value="3", timestamp_ms=13500.0),                     # Matches Segment 3
        Step(action="verify_text", value="Done", timestamp_ms=20000.0)            # Outside window (> 17000)
    ]

    mock_steps_dict = [
        {"action": "open", "url": "https://example.com", "timestamp_ms": 500.0},
        {"action": "click", "name": "Login", "timestamp_ms": 2500.0},
        {"action": "type", "name": "Username", "timestamp_ms": 5000.0},
        {"action": "wait", "value": "3", "timestamp_ms": 13500.0},
        {"action": "verify_text", "value": "Done", "timestamp_ms": 20000.0}
    ]

    aligner = AudioAligner()

    print(" [2/3] Running alignment logic on Dataclass steps...")
    aligned_dataclasses = aligner.align_steps(mock_steps_dataclass, mock_segments)

    # Dataclass Assertions
    assert aligned_dataclasses[0].voice_context is None, f"Step 0 should be None, got: {aligned_dataclasses[0].voice_context}"
    assert aligned_dataclasses[1].voice_context == "Click the login button", f"Step 1 mismatch: {aligned_dataclasses[1].voice_context}"
    assert aligned_dataclasses[2].voice_context == "Click the login button Now type admin username", f"Step 2 overlapping mismatch: {aligned_dataclasses[2].voice_context}"
    assert aligned_dataclasses[3].voice_context == "Wait for page load", f"Step 3 mismatch: {aligned_dataclasses[3].voice_context}"
    assert aligned_dataclasses[4].voice_context is None, f"Step 4 should be None, got: {aligned_dataclasses[4].voice_context}"

    print(" [3/3] Running alignment logic on Dictionary steps...")
    aligned_dicts = aligner.align_steps(mock_steps_dict, mock_segments)

    # Dictionary Assertions
    assert aligned_dicts[0].get("voice_context") is None, f"Dict Step 0 should be None, got: {aligned_dicts[0].get('voice_context')}"
    assert aligned_dicts[1].get("voice_context") == "Click the login button", f"Dict Step 1 mismatch: {aligned_dicts[1].get('voice_context')}"
    assert aligned_dicts[2].get("voice_context") == "Click the login button Now type admin username", f"Dict Step 2 mismatch: {aligned_dicts[2].get('voice_context')}"
    assert aligned_dicts[3].get("voice_context") == "Wait for page load", f"Dict Step 3 mismatch: {aligned_dicts[3].get('voice_context')}"
    assert aligned_dicts[4].get("voice_context") is None, f"Dict Step 4 should be None, got: {aligned_dicts[4].get('voice_context')}"

    print(" SUCCESS: All AudioAligner temporal window & concatenation assertions PASSED!")


if __name__ == "__main__":
    test_audio_alignment_math()
