#!/usr/bin/env python3
"""Rendering a score set into something a reader can check, and a machine can diff.

Two outputs, both deterministic:

  results/<subject>/report.md     for a human — every number beside its denominator
  results/<subject>/scores.json   for a machine — the same data, byte-stable across runs

THREE RULES THE RENDERER ENFORCES, BECAUSE A TABLE IS WHERE A BENCHMARK LIES MOST EASILY
----------------------------------------------------------------------------------------
1. `n/a` is never printed as `0.000`. A tool whose output format cannot express a tier gets a dash
   and a footnote. Zero means "got them all wrong"; a dash means "did not answer this question".

2. A cell that was computed over an excluded denominator says so. `unmapped` and `unspellable`
   counts sit in the same row as the score they affect, so a clean-looking precision computed over
   11 rows of 400 cannot be read as a clean precision.

3. The link-group table is not printed at Tier C. There the group key IS the callee name, so every
   group with the right name scores `exact` by construction and the column would read 100% for any
   tool that emitted anything. A metric that cannot fail is not reported as if it passed.
"""
from __future__ import annotations

import json
from pathlib import Path

from model import Tier
from score import ANCESTOR, EXACT, MISSED, OVER_FAN, PARTIAL, POLLUTED, UNKNOWN, UNPLACED, WRONG, ToolScore


def _f(x: float | None, nd: int = 3) -> str:
    return "—" if x is None else f"{x:.{nd}f}"


def _is_null(by_tier, tier) -> bool:
    sc = by_tier.get(tier)
    return bool(sc and sc.null_model)


def _secs(sc) -> str:
    if sc is None or sc.seconds is None:
        return "—"
    s = sc.seconds
    return f"{s:.0f}s" if s < 90 else f"{s / 60:.1f}m"


def _pct(n: int, d: int) -> str:
    return "—" if not d else f"{100.0 * n / d:.1f}%"


# Per-language provenance. Hardcoding the Java preamble put a claim on every TypeScript report —
# "read from compiled class files … cross-checked against javap" — that was false there, and
# STRONGER than the gate the TypeScript runner actually runs and honestly labels weaker. A
# provenance claim on a published artefact that points the wrong way is the worst class of error
# this benchmark can make, so the text is keyed on the language and nothing else (issue #9).
PROVENANCE = {
    "java": (
        "Java",
        "Ground truth is read from compiled class files with `java.lang.classfile` (JEP 484) and\n"
        "cross-checked instruction-for-instruction against an independent `javap` reader. No tool\n"
        "under test participates in producing it.",
        "call sites read from bytecode",
        "CHA envelope — sound, nominal dispatch",
    ),
    "typescript": (
        "TypeScript",
        "Ground truth is the TypeScript compiler's own type checker (`getResolvedSignature`). There\n"
        "is no second implementation of the type system, so gate 1 checks only that two checker entry\n"
        "points agree — it proves our USE of the checker, not the checker. Calls through a function\n"
        "value, where the checker names a type rather than an implementation, are recorded and NOT\n"
        "scored; their count is in the table below, because on idiomatic TypeScript it is not small.",
        "call sites the checker resolved",
        "declared-heritage + checker-assignable envelope — NOT sound, structural typing",
    ),
}


