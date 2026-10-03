#!/usr/bin/env python3
"""The canonical schema every tool's output is translated into, and the fidelity tiers that make
tools with different output structures comparable without punishing any of them.

THE PROBLEM THIS MODULE EXISTS TO SOLVE
---------------------------------------
The tools under test do not agree on what a call edge IS.

    java.lang.classfile / CodeQL  →  torture.Shape#area(int)      owner + name + erased params
    axiomengine              →  torture.Shape#area(int)      owner + name + params
    tree-sitter indexers          →  Shape.area                   owner + name, no params
    some graph exporters          →  area                         a bare symbol name

Scoring all four against a signature-exact oracle would report the last two as near-zero. That
number would be an artefact of the comparison, not a finding about the tool: an indexer that
correctly linked `b.area()` to `Shape.area` did the work, it just cannot spell the answer in the
oracle's alphabet. Reporting that as a miss is measuring our own scoring choice.

THE FIX: PROJECT BOTH SIDES TO THE SAME TIER
--------------------------------------------
Every comparison happens at a declared fidelity tier, and the GROUND TRUTH IS PROJECTED TO THAT TIER
TOO. At Tier B, `Shape#area(int)` and `Shape#area(long)` collapse to `Shape#area` on both sides, so
a tool that cannot express parameter types is compared against an oracle that is not expressing them
either. It is charged for nothing it did not get wrong.

    Tier A   type#name(p1,p2)   signature-exact — the only tier at which overload selection is
                                visible, and therefore the only tier at which a tool can be given
                                credit for getting it right
    Tier B   type#name          owner-qualified — the highest fidelity EVERY tool under test can
                                express, and therefore where the headline number is read
    Tier C   name               bare symbol — the floor; reported so a name-only tool has a number
                                at all, and read knowing that name collisions inflate it

A tool declares the highest tier it can emit. At a tier ABOVE its declared ceiling it is reported
as `n/a` — never as zero. A blank and a zero mean opposite things and the report must not conflate
them.

WHAT IS NOT CHARITY
-------------------
Projection is symmetric and mechanical. It never repairs a wrong answer, only stops counting a
difference in vocabulary as a wrong answer. A tool that names the wrong type is wrong at every
tier; a tool that names no type is scored at Tier C, where naming no type costs nothing — and the
report states that its Tier A and Tier B cells are absent by construction, so nobody reads its
Tier C number as comparable to another tool's Tier A.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable, Iterator


# What a tool required in order to answer, weakest to strongest. A CLOSED vocabulary, because a
# free-form string lets a run invent a label the report has no definition for — and because the old
# default (`"source only"`) failed OPEN in the most flattering direction: a tool staged with 63
# pre-typed platform IR modules was reported on the same budget as a tree-sitter indexer that gets
# nothing. Adapters must now declare it explicitly; forgetting is an error, not a flattering default.
BUDGETS = (
    "source only",           # the source tree, nothing else
    "build-mode=none",       # an indexer's own database, built without compiling
    "source + platform IR",  # source PLUS a staged, pre-typed model of the platform library
    "compiled build",        # source plus a full type-resolved compile (javac, classpath)
    "bytecode",              # the compiled class files — what the ORACLE itself reads
    "oracle",                # the ground truth itself — only the `ideal` reference row (#6)
)


class Tier(str, Enum):
    """A fidelity level at which both sides of a comparison are spelled."""
    A = "A"   # type#name(params)
    B = "B"   # type#name
    C = "C"   # name

    @property
    def rank(self) -> int:
        return {"A": 3, "B": 2, "C": 1}[self.value]

    def __le__(self, other: "Tier") -> bool:   # type: ignore[override]
        return self.rank <= other.rank

    @staticmethod
    def ordered() -> list["Tier"]:
        return [Tier.A, Tier.B, Tier.C]


# `pkg.Type#name(P1,P2)` — the oracle's spelling. `params` may be the literal `*` for a folded
# lambda body, which projects to itself at Tier A (it is not a parameter list, it is "unknowable").
REF_RE = re.compile(r"^(?P<type>[^#]*)#(?P<name>[^(]+)(?:\((?P<params>.*)\))?$")


def _split_params(body: str) -> tuple[str, ...]:
    """Split a parameter list on top-level commas only.

    Java's erased simple names never nest, so a plain `split(",")` was right there. A TypeScript
    signature is not: `map((a:A,b:B)=>C)` is ONE parameter whose text contains a comma, and
    splitting it naively invents a second parameter that exists on neither side of the comparison.
    """
    out: list[str] = []
    depth = 0
    cur = ""
    for ch in body:
        if ch in "(<[{":
            depth += 1
        elif ch in ")>]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return tuple(p for p in out if p)


@dataclass(frozen=True, order=True)
class Ref:
    """A reference to a method, carrying only what the emitting tool could actually express.

    `type` is None when the tool named no owner; `params` is None when it named no parameter list.
    None means "not expressible", which is what the tier machinery reads. It never means "empty":
    a no-argument method has `params == ()`, and the difference decides whether a tool is scored at
    Tier A or excused from it.
    """
    name: str
    type: str | None = None
    params: tuple[str, ...] | None = None

    def at(self, tier: Tier) -> str | None:
        """This reference spelled at `tier`, or None when it cannot be spelled there."""
        if tier is Tier.C:
            return self.name
        if self.type is None:
            return None
        if tier is Tier.B:
            return f"{self.type}#{self.name}"
        if self.params is None:
            return None
        if "*" in self.params:
            # UNKNOWN, not empty. This is the fallback spelling for a lambda body no invokedynamic
            # references, where the container's real signature could not be recovered. At Tier A it
            # would match nothing on either side, so the row is declared unspellable here and
            # excluded from BOTH sides with a count, rather than scored as everyone's miss.
            return None
        return f"{self.type}#{self.name}({','.join(self.params)})"

    @property
    def max_tier(self) -> Tier:
        if self.type is not None and self.params is not None:
            return Tier.A
        if self.type is not None:
            return Tier.B
        return Tier.C

    @staticmethod
    def parse(s: str) -> "Ref":
        """Parse the oracle spelling `pkg.Type#name(P1,P2)`; also accepts `pkg.Type#name` and `name`."""
        m = REF_RE.match(s)
        if not m:
            return Ref(name=s)
        raw_params = m.group("params")
        params: tuple[str, ...] | None
        if raw_params is None:
            params = None
        elif raw_params == "":
            params = ()
        elif raw_params == "*":
            params = ("*",)
        else:
            params = _split_params(raw_params)
        t = m.group("type") or None
        return Ref(name=m.group("name"), type=t, params=params)

    def __str__(self) -> str:
        return self.at(self.max_tier) or self.name


@dataclass(frozen=True)
class Edge:
    """One caller -> callee link as a tool reported it, with whatever provenance it gave.

    `line` and `file` are optional and used only for the call-site-level report; every headline
    metric is computed without them, because requiring them would silently exclude every tool that
    does not emit them — which is the same punishment this module exists to avoid.
    """
    caller: Ref
    callee: Ref
    file: str | None = None
    line: int | None = None
    # The file the CALLEE was declared in, when the tool reports it separately. Resolving the
    # callee against the CALLER's file placed 9,342 of gitnexus's rows on rxjava as ambiguous — the
    # tool had said exactly which file each target lived in and the harness threw it away.
    callee_file: str | None = None
    # What the tool itself said about its confidence, verbatim and unused by scoring. Kept so the
    # report can say whether a tool's own error labelling predicts its errors.
    confidence: str | None = None

    def at(self, tier: Tier) -> tuple[str, str] | None:
        a, b = self.caller.at(tier), self.callee.at(tier)
        return None if a is None or b is None else (a, b)


@dataclass
class ToolOutput:
    """One tool's answer for one subject, plus the declarations the report needs to be honest."""
    tool: str
    subject: str
    edges: list[Edge] = field(default_factory=list)
    # The highest tier this tool's OUTPUT FORMAT can express, declared by its adapter rather than
    # inferred from the rows. Inferring it would let one lucky fully-qualified row promote a tool
    # into a tier it cannot generally reach, and then score every other row of it as a miss.
    declared_tier: Tier = Tier.C
    # Free-form, recorded verbatim into the results manifest: version, command line, duration.
    meta: dict = field(default_factory=dict)

    def at(self, tier: Tier) -> set[tuple[str, str]]:
        """The edge set at `tier`. Rows that cannot be spelled there are dropped — see
        `unspellable_at` for the count, which the report prints beside the score so a tier whose
        denominator quietly shrank cannot be read as a clean result."""
        out: set[tuple[str, str]] = set()
        for e in self.edges:
            p = e.at(tier)
            if p is not None:
                out.add(p)
        return out

    def unspellable_at(self, tier: Tier) -> int:
        return sum(1 for e in self.edges if e.at(tier) is None)


