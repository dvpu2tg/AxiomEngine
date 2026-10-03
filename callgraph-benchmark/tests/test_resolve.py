"""The resolver: reading a tool's notation without guessing (PROTOCOL §5.1)."""
import unittest

from tests._fixtures import Fixture, ref, site, R, Ref


def java_fixture() -> Fixture:
    # p.Base declares tag(); p.Square extends Base and overrides nothing but describe();
    # p.A.Node and p.B.Node are two nested `Node`s, only p.B.Node declares visit();
    # p.Iface is an interface with member run(), implemented by p.Impl
    classes = ["p.Base", "p.Square", "p.A", "p.A.Node", "p.B", "p.B.Node", "p.Iface", "p.Impl", "p.Outer"]
    methods = ["p.Base#tag()", "p.Base#<init>()", "p.Square#describe()", "p.Square#<init>()",
               "p.A.Node#walk()", "p.B.Node#visit()", "p.Iface#run()", "p.Impl#run()", "p.Impl#<init>()",
               "p.Outer#constructor()", "p.Outer#<init>()"]
    heritage = ["p.Base\tclass\t", "p.Square\tclass\tp.Base", "p.A\tclass\t", "p.A.Node\tclass\t",
                "p.B\tclass\t", "p.B.Node\tclass\t", "p.Iface\tinterface\t", "p.Impl\tclass\tp.Iface",
                "p.Outer\tclass\t"]
    sites = [site("p.Square#describe()", 5, "tag", certain=["p.Base#tag()"], possible=["p.Base#tag()"])]
    return Fixture(sites, classes, methods, heritage)


