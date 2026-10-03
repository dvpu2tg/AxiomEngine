"""Small synthetic ground truths for the scorer and resolver tests.

Every regression here is one filed issue's edge case, reduced to a handful of methods so the test
runs in milliseconds and the expected verdict can be read off the fixture. The real subjects are
exercised by the gates in `<lang>/run/subject.sh`; these are the unit level under them.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))

import groundtruth as G   # noqa: E402
import language as L      # noqa: E402
import resolve as R       # noqa: E402
import score as S         # noqa: E402
from model import Edge, Ref, Tier, ToolOutput   # noqa: E402


def site(caller: str, line: int, name: str, *, certain=(), possible=(), rta=None, ancestors=(),
         kind: str = "internal", op: str = "INVOKEVIRTUAL", recv: str = "", params=()) -> dict:
    possible = list(possible)
    return {
        "site_id": f"{caller}@{line}#0", "caller": caller, "line": line, "seq": 0, "op": op,
        "receiver_static_type": recv or caller.split("#", 1)[0], "callee_name": name,
        "callee_params": list(params), "kind": kind, "certain": list(certain), "possible": possible,
        "possible_rta": list(possible if rta is None else rta), "declaring_ancestors": list(ancestors),
        "unique": len(possible) == 1, "unique_rta": len(possible if rta is None else rta) == 1,
    }


class Fixture:
    """Write a ground truth to a temp dir and build the resolver the harness would build."""

    def __init__(self, sites: list[dict], classes: list[str], methods: list[str],
                 heritage: list[str] = (), lang: str = "java", excluded: list[str] = (),
                 defaults: list[tuple[str, str]] = ()):
        self.dir = Path(tempfile.mkdtemp(prefix="cgb-test-"))
        (self.dir / "sites.jsonl").write_text("\n".join(json.dumps(s) for s in sites) + "\n")
        (self.dir / "classes.txt").write_text("\n".join(classes) + "\n")
        (self.dir / "methods.txt").write_text("\n".join(methods) + "\n")
        (self.dir / "excluded.txt").write_text("\n".join(excluded) + ("\n" if excluded else ""))
        self.gt = G.load(self.dir / "sites.jsonl", self.dir / "classes.txt", self.dir / "methods.txt",
                         "fixture", self.dir / "excluded.txt")
        self.lang = L.get(lang)
        self.rv = R.Resolver(self.gt.classes, {}, self.lang, self.gt.methods)
        self.rv.add_external(self.gt.external_ancestors)
        if heritage:
            self.rv.add_heritage(list(heritage))
        if defaults:
            self.rv.add_default_exports(list(defaults))

    def tool(self, edges: list[tuple[Ref, Ref]], *, files=None, lines=None, labels=None,
             tier: Tier = Tier.A, name: str = "t") -> ToolOutput:
        rows = []
        for i, (a, b) in enumerate(edges):
            rows.append(Edge(caller=a, callee=b,
                             file=(files or [None] * len(edges))[i],
                             line=(lines or [None] * len(edges))[i],
                             confidence=(labels or [None] * len(edges))[i]))
        return ToolOutput(tool=name, subject="fixture", declared_tier=tier, edges=rows, meta={})

    def score(self, edges, tier: Tier = Tier.B, **kw) -> S.ToolScore:
        return S.score(self.tool(edges, **kw), self.gt, self.rv, tier)


def ref(s: str) -> Ref:
    return Ref.parse(s)
