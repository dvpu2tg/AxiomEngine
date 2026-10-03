#!/usr/bin/env python3
"""Score every tool that produced an answer for one subject, and write the report.

    python3 bench/run.py --subject torture \
        --sites   .work/gt.sites.jsonl \
        --classes .work/gt.classes.txt \
        --methods .work/gt.methods.txt \
        --edges-dir .work/edges \
        --source subjects/torture/client --source subjects/torture/lib \
        --out results/torture

`--edges-dir` holds one directory per tool, each containing `<subject>.jsonl` in the canonical
schema. A tool that produced no file for this subject is simply absent from the report — never
reported as scoring zero, which would be a claim the run did not make.

Every input is hashed into the run manifest. A results directory whose manifest does not match a
re-run is a results directory that cannot be trusted, and the point of the manifest is to make that
checkable rather than assumed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(__file__).resolve().parent.parent

import groundtruth as G   # noqa: E402
import language as L      # noqa: E402
import report as RPT      # noqa: E402
import resolve as R       # noqa: E402
import chains as CH       # noqa: E402
import score as S         # noqa: E402
from model import Ref, Tier, read_edges   # noqa: E402


def _npm_version(pkg: str) -> str:
    """The version of a package in the benchmark's pinned `.tools/ts` tree."""
    pj = ROOT / ".tools" / "ts" / "node_modules" / pkg / "package.json"
    try:
        return str(json.loads(pj.read_text(encoding="utf-8")).get("version", "?"))
    except (OSError, ValueError):
        return "?"


def sha256(p: Path) -> str:
    """SHA-256 of the file with line endings normalised to LF. The manifest is a claim of
    byte-identity over CONTENT; a `\r\n` a JVM or a Python text stream chose on Windows is not
    content, and it made every hash differ on a platform where every line was the same (#45).
    docs/PROTOCOL.md §8 says what is hashed: the LF-normalised bytes."""
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk.replace(b"\r\n", b"\n"))
    return h.hexdigest()


def tool_version(cmd: list[str]) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (r.stdout or r.stderr).strip().splitlines()[0] if (r.stdout or r.stderr) else "?"
    except Exception:
        return "unavailable"


# `torture/F01Polymorphism.java` and every type nested in it belong to family F01. The families are a
# property of the SUBJECT, not of the harness, so the pattern is configurable and absent by default.
FAMILY_RE = re.compile(r"\b(F\d{2})")


def family_of(caller: Ref) -> str:
    t = caller.type or ""
    m = FAMILY_RE.search(t)
    return m.group(1) if m else "other"


def _adapter_of(tool: str, timings: dict) -> str | None:
    best = None
    for adapter in timings:
        if tool == adapter or tool.startswith(adapter + "-"):
            if best is None or len(adapter) > len(best):
                best = adapter
    return best


# Phases of an adapter's wall-clock that are NOT the tool's work, recorded by the adapter in
# timings-parts.tsv and published in seconds_breakdown: `staging` is the harness copying the subject
# (#8); `export` is the adapter reading the tool's answer out — gitnexus's CLI truncates a query
# result at 64 KiB, so its adapter pages it 200 rows per process, 238 launches on rxjava, and that
# loop was 85% of the tool's published `seconds` there (#98).
NOT_THE_TOOL = ("staging", "export")


def tool_seconds(tool: str, timings: dict, parts: dict) -> float | None:
    """The tool's own seconds: two labels from one adapter (`axiom` / `axiom-nolib`, `codeql` /
    `codeql-dispatch`) each cost the SHARED phase plus their OWN phase, not the adapter's whole
    wall-clock; the NOT_THE_TOOL phases are charged to nobody."""
    ad = _adapter_of(tool, timings)
    if ad is None:
        return None
    total = timings[ad]
    ph = parts.get(ad, {})
    own = {k[4:]: v for k, v in ph.items() if k.startswith("own:")}
    if own:
        if tool in own:
            return round(ph.get("shared", 0.0) + own[tool], 2)
        # a label with no own phase (a failed second solve): the adapter's total minus the
        # other labels' own phases
        return round(total - sum(own.values()) - sum(ph.get(k, 0.0) for k in NOT_THE_TOOL), 2)
    return round(total - sum(ph.get(k, 0.0) for k in NOT_THE_TOOL), 2)