def render(subject_summary: dict, scores: dict[str, dict[Tier, ToolScore]],
           run_meta: dict) -> str:
    """`scores[tool][tier] -> ToolScore`."""
    L: list[str] = []
    A = L.append
    lang = run_meta.get("language", "java")
    lname, preamble, sites_label, env_label = PROVENANCE.get(lang, PROVENANCE["java"])

    A(f"# {lname} call-graph benchmark — `{subject_summary['subject']}`")
    A("")
    A(preamble)
    A("See `docs/PROTOCOL.md` for every definition below; `docs/CROSS-LANGUAGE.md` for what is and")
    A("is not comparable across languages.")
    A("")

    # ── the subject ──────────────────────────────────────────────────────────────────────────
    A("## The subject, and the denominators every number below is over")
    A("")
    s = subject_summary
    A("| quantity | count |")
    A("|---|---:|")
    for k, label in (
        ("app_classes", "application types"),
        ("app_methods", "application methods"),
        ("sites_total", sites_label),
        ("sites_internal", "… application-internal"),
        ("sites_boundary", "… leaving the application (not scored, see §7)"),
        ("sites_indirect", "… through a function value, target not statically known (not scored)"),
        ("prior_internal_use", "**in the tool under test's own development corpus** — this number measures agreement with a project the tool was developed against, not a clean result"),
        ("sites_unresolved", "call expressions the checker could NOT resolve — no row of any kind; every recall denominator is short by this many, for every tool alike (#53)"),
        ("checker_resolved_pct", "… i.e. the checker resolved this % of the subject's call expressions (gate 0's floor is 55%)"),
        ("checker_target_in_subject_pct", "… and this % resolve to a target INSIDE the subject — the scorable share; a library target clears the floor without adding one (#67)"),
        ("edges_certain", "**CERTAIN** edges (declared targets) — `recall_certain` denominator"),
        ("edges_possible", f"**POSSIBLE** edges ({env_label}) — `recall_possible` denominator"),
        ("edges_possible_rta", "**RTA** edges (instantiated-types envelope) — `recall_rta` denominator"),
        ("link_groups", "link groups `(caller, callee-name)`, at Tier B"),
        ("link_groups_unique", "… **uniquely linked** (exactly one possible target) — the headline denominator"),
        ("link_groups_unique_tierA", "… uniquely linked at Tier A (overloads kept apart)"),
        ("link_groups_ambiguous", "… genuinely ambiguous (dispatch admits several)"),
    ):
        if k in s and s[k] is not False:
            A(f"| {label} | {s[k]:,} |" if isinstance(s[k], int) and not isinstance(s[k], bool) else f"| {label} | {'yes' if s[k] is True else s[k]} |")
    A("")
    A("Call sites by instruction: "
      + ", ".join(f"`{k}` {v}" for k, v in s.get("sites_by_op", {}).items()) + ".")
    A("")

    # ── headline ─────────────────────────────────────────────────────────────────────────────
    A("## Headline — Tier B (`type#name`)")
    A("")
    A("Tier B is the highest fidelity **every** tool under test can express, so it is the only tier")
    A("at which the whole field is comparable. The ground truth is projected to Tier B as well, so a")
    A("tool that cannot spell parameter types is not being asked to.")
    A("")
    A(_table(scores, Tier.B))
    A("")
    A("**`precision`** counts a false positive only OUTSIDE the envelope, so over-approximation")
    A("inside it is free — which is correct for a tool that names the override that actually runs,")
    A("and is why a tool emitting the WHOLE envelope scored 1.000 on it while resolving nothing.")
    A("**`prec-strict`** is the other bound: of everything the tool said, how much was the declared")
    A("answer. Read them as a pair, against the `ideal` row rather than against 1.000 — a")
    A("flow-sensitive tool that is *sharper than the bytecode* gets no credit from the strict bound.")
    A("Rows in *italics* are NULL MODELS, not tools: a floor to clear, never ranked.")
    A("")
    A("**`time`** is wall-clock for the adapter run that produced the answer, on the machine named")
    A("in the provenance block: the tool's own work plus this harness's translation of its output.")
    A("It is an order-of-magnitude figure for *what it costs to ask*, not a micro-benchmark.")
    if lang == "java":
        A("Two rows produced by one adapter invocation — `axiom`/`axiom-nolib`,")
        A("`codeql`/`codeql-dispatch` — share one measured run; splitting it would invent a number.")
    A("")
    A("**`needs`** is what the tool required to produce this answer, and it is a capability rather")
    A("than a score. `compiled build` means a working compile gave it full type information;")
    A("`build-mode=none` means it read the source tree without one; `source only` means it never")
    A("builds. A tool that needs a build is not usable where a build does not run, and a tool that")
    A("does not build is not seeing the same program. Comparing the two without saying so is the")
    A("easiest way to make a table mislead.")
    A("")
    A(_notes(scores, Tier.B))
    A("")

    # ── the discriminator ────────────────────────────────────────────────────────────────────
    A("## Uniquely-linked call resolution — the number that separates the tools")
    A("")
    A(f"Of the {s.get('link_groups_unique', 0):,} link groups where the language admits **exactly one**")
    A("target, what did each tool actually return? A set where one answer exists is not a win, and a")
    A("wrong single answer is worse than an honest set — so the five outcomes are kept apart rather")
    A("than folded into one rate.")
    A("")
    A(_group_table(scores, Tier.B, "unique"))
    A("")
    A("`exact` the one right method, alone · `over_fan` right method plus others, all sound ·")
    A("`polluted` right method plus something no envelope admits · `ancestor` named only a supertype")
    A("that declares the member (weaker, not fabricated) · `wrong` answered, none of it defensible ·")
    A("`missed` returned nothing.")
    A("")

    A("## Genuinely ambiguous call resolution")
    A("")
    A(f"The other {s.get('link_groups_ambiguous', 0):,} groups, where dispatch really does admit several")
    A("targets. Here `over_fan` is the *correct* behaviour and `exact` may mean the tool guessed one")
    A("branch and dropped the rest — so this table is read differently from the one above, and that")
    A("is exactly why they are not combined.")
    pooled = max((sc.get(Tier.B).ambiguous_name_pooled for sc in scores.values() if sc.get(Tier.B)), default=0)
    pooled_sites = max((sc.get(Tier.B).name_pooled_sites for sc in scores.values() if sc.get(Tier.B)), default=0)
    if pooled:
        A("")
        A(f"{pooled:,} of these groups ({pooled_sites:,} call sites) are not dispatch either: several one-target")
        A("calls of the same name in one method — `new A()` and `new B()`, `getProject()` on two receivers —")
        A("pooled under one key (#70). Each call has exactly one target; a tool that names some of them")
        A("but not all reads `partial` here, all of them `exact`.")
    merged = max((sc.get(Tier.B).ambiguous_merge_artefacts for sc in scores.values() if sc.get(Tier.B)), default=0)
    if merged:
        A("")
        A(f"{merged:,} of these groups are not dispatch at all: two or more Tier-A uniquely linked groups")
        A("(overloads of one caller, each with its one target) that merge into one group at Tier B. A")
        A("tool that resolved every one of them correctly reads `over_fan` there (#51) — discount them.")
    A("")
    A(_group_table(scores, Tier.B, "ambiguous"))
    A("")

    # ── chains ───────────────────────────────────────────────────────────────────────────────
    chain_tbl = _chain_table(scores, Tier.B)
    if chain_tbl:
        A("## Call chains — reachability at depth 1..3")
        A("")
        A("Nobody opens a call graph to look at one edge. They ask *if I change this, what breaks?*")
        A("and *can this reach that?* — both questions about PATHS, where error compounds: a chain is")
        A("only as sound as its weakest edge, and at the edge level answering \"all of them\" is free")
        A("(the null model reads precision 1.000 above). Over three hops it is not.")
        A("")
        A("`R@k` is recall of the reachability the declared graph has. `P@k` is the share of what the")
        A("tool claims reachable that the declared graph reaches — the HARSH bound, charging the")
        A("envelope at a genuinely ambiguous call; `P-env@k` is the permissive one, charging only")
        A("outside the envelope's closure. `blowup@k` is the size of the tool's answer over the size of")
        A("the true answer — how many times the real answer a change-impact query gets back. `k=1` is")
        A("the edge metric, so the series reads as one story. Issue #5.")
        A("")
        A(chain_tbl)
        A("")

    # ── overload selection ───────────────────────────────────────────────────────────────────
    A("## Tier A (`type#name(params)`) — overload selection")
    A("")
    A("Only tools whose output carries parameter types can be scored here. A dash is **not** a zero:")
    A("it means the tool's output format does not express the distinction, so the question was never")
    A("put to it.")
    A("")
    A(_table(scores, Tier.A))
    A("")

    A("## Tier C (`name`) — the floor")
    A("")
    A("Method name only, no owner. Reported so that a name-only tool has a number at all. Read it")
    A("knowing that any two same-named methods in the subject are indistinguishable here, which")
    A("inflates every tool's score — the link-group table is **not** reported at this tier, because")
    A("its key is the callee name and every tool would score 100% by construction.")
    A("")
    A(_table(scores, Tier.C))
    A("")

    # ── per confidence label ─────────────────────────────────────────────────────────────────
    conf = _confidence_table(scores, Tier.B)
    if conf:
        A("## Does a tool's own confidence label predict its errors?")
        A("")
        A("Every adapter carries the tool's self-reported confidence verbatim; scoring never reads it.")
        A("`rows`, `precision` and `prec-strict` are computed over the label's own rows. The verdict")
        A("columns are ATTRIBUTED: each uniquely-linked group is charged to the one label whose")
        A("target decided its verdict (the hit for `exact`; the ancestor or extra target for")
        A("`over_fan`; the target outside the envelope for `polluted` / `wrong`), so the columns sum to")
        A("the tool's own totals and a group is never counted twice (#41). `missed` has no label —")
        A("nothing was emitted — and is not a column here. The column to read is `wrong`: if a label")
        A("predicts the error, a consumer can filter on it; if it does not — or is inverted — the")
        A("precision figure above overstates what the output can be used for. Labels of the form")
        A("`term:score` are grouped by term with the score (rounded to two places) as sub-rows.")
        A("")
        A("The labels are the tools' own vocabularies, not one scale: axiom `known_edge` /")
        A("`multi_inferred`; graphify and code-review-graph `EXTRACTED` / `INFERRED`; codegraph")
        A("`<resolvedBy>:<confidence>`; GitNexus `<reason>:<confidence>`; CodeQL (TypeScript)")
        A("`imprecision=N`, 0 precise to 3 heuristic. A tool that also records the calls it could NOT")
        A("resolve is listed below the table: those rows have no target and are never scored, but a")
        A("consumer can tell \"it said it did not know\" from \"it missed\".")
        A("")
        A(conf)
        A("")
        unresolved = []
        for tool in sorted(scores):
            meta = (run_meta.get("tools") or {}).get(tool, {}) or {}
            by = meta.get("rows_by_status") or {}
            scored_labels = set((scores[tool].get(Tier.B).by_confidence or {}).keys()) if scores[tool].get(Tier.B) else set()
            # what each target-less status MEANS is the tool's own vocabulary; only
            # `ambiguous_unknown` is "I could not resolve this call" (#72 §8)
            meaning = {"ambiguous_unknown": "the tool says it could not resolve the call (read as `unknown`, not `missed`, #69)",
                       "boundary_lib": "the callee is outside the staged code (a library)",
                       "ambient_terminal": "the callee is an ambient declaration (a `.d.ts` type) with no body",
                       "intrinsic_terminal": "a language intrinsic with no method body",
                       "ambiguous_anon": "an anonymous target the tool does not name"}
            for label, n in sorted(by.items()):
                if label not in scored_labels and n:
                    what = meaning.get(label, "the callee is outside the staged code (a library)" if "lib" in label or "external" in label
                                       else "a target-less row in the tool's own vocabulary")
                    unresolved.append(f"- `{tool}` wrote {n:,} rows labelled `{label}` with no target — {what}, not scored")
        for u in unresolved:
            A(u)
        if unresolved:
            A("")

    # ── per family ───────────────────────────────────────────────────────────────────────────
    fam = _family_table(scores, Tier.B)
    if fam:
        A("## Per construct family — which language feature each tool loses")
        A("")
        A("A single percentage cannot say *what* a tool gets wrong. Each family is one source file")
        A("exercising one group of constructs; the cell is `exact / uniquely-linked groups`.")
        A("")
        A(fam)
        A("")

    # ── provenance ───────────────────────────────────────────────────────────────────────────
    A("## Provenance")
    A("")
    A("```json")
    A(json.dumps(run_meta, indent=2, sort_keys=True))
    A("```")
    A("")
    return "\n".join(L)


