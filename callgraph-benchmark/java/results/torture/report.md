# Java call-graph benchmark — `torture`

Ground truth is read from compiled class files with `java.lang.classfile` (JEP 484) and
cross-checked instruction-for-instruction against an independent `javap` reader. No tool
under test participates in producing it.
See `docs/PROTOCOL.md` for every definition below; `docs/CROSS-LANGUAGE.md` for what is and
is not comparable across languages.

## The subject, and the denominators every number below is over

| quantity | count |
|---|---:|
| application types | 88 |
| application methods | 275 |
| call sites read from bytecode | 290 |
| … application-internal | 208 |
| … leaving the application (not scored, see §7) | 82 |
| … through a function value, target not statically known (not scored) | 0 |
| **CERTAIN** edges (declared targets) — `recall_certain` denominator | 201 |
| **POSSIBLE** edges (CHA envelope — sound, nominal dispatch) — `recall_possible` denominator | 225 |
| **RTA** edges (instantiated-types envelope) — `recall_rta` denominator | 185 |
| link groups `(caller, callee-name)`, at Tier B | 178 |
| … **uniquely linked** (exactly one possible target) — the headline denominator | 145 |
| … uniquely linked at Tier A (overloads kept apart) | 144 |
| … genuinely ambiguous (dispatch admits several) | 33 |

Call sites by instruction: `INVOKEINTERFACE` 56, `INVOKESPECIAL` 73, `INVOKESTATIC` 49, `INVOKEVIRTUAL` 102, `METHODREF` 10.

## Headline — Tier B (`type#name`)

Tier B is the highest fidelity **every** tool under test can express, so it is the only tier
at which the whole field is comparable. The ground truth is projected to Tier B as well, so a
tool that cannot spell parameter types is not being asked to.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source + platform IR | 14s | 0.982 | 0.777 | 0.965 | 0.969 | 0.978 | 0.861 | 0.866 | 247 | 0, 13 duplicate |
| `axiom-nolib` | source only | 2s | 0.981 | 0.778 | 0.899 | 0.906 | 0.913 | 0.834 | 0.836 | 230 | 0, 13 duplicate |
| `code-review-graph` | source only | 1s | 0.894 | 0.868 | 0.759 | 0.641 | 0.683 | 0.810 | 0.811 | 174 | 82 (0 ambig, 47 out-of-scope, 18% of emitted, 35 unspellable, 0 §4-excluded), 10 duplicate |
| `code-review-graph-dispatch` | source only | 1s | 0.862 | 0.722 | 0.859 | 0.785 | 0.820 | 0.784 | 0.787 | 237 | 63 (6 ambig, 47 out-of-scope, 15% of emitted, 10 unspellable, 0 §4-excluded), 12 duplicate |
| `codegraph` | source only | 1s | 0.926 | 0.900 | 0.678 | 0.561 | 0.623 | 0.774 | 0.781 | 150 | 0, 5 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.925 | 0.771 | 0.678 | 0.664 | 0.699 | 0.722 | 0.723 | 175 | 0, 5 duplicate |
| `codeql` | compiled build | 12s | 1.000 | 1.000 | 0.990 | 0.785 | 0.803 | 0.995 | 0.995 | 197 | 165 (5 ambig, 148 out-of-scope, 40% of emitted, 0 unspellable, 12 §4-excluded), 14 duplicate |
| `codeql-dispatch` | compiled build | 16s | 1.000 | 0.786 | 0.849 | 0.946 | 0.962 | 0.816 | 0.817 | 215 | 117 (5 ambig, 100 out-of-scope, 29% of emitted, 0 unspellable, 12 §4-excluded), 11 duplicate |
| `gitnexus` | source only | 8s | 0.989 | 0.815 | 0.819 | 0.789 | 0.803 | 0.817 | 0.817 | 200 | 4 (0 ambig, 3 out-of-scope, 1% of emitted, 0 unspellable, 1 §4-excluded) |
| `graphify` | source only | 1s | 0.990 | 0.965 | 0.558 | 0.462 | 0.519 | 0.707 | 0.733 | 115 | 1 (0 ambig, 0 out-of-scope, 1 unspellable, 0 §4-excluded) |
| *`cha-null`* | bytecode | 0s | 1.000 | 0.794 | 0.889 | 1.000 | 1.000 | 0.839 | 0.840 | 223 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 0.794 | 0.803 | 1.000 | 1.000 | 199 | 0 |

**`precision`** counts a false positive only OUTSIDE the envelope, so over-approximation
inside it is free — which is correct for a tool that names the override that actually runs,
and is why a tool emitting the WHOLE envelope scored 1.000 on it while resolving nothing.
**`prec-strict`** is the other bound: of everything the tool said, how much was the declared
answer. Read them as a pair, against the `ideal` row rather than against 1.000 — a
flow-sensitive tool that is *sharper than the bytecode* gets no credit from the strict bound.
Rows in *italics* are NULL MODELS, not tools: a floor to clear, never ranked.

**`time`** is wall-clock for the adapter run that produced the answer, on the machine named
in the provenance block: the tool's own work plus this harness's translation of its output.
It is an order-of-magnitude figure for *what it costs to ask*, not a micro-benchmark.
Two rows produced by one adapter invocation — `axiom`/`axiom-nolib`,
`codeql`/`codeql-dispatch` — share one measured run; splitting it would invent a number.

**`needs`** is what the tool required to produce this answer, and it is a capability rather
than a score. `compiled build` means a working compile gave it full type information;
`build-mode=none` means it read the source tree without one; `source only` means it never
builds. A tool that needs a build is not usable where a build does not run, and a tool that
does not build is not seeing the same program. Comparing the two without saying so is the
easiest way to make a table mislead.

- `code-review-graph`: 0 rows named a type that matches more than one application type, 47 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `code-review-graph-dispatch`: 6 rows named a type that matches more than one application type, 47 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codeql`: 5 rows named a type that matches more than one application type, 148 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codeql-dispatch`: 5 rows named a type that matches more than one application type, 100 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `gitnexus`: 0 rows named a type that matches more than one application type, 3 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.

## Uniquely-linked call resolution — the number that separates the tools

Of the 145 link groups where the language admits **exactly one**
target, what did each tool actually return? A set where one answer exists is not a win, and a
wrong single answer is worse than an honest set — so the five outcomes are kept apart rather
than folded into one rate.

| tool | exact | over_fan | partial | polluted | ancestor | wrong | unknown | unplaced | missed | n | exact rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | 139 | 1 | 0 | 2 | 1 | 0 | 0 | 0 | 2 | 145 | 95.9% |
| `axiom-nolib` | 127 | 1 | 0 | 2 | 1 | 0 | 11 | 0 | 3 | 145 | 87.6% |
| `cha-null` | 145 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 145 | 100.0% |
| `code-review-graph` | 119 | 0 | 0 | 0 | 1 | 2 | 16 | 0 | 7 | 145 | 82.1% |
| `code-review-graph-dispatch` | 120 | 2 | 0 | 4 | 1 | 5 | 4 | 0 | 9 | 145 | 82.8% |
| `codegraph` | 97 | 0 | 0 | 0 | 0 | 2 | 33 | 0 | 13 | 145 | 66.9% |
| `codegraph-dispatch` | 96 | 0 | 0 | 1 | 0 | 2 | 33 | 0 | 13 | 145 | 66.2% |
| `codeql` | 143 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 145 | 98.6% |
| `codeql-dispatch` | 137 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 6 | 145 | 94.5% |
| `gitnexus` | 112 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 32 | 145 | 77.2% |
| `graphify` | 74 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 69 | 145 | 51.0% |
| `ideal` | 145 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 145 | 100.0% |

`exact` the one right method, alone · `over_fan` right method plus others, all sound ·
`polluted` right method plus something no envelope admits · `ancestor` named only a supertype
that declares the member (weaker, not fabricated) · `wrong` answered, none of it defensible ·
`missed` returned nothing.

