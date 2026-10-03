#!/usr/bin/env bash
# axiomengine: parse the subject into the relational IR, solve, adapt.
#
# THE PLATFORM IR IS A CONFIGURATION, NOT A FREEBIE. This engine takes the platform library as a
# typed IR and uses it as a TYPE ORACLE: without it a receiver typed through java.util cannot be
# resolved by any rule. The source-reading tools do not get that, so the engine is run BOTH ways and
# both rows are reported:
#
#     axiom         with the platform IR staged    — the tool as its authors intend it to run
#     axiom-nolib   source-equivalent staging      — the same input budget as the other tools
#
# Neither is "the real one"; they answer different questions and the report says which.
#
# A subject may also ship a stub library tree (the torture subject does, to make its `dep.*` a real
# boundary). A Maven subject has none — its dependencies are simply absent, which is the honest
# representation of analysing one module of a larger project.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"; SRC="${3:-}"
PARSER="${AXIOM_PARSER:?}"; ENGINE="${AXIOM_ENGINE:?}"; JDK_IR="${AXIOM_JDK_IR:-}"
# the commit of each checkout, recorded in every row's metadata (see adapt.py --parser-commit)
PARSER_COMMIT="$(git -C "$(dirname "$PARSER")" rev-parse HEAD 2>/dev/null || echo '?')"
ENGINE_COMMIT="$(git -C "$ENGINE" rev-parse HEAD 2>/dev/null || echo '?')"
[ -f "$PARSER" ] && [ -d "$ENGINE" ] || { echo "  SKIP: parser or engine not found"; exit 0; }
# the engine's pipeline script: `graph/pipeline/` since the repository was reshaped into one
# tree for parser + graph (#469); `src/pipeline/` before. `--debug` keeps `raw/` — the Soufflé
# relations the adapter reads — beside `graph.sqlite`; without it the engine deletes them once
# the database is written and the row silently vanished (#81).
RUN_SOUFFLE="$ENGINE/graph/pipeline/run-souffle.sh"; [ -f "$RUN_SOUFFLE" ] || RUN_SOUFFLE="$ENGINE/src/pipeline/run-souffle.sh"
export AXIOM_DEBUG=1

W="$WORK/axiom"; rm -rf "$W"; mkdir -p "$W"
STUB="$LANG_DIR/subjects/$SUBJECT/lib"
# timing PARTS (issue #8): `adapter<TAB>label<TAB>phase<TAB>seconds` — `shared` is paid by every
# label of this adapter, `own:<label>` by one, `staging` is harness cost billed to nobody
_T0() { python3 -c 'import time;print(time.time())'; }
_EL() { python3 -c "import time;print(round(time.time()-$1,2))"; }
tpart() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> "$WORK/timings-parts.tsv"; }

P0=$(_T0)
node "$PARSER" "$SRC" "$SUBJECT-client" false "$W/client-ir" > "$W/parse-client.log" 2>&1 || {
  echo "  !! parse failed"; tail -5 "$W/parse-client.log"; exit 1; }
# THE LIBRARY ROOTS ARE STABLE PATHS (#88). The engine keys its staged-library cache on the
# `--library` string, each module's path and its CSVs' size+mtime; a per-subject symlink farm
# under $W gave every solve a key of its own, so the warm-up (warm.sh, `--library $JDK_IR`)
# warmed a key no timed run used, every timed solve re-staged the 2 GB platform IR into
# `seconds` — 473 MB of duplicate facts per solve, 22 copies in one pass, and a full disk. The
# platform root is passed as itself, the stub IR is parsed once into a content-addressed
# directory (stub sources + parser commit) so its mtimes do not move between runs, and the
# engine's comma-separated --library joins them.
STUB_IR=""
if [ -d "$STUB" ]; then
  STUB_KEY="$( { echo "$PARSER_COMMIT"; find "$STUB" -type f | LC_ALL=C sort | xargs shasum; } | shasum | cut -c1-16)"
  STUB_IR="$ROOT/.work/java/_stub-ir/$SUBJECT-$STUB_KEY"
  if [ ! -f "$STUB_IR/all-types.csv" ]; then
    rm -rf "$STUB_IR.tmp"; mkdir -p "$(dirname "$STUB_IR")"
    node "$PARSER" "$STUB" "$SUBJECT-lib" false "$STUB_IR.tmp" > "$W/parse-lib.log" 2>&1 || {
      echo "  !! library parse failed"; tail -5 "$W/parse-lib.log"; exit 1; }
    rm -rf "$STUB_IR"; mv "$STUB_IR.tmp" "$STUB_IR"
  fi
fi
EMPTY_LIB="$ROOT/.work/java/_emptylib"; mkdir -p "$EMPTY_LIB"
tpart axiom axiom shared "$(_EL $P0)"

solve() {
  local label="$1" libroot="$2" note="$3" budget="$4"
  local S0; S0=$(_T0)
  bash "$RUN_SOUFFLE" --client-ir "$W/client-ir" --library "$libroot" --debug \
       --intermediate "$W/int-$label" --output "$W/out-$label" > "$W/solve-$label.log" 2>&1 || {
    echo "  !! solve failed ($label)"; tail -5 "$W/solve-$label.log"; return 1; }
  tpart axiom "$label" "own:$label" "$(_EL $S0)"
  # whether THIS solve staged the library or found it staged — the warm-up's answer in
  # warmup.tsv is about the warm-up; the timed run's own is what `seconds` includes (#88)
  # recorded as a timing PART (`libcache:<label>`, 1 = miss) because that file is snapshotted by
  # verify.sh: a re-run always hits, and the row itself must stay byte-identical
  local lib_miss=0; grep -q "cache miss" "$W/solve-$label.log" && lib_miss=1
  echo "  $label: library cache $([ "$lib_miss" = 1 ] && echo miss || echo hit)"
  tpart axiom "$label" "libcache:$label" "$lib_miss"
  python3 "$LANG_DIR/adapters/axiom/adapt.py" --ir "$W/client-ir" --out "$W/out-$label" \
      --subject "$SUBJECT" --label "$label" --meta "$note" --build "$budget" \
      --parser-commit "$PARSER_COMMIT" --engine-commit "$ENGINE_COMMIT" \
      --edges "$WORK/edges/$label/$SUBJECT.jsonl"
}

mods=0
if [ -n "$JDK_IR" ] && [ -d "$JDK_IR" ]; then
  for d in "$JDK_IR"/*/; do [ -f "$d/all-types.csv" ] && mods=$((mods+1)); done
fi
if [ "$mods" = 0 ]; then
  # no platform IR: the `axiom` configuration does not exist on this machine. Publishing the
  # `axiom-nolib` numbers under `axiom`'s name and budget is exactly what a fresh clone did (#75);
  # the row is reported ABSENT instead, and the reason printed.
  echo "  !! no platform IR at '$JDK_IR' — the \`axiom\` (source + platform IR) row is not produced; set AXIOM_JDK_IR"
else
  solve "axiom" "$JDK_IR${STUB_IR:+,$STUB_IR}" "platform IR modules staged: $mods" "source + platform IR"
fi

solve "axiom-nolib" "${STUB_IR:-$EMPTY_LIB}" "platform IR modules staged: 0" "source only"
