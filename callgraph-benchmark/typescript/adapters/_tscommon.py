#!/usr/bin/env python3
"""Shared by the TypeScript adapters: the one rule that differs from Java.

IN JAVA, every method has a declaring TYPE, so a tool that reports no owner has genuinely failed to
resolve one and is scored at Tier C.

IN TYPESCRIPT that inference is wrong. A module-level `export function helper()` has no class, and
its canonical container is the MODULE — `src/t03-functions.ts`. A tool that reports the symbol and
the file it came from has therefore named the container exactly; treating it as owner-less would
drop every top-level function in the subject to Tier C and report the tool as unable to express
something it expressed perfectly well.

So: no owner + a file => the container is that file's module path. That is reading the tool's own
output, not repairing it. A tool that reports neither stays owner-less and is scored at Tier C,
which is the honest record of what it said.
"""
from __future__ import annotations

import os


def module_of(file: str | None, root: str) -> str | None:
    """The canonical module container for a file the tool reported, or None."""
    if not file:
        return None
    f = file.replace("\\", "/")
    r = root.replace("\\", "/").rstrip("/") + "/"
    if f.startswith(r):
        f = f[len(r):]
    f = f.lstrip("./")
    return f if f.endswith((".ts", ".tsx", ".mts", ".cts")) else None


def container(owner: str | None, file: str | None, root: str) -> str | None:
    """The container a reference names: the declared owner when there is one, else the module."""
    if owner:
        return owner
    return module_of(file, root)


def _depth_walk(text: str):
    """Yield (index, char, depth-before) with `<([{` / `>)]}` tracked and `=>` NOT counted as a
    closing angle bracket."""
    depth = 0
    prev = ""
    for i, ch in enumerate(text):
        yield i, ch, depth
        if ch in "<([{":
            depth += 1
        elif ch in ")]}" or (ch == ">" and prev != "="):
            depth -= 1
        prev = ch


def ts_params(signature: str | None) -> tuple[str, ...] | None:
    """The parameter TYPES out of a TypeScript signature string — `(a: T, b?: U<V, W>): R` — or None
    when there is no signature. Splits on commas at depth zero of `<([{`, strips the `name:` /
    `name?:` prefix, a default value, and whitespace; a parameter written without a type reads as
    `any`. The Java splitter this replaced expected `<ret> (<Type name>, …)` ending in `)` and
    returned None for every TypeScript signature (a trailing `: R`), so codegraph's TypeScript rows
    were 98% unspellable at Tier A while the row was published as Tier A (issue #32 §1)."""
    if not signature:
        return None
    s = signature.strip()
    if not s.startswith("("):
        return None
    end = -1
    for i, ch, d in _depth_walk(s):
        if ch == ")" and d == 1:
            end = i
            break
    if end < 0:
        return None
    body = s[1:end]
    parts: list[str] = []
    cur = ""
    for i, ch, d in _depth_walk(body):
        if ch == "," and d == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    out: list[str] = []
    for p in parts:
        p = p.strip().lstrip(".")                         # `...rest`
        if not p:
            continue
        colon = next((i for i, ch, d in _depth_walk(p) if ch == ":" and d == 0), -1)
        t = p[colon + 1:] if colon >= 0 else "any"
        for i, ch, d in _depth_walk(t):                   # drop `= default` at depth zero
            if ch == "=" and d == 0 and t[i:i + 2] != "=>":
                t = t[:i]
                break
        out.append("".join(t.split()))
    return tuple(out)