def tool_breakdown(tool: str, timings: dict, parts: dict) -> dict | None:
    ad = _adapter_of(tool, timings)
    if ad is None or not parts.get(ad):
        return None
    ph = parts[ad]
    out = {"adapter_total": timings[ad], "shared": ph.get("shared"), "staging": ph.get("staging"),
           "own": ph.get("own:" + tool)}
    if ph.get("export") is not None:
        out["export"] = ph["export"]
    # whether the TIMED solve found the engine's staged library (0) or staged it (1) — the
    # warm-up's `cache` is about the warm-up, this is what `seconds` includes (#88)
    lc = ph.get("libcache:" + tool)
    if lc is not None:
        out["library_cache"] = "miss" if lc else "hit"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--language", default="java",
                    help="which LanguageProfile governs naming conventions (bench/language.py)")
    ap.add_argument("--sites", required=True, type=Path)
    ap.add_argument("--classes", required=True, type=Path)
    ap.add_argument("--methods", required=True, type=Path)
    ap.add_argument("--defaults", type=Path,
                    help="TypeScript: module -> default-exported container (oracle --mode defaults)")
    ap.add_argument("--coverage", type=Path,
                    help="TypeScript: the oracle's --mode coverage output (call_expressions / resolved), "
                         "so the calls the checker could not resolve are PUBLISHED, not dropped (#53)")
    ap.add_argument("--heritage", type=Path,
                    help="the oracle's --mode heritage: container kind and parents (issue #36)")
    ap.add_argument("--excluded", type=Path,
                    help="edges/callers a documented exclusion removed; applied to EVERY tool")
    ap.add_argument("--edges-dir", required=True, type=Path)
    ap.add_argument("--source", action="append", default=[], type=Path,
                    help="subject source root; used only to map a file to its package")
    ap.add_argument("--staged-copy", type=Path,
                    help="files<TAB>N / sha256<TAB>H of the tools' staged copy of the subject, into run (#83)")
    ap.add_argument("--timing-parts", type=Path,
                    help="adapter<TAB>label<TAB>phase<TAB>seconds: `shared` (paid by every label of the "
                         "adapter), `own:<label>`, `staging` (harness cost, billed to nobody) — issue #8")
    ap.add_argument("--prior-internal-use", action="store_true",
                    help="the subject is in the tool under test's own development corpus (registry flag); "
                         "printed in the report so the number is never read as clean (#72 §3)")
    ap.add_argument("--warmup", type=Path,
                    help="adapter<TAB>seconds<TAB>hit|miss from the warm-up pass (issue #42)")
    ap.add_argument("--timings", type=Path,
                    help="TSV of <adapter>\\t<seconds> written by the runner")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--module-prefix", default="",
                    help="TypeScript monorepo: the subject's directory as the tools spell it, "
                         "e.g. `excalidraw/`, stripped from every tool row's module path (#20)")
    ap.add_argument("--anonmap", type=Path,
                    help="`internal<TAB>canonical` from the oracle's --mode anonmap: the compiler's "
                         "own name for an anonymous / local / enum-body class (bench/resolve.py "
                         "add_compiler_names)")
    ap.add_argument("--families", action="store_true",
                    help="break the score down per construct family (subjects that are organised so)")
    a = ap.parse_args()

    lang = L.get(a.language)
    gt = G.load(a.sites, a.classes, a.methods, a.subject, a.excluded)
    summary = G.summarise(gt)
    summary["prior_internal_use"] = bool(a.prior_internal_use)
    if a.coverage and a.coverage.exists():
        cov = {}
        for ln in a.coverage.read_text(encoding="utf-8").splitlines():
            k, _, v = ln.partition("\t")
            cov[k.strip()] = v.strip()
        try:
            total, resolved = int(cov.get("call_expressions", 0)), int(cov.get("resolved", 0))
        except ValueError:
            total = resolved = 0
        if total:
            # every recall denominator on this subject is short by exactly this many calls, for
            # every tool alike — printed where the recall numbers are (#53 §1)
            summary["checker_call_expressions"] = total
            summary["checker_resolved"] = resolved
            summary["sites_unresolved"] = total - resolved
            summary["checker_resolved_pct"] = round(100.0 * resolved / total, 1)
            # and the share that resolves INTO the subject — gate 0's floor counts a library
            # target as covered, so a complete `lib` can clear it without adding one scorable
            # site (#67, comment); this figure says how much of the subject is actually scorable
            try:
                inside = int(cov.get("target_in_subject", 0))
                summary["checker_target_in_subject_pct"] = round(100.0 * inside / total, 1)
            except ValueError:
                pass
    # SIZE, so accuracy and time can be read against it: source files and lines under the scored
    # tree, by the language's own extensions. A 300-line library and a 100k-line application are
    # not the same measurement, and the README's size/time table is built from these.
    files = lines = 0
    for root in a.source:
        for g in lang.source_globs:
            for f in Path(root).rglob(g):
                if "node_modules" in f.parts or f.name.endswith(".d.ts"):
                    continue
                files += 1
                try:
                    lines += sum(1 for _ in f.open(encoding="utf-8", errors="replace"))
                except OSError:
                    pass
    summary["source_files"] = files
    summary["source_lines"] = lines

    resolver = R.Resolver(gt.classes, R.build_file_index(list(a.source), lang), lang, gt.methods)
    resolver.add_external(gt.external_ancestors)
    if a.heritage and a.heritage.exists():
        resolver.add_heritage(a.heritage.read_text(encoding="utf-8").splitlines())
    if a.anonmap and a.anonmap.exists():
        resolver.add_compiler_names(a.anonmap.read_text(encoding="utf-8").splitlines())
    resolver.module_prefix = a.module_prefix or None
    resolver._memo.clear()
    if a.defaults and a.defaults.exists():
        pairs = [tuple(ln.split("\t", 1)) for ln in a.defaults.read_text().splitlines() if "\t" in ln]
        resolver.add_default_exports(pairs)

    # adapter directory name -> wall-clock seconds. One adapter can emit SEVERAL tool labels
    # (`axiom` and `axiom-nolib` are two solves inside one invocation; `codeql` and
    # `codeql-dispatch` are two queries over one database), and splitting a single measured run
    # between them would be inventing a number. Both rows carry the adapter's total, and the report
    # says so.
    timings: dict[str, float] = {}
    if a.timings and a.timings.exists():
        for ln in a.timings.read_text(encoding="utf-8").splitlines():
            name, _, secs = ln.partition("\t")
            try:
                timings[name.strip().replace("_", "-")] = float(secs)
            except ValueError:
                pass

    warmup: dict[str, tuple[float, str]] = {}
    if a.warmup and a.warmup.exists():
        for ln in a.warmup.read_text(encoding="utf-8").splitlines():
            parts = ln.split("\t")
            if len(parts) >= 2:
                try:
                    warmup[parts[0].strip().replace("_", "-")] = (float(parts[1]), parts[2].strip() if len(parts) > 2 else "unknown")
                except ValueError:
                    pass

    def warmup_for(tool: str) -> tuple[float, str] | None:
        best = None
        for adapter, v in warmup.items():
            if tool == adapter or tool.startswith(adapter + "-"):
                if best is None or len(adapter) > best[0]:
                    best = (len(adapter), v)
        return best[1] if best else None

    # the parts, when an adapter recorded them: two labels from one adapter (`axiom` and
    # `axiom-nolib`, `codeql` and `codeql-dispatch`) each cost the SHARED phase plus their OWN
    # phase, not the adapter's whole wall-clock; a `staging` part is the harness copying the
    # subject and is charged to nobody (#8)
    parts: dict[str, dict[str, float]] = {}      # adapter -> phase -> seconds
    if a.timing_parts and a.timing_parts.exists():
        for ln in a.timing_parts.read_text(encoding="utf-8").splitlines():
            cols = ln.split("\t")
            if len(cols) >= 4:
                try:
                    ad = cols[0].strip().replace("_", "-")
                    parts.setdefault(ad, {})[cols[2].strip()] = round(parts.get(ad, {}).get(cols[2].strip(), 0.0) + float(cols[3]), 2)
                except ValueError:
                    pass

    def seconds_for(tool: str) -> float | None:
        return tool_seconds(tool, timings, parts)

    def breakdown_for(tool: str) -> dict | None:
        return tool_breakdown(tool, timings, parts)

    scores: dict[str, dict[Tier, S.ToolScore]] = {}
    inputs: dict[str, str] = {
        "sites": sha256(a.sites), "classes": sha256(a.classes), "methods": sha256(a.methods),
        **({"excluded": sha256(a.excluded)} if a.excluded and a.excluded.exists() else {}),
        **({"heritage": sha256(a.heritage)} if a.heritage and a.heritage.exists() else {}),
    }
    # the closures of both bounds, once per subject, at the headline tier (issue #5)
    chain_truth = CH.ChainTruth.build(gt, Tier.B)
    for tool_dir in sorted(p for p in a.edges_dir.iterdir() if p.is_dir()):
        f = tool_dir / f"{a.subject}.jsonl"
        if not f.exists():
            continue
        out = read_edges(f)
        # PROVENANCE FAILS CLOSED (issue #31): a row whose tool cannot be named with a version (or,
        # for axiom, a commit) is not a measurement anyone can reproduce, so it is not scored.
        ver = str(out.meta.get("version") or "").strip()
        commits = out.meta.get("parser_commit") and out.meta.get("engine_commit")
        if not out.meta.get("null_model") and not commits and (not ver or ver.split()[-1] in ("?", "")):
            raise SystemExit(f"{f}: no tool version recorded in _meta (got {ver!r}) — the adapter must record one")
        inputs[f"edges/{tool_dir.name}"] = sha256(f)
        by_tier = {
            tier: S.score(out, gt, resolver, tier,
                          family_of=family_of if a.families else None,
                          chain_truth=chain_truth)
            for tier in Tier.ordered()
        }
        for sc in by_tier.values():
            sc.seconds = seconds_for(out.tool)
        scores[out.tool] = by_tier

    if not scores:
        print(f"no tool output found under {a.edges_dir} for subject {a.subject}", file=sys.stderr)
        return 1

    staged: dict = {}
    if a.staged_copy and a.staged_copy.exists():
        for ln in a.staged_copy.read_text(encoding="utf-8").splitlines():
            k, _, v = ln.partition("\t")
            if k.strip() and v.strip():
                staged[k.strip()] = int(v) if v.strip().isdigit() else v.strip()
    run_meta = {
        "subject": a.subject,
        # the tools' staged copy of the subject: how many files, and a hash of the sorted list, so a
        # truncated input is visible in the manifest (#83)
        **({"staged_copy": staged} if staged else {}),
        "language": a.language,
        "platform": f"{platform.system()} {platform.machine()}",
        "python": platform.python_version(),
        # the oracle's own toolchain, per language: the bytecode readers' JDK for Java, the
        # PINNED checker for TypeScript — a different tsc can resolve an overload differently, and
        # the version was pinned and then never recorded (#54)
        **({"java": tool_version(["java", "-version"]), "javac": tool_version(["javac", "-version"])}
           if a.language == "java" else
           {"typescript": _npm_version("typescript"), "tsx": _npm_version("tsx")}),
        "input_sha256": inputs,
        "tools": {t: read_edges(a.edges_dir / t / f"{a.subject}.jsonl").meta
                  for t in sorted(scores)
                  if (a.edges_dir / t / f"{a.subject}.jsonl").exists()},
    }
    # the one-time cost each tool paid BEFORE its timed run, and whether its cache was hit —
    # `seconds` is the warm run only (issue #42)
    for t, meta in run_meta["tools"].items():
        w = warmup_for(t)
        if w is not None:
            meta["cold_seconds"], meta["cache"] = w
        bd = breakdown_for(t)
        if bd is not None:
            meta["seconds_breakdown"] = bd

    RPT.write(a.out, summary, scores, run_meta)
    print(f"wrote {a.out}/report.md and {a.out}/scores.json", file=sys.stderr)
    for tool in sorted(scores):
        sc = scores[tool][Tier.B]
        if sc.scorable and sc.vs_possible and sc.vs_certain:
            g = sc.unique_groups
            # A ratio is None when its denominator is zero — a tool that emitted nothing scorable.
            # Formatting None as a float crashes the run; printing it as `—` says what happened.
            def f(x: float | None) -> str:
                return "  —  " if x is None else f"{x:.3f}"
            print(f"  {tool:22s} P={f(sc.vs_possible.precision)} "
                  f"Rc={f(sc.vs_certain.recall)} Rp={f(sc.vs_possible.recall)} "
                  f"unique-exact={g.verdicts['exact']}/{g.total}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
