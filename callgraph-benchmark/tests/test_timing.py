"""The seconds column: the tool's own work, not the harness's (issues #8, #98)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bench"))
import run as R   # noqa: E402


class ToolSeconds(unittest.TestCase):
    def test_export_is_not_the_tools_time(self):
        # rxjava-shaped (#98): 360 s on the adapter's clock, 29.5 s of it indexing, the rest paging
        timings = {"gitnexus": 360.0}
        parts = {"gitnexus": {"staging": 2.0, "export": 328.5}}
        self.assertEqual(R.tool_seconds("gitnexus", timings, parts), 29.5)
        self.assertEqual(R.tool_breakdown("gitnexus", timings, parts)["export"], 328.5)

    def test_staging_alone_is_still_excluded(self):
        self.assertEqual(R.tool_seconds("graphify", {"graphify": 10.0}, {"graphify": {"staging": 1.5}}), 8.5)

    def test_two_labels_cost_the_shared_phase_plus_their_own(self):
        timings = {"axiom": 30.0}
        parts = {"axiom": {"shared": 5.0, "own:axiom": 20.0, "own:axiom-nolib": 4.0, "staging": 1.0}}
        self.assertEqual(R.tool_seconds("axiom", timings, parts), 25.0)
        self.assertEqual(R.tool_seconds("axiom-nolib", timings, parts), 9.0)

    def test_no_export_key_unless_one_was_recorded(self):
        self.assertNotIn("export", R.tool_breakdown("codegraph", {"codegraph": 4.0}, {"codegraph": {"staging": 0.1}}))

    def test_no_parts_is_the_whole_clock(self):
        self.assertEqual(R.tool_seconds("cha", {"cha": 3.0}, {}), 3.0)


if __name__ == "__main__":
    unittest.main()
