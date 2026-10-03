#!/usr/bin/env python3
"""Mapping a tool's vocabulary onto the oracle's, without inventing answers.

Tools spell the same type six different ways:

    torture.F01Polymorphism$Base     internal-ish, `$`-nested
    torture.F01Polymorphism.Base     source-ish, `.`-nested
    Base                             simple name, no package
    F01Polymorphism.Base             nested, no package
    (file: torture/F01Polymorphism.java, symbol: Base)
    (file: torture/F01Polymorphism.java, symbol: Base.area)

The oracle spells it `torture.F01Polymorphism.Base` — the full nesting chain, because flattening is
lossy and would corrupt the ground truth (docs/PROTOCOL.md §3). None of the six spellings above is
wrong; they are different notations for one type, and a scorer that string-compared them would
report five tools as having found nothing.

So every tool reference passes through here first, and the result is one of three verdicts:

    RESOLVED     exactly one application type answers to that spelling — use it
    AMBIGUOUS    more than one does (`Config` when the subject has `core.Config` and `util.Config`)
    UNKNOWN      none does — the reference is outside the application, or the tool made it up

THE RULE ON AMBIGUITY, AND WHY IT IS NOT CHARITY
------------------------------------------------
An AMBIGUOUS or UNKNOWN reference is EXCLUDED from the score and COUNTED in the report. It is not
resolved in the tool's favour and it is not counted against it, because neither is knowable: a
benchmark that picked whichever candidate made the edge a true positive would be scoring its own
tie-breaker, and one that called every ambiguous row a false positive would be charging a tool for
a package name it never claimed to omit.

What stops exclusion from becoming a free pass is that it is *reported beside every number it
touches*: `unmapped_rows` next to precision, and `oracle_edges_unreachable` next to recall — the
count of ground-truth edges this tool's notation cannot express even in principle. A tool whose
output is mostly unmapped cannot show a clean precision without the reader seeing why.

Simple-name resolution IS applied when it is unique, because then it is not a guess: in a subject
with exactly one `Base`, `Base` denotes it. That is reading the tool's notation, not repairing it.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from language import JAVA, LanguageProfile
from model import Ref


class Verdict(str, Enum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Resolution:
    verdict: Verdict
    ref: Ref | None = None
    candidates: tuple[str, ...] = ()


def build_file_index(source_roots: list[Path], lang: LanguageProfile = JAVA) -> dict[str, str]:
    """`relative/path/To.java` -> the namespace it declares, for tools that report a file and a bare
    name.

    An index-style tool usually knows which FILE a symbol came from even when it does not know the
    symbol's namespace. Handing the scorer that mapping turns a would-be AMBIGUOUS verdict into a
    RESOLVED one without any guessing: the namespace is read out of the source the tool parsed.

    In a language with no namespace DECLARATION — TypeScript, where a module is its path — the
    index maps a file to the path-derived module id instead, which is the same information written
    a different way.
    """
    index: dict[str, str] = {}
    for root in source_roots:
        if not root.exists():
            continue
        for pattern in lang.source_globs:
            for p in sorted(root.rglob(pattern)):
                rel = p.relative_to(root).as_posix()
                if lang.namespace_re is not None:
                    m = lang.namespace_re.search(p.read_text(encoding="utf-8", errors="replace"))
                    ns = m.group(1) if m else ""
                else:
                    ns = rel.rsplit(".", 1)[0]      # the module IS the path
                index[rel] = ns
                # basename too, marked, for a tool that reports only the file name — and for
                # placing a path a tool spelled from another root by its longest matching suffix
                index.setdefault("//" + p.name, [])
                index["//" + p.name].append((rel, ns))       # type: ignore[arg-type]
    return index


class Resolver:
    """Built once per subject from the oracle's own class list — the only authority on what exists."""

    def __init__(self, classes: set[str], file_index: dict[str, str] | None = None,
                 lang: LanguageProfile = JAVA, methods: set | None = None) -> None:
        self.classes = classes
        self.file_index = file_index or {}
        self.lang = lang
        self.module_prefix: str | None = None   # see _candidates; set by run.py --module-prefix
        self._memo: dict[tuple, Resolution] = {}
        # heritage (issue #36): container -> parents, container -> kind; from the oracle's
        # `--mode heritage`. Lets the resolver ask whether a container declares OR INHERITS a
        # member, and whether it can be a caller at all (an interface's member cannot).
        self.parents: dict[str, set[str]] = {}
        self.kinds: dict[str, str] = {}
        # application packages / modules, for refusing to read a foreign fully-qualified name
        # by its simple name (issue #37)
        self._app_packages: set[str] = set()
        for c in classes:
            if lang.name == "java":
                parts = c.split(".")
                # the leading lowercase segments are the package
                lead = []
                for seg in parts:
                    if seg[:1].isupper() or "$" in seg:
                        break
                    lead.append(seg)
                self._app_packages.add(".".join(lead))
        # container -> the method names the ground truth says it declares. Used to split an
        # AMBIGUOUS container by the method being referenced — see `resolve`.
        self._declares: dict[str, set[str]] = defaultdict(set)
        # method name -> the containers that declare it, for a callee spelled with NO owner
        self._declared_by: dict[str, set[str]] = defaultdict(set)
        for m in methods or ():
            if m.type is not None:
                self._declares[m.type].add(m.name)
                self._declared_by[m.name].add(m.type)
        # parent container -> method name -> the ANONYMOUS containers nested in it that declare
        # that method. An anonymous literal or class is keyed by the oracle with a line
        # (`Applicative.ts:$obj:ApplicativeComposition@308`, `pkg.Outer$anon:Runnable@41`) —
        # a key no tool can spell. See `resolve` for the rule that reads it.
        self._anon_children: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
        for c in self._declares:
            parent = self._anon_parent(c)
            if parent is not None:
                for n in self._declares[c]:
                    self._anon_children[parent][n].add(c)
        # every spelling that could denote a canonical class -> the classes it could denote
        self._by_alias: dict[str, set[str]] = defaultdict(set)
        for c in classes:
            for alias in self.lang.aliases(c):
                self._by_alias[alias].add(c)
        # AN ALIAS MUST NEVER SHADOW A REAL TYPE. `Outer$anon:Foo` generates the convenience alias
        # `Outer$Foo` for tools that name an anonymous class by its supertype — but `Outer$Foo` is
        # also the internal name of a genuine nested class, and where the subject has one, the
        # convenience alias resolved to the ANONYMOUS class instead. That is not an ambiguity
        # reported to the reader, it is a silently wrong answer, and on netty-transport it made a
        # correctly-spelled type resolve to the wrong one.
        #
        # So a spelling that is itself a canonical name denotes THAT type and nothing else.
        for name in list(self._by_alias):
            if name in classes:
                self._by_alias[name] = {name}

    def _anon_parent(self, c: str) -> str | None:
        """The container `c` is written inside, or None if `c` is top-level.

        Named as well as anonymous: `mod:Cluster` is inside `mod`, `pkg.Outer.Inner` inside
        `pkg.Outer`, `Applicative.ts:$obj:X@308` inside `Applicative.ts`.
        """
        if self.lang.name == "java":
            if "$anon:" in c:
                return c.rsplit("$anon:", 1)[0]
            parent = c.rsplit(".", 1)[0] if "." in c else None
            return parent if parent in self.classes else None
        mod, sep, decl = c.partition(":")
        if not sep:
            return None
        parts = decl.split(".")
        return f"{mod}:{'.'.join(parts[:-1])}" if len(parts) > 1 else mod

    def add_heritage(self, rows: list[str]) -> None:
        """`container<TAB>kind<TAB>parent,parent` lines from the oracle's `--mode heritage`."""
        self._memo.clear()
        for ln in rows:
            parts = ln.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            c, kind = parts[0], parts[1]
            ps = {p for p in (parts[2].split(",") if len(parts) > 2 else []) if p}
            self.kinds[c] = kind
            self.parents[c] = ps
        # (an interface member cannot be a CALLER — resolve() drops interface candidates from the
        # nested placement of a caller, and only there: `TediousConnection#execSql` is a perfectly
        # good callee, and dropping it for both roles turned 96 CodeQL kysely groups `wrong`)

    def declares_or_inherits(self, c: str, name: str) -> bool:
        """Does `c` declare `name`, or inherit it from an in-universe ancestor?"""
        seen: set[str] = set()
        stack = [c]
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x)
            if name in self._declares.get(x, ()):
                return True
            stack.extend(self.parents.get(x, ()))
        return False

    def declaring_ancestors(self, c: str, name: str) -> tuple[str, ...]:
        """The NEAREST in-universe ancestors of `c` that declare `name` — the ones a member lookup
        on `c` reaches first. Breadth-first over the heritage, so a superclass's member shadows an
        interface's default and a grandparent's; at the first level with any declaration, a class
        wins over interfaces (JVMS §5.4.3.3 resolves the superclass chain before the
        superinterfaces). Empty when `c` declares the name itself or inherits it from nothing
        in the universe."""
        if name in self._declares.get(c, ()):
            return ()
        seen = {c}
        level = list(self.parents.get(c, ()))
        while level:
            found = [x for x in level if name in self._declares.get(x, ())]
            if found:
                classes = [x for x in found if self.kinds.get(x) not in ("interface",)]
                pick = classes if len(classes) == 1 else found
                return tuple(dict.fromkeys(pick))
            nxt: list[str] = []
            for x in level:
                for pp in self.parents.get(x, ()):
                    if pp not in seen:
                        seen.add(pp)
                        nxt.append(pp)
            level = nxt
        return ()

    def _is_app_qualified(self, n: str) -> bool | None:
        """For a Java spelling with a package prefix: is that package one of the application's?
        None when the spelling carries no package (a simple or nested name)."""
        if self.lang.name != "java":
            return None
        parts = n.replace("/", ".").split(".")
        lead = []
        for seg in parts:
            if seg[:1].isupper() or "$" in seg or not seg:
                break
            lead.append(seg)
        if not lead or len(lead) == len(parts):
            return None
        pkg = ".".join(lead)
        # equal to, inside, above, or a trailing part of an application package (`types.Path` for
        # `org.apache.tools.ant.types.Path` is a partial spelling, not a foreign one)
        return any(pkg == ap or pkg.startswith(ap + ".") or ap.startswith(pkg + ".") or ap.endswith("." + pkg)
                   for ap in self._app_packages if ap)

    def add_external(self, types: dict[str, set[str]]) -> None:
        """Make the EXTERNAL declaring ancestors (GroundTruth.external_ancestors) resolvable.

        Their aliases are added only where they collide with nothing the application declares: an
        external `Artifact` must never make an application `Artifact` ambiguous, and where the
        subject has one, the external spelling is simply not readable — the row drops as before.
        """
        self._memo.clear()
        for t, names in types.items():
            for alias in self.lang.aliases(t):
                if alias not in self._by_alias:
                    self._by_alias[alias] = {t}
            self._declares[t] |= set(names)

    def add_compiler_names(self, rows: list[str]) -> None:
        """`internal<TAB>canonical` from the oracle's `--mode anonmap`: the name the COMPILER gave
        a class, beside the key this benchmark uses for it.

        The oracle keys an anonymous class by its supertype (`Outer$anon:Runnable@41`) and strips a
        local class's counter, because javac and ecj number them differently and a counter is not a
        name. That is right for a ground-truth KEY and wrong as a reading rule: a tool that reads
        the class files, or that reports what a compiler told it, spells them `Outer$1`,
        `Outer$1Local`, `Op$1` — and PROTOCOL's own promise is that notation is READ, not repaired.
        Three adapters already translate this by hand (CodeQL in `Names.qll`, codegraph in
        `anon_notation`, axiom natively); the ones that do not had a quarter of their rows deleted
        before scoring. The mapping is a fact about the artefact being scored, which the oracle just
        read, so it belongs here once rather than in every adapter.

        An internal name that collides with something already resolvable is not added — the same
        rule `add_external` uses, so this can widen what is readable and never make it ambiguous.
        """
        self._memo.clear()
        for row in rows:
            internal, _, canonical = row.partition("\t")
            internal, canonical = internal.strip(), canonical.strip()
            if not internal or not canonical or canonical not in self.classes:
                continue
            for alias in (internal, internal.rsplit(".", 1)[-1],
                          internal.replace("$", ".")):
                if alias and alias not in self._by_alias:
                    self._by_alias[alias] = {canonical}

    def add_default_exports(self, pairs: list[tuple[str, str]]) -> None:
        """`(module, canonical container)` for each module's DEFAULT export.

        A tool that records `export default class Command` as `Command#default` has still named
        it unambiguously — ES modules permit one default export — so `<module>#default` and its
        spellings alias the container. Reading a language guarantee, not guessing.
        """
        self._memo.clear()
        for mod, target in pairs:
            noext = mod
            for ext in (".ts", ".tsx", ".mts", ".cts"):
                if noext.endswith(ext):
                    noext = noext[: -len(ext)]
                    break
            for m in {mod, noext, noext.lstrip("./"), noext[4:] if noext.startswith("src/") else noext}:
                for sep in (":", "#", ".", "/"):
                    self._by_alias[f"{m}{sep}default"].add(target)

    @staticmethod
    def _aliases(canonical: str) -> set[str]:
        """Spellings of `canonical` a tool might reasonably emit.

        Only NOTATION variants are generated — separators, package elision, the `$anon:` form. No
        alias ever spans two different types, so an alias match is a reading of the tool's notation
        and never a similarity guess.
        """
        out = {canonical}
        simple = canonical.rsplit(".", 1)[-1]
        out.add(simple)
        if "$anon:" in simple:
            # `Outer$anon:Runnable@123`. The `@line` exists to keep the GROUND TRUTH unambiguous —
            # two anonymous classes in one outer implementing one interface would otherwise share a
            # name. No tool emits it, so the line-less forms are aliases too: a tool that says
            # `Outer$anon:Runnable` resolves whenever the subject has only one, and where it has
            # two the row is reported AMBIGUOUS and the tool's own file/line can narrow it. Making
            # the key unambiguous and the ALIASES generous is the only arrangement that is both
            # sound and fair; a loose key would corrupt the bounds, a strict alias would punish
            # every tool for a disambiguator invented here.
            outer, _, rest = simple.partition("$anon:")
            sup = rest.split("@", 1)[0]
            pkg = canonical[: -len(simple)]
            out |= {f"{pkg}{outer}$anon:{sup}", f"{outer}$anon:{sup}",
                    f"{pkg}{outer}.{sup}", f"{outer}.{sup}",
                    f"{pkg}{outer}${sup}", f"{outer}${sup}"}
        return {a for a in out if a}

    def resolve_type(self, name: str | None, file: str | None = None) -> Resolution:
        if name is None:
            return Resolution(Verdict.UNKNOWN)
        cands = self._candidates(name)
        if not cands and file and self.lang.name == "java" and self._is_app_qualified(name) is None:
            # a SIMPLE name, retried under the file's package (Java only — the `.`/`$` split is a
            # Java rule, and applying it to TypeScript placed `ns.Lexer` in the caller's module, #36)
            pkg = self._package_of(file)
            if pkg is not None:
                cands = self._candidates(f"{pkg}.{name.rsplit('.', 1)[-1].rsplit('$', 1)[-1]}")
        if len(cands) > 1 and file:
            # DISAMBIGUATE BY FILE, not merely fall back to it.
            #
            # A tool that flattens `pkg.Outer.Inner` to `pkg.Inner` makes two distinct types
            # collide, and this subject has exactly that (`F02Generics.Node`, `F07Modern.Node`).
            # But the tool also told us which FILE the reference came from, and Java requires the
            # public top-level type to be named after its file — so `torture/F02Generics.java`
            # narrows the pair to one without any guessing. Not using that would charge a tool for
            # an ambiguity it had already resolved in the row it emitted.
            narrowed = self._narrow_by_file(cands, file)
            if len(narrowed) == 1:
                cands = narrowed
        if len(cands) == 1:
            return Resolution(Verdict.RESOLVED, Ref(name="", type=next(iter(cands))))
        if len(cands) > 1:
            return Resolution(Verdict.AMBIGUOUS, candidates=tuple(sorted(cands)))
        return Resolution(Verdict.UNKNOWN)

    def _narrow_by_file(self, cands: set[str], file: str) -> set[str]:
        """Keep the candidates the file could actually declare."""
        f = file.replace("\\", "/")
        base = f.rsplit("/", 1)[-1]
        if self.lang.name != "java":
            # TypeScript: a module IS its path, so the file names the container's module exactly.
            # This was a no-op before #36, and a TS row naming the right file stayed AMBIGUOUS.
            g = f.lstrip("./")
            pre = self.module_prefix
            if pre and g.startswith(pre):
                g = g[len(pre):]
            hit = {c for c in cands if c == g or c.startswith(g + ":")}
            return hit or cands
        if not base.endswith(".java"):
            return cands
        outer = base[: -len(".java")]
        pkg = self._package_of(f)
        prefix = f"{pkg}.{outer}" if pkg else outer
        hit = {c for c in cands if c == prefix or c.startswith(prefix + ".")
               or c.startswith(prefix + "$")}
        # a non-public top-level type shares the file with the public one: `p/Util.java` may
        # declare `p.Helper` AND `p.Util.Helper`; the file names both, so it decides nothing (#36)
        if pkg:
            same_pkg_top = {c for c in cands if c.rsplit(".", 1)[0] == pkg and c not in hit
                            and self.file_index.get(f) == pkg}
            if same_pkg_top and hit:
                return cands
        return hit or cands

    def _top_level_of_file(self, file: str) -> str | None:
        """`pkg.Outer` for `pkg/Outer.java`, the public top-level type Java names after its file."""
        f = file.replace("\\", "/")
        base = f.rsplit("/", 1)[-1]
        if not base.endswith(".java"):
            return None
        pkg = self._package_of(f)
        outer = base[: -len(".java")]
        return f"{pkg}.{outer}" if pkg else outer

    def _package_of(self, file: str) -> str | None:
        f = file.replace("\\", "/").lstrip("./")
        pre = self.module_prefix
        if pre:
            # a monorepo layout: the tools index from an ancestor and the subject lives under the
            # prefix; a path outside it is context (a sibling package, a test tree), never placed
            if not f.startswith(pre) and "/" in f:
                return None
            if f.startswith(pre):
                f = f[len(pre):]
        hit = self.file_index.get(f)
        if isinstance(hit, str):
            return hit
        base = f.rsplit("/", 1)[-1]
        cands = self.file_index.get("//" + base) or []
        if "/" not in f:
            # the tool reported nothing but a basename
            return cands[0][1] if len(cands) == 1 else None
        # a PATH: it must end with one of the indexed relative paths (a tool that spells the file
        # from another root — an absolute path, or the ancestor a monorepo is indexed from). A path
        # that ends with none names a file outside the universe (`dtslint/Array.ts`) and is NOT
        # read as the subject's `Array.ts` by its basename: that charged every top-level call in
        # fp-ts's test tree to the tool.
        for rel, ns in cands:
            if f == rel or f.endswith("/" + rel):
                return ns
        return None

    def _candidates(self, name: str) -> set[str]:
        """Every application class a spelling could denote, trying progressively looser notations.

        TWO PASSES, AND THE ORDER IS THE POINT. A spelling that converts into a real canonical name
        denotes THAT type, even if some other type also generated it as a convenience alias. Mixing
        the two passes let `Outer$DelegatingChannelHandlerContext` — a genuine nested class written
        in internal notation — match the alias of an ANONYMOUS class that happens to implement an
        interface of the same name, and return the wrong type with no ambiguity reported. An
        exact-name pass that runs first cannot make that mistake.
        """
        n = name.strip()
        if not n:
            return set()
        # A MONOREPO SUBJECT is indexed by the tools from one directory up, so that the sibling
        # packages the checker types through are in their view too (issue #20). Their module paths
        # then carry the subject's directory as a prefix — `excalidraw/components/App.tsx` for the
        # oracle's `components/App.tsx` — and the prefix is stripped here, before any other
        # notation, because it is the harness's layout and not the tool's spelling.
        pre = self.module_prefix
        if pre and n.startswith(pre):
            n = n[len(pre):]
        variants = self.lang.notations(n)
        for variant in variants:
            if variant in self.classes:
                return {variant}
        # A FULLY-QUALIFIED NAME IN A FOREIGN PACKAGE IS NOT READ BY ITS SIMPLE NAME (issue #37).
        # `java.nio.file.Path` resolved to apache-ant's `types.Path` through the loosest notation,
        # and CodeQL — which spells the JDK type exactly — was charged `polluted` for an exact
        # answer. Only the exact and nested-separator forms may match a name whose package the
        # application does not declare; an external declaring ancestor (add_external) has its own
        # exact alias and is unaffected.
        foreign = self._is_app_qualified(n) is False
        pkg = self._package_prefix(n) if foreign else ""
        for variant in variants:
            if foreign and not variant.startswith(pkg + "."):
                continue                    # a variant that dropped the foreign package
            hit = self._by_alias.get(variant)
            if hit:
                return set(hit)
        return set()

    @staticmethod
    def _package_prefix(n: str) -> str:
        lead = []
        for seg in n.replace("/", ".").split("."):
            if seg[:1].isupper() or "$" in seg or not seg:
                break
            lead.append(seg)
        return ".".join(lead)

    @staticmethod
    def _notations(n: str) -> list[str]:
        """`n` rewritten into the benchmark's flattened convention, loosest last."""
        out = [n]
        slashed = n.replace("/", ".")
        if slashed != n:
            out.append(slashed)
        # The canonical key of an anonymous class carries a `@line` disambiguator that exists for
        # the GROUND TRUTH's soundness and that no tool emits. Strip it before matching.
        for form in list(out):
            if "$anon:" in form and "@" in form.rsplit("$anon:", 1)[1]:
                out.append(form.rsplit("@", 1)[0])
        # The INTERNAL nesting separator: `pkg.Outer$Inner` is the canonical `pkg.Outer.Inner`.
        # Without this the only route to a match is the bare simple name, which needlessly reports
        # AMBIGUOUS the moment a subject has two same-named nested types — punishing a tool that
        # spelled the full, unambiguous path.
        #
        # A name can carry BOTH: `pkg.Outer$Inner$anon:Runnable` is an anonymous class inside a
        # nested class. Only the NESTING separators convert; the `$anon:` marker must survive, or
        # the result denotes nothing. Handling only the marker-free case left every
        # two-levels-deep anonymous class unresolvable — 52 of them on netty-transport.
        for form in list(out):
            if "$" not in form:
                continue
            head, sep, tail = form.partition("$anon:")
            converted = head.replace("$", ".") + (sep + tail if sep else "")
            if converted != form:
                out.append(converted)
        # nested: pkg.Outer$Inner / pkg.Outer.Inner -> pkg.Inner  (the flattening convention)
        for form in list(out):
            if "$" in form:
                pkg, _, tail = form.rpartition(".") if "." in form else ("", "", form)
                leaf = tail.split("$")[-1]
                out.append(f"{pkg}.{leaf}" if pkg else leaf)
            parts = form.split(".")
            if len(parts) >= 2:
                # a dotted nested type: the last element is the type, the one before may be the outer
                out.append(".".join(parts[:-2] + parts[-1:]) if len(parts) >= 3 else parts[-1])
        # bare simple name, last resort. The `$anon:` marker survives — it is what distinguishes an
        # anonymous class from the interface it implements — but the `@line` disambiguator does not,
        # since no tool emits one. Without this, a tool that flattens a nested anonymous class
        # (`pkg.Outer.Inner$anon:Sup` -> `pkg.Inner$anon:Sup`) matches nothing at all: 26 such types
        # on netty-transport.
        for form in list(out):
            tail = form.rsplit(".", 1)[-1].rsplit("/", 1)[-1]
            if "$anon:" in tail:
                out.append(tail.rsplit("@", 1)[0] if "@" in tail.rsplit("$anon:", 1)[1] else tail)
        out.append(n.rsplit(".", 1)[-1].rsplit("$", 1)[-1].rsplit("/", 1)[-1])
        seen, uniq = set(), []
        for x in out:
            if x and x not in seen:
                seen.add(x)
                uniq.append(x)
        return uniq

    # ── the public entry point ───────────────────────────────────────────────────────────────
    def resolve(self, r: Ref, file: str | None = None, *, callee: bool = False,
                context_file: str | None = None) -> Resolution:
        """Memoised front of _resolve: the same (ref, file) is asked thousands of times per run —
        every tool's rows against one universe, gate 3 twenty times over — and the answer is a
        pure function of the resolver's tables (issue #57)."""
        key = (r, file, callee, context_file)
        hit = self._memo.get(key)
        if hit is None:
            hit = self._memo[key] = self._resolve(r, file, callee=callee, context_file=context_file)
        return hit

    def _resolve(self, r: Ref, file: str | None = None, *, callee: bool = False,
                 context_file: str | None = None) -> Resolution:
        """A whole method reference, type and all.

        The method NAME is passed through untouched: a tool that says `area` means `area`, and the
        only normalisation the benchmark applies to names is on the oracle's side (lambda bodies
        folded, constructors spelled `<init>`), which `normalise_name` mirrors here so the two
        vocabularies meet in the middle rather than the tool being asked to adopt ours.

        With `callee=True` a member the named container INHERITS is read the way the language
        reads it. `square.tag()` where `Square` extends `Base` and only `Base` declares `tag`: the
        source, the bytecode's symbolic reference and four of the tools all spell the target
        `Square#tag`; JVMS §5.4.3.3 (and a TypeScript prototype lookup) resolve that spelling to
        `Base#tag`, which is what the oracle's CERTAIN set holds. Scoring `Square#tag` as `wrong`
        charged those tools for the language's own notation. The rule is a lookup, not a guess:
        the nearest declaring ancestor, and AMBIGUOUS when two are equally near. A CALLER is
        never re-placed this way — a method body is in the class that declares it.

        `context_file` is the CALL SITE's file, offered for a callee whose own file the tool did
        not report. It narrows an AMBIGUOUS container only — after the method name has already
        dropped the candidates that do not declare or inherit the member (#36) — and never
        resolves an UNKNOWN one: `new EventLoopWorker(pool)` written inside `IoScheduler.java`,
        with `IoScheduler.EventLoopWorker` and `ComputationScheduler.EventLoopWorker` both
        matching the flattened spelling, denotes the one declared in that file; a spelling that
        matches nothing is not turned into something by the file it was written in.
        """
        name = normalise_name(r.name, r.type, self.lang)
        if r.type is None:
            # A CALLEE WITH NO OWNER — code-review-graph records half of apache-ant's calls as
            # a bare `isReference` / `getProject` — is read the way a bare type name is
            # (PROTOCOL §5.1): where exactly one application container declares that method,
            # the name denotes it; where several do, or none, the row stays owner-less and is
            # unspellable at Tier B, counted, never guessed. A CALLER is not read this way — a
            # body is in one place and the tool should know where.
            if callee and self._declared_by:
                owners = self._declared_by.get(name, set())
                if len(owners) == 1:
                    return Resolution(Verdict.RESOLVED,
                                      Ref(name=name, type=next(iter(owners)),
                                          params=_normalise_params(r.params, self.lang)))
            return Resolution(Verdict.RESOLVED, Ref(name=name, type=None, params=r.params))
        # THE METHOD NAME SPLITS AN AMBIGUOUS CONTAINER BEFORE THE FILE DOES (issue #36): the file
        # narrowed `Node` to `p.A.Node`, which does not declare `visit`, and the row was scored
        # against a method that does not exist. Candidates that neither declare nor inherit the
        # name are dropped first; only then is the file consulted.
        t = self.resolve_type(r.type, None)
        if t.verdict is Verdict.AMBIGUOUS and self._declares:
            keep = tuple(c for c in t.candidates if self.declares_or_inherits(c, name))
            if len(keep) == 1:
                t = Resolution(Verdict.RESOLVED, Ref(name="", type=keep[0]))
            elif keep:
                t = Resolution(Verdict.AMBIGUOUS, candidates=keep)
        if t.verdict is Verdict.AMBIGUOUS and file:
            narrowed = self._narrow_by_file(set(t.candidates), file)
            if len(narrowed) == 1:
                t = Resolution(Verdict.RESOLVED, Ref(name="", type=next(iter(narrowed))))
        elif t.verdict is Verdict.AMBIGUOUS and context_file and self.lang.name == "java":
            # THE CALL SITE's file, for a callee: only the candidate NESTED IN THE CALLER'S OWN
            # TOP-LEVEL CLASS is what Java name lookup finds first — a flattened `Worker` written
            # inside `Io.java` denotes `Io.Worker` when that exists. A candidate that merely lives
            # in the same file, or the caller-file candidate when the truth was another file's
            # `Worker` (12 wrong picks on rxjava, #36 reopened), is not decided by the file. Never
            # for TypeScript: an import can alias (`import { Worker as BW }`), so the file says
            # nothing about which module's `Worker` a flattened name means.
            narrowed = self._narrow_by_file(set(t.candidates), context_file)
            outer = self._top_level_of_file(context_file)
            nested = {c for c in narrowed if outer and (c.startswith(outer + ".") or c.startswith(outer + "$"))}
            if len(nested) == 1 and len(narrowed) == 1:
                t = Resolution(Verdict.RESOLVED, Ref(name="", type=next(iter(nested))))
        if t.verdict is Verdict.UNKNOWN and file:
            t = self.resolve_type(r.type, file)
        if t.verdict is Verdict.AMBIGUOUS and self._declares:
            # THE METHOD NAME CAN SPLIT AN AMBIGUOUS CONTAINER. fp-ts names every module after the
            # type it declares — `Option.ts` declares `interface Option` — so the bare owner `Option`
            # denotes both the module and the interface, and 4,194 of one tool's 6,546 rows were
            # reported ambiguous. But `Option#map` is only declared by the MODULE; the interface has
            # no member `map`. Keeping the candidates that actually declare the referenced method is
            # reading the ground truth, not guessing: where two still do, it stays ambiguous.
            # A container that INHERITS the member declares it for this purpose (#36 reopened,
            # J5/T4): `A.Node` inheriting `visit` from `Base` is as good an owner of `visit` as
            # `B.Node`, which declares it — dropping it here resolved the row to `B.Node` with
            # no ambiguity reported.
            keep = tuple(c for c in t.candidates if self.declares_or_inherits(c, name))
            if len(keep) == 1:
                t = Resolution(Verdict.RESOLVED, Ref(name="", type=keep[0]))
            elif keep:
                t = Resolution(Verdict.AMBIGUOUS, candidates=keep)
        if t.verdict is not Verdict.RESOLVED:
            return Resolution(t.verdict, candidates=t.candidates)
        assert t.ref is not None
        container = t.ref.type
        # A METHOD IS PLACED BY THE CONTAINER THE TOOL NAMED AND THE METHOD NAME, ONE LEVEL DOWN.
        # fp-ts builds every instance as `return { map: …, ap: (fa, fb) => pipe(…) }` — a literal
        # bound to nothing, which the oracle keys `Applicative.ts:$obj:ApplicativeComposition@308`,
        # a key no tool can spell; every tool that names that function says `Applicative.ts#ap`.
        # ioredis writes `const reject = () => …` inside a method of `Cluster`; the oracle's
        # container is `cluster/index.ts:Cluster`, CodeQL's is the module. In both, the tool named
        # the enclosing container and the name, and the name is declared by exactly one container
        # nested in it — so that is what the spelling denotes, the way a unique simple name denotes
        # its type. Two nested containers declaring the name stay AMBIGUOUS; a name the container
        # declares itself is never re-placed. The same rule reads a Java `Outer#run` onto the one
        # nested or anonymous class inside `Outer` that declares `run`.
        if self._declares and not self.declares_or_inherits(container, name):
            anon = self._anon_children.get(container, {}).get(name, set())
            if not callee and self.kinds:
                # a signature with no body cannot be a caller (#17)
                anon = {c for c in anon if self.kinds.get(c) != "interface"}
            if len(anon) == 1:
                container = next(iter(anon))
            elif len(anon) > 1:
                return Resolution(Verdict.AMBIGUOUS, candidates=tuple(sorted(anon)))
        elif callee and self._declares and name not in self._declares.get(container, ()):
            # inherited: the member lookup the language performs on this spelling (see above)
            up = self.declaring_ancestors(container, name)
            if len(up) == 1:
                container = up[0]
            elif len(up) > 1:
                return Resolution(Verdict.AMBIGUOUS, candidates=up)
        return Resolution(Verdict.RESOLVED,
                          Ref(name=name, type=container,
                              params=_normalise_params(r.params, self.lang)))


