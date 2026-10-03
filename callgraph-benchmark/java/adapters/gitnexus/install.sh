#!/usr/bin/env bash
# Pinned, isolated under .tools/node/gitnexus, and pinned ALL THE WAY DOWN — see
# adapters/codegraph/install.sh for the reasoning, and #103. `npm ci` installs exactly the
# committed package-lock.json and refuses to update it.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"   # the REPOSITORY root, three levels up (issue #31)
VERSION="${GITNEXUS_VERSION:-1.6.11}"

# The lock is the record of what ran, so it may not be silently bypassed: asking for a version the
# lock does not describe is an error, not an unpinned install.
node -e 'const [v, f] = process.argv.slice(1); const want = require(f).dependencies["gitnexus"];
         if (want !== v) { console.error(`GITNEXUS_VERSION=${v} is not what ${f} pins (${want}) — regenerate the lock`); process.exit(1); }' \
     "$VERSION" "$HERE/package.json"

DIR="$ROOT/.tools/node/gitnexus"
mkdir -p "$DIR"
cp "$HERE/package.json" "$HERE/package-lock.json" "$DIR/"
cd "$DIR"
npm ci --no-audit --no-fund
node -e "console.log(require('$DIR/node_modules/gitnexus/package.json').version)"
