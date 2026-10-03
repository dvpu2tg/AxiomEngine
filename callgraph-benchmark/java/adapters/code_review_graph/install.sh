#!/usr/bin/env bash
# Pinned, isolated, and pinned ALL THE WAY DOWN. A benchmark that reports a tool's score must be
# able to say WHICH tool — and "which tool" is not one version number. code-review-graph requires
# tree-sitter and tree-sitter-language-pack unbounded, and the grammar versions decide which calls
# are extracted at all, so a run pinned only at the top resolved a different analyser every month
# and the committed scores did not reproduce (#103).
#
# requirements.lock beside this file is the full closure, resolved once and committed. --no-deps
# installs exactly it and nothing else; `pip check` then proves the closure is complete, so a
# dependency that appears in a future release is a loud failure here rather than a silent float.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"   # the REPOSITORY root, three levels up (issue #31)
VERSION="${CRG_VERSION:-2.3.8}"
LOCK="$HERE/requirements.lock"

# The lock is the record of what ran, so it may not be silently bypassed: asking for a version the
# lock does not describe is an error, not an unpinned install.
grep -qx "code-review-graph==$VERSION" "$LOCK" || {
  echo "CRG_VERSION=$VERSION is not what $LOCK pins — regenerate the lock (see its header)" >&2
  exit 1; }

python3 -m venv --clear "$ROOT/.tools/crg-venv"
"$ROOT/.tools/crg-venv/bin/pip" install -q --disable-pip-version-check --no-deps -r "$LOCK"
"$ROOT/.tools/crg-venv/bin/pip" check
"$ROOT/.tools/crg-venv/bin/code-review-graph" --version 2>&1 | head -1
