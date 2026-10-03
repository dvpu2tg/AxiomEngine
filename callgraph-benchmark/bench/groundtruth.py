#!/usr/bin/env python3
"""The ground truth, loaded from the classfile oracle and shaped into the three things a score needs:
the two edge bounds, the link groups, and the scoring universe.

THE TWO BOUNDS
--------------
A call graph has two kinds of truth and collapsing them into one number hides whichever one you
were not looking at.

    CERTAIN  (G_lb)  the target the invoke instruction DECLARES. For invokestatic and invokespecial
                     this is the method that runs. For a virtual or interface call it is the static
                     type's member. A tool that omits one of these has missed a fact, so recall
                     against this set is the number a missing edge is undeniable in.

    POSSIBLE (G_ub)  CERTAIN plus every application subtype that declares the same member — the
                     sound class-hierarchy dispatch envelope. An answer inside it is a real runtime
                     possibility. Only an answer OUTSIDE it is a demonstrable false positive, which
                     is why precision is measured against this set and not against CERTAIN: charging
                     a tool for naming the override that actually runs would score it as wrong at
                     the moment it got sharper.

Recall is therefore reported twice — `recall_certain` (of the facts, how many did you find) and
`recall_possible` (of the sound envelope, how much of the dispatch space did you cover). They move
in opposite directions under over-approximation, which is the point: neither alone can be gamed.

LINK GROUPS — the metric this benchmark is built around
------------------------------------------------------
"Precision 0.98" says nothing about the question that decides whether a graph is usable: when the
language admits exactly ONE target, did the tool name that one method, or did it hand back a set?

A LINK GROUP is `(caller, callee_name)` — every call written in one method to one method name. The
oracle knows, for each group, the certain targets and the possible targets. A group whose possible
set has exactly one member is UNIQUELY LINKED: there is one right answer and no honest reason to
emit more than one. Each tool's answer for that group is scored as exactly one of:

    exact      the tool emitted that one target and nothing else          — the only clean win
    over_fan   it emitted that target plus others (all inside the envelope) — sound but imprecise
    polluted   it emitted that target plus something outside the envelope  — sound set, false members
    wrong      it emitted targets, none of them the right one             — a silent wrong answer
    missed     it emitted nothing for the group                           — a silent gap

Grouping on `(caller, callee_name)` rather than on a source line is deliberate: it needs no line
numbers, so a tool that emits none is measured on exactly the same footing as one that does. The
line-keyed version is computed too, for the tools that can support it, and reported separately.
"""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import replace, dataclass, field
from pathlib import Path

from model import Ref, Tier


@dataclass(frozen=True)
class Site:
    """One scored call site, as `oracle/ClassfileGroundTruth.java --mode sites` emitted it."""
    site_id: str
    caller: Ref
    line: int
    seq: int
    op: str
    receiver_static_type: str
    callee_name: str
    callee_params: tuple[str, ...]
    kind: str                      # "internal" | "boundary"
    certain: tuple[Ref, ...]
    possible: tuple[Ref, ...]
    possible_rta: tuple[Ref, ...]
    declaring_ancestors: tuple[Ref, ...] = ()

    @property
    def unique(self) -> bool:
        return len(self.possible) == 1

    @property
    def unique_rta(self) -> bool:
        return len(self.possible_rta) == 1


@dataclass
class LinkGroup:
    """Every call from one method to one method name, and the two bounds over that group."""
    caller: Ref
    callee_name: str
    certain: set[Ref] = field(default_factory=set)
    possible: set[Ref] = field(default_factory=set)
    possible_rta: set[Ref] = field(default_factory=set)
    declaring_ancestors: set[Ref] = field(default_factory=set)
    sites: list[Site] = field(default_factory=list)
    # set by groups_at: the number of Tier-A uniquely linked groups this projected group merges
    merged_unique: int = 0

    @property
    def key(self) -> tuple[str, str]:
        return (str(self.caller), self.callee_name)

    @property
    def unique(self) -> bool:
        """The language admits exactly one target across every site in the group."""
        return len(self.possible) == 1


