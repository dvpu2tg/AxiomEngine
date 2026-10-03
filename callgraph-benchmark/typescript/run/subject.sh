#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────────────────────
# ONE TYPESCRIPT SUBJECT, END TO END.
#
# The same four gates as Java, with one of them honestly weaker — and that difference is the whole
# reason this file does not just call the Java runner:
#
#   1  the checker is used CONSISTENTLY. Java compares two independent readers of one artefact and
#      thereby proves the bytecode was read right. TypeScript has exactly ONE implementation of its
#      type system, so there is no second reader to disagree with. What is checkable is that our two
#      entry points into it — `getResolvedSignature().declaration` and
#      `getSymbolAtLocation().declarations` — name the same code. That rules out a misuse of the
#      API, which is the failure mode available to us, and does NOT rule out a bug in the checker.
#   2  no two containers share a canonical name
#   3  the scorer itself can fail (mutation self-test)
#   4  every source file the tools read was also loaded by the checker. Ground truth for a file the
#      tools never saw — or a tool indexing a file the checker excluded — breaks the comparison in
#      the same two directions gate 4 guards in Java.
#
#   typescript/run/subject.sh torture
#   typescript/run/subject.sh <name> --heldout
# ─────────────────────────────────────────────────────────────────────────────────────────────
set -uo pipefail
# `comm`/`sort` need one collation and the oracle's lists are in code-point order; under
# en_US.UTF-8 typedoc's upper-case file names sorted differently and gate 4 reported 46 files
# "absent from the source tree" that were there (issue #29 §1)
export LC_ALL=C

LANG_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ROOT="$(cd "$LANG_DIR/.." && pwd)"
LANGUAGE="$(basename "$LANG_DIR")"
cd "$ROOT"

say()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
die()  { printf '\n\033[31mFAIL: %s\033[0m\n' "$*" >&2; exit 1; }

[ "${1:-}" = "--list" ] && { python3 bench/subject_info.py --list --language "$LANGUAGE" dummy; exit 0; }
NAME="${1:?usage: typescript/run/subject.sh <subject> [--heldout]}"
shift || true
ALLOW=""
for arg in "$@"; do [ "$arg" = "--heldout" ] && ALLOW="--allow-heldout"; done

INFO="$(python3 bench/subject_info.py "$NAME" --language "$LANGUAGE" $ALLOW)" || exit $?
eval "$INFO"

TSX="$ROOT/.tools/ts/node_modules/.bin/tsx"
[ -x "$TSX" ] || die "TypeScript toolchain missing — run typescript/install.sh"
export NODE_PATH="$ROOT/.tools/ts/node_modules"

if [ -n "${NEEDS_FETCH:-}" ]; then
  python3 "$LANG_DIR/subjects/fetch.py" "$SUBJECT" || die "fetch failed"
fi
PROJECT="${PROJECT_PATH:-$LANG_DIR/${PROJECT_FILE:-subjects/$SUBJECT/tsconfig.json}}"
[ -f "$PROJECT" ] || die "no tsconfig at $PROJECT"
if [ -n "${PROJECT_OVERRIDES:-}" ]; then
  # the registry's overrides, as a config that extends the project's own, written BESIDE it so
  # relative paths mean what they would in the original (issue #28 §4)
  DERIVED="$(dirname "$PROJECT")/tsconfig.callgraph-benchmark.json"
  python3 - "$PROJECT" "$DERIVED" "$PROJECT_OVERRIDES" <<'DERIVE'
import json, os, sys
base, dst, ov = sys.argv[1], sys.argv[2], json.loads(sys.argv[3])
cfg = {"extends": "./" + os.path.basename(base)}
cfg.update(ov)
json.dump(cfg, open(dst, "w"), indent=2)
DERIVE
  echo "  project overrides from the registry: $PROJECT_OVERRIDES"
  PROJECT="$DERIVED"
fi
if [ "${PRIOR_INTERNAL_USE:-}" = "1" ]; then
  # A project the tool was DEVELOPED AGAINST cannot also be neutral ground for measuring
  # it. The run proceeds — the team's split names these projects — but the warning is
  # printed here and the flag travels into the report, so the number is never read as if it
  # came from somewhere the tool had not seen.
  printf '\033[33m  PRIOR INTERNAL USE — this project is in the engine\x27s own TS corpus;\n'
  printf '  a number from it measures agreement with a project the tool was built against.\033[0m\n'
