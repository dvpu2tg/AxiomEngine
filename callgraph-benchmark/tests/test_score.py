"""The scorer: verdicts, attribution, corruption handling (PROTOCOL §2, §6; issues #1, #17, #35,
#41, #51, #57)."""
import unittest

from tests._fixtures import Fixture, ref, site, S, Ref, Tier


class GroupVerdict(unittest.TestCase):
    C, P, ANC = {"A#m()"}, {"A#m()"}, {"S#m()"}

    def v(self, answer, certain=None, possible=None, ancestors=None):
        c = self.C if certain is None else certain
        p = self.P if possible is None else possible
        a = self.ANC if ancestors is None else ancestors
        return S._group_verdict(set(answer), c, p, p | c | a)

    def test_the_six_verdicts(self):
        self.assertEqual(self.v([]), S.MISSED)
        self.assertEqual(self.v(["A#m()"]), S.EXACT)
        self.assertEqual(self.v(["A#m()", "S#m()"]), S.OVER_FAN)      # a declaring ancestor beside the answer
        self.assertEqual(self.v(["A#m()", "Z#m()"]), S.POLLUTED)      # something outside the envelope too
        self.assertEqual(self.v(["Z#m()"]), S.WRONG)
        self.assertEqual(self.v(["S#m()"]), S.ANCESTOR)               # only the supertype's declaration

    def test_abstract_declared_target_plus_implementor_is_exact(self):
        # #30: certain = the abstract declaration, possible = the one implementor; naming either or both
        c, p = {"I#m()"}, {"Impl#m()"}
        self.assertEqual(self.v(["I#m()"], c, p, set()), S.EXACT)
        self.assertEqual(self.v(["Impl#m()"], c, p, set()), S.EXACT)
        self.assertEqual(self.v(["I#m()", "Impl#m()"], c, p, set()), S.EXACT)

    def test_two_declared_runnable_targets_are_not_a_fan(self):
        # #51: two invokestatic sites on two overloads merge at Tier B; naming both is two answers
        c = p = {"T#f()", "U#f()"}
        self.assertEqual(self.v(["T#f()", "U#f()"], c, p, set()), S.EXACT)
        # ...but a runnable override beside the declared target is a fan
        self.assertEqual(self.v(["A#m()", "B#m()"], {"A#m()"}, {"A#m()", "B#m()"}, set()), S.OVER_FAN)


class Labels(unittest.TestCase):
    def test_score_labels_are_rounded_and_grouped(self):
        # #41: GitNexus writes `call:0.5700000000000001`
        self.assertEqual(S._label_key("call:0.5700000000000001"), "call:0.57")
        self.assertEqual(S._label_key("exact-match:0.9"), "exact-match:0.90")
        self.assertEqual(S._label_key("INFERRED"), "inferred")   # case-folded (#69)
        self.assertEqual(S._label_key(None), "")


def two_group_fixture() -> Fixture:
    # C#run calls A#m (unique) and B#g where B#g is abstract with one implementor
    classes = ["p.C", "p.A", "p.B", "p.BImpl", "p.Z"]
    methods = ["p.C#run()", "p.A#m()", "p.B#g()", "p.BImpl#g()", "p.Z#m()"]
    heritage = ["p.C\tclass\t", "p.A\tclass\t", "p.B\tabstract\t", "p.BImpl\tclass\tp.B", "p.Z\tclass\t"]
    sites = [site("p.C#run()", 10, "m", certain=["p.A#m()"], possible=["p.A#m()"]),
             site("p.C#run()", 11, "g", certain=["p.B#g()"], possible=["p.BImpl#g()"], ancestors=["p.B#g()"])]
    return Fixture(sites, classes, methods, heritage)


class Attribution(unittest.TestCase):
    def test_per_label_columns_sum_to_the_tool_totals(self):
        f = two_group_fixture()
        edges = [(ref("p.C#run()"), ref("p.A#m()")), (ref("p.C#run()"), ref("p.Z#m()")),
                 (ref("p.C#run()"), ref("p.BImpl#g()"))]
        sc = f.score(edges, labels=["hi", "lo", "hi"])
        self.assertEqual(sc.unique_groups.verdicts[S.POLLUTED], 1)
        self.assertEqual(sc.unique_groups.verdicts[S.EXACT], 1)
        by = sc.by_confidence
        self.assertEqual(by["lo"]["polluted"], 1)      # the row outside the envelope decided that verdict
        self.assertEqual(by["hi"]["exact"], 1)
        self.assertEqual(by["hi"]["polluted"] + by["lo"]["polluted"], 1)
        total = sum(d[k] for d in by.values() for k in ("exact", "over_fan", "polluted", "ancestor", "wrong"))
        self.assertEqual(total, sc.unique_groups.total - sc.unique_groups.verdicts[S.MISSED])


