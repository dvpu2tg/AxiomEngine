#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────────────────────
# VERIFY THE SCORES — the checks that have to pass before a number in results/ means anything.
#
# `run/torture.sh` gates the GROUND TRUTH before scoring. This gates the RESULT afterwards, and
# asks three different questions:
#
#   1. DETERMINISM. Every tool in the deterministic tier is run a second time from a clean state
#      and its canonical edge file must be byte-identical. A tool whose output moves between runs
#      does not have a score, it has a sample — and the claim "deterministic tier" is the one thing
#      this benchmark cannot verify by inspection.
#
#   2. REPRODUCIBILITY OF THE SCORE. The scorer is re-run over the same inputs and
#      results/<subject>/scores.json must be byte-identical. This catches non-determinism in the
#      HARNESS — a set iteration order leaking into a report, a dict that happens to hash
#      differently — which would otherwise look exactly like a tool changing.
#
#   3. THE MANIFEST. Every input SHA-256 recorded in scores.json is re-hashed and must match, so a
#      results directory cannot silently describe inputs that are no longer on disk.
#
#   typescript/run/verify.sh [subject] [--heldout]
# ─────────────────────────────────────────────────────────────────────────────────────────────
set -uo pipefail
# `comm`/`sort` need one collation and the oracle's lists are in code-point order; under
# en_US.UTF-8 typedoc's upper-case file names sorted differently and gate 4 reported 46 files
# "absent from the source tree" that were there (issue #29 §1)
export LC_ALL=C

LANG_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$LANG_DIR/.." && pwd)"
LANGUAGE="$(basename "$LANG_DIR")"
cd "$ROOT"
SUBJECT="${1:-torture}"
shift || true
ALLOW=""; for arg in "$@"; do [ "$arg" = "--heldout" ] && ALLOW="--allow-heldout"; done
INFO="$(python3 bench/subject_info.py "$SUBJECT" --language "$LANGUAGE" $ALLOW)" || exit $?
eval "$INFO"
W="$WORK"
EDGES="$W/edges"
FAIL=0

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
bad()  { printf '\033[31m  FAIL: %s\033[0m\n' "$*"; FAIL=1; }
good() { printf '  OK: %s\n' "$*"; }

[ -d "$EDGES" ] || { echo "no tool output under $EDGES — run run/subject.sh $SUBJECT first"; exit 2; }
[ -f "$RESULTS/scores.json" ] || { echo "no $RESULTS/scores.json — run $LANG_DIR/run/subject.sh $SUBJECT first"; exit 2; }

# ── 0. the ground truth on disk is what THIS commit's oracle emits ──────────────────────────
say "0/3 — the ground truth reproduces from this commit's oracle"
TSX="$ROOT/.tools/ts/node_modules/.bin/tsx"; export NODE_PATH="$ROOT/.tools/ts/node_modules"
PROJECT0="${PROJECT_PATH:-$LANG_DIR/${PROJECT_FILE:-subjects/$SUBJECT/tsconfig.json}}"
[ -n "${PROJECT_OVERRIDES:-}" ] && [ -f "$(dirname "$PROJECT0")/tsconfig.callgraph-benchmark.json" ] \
  && PROJECT0="$(dirname "$PROJECT0")/tsconfig.callgraph-benchmark.json"
OCV="$W/verify-oracle"; rm -rf "$OCV"; mkdir -p "$OCV"
OCX() { "$TSX" --no-cache "$LANG_DIR/oracle/ts-ground-truth.ts" --project "$PROJECT0" --root "$SRC_DIR" "$@"; }
for pair in "sites:gt.sites.jsonl" "containers:gt.classes.txt" "methods:gt.methods.txt" "excluded:gt.excluded.txt" "heritage:gt.heritage.txt" "defaults:gt.defaults.txt"; do
  m="${pair%%:*}"; f="${pair##*:}"
  OCX --mode "$m" > "$OCV/$f" 2>/dev/null
  if cmp -s "$OCV/$f" "$W/$f"; then good "$f reproduces ($(wc -l < "$W/$f" | tr -d ' ') lines)"; else bad "$f on disk is NOT what this commit's oracle emits"; fi
done

# ── 1. determinism ───────────────────────────────────────────────────────────────────────────
say "1/3 — determinism: every deterministic tool re-run from a clean state"
SNAP="$W/verify-snapshot"
rm -rf "$SNAP"; mkdir -p "$SNAP"
cp -R "$EDGES/." "$SNAP/"
# the re-runs below rewrite the wall-clock timings; the score is re-computed over the ORIGINAL
# ones, because a timing is a measurement of the machine and not a claim the score makes
cp "$W/timings.tsv" "$W/verify-timings.tsv" 2>/dev/null || : > "$W/verify-timings.tsv"
# the timing PARTS the adapters append to (#8) are snapshotted the same way, and the re-runs
# below write to a scratch copy so the scored file is the one the original run produced
cp "$W/timings-parts.tsv" "$W/verify-timings-parts.tsv" 2>/dev/null || : > "$W/verify-timings-parts.tsv"

AXIOM_ENGINE="${AXIOM_ENGINE:-$ROOT/../../AxiomEngine/wt/bench-engine}"
# the parser lives inside the engine repository since it was reshaped into one tree (#469);
# the separate checkout is the fallback for an older engine
if [ -z "${AXIOM_PARSER:-}" ]; then
  AXIOM_PARSER="$AXIOM_ENGINE/parser/dist/index.js"
  [ -f "$AXIOM_PARSER" ] || AXIOM_PARSER="$ROOT/../../AxiomEngine/wt/bench-parser/dist/index.js"
fi