fi

W="$WORK"; EDGES="$W/edges"
mkdir -p "$W"
export LANG_DIR LANGUAGE WORK="$W"

OC() { "$TSX" --no-cache "$LANG_DIR/oracle/ts-ground-truth.ts" --project "$PROJECT" --root "$SRC_DIR" "$@"; }

say "subject: $SUBJECT  [$SPLIT / $KIND]"
[ "$SPLIT" = heldout ] && printf '\033[33m  HELD OUT — score once, report the finding, do not tune against it.\033[0m\n'
echo "  $(find "$SRC_DIR" \( -name '*.ts' -o -name '*.tsx' -o -name '*.mts' -o -name '*.cts' \) -not -path '*/node_modules/*' | wc -l | tr -d ' ') source files"

# ── GATE 4: the checker and the tools see the same program ───────────────────────────────────
# Java can compare a source tree against a jar and demand they correspond. TypeScript has no second
# artefact — the CHECKER'S PROGRAM is the definition of what the subject is. So instead of demanding
# that a repository's file layout happen to match a tsconfig, the tools are given exactly the file
# set the checker loaded, and whatever that pruned is REPORTED.
#
# The direction that matters is unchanged and is the reason this exists: a tool indexing a file the
# checker never loaded has no ground truth to be scored against, and every edge it finds there is a
# false positive it did not earn. Real projects hit this constantly — typedoc's browser assets have
# their own DOM-targeted config, kysely ships an example app its config excludes.
say "gate 4/4 — the tools are given exactly the program the checker loaded"
OC --mode files > "$W/checker-files.txt" 2>/dev/null
# Every extension TypeScript compiles, not just `.ts` — typedoc ships `.cts` locale modules and
# `.tsx` plugins, and looking for `.ts` alone made 39 files the checker had loaded look like files
# that did not exist.
find "$SRC_DIR" \( -name '*.ts' -o -name '*.tsx' -o -name '*.mts' -o -name '*.cts' \) \
  -not -name '*.d.ts' -not -path '*/node_modules/*' \
  | sed "s|^$SRC_DIR/||" | sort > "$W/tool-files.txt"
PRUNED="$(comm -13 "$W/checker-files.txt" "$W/tool-files.txt" | wc -l | tr -d ' ')"
MISSING="$(comm -23 "$W/checker-files.txt" "$W/tool-files.txt" | wc -l | tr -d ' ')"
echo "  checker program: $(wc -l < "$W/checker-files.txt" | tr -d ' ') files"
echo "  pruned from the tools' view (not in the checker's program): $PRUNED"
comm -13 "$W/checker-files.txt" "$W/tool-files.txt" | head -4 | sed 's/^/      /'
[ "$MISSING" -gt 0 ] && die "the checker loaded $MISSING file(s) absent from the source tree"

# THE REST OF THE PROGRAM (issue #20). A monorepo package imports its siblings through `paths`
# (`@excalidraw/element` → `../element/src`), and the checker types every receiver that comes
# from them. Those files are not the subject — nothing in them is scored — but a tool that cannot
# see them cannot type what the checker typed, uniformly, for every tool. So the copy the tools
# index is rooted ONE COMMON ANCESTOR UP when the program has files outside the subject, with the
# subject at `$SUBJECT_SUBDIR` inside it and the siblings beside it; the tools' module paths then
# carry that prefix and the scorer strips it (`--module-prefix`). tests/ and dtslint/ trees a
# tsconfig happens to include arrive the same way — context, never scored.
OC --mode program > "$W/program-extra.txt" 2>/dev/null || : > "$W/program-extra.txt"
EXTRA="$(grep -c . "$W/program-extra.txt" || true)"
TOOLSRC="$W/subject-src"
rm -rf "$TOOLSRC"; mkdir -p "$TOOLSRC"
SUBJECT_SUBDIR=""
ANCESTOR="$SRC_DIR"
if [ "$EXTRA" -gt 0 ]; then
  UP="$(python3 -c '
