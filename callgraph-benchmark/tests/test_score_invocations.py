"""The three places that call bench/run.py must hand it the same inputs.

`subject.sh` scores a subject, `rescore.sh` re-scores it from disk, and `verify.sh` gate 2 re-scores
it to prove the scorer is deterministic. A flag added to one and not the others is silent: #105
gave `subject.sh` and `rescore.sh` `--anonmap` and not `verify.sh`, so gate 2 compared a score made
with the compiler's names against one made without them and would report the HARNESS as
non-deterministic; `--prior-internal-use` reached only `subject.sh`, so a re-score silently dropped
the disclosure that a subject is in the tool's own development corpus.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_py_flags(script: Path) -> set[str]:
    text = script.read_text(encoding="utf-8")
    start = text.index("python3 bench/run.py")
    call = []
    for line in text[start:].splitlines():
        call.append(line)
        if not line.rstrip().endswith("\\"):
            break
    flags = set(re.findall(r"--[a-z][a-z-]+", "\n".join(call)))
    # rescore.sh builds the TypeScript-only flags in $EXTRA; they are part of its call
    if "$EXTRA" in "\n".join(call):
        extra = re.search(r'EXTRA="(--defaults[^"]*)"', text)
        flags |= set(re.findall(r"--[a-z][a-z-]+", extra.group(1))) if extra else set()
    return flags


class ScoreInvocations(unittest.TestCase):
    def test_java_subject_and_verify_agree(self):
        self.assertEqual(run_py_flags(ROOT / "java/run/subject.sh"),
                         run_py_flags(ROOT / "java/run/verify.sh"))

    def test_typescript_subject_and_verify_agree(self):
        self.assertEqual(run_py_flags(ROOT / "typescript/run/subject.sh"),
                         run_py_flags(ROOT / "typescript/run/verify.sh"))

    def test_rescore_covers_both_languages(self):
        ts = run_py_flags(ROOT / "typescript/run/subject.sh")
        java = run_py_flags(ROOT / "java/run/subject.sh")
        self.assertEqual(run_py_flags(ROOT / "bench/rescore.sh"), ts | java,
                         "rescore.sh must pass every flag either runner passes")


if __name__ == "__main__":
    unittest.main()
