#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────────────────────
# ONE SUBJECT, END TO END — resolve, obtain, build ground truth, VERIFY it, run every tool, score.
#
#   java/run/subject.sh torture
#   run/subject.sh netty-transport
#   run/subject.sh hibernate-core --heldout      # held-out subjects require saying so
#   run/subject.sh --list
#
# A local subject is compiled here. A Maven subject is not built at all: the oracle reads the
# project's OWN PUBLISHED JAR and the tools read the -sources.jar from the same coordinate, both
# pinned by SHA-256. See subjects/fetch.py for why that is stronger than building a checkout.
#
# FOUR GATES, ALL FATAL, ALL BEFORE ANY TOOL IS SCORED. A score computed against unverified ground
# truth is worse than no score, because it looks exactly like a real one.
#
#   1  two independent bytecode readers agree, instruction for instruction
#   2  no two application types share a canonical name
#   3  the scorer itself can fail (mutation self-test)
#   4  the source the tools read and the bytecode the oracle reads describe the same program
#
# environment
#   AXIOM_PARSER   path to the parser's dist/index.js      (default: sibling checkout)
#   AXIOM_ENGINE   path to the engine checkout             (default: sibling checkout)
#   AXIOM_JDK_IR   platform IR root for the engine         (optional; absence is REPORTED)
# ─────────────────────────────────────────────────────────────────────────────────────────────
set -uo pipefail
# `comm`/`sort` need one collation and the oracle's lists are in code-point order; under
# en_US.UTF-8 typedoc's upper-case file names sorted differently and gate 4 reported 46 files
# "absent from the source tree" that were there (issue #29 §1)
export LC_ALL=C

LANG_DIR_SELF="$(cd "$(dirname "$0")/.." && pwd)"      # …/java
ROOT="$(cd "$LANG_DIR_SELF/.." && pwd)"                # repo root
LANGUAGE="$(basename "$LANG_DIR_SELF")"
cd "$ROOT"

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
die()  { printf '\n\033[31mFAIL: %s\033[0m\n' "$*" >&2; exit 1; }

[ "${1:-}" = "--list" ] && { python3 bench/subject_info.py --list --language "$LANGUAGE" dummy; exit 0; }
NAME="${1:?usage: run/subject.sh <subject> [--heldout]}"
shift || true
ALLOW=""
for arg in "$@"; do [ "$arg" = "--heldout" ] && ALLOW="--allow-heldout"; done

INFO="$(python3 bench/subject_info.py "$NAME" --language "$LANGUAGE" $ALLOW)" || exit $?
eval "$INFO"

command -v javac >/dev/null || die "no javac"
command -v javap >/dev/null || die "no javap"
JAVA_MAJOR="$(java -version 2>&1 | head -1 | sed -E 's/.*"([0-9]+).*/\1/')"
[ "${JAVA_MAJOR:-0}" -ge 24 ] || die "java.lang.classfile is final in JDK 24; found $JAVA_MAJOR"

W="$WORK"
EDGES="$W/edges"
OCDIR="$ROOT/.work/$LANGUAGE/oracle-classes"
mkdir -p "$W" "$OCDIR"
javac -d "$OCDIR" "$LANG_DIR/oracle/ClassfileGroundTruth.java" || die "oracle will not compile"

say "subject: $SUBJECT  [$SPLIT / $KIND]  ${COORDINATE:+$COORDINATE}"
[ "$SPLIT" = heldout ] && printf '\033[33m  HELD OUT — score once, report the finding, do not tune against it.\033[0m\n'

# ── 1. obtain ────────────────────────────────────────────────────────────────────────────────
if [ -n "$NEEDS_FETCH" ]; then
  python3 "$LANG_DIR/subjects/fetch.py" "$SUBJECT" || die "fetch failed"
elif [ -n "$NEEDS_COMPILE" ]; then
  say "compiling"
  rm -rf "$CLASSES_DIR" "$CP_DIR"; mkdir -p "$CLASSES_DIR" "$CP_DIR"
  if [ -n "${CP_SRC_DIR:-}" ] && [ -d "$CP_SRC_DIR" ]; then
    # `--release 21`: the class files are read by the oracle (any version) and by WALA (up to 21)
    javac --release 21 -g -d "$CP_DIR" $(find "$CP_SRC_DIR" -name '*.java') || die "javac (classpath tree)"
  fi
  javac --release 21 -g -d "$CLASSES_DIR" -cp "$CP_DIR" $(find "$SRC_DIR" -name '*.java') || die "javac (subject)"
