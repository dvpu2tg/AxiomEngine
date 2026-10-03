"""Adapter translations (issues #32, #40)."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    sys.path.insert(0, str(path.parent.parent))
    spec.loader.exec_module(mod)   # type: ignore[union-attr]
    return mod


class CodegraphJava(unittest.TestCase):
    def setUp(self):
        import tempfile
        self.m = load(ROOT / "java/adapters/codegraph/adapt.py", "cg_java")
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self._n = 0

    def run_adapter(self, dispatch: bool = False):
        """The tool's schema, written by hand: `calls` and `instantiates` edges, the
        `interface-impl` override index it also files under `calls`, and the `unresolved_refs`
        table it writes for a reference it could not resolve."""
        import contextlib, io, sqlite3, tempfile
        self._n += 1
        tmp = Path(self._dir.name) / str(self._n)
        tmp.mkdir()
        db = tmp / "codegraph.db"
        con = sqlite3.connect(db)
        con.executescript(
            "CREATE TABLE nodes(id TEXT, kind TEXT, name TEXT, qualified_name TEXT,"
            " file_path TEXT, signature TEXT);"
            "CREATE TABLE edges(source TEXT, target TEXT, kind TEXT, line INTEGER, metadata TEXT);"
            "CREATE TABLE unresolved_refs(from_node_id TEXT, reference_name TEXT,"
            " reference_kind TEXT, line INTEGER, file_path TEXT, status TEXT);")
        f = "p/Shapes.java"
        con.executemany("INSERT INTO nodes VALUES (?,?,?,?,?,?)", [
            ("m:go",   "method", "go",   "p::Caller::go",  f, "void ()"),
            ("m:decl", "method", "run",  "p::Iface::run",  f, "void ()"),
            ("m:impl", "method", "run",  "p::Impl::run",   f, "void ()"),
            ("c:impl", "class",  "Impl", "p::Impl",        f, None),
            ("m:ctor", "method", "Impl", "p::Impl::Impl",  f, "void ()"),
            # a TOP-LEVEL record's members are emitted as `function`, not `method`
            ("f:top",  "function", "shout", "p::shout",     f, "String ()"),
        ])
        con.executemany("INSERT INTO edges VALUES (?,?,?,?,?)", [
            # a call on the interface-typed receiver: the tool names the DECLARATION
            ("m:go", "m:decl", "calls", 7, '{"confidence":0.9,"resolvedBy":"instance-method"}'),
            ("m:go", "c:impl", "instantiates", 6, '{"confidence":0.9,"resolvedBy":"exact-match"}'),
            # the override index, filed under `calls`, declaration -> implementation (#40)
            ("m:decl", "m:impl", "calls", 3,
             '{"synthesizedBy":"interface-impl","via":"run","registeredAt":"p/Shapes.java:3"}'),
            # a METHOD REFERENCE: the tool files its resolved answer under `references`
            ("m:go", "m:impl", "references", 9,
             '{"confidence":0.95,"resolvedBy":"function-ref","refKind":"function_ref","fnRef":true}'),
            # a CONSTRUCTOR reference resolves to the TYPE
            ("m:go", "c:impl", "references", 10,
             '{"confidence":0.95,"resolvedBy":"function-ref","fnRef":true}'),
            # a plain type reference is not a call, even on the `references` kind
            ("m:go", "c:impl", "references", 11, '{"confidence":0.9,"resolvedBy":"exact-match"}'),
            # a caller the tool emitted as a `function` node
            ("f:top", "m:impl", "calls", 20, '{"confidence":0.9,"resolvedBy":"exact-match"}'),
        ])
        con.execute("INSERT INTO unresolved_refs VALUES (?,?,?,?,?,?)",
                    ("m:go", "x.run", "calls", 12, f, "failed"))
        # a reference the tool could not resolve that is NOT a call: must not become a call gap
        con.execute("INSERT INTO unresolved_refs VALUES (?,?,?,?,?,?)",
                    ("m:go", "Override", "decorates", 5, f, "failed"))
        con.commit(); con.close()
        from model import read_edges
        edges = tmp / "cg.jsonl"
        argv = sys.argv
        sys.argv = ["adapt.py", "--db", str(db), "--subject", "t", "--edges", str(edges)]
        if dispatch:
            sys.argv.append("--dispatch")
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                load(ROOT / "java/adapters/codegraph/adapt.py", "cg_java_run").main()
        finally:
            sys.argv = argv
        return read_edges(edges)

    def test_anonymous_class_notation(self):
        self.assertEqual(self.m.anon_notation("torture.F08Nesting.viaAnonymous.<Callable$anon@36>"),
                         "torture.F08Nesting$anon:Callable@36")
        self.assertEqual(self.m.anon_notation("A.m.<I$anon@1>.n.<J$anon@2>"), "A$anon:I@1$anon:J@2")
        self.assertEqual(self.m.anon_notation("plain.Type"), "plain.Type")

    def test_synthesized_rows_are_not_calls(self):
        """#40: a `synthesizedBy: interface-impl` link without `resolvedBy` runs DECLARATION ->
        implementation at the declaration's line. It is an override index, not a call, and must
        never be scored as one."""
        out = self.run_adapter()
        self.assertEqual(out.meta["synthesized_rows_skipped"], 1)
        self.assertNotIn(("p.Iface", "run", "p.Impl", "run"),
                         {(e.caller.type, e.caller.name, e.callee.type, e.callee.name)
                          for e in out.edges})

    def test_declared_gap_is_unknown_not_missed(self):
        """The tool's own `unresolved_refs` rows (`reference_kind='calls'`) are it saying "there
        is a call here I could not resolve" — PROTOCOL section 6 `unknown`, not `missed`. They
        add no edge, so no precision or recall figure can move."""
        base, out = self.run_adapter(), self.run_adapter()
        sites = out.meta.get("unresolved_sites") or []
        self.assertEqual([(s[0]["type"], s[0]["name"], s[1]) for s in sites],
                         [("p.Caller", "go", 12)])
        self.assertEqual(len(base.edges), len(out.edges))      # declaring a gap emits nothing

    def test_a_method_reference_is_a_call(self):
        """A `references` edge carrying `fnRef` is the tool's resolved answer for `Impl::run`, and
        javac emits an invokedynamic the class-file oracle scores. Reading only `calls` discarded
        it: 89 rows on apache-ant, 89 on spring-boot."""
        out = self.run_adapter()
        by_line = {e.line: e for e in out.edges}
        self.assertIn(9, by_line)
        self.assertEqual((by_line[9].callee.type, by_line[9].callee.name), ("p.Impl", "run"))
        self.assertEqual((by_line[10].callee.type, by_line[10].callee.name), ("p.Impl", "<init>"))
        self.assertNotIn(11, by_line)                 # a plain type reference stays out
        self.assertEqual(out.meta["function_ref_rows"], 2)

    def test_a_function_node_can_be_a_caller(self):
        """A top-level `record` emits its members as `function`; the TypeScript adapter has always
        accepted both kinds and the Java one accepted `method` alone."""
        out = self.run_adapter()
        by_line = {e.line: e for e in out.edges}
        self.assertIn(20, by_line)
        self.assertEqual(by_line[20].caller.name, "shout")

    def test_override_index_expands_only_under_dispatch(self):
        """The index is the tool's answer to what a call can REACH. PROTOCOL section 5.1 reads a
        multi-candidate answer as fan-out — but as a separate row, so the unprompted row above is
        byte-identical."""
        plain, disp = self.run_adapter(), self.run_adapter(dispatch=True)
        self.assertEqual(plain.meta["dispatch_expanded_sites"], 0)
        self.assertEqual(disp.meta["dispatch_expanded_sites"], 1)
        # the unprompted row names the declaration alone; the dispatch row adds the implementation
        self.assertEqual({(e.callee.type, e.callee.name) for e in plain.edges if e.line == 7},
                         {("p.Iface", "run")})
        self.assertEqual({(e.callee.type, e.callee.name) for e in disp.edges if e.line == 7},
                         {("p.Iface", "run"), ("p.Impl", "run")})
        self.assertEqual([e.confidence for e in disp.edges
                          if e.line == 7 and e.callee.type == "p.Impl"], ["interface-impl"])
        # and the index itself is still not a call in either row
        self.assertEqual(plain.meta["synthesized_rows_skipped"],
                         disp.meta["synthesized_rows_skipped"])


class CodegraphTypeScript(unittest.TestCase):
    def run_adapter(self):
        """A class field initializer's call, a static one, and a function identifier passed as an
        argument, on the tool's own schema."""
        import contextlib, io, sqlite3, tempfile
        from model import read_edges
        d = tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        tmp = Path(d.name)
        root = tmp / "src"; (root / "p").mkdir(parents=True)
        db = tmp / "codegraph.db"
        con = sqlite3.connect(db)
        con.executescript(
            "CREATE TABLE nodes(id TEXT, kind TEXT, name TEXT, qualified_name TEXT,"
            " file_path TEXT, signature TEXT, is_static INTEGER);"
            "CREATE TABLE edges(source TEXT, target TEXT, kind TEXT, line INTEGER, metadata TEXT);"
            "CREATE TABLE unresolved_refs(from_node_id TEXT, reference_name TEXT,"
            " reference_kind TEXT, line INTEGER, file_path TEXT, status TEXT);")
        con.executemany("INSERT INTO nodes VALUES (?,?,?,?,?,?,?)", [
            ("f1", "function", "helper", "helper",      "p/b.ts", "(n: number): string", 0),
            ("m1", "method",   "run",    "App::run",    "p/a.ts", "(): void", 0),
            ("p1", "property", "field",  "App::field",  "p/a.ts", "field", 0),
            ("p2", "property", "shared", "App::shared", "p/a.ts", "shared", 1),
        ])
        ok = '{"confidence":0.9,"resolvedBy":"exact-match"}'
        con.executemany("INSERT INTO edges VALUES (?,?,?,?,?)", [
            ("m1", "f1", "calls", 7, ok),
            ("p1", "f1", "calls", 3, ok),     # a class field initializer
            ("p2", "f1", "calls", 4, ok),     # a static one
            ("m1", "f1", "references", 9,
             '{"confidence":0.95,"resolvedBy":"function-ref","fnRef":true}'),
        ])
        con.execute("INSERT INTO unresolved_refs VALUES (?,?,?,?,?,?)",
                    ("p1", "x.mystery", "calls", 5, "p/a.ts", "failed"))
        con.commit(); con.close()
        edges = tmp / "cg.jsonl"
        argv = sys.argv
        sys.argv = ["adapt.py", "--db", str(db), "--root", str(root), "--subject", "t",
                    "--edges", str(edges)]
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                load(ROOT / "typescript/adapters/codegraph/adapt.py", "cg_ts_run").main()
        finally:
            sys.argv = argv
        return read_edges(edges)

    def test_a_field_initializer_call_runs_in_the_constructor(self):
        """PROTOCOL §3.1. The tool attributes the call to the FIELD and names the owner; the owner
        stays the declared name, which `bench/language.py` maps onto its module."""
        out = self.run_adapter()
        by_line = {e.line: e for e in out.edges}
        self.assertEqual((by_line[3].caller.type, by_line[3].caller.name), ("App", "constructor"))
        self.assertEqual((by_line[4].caller.type, by_line[4].caller.name), ("App", "<clinit>"))

    def test_a_property_sourced_gap_is_placed_the_same_way(self):
        out = self.run_adapter()
        (caller, line, _f), = out.meta["unresolved_sites"]
        self.assertEqual((caller["type"], caller["name"], line), ("App", "constructor", 5))

    def test_a_function_reference_is_not_a_call_in_typescript(self):
        """The reverse of the Java rule: passing a function identifier is not a call in TypeScript
        and the checker records no site, so the tool's `fnRef` row is a false positive."""
        out = self.run_adapter()
        self.assertEqual(sorted(e.line for e in out.edges), [3, 4, 7])

    def test_signature_reader(self):
        c = load(ROOT / "typescript/adapters/_tscommon.py", "tscommon")
        self.assertEqual(c.ts_params("(a: T, b?: U<V, W>): R"), ("T", "U<V,W>"))   # whitespace inside generics is normalised away
        self.assertEqual(c.ts_params("(): void"), ())
        self.assertEqual(c.ts_params("(x, y = 3): number"), ("any", "any"))
        self.assertIsNone(c.ts_params(None))


