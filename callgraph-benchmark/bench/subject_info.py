#!/usr/bin/env python3
"""Resolve a subject from the registry into the paths `run/subject.sh` needs.

Emits shell assignments so the runner stays a shell script and the registry stays one JSON file:

    eval "$(python3 bench/subject_info.py netty-transport)"

The HELD-OUT guard lives here rather than in the runner, because it is the one rule that must not be
bypassable by editing a shell loop: a held-out subject resolves only when `--allow-heldout` is
passed, and the runner passes it only for an explicit `--heldout` on the command line. The split is
worth nothing if it can be crossed by accident.
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("subject")
    ap.add_argument("--language", default="java")
    ap.add_argument("--allow-heldout", action="store_true")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    lang_dir = ROOT / a.language
    reg = json.loads((lang_dir / "subjects" / "registry.json").read_text(encoding="utf-8"))
    if a.list:
        for s in reg["subjects"]:
            print(f"{s['name']}\t{s['split']}\t{s['kind']}\t{s.get('coordinate', '-')}")
        return 0

    s = next((x for x in reg["subjects"] if x["name"] == a.subject), None)
    if s is None:
        print(f"unknown subject {a.subject!r}", file=sys.stderr)
        return 2

    if s["split"] == "blocked":
        print(f"refusing: {a.subject} is BLOCKED — {s.get('description','')}", file=sys.stderr)
        return 4
    if s["split"] == "heldout" and not a.allow_heldout:
        print(
            f"refusing: {a.subject} is HELD OUT.\n"
            f"  A held-out subject is scored once, and a bad result there is a finding to report,\n"
            f"  not a rule to adjust. Pass --heldout to run/subject.sh if that is what you intend.",
            file=sys.stderr)
        return 3

    cache = ROOT / ".subjects" / a.language / a.subject
    out = {
        "SUBJECT": s["name"],
        "LANGUAGE": a.language,
        "LANG_DIR": str(lang_dir),
        "SPLIT": s["split"],
        "KIND": s["kind"],
        "COORDINATE": s.get("coordinate", ""),
        "FAMILIES": "1" if s.get("families") else "",
        "INCLUDE_PREFIX": ",".join(s.get("include_prefix", [])),
    }
    out["PRIOR_INTERNAL_USE"] = "1" if s.get("prior_internal_use") else ""
    if s["kind"] == "github":
        # `path` is the SOURCE SUBTREE both sides read; `project` is the tsconfig, relative to the
        # repository root. They are separate because a project's config commonly sits at the root
        # while its sources sit under src/ — and pointing the tools at the root while the checker
        # loads only src/ is precisely what gate 4 refuses.
        repo = cache / "src"
        out["SRC_DIR"] = str(repo / s.get("path", "."))
        out["PROJECT_PATH"] = str(repo / s["project"])
        # A registry entry may carry `project_overrides` — an `exclude` list and/or compilerOptions
        # (a `paths` mapping to a declaration file the repository ships) — which the runner writes
        # into a config beside the original that `extends` it. Both the oracle and the tools read
        # the derived config. ts-morph clears gate 0 with `exclude: ["src/tests"]` (issue #28).
        if s.get("project_overrides"):
            out["PROJECT_OVERRIDES"] = json.dumps(s["project_overrides"], separators=(",", ":"))
        out["CLASSES_DIR"] = ""
        out["CP_DIR"] = ""
        out["NEEDS_FETCH"] = "1"
        out["NEEDS_COMPILE"] = ""
    elif s["kind"] == "maven":
        out["SRC_DIR"] = str(cache / "sources")
        out["CLASSES_DIR"] = str(cache / "classes")
        out["NEEDS_FETCH"] = "1"
        out["NEEDS_COMPILE"] = ""
        out["CP_DIR"] = ""
    else:
        out["SRC_DIR"] = str(lang_dir / s["source_roots"][0])
        out["PROJECT_FILE"] = s.get("project", "")
        out["CLASSES_DIR"] = str(ROOT / ".work" / a.language / a.subject / "client-classes")
        out["CP_SRC_DIR"] = str(lang_dir / s["classpath_roots"][0]) if s.get("classpath_roots") else ""
        out["CP_DIR"] = str(ROOT / ".work" / a.language / a.subject / "lib-classes")
        out["NEEDS_FETCH"] = ""
        out["NEEDS_COMPILE"] = "1"

    out["WORK"] = str(ROOT / ".work" / a.language / a.subject)
    out["RESULTS"] = str(lang_dir / "results" / a.subject)

    for k, v in out.items():
        # POSIX separators: the only consumers are the shell runners, whose `sed "s|^$SRC_DIR/||"`
        # read every backslash of a Windows path as an escape and gate 4 refused torture (#54)
        print(f"{k}={shlex.quote(v.as_posix() if isinstance(v, Path) else str(v).replace(chr(92), '/'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
