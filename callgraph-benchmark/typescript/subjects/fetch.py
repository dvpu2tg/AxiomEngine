#!/usr/bin/env python3
"""Fetch a TypeScript subject: the repository at a pinned commit.

    python3 typescript/subjects/fetch.py typedoc [--record-hashes]

WHY A REPOSITORY AND NOT A PUBLISHED ARTEFACT
---------------------------------------------
The Java side reads the project's own published jar, which removes every difference between our
build and theirs. TypeScript has no such artefact: npm ships `.js` and `.d.ts`, and the tools under
test read `.ts`. So the reproducible form is the repository at a fixed commit, fetched as a tarball
and pinned by SHA-256 — a changed hash under a fixed commit stops the run.

NODE_MODULES ARE NOT INSTALLED, DELIBERATELY
--------------------------------------------
Installing a project's dependencies would make the subject depend on a package manager, a lockfile
that may no longer resolve, and a network. It would also not change what is being measured: calls
into a dependency are BOUNDARY calls, scored against nothing, exactly as they are for the Java Maven
subjects whose dependencies are equally absent.

What it does change is how much the checker can resolve, and that is not left to assumption —
`--mode coverage` reports the fraction of call expressions the checker could resolve at all, and the
runner refuses to score a subject whose coverage is too low. A subject the checker cannot read is
measuring the staging, not the tools.
"""
from __future__ import annotations

import argparse, hashlib, io, json, shutil, sys, tarfile, urllib.request
from pathlib import Path

LANG_DIR = Path(__file__).resolve().parents[1]
ROOT = LANG_DIR.parent


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("subject")
    ap.add_argument("--record-hashes", action="store_true")
    a = ap.parse_args()

    regp = LANG_DIR / "subjects" / "registry.json"
    reg = json.loads(regp.read_text(encoding="utf-8"))
    s = next((x for x in reg["subjects"] if x["name"] == a.subject), None)
    if s is None:
        raise SystemExit(f"unknown subject {a.subject!r}")
    if s["kind"] != "github":
        print(f"{a.subject} is a {s['kind']} subject; nothing to fetch", file=sys.stderr)
        return 0
    if not s.get("commit"):
        raise SystemExit(f"{a.subject} has no pinned commit in the registry — pin one first")

    slug = s["repo"].removeprefix("https://github.com/").removesuffix(".git")
    url = f"https://codeload.github.com/{slug}/tar.gz/{s['commit']}"
    cache = ROOT / ".subjects" / "typescript" / a.subject
    cache.mkdir(parents=True, exist_ok=True)
    tgz = cache / f"{s['commit'][:12]}.tar.gz"

    if not tgz.exists():
        print(f"  fetching {url}", file=sys.stderr)
        tmp = tgz.with_suffix(".part")
        with urllib.request.urlopen(url, timeout=300) as r, tmp.open("wb") as out:
            shutil.copyfileobj(r, out)
        tmp.replace(tgz)

    observed = sha256(tgz)
    recorded = s.get("sha256")
    if recorded and not a.record_hashes:
        if observed != recorded:
            raise SystemExit(f"SHA-256 MISMATCH for {a.subject}\n  recorded {recorded}\n"
                             f"  observed {observed}\nRefusing to score against a changed artefact.")
        print(f"  hash verified ({a.subject})", file=sys.stderr)
    elif a.record_hashes:
        s["sha256"] = observed
        regp.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
        print(f"  recorded hash for {a.subject}", file=sys.stderr)

    src = cache / "src"
    if not src.exists():
        with tarfile.open(tgz) as tf:
            members = tf.getmembers()
            top = members[0].name.split("/")[0]
            stage = cache / "_stage"
            if stage.exists():
                shutil.rmtree(stage)
            # `filter="data"` refuses absolute paths, `..` escapes and device nodes. A benchmark
            # that unpacked a hostile tarball would be a remote-code-execution bug, not a metric.
            tf.extractall(stage, filter="data")
            (stage / top).rename(src)
            shutil.rmtree(stage, ignore_errors=True)

    sub = src / s.get("path", ".")
    n = sum(1 for _ in sub.rglob("*.ts"))
    print(f"  {a.subject}: {n} .ts files under {s.get('path', '.')}", file=sys.stderr)
    (cache / "meta.json").write_text(json.dumps({
        "subject": a.subject, "repo": s["repo"], "commit": s["commit"],
        "sha256": observed, "ts_files": n,
        "prior_internal_use": s.get("prior_internal_use", False),
    }, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
