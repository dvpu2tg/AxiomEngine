#!/usr/bin/env bash
# The TypeScript adapter shares the Java one's installation: one tool, one .tools/ (issue #31).
exec bash "$(cd "$(dirname "$0")/../../../java/adapters/graphify" && pwd)/install.sh" "$@"
