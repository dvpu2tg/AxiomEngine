#!/usr/bin/env python3
"""An INDEPENDENT reader of the same bytecode, sharing no code with `java.lang.classfile`.

Why this exists
---------------
`oracle/ClassfileGroundTruth.java` is the benchmark's ground truth. Every number every tool is
scored on comes out of it, so a bug in it is not a wrong number — it is a wrong benchmark, and a
wrong benchmark is worse than no benchmark. The defence is a second reader of the same artefacts
built on a different mechanism: `javap`, the JDK's own disassembler, whose textual output is a
different code path from the classfile parsing API.

The two are compared at the RAW layer — every invoke instruction exactly as the constant pool
spells it, before any exclusion, re-pointing, normalisation or lambda folding. That separation is
deliberate:

    agreement at the raw layer   =>  the bytecode was READ correctly
    agreement at --mode sites    =>  the CONVENTIONS were applied correctly

They are different failure modes. A convention bug the two readers share would survive a
sites-level comparison; a parse bug would not survive this one. Only the first is checkable by a
second reader, which is exactly why the conventions are written down separately in
docs/PROTOCOL.md and pinned by fixtures rather than trusted.

    python3 oracle/javap_reader.py <classes-dir> > raw.javap.txt
    java -cp <oc> ClassfileGroundTruth --app <classes-dir> --mode raw > raw.classfile.txt
    diff raw.classfile.txt raw.javap.txt        # must be empty

Both sides emit, sorted and deduplicated:

    <owner>.<name><descriptor> | <OPCODE> | <owner>.<name><descriptor>

A method reference is reported as `METHODREF_RAW` naming the implementation MethodHandle — bootstrap
argument 1 of a `LambdaMetafactory` call site. It appears in no invoke instruction, so a reader that
skips invokedynamic cannot see a single method-reference edge.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

THIS_CLASS_RE = re.compile(r"^\s*this_class:\s*#\d+\s*//\s*(\S+)\s*$")

# `         7: invokevirtual #10   // Method it/example/F11Packages$Helper.use:()Ljava/lang/String;`
INVOKE_RE = re.compile(
    r"^\s*\d+:\s+(invokevirtual|invokespecial|invokestatic|invokeinterface|invokedynamic)\s+"
    r"#\d+(?:,\s*\d+)?\s+//\s*(.*?)\s*$"
)
# `Method java/lang/Object."<init>":()V` — the owner is OMITTED for a call on the class itself, and
# EITHER half is quoted whenever it is not a valid Java identifier: the name for `"<init>"`, the
# owner for an array receiver, `"[Ltorture/Op;".clone:()Ljava/lang/Object;` (an array's `clone` is
# a real invokevirtual and the classfile API reports its owner as the array's internal name, so the
# two readers disagree by exactly that row if the quotes are not handled).
REF_HEAD_RE = re.compile(r"^(?:Interface)?Method\s+(.*)$")
# `InvokeDynamic #0:apply:()Ltorture/F06Functional$Sink;`
INDY_RE = re.compile(r"^InvokeDynamic\s+#(\d+):([\w<>$]+):(\(.*)$")

# In the BootstrapMethods table: `  0: #210 REF_invokeStatic java/lang/invoke/LambdaMetafactory...`
BSM_HEAD_RE = re.compile(r"^\s{2}(\d+):\s*#\d+\s+REF_\w+\s+([\w/$]+)\.[\w<>$]+:")
# `      #172 REF_invokeStatic torture/F06Functional.lambda$new$0:(Ltorture/...;)Ljava/lang/String;`
# `      #171 (Ltorture/F06Functional$Item;)Ljava/lang/String;`   <- a MethodType, not a handle
BSM_ARG_RE = re.compile(r"^\s{6}#\d+\s+(.*?)\s*$")
BSM_HANDLE_RE = re.compile(r"^REF_\w+\s+(.*)$")

# A member declaration: two-space indent, ends in `;`, and the next non-blank line is `descriptor:`.
DECL_RE = re.compile(r"^\s{2}\S.*;\s*$")
DESC_RE = re.compile(r"^\s{4}descriptor:\s*(\S+)\s*$")

LAMBDA_METAFACTORY = "java/lang/invoke/LambdaMetafactory"


def javap(class_files: list[Path]) -> list[str]:
    """Disassemble a BATCH of class files; returns one text block per class.

    `-p` private members, `-c` code, `-v` the constant pool and the BootstrapMethods table.

    Batched because this is a verification gate that runs on every subject, and one process per
    class file is ~400 process spawns on a small library and tens of thousands on a large one. A
    gate slow enough to be skipped is a gate that does not exist.
    """
    r = subprocess.run(["javap", "-p", "-c", "-v", *[str(p) for p in class_files]],
                       # latin-1: javap writes a modified-UTF-8 constant pool through a
                       # platform-encoded stream; under cp936 the decode raised, stdout was None,
                       # raw.javap.txt was empty and gate 1 reported "the two readers disagree"
                       # on commons-lang3, where they agree on all 9,473 instructions (#56).
                       # Every byte decodes under latin-1 and the reader only matches ASCII.
                       capture_output=True, text=True, encoding="latin-1", check=False)
    if r.returncode != 0 and not r.stdout:
        raise SystemExit(f"javap failed:\n{r.stderr}")
    # javap concatenates the classes, each starting with its own `Classfile <path>` banner.
    blocks: list[str] = []
    cur: list[str] = []
    for ln in r.stdout.splitlines():
        if ln.startswith("Classfile ") and cur:
            blocks.append("\n".join(cur))
            cur = []
        cur.append(ln)
    if cur:
        blocks.append("\n".join(cur))
    return blocks


def _split_ref(body: str, this_class: str) -> tuple[str, str, str] | None:
    """`owner.name:(desc)ret` -> (owner, name, `(desc)ret`), unquoting either half.

    Split on the `:` that begins the descriptor rather than on the first one: a quoted array owner
    contains `;` and a quoted `"<init>"` contains `<`, but neither contains `:(`.
    """
    k = body.find(":(")
    if k < 0:
        return None
    lhs, desc = body[:k], body[k + 1:]
    if lhs.endswith('"'):                      # the NAME is quoted: owner."<init>" or just "<init>"
        cut = lhs.rfind('."')
        if cut < 0:
            return this_class, lhs.strip('"'), desc
        return lhs[:cut].strip('"'), lhs[cut + 2:-1], desc
    cut = lhs.rfind(".")                       # internal names are slash-separated, so any `.` splits
    if cut < 0:
        return this_class, lhs, desc
    return lhs[:cut].strip('"'), lhs[cut + 1:], desc


def _bootstrap_targets(lines: list[str]) -> dict[int, str | None]:
    """bsm index -> "owner.name(desc)" of the implementation handle, or None when the bootstrap is
    not LambdaMetafactory (string concatenation, a record's `toString`, …)."""
    out: dict[int, str | None] = {}
    idx: int | None = None
    argno = 0
    in_table = False
    for ln in lines:
        if ln.startswith("BootstrapMethods:"):
            in_table = True
            continue
        if not in_table:
            continue
        if ln and not ln.startswith(" "):        # the table ended
            break
        head = BSM_HEAD_RE.match(ln)
        if head:
            idx = int(head.group(1))
            argno = 0
            out.setdefault(idx, None)
            if head.group(2) != LAMBDA_METAFACTORY:
                idx = None                        # record the index, but collect no target for it
            continue
        if re.match(r"^\s{4}Method arguments:", ln):
            argno = 0
            continue
        arg = BSM_ARG_RE.match(ln)
        if arg is None or idx is None:
            continue
        # args are (samMethodType, implMethod, instantiatedMethodType) — index 1 is the target
        h = BSM_HANDLE_RE.match(arg.group(1))
        if argno == 1 and h:
            ref = _split_ref(h.group(1), "")
            if ref is not None:
                out[idx] = f"{ref[0]}.{ref[1]}{ref[2]}"
        argno += 1
    return out


def _members(lines: list[str], this_class: str) -> list[tuple[int, str]]:
    """(line index of the declaration, `name+descriptor`) for every member javap printed."""
    simple = this_class.rsplit("/", 1)[-1]
    out: list[tuple[int, str]] = []
    for i, ln in enumerate(lines):
        if not DECL_RE.match(ln):
            continue
        desc = None
        for j in range(i + 1, min(i + 3, len(lines))):
            d = DESC_RE.match(lines[j])
            if d:
                desc = d.group(1)
                break
        if desc is None or not desc.startswith("("):
            continue                                    # a field, not a method
        body = ln.strip().rstrip(";")
        if body.startswith("static {}"):
            out.append((i, "<clinit>" + desc))
            continue
        before = body.split("(")[0].strip()
        token = before.split()[-1] if before.split() else ""
        # javap prints a constructor as the class's own (possibly `$`-qualified) name
        name = "<init>" if token.replace(".", "/") == this_class or token == simple else token
        out.append((i, name + desc))
    return out


def parse(text: str) -> set[str]:
    lines = text.splitlines()
    tc = next((m.group(1) for m in map(THIS_CLASS_RE.match, lines) if m), None)
    if tc is None:
        # a module-info or a block javap could not read; it contributes no invoke instructions
        return set()
    this_class = tc

    bsm = _bootstrap_targets(lines)
    members = _members(lines, this_class)
    if not members:
        return set()

    bounds = [(start, members[k + 1][0] if k + 1 < len(members) else len(lines))
              for k, (start, _) in enumerate(members)]

    rows: set[str] = set()
    for (start, sig), (_, end) in zip(members, bounds):
        frm = f"{this_class}.{sig}"
        for ln in lines[start:end]:
            m = INVOKE_RE.match(ln)
            if not m:
                continue
            op, comment = m.group(1).upper(), m.group(2)
            if op == "INVOKEDYNAMIC":
                d = INDY_RE.match(comment)
                if not d:
                    continue
                target = bsm.get(int(d.group(1)))
                if target is not None:
                    rows.add(f"{frm} | METHODREF_RAW | {target}")
                else:
                    rows.add(f"{frm} | INVOKEDYNAMIC | {d.group(2)}{d.group(3)}")
                continue
            h = REF_HEAD_RE.match(comment)
            if not h:
                continue
            ref = _split_ref(h.group(1), this_class)
            if ref is None:
                continue
            owner, name, desc = ref
            rows.add(f"{frm} | {op} | {owner}.{name}{desc}")
    return rows


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    root = Path(sys.argv[1])
    files = sorted(root.rglob("*.class"))
    if not files:
        print(f"no class files under {root}", file=sys.stderr)
        return 2
    rows: set[str] = set()
    BATCH = 80          # keeps the argv well inside ARG_MAX while amortising the process spawn
    for i in range(0, len(files), BATCH):
        for block in javap(files[i:i + BATCH]):
            rows |= parse(block)
    for r in sorted(rows):
        print(r)
    print(f"# raw invokes (deduplicated): {len(rows)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