import sys
m=0
for ln in open(sys.argv[1]):
    ln=ln.strip(); n=0
    while ln.startswith("../"): ln=ln[3:]; n+=1
    m=max(m,n)
print(m)' "$W/program-extra.txt")"
  ANCESTOR="$SRC_DIR"; for _ in $(seq 1 "$UP"); do ANCESTOR="$(dirname "$ANCESTOR")"; done
  SUBJECT_SUBDIR="$(python3 -c 'import os,sys;print(os.path.relpath(sys.argv[1],sys.argv[2]))' "$SRC_DIR" "$ANCESTOR")"
  echo "  program files outside the subject: $EXTRA — tools index from $(basename "$ANCESTOR")/, subject at $SUBJECT_SUBDIR/"
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    rel="$(python3 -c 'import os,sys;print(os.path.relpath(os.path.join(sys.argv[1],sys.argv[2]),sys.argv[3]))' "$SRC_DIR" "$f" "$ANCESTOR")"
    mkdir -p "$TOOLSRC/$(dirname "$rel")" || die "staging the tools' copy: mkdir failed for $rel"
    cp "$SRC_DIR/$f" "$TOOLSRC/$rel" || die "staging the tools' copy: cp failed for $f (disk full?)"
  done < "$W/program-extra.txt"
fi
SUBJ_COPY="$TOOLSRC${SUBJECT_SUBDIR:+/$SUBJECT_SUBDIR}"
mkdir -p "$SUBJ_COPY"
# EVERY COPY IS CHECKED (#83): a copy that fails half-way — the disk filled once — used to pass
# gate 4 and score every tool on a partial program (axiom 89.8% → 45.6% on excalidraw, with
# nothing in the report saying the input was wrong)
while IFS= read -r f; do
  [ -n "$f" ] || continue
  mkdir -p "$SUBJ_COPY/$(dirname "$f")" || die "staging the tools' copy: mkdir failed for $f"
  cp "$SRC_DIR/$f" "$SUBJ_COPY/$f" || die "staging the tools' copy: cp failed for $f (disk full?)"
done < "$W/checker-files.txt"
# and the COPY is compared with what the checker loaded — not the original tree, which is what
# gate 4 above compared and which says nothing about the copy
{ sed "s|^|${SUBJECT_SUBDIR:+$SUBJECT_SUBDIR/}|" "$W/checker-files.txt"
  while IFS= read -r f; do [ -n "$f" ] && python3 -c 'import os,sys;print(os.path.relpath(os.path.join(sys.argv[1],sys.argv[2]),sys.argv[3]))' "$SRC_DIR" "$f" "$ANCESTOR"; done < "$W/program-extra.txt"
} | sort > "$W/expected-copy.txt"
( cd "$TOOLSRC" && find . -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.mts' -o -name '*.cts' -o -name '*.d.ts' \) | sed 's|^\./||' | sort ) > "$W/actual-copy.txt"
COPY_MISSING="$(comm -23 "$W/expected-copy.txt" "$W/actual-copy.txt" | wc -l | tr -d ' ')"
if [ "$COPY_MISSING" != 0 ]; then
  comm -23 "$W/expected-copy.txt" "$W/actual-copy.txt" | head -5 | sed 's/^/      /'
  die "the tools' copy is missing $COPY_MISSING of the files the checker loaded — the copy failed"
fi
# the copy's identity travels into the manifest: its file count and the SHA-256 of its sorted file list
COPY_FILES="$(wc -l < "$W/actual-copy.txt" | tr -d ' ')"
COPY_SHA="$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$W/actual-copy.txt")"
printf 'files\t%s\nsha256\t%s\n' "$COPY_FILES" "$COPY_SHA" > "$W/staged-copy.txt"
# The pruned copy needs a tsconfig the TOOLS can use, and the original's `include`/`files` are
# written against the REPOSITORY's layout — copying it into a flattened copy matches nothing, and a
# tool that reads it then indexes zero files and scores zero. That is a harness failure wearing the
# costume of a result, so the config is SYNTHESISED: the original's compilerOptions, with an include
# that matches the pruned tree.
#
# `paths` is NOT dropped. It is how a project spells its own modules — type-graphql imports itself as
# `@/errors`, `@/metadata/getMetadataStorage`, and its tsconfig maps `@/*` to `./src/*`. The first
# version of this synthesis stripped `paths` with the other build-only keys, so every tool that
# resolves imports (all but one) saw ~200 unresolvable internal imports, typed nothing through them,
# and resolved 133 of 682 calls: axiom 25.6% exact, codeql 38.5% recall, on a subject the same tools
# score 60–70% on elsewhere. That was the harness punishing a project for its layout — the exact
# thing this benchmark is not allowed to do. The mappings are kept and RE-ROOTED at the pruned copy
# (which is rooted at SRC_DIR, not at the tsconfig's directory); a mapping that points outside the
# scored tree is dropped and named, because nothing at that path exists in the copy.
python3 - "$PROJECT" "$TOOLSRC/tsconfig.json" "$ANCESTOR" <<'GENCFG'
import json, os, re, sys
src, dst, root = sys.argv[1], sys.argv[2], os.path.realpath(sys.argv[3])
raw = open(src, encoding="utf-8").read()
# tsconfig is JSON-with-comments. Comments are stripped by a character scan that knows where the
# STRINGS are: the regex this replaced read `"@/*": ["./src/*"]` … `"src/**/*.ts"` as one block
# comment, threw the whole config away, and handed the tools a tsconfig with NO compilerOptions —
# silently, because the parse failure fell back to `{}`. A parse failure is now fatal.
def strip_jsonc(text):
    out, i, n = [], 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1]); i += 2; continue
            if c == '"':
                in_str = False
            i += 1; continue
        if c == '"':
            in_str = True; out.append(c); i += 1; continue
        if text.startswith("//", i):
            j = text.find("\n", i); i = n if j < 0 else j; continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2); i = n if j < 0 else j + 2; continue
        out.append(c); i += 1
    return "".join(out)
