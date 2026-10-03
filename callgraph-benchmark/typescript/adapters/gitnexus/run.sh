#!/usr/bin/env bash
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"; SRC="$3"
GNX="$ROOT/.tools/node/gitnexus/node_modules/.bin/gitnexus"
[ -x "$GNX" ] || { echo "  SKIP: gitnexus not installed"; exit 0; }
W="$WORK/gnx"; rm -rf "$W"; mkdir -p "$W/src"
# ITS OWN REGISTRY. `analyze` registers the index in a global ~/.gitnexus/registry.json under a
# lock, and every query looks the index up there. With subjects analysed in parallel (the Defects4J
# sweep runs 16 at a time) runs lost that race: "registry entry ... was not added", the index
# discarded, or a query that found nothing — the row absent. 28 + 2 of the first 294 bugs at -j16.
# GITNEXUS_HOME moves the registry and its lock under this run's own directory.
export GITNEXUS_HOME="$W/home"; mkdir -p "$GITNEXUS_HOME"
# staging the subject copy is HARNESS time, recorded and excluded from the tool's seconds (#8)
_T0() { python3 -c 'import time;print(time.time())'; }
_EL() { python3 -c "import time;print(round(time.time()-$1,2))"; }
C0=$(_T0)
cp -R "$SRC/." "$W/src/"
printf '%s\t%s\t%s\t%s\n' "gitnexus" "gitnexus" staging "$(_EL $C0)" >> "$WORK/timings-parts.tsv"
( cd "$W/src" && "$GNX" analyze . --skip-git ) > "$W/build.log" 2>&1 || { echo "  !! analyze failed"; tail -8 "$W/build.log"; exit 1; }
grep -E 'nodes \|' "$W/build.log" | tail -1 | sed 's/^/  /'
# EXPORT is not the tool's time (#98): its query CLI truncates a result at 64 KiB mid-JSON, so the
# adapter pages it 200 rows per process; that loop is recorded as its own part, published in
# seconds_breakdown.export and left out of `seconds`, the way `staging` is
X0=$(_T0)
python3 "$LANG_DIR/adapters/gitnexus/adapt.py" --gitnexus "$GNX" --src "$W/src" \
  --subject "$SUBJECT" --meta "gitnexus $(node -e "console.log(require('$ROOT/.tools/node/gitnexus/node_modules/gitnexus/package.json').version)" 2>/dev/null || echo '?')" \
  --edges "$WORK/edges/gitnexus/$SUBJECT.jsonl"
printf '%s\t%s\t%s\t%s\n' "gitnexus" "gitnexus" export "$(_EL $X0)" >> "$WORK/timings-parts.tsv"
