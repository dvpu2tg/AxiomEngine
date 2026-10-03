#!/usr/bin/env python3
"""Adapter: axiom-code-graph (the type-directed Datalog engine) -> the canonical edge schema.

WHAT THE TOOL EMITS
-------------------
`call-chain-edges.csv`, tab-separated, no header:

    FromExpr  FromMethod  ToExpr  ToMethod  Prov  EdgeStatus  Kind

`FromMethod` and `ToMethod` are content hashes into the parser's `all-methods.csv` registry, so the
adapter's whole job is the join back to names, plus the parameter list from
`all-method-parameters.csv`. `EdgeStatus` is the engine's own confidence label — `known_edge`,
`multi_inferred`, `boundary_lib`, `ambiguous_unknown` — carried through verbatim and never used by
the scorer, so the report can ask whether a tool's self-assessment predicts its errors.

TIER: A. The IR carries owner, method name and an erased parameter list, so this tool can be scored
at every tier including overload selection.

ONE CONVENTION THIS TOOL LOSES, AND WHY THE ADAPTER DOES NOT HIDE IT
---------------------------------------------------------------------
The engine's IR FLATTENS nested types: `torture.F02Generics.Node` and `torture.F07Modern.Node` are
both `torture.Node`. That is a documented limitation of the tool, not of its output format, so the
adapter must not repair it — writing the nesting back in from the file path would be scoring a
reconstruction the tool did not perform.

What the adapter DOES do is emit the `file` field the IR already carries on every method. The
resolver uses it to narrow a flattened name to the type the file declares, which is reading the
tool's own output rather than repairing it. Where even that leaves two candidates, the row is
reported AMBIGUOUS and excluded, and the count appears beside the score.

    python3 adapters/axiom/adapt.py --ir <client-ir> --out <engine-out> --subject <name> \
                                    --edges <dest.jsonl>
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

# The shared scoring core lives at the repo root, not under the language tree; find it by walking
# up rather than by counting directories, so moving an adapter cannot silently break the import.
_here = Path(__file__).resolve()
_root = next(p for p in _here.parents if (p / "bench" / "model.py").exists())
sys.path.insert(0, str(_root / "bench"))

from model import BUDGETS, Edge, Ref, Tier, ToolOutput, repo_relative, write_edges   # noqa: E402


def read_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def load_methods(ir: Path) -> tuple[dict[str, Ref], dict[str, str]]:
    """method-registry hash -> Ref, with the owner, the name and the erased parameter list."""
    params: dict[str, list[tuple[int, str]]] = defaultdict(list)
    ppath = ir / "all-method-parameters.csv"
    if ppath.exists():
        for r in read_tsv(ppath):
            h = r.get("methodRegistryLinkHash") or ""
            if not h:
                continue
            # `parameterBaseType` is the erased type; `parameterTypeName` still carries type
            # arguments. The oracle reads parameters out of an erased descriptor, so the erased
            # column is the one that can be compared; bench/resolve.py erases whatever arrives
            # anyway, so this is belt and braces rather than a transformation.
            t = (r.get("parameterBaseType") or r.get("parameterTypeName") or "").strip()
            if r.get("isVarArgs") == "true" and not t.endswith("[]"):
                t += "[]"
            try:
                pos = int(r.get("position") or 0)
            except ValueError:
                pos = 0
            params[h].append((pos, t))

    out: dict[str, Ref] = {}
    files: dict[str, str] = {}
    for r in read_tsv(ir / "all-methods.csv"):
        h = r.get("methodRegistryUniqueHash") or ""
        if not h:
            continue
        owner = (r.get("ownerQualifiedName") or "").strip() or None
        name = (r.get("name") or "").strip()
        kind = (r.get("methodKind") or "").strip()
        # The engine names a constructor after its type; the oracle spells it `<init>`. The IR
        # states the KIND, so the kind decides: a method that merely shares its class's name is a
        # method (issue #32 §3). The name-equality fallback stays only for a row without a kind.
        if kind == "CONSTRUCTOR" or (not kind and owner and name == owner.rsplit(".", 1)[-1]):
            name = "<init>"
        ps = tuple(t for _, t in sorted(params.get(h, [])))
        out[h] = Ref(name=name, type=owner, params=ps)
        fp = (r.get("filePath") or "").strip()
        if fp:
            files[h] = fp
    return out, files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ir", required=True, type=Path, help="the parser's client IR directory")
    ap.add_argument("--out", required=True, type=Path, help="the solver's output directory")
    ap.add_argument("--subject", required=True)
    ap.add_argument("--edges", required=True, type=Path, help="destination .jsonl")
    ap.add_argument("--label", default="axiom", help="tool name recorded in the output")
    ap.add_argument("--meta", default="", help="free-form note recorded in the manifest")
    ap.add_argument("--build", required=True, choices=BUDGETS)
    # WHICH axiom was measured. The parser and engine are sibling checkouts, not pinned artefacts,
    # so the commit each run used is written into the row's metadata and lands in scores.json.
    ap.add_argument("--parser-commit", default="?")
    ap.add_argument("--engine-commit", default="?")
    a = ap.parse_args()

    methods, files = load_methods(a.ir)

    edges: list[Edge] = []
    by_status: dict[str, int] = {}
    dropped_in_adapter = 0
    # the LINE of each expression, so a row the engine marks `ambiguous_unknown` — "there is a
    # call here and I could not resolve it" — can be handed to the scorer as the tool's own
    # statement about that call site: an `unknown`, not a silent `missed` (#69)
    lines: dict[str, int] = {}
    epath = a.ir / "all-expressions.csv"
    if epath.exists():
        with epath.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                h = (r.get("expressionUniqueHash") or "").strip()
                ln = (r.get("startLine") or "").strip()
                if h and ln.isdigit():
                    lines[h] = int(ln)
    unresolved: list[list] = []
    # A FIELD INITIALIZER's calls are attributed by the IR to the field (a `TYPE_REGISTRY_*`
    # caller, expression owner `FIELD_REGISTRY_*`). The oracle scores them where javac puts them
    # — a static field's in `<clinit>`, an instance field's in the constructor (one site, under
    # the first constructor, #78) — so the row's caller is spelled the same way: `T#<clinit>()`
    # or `T#<init>`, from the field's modifiers and owner. 105 such calls on gson were dropped
    # before this.
    field_caller: dict[str, Ref] = {}
    fpath = a.ir / "all-fields.csv"
    if fpath.exists():
        for r in read_tsv(fpath):
            fh = (r.get("fieldRegistryUniqueHash") or "").strip()
            owner = (r.get("ownerQualifiedName") or "").strip()
            if not fh or not owner:
                continue
            static = "STATIC" in (r.get("fieldModifier") or "")
            field_caller[fh] = Ref(name="<clinit>" if static else "<init>", type=owner, params=() if static else None)
    expr_owner: dict[str, str] = {}
    if epath.exists():
        with epath.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                h = (r.get("expressionUniqueHash") or "").strip()
                o = (r.get("expressionOwnerHash") or "").strip()
                if h and o.startswith("FIELD_REGISTRY"):
                    expr_owner[h] = o
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
            if status == "ambiguous_unknown" and from_m in methods and from_e in lines:
                c = methods[from_m]
                unresolved.append([{"name": c.name, "type": c.type, "params": list(c.params) if c.params is not None else None},
                                   lines[from_e], files.get(from_m)])
            # every status the engine wrote, INCLUDING the rows with no target (`ambiguous_unknown`,
            # `-`): the tool's own statement of what it could not resolve, counted per label so the
            # report can put "it said it did not know" beside "it missed"
            by_status[status] = by_status.get(status, 0) + 1
            caller = methods.get(from_m)
            callee = methods.get(to_m)
            if caller is None and from_m.startswith("TYPE_REGISTRY") and expr_owner.get(from_e) in field_caller:
                caller = field_caller[expr_owner[from_e]]
            if caller is None or callee is None:
                # A TYPE_REGISTRY_* caller (a field initialiser attributed to its type rather than
                # to a method) or a callee in the staged library, absent from the CLIENT registry.
                #
                # COUNTED, NOT SILENTLY DROPPED. Every other adapter's out-of-application rows pass
                # through the resolver and land in `unmapped_rows`, which the report prints beside
                # the score. Discarding these inside the adapter left this tool's `excluded` column
                # understating what it had emitted — the one guarantee the report makes about
                # exclusions ("never a way to look good by answering less") held less firmly for
                # this tool than for the others, and in its own favour.
                dropped_in_adapter += 1
                continue
            # the call's LINE travels with the row: an anonymous class the IR names without its
            # declaration line (`TypeAdapters$anon:TypeAdapter` — gson has forty of those in one
            # file) is placed by the line the call is on (#17), as the TypeScript adapter already did
            edges.append(Edge(caller=caller, callee=callee,
                              file=files.get(from_m), line=lines.get(from_e), confidence=status))

    out = ToolOutput(
        tool=a.label, subject=a.subject, edges=edges, declared_tier=Tier.A,
        # spelled relative to the repository when it lies inside it: the row is byte-identical whether
        # the runner passed --out as a relative or an absolute path (verify.sh gate 1)
        meta={"source": repo_relative(csv_path), "rows_kept": len(edges), "note": a.meta,
              "build": a.build, "dropped_in_adapter": dropped_in_adapter,
              "unresolved_sites": unresolved,
              "rows_by_status": by_status,
              "parser_commit": a.parser_commit, "engine_commit": a.engine_commit},
    )
    write_edges(a.edges, out)
    print(f"{a.label}/{a.subject}: {len(edges)} edges -> {a.edges}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
