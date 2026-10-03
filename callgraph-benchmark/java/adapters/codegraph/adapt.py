#!/usr/bin/env python3
"""Adapter: codegraph (colbymchenry) -> the canonical edge schema.

WHAT THE TOOL EMITS
-------------------
SQLite at `.codegraph/codegraph.db`:

    nodes(id, kind, name, qualified_name, file_path, signature, …)
        kind is file | class | interface | enum | method | field | import | namespace.
        `qualified_name` is `pkg::Outer::Inner::method` — the FULL nesting chain, which is the
        benchmark's canonical shape with a different separator.
        `signature` is `<return> (<Type name>, …)`, e.g. `String (Helper h)`.
    edges(source, target, kind, line)
        `calls` is the call graph; `instantiates` is object creation.

TIER: A. Uniquely among the tree-sitter tools here, it records a parameter list — as source-level
`Type name` pairs in `signature` — so overload selection can actually be scored.

THREE READINGS, NONE OF THEM A REPAIR
-------------------------------------
* `pkg::Outer::Inner::method` splits at the last `::`; the owner keeps its whole chain with `::`
  rewritten to `.`. Nothing is inferred — the tool already resolved the nesting.

* An `instantiates` edge is a CONSTRUCTOR call: `new Helper()` recorded as pointing at the type.
  It names the class, not which constructor, so the adapter looks for constructor nodes under that
  class. Exactly one -> that is the only answer the edge could mean, and its parameters are used.
  More than one -> the parameter list is left UNKNOWN (`None`), which makes the row unspellable at
  Tier A and scored at Tier B. Choosing one would be inventing an overload resolution the tool did
  not perform, and this benchmark is worthless the moment an adapter does that.

* `signature` carries parameter NAMES as well as types (`String (Helper h)`), so the trailing
  identifier is dropped and the leading type kept. `bench/resolve.py` then erases type arguments
  and simple-names it, the same treatment every tool's parameters get.

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
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

# The shared scoring core lives at the repo root, not under the language tree; find it by walking
# up rather than by counting directories, so moving an adapter cannot silently break the import.
_here = Path(__file__).resolve()
_root = next(p for p in _here.parents if (p / "bench" / "model.py").exists())
sys.path.insert(0, str(_root / "bench"))

from model import BUDGETS, Edge, Ref, Tier, ToolOutput, repo_relative, write_edges   # noqa: E402

# `String (Helper h)` / `(String m)` / `void ()` — the return type is whatever precedes the `(`.
SIG_RE = re.compile(r"\((.*)\)\s*$", re.S)


def split_params(signature: str | None) -> tuple[str, ...] | None:
    """The parameter TYPES out of a source-level signature, or None when there is no signature."""
    if not signature:
        return None
    m = SIG_RE.search(signature.strip())
    if not m:
        return None
    body = m.group(1).strip()
    if not body:
        return ()
    out: list[str] = []
    depth = 0
    cur = ""
    # split on commas that are not inside type arguments — `Map<String, Integer> m` is ONE parameter
    for ch in body:
        if ch in "<([":
            depth += 1
        elif ch in ">)]":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    params: list[str] = []
    for p in out:
        p = p.strip()
        if not p:
            continue
        # drop modifiers and the trailing parameter NAME: `final Map<K,V> m` -> `Map<K,V>`
        p = re.sub(r"^(final|@\w+)\s+", "", p).strip()
        toks = p.rsplit(" ", 1)
        params.append((toks[0] if len(toks) == 2 else p).strip())
    return tuple(params)


ANON_RE = re.compile(r"\.[A-Za-z_$][\w$]*\.<([A-Za-z_$][\w$]*)\$anon@(\d+)>")


def anon_notation(owner: str) -> str:
    """codegraph writes an anonymous class as `Outer.method.<Iface$anon@line>`; the oracle keys it
    `Outer$anon:Iface@line` (issue #32, reopened). The tool supplies the outer class, the
    supertype and the line — exactly the oracle's key — so this is a translation. Nested cases,
    `A.m.<I$anon@N>.n.<J$anon@M>`, become `A$anon:I@N$anon:J@M`."""
    while True:
        m = ANON_RE.search(owner)
        if not m:
            return owner
        owner = owner[: m.start()] + f"$anon:{m.group(1)}@{m.group(2)}" + owner[m.end():]


def owner_and_name(qualified: str) -> tuple[str | None, str]:
    if "::" not in qualified:
        return None, qualified
    owner, _, name = qualified.rpartition("::")
    owner = anon_notation(owner.replace("::", "."))
    return owner or None, name


def metadata_of(e) -> dict:
    try:
        return json.loads(e["metadata"] or "{}") or {}
    except Exception:
        return {}


def confidence_of(e, kind: str) -> str:
    """The tool's OWN confidence term, carried verbatim, with the relation kind kept apart
    (`calls` and `instantiates` are different claims — issue #41): `calls|exact-match:0.9`."""
    m = metadata_of(e)
    by = m.get("resolvedBy") or ("synthesized:" + m["synthesizedBy"] if m.get("synthesizedBy") else "unlabelled")
    c = m.get("confidence")
    return f"{kind}|{by}:{c}" if c is not None else f"{kind}|{by}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--edges", required=True, type=Path)
    ap.add_argument("--label", default="codegraph")
    ap.add_argument("--meta", default="")
    ap.add_argument("--build", default="source only", choices=BUDGETS)
    ap.add_argument("--dispatch", action="store_true",
                    help="expand calls through the tool's own interface-impl index (PROTOCOL §5.1); a SEPARATE row")
    a = ap.parse_args()

    con = sqlite3.connect(str(a.db))
    con.row_factory = sqlite3.Row
    nodes = {r["id"]: r for r in con.execute(
        "SELECT id, kind, name, qualified_name, file_path, signature FROM nodes")}

    # constructors, by the class that declares them: a constructor's name is its class's name
    ctors: dict[str, list] = defaultdict(list)
    for r in nodes.values():
        if r["kind"] != "method":
            continue
        owner, name = owner_and_name(r["qualified_name"])
        if owner and name == owner.rsplit(".", 1)[-1]:
            ctors[owner].append(r)

    def method_ref(r) -> Ref:
        owner, name = owner_and_name(r["qualified_name"])
        if owner and name == owner.rsplit(".", 1)[-1]:
            name = "<init>"
        return Ref(name=name, type=owner, params=split_params(r["signature"]))

    def type_ref(r) -> Ref:
        """An `instantiates` target: the TYPE, meaning its constructor."""
        owner = r["qualified_name"].replace("::", ".")
        cs = ctors.get(owner, [])
        params = split_params(cs[0]["signature"]) if len(cs) == 1 else None
        return Ref(name="<init>", type=owner, params=params)

    # the tool's OWN override index: a synthesized `interface-impl` row runs DECLARATION ->
    # implementation. Not a call (#40), but it is the tool's answer to "what could this reach".
    overrides: dict = defaultdict(list)
    for r in con.execute("SELECT source, target, metadata FROM edges WHERE kind IN ('calls','instantiates')"):
        md = metadata_of(r)
        if md.get("synthesizedBy") == "interface-impl" and not md.get("resolvedBy"):
            overrides[r["source"]].append(r["target"])

    # A top-level `record`'s members are emitted as `function`, not `method`, so a Java caller can
    # be either; the TypeScript adapter has always accepted both.
    CALLABLE = ("method", "function")

    edges: list[Edge] = []
    synthesized = 0
    expanded = 0
    fn_refs = 0
    for r in con.execute(
        "SELECT source, target, kind, line, metadata FROM edges "
        "WHERE kind IN ('calls', 'instantiates', 'references')"
    ):
        s, t = nodes.get(r["source"]), nodes.get(r["target"])
        if s is None or t is None or s["kind"] not in CALLABLE:
            continue
        if r["kind"] == "references":
            # A METHOD REFERENCE IS A CALL SITE. `DirectoryScanner::normalizePattern`,
            # `this::findMainClass`: javac emits an invokedynamic and the oracle scores it.
            # codegraph does NOT file its answer under `calls` — it writes a `references` edge
            # carrying `{"fnRef": true, "refKind": "function_ref"}` and the node it resolved the
            # reference to. Reading only `calls` threw that answer away: 89 rows on apache-ant,
            # 89 on spring-boot, and 52 and 72 uniquely-linked groups respectively where it was
            # the tool's only answer. Nothing is inferred; the target is the one the tool chose.
            #
            # The TypeScript adapter deliberately does NOT do this. See the note there.
            md0 = metadata_of(r)
            if not (md0.get("fnRef") or md0.get("refKind") == "function_ref"):
                continue
            if t["kind"] not in CALLABLE + ("class",):
                continue
            fn_refs += 1
        elif r["kind"] == "calls" and t["kind"] not in CALLABLE:
            continue
        # A SYNTHESIZED LINK IS NOT A CALL (issue #40). codegraph also writes, with kind `calls`,
        # its interface -> implementation index (`{"synthesizedBy": "interface-impl", …}`): 1,078
        # rows on rxjava from a bodiless declaration to a same-named implementation. The tool
        # labels them as synthesized; scoring them charged it 7 points of precision for an index
        # it never claimed was a call. Skipped and counted.
        md = metadata_of(r)
        if md.get("synthesizedBy") and not md.get("resolvedBy"):
            synthesized += 1
            continue
        # `Item::new` resolves to the TYPE and means its constructor, as `instantiates` does
        callee = type_ref(t) if (r["kind"] == "instantiates" or t["kind"] == "class") else method_ref(t)
        edges.append(Edge(caller=method_ref(s), callee=callee,
                          file=s["file_path"], line=r["line"] or None, confidence=confidence_of(r, r["kind"])))
        if a.dispatch and r["kind"] == "calls" and overrides.get(r["target"]):
            for impl in overrides[r["target"]]:
                it = nodes.get(impl)
                if it is None:
                    continue
                edges.append(Edge(caller=method_ref(s), callee=method_ref(it), file=s["file_path"],
                                  line=r["line"] or None, confidence="interface-impl"))
            expanded += 1

    # what the tool itself recorded as a call it could not resolve (§6 `unknown`, not `missed`)
    unresolved: list = []
    for r in con.execute("SELECT from_node_id, line, file_path FROM unresolved_refs "
                         "WHERE reference_kind = 'calls' AND status = 'failed'"):
        src = nodes.get(r["from_node_id"])
        if src is None or src["kind"] not in CALLABLE:
            continue
        cref = method_ref(src)
        if cref is None:
            continue
        unresolved.append([{"name": cref.name, "type": cref.type}, r["line"] or 0, r["file_path"]])

    out = ToolOutput(tool=a.label, subject=a.subject, edges=edges, declared_tier=Tier.A,
                     meta={"build": a.build, "source": repo_relative(a.db), "rows": len(edges), "version": a.meta,
                           "synthesized_rows_skipped": synthesized,
                           "function_ref_rows": fn_refs,
                           "dispatch_expanded_sites": expanded,
                           "declared_unresolved": len(unresolved),
                           **({"unresolved_sites": unresolved} if unresolved else {})})
    write_edges(a.edges, out)
    print(f"{a.label}/{a.subject}: {len(edges)} edges -> {a.edges}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