@dataclass
class GroundTruth:
    subject: str
    sites: list[Site]
    classes: set[str]              # application types, canonically spelled
    methods: set[Ref]              # application methods, canonically spelled
    groups: dict[tuple[str, str], LinkGroup]
    # `Type#name` of callers a documented exclusion removed, and `caller -> callee` of app-internal
    # edges it removed. Applied to EVERY tool's output, not only to the oracle's — see §4 and the
    # `noteExcluded` comment in the oracle. An exclusion applied to one side only is not an
    # exclusion, it is a penalty.
    excluded_callers: set[str] = field(default_factory=set)            # Tier A
    excluded_edges: set[tuple[str, str]] = field(default_factory=set)  # Tier A
    # Tier B forms, derived SAFELY: a Tier B key is admitted only when it cannot also match
    # something the ground truth still asks about. See `_safe_tier_b`.
    excluded_callers_b: set[str] = field(default_factory=set)
    excluded_edges_b: set[tuple[str, str]] = field(default_factory=set)
    # (caller at Tier B, callee name) groups where the oracle HAS NO GROUND TRUTH — a call through
    # a function value. An emitted edge matching one is dropped and counted, never scored.
    neutral_groups: set[tuple[str, str]] = field(default_factory=set)
    # containers that declare no constructor: a tool that synthesises one is not wrong
    no_ctor: set[str] = field(default_factory=set)
    # EXTERNAL DECLARING ANCESTORS. A call on a dependency's interface whose only implementer is in
    # the application — `ArtifactRepositoryLayout#getId()` in maven-core, declared in maven-artifact,
    # implemented once here — has an empty `certain` and a one-element `possible`. The tool that
    # names the declared method, which is the answer the language gives, was scored `missed` for
    # naming a type outside the universe, while the tool that named nothing was scored the same.
    # That is not one verdict, it is two. The declared target is now the group's declaring
    # ancestor, exactly as an in-universe supertype would be: neither exact nor wrong, `anc`. The
    # types live here so the resolver can read them and `in_universe` can admit them as CALLEES
    # only. 14% of maven-core's uniquely-linked groups are of this kind; 5–6% on the others.
    external_ancestors: dict[str, set[str]] = field(default_factory=dict)   # type -> method names
    # (caller at Tier B, external type, method name) — the exact sites that dispatch through an
    # external declared target. Admission is per SITE: the same `Artifact#getId` named from a
    # caller whose call is a boundary site (no application implementer) stays unmapped, as every
    # boundary row does.
    external_ancestor_keys: set[tuple[str, str, str]] = field(default_factory=set)
    # (caller at Tier B, line) of every INDIRECT site — a call through a function value, where the
    # oracle has no ground truth. `neutral_groups` keys the same sites by the NAME the call is
    # written with (`debug(...)`); a tool that resolves the value through data flow names the
    # function that runs (`wrappedDebug`), and the two never meet. The line does: a row at a line
    # where the oracle recorded only an indirect call with that name is answering the unscored
    # question, and is dropped as neutral on the tool's side too.
    indirect_lines: set[tuple[str, int]] = field(default_factory=set)
    # (caller at Tier B, line, callee name) of every SCORED site, so a line that carries both an
    # indirect call and a direct one keeps the direct one scorable
    scored_lines: set[tuple[str, int, str]] = field(default_factory=set)
    # (module, line) -> the callers the oracle records at that line. A tool that reports an
    # UNNAMED caller — axiom's `<arrow>` for an object-literal property arrow, whose name its IR
    # does not record — still says which file and line the call is on; where the oracle has
    # exactly one caller at that line, that is the function (issue #22). The same reading as
    # placing a call by line for the neutral zone (#18); a line with two callers stays unplaced.
    callers_at_line: dict[tuple[str, int], set[Ref]] = field(default_factory=dict)

    @property
    def method_names(self) -> set[str]:
        if not hasattr(self, "_names"):
            object.__setattr__(self, "_names", {m.name for m in self.methods})
        return self._names   # type: ignore[attr-defined]

    # ── edge bounds ──────────────────────────────────────────────────────────────────────────
    def certain_edges(self) -> set[tuple[Ref, Ref]]:
        return {(s.caller, t) for s in self.sites for t in s.certain}

    def possible_edges(self) -> set[tuple[Ref, Ref]]:
        return {(s.caller, t) for s in self.sites for t in s.possible}

    def rta_edges(self) -> set[tuple[Ref, Ref]]:
        return {(s.caller, t) for s in self.sites for t in s.possible_rta}

    def accepted_edges(self) -> set[tuple[Ref, Ref]]:
        """POSSIBLE plus the declaring-ancestor answers — the set an emitted edge must fall outside
        of to be a false positive.

        Naming the supertype that declares a member is a convention, not an error, so it is not
        charged as a false positive. It is deliberately NOT part of `possible`, because that would
        let a supertype answer earn recall for a target it does not reach."""
        return self.possible_edges() | {
            (s.caller, t) for s in self.sites for t in s.declaring_ancestors}

    def at(self, tier: Tier, which: str) -> set[tuple[str, str]]:
        """A bound projected to `tier`.

        Projecting the ORACLE as well as the tool is what makes a lower tier fair rather than
        merely lenient: at Tier B the oracle stops distinguishing overloads too, so a tool that
        cannot distinguish them is compared against a truth that is not asking it to.
        """
        src = self.certain_edges() if which == "certain" else self.possible_edges()
        out: set[tuple[str, str]] = set()
        for a, b in src:
            pa, pb = a.at(tier), b.at(tier)
            if pa is not None and pb is not None:
                out.add((pa, pb))
        return out

    # ── scoping ──────────────────────────────────────────────────────────────────────────────
    def in_universe(self, r: Ref) -> bool:
        """Is this reference inside the application?

        Everything outside is dropped from BOTH sides before scoring. A tool that also models the
        JDK is not rewarded for the extra edges and not charged for them either — the subject's own
        code is the only thing every tool here is trying to do, so it is the only thing compared.
        Boundary behaviour is reported separately and never folded into these numbers.

        A TYPE-LESS reference is scoped BY NAME, not discarded. Requiring a type here would delete
        every row of a name-only tool before it was scored — the tool would be reported as having
        found nothing, when what actually happened is that the harness threw its answer away for
        being spelled without an owner. That is the exact failure this benchmark is built to avoid,
        and it is asserted against in bench/selftest.py.
        """
        if r.type is not None:
            return r.type in self.classes
        return r.name in self.method_names

    def is_external_ancestor(self, caller: Ref, r: Ref) -> bool:
        """A callee spelled as the declared method on a dependency's type — admissible as an
        ANCESTOR answer for the sites that dispatch through it, never as a caller."""
        if r.type is None:
            return False
        k = caller.at(Tier.B)
        return k is not None and (k, r.type, r.name) in self.external_ancestor_keys


