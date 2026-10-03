#!/usr/bin/env bash
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"; SRC="$3"
GFY="${GRAPHIFY:-$ROOT/.tools/graphify-venv/bin/graphify}"
[ -x "$GFY" ] || { echo "  SKIP: graphify not installed"; exit 0; }
W="$WORK/gfy"; rm -rf "$W"; mkdir -p "$W/src"
# staging the subject copy is HARNESS time, recorded and excluded from the tool's seconds (#8)
_T0() { python3 -c 'import time;print(time.time())'; }
_EL() { python3 -c "import time;print(round(time.time()-$1,2))"; }
C0=$(_T0)
cp -R "$SRC/." "$W/src/"
printf '%s\t%s\t%s\t%s\n' "graphify" "graphify" staging "$(_EL $C0)" >> "$WORK/timings-parts.tsv"
( cd "$W/src" && "$GFY" update . --no-cluster ) > "$W/build.log" 2>&1 || { echo "  !! update failed"; tail -8 "$W/build.log"; exit 1; }
grep -E 'Rebuilt' "$W/build.log" | tail -1 | sed 's/^/  /'
python3 "$LANG_DIR/adapters/graphify/adapt.py" --graph "$W/src/graphify-out/graph.json" \
  --root "$W/src" --subject "$SUBJECT" --meta "graphifyy $("$ROOT/.tools/graphify-venv/bin/python" -c "import importlib.metadata as m; print(m.version('graphifyy'))" 2>/dev/null || echo '?')" --edges "$WORK/edges/graphify/$SUBJECT.jsonl"