fi
echo "  $(find "$CLASSES_DIR" -name '*.class' | wc -l | tr -d ' ') class files, $(find "$SRC_DIR" -name '*.java' | wc -l | tr -d ' ') source files"

PREFIX_ARG=""; [ -n "$INCLUDE_PREFIX" ] && PREFIX_ARG="--include-prefix $INCLUDE_PREFIX"
OC() { java -cp "$OCDIR" ClassfileGroundTruth --app "$CLASSES_DIR" $PREFIX_ARG "$@"; }

# ── GATE 4 first: it decides the scored universe the rest is built over ──────────────────────
say "gate 4/4 — source and bytecode describe the same program"
OC --mode classes > "$W/classes.all.txt" 2>/dev/null
python3 bench/correspondence.py --sources "$SRC_DIR" --classes-list "$W/classes.all.txt" \
        --emit-types "$W/types.txt" --language "$LANGUAGE" || die "source/bytecode correspondence"
ONLY="--only-types $W/types.txt"

# ── 2. ground truth ──────────────────────────────────────────────────────────────────────────
say "building ground truth"
OC $ONLY --mode sites     > "$W/gt.sites.jsonl"   2>/dev/null
OC $ONLY --mode classes   > "$W/gt.classes.txt"   2>/dev/null
OC $ONLY --mode methods   > "$W/gt.methods.txt"   2>/dev/null
OC $ONLY --mode excluded  > "$W/gt.excluded.txt"  2>/dev/null
OC $ONLY --mode heritage  > "$W/gt.heritage.txt"  2>/dev/null
OC $ONLY --mode anonmap   > "$W/gt.anonmap.txt"   2>/dev/null
OC        --mode raw      > "$W/raw.classfile.txt" 2>/dev/null
echo "  $(wc -l < "$W/gt.sites.jsonl" | tr -d ' ') call sites, $(wc -l < "$W/gt.classes.txt" | tr -d ' ') types, $(wc -l < "$W/gt.methods.txt" | tr -d ' ') methods"

say "gate 1/4 — independent reader agreement (java.lang.classfile vs javap)"
# stderr is KEPT: a reader that crashes must say so, not leave an empty file that gate 1 reads as
# a disagreement between two readers (#56)
python3 "$LANG_DIR/oracle/javap_reader.py" "$CLASSES_DIR" > "$W/raw.javap.txt" 2> "$W/raw.javap.err" \
  || die "javap reader failed: $(tail -3 "$W/raw.javap.err")"
if ! diff -q "$W/raw.classfile.txt" "$W/raw.javap.txt" >/dev/null; then
  diff -u "$W/raw.classfile.txt" "$W/raw.javap.txt" | head -30
  die "the two bytecode readers disagree — the ground truth is not trustworthy"
fi
echo "  OK: $(wc -l < "$W/raw.classfile.txt" | tr -d ' ') invoke instructions, identical on both readers"

# ── GATE 1b: a THIRD reader, independently written ───────────────────────────────────────────
# The README claimed this cross-check as a standing guarantee while nothing invoked it. Either it
# runs or the claim goes; it runs. `java/third_party/axiom/ClassFileOracle.java` is a third
# implementation over the same class files, written by other people solving the same problem — the
# check most likely to catch a CONVENTION this benchmark got wrong, which is the one thing a second
# READER cannot catch.
#
# It uses the flattened naming this benchmark deliberately does not, so the comparison projects
# through that flattening; a mismatch is reported and does not fail the run, because a disagreement
# about a convention is a finding to investigate rather than proof that either side is broken.
say "gate 1b/4 — third independent reader (informational)"
if [ -f "$LANG_DIR/third_party/axiom/ClassFileOracle.java" ]; then
  javac -d "$OCDIR" "$LANG_DIR/third_party/axiom/ClassFileOracle.java" 2>/dev/null \
    && java -cp "$OCDIR" ClassFileOracle --app "$CLASSES_DIR" --app-only \
         > "$W/third.lb.edges" 2>/dev/null \
    && python3 bench/third_reader_diff.py --sites "$W/gt.sites.jsonl" \
         --third "$W/third.lb.edges" --excluded "$W/gt.excluded.txt" | sed 's/^/  /' \
    || echo "  SKIP: third reader did not build or run"
else
  echo "  SKIP: no third reader vendored"
