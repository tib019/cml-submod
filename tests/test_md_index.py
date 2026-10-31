import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.md_index import build_index

FIXTURE = Path(__file__).parent / "fixtures" / "mini_md"


class TestMdIndex(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.idx = build_index(FIXTURE, None)

    def test_index_contains_each_kind(self):
        i = self.idx
        self.assertEqual(i["version"], "2.0.3")
        self.assertIn("SOV_zyuganov", i["focuses"])
        self.assertIn("mini_shared", i["focuses"])
        self.assertIn("oligarchs", i["ideas"])
        self.assertIn("mini_hidden_idea", i["ideas"])
        self.assertNotIn("law", i["ideas"])
        self.assertIn("MIN_person", i["characters"])
        self.assertIn("change_labour_unions_opinion", i["scripted_effects"])
        self.assertIn("emerging_communist_state_are_in_power", i["scripted_triggers"])
        self.assertIn("sov_other", i["event_namespaces"])
        self.assertIn("GFX_goal_generic_political_pressure", i["sprites"])
        self.assertIn("GFX_mini_animated", i["sprites"])
        self.assertIn("mini_category", i["decision_categories"])
        self.assertIn("mini_decision", i["decisions"])
        self.assertIn("mini_dynamic_modifier", i["dynamic_modifiers"])

    def test_files_relative_posix(self):
        files = self.idx["files"]
        self.assertIn("common/national_focus/mini_focus.txt", files)
        self.assertIn("localisation/english/mini_l_english.yml", files)
        self.assertNotIn("descriptor.mod", files)
        for f in files:
            self.assertNotIn("\\", f)
            self.assertFalse(f.startswith("/"))

    def test_lists_sorted(self):
        for key, val in self.idx.items():
            if isinstance(val, list):
                self.assertEqual(val, sorted(val), key)

    def test_broken_file_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "md"
            shutil.copytree(FIXTURE, root)
            (root / "common/scripted_effects/kaputt.txt").write_bytes(b"x = { y = \xff\xfe")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                idx = build_index(root, None)
            self.assertIn("kaputt.txt", err.getvalue())
            self.assertIn("change_labour_unions_opinion", idx["scripted_effects"])


if __name__ == "__main__":
    unittest.main()
