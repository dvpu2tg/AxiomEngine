#!/usr/bin/env bash
# Pinned, isolated under .tools/node/codegraph — never installed globally, so the version the
# report names is the version that ran.
#
# PINNED ALL THE WAY DOWN (#103). `npm install <pkg>@<version>` pins one package and floats every
# package under it; `npm ci` installs exactly the committed package-lock.json and refuses to update
# it, so the tree the tool is analysed with is the tree the lock names.
#
# Each npm tool also gets its OWN directory. They shared one .tools/node, and npm hoists and dedupes
# across everything in a tree — so installing the second tool could quietly move the first tool's
# transitive versions, which is the same defect one level up.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"   # the REPOSITORY root, three levels up (issue #31)
VERSION="${CODEGRAPH_VERSION:-1.6.0}"

# The lock is the record of what ran, so it may not be silently bypassed: asking for a version the
# lock does not describe is an error, not an unpinned install.
node -e 'const [v, f] = process.argv.slice(1); const want = require(f).dependencies["@colbymchenry/codegraph"];
         if (want !== v) { console.error(`CODEGRAPH_VERSION=${v} is not what ${f} pins (${want}) — regenerate the lock`); process.exit(1); }' \
     "$VERSION" "$HERE/package.json"

DIR="$ROOT/.tools/node/codegraph"
mkdir -p "$DIR"
cp "$HERE/package.json" "$HERE/package-lock.json" "$DIR/"
cd "$DIR"
npm ci --no-audit --no-fund
node -e "console.log(require('$DIR/node_modules/@colbymchenry/codegraph/package.json').version)"