fi

# ── GATE 1c: the ENVELOPE, by an independent implementation of JVMS §5.4.3.3 + §5.4.6 ───────
# Gate 1 proves the bytecode was READ correctly; gate 1b compares `certain`. Nothing checked
# `possible`, and on rxjava it omitted 8,172 runnable edges and included 56,403 impossible ones
# (issue #30) — both errors moving the `unique` flag the headline is built on. This gate recomputes
# every virtual, interface and method-reference site's envelope from the class files, in code
# written separately from the oracle's, and refuses the subject on any disagreement.
say "gate 1c/4 — the dispatch envelope agrees with an independent JVMS resolution + selection"
javac -d "$OCDIR" -cp "$OCDIR" "$LANG_DIR/oracle/EnvelopeCheck.java" || die "envelope checker will not compile"
if ! java -cp "$OCDIR" EnvelopeCheck --app "$CLASSES_DIR" $PREFIX_ARG $ONLY --sites "$W/gt.sites.jsonl" > "$W/envelope.diff" 2> "$W/envelope.log"; then
  head -20 "$W/envelope.diff"; tail -1 "$W/envelope.log"
  die "the oracle's envelope disagrees with the independent JVMS selection"
fi
echo "  OK: $(tail -1 "$W/envelope.log" | sed 's/^# envelope check: //')"

say "gate 2/4 — canonical type names are unambiguous"
OC $ONLY --mode collisions > "$W/collisions.txt" 2>/dev/null
if [ -s "$W/collisions.txt" ]; then
  head -10 "$W/collisions.txt"
  die "two application types share a canonical name — both bounds would be computed over a type that does not exist"
fi
echo "  OK: no collisions"

# ── the unit tests: one filed issue's edge case each (tests/) ─────────────────────────────
say "gate 3a — unit tests (tests/)"
if UT="$(bash bench/test.sh -q 2>&1)"; then echo "$UT" | tail -1 | sed 's/^/  /'; else
  echo "$UT" | tail -25; die "unit tests failed — run bash bench/test.sh"; fi

say "gate 3/4 — the scorer can fail (mutation self-test)"
python3 bench/selftest.py --sites "$W/gt.sites.jsonl" --classes "$W/gt.classes.txt" \
        --methods "$W/gt.methods.txt" --source "$SRC_DIR" --language "$LANGUAGE" \
        --excluded "$W/gt.excluded.txt" --heritage "$W/gt.heritage.txt" \
        || die "scorer self-test failed"

# ── 3. the tools ─────────────────────────────────────────────────────────────────────────────
# TOOLS="axiom codeql" re-runs only those; the other tools' rows and timings from the previous run
# are KEPT and re-scored against the (possibly re-read) ground truth. Without it, re-measuring one
# tool after updating its checkout meant re-running six.
TOOLS="${TOOLS:-cha axiom codeql codegraph code_review_graph gitnexus graphify}"
if [ "$TOOLS" = "cha axiom codeql codegraph code_review_graph gitnexus graphify" ]; then
  rm -rf "$EDGES"; mkdir -p "$EDGES"
  : > "$W/timings.tsv"; : > "$W/timings-parts.tsv"
else
  mkdir -p "$EDGES"; touch "$W/timings.tsv"
  for t in $TOOLS; do
    for d in "$EDGES/$t" "$EDGES/$(echo "$t" | tr _ -)" "$EDGES/$t"-* "$EDGES/$(echo "$t" | tr _ -)"-*; do rm -rf "$d"; done
    [ "$t" = cha ] && rm -rf "$EDGES/ideal"
    grep -v "^$t	" "$W/timings.tsv" > "$W/timings.tsv.new" 2>/dev/null || true; mv "$W/timings.tsv.new" "$W/timings.tsv"
    grep -v "^$t	" "$W/timings-parts.tsv" > "$W/timings-parts.tsv.new" 2>/dev/null || true; mv "$W/timings-parts.tsv.new" "$W/timings-parts.tsv"
  done
fi
AXIOM_ENGINE="${AXIOM_ENGINE:-$ROOT/../../AxiomEngine/wt/bench-engine}"
# the parser lives inside the engine repository since it was reshaped into one tree (#469);
# the separate checkout is the fallback for an older engine
if [ -z "${AXIOM_PARSER:-}" ]; then
  AXIOM_PARSER="$AXIOM_ENGINE/parser/dist/index.js"
  [ -f "$AXIOM_PARSER" ] || AXIOM_PARSER="$ROOT/../../AxiomEngine/wt/bench-parser/dist/index.js"
