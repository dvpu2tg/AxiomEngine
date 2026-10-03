#!/usr/bin/env python3
"""Adapter: code-review-graph (tirth8205) -> the canonical edge schema.

WHAT THE TOOL EMITS
-------------------
A SQLite graph at `<data-dir>/graph.db`. Two tables matter:

    nodes(kind, name, qualified_name, file_path, parent_name, params, …)
        kind is File | Class | Function. `qualified_name` is `<abs file>::<Owner>.<name>`, so the
        owner is a SIMPLE class name — the package appears nowhere in it.
    edges(kind, source_qualified, target_qualified, file_path, line, confidence_tier)
        kind CALLS is the call graph; confidence_tier is EXTRACTED | INFERRED.

TIER: B. It can express an owner and a method name, never a parameter list, so Tier A is reported
`n/a` — the question was not put to it. See `docs/PROTOCOL.md` §5.

THREE THINGS THE ADAPTER MUST READ CORRECTLY, AND ONE IT MUST NOT REPAIR
-------------------------------------------------------------------------
* A CALLS edge whose target is a **Class** node is a CONSTRUCTOR call — `new Helper()` is recorded
  as pointing at the type. Reading it as `Helper#<init>` is translating the tool's notation. On this
  subject that is 31 of 218 CALLS edges; dropping them would delete every object creation the tool
  found.

* An owner is a bare simple name (`Helper`, `Base`). The row also carries its FILE, and Java names
  the public top-level type after its file, so `bench/resolve.py` narrows the pair of `Node` types
  this subject contains without guessing. Passing the file is what keeps a correct answer from being
  reported AMBIGUOUS.

* `params` is a SOURCE-level string with parameter names (`(Helper h)`), not types, and only on the
  node — a call EDGE carries none. So the callee can never be spelled at Tier A no matter what the
  caller carries, which is why the declared ceiling is B for the whole tool rather than per row.

And the one not to repair: **86 of 218 CALLS targets are a bare method name** (`area`, `copy`) that
matches no node. That is not a notation difference — it is the tool saying it could not resolve the
call. Those rows are emitted as a name-only `Ref`, which is spellable at Tier C and *unspellable* at
Tier B, so they are counted in `unspellable_rows` and the link group reads `missed`. Inventing an
owner for them from the surrounding file would be manufacturing a resolution the tool did not
perform, and would make this benchmark worthless.

THE TOOL'S OWN DECLARED GAPS, AND ITS OWN CANDIDATE SET
-------------------------------------------------------
`extra` on a CALLS row carries two things this adapter used to discard:

* `bare_call_target` on a row whose target names no node — the tool saying "there is a call
  here and I could not resolve its owner". That is a DECLARED gap, and `docs/PROTOCOL.md` §6
  distinguishes it from a silent one (`unknown` vs `missed`). It travels as
  `meta.unresolved_sites`, the same channel axiom's `ambiguous_unknown` already used. It
  changes no precision or recall figure — only whether the report calls the tool silent.

* `ambiguous_targets` — a fully-qualified candidate set the tool computed itself for a call it
  could not narrow to one. §5.1 reads a multi-candidate row as fan-out, one edge per candidate,
  which is how axiom's `multi_inferred` and CodeQL's `getACallee(_)` are already read. Dropping
  it reported the tool as having found nothing at its dispatch sites. It is a different question
  from the unprompted answer, so it is a SEPARATE ROW (`--dispatch`), exactly as
  `codeql`/`codeql-dispatch` are two rows and never merged.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

# The shared scoring core lives at the repo root, not under the language tree; find it by walking
# up rather than by counting directories, so moving an adapter cannot silently break the import.
_here = Path(__file__).resolve()
_root = next(p for p in _here.parents if (p / "bench" / "model.py").exists())
sys.path.insert(0, str(_root / "bench"))

from model import BUDGETS, Edge, Ref, Tier, ToolOutput, repo_relative, write_edges   # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--root", required=True, type=Path,
                    help="the checkout the tool indexed; file paths are made relative to it")
    ap.add_argument("--subject", required=True)
    ap.add_argument("--edges", required=True, type=Path)
    ap.add_argument("--label", default="code-review-graph")
    ap.add_argument("--meta", default="")
    ap.add_argument("--build", default="source only", choices=BUDGETS)
    ap.add_argument("--dispatch", action="store_true",
                    help="read `extra.ambiguous_targets` as fan-out (PROTOCOL §5.1); a SEPARATE row")
    a = ap.parse_args()

    con = sqlite3.connect(str(a.db))
    con.row_factory = sqlite3.Row

    nodes: dict[str, sqlite3.Row] = {
        r["qualified_name"]: r
        for r in con.execute("SELECT kind, name, qualified_name, file_path, parent_name FROM nodes")
    }

    root = str(a.root).rstrip("/") + "/"

    def rel(p: str | None) -> str | None:
        if not p:
            return None
        return p[len(root):] if p.startswith(root) else p

    def to_ref(qname: str) -> Ref | None:
        n = nodes.get(qname)
        if n is None:
            # A bare method name: the tool found a call and did not resolve its owner. Recorded as
            # exactly that — a name with no type — never guessed at.
            if "::" not in qname:
                return Ref(name=qname)
            # A QUALIFIED name with no node (#91): the tool writes no Function node for a method
            # carrying an annotation (`@Test public void m()`, every `@Override`) yet records its
            # CALLS edges under `<file>::Owner.m`. That is the tool naming the owner and the
            # method; dropping the edge for want of a node threw away every call such a method
            # makes. Read the spelling: the last segment is the method, what precedes it the owner
            # (its module for a segment-less name).
            spelled = qname.split("::", 1)[1]
            owner, _, name = spelled.rpartition(".")
            return Ref(name=name, type=owner or None)
        if n["kind"] == "Class":
            # `new X()` is recorded as an edge to the TYPE. That is a constructor call.
            return Ref(name="<init>", type=n["name"])
        # a `Test` node is a method the tool classified as a test (`@Test`): a method all the same —
        # dropping it dropped every call a test makes (found by benchmark-test-impact, #91)
        if n["kind"] in ("Function", "Test"):
            return Ref(name=n["name"], type=n["parent_name"] or None)
        return None

    edges: list[Edge] = []
    unresolved: list = []
    fanned = 0
    # `extra` arrived with a later schema version; a graph written by an older build has the
    # CALLS rows but not the column, and must still score rather than crash.
    has_extra = any(c[1] == "extra" for c in con.execute("PRAGMA table_info(edges)"))
    for r in con.execute(
        "SELECT source_qualified, target_qualified, file_path, line, confidence_tier"
        + (", extra " if has_extra else ", '{}' AS extra ")
        + "FROM edges WHERE kind = 'CALLS'"
    ):
        caller = to_ref(r["source_qualified"])
        callee = to_ref(r["target_qualified"])
        if caller is None or callee is None:
            continue
        # THE TARGET NODE'S OWN FILE travels as `callee_file` (#36 reopened). The tool spells an
        # owner by its simple name, and the node it linked to carries the file that declares it;
        # without it the scorer had only the CALL SITE's file, and read `OnErrorReturnMaybeObserver`
        # by the file the call was in — 12 rows on rxjava where the tool had linked to the
        # same-named class in the caller's file, which is what it said, not what the scorer guessed.
        target = nodes.get(r["target_qualified"])
        extra = json.loads(r["extra"] or "{}")
        if target is None:
            cands = extra.get("ambiguous_targets") or []
            if cands and a.dispatch:
                # the tool's OWN candidate set, read as fan-out (§5.1): one edge per candidate,
                # each carrying the tool's own term for the claim
                for c in cands:
                    cref = to_ref(c)
                    if cref is None:
                        continue
                    ct = nodes.get(c)
                    edges.append(Edge(caller=caller, callee=cref, file=rel(r["file_path"]),
                                      callee_file=rel(ct["file_path"]) if ct is not None else None,
                                      line=r["line"] or None, confidence="ambiguous_targets"))
                fanned += 1
                continue
            # a call the tool FOUND and declared it could not resolve — §6 `unknown`, not `missed`
            unresolved.append([{"name": caller.name, "type": caller.type},
                               r["line"] or 0, rel(r["file_path"])])
        callee_file = rel(target["file_path"]) if target is not None else None
        edges.append(Edge(caller=caller, callee=callee, file=rel(r["file_path"]), callee_file=callee_file,
                          line=r["line"] or None, confidence=r["confidence_tier"]))

    out = ToolOutput(tool=a.label, subject=a.subject, edges=edges, declared_tier=Tier.B,
                     meta={"build": a.build, "source": repo_relative(a.db), "rows": len(edges), "version": a.meta,
                           "declared_unresolved": len(unresolved), "fanned_rows": fanned,
                           **({"unresolved_sites": unresolved} if unresolved else {})})
    write_edges(a.edges, out)
    print(f"{a.label}/{a.subject}: {len(edges)} edges -> {a.edges}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
