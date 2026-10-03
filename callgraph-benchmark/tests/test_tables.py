"""The README tables: the envelope-class rule and the ranking column (issues #1, #12, #49, #50)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bench"))
import readme_tables as RT   # noqa: E402


def row(strict: float, precision: float, exact: int = 90, total: int = 100, null=False, build="bytecode") -> dict:
    return {"scorable": True, "null_model": null, "build": build,
            "vs_certain": {"precision_strict": strict},
            "vs_possible": {"precision": precision},
            "unique_link_groups": {"counts": {"exact": exact}, "total": total}}


class EnvelopeClass(unittest.TestCase):
    NULL = row(0.0165, 1.0, 100, 100, null=True)     # rxjava's envelope: 98.35% fan

    def test_the_rxjava_dispatch_row_is_envelope_class(self):
        # #12 reopened: strict 0.0009 ABOVE the null's, fan share 98% of the envelope's
        self.assertTrue(RT.envelope_class(row(0.0174, 0.998), self.NULL))

    def test_a_sharp_row_with_plain_false_positives_is_not(self):
        # kysely-shaped: fan share 0.006 — false positives outside the envelope, not enumeration
        null = row(0.805, 1.0, null=True)
        self.assertFalse(RT.envelope_class(row(0.78, 0.786), null))

    def test_the_rule_is_off_where_the_subject_barely_dispatches(self):
        null = row(0.962, 1.0, null=True)
        self.assertFalse(RT.envelope_class(row(0.5, 1.0), null))


class Ranking(unittest.TestCase):
    def test_envelope_class_cells_do_not_rank(self):
        # #12 reopened: a row that is † on every subject cannot outrank an unmarked row with lower exact%
        import json, tempfile, pathlib
        root = pathlib.Path(tempfile.mkdtemp())
        (root / "java/results/s1").mkdir(parents=True)
        def b(exact, total, strict, prec, null=False, build="bytecode"):
            return {"B": {"scorable": True, "null_model": null, "build": build,
                          "vs_certain": {"precision_strict": strict}, "vs_possible": {"precision": prec},
                          "unique_link_groups": {"counts": {"exact": exact}, "total": total}}}
        scores = {"cha-null": b(100, 100, 0.5, 1.0, null=True), "ideal": b(100, 100, 1.0, 1.0, null=True, build="oracle"),
                  "enumerator": b(99, 100, 0.55, 1.0), "resolver": b(90, 100, 0.95, 0.97)}
        (root / "java/results/s1/scores.json").write_text(json.dumps({"scores": scores, "subject": {"link_groups_unique": 100}}))
        old_root, old_compare = RT.ROOT, RT.COMPARE
        try:
            RT.ROOT, RT.COMPARE = root, {"java": ["s1"], "typescript": []}
            table = RT.summary("java")
        finally:
            RT.ROOT, RT.COMPARE = old_root, old_compare
        rows = [ln for ln in table.splitlines() if ln.startswith("| `")]
        self.assertTrue(rows[0].startswith("| `resolver`"), table)
        self.assertIn("†", [ln for ln in rows if "enumerator" in ln][0])


class LibraryFreeHeadline(unittest.TestCase):
    """A row whose run was given the subject's external libraries is never ranked beside source-only
    tools: it is published in its own table next to the same tool's library-free row."""

    def fixture(self):
        import json, tempfile, pathlib
        root = pathlib.Path(tempfile.mkdtemp())
        (root / "java/results/s1").mkdir(parents=True)
        def b(exact, build, null=False):
            return {"B": {"scorable": True, "null_model": null, "build": build,
                          "vs_certain": {"precision_strict": 0.99}, "vs_possible": {"precision": 0.99},
                          "unique_link_groups": {"counts": {"exact": exact}, "total": 100},
                          "vs_rta": {"tp": 1, "fn": 0}}}
        scores = {"cha-null": b(100, "bytecode", null=True), "ideal": b(100, "oracle", null=True),
                  "axiom": b(99, "source + platform IR"), "axiom-nolib": b(90, "source only"),
                  "codeql": b(95, "build-mode=none"), "codeql-built": b(98, "compiled build"),
                  "graphify": b(70, "source only")}
        (root / "java/results/s1/scores.json").write_text(
            json.dumps({"scores": scores, "subject": {"link_groups_unique": 100}}))
        return root

    def render(self, fn):
        root = self.fixture()
        old_root, old_compare = RT.ROOT, RT.COMPARE
        try:
            RT.ROOT, RT.COMPARE = root, {"java": ["s1"], "typescript": []}
            return fn("java")
        finally:
            RT.ROOT, RT.COMPARE = old_root, old_compare

    def test_budgets_are_classified(self):
        for build, lib in (("source + platform IR", True), ("compiled build", True), ("source only", False),
                           ("build-mode=none", False), ("oracle", False), (None, False)):
            with self.subTest(build=build):
                self.assertEqual(RT.uses_libraries({"build": build}), lib)

    def test_the_ranked_matrix_holds_no_library_row(self):
        table = self.render(RT.summary)
        rows = [ln for ln in table.splitlines() if ln.startswith("| `") or ln.startswith("| **`")]
        self.assertNotIn("libraries", table)
        self.assertEqual(len(rows), 3, table)                  # codeql, AxiomEngine (nolib), graphify
        self.assertTrue(rows[0].startswith("| `codeql`"), table)  # 95 outranks the no-library 90
        self.assertIn("**`AxiomEngine`**", table)

    def test_the_library_table_pairs_each_row_with_its_library_free_run(self):
        table = self.render(RT.library_table)
        lines = [ln for ln in table.splitlines() if ln.startswith("| `")]
        self.assertEqual([ln.split("|")[1].strip() for ln in lines],
                         ["`AxiomEngine + libraries`", "`AxiomEngine`", "`codeql-built + libraries`"])


