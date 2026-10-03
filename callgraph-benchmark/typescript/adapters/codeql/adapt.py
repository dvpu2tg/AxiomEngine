#!/usr/bin/env python3
"""Adapter: CodeQL (JavaScript/TypeScript) -> canonical.

TIER: B, NOT A — and the difference is a real limitation, not a formatting choice.

CodeQL's Java library exposes a `Callable`'s erased parameter TYPES, so the Java adapter declares
Tier A. Its JavaScript/TypeScript library models a `Function`'s parameters as bindings, and what is
cheaply available is their NAMES. Declaring Tier A and emitting names would compare `b` against
`Base` and score the tool as getting every overload wrong — a number that is entirely an artefact of
the adapter. So the parameter list is emitted as UNKNOWN (`None`), Tier A reads `n/a`, and the
overload question is simply not put to this tool in TypeScript.

The resolution mechanism also differs from the Java side, which is what makes this a real comparison
rather than two readings of one answer: `DataFlow::InvokeNode.getACallee()` is a points-to style
resolution, not a type-checker query, so it does not share a mechanism with the oracle's
`getResolvedSignature`.
"""
from __future__ import annotations

import argparse, csv, sys
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in _here.parents if (p / "bench" / "model.py").exists())
sys.path.insert(0, str(_root / "bench"))

from model import Edge, Ref, Tier, ToolOutput, repo_relative, write_edges   # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, type=Path)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--edges", required=True, type=Path)
    ap.add_argument("--label", default="codeql")
    ap.add_argument("--meta", default="")
    ap.add_argument("--build", default="source only")
    a = ap.parse_args()

    edges: list[Edge] = []
    with a.csv.open(encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh):
            if len(row) < 8:
                continue
            ct, cn, _cp, et, en, _ep, f, line = row[:8]
            conf = row[8].strip() if len(row) > 8 else None    # `imprecision=N`, the tool's own grade
            try:
                ln = int(line)
            except ValueError:
                ln = None
            # params deliberately None — see the module docstring
            edges.append(Edge(caller=Ref(name=cn.strip(), type=ct.strip() or None),
                              callee=Ref(name=en.strip(), type=et.strip() or None),
                              file=f.strip() or None, line=ln, confidence=conf or None))

    out = ToolOutput(tool=a.label, subject=a.subject, edges=edges, declared_tier=Tier.B,
                     meta={"source": repo_relative(a.csv), "rows": len(edges), "version": a.meta,
                           "build": a.build})
    write_edges(a.edges, out)
    print(f"{a.label}/{a.subject}: {len(edges)} edges -> {a.edges}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
