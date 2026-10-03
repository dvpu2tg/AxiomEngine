#!/usr/bin/env bash
# One-time cost, paid BEFORE the timed run (issues #42, #8): node module load, grammar / WASM
# initialisation, venv import — the tool's first-run start-up, which used to land inside the
# first subject's `seconds`. Runs the adapter on a one-file stub into a scratch work dir.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"
W="$ROOT/.work/typescript/_warm/code_review_graph"; rm -rf "$W"; mkdir -p "$W/src"
printf "export class A { f(): number { return 1; } }\nexport function g(a: A): number { return a.f(); }\n" > "$W/src/a.ts"
if WORK="$W" bash "$LANG_DIR/adapters/code_review_graph/run.sh" "$LANG_DIR" warm "$W/src" > "$W/warm.log" 2>&1; then echo "cache=warmed"; else echo "cache=failed"; fi