class Corruptions(unittest.TestCase):
    def test_duplicates_score_identically_and_are_stated(self):
        f = two_group_fixture()
        edges = [(ref("p.C#run()"), ref("p.A#m()")), (ref("p.C#run()"), ref("p.BImpl#g()"))]
        once, twice = f.score(edges), f.score(edges + edges)
        self.assertEqual(once.unique_groups.verdicts, twice.unique_groups.verdicts)
        self.assertEqual(once.vs_certain.precision_strict, twice.vs_certain.precision_strict)
        self.assertEqual((once.duplicate_rows, twice.duplicate_rows), (0, 2))

    def test_ghost_caller_on_a_real_type_is_charged_and_on_an_invented_type_is_out_of_scope(self):
        f = two_group_fixture()
        good = [(ref("p.C#run()"), ref("p.A#m()"))]
        real_ghost = f.score(good + [(Ref("nothere", "p.C", ()), ref("p.A#m()"))])
        self.assertLess(real_ghost.vs_possible.precision, 1.0)
        invented = f.score(good + [(Ref("nothere", "p.Ghost__C", ()), ref("p.A#m()"))])
        self.assertEqual(invented.unmapped_rows, 1)
        self.assertEqual(invented.vs_possible.precision, 1.0)   # excluded, and the count says so

    def test_boundary_site_forms_no_group_and_its_implementors_are_accepted(self):
        # the second #30 pass: `map.get` on a JDK interface is a boundary; the app implementor is
        # an accepted answer, never a unique link
        classes, methods = ["p.C", "p.M", "p.A"], ["p.C#run()", "p.M#get()", "p.A#m()"]
        sites = [site("p.C#run()", 3, "get", kind="boundary", recv="java.util.Map",
                      ancestors=["p.M#get()"]),
                 site("p.C#run()", 4, "m", certain=["p.A#m()"], possible=["p.A#m()"])]
        f = Fixture(sites, classes, methods, ["p.C\tclass\t", "p.M\tclass\t", "p.A\tclass\t"])
        self.assertEqual(len(f.gt.groups), 1)
        sc = f.score([(ref("p.C#run()"), ref("p.M#get()")), (ref("p.C#run()"), ref("p.A#m()"))])
        self.assertEqual(sc.vs_possible.precision, 1.0)   # the implementor is accepted, not a false positive
        self.assertEqual(sc.unmapped_rows, 0)
        self.assertEqual(sc.unique_groups.total, 1)
        # and NOT naming the implementor is not a miss
        sc = f.score([(ref("p.C#run()"), ref("p.A#m()"))])
        self.assertEqual(sc.unique_groups.verdicts[S.MISSED], 0)


class CallerPlacement(unittest.TestCase):
    def test_ambiguous_caller_is_placed_by_its_line(self):
        # #17 reopened: two containers named Widget declare run(); the tool reported the line
        classes = ["m.ts", "m.ts:Widget", "m.ts:Inner.Widget", "m.ts:T"]
        methods = ["m.ts:Widget#run()", "m.ts:Inner.Widget#run()", "m.ts:T#target()"]
        heritage = ["m.ts\tcontainer\t", "m.ts:Widget\tclass\t", "m.ts:Inner.Widget\tclass\t", "m.ts:T\tclass\t"]
        sites = [site("m.ts:Widget#run()", 48, "target", certain=["m.ts:T#target()"], possible=["m.ts:T#target()"]),
                 site("m.ts:Inner.Widget#run()", 90, "target", certain=["m.ts:T#target()"], possible=["m.ts:T#target()"])]
        f = Fixture(sites, classes, methods, heritage, lang="typescript")
        placed = f.score([(Ref("run", "m.ts:Widget", ()), ref("m.ts:T#target()"))], files=["m.ts"], lines=[48])
        self.assertEqual(placed.unique_groups.verdicts[S.EXACT], 1)


class Memo(unittest.TestCase):
    def test_truth_derivation_is_cached_per_ground_truth(self):
        # #57: the same ground truth is derived once per tier, not once per score() call
        f = two_group_fixture()
        S._TRUTH_CACHE.clear()
        f.score([]); f.score([]); f.score([], tier=Tier.A)
        self.assertEqual(len([k for k in S._TRUTH_CACHE if k[0] == id(f.gt)]), 2)


if __name__ == "__main__":
    unittest.main()
