#!/usr/bin/env bash
# Pinned ALL THE WAY DOWN, and isolated under .tools/ like every other tool (issue #31).
#
# `uv tool install graphifyy==<version>` pinned one package and floated the twenty-odd tree-sitter
# grammars under it — and for a tree-sitter extractor the grammar version IS the analyser (#103).
# requirements.lock beside this file is the full closure, resolved once and committed; --no-deps
# installs exactly it and nothing else, and `pip check` then proves the closure is complete.
#
# It also moves out of `uv tool`'s shared `~/.local` into `$ROOT/.tools/graphify-venv`, so the
# install is per-checkout and cannot be a stale global left over from another benchmark — the same
# reason code-review-graph has its own venv. `run.sh` still honours $GRAPHIFY.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"   # the REPOSITORY root, three levels up (issue #31)
VERSION="${GRAPHIFY_VERSION:-0.9.58}"
LOCK="$HERE/requirements.lock"
VENV="$ROOT/.tools/graphify-venv"

# The lock is the record of what ran, so it may not be silently bypassed: asking for a version the
# lock does not describe is an error, not an unpinned install.
grep -qx "graphifyy==$VERSION" "$LOCK" || {
  echo "GRAPHIFY_VERSION=$VERSION is not what $LOCK pins — regenerate the lock (see its header)" >&2
  exit 1; }

python3 -m venv --clear "$VENV"
"$VENV/bin/pip" install -q --disable-pip-version-check --no-deps -r "$LOCK"
"$VENV/bin/pip" check
"$VENV/bin/python" -c "import importlib.metadata as m; print('graphifyy', m.version('graphifyy'))"