def load_cfg(path):
    text = strip_jsonc(open(path, encoding="utf-8").read())
    text = re.sub(r",(\s*[}\]])", r"\1", text)
    try:
        return json.loads(text)
    except Exception as e:
        raise SystemExit(f"tsconfig at {path} did not parse after comment stripping: {e}")
# `extends` IS RESOLVED, base first, the way tsc resolves it. kysely's tsconfig is three lines
# over a base; excalidraw's package config extends `../tsconfig.base.json`, which is where
# `jsx: react-jsx` and every `@excalidraw/*` path mapping live. Dropping `extends` as a build-only
# key handed the tools two compilerOptions for a .tsx code base. `baseUrl` and relative `paths`
# in a base config are relative to THAT file, so each level is re-rooted before merging.
def resolve_chain(path, seen=()):
    path = os.path.realpath(path)
    if path in seen:
        return {}
    cfg = load_cfg(path)
    merged = {}
    ext = cfg.get("extends")
    for e in (ext if isinstance(ext, list) else [ext] if ext else []):
        cand = os.path.join(os.path.dirname(path), e)
        if not os.path.isfile(cand) and os.path.isfile(cand + ".json"):
            cand = cand + ".json"
        if not os.path.isfile(cand):
            print(f"  tsconfig extends: {e!r} not found next to {os.path.basename(path)} — skipped")
            continue
        merged.update(resolve_chain(cand, seen + (path,)))
    own = dict(cfg.get("compilerOptions") or {})
    here = os.path.dirname(path)
    if "baseUrl" in own:
        own["baseUrl"] = os.path.realpath(os.path.join(here, own["baseUrl"]))
    if "paths" in own:
        b = own.get("baseUrl") or merged.get("baseUrl") or here
        own["paths"] = {k: [os.path.realpath(os.path.join(b, t)) for t in v] for k, v in own["paths"].items()}
    merged.update(own)
    return merged
opts = resolve_chain(src)
base = opts.get("baseUrl") or os.path.dirname(os.path.realpath(src))
paths = {}
for pat, targets in (opts.get("paths") or {}).items():
    kept = []
    for t in targets:
        abs_t = os.path.realpath(os.path.join(base, t))
        # the `*` in a target is not a path component; re-root the prefix before it
        head = abs_t.split("*", 1)[0]
        if head.startswith(root + os.sep) or head == root:
            rel = os.path.relpath(abs_t, root)
            kept.append("./" + rel if not rel.startswith(".") else rel)
        else:
            print(f"  tsconfig paths: dropped {pat!r} -> {t!r} (outside the scored tree)")
    if kept:
        paths[pat] = kept
