import unittest
import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_ppt_outline.py"
spec = importlib.util.spec_from_file_location("generate_ppt_outline", SCRIPT_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PptOutlineTests(unittest.TestCase):
    def test_duration_to_slide_count(self):
        self.assertEqual(mod.slide_count_by_duration(10), 7)
        self.assertEqual(mod.slide_count_by_duration(15), 9)
        self.assertEqual(mod.slide_count_by_duration(30), 14)

    def test_generate_outline_shape(self):
        data = mod.generate_outline("主题A", "管理层", 15, "说服", "zh")
        self.assertEqual(data["deck_title"], "主题A")
        self.assertEqual(len(data["slides"]), 9)
        self.assertIn("slide_title", data["slides"][0])
        self.assertIn("speaker_notes", data["slides"][0])


if __name__ == "__main__":
    unittest.main()
