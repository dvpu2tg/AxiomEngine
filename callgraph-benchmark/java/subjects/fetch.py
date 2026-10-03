#!/usr/bin/env python3
"""Fetch a Maven subject: the project's own published jar, and the sources that produced it.

    python3 subjects/fetch.py netty-transport [--record-hashes]

WHY THE PUBLISHED ARTEFACT RATHER THAN A BUILD
----------------------------------------------
For the torture subject the harness compiles the source itself, which is fine for 592 lines it also
wrote. At scale that becomes a liability: compiling a real project with our JDK, our flags and our
compiler produces bytecode that is *not* the bytecode the project ships, and every difference —
a changed `-parameters`, a different `-source` level, ecj instead of javac — lands in the ground
truth as a fact about the project. It also makes the subject reproducible only for someone who can
make that project's build work.

So the oracle reads `<artifact>.jar` — the bytecode the maintainers built and released — and the
tools read `<artifact>-sources.jar` from the same coordinate. Maven Central guarantees the two come
from one release. `run/subject.sh` still *checks* that guarantee (gate 4) rather than assuming it,
because a subject where the source and the bytecode disagree would score every tool for code it
never saw.

Both files are pinned by SHA-256. A changed hash under a fixed coordinate stops the run: it means
the artefact moved, and a benchmark whose inputs can move silently is not reproducible.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

CENTRAL = "https://repo1.maven.org/maven2"
LANG_DIR = Path(__file__).resolve().parents[1]     # java/ or typescript/
ROOT = LANG_DIR.parent


def load_registry() -> dict:
    return json.loads((LANG_DIR / "subjects" / "registry.json").read_text(encoding="utf-8"))


def find(registry: dict, name: str) -> dict:
    for s in registry["subjects"]:
        if s["name"] == name:
            return s
    raise SystemExit(f"unknown subject {name!r}; known: "
                     + ", ".join(s["name"] for s in registry["subjects"]))


def urls(coordinate: str) -> tuple[str, str, str]:
    group, artifact, version = coordinate.split(":")
    base = f"{CENTRAL}/{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}"
    return f"{base}.jar", f"{base}-sources.jar", f"{artifact}-{version}"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(url: str, dest: Path) -> None:
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"  fetching {url}", file=sys.stderr)
    with urllib.request.urlopen(url, timeout=180) as r, tmp.open("wb") as out:
        shutil.copyfileobj(r, out)
    tmp.replace(dest)


def unzip(jar: Path, dest: Path, suffix: str) -> int:
    """Extract entries ending in `suffix`. Returns the count.

    Paths are sanitised: a zip entry may name `../` and a benchmark that unpacked one would be a
    remote-code-execution bug rather than a measurement.
    """
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    n = 0
    with zipfile.ZipFile(jar) as z:
        for info in z.infolist():
            if info.is_dir() or not info.filename.endswith(suffix):
                continue
            target = (dest / info.filename).resolve()
            if not str(target).startswith(str(dest.resolve())):
                raise SystemExit(f"refusing to extract {info.filename!r} outside {dest}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)
            n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("subject")
    ap.add_argument("--record-hashes", action="store_true",
                    help="write the observed SHA-256 into the registry (first fetch only)")
    a = ap.parse_args()

    registry = load_registry()
    s = find(registry, a.subject)
    if s["kind"] != "maven":
        print(f"{a.subject} is a {s['kind']} subject; nothing to fetch", file=sys.stderr)
        return 0

    jar_url, src_url, stem = urls(s["coordinate"])
    cache = ROOT / ".subjects" / LANG_DIR.name / a.subject
    jar = cache / f"{stem}.jar"
    src = cache / f"{stem}-sources.jar"
    download(jar_url, jar)
    download(src_url, src)

    observed = {"jar": sha256(jar), "sources": sha256(src)}
    recorded = s.get("sha256")
    if recorded and not a.record_hashes:
        for k, want in recorded.items():
            if observed[k] != want:
                raise SystemExit(
                    f"SHA-256 MISMATCH for {a.subject} {k}\n"
                    f"  recorded {want}\n  observed {observed[k]}\n"
                    f"The artefact changed under a fixed coordinate. Refusing to score against it.")
        print(f"  hashes verified ({a.subject})", file=sys.stderr)
    elif a.record_hashes:
        s["sha256"] = observed
        (LANG_DIR / "subjects" / "registry.json").write_text(
            json.dumps(registry, indent=2) + "\n", encoding="utf-8")
        print(f"  recorded hashes for {a.subject}", file=sys.stderr)
    else:
        # FAIL CLOSED. The first fetch used to define the reference hash (trust on first use,
        # issue #38); a subject with no recorded hash is now refused until one is recorded on
        # purpose, in a commit that says so.
        raise SystemExit(f"NO HASHES RECORDED for {a.subject} — refusing to score an unpinned "
                         f"artefact. Record them deliberately: fetch.py {a.subject} --record-hashes")

    classes = cache / "classes"
    sources = cache / "sources"
    nc = unzip(jar, classes, ".class")
    ns = unzip(src, sources, ".java")
    print(f"  {a.subject}: {nc} class files, {ns} source files", file=sys.stderr)

    (cache / "meta.json").write_text(json.dumps({
        "subject": a.subject,
        "coordinate": s["coordinate"],
        "jar_url": jar_url,
        "sources_url": src_url,
        "sha256": observed,
        "class_files": nc,
        "source_files": ns,
    }, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
