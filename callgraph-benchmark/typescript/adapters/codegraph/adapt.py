#!/usr/bin/env python3
"""Adapter: codegraph -> canonical, TypeScript.

`qualified_name` is `Base::describe` for a method and a bare `viaInherited` for a module-level
function — note that unlike its Java output it carries NO module prefix, so the owner is a simple
declaration name and the module has to come from `file_path`. `bench/language.py`'s TypeScript alias
table maps `Base` onto `src/t01-classes.ts:Base` when exactly one module declares it, and reports
AMBIGUOUS when two do — which the `t05` family exists to produce on purpose.

TIER: A. The `signature` column carries source-level parameter types, as in Java.

THE TOOL'S OWN DECLARED GAPS, AND ITS OWN OVERRIDE INDEX
---------------------------------------------------------
* `unresolved_refs` is a FIRST-CLASS TABLE this tool writes: a row per reference it found and
  could not resolve, with the referring node, the file and the line. For `reference_kind='calls'`
  that is the tool saying "there is a call here I could not resolve" — a DECLARED gap, which
  `docs/PROTOCOL.md` §6 scores `unknown` rather than `missed`. It travels as
  `meta.unresolved_sites`, the channel axiom's `ambiguous_unknown` already used. Reading it
  changes no precision or recall figure — only whether the report calls the tool silent.

* the `synthesizedBy: interface-impl` rows stay skipped as calls (#40 — they run from a
  DECLARATION to an implementation, at the declaration's line, and are an override index rather
  than a call). But that index is the tool's own answer to "what could this call reach", and
  §5.1 reads a multi-candidate answer as fan-out. `--dispatch` expands a `calls` edge landing on
  an overridden declaration into the declaration plus its implementations, as a SEPARATE row —
  exactly as `ViableCallEdges.ql` gives CodeQL a second row that is never merged with its first.
"""
from __future__ import annotations

import argparse
import json, json, sqlite3, sys
from collections import defaultdict
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in _here.parents if (p / "bench" / "model.py").exists())
sys.path.insert(0, str(_root / "bench"))
sys.path.insert(0, str(_here.parents[1]))

from _tscommon import container, ts_params  # noqa: E402
from model import BUDGETS, Edge, Ref, Tier, ToolOutput, write_edges   # noqa: E402
sys.path.insert(0, str(_root / "java" / "adapters" / "codegraph"))


def confidence_of(e) -> str:
    """The tool's OWN confidence term, carried verbatim. codegraph writes `metadata` JSON on every
    edge — `{"confidence": 0.9, "resolvedBy": "exact-match", "refName": …}` — with resolvedBy in
    {exact-match, instance-method, import, qualified-name, fuzzy} and confidence in 0.4–0.9. The
    first version of this adapter carried the relation KIND (`calls`/`instantiates`) instead,
    which is not a confidence at all, so the report could not say whether the tool's own label
    predicts its errors. It can now."""
    m = metadata_of(e)
    by = m.get("resolvedBy") or ("synthesized:" + m["synthesizedBy"] if m.get("synthesizedBy") else "unlabelled")
    c = m.get("confidence")
    kind = e["kind"]
    return f"{kind}|{by}:{c}" if c is not None else f"{kind}|{by}"


