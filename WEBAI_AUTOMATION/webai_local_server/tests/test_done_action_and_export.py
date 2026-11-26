import asyncio
import tempfile
import os
import pytest
from pathlib import Path
from typing import Dict, Any

from webai_local_server.local_webai_server_guided import (
    TaskDone,
    _save_txt_extraction,
    _save_excel_extraction,
    _save_word_extraction,
    _auto_export_summary,
)

def test_save_extraction_functions():
    """Verify text, excel, and word extraction files save correctly without errors."""
    with tempfile.TemporaryDirectory() as tmpdir:
        payload = {
            "name": "Test Course Extraction",
            "value": "Computer Science & Engineering; Artificial Intelligence",
            "extract_type": "text",
            "url": "https://example.com/courses"
        }
        
        txt_path = os.path.join(tmpdir, "test.txt")
        xlsx_path = os.path.join(tmpdir, "test.xlsx")
        docx_path = os.path.join(tmpdir, "test.docx")
        
        _save_txt_extraction(txt_path, "new", payload)
        assert os.path.exists(txt_path)
        assert os.path.getsize(txt_path) > 0
        
        _save_excel_extraction(xlsx_path, "new", payload)
        assert os.path.exists(xlsx_path)
        assert os.path.getsize(xlsx_path) > 0
        
        _save_word_extraction(docx_path, "new", payload)
        assert os.path.exists(docx_path)
        assert os.path.getsize(docx_path) > 0

def test_task_done_exception_hierarchy():
    """Verify TaskDone is catchable specifically before generic Exception handler."""
    def dummy_exec(act: Dict[str, Any]):
        if act.get("action") == "done":
            raise TaskDone()
        raise RuntimeError("failed")

    caught_as_task_done = False
    caught_as_generic = False
    
    try:
        dummy_exec({"action": "done"})
    except TaskDone:
        caught_as_task_done = True
    except Exception:
        caught_as_generic = True

    assert caught_as_task_done is True
    assert caught_as_generic is False

def test_auto_export_summary_custom_folder_and_cleanup():
    """Verify _auto_export_summary extracts custom folder, writes excel/word/txt, and strips disclaimers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target_folder = os.path.join(tmpdir, "output")
        task_text = f"Go to https://sastra.edu/ and extract courses. store the documents to {target_folder} folder in excel or word."
        summary_text = (
            "List of UG/PG programmes offered at SASTRA:\n\n"
            "B.Tech. Programmes (UG):\n"
            "1. B.Tech. Aerospace Engineering\n"
            "2. B.Tech. Bioengineering\n\n"
            "M.Tech. Programmes (PG):\n"
            "1. M.Tech. Integrated Biotechnology\n\n"
            "Other UG/PG Programmes:\n"
            "- B.Optom\n\n"
            "Note: The course list has been extracted successfully. Saving this data as an Excel/Word file to D:\\output "
            "requires local file-system access, which is outside the scope of browser automation actions; please save "
            "the extracted list above using Excel or Word."
        )

        saved = _auto_export_summary(task_text, summary_text)
        assert len(saved) >= 2  # Excel and Word
        
        # Verify files were saved directly inside the target_folder
        saved_paths = [Path(p) for p in saved]
        for p in saved_paths:
            assert str(p.parent).lower() == target_folder.lower()
            assert p.exists()
            assert p.stat().st_size > 0

        # Check excel contents
        import pandas as pd
        excel_path = next(p for p in saved_paths if p.suffix == ".xlsx")
        df = pd.read_excel(excel_path)
        assert "Category" in df.columns
        assert "Programme" in df.columns
        assert any("Aerospace" in str(val) for val in df["Programme"].values)
        # Verify disclaimer line was not included in the rows
        assert not any("outside the scope" in str(val).lower() for val in df["Programme"].values)
