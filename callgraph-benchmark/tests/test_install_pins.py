"""Every tool under test is installed from a committed lock (#103).

A version number on the tool is not a pin. `code-review-graph==2.3.8` pulled tree-sitter and
tree-sitter-language-pack unbounded, and for a tree-sitter indexer the grammar version IS the
analyser: 13 of 15 dev subjects moved between the committed scores and a clean install, on a
constant tool version. A benchmark that reports a tool's score must be able to say WHICH tool, and
"which tool" is the whole closure.

So each installer's closure is resolved once, committed beside it, and installed verbatim — and
these tests are the gate that keeps it that way, because an unpinned dependency reintroduced later
produces no error, only numbers that quietly stop reproducing.

`java/adapters/codeql/ql/codeql-pack.lock.yml` is the precedent: that adapter has committed its
resolved pack versions from the start. The four package-manager installs had not.
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTERS = ROOT / "java" / "adapters"

# tool directory -> (lock file, the package the tool IS, the version install.sh defaults to)
PINNED = {
    "code_review_graph": ("requirements.lock", "code-review-graph", "2.3.8"),
    "graphify":          ("requirements.lock", "graphifyy", "0.9.58"),
    "codegraph":         ("package-lock.json", "@colbymchenry/codegraph", "1.6.0"),
    "gitnexus":          ("package-lock.json", "gitnexus", "1.6.11"),
}

# The dependencies the issue names, per tool: unbounded, and decisive for what gets extracted.
# Listed by name so the test says what it is protecting rather than only counting.
MUST_BE_PINNED = {
    "code_review_graph": ("tree-sitter", "tree-sitter-language-pack", "networkx", "pyyaml",
                          "watchdog", "fastmcp", "mcp"),
    "graphify":          ("tree-sitter", "tree-sitter-java", "tree-sitter-typescript", "networkx"),
}

# name==version, optionally with an environment marker. Anything else — >=, ~=, <, a bare name, a
# URL — is a dependency the resolver still gets to choose.
PIN_RE = re.compile(r"^[A-Za-z0-9._-]+==[^\s;]+(\s*;.*)?$")


def script_body(sh: Path) -> str:
    """The installer's executable lines. The comments above them explain the pinning at length and
    quote the unpinned commands they replaced, so a grep over the whole file reads its own prose."""
    return "\n".join(ln for ln in sh.read_text(encoding="utf-8").splitlines()
                      if not ln.lstrip().startswith("#"))


def requirement_lines(lock: Path) -> list[str]:
    out = []
    for ln in lock.read_text(encoding="utf-8").splitlines():
        ln = ln.split("#", 1)[0].strip() if not ln.lstrip().startswith("#") else ""
        if ln:
            out.append(ln)
    return out


def pinned_names(lock: Path) -> dict[str, set[str]]:
    """package -> the versions the lock allows. More than one is legitimate where the versions are
    split by an environment marker; the point is that the set is closed."""
    got: dict[str, set[str]] = {}
    for ln in requirement_lines(lock):
        name, _, rest = ln.partition("==")
        got.setdefault(name.strip().lower(), set()).add(rest.split(";")[0].strip())
    return got


class EveryInstallerHasALock(unittest.TestCase):
    def test_the_lock_exists_beside_its_installer(self):
        for tool, (lock, _pkg, _ver) in PINNED.items():
            with self.subTest(tool=tool):
                self.assertTrue((ADAPTERS / tool / "install.sh").is_file())
                self.assertTrue((ADAPTERS / tool / lock).is_file(),
                                f"{tool} installs a tool with no committed lock")

    def test_the_lock_names_the_version_the_installer_defaults_to(self):
        """A lock that describes a different version than the one the installer asks for is worse
        than no lock: it reads as a record of a run that never happened."""
        for tool, (lock, pkg, ver) in PINNED.items():
            with self.subTest(tool=tool):
                sh = script_body(ADAPTERS / tool / "install.sh")
                self.assertIn(f":-{ver}}}", sh, f"{tool}/install.sh does not default to {ver}")
                p = ADAPTERS / tool / lock
                if lock == "requirements.lock":
                    self.assertEqual(pinned_names(p).get(pkg.lower()), {ver})
                else:
                    self.assertEqual(
                        json.loads(p.read_text())["packages"][""]["dependencies"][pkg], ver)


class NothingIsResolvedAtInstallTime(unittest.TestCase):
    """The installer may not ask a package manager to choose a version. That choice is what the
    lock already made, and re-making it on a cloud VM months later is exactly the defect."""

    def test_pip_installs_the_lock_and_only_the_lock(self):
        for tool in ("code_review_graph", "graphify"):
            with self.subTest(tool=tool):
                sh = script_body(ADAPTERS / tool / "install.sh")
                self.assertIn("--no-deps -r", sh, "pip may still resolve dependencies")
                self.assertIn("requirements.lock", sh)
                # `pip check` is what makes --no-deps safe: it proves the committed closure is
                # complete instead of leaving a missing dependency to surface as a crash mid-run.
                self.assertRegex(sh, r"pip\" check")
                self.assertNotRegex(sh, r"pip\" install [^\n]*[\"']?[A-Za-z0-9._-]+==")

    def test_npm_installs_the_lock_and_refuses_to_update_it(self):
        for tool in ("codegraph", "gitnexus"):
            with self.subTest(tool=tool):
                sh = script_body(ADAPTERS / tool / "install.sh")
                self.assertIn("npm ci", sh)
                self.assertNotRegex(sh, r"npm install\b")

    def test_each_npm_tool_installs_into_its_own_prefix(self):
        """They shared one `.tools/node`, and npm hoists and dedupes across a whole tree — so
        installing the second tool could move the first tool's transitive versions. Two locks
        cannot describe one shared node_modules."""
        dirs = {tool: re.search(r'DIR="([^"]+)"',
                                script_body(ADAPTERS / tool / "install.sh")).group(1)
                for tool in ("codegraph", "gitnexus")}
        self.assertEqual(len(set(dirs.values())), 2, dirs)
        for tool, d in dirs.items():
            self.assertTrue(d.endswith(f"/.tools/node/{tool}"), d)


class EveryDependencyIsPinned(unittest.TestCase):
    def test_every_python_requirement_is_an_exact_version(self):
        for tool in ("code_review_graph", "graphify"):
            with self.subTest(tool=tool):
                lines = requirement_lines(ADAPTERS / tool / "requirements.lock")
                self.assertGreater(len(lines), 10, "that is not a closure")
                for ln in lines:
                    self.assertRegex(ln, PIN_RE, f"{tool}: unpinned requirement {ln!r}")

    def test_every_npm_package_is_pinned_and_hashed(self):
        """A version alone still lets a republished tarball through; `integrity` is what makes the
        lock a statement about bytes."""
        for tool in ("codegraph", "gitnexus"):
            with self.subTest(tool=tool):
                lock = json.loads((ADAPTERS / tool / "package-lock.json").read_text())
                self.assertGreaterEqual(lock["lockfileVersion"], 2)
                pkgs = {k: v for k, v in lock["packages"].items() if k}
                self.assertGreater(len(pkgs), 1, "that is not a closure")
                for path, entry in pkgs.items():
                    self.assertRegex(entry.get("version", ""), r"^\d+\.\d+\.\d+",
                                     f"{tool}: {path} has no exact version")
                    self.assertIn("resolved", entry, f"{tool}: {path} has no resolved URL")
                    self.assertIn("integrity", entry, f"{tool}: {path} has no integrity hash")

    def test_the_dependencies_the_issue_names_are_in_the_lock(self):
        """The grammar versions decide which calls are extracted at all, so these in particular are
        never allowed back out of the lock."""
        for tool, names in MUST_BE_PINNED.items():
            got = pinned_names(ADAPTERS / tool / "requirements.lock")
            for name in names:
                with self.subTest(tool=tool, dep=name):
                    self.assertIn(name, got, f"{tool} no longer pins {name}")
                    for v in got[name]:
                        self.assertRegex(v, r"^\d+\.\d+")


if __name__ == "__main__":
    unittest.main()