def metadata_of(e) -> dict:
    try:
        return json.loads(e["metadata"] or "{}") or {}
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--root", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--edges", required=True, type=Path)
    ap.add_argument("--label", default="codegraph")
    ap.add_argument("--meta", default="")
    ap.add_argument("--build", default="source only", choices=BUDGETS)
    ap.add_argument("--dispatch", action="store_true",
                    help="expand calls through the tool's own interface-impl index (PROTOCOL §5.1); a SEPARATE row")
    a = ap.parse_args()

    CALLER_KINDS_REF = ("method", "function")
    CALLER_KINDS = CALLER_KINDS_REF + ("property",)

    con = sqlite3.connect(str(a.db)); con.row_factory = sqlite3.Row
    nodes = {r["id"]: r for r in con.execute(
        "SELECT id, kind, name, qualified_name, file_path, signature, is_static FROM nodes")}

    def ref(r) -> Ref | None:
        q = r["qualified_name"] or r["name"]
        owner, _, name = q.rpartition("::")
        if not name:
            return None
        c = container(owner or None, r["file_path"], a.root)
        return Ref(name=name, type=c, params=ts_params(r["signature"]))

    def type_ref(r) -> Ref:
        q = (r["qualified_name"] or r["name"]).replace("::", ".")
        return Ref(name="constructor", type=container(q, r["file_path"], a.root))

    # the tool's OWN override index: a synthesized `interface-impl` row runs DECLARATION ->
    # implementation. Not a call (#40), but it is the tool's answer to "what could this reach".
    overrides: dict = defaultdict(list)
    for r in con.execute("SELECT source, target, metadata FROM edges WHERE kind IN ('calls','instantiates')"):
        md = metadata_of(r)
        if md.get("synthesizedBy") == "interface-impl" and not md.get("resolvedBy"):
            overrides[r["source"]].append(r["target"])

    def caller_ref(r) -> Ref | None:
        """The CALLER a codegraph source node denotes.

        A `property` source is a call written in a class FIELD INITIALIZER, which PROTOCOL §3.1
        says runs in the constructor, and in `<clinit>` when the field is static. codegraph
        attributes such a call to the field and names the owner, so this is reading its notation.
        """
        if r["kind"] in CALLER_KINDS_REF:
            return ref(r)
        if r["kind"] == "property":
            owner, _, _n = (r["qualified_name"] or "").rpartition("::")
            if not owner:
                return None
            return Ref(name=("<clinit>" if r["is_static"] else "constructor"),
                       type=container(owner, r["file_path"], a.root), params=None)
        return None

    # MEASURED AND DELIBERATELY NOT READ HERE: a `references` edge carrying `{"fnRef": true}`.
    # The JAVA adapter reads those, because a method reference compiles to an invokedynamic and
    # the class-file oracle scores it. TypeScript is the other way round: `higherOrder(helper, 1)`
    # passes a function identifier, the checker records no call at that line, and the tool's row
    # is a false positive. Reading them moved precision 0.892 -> 0.868 on torture, 0.949 -> 0.926
    # on type-graphql and 0.759 -> 0.751 on typedoc, with no recall gain on any of the three.
    # `docs/CROSS-LANGUAGE.md` covers a call THROUGH a function value and not the creation of one,
    # which is the distinction that decides this.

    edges: list[Edge] = []
    synthesized = 0
    expanded = 0
    for e in con.execute("SELECT source, target, kind, line, metadata FROM edges "
                         "WHERE kind IN ('calls','instantiates')"):
        s, t = nodes.get(e["source"]), nodes.get(e["target"])
        if s is None or t is None or s["kind"] not in CALLER_KINDS:
            continue
        if e["kind"] == "calls" and t["kind"] not in ("method", "function"):
            continue
        md = metadata_of(e)
        if md.get("synthesizedBy") and not md.get("resolvedBy"):   # an index link, not a call (#40)
            synthesized += 1
            continue
        caller = caller_ref(s)
        callee = ref(t) if e["kind"] == "calls" else type_ref(t)
        if caller is None or callee is None:
            continue
        edges.append(Edge(caller=caller, callee=callee, file=s["file_path"],
                          line=e["line"] or None, confidence=confidence_of(e)))
        if a.dispatch and e["kind"] == "calls" and overrides.get(e["target"]):
            for impl in overrides[e["target"]]:
                it = nodes.get(impl)
                if it is None:
                    continue
                iref = ref(it)
                if iref is None:
                    continue
                edges.append(Edge(caller=caller, callee=iref, file=s["file_path"],
                                  line=e["line"] or None, confidence="interface-impl"))
            expanded += 1

    # what the tool itself recorded as a call it could not resolve (§6 `unknown`, not `missed`)
    unresolved: list = []
    for r in con.execute("SELECT from_node_id, line, file_path FROM unresolved_refs "
                         "WHERE reference_kind = 'calls' AND status = 'failed'"):
        src = nodes.get(r["from_node_id"])
        if src is None or src["kind"] not in CALLER_KINDS:
            continue
        cref = caller_ref(src)
        if cref is None:
            continue
        unresolved.append([{"name": cref.name, "type": cref.type}, r["line"] or 0, r["file_path"]])

    out = ToolOutput(tool=a.label, subject=a.subject, edges=edges, declared_tier=Tier.A,
                     meta={"rows": len(edges), "version": a.meta, "build": a.build,
                           "synthesized_rows_skipped": synthesized,
                           "dispatch_expanded_sites": expanded,
                           "declared_unresolved": len(unresolved),
                           **({"unresolved_sites": unresolved} if unresolved else {})})
    write_edges(a.edges, out)
    print(f"{a.label}/{a.subject}: {len(edges)} edges -> {a.edges}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
