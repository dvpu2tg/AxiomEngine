# Call-graph benchmark

*Java and TypeScript; the harness is language-agnostic below the oracle, and other languages follow.*

**How well does a code-graph tool actually resolve a call — to the one concrete method, or to a
set?** Measured against ground truth read from compiled bytecode (Java, the JDK's own class-file
parser) or from the compiler's type checker (TypeScript), with every tool's output structure
accommodated rather than penalised.

```bash
java/run/subject.sh --list              # the registered subjects and their dev / held-out split
java/run/subject.sh spring-boot         # obtain, verify ground truth, run every tool, score, report
typescript/run/subject.sh excalidraw
java/run/verify.sh spring-boot          # re-run everything; assert it reproduces byte-for-byte
TOOLS="axiom" java/run/subject.sh rxjava   # re-run one tool, re-score against the others' kept rows
python3 bench/readme_tables.py --write  # regenerate the README matrices and docs/RESULTS.md
```

---

## What is being measured

For every call written in a subject's source, the benchmark asks which method a tool says it
reaches, and compares that against three bounds read from the `.class` files the subject's own build
produced:

| bound | meaning |
|---|---|
| **CERTAIN** | the target the invoke instruction declares — a miss here is undeniable |
| **POSSIBLE** | plus the sound class-hierarchy dispatch envelope — an answer outside it is a demonstrable false positive |
| **RTA** | the envelope restricted to types the application actually instantiates — tighter, more realistic, unsound in principle |

From those come precision, `prec-strict`, `recall_certain`, `recall_possible`, `recall_rta`, strict F1/MCC — and the
metric the benchmark is built around:

> Of the call sites where the language admits **exactly one** target, how many did the tool link to
> that one concrete method, versus handing back a set, versus getting it wrong, versus missing it?

An aggregate precision figure cannot answer that, and it is the question that decides whether a call
graph is usable for change-impact or reachability.

---

## Why the ground truth can be trusted

Everything every tool is scored on comes out of one reader, so a bug in it is not a wrong number —
it is a wrong benchmark. Three gates run **before** any tool is scored, and all three are fatal:

1. **Two independent readers agree.** `oracle/ClassfileGroundTruth.java` (`java.lang.classfile`,
   JEP 484) and `oracle/javap_reader.py` (the JDK disassembler, no shared code) must agree on every
   invoke instruction, at the raw layer, before any convention is applied. On the torture subject
   that is **every invoke instruction, identical** (the count is printed by each run; the number in this sentence was stale twice).
2. **No two application types share a canonical name.** Otherwise both bounds would be computed over
   a type that does not exist. (This is not hypothetical — the flattening convention some IRs use
   collides two distinct `Node` types in a 592-line subject.)
3. **The scorer can fail.** `bench/selftest.py` builds eight synthetic tools out of the ground truth,
   each broken in one known way, and asserts the score says so — including two *fairness* mutations
   that must **not** lose points. A harness that cannot fail proves nothing when it passes.

