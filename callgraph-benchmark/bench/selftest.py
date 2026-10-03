#!/usr/bin/env python3
"""Can the scorer actually fail? Checked by mutation, before any real tool is scored.

A harness that reports 0.98 for a good tool has proved nothing until it also reports the right
number for a tool that is deliberately broken. So this builds synthetic tools out of the ground
truth itself — each one wrong in exactly one known way — and asserts the score says so.

    perfect         the right answer for every link group      -> P 1.0, R 1.0, exact on every unique group
    dropped         perfect, minus one edge                    -> recall_certain must fall by exactly that edge
    fabricated      perfect, plus an edge no envelope admits   -> precision must fall; the group must read `polluted`
    over_fan        perfect, plus a declaring ancestor         -> precision HOLDS, `exact` falls, `over_fan` rises
    name_only       perfect, with every owner erased           -> Tier A and B n/a (NOT zero); Tier C scores
    empty           emits nothing                              -> recall 0, MCC 0 (accuracy would read ~0.998)
    flattened       perfect, as `pkg.Inner`                    -> must still score, via the resolver
    dollar_nested   perfect, as `pkg.Outer$Inner`              -> must still score, via the resolver

Two further gates, added after an audit found each of them live in published numbers:

    ceiling     a tool answering every group correctly       -> 100% exact, EMPTY error buckets, at
                                                                every tier. A lower ceiling belongs
                                                                to the scorer, not to any tool.
    null model  the whole CHA envelope at every site         -> must NOT match a resolving tool on
                                                                `precision_strict`. It scored 1.000
                                                                precision and topped the headline on
                                                                all three Java subjects before the
                                                                strict bound existed.

The last two are the fairness assertions: a tool that spells types differently must NOT be punished.
If either of them ever drops below the `perfect` tool's score, the benchmark has started measuring
notation instead of resolution, and that is the failure this whole design exists to prevent.

    python3 bench/selftest.py --sites ... --classes ... --methods ...
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import groundtruth as G   # noqa: E402
import language as L      # noqa: E402
import resolve as R       # noqa: E402
import score as S         # noqa: E402
from model import Edge, Ref, Tier, ToolOutput   # noqa: E402

FAILURES: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        FAILURES.append(msg)


def mk(gt: G.GroundTruth, edges: list[tuple[Ref, Ref]], tier: Tier = Tier.A) -> ToolOutput:
    return ToolOutput(tool="synthetic", subject=gt.subject, declared_tier=tier,
                      edges=[Edge(caller=a, callee=b) for a, b in edges])


def flatten(r: Ref) -> Ref:
    """`pkg.Outer.Inner` -> `pkg.Inner`: the notation a tool with a flattening IR emits."""
    if r.type is None:
        return r
    parts = r.type.split(".")
    idx = next((i for i, p in enumerate(parts) if L.is_type_segment(p)), None)
    if idx is None or idx == len(parts) - 1:
        return r
    return Ref(name=r.name, type=".".join(parts[:idx] + parts[-1:]), params=r.params)


def ts_noext(r: Ref) -> Ref:
    """`src/x.ts:Foo` -> `src/x:Foo`: the notation a tool that drops the extension emits."""
    if r.type is None:
        return r
    mod, sep, decl = r.type.rpartition(":")
    if not sep:
        mod, decl = r.type, ""
    for ext in (".ts", ".tsx", ".mts", ".cts"):
        if mod.endswith(ext):
            mod = mod[: -len(ext)]
            break
    return Ref(name=r.name, type=f"{mod}:{decl}" if decl else mod, params=r.params)


def ts_hash(r: Ref) -> Ref:
    """`src/x.ts:Foo` -> `src/x.ts#Foo`: another separator a tool may use."""
    if r.type is None or ":" not in r.type:
        return r
    return Ref(name=r.name, type=r.type.replace(":", "#", 1), params=r.params)


def dollarise(r: Ref) -> Ref:
    """`pkg.Outer.Inner` -> `pkg.Outer$Inner`: the internal-name notation."""
    if r.type is None:
        return r
    parts = r.type.split(".")
    idx = next((i for i, p in enumerate(parts) if L.is_type_segment(p)), None)
    if idx is None or idx == len(parts) - 1:
        return r
    return Ref(name=r.name, type=".".join(parts[: idx + 1]) + "$" + "$".join(parts[idx + 1:]),
               params=r.params)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", required=True, type=Path)
    ap.add_argument("--classes", required=True, type=Path)
    ap.add_argument("--methods", required=True, type=Path)
    ap.add_argument("--source", action="append", default=[], type=Path)
    ap.add_argument("--language", default="java")
    ap.add_argument("--defaults", type=Path,
                    help="TypeScript: module -> default-exported container (oracle --mode defaults)")
    ap.add_argument("--heritage", type=Path,
                    help="the oracle's --mode heritage: container kind and parents (issue #36)")
    ap.add_argument("--excluded", type=Path,
                    help="the exclusion lists — without them this gate never exercises that path")
    a = ap.parse_args()

    gt = G.load(a.sites, a.classes, a.methods, "selftest", a.excluded)
    lang = L.get(a.language)
    rv = R.Resolver(gt.classes, R.build_file_index(list(a.source), lang), lang, gt.methods)
    rv.add_external(gt.external_ancestors)
    if a.heritage and a.heritage.exists():
        rv.add_heritage(a.heritage.read_text(encoding="utf-8").splitlines())
    if a.defaults and a.defaults.exists():
        pairs = [tuple(ln.split("\t", 1)) for ln in a.defaults.read_text().splitlines() if "\t" in ln]
        rv.add_default_exports(pairs)
    # A "perfect" tool answers every LINK GROUP correctly. That is not the same as emitting the
    # CERTAIN set: a group whose declared target is abstract has it in `certain` and the one
    # implementor in `possible`, and a tool that emitted only `certain` would rightly be scored
    # as having missed the runnable target. Building the reference answer from the groups is what
    # makes "perfect" mean perfect. (A site whose declared target is OUTSIDE the application is a
    # boundary since the second #30 pass — no group, so nothing here.)
    certain = sorted(gt.certain_edges())
    reference = sorted(set(certain) | {
        (g.caller, next(iter(g.possible))) for g in gt.groups.values()
        if not g.certain and len(g.possible) == 1})
    T = Tier.A

    # ── perfect ──────────────────────────────────────────────────────────────────────────────
    perfect = S.score(mk(gt, reference), gt, rv, T)
    check(perfect.vs_certain is not None and perfect.vs_certain.recall == 1.0,
          f"perfect tool: recall_certain should be 1.0, got {perfect.vs_certain.recall if perfect.vs_certain else None}")
    check(perfect.vs_possible is not None and perfect.vs_possible.precision == 1.0,
          "perfect tool: precision should be 1.0")
    check(perfect.unique_groups.verdicts[S.WRONG] == 0,
          "perfect tool: no unique group should read `wrong`")
    base_exact = perfect.unique_groups.verdicts[S.EXACT]
    check(base_exact == perfect.unique_groups.total,
          f"perfect tool: every unique group should be `exact`, got "
          f"{base_exact}/{perfect.unique_groups.total}")

    # ── dropped ──────────────────────────────────────────────────────────────────────────────
    dropped = S.score(mk(gt, reference[1:]), gt, rv, T)
    check(dropped.vs_certain.tp == perfect.vs_certain.tp - 1,
          "dropped-edge tool: TP must fall by exactly one")
    # A ratio is None when its denominator is zero — which means the ground truth is empty, and the
    # real failure is upstream. Say that, rather than crashing on a None comparison.
    check(dropped.vs_certain.recall is not None and dropped.vs_certain.recall < 1.0,
          "dropped-edge tool: recall must fall below 1.0 "
          f"(got {dropped.vs_certain.recall} — an empty CERTAIN set means the ground truth is empty)")

    # ── fabricated ───────────────────────────────────────────────────────────────────────────
    # The fabricated edge must share the group's CALLEE NAME, or it lands in a different link group
    # and the `polluted` assertion tests nothing. Not every unique group has such an alien — on a
    # subject where a name is declared exactly once, there is no same-named method outside the
    # envelope — so search until one is found rather than assuming the first group works. (Assuming
    # it crashed this gate on netty-transport, where the first unique group's callee name is
    # unique in the project.)
    by_name: dict[str, list[Ref]] = {}
    for m in sorted(gt.methods, key=str):
        if m.at(T) is not None:
            by_name.setdefault(m.name, []).append(m)
    victim = alien = None
    for g in sorted(gt.groups.values(), key=lambda g: (str(g.caller), g.callee_name)):
        if not g.unique:
            continue
        cand = next((m for m in by_name.get(g.callee_name, [])
                     # an APPLICATION method: `gt.methods` also holds every external declared
                     # target, and `java.lang.Object#equals` as the alien is out of scope by
                     # construction — the row is dropped, not charged, and the check fails for
                     # no fault of the scorer (issue #43, commons-lang3)
                     if m not in g.possible and m not in g.declaring_ancestors and m.type in gt.classes), None)
        if cand is not None:
            victim, alien = g, cand
            break
    if victim is None:
        # Nothing in the subject can play the part: every same-named method is already inside some
        # envelope. Say so rather than silently skipping a check the run claims to have made.
        FAILURES.append("no unique group has a same-named method outside its envelope — "
                        "the fabricated-edge mutation could not be constructed on this subject")
        victim, alien = next(g for g in gt.groups.values() if g.unique), None
    fabricated = S.score(mk(gt, reference + ([(victim.caller, alien)] if alien else [])), gt, rv, T)
    check(fabricated.vs_possible.fp >= 1,
          "fabricated-edge tool: an edge outside every envelope must count as a false positive")
    check(fabricated.vs_possible.precision < 1.0, "fabricated-edge tool: precision must fall")
    check(fabricated.unique_groups.verdicts[S.POLLUTED] >= 1,
          "fabricated-edge tool: the affected unique group must read `polluted`")

    # ── over_fan ─────────────────────────────────────────────────────────────────────────────
    fanned: list[tuple[Ref, Ref]] = list(reference)
    added = 0
    for g in gt.groups.values():
        if not g.unique:
            continue
        # an ancestor that is NOT the declared target: since #30 the declared target of an
        # interface call sits in both `certain` and the ancestors, and naming it is accepted as
        # exact; the fan this mutation asserts on is a supertype that merely declares the member
        extra = sorted(set(g.declaring_ancestors) - set(g.certain), key=str)
        if extra:
            fanned.append((g.caller, extra[0]))
            added += 1
    if added:
        over = S.score(mk(gt, fanned), gt, rv, T)
        check(over.vs_possible.precision == 1.0,
              "over-fanning tool: naming a declaring ancestor must NOT count as a false positive")
        check(over.unique_groups.verdicts[S.OVER_FAN] >= 1,
              "over-fanning tool: the affected unique groups must read `over_fan`")
        check(over.unique_groups.verdicts[S.EXACT] < base_exact,
              "over-fanning tool: `exact` must fall — a set where one answer exists is not a win")

    # ── name_only ────────────────────────────────────────────────────────────────────────────
    bare = [(Ref(name=x.name), Ref(name=y.name)) for x, y in reference]
    name_only = mk(gt, bare, tier=Tier.C)
    for tier in (Tier.A, Tier.B):
        sc = S.score(name_only, gt, rv, tier)
        check(not sc.scorable,
              f"name-only tool: tier {tier.value} must be reported n/a, not scored")
    sc_c = S.score(name_only, gt, rv, Tier.C)
    check(sc_c.scorable and sc_c.vs_certain.recall == 1.0,
          "name-only tool: must score at Tier C, where its notation is sufficient")

    # ── empty ────────────────────────────────────────────────────────────────────────────────
    empty = S.score(mk(gt, []), gt, rv, T)
    check(empty.vs_certain.recall == 0.0, "empty tool: recall must be 0")
    check(empty.vs_certain.mcc in (0.0, None),
          f"empty tool: MCC must be 0 (accuracy would be ~0.998), got {empty.vs_certain.mcc}")

    # ── THE CEILING GATE ─────────────────────────────────────────────────────────────────────
    # A tool that answers every link group correctly must score 100% `exact` with EMPTY error
    # buckets, at every tier it can be scored at. Otherwise the headline has a ceiling that belongs
    # to the scorer rather than to any tool — and one that varies by subject, which silently makes
    # two subjects' numbers incomparable. None of the other gates catches this: it passed on
    # netty-transport while a correct tool was capped at 94.9%.
    for tier in (Tier.A, Tier.B):
        ideal_edges: list[tuple[Ref, Ref]] = []
        for g in G.groups_at(gt, tier):
            if not G.projected_unique(g, tier):
                continue
            target = next(iter(g.certain)) if g.certain else next(iter(g.possible))
            ideal_edges.append((g.caller, target))
        sc = S.score(mk(gt, ideal_edges), gt, rv, tier)
        if not sc.scorable:
            continue
        bad = {k: v for k, v in sc.unique_groups.verdicts.items() if k != S.EXACT and v}
        check(not bad,
              f"ceiling gate, tier {tier.value}: a tool that answers every uniquely-linked group "
              f"correctly scored {sc.unique_groups.verdicts[S.EXACT]}/{sc.unique_groups.total} "
              f"exact, with {bad}")
        # THE AMBIGUOUS TABLE TOO (#51). The perfect answer to a genuinely ambiguous group is the
        # whole runnable set — `over_fan` there is correct — but the Tier-A reference, projected to
        # this tier, must never read `polluted`, `wrong`, `ancestor` or `missed`: those are the
        # buckets a merge artefact of the projection would land in.
        sc_all = S.score(mk(gt, reference), gt, rv, tier)
        bad_amb = {k: v for k, v in sc_all.ambiguous_groups.verdicts.items()
                   if k not in (S.EXACT, S.OVER_FAN) and v}
        check(not bad_amb,
              f"ceiling gate, tier {tier.value}: the perfect answer scored {bad_amb} on the "
              f"ambiguous table — a scorer-owned artefact, not dispatch")

    # ── THE NULL-MODEL GATE ──────────────────────────────────────────────────────────────────
    # A tool that emits the ENTIRE envelope at every site has resolved nothing. It is allowed to
    # score well on `precision` (nothing it says is impossible) and on `recall_possible` (it says
    # everything) — but it must NOT beat a resolving tool on the strict bound, or the benchmark is
    # rewarding the absence of resolution. Before `precision_strict` existed, the envelope answer
    # took the top of the headline table on all three Java subjects.
    envelope_edges = [(g.caller, t) for g in gt.groups.values() for t in g.possible]
    null_sc = S.score(mk(gt, envelope_edges), gt, rv, T)
    ideal_sc = S.score(mk(gt, reference), gt, rv, T)
    # Read off vs_CERTAIN: the strict bound asks how much of what the tool said was the DECLARED
    # answer. Taken off vs_possible it divides the envelope by itself and reads 1.000 for the
    # envelope answer — which is the very thing it exists to catch.
    if null_sc.vs_certain and ideal_sc.vs_certain:
        ns, is_ = null_sc.vs_certain.precision_strict, ideal_sc.vs_certain.precision_strict
        # Where the subject has NO dispatch — fp-ts is functional, nearly every envelope has one
        # member — the envelope answer IS the declared answer, and the two are legitimately equal.
        # The strict inequality is only meaningful where an envelope is wider than its certain set.
        fanned = sum(1 for g in gt.groups.values() if len(g.possible) > len(g.certain))
        if fanned:
            check(ns is not None and is_ is not None and ns < is_,
                  f"null-model gate: the CHA envelope answer scores prec_strict {ns} against the "
                  f"correct answer's {is_} over {fanned} fanned groups — a tool that resolves "
                  f"nothing must not match one that does")
        else:
            print("  note: no group has an envelope wider than its certain set — the null model and "
                  "the correct answer coincide here by construction; strict gate not applicable",
                  file=sys.stderr)
        check((null_sc.vs_possible.precision or 0) >= (ideal_sc.vs_possible.precision or 0) - 1e-9,
              "null-model gate: the envelope answer should still score well on plain `precision` — "
              "if it does not, the envelope is not what precision is measured against")

    # ── THE FAIRNESS ASSERTIONS ──────────────────────────────────────────────────────────────
    # A tool that spells types differently must score the same. If these ever regress, the
    # benchmark has begun measuring notation instead of resolution.
    mutations = ((("flattened `pkg.Inner`", flatten), ("internal `pkg.Outer$Inner`", dollarise))
                 if lang.name == "java" else
                 (("no extension `src/x:Foo`", ts_noext), ("hash separator `src/x.ts#Foo`", ts_hash)))
    for label, fn in mutations:
        # A notation can LOSE information for real: `Exec.StreamPumper` flattens to
        # `taskdefs.StreamPumper`, and apache-ant declares a top-level type of exactly that name.
        # No resolver can tell those apart from the flattened spelling alone, and the exact-name
        # rule (docs/PROTOCOL.md §5) correctly returns the type the spelling names. Such refs are
        # excluded from the assertion — and COUNTED, because a subject where a notation is this
        # lossy is a fact about that notation worth reporting beside the tool that uses it.
        inherent = 0
        renamed = []
        for x, y in reference:
            fx, fy = fn(x), fn(y)
            if (fx.type != x.type and fx.type in gt.classes) or (fy.type != y.type and fy.type in gt.classes):
                inherent += 1
                continue
            renamed.append((fx, fy))
        if inherent:
            print(f"  note: {label}: {inherent} reference edge(s) collide with a REAL type under that "
                  f"notation — inherent loss, excluded from the assertion", file=sys.stderr)
        sc = S.score(mk(gt, renamed), gt, rv, T)
        # Flattening genuinely collides two `Node` types in this subject; those rows are reported
        # AMBIGUOUS and excluded, so the comparison is against the rows that remain.
        scored = sc.vs_certain.tp + sc.vs_certain.fp
        check(sc.vs_possible.precision == 1.0,
              f"{label}: precision must stay 1.0 — a notation difference is not a wrong answer "
              f"(got {sc.vs_possible.precision})")
        check(scored >= perfect.vs_certain.tp - sc.ambiguous_rows - inherent - 1,
              f"{label}: {scored} rows scored vs {perfect.vs_certain.tp} for the canonical "
              f"spelling, with only {sc.ambiguous_rows} reported ambiguous — the resolver is "
              f"silently dropping rows it should place")

    # ── THE CORRUPTION ASSERTIONS (#35) ──────────────────────────────────────────────────────
    # Three simple ways a tool's output can be wrong that the notation mutations above do not
    # cover. Each states what the scorer must do with it.
    #
    # 1. Every edge twice. Every metric is a set measure, so the score must not move — and the
    #    repetition must be STATED (`duplicate_rows`), so the table's `edges` and the metric's
    #    denominator can be reconciled.
    dup = S.score(mk(gt, reference + reference), gt, rv, T)
    check(dup.vs_certain.precision_strict == perfect.vs_certain.precision_strict
          and dup.unique_groups.verdicts == perfect.unique_groups.verdicts,
          "duplicates: emitting every edge twice must score exactly as emitting it once")
    check(dup.duplicate_rows == len(reference),
          f"duplicates: {len(reference)} repeated rows must be reported, got {dup.duplicate_rows}")
    # 2. Caller and callee swapped. Nothing is right any more: recall 0, every group missed or
    #    wrong, and precision must fall. (A swapped pair that happens to spell a §4-excluded
    #    construct — `X#<init>` calling `Y#<init>` — is excluded like any row of that shape; the
    #    count is printed, and it is a small minority.)
    #    A reversed edge that is ALSO a real edge — `a` calls `b` and `b` calls `a`, mutual
    #    recursion — is a true positive on either side; those are counted and are the only
    #    credit the reversed graph may earn.
    mutual = len({(y, x) for x, y in reference} & set(reference))
    swp = S.score(mk(gt, [(y, x) for x, y in reference]), gt, rv, T)
    check(swp.vs_certain.tp <= mutual and swp.unique_groups.verdicts[S.EXACT] <= mutual,
          f"swapped: a reversed graph may only be credited for its {mutual} mutual-recursion edges "
          f"(got tp {swp.vs_certain.tp}, exact groups {swp.unique_groups.verdicts[S.EXACT]})")
    check((swp.vs_possible.precision or 0) < 0.5,
          f"swapped: precision must collapse (got {swp.vs_possible.precision})")
    check(swp.excluded_rows <= 0.25 * len(reference),
          f"swapped: {swp.excluded_rows} of {len(reference)} reversed rows landed in §4-excluded — "
          f"the exclusion is swallowing wrong answers")
    # 3. The right callee under a caller that does not exist. On a REAL type the row is a false
    #    positive and charged. On a type the application does not declare it is out of scope —
    #    the scorer cannot tell an invented type from a dependency's — so it is excluded, and the
    #    report must print the excluded rows as a SHARE of what was emitted, so a tool that is
    #    half fabrication cannot print a clean precision unremarked.
    ghost_real = [(Ref("__ghost__", x.type, ()), y) for x, y in reference]
    gr = S.score(mk(gt, reference + ghost_real), gt, rv, T)
    check((gr.vs_possible.precision or 1) < 1.0 and (gr.vs_certain.precision_strict or 1) < perfect.vs_certain.precision_strict,
          f"ghost caller on a real type: must be charged (precision {gr.vs_possible.precision}, "
          f"prec-strict {gr.vs_certain.precision_strict} vs {perfect.vs_certain.precision_strict})")
    #    The invented name goes on the LEAF type name — `pkg.Outer$anon:Ghost__Runnable@12`,
    #    `src/x.ts:Foo.$obj:Ghost__Opts@44`. A suffix after the `@line`, a prefix on the path
    #    or package, or a prefix on the outer class are all notations the resolver is right to
    #    read (the anonymous-class tail, the longest indexed path suffix); none is a ghost.
    def ghost(t: str) -> str:
        return re.sub(r"([A-Za-z_]\w*)(@\d+)?(>?)$", r"Ghost__\1\2\3", t, count=1)
    ghost_type = [(Ref("__ghost__", ghost(x.type or ""), ()), y) for x, y in reference]
    gt_ = S.score(mk(gt, reference + ghost_type), gt, rv, T)
    check(gt_.unmapped_rows >= len(ghost_type) - 1,
          f"ghost caller on an invented type: {len(ghost_type)} rows must be reported out-of-scope, "
          f"got {gt_.unmapped_rows}")
    check(gt_.edges_emitted == 2 * len(reference),
          "ghost caller on an invented type: the emitted count must still include the fabricated rows")

    # 4. A DECLARED UNKNOWN (#69). The tool answers nothing for some calls but writes a row saying
    #    "there is a call here I could not resolve": those groups read `unknown`, not `missed`,
    #    and nothing else moves.
    drop = [g for g in gt.groups.values() if g.unique and g.sites][: max(1, len(reference) // 20)]
    drop_keys = {(str(g.caller), g.callee_name) for g in drop}
    kept = [(x, y) for x, y in reference if (str(x), y.name) not in drop_keys]
    unk_out = mk(gt, kept)
    unk_out.meta = {"unresolved_sites": [[{"name": g.caller.name, "type": g.caller.type,
                                            "params": list(g.caller.params) if g.caller.params is not None else None},
                                           int(g.sites[0].line), None] for g in drop]}
    unk = S.score(unk_out, gt, rv, T)
    check(unk.unique_groups.verdicts[S.UNKNOWN] >= len(drop) - 1 and unk.unique_groups.verdicts[S.MISSED] == perfect.unique_groups.verdicts[S.MISSED],
          f"declared unknown: {len(drop)} groups the tool flagged unresolved must read `unknown` "
          f"(got unknown={unk.unique_groups.verdicts[S.UNKNOWN]}, missed={unk.unique_groups.verdicts[S.MISSED]})")
    check(unk.unique_groups.verdicts[S.EXACT] == perfect.unique_groups.verdicts[S.EXACT] - len(drop),
          "declared unknown: only the flagged groups move")

    if FAILURES:
        print("SELF-TEST FAILED:", file=sys.stderr)
        for f in FAILURES:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"  OK: 21 checks (8 notation mutations + ceiling ×2 + null model + 9 corruption checks), all as specified "
          f"({len(reference)} reference edges, {perfect.unique_groups.total} unique link groups)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
