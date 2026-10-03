#!/usr/bin/env bash
# Pinned TypeScript toolchain for the oracle. The checker's VERSION is part of the ground truth —
# a different tsc can resolve an overload differently — so it is pinned and recorded, not floated.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/.tools/ts"
cd "$ROOT/.tools/ts"
cat > package.json <<'JSON'
{"name":"bench-ts-oracle","private":true,"type":"module",
 "dependencies":{"typescript":"5.6.3","tsx":"4.19.2"}}
JSON
npm install --no-audit --no-fund