The conventions layer is additionally cross-checked against a third, independently written
class-file reader (the engine's own), which agrees on both bounds exactly.

---

## Not punishing a tool for its output structure

The tools disagree about what a call edge even is:

```
java.lang.classfile / CodeQL   torture.Shape#area(int)     owner + name + erased params
axiom-code-graph               torture.Shape#area(int)     owner + name + params
tree-sitter indexers           Shape.area                  owner + name, no params
some graph exporters           area                        a bare symbol name
```

Scoring all four against a signature-exact oracle would report the last two as near-zero — a fact
about our scoring choice, not about those tools. So:

* **Every comparison happens at a fidelity tier, and the ground truth is projected to that tier
  too.** At Tier B the oracle stops distinguishing overloads as well, so a tool that cannot spell
  parameter types is not being asked to. The headline is Tier B, the highest fidelity every tool can
  express.
* **A tier above a tool's ceiling reads `n/a`, never `0`.** A blank and a zero mean opposite things.
* **Notation is read, not repaired.** `pkg.Outer$Inner`, `pkg.Outer.Inner`, `Inner`, and
  (file + symbol) all resolve to one type. A reference matching *more than one* application type is
  excluded and **counted in the same table row as the score**, so an exclusion can never be a way to
  look good by answering less.
* **A type-less reference is scoped by name, not discarded** — otherwise a name-only tool's every
  row would be deleted before scoring and reported as "found nothing".
* **A tool is given the project the way the project spells itself.** In TypeScript the tools get
  the checker's file set with a synthesised tsconfig that keeps the project's `paths` mappings —
  the first version dropped them, and CodeQL read 38% recall on type-graphql instead of 89% (#14).
  An anonymous function is named by the binding the source gives it, on both sides (#15).

`docs/PROTOCOL.md` is the normative statement of all of it.

---

## Layout

```
bench/                the language-neutral core: canonical schema, resolver, metrics, report,
                      the mutation self-test, the README/RESULTS generator
<lang>/subjects/      the registry (pinned coordinates + SHA-256, dev / held-out / blocked split)
<lang>/oracle/        ground truth — java.lang.classfile + the independent javap reader (Java);
                      the type checker, two entry points cross-checked (TypeScript)
<lang>/adapters/      one per tool — each turns that tool's native output into the canonical schema
<lang>/run/           end-to-end, gated, manifested
<lang>/results/       committed reports and scores, with a SHA-256 manifest of every input
docs/                 PROTOCOL.md (every definition and the evidence for every exclusion),
                      CROSS-LANGUAGE.md, AUDIT.md, RESULTS.md (generated)
tests/                one filed issue's edge case each, in milliseconds — gate 3a of every run
```

Four speeds, and the slow one is for final benchmarking only:

```
bash bench/test.sh                          unit tests (seconds)          — after every change
bash bench/rescore.sh <lang> <subject>      re-score from disk (seconds)  — scorer, resolver, report
TOOLS=cha bash <lang>/run/subject.sh <s>    ground truth + gates (minutes) — oracle change, tools kept
bash <lang>/run/subject.sh <s>              everything                     — adapters, tools, final numbers
bash <lang>/run/verify.sh <s>               before a number is cited
```

An adapter is the only place a tool's native format is touched. It may shell out, read a SQLite
file or scrape a report; none of that reaches the scorer, which sees only canonical JSONL.

---

## Status

**Phase 1 — deterministic tools: done**, five real projects per language plus a diagnostic
`torture` subject each, every subject through every gate. **Phase 2 — held out:** `hibernate-core`,
`tomcat-embed-core` (Java) and the team's held-out TypeScript list are registered and unrun; a bad
result there is a finding to report, not a rule to adjust (`docs/PROTOCOL.md` §9). **Phase 3 —
agent-driven tools** (Understand-Anything, LLM-backed modes): not started; run N times, reported in
a separate tier with variance, never averaged into these tables.

| tool | tier | `needs` | what it is |
|---|---|---|---|
| `axiom-code-graph` | A | source only (`AxiomEngine`, both languages; Java id `axiom-nolib`) · source + platform IR (`AxiomEngine + libraries`, Java id `axiom`, not ranked) | the tool this benchmark was written to measure; parser and engine `2163292b` (one repository since #469; `origin/main` at run time), recorded per row |
| CodeQL | A | compiled build (`torture`) · build-mode=none (the five Maven subjects: the sources jar, no build, dependencies absent) · source only (TS) | two rows in Java: `codeql` = `getCallee()`, `codeql-dispatch` = `viableCallable()`; TS rows carry its `imprecision` grade |
| WALA 1.6.7 | — | bytecode | `java/adapters/wala` exists (CHA / RTA / 0-CFA rows, issue #6/#25) but is **not in the comparison**: Java-only, and withdrawn at the user's request |
| `colbymchenry/codegraph` | A | source only | SQLite index; the one tree-sitter tool here that records a parameter list; carries `resolvedBy:confidence` |
| `tirth8205/code-review-graph` | B | source only | SQLite index; `EXTRACTED`/`INFERRED` |
| GitNexus | B | source only | LadybugDB via Cypher; ids carry arity, not parameter types; carries `reason:confidence` |
| Graphify | B | source only | deterministic `update --no-cluster` AST path, no LLM; `EXTRACTED`/`INFERRED`. Graphify's own published benchmarks are LLM-memory retrieval (LOCOMO, LongMemEval), a different task; its graph carries `contains` / `imports` / `references` / `method` / `calls` relations and only the `calls` relation asserts a call, so only that is scored here. Its `path` command walks every relation: on the torture subject `path describe area` answers `F01Polymorphism --contains--> Square`, a navigation hop, not the call chain |
| *`cha-null`* | — | bytecode / checker | the **null model**: the whole CHA envelope at every site, resolving nothing; a floor, never ranked |
| *`ideal`* | — | oracle | the **reference**: the correct answer for every link group; a ceiling, never ranked, and the calibration of the adjusted column |

### Results

One matrix per language. Every number is generated from `*/results/*/scores.json` by
`bench/readme_tables.py` — a number cannot appear here that the JSON does not contain — and the
full per-subject tables (precision, `prec-strict`, three recalls, the five verdict buckets, time,
`needs`, the null-model row) are in [`docs/RESULTS.md`](docs/RESULTS.md).

<!-- results:begin -->

**Calls with exactly one target, and how many of them each tool linked to it** (Tier B). The
unit is a `(caller, callee-name)` group with one possible target: the first row is what the
ground truth found — how many such groups per subject — and every tool cell is a count of those
the tool got right, with the percentage under it; the last column sums the five. A method that
calls two different one-target methods of the same name (`new A()` and `new B()`) forms one
pooled group that is not counted here; those are counted beside the ambiguous table in each
report (#70). Five real projects per language. The
counts behind every percentage — found / fan / polluted / wrong / missed against the ground
truth's own number of calls — are in the verdict tables below; every other column (precision,
strict precision, three recalls, time, `needs`) is in [`docs/RESULTS.md`](docs/RESULTS.md), generated from the
same JSON. The first row is the ground truth's own count of such calls. The CHA envelope
answer (`cha-null`) scores 100 on exact% by construction and is printed as the floor row; the
bounds table below is where an enumerator and a resolver come apart.

† *italic* = envelope-class on that subject: the row reproduces ≥ 80% of the CHA
envelope's fan share with a strict precision below 1.5× the null model's — its
output composition is the envelope's: it fans where the envelope fans, so exact% there cannot
tell resolution from enumeration (#12, #49). A statement about the row's shape, not a score. Not
applied where the null model's strict precision is ≥ 0.9: the subject barely dispatches
and the envelope is genuinely the right answer (fp-ts is the clearest case). Not counted as a lead:
rows are ranked with their † cells left out, and a summed column that includes one carries the
mark. ↓ = strict precision below the null model's on that subject without being envelope-class
— the row fabricates rather than fans; on a dispatch-light subject the null model's strict
precision is close to 1.0 and the mark says little.

#### Java

| tool | maven-core | netty-transport | spring-boot | apache-ant | rxjava | all five |
|---|---:|---:|---:|---:|---:|---:|
| **ground truth** (bytecode): one-target groups | **2,318** <sub>100%</sub> | **2,142** <sub>100%</sub> | **4,638** <sub>100%</sub> | **14,241** <sub>100%</sub> | **9,918** <sub>100%</sub> | **33,257** <sub>100%</sub> |
| `codeql` | 2,316 <sub>99.9%</sub> | 2,083 <sub>97.2%</sub> | 4,629 <sub>99.8%</sub> | 14,216 <sub>99.8%</sub> | 9,916 <sub>100.0%</sub> | 33,160 <sub>99.7%</sub> |
| **`AxiomEngine`** | *2,296* <sub>99.1%</sub>† | 1,843 <sub>86.0%</sub> | *4,402* <sub>94.9%</sub>† | *13,718* <sub>96.3%</sub>† | 9,833 <sub>99.1%</sub> | 32,092 <sub>96.5%</sub>† |
| `gitnexus` | 2,103 <sub>90.7%</sub>↓ | 1,631 <sub>76.1%</sub> | 3,858 <sub>83.2%</sub>↓ | 12,238 <sub>85.9%</sub> | 6,410 <sub>64.6%</sub> | 26,240 <sub>78.9%</sub> |
| `codegraph` | 2,123 <sub>91.6%</sub>↓ | 1,561 <sub>72.9%</sub> | 3,963 <sub>85.4%</sub>↓ | 10,719 <sub>75.3%</sub> | 7,749 <sub>78.1%</sub> | 26,115 <sub>78.5%</sub> |
| `codegraph-dispatch` | 2,122 <sub>91.5%</sub>↓ | 1,511 <sub>70.5%</sub> | 3,958 <sub>85.3%</sub>↓ | 10,661 <sub>74.9%</sub>↓ | 7,748 <sub>78.1%</sub> | 26,000 <sub>78.2%</sub> |
| `code-review-graph` | 1,877 <sub>81.0%</sub>↓ | 1,415 <sub>66.1%</sub> | 3,594 <sub>77.5%</sub>↓ | 10,120 <sub>71.1%</sub> | 6,919 <sub>69.8%</sub> | 23,925 <sub>71.9%</sub> |
| `code-review-graph-dispatch` | 1,876 <sub>80.9%</sub>↓ | 1,411 <sub>65.9%</sub> | 3,601 <sub>77.6%</sub>↓ | 10,097 <sub>70.9%</sub>↓ | 6,847 <sub>69.0%</sub> | 23,832 <sub>71.7%</sub> |
| `graphify` | 1,964 <sub>84.7%</sub> | 1,336 <sub>62.4%</sub> | 3,491 <sub>75.3%</sub> | 9,309 <sub>65.4%</sub> | 6,339 <sub>63.9%</sub> | 22,439 <sub>67.5%</sub> |
| `codeql-dispatch` | *2,285* <sub>98.6%</sub>† | *2,070* <sub>96.6%</sub>† | *4,523* <sub>97.5%</sub>† | *14,184* <sub>99.6%</sub>† | *9,744* <sub>98.2%</sub>† | 32,806 <sub>98.6%</sub>† |
| *`cha-null`* | 2,318 <sub>100.0%</sub> | 2,142 <sub>100.0%</sub> | 4,638 <sub>100.0%</sub> | 14,241 <sub>100.0%</sub> | 9,918 <sub>100.0%</sub> | 33,257 <sub>100.0%</sub> |

Over all 6 committed non-torture Java subjects (the five above plus gson, whose tables are in `docs/RESULTS.md`): `codeql` 99.7% (33,976/34,089), `codeql-dispatch` 98.6% (33,599/34,089), `AxiomEngine` 96.4% (32,865/34,089). The five compared were chosen before this pass; the sensitivity to that choice is stated here so it is not silent.

#### TypeScript

| tool | kysely | typedoc | fp-ts | ioredis | excalidraw | all five |
|---|---:|---:|---:|---:|---:|---:|
| **ground truth** (type checker): one-target groups | **2,537** <sub>100%</sub> | **2,130** <sub>100%</sub> | **2,245** <sub>100%</sub> | **298** <sub>100%</sub> | **2,619** <sub>100%</sub> | **9,829** <sub>100%</sub> |
| **`AxiomEngine`** | *2,031* <sub>80.1%</sub>† | 1,914 <sub>89.9%</sub>↓ | 2,138 <sub>95.2%</sub> | 273 <sub>91.6%</sub>↓ | 2,375 <sub>90.7%</sub>↓ | 8,731 <sub>88.8%</sub>† |
| `codeql` | 2,007 <sub>79.1%</sub> | 1,796 <sub>84.3%</sub>↓ | 2,175 <sub>96.9%</sub>↓ | 250 <sub>83.9%</sub>↓ | 2,392 <sub>91.3%</sub>↓ | 8,620 <sub>87.7%</sub> |
| `code-review-graph` | 1,768 <sub>69.7%</sub> | 1,672 <sub>78.5%</sub>↓ | 1,321 <sub>58.8%</sub>↓ | 231 <sub>77.5%</sub>↓ | 2,048 <sub>78.2%</sub>↓ | 7,040 <sub>71.6%</sub> |
| `code-review-graph-dispatch` | 1,768 <sub>69.7%</sub> | 1,672 <sub>78.5%</sub>↓ | 1,304 <sub>58.1%</sub>↓ | 230 <sub>77.2%</sub>↓ | 2,047 <sub>78.2%</sub>↓ | 7,021 <sub>71.4%</sub> |
| `codegraph` | 1,439 <sub>56.7%</sub> | 1,528 <sub>71.7%</sub>↓ | 1,440 <sub>64.1%</sub>↓ | 197 <sub>66.1%</sub>↓ | 1,821 <sub>69.5%</sub>↓ | 6,425 <sub>65.4%</sub> |
| `codegraph-dispatch` | 1,439 <sub>56.7%</sub> | 1,528 <sub>71.7%</sub>↓ | 1,440 <sub>64.1%</sub>↓ | 197 <sub>66.1%</sub>↓ | 1,821 <sub>69.5%</sub>↓ | 6,425 <sub>65.4%</sub> |
| `gitnexus` | 1,699 <sub>67.0%</sub> | 1,339 <sub>62.9%</sub> | 1,971 <sub>87.8%</sub>↓ | 190 <sub>63.8%</sub> | 1,201 <sub>45.9%</sub>↓ | 6,400 <sub>65.1%</sub> |
| `graphify` | 1,247 <sub>49.2%</sub> | 1,177 <sub>55.3%</sub>↓ | 826 <sub>36.8%</sub>↓ | 193 <sub>64.8%</sub>↓ | 1,451 <sub>55.4%</sub>↓ | 4,894 <sub>49.8%</sub> |
| *`cha-null`* | 2,537 <sub>100.0%</sub> | 2,130 <sub>100.0%</sub> | 2,245 <sub>100.0%</sub> | 298 <sub>100.0%</sub> | 2,619 <sub>100.0%</sub> | 9,829 <sub>100.0%</sub> |

Over all 8 committed non-torture TypeScript subjects (the five above plus type-graphql, ts-morph, cheerio, whose tables are in `docs/RESULTS.md`): `AxiomEngine` 79.5% (12,681/15,951), `codeql` 79.4% (12,662/15,951), `code-review-graph` 66.2% (10,554/15,951). The five compared were chosen before this pass; the sensitivity to that choice is stated here so it is not silent.

**With external libraries — not ranked.** Every table in this README compares runs that
were given the subject's source and nothing else. Some tools can also be given the external
libraries the subject calls into — AxiomEngine the JDK's platform IR, CodeQL a compiled build on
a local subject — and can then type a receiver that comes out of a library call
(`list.get(0).foo()`), which a source-only tool cannot. Those runs are shown here, each beside
the same tool's library-free run, so what the libraries bought is visible; they are left out
of every ranking, because no other tool under test was offered the same input.

#### Java

| row | budget | maven-core | netty-transport | spring-boot | apache-ant | rxjava | all |
|---|:--|---:|---:|---:|---:|---:|---:|
| `AxiomEngine + libraries` | source + platform IR | 2,299 <sub>99.2%</sub> | 1,843 <sub>86.0%</sub> | 4,437 <sub>95.7%</sub> | 13,729 <sub>96.4%</sub> | 9,840 <sub>99.2%</sub> | 32,148 <sub>96.7%</sub> |
| `AxiomEngine` | source only | 2,296 <sub>99.1%</sub> | 1,843 <sub>86.0%</sub> | 4,402 <sub>94.9%</sub> | 13,718 <sub>96.3%</sub> | 9,833 <sub>99.1%</sub> | 32,092 <sub>96.5%</sub> |

**Seven questions a consumer asks a call graph**, each scored against the ground truth on
its own terms (`bench/tasks.py`; same Tier-B edges and truth as everything above; samples
seeded, pooled over the five subjects). *Callees / callers of a method*: per-method F1 of the
tool's set against the declared set. *Path A→B*: of 500 sampled pairs joined by a declared
call path of ≤3 hops, the share the tool's graph joins within 6. *Blast radius*: Jaccard of
the transitive callers within 3 hops for 300 sampled methods. *"Nothing calls X"*: precision
and recall of the tool's uncalled-method claims against the declared graph's. *Dispatch set*:
Jaccard of the tool's targets against the runnable set at genuinely ambiguous sites (the
envelope answer scores 1.0 here by construction). *File→file dependencies*: F1 of the
cross-file call relation.

#### Java

| tool | callees of a method<br><sub>mean F1</sub> | callers of a method<br><sub>mean F1</sub> | path A→B exists<br><sub>share</sub> | blast radius (3 hops)<br><sub>mean Jaccard</sub> | "nothing calls X"<br><sub>precision</sub> | "nothing calls X"<br><sub>recall</sub> | dispatch set at ambiguous sites<br><sub>mean Jaccard</sub> | file→file dependencies<br><sub>F1</sub> |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `codeql` | 0.998 | 0.992 | 0.992 | 0.989 | 0.993 | 0.999 | 0.238 | 0.998 |
| `codeql-dispatch` | 0.876 | 0.917 | 0.833 | 0.579 | 0.862 | 0.508 | 0.913 | 0.872 |
| **`AxiomEngine`** | 0.978 | 0.967 | 0.974 | 0.750 | 0.965 | 0.778 | 0.497 | 0.976 |
| `codegraph` | 0.755 | 0.814 | 0.722 | 0.709 | 0.873 | 0.898 | 0.193 | 0.737 |
| `gitnexus` | 0.809 | 0.858 | 0.806 | 0.669 | 0.873 | 0.622 | 0.375 | 0.876 |
| `codegraph-dispatch` | 0.750 | 0.814 | 0.744 | 0.610 | 0.862 | 0.775 | 0.396 | 0.773 |
| `code-review-graph` | 0.648 | 0.712 | 0.589 | 0.596 | 0.791 | 0.814 | 0.143 | 0.650 |
| `code-review-graph-dispatch` | 0.652 | 0.733 | 0.638 | 0.592 | 0.796 | 0.690 | 0.174 | 0.658 |
| `graphify` | 0.673 | 0.717 | 0.585 | 0.632 | 0.799 | 0.986 | 0.144 | 0.671 |
| *`cha-null`* | 0.885 | 0.933 | 0.846 | 0.627 | 0.904 | 0.626 | 1.000 | 0.882 |
| *`ideal`* | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.240 | 1.000 |

#### TypeScript

| tool | callees of a method<br><sub>mean F1</sub> | callers of a method<br><sub>mean F1</sub> | path A→B exists<br><sub>share</sub> | blast radius (3 hops)<br><sub>mean Jaccard</sub> | "nothing calls X"<br><sub>precision</sub> | "nothing calls X"<br><sub>recall</sub> | dispatch set at ambiguous sites<br><sub>mean Jaccard</sub> | file→file dependencies<br><sub>F1</sub> |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`AxiomEngine`** | 0.895 | 0.873 | 0.877 | 0.803 | 0.934 | 0.940 | 0.666 | 0.896 |
| `codeql` | 0.888 | 0.849 | 0.828 | 0.777 | 0.928 | 0.965 | 0.438 | 0.895 |
| `code-review-graph` | 0.693 | 0.749 | 0.654 | 0.624 | 0.876 | 0.928 | 0.211 | 0.708 |
| `code-review-graph-dispatch` | 0.696 | 0.751 | 0.671 | 0.616 | 0.878 | 0.904 | 0.264 | 0.714 |
| `codegraph` | 0.636 | 0.667 | 0.658 | 0.575 | 0.845 | 0.961 | 0.297 | 0.663 |
| `codegraph-dispatch` | 0.636 | 0.667 | 0.660 | 0.571 | 0.844 | 0.955 | 0.366 | 0.663 |
| `gitnexus` | 0.663 | 0.616 | 0.565 | 0.533 | 0.818 | 0.901 | 0.377 | 0.685 |
| `graphify` | 0.483 | 0.564 | 0.436 | 0.469 | 0.805 | 0.973 | 0.159 | 0.616 |
| *`cha-null`* | 0.982 | 0.979 | 0.971 | 0.918 | 0.984 | 0.939 | 1.000 | 0.986 |
| *`ideal`* | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.509 | 1.000 |

**Against the three bounds.** What the oracle knows comes in three sizes, and a tool can be
read against each: **CERTAIN** — the declared target, what the call instruction names;
**RTA** — every target that can run on a receiver the program actually instantiates;
**CHA** — every target that can run under class-hierarchy dispatch, the envelope. Every cell is a
count and the share of the ground-truth row (or of the tool's own emitted rows, for the last
two columns), summed over the five subjects; rxjava's 380,000-edge envelope dominates the RTA
and CHA columns for Java, and the per-subject values are in docs/RESULTS.md. A resolver is high on CERTAIN
recall and on `strict`; an enumerator is 1.000 on CHA recall and low on `strict` (the
`cha-null` row is exactly that); a tool that models dispatch sits between RTA and CHA.

#### Java

| tool | one target: found | CERTAIN edges found | RTA edges found | CHA edges found | rows emitted | … inside the envelope | … the declared target |
|---|---:|---:|---:|---:|---:|---:|---:|
| **ground truth** | **33,257** | **41,953** | **406,494** | **414,616** | — | — | — |
| `codeql` | 33,160 <sub>99.7%</sub> | 41,835 <sub>99.7%</sub> | 32,686 <sub>8.0%</sub> | 36,351 <sub>8.8%</sub> | 41,967 | 41,835 <sub>99.7%</sub> | 41,835 <sub>99.7%</sub> |
| `codeql-dispatch` | 32,806 <sub>98.6%</sub> | 36,206 <sub>86.3%</sub> | 380,340 <sub>93.6%</sub> | 388,194 <sub>93.6%</sub> | 659,399 | 657,917 <sub>99.8%</sub> | 36,206 <sub>5.5%</sub> |
| **`AxiomEngine`** | 32,092 <sub>96.5%</sub> | 41,287 <sub>98.4%</sub> | 42,794 <sub>10.5%</sub> | 47,903 <sub>11.6%</sub> | 58,379 | 56,784 <sub>97.3%</sub> | 41,287 <sub>70.7%</sub> |
| `gitnexus` | 26,240 <sub>78.9%</sub> | 34,729 <sub>82.8%</sub> | 65,481 <sub>16.1%</sub> | 70,595 <sub>17.0%</sub> | 80,744 | 75,207 <sub>93.1%</sub> | 34,729 <sub>43.0%</sub> |
| `codegraph` | 26,115 <sub>78.5%</sub> | 32,476 <sub>77.4%</sub> | 26,428 <sub>6.5%</sub> | 28,956 <sub>7.0%</sub> | 41,527 | 33,597 <sub>80.9%</sub> | 32,476 <sub>78.2%</sub> |
| `codegraph-dispatch` | 26,000 <sub>78.2%</sub> | 32,494 <sub>77.5%</sub> | 176,872 <sub>43.5%</sub> | 181,875 <sub>43.9%</sub> | 218,374 | 186,558 <sub>85.4%</sub> | 32,494 <sub>14.9%</sub> |
| `code-review-graph` | 23,925 <sub>71.9%</sub> | 27,987 <sub>66.7%</sub> | 24,222 <sub>6.0%</sub> | 26,624 <sub>6.4%</sub> | 38,037 | 30,096 <sub>79.1%</sub> | 27,987 <sub>73.6%</sub> |
| `code-review-graph-dispatch` | 23,832 <sub>71.7%</sub> | 29,403 <sub>70.1%</sub> | 26,851 <sub>6.6%</sub> | 29,535 <sub>7.1%</sub> | 49,402 | 35,217 <sub>71.3%</sub> | 29,403 <sub>59.5%</sub> |
| `graphify` | 22,439 <sub>67.5%</sub> | 27,781 <sub>66.2%</sub> | 21,872 <sub>5.4%</sub> | 24,215 <sub>5.8%</sub> | 29,162 | 27,913 <sub>95.7%</sub> | 27,781 <sub>95.3%</sub> |
| *`cha-null`* | 33,257 <sub>100.0%</sub> | 36,468 <sub>86.9%</sub> | 406,494 <sub>100.0%</sub> | 414,616 <sub>100.0%</sub> | 414,616 | 414,616 <sub>100.0%</sub> | 36,468 <sub>8.8%</sub> |
| *`ideal`* | 33,257 <sub>100.0%</sub> | 41,953 <sub>100.0%</sub> | 32,802 <sub>8.1%</sub> | 36,468 <sub>8.8%</sub> | 41,953 | 41,953 <sub>100.0%</sub> | 41,953 <sub>100.0%</sub> |

#### TypeScript

| tool | one target: found | CERTAIN edges found | RTA edges found | CHA edges found | rows emitted | … inside the envelope | … the declared target |
|---|---:|---:|---:|---:|---:|---:|---:|
| **ground truth** | **9,829** | **10,383** | **8,805** | **11,133** | — | — | — |
| **`AxiomEngine`** | 8,731 <sub>88.8%</sub> | 9,154 <sub>88.2%</sub> | 7,551 <sub>85.8%</sub> | 9,638 <sub>86.6%</sub> | 10,580 | 9,881 <sub>93.4%</sub> | 9,154 <sub>86.5%</sub> |
| `codeql` | 8,620 <sub>87.7%</sub> | 8,957 <sub>86.3%</sub> | 7,198 <sub>81.7%</sub> | 9,004 <sub>80.9%</sub> | 9,836 | 9,150 <sub>93.0%</sub> | 8,957 <sub>91.1%</sub> |
| `code-review-graph` | 7,040 <sub>71.6%</sub> | 7,244 <sub>69.8%</sub> | 5,552 <sub>63.1%</sub> | 7,204 <sub>64.7%</sub> | 9,078 | 7,257 <sub>79.9%</sub> | 7,244 <sub>79.8%</sub> |
| `code-review-graph-dispatch` | 7,021 <sub>71.4%</sub> | 7,382 <sub>71.1%</sub> | 5,672 <sub>64.4%</sub> | 7,415 <sub>66.6%</sub> | 9,787 | 7,469 <sub>76.3%</sub> | 7,382 <sub>75.4%</sub> |
| `codegraph` | 6,425 <sub>65.4%</sub> | 6,635 <sub>63.9%</sub> | 5,115 <sub>58.1%</sub> | 6,712 <sub>60.3%</sub> | 8,103 | 6,713 <sub>82.8%</sub> | 6,635 <sub>81.9%</sub> |
| `codegraph-dispatch` | 6,425 <sub>65.4%</sub> | 6,638 <sub>63.9%</sub> | 5,124 <sub>58.2%</sub> | 6,771 <sub>60.8%</sub> | 8,194 | 6,772 <sub>82.6%</sub> | 6,638 <sub>81.0%</sub> |
| `gitnexus` | 6,400 <sub>65.1%</sub> | 6,735 <sub>64.9%</sub> | 5,835 <sub>66.3%</sub> | 6,901 <sub>62.0%</sub> | 9,830 | 6,957 <sub>70.8%</sub> | 6,735 <sub>68.5%</sub> |
| `graphify` | 4,894 <sub>49.8%</sub> | 5,008 <sub>48.2%</sub> | 3,916 <sub>44.5%</sub> | 5,021 <sub>45.1%</sub> | 6,157 | 5,030 <sub>81.7%</sub> | 5,008 <sub>81.3%</sub> |
| *`cha-null`* | 9,829 <sub>100.0%</sub> | 10,136 <sub>97.6%</sub> | 8,805 <sub>100.0%</sub> | 11,133 <sub>100.0%</sub> | 11,133 | 11,133 <sub>100.0%</sub> | 10,136 <sub>91.0%</sub> |
| *`ideal`* | 9,829 <sub>100.0%</sub> | 10,383 <sub>100.0%</sub> | 8,133 <sub>92.4%</sub> | 10,136 <sub>91.0%</sub> | 10,383 | 10,383 <sub>100.0%</sub> | 10,383 <sub>100.0%</sub> |

**F1, fan and noise.** Edge-level, pooled over the five subjects from the counts. Of each
tool's rows, **strict** are the declared target, **fan** could run but are not what the call
names (other overrides — the envelope's own row is mostly fan), and **noise** lie outside the
class-hierarchy envelope and can never run. F1 uses precision = strict + fan; F1-strict charges
the fan too. Recall is over the declared edges.

#### Java

| tool | F1 | F1-strict | recall | precision | strict | fan | noise |
|---|---:|---:|---:|---:|---:|---:|---:|
| `codeql` | 0.997 | 0.997 | 0.997 | 0.997 | 0.997 | 0.000 | 0.003 |
| `codeql-dispatch` | 0.926 | 0.103 | 0.863 | 0.998 | 0.055 | 0.943 | 0.002 |
| **`AxiomEngine`** | 0.978 | 0.823 | 0.984 | 0.973 | 0.707 | 0.265 | 0.027 |
| `gitnexus` | 0.877 | 0.566 | 0.828 | 0.931 | 0.430 | 0.501 | 0.069 |
| `codegraph` | 0.791 | 0.778 | 0.774 | 0.809 | 0.782 | 0.027 | 0.191 |
| `codegraph-dispatch` | 0.812 | 0.250 | 0.775 | 0.854 | 0.149 | 0.706 | 0.146 |
| `code-review-graph` | 0.724 | 0.700 | 0.667 | 0.791 | 0.736 | 0.055 | 0.209 |
| `code-review-graph-dispatch` | 0.707 | 0.644 | 0.701 | 0.713 | 0.595 | 0.118 | 0.287 |
| `graphify` | 0.783 | 0.781 | 0.662 | 0.957 | 0.953 | 0.005 | 0.043 |
| *`cha-null`* | 0.930 | 0.160 | 0.869 | 1.000 | 0.088 | 0.912 | 0.000 |

#### TypeScript

| tool | F1 | F1-strict | recall | precision | strict | fan | noise |
|---|---:|---:|---:|---:|---:|---:|---:|
| **`AxiomEngine`** | 0.907 | 0.873 | 0.882 | 0.934 | 0.865 | 0.069 | 0.066 |
| `codeql` | 0.895 | 0.886 | 0.863 | 0.930 | 0.911 | 0.020 | 0.070 |
| `code-review-graph` | 0.745 | 0.744 | 0.698 | 0.799 | 0.798 | 0.001 | 0.201 |
| `code-review-graph-dispatch` | 0.736 | 0.732 | 0.711 | 0.763 | 0.754 | 0.009 | 0.237 |
| `codegraph` | 0.722 | 0.718 | 0.639 | 0.828 | 0.819 | 0.010 | 0.172 |
| `codegraph-dispatch` | 0.721 | 0.715 | 0.639 | 0.826 | 0.810 | 0.016 | 0.174 |
| `gitnexus` | 0.677 | 0.666 | 0.649 | 0.708 | 0.685 | 0.023 | 0.292 |
| `graphify` | 0.607 | 0.606 | 0.482 | 0.817 | 0.813 | 0.004 | 0.183 |
| *`cha-null`* | 0.988 | 0.942 | 0.976 | 1.000 | 0.910 | 0.090 | 0.000 |

**What the ground truth saw.** Per subject, before any tool is scored: what the JDK's
bytecode readers (Java) or the pinned type checker (TypeScript) found. `internal` calls have
a declared target in the application; `boundary` calls leave it (a JDK or dependency method
— not scored); TypeScript `indirect` calls go through a function value (not scored) and
`unresolved` are call expressions the checker could not resolve at all (no row; every
denominator is short by that many, #53). `certain` edges are the declared targets; the
`envelope` is every method that can run under class-hierarchy dispatch; `one target` is the
headline denominator, `several targets` the genuinely ambiguous rest.

#### Java

| subject | files | lines | types | methods | call sites | internal | boundary | certain edges | RTA edges | CHA edges | CHA ÷ certain | one target | several targets |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| torture | 16 | 709 | 88 | 275 | 290 | 208 | 82 | 201 | 185 | 225 | 1.1× | **145** | 33 |
| maven-core | 363 | 45412 | 429 | 2,985 | 9,757 | 3,237 | 6,520 | 2,755 | 2,461 | 2,874 | 1.0× | **2,318** | 161 |
| netty-transport | 188 | 34076 | 371 | 3,108 | 5,947 | 3,614 | 2,333 | 3,283 | 4,350 | 5,148 | 1.6× | **2,142** | 672 |
| spring-boot | 747 | 82898 | 963 | 5,613 | 15,541 | 6,220 | 9,321 | 5,458 | 5,205 | 6,021 | 1.1× | **4,638** | 420 |
| apache-ant | 798 | 201831 | 1,143 | 10,354 | 35,704 | 22,062 | 13,642 | 17,249 | 18,085 | 22,925 | 1.3× | **14,241** | 1,588 |
| rxjava | 856 | 183062 | 1,747 | 10,125 | 25,218 | 17,156 | 8,062 | 15,718 | 379,351 | 380,770 | 24.2× | **9,918** | 3,799 |
| gson | 84 | 18556 | 196 | 1,041 | 2,940 | 1,654 | 1,286 | 1,414 | 3,665 | 3,666 | 2.6× | **832** | 379 |

#### TypeScript

| subject | files | lines | types | methods | call sites | internal | boundary | indirect | unresolved | certain edges | RTA edges | CHA edges | CHA ÷ certain | one target | several targets |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| torture | 13 | 352 | 67 | 134 | 86 | 67 | 9 | 10 | 0 | 68 | 59 | 90 | 1.3× | **53** | 13 |
| kysely | 260 | 35240 | 611 | 2,206 | 4,193 | 3,477 | 592 | 124 | 6 | 2,835 | 2,792 | 3,385 | 1.2× | **2,537** | 201 |
| typedoc | 177 | 36380 | 572 | 1,451 | 5,666 | 3,261 | 1,773 | 632 | 804 | 2,363 | 1,605 | 2,536 | 1.1× | **2,130** | 95 |
| fp-ts | 123 | 58526 | 1,324 | 3,133 | 4,968 | 2,386 | 0 | 2,582 | 744 | 2,269 | 2,269 | 2,269 | 1.0× | **2,245** | 12 |
| ioredis | 37 | 21535 | 100 | 2,032 | 800 | 371 | 316 | 113 | 394 | 308 | 229 | 310 | 1.0× | **298** | 5 |
| excalidraw | 439 | 126225 | 679 | 2,113 | 11,767 | 4,234 | 7,026 | 507 | 2,204 | 2,679 | 1,914 | 2,701 | 1.0× | **2,619** | 23 |
| type-graphql | 115 | 4894 | 195 | 209 | 613 | 292 | 283 | 38 | 66 | 257 | 207 | 256 | 1.0× | **250** | 3 |
| ts-morph | 1007 | 82887 | 1,441 | 3,881 | 8,301 | 6,502 | 1,601 | 198 | 435 | 5,904 | 2,777 | 6,121 | 1.0× | **5,668** | 83 |
| cheerio | 33 | 12574 | 31 | 173 | 452 | 263 | 146 | 43 | 102 | 209 | 209 | 209 | 1.0× | **204** | 2 |

**Verdicts — every call accounted for.** The first row is the ground truth: how many
uniquely linked calls the bytecode (Java) or the type checker (TypeScript) says the five
subjects contain. Each tool row partitions exactly those calls: **found** = linked to the one
method that runs (or its declaration); **fan** = the right method plus others; **polluted** =
the right method plus one outside the envelope; **vague** = only a supertype that declares the
member; **wrong** = only impossible targets; **unknown** = no answer, but the tool wrote a row
saying it could not resolve a call at that line (AxiomEngine's `ambiguous_unknown`); **unplaced** = the
tool answered but every row for the group was excluded by the resolver (ambiguous or
owner-less spelling, target outside the universe); **missed** = nothing at all, a silent gap
(#69). Rows sum to the ground-truth row. The second table is the same partition per subject
(`found · fan · polluted · vague · wrong · unknown · unplaced · missed`).

#### Java

| tool | found | fan | polluted | vague | wrong | unknown | unplaced | missed | of | found % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **ground truth** (bytecode) | — | — | — | — | — | — | — | — | **33,257** | — |
| `codeql` | 33,160 | 0 | 21 | 0 | 0 | 0 | 64 | 12 | 33,257 | 99.7% |
| **`AxiomEngine`**† | 32,092 | 376 | 355 | 11 | 2 | 144 | 0 | 277 | 33,257 | 96.5% |
| `gitnexus` | 26,240 | 5 | 2,196 | 10 | 366 | 0 | 1 | 4,439 | 33,257 | 78.9% |
| `codegraph` | 26,115 | 1 | 67 | 28 | 2,596 | 2,466 | 12 | 1,972 | 33,257 | 78.5% |
| `codegraph-dispatch` | 26,000 | 5 | 194 | 23 | 2,585 | 2,466 | 12 | 1,972 | 33,257 | 78.2% |
| `code-review-graph` | 23,925 | 0 | 22 | 74 | 2,227 | 5,845 | 12 | 1,152 | 33,257 | 71.9% |
| `code-review-graph-dispatch` | 23,832 | 55 | 959 | 74 | 2,806 | 4,372 | 12 | 1,147 | 33,257 | 71.7% |
| `graphify` | 22,439 | 0 | 4 | 9 | 927 | 0 | 221 | 9,657 | 33,257 | 67.5% |
| `codeql-dispatch`† | 32,806 | 0 | 190 | 0 | 1 | 0 | 84 | 176 | 33,257 | 98.6% |

| tool | maven-core<br><sub>2,318 calls</sub> | netty-transport<br><sub>2,142 calls</sub> | spring-boot<br><sub>4,638 calls</sub> | apache-ant<br><sub>14,241 calls</sub> | rxjava<br><sub>9,918 calls</sub> |
|---|---:|---:|---:|---:|---:|
| **ground truth** (bytecode) | 2,318 | 2,142 | 4,638 | 14,241 | 9,918 |
| `codeql` | 2,316 · 0 · 0 · 0 · 0 · 0 · 2 · 0 | 2,083 · 0 · 0 · 0 · 0 · 0 · 54 · 5 | 4,629 · 0 · 0 · 0 · 0 · 0 · 4 · 5 | 14,216 · 0 · 19 · 0 · 0 · 0 · 4 · 2 | 9,916 · 0 · 2 · 0 · 0 · 0 · 0 · 0 |
| **`AxiomEngine`** | 2,296 · 0 · 9 · 0 · 0 · 6 · 0 · 7 | 1,843 · 27 · 166 · 3 · 2 · 13 · 0 · 88 | 4,402 · 6 · 22 · 0 · 0 · 49 · 0 · 159 | 13,718 · 341 · 88 · 8 · 0 · 63 · 0 · 23 | 9,833 · 2 · 70 · 0 · 0 · 13 · 0 · 0 |
| `gitnexus` | 2,103 · 0 · 95 · 0 · 6 · 0 · 0 · 114 | 1,631 · 2 · 233 · 2 · 37 · 0 · 0 · 237 | 3,858 · 0 · 215 · 0 · 28 · 0 · 0 · 537 | 12,238 · 3 · 820 · 8 · 187 · 0 · 1 · 984 | 6,410 · 0 · 833 · 0 · 108 · 0 · 0 · 2,567 |
| `codegraph` | 2,123 · 0 · 21 · 0 · 42 · 70 · 1 · 61 | 1,561 · 0 · 0 · 18 · 238 · 154 · 7 · 164 | 3,963 · 1 · 5 · 0 · 115 · 299 · 2 · 253 | 10,719 · 0 · 35 · 9 · 1759 · 1335 · 2 · 382 | 7,749 · 0 · 6 · 1 · 442 · 608 · 0 · 1,112 |
| `codegraph-dispatch` | 2,122 · 0 · 22 · 0 · 42 · 70 · 1 · 61 | 1,511 · 3 · 62 · 15 · 226 · 154 · 7 · 164 | 3,958 · 1 · 10 · 0 · 115 · 299 · 2 · 253 | 10,661 · 1 · 93 · 7 · 1760 · 1335 · 2 · 382 | 7,748 · 0 · 7 · 1 · 442 · 608 · 0 · 1,112 |
| `code-review-graph` | 1,877 · 0 · 0 · 0 · 67 · 321 · 0 · 53 | 1,415 · 0 · 0 · 23 · 265 · 299 · 8 · 132 | 3,594 · 0 · 3 · 8 · 237 · 590 · 3 · 203 | 10,120 · 0 · 7 · 6 · 1326 · 2426 · 1 · 355 | 6,919 · 0 · 12 · 37 · 332 · 2209 · 0 · 409 |
| `code-review-graph-dispatch` | 1,876 · 0 · 36 · 0 · 81 · 273 · 0 · 52 | 1,411 · 27 · 26 · 23 · 293 · 223 · 8 · 131 | 3,601 · 0 · 92 · 8 · 266 · 465 · 3 · 203 | 10,097 · 5 · 550 · 6 · 1633 · 1593 · 1 · 356 | 6,847 · 23 · 255 · 37 · 533 · 1818 · 0 · 405 |
| `graphify` | 1,964 · 0 · 0 · 0 · 1 · 0 · 19 · 334 | 1,336 · 0 · 0 · 3 · 15 · 0 · 15 · 773 | 3,491 · 0 · 1 · 0 · 45 · 0 · 30 · 1,071 | 9,309 · 0 · 3 · 6 · 708 · 0 · 148 · 4,067 | 6,339 · 0 · 0 · 0 · 158 · 0 · 9 · 3,412 |
| `codeql-dispatch` | 2,285 · 0 · 10 · 0 · 1 · 0 · 4 · 18 | 2,070 · 0 · 1 · 0 · 0 · 0 · 54 · 17 | 4,523 · 0 · 1 · 0 · 0 · 0 · 20 · 94 | 14,184 · 0 · 38 · 0 · 0 · 0 · 6 · 13 | 9,744 · 0 · 140 · 0 · 0 · 0 · 0 · 34 |

#### TypeScript

| tool | found | fan | polluted | vague | wrong | unknown | unplaced | missed | of | found % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **ground truth** (type checker) | — | — | — | — | — | — | — | — | **9,829** | — |
| **`AxiomEngine`**† | 8,731 | 0 | 13 | 0 | 0 | 723 | 0 | 362 | 9,829 | 88.8% |
| `codeql` | 8,620 | 0 | 13 | 0 | 1 | 0 | 49 | 1,146 | 9,829 | 87.7% |
| `code-review-graph` | 7,040 | 0 | 0 | 0 | 58 | 485 | 19 | 2,227 | 9,829 | 71.6% |
| `code-review-graph-dispatch` | 7,021 | 0 | 130 | 0 | 74 | 358 | 19 | 2,227 | 9,829 | 71.4% |
| `codegraph` | 6,425 | 0 | 23 | 1 | 235 | 702 | 31 | 2,412 | 9,829 | 65.4% |
| `codegraph-dispatch` | 6,425 | 1 | 23 | 0 | 235 | 702 | 31 | 2,412 | 9,829 | 65.4% |
| `gitnexus` | 6,400 | 0 | 47 | 0 | 10 | 0 | 2 | 3,370 | 9,829 | 65.1% |
| `graphify` | 4,894 | 0 | 0 | 0 | 130 | 0 | 2 | 4,803 | 9,829 | 49.8% |

| tool | kysely<br><sub>2,537 calls</sub> | typedoc<br><sub>2,130 calls</sub> | fp-ts<br><sub>2,245 calls</sub> | ioredis<br><sub>298 calls</sub> | excalidraw<br><sub>2,619 calls</sub> |
|---|---:|---:|---:|---:|---:|
| **ground truth** (type checker) | 2,537 | 2,130 | 2,245 | 298 | 2,619 |
| **`AxiomEngine`** | 2,031 · 0 · 6 · 0 · 0 · 491 · 0 · 9 | 1,914 · 0 · 5 · 0 · 0 · 126 · 0 · 85 | 2,138 · 0 · 0 · 0 · 0 · 21 · 0 · 86 | 273 · 0 · 2 · 0 · 0 · 15 · 0 · 8 | 2,375 · 0 · 0 · 0 · 0 · 70 · 0 · 174 |
| `codeql` | 2,007 · 0 · 2 · 0 · 0 · 0 · 22 · 506 | 1,796 · 0 · 8 · 0 · 0 · 0 · 23 · 303 | 2,175 · 0 · 0 · 0 · 0 · 0 · 0 · 70 | 250 · 0 · 3 · 0 · 1 · 0 · 0 · 44 | 2,392 · 0 · 0 · 0 · 0 · 0 · 4 · 223 |
| `code-review-graph` | 1,768 · 0 · 0 · 0 · 20 · 123 · 2 · 624 | 1,672 · 0 · 0 · 0 · 25 · 148 · 14 · 271 | 1,321 · 0 · 0 · 0 · 0 · 176 · 0 · 748 | 231 · 0 · 0 · 0 · 6 · 12 · 0 · 49 | 2,048 · 0 · 0 · 0 · 7 · 26 · 3 · 535 |
| `code-review-graph-dispatch` | 1,768 · 0 · 11 · 0 · 32 · 100 · 2 · 624 | 1,672 · 0 · 13 · 0 · 28 · 132 · 14 · 271 | 1,304 · 0 · 91 · 0 · 0 · 102 · 0 · 748 | 230 · 0 · 3 · 0 · 7 · 9 · 0 · 49 | 2,047 · 0 · 12 · 0 · 7 · 15 · 3 · 535 |
| `codegraph` | 1,439 · 0 · 0 · 0 · 128 · 447 · 0 · 523 | 1,528 · 0 · 3 · 1 · 76 · 101 · 12 · 409 | 1,440 · 0 · 18 · 0 · 0 · 12 · 2 · 773 | 197 · 0 · 0 · 0 · 12 · 23 · 4 · 62 | 1,821 · 0 · 2 · 0 · 19 · 119 · 13 · 645 |
| `codegraph-dispatch` | 1,439 · 0 · 0 · 0 · 128 · 447 · 0 · 523 | 1,528 · 1 · 3 · 0 · 76 · 101 · 12 · 409 | 1,440 · 0 · 18 · 0 · 0 · 12 · 2 · 773 | 197 · 0 · 0 · 0 · 12 · 23 · 4 · 62 | 1,821 · 0 · 2 · 0 · 19 · 119 · 13 · 645 |
| `gitnexus` | 1,699 · 0 · 0 · 0 · 0 · 0 · 0 · 838 | 1,339 · 0 · 1 · 0 · 10 · 0 · 0 · 780 | 1,971 · 0 · 44 · 0 · 0 · 0 · 0 · 230 | 190 · 0 · 2 · 0 · 0 · 0 · 0 · 106 | 1,201 · 0 · 0 · 0 · 0 · 0 · 2 · 1,416 |
| `graphify` | 1,247 · 0 · 0 · 0 · 33 · 0 · 0 · 1,257 | 1,177 · 0 · 0 · 0 · 55 · 0 · 0 · 898 | 826 · 0 · 0 · 0 · 25 · 0 · 0 · 1,394 | 193 · 0 · 0 · 0 · 9 · 0 · 1 · 95 | 1,451 · 0 · 0 · 0 · 8 · 0 · 1 · 1,159 |

**Call chains at depth 3** — `R@3 · blowup@3`: of the method pairs the declared graph
reaches within three calls, the share the tool's graph also reaches; and the size of the
tool's answer over the true one — what a change-impact query gets back. `k=1` is the
edge metric; over three hops a fanning graph stops being free (issue #5). A blowup
**below 1×** is unsound in the other direction — the tool hands back less than the true
set (#50; P@3 was one number printed twice, since P × blowup ≡ recall). Italic rows are
the bracket: the null model below, the ideal answer above.

#### Java

| tool | maven-core | netty-transport | spring-boot | apache-ant | rxjava |
|---|---:|---:|---:|---:|---:|
| `codeql` | 1.00 · 1.0× | 0.95 · 1.0× | 1.00 · 1.0× | 1.00 · 1.0× | 1.00 · 1.0× |
| `codeql-dispatch` | 0.79 · 2.0× | 0.73 · 2.9× | 0.93 · 1.5× | 0.97 · 2.7× | 0.74 · 245.9× |
| **`AxiomEngine`** | 0.98 · 2.0× | 0.93 · 3.1× | 0.95 · 1.6× | 0.99 · 1.9× | 1.00 · 5.0× |
| `codegraph` | 0.91 · 1.7× | 0.52 · 0.7× | 0.80 · 1.2× | 0.67 · 1.0× | 0.62 · 0.8× |
| `gitnexus` | 0.92 · 1.8× | 0.80 · 1.8× | 0.79 · 1.2× | 0.86 · 1.4× | 0.61 · 5.1× |
| `codegraph-dispatch` | 0.91 · 2.7× | 0.53 · 1.1× | 0.80 · 1.5× | 0.67 · 1.6× | 0.68 · 19.3× |
| `code-review-graph` | 0.75 · 1.4× | 0.38 · 0.5× | 0.63 · 1.0× | 0.58 · 0.9× | 0.53 · 0.7× |
| `code-review-graph-dispatch` | 0.77 · 1.5× | 0.45 · 0.7× | 0.68 · 1.3× | 0.64 · 1.3× | 0.56 · 1.1× |
| `graphify` | 0.74 · 0.7× | 0.41 · 0.4× | 0.64 · 0.7× | 0.47 · 0.5× | 0.55 · 0.6× |
| *`cha-null`* | 0.80 · 1.5× | 0.78 · 2.8× | 0.94 · 1.4× | 0.97 · 2.4× | 0.74 · 108.4× |
| *`ideal`* | 1.00 · 1.0× | 1.00 · 1.0× | 1.00 · 1.0× | 1.00 · 1.0× | 1.00 · 1.0× |

#### TypeScript

| tool | kysely | typedoc | fp-ts | ioredis | excalidraw |
|---|---:|---:|---:|---:|---:|
| **`AxiomEngine`** | 0.76 · 1.6× | 0.88 · 1.2× | 0.95 · 1.0× | 0.93 · 1.1× | 0.84 · 0.9× |
| `codeql` | 0.72 · 0.8× | 0.78 · 1.2× | 0.98 · 1.0× | 0.79 · 1.1× | 0.85 · 0.9× |
| `code-review-graph` | 0.67 · 0.7× | 0.66 · 1.0× | 0.56 · 0.7× | 0.58 · 0.9× | 0.77 · 1.3× |
| `code-review-graph-dispatch` | 0.68 · 0.8× | 0.68 · 1.1× | 0.60 · 0.9× | 0.59 · 1.1× | 0.78 · 1.3× |
| `codegraph` | 0.53 · 0.8× | 0.65 · 1.0× | 0.71 · 0.8× | 0.65 · 1.2× | 0.70 · 0.9× |
| `codegraph-dispatch` | 0.53 · 0.9× | 0.65 · 1.0× | 0.71 · 0.8× | 0.65 · 1.3× | 0.70 · 0.9× |
| `gitnexus` | 0.52 · 0.6× | 0.59 · 0.6× | 0.89 · 2.7× | 0.50 · 0.5× | 0.32 · 0.5× |
| `graphify` | 0.44 · 0.5× | 0.40 · 0.4× | 0.34 · 0.4× | 0.51 · 0.7× | 0.48 · 0.5× |
| *`cha-null`* | 0.91 · 1.7× | 0.98 · 1.7× | 1.00 · 1.0× | 0.99 · 1.0× | 1.00 · 1.0× |
| *`ideal`* | 1.00 · 1.0× | 1.00 · 1.0× | 1.00 · 1.0× | 1.00 · 1.0× | 1.00 · 1.0× |

**Size and time.** Wall-clock seconds per tool row, subjects smallest first. Where one adapter
produces two rows (Java `AxiomEngine` with and without libraries: one parse, two solves; `codeql` / `codeql-dispatch`:
one database, two queries) each row is the shared phase plus its own — not the adapter's
whole wall-clock twice (#8); copying the subject into a tool's work directory is harness
time and is charged to nobody. `run.tools.<tool>.seconds_breakdown` in each `scores.json`
has the parts. `codeql` time includes the database build; `AxiomEngine` includes parse and solve;
the index tools include their indexing pass. `gitnexus` excludes its adapter's export: the tool's query CLI
truncates a result at 64 KiB, so the adapter pages it one process per 200 rows, and that loop is
published as `seconds_breakdown.export` rather than charged to the tool (#98). Measured on a
dedicated VM (GCP c3-standard-22, Intel Xeon Platinum 8481C, 22 vCPU, 88 GB, Ubuntu 24.04), one subject and one tool at a time with nothing else running;
still a single run per tool, so read small differences as noise. WARM runs only: a tool's one-time cost (AxiomEngine's
Soufflé compile, CodeQL's query compile) is paid in a warm-up pass before the timed run and
recorded per subject as `run.tools.<tool>.cold_seconds` with whether its cache was hit (#42);
before that, the first subject of a session carried the compile — AxiomEngine read 82 s on a
195-line file and 4 s on kysely. The Java `AxiomEngine + libraries` row also stages the platform IR once per
library key; until #88 the timed run's key differed from the warm-up's (a per-subject symlink
farm), so every Java solve re-staged it into `seconds` — the roots are stable paths now, and
`run.tools.<label>.seconds_breakdown.library_cache` says whether each timed solve hit it.

#### Java

| subject | files | lines | call sites | unique groups | `AxiomEngine` | `code-review-graph` | `code-review-graph-dispatch` | `codegraph` | `codegraph-dispatch` | `gitnexus` | `graphify` | `codeql` | `codeql-dispatch` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| torture | 16 | 709 | 290 | 145 | 2s | 1s | 1s | 1s | 1s | 8s | 1s | — | — |
| gson | 84 | 18556 | 2,940 | 832 | 6s | 2s | 2s | 1s | 1s | 12s | 2s | 20s | 26s |
| netty-transport | 188 | 34076 | 5,947 | 2,142 | 9s | 4s | 4s | 2s | 2s | 17s | 4s | 23s | 28s |
| maven-core | 363 | 45412 | 9,757 | 2,318 | 13s | 5s | 5s | 2s | 2s | 20s | 5s | 31s | 38s |
| spring-boot | 747 | 82898 | 15,541 | 4,638 | 20s | 8s | 8s | 3s | 3s | 29s | 9s | 1.8m | 2.2m |
| rxjava | 856 | 183062 | 25,218 | 9,918 | 41s | 17s | 17s | 9s | 9s | 45s | 16s | 1.7m | 2.2m |
| apache-ant | 798 | 201831 | 35,704 | 14,241 | 47s | 19s | 19s | 6s | 6s | 49s | 15s | 38s | 55s |

#### TypeScript

| subject | files | lines | call sites | unique groups | `AxiomEngine` | `code-review-graph` | `code-review-graph-dispatch` | `codegraph` | `codegraph-dispatch` | `codeql` | `gitnexus` | `graphify` |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| torture | 13 | 352 | 86 | 53 | 1s | 1s | 1s | 1s | 1s | 12s | 10s | 0s |
| type-graphql | 115 | 4894 | 613 | 250 | 2s | 2s | 2s | 1s | 1s | 14s | 21s | 1s |
| cheerio | 33 | 12574 | 452 | 204 | 2s | 2s | 2s | 1s | 1s | 14s | 12s | 1s |
| ioredis | 37 | 21535 | 800 | 298 | 3s | 2s | 2s | 1s | 1s | 17s | 19s | 2s |
| kysely | 260 | 35240 | 4,193 | 2,537 | 5s | 3s | 3s | 2s | 2s | 18s | 32s | 3s |
| typedoc | 177 | 36380 | 5,666 | 2,130 | 8s | 5s | 5s | 2s | 2s | 24s | 31s | 5s |
| fp-ts | 123 | 58526 | 4,968 | 2,245 | 17s | 14s | 14s | 4s | 4s | 38s | 50s | 7s |
| ts-morph | 1007 | 82887 | 8,301 | 5,668 | 9s | 8s | 8s | 3s | 3s | 25s | 38s | 16s |
| excalidraw | 439 | 126225 | 11,767 | 2,619 | 22s | 22s | 22s | 5s | 5s | 46s | 71s | 11s |

<!-- results:end -->

### How to read it

* **Java is a measurement; TypeScript is a diagnostic.** The Java ground truth is the project's
  own published bytecode, read by two independent readers that agree instruction-for-instruction.
  The TypeScript ground truth is the compiler's type checker, which has one implementation, and one
  tool under test — AxiomEngine — was developed against that same checker. `docs/CROSS-LANGUAGE.md`.
* **The one number that means the same thing in both languages** is the matrix above: of the
  calls where the language admits exactly one target, how many did the tool link to that one
  method. The small figure is that share × sharpness — a diagnostic the envelope answer cannot
  top, not the ranking (it charges a tool for naming the overrides that really run and nothing
  for edges it never emits). `R possible` is *not* that number — on rxjava (envelope 42×
  the declared set) it measures closeness to the null model, and every resolving tool reads
  0.02–0.04 on it.
* **Sharpness rewards the declared answer.** `prec-strict` counts a row as right only when it is
  the declared target, so a tool that names the three overrides that can run at a dispatching
  site is scored less sharp than one that names the declaration — even though each override is
  real. That is the one thing this oracle can hold a tool to: it has no ground truth sharper than
  the CHA envelope for which override runs, so "sharp" here means *close to the static call
  graph*, and the chains matrix (blowup at depth 3) is the other side of the same fact.
* **`prec-strict` is the column the null model cannot max where the subject dispatches.** `precision` charges a false positive
  only outside the envelope, so emitting the whole envelope scores 1.000; `prec-strict` asks how
  much of what a tool said was the declared answer. A row that reproduces the envelope's fan share
  (≥ 80%) with a strict precision below 1.5× the null model's is marked † and not counted as a lead (#12).
  Where a subject does not dispatch (fp-ts: null strict 1.000) the envelope *is* the declared set and
  the null model is genuinely right; those cells are marked dispatch-light, and F1/MCC are printed in
  the strict form for the same reason (#1).
* **The ranked tables are library-free.** A run given the subject's external libraries (AxiomEngine
  with the JDK's platform IR; CodeQL compiled against a classpath, on `torture` only) can type a
  receiver that comes out of a library call, which a source-only tool cannot. Those runs are not
  ranked; they are shown beside the same tool's library-free run under "With external libraries".
  CodeQL on the five Maven subjects is `build-mode=none` — the sources jar, dependencies absent — and
  is ranked. `needs` is a capability, not a score.

### Where axiom-code-graph lands

Every number in this list is generated from `*/results/*/scores.json` by
`bench/readme_tables.py --write`, like the tables above. Hand-written figures here drifted from
the tables beside them twice (#34, #94), so none are written by hand. Ranks count every ranked
row, and an envelope-class (†) row ranked above AxiomEngine is named rather than dropped.

<!-- standings:begin -->

**Java** (the five compared subjects, library-free rows):

- **Leader on each subject:** maven-core `codeql` 99.9% (0.1 below the ceiling); netty-transport `codeql` 97.2% (2.8 below the ceiling); spring-boot `codeql` 99.8% (0.2 below the ceiling); apache-ant `codeql` 99.8% (0.2 below the ceiling); rxjava `codeql` 100.0% (0.0 below the ceiling).
- **`AxiomEngine` by subject** (exact%, rank among every ranked row): maven-core 99.1% — #2 of 9; netty-transport 86.0% — #3 of 9 (above it and envelope-class there: `codeql-dispatch`); spring-boot 94.9% — #3 of 9 (above it and envelope-class there: `codeql-dispatch`); apache-ant 96.3% — #3 of 9 (above it and envelope-class there: `codeql-dispatch`); rxjava 99.1% — #2 of 9.
- **Pooled:** 32,092 of 33,257 one-target groups (96.5%); the 1,165 not found are 376 fan, 355 polluted, 11 vague, 2 wrong, 144 unknown, 277 missed.
- **Against `codeql`:** behind `codeql` on maven-core (99.1 vs 99.9), netty-transport (86.0 vs 97.2), spring-boot (94.9 vs 99.8), apache-ant (96.3 vs 99.8), rxjava (99.1 vs 100.0).

**TypeScript** (the five compared subjects, library-free rows):

- **Leader on each subject:** kysely `AxiomEngine` 80.1% (19.9 below the ceiling); typedoc `AxiomEngine` 89.9% (10.1 below the ceiling); fp-ts `codeql` 96.9% (3.1 below the ceiling); ioredis `AxiomEngine` 91.6% (8.4 below the ceiling); excalidraw `codeql` 91.3% (8.7 below the ceiling).
- **`AxiomEngine` by subject** (exact%, rank among every ranked row): kysely 80.1% — #1 of 8; typedoc 89.9% — #1 of 8; fp-ts 95.2% — #2 of 8; ioredis 91.6% — #1 of 8; excalidraw 90.7% — #2 of 8.
- **Pooled:** 8,731 of 9,829 one-target groups (88.8%); the 1,098 not found are 13 polluted, 723 unknown, 362 missed.
- **Against `codeql`:** ahead of `codeql` on kysely (80.1 vs 79.1), typedoc (89.9 vs 84.3), ioredis (91.6 vs 83.9); behind `codeql` on fp-ts (95.2 vs 96.9), excalidraw (90.7 vs 91.3).

<!-- standings:end -->

**What the Java numbers are measured on.** The **JVMS envelope** (#30), with calls whose declared
target is outside the application excluded as boundaries, and with javac's Java-8 lowering undone
(#66): a call on an interface with one application implementor is uniquely linked to it, and
naming the declaration or the implementor is exact. `codeql` reads the sources jar with no build
and no network (#117); `codeql-dispatch` is the envelope by construction and reads as one. The
bounds table and the chains matrix say what exact% cannot — whose output is the envelope's, and
how much bigger than the true reachable set a change-impact query comes back.

**Reading the TypeScript numbers.** The ground truth is one implementation of the type system,
aligned in places with one tool's own tests, and adapter effort is a confound the audit named
first (#7.3) and has charged in both directions. The AxiomEngine–CodeQL lead has moved with every
audit pass, in both directions (81.9 vs 67.1 in the first README, 87.5 vs 81.5 after the fourth),
as the oracle stopped naming typedoc callers after a number, stopped scoring `new C()` as
dispatch, learned to resolve calls through mapped types, and attributed class field initializers
to the constructor (#74). Over every committed TypeScript subject, not only the five, the line
under the matrix gives the pooled order.

### What the audit found, in one line each

Issues filed against this benchmark's own measurements are tracked on GitHub; every closure is an
entry in [`docs/AUDIT.md`](docs/AUDIT.md) with before/after numbers, and the open ones are the
open ones — this paragraph does not count them, because the count was wrong within a day of
being written (#48). The largest findings, oldest last: **the Java oracle scored calls on JDK
interfaces as uniquely linked to the one application implementor** (second #30 pass — every
`Map.get` in maven-core to one anonymous `AbstractMap`, credited to application-only CHA and
charged to the tool that answered `Map#get`); the headline's ranking column was maxed by the
envelope answer by construction (#1, #12, #49 — the adjusted column); the resolver returned
silently wrong verdicts (#36, #37); the Java envelope was not the CHA envelope (#30 — gate 1c
now checks it independently); seven Java conventions were wrong including the torture subject's
own `new Middle().new Deep()` (#26); the TypeScript envelope was documented as one thing and
computed as another (#27); nothing reproduced off macOS (#45, #54, #56); the TypeScript oracle
emitted false ground truth in four places (#52); a subject was blocked for the harness's own
tsconfig artefact (#55). **Most failures this benchmark has found were in the benchmark**, and
they have not favoured one side: the second #30 pass moved CodeQL's maven-core exact% from 87.9
to 100.0 and AxiomEngine's from 87.3 to 98.4; the
#53 caller fix moved CodeQL's excalidraw exact% from 84.3 to 90.6 and AxiomEngine's from 90.8 to 87.9.

Every torture subject ships `EXPECTED.md` — the oracle's own site table, one row per construct,
generated by `bench/expected.py` — so a reader can check what the oracle says about a class-field
arrow, a union receiver or a generic bridge before the same oracle is trusted on 35,000 sites of
apache-ant.

### Verified

`<lang>/run/verify.sh <subject>` re-runs the committed oracle and requires the ground truth on
disk to hash identically (LF-normalised, #45) to what it emits, re-runs every tool from a clean
state and requires byte-identical edge files, re-scores and requires a byte-identical
`scores.json`, and re-hashes every manifest entry. The subjects it has passed on with these
numbers are listed in `docs/AUDIT.md` under the pass that produced them, with the platform
(`run.platform`, `run.java` / `run.typescript` in each `scores.json`). A number on a subject that
has not been through it is a number, not a claim. The current tables (pass 9) verified on all
seven Java subjects and eight of nine TypeScript ones. **excalidraw did not**: gitnexus labels one
edge's confidence differently on different clean runs. Its edge set, and so every score, is the
same each time (#121). AxiomEngine's rows carry the parser and engine
commit they were produced by — both `origin/main` at the time of the run. `TOOLS="axiom"
bash java/run/subject.sh <subject>` re-runs one tool and re-scores; `bash bench/rescore.sh`
re-scores without running anything.

### The caveats that matter

`torture` (Java) was written by the authors of one tool under test. Four of the team's TypeScript
dev projects and five of its held-out ones are in the engine's own corpus and carry a
`prior_internal_use` flag; the five TypeScript subjects run here are from the clean half, with
excalidraw moved from held-out to dev on 2026-09-12 at the user's request to replace type-graphql
(whose table is kept in `docs/RESULTS.md`). `kafka-clients` (generated code), `got` and `remeda`
(checker coverage below the floor without `node_modules`) and `axios` (JavaScript source) are
**blocked**, registered with the reason; `ts-morph` and `cheerio` clear the floor with registry
`project_overrides` (#28, #55) and are reported, with type-graphql, as further TypeScript
subjects in `docs/RESULTS.md`.

## Requirements

JDK 24+ (`java.lang.classfile` is final there), Python 3.10+, and whatever each adapter's tool
needs. A tool that is not installed is **absent from the report** — never reported as scoring zero,
which would be a claim the run did not make.

Each `adapters/<tool>/install.sh` installs into `.tools/`, never globally, and installs **exactly a
committed lock** — `requirements.lock` for the Python tools, `package-lock.json` for the npm ones,
`ql/codeql-pack.lock.yml` for CodeQL. A version on the tool alone is not a pin: `code-review-graph`
requires tree-sitter and its grammar pack unbounded, and for a tree-sitter indexer the grammar
version *is* the analyser, so a top-level pin let a clean install resolve a different analyser every
month and move 13 of 15 dev subjects at a constant tool version (#103). Each lock's header says how
to regenerate it; regenerating one is a re-run of every subject, not a housekeeping commit.