rerun() {
  local name="$1"; shift
  printf '  re-running %s…\n' "$name"
  "$@" > "$W/verify-$name.log" 2>&1 || { bad "$name re-run failed (see $W/verify-$name.log)"; return 1; }
}

# the tools read the pruned copy gate 4 built (`subject-src`), not the original tree — see subject.sh
TOOL_SRC="$W/subject-src"
[ -d "$TOOL_SRC" ] || { echo "no $TOOL_SRC — run typescript/run/subject.sh $SUBJECT first"; exit 2; }
SUBJECT_SUBDIR="$(cat "$W/subject-subdir.txt" 2>/dev/null || true)"
export NODE_PATH="$ROOT/.tools/ts/node_modules"
PROJECT="${PROJECT_PATH:-$LANG_DIR/${PROJECT_FILE:-subjects/$SUBJECT/tsconfig.json}}"
export AXIOM_PARSER AXIOM_ENGINE PROJECT SUBJECT_SRC="$TOOL_SRC" SUBJECT_SUBDIR
export LANG_DIR LANGUAGE WORK="$W"
for t in cha axiom codeql codegraph code_review_graph gitnexus graphify; do
  [ -x "$LANG_DIR/adapters/$t/run.sh" ] && rerun "$t" bash "$LANG_DIR/adapters/$t/run.sh" "$LANG_DIR" "$SUBJECT" "$TOOL_SRC"
done

for f in "$SNAP"/*/"$SUBJECT.jsonl"; do
  [ -e "$f" ] || continue
  tool="$(basename "$(dirname "$f")")"
  now="$EDGES/$tool/$SUBJECT.jsonl"
  if [ ! -f "$now" ]; then
    bad "$tool produced no output on the second run"
  elif ! diff -q "$f" "$now" >/dev/null; then
    bad "$tool is NOT deterministic — $(diff "$f" "$now" | grep -c '^[<>]') differing rows"
    diff "$f" "$now" | head -6 | sed 's/^/      /'
  else
    good "$tool byte-identical across two runs ($(grep -c . "$now") rows)"
  fi
done

# the re-runs appended their own timing parts; the original run's file is put back
cp "$W/verify-timings-parts.tsv" "$W/timings-parts.tsv" 2>/dev/null || true

# ── 2. the score itself reproduces ───────────────────────────────────────────────────────────
say "2/3 — the scorer is deterministic over fixed inputs"
cp "$RESULTS/scores.json" "$W/scores.before.json"
FAM=""; [ -n "${FAMILIES:-}" ] && FAM="--families"
python3 bench/run.py --subject "$SUBJECT" --language "$LANGUAGE" \
  --sites "$W/gt.sites.jsonl" --classes "$W/gt.classes.txt" --methods "$W/gt.methods.txt" \
  --excluded "$W/gt.excluded.txt" --heritage "$W/gt.heritage.txt" --defaults "$W/gt.defaults.txt" --coverage "$W/coverage.txt" --edges-dir "$EDGES" --source "$SRC_DIR" \
  --timings "$W/verify-timings.tsv" --warmup "$W/warmup.tsv" --timing-parts "$W/verify-timings-parts.tsv" --staged-copy "$W/staged-copy.txt" ${PRIOR_INTERNAL_USE:+--prior-internal-use} ${SUBJECT_SUBDIR:+--module-prefix "$SUBJECT_SUBDIR/"} \
  --out "$RESULTS" $FAM > "$W/verify-score.log" 2>&1 \
  || bad "re-scoring failed (see $W/verify-score.log)"

# The run manifest records the host's java/javac banner and platform, which are constant here; the
# comparison is over the whole file precisely so that a change in ANY of it is surfaced rather than
# assumed harmless.
if diff -q "$W/scores.before.json" "$RESULTS/scores.json" >/dev/null; then
  good "scores.json byte-identical when re-scored"
else
  bad "scores.json changed when re-scored over identical inputs — the HARNESS is non-deterministic"
  diff "$W/scores.before.json" "$RESULTS/scores.json" | head -12 | sed 's/^/      /'
fi

# ── 3. the manifest describes what is actually on disk ───────────────────────────────────────
say "3/3 — every input hash in the manifest still matches"
python3 - "$SUBJECT" "$LANGUAGE" "$RESULTS" <<'PY'
import hashlib, json, sys
from pathlib import Path

subject, language, results = sys.argv[1], sys.argv[2], sys.argv[3]
work = Path(".work") / language / subject
scores = json.loads((Path(results) / "scores.json").read_text())
recorded = scores["run"]["input_sha256"]

paths = {
    "sites":    work / "gt.sites.jsonl",
    "classes":  work / "gt.classes.txt",
    "methods":  work / "gt.methods.txt",
    "excluded": work / "gt.excluded.txt",
    "heritage": work / "gt.heritage.txt",
}
bad = 0
for key, want in sorted(recorded.items()):
    p = paths.get(key)
    if p is None and key.startswith("edges/"):
        p = work / "edges" / key.split("/", 1)[1] / f"{subject}.jsonl"
    if p is None or not p.exists():
        print(f"  FAIL: {key} recorded in the manifest but not on disk")
        bad = 1
        continue
    got = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()   # LF-normalised, as run.py hashes (#45)
    if got != want:
        print(f"  FAIL: {key} hash differs\n        manifest {want}\n        on disk  {got}")
        bad = 1
    else:
        print(f"  OK: {key}")
sys.exit(bad)
PY
[ $? -eq 0 ] || FAIL=1

say "verdict"
if [ "$FAIL" = 0 ]; then
  printf '\033[32m  VERIFIED — every tool reproduces, the scorer reproduces, the manifest matches.\033[0m\n'
else
  printf '\033[31m  NOT VERIFIED — see the failures above. Do not cite these numbers.\033[0m\n'
fi
exit $FAIL
