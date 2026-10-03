#!/usr/bin/env python3
"""Render the README's result tables from results/*/scores.json — never by hand.

A hand-edited results table drifts from the data behind it the first time a subject is re-run. This
reads every `scores.json` that exists and prints the Markdown the README embeds between two markers,
so `python3 bench/readme_tables.py --write` is the only way a number gets into the README and the
README can never claim something the JSON does not.

    python3 bench/readme_tables.py            # print
    python3 bench/readme_tables.py --write    # splice into README.md between the markers
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- results:begin -->"
END = "<!-- results:end -->"
# the standings under "Where axiomengine lands": every number in that paragraph is generated,
# because hand-written ones drifted from the tables beside them (#34, #94)
SBEGIN = "<!-- standings:begin -->"
SEND = "<!-- standings:end -->"

ORDER = {
    "java": ["torture", "maven-core", "netty-transport", "spring-boot", "apache-ant", "rxjava", "gson"],
    "typescript": ["torture", "kysely", "typedoc", "fp-ts", "ioredis", "excalidraw", "type-graphql", "ts-morph", "cheerio"],
}
# The five REAL projects per language — the comparison. `torture` is a diagnostic and stays out of
# the summary; type-graphql was replaced by excalidraw at the user's request and keeps its full
# table in docs/RESULTS.md.
COMPARE = {
    "java": ["maven-core", "netty-transport", "spring-boot", "apache-ant", "rxjava"],
    "typescript": ["kysely", "typedoc", "fp-ts", "ioredis", "excalidraw"],
}
FULL = "docs/RESULTS.md"
# where the published run was measured — named in the time note, since every `seconds` depends on it
RUN_HOST = "GCP c3-standard-22, Intel Xeon Platinum 8481C, 22 vCPU, 88 GB, Ubuntu 24.04"

# Row labels. Tool ids (`axiom`, `axiom-nolib`, ...) are what the adapters, edge files and scores.json
# carry; the product is called AxiomEngine, so its rows print under that name. Every other id prints
# as-is.
DISPLAY = {"axiom": "AxiomEngine", "axiom-nolib": "AxiomEngine"}

# THE HEADLINE IS LIBRARY-FREE. A row whose run was given the subject's external libraries — the
# JDK's platform IR (Java `axiom`), a compiled build with its classpath (CodeQL on a local subject) —
# can type a receiver that comes out of a library call (`list.get(0).foo()`); a source-only tool
# cannot, and was charged a miss for it. Every ranked table compares library-free rows only; the
# library-enabled rows are published beside their library-free counterpart in their own table,
# never ranked. Decided from the budget each row records, so a new tool is classified the same way.
LIBRARY_BUILDS = ("platform IR", "compiled build")


def uses_libraries(b: dict) -> bool:
    return any(k in (b.get("build") or "") for k in LIBRARY_BUILDS)


def library_free(scores: dict) -> dict:
    """The rows a ranked table compares: every row whose run was not given external libraries."""
    return {t: byt for t, byt in scores.items() if not uses_libraries(byt["B"])}


def display(t: str, lib: bool = False) -> str:
    return DISPLAY.get(t, t) + (" + libraries" if lib else "")


def label(t: str, null: bool = False, lib: bool = False) -> str:
    """Markdown cell for a tool row: italic for the null model, bold for AxiomEngine's headline row."""
    name = f"`{display(t, lib)}`"
    if null:
        return f"*{name}*"
    return f"**{name}**" if t in ("axiom", "axiom-nolib") and not lib else name


def sharpness(b: dict, ideal_b: dict | None) -> float:
    """`min(1, prec-strict / ideal prec-strict)` — how much of what the row said was the declared
    answer, calibrated on the `ideal` reference row (the correct answer for every group). 1.0 for
    a row as sharp as the truth; the CHA envelope's is its own strict precision (0.03 on rxjava,
    0.74 on maven-core)."""
    st = b["vs_certain"].get("precision_strict") or 0.0
    ist = (ideal_b or {}).get("vs_certain", {}).get("precision_strict") or 1.0
    return min(1.0, st / ist) if ist else 0.0


def adjusted_exact(b: dict, ideal_b: dict | None) -> float:
    """exact% × sharpness — a DIAGNOSTIC, printed small beside exact%, never the ranking column.
    It was the ranking column for one pass (#49's proposal): it multiplies by strict precision,
    which charges every emitted row that is not the declared target — a tool naming the three
    overrides that can run at a dispatching site pays for two of them — while a tool that emits
    few edges pays nothing for what it leaves out beyond the groups it misses. A row with 65%
    exact and blowup 0.5× outranked one with 83% exact: the number rewarded under-reporting,
    the opposite of what a call graph is for. The README ranks on exact% — the benchmark's own
    question — with the null model's row printed as the floor it is and the † composition marker
    for enumeration; this figure and the chains matrix carry the fan-out side of the story."""
    g = b["unique_link_groups"]
    ex = g["counts"].get("exact", 0) / g["total"] if g["total"] else 0.0
    return 100 * ex * sharpness(b, ideal_b)


def envelope_class(b: dict, null_b: dict | None, ideal_b: dict | None = None) -> bool:
    """ISSUE #12 / #49. A row is envelope-class on a subject when its OWN OUTPUT COMPOSITION is the
    envelope's: it reproduces at least 80% of the envelope's fan share (`precision − prec-strict`
    against `1 − null strict`) and its strict precision is below 1.5× the null model's. A margin,
    not `<=`: the first rule let a dispatch row 0.0009 above the null's strict precision rank
    first unmarked on rxjava, and fired on 0 of 82 cells (#49).

    Composition, not score: comparing the adjusted score to the null model's would flag a tool
    that answers sharply but misses 20% of the groups, because the null row is built from the
    oracle's own envelope and has perfect recall by construction — that is a recall gap, not
    enumeration. Not applied where the subject barely dispatches (null strict ≥ 0.9): there the
    envelope ≈ the declared set and nothing can be told apart."""
    if not null_b:
        return False
    ns = null_b["vs_certain"].get("precision_strict") or 0.0
    if ns >= DISPATCH_LIGHT:
        return False
    strict = b["vs_certain"].get("precision_strict") or 0.0
    fan = (b["vs_possible"]["precision"] or 0.0) - strict
    return strict < ENVELOPE_STRICT_RATIO * ns and fan >= ENVELOPE_FAN_SHARE * (1.0 - ns)


ENVELOPE_STRICT_RATIO = 1.5   # prec-strict must be below this multiple of the null model's
ENVELOPE_FAN_SHARE = 0.8      # ... while reproducing at least this share of the envelope's fan
DISPATCH_LIGHT = 0.9   # null-model strict precision at or above which the subject barely fans


