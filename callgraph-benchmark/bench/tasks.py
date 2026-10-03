"""Task-level scores: the questions a consumer actually asks a call graph, each scored against
the ground truth on its own terms (issue: "5–10 different tests").

The edge metrics say whether individual links are right. These say whether the ANSWERS a
graph gives to the questions people run on it are right — the questions the engine's own
`schema_queries` lists (callers_of, callees_of, blast radius, reachability, blind spots) and the
ones a navigation tool advertises (`path A B`). Every task is computed from the same Tier-B edge
set the headline is scored on, against the same ground truth, with deterministic sampling
(seeded), so a tool cannot do well here by a different reading of its output.

    callees_of   for each method with ≥1 declared callee: F1 of the tool's callee set against
                 the declared set (precision inside the envelope, recall against CERTAIN); mean
    callers_of   the same, reversed, per callee
    path         of 500 sampled (A, B) pairs joined by a declared call path of 1–3 hops, the
                 share the tool's graph also joins within 6 hops
    blast_radius for 300 sampled methods: Jaccard of the transitive CALLERS within 3 hops
                 (what changes if I change this) against the truth's; mean
    uncalled     "nothing calls X": precision and recall of the tool's uncalled-method claims
                 against the methods the declared graph never calls
    dispatch     for the genuinely ambiguous groups: Jaccard of the tool's target set against
                 the runnable set; mean
    file_deps    file → file call dependencies: F1 against the declared graph's
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from chains import Bits
from language import is_type_segment


@dataclass
class TaskScores:
    tasks: dict[str, dict] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return dict(self.tasks)


def _f1(p: float | None, r: float | None) -> float | None:
    if p is None or r is None or p + r == 0:
        return None
    return 2 * p * r / (p + r)


def _per_node_f1(answer: dict[str, set[str]], truth: dict[str, set[str]], accepted: dict[str, set[str]]) -> dict:
    """Mean per-node F1 over the nodes the truth has an answer for; a node the tool says nothing
    about scores 0 (a missed question is a wrong answer to it)."""
    vals: list[float] = []
    for node, want in truth.items():
        got = answer.get(node, set())
        ok = accepted.get(node, set()) | want
        if not got:
            vals.append(0.0)
            continue
        p = len(got & ok) / len(got)
        r = len(got & want) / len(want)
        vals.append(_f1(p, r) or 0.0)
    # math.fsum, not sum(): `vals` is filled in set order, which varies per process, and before
    # Python 3.12 a float sum() depends on its order in the last bits, so scores.json differed
    # between two scorings of identical inputs (#93)
    return {"n": len(vals), "mean_f1": math.fsum(vals) / len(vals) if vals else None}


def score_tasks(emitted: set[tuple[str, str]], certain: set[tuple[str, str]], possible: set[tuple[str, str]],
                accepted: set[tuple[str, str]], methods: set[str], ambiguous_groups, seed: int = 1) -> TaskScores:
    ts = TaskScores()
    rng = random.Random(seed)

    def by_src(edges):
        d: dict[str, set[str]] = {}
        for a, b in edges:
            d.setdefault(a, set()).add(b)
        return d

    def by_dst(edges):
        d: dict[str, set[str]] = {}
        for a, b in edges:
            d.setdefault(b, set()).add(a)
        return d

    # ── callees_of / callers_of ──────────────────────────────────────────────────────────
    ts.tasks["callees_of"] = _per_node_f1(by_src(emitted), by_src(certain), by_src(accepted))
    ts.tasks["callers_of"] = _per_node_f1(by_dst(emitted), by_dst(certain), by_dst(accepted))

    # ── one node index for the closures ──────────────────────────────────────────────────
    names = set(methods)
    for a, b in certain | possible | emitted:
        names.add(a)
        names.add(b)
    index = {n: i for i, n in enumerate(sorted(names))}
    inv = {i: n for n, i in index.items()}
    truth_b = Bits.from_edges(certain, index)
    tool_b = Bits.from_edges(emitted, index)
    truth3 = truth_b.closure(3).rows
    tool6 = tool_b.closure(6).rows

    # ── path: sampled declared pairs within 3 hops → does the tool's graph join them? ────
    pairs: list[tuple[int, int]] = []
    for a, bits in truth3.items():
        b = bits
        while b:
            low = b & -b
            pairs.append((a, low.bit_length() - 1))
            b ^= low
    # the bitset rows come out in set-iteration order, which Python randomises per process:
    # sorted before the seeded shuffle, so two runs draw the same sample (verify.sh gate 1)
    pairs.sort()
    rng.shuffle(pairs)
    sample = pairs[:500]
    joined = sum(1 for a, b in sample if (tool6.get(a, 0) >> b) & 1)
    ts.tasks["path"] = {"n": len(sample), "found": joined, "share": joined / len(sample) if sample else None}

    # ── blast radius: transitive callers within 3 hops, Jaccard per sampled method ───────
    rev_truth = Bits.from_edges({(b, a) for a, b in certain}, index).closure(3).rows
    rev_tool = Bits.from_edges({(b, a) for a, b in emitted}, index).closure(3).rows
    targets = sorted(rev_truth)                # methods something calls, transitively
    rng.shuffle(targets)
    js: list[float] = []
    for i in targets[:300]:
        t, g = rev_truth.get(i, 0), rev_tool.get(i, 0)
        union = (t | g).bit_count()
        js.append((t & g).bit_count() / union if union else 1.0)
    ts.tasks["blast_radius"] = {"n": len(js), "mean_jaccard": math.fsum(js) / len(js) if js else None}

    # ── uncalled: "nothing calls X" ──────────────────────────────────────────────────────
    called_truth = {b for _, b in certain}
    called_tool = {b for _, b in emitted}
    universe = set(methods)
    unc_truth = universe - called_truth
    unc_tool = universe - called_tool
    tp = len(unc_tool & unc_truth)
    ts.tasks["uncalled"] = {"claims": len(unc_tool), "truth": len(unc_truth),
                            "precision": tp / len(unc_tool) if unc_tool else None,
                            "recall": tp / len(unc_truth) if unc_truth else None}

    # ── dispatch: the ambiguous groups, Jaccard against the runnable set ─────────────────
    src = by_src(emitted)
    js = []
    for g in ambiguous_groups:
        want = g["possible"]
        got = {b for b in src.get(g["caller"], set()) if b.split("#", 1)[-1].split("(", 1)[0] == g["name"]}
        union = len(want | got)
        js.append(len(want & got) / union if union else 1.0)
    ts.tasks["dispatch"] = {"n": len(js), "mean_jaccard": math.fsum(js) / len(js) if js else None}

    # ── file_deps: file → file call dependencies ────────────────────────────────────────
    def file_of(m: str) -> str:
        t = m.split("#", 1)[0]
        if ":" in t or "/" in t:                       # TypeScript: `module:Container` — the module
            return t.split(":", 1)[0]
        parts = t.split(".")                           # Java: package + the first capitalised segment
        for i, seg in enumerate(parts):
            if is_type_segment(seg):
                top = ".".join(parts[: i + 1]).split("$anon:", 1)[0]
                # `Outer$Inner` is the binary spelling of a nested class and lives in Outer's file;
                # a type whose own name STARTS with `$` (gson's `$Gson$Types`) has no such split (#97)
                return top if seg.startswith("$") else top.split("$", 1)[0]
        return t
    fd_truth = {(file_of(a), file_of(b)) for a, b in certain if file_of(a) != file_of(b)}
    fd_acc = {(file_of(a), file_of(b)) for a, b in accepted if file_of(a) != file_of(b)}
    fd_tool = {(file_of(a), file_of(b)) for a, b in emitted if file_of(a) != file_of(b)}
    p = len(fd_tool & (fd_acc | fd_truth)) / len(fd_tool) if fd_tool else None
    r = len(fd_tool & fd_truth) / len(fd_truth) if fd_truth else None
    ts.tasks["file_deps"] = {"truth": len(fd_truth), "claims": len(fd_tool), "precision": p, "recall": r, "f1": _f1(p, r)}
    return ts
