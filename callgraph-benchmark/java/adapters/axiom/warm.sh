#!/usr/bin/env bash
# One-time cost, paid BEFORE the timed run (issue #42): the engine compiles its Soufflé program to
# a native binary the first time a rule set is seen and caches it by content hash, and stages the
# platform IR's signatures once per library key. Timing the whole run.sh charged whichever
# subject ran first after an engine change with that compile. This solves a one-class stub — with
# the same staged platform IR the timed run uses — so both land here, and prints whether the
# binary cache was hit; subject.sh records that beside the timed run as `cold_seconds`.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"
PARSER="${AXIOM_PARSER:?}"; ENGINE="${AXIOM_ENGINE:?}"; JDK_IR="${AXIOM_JDK_IR:-}"
[ -f "$PARSER" ] && [ -d "$ENGINE" ] || { echo "cache=skipped"; exit 0; }
W="$ROOT/.work/java/_warm/axiom"; rm -rf "$W"; mkdir -p "$W/src/w" "$W/emptylib"
printf 'package w;\npublic class A { int f() { return 1; } static int g(A a) { return a.f(); } }\n' > "$W/src/w/A.java"
node "$PARSER" "$W/src" "warm-java" false "$W/ir" > "$W/parse.log" 2>&1
LIB="$W/emptylib"; [ -n "$JDK_IR" ] && [ -d "$JDK_IR" ] && LIB="$JDK_IR"
RUN_SOUFFLE="$ENGINE/graph/pipeline/run-souffle.sh"; [ -f "$RUN_SOUFFLE" ] || RUN_SOUFFLE="$ENGINE/src/pipeline/run-souffle.sh"
AXIOM_DEBUG=1 bash "$RUN_SOUFFLE" --debug --language java \
     --client-ir "$W/ir" --library "$LIB" \
     --intermediate "$W/int" --output "$W/out" > "$W/solve.log" 2>&1 || { echo "cache=failed"; exit 0; }
if grep -q "cache miss" "$W/solve.log"; then echo "cache=miss"; else echo "cache=hit"; fi