def load(sites_path: Path, classes_path: Path, methods_path: Path, subject: str,
         excluded_path: Path | None = None) -> GroundTruth:
    sites: list[Site] = []
    for ln in sites_path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        d = json.loads(ln)
        sites.append(Site(
            site_id=d["site_id"],
            caller=Ref.parse(d["caller"]),
            line=d["line"],
            seq=d["seq"],
            op=d["op"],
            receiver_static_type=d["receiver_static_type"],
            callee_name=d["callee_name"],
            callee_params=tuple(d["callee_params"]),
            kind=d["kind"],
            certain=tuple(Ref.parse(x) for x in d["certain"]),
            possible=tuple(Ref.parse(x) for x in d["possible"]),
            possible_rta=tuple(Ref.parse(x) for x in d["possible_rta"]),
            declaring_ancestors=tuple(Ref.parse(x) for x in d.get("declaring_ancestors", [])),
        ))

    classes = {c.strip() for c in classes_path.read_text(encoding="utf-8").splitlines() if c.strip()}
    methods = {Ref.parse(m.strip()) for m in methods_path.read_text(encoding="utf-8").splitlines()
               if m.strip()}
    # the external declared target of a site that dispatches into the application (see
    # GroundTruth.external_ancestors)
    indirect_lines: set[tuple[str, int]] = set()
    scored_lines: set[tuple[str, int, str]] = set()
    callers_at_line: dict[tuple[str, int], set[Ref]] = {}
    for s in sites:
        kb = s.caller.at(Tier.B)
        if kb is None:
            continue
        if s.caller.type:
            callers_at_line.setdefault((s.caller.type.partition(":")[0], int(s.line)), set()).add(s.caller)
        if s.kind == "indirect":
            indirect_lines.add((kb, int(s.line)))
        elif s.possible:
            scored_lines.add((kb, int(s.line), s.callee_name))
    external: dict[str, set[str]] = {}
    external_keys: set[tuple[str, str, str]] = set()
    for i, s in enumerate(sites):
        if s.certain or not s.possible or not s.receiver_static_type or s.receiver_static_type in classes:
            continue
        ext = Ref(name=s.callee_name, type=s.receiver_static_type, params=tuple(s.callee_params))
        external.setdefault(ext.type, set()).add(ext.name)
        kb = s.caller.at(Tier.B)
        if kb is not None:
            external_keys.add((kb, ext.type, ext.name))
        if ext not in s.declaring_ancestors:
            sites[i] = replace(s, declaring_ancestors=(*s.declaring_ancestors, ext))
    # THE UNIVERSE MUST CONTAIN EVERYTHING THE SITES NAME. A lambda written inside a static
    # initialiser is folded onto `<clinit>`, which the declaration walk excludes — so a caller existed
    # in the sites and not in the universe, and at Tier C, where scoping is by name, every row
    # naming it was deleted from both sides. Deriving the universe from the sites as well makes the
    # two consistent by construction (the TypeScript oracle already does this).
    for s in sites:
        methods.add(s.caller)
        for t in (*s.certain, *s.possible, *s.possible_rta, *s.declaring_ancestors):
            methods.add(t)
        classes.add(s.caller.type) if s.caller.type else None
        for t in (*s.certain, *s.possible):
            if t.type:
                classes.add(t.type)

    groups: dict[tuple[str, str], LinkGroup] = {}
    for s in sites:
        # A boundary site has no application target, so it forms no group: there is nothing inside
        # the subject for a tool to have linked it to, and a group with an empty envelope would make
        # every tool score `missed` on a site where missing is the correct answer.
        if not s.possible:
            continue
        k = (str(s.caller), s.callee_name)
        g = groups.get(k)
        if g is None:
            g = groups[k] = LinkGroup(caller=s.caller, callee_name=s.callee_name)
        g.certain |= set(s.certain)
        g.possible |= set(s.possible)
        g.possible_rta |= set(s.possible_rta)
        g.declaring_ancestors |= set(s.declaring_ancestors)
        g.sites.append(s)

    ex_callers: set[str] = set()
    ex_edges: set[tuple[str, str]] = set()
    neutral: set[tuple[str, str]] = set()
    no_ctor: set[str] = set()
    if excluded_path is not None and excluded_path.exists():
        for ln in excluded_path.read_text(encoding="utf-8").splitlines():
            kind, _, rest = ln.partition("\t")
            if kind == "CALLER":
                ex_callers.add(rest.strip())          # `Type#name(params)` — Tier A
            elif kind == "INDIRECT":
                caller, _, name = rest.partition("\t")
                r = Ref.parse(caller.strip())
                k = r.at(Tier.B)
                if k is not None:
                    neutral.add((k, name.strip()))
            elif kind == "NOCTOR":
                no_ctor.add(rest.strip())
            elif kind == "EDGE" and " -> " in rest:
                a, _, b = rest.partition(" -> ")
                # The oracle writes exclusions at full signature fidelity. The comparison happens at
                # Tier B, so both spellings are stored: a Tier-A-only key would silently fail to
                # match and the excluded construct would be charged as a false positive after all —
                # which is the exact bug this mechanism exists to fix.
                ra, rb = Ref.parse(a.strip()), Ref.parse(b.strip())
                ka, kb = ra.at(Tier.A), rb.at(Tier.A)
                if ka is not None and kb is not None:
                    ex_edges.add((ka, kb))

    # A NEUTRAL ZONE MUST NOT SWALLOW A SCORED GROUP. It is keyed on (caller, callee-name), and
    # so is the link-group metric — so one call to `map` through a function value in a module's
    # top-level code neutralised every DIRECT call to `map` from the same code, deleting answers the
    # ground truth still asks about (ten groups on fp-ts, found by the ceiling gate). Where a group
    # has any scored site, the tool is judged on that part and the neutral entry is dropped.
    scored_b = set()
    for s_ in sites:
        if s_.possible:
            ca = s_.caller.at(Tier.B)
            if ca is not None:
                scored_b.add((ca, s_.callee_name))
    neutral = {k for k in neutral if k not in scored_b}

    # ── THE SAFE TIER B DERIVATION ───────────────────────────────────────────────────────────
    # A tool that cannot spell parameters still needs its excluded rows removed, so a Tier B form is
    # needed — but `Foo#<init>()` and `Foo#<init>(int)` are ONE STRING at Tier B, so a blanket
    # projection deletes answers to call sites the oracle is still asking about.
    #
    # A Tier B key is therefore admitted only when nothing survives under it:
    #   * a caller name, only when EVERY overload of that name was excluded (no scored site remains);
    #   * an edge, only when no edge in `possible` spells the same way at Tier B.
    # AND THE SAME RULE AT TIER A. An exclusion must never remove something the ground truth still
    # asks about, at ANY tier. A `<clinit>` is excluded as a caller, but a lambda written inside one
    # is folded back onto it — so scored sites exist under a name that is simultaneously on the
    # exclusion list, and the answer to those sites was being deleted from every tool at once.
    # apache-ant surfaced three such groups; the ceiling gate is what made them visible.
    scored_callers_a = {c for c in (s.caller.at(Tier.A) for s in sites) if c is not None}
    ex_callers = {k for k in ex_callers if k not in scored_callers_a}

    possible_a = set()
    for s_ in sites:
        ca = s_.caller.at(Tier.A)
        for t in s_.possible:
            ta = t.at(Tier.A)
            if ca is not None and ta is not None:
                possible_a.add((ca, ta))
    ex_edges = {e for e in ex_edges if e not in possible_a}

    scored_callers_b = {c for c in (s.caller.at(Tier.B) for s in sites) if c is not None}
    ex_callers_b = set()
    for k in ex_callers:
        b = Ref.parse(k).at(Tier.B)
        if b is not None and b not in scored_callers_b:
            ex_callers_b.add(b)

    possible_b = set()
    for s_ in sites:
        ca = s_.caller.at(Tier.B)
        for t in s_.possible:
            tb = t.at(Tier.B)
            if ca is not None and tb is not None:
                possible_b.add((ca, tb))
    ex_edges_b = set()
    for a_, b_ in ex_edges:
        pa, pb = Ref.parse(a_).at(Tier.B), Ref.parse(b_).at(Tier.B)
        if pa is not None and pb is not None and (pa, pb) not in possible_b:
            ex_edges_b.add((pa, pb))

    return GroundTruth(subject=subject, sites=sites, classes=classes, methods=methods, groups=groups,
                       excluded_callers=ex_callers, excluded_edges=ex_edges,
                       excluded_callers_b=ex_callers_b, excluded_edges_b=ex_edges_b,
                       neutral_groups=neutral, no_ctor=no_ctor, external_ancestors=external,
                       external_ancestor_keys=external_keys, indirect_lines=indirect_lines,
                       scored_lines=scored_lines, callers_at_line=callers_at_line)


