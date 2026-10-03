#!/usr/bin/env bash
# CodeQL, JavaScript/TypeScript extractor. No build is required for this language — the extractor
# reads the source tree directly — so the `needs` column reads `source only`, unlike the Java side
# where a local subject is compiled.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"; SRC="$3"
CODEQL="${CODEQL:-$(command -v codeql || echo "$HOME/codeql-home/codeql/codeql")}"
[ -x "$CODEQL" ] || { echo "  SKIP: no codeql CLI"; exit 0; }
# NO NETWORK FOR THE EXTRACTOR — the same guard as the Java adapter (see its run.sh, #115): a
# dependency the extractor fetched would be a library only this tool was given.
offline() {
  HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9 https_proxy=http://127.0.0.1:9 http_proxy=http://127.0.0.1:9 \
  JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:+$JAVA_TOOL_OPTIONS }-Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=9 -Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=9" \
  "$@"
}
W="$WORK/codeql"; rm -rf "$W"; mkdir -p "$W"
# timing PARTS (issue #8): `adapter<TAB>label<TAB>phase<TAB>seconds` — `shared` is paid by every
# label of this adapter, `own:<label>` by one, `staging` is harness cost billed to nobody
_T0() { python3 -c 'import time;print(time.time())'; }
_EL() { python3 -c "import time;print(round(time.time()-$1,2))"; }
tpart() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> "$WORK/timings-parts.tsv"; }
D0=$(_T0)
offline "$CODEQL" database create "$W/db" --language=javascript --source-root="$SRC" --overwrite \
  > "$W/create.log" 2>&1 || { echo "  !! db create failed"; tail -10 "$W/create.log"; exit 1; }
tpart codeql codeql shared "$(_EL $D0)"
# the query LIBRARY is pinned in qlpack.yml + codeql-pack.lock.yml (#71)
"$CODEQL" pack install "$LANG_DIR/adapters/codeql/ql" > "$W/pack.log" 2>&1 || {
  echo "  !! codeql pack install failed"; tail -8 "$W/pack.log"; exit 1; }
VERSION="$("$CODEQL" version --format=terse 2>/dev/null || echo '?')"
LIB="$(awk '/codeql\/javascript-all:/{getline; gsub(/ +version: */,""); print}' "$LANG_DIR/adapters/codeql/ql/codeql-pack.lock.yml" 2>/dev/null || echo '?')"
VERSION="$VERSION javascript-all $LIB"
Q0=$(_T0)
"$CODEQL" query run --database="$W/db" --output="$W/q.bqrs" --ram=4096 \
  "$LANG_DIR/adapters/codeql/ql/CallEdges.ql" > "$W/q.log" 2>&1 || {
    echo "  !! query failed"; tail -10 "$W/q.log"; exit 1; }
tpart codeql codeql own:codeql "$(_EL $Q0)"
"$CODEQL" bqrs decode --format=csv --no-titles "$W/q.bqrs" > "$W/q.csv"
python3 "$LANG_DIR/adapters/codeql/adapt.py" --csv "$W/q.csv" --subject "$SUBJECT" \
  --meta "codeql $VERSION" --build "source only" \
  --edges "$WORK/edges/codeql/$SUBJECT.jsonl"