def _table(scores: dict[str, dict[Tier, ToolScore]], tier: Tier) -> str:
    rows = ["| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |",
            "|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    ordered = [t for t in sorted(scores) if not _is_null(scores[t], tier)]
    ordered += [t for t in sorted(scores) if _is_null(scores[t], tier)]
    for tool in ordered:
        sc = scores[tool].get(tier)
        if sc is None or not sc.scorable:
            rows.append(f"| `{tool}` | {sc.build if sc else '—'} | {_secs(sc)} | — | — | — | — | — | — | — | — | "
                        f"*{sc.reason if sc else 'not run'}* |")
            continue
        vc, vp, vr = sc.vs_certain, sc.vs_possible, sc.vs_rta
        assert vc and vp and vr
        excluded = (sc.unmapped_rows + sc.ambiguous_rows + sc.unspellable_rows
                    + sc.excluded_rows)
        # the out-of-scope share is printed AS A SHARE of what the tool emitted: a row whose caller
        # is on a type the application does not declare is excluded, not charged, and a tool that
        # is half out-of-scope must not read as a clean precision (#35)
        share = f", {100 * sc.unmapped_rows / sc.edges_emitted:.0f}% of emitted" if sc.edges_emitted and sc.unmapped_rows else ""
        dup = f", {sc.duplicate_rows} duplicate" if sc.duplicate_rows else ""
        exc = ("0" if excluded == 0 else (
            f"{excluded} ({sc.ambiguous_rows} ambig, {sc.unmapped_rows} out-of-scope{share}, "
            f"{sc.unspellable_rows} unspellable, {sc.excluded_rows} §4-excluded)")) + dup
        rows.append(
            f"| {'*`' + tool + '`*' if sc.null_model else '`' + tool + '`'} | {sc.build} | {_secs(sc)} | "
            f"{_f(vp.precision)} | {_f(vc.precision_strict)} | {_f(vc.recall)} | {_f(vp.recall)} | "
            f"{_f(vr.recall)} | {_f(vc.f1_strict)} | {_f(vc.mcc_strict)} | {sc.edges_scored:,} | {exc} |")
    return "\n".join(rows)


def _notes(scores: dict[str, dict[Tier, ToolScore]], tier: Tier) -> str:
    notes = []
    for tool in sorted(scores):
        sc = scores[tool].get(tier)
        if sc and sc.scorable and (sc.ambiguous_rows or sc.unmapped_rows):
            notes.append(
                f"- `{tool}`: {sc.ambiguous_rows} rows named a type that matches more than one "
                f"application type, {sc.unmapped_rows} named a type outside the application or one "
                f"that could not be placed. Both are excluded from the numbers above rather than "
                f"counted for or against — see `docs/PROTOCOL.md` §5.")
    return "\n".join(notes) if notes else "*Every emitted row was placed in the subject.*"


def _group_table(scores: dict[str, dict[Tier, ToolScore]], tier: Tier, which: str) -> str:
    rows = [f"| tool | {EXACT} | {OVER_FAN} | {PARTIAL} | {POLLUTED} | {ANCESTOR} | {WRONG} | {UNKNOWN} | {UNPLACED} | {MISSED} | n | exact rate |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for tool in sorted(scores):
        sc = scores[tool].get(tier)
        if sc is None or not sc.scorable:
            rows.append(f"| `{tool}` | — | — | — | — | — | — | — | — | — | — | — |")
            continue
        g = sc.unique_groups if which == "unique" else sc.ambiguous_groups
        rows.append(
            f"| `{tool}` | {g.verdicts[EXACT]} | {g.verdicts[OVER_FAN]} | {g.verdicts[PARTIAL]} | {g.verdicts[POLLUTED]} | "
            f"{g.verdicts[ANCESTOR]} | {g.verdicts[WRONG]} | {g.verdicts[UNKNOWN]} | {g.verdicts[UNPLACED]} | {g.verdicts[MISSED]} | {g.total} | "
            f"{_pct(g.verdicts[EXACT], g.total)} |")
    return "\n".join(rows)


def _chain_table(scores: dict[str, dict[Tier, ToolScore]], tier: Tier) -> str:
    """Reachability at depth 1..3 — what a change-impact or reachability consumer actually gets."""
    depths: list[int] = []
    for t in scores.values():
        sc = t.get(tier)
        if sc and sc.chains:
            depths = sorted(sc.chains.by_depth)
            break
    if not depths:
        return ""
    head = "| tool | needs |" + "".join(f" R@{k} | P@{k} | P-env@{k} | blowup@{k} |" for k in depths)
    rule = "|---|:--|" + "---:|" * (4 * len(depths))
    rows = [head, rule]
    ordered = [t for t in sorted(scores) if not _is_null(scores[t], tier)]
    ordered += [t for t in sorted(scores) if _is_null(scores[t], tier)]
    for tool in ordered:
        sc = scores[tool].get(tier)
        name = f"*`{tool}`*" if _is_null(scores[tool], tier) else f"`{tool}`"
        if sc is None or not sc.scorable or not sc.chains:
            rows.append(f"| {name} | {sc.build if sc else '—'} |" + " — |" * (4 * len(depths)))
            continue
        cells = []
        for k in depths:
            d = sc.chains.by_depth[k]
            cells += [_f(d["recall"]), _f(d["precision"]), _f(d["precision_env"]),
                      "—" if d["blowup"] is None else f"{d['blowup']:.2f}×"]
        rows.append(f"| {name} | {sc.build} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def _confidence_table(scores: dict[str, dict[Tier, ToolScore]], tier: Tier) -> str:
    rows = ["| tool | label | rows | precision | prec-strict | exact | over_fan | polluted | ancestor | wrong |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    any_ = False

    def line(tool: str, label: str, d: dict, sub: bool = False) -> str:
        return (f"| {tool} | {'&nbsp;&nbsp;↳ ' if sub else ''}`{label}` | {d['rows']:,} | {_f(d['precision'])} | "
                f"{_f(d['precision_strict'])} | {d['exact']} | {d.get('over_fan', 0)} | {d.get('polluted', 0)} | "
                f"{d.get('ancestor', 0)} | {d['wrong']} |")

    for tool in sorted(scores):
        sc = scores[tool].get(tier)
        if not sc or not sc.scorable or not sc.by_confidence:
            continue
        for label, d in sorted(sc.by_confidence.items()):
            any_ = True
            rows.append(line(f"`{tool}`", label, d))
            for sub, sd in sorted((d.get("by_score") or {}).items()):
                rows.append(line("", sub, sd, sub=True))
    return "\n".join(rows) if any_ else ""


def _family_table(scores: dict[str, dict[Tier, ToolScore]], tier: Tier) -> str:
    fams: set[str] = set()
    for t in scores.values():
        sc = t.get(tier)
        if sc and sc.scorable:
            fams |= set(sc.by_family)
    if not fams:
        return ""
    order = sorted(fams)
    rows = ["| tool | " + " | ".join(order) + " |",
            "|---" * (len(order) + 1) + "|"]
    for tool in sorted(scores):
        sc = scores[tool].get(tier)
        if sc is None or not sc.scorable:
            rows.append(f"| `{tool}` | " + " | ".join("—" for _ in order) + " |")
            continue
        cells = []
        for f in order:
            d = sc.by_family.get(f, {})
            u = d.get("unique", {})
            n = u.get("total", 0)
            e = u.get("counts", {}).get(EXACT, 0)
            cells.append("—" if not n else f"{e}/{n}")
        rows.append(f"| `{tool}` | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def write(out_dir: Path, subject_summary: dict, scores: dict[str, dict[Tier, ToolScore]],
          run_meta: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text(
        render(subject_summary, scores, run_meta), encoding="utf-8")
    payload = {
        "subject": subject_summary,
        "run": run_meta,
        "scores": {tool: {t.value: sc.as_dict() for t, sc in by_tier.items()}
                   for tool, by_tier in scores.items()},
    }
    (out_dir / "scores.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
