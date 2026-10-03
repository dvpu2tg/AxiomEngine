#!/usr/bin/env bash
# The unit tests under tests/: one filed issue's edge case each, reduced to a handful of methods.
# Run by both runners as a gate before any subject is scored, and on its own:
#     bash bench/test.sh
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests -t . -p 'test_*.py' "$@"
