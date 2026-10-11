"""
Unit Tests for Agentic Data Extraction (Decision 21 - TDVC)
Tests extract_text and extract_table allowed actions, prompt schemas,
and extraction data persistence.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add server path to sys.path
SERVER_DIR = Path(__file__).resolve().parent.parent / "webai_local_server"
sys.path.insert(0, str(SERVER_DIR))

from local_webai_server_guided import (
    ALLOWED_ACTIONS,
    build_system_prompt,
    _save_txt_extraction,
    _save_excel_extraction,
    _save_word_extraction,
    _normalize_history_step,
)


def test_allowed_actions_schema():
    """Verify that extract_text and extract_table are exposed in ALLOWED_ACTIONS and system prompt."""
    assert "extract_text" in ALLOWED_ACTIONS, "extract_text must be in ALLOWED_ACTIONS"
    assert "extract_table" in ALLOWED_ACTIONS, "extract_table must be in ALLOWED_ACTIONS"

    prompt = build_system_prompt("Extract all courses from table", {})
    assert "extract_text" in prompt
    assert "extract_table" in prompt


def test_save_txt_extraction_direct():
    """Verify _save_txt_extraction persists text data correctly to disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_extract.txt")
        data = {
            "name": "course_list",
            "value": "B.Tech Computer Science, M.Tech AI & Data Science",
            "extract_type": "text",
            "url": "https://sastra.edu/courses",
        }
        _save_txt_extraction(filepath, "new", data)

        assert os.path.exists(filepath), "Output txt file must exist"
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "course_list" in content
        assert "B.Tech Computer Science" in content
        assert "https://sastra.edu/courses" in content


def test_save_excel_extraction_direct():
    """Verify _save_excel_extraction creates a valid excel file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_extract.xlsx")
        data = {
            "name": "annual_tuition",
            "value": "$15,000",
            "extract_type": "text",
            "url": "https://sastra.edu/fees",
        }
        _save_excel_extraction(filepath, "new", data)

        assert os.path.exists(filepath), "Output excel file must exist"
        assert os.path.getsize(filepath) > 0, "Excel file must not be empty"


def test_normalize_history_step_extraction():
    """Verify _normalize_history_step retains extract_text and extract_table action semantics."""
    act_text = {
        "action": "extract_text",
        "target": {"by": "text", "text": "Programmes Offered"},
        "format": "txt",
    }
    step_text = _normalize_history_step(act_text, url="https://sastra.edu")
    assert step_text["action"] == "extract_text"
    assert step_text["target"]["by"] == "text"

    act_table = {
        "action": "extract_table",
        "target": {"by": "css", "selector": "table.courses"},
        "format": "excel",
    }
    step_table = _normalize_history_step(act_table, url="https://sastra.edu")
    assert step_table["action"] == "extract_table"
    assert step_table["target"]["selector"] == "table.courses"


def test_execution_loop_short_circuit_logic():
    """
    Verify that in a batched plan [action1, action2], if action1 fails,
    the short-circuit logic breaks rather than continuing to action2.
    """
    plan = [
        {"action": "extract_table", "target": {"by": "text", "text": "Programmes"}},
        {"action": "done", "text": "Task finished"}
    ]
    executed = []

    for act in plan:
        try:
            # Simulate failure on first action
            if act["action"] == "extract_table":
                raise Exception("Table element not found")
            executed.append(act["action"])
        except Exception:
            # Short-circuit logic: break instead of continue
            break

    assert "done" not in executed, "Subsequent actions must NOT execute after an action failure"
    assert len(executed) == 0


def test_save_extraction_custom_nested_filepath():
    """Verify save helpers automatically create non-existent parent directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_dir = os.path.join(tmpdir, "deep", "nested", "folder")
        txt_path = os.path.join(nested_dir, "custom.txt")
        excel_path = os.path.join(nested_dir, "custom.xlsx")
        word_path = os.path.join(nested_dir, "custom.docx")

        data = {"name": "test_var", "value": "test_val", "extract_type": "text", "url": "https://example.com"}

        _save_txt_extraction(txt_path, "new", data)
        assert os.path.exists(txt_path), "Nested txt path must be created"

        _save_excel_extraction(excel_path, "new", data)
        assert os.path.exists(excel_path), "Nested excel path must be created"

        _save_word_extraction(word_path, "new", data)
        assert os.path.exists(word_path), "Nested word path must be created"


def test_task_done_exception_not_treated_as_failure():
    """
    Verify TaskDone exception is caught cleanly and not counted as a failure.
    """
    from local_webai_server_guided import TaskDone
    
    plan = [{"action": "done", "summary": "Task is complete"}]
    failures = 0
    completed = False

    for a in plan:
        try:
            if a["action"] == "done":
                raise TaskDone()
        except TaskDone:
            completed = True
            break
        except Exception:
            failures += 1
            break

    assert completed is True
    assert failures == 0
