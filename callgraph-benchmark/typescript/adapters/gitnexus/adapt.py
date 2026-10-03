#!/usr/bin/env python3
"""Adapter: GitNexus -> canonical, TypeScript.

WHAT THE TOOL EMITS
-------------------
A LadybugDB graph queried through `gitnexus cypher`. Symbol ids carry the structure:

    Method:torture/F02Generics.java:Box.get#0
    │      │                        │   │  └ ARITY, not a type list
    │      │                        │   └ method name
    │      │                        └ owner, a SIMPLE class name
    │      └ file
    └ node label (Method | Function | File | …)

Relationships are all `CodeRelation` with a `type` property; `CALLS` is the call graph.

TIER: B. The id carries an owner and a method name but only an ARITY — `#1` says "one parameter",
not which type. Arity is not a signature, so Tier A is reported `n/a`: the tool was never asked the
overload question and a zero there would say it got them wrong.

WHAT IS AND IS NOT READ
-----------------------
* A `Method:` target is a method. Owner and name come straight out of the id, and the FILE comes
  with it, which is what lets `bench/resolve.py` place a simple owner name unambiguously.

* A `Function:` target is GitNexus's node for a function VALUE — a field or local holding a lambda
  (`F06Functional.field`, `F06Functional.viaLocal.s@43:30`). That is a real answer to a different
  question: it names the variable the call goes through, not the method that runs. The oracle folds
  a lambda body into its lexically enclosing method, so there is no honest mapping from a variable
  id to a method, and inventing one would manufacture a resolution. These rows are emitted with the
  variable's own name and no owner — spellable only at Tier C — so they count as unresolved at the
  tiers that matter and are visible in `unspellable_rows` rather than silently dropped.

* A constructor is named after its class in the id (`Helper.Helper#0`), and is rewritten to
  `<init>` to match the class-file spelling — a notation change, not a resolution.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# The shared scoring core lives at the repo root, not under the language tree; find it by walking
# up rather than by counting directories, so moving an adapter cannot silently break the import.
_here = Path(__file__).resolve()
_root = next(p for p in _here.parents if (p / "bench" / "model.py").exists())
sys.path.insert(0, str(_root / "bench"))
sys.path.insert(0, str(_here.parents[1]))
from _tscommon import container, module_of   # noqa: E402

from model import BUDGETS, Edge, Ref, Tier, ToolOutput, write_edges   # noqa: E402

# `Method:torture/F02Generics.java:Box.get#0`
ID_RE = re.compile(r"^(?P<label>[A-Za-z]+):(?P<file>[^:]+):(?P<sym>.+)$")


ROOT = ""      # set from --src; a module-level symbol's container is its FILE (see _tscommon)


def parse_id(node_id: str) -> tuple[str, str, Ref] | None:
    """(label, file, ref) or None when the id is not a symbol reference."""
    m = ID_RE.match(node_id or "")
    if not m:
        # `File:lib/application.ts` — TWO components, so ID_RE (which wants three) never matched and
        # the whole row was discarded. This is GitNexus's node for a call written at a module's TOP
        # LEVEL, and the oracle has a caller for exactly that: `<module>`, owned by the module
        # (`typescript/oracle/ts-ground-truth.ts:836`). The axiom adapter already translates its own
        # MODULE_INITIALIZER to the same pair; not doing it here deleted a fifth to a quarter of the
        # tool's rows before scoring. The same defect as issue #16, which cost CodeQL 750 of fp-ts's
        # groups.
        if (node_id or "").startswith("File:"):
            file = node_id.split(":", 1)[1]
            mod = module_of(file, ROOT)
            if mod:
                return "File", file, Ref(name="<module>", type=mod)
        return None
    label, file, sym = m.group("label"), m.group("file"), m.group("sym")
    sym = sym.split("#", 1)[0]              # drop the arity suffix — it is not a type list
    if label == "Class":
        # a call edge pointing at a TYPE is an object creation, the same convention the other
        # index-style tools use
        return label, file, Ref(name="<init>", type=sym)
    if "." not in sym:
        # `Function:src/t03-functions.ts:helper` — a module-level function. It has no class owner
        # and does not need one: in TypeScript the MODULE is the container, and the id already
        # names the file. Leaving it owner-less would drop every top-level function to Tier C.
        return label, file, Ref(name=sym, type=container(None, file, ROOT))
    owner, _, name = sym.rpartition(".")
    if label == "Class":
        pass
    if label not in ("Method", "Constructor"):
        # a function VALUE (a field or local holding a lambda): the tool named the variable, not a
        # method. Recorded name-only rather than mapped onto a method it did not name.
        return label, file, Ref(name=name)
    if name == owner.rsplit(".", 1)[-1]:
        name = "<init>"
    return label, file, Ref(name=name, type=owner)


# The CLI truncates its output at exactly 64 KiB, mid-string, with no error — measured: 200 rows of
# this projection is ~40 KB and parses, 500 rows is ~65,564 bytes and does not. A fixed page size
# would therefore be a guess that breaks on a project with longer identifiers, so the pager HALVES
# on truncation instead and only gives up below one row.
PAGE = 200


def run_cypher(gitnexus: str, cwd: Path, query: str) -> list[dict]:
    # The CLI already prints a JSON envelope; it has no `--json` flag, and passing one is a hard
    # error rather than an ignored option.
    r = subprocess.run([gitnexus, "cypher", query], cwd=str(cwd),
                       capture_output=True, text=True)
    text = r.stdout
    start = text.find("{")
    if start < 0:
        # AN EMPTY RESULT IS `[]`, NOT AN ERROR. With no row to return the CLI prints a bare JSON
        # array instead of its envelope, and this read it as "no JSON" and exited: the pager asks
        # for one page past the end, so a result set that ended exactly on a page boundary (a
        # multiple of PAGE rows) lost the bug's whole gitnexus output. Deterministic, which is
        # why Jsoup-17, JacksonCore-10 and JxPath-18 failed on every Defects4J sweep.
        arr = text.find("[")
        if arr >= 0 and text[arr:].lstrip("[").lstrip().startswith("]"):
            return []
        raise SystemExit(f"gitnexus cypher produced no JSON:\n{r.stdout}\n{r.stderr}")
    try:
        payload = json.loads(text[start:])
    except json.JSONDecodeError as e:
        # The whole result set comes back as ONE json string field, and past 64 KiB it is TRUNCATED
        # mid-string with no error. Silently keeping whatever parsed would score the tool on a
        # fraction of its answer — a number that looks entirely normal. Signal instead, and let the
        # caller shrink the page.
        raise Truncated(str(e)) from e
    if "error" in payload:
        raise SystemExit(f"gitnexus cypher error: {payload['error']}")
    rows = payload.get("rows")
    if rows is not None:
        return rows
    return _from_markdown(payload.get("markdown", ""))


class Truncated(Exception):
    """The CLI cut its own output off mid-JSON."""


def paged(gitnexus: str, cwd: Path, body: str, projection: str, order: str) -> list[dict]:
    """Run `body RETURN projection ORDER BY order` in pages, halving the page when the CLI truncates.

    THE `ORDER BY` IS NOT COSMETIC. `SKIP`/`LIMIT` over an unordered result has no defined row order
    in a graph database, so successive pages may skip rows and repeat others — and the harness's own
    determinism check caught exactly that: two runs of this adapter over one fixed index produced
    different edge files, which read as "the tool is non-deterministic" when the instability was
    here. Ordering on the projected columns makes the pagination total and repeatable.
    """
    out: list[dict] = []
    skip = 0
    page = PAGE
    while True:
        try:
            rows = run_cypher(gitnexus, cwd,
                              f"{body} RETURN {projection} ORDER BY {order} "
                              f"SKIP {skip} LIMIT {page}")
        except Truncated:
            page //= 2
            if page < 1:
                raise SystemExit("gitnexus truncates even a single-row page")
            continue
        out.extend(rows)
        if len(rows) < page:
            return out
        skip += len(rows)


def _from_markdown(md: str) -> list[dict]:
    """The CLI prints a markdown table when it has no structured mode; parse it rather than
    depending on a flag that may not exist in every release."""
    lines = [ln.strip() for ln in md.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return []
    header = [c.strip() for c in lines[0].strip("|").split("|")]
    out = []
    for ln in lines[2:]:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        if len(cells) == len(header):
            out.append(dict(zip(header, cells)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gitnexus", required=True)
    ap.add_argument("--src", required=True, type=Path)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--edges", required=True, type=Path)
    ap.add_argument("--label", default="gitnexus")
    ap.add_argument("--meta", default="")
    ap.add_argument("--build", default="source only", choices=BUDGETS)
    a = ap.parse_args()

    global ROOT
    ROOT = str(a.src)

    rows = paged(a.gitnexus, a.src,
                 "MATCH (s)-[r:CodeRelation]->(t) WHERE r.type = 'CALLS'",
                 "s.id AS sid, t.id AS tid, s.filePath AS sfile, s.startLine AS sline, "
                 "r.confidence AS conf, r.reason AS reason",
                 order="sid, tid, sline")

    edges: list[Edge] = []
    for row in rows:
        s = parse_id(row.get("sid", ""))
        t = parse_id(row.get("tid", ""))
        if s is None or t is None:
            continue
        _, sfile, caller = s
        _, tfile, callee = t      # the target id names ITS OWN file — issue #11
        if caller.type is None:            # a call attributed to a non-method node
            continue
        # GitNexus's CALLS relation carries no call-site line — `s.startLine` is the CALLER's
        # declaration row (4% of rows land on a call line, #72 §1). A wrong line is worse than none:
        # the line-based placements (#17, #18, #22) must simply not apply to this tool.
        line = None
        _decl_line = row.get("sline")
        try:
            _decl_line = int(_decl_line)
        except (TypeError, ValueError):
            _decl_line = None
        # the tool's OWN confidence term: every CALLS relation carries `confidence` (0–1) and
        # `reason` (`import-resolved`, …). Carried verbatim so the report can score each class of
        # the tool's answers on its own; the first version of this adapter did not read it.
        reason = row.get("reason") or "unlabelled"
        conf = row.get("conf")
        label = f"{reason}:{conf}" if conf not in (None, "") else reason
        edges.append(Edge(caller=caller, callee=callee,
                          file=row.get("sfile") or sfile, line=line, callee_file=tfile,
                          confidence=label))

    out = ToolOutput(tool=a.label, subject=a.subject, edges=edges, declared_tier=Tier.B,
                     meta={"rows": len(edges), "version": a.meta, "build": a.build})
    write_edges(a.edges, out)
    print(f"{a.label}/{a.subject}: {len(edges)} edges -> {a.edges}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
