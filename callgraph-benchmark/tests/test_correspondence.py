"""The source side of the universe: which types a file declares (#97).

`$` is a letter to the JLS. A type whose own name carries one — gson's `$Gson$Types` — is
declared by source like any other, and a scanner that cannot read it drops the type out of the
scored universe for every tool at once.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bench"))
from correspondence import top_level, toplevel_types  # noqa: E402
import language as L  # noqa: E402


class ToplevelTypes(unittest.TestCase):
    def test_plain_declarations(self):
        self.assertEqual(toplevel_types("public class Foo {}"), ["Foo"])
        self.assertEqual(toplevel_types("interface Bar {}"), ["Bar"])
        self.assertEqual(toplevel_types("enum Baz { A, B }"), ["Baz"])
        self.assertEqual(toplevel_types("record Pt(int x) {}"), ["Pt"])
        self.assertEqual(toplevel_types("@interface Ann {}"), ["Ann"])

    def test_dollar_in_a_type_name(self):
        # gson's com/google/gson/internal/$Gson$Types.java — 500 lines the bytecode reader
        # sees 666 times, and which `\w` cannot spell
        self.assertEqual(toplevel_types("public final class $Gson$Types {}"), ["$Gson$Types"])

    def test_dollar_in_a_trailing_position(self):
        self.assertEqual(toplevel_types("class Money$ {}"), ["Money$"])

    def test_leading_dollar_alone(self):
        self.assertEqual(toplevel_types("class $ {}"), ["$"])

    def test_nested_types_are_not_toplevel(self):
        src = "class Outer {\n  class $Inner$ {}\n}\n"
        self.assertEqual(toplevel_types(src), ["Outer"])

    def test_a_dollar_type_beside_a_public_one(self):
        # the non-public type is invisible to a name-based rule; content is what decides
        src = "public class Api {}\nfinal class $Gson$Types {}\n"
        self.assertEqual(toplevel_types(src), ["Api", "$Gson$Types"])

    def test_an_identifier_never_starts_with_a_digit(self):
        # `class 1Bad` is not Java; the scanner must not invent a type for it
        self.assertEqual(toplevel_types("class 1Bad {}"), [])

    def test_a_dollar_name_in_a_comment_or_string_is_not_a_declaration(self):
        self.assertEqual(toplevel_types('// class $Ghost$ {}\nclass Real {}'), ["Real"])
        self.assertEqual(toplevel_types('class Real { String s = "class $Ghost$ {}"; }'), ["Real"])


if __name__ == "__main__":
    unittest.main()


class TopLevel(unittest.TestCase):
    """Which top-level type a bytecode class belongs to: the other half of gate 4 (#97)."""

    def test_a_member_of_a_dollar_named_class_belongs_to_it(self):
        # the nested class was taken for the top-level type, so gate 4 reported three gson types
        # "without source" and failed at 3.7%
        self.assertEqual(top_level("com.google.gson.internal.$Gson$Types.GenericArrayTypeImpl"),
                         "com.google.gson.internal.$Gson$Types")

    def test_a_dollar_named_class_is_its_own_top_level(self):
        self.assertEqual(top_level("com.google.gson.internal.$Gson$Types"),
                         "com.google.gson.internal.$Gson$Types")

    def test_an_anonymous_class_of_one(self):
        self.assertEqual(top_level("pkg.$Dollar$Types$anon:Runnable@5"), "pkg.$Dollar$Types")

    def test_ordinary_names_are_unchanged(self):
        self.assertEqual(top_level("pkg.sub.Outer.Inner"), "pkg.sub.Outer")
        self.assertEqual(top_level("pkg.Outer$anon:Runnable@12"), "pkg.Outer")

    def test_a_package_with_a_leading_underscore_is_still_a_package(self):
        self.assertEqual(top_level("pkg._internal.Outer.Inner"), "pkg._internal.Outer")


class TypeSegment(unittest.TestCase):
    def test_segments(self):
        for seg, want in (("Outer", True), ("$Gson$Types", True), ("_Impl", True),
                          ("gson", False), ("_internal", False), ("$", False), ("", False)):
            with self.subTest(seg=seg):
                self.assertEqual(L.is_type_segment(seg), want)

    def test_the_flattened_alias_of_a_nested_dollar_type(self):
        # `pkg.$Dollar$Types.Impl` flattens to `pkg.Impl`, as `pkg.Outer.Inner` does to `pkg.Inner`
        self.assertIn("pkg.Impl", L._java_aliases("pkg.$Dollar$Types.Impl"))
