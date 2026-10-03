#!/usr/bin/env python3
"""Adapter: CodeQL -> the canonical edge schema.

The query already emits the columns the schema wants, so this is a straight translation:

    callerType, callerName, callerParams, calleeType, calleeName, calleeParams, file, line

TIER: A. CodeQL resolves overloads and its `Callable` carries an erased parameter list, so it is
scored at every tier — including the one only a signature-aware tool can be credited for.

TWO NOTATION DIFFERENCES, BOTH HANDLED BY READING RATHER THAN REWRITING
-----------------------------------------------------------------------
* CodeQL spells a nested type `pkg.Outer$Inner` in `getQualifiedName()`; the benchmark's canonical
  form is `pkg.Outer.Inner`. `bench/resolve.py` maps between them — a notation difference, not a
  disagreement about which type is meant.
* CodeQL names an anonymous class `pkg.Outer$1` (or `new Runnable(...) { ... }` in some contexts).
  The benchmark keys anonymous classes by supertype, because javac and ecj number them differently.
  The resolver's alias table covers the `$N` form; where it cannot, the row is reported AMBIGUOUS or
  UNKNOWN and counted, never silently dropped.

An empty `calleeParams` means a no-argument method — `()` — and is NOT the same as the tool being
unable to express parameters. The distinction decides whether a row is scored at Tier A or excused
from it, so it is preserved explicitly rather than left to a falsy check.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# The shared scoring core lives at the repo root, not under the language tree; find it by walking
# up rather than by counting directories, so moving an adapter cannot silently break the import.
_here = Path(__file__).resolve()
_root = next(p for p in _here.parents if (p / "bench" / "model.py").exists())
sys.path.insert(0, str(_root / "bench"))

from model import BUDGETS, Edge, Ref, Tier, ToolOutput, repo_relative, write_edges   # noqa: E402


def ref(type_name: str, name: str, params: str) -> Ref:
    t = type_name.strip() or None
    ps = tuple(p for p in (x.strip() for x in params.split(",")) if p)
    return Ref(name=name.strip(), type=t, params=ps)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, type=Path)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--edges", required=True, type=Path)
    ap.add_argument("--label", default="codeql")
    ap.add_argument("--meta", default="")
    ap.add_argument("--build", required=True, choices=BUDGETS,
                    help="what the tool required; see bench/model.py BUDGETS")
    a = ap.parse_args()

    edges: list[Edge] = []
    with a.csv.open(encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh):
            if len(row) < 8:
                continue
            ct, cn, cp, et, en, ep, f, line = (x for x in row[:8])
            try:
                ln = int(line)
            except ValueError:
                ln = None
            edges.append(Edge(caller=ref(ct, cn, cp), callee=ref(et, en, ep),
                              file=f.strip() or None, line=ln))

    out = ToolOutput(tool=a.label, subject=a.subject, edges=edges, declared_tier=Tier.A,
                     meta={"source": repo_relative(a.csv), "rows": len(edges), "version": a.meta,
                           "build": a.build})
    write_edges(a.edges, out)
    print(f"{a.label}/{a.subject}: {len(edges)} edges -> {a.edges}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