class Standings(unittest.TestCase):
    """#94: the claims under "Where axiom-code-graph lands" are computed, and a rank never hides an
    exclusion — an envelope-class row ranked above AxiomEngine is named."""

    def test_rank_names_the_envelope_row_above(self):
        import json, tempfile, pathlib
        root = pathlib.Path(tempfile.mkdtemp())
        (root / "java/results/s1").mkdir(parents=True)
        def b(exact, strict, prec, build="source only", null=False):
            return {"B": {"scorable": True, "null_model": null, "build": build,
                          "vs_certain": {"precision_strict": strict}, "vs_possible": {"precision": prec},
                          "unique_link_groups": {"counts": {"exact": exact, "missed": 100 - exact}, "total": 100}}}
        scores = {"cha-null": b(100, 0.5, 1.0, "bytecode", null=True), "ideal": b(100, 1.0, 1.0, "oracle", null=True),
                  "codeql": b(99, 0.99, 0.99), "codeql-dispatch": b(98, 0.55, 1.0),
                  "axiom-nolib": b(95, 0.9, 0.95), "axiom": b(97, 0.9, 0.95, "source + platform IR")}
        (root / "java/results/s1/scores.json").write_text(json.dumps({"scores": scores, "subject": {}}))
        old_root, old_compare = RT.ROOT, RT.COMPARE
        try:
            RT.ROOT, RT.COMPARE = root, {"java": ["s1"], "typescript": []}
            text = RT.standings("java")
        finally:
            RT.ROOT, RT.COMPARE = old_root, old_compare
        self.assertIn("s1 `codeql` 99.0% (1.0 below the ceiling)", text)
        # the library row (97) is not ranked; the library-free one is #3, codeql-dispatch named
        self.assertIn("s1 95.0% — #3 of 3 (above it and envelope-class there: `codeql-dispatch`)", text)
        self.assertIn("95 of 100 one-target groups (95.0%); the 5 not found are 5 missed", text)
        self.assertIn("behind `codeql` on s1 (95.0 vs 99.0)", text)


class Accuracy(unittest.TestCase):
    def test_strict_fan_noise_partition_the_rows(self):
        import json, tempfile, pathlib
        root = pathlib.Path(tempfile.mkdtemp())
        (root / "java/results/s1").mkdir(parents=True)
        # 100 rows: 60 declared targets, 30 runnable overrides (fan), 10 outside the envelope (noise)
        b = {"B": {"scorable": True, "null_model": False, "build": "source only",
                   "vs_certain": {"tp": 60, "fn": 20, "emitted": 100, "precision_strict": 0.6},
                   "vs_possible": {"fp": 10, "precision": 0.9},
                   "unique_link_groups": {"counts": {"exact": 50}, "total": 60}}}
        (root / "java/results/s1/scores.json").write_text(json.dumps({"scores": {"t": b}, "subject": {}}))
        old_root, old_compare = RT.ROOT, RT.COMPARE
        try:
            RT.ROOT, RT.COMPARE = root, {"java": ["s1"], "typescript": []}
            row = [ln for ln in RT.accuracy_table("java").splitlines() if ln.startswith("| `t`")][0]
        finally:
            RT.ROOT, RT.COMPARE = old_root, old_compare
        cells = [c.strip() for c in row.split("|")[2:-1]]
        # F1 = 2·0.9·0.75/1.65, F1-strict = 2·0.6·0.75/1.35, recall 0.75, precision 0.9, strict 0.6, fan 0.3, noise 0.1
        self.assertEqual(cells, ["0.818", "0.667", "0.750", "0.900", "0.600", "0.300", "0.100"])


class AdjustedExact(unittest.TestCase):
    def test_null_model_scores_its_own_strict_precision(self):
        ideal = row(1.0, 1.0, 100, 100, null=True, build="oracle")
        null = row(0.546, 1.0, 100, 100, null=True)
        self.assertAlmostEqual(RT.adjusted_exact(null, ideal), 54.6, places=6)

    def test_a_resolver_is_ranked_above_the_envelope(self):
        ideal = row(1.0, 1.0, 100, 100, null=True, build="oracle")
        null = row(0.546, 1.0, 100, 100, null=True)
        codeql = row(0.99, 0.99, 100, 100)
        self.assertGreater(RT.adjusted_exact(codeql, ideal), RT.adjusted_exact(null, ideal))

    def test_sharpness_is_capped_at_one(self):
        ideal = row(0.9, 1.0, 100, 100, null=True, build="oracle")
        self.assertEqual(RT.sharpness(row(1.0, 1.0), ideal), 1.0)


class ChainIdentity(unittest.TestCase):
    def test_precision_times_blowup_is_recall(self):
        # #50: the README prints recall and blowup because P × blowup ≡ recall
        tp, n_ans, n_t = 36646, 12237324, 49597
        p, blowup, r = tp / n_ans, n_ans / n_t, tp / n_t
        self.assertAlmostEqual(p * blowup, r, places=9)


if __name__ == "__main__":
    unittest.main()