## Genuinely ambiguous call resolution

The other 33 groups, where dispatch really does admit several
targets. Here `over_fan` is the *correct* behaviour and `exact` may mean the tool guessed one
branch and dropped the rest — so this table is read differently from the one above, and that
is exactly why they are not combined.

10 of these groups (36 call sites) are not dispatch either: several one-target
calls of the same name in one method — `new A()` and `new B()`, `getProject()` on two receivers —
pooled under one key (#70). Each call has exactly one target; a tool that names some of them
but not all reads `partial` here, all of them `exact`.

| tool | exact | over_fan | partial | polluted | ancestor | wrong | unknown | unplaced | missed | n | exact rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | 14 | 17 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 33 | 42.4% |
| `axiom-nolib` | 14 | 16 | 0 | 2 | 0 | 0 | 1 | 0 | 0 | 33 | 42.4% |
| `cha-null` | 10 | 23 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 33 | 30.3% |
| `code-review-graph` | 17 | 0 | 1 | 0 | 1 | 0 | 13 | 0 | 1 | 33 | 51.5% |
| `code-review-graph-dispatch` | 17 | 9 | 2 | 3 | 1 | 0 | 0 | 0 | 1 | 33 | 51.5% |
| `codegraph` | 24 | 0 | 0 | 1 | 0 | 0 | 7 | 0 | 1 | 33 | 72.7% |
| `codegraph-dispatch` | 12 | 11 | 0 | 2 | 0 | 0 | 7 | 0 | 1 | 33 | 36.4% |
| `codeql` | 33 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 33 | 100.0% |
| `codeql-dispatch` | 14 | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 33 | 42.4% |
| `gitnexus` | 15 | 15 | 0 | 1 | 0 | 0 | 0 | 0 | 2 | 33 | 45.5% |
| `graphify` | 21 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 33 | 63.6% |
| `ideal` | 33 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 33 | 100.0% |

## Call chains — reachability at depth 1..3

Nobody opens a call graph to look at one edge. They ask *if I change this, what breaks?*
and *can this reach that?* — both questions about PATHS, where error compounds: a chain is
only as sound as its weakest edge, and at the edge level answering "all of them" is free
(the null model reads precision 1.000 above). Over three hops it is not.

`R@k` is recall of the reachability the declared graph has. `P@k` is the share of what the
tool claims reachable that the declared graph reaches — the HARSH bound, charging the
envelope at a genuinely ambiguous call; `P-env@k` is the permissive one, charging only
outside the envelope's closure. `blowup@k` is the size of the tool's answer over the size of
the true answer — how many times the real answer a change-impact query gets back. `k=1` is
the edge metric, so the series reads as one story. Issue #5.

| tool | needs | R@1 | P@1 | P-env@1 | blowup@1 | R@2 | P@2 | P-env@2 | blowup@2 | R@3 | P@3 | P-env@3 | blowup@3 |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source + platform IR | 0.965 | 0.777 | 0.861 | 1.24× | 0.962 | 0.755 | 0.846 | 1.27× | 0.962 | 0.752 | 0.847 | 1.28× |
| `axiom-nolib` | source only | 0.899 | 0.778 | 0.865 | 1.16× | 0.906 | 0.757 | 0.851 | 1.20× | 0.907 | 0.754 | 0.853 | 1.20× |
| `code-review-graph` | source only | 0.759 | 0.868 | 0.830 | 0.87× | 0.748 | 0.850 | 0.810 | 0.88× | 0.746 | 0.850 | 0.811 | 0.88× |
| `code-review-graph-dispatch` | source only | 0.859 | 0.722 | 0.734 | 1.19× | 0.846 | 0.717 | 0.728 | 1.18× | 0.843 | 0.718 | 0.729 | 1.17× |
| `codegraph` | source only | 0.678 | 0.912 | 0.854 | 0.74× | 0.667 | 0.918 | 0.852 | 0.73× | 0.665 | 0.918 | 0.853 | 0.72× |
| `codegraph-dispatch` | source only | 0.678 | 0.780 | 0.844 | 0.87× | 0.671 | 0.773 | 0.844 | 0.87× | 0.669 | 0.771 | 0.845 | 0.87× |
| `codeql` | compiled build | 0.990 | 1.000 | 0.900 | 0.99× | 0.991 | 1.000 | 0.899 | 0.99× | 0.992 | 1.000 | 0.900 | 0.99× |
| `codeql-dispatch` | compiled build | 0.849 | 0.786 | 0.977 | 1.08× | 0.846 | 0.764 | 0.961 | 1.11× | 0.847 | 0.760 | 0.962 | 1.11× |
| `gitnexus` | source only | 0.819 | 0.815 | 0.872 | 1.01× | 0.833 | 0.809 | 0.867 | 1.03× | 0.835 | 0.811 | 0.868 | 1.03× |
| `graphify` | source only | 0.558 | 0.965 | 0.902 | 0.58× | 0.538 | 0.962 | 0.900 | 0.56× | 0.538 | 0.962 | 0.901 | 0.56× |
| *`cha-null`* | bytecode | 0.889 | 0.794 | 1.000 | 1.12× | 0.889 | 0.782 | 1.000 | 1.14× | 0.890 | 0.778 | 1.000 | 1.14× |
| *`ideal`* | oracle | 1.000 | 1.000 | 0.900 | 1.00× | 1.000 | 1.000 | 0.900 | 1.00× | 1.000 | 1.000 | 0.901 | 1.00× |

## Tier A (`type#name(params)`) — overload selection

Only tools whose output carries parameter types can be scored here. A dash is **not** a zero:
it means the tool's output format does not express the distinction, so the question was never
put to it.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source + platform IR | 14s | 0.982 | 0.776 | 0.950 | 0.956 | 0.962 | 0.855 | 0.859 | 246 | 4 (0 ambig, 0 out-of-scope, 4 unspellable, 0 §4-excluded), 13 duplicate |
| `axiom-nolib` | source only | 2s | 0.944 | 0.751 | 0.886 | 0.893 | 0.897 | 0.813 | 0.815 | 237 | 4 (0 ambig, 0 out-of-scope, 4 unspellable, 0 §4-excluded), 13 duplicate |
| `code-review-graph` | source only | 1s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `code-review-graph-dispatch` | source only | 1s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `codegraph` | source only | 1s | 0.876 | 0.848 | 0.473 | 0.378 | 0.400 | 0.607 | 0.632 | 112 | 41 (0 ambig, 0 out-of-scope, 41 unspellable, 0 §4-excluded), 5 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.885 | 0.693 | 0.473 | 0.480 | 0.476 | 0.562 | 0.572 | 137 | 41 (0 ambig, 0 out-of-scope, 41 unspellable, 0 §4-excluded), 5 duplicate |
| `codeql` | compiled build | 12s | 0.994 | 0.995 | 0.990 | 0.787 | 0.805 | 0.993 | 0.993 | 200 | 165 (5 ambig, 148 out-of-scope, 40% of emitted, 0 unspellable, 12 §4-excluded), 14 duplicate |
| `codeql-dispatch` | compiled build | 16s | 0.995 | 0.784 | 0.851 | 0.947 | 0.962 | 0.816 | 0.816 | 218 | 117 (5 ambig, 100 out-of-scope, 29% of emitted, 0 unspellable, 12 §4-excluded), 11 duplicate |
| `gitnexus` | source only | 8s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `graphify` | source only | 1s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| *`cha-null`* | bytecode | 0s | 1.000 | 0.796 | 0.891 | 1.000 | 1.000 | 0.840 | 0.841 | 225 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 0.796 | 0.805 | 1.000 | 1.000 | 201 | 0 |

## Tier C (`name`) — the floor

Method name only, no owner. Reported so that a name-only tool has a number at all. Read it
knowing that any two same-named methods in the subject are indistinguishable here, which
inflates every tool's score — the link-group table is **not** reported at this tier, because
its key is the callee name and every tool would score 100% by construction.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source + platform IR | 14s | 1.000 | 0.972 | 0.988 | 0.988 | 0.986 | 0.980 | 0.980 | 176 | 0, 13 duplicate |
| `axiom-nolib` | source only | 2s | 1.000 | 0.981 | 0.913 | 0.913 | 0.908 | 0.946 | 0.946 | 161 | 0, 13 duplicate |
| `code-review-graph` | source only | 1s | 0.912 | 0.868 | 0.954 | 0.954 | 0.958 | 0.909 | 0.910 | 190 | 47 (0 ambig, 47 out-of-scope, 18% of emitted, 0 unspellable, 0 §4-excluded), 10 duplicate |
| `code-review-graph-dispatch` | source only | 1s | 0.912 | 0.868 | 0.954 | 0.954 | 0.958 | 0.909 | 0.910 | 190 | 53 (6 ambig, 47 out-of-scope, 15% of emitted, 0 unspellable, 0 §4-excluded), 12 duplicate |
| `codegraph` | source only | 1s | 0.953 | 0.938 | 0.705 | 0.705 | 0.768 | 0.805 | 0.813 | 130 | 0, 5 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.953 | 0.938 | 0.705 | 0.705 | 0.768 | 0.805 | 0.813 | 130 | 0, 5 duplicate |
| `codeql` | compiled build | 12s | 1.000 | 1.000 | 0.988 | 0.988 | 1.000 | 0.994 | 0.994 | 171 | 165 (5 ambig, 148 out-of-scope, 40% of emitted, 0 unspellable, 12 §4-excluded), 14 duplicate |
| `codeql-dispatch` | compiled build | 16s | 1.000 | 0.982 | 0.954 | 0.954 | 0.965 | 0.968 | 0.968 | 168 | 117 (5 ambig, 100 out-of-scope, 29% of emitted, 0 unspellable, 12 §4-excluded), 11 duplicate |
| `gitnexus` | source only | 8s | 0.993 | 0.986 | 0.803 | 0.803 | 0.831 | 0.885 | 0.889 | 141 | 4 (0 ambig, 3 out-of-scope, 1% of emitted, 0 unspellable, 1 §4-excluded) |
| `graphify` | source only | 1s | 1.000 | 1.000 | 0.555 | 0.555 | 0.606 | 0.714 | 0.744 | 96 | 0 |
| *`cha-null`* | bytecode | 0s | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 173 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 173 | 0 |

## Does a tool's own confidence label predict its errors?

Every adapter carries the tool's self-reported confidence verbatim; scoring never reads it.
`rows`, `precision` and `prec-strict` are computed over the label's own rows. The verdict
columns are ATTRIBUTED: each uniquely-linked group is charged to the one label whose
target decided its verdict (the hit for `exact`; the ancestor or extra target for
`over_fan`; the target outside the envelope for `polluted` / `wrong`), so the columns sum to
the tool's own totals and a group is never counted twice (#41). `missed` has no label —
nothing was emitted — and is not a column here. The column to read is `wrong`: if a label
predicts the error, a consumer can filter on it; if it does not — or is inverted — the
precision figure above overstates what the output can be used for. Labels of the form
`term:score` are grouped by term with the score (rounded to two places) as sub-rows.

The labels are the tools' own vocabularies, not one scale: axiom `known_edge` /
`multi_inferred`; graphify and code-review-graph `EXTRACTED` / `INFERRED`; codegraph
`<resolvedBy>:<confidence>`; GitNexus `<reason>:<confidence>`; CodeQL (TypeScript)
`imprecision=N`, 0 precise to 3 heuristic. A tool that also records the calls it could NOT
resolve is listed below the table: those rows have no target and are never scored, but a
consumer can tell "it said it did not know" from "it missed".

| tool | label | rows | precision | prec-strict | exact | over_fan | polluted | ancestor | wrong |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | `known_edge` | 175 | 1.000 | 0.970 | 130 | 0 | 0 | 1 | 0 |
| `axiom` | `multi_inferred` | 87 | 0.927 | 0.383 | 9 | 1 | 2 | 0 | 0 |
| `axiom-nolib` | `known_edge` | 163 | 1.000 | 0.961 | 117 | 0 | 0 | 1 | 0 |
| `axiom-nolib` | `multi_inferred` | 90 | 0.926 | 0.408 | 10 | 1 | 2 | 0 | 0 |
| `code-review-graph` | `extracted` | 261 | 0.894 | 0.868 | 119 | 0 | 0 | 1 | 2 |
| `code-review-graph-dispatch` | `ambiguous_targets` | 71 | 0.744 | 0.317 | 1 | 2 | 4 | 0 | 3 |
| `code-review-graph-dispatch` | `extracted` | 236 | 0.894 | 0.868 | 119 | 0 | 0 | 1 | 2 |
| `codegraph` | `calls|exact-match` | 51 | 1.000 | 0.980 | 48 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.40` | 19 | 1.000 | 0.947 | 17 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.90` | 32 | 1.000 | 1.000 | 31 | 0 | 0 | 0 | 0 |
| `codegraph` | `calls|instance-method` | 54 | 0.825 | 0.796 | 30 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.65` | 2 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.70` | 22 | 0.650 | 0.591 | 13 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.90` | 30 | 1.000 | 0.933 | 15 | 0 | 0 | 0 | 0 |
| `codegraph` | `calls|qualified-name` | 2 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|qualified-name:0.85` | 2 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | 0 |
| `codegraph` | `instantiates|exact-match` | 35 | 1.000 | 1.000 | 11 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.90` | 35 | 1.000 | 1.000 | 11 | 0 | 0 | 0 | 0 |
| `codegraph` | `instantiates|framework` | 12 | 0.727 | 0.727 | 6 | 0 | 0 | 0 | 2 |
|  | &nbsp;&nbsp;↳ `instantiates|framework:0.70` | 12 | 0.727 | 0.727 | 6 | 0 | 0 | 0 | 2 |
| `codegraph` | `references|function-ref` | 1 | 1.000 | 1.000 | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `references|function-ref:0.90` | 1 | 1.000 | 1.000 | 0 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|exact-match` | 51 | 1.000 | 0.980 | 47 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.40` | 19 | 1.000 | 0.947 | 16 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.90` | 32 | 1.000 | 1.000 | 31 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|instance-method` | 54 | 0.825 | 0.796 | 30 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.65` | 2 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.70` | 22 | 0.650 | 0.591 | 13 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.90` | 30 | 1.000 | 0.933 | 15 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|qualified-name` | 2 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|qualified-name:0.85` | 2 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `instantiates|exact-match` | 35 | 1.000 | 1.000 | 11 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.90` | 35 | 1.000 | 1.000 | 11 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `instantiates|framework` | 12 | 0.727 | 0.727 | 6 | 0 | 0 | 0 | 2 |
|  | &nbsp;&nbsp;↳ `instantiates|framework:0.70` | 12 | 0.727 | 0.727 | 6 | 0 | 0 | 0 | 2 |
| `codegraph-dispatch` | `interface-impl` | 25 | 0.920 | 0.000 | 0 | 0 | 1 | 0 | 0 |
| `codegraph-dispatch` | `references|function-ref` | 1 | 1.000 | 1.000 | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `references|function-ref:0.90` | 1 | 1.000 | 1.000 | 0 | 0 | 0 | 0 | 0 |
| `gitnexus` | `callable-value-flow` | 2 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `callable-value-flow:0.80` | 2 | — | — | 0 | 0 | 0 | 0 | 0 |
| `gitnexus` | `global` | 65 | 1.000 | 0.985 | 42 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `global:0.85` | 65 | 1.000 | 0.985 | 42 | 0 | 0 | 0 | 0 |
| `gitnexus` | `import-resolved` | 2 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `import-resolved:0.85` | 2 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
| `gitnexus` | `interface-dispatch` | 33 | 1.000 | 0.000 | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `interface-dispatch:0.85` | 33 | 1.000 | 0.000 | 0 | 0 | 0 | 0 | 0 |
| `gitnexus` | `local-call` | 93 | 0.978 | 0.967 | 60 | 0 | 0 | 1 | 0 |
|  | &nbsp;&nbsp;↳ `local-call:0.85` | 93 | 0.978 | 0.967 | 60 | 0 | 0 | 1 | 0 |
| `gitnexus` | `scope-resolution: call` | 9 | 1.000 | 1.000 | 9 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `scope-resolution: call:0.57` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `scope-resolution: call:0.59` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `scope-resolution: call:0.61` | 5 | 1.000 | 1.000 | 5 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `scope-resolution: call:0.63` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `scope-resolution: call:1.00` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
| `graphify` | `extracted` | 93 | 0.989 | 0.957 | 63 | 0 | 0 | 1 | 1 |
| `graphify` | `inferred` | 23 | 1.000 | 1.000 | 11 | 0 | 0 | 0 | 0 |

- `axiom` wrote 1 rows labelled `ambiguous_anon` with no target — an anonymous target the tool does not name, not scored
- `axiom` wrote 2 rows labelled `ambiguous_unknown` with no target — the tool says it could not resolve the call (read as `unknown`, not `missed`, #69), not scored
- `axiom` wrote 97 rows labelled `boundary_lib` with no target — the callee is outside the staged code (a library), not scored
- `axiom-nolib` wrote 1 rows labelled `ambiguous_anon` with no target — an anonymous target the tool does not name, not scored
- `axiom-nolib` wrote 47 rows labelled `ambiguous_unknown` with no target — the tool says it could not resolve the call (read as `unknown`, not `missed`, #69), not scored
- `axiom-nolib` wrote 48 rows labelled `boundary_lib` with no target — the callee is outside the staged code (a library), not scored

## Per construct family — which language feature each tool loses

A single percentage cannot say *what* a tool gets wrong. Each family is one source file
exercising one group of constructs; the cell is `exact / uniquely-linked groups`.

| tool | F01 | F02 | F03 | F04 | F05 | F06 | F07 | F08 | F09 | F10 | F11 | F12 | other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `axiom` | 10/12 | 13/13 | 24/24 | 7/7 | 1/1 | 13/14 | 10/10 | 14/15 | 2/2 | 4/4 | 14/15 | 27/28 | — |
| `axiom-nolib` | 10/12 | 11/13 | 16/24 | 7/7 | 1/1 | 11/14 | 10/10 | 14/15 | 2/2 | 4/4 | 14/15 | 27/28 | — |
| `cha-null` | 12/12 | 13/13 | 24/24 | 7/7 | 1/1 | 14/14 | 10/10 | 15/15 | 2/2 | 4/4 | 15/15 | 28/28 | — |
| `code-review-graph` | 9/12 | 12/13 | 24/24 | 6/7 | 1/1 | 12/14 | 4/10 | 14/15 | 0/2 | 4/4 | 12/15 | 21/28 | — |
| `code-review-graph-dispatch` | 9/12 | 12/13 | 24/24 | 6/7 | 1/1 | 12/14 | 4/10 | 14/15 | 1/2 | 4/4 | 12/15 | 21/28 | — |
| `codegraph` | 10/12 | 4/13 | 17/24 | 6/7 | 1/1 | 8/14 | 4/10 | 10/15 | 1/2 | 4/4 | 11/15 | 21/28 | — |
| `codegraph-dispatch` | 10/12 | 4/13 | 17/24 | 6/7 | 1/1 | 8/14 | 4/10 | 10/15 | 1/2 | 4/4 | 10/15 | 21/28 | — |
| `codeql` | 12/12 | 13/13 | 24/24 | 7/7 | 1/1 | 14/14 | 8/10 | 15/15 | 2/2 | 4/4 | 15/15 | 28/28 | — |
| `codeql-dispatch` | 12/12 | 13/13 | 24/24 | 7/7 | 1/1 | 12/14 | 5/10 | 15/15 | 2/2 | 4/4 | 14/15 | 28/28 | — |
| `gitnexus` | 9/12 | 6/13 | 14/24 | 6/7 | 1/1 | 10/14 | 7/10 | 14/15 | 2/2 | 4/4 | 14/15 | 25/28 | — |
| `graphify` | 10/12 | 4/13 | 10/24 | 6/7 | 0/1 | 4/14 | 1/10 | 6/15 | 1/2 | 4/4 | 10/15 | 18/28 | — |
| `ideal` | 12/12 | 13/13 | 24/24 | 7/7 | 1/1 | 14/14 | 10/10 | 15/15 | 2/2 | 4/4 | 15/15 | 28/28 | — |

## Provenance

```json
{
  "input_sha256": {
    "classes": "d4b2692401ceaf408267289b796021471491cad9a4478e881502a4a036799661",
    "edges/axiom": "ef9f50040714a5fe8d16a17a52570649407f3be4875c9b90e1c94290f206686f",
    "edges/axiom-nolib": "af046d29cc873249c144a92b18f67e5f4f55c8ea38af657988bdb609b295b8db",
    "edges/cha-null": "3b4410b4c661d6dc0a3d1718f6af2a93b0331da4084202f48b3aefa13aae97d7",
    "edges/code-review-graph": "669169367db4658560b0673ba05f8a1337939f4f3a20e30124d24ad757512269",
    "edges/code-review-graph-dispatch": "ee20a0d700537a792e24d8287cf9fbd3327b712586e124920e0e8b1af7c93760",
    "edges/codegraph": "6a4f5beed49eb16704805f759344013291055b7ccfee16eb95f720149b6d2174",
    "edges/codegraph-dispatch": "4103d0a88a4eaef082a60762d4a88c9f66f935d49f36b51184db254eaa935779",
    "edges/codeql": "ae9e985df3f084fbb22171597970c00f14da96a658975156214c57103f9a4082",
    "edges/codeql-dispatch": "bdfbbb13c9f1b4cc7e0945fed90c30586c7ffe626faf33e0167424d5d9e5ba40",
    "edges/gitnexus": "4130a8edfe58dd4cbae894e47244c2bae0123b5371574bc975ea7a21ec59aca5",
    "edges/graphify": "1368018b9ac5e4bf55b2eb589bd484827696f664c461c1425b41d6783b1ff165",
    "edges/ideal": "1fbc01ead2c9bd1263b3f765031842b9075aa71cb1a98da9ce8fd343bf0747d8",
    "excluded": "3c1834d97dc37568dd72f8b1673ddeed7fd9e13d618e2e505b44cbcdfca5a5d7",
    "heritage": "8ff3c9faa003c7871da5960812094ad01da56b4042de80c6b0a4aeb386d1b7c3",
    "methods": "4ef6cd9e2c44f88a80676506c6e4ce69b182d63c81e28edfc9e3d67d790e80dc",
    "sites": "6a0363e05f918ba1b008f1f5e299fb35e0719732e219711d879317ce0a68a42b"
  },
  "java": "openjdk version \"24.0.2\" 2025-07-15",
  "javac": "javac 24.0.2",
  "language": "java",
  "platform": "Linux x86_64",
  "python": "3.12.3",
  "subject": "torture",
  "tools": {
    "axiom": {
      "build": "source + platform IR",
      "cache": "miss",
      "cold_seconds": 225.11,
      "dropped_in_adapter": 100,
      "engine_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "note": "platform IR modules staged: 63",
      "parser_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "rows_by_status": {
        "ambiguous_anon": 1,
        "ambiguous_unknown": 2,
        "boundary_lib": 97,
        "known_edge": 175,
        "multi_inferred": 87
      },
      "rows_kept": 262,
      "seconds_breakdown": {
        "adapter_total": 14.89,
        "library_cache": "miss",
        "own": 12.89,
        "shared": 1.34,
        "staging": null
      },
      "source": ".work/java/torture/axiom/out-axiom/raw/call-chain-edges.csv",
      "unresolved_sites": [
        [
          {
            "name": "wire",
            "params": [],
            "type": "torture.F06Functional"
          },
          57,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F06Functional.java"
        ]
      ]
    },
    "axiom-nolib": {
      "build": "source only",
      "cache": "miss",
      "cold_seconds": 225.11,
      "dropped_in_adapter": 96,
      "engine_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "note": "platform IR modules staged: 0",
      "parser_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "rows_by_status": {
        "ambiguous_anon": 1,
        "ambiguous_unknown": 47,
        "boundary_lib": 48,
        "known_edge": 163,
        "multi_inferred": 90
      },
      "rows_kept": 253,
      "seconds_breakdown": {
        "adapter_total": 14.89,
        "library_cache": "miss",
        "own": 0.47,
        "shared": 1.34,
        "staging": null
      },
      "source": ".work/java/torture/axiom/out-axiom-nolib/raw/call-chain-edges.csv",
      "unresolved_sites": [
        [
          {
            "name": "fromIndexedFor",
            "params": [],
            "type": "torture.F03Var"
          },
          25,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "params": [],
            "type": "torture.F03Var"
          },
          26,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "params": [],
            "type": "torture.F03Var"
          },
          26,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "params": [],
            "type": "torture.F03Var"
          },
          26,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnReturn",
            "params": [],
            "type": "torture.F03Var"
          },
          33,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnField",
            "params": [],
            "type": "torture.F03Var"
          },
          34,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "params": [],
            "type": "torture.F03Var"
          },
          35,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "params": [],
            "type": "torture.F03Var"
          },
          35,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "params": [],
            "type": "torture.F03Var"
          },
          35,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromTryResource",
            "params": [
              "java.io.StringReader"
            ],
            "type": "torture.F03Var"
          },
          39,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "viaServiceLoader",
            "params": [],
            "type": "torture.F09BlindSpots"
          },
          32,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "<init>",
            "params": [
              "String"
            ],
            "type": "it.example.F11Packages.Failure"
          },
          34,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/it/example/F11Packages.java"
        ],
        [
          {
            "name": "o5",
            "params": [],
            "type": "torture.F01Polymorphism"
          },
          57,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F01Polymorphism.java"
        ],
        [
          {
            "name": "viaElement",
            "params": [
              "List"
            ],
            "type": "torture.F02Generics"
          },
          50,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F02Generics.java"
        ],
        [
          {
            "name": "viaMapValue",
            "params": [
              "Map"
            ],
            "type": "torture.F02Generics"
          },
          52,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F02Generics.java"
        ],
        [
          {
            "name": "make",
            "params": [],
            "type": "torture.F02Generics"
          },
          54,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F02Generics.java"
        ],
        [
          {
            "name": "makeMap",
            "params": [],
            "type": "torture.F02Generics"
          },
          55,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F02Generics.java"
        ],
        [
          {
            "name": "many",
            "params": [],
            "type": "torture.F03Var"
          },
          18,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromGenericElement",
            "params": [],
            "type": "torture.F03Var"
          },
          23,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "mapReturn",
            "params": [],
            "type": "torture.F03Var"
          },
          31,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromLambdaParam",
            "params": [
              "List"
            ],
            "type": "torture.F03Var"
          },
          38,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromLibraryVar",
            "params": [],
            "type": "torture.F03Var"
          },
          41,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fromLibraryVar",
            "params": [],
            "type": "torture.F03Var"
          },
          41,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F03Var.java"
        ],
        [
          {
            "name": "fireTopic",
            "params": [
              "String",
              "String"
            ],
            "type": "torture.F04Events"
          },
          46,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F04Events.java"
        ],
        [
          {
            "name": "viaTable",
            "params": [
              "String",
              "Item"
            ],
            "type": "torture.F06Functional"
          },
          46,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F06Functional.java"
        ],
        [
          {
            "name": "viaHigherOrder",
            "params": [
              "Item"
            ],
            "type": "torture.F06Functional"
          },
          50,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F06Functional.java"
        ],
        [
          {
            "name": "insideLambda",
            "params": [
              "List"
            ],
            "type": "torture.F06Functional"
          },
          53,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F06Functional.java"
        ],
        [
          {
            "name": "insideLambda",
            "params": [
              "List"
            ],
            "type": "torture.F06Functional"
          },
          53,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F06Functional.java"
        ],
        [
          {
            "name": "insideLambda",
            "params": [
              "List"
            ],
            "type": "torture.F06Functional"
          },
          53,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F06Functional.java"
        ],
        [
          {
            "name": "wire",
            "params": [],
            "type": "torture.F06Functional"
          },
          57,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F06Functional.java"
        ],
        [
          {
            "name": "viaReflection",
            "params": [
              "Object",
              "String"
            ],
            "type": "torture.F09BlindSpots"
          },
          20,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "params": [
              "String"
            ],
            "type": "torture.F09BlindSpots"
          },
          24,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "params": [
              "String"
            ],
            "type": "torture.F09BlindSpots"
          },
          24,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "params": [
              "String"
            ],
            "type": "torture.F09BlindSpots"
          },
          24,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "params": [
              "InvocationHandler"
            ],
            "type": "torture.F09BlindSpots"
          },
          28,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "params": [
              "InvocationHandler"
            ],
            "type": "torture.F09BlindSpots"
          },
          28,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "params": [
              "InvocationHandler"
            ],
            "type": "torture.F09BlindSpots"
          },
          28,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaListElement",
            "params": [],
            "type": "torture.F10Flow"
          },
          32,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "params": [],
            "type": "torture.F10Flow"
          },
          32,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "params": [],
            "type": "torture.F10Flow"
          },
          32,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "params": [],
            "type": "torture.F10Flow"
          },
          32,
          "/home/Anonymous/bench/callgraph-benchmark/java/subjects/torture/client/torture/F10Flow.java"
        ]
      ]
    },
    "cha-null": {
      "build": "bytecode",
      "null_model": true,
      "reference": "null",
      "rows": 225,
      "version": "CHA envelope (no resolution)"
    },
    "code-review-graph": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 1.12,
      "declared_unresolved": 90,
      "fanned_rows": 0,
      "rows": 261,
      "seconds_breakdown": {
        "adapter_total": 1.39,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/java/torture/crg/data/graph.db",
      "unresolved_sites": [
        [
          {
            "name": "viaBase",
            "type": "F01Polymorphism"
          },
          41,
          "torture/F01Polymorphism.java"
        ],
        [
          {
            "name": "viaInterface",
            "type": "F01Polymorphism"
          },
          43,
          "torture/F01Polymorphism.java"
        ],
        [
          {
            "name": "viaAllocated",
            "type": "F01Polymorphism"
          },
          45,
          "torture/F01Polymorphism.java"
        ],
        [
          {
            "name": "viaCovariant",
            "type": "F01Polymorphism"
          },
          47,
          "torture/F01Polymorphism.java"
        ],
        [
          {
            "name": "viaDiamond",
            "type": "F01Polymorphism"
          },
          49,
          "torture/F01Polymorphism.java"
        ],
        [
          {
            "name": "o5",
            "type": "F01Polymorphism"
          },
          57,
          "torture/F01Polymorphism.java"
        ],
        [
          {
            "name": "viaRecursiveBound",
            "type": "F02Generics"
          },
          42,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaLibraryGeneric",
            "type": "F02Generics"
          },
          46,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "make",
            "type": "F02Generics"
          },
          54,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "makeMap",
            "type": "F02Generics"
          },
          55,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "many",
            "type": "F03Var"
          },
          18,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromGenericElement",
            "type": "F03Var"
          },
          23,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromIndexedFor",
            "type": "F03Var"
          },
          25,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromIndexedFor",
            "type": "F03Var"
          },
          25,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "mapReturn",
            "type": "F03Var"
          },
          31,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnReturn",
            "type": "F03Var"
          },
          33,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnReturn",
            "type": "F03Var"
          },
          33,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnField",
            "type": "F03Var"
          },
          34,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnField",
            "type": "F03Var"
          },
          34,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromLambdaParam",
            "type": "F03Var"
          },
          38,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromTryResource",
            "type": "F03Var"
          },
          39,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromTryResource",
            "type": "F03Var"
          },
          39,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromLibraryVar",
            "type": "F03Var"
          },
          41,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromLibraryVar",
            "type": "F03Var"
          },
          41,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "handle",
            "type": "AuditHandler"
          },
          21,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "fireAll",
            "type": "F04Events"
          },
          42,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "fireSingle",
            "type": "F04Events"
          },
          44,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "fireTopic",
            "type": "F04Events"
          },
          46,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "fireTopic",
            "type": "F04Events"
          },
          46,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryBus",
            "type": "F04Events"
          },
          48,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryReturn",
            "type": "F04Events"
          },
          50,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryDefault",
            "type": "F04Events"
          },
          52,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "F04Events"
          },
          55,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "F04Events"
          },
          56,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "F04Events"
          },
          60,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "F04Events"
          },
          61,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "F04Events"
          },
          61,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "upper",
            "type": "Item"
          },
          20,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "viaTable",
            "type": "F06Functional"
          },
          46,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "insideLambda",
            "type": "F06Functional"
          },
          53,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "insideLambda",
            "type": "F06Functional"
          },
          53,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "insideLambda",
            "type": "F06Functional"
          },
          53,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "wire",
            "type": "F06Functional"
          },
          56,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "wire",
            "type": "F06Functional"
          },
          57,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "wire",
            "type": "F06Functional"
          },
          58,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "describe",
            "type": "F07Modern"
          },
          16,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "describe",
            "type": "F07Modern"
          },
          17,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "describe",
            "type": "F07Modern"
          },
          18,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "accessor",
            "type": "F07Modern"
          },
          22,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "declared",
            "type": "F07Modern"
          },
          24,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "nested",
            "type": "F07Modern"
          },
          27,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "viaInstanceof",
            "type": "F07Modern"
          },
          31,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "viaAnonymous",
            "type": "F08Nesting"
          },
          36,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "encode",
            "type": "UpperCodec"
          },
          16,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "F09BlindSpots"
          },
          20,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "F09BlindSpots"
          },
          20,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "F09BlindSpots"
          },
          21,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaServiceLoader",
            "type": "F09BlindSpots"
          },
          32,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaServiceLoader",
            "type": "F09BlindSpots"
          },
          32,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "direct",
            "type": "F09BlindSpots"
          },
          36,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaField",
            "type": "F10Flow"
          },
          21,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaTernary",
            "type": "F10Flow"
          },
          22,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaSwitchExpr",
            "type": "F10Flow"
          },
          25,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaReassignment",
            "type": "F10Flow"
          },
          27,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaParameter",
            "type": "F10Flow"
          },
          30,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "type": "F10Flow"
          },
          32,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "type": "F10Flow"
          },
          32,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "type": "F10Flow"
          },
          32,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaChainedReturn",
            "type": "F10Flow"
          },
          33,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "use",
            "type": "F11Conventions"
          },
          41,
          "torture/F11Conventions.java"
        ],
        [
          {
            "name": "mkRef",
            "type": "F11Conventions"
          },
          42,
          "torture/F11Conventions.java"
        ],
        [
          {
            "name": "same",
            "type": "F11Conventions"
          },
          46,
          "torture/F11Conventions.java"
        ],
        [
          {
            "name": "main",
            "type": "F11Conventions"
          },
          53,
          "torture/F11Conventions.java"
        ],
        [
          {
            "name": "count",
            "type": "F12Lowering"
          },
          50,
          "torture/F12Lowering.java"
        ],
        [
          {
            "name": "helper",
            "type": "F12Lowering"
          },
          57,
          "torture/F12Lowering.java"
        ],
        [
          {
            "name": "area",
            "type": "F12Lowering"
          },
          63,
          "torture/F12Lowering.java"
        ],
        [
          {
            "name": "useA",
            "type": "F12Lowering"
          },
          77,
          "torture/F12Lowering.java"
        ],
        [
          {
            "name": "main",
            "type": "F12Lowering"
          },
          90,
          "torture/F12Lowering.java"
        ]
      ],
      "version": "code-review-graph 2.3.8"
    },
    "code-review-graph-dispatch": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 1.12,
      "declared_unresolved": 65,
      "fanned_rows": 25,
      "rows": 307,
      "seconds_breakdown": {
        "adapter_total": 1.39,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/java/torture/crg/data/graph.db",
      "unresolved_sites": [
        [
          {
            "name": "o5",
            "type": "F01Polymorphism"
          },
          57,
          "torture/F01Polymorphism.java"
        ],
        [
          {
            "name": "viaLibraryGeneric",
            "type": "F02Generics"
          },
          46,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "make",
            "type": "F02Generics"
          },
          54,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "makeMap",
            "type": "F02Generics"
          },
          55,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "many",
            "type": "F03Var"
          },
          18,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromGenericElement",
            "type": "F03Var"
          },
          23,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromIndexedFor",
            "type": "F03Var"
          },
          25,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromIndexedFor",
            "type": "F03Var"
          },
          25,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "mapReturn",
            "type": "F03Var"
          },
          31,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnReturn",
            "type": "F03Var"
          },
          33,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnReturn",
            "type": "F03Var"
          },
          33,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnField",
            "type": "F03Var"
          },
          34,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnField",
            "type": "F03Var"
          },
          34,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromLambdaParam",
            "type": "F03Var"
          },
          38,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromTryResource",
            "type": "F03Var"
          },
          39,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromTryResource",
            "type": "F03Var"
          },
          39,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromLibraryVar",
            "type": "F03Var"
          },
          41,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromLibraryVar",
            "type": "F03Var"
          },
          41,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "handle",
            "type": "AuditHandler"
          },
          21,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "fireTopic",
            "type": "F04Events"
          },
          46,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "fireTopic",
            "type": "F04Events"
          },
          46,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryBus",
            "type": "F04Events"
          },
          48,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryReturn",
            "type": "F04Events"
          },
          50,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryDefault",
            "type": "F04Events"
          },
          52,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "F04Events"
          },
          55,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "F04Events"
          },
          56,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "F04Events"
          },
          60,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "F04Events"
          },
          61,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "upper",
            "type": "Item"
          },
          20,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "viaTable",
            "type": "F06Functional"
          },
          46,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "insideLambda",
            "type": "F06Functional"
          },
          53,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "insideLambda",
            "type": "F06Functional"
          },
          53,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "insideLambda",
            "type": "F06Functional"
          },
          53,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "wire",
            "type": "F06Functional"
          },
          56,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "wire",
            "type": "F06Functional"
          },
          57,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "wire",
            "type": "F06Functional"
          },
          58,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "accessor",
            "type": "F07Modern"
          },
          22,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "viaAnonymous",
            "type": "F08Nesting"
          },
          36,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "encode",
            "type": "UpperCodec"
          },
          16,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "F09BlindSpots"
          },
          20,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "F09BlindSpots"
          },
          20,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "F09BlindSpots"
          },
          21,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaServiceLoader",
            "type": "F09BlindSpots"
          },
          32,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaListElement",
            "type": "F10Flow"
          },
          32,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "type": "F10Flow"
          },
          32,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "type": "F10Flow"
          },
          32,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaChainedReturn",
            "type": "F10Flow"
          },
          33,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "same",
            "type": "F11Conventions"
          },
          46,
          "torture/F11Conventions.java"
        ],
        [
          {
            "name": "main",
            "type": "F11Conventions"
          },
          53,
          "torture/F11Conventions.java"
        ],
        [
          {
            "name": "count",
            "type": "F12Lowering"
          },
          50,
          "torture/F12Lowering.java"
        ],
        [
          {
            "name": "helper",
            "type": "F12Lowering"
          },
          57,
          "torture/F12Lowering.java"
        ],
        [
          {
            "name": "useA",
            "type": "F12Lowering"
          },
          77,
          "torture/F12Lowering.java"
        ],
        [
          {
            "name": "main",
            "type": "F12Lowering"
          },
          90,
          "torture/F12Lowering.java"
        ]
      ],
      "version": "code-review-graph 2.3.8"
    },
    "codegraph": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 0.87,
      "declared_unresolved": 92,
      "dispatch_expanded_sites": 0,
      "function_ref_rows": 1,
      "rows": 155,
      "seconds_breakdown": {
        "adapter_total": 0.81,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/java/torture/cg/src/.codegraph/codegraph.db",
      "synthesized_rows_skipped": 17,
      "unresolved_sites": [
        [
          {
            "name": "create",
            "type": "it.example.F11Packages"
          },
          24,
          "it/example/F11Packages.java"
        ],
        [
          {
            "name": "viaInherited",
            "type": "torture.F01Polymorphism"
          },
          51,
          "torture/F01Polymorphism.java"
        ],
        [
          {
            "name": "firstOf",
            "type": "torture.F02Generics"
          },
          35,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaSubclassBinding",
            "type": "torture.F02Generics"
          },
          38,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaSubclassBinding",
            "type": "torture.F02Generics"
          },
          38,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaInlineBinding",
            "type": "torture.F02Generics"
          },
          40,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaGenericMethod",
            "type": "torture.F02Generics"
          },
          44,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaLibraryGeneric",
            "type": "torture.F02Generics"
          },
          46,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaLibraryGeneric",
            "type": "torture.F02Generics"
          },
          46,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaChainedGeneric",
            "type": "torture.F02Generics"
          },
          48,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaChainedGeneric",
            "type": "torture.F02Generics"
          },
          48,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaChainedGeneric",
            "type": "torture.F02Generics"
          },
          48,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaElement",
            "type": "torture.F02Generics"
          },
          50,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaElement",
            "type": "torture.F02Generics"
          },
          50,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaMapValue",
            "type": "torture.F02Generics"
          },
          52,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaMapValue",
            "type": "torture.F02Generics"
          },
          52,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "fromChain",
            "type": "torture.F03Var"
          },
          22,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromGenericElement",
            "type": "torture.F03Var"
          },
          23,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromGenericElement",
            "type": "torture.F03Var"
          },
          23,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromIndexedFor",
            "type": "torture.F03Var"
          },
          25,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromIndexedFor",
            "type": "torture.F03Var"
          },
          25,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "torture.F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "torture.F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "torture.F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnReturn",
            "type": "torture.F03Var"
          },
          33,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnReturn",
            "type": "torture.F03Var"
          },
          33,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnReturn",
            "type": "torture.F03Var"
          },
          33,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnField",
            "type": "torture.F03Var"
          },
          34,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnField",
            "type": "torture.F03Var"
          },
          34,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnField",
            "type": "torture.F03Var"
          },
          34,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "torture.F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "torture.F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "torture.F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromLambdaParam",
            "type": "torture.F03Var"
          },
          38,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromTryResource",
            "type": "torture.F03Var"
          },
          39,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromLibraryVar",
            "type": "torture.F03Var"
          },
          41,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fireAll",
            "type": "torture.F04Events"
          },
          42,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "fireTopic",
            "type": "torture.F04Events"
          },
          46,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "fireTopic",
            "type": "torture.F04Events"
          },
          46,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryBus",
            "type": "torture.F04Events"
          },
          48,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryReturn",
            "type": "torture.F04Events"
          },
          50,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryReturn",
            "type": "torture.F04Events"
          },
          50,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryDefault",
            "type": "torture.F04Events"
          },
          52,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F04Events"
          },
          55,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F04Events"
          },
          56,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F04Events"
          },
          60,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F04Events"
          },
          61,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "upper",
            "type": "torture.F06Functional.Item"
          },
          20,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "viaTable",
            "type": "torture.F06Functional"
          },
          46,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "viaTable",
            "type": "torture.F06Functional"
          },
          46,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "viaChain",
            "type": "torture.F06Functional"
          },
          48,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "applyTwice",
            "type": "torture.F06Functional"
          },
          51,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "applyTwice",
            "type": "torture.F06Functional"
          },
          51,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "insideLambda",
            "type": "torture.F06Functional"
          },
          53,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F06Functional"
          },
          56,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F06Functional"
          },
          57,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "describe",
            "type": "torture.F07Modern"
          },
          16,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "describe",
            "type": "torture.F07Modern"
          },
          17,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "describe",
            "type": "torture.F07Modern"
          },
          18,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "accessor",
            "type": "torture.F07Modern"
          },
          22,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "declared",
            "type": "torture.F07Modern"
          },
          24,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "nested",
            "type": "torture.F07Modern"
          },
          27,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "viaInstanceof",
            "type": "torture.F07Modern"
          },
          31,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "viaLocalClass",
            "type": "torture.F08Nesting"
          },
          32,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "viaAnonymous",
            "type": "torture.F08Nesting"
          },
          39,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "viaInner",
            "type": "torture.F08Nesting"
          },
          42,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "viaNested",
            "type": "torture.F08Nesting"
          },
          43,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "viaDeep",
            "type": "torture.F08Nesting"
          },
          44,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "encode",
            "type": "torture.F09BlindSpots.UpperCodec"
          },
          16,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "torture.F09BlindSpots"
          },
          20,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "torture.F09BlindSpots"
          },
          20,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "torture.F09BlindSpots"
          },
          21,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "torture.F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "torture.F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "torture.F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "torture.F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "torture.F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "torture.F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaServiceLoader",
            "type": "torture.F09BlindSpots"
          },
          32,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaServiceLoader",
            "type": "torture.F09BlindSpots"
          },
          32,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaArrayElement",
            "type": "torture.F10Flow"
          },
          28,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaCast",
            "type": "torture.F10Flow"
          },
          29,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaReturnValue",
            "type": "torture.F10Flow"
          },
          31,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "type": "torture.F10Flow"
          },
          32,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "type": "torture.F10Flow"
          },
          32,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaChainedReturn",
            "type": "torture.F10Flow"
          },
          33,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaChainedReturn",
            "type": "torture.F10Flow"
          },
          33,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "same",
            "type": "torture.F11Conventions"
          },
          46,
          "torture/F11Conventions.java"
        ],
        [
          {
            "name": "main",
            "type": "torture.F11Conventions"
          },
          49,
          "torture/F11Conventions.java"
        ],
        [
          {
            "name": "count",
            "type": "torture.F12Lowering"
          },
          50,
          "torture/F12Lowering.java"
        ],
        [
          {
            "name": "helper",
            "type": "torture.F12Lowering"
          },
          57,
          "torture/F12Lowering.java"
        ],
        [
          {
            "name": "main",
            "type": "torture.F12Lowering"
          },
          88,
          "torture/F12Lowering.java"
        ]
      ],
      "version": "codegraph 1.6.0"
    },
    "codegraph-dispatch": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 0.87,
      "declared_unresolved": 92,
      "dispatch_expanded_sites": 15,
      "function_ref_rows": 1,
      "rows": 180,
      "seconds_breakdown": {
        "adapter_total": 0.81,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/java/torture/cg/src/.codegraph/codegraph.db",
      "synthesized_rows_skipped": 17,
      "unresolved_sites": [
        [
          {
            "name": "create",
            "type": "it.example.F11Packages"
          },
          24,
          "it/example/F11Packages.java"
        ],
        [
          {
            "name": "viaInherited",
            "type": "torture.F01Polymorphism"
          },
          51,
          "torture/F01Polymorphism.java"
        ],
        [
          {
            "name": "firstOf",
            "type": "torture.F02Generics"
          },
          35,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaSubclassBinding",
            "type": "torture.F02Generics"
          },
          38,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaSubclassBinding",
            "type": "torture.F02Generics"
          },
          38,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaInlineBinding",
            "type": "torture.F02Generics"
          },
          40,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaGenericMethod",
            "type": "torture.F02Generics"
          },
          44,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaLibraryGeneric",
            "type": "torture.F02Generics"
          },
          46,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaLibraryGeneric",
            "type": "torture.F02Generics"
          },
          46,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaChainedGeneric",
            "type": "torture.F02Generics"
          },
          48,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaChainedGeneric",
            "type": "torture.F02Generics"
          },
          48,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaChainedGeneric",
            "type": "torture.F02Generics"
          },
          48,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaElement",
            "type": "torture.F02Generics"
          },
          50,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaElement",
            "type": "torture.F02Generics"
          },
          50,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaMapValue",
            "type": "torture.F02Generics"
          },
          52,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "viaMapValue",
            "type": "torture.F02Generics"
          },
          52,
          "torture/F02Generics.java"
        ],
        [
          {
            "name": "fromChain",
            "type": "torture.F03Var"
          },
          22,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromGenericElement",
            "type": "torture.F03Var"
          },
          23,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromGenericElement",
            "type": "torture.F03Var"
          },
          23,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromIndexedFor",
            "type": "torture.F03Var"
          },
          25,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromIndexedFor",
            "type": "torture.F03Var"
          },
          25,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "torture.F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "torture.F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntry",
            "type": "torture.F03Var"
          },
          26,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnReturn",
            "type": "torture.F03Var"
          },
          33,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnReturn",
            "type": "torture.F03Var"
          },
          33,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnReturn",
            "type": "torture.F03Var"
          },
          33,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnField",
            "type": "torture.F03Var"
          },
          34,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnField",
            "type": "torture.F03Var"
          },
          34,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnField",
            "type": "torture.F03Var"
          },
          34,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "torture.F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "torture.F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromMapEntryOnDeclared",
            "type": "torture.F03Var"
          },
          35,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromLambdaParam",
            "type": "torture.F03Var"
          },
          38,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromTryResource",
            "type": "torture.F03Var"
          },
          39,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fromLibraryVar",
            "type": "torture.F03Var"
          },
          41,
          "torture/F03Var.java"
        ],
        [
          {
            "name": "fireAll",
            "type": "torture.F04Events"
          },
          42,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "fireTopic",
            "type": "torture.F04Events"
          },
          46,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "fireTopic",
            "type": "torture.F04Events"
          },
          46,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryBus",
            "type": "torture.F04Events"
          },
          48,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryReturn",
            "type": "torture.F04Events"
          },
          50,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryReturn",
            "type": "torture.F04Events"
          },
          50,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "viaLibraryDefault",
            "type": "torture.F04Events"
          },
          52,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F04Events"
          },
          55,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F04Events"
          },
          56,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F04Events"
          },
          60,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F04Events"
          },
          61,
          "torture/F04Events.java"
        ],
        [
          {
            "name": "upper",
            "type": "torture.F06Functional.Item"
          },
          20,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "viaTable",
            "type": "torture.F06Functional"
          },
          46,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "viaTable",
            "type": "torture.F06Functional"
          },
          46,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "viaChain",
            "type": "torture.F06Functional"
          },
          48,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "applyTwice",
            "type": "torture.F06Functional"
          },
          51,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "applyTwice",
            "type": "torture.F06Functional"
          },
          51,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "insideLambda",
            "type": "torture.F06Functional"
          },
          53,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F06Functional"
          },
          56,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "wire",
            "type": "torture.F06Functional"
          },
          57,
          "torture/F06Functional.java"
        ],
        [
          {
            "name": "describe",
            "type": "torture.F07Modern"
          },
          16,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "describe",
            "type": "torture.F07Modern"
          },
          17,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "describe",
            "type": "torture.F07Modern"
          },
          18,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "accessor",
            "type": "torture.F07Modern"
          },
          22,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "declared",
            "type": "torture.F07Modern"
          },
          24,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "nested",
            "type": "torture.F07Modern"
          },
          27,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "viaInstanceof",
            "type": "torture.F07Modern"
          },
          31,
          "torture/F07Modern.java"
        ],
        [
          {
            "name": "viaLocalClass",
            "type": "torture.F08Nesting"
          },
          32,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "viaAnonymous",
            "type": "torture.F08Nesting"
          },
          39,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "viaInner",
            "type": "torture.F08Nesting"
          },
          42,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "viaNested",
            "type": "torture.F08Nesting"
          },
          43,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "viaDeep",
            "type": "torture.F08Nesting"
          },
          44,
          "torture/F08Nesting.java"
        ],
        [
          {
            "name": "encode",
            "type": "torture.F09BlindSpots.UpperCodec"
          },
          16,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "torture.F09BlindSpots"
          },
          20,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "torture.F09BlindSpots"
          },
          20,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaReflection",
            "type": "torture.F09BlindSpots"
          },
          21,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "torture.F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "torture.F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaForName",
            "type": "torture.F09BlindSpots"
          },
          24,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "torture.F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "torture.F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaProxy",
            "type": "torture.F09BlindSpots"
          },
          28,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaServiceLoader",
            "type": "torture.F09BlindSpots"
          },
          32,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaServiceLoader",
            "type": "torture.F09BlindSpots"
          },
          32,
          "torture/F09BlindSpots.java"
        ],
        [
          {
            "name": "viaArrayElement",
            "type": "torture.F10Flow"
          },
          28,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaCast",
            "type": "torture.F10Flow"
          },
          29,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaReturnValue",
            "type": "torture.F10Flow"
          },
          31,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "type": "torture.F10Flow"
          },
          32,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaListElement",
            "type": "torture.F10Flow"
          },
          32,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaChainedReturn",
            "type": "torture.F10Flow"
          },
          33,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "viaChainedReturn",
            "type": "torture.F10Flow"
          },
          33,
          "torture/F10Flow.java"
        ],
        [
          {
            "name": "same",
            "type": "torture.F11Conventions"
          },
          46,
          "torture/F11Conventions.java"
        ],
        [
          {
            "name": "main",
            "type": "torture.F11Conventions"
          },
          49,
          "torture/F11Conventions.java"
        ],
        [
          {
            "name": "count",
            "type": "torture.F12Lowering"
          },
          50,
          "torture/F12Lowering.java"
        ],
        [
          {
            "name": "helper",
            "type": "torture.F12Lowering"
          },
          57,
          "torture/F12Lowering.java"
        ],
        [
          {
            "name": "main",
            "type": "torture.F12Lowering"
          },
          88,
          "torture/F12Lowering.java"
        ]
      ],
      "version": "codegraph 1.6.0"
    },
    "codeql": {
      "build": "compiled build",
      "cache": "miss",
      "cold_seconds": 63.5,
      "rows": 371,
      "seconds_breakdown": {
        "adapter_total": 28.03,
        "own": 4.4,
        "shared": 8.09,
        "staging": null
      },
      "source": ".work/java/torture/codeql/codeql.csv",
      "version": "codeql 2.23.8 java-all 7.8.2"
    },
    "codeql-dispatch": {
      "build": "compiled build",
      "cache": "miss",
      "cold_seconds": 63.5,
      "rows": 341,
      "seconds_breakdown": {
        "adapter_total": 28.03,
        "own": 7.64,
        "shared": 8.09,
        "staging": null
      },
      "source": ".work/java/torture/codeql/codeql-dispatch.csv",
      "version": "codeql 2.23.8 java-all 7.8.2"
    },
    "gitnexus": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 9.93,
      "rows": 204,
      "seconds_breakdown": {
        "adapter_total": 9.31,
        "export": 1.19,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "version": "gitnexus 1.6.11"
    },
    "graphify": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 0.4,
      "rows": 116,
      "seconds_breakdown": {
        "adapter_total": 0.61,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/java/torture/gfy/src/graphify-out/graph.json",
      "version": "graphifyy 0.9.58"
    },
    "ideal": {
      "build": "oracle",
      "null_model": true,
      "reference": "ideal",
      "rows": 201,
      "version": "the correct answer for every link group (a ceiling, not a tool)"
    }
  }
}
```
