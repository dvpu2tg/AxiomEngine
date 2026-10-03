#!/usr/bin/env python3
"""Adapter: axiomengine (TypeScript front end) -> the canonical edge schema.

WHAT THE TOOL EMITS
-------------------
The same `call-chain-edges.csv` as the Java front end, but keyed into the TypeScript registries:

    FromExpr  FromMethod  ToExpr  ToMethod  Prov  EdgeStatus  Kind

`all-typescript-methods.csv` carries `ownerQualifiedName` as `src/t01-classes#Base` — the module
path WITHOUT its extension, `#` as the nesting separator — where the benchmark's canonical container
is `src/t01-classes.ts:Base`. That is a notation difference and `bench/language.py`'s TypeScript
alias table reads it; the adapter does not rewrite it.

A MODULE_INITIALIZER is the module's top-level code. The oracle calls that caller `<module>`, and so
does the parser, so the two already agree.

ARROW FUNCTIONS. The IR records every arrow as a method named `<arrow>` and states its binding
separately: a variable's `boundFunctionLinkHash`, a field's or variable's
`initializerExpressionLinkHash` (through the expression tree, possibly behind a wrapper call), and
for an unbound closure the `enclosingMemberLinkHash` it is nested in. The adapter reads those three
statements — translation, not repair — and names the function the way the oracle does: by its
binding, or folded into its enclosing function. An arrow the IR binds to nothing it can name (an
object-literal property, `register({ perform: (…) => … })`) stays `<arrow>` and is scored as the
tool reported it.

TIER: A. The IR carries an owner, a name and a parameter list, so overload selection is scorable —
which matters more in TypeScript than in Java, because a TS overload set is several DECLARATION
signatures over one implementation and `getResolvedSignature` names the arm.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in _here.parents if (p / "bench" / "model.py").exists())
sys.path.insert(0, str(_root / "bench"))

from model import BUDGETS, Edge, Ref, Tier, ToolOutput, repo_relative, write_edges   # noqa: E402


# an expression row carries the expression's text; excalidraw has literals past the default limit
csv.field_size_limit(1 << 30)

# The wrappers an arrow is idiomatically passed through on its way to a binding. The SAME list the
# oracle's `bindingParent` walks, so both sides name `handleMove = withBatchedUpdates((e) => …)`
# by the field and `const Comp = memo(() => …)` by the variable.
WRAPPERS = frozenset({"CALL_EXPRESSION", "PARENTHESIZED", "AS_EXPRESSION", "SATISFIES_EXPRESSION",
                      "TYPE_ASSERTION", "NON_NULL_EXPRESSION"})
ANON = frozenset({"<arrow>", "<function>", ""})


def read_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def load_methods(ir: Path) -> tuple[dict[str, Ref], dict[str, str], dict[str, str]]:
    params: dict[str, list[tuple[int, str]]] = defaultdict(list)
    ppath = ir / "all-typescript-method-parameters.csv"
    if ppath.exists():
        for r in read_tsv(ppath):
            h = r.get("tsMethodLinkHash") or r.get("methodRegistryLinkHash") or ""
            if not h:
                continue
            t = (r.get("parameterTypeName") or r.get("parameterBaseType") or "").strip()
            try:
                pos = int(r.get("position") or 0)
            except ValueError:
                pos = 0
            params[h].append((pos, t))

    # `export const map = (f) => …` is recorded as a method named `<arrow>`, and SEPARATELY the
    # variable `map` carries `boundFunctionLinkHash` -> that method. The IR states the binding
    # outright, so reading it is translation, not repair. Without it every arrow-function caller and
    # callee is `<arrow>`, which matches nothing on the oracle's side — on fp-ts, whose surface is
    # almost entirely `export const f = (…) => …`, that scored the tool at 4% while it had resolved
    # the calls.
    bound: dict[str, str] = {}
    vpath = ir / "all-typescript-variables.csv"
    if vpath.exists():
        for r in read_tsv(vpath):
            h = (r.get("boundFunctionLinkHash") or "").strip()
            n = (r.get("name") or "").strip()
            if h and n:
                bound.setdefault(h, n)

    # The variable rule above reads a DIRECT binding. Two more bindings are stated in the IR just as
    # plainly, through the expression tree: an arrow that is a CLASS FIELD's initializer
    # (`private onPointerDown = (e) => …`, ~400 of them in excalidraw's App) and an arrow reached
    # through a wrapper call (`handleMove = withBatchedUpdates((e) => …)`, `const C = memo(() => …)`).
    # `all-typescript-expressions.csv` records the arrow as an expression whose
    # `anonymousDeclarationHash` is the method, with its parent chain; a field's or variable's
    # `initializerExpressionLinkHash` names the root of that chain. Walking the wrappers is the same
    # walk the oracle makes, so the two sides name the same function the same way.
    exprs: dict[str, dict] = {}
    epath = ir / "all-typescript-expressions.csv"
    anon_expr: dict[str, str] = {}      # method hash -> the expression that IS the arrow
    if epath.exists():
        for r in read_tsv(epath):
            h = (r.get("tsExpressionUniqueHash") or "").strip()
            if not h:
                continue
            exprs[h] = r
            a = (r.get("anonymousDeclarationHash") or "").strip()
            if a and (r.get("kind") or "") in ("ARROW_FUNCTION", "FUNCTION_EXPRESSION"):
                anon_expr.setdefault(a, h)

    def root_of(eh: str) -> str:
        seen = 0
        while seen < 8:
            parent = (exprs.get(eh, {}).get("parentExpressionHash") or "").strip()
            if not parent or exprs.get(parent, {}).get("kind") not in WRAPPERS:
                return eh
            eh = parent
            seen += 1
        return eh

    init_binding: dict[str, tuple[str, str | None]] = {}   # root expression -> (name, owner)
    fpath = ir / "all-typescript-fields.csv"
    if fpath.exists():
        for r in read_tsv(fpath):
            ie = (r.get("initializerExpressionLinkHash") or "").strip()
            n = (r.get("name") or "").strip()
            if ie and n:
                init_binding.setdefault(ie, (n, (r.get("ownerQualifiedName") or "").strip() or None))
    if vpath.exists():
        for r in read_tsv(vpath):
            ie = (r.get("initializerExpressionLinkHash") or "").strip()
            n = (r.get("name") or "").strip()
            if ie and n:
                init_binding.setdefault(ie, (n, None))

    rows = read_tsv(ir / "all-typescript-methods.csv")
    raw: dict[str, dict] = {}
    for r in rows:
        h = (r.get("tsMethodUniqueHash") or r.get("methodRegistryUniqueHash") or "").strip()
        if h:
            raw[h] = r

    named: dict[str, tuple[str, str | None]] = {}   # method hash -> (name, owner override)

    def name_of(h: str, depth: int = 0) -> tuple[str, str | None]:
        if h in named:
            return named[h]
        r = raw[h]
        owner = (r.get("ownerQualifiedName") or "").strip() or None
        name = (r.get("name") or "").strip()
        kind = (r.get("methodKind") or "").strip()
        if kind == "CONSTRUCTOR":
            out = ("constructor", owner)
        elif kind == "OBJECT_LITERAL_METHOD":
            # `export const AndNode = freeze({ create(…) {…} })` — kysely's whole operation-node
            # layer. The IR owns the method to the MODULE and points `tsTypeLinkHash` at the
            # literal expression; the literal is the variable's initializer behind a wrapper call.
            # The oracle keys the literal by that binding (`function-node.ts:AndNode`), as does
            # every other tool, so the owner is read off the binding when the IR states one.
            lit = (r.get("tsTypeLinkHash") or "").strip()
            if lit in exprs and root_of(lit) in init_binding:
                n, o = init_binding[root_of(lit)]
                out = (name, f"{o or owner}#{n}" if (o or owner) else n)
            else:
                out = (name, owner)
        elif kind == "MODULE_INITIALIZER":
            out = ("<module>", owner)
        elif name not in ANON:
            out = (name, owner)
        elif h in bound:
            out = (bound[h], owner)
        elif h in anon_expr and root_of(anon_expr[h]) in init_binding:
            n, o = init_binding[root_of(anon_expr[h])]
            out = (n, o or owner)
        elif h in anon_expr and exprs.get((exprs.get(root_of(anon_expr[h]), {}).get("parentExpressionHash") or "").strip(), {}).get("kind") == "OBJECT_LITERAL":
            # an object-literal PROPERTY: the oracle names it by the property, the IR does not
            # record the property name, and the adapter does not invent one
            out = (name, owner)
        else:
            # A CLOSURE: unnamed, nested in something. The oracle folds it into the function it is
            # lexically inside; the IR states that function as `enclosingMemberLinkHash`, so the
            # adapter folds the same way. Top-level closures fold to the module.
            encl = (r.get("enclosingMemberLinkHash") or "").strip()
            if encl and encl in raw and encl != h and depth < 12:
                out = name_of(encl, depth + 1)
            else:
                out = ("<module>", (r.get("filePath") or "").strip().rsplit(".", 1)[0] or owner)
        named[h] = out
        return out

    refs: dict[str, Ref] = {}
    files: dict[str, str] = {}
    kinds: dict[str, str] = {}
    for h, r in raw.items():
        name, owner = name_of(h)
        ps = tuple(t for _, t in sorted(params.get(h, [])))
        refs[h] = Ref(name=name, type=owner, params=ps)
        kinds[h] = (r.get("methodKind") or "").strip()
        fp = (r.get("filePath") or "").strip()
        if fp:
            files[h] = fp
    return refs, files, kinds


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--edges", required=True, type=Path)
    ap.add_argument("--label", default="axiom")
    ap.add_argument("--meta", default="")
    ap.add_argument("--build", required=True, choices=BUDGETS)
    # WHICH axiom was measured. The parser and engine are sibling checkouts, not pinned artefacts,
    # so the commit each run used is written into the row's metadata and lands in scores.json.
    ap.add_argument("--parser-commit", default="?")
    ap.add_argument("--engine-commit", default="?")
    a = ap.parse_args()

    methods, files, kinds = load_methods(a.ir)
    # the LINE of each call expression — the same registry the arrow bindings come from — so a
    # row can be matched to the oracle's site record and, where the site is a call through a
    # function value, dropped as neutral the way the oracle drops it
    lines: dict[str, int] = {}
    epath = a.ir / "all-typescript-expressions.csv"
    if epath.exists():
        for r in read_tsv(epath):
            h = (r.get("tsExpressionUniqueHash") or "").strip()
            ln = (r.get("startLine") or "").strip()
            if h and ln.isdigit():
                lines[h] = int(ln)
    edges: list[Edge] = []
    by_status: dict[str, int] = {}
    function_type_targets = 0
    unmapped_rows = 0
    unresolved: list[list] = []   # the tool's own "could not resolve this call" rows (#69)
    # the Soufflé relation the adapter reads: at the output root before the engine's bundle
    # stage, under `raw/` since it (kept only with --debug, which run.sh passes) — #81
    csv_path = a.out / "call-chain-edges.csv"
    if not csv_path.exists() and (a.out / "raw" / "call-chain-edges.csv").exists():
        csv_path = a.out / "raw" / "call-chain-edges.csv"
    if not csv_path.exists():
        raise SystemExit(f"{a.out}: no call-chain-edges.csv (nor raw/); the engine's output layout changed, "
                         f"or the solve did not keep its raw relations — the row is NOT produced")
    with csv_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if len(row) < 7:
                continue
            from_e, from_m, _, to_m, _prov, status, _kind = row[:7]
            # every status the engine wrote, including `ambiguous_unknown` rows with no target —
            # the tool's own statement of what it could not resolve, counted per label
            by_status[status] = by_status.get(status, 0) + 1
            caller, callee = methods.get(from_m), methods.get(to_m)
            if status == "ambiguous_unknown" and caller is not None and from_e in lines:
                unresolved.append([{"name": caller.name, "type": caller.type,
                                    "params": list(caller.params) if caller.params is not None else None},
                                   lines[from_e], files.get(from_m)])
            if caller is None or callee is None:
                # a hash the IR's method registry does not hold — a target outside the staged
                # code, or an engine row with no target. Counted, never silently dropped (#41).
                unmapped_rows += 1
                continue
            # A target that is a FUNCTION TYPE — `f: (t: T) => U`, recorded by the IR as a
            # `<function-type>` signature — is the tool saying the call goes through a function
            # value. The oracle says the same of those sites (`indirect`) and does not score them;
            # scoring the tool's row would charge it a false positive for agreeing with the oracle.
            # Dropped symmetrically, and counted.
            if kinds.get(to_m) == "FUNCTION_TYPE_SIGNATURE":
                function_type_targets += 1
                continue
            edges.append(Edge(caller=caller, callee=callee, file=files.get(from_m),
                              line=lines.get(from_e), confidence=status))

    out = ToolOutput(tool=a.label, subject=a.subject, edges=edges, declared_tier=Tier.A,
                     meta={"source": repo_relative(csv_path), "rows": len(edges), "note": a.meta,
                           "function_type_targets_dropped": function_type_targets,
                           "rows_without_method": unmapped_rows,
                           "unresolved_sites": unresolved,
                           "rows_by_status": by_status,
                           "build": a.build, "parser_commit": a.parser_commit,
                           "engine_commit": a.engine_commit})
    write_edges(a.edges, out)
    print(f"{a.label}/{a.subject}: {len(edges)} edges -> {a.edges}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
