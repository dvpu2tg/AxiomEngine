"""The TypeScript oracle on the torture files whose expectations were written before the oracle
ran (t09 — issue #39; t10 — issues #52, #53). Skipped when the pinned toolchain is absent."""
import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TSX = ROOT / ".tools/ts/node_modules/.bin/tsx"
ORACLE = ROOT / "typescript/oracle/ts-ground-truth.ts"
PROJECT = ROOT / "typescript/subjects/torture/tsconfig.json"
SRC = ROOT / "typescript/subjects/torture"


def short(xs):
    return sorted(x.split(":")[-1] for x in xs)


@unittest.skipUnless(TSX.exists(), "no pinned TypeScript toolchain (typescript/install.sh)")
class TypeScriptOracleTorture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env = dict(os.environ, NODE_PATH=str(ROOT / ".tools/ts/node_modules"))

        def oracle(mode: str) -> str:
            # `--no-cache`: two runners starting the suite at once raced on tsx's compile cache and
            # one of them failed gate 3a with the cause swallowed (#82); the stderr is now in the
            # message
            r = subprocess.run([str(TSX), "--no-cache", str(ORACLE), "--project", str(PROJECT), "--root", str(SRC),
                                "--mode", mode], capture_output=True, text=True, env=env)
            if r.returncode != 0:
                raise AssertionError(f"oracle --mode {mode} failed (rc {r.returncode}):\n{r.stderr[-4000:]}")
            return r.stdout
        out = oracle("sites")
        cls.sites = [json.loads(ln) for ln in out.splitlines() if ln.strip()]
        cls.heritage = oracle("heritage")

    def at(self, module: str, line: int, name: str) -> dict:
        rows = [s for s in self.sites if s["caller"].startswith(module) and s["line"] == line and s["callee_name"] == name]
        self.assertEqual(len(rows), 1, f"{module}:{line} {name}: {rows}")
        return rows[0]

    # t09 — a member declared in a type literal (#39)
    def test_type_literal_member_resolves_to_the_apparent_type(self):
        s = self.at("src/t09-typelit.ts", 19, "getValue")
        self.assertEqual(short(s["certain"]), ["Options#getValue(string)"])

    def test_containerless_type_literal_member_is_indirect(self):
        s = self.at("src/t09-typelit.ts", 25, "toObject")
        self.assertEqual(s["kind"], "indirect")

    # t10 — #52
    def test_union_of_callables_is_indirect(self):
        s = self.at("src/t10-audit.ts", 10, "chosen")
        self.assertEqual(s["kind"], "indirect")
        self.assertEqual(s["certain"], [])

    def test_interface_member_reached_through_a_union_arm_is_declared_not_runnable(self):
        s = self.at("src/t10-audit.ts", 18, "m")
        self.assertIn("R#m()", short(s["certain"]))
        self.assertNotIn("R#m()", short(s["possible"]))
        self.assertIn("RImpl#m()", short(s["possible"]))

    def test_rta_is_seeded_only_from_instantiated_receivers(self):
        s = self.at("src/t10-audit.ts", 25, "run")
        self.assertIn("Base#run()", short(s["possible"]))
        self.assertEqual(short(s["possible_rta"]), ["Deeper#run()"])

    def test_new_does_not_dispatch(self):
        s = self.at("src/t10-audit.ts", 34, "constructor")
        self.assertEqual(short(s["possible"]), ["WithCtor#constructor(number)"])
        self.assertTrue(s["unique"])

    # t10 — #53
    def test_arrow_passed_through_a_call_folds_into_the_enclosing_function(self):
        s = self.at("src/t10-audit.ts", 43, "helper")
        self.assertEqual(s["caller"], "src/t10-audit.ts#callerOfPredicate(number[])")

    def test_element_access_call_is_named_as_written(self):
        s = self.at("src/t10-audit.ts", 48, "handler")
        self.assertEqual(s["kind"], "indirect")

    # t11 — #67, #68, #73, #74, #80
    def test_inherited_member_resolves_to_the_declaring_base(self):
        s = self.at("src/t11-envelope2.ts", 6, "area")
        self.assertEqual(short(s["possible"]), ["PlainBase#area()"]); self.assertTrue(s["unique"])

    def test_structural_implementor_of_an_instantiated_generic_interface(self):
        s = self.at("src/t11-envelope2.ts", 10, "get")
        self.assertEqual(short(s["possible"]), ["NumBox#get()"])

    def test_abstract_redeclaration_is_not_runnable(self):
        s = self.at("src/t11-envelope2.ts", 15, "f")
        self.assertEqual(short(s["possible"]), ["C5#f()"]); self.assertTrue(s["unique"])

    def test_union_with_a_library_arm_is_a_boundary(self):
        s = self.at("src/t11-envelope2.ts", 19, "toString")
        self.assertEqual(s["kind"], "boundary"); self.assertIn("Alpha#toString()", short(s["declaring_ancestors"]))

    def test_rta_keeps_an_implementation_inherited_by_an_instantiated_subclass(self):
        s = self.at("src/t11-envelope2.ts", 24, "find")
        self.assertEqual(short(s["possible_rta"]), ["Repo#find()"])

    def test_returned_closure_stored_in_a_field_is_indirect(self):
        s = self.at("src/t11-envelope2.ts", 31, "header")
        self.assertEqual(s["kind"], "indirect")

    def test_field_initializers_belong_to_the_class(self):
        s = self.at("src/t11-envelope2.ts", 35, "constructor")
        self.assertEqual(s["caller"], "src/t11-envelope2.ts:Application#constructor()")
        s = self.at("src/t11-envelope2.ts", 36, "mkRegistry")
        self.assertEqual(s["caller"], "src/t11-envelope2.ts:Application#<clinit>()")

    def test_static_call_does_not_dispatch(self):
        s = self.at("src/t11-envelope2.ts", 42, "make")
        self.assertEqual(short(s["possible"]), ["K#make()"])

    def test_union_receiver_keeps_the_declared_signature(self):
        s = self.at("src/t11-envelope2.ts", 45, "set")
        self.assertEqual(short(s["certain"]), ["Bx#set(T)"]); self.assertTrue(s["unique"])

    def test_merged_class_and_interface_is_a_class_in_the_heritage(self):
        # ioredis writes `class Redis` and `interface Redis`; the torture subject's t01 Square is a
        # plain class — the rule is exercised on real subjects, the format is checked here
        for ln in self.heritage.splitlines():
            parts = ln.split("\t")
            self.assertGreaterEqual(len(parts), 2)
            self.assertIn(parts[1], ("class", "interface", "object", "container"))


if __name__ == "__main__":
    unittest.main()
