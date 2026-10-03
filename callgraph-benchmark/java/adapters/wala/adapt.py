#!/usr/bin/env python3
"""Adapter: WALA (CHA / RTA / 0-CFA) -> the canonical edge schema.

WHAT THE DRIVER EMITS
---------------------
    caller<TAB>callee<TAB>algo

with a method spelled `pkg.Outer$Inner#name(Simple,…)`: the internal `$` nesting the class file
uses, an anonymous class by its supertype (`Outer$anon:Runnable`), a local class without its
counter, an enum-constant body folded onto its enum — every one of them a convention
`docs/PROTOCOL.md` §3 states and `bench/resolve.py` reads.

A LAMBDA BODY (`lambda$m$0`) as a CALLER is folded into `m` by the resolver's notation rule. As a
CALLEE it is dropped here: the oracle has no edge from `m` to its own lambda body (the body IS `m`
after the fold), so keeping the row would score a self-edge that is an artefact of the fold, not
a claim the tool made about the program.

TIER: A — the descriptor's parameter types, erased and simple-named, exactly as the oracle spells them.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in _here.parents if (p / "bench" / "model.py").exists())
sys.path.insert(0, str(_root / "bench"))

from model import BUDGETS, Edge, Ref, Tier, ToolOutput, repo_relative, write_edges   # noqa: E402

LAMBDA = re.compile(r"^lambda\$")
SIG = re.compile(r"^(?P<type>[^#]+)#(?P<name>[^(]+)\((?P<params>.*)\)$")


def parse(s: str) -> Ref | None:
    m = SIG.match(s.strip())
    if not m:
        return None
    params = tuple(p for p in m.group("params").split(",") if p)
    return Ref(name=m.group("name"), type=m.group("type"), params=params)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", required=True, type=Path)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--edges", required=True, type=Path)
    ap.add_argument("--meta", default="")
    ap.add_argument("--build", required=True, choices=BUDGETS)
    a = ap.parse_args()

    edges: list[Edge] = []
    lambda_targets = 0
    for ln in a.tsv.read_text(encoding="utf-8").splitlines():
        parts = ln.split("\t")
        if len(parts) < 3:
            continue
        caller, callee = parse(parts[0]), parse(parts[1])
        if caller is None or callee is None:
            continue
        if LAMBDA.match(callee.name):
            lambda_targets += 1
            continue
        edges.append(Edge(caller=caller, callee=callee, confidence=parts[2]))

    out = ToolOutput(tool=a.label, subject=a.subject, edges=edges, declared_tier=Tier.A,
                     meta={"source": repo_relative(a.tsv), "rows": len(edges), "version": a.meta,
                           "build": a.build, "lambda_body_targets_dropped": lambda_targets})
    write_edges(a.edges, out)
    print(f"{a.label}/{a.subject}: {len(edges)} edges -> {a.edges}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
