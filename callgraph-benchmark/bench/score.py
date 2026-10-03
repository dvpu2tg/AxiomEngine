#!/usr/bin/env python3
"""The metrics, and the definitions that make them mean something.

WHY THERE ARE THREE RECALLS AND NOT ONE
---------------------------------------
A call graph has more than one kind of truth, and a single recall figure silently picks one:

    recall_certain   of the targets the bytecode DECLARES, how many did the tool find?
                     A miss here is undeniable — the instruction names that method.
    recall_possible  of the sound CHA dispatch envelope, how much did the tool cover?
                     A tool that resolves every static call but never fans a virtual one scores
                     well on `certain` and badly here, which is exactly the distinction wanted.
    recall_rta       of the RTA envelope — the same question restricted to types the application
                     actually instantiates. Between the other two, and the most realistic of the
                     three, at the cost of being unsound in principle.

PRECISION IS MEASURED AGAINST THE ENVELOPE, NOT AGAINST THE FACTS
-----------------------------------------------------------------
`Base b = new Unit(); b.area()` compiles to an invokevirtual naming `Base#area`. A tool that
flow-types the receiver answers `Unit#area` — the method that actually runs. Scoring that against
`certain` would call it a false positive at the moment it got *sharper* than the bytecode. So an
emitted edge counts as correct when it lies inside `possible`, and only an edge outside every
envelope is a false positive. Precision against `certain` is computed too and reported beside it,
because the gap between the two is itself the measurement of how much a tool over-approximates.

ACCURACY IS NOT REPORTED, AND MCC IS
------------------------------------
At this class imbalance accuracy is meaningless: ~99.8% of the (method x method) universe is a
non-edge, so a tool that returns NOTHING scores 0.998. MCC uses all four cells of the contingency
table and collapses to 0 for that tool, which is the honest answer. The universe is stated with
every MCC value, because MCC depends on it and a reader cannot check the figure without it.

EVERY NUMBER CARRIES ITS DENOMINATOR AND ITS EXCLUSIONS
-------------------------------------------------------
`unmapped_rows` (rows whose types could not be placed in the subject unambiguously) and
`unspellable_rows` (rows that cannot be written at the tier being scored) are reported beside every
score they touch. Both EXCLUDE rows from the comparison, and an exclusion that is not printed is a
way to look good by answering less.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from chains import ChainScore, ChainTruth, score_chains
from tasks import score_tasks
from groundtruth import GroundTruth, LinkGroup, groups_at, merge_artefacts, name_pooled, projected_unique
from model import Edge, Ref, Tier, ToolOutput
from resolve import Resolution, Resolver, Verdict, normalise_name

# the spellings tools use for a function they could not name — placed by line, see _resolved_edges
UNNAMED = frozenset({"<arrow>", "<function>", "<function-expression>", "<anonymous>"})


# ── contingency ──────────────────────────────────────────────────────────────────────────────
@dataclass
class Contingency:
    tp: int
    fp: int
    fn: int
    universe: int      # |methods|^2 — every ordered pair that COULD be an edge
    emitted: int = 0   # |E| — everything the tool said, which is what the strict bound divides by

    @property
    def tn(self) -> int:
        return max(0, self.universe - self.tp - self.fp - self.fn)

    @property
    def precision(self) -> float | None:
        d = self.tp + self.fp
        return self.tp / d if d else None

    @property
    def precision_strict(self) -> float | None:
        """TP over EVERYTHING the tool emitted — the bound `precision` does not put on it.

        `precision` counts a false positive only OUTSIDE the accepted envelope, so every edge inside
        the envelope is free: neither a hit nor a miss. That is the right call for a tool that names
        the override which actually runs — and it means a tool that emits the ENTIRE envelope at
        every call site, resolving nothing, scores `precision` 1.000, `recall_possible` ~1.000, F1
        and MCC at ceiling, and tops the uniquely-linked table. Measured on all three Java subjects.

        Recall already carries two bounds so neither can be gamed alone. Precision carried only the
        permissive one. This is the other: `precision` asks *is anything you said impossible?*, this
        asks *how much of what you said was the declared answer?* A soundly-fanning tool sits high
        on the first and low on the second, which is the fact one figure was hiding.

        It is NOT a target to maximise either: a flow-sensitive tool that names the override which
        actually runs is sharper than the bytecode and this bound gives it no credit. That is why
        the report carries an `ideal` reference row — the correct answer for every group — so the
        column is read against a real ceiling rather than against 1.000.
        """
        return self.tp / self.emitted if self.emitted else None

    @property
    def recall(self) -> float | None:
        d = self.tp + self.fn
        return self.tp / d if d else None

    @property
    def f1(self) -> float | None:
        p, r = self.precision, self.recall
        if p is None or r is None or p + r == 0:
            return None
        return 2 * p * r / (p + r)

    @property
    def mcc(self) -> float | None:
        return self._mcc(self.fp)

    def _mcc(self, fp: int) -> float | None:
        tp, fn = self.tp, self.fn
        tn = max(0, self.universe - tp - fp - fn)
        num = tp * tn - fp * fn
        den = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
        return num / den if den else None

    # THE STRICT PAIR. `f1` and `mcc` are built on `precision`, which charges a false positive only
    # outside the envelope — so the null model, which emits the envelope, maxes both on every
    # subject where the envelope covers the sites (6 of 10 in the first audit, issue #1). They are
    # kept in the JSON for the record; the tables print these two, which count every emitted row
    # that is not the declared target as a false positive — the same denominator `precision_strict`
    # uses. Where a subject does not dispatch at all (fp-ts: envelope = declared set) the null model
    # is genuinely the right answer and maxes these too; that is a fact about the subject, and the
    # README says so instead of claiming the column is un-maxable.
    @property
    def fp_strict(self) -> int:
        return max(0, self.emitted - self.tp)

    @property
    def f1_strict(self) -> float | None:
        p, r = self.precision_strict, self.recall
        if p is None or r is None or p + r == 0:
            return None
        return 2 * p * r / (p + r)

    @property
    def mcc_strict(self) -> float | None:
        return self._mcc(self.fp_strict) if self.emitted else None

    def as_dict(self) -> dict:
        return {"tp": self.tp, "fp": self.fp, "fn": self.fn, "tn": self.tn,
                "universe": self.universe, "emitted": self.emitted,
                "precision": self.precision, "precision_strict": self.precision_strict,
                "recall": self.recall, "f1": self.f1, "mcc": self.mcc,
                "f1_strict": self.f1_strict, "mcc_strict": self.mcc_strict}


# ── link-group verdicts ──────────────────────────────────────────────────────────────────────
EXACT    = "exact"      # emitted the one right target and nothing else
OVER_FAN = "over_fan"   # right target + other targets, all inside the envelope
POLLUTED = "polluted"   # right target + at least one target outside every envelope
ANCESTOR = "ancestor"   # named only a SUPERTYPE that declares the member — weaker, not fabricated
WRONG    = "wrong"      # emitted targets, none of them right and none defensible
MISSED   = "missed"     # emitted nothing at all — a silent gap
# `missed` was three outcomes (#69): the two that are not silence get their own bucket
UNKNOWN  = "unknown"    # emitted no answer, but a row saying it could not resolve THIS call
UNPLACED = "unplaced"   # emitted an answer, but every row for the group was excluded by the resolver
PARTIAL  = "partial"    # a name-pooled group (several declared, non-dispatching targets): named some, not all (#70)


@dataclass
class GroupScore:
    verdicts: Counter = field(default_factory=Counter)
    # the groups behind each verdict, so a report can name them rather than only count them
    examples: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))

    @property
    def total(self) -> int:
        return sum(self.verdicts.values())

    def rate(self, v: str) -> float | None:
        return self.verdicts[v] / self.total if self.total else None

    def as_dict(self, max_examples: int = 12) -> dict:
        return {
            "total": self.total,
            "counts": dict(sorted(self.verdicts.items())),
            "rates": {k: self.rate(k) for k in (EXACT, OVER_FAN, PARTIAL, POLLUTED, ANCESTOR, WRONG, UNKNOWN, UNPLACED, MISSED)},
            "examples": {k: sorted(v)[:max_examples] for k, v in sorted(self.examples.items())},
        }


@dataclass
class ToolScore:
    tool: str
    subject: str
    tier: Tier
    scorable: bool                 # False when the tier is above the tool's declared ceiling
    reason: str = ""
    edges_emitted: int = 0
    # rows that repeat a (caller, callee) pair already emitted. Every metric is a SET measure, so
    # a tool that writes each edge twice scores exactly as one that writes it once — stated here so
    # the table's `edges` and the metric's denominator can be reconciled (#35)
    duplicate_rows: int = 0
    edges_scored: int = 0
    unmapped_rows: int = 0
    ambiguous_rows: int = 0
    unspellable_rows: int = 0
    excluded_rows: int = 0
    # What the tool needed in order to produce this answer. Not a metric — a capability, and one
    # that changes what the tool could SEE. A result obtained from a working compile is not
    # comparable to one obtained from a source tree alone, and a table that omits it invites the
    # reader to compare them anyway.
    build: str = "source only"
    # A null model is scored exactly like a tool and then rendered APART from the tools, so that it
    # is a floor to clear rather than a competitor to beat.
    null_model: bool = False
    # Wall-clock seconds for the ADAPTER RUN that produced this answer, on the machine named in the
    # manifest. It includes the tool's own startup and this harness's translation of its output, so
    # it is an order-of-magnitude figure for "what does it cost to ask", not a micro-benchmark.
    seconds: float | None = None
    vs_certain: Contingency | None = None
    vs_possible: Contingency | None = None
    vs_rta: Contingency | None = None
    unique_groups: GroupScore = field(default_factory=GroupScore)
    ambiguous_groups: GroupScore = field(default_factory=GroupScore)
    # ambiguous groups at this tier that are merges of ≥2 Tier-A uniquely linked groups (#51)
    ambiguous_merge_artefacts: int = 0
    tasks: dict = field(default_factory=dict)      # bench/tasks.py, Tier B only
    # ambiguous groups that pool several one-target calls under one name — not dispatch (#70)
    ambiguous_name_pooled: int = 0
    name_pooled_sites: int = 0
    by_family: dict[str, dict] = field(default_factory=dict)
    # reachability at depth 1..3 over the same edge set — issue #5; None when not computed
    chains: "ChainScore | None" = None
    # the tool's OWN confidence label, each value scored on its own rows (issue #10)
    by_confidence: dict[str, dict] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "tool": self.tool, "subject": self.subject, "tier": self.tier.value,
            "scorable": self.scorable, "reason": self.reason,
            "edges_emitted": self.edges_emitted, "edges_scored": self.edges_scored,
            "duplicate_rows": self.duplicate_rows,
            "unmapped_rows": self.unmapped_rows, "ambiguous_rows": self.ambiguous_rows,
            "unspellable_rows": self.unspellable_rows,
            "excluded_rows": self.excluded_rows,
            "build": self.build,
            "null_model": self.null_model,
            "seconds": self.seconds,
            "vs_certain":  self.vs_certain.as_dict()  if self.vs_certain  else None,
            "vs_possible": self.vs_possible.as_dict() if self.vs_possible else None,
            "vs_rta":      self.vs_rta.as_dict()      if self.vs_rta      else None,
            "unique_link_groups": self.unique_groups.as_dict(),
            "ambiguous_link_groups": self.ambiguous_groups.as_dict(),
            "ambiguous_merge_artefacts": self.ambiguous_merge_artefacts,
            "tasks": self.tasks,
            "ambiguous_name_pooled": self.ambiguous_name_pooled,
            "name_pooled_sites": self.name_pooled_sites,
            "by_family": self.by_family,
            "chains": self.chains.as_dict() if self.chains else None,
            "by_confidence": self.by_confidence,
        }


# ── the scoring pass ─────────────────────────────────────────────────────────────────────────
def _resolved_edges(out: ToolOutput, gt: GroundTruth, resolver: Resolver
                    ) -> tuple[list[tuple[Ref, Ref]], list[str], int, int, int]:
    """Map a tool's rows onto the oracle's vocabulary.

    Returns (edges, labels, unmapped, ambiguous, excluded) — `labels` parallel to `edges`.

    A row is dropped when either end cannot be placed in the subject unambiguously. Dropping is the
    only defensible handling — see bench/resolve.py — and both counts come back so every score can
    be printed next to the number of rows it did not look at.
    """
    edges: list[tuple[Ref, Ref]] = []
    labels: list[str] = []          # parallel to `edges`: the row's confidence label (#41)
    unmapped = ambiguous = excluded = 0
    # (caller Ref, callee name) of every row the resolver could NOT place although its caller was
    # placed — an `unplaced` group, not a silent miss (#69)
    unplaced: set[tuple[Ref, str]] = set()
    def note_unplaced(a: Resolution, callee: Ref) -> None:
        if a.verdict is Verdict.RESOLVED and a.ref is not None:
            unplaced.add((a.ref, normalise_name(callee.name, callee.type, resolver.lang)))
    for e in out.edges:
        a = resolver.resolve(e.caller, e.file)
        if (a.verdict is Verdict.RESOLVED and a.ref is not None and e.line is not None
                and e.caller.name in UNNAMED and a.ref.type is not None):
            # an unnamed caller, placed by the line the tool reported (GroundTruth.callers_at_line)
            here = gt.callers_at_line.get((a.ref.type.partition(":")[0], int(e.line)), set())
            if len(here) == 1:
                a = Resolution(Verdict.RESOLVED, next(iter(here)))
        elif a.verdict is Verdict.AMBIGUOUS and a.candidates and e.line is not None:
            # an AMBIGUOUS caller — several containers of that name declare or inherit the method
            # (a nested class and the class enclosing it, an interface and its implementation) —
            # is placed by the line the tool reported when exactly one of the candidates has a
            # caller at (module, line) in the ground truth (issue #17). The line is the tool's own
            # evidence, not the scorer's guess: a caller placed this way still has to name the
            # method the oracle saw there.
            modules = {c.partition(":")[0] for c in a.candidates}
            want = {e.caller.name, resolver.lang.ctor_canonical} if e.caller.name in resolver.lang.ctor_aliases \
                else {e.caller.name}
            here = {r for m in modules for r in gt.callers_at_line.get((m, int(e.line)), set())
                    if r.type in a.candidates and r.name in want}
            if len(here) == 1:
                a = Resolution(Verdict.RESOLVED, next(iter(here)))
        # a CALLEE is placed by its own file; the call site's file only narrows a spelling that
        # is still ambiguous after the method name has been consulted (#36 — narrowing first, by
        # the caller's file, returned silently wrong types), and never resolves an unknown one
        b = resolver.resolve(e.callee, e.callee_file, callee=True, context_file=e.file)
        if a.verdict is Verdict.AMBIGUOUS or b.verdict is Verdict.AMBIGUOUS:
            ambiguous += 1
            note_unplaced(a, e.callee)
            continue
        if a.verdict is not Verdict.RESOLVED or b.verdict is not Verdict.RESOLVED:
            unmapped += 1
            note_unplaced(a, e.callee)
            continue
        assert a.ref is not None and b.ref is not None
        # Only application-internal links are scored. A tool that also models the JDK is neither
        # rewarded nor charged for it; the subject's own code is the one thing every tool here is
        # trying to do, so it is the only thing compared.
        # (a callee spelled as the declared method on a dependency's type is admitted, as an
        # ancestor answer — GroundTruth.external_ancestors; a CALLER never is)
        if not gt.in_universe(a.ref) or not (gt.in_universe(b.ref) or gt.is_external_ancestor(a.ref, b.ref)):
            unmapped += 1
            note_unplaced(a, e.callee)
            continue
        # SYMMETRIC EXCLUSION. A construct docs/PROTOCOL.md §4 removed from the ground truth is
        # removed from the tool's answer too. Without this, a tool that reports an implicit
        # `super()` — a real instruction, just not a written call — is charged a false positive for
        # reporting something the benchmark decided not to measure. The count is carried into the
        # report so the removal is visible rather than silent.
        ca, cb = a.ref.at(Tier.B), b.ref.at(Tier.B)
        ka, kb = a.ref.at(Tier.A), b.ref.at(Tier.A)
        # A NEUTRAL ZONE: the oracle declared it has no ground truth for this (caller, callee-name)
        # group, or the callee is a constructor of a class that declares none. Answering there is
        # neither right nor wrong, and charging it would report a tool as imprecise precisely where
        # it is MORE capable than the oracle.
        neutral = ((ca, b.ref.name) in gt.neutral_groups
                   or (b.ref.name in ("constructor", "<init>") and b.ref.type in gt.no_ctor)
                   or (e.line is not None and (ca, int(e.line)) in gt.indirect_lines
                       and (ca, int(e.line), b.ref.name) not in gt.scored_lines))
        # Matched at Tier A when the tool spelled parameters, and otherwise against the SAFE Tier B
        # sets — the ones that cannot also delete an answer the ground truth still asks for.
        caller_excluded = (ka in gt.excluded_callers) if ka is not None else (
            ca in gt.excluded_callers_b)
        edge_excluded = (((ka, kb) in gt.excluded_edges)
                         if ka is not None and kb is not None
                         else ((ca, cb) in gt.excluded_edges_b))
        if neutral or caller_excluded or edge_excluded:
            excluded += 1
            continue
        edges.append((a.ref, b.ref))
        labels.append(_label_key(e.confidence))
    out.unplaced = unplaced   # type: ignore[attr-defined]  # read by score(); ToolOutput is a plain dataclass
    return edges, labels, unmapped, ambiguous, excluded


def _project(pairs: list[tuple[Ref, Ref]], tier: Tier) -> tuple[set[tuple[str, str]], int]:
    out: set[tuple[str, str]] = set()
    unspellable = 0
    for a, b in pairs:
        pa, pb = a.at(tier), b.at(tier)
        if pa is None or pb is None:
            unspellable += 1
            continue
        out.add((pa, pb))
    return out, unspellable


def _gt_bound(gt: GroundTruth, which: str) -> set[tuple[Ref, Ref]]:
    if which == "certain":
        return {(s.caller, t) for s in gt.sites for t in s.certain}
    if which == "possible":
        return {(s.caller, t) for s in gt.sites for t in s.possible}
    if which == "accepted":
        return gt.accepted_edges()
    return {(s.caller, t) for s in gt.sites for t in s.possible_rta}


def _contingency(emitted: set[tuple[str, str]], truth: set[tuple[str, str]],
                 envelope: set[tuple[str, str]], universe: int) -> Contingency:
    """TP counts an emitted edge that lies inside `truth`; FP counts one outside the ENVELOPE.

    Splitting the two is the whole point. Against `certain`, an edge naming the subtype that
    actually runs is neither a hit nor a miss — it is inside the envelope, so it is not charged as a
    false positive, but it does not fill a `certain` slot either. Folding it into FP would report a
    tool as imprecise for being right.
    """
    tp = len(emitted & truth)
    fp = len(emitted - envelope)
    fn = len(truth - emitted)
    return Contingency(tp=tp, fp=fp, fn=fn, universe=universe, emitted=len(emitted))


def _group_verdict(answer: set[str], certain: set[str], possible: set[str],
                   accepted: set[str]) -> str:
    """`accepted` is `possible` plus the declaring-ancestor answers: inside it the tool is
    over-approximating, outside it the tool is inventing.

    `certain` is the DECLARED target(s) and `possible` what can RUN; since #30 an abstract
    declared target is in the first and not the second, so an interface with one implementor is
    uniquely linked to the implementor and naming EITHER is the right answer — the declaration is
    the language-level one, the implementor the runtime one. A group can carry two declared
    targets (two sites in one method calling the same member through different static types) and
    naming both is not a fan: a fan is more than one RUNNABLE target, or a supertype that merely
    declares the member alongside the one that runs.
    """
    if not answer:
        return MISSED
    right = certain | possible
    hit = answer & right
    if not hit:
        # Nothing it named can actually run here. If everything it named is nonetheless a
        # SUPERTYPE that declares the member — `new ChannelInitializer(){…}` answered as
        # `ChannelInitializer#<init>`, which is the only type the source names — that is a weaker
        # answer, not an invented one. Reported on its own: it does not reach the method that
        # runs, so it is not `exact` and earns no recall, but calling it `wrong` overstates the
        # error and hides the difference between a tool that is vague and one that is incorrect.
        return ANCESTOR if answer <= accepted else WRONG
    if answer - accepted:
        return POLLUTED
    if answer - right:                       # a declaring ancestor beside the right answer
        return OVER_FAN
    # a fan is more than one RUNNABLE target that is not itself a declared target: two declared
    # targets that both run (two `invokestatic` sites on two overloads, merged at Tier B) are two
    # answers to two questions, not a set (#51)
    runnable = answer & possible
    if len(runnable) <= 1 and len(certain) > 1 and certain == possible:
        # a NAME-POOLED group — `new A()` and `new B()` in one method, one `<init>` group with two
        # declared targets and no dispatch: naming one of them is half the answer, not the answer
        # (#70); naming all of them is exact (#51)
        return EXACT if certain <= answer else PARTIAL
    return EXACT if len(runnable) <= 1 or runnable <= certain else OVER_FAN


_SCORE_RE = re.compile(r"^(.*?):(-?\d+(?:\.\d+)?)$")


def _label_key(label: str | None) -> str:
    """A tool's `term:score` label with the score rounded to two places — GitNexus writes
    `call:0.5700000000000001` (#41) — and everything else as written. Empty stays empty."""
    if not label:
        return ""
    m = _SCORE_RE.match(label.strip())
    if m:
        return f"{m.group(1).lower()}:{float(m.group(2)):.2f}"
    # `EXTRACTED` and `extracted` are one class (#69, comment)
    return label.strip().lower()


def _offending(v: str, answer: set[str], certain: set[str], possible: set[str],
               accepted: set[str]) -> set[str]:
    """The targets that DECIDED a group's verdict — what a per-label table should charge or credit.

    exact: the hit. over_fan: everything beside the one right answer (the declaring ancestor, the
    extra runnable targets). polluted / wrong: the targets outside the envelope. ancestor: the
    supertype answers. missed: nothing was emitted, so nothing is attributed.
    """
    right = certain | possible
    if v == EXACT:
        return answer & right
    if v == OVER_FAN:
        hit = answer & possible
        keep = {min(hit)} if hit else (answer & right)
        return answer - keep
    if v in (POLLUTED, WRONG):
        return answer - accepted
    if v == ANCESTOR:
        return answer
    return set()


def _ref_from_meta(d) -> Ref:
    if isinstance(d, str):
        return Ref.parse(d)
    return Ref(name=d.get("name", ""), type=d.get("type"), params=tuple(d["params"]) if d.get("params") is not None else None)


def _score_groups(groups: list[LinkGroup], emitted: set[tuple[str, str]], tier: Tier,
                  label_of: dict[tuple[str, str], str] | None = None,
                  attribution: dict[str, Counter] | None = None,
                  unknown_at: set[tuple[str, int]] | None = None,
                  unplaced_keys: set[tuple[str, str]] | None = None) -> GroupScore:
    """Score the link groups — the metric that answers 'one concrete method, or a set?'.

    With `label_of` and `attribution`, every group's verdict is ALSO charged to exactly one
    confidence label: the label of the target(s) that decided the verdict (`_offending`), the most
    frequent one when several labels contributed, ties broken by name. One group, one label, so
    the per-label columns sum to the tool's own totals (#41; the previous table scored each label's
    rows alone and double-counted a group whose rows carried two labels).
    """
    by_caller_name: dict[tuple[str, str], set[str]] = defaultdict(set)
    for a, b in emitted:
        # `b` is spelled at `tier`; its bare method name is the group key's second half
        name = b.split("#", 1)[1].split("(", 1)[0] if "#" in b else b.split("(", 1)[0]
        by_caller_name[(a, name)].add(b)

    gs = GroupScore()
    for g in groups:
        ca = g.caller.at(tier)
        if ca is None:
            continue
        certain = {c for c in (r.at(tier) for r in g.certain) if c is not None}
        possible = {p for p in (r.at(tier) for r in g.possible) if p is not None}
        if not possible:
            continue
        # the declared target is always an accepted answer, whether or not the oracle also listed
        # it as a declaring ancestor: naming the declaration is never pollution
        accepted = possible | certain | {a for a in (r.at(tier) for r in g.declaring_ancestors)
                                         if a is not None}
        answer = by_caller_name.get((ca, g.callee_name), set())
        v = _group_verdict(answer, certain, possible, accepted)
        if v == MISSED:
            # not silence when the tool SAID it could not resolve a call at one of the group's
            # lines, or when it answered and the resolver could not place the answer (#69)
            if unknown_at and any((ca, int(st.line)) in unknown_at for st in g.sites):
                v = UNKNOWN
            elif unplaced_keys and (ca, g.callee_name) in unplaced_keys:
                v = UNPLACED
        gs.verdicts[v] += 1
        gs.examples[v].append(f"{ca} -> {g.callee_name} | expected {sorted(possible)} | got {sorted(answer)}")
        if label_of is not None and attribution is not None and answer:
            decided = _offending(v, answer, certain, possible, accepted) or answer
            votes = Counter(label_of.get((ca, t), "") for t in decided)
            label = sorted(votes.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
            attribution[label][v] += 1
    return gs


_TRUTH_CACHE: dict[tuple[int, Tier], tuple] = {}


def _truth_at(gt: GroundTruth, tier: Tier) -> tuple:
    """The four projected bounds, the MCC universe and the re-formed groups — pure functions of
    the ground truth, memoised per (ground truth, tier). Gate 3 scores fifteen synthetic tools
    over one ground truth and re-derived all of this every time: 19 s per call on rxjava, 253 s
    for the gate (issue #57). The ground truth is immutable for the life of a run."""
    key = (id(gt), tier)
    hit = _TRUTH_CACHE.get(key)
    if hit is not None and hit[0] is gt:
        return hit[1]
    # (unsorted: _project returns a set and a count, both order-independent, and sorting 400k
    # dataclass Refs by their generated comparison was 30 s of the 34 s this took on rxjava)
    certain_t, _  = _project(list(_gt_bound(gt, "certain")),  tier)
    possible_t, _ = _project(list(_gt_bound(gt, "possible")), tier)
    rta_t, _      = _project(list(_gt_bound(gt, "rta")),      tier)
    accepted_t, _ = _project(list(_gt_bound(gt, "accepted")), tier)
    # The universe for MCC: every ordered (app method, app method) pair that could be an edge,
    # counted at THIS tier, because two methods that differ only in their parameter list are one
    # method at Tier B and the universe must shrink with them.
    names = {m.at(tier) for m in gt.methods}
    names.discard(None)
    universe = len(names) ** 2
    at_tier = groups_at(gt, tier)
    uniq = [g for g in at_tier if projected_unique(g, tier)]
    ambi = [g for g in at_tier if not projected_unique(g, tier)]
    value = (certain_t, possible_t, rta_t, accepted_t, universe, at_tier, uniq, ambi)
    _TRUTH_CACHE[key] = (gt, value)
    return value


def score(out: ToolOutput, gt: GroundTruth, resolver: Resolver, tier: Tier,
          family_of=None, chain_truth: "ChainTruth | None" = None) -> ToolScore:
    """One tool, one subject, one fidelity tier."""
    s = ToolScore(tool=out.tool, subject=gt.subject, tier=tier, scorable=True,
                  edges_emitted=len(out.edges),
                  duplicate_rows=len(out.edges) - len({(e.caller, e.callee) for e in out.edges}),
                  build=str(out.meta.get("build", "source only")),
                  null_model=bool(out.meta.get("null_model", False)))

    if tier.rank > out.declared_tier.rank:
        # ABOVE the tool's ceiling. Reported absent, never zero: a tool that cannot spell parameter
        # types has not failed overload selection, it has declined to answer the question, and a 0
        # in that cell would be read as "got them all wrong".
        s.scorable = False
        s.reason = (f"output format cannot express tier {tier.value} "
                    f"(declared ceiling: {out.declared_tier.value})")
        return s

    pairs, pair_labels, unmapped, ambiguous, excluded = _resolved_edges(out, gt, resolver)
    s.unmapped_rows, s.ambiguous_rows, s.excluded_rows = unmapped, ambiguous, excluded

    emitted, unspellable = _project(pairs, tier)
    s.unspellable_rows = unspellable
    s.edges_scored = len(emitted)

    certain_t, possible_t, rta_t, accepted_t, universe, at_tier, uniq, ambi = _truth_at(gt, tier)

    s.vs_certain  = _contingency(emitted, certain_t,  accepted_t, universe)
    s.vs_possible = _contingency(emitted, possible_t, accepted_t, universe)
    s.vs_rta      = _contingency(emitted, rta_t,      accepted_t, universe)

    # Reachability, from the same edge set the edge metrics were computed over — so the k=1 row of
    # the chain table is literally the edge row, and the series reads as one story (issue #5).
    if chain_truth is not None and chain_truth.tier is tier:
        s.chains = score_chains(emitted, chain_truth)

    # Groups re-formed AT THIS TIER, and `unique` judged on the PROJECTED target set — see
    # groundtruth.groups_at. Using the Tier A groups here put a scorer-owned ceiling on the headline.
    # what the tool itself said it could not resolve: `meta.unresolved_sites` = [[caller, line]…]
    # written by an adapter for the tool's own "unknown" label (axiom `ambiguous_unknown`), keyed
    # by the caller at this tier and the line (#69)
    unknown_at: set[tuple[str, int]] = set()
    for item in out.meta.get("unresolved_sites") or []:
        try:
            cref = _ref_from_meta(item[0])
            r = resolver.resolve(cref, item[2] if len(item) > 2 else None)
            ca = r.ref.at(tier) if r.verdict is Verdict.RESOLVED and r.ref is not None else None
            if ca is not None:
                unknown_at.add((ca, int(item[1])))
        except (TypeError, ValueError, IndexError):
            continue
    unplaced_keys = {(r.at(tier), n) for r, n in getattr(out, "unplaced", set())}
    unplaced_keys.discard((None, ""))
    s.unique_groups = _score_groups(uniq, emitted, tier, unknown_at=unknown_at, unplaced_keys=unplaced_keys)
    s.ambiguous_groups = _score_groups(ambi, emitted, tier, unknown_at=unknown_at, unplaced_keys=unplaced_keys)
    s.ambiguous_merge_artefacts = merge_artefacts(at_tier, tier)
    if tier is Tier.B:
        # the task-level scores — callers_of, callees_of, path, blast radius, uncalled, dispatch,
        # file dependencies — on the same edge set and truth (bench/tasks.py)
        amb_dicts = []
        for g in ambi:
            ca = g.caller.at(tier)
            if ca is None:
                continue
            amb_dicts.append({"caller": ca, "name": g.callee_name,
                              "possible": {p for p in (r.at(tier) for r in g.possible) if p is not None}})
        names_b = {m.at(tier) for m in gt.methods}
        names_b.discard(None)
        s.tasks = score_tasks(emitted, certain_t, possible_t, accepted_t, names_b, amb_dicts).as_dict()
    s.ambiguous_name_pooled, s.name_pooled_sites = name_pooled(at_tier, tier)

    # THE PER-LABEL TABLE (#10, #41). Every labelled tool gets one — no cap on the label count —
    # keyed by the label's TERM (`call`, `exact-match`, `INFERRED`, `resolved|typecheck`) with the
    # score sub-buckets (`call:0.57`) nested under it, so a tool whose scores carry float noise
    # or a dozen distinct values still reads as a handful of rows. Per-row measures (rows,
    # precision, prec-strict) are computed over the label's own rows; the group verdicts are
    # attributed, one label per group, by _score_groups.
    labels = {_label_key(e.confidence) for e in out.edges if e.confidence}
    if labels and not out.meta.get("null_model"):
        label_of: dict[tuple[str, str], str] = {}
        for (ra, rb), lab in zip(pairs, pair_labels):
            pa, pb = ra.at(tier), rb.at(tier)
            if pa is not None and pb is not None:
                # a pair emitted under two labels is attributed to the first by name; the
                # per-row columns still count both rows
                label_of[(pa, pb)] = min(label_of.get((pa, pb), lab), lab)
        attribution: dict[str, Counter] = defaultdict(Counter)
        _score_groups(uniq, emitted, tier, label_of, attribution)

        def cell(rows: list[Edge], att: Counter) -> dict:
            sub = ToolOutput(tool=out.tool, subject=out.subject, declared_tier=out.declared_tier,
                             edges=rows, meta=out.meta)
            sp, _, _, _, _ = _resolved_edges(sub, gt, resolver)
            se, _ = _project(sp, tier)
            c = _contingency(se, certain_t, accepted_t, universe)
            return {
                "rows": len(rows),
                "precision": _contingency(se, possible_t, accepted_t, universe).precision,
                "precision_strict": c.precision_strict,
                "exact": att[EXACT], "over_fan": att[OVER_FAN], "polluted": att[POLLUTED],
                "ancestor": att[ANCESTOR], "wrong": att[WRONG],
            }

        by_term: dict[str, list[str]] = defaultdict(list)
        for lab in sorted(labels):
            by_term[lab.rsplit(":", 1)[0] if _SCORE_RE.match(lab) else lab].append(lab)
        for term, subs in sorted(by_term.items()):
            rows = [e for e in out.edges if _label_key(e.confidence) in subs]
            att = Counter()
            for lab in subs:
                att.update(attribution.get(lab, Counter()))
            entry = cell(rows, att)
            if len(subs) > 1 or subs[0] != term:
                entry["by_score"] = {
                    lab: cell([e for e in out.edges if _label_key(e.confidence) == lab],
                              attribution.get(lab, Counter()))
                    for lab in subs}
            s.by_confidence[term] = entry
        unl = [e for e in out.edges if not e.confidence]
        if unl:
            s.by_confidence["(unlabelled)"] = cell(unl, attribution.get("", Counter()))

    if family_of is not None:
        buckets: dict[str, list[LinkGroup]] = defaultdict(list)
        for g in at_tier:
            buckets[family_of(g.caller)].append(g)
        for fam, gs in sorted(buckets.items()):
            u = [g for g in gs if projected_unique(g, tier)]
            s.by_family[fam] = {
                "link_groups": len(gs),
                "unique": _score_groups(u, emitted, tier).as_dict(max_examples=4),
                "ambiguous": _score_groups([g for g in gs if not projected_unique(g, tier)],
                                           emitted, tier).as_dict(max_examples=4),
            }
    return s