class AxiomJava(unittest.TestCase):
    """The Java axiom adapter on a synthetic IR (pass 8, found on gson): every edge carries the
    call's line, and a field initializer's call is charged to `<clinit>` / `<init>`."""

    def run_adapter(self, tmp: Path):
        import contextlib
        import io
        from model import read_edges
        ir, out = tmp / "ir", tmp / "out"
        ir.mkdir(); out.mkdir()
        (ir / "all-methods.csv").write_text(
            "methodRegistryUniqueHash\townerQualifiedName\tname\tmethodKind\tfilePath\n"
            "M1\tp.A\tcaller\tMETHOD\tp/A.java\n"
            "M2\tp.B\thelper\tMETHOD\tp/B.java\n"
            "M3\tp.B\tB\tCONSTRUCTOR\tp/B.java\n", encoding="utf-8")
        (ir / "all-method-parameters.csv").write_text(
            "methodRegistryLinkHash\tposition\tparameterBaseType\tparameterTypeName\tisVarArgs\n", encoding="utf-8")
        (ir / "all-fields.csv").write_text(
            "fieldRegistryUniqueHash\townerQualifiedName\tfieldModifier\n"
            "FIELD_REGISTRY_S\tp.A\tPRIVATE STATIC FINAL\n"
            "FIELD_REGISTRY_I\tp.A\tPRIVATE FINAL\n", encoding="utf-8")
        (ir / "all-expressions.csv").write_text(
            "expressionUniqueHash\tstartLine\texpressionOwnerHash\n"
            "E1\t17\tM1\n"
            "E2\t5\tFIELD_REGISTRY_S\n"
            "E3\t9\tFIELD_REGISTRY_I\n", encoding="utf-8")
        (out / "call-chain-edges.csv").write_text(
            "E1\tM1\t-\tM2\tdirect\tknown_edge\tcall\n"
            "E2\tTYPE_REGISTRY_A\t-\tM3\tdirect\tknown_edge\tnew\n"
            "E3\tTYPE_REGISTRY_A\t-\tM2\tdirect\tknown_edge\tcall\n", encoding="utf-8")
        edges = tmp / "axiom.jsonl"
        argv = sys.argv
        sys.argv = ["adapt.py", "--ir", str(ir), "--out", str(out), "--subject", "t", "--edges", str(edges),
                    "--build", "source only"]
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                load(ROOT / "java/adapters/axiom/adapt.py", "axiom_java").main()
        finally:
            sys.argv = argv
        return read_edges(edges)

    def test_every_edge_carries_the_call_line(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            out = self.run_adapter(Path(d))
        by_line = {e.line: e for e in out.edges}
        self.assertEqual(sorted(by_line), [5, 9, 17])
        self.assertEqual((by_line[17].caller.type, by_line[17].caller.name), ("p.A", "caller"))

    def test_field_initializer_calls_are_charged_to_clinit_or_init(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            out = self.run_adapter(Path(d))
        by_line = {e.line: e for e in out.edges}
        self.assertEqual((by_line[5].caller.type, by_line[5].caller.name, by_line[5].caller.params), ("p.A", "<clinit>", ()))
        self.assertEqual((by_line[9].caller.type, by_line[9].caller.name, by_line[9].caller.params), ("p.A", "<init>", None))
        self.assertEqual(by_line[5].callee.name, "<init>")   # the constructor row's KIND decides its name
        self.assertEqual(out.meta["dropped_in_adapter"], 0)


class ModuleLevelCaller(unittest.TestCase):
    """#99: a module is a caller, and its id has two components, not three.

    The oracle names a call written at a module's top level `<module>`, owned by the module
    (typescript/oracle/ts-ground-truth.ts). The id pattern wanted `<label>:<file>:<symbol>`,
    so a two-component module id never matched, parse_id returned None, and the row was
    dropped by the `if s is None or t is None: continue` in main() without a counter.
    """

    def setUp(self):
        self.m = load(ROOT / "typescript/adapters/gitnexus/adapt.py", "gnx_ts")
        self.m.ROOT = "/tmp/subject"

    def test_a_module_id_is_the_module_caller(self):
        got = self.m.parse_id("File:lib/application.ts")
        self.assertIsNotNone(got, "a module id must parse; before #99 this was None")
        _, file, r = got
        self.assertEqual((r.name, r.type), ("<module>", "lib/application.ts"))
        self.assertEqual(file, "lib/application.ts")

    def test_the_root_prefix_is_stripped_like_any_other_symbol(self):
        _, _, r = self.m.parse_id("File:/tmp/subject/src/index.ts")
        self.assertEqual(r.type, "src/index.ts")

    def test_a_non_source_file_is_still_not_a_symbol(self):
        # a module container is only a container when it is a module: package.json is not
        self.assertIsNone(self.m.parse_id("File:package.json"))
        self.assertIsNone(self.m.parse_id("File:README.md"))

    def test_named_symbols_are_unchanged(self):
        _, _, meth = self.m.parse_id("Method:lib/application.ts:Application.bootstrap#1")
        self.assertEqual((meth.name, meth.type), ("bootstrap", "Application"))
        _, _, fn = self.m.parse_id("Function:lib/utils/fs.ts:getCommonDirectory")
        self.assertEqual((fn.name, fn.type), ("getCommonDirectory", "lib/utils/fs.ts"))


class CodeReviewGraph(unittest.TestCase):
    """The target node's own file travels as `callee_file` (#36 reopened): the tool links
    `downstream.onComplete()` to the same-named class in the CALLER's file, and that is what the
    row must say, not what the scorer reads from the call site."""

    def run_adapter(self, tmp: Path, lang: str, dispatch: bool = False):
        import contextlib
        import io
        import sqlite3
        from model import read_edges
        root = tmp / "src"; root.mkdir()
        db = tmp / "graph.db"
        con = sqlite3.connect(db)
        con.executescript(
            "CREATE TABLE nodes(kind TEXT, name TEXT, qualified_name TEXT, file_path TEXT, parent_name TEXT, params TEXT);"
            "CREATE TABLE edges(kind TEXT, source_qualified TEXT, target_qualified TEXT, file_path TEXT, line INTEGER, confidence_tier TEXT, extra TEXT);")
        ext = "java" if lang == "java" else "ts"
        a, b = f"{root}/p/A.{ext}", f"{root}/p/B.{ext}"
        con.executemany("INSERT INTO nodes VALUES (?,?,?,?,?,?)", [
            ("Function", "caller", f"{a}::Node.caller", a, "Node", "()"),
            ("Function", "visit", f"{b}::Node.visit", b, "Node", "()"),
            ("Class", "Node", f"{b}::Node", b, None, None),
            ("Test", "testIt", f"{a}::NodeTest.testIt", a, "NodeTest", "()"),      # a @Test method (#91)
        ])
        con.executemany("INSERT INTO edges VALUES (?,?,?,?,?,?,?)", [
            ("CALLS", f"{a}::Node.caller", f"{b}::Node.visit", a, 7, "EXTRACTED", "{}"),
            ("CALLS", f"{a}::Node.caller", f"{b}::Node", a, 8, "EXTRACTED", "{}"),
            ("CALLS", f"{a}::NodeTest.testIt", f"{b}::Node.visit", a, 9, "EXTRACTED", "{}"),
            # an annotated method the tool wrote NO node for, but whose calls it recorded (#91)
            ("CALLS", f"{a}::Node.overridden", f"{b}::Node.visit", a, 10, "EXTRACTED", "{}"),
            # a bare target the tool DECLARED it could not resolve: `unknown`, never `missed`
            ("CALLS", f"{a}::Node.caller", "visit", a, 11, "EXTRACTED",
             '{"bare_call_target": "visit", "receiver": "n"}'),
            # the same call with the tool's OWN candidate set: fan-out under --dispatch only
            ("CALLS", f"{a}::Node.caller", "walk", a, 12, "EXTRACTED",
             '{"bare_call_target": "walk", "ambiguous_target_count": 1,'
             f' "ambiguous_targets": ["{b}::Node.visit"]}}'),
        ])
        con.commit(); con.close()
        edges = tmp / "crg.jsonl"
        argv = sys.argv
        sys.argv = ["adapt.py", "--db", str(db), "--root", str(root), "--subject", "t", "--edges", str(edges)]
        if dispatch:
            sys.argv.append("--dispatch")
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                load(ROOT / f"{lang}/adapters/code_review_graph/adapt.py", f"crg_{lang}").main()
        finally:
            sys.argv = argv
        return read_edges(edges)

    def test_callee_file_is_the_target_nodes_file(self):
        import tempfile
        for lang, ext in (("java", "java"), ("typescript", "ts")):
            with tempfile.TemporaryDirectory() as d:
                out = self.run_adapter(Path(d), lang)
            by_line = {e.line: e for e in out.edges}
            self.assertEqual(sorted(by_line), [7, 8, 9, 10, 11, 12])
            self.assertEqual((by_line[9].caller.type, by_line[9].caller.name), ("NodeTest", "testIt"))   # a Test node is a method
            self.assertEqual((by_line[10].caller.type, by_line[10].caller.name), ("Node", "overridden"))  # read from the spelling
            self.assertEqual(by_line[7].file, f"p/A.{ext}")            # the call site
            self.assertEqual(by_line[7].callee_file, f"p/B.{ext}")     # the target's declaration
            self.assertEqual(by_line[8].callee_file, f"p/B.{ext}")     # a constructor call, too

    def test_declared_gap_is_unknown_not_missed(self):
        """A bare target the tool DECLARED it could not resolve travels as `meta.unresolved_sites`,
        so PROTOCOL §6 reads the group `unknown` (a gap a consumer can route around) rather than
        `missed` (a silent one). It adds no edge and so moves no precision or recall figure."""
        import tempfile
        for lang in ("java", "typescript"):
            with tempfile.TemporaryDirectory() as d:
                out = self.run_adapter(Path(d), lang)
            sites = out.meta.get("unresolved_sites") or []
            self.assertEqual(sorted(s[1] for s in sites), [11, 12])
            self.assertEqual(sites[0][0]["name"], "caller")
            # the unprompted row is UNCHANGED: still the bare name the tool spelled, with no
            # owner — unspellable at Tier B, exactly as before. Declaring the gap adds no edge.
            at12 = [e for e in out.edges if e.line == 12]
            self.assertEqual([(e.callee.type, e.callee.name) for e in at12], [(None, "walk")])
            self.assertEqual(out.meta["fanned_rows"], 0)

    def test_candidate_set_is_fanned_out_only_under_dispatch(self):
        """`ambiguous_targets` is the tool's own answer to what the call could reach. PROTOCOL §5.1
        reads a multi-candidate row as one edge per candidate — but as a SEPARATE row, so the
        unprompted answer above is unchanged."""
        import tempfile
        for lang in ("java", "typescript"):
            with tempfile.TemporaryDirectory() as d:
                out = self.run_adapter(Path(d), lang, dispatch=True)
            at12 = [e for e in out.edges if e.line == 12]
            self.assertEqual([(e.callee.type, e.callee.name) for e in at12], [("Node", "visit")])
            self.assertEqual(at12[0].confidence, "ambiguous_targets")
            # a declared gap with NO candidate set is still declared, not fanned
            self.assertEqual([s[1] for s in (out.meta.get("unresolved_sites") or [])], [11])


if __name__ == "__main__":
    unittest.main()


class GitNexusJava(unittest.TestCase):
    """#100: the id's `#<arity>[~T1,T2,…]` suffix carries an erased parameter list on an
    overloaded member, and an arity alone is not one."""

    def setUp(self):
        self.m = load(ROOT / "java/adapters/gitnexus/adapt.py", "gnx_java")

    def test_parameter_list_is_read(self):
        _label, file, ref = self.m.parse_id(
            "Method:src/main/java/p/DoubleMetaphone.java:DoubleMetaphone.contains#4~String,int,int,String")
        self.assertEqual(file, "src/main/java/p/DoubleMetaphone.java")
        self.assertEqual((ref.type, ref.name), ("DoubleMetaphone", "contains"))
        self.assertEqual(ref.params, ("String", "int", "int", "String"))

    def test_arity_alone_is_not_a_parameter_list(self):
        # a count is not a signature: inventing ("?", "?") would be an overload answer the tool
        # never gave, and the resolver would erase and compare it like any other
        _label, _file, ref = self.m.parse_id("Method:p/Box.java:Box.get#2")
        self.assertIsNone(ref.params)
        self.assertEqual((ref.type, ref.name), ("Box", "get"))

    def test_constructor_keeps_its_parameters(self):
        _label, _file, ref = self.m.parse_id(
            "Constructor:p/ColognePhonetic.java:CologneBuffer.CologneBuffer#1~char[]")
        self.assertEqual((ref.type, ref.name), ("CologneBuffer", "<init>"))
        self.assertEqual(ref.params, ("char[]",))

    def test_a_type_target_is_a_construction_with_no_parameters(self):
        _label, _file, ref = self.m.parse_id("Class:p/Helper.java:Helper")
        self.assertEqual((ref.type, ref.name), ("Helper", "<init>"))
        self.assertIsNone(ref.params)

    def test_parse_params(self):
        self.assertIsNone(self.m.parse_params("0"))
        self.assertIsNone(self.m.parse_params(""))
        self.assertIsNone(self.m.parse_params("2~"))
        self.assertEqual(self.m.parse_params("1~char[]"), ("char[]",))
        self.assertEqual(self.m.parse_params("2~String, int"), ("String", "int"))


class EdgeFileProvenance(unittest.TestCase):
    """#104: the edge file is hashed into the manifest, so `_meta.source` must not carry the
    checkout's absolute path — two checkouts of an identical run must write identical bytes."""

    def write(self, source) -> bytes:
        import tempfile
        from model import Tier, ToolOutput, write_edges
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "e.jsonl"
            write_edges(f, ToolOutput(tool="t", subject="s", declared_tier=Tier.B,
                                      meta={"source": source, "version": "t 1"}))
            return f.read_bytes()

    def meta(self, source) -> dict:
        import json
        return json.loads(self.write(source).splitlines()[0])["_meta"]

    def test_a_source_inside_the_repository_is_written_relative_to_it(self):
        src = ROOT / ".work" / "typescript" / "torture" / "gfy" / "src" / "graphify-out" / "graph.json"
        self.assertEqual(self.meta(str(src))["source"], ".work/typescript/torture/gfy/src/graphify-out/graph.json")

    def test_absolute_and_relative_spellings_write_the_same_bytes(self):
        import os
        rel = ".work/java/torture/crg/data/graph.db"
        cwd = os.getcwd()
        os.chdir(ROOT)
        try:
            self.assertEqual(self.write(rel), self.write(str(ROOT / rel)))
            self.assertEqual(self.write(rel), self.write(Path(rel)))
        finally:
            os.chdir(cwd)

    def test_a_source_outside_the_repository_is_kept_as_given(self):
        self.assertEqual(self.meta("/elsewhere/graph.db")["source"], "/elsewhere/graph.db")

    def test_a_row_without_a_source_is_unchanged(self):
        import tempfile
        from model import Tier, ToolOutput, write_edges
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "e.jsonl"
            write_edges(f, ToolOutput(tool="t", subject="s", declared_tier=Tier.B, meta={"rows": 0}))
            self.assertNotIn("source", f.read_text().splitlines()[0])


class ManifestSourceIsPortable(unittest.TestCase):
    """#104: `_meta.source` is the first line of the edge file, and that file is what
    `run.input_sha256["edges/<tool>"]` hashes. Recorded absolutely, the hash is a statement about
    WHERE THE CHECKOUT LIVES: the same tool, on the same subject, run from a different directory
    produces a different manifest entry with an identical graph — so the manifest reports drift
    where there is none, and would equally hide real drift behind an expected difference.

    The test is run over two checkouts, because that is the only way to see it. Each is a skeleton
    — `bench/model.py` and the adapter, at their real relative paths — and the input is staged at
    the SAME relative path in both. Everything about the two runs is identical except the absolute
    prefix, so any difference in the emitted bytes is that prefix and nothing else.
    """

    GRAPH = {
        "nodes": [
            {"id": "t_impl", "label": "Impl", "source_file": "p/Shapes.java"},
            {"id": "m_go", "label": ".go()", "source_file": "p/Shapes.java",
             "source_location": "line 7"},
            {"id": "m_run", "label": ".run()", "source_file": "p/Shapes.java",
             "source_location": "line 3"},
        ],
        "links": [
            {"source": "t_impl", "target": "m_go", "relation": "method"},
            {"source": "t_impl", "target": "m_run", "relation": "method"},
            {"source": "m_go", "target": "m_run", "relation": "calls",
             "source_file": "p/Shapes.java", "source_location": "line 7",
             "confidence": "EXTRACTED"},
        ],
    }

    # Both graphify adapters take the same `--graph`, and both spelled it absolutely. `_tscommon`
    # is the TypeScript adapters' shared helper, imported from one directory up.
    ADAPTERS = ("java/adapters/graphify/adapt.py", "typescript/adapters/graphify/adapt.py")
    EXTRA = ("typescript/adapters/_tscommon.py",)
    # where a real run stages the tool's output, relative to the repository root
    STAGED = ".work/java/torture/gfy/src/graphify-out/graph.json"

    def setUp(self):
        import tempfile
        self._dir = tempfile.TemporaryDirectory(prefix="cgb-104-")
        self.addCleanup(self._dir.cleanup)

    def emit(self, adapter: str, checkout: str) -> bytes:
        """Build a checkout at `checkout`, stage the graph at the fixed relative path, and run the
        adapter there as the harness runs it — a subprocess, so the checkout's own `bench/model.py`
        is the one that is imported."""
        import json, shutil, subprocess
        root = Path(self._dir.name) / checkout
        for rel in ("bench/model.py", adapter) + self.EXTRA:
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, dst)
        graph = root / self.STAGED
        graph.parent.mkdir(parents=True, exist_ok=True)
        graph.write_text(json.dumps(self.GRAPH), encoding="utf-8")
        edges = root / "out.jsonl"
        subprocess.run(
            [sys.executable, str(root / adapter), "--graph", str(graph), "--subject", "torture",
             "--meta", "graphifyy 0.9.58", "--edges", str(edges)],
            check=True, capture_output=True)
        return edges.read_bytes()

    def test_the_same_graph_hashes_the_same_from_two_checkouts(self):
        import hashlib
        for adapter in self.ADAPTERS:
            with self.subTest(adapter=adapter):
                a = self.emit(adapter, "home-runner-work-bench")
                b = self.emit(adapter, "b")
                self.assertEqual(hashlib.sha256(a).hexdigest(), hashlib.sha256(b).hexdigest(),
                                 "the manifest entry moved with the checkout location")

    def test_the_provenance_is_kept_not_dropped(self):
        """Stability is not bought by deleting the field: the recorded path still names the input,
        repository-relative and with `/` separators on every platform."""
        import json
        for adapter in self.ADAPTERS:
            with self.subTest(adapter=adapter):
                meta = json.loads(self.emit(adapter, "kept").splitlines()[0])["_meta"]
                self.assertEqual(meta["source"], self.STAGED)


class RepoRelative(unittest.TestCase):
    """The one helper every adapter now spells `_meta.source` through (#104)."""

    def setUp(self):
        from model import repo_relative
        self.f = repo_relative

    def test_a_path_inside_the_repository_is_relative_and_posix(self):
        self.assertEqual(self.f(ROOT / "bench" / "model.py"), "bench/model.py")

    def test_a_path_outside_the_repository_stays_absolute(self):
        """Not a relative spelling that would resolve somewhere else: an input the harness does not
        own is stated plainly, and the manifest is allowed to say it is not portable."""
        outside = Path(ROOT.anchor) / "elsewhere" / "graph.json"
        self.assertEqual(self.f(outside), str(outside))