def normalise_name(name: str, type_name: str | None, lang: LanguageProfile = JAVA) -> str:
    """The oracle's spelling of a method name, from whatever the tool called it.

    Three notations, all of which mean the same method:
      * a constructor: `<init>`, `constructor`, `new`, or the type's own simple name
      * a lambda body: `lambda$run$0` -> the method that contains it, `run` (the oracle folds a
        lambda body into its lexical container; a tool that reports the body by name is saying the
        same thing in a different notation)
      * anything else, unchanged
    """
    n = name.strip()
    if n in lang.ctor_aliases:
        return lang.ctor_canonical
    # "A method named after its type is a constructor" is a JAVA rule. In TypeScript a module named
    # `pipeable.ts` legitimately exports a function named `pipeable`, and applying the rule renamed
    # every such function to `constructor` — 41 false positives on fp-ts from a notation mutation
    # that changed nothing about the method.
    if (lang.name == "java" and type_name is not None and n
            and n == type_name.rsplit(".", 1)[-1].rsplit("$", 1)[-1]):
        return lang.ctor_canonical
    if lang.closure_re is not None:
        m = lang.closure_re.match(n)
        if m and m.group("m"):
            return lang.ctor_canonical if m.group("m") == "new" else m.group("m")
    return n


def _normalise_params(params: tuple[str, ...] | None,
                      lang: LanguageProfile = JAVA) -> tuple[str, ...] | None:
    """Erase and simple-name a parameter list the way the oracle does, so Tier A can be compared.

    The oracle reads parameters out of an erased descriptor: `List<String>` is `List`, a type
    variable is its bound, and every type is spelled by its simple name. A tool that reports source
    types is not wrong to include the type arguments — it is reporting a different thing — so they
    are erased here rather than counted as a mismatch.
    """
    if params is None:
        return None
    out = []
    for p in params:
        p = p.strip()
        if p == "*":
            out.append("*")
            continue
        arr = ""
        while p.endswith("[]"):
            arr += "[]"
            p = p[:-2]
        if lang.erases_generics:
            p = re.sub(r"<.*>", "", p)                   # erase type arguments
            p = p.rsplit(".", 1)[-1].rsplit("$", 1)[-1]  # simple-name it
        else:
            # TypeScript: the oracle strips every space from a parameter type (`T|ReadonlyArray<T>`);
            # a tool that writes `T | ReadonlyArray<T>` is spelling the same type, and Tier A was
            # measuring the spaces — 383 of axiom's 551 Tier-A losses on kysely (#68 §1)
            p = re.sub(r"\s+", "", p)
        p = re.sub(r"\.\.\.$", "[]", p)                  # varargs is an array in the descriptor
        out.append(p + arr)
    return tuple(out)
