#!/usr/bin/env bash
set -euo pipefail
# NO TELEMETRY. codegraph reports usage by default: every run appends to one shared
# ~/.codegraph/telemetry-queue.jsonl (sixteen at once in the Defects4J sweep) and sends it under a
# machine id. A benchmark run is not usage, and a file every parallel run writes is shared state
# the results must not depend on. Its documented off-switches:
export CODEGRAPH_TELEMETRY=0 DO_NOT_TRACK=1
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"; SRC="$3"
CG="$ROOT/.tools/node/codegraph/node_modules/.bin/codegraph"
[ -x "$CG" ] || { echo "  SKIP: codegraph not installed"; exit 0; }
W="$WORK/cg"; rm -rf "$W"; mkdir -p "$W/src"
# staging the subject copy is HARNESS time, recorded and excluded from the tool's seconds (#8)
_T0() { python3 -c 'import time;print(time.time())'; }
_EL() { python3 -c "import time;print(round(time.time()-$1,2))"; }
C0=$(_T0)
cp -R "$SRC/." "$W/src/"
printf '%s\t%s\t%s\t%s\n' "codegraph" "codegraph" staging "$(_EL $C0)" >> "$WORK/timings-parts.tsv"
( cd "$W/src" && "$CG" init ) > "$W/build.log" 2>&1 || { echo "  !! init failed"; tail -8 "$W/build.log"; exit 1; }
grep -E 'nodes,' "$W/build.log" | tail -1 | sed 's/^/  /'
python3 "$LANG_DIR/adapters/codegraph/adapt.py" --db "$W/src/.codegraph/codegraph.db" \
  --root "$W/src" --subject "$SUBJECT" --meta "codegraph $(node -e "console.log(require('$ROOT/.tools/node/codegraph/node_modules/@colbymchenry/codegraph/package.json').version)" 2>/dev/null || echo '?')" \
  --edges "$WORK/edges/codegraph/$SUBJECT.jsonl"

# TWO ROWS, never merged (PROTOCOL §5.1, and the codeql/codeql-dispatch precedent): the
# tool's unprompted answer, and the same tool asked what a call could REACH using the
# candidate set / override index it records itself.
python3 "$LANG_DIR/adapters/codegraph/adapt.py" --db "$W/src/.codegraph/codegraph.db" \
  --root "$W/src" --subject "$SUBJECT" --dispatch --label "codegraph-dispatch" --meta "codegraph $(node -e "console.log(require('$ROOT/.tools/node/codegraph/node_modules/@colbymchenry/codegraph/package.json').version)" 2>/dev/null || echo '?')" \
  --edges "$WORK/edges/codegraph-dispatch/$SUBJECT.jsonl"