class ResolveJava(unittest.TestCase):
    def setUp(self):
        self.f = java_fixture()

    def test_unique_simple_name_resolves(self):
        r = self.f.rv.resolve(ref("Square#describe()"))
        self.assertIs(r.verdict, R.Verdict.RESOLVED)
        self.assertEqual(r.ref.type, "p.Square")

    def test_flattened_nested_name_is_ambiguous_until_the_method_name_splits_it(self):
        # #36: `p.Node#visit` — two nested Nodes, only one declares visit
        r = self.f.rv.resolve(ref("p.Node#visit()"))
        self.assertIs(r.verdict, R.Verdict.RESOLVED)
        self.assertEqual(r.ref.type, "p.B.Node")
        # a name neither declares stays ambiguous, whatever file the tool reports
        r = self.f.rv.resolve(Ref(name="frob", type="p.Node"), "p/A.java")
        self.assertIs(r.verdict, R.Verdict.AMBIGUOUS)

    def test_foreign_package_is_never_read_by_simple_name(self):
        # #37: java.nio.file.Path must not become the application's Path
        f = Fixture([], ["org.apache.tools.ant.types.Path"], ["org.apache.tools.ant.types.Path#list()"])
        self.assertIs(f.rv.resolve(ref("java.nio.file.Path#list()")).verdict, R.Verdict.UNKNOWN)
        self.assertIs(f.rv.resolve(ref("types.Path#list()")).verdict, R.Verdict.RESOLVED)

    def test_inherited_member_callee_resolves_to_the_declaring_ancestor(self):
        # `square.tag()` spelled on the receiver's type is Base#tag by JVMS §5.4.3.3
        r = self.f.rv.resolve(ref("p.Square#tag()"), callee=True)
        self.assertEqual((r.verdict, r.ref.type), (R.Verdict.RESOLVED, "p.Base"))
        # a CALLER is never re-placed: a method body is in the class that declares it
        r = self.f.rv.resolve(ref("p.Square#tag()"))
        self.assertEqual(r.ref.type, "p.Square")

    def test_interface_member_is_a_valid_callee_but_never_a_caller(self):
        # #17 reopened: nested placement of `p.Outer#run` must not land on an interface as a CALLER;
        # as a CALLEE an interface method is a perfectly good declared target
        f = Fixture([], ["p.Outer", "p.Outer.Iface", "p.Outer.Impl"],
                    ["p.Outer#<init>()", "p.Outer.Iface#run()", "p.Outer.Impl#run()"],
                    ["p.Outer\tclass\t", "p.Outer.Iface\tinterface\t", "p.Outer.Impl\tclass\tp.Outer.Iface"])
        r = f.rv.resolve(ref("p.Outer#run()"))
        self.assertEqual((r.verdict, r.ref.type), (R.Verdict.RESOLVED, "p.Outer.Impl"))
        r = f.rv.resolve(ref("p.Outer.Iface#run()"), callee=True)
        self.assertEqual((r.verdict, r.ref.type), (R.Verdict.RESOLVED, "p.Outer.Iface"))

    def test_constructor_is_a_legal_java_method_name(self):
        # #44: guava's TypeToken#constructor(Constructor) is a method, not <init>
        r = self.f.rv.resolve(ref("p.Outer#constructor()"))
        self.assertEqual(r.ref.name, "constructor")
        self.assertEqual(self.f.rv.resolve(ref("p.Outer#<init>()")).ref.name, "<init>")
        self.assertEqual(self.f.rv.resolve(ref("p.Outer#Outer()")).ref.name, "<init>")   # javac's own spelling

    def test_call_site_file_narrows_an_ambiguous_callee_only_after_the_name_split(self):
        # a flattened nested type with two candidates that BOTH declare the member: the call site's
        # file decides; a spelling that matches nothing is not turned into something by the file
        f = Fixture([], ["q.Io", "q.Io.Worker", "q.Comp", "q.Comp.Worker"],
                    ["q.Io.Worker#<init>()", "q.Comp.Worker#<init>()", "q.Io#make()"],
                    ["q.Io\tclass\t", "q.Io.Worker\tclass\t", "q.Comp\tclass\t", "q.Comp.Worker\tclass\t"])
        f.rv.file_index = R.build_file_index([], f.lang)
        f.rv.file_index.update({"q/Io.java": "q", "q/Comp.java": "q"})
        r = f.rv.resolve(ref("q.Worker#<init>()"), None, callee=True, context_file="q/Io.java")
        self.assertEqual((r.verdict, r.ref.type), (R.Verdict.RESOLVED, "q.Io.Worker"))
        r = f.rv.resolve(ref("q.Worker#<init>()"), None, callee=True, context_file="q/Elsewhere.java")
        self.assertIs(r.verdict, R.Verdict.AMBIGUOUS)
        r = f.rv.resolve(ref("q.Nothing#<init>()"), None, callee=True, context_file="q/Io.java")
        self.assertIs(r.verdict, R.Verdict.UNKNOWN)

    def test_name_split_counts_an_inherited_member_as_declared(self):
        # #36 reopened, J5/T4: p.A.Node inherits visit() from p.Base, p.B.Node declares it; from a
        # third file the bare `Node#visit` denotes either — AMBIGUOUS, not B.Node
        f = Fixture([], ["p.Base", "p.A", "p.A.Node", "p.B", "p.B.Node", "p.C"],
                    ["p.Base#visit()", "p.A.Node#other()", "p.B.Node#visit()", "p.C#run()"],
                    ["p.Base\tclass\t", "p.A.Node\tclass\tp.Base", "p.B.Node\tclass\t", "p.C\tclass\t"])
        f.rv.file_index = R.build_file_index([], f.lang)
        f.rv.file_index.update({"p/A.java": "p", "p/B.java": "p", "p/C.java": "p"})
        r = f.rv.resolve(Ref(name="visit", type="Node"), None, callee=True, context_file="p/C.java")
        self.assertIs(r.verdict, R.Verdict.AMBIGUOUS)
        self.assertEqual(set(r.candidates), {"p.A.Node", "p.B.Node"})
        # the same in TypeScript: a.ts:Lexer inherits next() from d.ts:BaseLexer
        t = Fixture([], ["src/a.ts:Lexer", "src/b.ts:Lexer", "src/d.ts:BaseLexer", "src/c.ts"],
                    ["src/a.ts:Lexer#peek()", "src/b.ts:Lexer#next()", "src/d.ts:BaseLexer#next()", "src/c.ts#main()"],
                    ["src/a.ts:Lexer\tclass\tsrc/d.ts:BaseLexer", "src/b.ts:Lexer\tclass\t",
                     "src/d.ts:BaseLexer\tclass\t", "src/c.ts\tcontainer\t"], lang="typescript")
        r = t.rv.resolve(Ref(name="next", type="Lexer"), None, callee=True, context_file="src/c.ts")
        self.assertIs(r.verdict, R.Verdict.AMBIGUOUS)
        # and with the callee's OWN file the row is decided, then read through the inheritance
        r = t.rv.resolve(Ref(name="next", type="Lexer"), "src/a.ts", callee=True, context_file="src/c.ts")
        self.assertEqual((r.verdict, r.ref.type), (R.Verdict.RESOLVED, "src/d.ts:BaseLexer"))

    def test_call_site_file_never_narrows_a_typescript_callee(self):
        # #36 reopened: `import { Worker as BW } from "./b"` — the file says nothing about which
        # module's Worker a flattened name means
        f = Fixture([], ["src/a.ts", "src/a.ts:Worker", "src/b.ts", "src/b.ts:Worker"],
                    ["src/a.ts:Worker#run()", "src/b.ts:Worker#run()"],
                    ["src/a.ts\tcontainer\t", "src/a.ts:Worker\tclass\t", "src/b.ts\tcontainer\t", "src/b.ts:Worker\tclass\t"],
                    lang="typescript")
        r = f.rv.resolve(Ref(name="run", type="Worker"), None, callee=True, context_file="src/a.ts")
        self.assertIs(r.verdict, R.Verdict.AMBIGUOUS)

    def test_typescript_parameter_whitespace_is_not_a_difference(self):
        # #68 §1: the oracle strips spaces from parameter types; so must the tool side
        f = Fixture([], ["m.ts"], ["m.ts#asArray(T|ReadonlyArray<T>)"], ["m.ts\tcontainer\t"], lang="typescript")
        r = f.rv.resolve(Ref(name="asArray", type="m.ts", params=("T | ReadonlyArray<T>",)))
        self.assertEqual(r.ref.params, ("T|ReadonlyArray<T>",))

    def test_owner_less_callee_resolves_only_when_one_container_declares_it(self):
        r = self.f.rv.resolve(Ref(name="describe"), callee=True)
        self.assertEqual((r.verdict, r.ref.type), (R.Verdict.RESOLVED, "p.Square"))
        r = self.f.rv.resolve(Ref(name="run"), callee=True)          # Iface and Impl both declare run
        self.assertIsNone(r.ref.type)
        r = self.f.rv.resolve(Ref(name="describe"))                  # a caller: never re-placed
        self.assertIsNone(r.ref.type)

    def test_memo_is_invalidated_when_tables_change(self):
        r1 = self.f.rv.resolve(ref("p.Impl#run()"), callee=True)
        self.f.rv.add_heritage(["p.Impl\tclass\tp.Iface"])
        r2 = self.f.rv.resolve(ref("p.Impl#run()"), callee=True)
        self.assertEqual(r1.ref, r2.ref)


