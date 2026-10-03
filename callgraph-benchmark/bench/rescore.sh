#!/usr/bin/env bash
# Re-score ONE subject from what is already on disk — the ground truth under .work/ and every
# tool's canonical edge file — without re-running the oracle, the gates or any tool.
#
#     bash bench/rescore.sh java maven-core
#     bash bench/rescore.sh typescript kysely
#
# The three speeds, slowest last:
#   bash bench/test.sh                          unit tests, seconds — after EVERY change
#   bash bench/rescore.sh <lang> <subject>      scorer / resolver / report change, seconds to minutes
#   TOOLS=cha bash <lang>/run/subject.sh <s>    oracle change: ground truth + gates, tools kept
#   bash <lang>/run/subject.sh <s>              adapter or tool change: everything (final benchmarking)
#   bash <lang>/run/verify.sh <s>               before a number is cited
set -euo pipefail
export LC_ALL=C
cd "$(dirname "$0")/.."
LANGUAGE="${1:?java|typescript}"; SUBJECT="${2:?subject}"
INFO="$(python3 bench/subject_info.py "$SUBJECT" --language "$LANGUAGE" --allow-heldout)"; eval "$INFO"
W="$WORK"; EDGES="$W/edges"
[ -f "$W/gt.sites.jsonl" ] || { echo "no ground truth under $W — run $LANGUAGE/run/subject.sh $SUBJECT first"; exit 2; }
FAM=""; [ -n "${FAMILIES:-}" ] && FAM="--families"
EXTRA=""
if [ "$LANGUAGE" = typescript ]; then
  SUBJECT_SUBDIR="$(cat "$W/subject-subdir.txt" 2>/dev/null || true)"
  EXTRA="--defaults $W/gt.defaults.txt --coverage $W/coverage.txt --staged-copy $W/staged-copy.txt ${PRIOR_INTERNAL_USE:+--prior-internal-use} ${SUBJECT_SUBDIR:+--module-prefix $SUBJECT_SUBDIR/}"
fi
python3 bench/run.py --subject "$SUBJECT" --language "$LANGUAGE" \
  --sites "$W/gt.sites.jsonl" --classes "$W/gt.classes.txt" --methods "$W/gt.methods.txt" \
  --excluded "$W/gt.excluded.txt" --heritage "$W/gt.heritage.txt" --anonmap "$W/gt.anonmap.txt" \
  --edges-dir "$EDGES" --source "$SRC_DIR" \
  --timings "$W/timings.tsv" --warmup "$W/warmup.tsv" --timing-parts "$W/timings-parts.tsv" --out "$RESULTS" $EXTRA $FAM
