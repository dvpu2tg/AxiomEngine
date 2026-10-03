#!/usr/bin/env bash
# One-time cost, paid BEFORE the timed run (issues #42, #8): node module load, grammar / WASM
# initialisation, venv import — the tool's first-run start-up, which used to land inside the
# first subject's `seconds`. Runs the adapter on a one-file stub into a scratch work dir.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"
W="$ROOT/.work/java/_warm/graphify"; rm -rf "$W"; mkdir -p "$W/src"
mkdir -p "$W/src/w"; printf "package w;\npublic class A { int f() { return 1; } static int g(A a) { return a.f(); } }\n" > "$W/src/w/A.java"
if WORK="$W" bash "$LANG_DIR/adapters/graphify/run.sh" "$LANG_DIR" warm "$W/src" > "$W/warm.log" 2>&1; then echo "cache=warmed"; else echo "cache=failed"; fi
