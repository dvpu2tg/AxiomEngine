#!/usr/bin/env python3
"""Call CHAINS — whether a tool's graph answers the question people actually ask of it.

WHY AN EDGE METRIC IS NOT ENOUGH
--------------------------------
Nobody opens a call graph to look at one edge. They ask "if I change this method, what breaks?" and
"can this entry point reach that sink?" — both of which are questions about PATHS. A graph can be
excellent edge-by-edge and useless for either, because path error compounds: a chain is only as
sound as its weakest edge, and a graph that over-approximates 20% per hop over-approximates far more
than 20% over three hops.

That compounding is also the reason this module exists at all. At the edge level, answering "all of
them" is free — the whole CHA envelope scores precision 1.000, recall_possible 1.000, F1 and MCC at
ceiling, because a false positive is counted only OUTSIDE the envelope and the envelope is what was
emitted. Nothing in an edge-level table can tell that answer apart from a tool that resolved every
call. Over three hops it separates immediately: on netty-transport the envelope answer reaches
35,225 method pairs where the truth reaches 8,100. A change-impact consumer asking what one method
affects gets 4.3x the real answer.

WHAT IS MEASURED
----------------
`reach@k` — the set of ordered pairs `(a, b)` with a call path from `a` to `b` of length 1..k. Sets,
not path enumerations: the pair set is polynomial and stable, where the path count explodes and is
dominated by however many ways there are to walk the same cycle. k = 1 is exactly the edge metric,
which is what makes the k-series readable as one story rather than as a second, unrelated score.

Both bounds come along, because the same trap applies one level up. Scoring a tool's closure against
the closure of the POSSIBLE graph reproduces the edge-level flaw exactly — the envelope's closure is
inside the envelope's closure by construction, so its precision is 1.000 at every depth. So:

    chain_recall@k      |ans & truth| / |truth|    of the reachability that is undeniable, how much?
    chain_precision@k   |ans & truth| / |ans|      of what you claim is reachable, how much is real?
    chain_precision_env |ans & truth| / (tp + fp)  the permissive bound, fp counted outside `env`
    blowup@k            |ans| / |truth|            how many times the real answer a consumer gets

`chain_precision` is deliberately the HARSH bound: at a genuinely ambiguous virtual call the CHA
envelope is the sound answer and this charges for it. It is not "the right number" on its own any
more than `chain_precision_env` is — they are the two ends, and a tool's honesty is where it sits
between them. Printing only one of them is how the edge-level metric came to be gameable.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from groundtruth import GroundTruth
from model import Tier

# 1 is the edge metric itself; 3 is where over-approximation has compounded enough to be unmistakable
# and still costs under a tenth of a second on the largest subject measured.
DEPTHS = (1, 2, 3)


class Bits:
    """Per-node reachability as Python-int bitsets over one shared node index.

    The set-of-pairs version took minutes on rxjava, whose CHA envelope is 696k edges over 9.6k
    methods: its depth-3 closure is tens of millions of pairs, and a Python set of tuples is the
    wrong shape for that. A bitset per source node makes the closure a handful of ORs per node
    and every metric a popcount; the result is identical, pair for pair.
    """

    def __init__(self, index: dict[str, int]):
        self.index = index
        self.rows: dict[int, int] = {}

    @staticmethod
    def from_edges(edges: set[tuple[str, str]], index: dict[str, int]) -> "Bits":
        b = Bits(index)
        for a, c in edges:
            ia, ic = index.get(a), index.get(c)
            if ia is None or ic is None:
                continue
            b.rows[ia] = b.rows.get(ia, 0) | (1 << ic)
        return b

    def closure(self, k: int) -> "Bits":
        """Ordered pairs joined by a path of length 1..k, as bitsets."""
        succ = self.rows
        reach = dict(succ)
        frontier = dict(succ)
        for _ in range(k - 1):
            nxt: dict[int, int] = {}
            for a, fr in frontier.items():
                acc = 0
                f = fr
                while f:
                    low = f & -f
                    b = low.bit_length() - 1
                    f ^= low
                    acc |= succ.get(b, 0)
                new = acc & ~reach.get(a, 0)
                if new:
                    reach[a] = reach.get(a, 0) | new
                    nxt[a] = new
            if not nxt:
                break
            frontier = nxt
        out = Bits(self.index)
        out.rows = reach
        return out

    def size(self) -> int:
        return sum(r.bit_count() for r in self.rows.values())

    def inter(self, other: "Bits") -> int:
        return sum((r & other.rows.get(a, 0)).bit_count() for a, r in self.rows.items())

    def minus(self, other: "Bits") -> int:
        return sum((r & ~other.rows.get(a, 0)).bit_count() for a, r in self.rows.items())


def closure(edges: set[tuple[str, str]], k: int) -> set[tuple[str, str]]:
    """Ordered pairs joined by a path of length 1..k (the reference, set-of-pairs form; used by
    the self-test to check the bitset form pair for pair)."""
    succ: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        succ[a].add(b)
    reach = set(edges)
    frontier = set(edges)
    for _ in range(k - 1):
        nxt = set()
        for a, b in frontier:
            for c in succ.get(b, ()):
                p = (a, c)
                if p not in reach:
                    reach.add(p)
                    nxt.add(p)
        if not nxt:
            break
        frontier = nxt
    return reach


@dataclass
class ChainTruth:
    """The two bounds' closures for one subject at one tier, computed once and shared by every tool."""
    tier: Tier
    index: dict[str, int] = field(default_factory=dict)
    truth: dict[int, Bits] = field(default_factory=dict)
    env: dict[int, Bits] = field(default_factory=dict)

    @staticmethod
    def build(gt: GroundTruth, tier: Tier, depths=DEPTHS) -> "ChainTruth":
        def at(pairs):
            out = set()
            for a, b in pairs:
                pa, pb = a.at(tier), b.at(tier)
                if pa is not None and pb is not None:
                    out.add((pa, pb))
            return out

        certain, possible = at(gt.certain_edges()), at(gt.possible_edges())
        # one node index for the subject: every method name at this tier, plus anything the
        # bounds mention (a tool's row naming something outside it is simply not a pair here)
        names = {m.at(tier) for m in gt.methods}
        names.discard(None)
        for a, b in certain | possible:
            names.add(a)
            names.add(b)
        index = {n: i for i, n in enumerate(sorted(names))}
        ct = ChainTruth(tier=tier, index=index)
        cb, pb = Bits.from_edges(certain, index), Bits.from_edges(possible, index)
        for k in depths:
            ct.truth[k] = cb.closure(k)
            ct.env[k] = pb.closure(k)
        return ct


@dataclass
class ChainScore:
    """One tool's reachability answer, at one tier, across the depth series."""
    tier: Tier
    by_depth: dict[int, dict] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"tier": self.tier.value,
                "by_depth": {str(k): v for k, v in sorted(self.by_depth.items())}}


def score_chains(emitted: set[tuple[str, str]], truth: ChainTruth, depths=DEPTHS) -> ChainScore:
    """Score a tool's edge set as a reachability answer at each depth."""
    cs = ChainScore(tier=truth.tier)
    base = Bits.from_edges(emitted, truth.index)
    for k in depths:
        ans = base.closure(k)
        t, env = truth.truth[k], truth.env[k]
        n_ans, n_t = ans.size(), t.size()
        tp = ans.inter(t)
        fp_env = ans.minus(env)
        cs.by_depth[k] = {
            "reach": n_ans,
            "truth": n_t,
            "recall": tp / n_t if n_t else None,
            # The harsh bound: everything claimed reachable that the declared graph does not reach.
            "precision": tp / n_ans if n_ans else None,
            # The permissive bound, mirroring the edge-level `precision`.
            "precision_env": tp / (tp + fp_env) if (tp + fp_env) else None,
            "blowup": n_ans / n_t if n_t else None,
        }
    return cs
