#!/usr/bin/env bash
# code-review-graph: index the subject and read the CALLS edges out of its SQLite graph.
#
# THE SUBJECT IS COPIED TO AN ISOLATED CHECKOUT FIRST. The tool resolves a repository root by
# walking upward to the enclosing git repository, so running it in place indexed the whole benchmark
# — 31 files instead of 11, including this harness's own Python. A tool scored on the wrong corpus
# produces a number that looks entirely normal, which is why the isolation is not optional.
#
# The copy is `git init`-ed because that is what the tool uses to decide the root; its data
# directory is pinned to the work tree so no state survives between runs.
set -euo pipefail

LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"; SRC="${3:-$ROOT/subjects/$2/client}"
VENV="$ROOT/.tools/crg-venv"
CRG="$VENV/bin/code-review-graph"
[ -x "$CRG" ] || { echo "  SKIP: code-review-graph not installed (see adapters/code_review_graph/install.sh)"; exit 0; }

W="$WORK/crg"
SUBJECT_SRC_REAL="$SRC"
SRC="$W/src"
DATA="$W/data"
rm -rf "$W"; mkdir -p "$SRC" "$DATA"
# staging the subject copy is HARNESS time, recorded and excluded from the tool's seconds (#8)
_T0() { python3 -c 'import time;print(time.time())'; }
_EL() { python3 -c "import time;print(round(time.time()-$1,2))"; }
C0=$(_T0)
cp -R "$SUBJECT_SRC_REAL/." "$SRC/"
printf '%s\t%s\t%s\t%s\n' "code_review_graph" "code-review-graph" staging "$(_EL $C0)" >> "$WORK/timings-parts.tsv"
( cd "$SRC" && git init -q && git add -A && git -c user.email=b@b -c user.name=b commit -qm subject )

VERSION="$("$VENV/bin/pip" show code-review-graph 2>/dev/null | awk '/^Version:/{print $2}')"
( cd "$SRC" && CRG_DATA_DIR="$DATA" "$CRG" build ) > "$W/build.log" 2>&1 || {
  echo "  !! build failed"; tail -15 "$W/build.log"; exit 1; }
tail -1 "$W/build.log" | sed 's/^/  /'

python3 "$LANG_DIR/adapters/code_review_graph/adapt.py" \
    --db "$DATA/graph.db" --root "$SRC" --subject "$SUBJECT" \
    --meta "code-review-graph $VERSION" \
    --edges "$WORK/edges/code-review-graph/$SUBJECT.jsonl"

# TWO ROWS, never merged (PROTOCOL §5.1, and the codeql/codeql-dispatch precedent): the
# tool's unprompted answer, and the same tool asked what a call could REACH using the
# candidate set / override index it records itself.
python3 "$LANG_DIR/adapters/code_review_graph/adapt.py" \
    --db "$DATA/graph.db" --root "$SRC" --subject "$SUBJECT" --dispatch --label "code-review-graph-dispatch" \
    --meta "code-review-graph $VERSION" \
    --edges "$WORK/edges/code-review-graph-dispatch/$SUBJECT.jsonl"
