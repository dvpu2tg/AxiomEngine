#!/usr/bin/env bash
# The CHA null model: the whole envelope at every site, no resolution. A floor, never a competitor.
# Given the oracle's own answer on purpose — it should be beaten on sharpness, not on coverage.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"
python3 "$ROOT/bench/null_model.py" --sites "$WORK/gt.sites.jsonl" --subject "$SUBJECT" \
  --edges "$WORK/edges/cha-null/$SUBJECT.jsonl"
# The other end of the bracket: the correct answer for every link group. A ceiling, never ranked.
python3 "$ROOT/bench/null_model.py" --sites "$WORK/gt.sites.jsonl" --subject "$SUBJECT" --ideal \
  --label ideal --edges "$WORK/edges/ideal/$SUBJECT.jsonl"
