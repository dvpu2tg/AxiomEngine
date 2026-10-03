#!/usr/bin/env python3
"""The CHA null model — a permanent floor row, scored exactly like a tool and ranked as none.

It emits, at every call site, the ENTIRE dispatch envelope the ground truth admits. It performs no
resolution whatsoever: it is what "I don't know, here is everything it could be" looks like when
written down as a call graph.

WHY IT IS IN EVERY TABLE
------------------------
Because for a while it would have WON one. Before `precision_strict` existed, this answer scored
precision 1.000, recall_possible ~1.000, F1 and MCC at ceiling, and took the top of the
uniquely-linked column on all three Java subjects — while resolving nothing. Every metric the
benchmark published was maximised by refusing to answer.

A floor that is only asserted in a test can drift out of the published tables. This one is rendered
beside the tools, in italics, never ranked: a reader can see at a glance how much of a tool's score
is resolution and how much is available for free.

It is given the STRONGEST possible input — the oracle's own envelope — on purpose. It should be
beaten on sharpness, not on coverage.

    python3 bench/null_model.py --sites <gt.sites.jsonl> --subject <name> --edges <dest.jsonl>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from model import Edge, Ref, Tier, ToolOutput, write_edges   # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", required=True, type=Path)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--edges", required=True, type=Path)
    ap.add_argument("--label", default="cha-null")
    # THE OTHER END OF THE BRACKET (issue #6). `--ideal` emits the correct answer for every link
    # group — the declared target where there is one, the single implementer where the declared
    # target is outside the universe — so every column is bracketed at both ends: the null model
    # is what "everything" scores, the ideal row is what "exactly right" scores. Neither is ranked.
    # The ideal row does NOT read 1.000 on prec-strict: a group whose declared target is external
    # is answered with the one implementer, which is possible-not-certain by construction.
    ap.add_argument("--ideal", action="store_true")
    a = ap.parse_args()

    edges: list[Edge] = []
    seen: set[tuple[str, str]] = set()
    for ln in a.sites.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        d = json.loads(ln)
        caller = Ref.parse(d["caller"])
        if a.ideal:
            targets = d["certain"] or (d["possible"] if len(d["possible"]) == 1 else [])
        else:
            targets = d["possible"]
        for t in targets:
            k = (d["caller"], t)
            if k in seen:
                continue
            seen.add(k)
            edges.append(Edge(caller=caller, callee=Ref.parse(t),
                              confidence="ideal" if a.ideal else "envelope"))

    out = ToolOutput(
        tool=a.label, subject=a.subject, edges=edges, declared_tier=Tier.A,
        meta={"rows": len(edges), "null_model": True, "build": "oracle" if a.ideal else "bytecode",
              "reference": "ideal" if a.ideal else "null",
              "version": "the correct answer for every link group (a ceiling, not a tool)" if a.ideal
                         else "CHA envelope (no resolution)"},
    )
    write_edges(a.edges, out)
    print(f"{a.label}/{a.subject}: {len(edges)} edges -> {a.edges}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
