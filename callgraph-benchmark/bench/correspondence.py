#!/usr/bin/env python3
"""Gate 4 — do the source the tools read and the bytecode the oracle reads describe the same program?

A Maven subject is two artefacts: `<a>.jar` for ground truth and `<a>-sources.jar` for the tools.
They are supposed to be one release. If they are not, the benchmark breaks in two directions, and
the second is severe enough that it has to be a gate rather than a note:

  SOURCE WITHOUT BYTECODE — the tools see code the oracle has no truth for. Every edge they find in
  it becomes an unmapped row or a false positive. Bad, and visible in the excluded counts.

  BYTECODE WITHOUT SOURCE — the oracle has ground truth for code no tool could read. Every one of
  those edges is a `missed` against every tool at once. This silently DEFLATES the whole field, and
  it looks exactly like a real result: a uniformly lower recall with no obvious cause. Nothing else
  in the harness can detect it.

So both directions are computed, and the scored universe is restricted to the INTERSECTION —
`--emit-types` writes it, and the oracle's `--only-types` consumes it. A tool is then never charged
for a type nobody gave it, and never credited for one the oracle cannot check.

    python3 bench/correspondence.py --sources <dir> --classes-list <file> [--emit-types <file>]
                                    [--max-missing-pct 2.0]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from language import JAVA, LanguageProfile, is_type_segment   # noqa: E402

IGNORED = {"package-info.java", "module-info.java"}


# `$` is a letter to the JLS (§3.8), and a type whose own name carries one is declared like any
# other: gson's `$Gson$Types`. `\w` cannot spell it, so the type was never found on the source
# side and left the scored universe for every tool at once (#97). `\w` also admits a leading
# digit, which no identifier has.
IDENT = r"[A-Za-z_$][\w$]*"
DECL_RE = re.compile(rf"\b(?:class|interface|enum|record)\s+({IDENT})|@interface\s+({IDENT})")


def toplevel_types(text: str) -> list[str]:
    """Every type declared at BRACE DEPTH ZERO — which is what "top-level" actually means.

    A column-0 pattern was the first attempt, and it failed on `/*package-private*/ class FailFast`
    (the comment pushes the keyword off column 0) and would equally fail on any leading annotation.
    Indentation is not the definition; nesting depth is. Comments and string literals are blanked
    first so a brace inside one does not shift the count.
    """
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", "", text)
    text = re.sub(r'"(?:\\.|[^"\\\n])*"', '""', text)
    text = re.sub(r"'(?:\\.|[^'\\\n])*'", "''", text)
    out: list[str] = []
    depth = 0
    pos = 0
    for m in re.finditer(rf"[{{}}]|\b(?:class|interface|enum|record)\s+{IDENT}|@interface\s+{IDENT}", text):
        tok = m.group(0)
        if tok == "{":
            depth += 1
        elif tok == "}":
            depth = max(0, depth - 1)
        elif depth == 0:
            d = DECL_RE.match(tok)
            if d:
                out.append(d.group(1) or d.group(2))
    return out


def source_types(src: Path, lang: LanguageProfile = JAVA) -> set[str]:
    """Every TOP-LEVEL type each source file declares.

    Derived from the file's CONTENT, not from its name. Java requires only the PUBLIC top-level type
    to match the file name, and a non-public one declared beside it is invisible to a name-based
    rule — `MailPrintStream` lives in `MailMessage.java`, `ConstantPool` in `ClassNameReader.java`.
    Missing them is not merely lost coverage: the type is then absent from `--only-types`, so the
    oracle drops it from the scoring universe while STILL EMITTING SITES whose targets name it. Those
    groups become unwinnable for every tool at once, and the ceiling gate is what surfaced them.
    """
    out: set[str] = set()
    for pattern in lang.source_globs:
        for p in sorted(src.rglob(pattern)):
            if p.name in IGNORED:
                continue
            if lang.namespace_re is not None:
                text = p.read_text(encoding="utf-8", errors="replace")
                m = lang.namespace_re.search(text)
                ns = m.group(1) if m else ""
                for name in toplevel_types(text):
                    out.add(f"{ns}.{name}" if ns else name)
                continue
            else:
                ns = p.relative_to(src).as_posix().rsplit(".", 1)[0]
                out.add(ns)
                continue
            out.add(f"{ns}.{p.stem}" if ns else p.stem)
    return out


def top_level(canonical: str) -> str:
    """`pkg.Outer.Inner` / `pkg.Outer$anon:Sup@12` -> `pkg.Outer`."""
    c = canonical.split("$anon:")[0]
    parts = c.split(".")
    for i, seg in enumerate(parts):
        if is_type_segment(seg):
            return ".".join(parts[: i + 1])
    return c


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", required=True, type=Path)
    ap.add_argument("--classes-list", required=True, type=Path,
                    help="output of ClassfileGroundTruth --mode classes")
    ap.add_argument("--emit-types", type=Path,
                    help="write the intersection, for the oracle's --only-types")
    ap.add_argument("--language", default="java")
    ap.add_argument("--max-missing-pct", type=float, default=2.0,
                    help="fail if more than this %% of bytecode types have no source")
    a = ap.parse_args()

    from language import get as _get
    src = source_types(a.sources, _get(a.language))
    classes = [c.strip() for c in a.classes_list.read_text(encoding="utf-8").splitlines() if c.strip()]
    # `package-info.class` / `module-info.class` declare no methods and no call sites; the source
    # side already ignores their .java files, and counting them as "bytecode without source" refused
    # commons-lang3 (7.2%), jackson-databind (4.2%) and guava (2.6%) with ZERO real missing types
    # (issue #29 §2)
    classes = [c for c in classes if not c.rsplit(".", 1)[-1] in ("package-info", "module-info")]
    byte_top = {top_level(c) for c in classes}

    both = src & byte_top
    only_src = src - byte_top
    only_byte = byte_top - src

    print(f"  source top-level types:   {len(src)}")
    print(f"  bytecode top-level types: {len(byte_top)}")
    print(f"  in both:                  {len(both)}")
    print(f"  source without bytecode:  {len(only_src)}")
    print(f"  bytecode without source:  {len(only_byte)}")
    for t in sorted(only_byte)[:8]:
        print(f"      (no source) {t}")
    for t in sorted(only_src)[:8]:
        print(f"      (no bytecode) {t}")

    if a.emit_types:
        a.emit_types.write_text("\n".join(sorted(both)) + "\n", encoding="utf-8")
        print(f"  scored universe restricted to {len(both)} types -> {a.emit_types}")

    if not byte_top:
        print("  FAIL: no bytecode types at all")
        return 1
    pct = 100.0 * len(only_byte) / len(byte_top)
    if pct > a.max_missing_pct:
        print(f"  FAIL: {pct:.1f}% of bytecode types have no source (limit {a.max_missing_pct}%). "
              f"Every edge in them would score as missed against every tool at once.")
        return 1
    print(f"  OK: {pct:.1f}% of bytecode types lack source (limit {a.max_missing_pct}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
