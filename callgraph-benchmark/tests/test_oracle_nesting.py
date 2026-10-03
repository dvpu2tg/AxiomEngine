"""Nesting is read from InnerClasses, not from the position of a `$` (#97).

`$` is a letter to the JLS, so a top-level class may carry one in its own name — gson's
`$Gson$Types`. Reading it as a nesting separator canonicalised that class to a spelling with a
doubled dot, which is not a type anyone can write, and took it out of the scored universe for
every tool at once. JVMS 4.7.6 settles it: a nested class's own class file carries an
InnerClasses entry for itself, and a top-level one does not.
"""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "java/oracle/ClassfileGroundTruth.java"

SOURCE = """package pkg;

public final class $Dollar$Types {
    static final class Impl { int go() { return 1; } }
    Object anon() { return new Runnable() { public void run() {} }; }
    int local() { class Helper { int v() { return 2; } } return new Helper().v(); }
}
"""

OUTER = """package pkg;

public class Outer {
    static class Inner { int go() { return 3; } }
}
"""


@unittest.skipUnless(shutil.which("javac") and shutil.which("java"), "no JDK")
class OracleNesting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="cgb-nesting-"))
        src, classes, oc = cls.tmp / "src/pkg", cls.tmp / "classes", cls.tmp / "oc"
        src.mkdir(parents=True); classes.mkdir(); oc.mkdir()
        (src / "$Dollar$Types.java").write_text(SOURCE, encoding="utf-8")
        (src / "Outer.java").write_text(OUTER, encoding="utf-8")
        subprocess.run(["javac", "-g", "-d", str(classes),
                        str(src / "$Dollar$Types.java"), str(src / "Outer.java")], check=True)
        subprocess.run(["javac", "-d", str(oc), str(ORACLE)], check=True)
        out = subprocess.run(["java", "-cp", str(oc), "ClassfileGroundTruth", "--app", str(classes),
                              "--include-prefix", "pkg", "--mode", "classes"],
                             capture_output=True, text=True, check=True).stdout
        cls.classes = [ln.strip() for ln in out.splitlines() if ln.strip()]
        # the scope the harness actually runs under: gate 4 hands the oracle its top-level types
        only = cls.tmp / "only.txt"
        only.write_text("pkg.$Dollar$Types\npkg.Outer\n", encoding="utf-8")
        out = subprocess.run(["java", "-cp", str(oc), "ClassfileGroundTruth", "--app", str(classes),
                              "--include-prefix", "pkg", "--only-types", str(only), "--mode", "methods"],
                             capture_output=True, text=True, check=True).stdout
        cls.scoped_methods = [ln.strip() for ln in out.splitlines() if ln.strip() and not ln.startswith("#")]

    def test_a_toplevel_class_keeps_the_dollars_in_its_own_name(self):
        self.assertIn("pkg.$Dollar$Types", self.classes)

    def test_no_canonical_name_has_a_doubled_dot(self):
        # `com.google.gson.internal..Gson.Types` was the shape of the defect
        self.assertEqual([c for c in self.classes if ".." in c], [])

    def test_a_member_of_a_dollar_named_class_nests_under_it(self):
        self.assertIn("pkg.$Dollar$Types.Impl", self.classes)

    def test_ordinary_nesting_is_unchanged(self):
        self.assertIn("pkg.Outer", self.classes)
        self.assertIn("pkg.Outer.Inner", self.classes)

    def test_a_local_class_drops_the_counter_the_source_does_not_have(self):
        self.assertIn("pkg.$Dollar$Types.Helper", self.classes)

    def test_an_anonymous_class_is_keyed_by_its_supertype(self):
        anon = [c for c in self.classes if "$anon:" in c]
        self.assertTrue(anon, self.classes)
        self.assertTrue(all(c.startswith("pkg.$Dollar$Types$anon:Runnable") for c in anon), anon)

    def test_only_types_keeps_the_members_of_a_dollar_named_class(self):
        # `topLevelOf` read `$Dollar$Types` as a package and the nested class as the top-level
        # type, so `--only-types` dropped every nested member's methods from the ground truth
        for m in ("pkg.$Dollar$Types.Impl#go()", "pkg.$Dollar$Types.Helper#v()",
                  "pkg.$Dollar$Types#anon()", "pkg.Outer.Inner#go()"):
            self.assertIn(m, self.scoped_methods)


if __name__ == "__main__":
    unittest.main()
