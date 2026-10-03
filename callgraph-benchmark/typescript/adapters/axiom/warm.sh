#!/usr/bin/env bash
# One-time cost, paid BEFORE the timed run (issue #42): the engine compiles its Soufflé program to
# a native binary the first time a rule set is seen and caches it by content hash. Timing the
# whole run.sh made the first subject after an engine change read ~90 s on a 195-line file and
# every later one ~1 s. This solves a one-file stub so the compile lands here, and prints whether
# the cache was hit; subject.sh records that beside the timed run as `cold_seconds`.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"
PARSER="${AXIOM_PARSER:?}"; ENGINE="${AXIOM_ENGINE:?}"
[ -f "$PARSER" ] && [ -d "$ENGINE" ] || { echo "cache=skipped"; exit 0; }
W="$ROOT/.work/typescript/_warm/axiom"; rm -rf "$W"; mkdir -p "$W/src" "$W/emptylib"
printf 'export class A { f(): number { return 1; } }\nexport function g(a: A): number { return a.f(); }\n' > "$W/src/a.ts"
node "$PARSER" "$W/src" "warm-ts" false "$W/ir" > "$W/parse.log" 2>&1
RUN_SOUFFLE="$ENGINE/graph/pipeline/run-souffle.sh"; [ -f "$RUN_SOUFFLE" ] || RUN_SOUFFLE="$ENGINE/src/pipeline/run-souffle.sh"
AXIOM_DEBUG=1 bash "$RUN_SOUFFLE" --debug --language typescript \
     --client-ir "$W/ir" --library "$W/emptylib" \
     --intermediate "$W/int" --output "$W/out" > "$W/solve.log" 2>&1 || { echo "cache=failed"; exit 0; }
if grep -q "cache miss" "$W/solve.log"; then echo "cache=miss"; else echo "cache=hit"; fi
