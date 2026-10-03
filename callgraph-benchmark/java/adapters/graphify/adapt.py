#!/usr/bin/env python3
"""Adapter: Graphify -> the canonical edge schema.

WHAT THE TOOL EMITS
-------------------
`graphify-out/graph.json`, written by the deterministic AST extractor (`graphify update --no-cluster`,
no LLM involved — the semantic layer is for docs and images, not code):

    nodes: {id, label, source_file, source_location, _callable, _origin}
    links: {source, target, relation, confidence, source_file, source_location}

`relation` is `calls` | `method` | `contains` | `references` | `imports` | `implements` | `inherits`.
`confidence` is `EXTRACTED` (explicit in the source) or `INFERRED` (derived by resolution).

TIER: B. A method's `label` is `.use()` — the parentheses are always empty, so no parameter list is
expressible and Tier A is reported `n/a` rather than zero.

THE OWNER IS NOT IN THE NODE — IT IS IN AN EDGE
-----------------------------------------------
Node ids are lowercased and underscore-joined (`it_example_f11packages_helper_use`), which cannot be
split back into a package/type/method reliably: `f11packages_helper_use` could be any of several
splits, and guessing one would be inventing structure. But the graph states the answer directly —
a `method` relation runs from the declaring TYPE's node to the method's node, and the type node's
`label` is its simple name (`Helper`).

So the owner is read from that edge. That is using the tool's own resolution, not reconstructing it.
A method node with no incoming `method` edge (a top-level function, or a body the extractor did not
attach) is emitted name-only, spellable at Tier C, counted as unspellable at Tier B — the honest
record of "this tool did not say which type".

`source_file` travels with every node, so `bench/resolve.py` can place a simple owner name against
the file that declares it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# The shared scoring core lives at the repo root, not under the language tree; find it by walking
# up rather than by counting directories, so moving an adapter cannot silently break the import.
_here = Path(__file__).resolve()
_root = next(p for p in _here.parents if (p / "bench" / "model.py").exists())
sys.path.insert(0, str(_root / "bench"))

from model import BUDGETS, Edge, Ref, Tier, ToolOutput, repo_relative, write_edges   # noqa: E402

LINE_RE = re.compile(r"L(\d+)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", required=True, type=Path)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--edges", required=True, type=Path)
    ap.add_argument("--label", default="graphify")
    ap.add_argument("--meta", default="")
    ap.add_argument("--build", default="source only", choices=BUDGETS)
    a = ap.parse_args()

    g = json.loads(a.graph.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in g.get("nodes", [])}
    links = g.get("links", g.get("edges", []))

    # the declaring type of each method, taken from the `method` relation the graph already carries
    owner_of: dict[str, str] = {}
    for l in links:
        if l.get("relation") != "method":
            continue
        parent = nodes.get(l.get("source"))
        if parent is None:
            continue
        owner = (parent.get("label") or "").strip()
        if owner:
            owner_of[l.get("target")] = owner

    l_source: list = [None]      # the current link's source, so a type node as CALLER is not a ctor

    def ref(node_id: str) -> Ref | None:
        n = nodes.get(node_id)
        if n is None:
            return None
        label = (n.get("label") or "").strip()
        # a callable's label is `.name()`; a type's is its bare simple name
        name = label.lstrip(".").split("(", 1)[0].strip()
        if not name:
            return None
        # A `calls` edge whose TARGET is a type node (no parentheses: `Node`) is the tool's
        # `new X()`; the callee is X's constructor (issue #32 §2)
        if "(" not in label and node_id != l_source[0]:
            return Ref(name="<init>", type=name)
        owner = owner_of.get(node_id)
        if owner and name == owner:
            name = "<init>"
        return Ref(name=name, type=owner)

    def line_of(loc: str | None) -> int | None:
        m = LINE_RE.search(loc or "")
        return int(m.group(1)) if m else None

    edges: list[Edge] = []
    for l in links:
        if l.get("relation") != "calls":
            continue
        l_source[0] = l.get("source")
        caller, callee = ref(l.get("source")), ref(l.get("target"))
        if caller is None or callee is None:
            continue
        edges.append(Edge(caller=caller, callee=callee,
                          file=l.get("source_file") or nodes[l["source"]].get("source_file"),
                          line=line_of(l.get("source_location")),
                          confidence=l.get("confidence")))

    out = ToolOutput(tool=a.label, subject=a.subject, edges=edges, declared_tier=Tier.B,
                     meta={"source": repo_relative(a.graph), "rows": len(edges), "version": a.meta,
                           "build": a.build})
    write_edges(a.edges, out)
    print(f"{a.label}/{a.subject}: {len(edges)} edges -> {a.edges}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