# `typeRoots` / `types` are NOT build-only: they decide which ambient declarations the program
# sees, and dropping them handed the tools a program the checker did not have — 45 typedoc calls
# the ground truth resolves were unresolvable under the tools' config (#76). Kept, re-rooted at
# the pruned copy like `paths`; an entry pointing outside the scored tree is dropped and printed.
type_roots = []
for tr in (opts.get("typeRoots") or []):
    abs_tr = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(src)), tr)) if not os.path.isabs(tr) else tr
    if abs_tr.startswith(root + os.sep) or abs_tr == root:
        rel = os.path.relpath(abs_tr, root)
        type_roots.append("./" + rel if not rel.startswith(".") else rel)
    else:
        print(f"  tsconfig typeRoots: dropped {tr!r} (outside the scored tree)")
types = opts.get("types")
for k in ("typeRoots", "types", "paths", "baseUrl", "rootDir", "outDir", "tsBuildInfoFile",
          "incremental", "composite", "project", "extends"):
    opts.pop(k, None)
if type_roots:
    opts["typeRoots"] = type_roots
if types is not None:
    opts["types"] = types
if type_roots or types is not None:
    print(f"  tsconfig typeRoots/types: kept ({len(type_roots)} root(s), types={types!r})")
if paths:
    opts["baseUrl"] = "."
    opts["paths"] = paths
    print(f"  tsconfig paths: kept {len(paths)} mapping(s), re-rooted at the pruned copy")
opts.setdefault("skipLibCheck", True)
opts.setdefault("noEmit", True)
json.dump({"compilerOptions": opts, "include": ["**/*"]}, open(dst, "w"), indent=2)
GENCFG
[ -f "$SRC_DIR/package.json" ] && cp "$SRC_DIR/package.json" "$SUBJ_COPY/" 2>/dev/null
[ -n "$SUBJECT_SUBDIR" ] && [ -f "$ANCESTOR/package.json" ] && cp "$ANCESTOR/package.json" "$TOOLSRC/" 2>/dev/null
export SUBJECT_SUBDIR
printf '%s\n' "$SUBJECT_SUBDIR" > "$W/subject-subdir.txt"
# ONLY THE TOOLS read the pruned copy. The ORACLE stays rooted at the original tree, because the
# checker's program is defined by the real tsconfig against the real paths — re-rooting it at a copy
# put every file outside its own root and produced a subject with zero resolvable calls.
TOOL_SRC="$TOOLSRC"
# CORE TYPESCRIPT ONLY. A subject with .js in its scored tree is measuring two languages at once —
# the checker resolves through .js with far less information, and no tool here is being evaluated
# for JavaScript. The count is printed every run; a non-zero count is a reason to move the subject
# to `blocked`, not a number to absorb.
JS_IN_TREE="$(find "$SRC_DIR" \( -name '*.js' -o -name '*.mjs' -o -name '*.cjs' -o -name '*.jsx' \) -not -path '*/node_modules/*' | wc -l | tr -d ' ')"
echo "  TypeScript purity: $JS_IN_TREE JavaScript file(s) in the scored tree$( [ "$JS_IN_TREE" = 0 ] && echo ' — 100% TypeScript' )"
echo "  OK: the tools' copy holds every file the checker loaded ($COPY_FILES files, list sha256 ${COPY_SHA:0:12}…)"

# ── GATE 0: can the checker read this subject at all? ────────────────────────────────────────
say "gate 0 — checker resolution coverage"
OC --mode coverage > "$W/coverage.txt" 2>"$W/coverage.err"
sed 's/^/  /' "$W/coverage.txt"
COV="$(awk -F'\t' '$1=="resolved_pct"{print int($2)}' "$W/coverage.txt")"
# the floor is a protocol constant, not an environment knob (#67 §7)
MINCOV=55
if [ "${COV:-0}" -lt "$MINCOV" ]; then
  die "the checker resolved only ${COV}% of this subject's call expressions (floor ${MINCOV}%).
     Every score would be conditional on that rather than on the tools. Fix the tsconfig, or
     record the subject as blocked with the reason — do not score it."