fi
AXIOM_JDK_IR="${AXIOM_JDK_IR:-$ROOT/../../AxiomEngine/jdk}"
export LANG_DIR="$LANG_DIR" LANGUAGE="$LANGUAGE" WORK="$W"

# A tool that fails or is absent is ABSENT FROM THE REPORT — never a zero, which would be a claim
# the run did not make.
for t in $TOOLS; do
  [ -x "$LANG_DIR/adapters/$t/run.sh" ] || continue
  say "tool: $t"
  # WARM FIRST (issue #42): a tool's one-time cost — axiom's Soufflé compile and platform-IR
  # staging, CodeQL's query compile — is paid here, timed on its own, and recorded as
  # `cold_seconds` with whether the tool's cache was hit. `seconds` is then the warm run, the
  # same for the first subject of a session as for the tenth.
  if [ -x "$LANG_DIR/adapters/$t/warm.sh" ]; then
    C0=$(python3 -c 'import time;print(time.time())')
    CACHE=$(AXIOM_PARSER="$AXIOM_PARSER" AXIOM_ENGINE="$AXIOM_ENGINE" AXIOM_JDK_IR="$AXIOM_JDK_IR" \
            bash "$LANG_DIR/adapters/$t/warm.sh" "$LANG_DIR" 2>/dev/null | grep -o 'cache=[a-z]*' | tail -1 || true)
    CL=$(python3 -c "import time;print(round(time.time()-$C0,2))")
    echo "  warm-up ${CL}s (${CACHE:-cache=unknown})"
    grep -v "^$t	" "$W/warmup.tsv" > "$W/warmup.tsv.new" 2>/dev/null || true; mv "$W/warmup.tsv.new" "$W/warmup.tsv"
    printf '%s\t%s\t%s\n' "$t" "$CL" "${CACHE#cache=}" >> "$W/warmup.tsv"
  fi
  T0=$(python3 -c 'import time;print(time.time())')
  AXIOM_PARSER="$AXIOM_PARSER" AXIOM_ENGINE="$AXIOM_ENGINE" AXIOM_JDK_IR="$AXIOM_JDK_IR" \
  SUBJECT_SRC="$SRC_DIR" SUBJECT_CLASSES="$CLASSES_DIR" SUBJECT_CP="${CP_DIR:-}" \
  SUBJECT_WORK="$W" \
    bash "$LANG_DIR/adapters/$t/run.sh" "$LANG_DIR" "$SUBJECT" "$SRC_DIR" \
    || echo "  !! $t failed — reported as absent, never as zero"
  EL=$(python3 -c "import time;print(round(time.time()-$T0,2))")
  echo "  ${EL}s"
  printf '%s\t%s\n' "$t" "$EL" >> "$W/timings.tsv"
done

# THE TOOL UNDER TEST MUST HAVE RUN. The axiom adapter skips itself when the parser or engine is
# not found, and a fresh checkout then produced a complete-looking report with no axiom row
# (#72 §2). Refuse, unless the caller says the omission is intended.
case " $TOOLS " in *" axiom "*)
  [ -f "$EDGES/axiom/$SUBJECT.jsonl" ] || [ -n "${ALLOW_MISSING_AXIOM:-}" ] \
    || die "axiom produced no rows (parser/engine not found?) — set AXIOM_PARSER / AXIOM_ENGINE, or ALLOW_MISSING_AXIOM=1 to score without it";;
esac

# ── 4. score ─────────────────────────────────────────────────────────────────────────────────
say "scoring"
FAM=""; [ -n "$FAMILIES" ] && FAM="--families"
python3 bench/run.py --subject "$SUBJECT" --language "$LANGUAGE" \
  --sites "$W/gt.sites.jsonl" --classes "$W/gt.classes.txt" --methods "$W/gt.methods.txt" \
  --excluded "$W/gt.excluded.txt" --heritage "$W/gt.heritage.txt" --anonmap "$W/gt.anonmap.txt" \
  --edges-dir "$EDGES" --source "$SRC_DIR" \
  --timings "$W/timings.tsv" --warmup "$W/warmup.tsv" --timing-parts "$W/timings-parts.tsv" \
  --out "$RESULTS" $FAM || die "scoring failed"

say "done — $RESULTS/report.md"