class ResolveCompilerNames(unittest.TestCase):
    """#96: the name javac writes into the class file is a notation, and must be read.

    The oracle keys an anonymous class by its supertype and strips a local class's counter,
    because javac and ecj number them differently. A tool that reads the class files spells
    them `Outer$1` / `Outer$1Local` / `Enum$1`, and before #96 every such row was dropped.
    """

    def setUp(self):
        classes = ["p.Outer", "p.Outer$anon:Runnable@12", "p.Outer.Local", "p.Op"]
        methods = ["p.Outer#go()", "p.Outer$anon:Runnable@12#run()", "p.Outer.Local#work()",
                   "p.Op#apply()"]
        heritage = ["p.Outer\tclass\t", "p.Outer$anon:Runnable@12\tclass\t",
                    "p.Outer.Local\tclass\t", "p.Op\tenum\t"]
        self.f = Fixture([site("p.Outer#go()", 12, "run",
                               certain=["p.Outer$anon:Runnable@12#run()"],
                               possible=["p.Outer$anon:Runnable@12#run()"])],
                         classes, methods, heritage)
        self.rows = ["p.Outer$1\tp.Outer$anon:Runnable@12",
                     "p.Outer$1Local\tp.Outer.Local",
                     "p.Op$1\tp.Op"]

    def test_compiler_names_are_unreadable_until_the_map_is_supplied(self):
        # the pre-#96 behaviour, pinned so the fix cannot be mistaken for something the
        # alias table already did
        self.assertIs(self.f.rv.resolve(ref("p.Outer$1#run()")).verdict, R.Verdict.UNKNOWN)

    def test_anonymous_local_and_enum_body_names_resolve(self):
        self.f.rv.add_compiler_names(self.rows)
        for spelling, want in (("p.Outer$1#run()", "p.Outer$anon:Runnable@12"),
                               ("Outer$1#run()", "p.Outer$anon:Runnable@12"),
                               ("p.Outer$1Local#work()", "p.Outer.Local"),
                               ("p.Op$1#apply()", "p.Op")):
            with self.subTest(spelling):
                r = self.f.rv.resolve(ref(spelling))
                self.assertIs(r.verdict, R.Verdict.RESOLVED)
                self.assertEqual(r.ref.type, want)

    def test_an_alias_that_already_resolves_is_not_overwritten(self):
        # the safety property the fix rests on: this can widen what is readable and can never
        # redirect a spelling that already meant something
        before = dict(self.f.rv._by_alias)
        self.f.rv.add_compiler_names(self.rows + ["p.Outer\tp.Op"])
        self.assertEqual(self.f.rv._by_alias["p.Outer"], before["p.Outer"])
        self.assertEqual(self.f.rv.resolve(ref("p.Outer#go()")).ref.type, "p.Outer")

    def test_a_row_naming_an_unknown_canonical_is_ignored(self):
        self.f.rv.add_compiler_names(["p.Ghost$1\tp.NotAClass"])
        self.assertIs(self.f.rv.resolve(ref("p.Ghost$1#run()")).verdict, R.Verdict.UNKNOWN)


