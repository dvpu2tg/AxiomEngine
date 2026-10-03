#!/usr/bin/env bash
# Graphify: the DETERMINISTIC path only.
#
# `graphify update --no-cluster` runs the tree-sitter extractor and nothing else: no LLM, no
# embeddings, no community naming. The semantic layer exists for docs, PDFs and images, not for
# code, and including it would put a non-deterministic step in a deterministic tier.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"; SRC="${3:-$ROOT/subjects/$2/client}"
GFY="${GRAPHIFY:-$ROOT/.tools/graphify-venv/bin/graphify}"
[ -x "$GFY" ] || { echo "  SKIP: graphify not installed (adapters/graphify/install.sh)"; exit 0; }
W="$WORK/gfy"; SUBJECT_SRC_REAL="$SRC"; SRC="$W/src"
rm -rf "$W"; mkdir -p "$SRC"
# staging the subject copy is HARNESS time, recorded and excluded from the tool's seconds (#8)
_T0() { python3 -c 'import time;print(time.time())'; }
_EL() { python3 -c "import time;print(round(time.time()-$1,2))"; }
C0=$(_T0)
cp -R "$SUBJECT_SRC_REAL/." "$SRC/"
printf '%s\t%s\t%s\t%s\n' "graphify" "graphify" staging "$(_EL $C0)" >> "$WORK/timings-parts.tsv"
VERSION="$("$ROOT/.tools/graphify-venv/bin/python" -c "import importlib.metadata as m; print(m.version('graphifyy'))" 2>/dev/null || echo '?')"
( cd "$SRC" && "$GFY" update . --no-cluster ) > "$W/build.log" 2>&1 || { echo "  !! update failed"; tail -15 "$W/build.log"; exit 1; }
grep -E 'Rebuilt' "$W/build.log" | tail -1 | sed 's/^/  /'
python3 "$LANG_DIR/adapters/graphify/adapt.py" --graph "$SRC/graphify-out/graph.json" \
    --subject "$SUBJECT" --meta "graphifyy ${VERSION:-?}" \
    --edges "$WORK/edges/graphify/$SUBJECT.jsonl"