# ── serialisation ────────────────────────────────────────────────────────────────────────────
# One JSON object per line. Adapters write this and nothing else; every downstream stage reads it
# and nothing else. The boundary is deliberate: an adapter may shell out to a tool, read a SQLite
# file or scrape a report, and none of that reaches the scorer.

def _ref_to_json(r: Ref) -> dict:
    d: dict = {"name": r.name}
    if r.type is not None:
        d["type"] = r.type
    if r.params is not None:
        d["params"] = list(r.params)
    return d


def _ref_from_json(d: dict | str) -> Ref:
    if isinstance(d, str):
        return Ref.parse(d)
    params = d.get("params")
    return Ref(
        name=d["name"],
        type=d.get("type"),
        params=None if params is None else tuple(params),
    )


def repo_relative(p) -> str:
    """How an adapter must spell a path it records in `_meta` — relative to the REPOSITORY root,
    with `/` separators, on every machine.

    `_meta` is the first line of the edge file, and `run.input_sha256["edges/<tool>"]` hashes that
    file. An absolute `_meta.source` therefore makes the manifest entry a statement about WHERE THE
    CHECKOUT IS, not about what the tool emitted: the same tool, on the same subject, run from
    `/home/runner/bench` instead of `/Users/x/bench`, produces a different hash with an identical
    graph. PROTOCOL §8 says a results directory whose manifest does not reproduce cannot be
    trusted, so a hash that reports drift where there is none also hides real drift behind an
    expected difference — and `verify.sh` gate 3 re-hashes exactly these entries (#104).

    The provenance is NOT dropped to get the hash stable. `.work/typescript/torture/gfy/src/
    graphify-out/graph.json` identifies the input exactly as well as the absolute form did; it just
    says it the same way everywhere. A path that lies OUTSIDE the repository is left absolute —
    it is outside the harness's control and the manifest should say so plainly, rather than hide it
    behind a relative spelling that would resolve somewhere else entirely.
    """
    root = Path(__file__).resolve().parents[1]
    try:
        # as_posix(), not str(): a Windows run must hash to what a POSIX run hashes (#45).
        return Path(p).resolve().relative_to(root).as_posix()
    except ValueError:
        return str(p)


