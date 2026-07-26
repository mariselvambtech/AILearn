import os
import sys
import unittest
from pathlib import Path

# Add project root and local server path to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir / "webai_local_server"))

from webai_local_server.local_webai_server_guided import (
    _extract_json_array,
    _prune_dom_snapshot,
    _writeback_healed_step,
)


class TestHermesFeatures(unittest.TestCase):
    def test_extract_json_array_markdown(self):
        sample_markdown = '```json\n[{"action": "click", "by": "text", "text": "Submit"}]\n```'
        result = _extract_json_array(sample_markdown)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["action"], "click")

    def test_extract_json_array_chatter(self):
        sample_chatter = 'Here is your action plan:\n[{"action": "type", "text": "test"}]\nHope this helps!'
        result = _extract_json_array(sample_chatter)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["action"], "type")

    def test_prune_dom_snapshot(self):
        html = '<html><head><script>alert(1)</script></head><body><div class="main"><button id="btn1">Click Me</button><input name="query" type="text"/></div></body></html>'
        pruned = _prune_dom_snapshot(html)
        self.assertIn("button", pruned)
        self.assertNotIn("script", pruned)

    def test_writeback_healed_step_invalid_id(self):
        # Should gracefully return False if no automation ID is provided
        res = _writeback_healed_step(automation_id=None, step_index=0, new_locators=[])
        self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()
