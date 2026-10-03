"""Ground-truth loading: groups, projections, merge artefacts (issues #2, #19, #51)."""
import unittest

from tests._fixtures import Fixture, ref, site, G, S, Tier


class TierMerge(unittest.TestCase):
    def fixture(self) -> Fixture:
        # #51's F2-tier: two Tier-A unique groups that merge at Tier B, one Tier-A ambiguous group
        # that becomes unique at Tier B
        classes = ["app.C", "app.T", "app.U", "app.D", "app.V"]
        methods = ["app.C#run(int)", "app.C#run(long)", "app.T#f()", "app.U#f()", "app.D#g()",
                   "app.V#h(int)", "app.V#h(long)"]
        sites = [site("app.C#run(int)", 1, "f", certain=["app.T#f()"], possible=["app.T#f()"]),
                 site("app.C#run(long)", 2, "f", certain=["app.U#f()"], possible=["app.U#f()"]),
                 site("app.D#g()", 3, "h", certain=["app.V#h(int)", "app.V#h(long)"],
                      possible=["app.V#h(int)", "app.V#h(long)"])]
        return Fixture(sites, classes, methods, [f"{c}\tclass\t" for c in classes])

    def test_merge_artefacts_are_counted_and_the_perfect_answer_is_never_charged(self):
        f = self.fixture()
        at_b = G.groups_at(f.gt, Tier.B)
        self.assertEqual(G.merge_artefacts(at_b, Tier.B), 1)
        perfect = [(ref("app.C#run(int)"), ref("app.T#f()")), (ref("app.C#run(long)"), ref("app.U#f()")),
                   (ref("app.D#g()"), ref("app.V#h(int)")), (ref("app.D#g()"), ref("app.V#h(long)"))]
        sc = f.score(perfect, tier=Tier.B)
        self.assertEqual(sc.ambiguous_merge_artefacts, 1)
        bad = {k: v for k, v in sc.ambiguous_groups.verdicts.items() if k not in (S.EXACT, S.OVER_FAN) and v}
        self.assertEqual(bad, {})
        # D#g merges into one unique group at Tier B and the two declared runnable targets are exact
        self.assertEqual(sc.unique_groups.verdicts[S.EXACT], 1)
        sca = f.score(perfect, tier=Tier.A)
        self.assertEqual(sca.unique_groups.verdicts[S.EXACT], 2)


class ExternalAncestor(unittest.TestCase):
    def test_boundary_sites_do_not_admit_external_spellings(self):
        # a boundary row naming the external declared method is out of the universe, like every boundary row
        f = Fixture([site("p.C#run()", 1, "get", kind="boundary", recv="java.util.Map", ancestors=["p.M#get()"])],
                    ["p.C", "p.M"], ["p.C#run()", "p.M#get()"], ["p.C\tclass\t", "p.M\tclass\t"])
        sc = f.score([(ref("p.C#run()"), ref("java.util.Map#get()"))])
        self.assertEqual(sc.unmapped_rows, 1)


if __name__ == "__main__":
    unittest.main()
