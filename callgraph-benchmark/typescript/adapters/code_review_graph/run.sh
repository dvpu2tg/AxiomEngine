#!/usr/bin/env bash
# The tool resolves its repository root by walking up to the enclosing git repo, so the subject is
# copied to an isolated, freshly `git init`-ed checkout — otherwise it indexes this whole benchmark.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"; SRC="$3"
VENV="$ROOT/.tools/crg-venv"; CRG="$VENV/bin/code-review-graph"
[ -x "$CRG" ] || { echo "  SKIP: code-review-graph not installed"; exit 0; }
W="$WORK/crg"; rm -rf "$W"; mkdir -p "$W/src" "$W/data"
# staging the subject copy is HARNESS time, recorded and excluded from the tool's seconds (#8)
_T0() { python3 -c 'import time;print(time.time())'; }
_EL() { python3 -c "import time;print(round(time.time()-$1,2))"; }
C0=$(_T0)
cp -R "$SRC/." "$W/src/"
printf '%s\t%s\t%s\t%s\n' "code_review_graph" "code-review-graph" staging "$(_EL $C0)" >> "$WORK/timings-parts.tsv"
( cd "$W/src" && git init -q && git add -A && git -c user.email=b@b -c user.name=b commit -qm subject )
VERSION="$("$VENV/bin/pip" show code-review-graph 2>/dev/null | awk '/^Version:/{print $2}')"
( cd "$W/src" && CRG_DATA_DIR="$W/data" "$CRG" build ) > "$W/build.log" 2>&1 || {
  echo "  !! build failed"; tail -8 "$W/build.log"; exit 1; }
tail -1 "$W/build.log" | sed 's/^/  /'
python3 "$LANG_DIR/adapters/code_review_graph/adapt.py" --db "$W/data/graph.db" --root "$W/src" \
  --subject "$SUBJECT" --meta "code-review-graph $VERSION" \
  --edges "$WORK/edges/code-review-graph/$SUBJECT.jsonl"

# TWO ROWS, never merged (PROTOCOL §5.1, and the codeql/codeql-dispatch precedent): the
# tool's unprompted answer, and the same tool asked what a call could REACH using the
# candidate set / override index it records itself.
python3 "$LANG_DIR/adapters/code_review_graph/adapt.py" --db "$W/data/graph.db" --root "$W/src" \
  --subject "$SUBJECT" --dispatch --label "code-review-graph-dispatch" --meta "code-review-graph $VERSION" \
  --edges "$WORK/edges/code-review-graph-dispatch/$SUBJECT.jsonl"