def groups_at(gt: GroundTruth, tier: Tier) -> list[LinkGroup]:
    """Re-form the link groups AT THE SCORING TIER.

    The groups are built keyed on the Tier A caller, because that is the only spelling that cannot
    merge two different methods. But a tool's answer is indexed on the caller AT THE TIER BEING
    SCORED — so at Tier B two overloads of one caller merge on the answer side and stay split on the
    truth side, and each group inherits the other's targets. A tool that resolved both correctly
    reads `polluted` on both.

    Measured before the fix: a tool answering EVERY group correctly scored 94.9% on netty-transport
    and 98.1% on spring-boot, with 98 and 77 `polluted` respectively — a ceiling belonging to the
    scorer rather than to any tool, and one that is exactly 100% on `torture`, which is the subject
    the published conclusions compare the scale results against.

    Re-forming at the tier also moves the DENOMINATOR, and that is correct rather than incidental:
    two overloads of one target are one method at Tier B, so a group that looks uniquely linked at
    Tier A can be genuinely ambiguous at Tier B. The headline count must be counted at the headline
    tier.
    """
    merged: dict[tuple[str, str], LinkGroup] = {}
    pre_images: dict[tuple[str, str], int] = {}     # how many Tier-A UNIQUE groups merged here
    for g in gt.groups.values():
        ca = g.caller.at(tier)
        if ca is None:
            continue
        k = (ca, g.callee_name)
        m = merged.get(k)
        if m is None:
            m = merged[k] = LinkGroup(caller=g.caller, callee_name=g.callee_name)
        m.certain |= g.certain
        m.possible |= g.possible
        m.possible_rta |= g.possible_rta
        m.declaring_ancestors |= g.declaring_ancestors
        m.sites.extend(g.sites)
        if g.unique:
            pre_images[k] = pre_images.get(k, 0) + 1
    for k, m in merged.items():
        m.merged_unique = pre_images.get(k, 0)
    return list(merged.values())