fi
echo "  OK: ${COV}% (floor ${MINCOV}%)"

# ── ground truth ─────────────────────────────────────────────────────────────────────────────
say "building ground truth"
OC --mode sites      > "$W/gt.sites.jsonl"  2>/dev/null
OC --mode containers > "$W/gt.classes.txt"  2>/dev/null
OC --mode methods    > "$W/gt.methods.txt"  2>/dev/null
# The neutral zones: call sites where the oracle declares it has NO ground truth (a call through a
# function value) and constructors of classes that declare none. Applied to every tool's output —
# see bench/score.py. Without this a tool that resolves a function value is charged a false positive
# for being more capable than the oracle.
OC --mode excluded   > "$W/gt.excluded.txt"  2>/dev/null
OC --mode heritage   > "$W/gt.heritage.txt"  2>/dev/null
OC --mode defaults   > "$W/gt.defaults.txt"  2>/dev/null
echo "  $(wc -l < "$W/gt.sites.jsonl" | tr -d ' ') call sites, $(wc -l < "$W/gt.classes.txt" | tr -d ' ') containers, $(wc -l < "$W/gt.methods.txt" | tr -d ' ') methods"

say "gate 1/4 — the checker is used consistently (two entry points agree)"
OC --mode crosscheck > "$W/crosscheck.txt" 2>"$W/crosscheck.err" || {
  head -10 "$W/crosscheck.txt"; die "two checker entry points name different code"; }
tail -1 "$W/crosscheck.err" | sed 's/^/  /'
echo "  NOTE: weaker than the Java gate — TypeScript has one type-system implementation, so this"
echo "        proves our USE of the checker, not the checker itself."

say "gate 2/4 — canonical container names are unambiguous"
OC --mode collisions > "$W/collisions.txt" 2>/dev/null
[ -s "$W/collisions.txt" ] && { head -10 "$W/collisions.txt"; die "two containers share a canonical name"; }
echo "  OK: no collisions"

# ── the unit tests: one filed issue's edge case each (tests/) ─────────────────────────────
say "gate 3a — unit tests (tests/)"
if UT="$(bash bench/test.sh -q 2>&1)"; then echo "$UT" | tail -1 | sed 's/^/  /'; else
  echo "$UT" | tail -25; die "unit tests failed — run bash bench/test.sh"; fi

say "gate 3/4 — the scorer can fail (mutation self-test)"
python3 bench/selftest.py --sites "$W/gt.sites.jsonl" --classes "$W/gt.classes.txt" \
        --methods "$W/gt.methods.txt" --source "$SRC_DIR" --language "$LANGUAGE" \
        --excluded "$W/gt.excluded.txt" --heritage "$W/gt.heritage.txt" --defaults "$W/gt.defaults.txt" \
        || die "scorer self-test failed"

# ── tools ────────────────────────────────────────────────────────────────────────────────────
# TOOLS="axiom codeql" re-runs only those; the other tools' rows and timings from the previous run
# are KEPT and re-scored against the (possibly re-read) ground truth. Without it, re-measuring one
# tool after updating its checkout meant re-running six.
TOOLS="${TOOLS:-cha axiom codeql codegraph code_review_graph gitnexus graphify}"
if [ "$TOOLS" = "cha axiom codeql codegraph code_review_graph gitnexus graphify" ]; then
  rm -rf "$EDGES"; mkdir -p "$EDGES"
  : > "$W/timings.tsv"; : > "$W/timings-parts.tsv"
else
  mkdir -p "$EDGES"; touch "$W/timings.tsv"
  for t in $TOOLS; do
    for d in "$EDGES/$t" "$EDGES/$(echo "$t" | tr _ -)" "$EDGES/$t"-* "$EDGES/$(echo "$t" | tr _ -)"-*; do rm -rf "$d"; done
    [ "$t" = cha ] && rm -rf "$EDGES/ideal"
    grep -v "^$t	" "$W/timings.tsv" > "$W/timings.tsv.new" 2>/dev/null || true; mv "$W/timings.tsv.new" "$W/timings.tsv"
    grep -v "^$t	" "$W/timings-parts.tsv" > "$W/timings-parts.tsv.new" 2>/dev/null || true; mv "$W/timings-parts.tsv.new" "$W/timings-parts.tsv"
  done
