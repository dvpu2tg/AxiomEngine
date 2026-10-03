#!/usr/bin/env python3
"""Compare this benchmark's CERTAIN edges against a third, independently written class-file reader.

Gate 1 proves the BYTECODE was read correctly, by comparing two readers of the artefact. It cannot
prove the CONVENTIONS were applied correctly, because both readers here share them. A third reader
written by other people — `java/third_party/axiom/ClassFileOracle.java`, from the engine's own
repository — does not share them, which makes it the one check likely to catch a convention this
benchmark got wrong.

It is INFORMATIONAL, not fatal. The two use different naming (it flattens nested types to
`pkg.Simple`; this benchmark keeps the chain, because flattening is lossy — see PROTOCOL §3), so the
comparison projects through that flattening, and a residual disagreement is a finding to investigate
rather than proof that either side is broken. Reporting a number here, every run, is the difference
between a checked claim and a claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def flatten(ref: str) -> str:
    """This benchmark's `pkg.Outer.Inner#m(p)` in the third reader's flattened spelling."""
    t, _, m = ref.partition("#")
    if "$anon:" in t:
        head, _, sup = t.partition("$anon:")
        sup = sup.split("@", 1)[0]
        pkg, _, outer = head.rpartition(".")
        return f"{pkg + '.' if pkg else ''}{outer}$anon:{sup}#{m}"
    parts = t.split(".")
    for i, p in enumerate(parts):
        if p[:1].isupper():
            return ".".join(parts[:i] + parts[-1:]) + "#" + m
    return ref


def sigfree(edge: str) -> str:
    """`A#m(x) -> B#n(y)` without either parameter list — the key two spellings of one edge share."""
    a, _, b = edge.partition(" -> ")
    return a.split("(", 1)[0] + " -> " + b.split("(", 1)[0]


def is_convention(edge: str, excluded: set[str]) -> bool:
    """A one-sided edge the third reader emits BY DESIGN: an implicit `super()` / default
    constructor, or any edge on this benchmark's own §4 exclusion list (which the third reader does
    not apply). Both spellings are flattened before the comparison."""
    if edge in excluded:
        return True
    a, _, b = edge.partition(" -> ")
    return a.endswith("#<init>()") and b.endswith("#<init>()")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", required=True, type=Path)
    ap.add_argument("--third", required=True, type=Path)
    ap.add_argument("--excluded", type=Path, help="the oracle's --mode excluded list (EDGE rows)")
    ap.add_argument("--show", type=int, default=100, help="how many unexplained residuals to print")
    a = ap.parse_args()

    ours: set[str] = set()
    for ln in a.sites.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        d = json.loads(ln)
        for t in d["certain"]:
            ours.add(f"{flatten(d['caller'])} -> {flatten(t)}")
    excluded: set[str] = set()
    if a.excluded and a.excluded.exists():
        for ln in a.excluded.read_text(encoding="utf-8").splitlines():
            kind, _, rest = ln.partition("\t")
            if kind == "EDGE" and " -> " in rest:
                x, _, y = rest.strip().partition(" -> ")
                excluded.add(f"{flatten(x)} -> {flatten(y)}")

    theirs = {ln.strip() for ln in a.third.read_text(encoding="utf-8").splitlines() if ln.strip()}
    only_ours, only_theirs = ours - theirs, theirs - ours
    agree = len(ours & theirs)
    total = max(len(ours | theirs), 1)

    # BUCKETED, NOT COUNTED (#46). The bare percentage was dominated by two readers agreeing about
    # the program and disagreeing about spelling: on rxjava all 566 residuals were notation or a
    # documented exclusion, and the 85 unexplained ones on apache-ant — the number this gate
    # exists to surface — were invisible inside "93.8%".
    #   spelling    — the residual pairs with one on the other side under the signature-free key
    #   convention  — a one-sided edge the third reader emits by design (implicit super(), §4)
    #   unexplained — the rest: a candidate real disagreement, every one printed
    ours_keys = {sigfree(e) for e in only_ours}
    theirs_keys = {sigfree(e) for e in only_theirs}
    spelling_ours = {e for e in only_ours if sigfree(e) in theirs_keys}
    spelling_theirs = {e for e in only_theirs if sigfree(e) in ours_keys}
    conv_theirs = {e for e in only_theirs - spelling_theirs if is_convention(e, excluded)}
    conv_ours = {e for e in only_ours - spelling_ours if e in excluded}
    unexplained_ours = only_ours - spelling_ours - conv_ours
    unexplained_theirs = only_theirs - spelling_theirs - conv_theirs

    print(f"third reader: {agree}/{total} edges agree ({100.0 * agree / total:.1f}%) — raw; "
          f"{len(only_ours)} only here, {len(only_theirs)} only there, of which:")
    print(f"    spelling (same edge, different parameter notation): {len(spelling_ours)} here / {len(spelling_theirs)} there")
    print(f"    convention (implicit super() / §4 exclusion the third reader does not apply): "
          f"{len(conv_ours)} here / {len(conv_theirs)} there")
    print(f"    UNEXPLAINED: {len(unexplained_ours)} only this oracle, {len(unexplained_theirs)} only third reader"
          f"{' — none' if not (unexplained_ours or unexplained_theirs) else ''}")
    for e in sorted(unexplained_theirs)[:a.show]:
        print(f"      only third reader: {e}")
    for e in sorted(unexplained_ours)[:a.show]:
        print(f"      only this oracle:  {e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