def fmt(x: float | None) -> str:
    return "—" if x is None else f"{x:.3f}"


def secs(x: float | None) -> str:
    if x is None:
        return "—"
    return f"{x:.0f}s" if x < 90 else f"{x / 60:.1f}m"


def table(lang: str, subject: str) -> str | None:
    p = ROOT / lang / "results" / subject / "scores.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8"))
    sub = d["subject"]
    rows, null_rows = [], []
    for tool, byt in d["scores"].items():
        b = byt["B"]
        if not b["scorable"]:
            continue
        g = b["unique_link_groups"]["counts"]
        n = b["unique_link_groups"]["total"]
        e = g.get("exact", 0)
        row = (e, tool, b, g, n, byt["A"]["scorable"])
        (null_rows if b.get("null_model") else rows).append(row)
    rows.sort(reverse=True)

    cha = [r for r in null_rows if r[2].get("build") != "oracle"]
    ideal = [r for r in null_rows if r[2].get("build") == "oracle"]
    null_b = cha[0][2] if cha else None
    ideal_b = ideal[0][2] if ideal else None
    null_strict = (null_b["vs_certain"].get("precision_strict") or 0.0) if null_b else 0.0
    fans = null_strict < DISPATCH_LIGHT
    resolving = [r for r in rows if not envelope_class(r[2], null_b, ideal_b)]
    envelope = [r for r in rows if r not in resolving]
    # ranked on exact%, the README's column (rows are (exact, tool, ...), sorted above)

    hdr = ("| tool | needs | time | tier | precision | **prec-strict** | R certain | R possible | "
           "**exact** | fan | poll | anc | wrong | missed | exact % | **adjusted** |\n"
           "|---|:--|---:|:--:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    lines = [hdr]
    def emit(e, tool, b, g, n, a):
        vc, vp = b["vs_certain"], b["vs_possible"]
        name = label(tool, null=bool(b.get("null_model")), lib=uses_libraries(b))
        lines.append(
            f"| {name} | {b.get('build', '?')} | {secs(b.get('seconds'))} | {'A' if a else 'B'} | "
            f"{fmt(vp['precision'])} | {fmt(vc.get('precision_strict'))} | {fmt(vc['recall'])} | "
            f"{fmt(vp['recall'])} | {e} | {g.get('over_fan', 0)} | {g.get('polluted', 0)} | "
            f"{g.get('ancestor', 0)} | {g.get('wrong', 0)} | {g.get('missed', 0)} | {100 * e / n:.1f}% | "
            f"{adjusted_exact(b, ideal_b):.1f} |")
    for r in resolving:
        emit(*r)
    if envelope or null_rows:
        note = (f"envelope-class: fan share ≥ {ENVELOPE_FAN_SHARE:.0%} of the envelope's and prec-strict < {ENVELOPE_STRICT_RATIO}× the null model's" if fans
                else "dispatch-light subject (null model strict ≥ 0.9): the envelope-class rule cannot discriminate here")
        lines.append(f"| *— {note} —* | | | | | | | | | | | | | | | |")
        for r in envelope + null_rows:
            emit(*r)

    ratio = sub['edges_possible'] / max(sub['edges_certain'], 1)
    head = (f"{sub['app_classes']:,} types · {sub['app_methods']:,} methods · "
            f"{sub['sites_total']:,} call sites · {sub['edges_certain']:,} certain / "
            f"{sub['edges_possible']:,} envelope edges (**{ratio:.1f}×**) · "
            f"**{sub['link_groups_unique']:,} uniquely-linked** groups")
    if sub.get("sites_indirect"):
        head += f" · {sub['sites_indirect']:,} sites through a function value (not scored)"
    if sub.get("sites_unresolved"):
        head += (f" · **{sub['sites_unresolved']:,} call expressions the checker could not resolve** "
                 f"({sub.get('checker_resolved_pct')}% resolved; no row, every denominator short by that)")
    return f"##### `{subject}`\n\n{head}\n\n" + "\n".join(lines) + "\n"


def summary(lang: str) -> str:
    """ONE matrix per language: subject × tool -> `exact% / adjusted`, ranked on exact%, with the
    null model's row as the floor line. This is what the README shows; the
    per-subject tables with every column live in docs/RESULTS.md."""
    subjects = [s for s in COMPARE[lang] if (ROOT / lang / "results" / s / "scores.json").exists()]
    data: dict[str, dict[str, tuple[float, float, int, bool, int, bool]]] = {}   # tool -> subject -> (adjusted, exact%, n, envelope-class, found, below-null)
    ns: dict[str, int] = {}
    null_name = None
    for sub in subjects:
        d = json.loads((ROOT / lang / "results" / sub / "scores.json").read_text(encoding="utf-8"))
        null_b = ideal_b = None
        for t, byt in library_free(d["scores"]).items():
            b = byt["B"]
            if b["scorable"] and b.get("null_model"):
                if b.get("build") == "oracle":
                    ideal_b = b
                else:
                    null_b, null_name = b, t
        for t, byt in library_free(d["scores"]).items():
            b = byt["B"]
            if not b["scorable"] or (b.get("null_model") and b.get("build") == "oracle"):
                continue
            g = b["unique_link_groups"]
            pct = 100 * g["counts"].get("exact", 0) / g["total"] if g["total"] else 0.0
            below = (not b.get("null_model") and null_b is not None
                     and (b["vs_certain"].get("precision_strict") or 0.0) < (null_b["vs_certain"].get("precision_strict") or 0.0))
            data.setdefault(t, {})[sub] = (adjusted_exact(b, ideal_b), pct, g["total"],
                                           False if b.get("null_model") else envelope_class(b, null_b, ideal_b),
                                           g["counts"].get("exact", 0), below)
            ns[sub] = g["total"]
    real = [t for t in data if t != null_name]
    # RANKED WITH † CELLS EXCLUDED: a cell whose composition is the envelope's is "not counted as
    # a lead", so it contributes nothing to the row's ranking key (#12 reopened); the cell itself
    # is still printed, marked
    def rank_key(t: str) -> float:
        vals = [v[4] for v in data[t].values() if not v[3]]
        tot = [v[2] for v in data[t].values() if not v[3]]
        return -sum(vals) / sum(tot) if tot else 0.0
    tools = sorted(real, key=rank_key)
    if null_name in data:
        tools.append(null_name)
    hdr = "| tool | " + " | ".join(subjects) + " | all five |"
    sep = "|---|" + "---:|" * (len(subjects) + 1)
    lines = [hdr, sep]
    source = "bytecode" if lang == "java" else "type checker"
    lines.append(f"| **ground truth** ({source}): one-target groups | "
                 + " | ".join(f"**{ns[s]:,}** <sub>100%</sub>" for s in subjects)
                 + f" | **{sum(ns.values()):,}** <sub>100%</sub> |")
    for t in tools:
        cells, found, of, any_env = [], 0, 0, False
        for s in subjects:
            v = data[t].get(s)
            if v is None:
                cells.append("—")
                continue
            adj, pct, n, env, e, below = v
            found += e; of += n; any_env |= env
            cell = f"*{e:,}* <sub>{pct:.1f}%</sub>†" if env else f"{e:,} <sub>{pct:.1f}%</sub>"
            if below and not env:
                cell += "↓"
            cells.append(cell)
        mean = (f"{found:,} <sub>{100 * found / of:.1f}%</sub>" + ("†" if any_env else "")) if of else "—"
        name = label(t, null=(t == null_name))
        lines.append(f"| {name} | " + " | ".join(cells) + f" | {mean} |")
    return "\n".join(lines)


VERDICTS = (("exact", "found"), ("over_fan", "fan"), ("polluted", "polluted"), ("ancestor", "vague"),
            ("wrong", "wrong"), ("unknown", "unknown"), ("unplaced", "unplaced"), ("missed", "missed"))


def full_set_note(lang: str) -> str:
    """The headline compares five subjects per language; the repository commits more. The
    pooled found% of the two leading rows over EVERY committed non-torture subject is printed so
    the choice of five is disclosed rather than silent — on TypeScript the lead reverses on the
    full set (#72 §4)."""
    subs = [s for s in ORDER[lang] if s != "torture" and (ROOT / lang / "results" / s / "scores.json").exists()]
    extra = [s for s in subs if s not in COMPARE[lang]]
    if not extra:
        return ""
    found: dict[str, int] = {}
    of: dict[str, int] = {}
    for sub in subs:
        d = json.loads((ROOT / lang / "results" / sub / "scores.json").read_text(encoding="utf-8"))
        for t, byt in library_free(d["scores"]).items():
            b = byt["B"]
            if not b["scorable"] or b.get("null_model"):
                continue
            g = b["unique_link_groups"]
            found[t] = found.get(t, 0) + g["counts"].get("exact", 0)
            of[t] = of.get(t, 0) + g["total"]
    ranked = sorted((t for t in found if of[t]), key=lambda t: -found[t] / of[t])
    top = ", ".join(f"`{display(t)}` {100 * found[t] / of[t]:.1f}% ({found[t]:,}/{of[t]:,})" for t in ranked[:3])
    return (f"Over all {len(subs)} committed non-torture {lang.replace('typescript', 'TypeScript').replace('java', 'Java')} "
            f"subjects (the five above plus {', '.join(extra)}, whose tables are in `{FULL}`): {top}. "
            f"The five compared were chosen before this pass; the sensitivity to that choice is stated here so it is not silent.")


def verdicts(lang: str) -> str:
    """ONE table per language, every number a COUNT against the same denominator. The first row
    is the ground truth itself — how many uniquely linked calls the bytecode (Java) or the
    checker (TypeScript) says there are, per subject — and every tool row partitions exactly
    that many calls into found / fan / polluted / wrong / missed, so each row sums to the
    ground-truth row and a reader can link any cell back to the oracle. The percentages in the
    matrix above are `found / ground truth`; this is where they come from."""
    subjects = [s for s in COMPARE[lang] if (ROOT / lang / "results" / s / "scores.json").exists()]
    truth: dict[str, int] = {}
    per_tool: dict[str, dict[str, dict[str, int]]] = {}
    env_flags: dict[str, set[str]] = {}
    source = "bytecode" if lang == "java" else "type checker"
    for sub in subjects:
        d = json.loads((ROOT / lang / "results" / sub / "scores.json").read_text(encoding="utf-8"))
        truth[sub] = d["subject"]["link_groups_unique"]
        null_b = ideal_b = None
        for t, byt in library_free(d["scores"]).items():
            b = byt["B"]
            if b["scorable"] and b.get("null_model"):
                if b.get("build") == "oracle":
                    ideal_b = b
                else:
                    null_b = b
        for t, byt in library_free(d["scores"]).items():
            b = byt["B"]
            if not b["scorable"] or b.get("null_model"):
                continue
            per_tool.setdefault(t, {})[sub] = b["unique_link_groups"]["counts"]
            if envelope_class(b, null_b, ideal_b):
                env_flags.setdefault(t, set()).add(sub)
    total = sum(truth.values())
    # the same ranking as the headline: † cells left out of the key (#12)
    def rank_key(t: str) -> float:
        subs = [s for s in per_tool[t] if s not in env_flags.get(t, set())]
        n = sum(truth[s] for s in subs)
        return -sum(per_tool[t][s].get("exact", 0) for s in subs) / n if n else 0.0
    tools = sorted(per_tool, key=rank_key)
    lines = ["| tool | found | fan | polluted | vague | wrong | unknown | unplaced | missed | of | found % |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    lines.append(f"| **ground truth** ({source}) | — | — | — | — | — | — | — | — | **{total:,}** | — |")
    for t in tools:
        c = {k: sum(per_tool[t].get(s, {}).get(k, 0) for s in subjects) for k, _ in VERDICTS}
        n = sum(sum(per_tool[t].get(s, {}).values()) for s in subjects)
        name = label(t)
        if env_flags.get(t):
            name += "†"
        lines.append(f"| {name} | {c['exact']:,} | {c['over_fan']:,} | {c['polluted']:,} | {c['ancestor']:,} | "
                     f"{c['wrong']:,} | {c['unknown']:,} | {c['unplaced']:,} | {c['missed']:,} | {n:,} | {100 * c['exact'] / n:.1f}% |")
    # per subject, the same partition
    lines.append("")
    lines.append("| tool | " + " | ".join(f"{s}<br><sub>{truth[s]:,} calls</sub>" for s in subjects) + " |")
    lines.append("|---|" + "---:|" * len(subjects))
    lines.append(f"| **ground truth** ({source}) | " + " | ".join(f"{truth[s]:,}" for s in subjects) + " |")
    for t in tools:
        cells = []
        for s in subjects:
            c = per_tool[t].get(s)
            cells.append("—" if c is None else
                         f"{c.get('exact', 0):,} · {c.get('over_fan', 0)} · {c.get('polluted', 0)} · {c.get('ancestor', 0)} · {c.get('wrong', 0)} · {c.get('unknown', 0)} · {c.get('unplaced', 0)} · {c.get('missed', 0):,}")
        name = label(t)
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def bounds_table(lang: str) -> str:
    """The three bounds side by side, every cell a COUNT and the percentage of the ground-truth
    row it is. The ground-truth row says how many edges each bound holds over the five compared
    subjects — CERTAIN (the declared target: what the instruction names), RTA (the targets that
    can run on receivers the program actually instantiates) and CHA (every target that can run
    under class-hierarchy dispatch); each tool row says how many of those edges it found, how many
    of its own rows lay inside the CHA envelope (precision) and how many were the declared target
    (strict). Counts are summed over the subjects, so the percentages are pooled — and pooled
    recall against RTA/CHA is dominated by rxjava's 380,000-edge envelope; the per-subject values
    are in docs/RESULTS.md."""
    subjects = [s for s in COMPARE[lang] if (ROOT / lang / "results" / s / "scores.json").exists()]
    gt = {"certain": 0, "rta": 0, "possible": 0, "unique": 0}
    acc: dict[str, dict[str, int]] = {}
    null_flags: dict[str, bool] = {}
    keys = ("exact", "n", "tp_c", "tp_r", "tp_p", "fp", "emitted", "inside")
    for sub in subjects:
        d = json.loads((ROOT / lang / "results" / sub / "scores.json").read_text(encoding="utf-8"))
        S = d["subject"]
        gt["unique"] += S["link_groups_unique"]
        # the bounds AT TIER B — tp + fn of any scored row is the projected truth size, and the
        # tool counts below are Tier-B projections too (two overloads are one method there)
        first = next(byt["B"] for byt in d["scores"].values() if byt["B"]["scorable"])
        gt["certain"] += first["vs_certain"]["tp"] + first["vs_certain"]["fn"]
        gt["rta"] += first["vs_rta"]["tp"] + first["vs_rta"]["fn"]
        gt["possible"] += first["vs_possible"]["tp"] + first["vs_possible"]["fn"]
        for t, byt in library_free(d["scores"]).items():
            b = byt["B"]
            if not b["scorable"]:
                continue
            a = acc.setdefault(t, {k: 0 for k in keys})
            null_flags[t] = bool(b.get("null_model"))
            a["exact"] += b["unique_link_groups"]["counts"].get("exact", 0); a["n"] += b["unique_link_groups"]["total"]
            a["tp_c"] += b["vs_certain"]["tp"]; a["tp_r"] += b["vs_rta"]["tp"]; a["tp_p"] += b["vs_possible"]["tp"]
            a["fp"] += b["vs_possible"]["fp"]; a["emitted"] += b["vs_certain"]["emitted"]
            # rows inside the envelope = everything scored that was not a false positive
            a["inside"] += b["edges_scored"] - b["vs_possible"]["fp"]
    def cell(k, of): return f"{k:,} <sub>{100 * k / of:.1f}%</sub>" if of else "—"
    lines = ["| tool | one target: found | CERTAIN edges found | RTA edges found | CHA edges found | rows emitted | … inside the envelope | … the declared target |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    lines.append(f"| **ground truth** | **{gt['unique']:,}** | **{gt['certain']:,}** | **{gt['rta']:,}** | **{gt['possible']:,}** | — | — | — |")
    tools = sorted((t for t in acc if not null_flags[t]), key=lambda t: -acc[t]["exact"] / max(acc[t]["n"], 1))
    tools += sorted(t for t in acc if null_flags[t])
    for t in tools:
        a = acc[t]
        name = label(t, null=null_flags[t])
        lines.append(f"| {name} | {cell(a['exact'], gt['unique'])} | {cell(a['tp_c'], gt['certain'])} | "
                     f"{cell(a['tp_r'], gt['rta'])} | {cell(a['tp_p'], gt['possible'])} | {a['emitted']:,} | "
                     f"{cell(a['inside'], a['emitted'])} | {cell(a['tp_c'], a['emitted'])} |")
    return "\n".join(lines)


def accuracy_table(lang: str) -> str:
    """Edge-level F1 and where each tool's rows go, pooled over the five compared subjects from the
    counts (not averaged ratios): of a tool's rows, `strict` are the declared target, `fan` could run
    but are not declared (other overrides), `noise` lie outside the class-hierarchy envelope and can
    never run. F1 uses precision = strict + fan; F1-strict charges the fan too. Recall is over the
    declared (CERTAIN) edges."""
    subjects = [s for s in COMPARE[lang] if (ROOT / lang / "results" / s / "scores.json").exists()]
    acc: dict[str, dict[str, int]] = {}
    null_flags: dict[str, bool] = {}
    for sub in subjects:
        d = json.loads((ROOT / lang / "results" / sub / "scores.json").read_text(encoding="utf-8"))
        for t, byt in library_free(d["scores"]).items():
            b = byt["B"]
            if not b["scorable"] or b.get("build") == "oracle":
                continue
            a = acc.setdefault(t, {"tp": 0, "fn": 0, "em": 0, "fp": 0, "ex": 0, "n": 0})
            null_flags[t] = bool(b.get("null_model"))
            c, p = b["vs_certain"], b["vs_possible"]
            a["tp"] += c["tp"]; a["fn"] += c["fn"]; a["em"] += c["emitted"]; a["fp"] += p["fp"]
            g = b["unique_link_groups"]; a["ex"] += g["counts"].get("exact", 0); a["n"] += g["total"]
    lines = ["| tool | F1 | F1-strict | recall | precision | strict | fan | noise |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    tools = sorted((t for t in acc if not null_flags[t]), key=lambda t: -acc[t]["ex"] / max(acc[t]["n"], 1))
    tools += sorted(t for t in acc if null_flags[t])
    for t in tools:
        a = acc[t]
        if not a["em"]:
            continue
        rec = a["tp"] / max(a["tp"] + a["fn"], 1)
        noise = a["fp"] / a["em"]; prec = 1 - noise; strict = a["tp"] / a["em"]; fan = prec - strict
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        f1s = 2 * strict * rec / (strict + rec) if strict + rec else 0.0
        lines.append(f"| {label(t, null=null_flags[t])} | {f1:.3f} | {f1s:.3f} | {rec:.3f} | {prec:.3f} | "
                     f"{strict:.3f} | {fan:.3f} | {noise:.3f} |")
    return "\n".join(lines)


TASKS = (("callees_of", "mean_f1", "n"), ("callers_of", "mean_f1", "n"), ("path", "share", "n"),
         ("blast_radius", "mean_jaccard", "n"), ("uncalled", "precision", "claims"), ("uncalled", "recall", "truth"),
         ("dispatch", "mean_jaccard", "n"), ("file_deps", "f1", "truth"))


def tasks_table(lang: str) -> str:
    """Seven questions a consumer runs on a call graph, each scored against the ground truth on its
    own terms (bench/tasks.py), pooled over the five compared subjects — weighted by each
    subject's sample size for that task. Same edges, same truth, same tier as the headline."""
    subjects = [s for s in COMPARE[lang] if (ROOT / lang / "results" / s / "scores.json").exists()]
    acc: dict[str, dict[tuple, list]] = {}
    null_flags: dict[str, bool] = {}
    exact: dict[str, list] = {}
    for sub in subjects:
        d = json.loads((ROOT / lang / "results" / sub / "scores.json").read_text(encoding="utf-8"))
        for t, byt in library_free(d["scores"]).items():
            b = byt["B"]
            if not b["scorable"] or not b.get("tasks"):
                continue
            null_flags[t] = bool(b.get("null_model"))
            g = b["unique_link_groups"]
            exact.setdefault(t, []).append(g["counts"].get("exact", 0) / max(g["total"], 1))
            for task, metric, weight in TASKS:
                v = b["tasks"].get(task, {})
                if v.get(metric) is None:
                    continue
                acc.setdefault(t, {}).setdefault((task, metric), []).append((v[metric], v.get(weight) or 1))
    tools = sorted((t for t in acc if not null_flags[t]), key=lambda t: -sum(exact[t]) / len(exact[t]))
    tools += sorted(t for t in acc if null_flags[t])
    hdr = ("| tool | callees of a method<br><sub>mean F1</sub> | callers of a method<br><sub>mean F1</sub> | "
           "path A→B exists<br><sub>share</sub> | blast radius (3 hops)<br><sub>mean Jaccard</sub> | "
           "\"nothing calls X\"<br><sub>precision</sub> | \"nothing calls X\"<br><sub>recall</sub> | "
           "dispatch set at ambiguous sites<br><sub>mean Jaccard</sub> | file→file dependencies<br><sub>F1</sub> |")
    lines = [hdr, "|---|" + "---:|" * len(TASKS)]
    for t in tools:
        cells = []
        for task, metric, _ in TASKS:
            vals = acc[t].get((task, metric))
            if not vals:
                cells.append("—")
                continue
            w = sum(n for _, n in vals)
            cells.append(f"{sum(v * n for v, n in vals) / w:.3f}" if w else "—")
        name = label(t, null=null_flags[t])
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def oracle_table(lang: str) -> str:
    """What the ground truth itself saw, per subject — the JDK's bytecode readers (Java) or the
    type checker (TypeScript) before any tool is scored: the sizes every percentage is a fraction
    of. A precision over 12 edges and one over 12,000 are not the same claim."""
    rows = []
    ts = lang == "typescript"
    hdr = ("| subject | files | lines | types | methods | call sites | internal | boundary"
           + (" | indirect | unresolved" if ts else "")
           + " | certain edges | RTA edges | CHA edges | CHA ÷ certain | one target | several targets |")
    sep = "|---|" + "---:|" * (hdr.count("|") - 2)
    rows += [hdr, sep]
    for sub in ORDER[lang]:
        p = ROOT / lang / "results" / sub / "scores.json"
        if not p.exists():
            continue
        S = json.loads(p.read_text(encoding="utf-8"))["subject"]
        ratio = S["edges_possible"] / max(S["edges_certain"], 1)
        cells = [sub, f"{S.get('source_files') or '—'}", f"{S.get('source_lines') or '—'}",
                 f"{S['app_classes']:,}", f"{S['app_methods']:,}", f"{S['sites_total']:,}",
                 f"{S['sites_internal']:,}", f"{S['sites_boundary']:,}"]
        if ts:
            cells += [f"{S.get('sites_indirect', 0):,}", f"{S.get('sites_unresolved', 0):,}"]
        cells += [f"{S['edges_certain']:,}", f"{S['edges_possible_rta']:,}", f"{S['edges_possible']:,}", f"{ratio:.1f}×",
                  f"**{S['link_groups_unique']:,}**", f"{S['link_groups_ambiguous']:,}"]
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def size_time(lang: str) -> str:
    """Subjects by size, with every tool's wall-clock time. Accuracy without size and time is half a
    result: a tool that is 5 points behind and 30× faster is a different trade than one that is 5
    points behind and 2× slower, and a 300-line library and a 100k-line application are not the
    same measurement. `torture` is included as the small end of the scale."""
    subs = []
    for sub in ORDER[lang]:
        p = ROOT / lang / "results" / sub / "scores.json"
        if p.exists():
            subs.append((sub, json.loads(p.read_text(encoding="utf-8"))))
    subs.sort(key=lambda x: x[1]["subject"].get("source_lines") or x[1]["subject"]["sites_total"])
    tools: list[str] = []
    for _, d in subs:
        for t, byt in library_free(d["scores"]).items():
            if byt["B"]["scorable"] and not byt["B"].get("null_model") and t not in tools:
                tools.append(t)
    hdr = "| subject | files | lines | call sites | unique groups | " + " | ".join(f"`{display(t)}`" for t in tools) + " |"
    sep = "|---|---:|---:|---:|---:|" + "---:|" * len(tools)
    lines = [hdr, sep]
    for sub, d in subs:
        S = d["subject"]
        cells = []
        for t in tools:
            b = library_free(d["scores"]).get(t, {}).get("B")
            cells.append(secs(b.get("seconds")) if b and b["scorable"] else "—")
        lines.append(f"| {sub} | {S.get('source_files') or '—'} | {S.get('source_lines') or '—'} | "
                     f"{S['sites_total']:,} | {S['link_groups_unique']:,} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def chains_matrix(lang: str) -> str:
    """Reachability at depth 3, one cell per (tool, subject): `R@3 · blowup@3`. The edge matrix
    above cannot see that a fanning graph returns 4x the real answer to a change-impact query; this
    one can (issue #5). Recall, not precision: P@k × blowup@k ≡ recall@k identically, so the old
    `P@3 · blowup` pair was one number printed twice and hid a blowup below 1× — a tool that
    finds a third of the reachable set — behind the best-looking P@3 in the table (#50). Null and
    ideal rows included in italics as the two ends of the bracket."""
    subjects = [s for s in COMPARE[lang] if (ROOT / lang / "results" / s / "scores.json").exists()]
    data: dict[str, dict[str, tuple[float | None, float | None]]] = {}
    null_flags: dict[str, bool] = {}
    exact: dict[str, list[float]] = {}
    for sub in subjects:
        d = json.loads((ROOT / lang / "results" / sub / "scores.json").read_text(encoding="utf-8"))
        for t, byt in library_free(d["scores"]).items():
            b = byt["B"]
            if not b["scorable"] or not b.get("chains"):
                continue
            k3 = b["chains"]["by_depth"].get("3") or {}
            data.setdefault(t, {})[sub] = (k3.get("recall"), k3.get("blowup"))
            null_flags[t] = bool(b.get("null_model"))
            g = b["unique_link_groups"]
            exact.setdefault(t, []).append(g["counts"].get("exact", 0) / max(g["total"], 1))
    # the same row order as the exact matrix, so a reader can relate the two
    tools = sorted((t for t in data if not null_flags[t]),
                   key=lambda t: -sum(exact[t]) / len(exact[t]))
    tools += sorted(t for t in data if null_flags[t])
    hdr = "| tool | " + " | ".join(subjects) + " |"
    sep = "|---|" + "---:|" * len(subjects)
    lines = [hdr, sep]
    for t in tools:
        cells = []
        for sub in subjects:
            v = data[t].get(sub)
            if v is None or v[0] is None:
                # a tool that emitted nothing has recall 0 and blowup 0 — printed as such,
                # never as a dash (#50)
                cells.append("0.00 · 0.0×" if v is not None else "—")
            else:
                cells.append(f"{v[0]:.2f} · {v[1]:.1f}×")
        name = label(t, null=null_flags[t])
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def library_table(lang: str) -> str:
    """Each library-enabled row beside its library-free counterpart, per compared subject, as
    `exact / one-target groups` — what the libraries bought. Not ranked, and not in any other table."""
    subjects = [s for s in COMPARE[lang] if (ROOT / lang / "results" / s / "scores.json").exists()]
    pairs: dict[str, str] = {}
    cells: dict[str, dict[str, tuple[int, int, str]]] = {}
    for sub in subjects:
        d = json.loads((ROOT / lang / "results" / sub / "scores.json").read_text(encoding="utf-8"))
        for t, byt in d["scores"].items():
            b = byt["B"]
            if not b["scorable"] or not uses_libraries(b):
                continue
            free = next((c for c in (f"{t}-nolib", t.removesuffix("-lib")) if c != t and c in d["scores"]
                         and not uses_libraries(d["scores"][c]["B"])), None)
            pairs[t] = free or ""
            for row in (t, free):
                if row is None:
                    continue
                g = d["scores"][row]["B"]["unique_link_groups"]
                cells.setdefault(row, {})[sub] = (g["counts"].get("exact", 0), g["total"],
                                                  d["scores"][row]["B"].get("build") or "?")
    if not pairs:
        return ""
    lines = ["| row | budget | " + " | ".join(subjects) + " | all |", "|---|:--|" + "---:|" * (len(subjects) + 1)]
    def line(row: str, lib: bool) -> str:
        vals = cells.get(row, {})
        found = sum(v[0] for v in vals.values()); of = sum(v[1] for v in vals.values())
        budget = next(iter(vals.values()))[2] if vals else "?"
        cs = [f"{vals[s][0]:,} <sub>{100 * vals[s][0] / vals[s][1]:.1f}%</sub>" if s in vals and vals[s][1] else "—"
              for s in subjects]
        allc = f"{found:,} <sub>{100 * found / of:.1f}%</sub>" if of else "—"
        return f"| `{display(row, lib)}` | {budget} | " + " | ".join(cs) + f" | {allc} |"
    for t, free in sorted(pairs.items()):
        lines.append(line(t, True))
        if free:
            lines.append(line(free, False))
    return "\n".join(lines)


def _pct(e: int, n: int) -> str:
    return f"{100 * e / n:.1f}%" if n else "—"


def standings(lang: str) -> str:
    """The claims the README makes about where each tool lands, computed rather than written (#94):
    the leader on each compared subject and its distance from the ceiling; AxiomEngine's exact% and
    RANK among every ranked row on each subject, naming any envelope-class (†) row ranked above it
    so no exclusion is silent; its pooled found% and what its non-found groups are; and where it is
    ahead of or behind `codeql`."""
    subjects = [s for s in COMPARE[lang] if (ROOT / lang / "results" / s / "scores.json").exists()]
    if not subjects:
        return ""
    lead, ranks, vs = [], [], {"ahead": [], "behind": [], "level": []}
    found = total = 0
    counts: dict[str, int] = {}
    ax_name = None
    for sub in subjects:
        d = json.loads((ROOT / lang / "results" / sub / "scores.json").read_text(encoding="utf-8"))
        sc = library_free(d["scores"])
        null_b = ideal_b = None
        for t, byt in sc.items():
            b = byt["B"]
            if b["scorable"] and b.get("null_model"):
                if b.get("build") == "oracle":
                    ideal_b = b
                else:
                    null_b = b
        rows = []
        for t, byt in sc.items():
            b = byt["B"]
            if not b["scorable"] or b.get("null_model"):
                continue
            g = b["unique_link_groups"]
            rows.append((g["counts"].get("exact", 0) / g["total"] if g["total"] else 0.0, t, b,
                         envelope_class(b, null_b, ideal_b)))
        rows.sort(key=lambda r: (-r[0], r[1]))
        if not rows:
            continue
        top = rows[0]
        lead.append(f"{sub} `{display(top[1])}` {100 * top[0]:.1f}% ({100 - 100 * top[0]:.1f} below the ceiling)")
        ax = next((r for r in rows if r[1] in ("axiom-nolib", "axiom")), None)
        if ax is None:
            continue
        ax_name = display(ax[1])
        i = rows.index(ax)
        above_env = [f"`{display(r[1])}`" for r in rows[:i] if r[3]]
        rank = f"{sub} {100 * ax[0]:.1f}% — #{i + 1} of {len(rows)}"
        if above_env:
            rank += f" (above it and envelope-class there: {', '.join(above_env)})"
        ranks.append(rank)
        g = ax[2]["unique_link_groups"]
        found += g["counts"].get("exact", 0); total += g["total"]
        for k, v in g["counts"].items():
            if k != "exact":
                counts[k] = counts.get(k, 0) + v
        cq = next((r for r in rows if r[1] == "codeql"), None)
        if cq is not None:
            d_pts = 100 * (ax[0] - cq[0])
            key = "ahead" if d_pts > 0.05 else "behind" if d_pts < -0.05 else "level"
            vs[key].append(f"{sub} ({100 * ax[0]:.1f} vs {100 * cq[0]:.1f})")
    out = [f"- **Leader on each subject:** " + "; ".join(lead) + "."]
    if ax_name:
        out.append(f"- **`{ax_name}` by subject** (exact%, rank among every ranked row): " + "; ".join(ranks) + ".")
        names = dict(VERDICTS)
        miss = ", ".join(f"{counts[k]:,} {names.get(k, k)}" for k, _ in VERDICTS if counts.get(k))
        out.append(f"- **Pooled:** {found:,} of {total:,} one-target groups ({_pct(found, total)}); "
                   f"the {total - found:,} not found are {miss}.")
        parts = []
        for key, word in (("ahead", "ahead of"), ("behind", "behind"), ("level", "level with")):
            if vs[key]:
                parts.append(f"{word} `codeql` on {', '.join(vs[key])}")
        if parts:
            out.append(f"- **Against `codeql`:** " + "; ".join(parts) + ".")
    return "\n".join(out)


def render_standings() -> str:
    out = [SBEGIN, ""]
    for lang, name in (("java", "Java"), ("typescript", "TypeScript")):
        t = standings(lang)
        if t:
            out += [f"**{name}** (the five compared subjects, library-free rows):", "", t, ""]
    out.append(SEND)
    return "\n".join(out)


def render() -> str:
    out = [BEGIN, ""]
    out.append("**Calls with exactly one target, and how many of them each tool linked to it** (Tier B). The")
    out.append("unit is a `(caller, callee-name)` group with one possible target: the first row is what the")
    out.append("ground truth found — how many such groups per subject — and every tool cell is a count of those")
    out.append("the tool got right, with the percentage under it; the last column sums the five. A method that")
    out.append("calls two different one-target methods of the same name (`new A()` and `new B()`) forms one")
    out.append("pooled group that is not counted here; those are counted beside the ambiguous table in each")
    out.append("report (#70). Five real projects per language. The")
    out.append("counts behind every percentage — found / fan / polluted / wrong / missed against the ground")
    out.append("truth's own number of calls — are in the verdict tables below; every other column (precision,")
    out.append(f"strict precision, three recalls, time, `needs`) is in [`{FULL}`]({FULL}), generated from the")
    out.append("same JSON. The first row is the ground truth's own count of such calls. The CHA envelope")
    out.append("answer (`cha-null`) scores 100 on exact% by construction and is printed as the floor row; the")
    out.append("bounds table below is where an enumerator and a resolver come apart.")
    out.append("")
    out.append(f"† *italic* = envelope-class on that subject: the row reproduces ≥ {ENVELOPE_FAN_SHARE:.0%} of the CHA")
    out.append(f"envelope's fan share with a strict precision below {ENVELOPE_STRICT_RATIO}× the null model's — its")
    out.append("output composition is the envelope's: it fans where the envelope fans, so exact% there cannot")
    out.append("tell resolution from enumeration (#12, #49). A statement about the row's shape, not a score. Not")
    out.append(f"applied where the null model's strict precision is ≥ {DISPATCH_LIGHT}: the subject barely dispatches")
    out.append("and the envelope is genuinely the right answer (fp-ts is the clearest case). Not counted as a lead:")
    out.append("rows are ranked with their † cells left out, and a summed column that includes one carries the")
    out.append("mark. ↓ = strict precision below the null model's on that subject without being envelope-class")
    out.append("— the row fabricates rather than fans; on a dispatch-light subject the null model's strict")
    out.append("precision is close to 1.0 and the mark says little.")
    out.append("")
    for lang, label in (("java", "Java"), ("typescript", "TypeScript")):
        out.append(f"#### {label}\n")
        out.append(summary(lang))
        out.append("")
        note = full_set_note(lang)
        if note:
            out.append(note)
            out.append("")
    libs = [(lang, name, library_table(lang)) for lang, name in (("java", "Java"), ("typescript", "TypeScript"))]
    if any(t for _, _, t in libs):
        out.append("**With external libraries — not ranked.** Every table in this README compares runs that")
        out.append("were given the subject's source and nothing else. Some tools can also be given the external")
        out.append("libraries the subject calls into — AxiomEngine the JDK's platform IR, CodeQL a compiled build on")
        out.append("a local subject — and can then type a receiver that comes out of a library call")
        out.append("(`list.get(0).foo()`), which a source-only tool cannot. Those runs are shown here, each beside")
        out.append("the same tool's library-free run, so what the libraries bought is visible; they are left out")
        out.append("of every ranking, because no other tool under test was offered the same input.")
        out.append("")
        for lang, name, t in libs:
            if t:
                out.append(f"#### {name}\n")
                out.append(t)
                out.append("")
    out.append("**Seven questions a consumer asks a call graph**, each scored against the ground truth on")
    out.append("its own terms (`bench/tasks.py`; same Tier-B edges and truth as everything above; samples")
    out.append("seeded, pooled over the five subjects). *Callees / callers of a method*: per-method F1 of the")
    out.append("tool's set against the declared set. *Path A→B*: of 500 sampled pairs joined by a declared")
    out.append("call path of ≤3 hops, the share the tool's graph joins within 6. *Blast radius*: Jaccard of")
    out.append("the transitive callers within 3 hops for 300 sampled methods. *\"Nothing calls X\"*: precision")
    out.append("and recall of the tool's uncalled-method claims against the declared graph's. *Dispatch set*:")
    out.append("Jaccard of the tool's targets against the runnable set at genuinely ambiguous sites (the")
    out.append("envelope answer scores 1.0 here by construction). *File→file dependencies*: F1 of the")
    out.append("cross-file call relation.")
    out.append("")
    for lang, label in (("java", "Java"), ("typescript", "TypeScript")):
        out.append(f"#### {label}\n")
        out.append(tasks_table(lang))
        out.append("")
    out.append("**Against the three bounds.** What the oracle knows comes in three sizes, and a tool can be")
    out.append("read against each: **CERTAIN** — the declared target, what the call instruction names;")
    out.append("**RTA** — every target that can run on a receiver the program actually instantiates;")
    out.append("**CHA** — every target that can run under class-hierarchy dispatch, the envelope. Every cell is a")
    out.append("count and the share of the ground-truth row (or of the tool's own emitted rows, for the last")
    out.append("two columns), summed over the five subjects; rxjava's 380,000-edge envelope dominates the RTA")
    out.append("and CHA columns for Java, and the per-subject values are in docs/RESULTS.md. A resolver is high on CERTAIN")
    out.append("recall and on `strict`; an enumerator is 1.000 on CHA recall and low on `strict` (the")
    out.append("`cha-null` row is exactly that); a tool that models dispatch sits between RTA and CHA.")
    out.append("")
    for lang, label in (("java", "Java"), ("typescript", "TypeScript")):
        out.append(f"#### {label}\n")
        out.append(bounds_table(lang))
        out.append("")
    out.append("**F1, fan and noise.** Edge-level, pooled over the five subjects from the counts. Of each")
    out.append("tool's rows, **strict** are the declared target, **fan** could run but are not what the call")
    out.append("names (other overrides — the envelope's own row is mostly fan), and **noise** lie outside the")
    out.append("class-hierarchy envelope and can never run. F1 uses precision = strict + fan; F1-strict charges")
    out.append("the fan too. Recall is over the declared edges.")
    out.append("")
    for lang, label in (("java", "Java"), ("typescript", "TypeScript")):
        out.append(f"#### {label}\n")
        out.append(accuracy_table(lang))
        out.append("")
    out.append("**What the ground truth saw.** Per subject, before any tool is scored: what the JDK's")
    out.append("bytecode readers (Java) or the pinned type checker (TypeScript) found. `internal` calls have")
    out.append("a declared target in the application; `boundary` calls leave it (a JDK or dependency method")
    out.append("— not scored); TypeScript `indirect` calls go through a function value (not scored) and")
    out.append("`unresolved` are call expressions the checker could not resolve at all (no row; every")
    out.append("denominator is short by that many, #53). `certain` edges are the declared targets; the")
    out.append("`envelope` is every method that can run under class-hierarchy dispatch; `one target` is the")
    out.append("headline denominator, `several targets` the genuinely ambiguous rest.")
    out.append("")
    for lang, label in (("java", "Java"), ("typescript", "TypeScript")):
        out.append(f"#### {label}\n")
        out.append(oracle_table(lang))
        out.append("")
    out.append("**Verdicts — every call accounted for.** The first row is the ground truth: how many")
    out.append("uniquely linked calls the bytecode (Java) or the type checker (TypeScript) says the five")
    out.append("subjects contain. Each tool row partitions exactly those calls: **found** = linked to the one")
    out.append("method that runs (or its declaration); **fan** = the right method plus others; **polluted** =")
    out.append("the right method plus one outside the envelope; **vague** = only a supertype that declares the")
    out.append("member; **wrong** = only impossible targets; **unknown** = no answer, but the tool wrote a row")
    out.append("saying it could not resolve a call at that line (AxiomEngine's `ambiguous_unknown`); **unplaced** = the")
    out.append("tool answered but every row for the group was excluded by the resolver (ambiguous or")
    out.append("owner-less spelling, target outside the universe); **missed** = nothing at all, a silent gap")
    out.append("(#69). Rows sum to the ground-truth row. The second table is the same partition per subject")
    out.append("(`found · fan · polluted · vague · wrong · unknown · unplaced · missed`).")
    out.append("")
    for lang, label in (("java", "Java"), ("typescript", "TypeScript")):
        out.append(f"#### {label}\n")
        out.append(verdicts(lang))
        out.append("")
    out.append("**Call chains at depth 3** — `R@3 · blowup@3`: of the method pairs the declared graph")
    out.append("reaches within three calls, the share the tool's graph also reaches; and the size of the")
    out.append("tool's answer over the true one — what a change-impact query gets back. `k=1` is the")
    out.append("edge metric; over three hops a fanning graph stops being free (issue #5). A blowup")
    out.append("**below 1×** is unsound in the other direction — the tool hands back less than the true")
    out.append("set (#50; P@3 was one number printed twice, since P × blowup ≡ recall). Italic rows are")
    out.append("the bracket: the null model below, the ideal answer above.")
    out.append("")
    for lang, label in (("java", "Java"), ("typescript", "TypeScript")):
        out.append(f"#### {label}\n")
        out.append(chains_matrix(lang))
        out.append("")
    out.append("**Size and time.** Wall-clock seconds per tool row, subjects smallest first. Where one adapter")
    out.append("produces two rows (Java `AxiomEngine` with and without libraries: one parse, two solves; `codeql` / `codeql-dispatch`:")
    out.append("one database, two queries) each row is the shared phase plus its own — not the adapter's")
    out.append("whole wall-clock twice (#8); copying the subject into a tool's work directory is harness")
    out.append("time and is charged to nobody. `run.tools.<tool>.seconds_breakdown` in each `scores.json`")
    out.append("has the parts. `codeql` time includes the database build; `AxiomEngine` includes parse and solve;")
    out.append("the index tools include their indexing pass. `gitnexus` excludes its adapter's export: the tool's query CLI")
    out.append("truncates a result at 64 KiB, so the adapter pages it one process per 200 rows, and that loop is")
    out.append("published as `seconds_breakdown.export` rather than charged to the tool (#98). Measured on a")
    out.append(f"dedicated VM ({RUN_HOST}), one subject and one tool at a time with nothing else running;")
    out.append("still a single run per tool, so read small differences as noise. WARM runs only: a tool's one-time cost (AxiomEngine's")
    out.append("Soufflé compile, CodeQL's query compile) is paid in a warm-up pass before the timed run and")
    out.append("recorded per subject as `run.tools.<tool>.cold_seconds` with whether its cache was hit (#42);")
    out.append("before that, the first subject of a session carried the compile — AxiomEngine read 82 s on a")
    out.append("195-line file and 4 s on kysely. The Java `AxiomEngine + libraries` row also stages the platform IR once per")
    out.append("library key; until #88 the timed run's key differed from the warm-up's (a per-subject symlink")
    out.append("farm), so every Java solve re-staged it into `seconds` — the roots are stable paths now, and")
    out.append("`run.tools.<label>.seconds_breakdown.library_cache` says whether each timed solve hit it.")
    out.append("")
    for lang, label in (("java", "Java"), ("typescript", "TypeScript")):
        out.append(f"#### {label}\n")
        out.append(size_time(lang))
        out.append("")
    out.append(END)
    return "\n".join(out)


def render_full() -> str:
    out = ["# Full results — every subject, every column", "",
           "Generated by `bench/readme_tables.py --write` from `*/results/*/scores.json`. Do not edit.", ""]
    for lang, label in (("java", "Java"), ("typescript", "TypeScript")):
        out.append(f"## {label}\n")
        for s in ORDER[lang] + (["type-graphql"] if lang == "typescript" else []):
            # torture, the five compared subjects, then the extra subjects (type-graphql, ts-morph)
            t = table(lang, s)
            if t:
                out.append(t)
        reg = json.loads((ROOT / lang / "subjects" / "registry.json").read_text(encoding="utf-8"))
        blocked = [x for x in reg["subjects"] if x.get("split") == "blocked"]
        if blocked:
            out.append("**Blocked** — registered, refused by a gate, kept with the reason:\n")
            for x in blocked:
                out.append(f"- `{x['name']}` — {x['description'].split('. ', 1)[0]}.")
            out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    text = render()
    if not a.write:
        print(text)
        return 0
    readme = ROOT / "README.md"
    s = readme.read_text(encoding="utf-8")
    if BEGIN in s and END in s:
        s = s[: s.index(BEGIN)] + text + s[s.index(END) + len(END):]
    else:
        raise SystemExit("README.md has no results markers")
    if SBEGIN in s and SEND in s:
        s = s[: s.index(SBEGIN)] + render_standings() + s[s.index(SEND) + len(SEND):]
    readme.write_text(s, encoding="utf-8")
    (ROOT / FULL).write_text(render_full() + "\n", encoding="utf-8")
    print(f"README summary spliced; full tables -> {FULL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