class ResolveTypeScript(unittest.TestCase):
    def test_path_is_not_a_basename(self):
        # a tool reporting `dtslint/Array.ts` has named a file outside the universe
        f = Fixture([], ["src/Array.ts", "src/Array.ts:Foo"], ["src/Array.ts#map()", "src/Array.ts:Foo#m()"],
                    ["src/Array.ts\tcontainer\t", "src/Array.ts:Foo\tclass\t"], lang="typescript")
        self.assertIs(f.rv.resolve(ref("dtslint/Array.ts#map()")).verdict, R.Verdict.UNKNOWN)
        self.assertIs(f.rv.resolve(ref("src/Array.ts#map()")).verdict, R.Verdict.RESOLVED)

    def test_merged_class_and_interface_is_a_class(self):
        # ioredis: `class Redis` + `interface Redis`; the heritage row says class, so it can be a caller
        f = Fixture([], ["Redis.ts", "Redis.ts:Redis"], ["Redis.ts:Redis#connect()", "Redis.ts:Redis#once()"],
                    ["Redis.ts\tcontainer\t", "Redis.ts:Redis\tclass\t"], lang="typescript")
        r = f.rv.resolve(ref("Redis.ts#connect()"))
        self.assertEqual((r.verdict, r.ref.type), (R.Verdict.RESOLVED, "Redis.ts:Redis"))

    def test_ctor_alias_keeps_ctor_and_new_as_ordinary_names(self):
        f = Fixture([], ["m.ts"], ["m.ts#ctor()", "m.ts#new()"], ["m.ts\tcontainer\t"], lang="typescript")
        self.assertEqual(f.rv.resolve(ref("m.ts#ctor()")).ref.name, "ctor")


if __name__ == "__main__":
    unittest.main()
