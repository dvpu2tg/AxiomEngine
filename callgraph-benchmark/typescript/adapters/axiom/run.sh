#!/usr/bin/env bash
# axiom-code-graph, TypeScript front end.
#
# ONE CONFIGURATION, not two. The Java runs are split into `axiom` and `axiom-nolib` because the
# platform IR is a type oracle the source-reading tools do not get. TypeScript has no equivalent
# staged platform IR in this pipeline — `--library` is empty — so there is only one row and no
# staging advantage to disclose.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"; SRC="${3:-}"
PARSER="${AXIOM_PARSER:?}"; ENGINE="${AXIOM_ENGINE:?}"
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

W="$WORK/axiom"; rm -rf "$W"; mkdir -p "$W/emptylib"
# timing PARTS (issue #8): `adapter<TAB>label<TAB>phase<TAB>seconds` — `shared` is paid by every
# label of this adapter, `own:<label>` by one, `staging` is harness cost billed to nobody
_T0() { python3 -c 'import time;print(time.time())'; }
_EL() { python3 -c "import time;print(round(time.time()-$1,2))"; }
tpart() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> "$WORK/timings-parts.tsv"; }
P0=$(_T0)
node "$PARSER" "$SRC" "$SUBJECT-ts" false "$W/ir" > "$W/parse.log" 2>&1 || {
  echo "  !! parse failed"; tail -5 "$W/parse.log"; exit 1; }
tpart axiom axiom shared "$(_EL $P0)"
S0=$(_T0)
bash "$RUN_SOUFFLE" --language typescript --debug \
     --client-ir "$W/ir" --library "$W/emptylib" \
     --intermediate "$W/int" --output "$W/out" > "$W/solve.log" 2>&1 || {
  echo "  !! solve failed"; tail -5 "$W/solve.log"; exit 1; }
tpart axiom axiom own:axiom "$(_EL $S0)"
python3 "$LANG_DIR/adapters/axiom/adapt.py" --ir "$W/ir" --out "$W/out" \
    --subject "$SUBJECT" --label axiom --meta "typescript front end, empty library" \
    --parser-commit "$PARSER_COMMIT" --engine-commit "$ENGINE_COMMIT" \
    --build "source only" \
    --edges "$WORK/edges/axiom/$SUBJECT.jsonl"
