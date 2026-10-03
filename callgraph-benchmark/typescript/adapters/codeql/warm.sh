#!/usr/bin/env bash
# One-time cost, paid BEFORE the timed run (issue #42): the query pack's dependencies are
# installed and the queries compiled to the CLI's cache. `codeql query run` does both lazily on
# first use, so the first subject of a run carried them in its `seconds`. Prints whether the
# compile cache was hit.
set -euo pipefail
LANG_DIR="$1"
CODEQL="${CODEQL:-$(command -v codeql || echo "$HOME/codeql-home/codeql/codeql")}"
[ -x "$CODEQL" ] || { echo "cache=skipped"; exit 0; }
LOG="$(mktemp)"
"$CODEQL" pack install "$LANG_DIR/adapters/codeql/ql" > "$LOG" 2>&1 || true
"$CODEQL" query compile -v "$LANG_DIR/adapters/codeql/ql" >> "$LOG" 2>&1 || { echo "cache=failed"; rm -f "$LOG"; exit 0; }
# with -v the CLI says "Compilation cache hit for <query>" per query it did not recompile
n=$(grep -c "^Compiling query plan" "$LOG" || true); h=$(grep -c "Compilation cache hit" "$LOG" || true)
if [ "$n" -gt 0 ] && [ "$h" -ge "$n" ]; then echo "cache=hit"; else echo "cache=miss"; fi
rm -f "$LOG"