def name_pooled(groups: list[LinkGroup], tier: Tier) -> tuple[int, int]:
    """(groups, call sites): groups that are ambiguous at `tier` only because the key pools
    same-named calls with different one-target receivers — `new A()` + `new B()` in one method,
    `getProject()` on a Task and on a Target. Every site in such a group has exactly one possible
    target; none of it is dispatch (#70). Printed beside the ambiguous table and the headline."""
    n = sites = 0
    for g in groups:
        if projected_unique(g, tier) or not g.sites:
            continue
        if all(len({r.at(tier) for r in st.possible} - {None}) == 1 for st in g.sites):
            n += 1
            sites += len(g.sites)
    return n, sites


def merge_artefacts(groups: list[LinkGroup], tier: Tier) -> int:
    """How many groups that are AMBIGUOUS at `tier` are merges of two or more Tier-A uniquely
    linked groups — `C#run(int) -> T#f` and `C#run(long) -> U#f` becoming one `C#run -> f` at
    Tier B with two runnable targets (issue #51). Those are an artefact of the projection, not
    dispatch, and a perfect tool reads `over_fan` on every one; the count is printed beside the
    ambiguous table so a reader can discount them."""
    return sum(1 for g in groups if not projected_unique(g, tier) and g.merged_unique >= 2)


