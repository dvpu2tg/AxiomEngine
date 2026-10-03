# TypeScript call-graph benchmark — `torture`

Ground truth is the TypeScript compiler's own type checker (`getResolvedSignature`). There
is no second implementation of the type system, so gate 1 checks only that two checker entry
points agree — it proves our USE of the checker, not the checker. Calls through a function
value, where the checker names a type rather than an implementation, are recorded and NOT
scored; their count is in the table below, because on idiomatic TypeScript it is not small.
See `docs/PROTOCOL.md` for every definition below; `docs/CROSS-LANGUAGE.md` for what is and
is not comparable across languages.

## The subject, and the denominators every number below is over

| quantity | count |
|---|---:|
| application types | 67 |
| application methods | 134 |
| call sites the checker resolved | 86 |
| … application-internal | 67 |
| … leaving the application (not scored, see §7) | 9 |
| … through a function value, target not statically known (not scored) | 10 |
| call expressions the checker could NOT resolve — no row of any kind; every recall denominator is short by this many, for every tool alike (#53) | 0 |
| … i.e. the checker resolved this % of the subject's call expressions (gate 0's floor is 55%) | 100.0 |
| … and this % resolve to a target INSIDE the subject — the scorable share; a library target clears the floor without adding one (#67) | 91.8 |
| **CERTAIN** edges (declared targets) — `recall_certain` denominator | 68 |
| **POSSIBLE** edges (declared-heritage + checker-assignable envelope — NOT sound, structural typing) — `recall_possible` denominator | 90 |
| **RTA** edges (instantiated-types envelope) — `recall_rta` denominator | 59 |
| link groups `(caller, callee-name)`, at Tier B | 66 |
| … **uniquely linked** (exactly one possible target) — the headline denominator | 53 |
| … uniquely linked at Tier A (overloads kept apart) | 53 |
| … genuinely ambiguous (dispatch admits several) | 13 |

Call sites by instruction: `CALL` 80, `NEW` 6.

## Headline — Tier B (`type#name`)

Tier B is the highest fidelity **every** tool under test can express, so it is the only tier
at which the whole field is comparable. The ground truth is projected to Tier B as well, so a
tool that cannot spell parameter types is not being asked to.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 1s | 0.920 | 0.741 | 0.926 | 0.767 | 0.780 | 0.824 | 0.828 | 85 | 16 (0 ambig, 0 out-of-scope, 2 unspellable, 14 §4-excluded), 3 duplicate |
| `code-review-graph` | source only | 1s | 0.892 | 0.875 | 0.515 | 0.367 | 0.407 | 0.648 | 0.670 | 40 | 24 (4 ambig, 7 out-of-scope, 11% of emitted, 7 unspellable, 6 §4-excluded) |
| `code-review-graph-dispatch` | source only | 1s | 0.918 | 0.712 | 0.544 | 0.500 | 0.492 | 0.617 | 0.621 | 52 | 19 (6 ambig, 7 out-of-scope, 10% of emitted, 0 unspellable, 6 §4-excluded), 2 duplicate |
| `codegraph` | source only | 1s | 0.900 | 0.854 | 0.515 | 0.400 | 0.492 | 0.642 | 0.662 | 41 | 19 (9 ambig, 0 out-of-scope, 0 unspellable, 10 §4-excluded) |
| `codegraph-dispatch` | source only | 1s | 0.886 | 0.778 | 0.515 | 0.433 | 0.542 | 0.619 | 0.632 | 45 | 19 (9 ambig, 0 out-of-scope, 0 unspellable, 10 §4-excluded) |
| `codeql` | source only | 12s | 0.967 | 0.879 | 0.853 | 0.656 | 0.712 | 0.866 | 0.865 | 66 | 36 (7 ambig, 0 out-of-scope, 0 unspellable, 29 §4-excluded), 3 duplicate |
| `gitnexus` | source only | 10s | 0.880 | 0.810 | 0.691 | 0.489 | 0.576 | 0.746 | 0.747 | 58 | 15 (0 ambig, 3 out-of-scope, 4% of emitted, 0 unspellable, 12 §4-excluded) |
| `graphify` | source only | 0s | 0.886 | 0.644 | 0.426 | 0.433 | 0.542 | 0.513 | 0.523 | 45 | 14 (5 ambig, 0 out-of-scope, 0 unspellable, 9 §4-excluded) |
| *`cha-null`* | bytecode | 0s | 1.000 | 0.656 | 0.868 | 1.000 | 1.000 | 0.747 | 0.753 | 90 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 0.656 | 0.712 | 1.000 | 1.000 | 68 | 0 |

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

**`needs`** is what the tool required to produce this answer, and it is a capability rather
than a score. `compiled build` means a working compile gave it full type information;
`build-mode=none` means it read the source tree without one; `source only` means it never
builds. A tool that needs a build is not usable where a build does not run, and a tool that
does not build is not seeing the same program. Comparing the two without saying so is the
easiest way to make a table mislead.

- `code-review-graph`: 4 rows named a type that matches more than one application type, 7 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `code-review-graph-dispatch`: 6 rows named a type that matches more than one application type, 7 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codegraph`: 9 rows named a type that matches more than one application type, 0 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codegraph-dispatch`: 9 rows named a type that matches more than one application type, 0 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codeql`: 7 rows named a type that matches more than one application type, 0 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `gitnexus`: 0 rows named a type that matches more than one application type, 3 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `graphify`: 5 rows named a type that matches more than one application type, 0 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.

## Uniquely-linked call resolution — the number that separates the tools

Of the 53 link groups where the language admits **exactly one**
target, what did each tool actually return? A set where one answer exists is not a win, and a
wrong single answer is worse than an honest set — so the five outcomes are kept apart rather
than folded into one rate.

| tool | exact | over_fan | partial | polluted | ancestor | wrong | unknown | unplaced | missed | n | exact rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | 47 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 5 | 53 | 88.7% |
| `cha-null` | 53 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 53 | 100.0% |
| `code-review-graph` | 30 | 0 | 0 | 0 | 0 | 0 | 5 | 1 | 17 | 53 | 56.6% |
| `code-review-graph-dispatch` | 31 | 0 | 0 | 0 | 0 | 0 | 3 | 1 | 18 | 53 | 58.5% |
| `codegraph` | 32 | 0 | 0 | 0 | 0 | 1 | 7 | 4 | 9 | 53 | 60.4% |
| `codegraph-dispatch` | 31 | 0 | 0 | 1 | 0 | 1 | 7 | 4 | 9 | 53 | 58.5% |
| `codeql` | 47 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 5 | 53 | 88.7% |
| `gitnexus` | 36 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 17 | 53 | 67.9% |
| `graphify` | 29 | 0 | 0 | 0 | 0 | 1 | 0 | 4 | 19 | 53 | 54.7% |
| `ideal` | 53 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 53 | 100.0% |

`exact` the one right method, alone · `over_fan` right method plus others, all sound ·
`polluted` right method plus something no envelope admits · `ancestor` named only a supertype
that declares the member (weaker, not fabricated) · `wrong` answered, none of it defensible ·
`missed` returned nothing.

## Genuinely ambiguous call resolution

The other 13 groups, where dispatch really does admit several
targets. Here `over_fan` is the *correct* behaviour and `exact` may mean the tool guessed one
branch and dropped the rest — so this table is read differently from the one above, and that
is exactly why they are not combined.

| tool | exact | over_fan | partial | polluted | ancestor | wrong | unknown | unplaced | missed | n | exact rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | 6 | 6 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 13 | 46.2% |
| `cha-null` | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 0.0% |
| `code-review-graph` | 5 | 0 | 0 | 0 | 0 | 0 | 8 | 0 | 0 | 13 | 38.5% |
| `code-review-graph-dispatch` | 6 | 5 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 13 | 46.2% |
| `codegraph` | 4 | 0 | 0 | 0 | 0 | 0 | 6 | 3 | 0 | 13 | 30.8% |
| `codegraph-dispatch` | 1 | 3 | 0 | 0 | 0 | 0 | 6 | 3 | 0 | 13 | 7.7% |
| `codeql` | 9 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 13 | 69.2% |
| `gitnexus` | 10 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 13 | 76.9% |
| `graphify` | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 13 | 76.9% |
| `ideal` | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 100.0% |

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
| `axiom` | source only | 0.926 | 0.778 | 0.840 | 1.19× | 0.936 | 0.737 | 0.811 | 1.27× | 0.936 | 0.737 | 0.811 | 1.27× |
| `code-review-graph` | source only | 0.515 | 0.897 | 0.854 | 0.57× | 0.462 | 0.900 | 0.857 | 0.51× | 0.462 | 0.900 | 0.857 | 0.51× |
| `code-review-graph-dispatch` | source only | 0.544 | 0.725 | 0.860 | 0.75× | 0.487 | 0.691 | 0.864 | 0.71× | 0.487 | 0.691 | 0.864 | 0.71× |
| `codegraph` | source only | 0.515 | 0.854 | 0.875 | 0.60× | 0.474 | 0.841 | 0.881 | 0.56× | 0.474 | 0.841 | 0.881 | 0.56× |
| `codegraph-dispatch` | source only | 0.515 | 0.778 | 0.854 | 0.66× | 0.474 | 0.740 | 0.860 | 0.64× | 0.474 | 0.740 | 0.860 | 0.64× |
| `codeql` | source only | 0.853 | 0.892 | 0.906 | 0.96× | 0.821 | 0.831 | 0.901 | 0.99× | 0.821 | 0.831 | 0.901 | 0.99× |
| `gitnexus` | source only | 0.691 | 0.825 | 0.783 | 0.84× | 0.679 | 0.736 | 0.707 | 0.92× | 0.679 | 0.736 | 0.707 | 0.92× |
| `graphify` | source only | 0.426 | 0.674 | 0.879 | 0.63× | 0.385 | 0.612 | 0.909 | 0.63× | 0.385 | 0.612 | 0.909 | 0.63× |
| *`cha-null`* | bytecode | 0.868 | 0.656 | 1.000 | 1.32× | 0.821 | 0.552 | 1.000 | 1.49× | 0.821 | 0.552 | 1.000 | 1.49× |
| *`ideal`* | oracle | 1.000 | 1.000 | 0.883 | 1.00× | 1.000 | 1.000 | 0.848 | 1.00× | 1.000 | 1.000 | 0.848 | 1.00× |

## Tier A (`type#name(params)`) — overload selection

Only tools whose output carries parameter types can be scored here. A dash is **not** a zero:
it means the tool's output format does not express the distinction, so the question was never
put to it.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 1s | 0.907 | 0.729 | 0.912 | 0.756 | 0.763 | 0.810 | 0.815 | 85 | 16 (0 ambig, 0 out-of-scope, 2 unspellable, 14 §4-excluded), 3 duplicate |
| `code-review-graph` | source only | 1s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `code-review-graph-dispatch` | source only | 1s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `codegraph` | source only | 1s | 0.800 | 0.742 | 0.338 | 0.267 | 0.288 | 0.465 | 0.500 | 31 | 29 (9 ambig, 0 out-of-scope, 10 unspellable, 10 §4-excluded) |
| `codegraph-dispatch` | source only | 1s | 0.794 | 0.657 | 0.338 | 0.300 | 0.339 | 0.447 | 0.470 | 35 | 29 (9 ambig, 0 out-of-scope, 10 unspellable, 10 §4-excluded) |
| `codeql` | source only | 12s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `gitnexus` | source only | 10s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `graphify` | source only | 0s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| *`cha-null`* | bytecode | 0s | 1.000 | 0.656 | 0.868 | 1.000 | 1.000 | 0.747 | 0.753 | 90 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 0.656 | 0.712 | 1.000 | 1.000 | 68 | 0 |

## Tier C (`name`) — the floor

Method name only, no owner. Reported so that a name-only tool has a number at all. Read it
knowing that any two same-named methods in the subject are indistinguishable here, which
inflates every tool's score — the link-group table is **not** reported at this tier, because
its key is the callee name and every tool would score 100% by construction.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 1s | 0.934 | 0.919 | 0.934 | 0.919 | 0.900 | 0.927 | 0.926 | 62 | 14 (0 ambig, 0 out-of-scope, 0 unspellable, 14 §4-excluded), 3 duplicate |
| `code-review-graph` | source only | 1s | 0.913 | 0.894 | 0.689 | 0.677 | 0.640 | 0.778 | 0.783 | 47 | 17 (4 ambig, 7 out-of-scope, 11% of emitted, 0 unspellable, 6 §4-excluded) |
| `code-review-graph-dispatch` | source only | 1s | 0.913 | 0.894 | 0.689 | 0.677 | 0.640 | 0.778 | 0.783 | 47 | 19 (6 ambig, 7 out-of-scope, 10% of emitted, 0 unspellable, 6 §4-excluded), 2 duplicate |
| `codegraph` | source only | 1s | 0.925 | 0.902 | 0.607 | 0.597 | 0.660 | 0.725 | 0.738 | 41 | 19 (9 ambig, 0 out-of-scope, 0 unspellable, 10 §4-excluded) |
| `codegraph-dispatch` | source only | 1s | 0.925 | 0.902 | 0.607 | 0.597 | 0.660 | 0.725 | 0.738 | 41 | 19 (9 ambig, 0 out-of-scope, 0 unspellable, 10 §4-excluded) |
| `codeql` | source only | 12s | 0.964 | 0.947 | 0.885 | 0.871 | 0.880 | 0.915 | 0.915 | 57 | 36 (7 ambig, 0 out-of-scope, 0 unspellable, 29 §4-excluded), 3 duplicate |
| `gitnexus` | source only | 10s | 0.904 | 0.885 | 0.754 | 0.758 | 0.800 | 0.814 | 0.815 | 52 | 15 (0 ambig, 3 out-of-scope, 4% of emitted, 0 unspellable, 12 §4-excluded) |
| `graphify` | source only | 0s | 0.907 | 0.886 | 0.639 | 0.629 | 0.660 | 0.743 | 0.751 | 44 | 14 (5 ambig, 0 out-of-scope, 0 unspellable, 9 §4-excluded) |
| *`cha-null`* | bytecode | 0s | 1.000 | 0.984 | 1.000 | 1.000 | 1.000 | 0.992 | 0.992 | 62 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 0.984 | 0.980 | 1.000 | 1.000 | 61 | 0 |

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
| `axiom` | `known_edge` | 66 | 0.922 | 0.904 | 44 | 0 | 0 | 0 | 0 |
| `axiom` | `multi_inferred` | 37 | 0.917 | 0.485 | 3 | 0 | 1 | 0 | 0 |
| `code-review-graph` | `extracted` | 64 | 0.892 | 0.875 | 30 | 0 | 0 | 0 | 0 |
| `code-review-graph-dispatch` | `ambiguous_targets` | 14 | 1.000 | 0.167 | 1 | 0 | 0 | 0 | 0 |
| `code-review-graph-dispatch` | `extracted` | 57 | 0.892 | 0.875 | 30 | 0 | 0 | 0 | 0 |
| `codegraph` | `calls|exact-match` | 32 | 0.880 | 0.840 | 20 | 0 | 0 | 0 | 1 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.40` | 18 | 0.909 | 0.818 | 8 | 0 | 0 | 0 | 1 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.90` | 14 | 0.857 | 0.857 | 12 | 0 | 0 | 0 | 0 |
| `codegraph` | `calls|import` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|import:0.90` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
| `codegraph` | `calls|instance-method` | 12 | 0.857 | 0.750 | 4 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.70` | 3 | 0.500 | 0.500 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.80` | 2 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.90` | 7 | 1.000 | 0.750 | 1 | 0 | 0 | 0 | 0 |
| `codegraph` | `calls|qualified-name` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|qualified-name:0.85` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
| `codegraph` | `instantiates|exact-match` | 13 | 1.000 | 1.000 | 6 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.40` | 3 | 1.000 | 1.000 | 3 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.90` | 10 | 1.000 | 1.000 | 3 | 0 | 0 | 0 | 0 |
| `codegraph` | `instantiates|import` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|import:0.90` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|exact-match` | 32 | 0.880 | 0.840 | 20 | 0 | 0 | 0 | 1 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.40` | 18 | 0.909 | 0.818 | 8 | 0 | 0 | 0 | 1 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.90` | 14 | 0.857 | 0.857 | 12 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|import` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|import:0.90` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|instance-method` | 12 | 0.857 | 0.750 | 4 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.70` | 3 | 0.500 | 0.500 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.80` | 2 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.90` | 7 | 1.000 | 0.750 | 1 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|qualified-name` | 1 | 1.000 | 1.000 | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|qualified-name:0.85` | 1 | 1.000 | 1.000 | 0 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `instantiates|exact-match` | 13 | 1.000 | 1.000 | 6 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.40` | 3 | 1.000 | 1.000 | 3 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.90` | 10 | 1.000 | 1.000 | 3 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `instantiates|import` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|import:0.90` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `interface-impl` | 4 | 0.750 | 0.000 | 0 | 0 | 1 | 0 | 0 |
| `codeql` | `imprecision=0` | 105 | 0.967 | 0.879 | 47 | 0 | 0 | 0 | 0 |
| `gitnexus` | `callable-value-flow` | 2 | 0.000 | 0.000 | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `callable-value-flow:0.80` | 2 | 0.000 | 0.000 | 0 | 0 | 0 | 0 | 0 |
| `gitnexus` | `global` | 22 | 1.000 | 1.000 | 11 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `global:0.85` | 22 | 1.000 | 1.000 | 11 | 0 | 0 | 0 | 0 |
| `gitnexus` | `import-resolved` | 7 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `import-resolved:0.85` | 7 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
| `gitnexus` | `interface-dispatch` | 5 | 1.000 | 0.000 | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `interface-dispatch:0.85` | 5 | 1.000 | 0.000 | 0 | 0 | 0 | 0 | 0 |
| `gitnexus` | `local-call` | 34 | 0.889 | 0.889 | 24 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `local-call:0.85` | 34 | 0.889 | 0.889 | 24 | 0 | 0 | 0 | 0 |
| `gitnexus` | `property-dispatch` | 3 | 0.333 | 0.000 | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `property-dispatch:0.70` | 3 | 0.333 | 0.000 | 0 | 0 | 0 | 0 | 0 |
| `graphify` | `extracted` | 59 | 0.886 | 0.644 | 29 | 0 | 0 | 0 | 1 |

- `axiom` wrote 10 rows labelled `ambiguous_unknown` with no target — the tool says it could not resolve the call (read as `unknown`, not `missed`, #69), not scored

## Per construct family — which language feature each tool loses

A single percentage cannot say *what* a tool gets wrong. Each family is one source file
exercising one group of constructs; the cell is `exact / uniquely-linked groups`.

| tool | other |
|---|---|
| `axiom` | 47/53 |
| `cha-null` | 53/53 |
| `code-review-graph` | 30/53 |
| `code-review-graph-dispatch` | 31/53 |
| `codegraph` | 32/53 |
| `codegraph-dispatch` | 31/53 |
| `codeql` | 47/53 |
| `gitnexus` | 36/53 |
| `graphify` | 29/53 |
| `ideal` | 53/53 |

## Provenance

```json
{
  "input_sha256": {
    "classes": "c88c23362af167f5124e03bfee3a3225183297f768fce56409d9a2996888ecf7",
    "edges/axiom": "9e80e3869660878d02e40d54b05c898bf7a1722243fc7f7ca46f90ecf10da93f",
    "edges/cha-null": "f6d76df20c77ba6b2ccef8dcfc2e95db4b3eba6bf3f6b89990f20349d3c1d1e8",
    "edges/code-review-graph": "5e3ca3659556e2ff2f9fe04781d6548ffec76bb4ca52fff3c8d48e1b35d5aff3",
    "edges/code-review-graph-dispatch": "960eafac109cf1556af11769ec36825ff8d8693cff6212d4331e00f65569f7c9",
    "edges/codegraph": "cf7c9ab97ba4034f8d46cf93b53ef1a3f389f63602b0b14380704fe3de9cb4f9",
    "edges/codegraph-dispatch": "d1e0383b3e1a5950e9172aa9b3e7c1aaff2ea31c09743d68f92ca4c424f3d422",
    "edges/codeql": "2c8c266c4bb70ffb19c3396c0044c7b59ed99c709a52a8889d0b4650e30cbcbc",
    "edges/gitnexus": "63b130ddd85c7a01e6f1c6b38990c13277bb1e9ac40046ede473a4088ce521fd",
    "edges/graphify": "c94677adbc92520d01ff8bbd6640529eea75fcaef6c8bd74088877fdf2e13271",
    "edges/ideal": "c4fef2f632cf81edcda8dfd6dce67df0a5f30f3ed64d879506cfcba688c122a7",
    "excluded": "297865a293be474000a617353993da71f4bcded8709b05a030f9a41977f579cd",
    "heritage": "bb94d1012f5a2ee21c7433bd1544e50cc905332e9a0aecb625eb8bde655dfbc6",
    "methods": "e544b508ccdf72fbf279a51a8445d02659d2b3822b504accf811baace2243879",
    "sites": "f345908010eda42c1d1f275cee1385f6d1ecc1b7d5abd0ebd16b55586a9b772d"
  },
  "language": "typescript",
  "platform": "Linux x86_64",
  "python": "3.12.3",
  "staged_copy": {
    "files": 13,
    "sha256": "e73e3c309dbb39fa420f17aec1c8e1c66963e96abdfca157ca409dea9246b652"
  },
  "subject": "torture",
  "tools": {
    "axiom": {
      "build": "source only",
      "cache": "miss",
      "cold_seconds": 166.93,
      "engine_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "function_type_targets_dropped": 7,
      "note": "typescript front end, empty library",
      "parser_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "rows": 103,
      "rows_by_status": {
        "ambiguous_unknown": 10,
        "known_edge": 72,
        "multi_inferred": 38
      },
      "rows_without_method": 10,
      "seconds_breakdown": {
        "adapter_total": 1.12,
        "own": 0.4,
        "shared": 0.61,
        "staging": null
      },
      "source": ".work/typescript/torture/axiom/out/raw/call-chain-edges.csv",
      "unresolved_sites": [
        [
          {
            "name": "handle",
            "params": [
              "string"
            ],
            "type": "src/t02-structural#LoudHandler"
          },
          14,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "handle",
            "params": [
              "string"
            ],
            "type": "src/t02-structural#quietHandler"
          },
          19,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "string"
            ],
            "type": "src/t02-structural"
          },
          32,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "usesClosure",
            "params": [
              "number[]"
            ],
            "type": "src/t03-functions"
          },
          14,
          "src/t03-functions.ts"
        ],
        [
          {
            "name": "viaTable",
            "params": [
              "string",
              "number"
            ],
            "type": "src/t03-functions"
          },
          23,
          "src/t03-functions.ts"
        ],
        [
          {
            "name": "viaGenericMethod",
            "params": [
              ""
            ],
            "type": "src/t04-overloads"
          },
          19,
          "src/t04-overloads.ts"
        ],
        [
          {
            "name": "run",
            "params": [],
            "type": "src/t06-arrows#Widget"
          },
          26,
          "src/t06-arrows.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "src/t06-arrows"
          },
          53,
          "src/t06-arrows.ts"
        ],
        [
          {
            "name": "chooseFn",
            "params": [
              "boolean"
            ],
            "type": "src/t10-audit"
          },
          10,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "binaryFindPartition",
            "params": [
              "number[]",
              "(v: number) => boolean"
            ],
            "type": "src/t10-audit"
          },
          38,
          "src/t10-audit.ts"
        ]
      ]
    },
    "cha-null": {
      "build": "bytecode",
      "null_model": true,
      "reference": "null",
      "rows": 90,
      "version": "CHA envelope (no resolution)"
    },
    "code-review-graph": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 1.11,
      "declared_unresolved": 28,
      "fanned_rows": 0,
      "rows": 64,
      "seconds_breakdown": {
        "adapter_total": 1.35,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/torture/crg/data/graph.db",
      "unresolved_sites": [
        [
          {
            "name": "describe",
            "type": "src/t01-classes.ts"
          },
          14,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "describe",
            "type": "src/t01-classes.ts"
          },
          14,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "viaBase",
            "type": "src/t01-classes.ts"
          },
          30,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "viaInterface",
            "type": "src/t01-classes.ts"
          },
          32,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "viaAllocated",
            "type": "src/t01-classes.ts"
          },
          34,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "viaInherited",
            "type": "src/t01-classes.ts"
          },
          36,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "handle",
            "type": "LoudHandler"
          },
          14,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "handle",
            "type": "src/t02-structural.ts"
          },
          19,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "dispatch",
            "type": "src/t02-structural.ts"
          },
          22,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "viaInline",
            "type": "src/t02-structural.ts"
          },
          32,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "usesClosure",
            "type": "src/t03-functions.ts"
          },
          14,
          "src/t03-functions.ts"
        ],
        [
          {
            "name": "higherOrder",
            "type": "src/t03-functions.ts"
          },
          18,
          "src/t03-functions.ts"
        ],
        [
          {
            "name": "call",
            "type": "Holder"
          },
          27,
          "src/t03-functions.ts"
        ],
        [
          {
            "name": "map",
            "type": "Box"
          },
          15,
          "src/t04-overloads.ts"
        ],
        [
          {
            "name": "viaGenericMethod",
            "type": "src/t04-overloads.ts"
          },
          19,
          "src/t04-overloads.ts"
        ],
        [
          {
            "name": "viaCore",
            "type": "src/t05-modules.ts"
          },
          8,
          "src/t05-modules.ts"
        ],
        [
          {
            "name": "viaUtil",
            "type": "src/t05-modules.ts"
          },
          9,
          "src/t05-modules.ts"
        ],
        [
          {
            "name": "run",
            "type": "Widget"
          },
          26,
          "src/t06-arrows.ts"
        ],
        [
          {
            "name": "dispatch",
            "type": "src/t08-envelope.ts"
          },
          11,
          "src/t08-envelope.ts"
        ],
        [
          {
            "name": "dispatchFn",
            "type": "src/t08-envelope.ts"
          },
          28,
          "src/t08-envelope.ts"
        ],
        [
          {
            "name": "chooseFn",
            "type": "src/t10-audit.ts"
          },
          10,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "viaUnionArm",
            "type": "src/t10-audit.ts"
          },
          18,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "binaryFindPartition",
            "type": "src/t10-audit.ts"
          },
          38,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "inherited",
            "type": "src/t11-envelope2.ts"
          },
          6,
          "src/t11-envelope2.ts"
        ],
        [
          {
            "name": "generic",
            "type": "src/t11-envelope2.ts"
          },
          10,
          "src/t11-envelope2.ts"
        ],
        [
          {
            "name": "abstractRedecl",
            "type": "src/t11-envelope2.ts"
          },
          15,
          "src/t11-envelope2.ts"
        ],
        [
          {
            "name": "boundFn",
            "type": "src/t11-envelope2.ts"
          },
          27,
          "src/t11-envelope2.ts"
        ],
        [
          {
            "name": "page",
            "type": "src/t11-envelope2.ts"
          },
          31,
          "src/t11-envelope2.ts"
        ]
      ],
      "version": "code-review-graph 2.3.8"
    },
    "code-review-graph-dispatch": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 1.11,
      "declared_unresolved": 21,
      "fanned_rows": 7,
      "rows": 71,
      "seconds_breakdown": {
        "adapter_total": 1.35,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/torture/crg/data/graph.db",
      "unresolved_sites": [
        [
          {
            "name": "viaInterface",
            "type": "src/t01-classes.ts"
          },
          32,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "viaInherited",
            "type": "src/t01-classes.ts"
          },
          36,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "handle",
            "type": "LoudHandler"
          },
          14,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "handle",
            "type": "src/t02-structural.ts"
          },
          19,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "dispatch",
            "type": "src/t02-structural.ts"
          },
          22,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "viaInline",
            "type": "src/t02-structural.ts"
          },
          32,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "usesClosure",
            "type": "src/t03-functions.ts"
          },
          14,
          "src/t03-functions.ts"
        ],
        [
          {
            "name": "higherOrder",
            "type": "src/t03-functions.ts"
          },
          18,
          "src/t03-functions.ts"
        ],
        [
          {
            "name": "call",
            "type": "Holder"
          },
          27,
          "src/t03-functions.ts"
        ],
        [
          {
            "name": "map",
            "type": "Box"
          },
          15,
          "src/t04-overloads.ts"
        ],
        [
          {
            "name": "viaGenericMethod",
            "type": "src/t04-overloads.ts"
          },
          19,
          "src/t04-overloads.ts"
        ],
        [
          {
            "name": "run",
            "type": "Widget"
          },
          26,
          "src/t06-arrows.ts"
        ],
        [
          {
            "name": "dispatch",
            "type": "src/t08-envelope.ts"
          },
          11,
          "src/t08-envelope.ts"
        ],
        [
          {
            "name": "dispatchFn",
            "type": "src/t08-envelope.ts"
          },
          28,
          "src/t08-envelope.ts"
        ],
        [
          {
            "name": "chooseFn",
            "type": "src/t10-audit.ts"
          },
          10,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "viaUnionArm",
            "type": "src/t10-audit.ts"
          },
          18,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "binaryFindPartition",
            "type": "src/t10-audit.ts"
          },
          38,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "inherited",
            "type": "src/t11-envelope2.ts"
          },
          6,
          "src/t11-envelope2.ts"
        ],
        [
          {
            "name": "generic",
            "type": "src/t11-envelope2.ts"
          },
          10,
          "src/t11-envelope2.ts"
        ],
        [
          {
            "name": "boundFn",
            "type": "src/t11-envelope2.ts"
          },
          27,
          "src/t11-envelope2.ts"
        ],
        [
          {
            "name": "page",
            "type": "src/t11-envelope2.ts"
          },
          31,
          "src/t11-envelope2.ts"
        ]
      ],
      "version": "code-review-graph 2.3.8"
    },
    "codegraph": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 0.75,
      "declared_unresolved": 23,
      "dispatch_expanded_sites": 0,
      "rows": 60,
      "seconds_breakdown": {
        "adapter_total": 0.77,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "synthesized_rows_skipped": 7,
      "unresolved_sites": [
        [
          {
            "name": "constructor",
            "type": "Square"
          },
          18,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Unit"
          },
          25,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "viaBase",
            "type": "src/t01-classes.ts"
          },
          30,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "viaInterface",
            "type": "src/t01-classes.ts"
          },
          32,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "viaAllocated",
            "type": "src/t01-classes.ts"
          },
          34,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "handle",
            "type": "LoudHandler"
          },
          14,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "handle",
            "type": "src/t02-structural.ts"
          },
          19,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "dispatch",
            "type": "src/t02-structural.ts"
          },
          22,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "viaInline",
            "type": "src/t02-structural.ts"
          },
          32,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "viaTable",
            "type": "src/t03-functions.ts"
          },
          23,
          "src/t03-functions.ts"
        ],
        [
          {
            "name": "viaGenericMethod",
            "type": "src/t04-overloads.ts"
          },
          19,
          "src/t04-overloads.ts"
        ],
        [
          {
            "name": "viaInner",
            "type": "Widget"
          },
          31,
          "src/t06-arrows.ts"
        ],
        [
          {
            "name": "dispatch",
            "type": "src/t08-envelope.ts"
          },
          11,
          "src/t08-envelope.ts"
        ],
        [
          {
            "name": "dispatchFn",
            "type": "src/t08-envelope.ts"
          },
          28,
          "src/t08-envelope.ts"
        ],
        [
          {
            "name": "chooseFn",
            "type": "src/t10-audit.ts"
          },
          10,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "viaUnionArm",
            "type": "src/t10-audit.ts"
          },
          18,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "WithCtor"
          },
          30,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Sub"
          },
          31,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "binaryFindPartition",
            "type": "src/t10-audit.ts"
          },
          38,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "elementAccess",
            "type": "src/t10-audit.ts"
          },
          48,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "inherited",
            "type": "src/t11-envelope2.ts"
          },
          6,
          "src/t11-envelope2.ts"
        ],
        [
          {
            "name": "abstractRedecl",
            "type": "src/t11-envelope2.ts"
          },
          15,
          "src/t11-envelope2.ts"
        ],
        [
          {
            "name": "page",
            "type": "src/t11-envelope2.ts"
          },
          31,
          "src/t11-envelope2.ts"
        ]
      ],
      "version": "codegraph 1.6.0"
    },
    "codegraph-dispatch": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 0.75,
      "declared_unresolved": 23,
      "dispatch_expanded_sites": 4,
      "rows": 64,
      "seconds_breakdown": {
        "adapter_total": 0.77,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "synthesized_rows_skipped": 7,
      "unresolved_sites": [
        [
          {
            "name": "constructor",
            "type": "Square"
          },
          18,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Unit"
          },
          25,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "viaBase",
            "type": "src/t01-classes.ts"
          },
          30,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "viaInterface",
            "type": "src/t01-classes.ts"
          },
          32,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "viaAllocated",
            "type": "src/t01-classes.ts"
          },
          34,
          "src/t01-classes.ts"
        ],
        [
          {
            "name": "handle",
            "type": "LoudHandler"
          },
          14,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "handle",
            "type": "src/t02-structural.ts"
          },
          19,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "dispatch",
            "type": "src/t02-structural.ts"
          },
          22,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "viaInline",
            "type": "src/t02-structural.ts"
          },
          32,
          "src/t02-structural.ts"
        ],
        [
          {
            "name": "viaTable",
            "type": "src/t03-functions.ts"
          },
          23,
          "src/t03-functions.ts"
        ],
        [
          {
            "name": "viaGenericMethod",
            "type": "src/t04-overloads.ts"
          },
          19,
          "src/t04-overloads.ts"
        ],
        [
          {
            "name": "viaInner",
            "type": "Widget"
          },
          31,
          "src/t06-arrows.ts"
        ],
        [
          {
            "name": "dispatch",
            "type": "src/t08-envelope.ts"
          },
          11,
          "src/t08-envelope.ts"
        ],
        [
          {
            "name": "dispatchFn",
            "type": "src/t08-envelope.ts"
          },
          28,
          "src/t08-envelope.ts"
        ],
        [
          {
            "name": "chooseFn",
            "type": "src/t10-audit.ts"
          },
          10,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "viaUnionArm",
            "type": "src/t10-audit.ts"
          },
          18,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "WithCtor"
          },
          30,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Sub"
          },
          31,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "binaryFindPartition",
            "type": "src/t10-audit.ts"
          },
          38,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "elementAccess",
            "type": "src/t10-audit.ts"
          },
          48,
          "src/t10-audit.ts"
        ],
        [
          {
            "name": "inherited",
            "type": "src/t11-envelope2.ts"
          },
          6,
          "src/t11-envelope2.ts"
        ],
        [
          {
            "name": "abstractRedecl",
            "type": "src/t11-envelope2.ts"
          },
          15,
          "src/t11-envelope2.ts"
        ],
        [
          {
            "name": "page",
            "type": "src/t11-envelope2.ts"
          },
          31,
          "src/t11-envelope2.ts"
        ]
      ],
      "version": "codegraph 1.6.0"
    },
    "codeql": {
      "build": "source only",
      "cache": "miss",
      "cold_seconds": 49.1,
      "rows": 105,
      "seconds_breakdown": {
        "adapter_total": 18.69,
        "own": 6.12,
        "shared": 6.32,
        "staging": null
      },
      "source": ".work/typescript/torture/codeql/q.csv",
      "version": "codeql 2.23.8 javascript-all 2.6.18"
    },
    "gitnexus": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 7.25,
      "rows": 73,
      "seconds_breakdown": {
        "adapter_total": 10.25,
        "export": 0.66,
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
      "rows": 59,
      "seconds_breakdown": {
        "adapter_total": 0.5,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/torture/gfy/src/graphify-out/graph.json",
      "version": "graphifyy 0.9.58"
    },
    "ideal": {
      "build": "oracle",
      "null_model": true,
      "reference": "ideal",
      "rows": 68,
      "version": "the correct answer for every link group (a ceiling, not a tool)"
    }
  },
  "tsx": "4.19.2",
  "typescript": "5.6.3"
}
```
