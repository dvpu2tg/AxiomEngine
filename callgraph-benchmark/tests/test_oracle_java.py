"""The Java oracle on the conventions torture file (F11Conventions): the expectations are derived
from the JVMS, not from any tool (issues #30 second pass, #47). Skipped when no JDK is present."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "java/subjects/torture/client"
ORACLE = ROOT / "java/oracle/ClassfileGroundTruth.java"


@unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "no JDK")
class JavaOracleConventions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="cgb-oracle-"))
        classes, oc = cls.tmp / "classes", cls.tmp / "oc"
        classes.mkdir(); oc.mkdir()
        # the conventions file alone: it has no dependency, and the rest of the torture client needs
        # its classpath tree (built by java/run/subject.sh)
        subprocess.run(["javac", "-g", "-d", str(classes), str(SRC / "torture/F11Conventions.java")], check=True)
        subprocess.run(["javac", "-d", str(oc), str(ORACLE)], check=True)
        out = subprocess.run(["java", "-cp", str(oc), "ClassfileGroundTruth", "--app", str(classes),
                              "--include-prefix", "torture", "--mode", "sites"],
                             capture_output=True, text=True, check=True).stdout
        cls.sites = [json.loads(ln) for ln in out.splitlines() if ln.strip()]
        cls.by = {}
        for s in cls.sites:
            cls.by.setdefault((s["caller"], s["callee_name"]), []).append(s)

    def one(self, caller: str, name: str) -> dict:
        rows = self.by.get((caller, name), [])
        self.assertEqual(len(rows), 1, f"{caller} -> {name}: {rows}")
        return rows[0]

    def test_private_superclass_method_is_not_a_declaring_ancestor(self):
        s = self.one("torture.F11Conventions.OuterSub#own()", "secret")
        self.assertEqual(s["certain"], ["torture.F11Conventions.OuterSub#secret()"])
        self.assertNotIn("torture.F11Conventions.Outer#secret()", s["declaring_ancestors"])

    def test_external_declared_target_is_a_boundary_with_accepted_implementors(self):
        s = self.one("torture.F11Conventions#total(List)", "size")
        self.assertEqual(s["kind"], "boundary")
        self.assertEqual(s["possible"], [])
        self.assertFalse(s["unique"])
        self.assertIn("torture.F11Conventions.Ints#size()", s["declaring_ancestors"])

    def test_rta_excludes_a_class_reached_only_by_method_reference(self):
        s = self.one("torture.F11Conventions#use(Src)", "get")
        self.assertEqual(s["possible"], ["torture.F11Conventions.NewSrc#get()", "torture.F11Conventions.RefSrc#get()"])
        self.assertEqual(s["possible_rta"], ["torture.F11Conventions.NewSrc#get()"])

    def test_record_equals_is_a_real_member(self):
        s = self.one("torture.F11Conventions#same(P,P)", "equals")
        self.assertEqual(s["certain"], ["torture.F11Conventions.P#equals(Object)"])

    def test_output_uses_lf_only(self):
        out = subprocess.run(["java", "-cp", str(self.tmp / "oc"), "ClassfileGroundTruth", "--app",
                              str(self.tmp / "classes"), "--include-prefix", "torture", "--mode", "classes"],
                             capture_output=True, check=True).stdout
        self.assertNotIn(b"\r", out)


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "no JDK")
class JavaOracleLowering(unittest.TestCase):
    """F12Lowering at `--release 8` and at the current release: the oracle must undo javac's
    lowering the same way on both (issues #66, #26, #77, #78, #79)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="cgb-lowering-"))
        oc = cls.tmp / "oc"; oc.mkdir()
        subprocess.run(["javac", "-d", str(oc), str(ORACLE), str(ORACLE.parent / "EnvelopeCheck.java")], check=True)
        srcs = [str(SRC / "torture/F12Lowering.java"), *map(str, (SRC / "other").glob("*.java")), *map(str, (SRC / "far").glob("*.java"))]
        cls.sites = {}
        for rel, flags in (("8", ["--release", "8"]), ("now", [])):
            d = cls.tmp / rel; d.mkdir()
            subprocess.run(["javac", *flags, "-g", "-d", str(d), *srcs], check=True, capture_output=True)
            out = subprocess.run(["java", "-cp", str(oc), "ClassfileGroundTruth", "--app", str(d), "--mode", "sites"],
                                 capture_output=True, text=True, check=True).stdout
            cls.sites[rel] = [json.loads(ln) for ln in out.splitlines() if ln.strip()]
            (d / "sites.jsonl").write_text(out)
            chk = subprocess.run(["java", "-cp", str(oc), "EnvelopeCheck", "--app", str(d), "--sites", str(d / "sites.jsonl")],
                                 capture_output=True, text=True)
            assert chk.returncode == 0, chk.stdout + chk.stderr

    def rows(self, rel, caller_tail, name):
        return [s for s in self.sites[rel] if s["caller"].endswith(caller_tail) and s["callee_name"] == name]

    def test_release_8_and_current_agree(self):
        key = lambda s: (s["caller"], s["line"], s["callee_name"], tuple(s["certain"]), tuple(s["possible"]))
        self.assertEqual(sorted(map(key, self.sites["8"])), sorted(map(key, self.sites["now"])))

    def test_access_accessor_is_the_written_call(self):
        for rel in ("8", "now"):
            r = self.rows(rel, "Inner#peek()", "secret")
            self.assertEqual([x["certain"] for x in r], [["torture.F12Lowering#secret()"]], rel)

    def test_private_constructor_accessor_is_the_written_new(self):
        for rel in ("8", "now"):
            r = self.rows(rel, "F12Lowering#mk()", "<init>")
            self.assertEqual([x["certain"] for x in r], [["torture.F12Lowering.Priv#<init>()"]], rel)

    def test_written_new_base_in_a_constructor_is_kept(self):
        r = self.rows("now", "Sub#<init>()", "<init>")
        self.assertEqual(sorted(x["certain"][0] for x in r),
                         ["torture.F12Lowering.Base#<init>()", "torture.F12Lowering.Base#<init>(int)"])

    def test_iterator_subtype_calls_are_written_and_covariant_for_each_is_lowered(self):
        self.assertEqual(len(self.rows("now", "F12Lowering#drain(MyIter)", "hasNext")), 1)
        self.assertEqual(len(self.rows("now", "F12Lowering#drain(MyIter)", "next")), 1)
        self.assertEqual(self.rows("now", "F12Lowering#count(Bag)", "iterator"), [])
        self.assertEqual(self.rows("now", "F12Lowering#count(Bag)", "hasNext"), [])

    def test_enum_valueof_overload_is_the_sources_own(self):
        r = self.rows("now", "F12Lowering#pick()", "valueOf")
        self.assertEqual([x["certain"] for x in r], [["torture.F12Lowering.Color#valueOf(int)"]])

    def test_static_initializer_of_a_class_is_a_caller(self):
        self.assertEqual(len(self.rows("now", "F12Lowering#<clinit>()", "helper")), 1)

    def test_constructor_reference_instantiates_for_rta(self):
        r = self.rows("now", "F12Lowering#area(Shape)", "area")[0]
        self.assertEqual(r["possible_rta"], ["torture.F12Lowering.Sq#area()"])

    def test_field_initializer_is_one_site(self):
        r = [s for s in self.sites["now"] if ".Init#<init>" in s["caller"] and s["callee_name"] == "compute"]
        self.assertEqual(len(r), 1)

    def test_visibility_bridge_resolves_to_the_declaring_method(self):
        r = self.rows("now", "F12Lowering#viaBridge(Shw)", "pub")
        self.assertEqual([x["certain"] for x in r], [["torture.F12Lowering.Hid#pub()"]])

    def test_transitive_override_is_in_the_envelope(self):
        r = self.rows("now", "other.A#call(A)", "m")[0]
        self.assertIn("far.C#m()", r["possible"])

    def test_multi_line_try_with_resources_scores_only_the_written_call(self):
        names = sorted(s["callee_name"] for s in self.sites["now"] if s["caller"].endswith("F12Lowering#twr()"))
        self.assertEqual(names, ["<init>", "work"])

    def test_anonymous_constructor_chain_is_not_a_second_site(self):
        r = [s for s in self.sites["now"] if "$anon:Base" in s["caller"]]
        self.assertEqual(r, [])

    def test_site_ids_are_unique(self):
        ids = [s["site_id"] for s in self.sites["now"]]
        self.assertEqual(len(ids), len(set(ids)))
