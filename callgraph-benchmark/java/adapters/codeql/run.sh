#!/usr/bin/env bash
# CodeQL: build a database over the subject's source, then ask the extractor two questions.
#
# TWO DATABASE MODES, chosen by what the subject actually is:
#   a LOCAL subject is compiled, because the harness compiles it anyway and a real build gives the
#     extractor full type information;
#   a MAVEN subject uses `--build-mode=none`, which indexes the -sources.jar without a build. Its
#     dependencies are absent either way — that is the honest representation of analysing one module
#     — and asking CodeQL to resolve a full Maven build would be measuring the build, not the tool.
#
# The mode is recorded in the run manifest, because it changes what CodeQL can see.
#
# TWO CONFIGURATIONS, REPORTED SEPARATELY:
#   codeql           `Call.getCallee()`   — the declared target; CodeQL's answer unprompted
#   codeql-dispatch  `viableCallable()`   — the virtual-dispatch fan from its dispatch library
# Merging them would let the permissive one set recall and the conservative one set precision.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"; SRC="${3:-}"
CODEQL="${CODEQL:-$(command -v codeql || echo "$HOME/codeql-home/codeql/codeql")}"
[ -x "$CODEQL" ] || { echo "  SKIP: no codeql CLI (set CODEQL=…)"; exit 0; }
# NO NETWORK FOR THE EXTRACTOR. Buildless Java extraction guesses jars from the subject's imports and
# downloads them from Maven Central: on rxjava it fetched for the subject's OWN published artifact
# (io.reactivex.rxjava3:rxjava:3.1.6), reactive-streams, and two unrelated `rxjava` artifacts. The
# output then depends on the network — same CLI, same query packs, 20,717 rows on one run and 26,584
# on another — and a jar that did arrive would be a library only this tool was given (#115). Only
# `database create` is cut off (`pack install` still needs the registry), through a closed proxy the
# JVM and the environment both honour; offline, rxjava gives 26,584 rows, byte-identical run to run.
offline() {
  HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=http://127.0.0.1:9 https_proxy=http://127.0.0.1:9 http_proxy=http://127.0.0.1:9 \
  JAVA_TOOL_OPTIONS="${JAVA_TOOL_OPTIONS:+$JAVA_TOOL_OPTIONS }-Dhttp.proxyHost=127.0.0.1 -Dhttp.proxyPort=9 -Dhttps.proxyHost=127.0.0.1 -Dhttps.proxyPort=9" \
  "$@"
}

W="$WORK/codeql"; rm -rf "$W"; mkdir -p "$W/build"
CP="${SUBJECT_CP:-}"

# timing PARTS (issue #8): `adapter<TAB>label<TAB>phase<TAB>seconds` — `shared` is paid by every
# label of this adapter, `own:<label>` by one, `staging` is harness cost billed to nobody
_T0() { python3 -c 'import time;print(time.time())'; }
_EL() { python3 -c "import time;print(round(time.time()-$1,2))"; }
tpart() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> "$WORK/timings-parts.tsv"; }
D0=$(_T0)
if [ -n "$CP" ] && [ -d "$CP" ]; then
  cat > "$W/build.sh" <<BUILD
#!/usr/bin/env bash
set -euo pipefail
javac -g -d "$W/build" -cp "$CP" \$(find "$SRC" -name '*.java')
BUILD
  chmod +x "$W/build.sh"
  MODE="compiled build"
  echo "  building database (compiled)…"
  offline "$CODEQL" database create "$W/db" --language=java --source-root="$SRC" \
      --command="$W/build.sh" --overwrite > "$W/create.log" 2>&1 \
      || { tail -20 "$W/create.log"; exit 1; }
else
  MODE="build-mode=none"
  echo "  building database (build-mode=none)…"
  offline "$CODEQL" database create "$W/db" --language=java --source-root="$SRC" \
      --build-mode=none --overwrite > "$W/create.log" 2>&1 \
      || { tail -20 "$W/create.log"; exit 1; }
fi

tpart codeql codeql shared "$(_EL $D0)"
# the query LIBRARY is pinned in qlpack.yml + codeql-pack.lock.yml (#71): a failed install is
# fatal for this tool, and the resolved library version is recorded beside the CLI's
"$CODEQL" pack install "$LANG_DIR/adapters/codeql/ql" > "$W/pack.log" 2>&1 || {
  echo "  !! codeql pack install failed"; tail -8 "$W/pack.log"; exit 1; }
VERSION="$("$CODEQL" version --format=terse 2>/dev/null || echo '?')"
LIB="$(awk '/codeql\/java-all:/{getline; gsub(/ +version: */,""); print}' "$LANG_DIR/adapters/codeql/ql/codeql-pack.lock.yml" 2>/dev/null || echo '?')"
VERSION="$VERSION java-all $LIB"

run_query() {
  local label="$1" query="$2"
  local Q0; Q0=$(_T0)
  "$CODEQL" query run --database="$W/db" --output="$W/$label.bqrs" \
      --ram=4096 "$LANG_DIR/adapters/codeql/ql/$query" > "$W/$label.log" 2>&1 || {
        echo "  !! $query failed"; tail -12 "$W/$label.log"; return 1; }
  tpart codeql "$label" "own:$label" "$(_EL $Q0)"
  "$CODEQL" bqrs decode --format=csv --no-titles --result-set=select \
      "$W/$label.bqrs" > "$W/$label.csv" 2>/dev/null \
    || "$CODEQL" bqrs decode --format=csv --no-titles "$W/$label.bqrs" > "$W/$label.csv"
  python3 "$LANG_DIR/adapters/codeql/adapt.py" --csv "$W/$label.csv" --subject "$SUBJECT" \
      --label "$label" --meta "codeql $VERSION" --build "$MODE" \
      --edges "$WORK/edges/$label/$SUBJECT.jsonl"
}
run_query "codeql"          "StaticCallEdges.ql"
run_query "codeql-dispatch" "ViableCallEdges.ql" || true
