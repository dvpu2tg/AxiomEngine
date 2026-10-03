"""The seven task scores (bench/tasks.py, pass 8) on a graph small enough to check by hand."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))

from tasks import score_tasks  # noqa: E402

A, B, C, D, E = "p.A#a()", "p.B#b()", "p.C#c()", "p.D#d()", "p.E#e()"
CERTAIN = {(A, B), (B, C), (C, D)}          # a → b → c → d; e is uncalled
METHODS = {A, B, C, D, E}


class Tasks(unittest.TestCase):
    def test_perfect_graph_scores_one_everywhere(self):
        t = score_tasks(set(CERTAIN), set(CERTAIN), set(), set(CERTAIN), METHODS, []).as_dict()
        self.assertEqual(t["callees_of"]["mean_f1"], 1.0)
        self.assertEqual(t["callers_of"]["mean_f1"], 1.0)
        self.assertEqual(t["path"]["share"], 1.0)
        self.assertEqual(t["path"]["n"], 6)              # ab ac ad bc bd cd — every pair within 3 hops
        self.assertEqual(t["blast_radius"]["mean_jaccard"], 1.0)
        self.assertEqual((t["uncalled"]["precision"], t["uncalled"]["recall"]), (1.0, 1.0))
        self.assertEqual(t["file_deps"]["f1"], 1.0)

    def test_a_missing_edge_breaks_paths_and_blast_radius(self):
        emitted = {(A, B), (C, D)}                        # b → c missing
        t = score_tasks(emitted, set(CERTAIN), set(), set(CERTAIN), METHODS, []).as_dict()
        self.assertAlmostEqual(t["path"]["share"], 2 / 6)  # only ab and cd survive
        # callers of C within 3 hops: truth {B, A}, tool {} → 0; of D: truth {C, B, A}, tool {C} → 1/3;
        # of B: {A} both → 1
        self.assertAlmostEqual(t["blast_radius"]["mean_jaccard"], (0 + 1 / 3 + 1) / 3)
        # uncalled: the tool claims {A, C, E} (nothing reaches C in its graph), the truth is {A, E}
        self.assertAlmostEqual(t["uncalled"]["precision"], 2 / 3)
        self.assertAlmostEqual(t["uncalled"]["recall"], 1.0)

    def test_an_edge_in_the_accepted_set_is_not_charged_as_wrong(self):
        emitted = set(CERTAIN) | {(A, E)}
        t = score_tasks(emitted, set(CERTAIN), {(A, E)}, set(CERTAIN) | {(A, E)}, METHODS, []).as_dict()
        self.assertEqual(t["callees_of"]["mean_f1"], 1.0)
        self.assertEqual(t["file_deps"]["precision"], 1.0)

    def test_dispatch_is_jaccard_against_the_runnable_set(self):
        groups = [{"caller": A, "name": "b", "possible": {"p.B#b()", "p.B2#b()"}}]
        t = score_tasks({(A, "p.B#b()")}, set(), set(), set(), METHODS, groups).as_dict()
        self.assertAlmostEqual(t["dispatch"]["mean_jaccard"], 1 / 2)
        t = score_tasks({(A, "p.B#b()"), (A, "p.B2#b()")}, set(), set(), set(), METHODS, groups).as_dict()
        self.assertEqual(t["dispatch"]["mean_jaccard"], 1.0)

    def test_file_of_java_and_typescript(self):
        emitted = {("p.q.Outer$Inner#m()", "p.q.Other#n()"), ("src/a.ts:C#m()", "src/b.ts:D#n()")}
        t = score_tasks(emitted, emitted, set(), emitted, set(), []).as_dict()
        self.assertEqual(t["file_deps"]["truth"], 2)
        same_file = {("p.q.Outer$Inner#m()", "p.q.Outer#n()")}
        t = score_tasks(same_file, same_file, set(), same_file, set(), []).as_dict()
        self.assertEqual(t["file_deps"]["truth"], 0)
        # #97: a class whose own name starts with `$` is one file, and its members live in it
        dollar = {("g.$Gson$Types.WildcardTypeImpl#m()", "g.$Gson$Types#n()")}
        t = score_tasks(dollar, dollar, set(), dollar, set(), []).as_dict()
        self.assertEqual(t["file_deps"]["truth"], 0)
        apart = {("g.$Gson$Types#n()", "g.Gson#m()")}
        t = score_tasks(apart, apart, set(), apart, set(), []).as_dict()
        self.assertEqual(t["file_deps"]["truth"], 1)

    def test_samples_do_not_depend_on_set_iteration_order(self):
        # verify.sh re-scores identical inputs in a fresh process (a different hash seed): the
        # sampled pairs and targets must come out the same
        import json
        import os
        import subprocess
        prog = (
            "import sys, json, random; sys.path.insert(0, 'bench')\n"
            "from tasks import score_tasks\n"
            "rng = random.Random(7); N = 400\n"
            "ml = sorted(f'p.C{i % 40}#m{i}()' for i in range(N))\n"
            "certain = {(ml[rng.randrange(N)], ml[rng.randrange(N)]) for _ in range(900)}\n"
            "emitted = {e for e in sorted(certain) if rng.random() < 0.8}\n"
            "print(json.dumps(score_tasks(emitted, certain, set(), certain, set(ml), []).as_dict(), sort_keys=True))\n")
        outs = set()
        for seed in ("1", "2", "3"):
            r = subprocess.run([sys.executable, "-c", prog], cwd=ROOT, capture_output=True, text=True,
                               env={**os.environ, "PYTHONHASHSEED": seed}, check=True)
            outs.add(r.stdout)
        self.assertEqual(len(outs), 1)


if __name__ == "__main__":
    unittest.main()