def projected_unique(g: LinkGroup, tier: Tier) -> bool:
    """Is this group uniquely linked AT `tier`? Judged on the projected target set, so two overloads
    of one method count as the one method they are at Tier B."""
    seen = {p for p in (r.at(tier) for r in g.possible) if p is not None}
    return len(seen) == 1


def summarise(gt: GroundTruth) -> dict:
    """The denominators, printed at the top of every report.

    A precision figure is unreadable without them: 0.98 over 12 edges and 0.98 over 12,000 are not
    the same claim, and a recall denominator that moved between two runs makes the two numbers
    incomparable however similar they look.
    """
    by_op: dict[str, int] = defaultdict(int)
    for s in gt.sites:
        by_op[s.op] += 1
    # COUNTED AT THE HEADLINE TIER. Since issue #2 the verdict tables re-form groups at the tier
    # being scored, so a denominator counted on the Tier A groups disagreed with the table under
    # it (2,308 in the header, n=2,127 in the table on maven-core). Both now say the same thing.
    at_b = groups_at(gt, Tier.B)
    uniq = [g for g in at_b if projected_unique(g, Tier.B)]
    uniq_a = [g for g in gt.groups.values() if g.unique]
    return {
        "subject": gt.subject,
        "app_classes": len(gt.classes),
        "app_methods": len(gt.methods),
        "sites_total": len(gt.sites),
        "sites_internal": sum(1 for s in gt.sites if s.kind == "internal"),
        "sites_boundary": sum(1 for s in gt.sites if s.kind == "boundary"),
        # TypeScript only: a call through a function VALUE, where the checker can name the function
        # TYPE but not which implementation was passed. Recorded so the site counts add up and the
        # blind spot is visible, scored against nothing. Java has no equivalent because a bytecode
        # invoke always names a target.
        "sites_indirect": sum(1 for s in gt.sites if s.kind == "indirect"),
        "sites_by_op": dict(sorted(by_op.items())),
        "edges_certain": len(gt.certain_edges()),
        "edges_possible": len(gt.possible_edges()),
        "edges_possible_rta": len(gt.rta_edges()),
        "link_groups": len(at_b),
        "link_groups_unique": len(uniq),
        "link_groups_ambiguous": len(at_b) - len(uniq),
        "link_groups_unique_tierA": len(uniq_a),
        "link_groups_unique_rta": sum(1 for g in gt.groups.values() if len(g.possible_rta) == 1),
    }