def write_edges(path: Path, out: ToolOutput) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for e in out.edges:
        row: dict = {"caller": _ref_to_json(e.caller), "callee": _ref_to_json(e.callee)}
        if e.file is not None:
            row["file"] = e.file
        if e.line is not None:
            row["line"] = e.line
        if e.callee_file is not None:
            row["callee_file"] = e.callee_file
        if e.confidence is not None:
            row["confidence"] = e.confidence
        rows.append(json.dumps(row, sort_keys=True, separators=(",", ":")))
    # Sorted, so a tool that enumerates its graph in a hash-dependent order still produces a
    # byte-identical file across runs. A benchmark that cannot diff two runs cannot detect drift.
    rows.sort()
    meta = dict(out.meta)
    # the backstop for an adapter that recorded its input absolutely (#104); a spelling that is
    # already relative is left alone rather than re-resolved against whatever the cwd is
    src = meta.get("source")
    if src:
        meta["source"] = repo_relative(src) if Path(src).is_absolute() else Path(src).as_posix()
    header = json.dumps(
        {"_meta": {"tool": out.tool, "subject": out.subject,
                   "declared_tier": out.declared_tier.value, **meta}},
        sort_keys=True, separators=(",", ":"))
    # newline="\n": Path.write_text would translate to the platform's separator on Windows, and
    # the edge files are hashed into the manifest (#45)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(header + "\n" + "\n".join(rows) + ("\n" if rows else ""))


def read_edges(path: Path) -> ToolOutput:
    edges: list[Edge] = []
    meta: dict = {}
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        d = json.loads(ln)
        if "_meta" in d:
            meta = d["_meta"]
            continue
        edges.append(Edge(
            caller=_ref_from_json(d["caller"]),
            callee=_ref_from_json(d["callee"]),
            file=d.get("file"),
            line=d.get("line"),
            callee_file=d.get("callee_file"),
            confidence=d.get("confidence"),
        ))
    return ToolOutput(
        tool=meta.get("tool", path.parent.name),
        subject=meta.get("subject", "?"),
        edges=edges,
        declared_tier=Tier(meta.get("declared_tier", "C")),
        meta={k: v for k, v in meta.items() if k not in ("tool", "subject", "declared_tier")},
    )


def iter_jsonl(path: Path) -> Iterator[dict]:
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if ln:
            yield json.loads(ln)


def dedupe(edges: Iterable[Edge]) -> list[Edge]:
    """Collapse rows that differ only in provenance.

    A tool that reports the same link once per call site is not more correct than one that reports
    it once, and an edge-level metric that counted them twice would reward verbosity. Site-level
    metrics read the original list, so nothing is lost.
    """
    seen: dict[tuple, Edge] = {}
    for e in edges:
        seen.setdefault((e.caller, e.callee), e)
    return list(seen.values())
