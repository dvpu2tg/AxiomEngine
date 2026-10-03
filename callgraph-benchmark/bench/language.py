#!/usr/bin/env python3
"""What differs between languages, isolated so that nothing else has to know.

The metrics, the tier projection, the link-group verdicts and the resolver's ambiguity rules are
language-independent — they are statements about call resolution, not about Java. What IS
language-specific is small and concrete:

  * how a source file declares the namespace a type lives in (a Java `package`, a TS module path)
  * what a constructor is called (`<init>`, `constructor`)
  * how a lambda/closure body is named, when the language names one at all
  * whether parameter types are erased, and how a type is spelled simply

Keeping those in one profile per language is what makes a cross-language comparison *possible* to
state honestly. It does not make the numbers comparable — see docs/CROSS-LANGUAGE.md — but it does
guarantee that a difference between the Java and TypeScript tables is a difference in the tools or
in the languages, never a difference in two independently drifted harnesses.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


def is_type_segment(seg: str) -> bool:
    """Whether one dot-segment of a Java canonical name is a TYPE rather than a package.

    By convention a package segment is lower-case and a type is capitalised. `$` and `_` are
    letters to the JLS (§3.8), so the capital is read after any leading run of them: gson's
    `$Gson$Types` is a type. Read on the raw first character it was taken for a package, and the
    first capital after it, a NESTED class, was taken for the top-level type (#97)."""
    return seg.lstrip("$_")[:1].isupper()


def _java_aliases(canonical: str) -> set[str]:
    """Spellings of a Java type a tool might emit. See bench/resolve.py for the rules."""
    out = {canonical}
    simple = canonical.rsplit(".", 1)[-1]
    out.add(simple)
    # the FLATTENED spelling, `pkg.Outer.Inner` -> `pkg.Inner`, with whatever anonymous tail the
    # leaf carries: netty's `AbstractChannel.AbstractUnsafe$anon:Runnable@704$anon:Runnable@712`
    # flattens to `channel.AbstractUnsafe$anon:…` and the tail-parsing rules below only read the
    # first `$anon:`, so the self-test's flatten mutation found one row the resolver dropped
    parts = canonical.split(".")
    first_type = next((i for i, seg in enumerate(parts) if is_type_segment(seg)), None)
    if first_type is not None and first_type < len(parts) - 1:
        out.add(".".join(parts[:first_type] + parts[-1:]))
    if "$anon:" in simple:
        outer, _, rest = simple.partition("$anon:")
        sup = rest.split("@", 1)[0]
        pkg = canonical[: -len(simple)]
        out |= {f"{pkg}{outer}$anon:{sup}", f"{outer}$anon:{sup}",
                f"{pkg}{outer}.{sup}", f"{outer}.{sup}",
                f"{pkg}{outer}${sup}", f"{outer}${sup}"}
    return {a for a in out if a}


def _java_notations(n: str) -> list[str]:
    out = [n]
    slashed = n.replace("/", ".")
    if slashed != n:
        out.append(slashed)
    for form in list(out):
        if "$anon:" in form and "@" in form.rsplit("$anon:", 1)[1]:
            out.append(form.rsplit("@", 1)[0])
    for form in list(out):
        if "$" not in form:
            continue
        head, sep, tail = form.partition("$anon:")
        converted = head.replace("$", ".") + (sep + tail if sep else "")
        if converted != form:
            out.append(converted)
    for form in list(out):
        if "$" in form:
            pkg, _, tail = form.rpartition(".") if "." in form else ("", "", form)
            leaf = tail.split("$")[-1]
            out.append(f"{pkg}.{leaf}" if pkg else leaf)
        parts = form.split(".")
        # `pkg.Outer.Inner` -> `pkg.Inner`: drop the second-to-last segment ONLY when it is a type.
        # Dropping it unconditionally turned `taskdefs.optional.Property` into `taskdefs.Property` —
        # a different, real type in a different PACKAGE — and resolved it silently. A package
        # segment is lowercase by convention; a type is not.
        if len(parts) >= 3 and parts[-2][:1].isupper():
            out.append(".".join(parts[:-2] + parts[-1:]))
        elif len(parts) == 2 and parts[-2][:1].isupper():
            out.append(parts[-1])
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


def _ts_aliases(canonical: str) -> set[str]:
    """Spellings of a TypeScript container a tool might emit.

    The canonical form is `<module path>:<Declaration>` — `src/parse.ts:Lexer` — or the bare module
    path for a module-level function. A tool may drop the extension, drop a leading `./` or `src/`,
    use the declaration name alone, or join the two with `.` or `#`. None of those spellings can
    denote two different containers unless two modules declare the same name, and that case is
    reported AMBIGUOUS like any other.
    """
    out = {canonical}
    mod, sep, decl = canonical.rpartition(":")
    if not sep:
        mod, decl = canonical, ""
    noext = mod
    for ext in (".ts", ".tsx", ".mts", ".cts", ".d.ts", ".js"):
        if noext.endswith(ext):
            noext = noext[: -len(ext)]
            break
    forms = {mod, noext, noext.lstrip("./")}
    for f in list(forms):
        if f.startswith("src/"):
            forms.add(f[4:])
    if decl:
        out.add(decl)
        for f in forms:
            out |= {f"{f}:{decl}", f"{f}.{decl}", f"{f}#{decl}", f"{f}/{decl}"}
    else:
        out |= forms
    return {a for a in out if a}


def _ts_notations(n: str) -> list[str]:
    """`n` rewritten toward the canonical `<module>:<Declaration>` form, loosest last."""
    out = [n, n.replace("\\", "/")]
    for form in list(out):
        if "#" in form:
            out.append(form.replace("#", ":"))
    for form in list(out):
        for ext in (".ts", ".tsx", ".mts", ".cts"):
            if ext in form:
                out.append(form.replace(ext, ""))
    for form in list(out):
        if form.startswith("./"):
            out.append(form[2:])
    # the declaration name alone, which is what a tool that reports no module emits — but ONLY
    # when the tool reported no module: a spelling that carries a path names a file, and a file
    # outside the universe (`dtslint/Array.ts`, a test tree the tools index as context since #20)
    # must not be read as the subject's `Array.ts` by its basename. That read turned every
    # top-level call in fp-ts's dtslint tests into a false positive charged to the tool.
    if "/" not in n:
        tail = n.rsplit(":", 1)[-1].rsplit("#", 1)[-1]
        for ext in (".ts", ".tsx", ".mts", ".cts"):
            if tail.endswith(ext):
                tail = tail[: -len(ext)]
        out.append(tail)
    elif ":" in n:
        # `path:Decl` from a tool — the declaration name alone still identifies a unique class
        out.append(n.rsplit(":", 1)[-1])
    seen, uniq = set(), []
    for x in out:
        if x and x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


@dataclass(frozen=True)
class LanguageProfile:
    name: str
    # file extensions that hold source, for the file -> namespace index
    source_globs: tuple[str, ...]
    # matches the namespace declaration inside a source file, group(1) = the namespace
    namespace_re: re.Pattern | None
    # spellings a tool might use for a constructor
    ctor_aliases: frozenset[str]
    # the canonical spelling of a constructor
    ctor_canonical: str
    # matches a compiler-generated closure body name, group("m") = the enclosing method if known
    closure_re: re.Pattern | None
    # does the type system erase generic arguments in a signature?
    erases_generics: bool
    # separator between a namespace and a top-level type, in canonical names
    namespace_sep: str = "."
    # how a tool's spelling of a container is mapped onto the canonical one
    aliases: object = None       # (canonical) -> set[str]
    notations: object = None     # (spelling)  -> list[str], loosest last


JAVA = LanguageProfile(
    name="java",
    source_globs=("*.java",),
    namespace_re=re.compile(r"^\s*package\s+([\w.]+)\s*;", re.M),
    # ONLY the two spellings no Java method can have. `constructor` and `ctor` are legal method
    # names — guava declares `TypeToken#constructor(Constructor)` — and aliasing them renamed a
    # real method to `<init>` and lost its three edges from a perfect answer (issue #44). Every
    # Java adapter here spells a constructor `<init>` itself; an adapter that meets a tool
    # writing `constructor` maps it by the tool's kind column, not by name.
    ctor_aliases=frozenset({"<init>", "<constructor>"}),
    ctor_canonical="<init>",
    # javac emits `lambda$<method>$<n>`; ecj emits `lambda$<n>` with no method component at all,
    # which is why the oracle reads a lambda's container off the invokedynamic site instead of
    # parsing this. The pattern exists only to read a TOOL that reports the body by name.
    closure_re=re.compile(r"^lambda\$(?:(?P<m>[A-Za-z_$][\w$]*)\$)?\d+$"),
    erases_generics=True,
    aliases=_java_aliases,
    notations=_java_notations,
)

TYPESCRIPT = LanguageProfile(
    name="typescript",
    source_globs=("*.ts", "*.tsx", "*.mts", "*.cts"),
    # TypeScript has no `package` statement. A module IS its file path, so the namespace comes from
    # the path rather than from anything written in the file, and `namespace_re` is None: the
    # resolver falls back to the path-derived module id the oracle uses.
    namespace_re=None,
    # NOT `ctor` or `new`: in TypeScript those are ordinary identifiers, and typedoc declares a
    # module-level `function ctor(…)` — the Java-style alias rewrote it to `constructor` and a
    # perfect tool lost the edge (ceiling gate, typedoc).
    ctor_aliases=frozenset({"constructor", "<init>", "<constructor>"}),
    ctor_canonical="constructor",
    # TS has no compiler-generated closure names — an arrow function is anonymous and tools name it
    # by position or by the variable holding it. The oracle folds a closure body into its lexically
    # enclosing function, and a tool that names the variable instead is reported, not rewritten.
    closure_re=None,
    # Generics are erased at runtime but the CHECKER sees them, and it is the checker that resolves
    # a call. A signature is compared as the checker spells it.
    erases_generics=False,
    aliases=_ts_aliases,
    notations=_ts_notations,
)

PROFILES = {p.name: p for p in (JAVA, TYPESCRIPT)}


def get(name: str) -> LanguageProfile:
    try:
        return PROFILES[name]
    except KeyError:
        raise SystemExit(f"unknown language {name!r}; known: {', '.join(sorted(PROFILES))}")