fi
AXIOM_ENGINE="${AXIOM_ENGINE:-$ROOT/../../AxiomEngine/wt/bench-engine}"
# the parser lives inside the engine repository since it was reshaped into one tree (#469);
# the separate checkout is the fallback for an older engine
if [ -z "${AXIOM_PARSER:-}" ]; then
  AXIOM_PARSER="$AXIOM_ENGINE/parser/dist/index.js"
  [ -f "$AXIOM_PARSER" ] || AXIOM_PARSER="$ROOT/../../AxiomEngine/wt/bench-parser/dist/index.js"
fi
export AXIOM_PARSER AXIOM_ENGINE PROJECT SUBJECT_SRC="${TOOL_SRC:-$SRC_DIR}"

for t in $TOOLS; do
  [ -x "$LANG_DIR/adapters/$t/run.sh" ] || continue
  say "tool: $t"
  # WARM FIRST (issue #42): a tool's one-time cost — axiom's Soufflé compile, CodeQL's query
  # compile — is paid here, timed on its own, and recorded as `cold_seconds` with whether the
  # tool's cache was hit. `seconds` is then the warm run, the same for the first subject of a
  # session as for the tenth.
  if [ -x "$LANG_DIR/adapters/$t/warm.sh" ]; then
    C0=$(python3 -c 'import time;print(time.time())')
    CACHE=$(bash "$LANG_DIR/adapters/$t/warm.sh" "$LANG_DIR" 2>/dev/null | grep -o 'cache=[a-z]*' | tail -1 || true)
    CL=$(python3 -c "import time;print(round(time.time()-$C0,2))")
    echo "  warm-up ${CL}s (${CACHE:-cache=unknown})"
    grep -v "^$t	" "$W/warmup.tsv" > "$W/warmup.tsv.new" 2>/dev/null || true; mv "$W/warmup.tsv.new" "$W/warmup.tsv"
    printf '%s\t%s\t%s\n' "$t" "$CL" "${CACHE#cache=}" >> "$W/warmup.tsv"
  fi
  T0=$(python3 -c 'import time;print(time.time())')
  bash "$LANG_DIR/adapters/$t/run.sh" "$LANG_DIR" "$SUBJECT" "${TOOL_SRC:-$SRC_DIR}" \
    || echo "  !! $t failed — reported as absent, never as zero"
  EL=$(python3 -c "import time;print(round(time.time()-$T0,2))")
  echo "  ${EL}s"
  printf '%s\t%s\n' "$t" "$EL" >> "$W/timings.tsv"
done

# THE TOOL UNDER TEST MUST HAVE RUN. The axiom adapter skips itself when the parser or engine is
# not found, and a fresh checkout then produced a complete-looking report with no axiom row
# (#72 §2). Refuse, unless the caller says the omission is intended.
case " $TOOLS " in *" axiom "*)
  [ -f "$EDGES/axiom/$SUBJECT.jsonl" ] || [ -n "${ALLOW_MISSING_AXIOM:-}" ] \
    || die "axiom produced no rows (parser/engine not found?) — set AXIOM_PARSER / AXIOM_ENGINE, or ALLOW_MISSING_AXIOM=1 to score without it";;
esac

say "scoring"
FAM=""; [ -n "$FAMILIES" ] && FAM="--families"
python3 bench/run.py --subject "$SUBJECT" --language "$LANGUAGE" \
  --sites "$W/gt.sites.jsonl" --classes "$W/gt.classes.txt" --methods "$W/gt.methods.txt" \
  --excluded "$W/gt.excluded.txt" --heritage "$W/gt.heritage.txt" --defaults "$W/gt.defaults.txt" --coverage "$W/coverage.txt" --edges-dir "$EDGES" --source "$SRC_DIR" \
  --timings "$W/timings.tsv" --warmup "$W/warmup.tsv" --timing-parts "$W/timings-parts.tsv" --staged-copy "$W/staged-copy.txt" ${PRIOR_INTERNAL_USE:+--prior-internal-use} ${SUBJECT_SUBDIR:+--module-prefix "$SUBJECT_SUBDIR/"} \
  --out "$RESULTS" $FAM || die "scoring failed"

say "done — $RESULTS/report.md"
