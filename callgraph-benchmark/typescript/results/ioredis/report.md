# TypeScript call-graph benchmark — `ioredis`

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
| application types | 100 |
| application methods | 2,032 |
| call sites the checker resolved | 800 |
| … application-internal | 371 |
| … leaving the application (not scored, see §7) | 316 |
| … through a function value, target not statically known (not scored) | 113 |
| call expressions the checker could NOT resolve — no row of any kind; every recall denominator is short by this many, for every tool alike (#53) | 394 |
| … i.e. the checker resolved this % of the subject's call expressions (gate 0's floor is 55%) | 67.2 |
| … and this % resolve to a target INSIDE the subject — the scorable share; a library target clears the floor without adding one (#67) | 40.8 |
| **CERTAIN** edges (declared targets) — `recall_certain` denominator | 308 |
| **POSSIBLE** edges (declared-heritage + checker-assignable envelope — NOT sound, structural typing) — `recall_possible` denominator | 310 |
| **RTA** edges (instantiated-types envelope) — `recall_rta` denominator | 229 |
| link groups `(caller, callee-name)`, at Tier B | 303 |
| … **uniquely linked** (exactly one possible target) — the headline denominator | 298 |
| … uniquely linked at Tier A (overloads kept apart) | 296 |
| … genuinely ambiguous (dispatch admits several) | 5 |

Call sites by instruction: `CALL` 714, `NEW` 86.

## Headline — Tier B (`type#name`)

Tier B is the highest fidelity **every** tool under test can express, so it is the only tier
at which the whole field is comparable. The ground truth is projected to Tier B as well, so a
tool that cannot spell parameter types is not being asked to.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 3s | 0.962 | 0.953 | 0.922 | 0.906 | 0.899 | 0.937 | 0.937 | 296 | 14 (6 ambig, 4 out-of-scope, 1% of emitted, 0 unspellable, 4 §4-excluded), 56 duplicate |
| `code-review-graph` | source only | 2s | 0.667 | 0.670 | 0.761 | 0.747 | 0.731 | 0.713 | 0.714 | 348 | 577 (6 ambig, 374 out-of-scope, 36% of emitted, 112 unspellable, 85 §4-excluded), 260 duplicate |
| `code-review-graph-dispatch` | source only | 2s | 0.630 | 0.633 | 0.768 | 0.753 | 0.740 | 0.694 | 0.697 | 371 | 566 (6 ambig, 374 out-of-scope, 35% of emitted, 101 unspellable, 85 §4-excluded), 262 duplicate |
| `codegraph` | source only | 1s | 0.689 | 0.689 | 0.660 | 0.656 | 0.652 | 0.674 | 0.674 | 293 | 42 (1 ambig, 34 out-of-scope, 8% of emitted, 0 unspellable, 7 §4-excluded), 85 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.680 | 0.680 | 0.660 | 0.656 | 0.652 | 0.670 | 0.670 | 297 | 42 (1 ambig, 34 out-of-scope, 8% of emitted, 0 unspellable, 7 §4-excluded), 85 duplicate |
| `codeql` | source only | 17s | 0.791 | 0.785 | 0.850 | 0.838 | 0.846 | 0.816 | 0.817 | 331 | 176 (0 ambig, 3 out-of-scope, 0% of emitted, 0 unspellable, 173 §4-excluded), 194 duplicate |
| `gitnexus` | source only | 19s | 0.980 | 0.980 | 0.650 | 0.636 | 0.630 | 0.782 | 0.798 | 203 | 28 (1 ambig, 9 out-of-scope, 3% of emitted, 3 unspellable, 15 §4-excluded), 41 duplicate |
| `graphify` | source only | 2s | 0.800 | 0.802 | 0.647 | 0.636 | 0.709 | 0.716 | 0.720 | 247 | 39 (1 ambig, 35 out-of-scope, 12% of emitted, 0 unspellable, 3 §4-excluded) |
| *`cha-null`* | bytecode | 0s | 1.000 | 0.974 | 0.980 | 1.000 | 1.000 | 0.977 | 0.977 | 308 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 0.974 | 1.000 | 1.000 | 1.000 | 306 | 0 |

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

- `axiom`: 6 rows named a type that matches more than one application type, 4 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `code-review-graph`: 6 rows named a type that matches more than one application type, 374 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `code-review-graph-dispatch`: 6 rows named a type that matches more than one application type, 374 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codegraph`: 1 rows named a type that matches more than one application type, 34 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codegraph-dispatch`: 1 rows named a type that matches more than one application type, 34 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codeql`: 0 rows named a type that matches more than one application type, 3 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `gitnexus`: 1 rows named a type that matches more than one application type, 9 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `graphify`: 1 rows named a type that matches more than one application type, 35 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.

## Uniquely-linked call resolution — the number that separates the tools

Of the 298 link groups where the language admits **exactly one**
target, what did each tool actually return? A set where one answer exists is not a win, and a
wrong single answer is worse than an honest set — so the five outcomes are kept apart rather
than folded into one rate.

| tool | exact | over_fan | partial | polluted | ancestor | wrong | unknown | unplaced | missed | n | exact rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | 273 | 0 | 0 | 2 | 0 | 0 | 15 | 0 | 8 | 298 | 91.6% |
| `cha-null` | 298 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 298 | 100.0% |
| `code-review-graph` | 231 | 0 | 0 | 0 | 0 | 6 | 12 | 0 | 49 | 298 | 77.5% |
| `code-review-graph-dispatch` | 230 | 0 | 0 | 3 | 0 | 7 | 9 | 0 | 49 | 298 | 77.2% |
| `codegraph` | 197 | 0 | 0 | 0 | 0 | 12 | 23 | 4 | 62 | 298 | 66.1% |
| `codegraph-dispatch` | 197 | 0 | 0 | 0 | 0 | 12 | 23 | 4 | 62 | 298 | 66.1% |
| `codeql` | 250 | 0 | 0 | 3 | 0 | 1 | 0 | 0 | 44 | 298 | 83.9% |
| `gitnexus` | 190 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 106 | 298 | 63.8% |
| `graphify` | 193 | 0 | 0 | 0 | 0 | 9 | 0 | 1 | 95 | 298 | 64.8% |
| `ideal` | 298 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 298 | 100.0% |

`exact` the one right method, alone · `over_fan` right method plus others, all sound ·
`polluted` right method plus something no envelope admits · `ancestor` named only a supertype
that declares the member (weaker, not fabricated) · `wrong` answered, none of it defensible ·
`missed` returned nothing.

## Genuinely ambiguous call resolution

The other 5 groups, where dispatch really does admit several
targets. Here `over_fan` is the *correct* behaviour and `exact` may mean the tool guessed one
branch and dropped the rest — so this table is read differently from the one above, and that
is exactly why they are not combined.

3 of these groups (6 call sites) are not dispatch either: several one-target
calls of the same name in one method — `new A()` and `new B()`, `getProject()` on two receivers —
pooled under one key (#70). Each call has exactly one target; a tool that names some of them
but not all reads `partial` here, all of them `exact`.

| tool | exact | over_fan | partial | polluted | ancestor | wrong | unknown | unplaced | missed | n | exact rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | 1 | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 5 | 20.0% |
| `cha-null` | 3 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 60.0% |
| `code-review-graph` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 5 | 40.0% |
| `code-review-graph-dispatch` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 5 | 40.0% |
| `codegraph` | 2 | 0 | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 5 | 40.0% |
| `codegraph-dispatch` | 2 | 0 | 1 | 0 | 0 | 2 | 0 | 0 | 0 | 5 | 40.0% |
| `codeql` | 1 | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 5 | 20.0% |
| `gitnexus` | 4 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 80.0% |
| `graphify` | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 5 | 40.0% |
| `ideal` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 | 100.0% |

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
| `axiom` | source only | 0.922 | 0.962 | 0.953 | 0.96× | 0.938 | 0.919 | 0.926 | 1.02× | 0.931 | 0.865 | 0.884 | 1.08× |
| `code-review-graph` | source only | 0.761 | 0.708 | 0.702 | 1.08× | 0.657 | 0.657 | 0.650 | 1.00× | 0.580 | 0.631 | 0.626 | 0.92× |
| `code-review-graph-dispatch` | source only | 0.768 | 0.671 | 0.666 | 1.14× | 0.666 | 0.587 | 0.581 | 1.14× | 0.590 | 0.543 | 0.539 | 1.09× |
| `codegraph` | source only | 0.660 | 0.689 | 0.689 | 0.96× | 0.649 | 0.598 | 0.598 | 1.09× | 0.648 | 0.531 | 0.532 | 1.22× |
| `codegraph-dispatch` | source only | 0.660 | 0.680 | 0.680 | 0.97× | 0.649 | 0.575 | 0.575 | 1.13× | 0.648 | 0.495 | 0.496 | 1.31× |
| `codeql` | source only | 0.850 | 0.867 | 0.861 | 0.98× | 0.799 | 0.789 | 0.799 | 1.01× | 0.792 | 0.719 | 0.739 | 1.10× |
| `gitnexus` | source only | 0.650 | 0.980 | 0.966 | 0.66× | 0.579 | 0.969 | 0.951 | 0.60× | 0.496 | 0.945 | 0.928 | 0.52× |
| `graphify` | source only | 0.647 | 0.802 | 0.795 | 0.81× | 0.568 | 0.747 | 0.741 | 0.76× | 0.508 | 0.709 | 0.704 | 0.72× |
| *`cha-null`* | bytecode | 0.980 | 0.974 | 1.000 | 1.01× | 0.986 | 0.968 | 1.000 | 1.02× | 0.985 | 0.954 | 1.000 | 1.03× |
| *`ideal`* | oracle | 1.000 | 1.000 | 0.981 | 1.00× | 1.000 | 1.000 | 0.986 | 1.00× | 1.000 | 1.000 | 0.985 | 1.00× |

## Tier A (`type#name(params)`) — overload selection

Only tools whose output carries parameter types can be scored here. A dash is **not** a zero:
it means the tool's output format does not express the distinction, so the question was never
put to it.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 3s | 0.631 | 0.637 | 0.627 | 0.606 | 0.585 | 0.632 | 0.632 | 303 | 14 (6 ambig, 4 out-of-scope, 1% of emitted, 0 unspellable, 4 §4-excluded), 56 duplicate |
| `code-review-graph` | source only | 2s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `code-review-graph-dispatch` | source only | 2s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `codegraph` | source only | 1s | 0.599 | 0.599 | 0.529 | 0.526 | 0.498 | 0.562 | 0.563 | 272 | 64 (1 ambig, 34 out-of-scope, 8% of emitted, 22 unspellable, 7 §4-excluded), 85 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.591 | 0.591 | 0.529 | 0.526 | 0.498 | 0.558 | 0.559 | 276 | 64 (1 ambig, 34 out-of-scope, 8% of emitted, 22 unspellable, 7 §4-excluded), 85 duplicate |
| `codeql` | source only | 17s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `gitnexus` | source only | 19s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `graphify` | source only | 2s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| *`cha-null`* | bytecode | 0s | 1.000 | 0.974 | 0.981 | 1.000 | 1.000 | 0.977 | 0.977 | 310 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 0.974 | 1.000 | 1.000 | 1.000 | 308 | 0 |

## Tier C (`name`) — the floor

Method name only, no owner. Reported so that a name-only tool has a number at all. Read it
knowing that any two same-named methods in the subject are indistinguishable here, which
inflates every tool's score — the link-group table is **not** reported at this tier, because
its key is the callee name and every tool would score 100% by construction.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 3s | 0.977 | 0.977 | 0.949 | 0.949 | 0.934 | 0.963 | 0.963 | 265 | 14 (6 ambig, 4 out-of-scope, 1% of emitted, 0 unspellable, 4 §4-excluded), 56 duplicate |
| `code-review-graph` | source only | 2s | 0.576 | 0.576 | 0.864 | 0.864 | 0.843 | 0.691 | 0.705 | 410 | 465 (6 ambig, 374 out-of-scope, 36% of emitted, 0 unspellable, 85 §4-excluded), 260 duplicate |
| `code-review-graph-dispatch` | source only | 2s | 0.576 | 0.576 | 0.864 | 0.864 | 0.843 | 0.691 | 0.705 | 410 | 465 (6 ambig, 374 out-of-scope, 35% of emitted, 0 unspellable, 85 §4-excluded), 262 duplicate |
| `codegraph` | source only | 1s | 0.739 | 0.739 | 0.725 | 0.725 | 0.697 | 0.732 | 0.732 | 268 | 42 (1 ambig, 34 out-of-scope, 8% of emitted, 0 unspellable, 7 §4-excluded), 85 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.739 | 0.739 | 0.725 | 0.725 | 0.697 | 0.732 | 0.732 | 268 | 42 (1 ambig, 34 out-of-scope, 8% of emitted, 0 unspellable, 7 §4-excluded), 85 duplicate |
| `codeql` | source only | 17s | 0.862 | 0.862 | 0.890 | 0.890 | 0.869 | 0.876 | 0.876 | 282 | 176 (0 ambig, 3 out-of-scope, 0% of emitted, 0 unspellable, 173 §4-excluded), 194 duplicate |
| `gitnexus` | source only | 19s | 0.989 | 0.989 | 0.659 | 0.659 | 0.636 | 0.791 | 0.807 | 182 | 25 (1 ambig, 9 out-of-scope, 3% of emitted, 0 unspellable, 15 §4-excluded), 41 duplicate |
| `graphify` | source only | 2s | 0.841 | 0.841 | 0.696 | 0.696 | 0.773 | 0.762 | 0.765 | 226 | 39 (1 ambig, 35 out-of-scope, 12% of emitted, 0 unspellable, 3 §4-excluded) |
| *`cha-null`* | bytecode | 0s | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 273 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 273 | 0 |

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
| `axiom` | `known_edge` | 358 | 0.968 | 0.969 | 272 | 0 | 0 | 0 | 0 |
| `axiom` | `multi_inferred` | 15 | 0.778 | 0.500 | 1 | 0 | 2 | 0 | 0 |
| `code-review-graph` | `extracted` | 1,041 | 0.667 | 0.670 | 231 | 0 | 0 | 0 | 6 |
| `code-review-graph-dispatch` | `ambiguous_targets` | 26 | 0.125 | 0.125 | 0 | 0 | 3 | 0 | 1 |
| `code-review-graph-dispatch` | `extracted` | 1,030 | 0.667 | 0.670 | 230 | 0 | 0 | 0 | 6 |
| `codegraph` | `calls|exact-match` | 279 | 0.636 | 0.636 | 131 | 0 | 0 | 0 | 9 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.40` | 110 | 0.541 | 0.541 | 46 | 0 | 0 | 0 | 3 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.70` | 10 | 0.444 | 0.444 | 4 | 0 | 0 | 0 | 3 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.90` | 159 | 0.723 | 0.723 | 81 | 0 | 0 | 0 | 3 |
| `codegraph` | `calls|import` | 52 | 1.000 | 1.000 | 39 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|import:0.90` | 52 | 1.000 | 1.000 | 39 | 0 | 0 | 0 | 0 |
| `codegraph` | `calls|instance-method` | 47 | 0.414 | 0.414 | 12 | 0 | 0 | 0 | 3 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.65` | 4 | 0.000 | 0.000 | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.70` | 24 | 0.176 | 0.176 | 3 | 0 | 0 | 0 | 3 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.80` | 3 | 0.500 | 0.500 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.90` | 16 | 1.000 | 1.000 | 8 | 0 | 0 | 0 | 0 |
| `codegraph` | `instantiates|exact-match` | 11 | 1.000 | 1.000 | 8 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.40` | 8 | 1.000 | 1.000 | 7 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.90` | 3 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
| `codegraph` | `instantiates|fuzzy` | 3 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|fuzzy:0.50` | 3 | — | — | 0 | 0 | 0 | 0 | 0 |
| `codegraph` | `instantiates|import` | 16 | 1.000 | 1.000 | 7 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|import:0.90` | 16 | 1.000 | 1.000 | 7 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|exact-match` | 279 | 0.636 | 0.636 | 131 | 0 | 0 | 0 | 9 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.40` | 110 | 0.541 | 0.541 | 46 | 0 | 0 | 0 | 3 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.70` | 10 | 0.444 | 0.444 | 4 | 0 | 0 | 0 | 3 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.90` | 159 | 0.723 | 0.723 | 81 | 0 | 0 | 0 | 3 |
| `codegraph-dispatch` | `calls|import` | 52 | 1.000 | 1.000 | 39 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|import:0.90` | 52 | 1.000 | 1.000 | 39 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|instance-method` | 47 | 0.414 | 0.414 | 12 | 0 | 0 | 0 | 3 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.65` | 4 | 0.000 | 0.000 | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.70` | 24 | 0.176 | 0.176 | 3 | 0 | 0 | 0 | 3 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.80` | 3 | 0.500 | 0.500 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.90` | 16 | 1.000 | 1.000 | 8 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `instantiates|exact-match` | 11 | 1.000 | 1.000 | 8 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.40` | 8 | 1.000 | 1.000 | 7 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.90` | 3 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `instantiates|fuzzy` | 3 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|fuzzy:0.50` | 3 | — | — | 0 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `instantiates|import` | 16 | 1.000 | 1.000 | 7 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|import:0.90` | 16 | 1.000 | 1.000 | 7 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `interface-impl` | 4 | 0.000 | 0.000 | 0 | 0 | 0 | 0 | 0 |
| `codeql` | `imprecision=0` | 622 | 0.791 | 0.785 | 250 | 0 | 3 | 0 | 1 |
| `gitnexus` | `callable-value-flow` | 3 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `callable-value-flow:0.80` | 3 | — | — | 0 | 0 | 0 | 0 | 0 |
| `gitnexus` | `global` | 116 | 1.000 | 1.000 | 88 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `global:0.85` | 116 | 1.000 | 1.000 | 88 | 0 | 0 | 0 | 0 |
| `gitnexus` | `import-resolved` | 109 | 0.987 | 0.988 | 74 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `import-resolved:0.85` | 109 | 0.987 | 0.988 | 74 | 0 | 0 | 0 | 0 |
| `gitnexus` | `interface-dispatch` | 5 | 0.000 | 0.000 | 0 | 0 | 2 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `interface-dispatch:0.85` | 5 | 0.000 | 0.000 | 0 | 0 | 2 | 0 | 0 |
| `gitnexus` | `local-call` | 36 | 0.966 | 0.966 | 28 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `local-call:0.85` | 36 | 0.966 | 0.966 | 28 | 0 | 0 | 0 | 0 |
| `graphify` | `extracted` | 266 | 0.795 | 0.795 | 177 | 0 | 0 | 0 | 8 |
| `graphify` | `inferred` | 20 | 0.875 | 0.889 | 16 | 0 | 0 | 0 | 1 |

- `axiom` wrote 800 rows labelled `ambiguous_unknown` with no target — the tool says it could not resolve the call (read as `unknown`, not `missed`, #69), not scored

## Provenance

```json
{
  "input_sha256": {
    "classes": "d8c9efc01911af76646f5bc0408ad2bd6876f4f43e3bca29f946191029227f83",
    "edges/axiom": "7970aec79fffd0e84bea8f5fd73be0e2797c77287b01da9d6ab01807bbd37589",
    "edges/cha-null": "b5c2fb7444a7fec0e8c3506ecd4d7e3467e86bbb57402e156bef6019cd10dddb",
    "edges/code-review-graph": "98a23af48911d2e31920bebcfdf687a1e5d8d4b9e0d9965a49441dc4af584859",
    "edges/code-review-graph-dispatch": "a709e5cff14b9a9df78b4a61c48ad72517b71df49a214f1302c582decc41f7b9",
    "edges/codegraph": "a006eedd35c0f37b1bf8dd19899fabfdeb5d9b9cecd1f5007c0e89597ab3106d",
    "edges/codegraph-dispatch": "d754673c05911e4f41ef1240a6b85379cc873bf8888102784290924ee4a37473",
    "edges/codeql": "fc9afc64545ad1ce7e52fafd6903c8bd8e91472ae0de2a0d88e0f0152e5163d3",
    "edges/gitnexus": "4fcb0097b7ef19166ef4b95b07690c9deec44303ad975d371eb2a7bf49b38214",
    "edges/graphify": "af949f72965f56097df452bad2fcc7f52ff701bd5ef0596352d028f4680967c7",
    "edges/ideal": "353f6c3e6fe14f0d715e43097336b82ee339aea4f67ae69b3a60bd895973dfc9",
    "excluded": "f3f9f0728a5a145beb26a50a9a234a7c32fb35f936bd6346c888314c3bc4aa0b",
    "heritage": "a5c53df325d0b9607e3249ee5eccdf344c61821b6e8b2bf7332f425504223c3d",
    "methods": "6d8422f64ec8e6f6acdc7a04f0ec1ec6d7b7985edc3cc8415a18ffc8b3b7bddd",
    "sites": "31208d96536ce619be0cab073adac1811725a67b813da808c8e560f98f694fdc"
  },
  "language": "typescript",
  "platform": "Linux x86_64",
  "python": "3.12.3",
  "staged_copy": {
    "files": 37,
    "sha256": "26f49667147c593dc634df1f5906b46d2476643da397fff25452c7bf0ab4a1b4"
  },
  "subject": "ioredis",
  "tools": {
    "axiom": {
      "build": "source only",
      "cache": "hit",
      "cold_seconds": 0.86,
      "engine_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "function_type_targets_dropped": 35,
      "note": "typescript front end, empty library",
      "parser_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "rows": 373,
      "rows_by_status": {
        "ambiguous_unknown": 800,
        "known_edge": 393,
        "multi_inferred": 15
      },
      "rows_without_method": 800,
      "seconds_breakdown": {
        "adapter_total": 3.35,
        "own": 1.39,
        "shared": 1.62,
        "staging": null
      },
      "source": ".work/typescript/ioredis/axiom/out/raw/call-chain-edges.csv",
      "unresolved_sites": [
        [
          {
            "name": "_iterateKeys",
            "params": [
              "(key: CommandParameter) => CommandParameter"
            ],
            "type": "Command#Command"
          },
          355,
          "Command.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "Command"
          },
          420,
          "Command.ts"
        ],
        [
          {
            "name": "autoPipelineQueueSize",
            "params": [],
            "type": "Redis#Redis"
          },
          160,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "params": [
              "unknown[]"
            ],
            "type": "Redis#Redis"
          },
          724,
          "Redis.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "params": [
              "",
              "string"
            ],
            "type": "autoPipelining"
          },
          28,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "autoPipelining"
          },
          73,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "autoPipelineQueueSize",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          402,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "params": [
              "boolean",
              "string"
            ],
            "type": "cluster/index#Cluster"
          },
          564,
          "cluster/index.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "params": [
              "SrvRecordsGroup"
            ],
            "type": "cluster/util"
          },
          111,
          "cluster/util.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "redis/event_handler"
          },
          90,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "transaction"
          },
          18,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "transaction"
          },
          36,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "any[] | null"
            ],
            "type": "transaction"
          },
          108,
          "transaction.ts"
        ],
        [
          {
            "name": "getStringValue",
            "params": [
              "any"
            ],
            "type": "utils/debug"
          },
          22,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "params": [
              "any"
            ],
            "type": "utils/debug"
          },
          25,
          "utils/debug.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "params": [
              "any",
              "BufferEncoding"
            ],
            "type": "utils/index"
          },
          22,
          "utils/index.ts"
        ],
        [
          {
            "name": "getFlagMap",
            "params": [],
            "type": "Command#Command"
          },
          129,
          "Command.ts"
        ],
        [
          {
            "name": "getFlagMap",
            "params": [],
            "type": "Command#Command"
          },
          129,
          "Command.ts"
        ],
        [
          {
            "name": "getFlagMap",
            "params": [
              "FlagMap",
              "string"
            ],
            "type": "Command#Command"
          },
          132,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "Array<ArgumentType>",
              "CommandOptions",
              "Callback"
            ],
            "type": "Command#Command"
          },
          182,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "Command#Command"
          },
          197,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "Command#Command"
          },
          199,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "Command#Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "Command#Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "Command#Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "getSlot",
            "params": [],
            "type": "Command#Command"
          },
          216,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "params": [
              "object"
            ],
            "type": "Command#Command"
          },
          234,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "params": [
              "object"
            ],
            "type": "Command#Command"
          },
          255,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "params": [
              "object"
            ],
            "type": "Command#Command"
          },
          269,
          "Command.ts"
        ],
        [
          {
            "name": "transformReply",
            "params": [
              "Buffer | Buffer[]"
            ],
            "type": "Command#Command"
          },
          303,
          "Command.ts"
        ],
        [
          {
            "name": "setTimeout",
            "params": [
              "number"
            ],
            "type": "Command#Command"
          },
          315,
          "Command.ts"
        ],
        [
          {
            "name": "setTimeout",
            "params": [],
            "type": "Command#Command"
          },
          317,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "params": [],
            "type": "Command#Command"
          },
          324,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "params": [
              "",
              ""
            ],
            "type": "Command#Command"
          },
          329,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "params": [
              ""
            ],
            "type": "Command#Command"
          },
          337,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "params": [],
            "type": "Command#Command"
          },
          344,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "params": [
              "(key: CommandParameter) => CommandParameter"
            ],
            "type": "Command#Command"
          },
          357,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "params": [
              "(key: CommandParameter) => CommandParameter"
            ],
            "type": "Command#Command"
          },
          360,
          "Command.ts"
        ],
        [
          {
            "name": "_convertValue",
            "params": [
              ""
            ],
            "type": "Command#Command"
          },
          375,
          "Command.ts"
        ],
        [
          {
            "name": "_convertValue",
            "params": [
              ""
            ],
            "type": "Command#Command"
          },
          379,
          "Command.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "Command"
          },
          404,
          "Command.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "Command"
          },
          407,
          "Command.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "Command"
          },
          413,
          "Command.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "Command"
          },
          414,
          "Command.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "Command"
          },
          416,
          "Command.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "Command"
          },
          417,
          "Command.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "Command"
          },
          419,
          "Command.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "Command"
          },
          428,
          "Command.ts"
        ],
        [
          {
            "name": "push",
            "params": [
              "string | Buffer"
            ],
            "type": "Command#MixedBuffers"
          },
          448,
          "Command.ts"
        ],
        [
          {
            "name": "push",
            "params": [
              "string | Buffer"
            ],
            "type": "Command#MixedBuffers"
          },
          449,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "params": [],
            "type": "Command#MixedBuffers"
          },
          453,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "params": [],
            "type": "Command#MixedBuffers"
          },
          456,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "params": [],
            "type": "Command#MixedBuffers"
          },
          457,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "params": [],
            "type": "Command#MixedBuffers"
          },
          458,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "params": [],
            "type": "Command#MixedBuffers"
          },
          459,
          "Command.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "DataHandler"
          },
          9,
          "DataHandler.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "DataHandledable",
              "ParserOptions"
            ],
            "type": "DataHandler#DataHandler"
          },
          45,
          "DataHandler.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "DataHandledable",
              "ParserOptions"
            ],
            "type": "DataHandler#DataHandler"
          },
          59,
          "DataHandler.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "DataHandler#DataHandler"
          },
          60,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          99,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          103,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          107,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          118,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          118,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          119,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          123,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          125,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          127,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          128,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          131,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          134,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          135,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          136,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          139,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          140,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          143,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          147,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          148,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          150,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          151,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          154,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          160,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          167,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          174,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          179,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          187,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          207,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          219,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          220,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          221,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "args",
            "params": [
              ""
            ],
            "type": "DataHandler#DataHandler"
          },
          225,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          226,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          226,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "params": [
              "ReplyData"
            ],
            "type": "DataHandler#DataHandler"
          },
          227,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "params": [
              "ReplyData | Error"
            ],
            "type": "DataHandler#DataHandler"
          },
          232,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "params": [
              "ReplyData | Error"
            ],
            "type": "DataHandler#DataHandler"
          },
          236,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "params": [
              "ReplyData | Error"
            ],
            "type": "DataHandler#DataHandler"
          },
          240,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "params": [
              "ReplyData | Error"
            ],
            "type": "DataHandler#DataHandler"
          },
          242,
          "DataHandler.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "DataHandler"
          },
          249,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "params": [
              "Respondable",
              "number"
            ],
            "type": "DataHandler"
          },
          252,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "params": [
              "Respondable",
              "number"
            ],
            "type": "DataHandler"
          },
          253,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "params": [
              "Respondable",
              "number"
            ],
            "type": "DataHandler"
          },
          260,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "params": [
              "Respondable",
              "number"
            ],
            "type": "DataHandler"
          },
          263,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "params": [
              "Respondable",
              "number"
            ],
            "type": "DataHandler"
          },
          268,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "params": [
              "Respondable",
              "number"
            ],
            "type": "DataHandler"
          },
          269,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "params": [
              "Respondable",
              "number"
            ],
            "type": "DataHandler"
          },
          273,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "params": [
              "Respondable",
              "number"
            ],
            "type": "DataHandler"
          },
          274,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "params": [
              "Respondable",
              "number"
            ],
            "type": "DataHandler"
          },
          286,
          "DataHandler.ts"
        ],
        [
          {
            "name": "generateMultiWithNodes",
            "params": [
              "",
              ""
            ],
            "type": "Pipeline"
          },
          18,
          "Pipeline.ts"
        ],
        [
          {
            "name": "generateMultiWithNodes",
            "params": [
              "",
              ""
            ],
            "type": "Pipeline"
          },
          22,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "Redis | Cluster"
            ],
            "type": "Pipeline#Pipeline"
          },
          52,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "Redis | Cluster"
            ],
            "type": "Pipeline#Pipeline"
          },
          52,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "Redis | Cluster"
            ],
            "type": "Pipeline#Pipeline"
          },
          59,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "Redis | Cluster"
            ],
            "type": "Pipeline#Pipeline"
          },
          64,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "Redis | Cluster"
            ],
            "type": "Pipeline#Pipeline"
          },
          70,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "params": [
              "unknown[]",
              "number"
            ],
            "type": "Pipeline#Pipeline"
          },
          78,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "params": [
              "unknown[]",
              "number"
            ],
            "type": "Pipeline#Pipeline"
          },
          86,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "params": [
              "unknown[]",
              "number"
            ],
            "type": "Pipeline#Pipeline"
          },
          126,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "params": [
              "unknown[]",
              "number"
            ],
            "type": "Pipeline#Pipeline"
          },
          126,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "params": [
              "unknown[]",
              "number"
            ],
            "type": "Pipeline#Pipeline"
          },
          135,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "params": [
              "unknown[]",
              "number"
            ],
            "type": "Pipeline#Pipeline"
          },
          150,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "string",
              "string"
            ],
            "type": "Pipeline#Pipeline"
          },
          168,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "params": [
              "unknown[]",
              "number"
            ],
            "type": "Pipeline#Pipeline"
          },
          199,
          "Pipeline.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command"
            ],
            "type": "Pipeline#Pipeline"
          },
          210,
          "Pipeline.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command"
            ],
            "type": "Pipeline#Pipeline"
          },
          210,
          "Pipeline.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command"
            ],
            "type": "Pipeline#Pipeline"
          },
          218,
          "Pipeline.ts"
        ],
        [
          {
            "name": "addBatch",
            "params": [
              ""
            ],
            "type": "Pipeline#Pipeline"
          },
          228,
          "Pipeline.ts"
        ],
        [
          {
            "name": "addBatch",
            "params": [
              ""
            ],
            "type": "Pipeline#Pipeline"
          },
          229,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Pipeline"
          },
          243,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "Pipeline"
          },
          249,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Pipeline"
          },
          253,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          265,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          265,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          269,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          272,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "Pipeline"
          },
          274,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "Pipeline"
          },
          278,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          286,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          290,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          293,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          300,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          302,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          306,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          307,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          308,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          321,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          322,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "Pipeline"
          },
          330,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "params": [
              ""
            ],
            "type": "Pipeline#stream"
          },
          362,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "params": [
              ""
            ],
            "type": "Pipeline#stream"
          },
          362,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "params": [
              ""
            ],
            "type": "Pipeline#stream"
          },
          366,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "params": [
              ""
            ],
            "type": "Pipeline#stream"
          },
          374,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "params": [
              ""
            ],
            "type": "Pipeline#stream"
          },
          374,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "params": [
              ""
            ],
            "type": "Pipeline#stream"
          },
          376,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "params": [
              ""
            ],
            "type": "Pipeline#stream"
          },
          376,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "params": [
              ""
            ],
            "type": "Pipeline#stream"
          },
          378,
          "Pipeline.ts"
        ],
        [
          {
            "name": "execPipeline",
            "params": [],
            "type": "Pipeline"
          },
          390,
          "Pipeline.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "Redis"
          },
          36,
          "Redis.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "Redis"
          },
          112,
          "Redis.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "Redis"
          },
          113,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "unknown",
              "unknown",
              "unknown"
            ],
            "type": "Redis#Redis"
          },
          127,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "unknown",
              "unknown",
              "unknown"
            ],
            "type": "Redis#Redis"
          },
          140,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "unknown",
              "unknown",
              "unknown"
            ],
            "type": "Redis#Redis"
          },
          144,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "unknown",
              "unknown",
              "unknown"
            ],
            "type": "Redis#Redis"
          },
          144,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "unknown",
              "unknown",
              "unknown"
            ],
            "type": "Redis#Redis"
          },
          153,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "Callback<void>"
            ],
            "type": "Redis#Redis"
          },
          176,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "",
              ""
            ],
            "type": "Redis#Redis"
          },
          182,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "",
              ""
            ],
            "type": "Redis#Redis"
          },
          182,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "",
              ""
            ],
            "type": "Redis#Redis"
          },
          200,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          208,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          224,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          231,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          232,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          235,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          240,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          251,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          255,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          256,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          258,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          265,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          267,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          269,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          275,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          276,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          279,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          281,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          284,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "NetStream"
            ],
            "type": "Redis#Redis"
          },
          285,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          289,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          290,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          293,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          294,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          294,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "Callback<void>"
            ],
            "type": "Redis#Redis"
          },
          302,
          "Redis.ts"
        ],
        [
          {
            "name": "disconnect",
            "params": [
              ""
            ],
            "type": "Redis#Redis"
          },
          317,
          "Redis.ts"
        ],
        [
          {
            "name": "disconnect",
            "params": [
              ""
            ],
            "type": "Redis#Redis"
          },
          321,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "params": [
              "Callback<Redis>"
            ],
            "type": "Redis#Redis"
          },
          395,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "params": [
              "Callback<Redis>"
            ],
            "type": "Redis#Redis"
          },
          396,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "Redis#Redis"
          },
          399,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          425,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          428,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          436,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          452,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          451,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          467,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          476,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          482,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          491,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          499,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          515,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          518,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          534,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          537,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream"
            ],
            "type": "Redis#Redis"
          },
          538,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "params": [],
            "type": "Redis#Redis"
          },
          546,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "params": [],
            "type": "Redis#Redis"
          },
          547,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "params": [],
            "type": "Redis#Redis"
          },
          547,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "params": [],
            "type": "Redis#Redis"
          },
          553,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "params": [],
            "type": "Redis#Redis"
          },
          554,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "params": [
              "string",
              "unknown"
            ],
            "type": "Redis#Redis"
          },
          621,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "params": [
              "string",
              "unknown"
            ],
            "type": "Redis#Redis"
          },
          622,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "params": [
              "string",
              "unknown"
            ],
            "type": "Redis#Redis"
          },
          625,
          "Redis.ts"
        ],
        [
          {
            "name": "resetCommandQueue",
            "params": [],
            "type": "Redis#Redis"
          },
          705,
          "Redis.ts"
        ],
        [
          {
            "name": "resetOfflineQueue",
            "params": [],
            "type": "Redis#Redis"
          },
          709,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "params": [
              "unknown[]"
            ],
            "type": "Redis#Redis"
          },
          721,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "params": [
              "unknown[]"
            ],
            "type": "Redis#Redis"
          },
          723,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "params": [
              "unknown[]"
            ],
            "type": "Redis#Redis"
          },
          730,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "params": [
              "unknown[]"
            ],
            "type": "Redis#Redis"
          },
          734,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "params": [
              "unknown[]"
            ],
            "type": "Redis#Redis"
          },
          736,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "params": [
              "unknown[]"
            ],
            "type": "Redis#Redis"
          },
          739,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "params": [
              "unknown[]"
            ],
            "type": "Redis#Redis"
          },
          742,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "params": [
              "RedisStatus",
              "unknown"
            ],
            "type": "Redis#Redis"
          },
          755,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "params": [
              "RedisStatus",
              "unknown"
            ],
            "type": "Redis#Redis"
          },
          763,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "params": [
              "RedisStatus",
              "unknown"
            ],
            "type": "Redis#Redis"
          },
          763,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "params": [
              "Error",
              "FlushQueueOptions"
            ],
            "type": "Redis#Redis"
          },
          786,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "params": [
              "Error",
              "FlushQueueOptions"
            ],
            "type": "Redis#Redis"
          },
          793,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "params": [
              "Error",
              "FlushQueueOptions"
            ],
            "type": "Redis#Redis"
          },
          794,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "params": [
              "Error",
              "FlushQueueOptions"
            ],
            "type": "Redis#Redis"
          },
          801,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "params": [
              "Error",
              "FlushQueueOptions"
            ],
            "type": "Redis#Redis"
          },
          804,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "params": [
              "Error",
              "FlushQueueOptions"
            ],
            "type": "Redis#Redis"
          },
          805,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "params": [
              "Callback"
            ],
            "type": "Redis#Redis"
          },
          817,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "Redis#Redis"
          },
          819,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "Redis#Redis"
          },
          820,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "Redis#Redis"
          },
          833,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "Redis#Redis"
          },
          835,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "Redis#Redis"
          },
          836,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "Redis#Redis"
          },
          851,
          "Redis.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "Redis#Redis"
          },
          854,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "Options"
            ],
            "type": "ScanStream#ScanStream"
          },
          20,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "params": [],
            "type": "ScanStream#ScanStream"
          },
          25,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "params": [],
            "type": "ScanStream#ScanStream"
          },
          31,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "params": [],
            "type": "ScanStream#ScanStream"
          },
          34,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "params": [],
            "type": "ScanStream#ScanStream"
          },
          37,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "params": [],
            "type": "ScanStream#ScanStream"
          },
          40,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "params": [],
            "type": "ScanStream#ScanStream"
          },
          40,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "params": [],
            "type": "ScanStream#ScanStream"
          },
          43,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "params": [
              "",
              ""
            ],
            "type": "ScanStream#ScanStream"
          },
          45,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "params": [
              "",
              ""
            ],
            "type": "ScanStream#ScanStream"
          },
          48,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "params": [
              "",
              ""
            ],
            "type": "ScanStream#ScanStream"
          },
          52,
          "ScanStream.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "number | null",
              "string",
              "boolean"
            ],
            "type": "Script#Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "number | null",
              "string",
              "boolean"
            ],
            "type": "Script#Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "number | null",
              "string",
              "boolean"
            ],
            "type": "Script#Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "number | null",
              "string",
              "boolean"
            ],
            "type": "Script#Script"
          },
          18,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "params": [
              ""
            ],
            "type": "Script#Script.CustomScriptCommand"
          },
          23,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "params": [
              ""
            ],
            "type": "Script#Script.CustomScriptCommand"
          },
          24,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "params": [
              ""
            ],
            "type": "Script#Script.CustomScriptCommand"
          },
          26,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "params": [
              "object"
            ],
            "type": "Script#Script.CustomScriptCommand"
          },
          29,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "params": [
              "object"
            ],
            "type": "Script#Script.CustomScriptCommand"
          },
          30,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "params": [
              "any",
              "any[]",
              "any",
              "Callback"
            ],
            "type": "Script#Script"
          },
          44,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "params": [
              "any",
              "any[]",
              "any",
              "Callback"
            ],
            "type": "Script#Script"
          },
          53,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "params": [
              "any",
              "any[]",
              "any",
              "Callback"
            ],
            "type": "Script#Script"
          },
          55,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "params": [
              "Error"
            ],
            "type": "Script#Script"
          },
          56,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "params": [
              "Error"
            ],
            "type": "Script#Script"
          },
          62,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "params": [
              "Error"
            ],
            "type": "Script#Script"
          },
          65,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "params": [
              "any",
              "any[]",
              "any",
              "Callback"
            ],
            "type": "Script#Script"
          },
          68,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "params": [
              "any",
              "any[]",
              "any",
              "Callback"
            ],
            "type": "Script#Script"
          },
          69,
          "Script.ts"
        ],
        [
          {
            "name": "channels",
            "params": [
              "AddSet | DelSet"
            ],
            "type": "SubscriptionSet#SubscriptionSet"
          },
          25,
          "SubscriptionSet.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "autoPipelining"
          },
          6,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "autoPipelining"
          },
          7,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "params": [
              "",
              "string"
            ],
            "type": "autoPipelining"
          },
          31,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "params": [
              "",
              "string"
            ],
            "type": "autoPipelining"
          },
          42,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "params": [
              "",
              "string"
            ],
            "type": "autoPipelining"
          },
          45,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "params": [
              "",
              "string"
            ],
            "type": "autoPipelining"
          },
          46,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "params": [
              "",
              "string"
            ],
            "type": "autoPipelining"
          },
          55,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "autoPipelining"
          },
          56,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "autoPipelining"
          },
          64,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "autoPipelining"
          },
          68,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "shouldUseAutoPipelining",
            "params": [
              "",
              "string",
              "string"
            ],
            "type": "autoPipelining"
          },
          89,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "shouldUseAutoPipelining",
            "params": [
              "",
              "string",
              "string"
            ],
            "type": "autoPipelining"
          },
          88,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "params": [
              "ArgumentType[]"
            ],
            "type": "autoPipelining"
          },
          100,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "params": [
              "ArgumentType[]"
            ],
            "type": "autoPipelining"
          },
          100,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "params": [
              "ArgumentType[]"
            ],
            "type": "autoPipelining"
          },
          106,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          123,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          123,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          124,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          125,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "autoPipelining"
          },
          126,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "autoPipelining"
          },
          128,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "autoPipelining"
          },
          132,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          150,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          151,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          155,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          156,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          159,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          162,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          175,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          179,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "autoPipelining"
          },
          180,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "any"
            ],
            "type": "autoPipelining"
          },
          182,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error | null",
              "any"
            ],
            "type": "autoPipelining"
          },
          186,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "autoPipelining"
          },
          190,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "autoPipelining"
          },
          193,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "params": [
              "",
              "string",
              "string",
              "ArgumentType[]",
              ""
            ],
            "type": "autoPipelining"
          },
          196,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "cluster/ClusterOptions"
          },
          202,
          "cluster/ClusterOptions.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "cluster/ClusterSubscriber"
          },
          7,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ConnectionPool",
              "EventEmitter"
            ],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          26,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "",
              "string"
            ],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          31,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ConnectionPool",
              "EventEmitter"
            ],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          35,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          39,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "start",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          53,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "stop",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          59,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "stop",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          62,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "onSubscriberEnd",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          67,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "onSubscriberEnd",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          75,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          85,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          86,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          90,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          91,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          96,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          104,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          131,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          138,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          146,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          148,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          150,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          163,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          172,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          185,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [
              "",
              ""
            ],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          186,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          190,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "params": [
              "",
              "",
              ""
            ],
            "type": "cluster/ClusterSubscriber#ClusterSubscriber"
          },
          191,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "cluster/ConnectionPool"
          },
          6,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          21,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getNodes",
            "params": [
              "NodeRole"
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          26,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getNodes",
            "params": [
              "NodeRole"
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          26,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getSampleInstance",
            "params": [
              "NodeRole"
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          34,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "params": [
              "RedisOptions",
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          44,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "params": [
              "RedisOptions",
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          47,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "params": [
              "RedisOptions",
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          57,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "params": [
              "RedisOptions",
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          58,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "params": [
              "RedisOptions",
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          58,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "params": [
              "RedisOptions",
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          68,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "params": [
              "RedisOptions",
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          70,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "params": [],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          92,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "params": [],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          93,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "params": [],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          94,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "params": [
              "RedisOptions",
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          98,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          101,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "params": [
              "RedisOptions[]"
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          113,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "params": [
              "RedisOptions[]"
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          115,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "params": [
              "RedisOptions[]"
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          125,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "params": [
              "RedisOptions[]"
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          125,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "params": [
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          127,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "params": [
              ""
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          128,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "params": [
              "RedisOptions[]"
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          132,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "params": [
              "RedisOptions[]"
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          132,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "removeNode",
            "params": [
              "string"
            ],
            "type": "cluster/ConnectionPool#ConnectionPool"
          },
          144,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "cluster/DelayQueue"
          },
          4,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "push",
            "params": [
              "string",
              "Function",
              "DelayQueueOptions"
            ],
            "type": "cluster/DelayQueue#DelayQueue"
          },
          28,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "push",
            "params": [
              "string",
              "Function",
              "DelayQueueOptions"
            ],
            "type": "cluster/DelayQueue#DelayQueue"
          },
          32,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "push",
            "params": [
              "string",
              "Function",
              "DelayQueueOptions"
            ],
            "type": "cluster/DelayQueue#DelayQueue"
          },
          35,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "push",
            "params": [],
            "type": "cluster/DelayQueue#DelayQueue"
          },
          36,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "execute",
            "params": [
              "string"
            ],
            "type": "cluster/DelayQueue#DelayQueue"
          },
          53,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "execute",
            "params": [
              "string"
            ],
            "type": "cluster/DelayQueue#DelayQueue"
          },
          57,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "execute",
            "params": [
              "string"
            ],
            "type": "cluster/DelayQueue#DelayQueue"
          },
          57,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "cluster/index"
          },
          41,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "cluster/index"
          },
          43,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "cluster/index"
          },
          85,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "cluster/index"
          },
          97,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "cluster/index"
          },
          103,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "cluster/index"
          },
          104,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClusterNode[]",
              "ClusterOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          120,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClusterNode[]",
              "ClusterOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          123,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClusterNode[]",
              "ClusterOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          136,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClusterNode[]",
              "ClusterOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          138,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClusterNode[]",
              "ClusterOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          147,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          148,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClusterNode[]",
              "ClusterOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          150,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          151,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClusterNode[]",
              "ClusterOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          153,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClusterNode[]",
              "ClusterOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          156,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          157,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClusterNode[]",
              "ClusterOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          163,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClusterNode[]",
              "ClusterOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          163,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClusterNode[]",
              "ClusterOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          171,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          172,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          181,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          187,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          187,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          194,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          194,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          197,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          202,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          203,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          210,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          214,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          214,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyHandler",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          224,
          "cluster/index.ts"
        ],
        [
          {
            "name": "refreshListener",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          230,
          "cluster/index.ts"
        ],
        [
          {
            "name": "refreshListener",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          236,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          253,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          255,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          257,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          260,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          261,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          262,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          262,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          266,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          276,
          "cluster/index.ts"
        ],
        [
          {
            "name": "disconnect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          292,
          "cluster/index.ts"
        ],
        [
          {
            "name": "disconnect",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          294,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "params": [
              "Callback<\"OK\">"
            ],
            "type": "cluster/index#Cluster"
          },
          317,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "params": [
              "Callback<\"OK\">"
            ],
            "type": "cluster/index#Cluster"
          },
          325,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "params": [
              "Callback<\"OK\">"
            ],
            "type": "cluster/index#Cluster"
          },
          325,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "params": [
              "Callback<\"OK\">"
            ],
            "type": "cluster/index#Cluster"
          },
          329,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "params": [
              "Callback<\"OK\">"
            ],
            "type": "cluster/index#Cluster"
          },
          330,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "params": [
              "Callback<\"OK\">"
            ],
            "type": "cluster/index#Cluster"
          },
          338,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "params": [
              "Callback<\"OK\">"
            ],
            "type": "cluster/index#Cluster"
          },
          339,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "params": [
              "Callback<\"OK\">"
            ],
            "type": "cluster/index#Cluster"
          },
          339,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "params": [
              "Callback<\"OK\">"
            ],
            "type": "cluster/index#Cluster"
          },
          340,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          341,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          341,
          "cluster/index.ts"
        ],
        [
          {
            "name": "duplicate",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          368,
          "cluster/index.ts"
        ],
        [
          {
            "name": "duplicate",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          369,
          "cluster/index.ts"
        ],
        [
          {
            "name": "nodes",
            "params": [
              "NodeRole"
            ],
            "type": "cluster/index#Cluster"
          },
          378,
          "cluster/index.ts"
        ],
        [
          {
            "name": "delayUntilReady",
            "params": [
              "Callback"
            ],
            "type": "cluster/index#Cluster"
          },
          391,
          "cluster/index.ts"
        ],
        [
          {
            "name": "refreshSlotsCache",
            "params": [
              "Callback<void>"
            ],
            "type": "cluster/index#Cluster"
          },
          416,
          "cluster/index.ts"
        ],
        [
          {
            "name": "wrapper",
            "params": [
              "Error"
            ],
            "type": "cluster/index#Cluster"
          },
          429,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "params": [
              "number"
            ],
            "type": "cluster/index#Cluster"
          },
          448,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          453,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          455,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          458,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          462,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream",
              "any"
            ],
            "type": "cluster/index#Cluster"
          },
          476,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream",
              "any"
            ],
            "type": "cluster/index#Cluster"
          },
          479,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream",
              "any"
            ],
            "type": "cluster/index#Cluster"
          },
          486,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream",
              "any"
            ],
            "type": "cluster/index#Cluster"
          },
          486,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream",
              "any"
            ],
            "type": "cluster/index#Cluster"
          },
          495,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream",
              "any"
            ],
            "type": "cluster/index#Cluster"
          },
          496,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          500,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          503,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          504,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          511,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          514,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          518,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          527,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          530,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "params": [
              "boolean",
              "string"
            ],
            "type": "cluster/index#Cluster"
          },
          539,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "params": [
              "boolean",
              "string"
            ],
            "type": "cluster/index#Cluster"
          },
          552,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "params": [
              "boolean",
              "string"
            ],
            "type": "cluster/index#Cluster"
          },
          560,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "params": [
              "boolean",
              "string"
            ],
            "type": "cluster/index#Cluster"
          },
          563,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "params": [
              "boolean",
              "string"
            ],
            "type": "cluster/index#Cluster"
          },
          602,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "params": [
              "boolean",
              "string"
            ],
            "type": "cluster/index#Cluster"
          },
          609,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "params": [
              "Error",
              "{ value?: any }",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          652,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "params": [
              "Error",
              "{ value?: any }",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          653,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "params": [
              "Error",
              "{ value?: any }",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          657,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "params": [
              "Error",
              "{ value?: any }",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          663,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "params": [
              "Error",
              "{ value?: any }",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          667,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "params": [
              "Error",
              "{ value?: any }",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          670,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "params": [
              "Error",
              "{ value?: any }",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          681,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "params": [
              "Error",
              "{ value?: any }",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          690,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "params": [
              "Error",
              "{ value?: any }",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          693,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resetOfflineQueue",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          698,
          "cluster/index.ts"
        ],
        [
          {
            "name": "clearNodesRefreshInterval",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          703,
          "cluster/index.ts"
        ],
        [
          {
            "name": "nextRound",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          713,
          "cluster/index.ts"
        ],
        [
          {
            "name": "nextRound",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          714,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "params": [
              "ClusterStatus"
            ],
            "type": "cluster/index#Cluster"
          },
          730,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "params": [
              "ClusterStatus"
            ],
            "type": "cluster/index#Cluster"
          },
          732,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          733,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "params": [
              "Error"
            ],
            "type": "cluster/index#Cluster"
          },
          742,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "params": [
              "Error"
            ],
            "type": "cluster/index#Cluster"
          },
          750,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "params": [
              "Error"
            ],
            "type": "cluster/index#Cluster"
          },
          758,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          760,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          761,
          "cluster/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          762,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "params": [
              "Error"
            ],
            "type": "cluster/index#Cluster"
          },
          767,
          "cluster/index.ts"
        ],
        [
          {
            "name": "flushQueue",
            "params": [
              "Error"
            ],
            "type": "cluster/index#Cluster"
          },
          776,
          "cluster/index.ts"
        ],
        [
          {
            "name": "executeOfflineCommands",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          783,
          "cluster/index.ts"
        ],
        [
          {
            "name": "executeOfflineCommands",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          787,
          "cluster/index.ts"
        ],
        [
          {
            "name": "natMapper",
            "params": [
              "NodeKey | RedisOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          801,
          "cluster/index.ts"
        ],
        [
          {
            "name": "natMapper",
            "params": [
              "NodeKey | RedisOptions"
            ],
            "type": "cluster/index#Cluster"
          },
          802,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "params": [
              "Redis",
              "Callback<void>"
            ],
            "type": "cluster/index#Cluster"
          },
          812,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "params": [
              "Error",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          844,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "params": [
              "Error",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          854,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "params": [
              "Error",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          871,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "params": [
              "Error",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          872,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "params": [
              "Error",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          875,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "params": [
              "Error",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          889,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "params": [
              "Error",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          892,
          "cluster/index.ts"
        ],
        [
          {
            "name": "invokeReadyDelayedCallbacks",
            "params": [
              "Error"
            ],
            "type": "cluster/index#Cluster"
          },
          914,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          933,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          935,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          943,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "params": [
              "string"
            ],
            "type": "cluster/index#Cluster"
          },
          952,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          955,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          960,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          960,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sortedKeys",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          961,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sortedKeys",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          961,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          966,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          974,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          977,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          979,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "params": [
              "string"
            ],
            "type": "cluster/index#Cluster"
          },
          993,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          996,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          1001,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          1003,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "params": [
              "",
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          1004,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          1017,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          1018,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          1027,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          1028,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          1029,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "params": [],
            "type": "cluster/index#Cluster"
          },
          1036,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          1037,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          1042,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "params": [
              ""
            ],
            "type": "cluster/index#Cluster"
          },
          1044,
          "cluster/index.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "params": [
              "NodeKey"
            ],
            "type": "cluster/util"
          },
          32,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "params": [
              "NodeKey"
            ],
            "type": "cluster/util"
          },
          34,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "params": [
              "NodeKey"
            ],
            "type": "cluster/util"
          },
          37,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "params": [
              "NodeKey"
            ],
            "type": "cluster/util"
          },
          38,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "params": [
              "NodeKey"
            ],
            "type": "cluster/util"
          },
          38,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "params": [
              "Array<string | number | object>"
            ],
            "type": "cluster/util"
          },
          45,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "params": [
              ""
            ],
            "type": "cluster/util"
          },
          48,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "params": [
              ""
            ],
            "type": "cluster/util"
          },
          50,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "params": [
              ""
            ],
            "type": "cluster/util"
          },
          54,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "params": [
              ""
            ],
            "type": "cluster/util"
          },
          57,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "params": [
              "RedisOptions[]"
            ],
            "type": "cluster/util"
          },
          76,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "params": [
              "RedisOptions[]"
            ],
            "type": "cluster/util"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "params": [
              "RedisOptions[]"
            ],
            "type": "cluster/util"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "params": [
              ""
            ],
            "type": "cluster/util"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "groupSrvRecords",
            "params": [
              "SrvRecord[]"
            ],
            "type": "cluster/util"
          },
          86,
          "cluster/util.ts"
        ],
        [
          {
            "name": "groupSrvRecords",
            "params": [
              "SrvRecord[]"
            ],
            "type": "cluster/util"
          },
          93,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "params": [
              "SrvRecordsGroup"
            ],
            "type": "cluster/util"
          },
          103,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "params": [
              "SrvRecordsGroup"
            ],
            "type": "cluster/util"
          },
          107,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "params": [
              "SrvRecordsGroup"
            ],
            "type": "cluster/util"
          },
          108,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "params": [
              "SrvRecordsGroup"
            ],
            "type": "cluster/util"
          },
          115,
          "cluster/util.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "connectors/AbstractConnector"
          },
          4,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "params": [],
            "type": "connectors/AbstractConnector#AbstractConnector"
          },
          28,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "timeout",
            "params": [],
            "type": "connectors/AbstractConnector#AbstractConnector"
          },
          29,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "timeout",
            "params": [],
            "type": "connectors/AbstractConnector#AbstractConnector"
          },
          35,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "params": [],
            "type": "connectors/AbstractConnector#AbstractConnector"
          },
          38,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "params": [],
            "type": "connectors/AbstractConnector#AbstractConnector"
          },
          38,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "params": [],
            "type": "connectors/AbstractConnector#AbstractConnector"
          },
          39,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "connectors/SentinelConnector/FailoverDetector"
          },
          5,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "params": [],
            "type": "connectors/SentinelConnector/FailoverDetector#FailoverDetector"
          },
          29,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "params": [],
            "type": "connectors/SentinelConnector/FailoverDetector#FailoverDetector"
          },
          34,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "promise",
            "params": [
              ""
            ],
            "type": "connectors/SentinelConnector/FailoverDetector#FailoverDetector"
          },
          35,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "params": [],
            "type": "connectors/SentinelConnector/FailoverDetector#FailoverDetector"
          },
          43,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "params": [],
            "type": "connectors/SentinelConnector/FailoverDetector#FailoverDetector"
          },
          52,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "disconnect",
            "params": [],
            "type": "connectors/SentinelConnector/FailoverDetector#FailoverDetector"
          },
          60,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "Array<Partial<SentinelAddress>>"
            ],
            "type": "connectors/SentinelConnector/SentinelIterator#SentinelIterator"
          },
          20,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "reset",
            "params": [
              "boolean"
            ],
            "type": "connectors/SentinelConnector/SentinelIterator#SentinelIterator"
          },
          34,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "reset",
            "params": [
              "boolean"
            ],
            "type": "connectors/SentinelConnector/SentinelIterator#SentinelIterator"
          },
          34,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "add",
            "params": [
              "SentinelAddress"
            ],
            "type": "connectors/SentinelConnector/SentinelIterator#SentinelIterator"
          },
          46,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "toString",
            "params": [],
            "type": "connectors/SentinelConnector/SentinelIterator#SentinelIterator"
          },
          51,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "connectors/SentinelConnector/index"
          },
          19,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "SentinelConnectionOptions"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          74,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "SentinelConnectionOptions"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          77,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "check",
            "params": [
              "{ role?: string }"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          86,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          134,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          136,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          139,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [
              ""
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          139,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          156,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          162,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          170,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          171,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          172,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          172,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          174,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          175,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          175,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          178,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          194,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          196,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "params": [
              "RedisClient"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          216,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "params": [
              "RedisClient"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          220,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "params": [
              "RedisClient"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          220,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "params": [
              ""
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          225,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "params": [
              ""
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          227,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "params": [
              ""
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          235,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "params": [
              "RedisClient"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          239,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "params": [
              "RedisClient"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          253,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "params": [
              "RedisClient"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          254,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "params": [
              "RedisClient"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          264,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "params": [
              "RedisClient"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          268,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "params": [
              "RedisClient"
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          268,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "availableSlaves",
            "params": [
              ""
            ],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          274,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          358,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          361,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "params": [],
            "type": "connectors/SentinelConnector/index#SentinelConnector"
          },
          375,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "params": [
              "AddressFromResponse[]",
              "PreferredSlaves"
            ],
            "type": "connectors/SentinelConnector/index"
          },
          391,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "params": [
              "AddressFromResponse[]",
              "PreferredSlaves"
            ],
            "type": "connectors/SentinelConnector/index"
          },
          396,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "addressResponseToAddress",
            "params": [
              "AddressFromResponse"
            ],
            "type": "connectors/SentinelConnector/index"
          },
          440,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "ErrorEmitter"
            ],
            "type": "connectors/StandaloneConnector#StandaloneConnector"
          },
          43,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "ErrorEmitter"
            ],
            "type": "connectors/StandaloneConnector#StandaloneConnector"
          },
          53,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "params": [
              "",
              ""
            ],
            "type": "connectors/StandaloneConnector#StandaloneConnector"
          },
          54,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "params": [],
            "type": "connectors/StandaloneConnector#StandaloneConnector"
          },
          56,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "params": [],
            "type": "connectors/StandaloneConnector#StandaloneConnector"
          },
          56,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "params": [],
            "type": "connectors/StandaloneConnector#StandaloneConnector"
          },
          62,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "params": [],
            "type": "connectors/StandaloneConnector#StandaloneConnector"
          },
          64,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "params": [],
            "type": "connectors/StandaloneConnector#StandaloneConnector"
          },
          67,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "params": [],
            "type": "connectors/StandaloneConnector#StandaloneConnector"
          },
          71,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "params": [],
            "type": "connectors/StandaloneConnector#StandaloneConnector"
          },
          75,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "",
              "RedisError"
            ],
            "type": "errors/ClusterAllFailedError#ClusterAllFailedError"
          },
          7,
          "errors/ClusterAllFailedError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "",
              "RedisError"
            ],
            "type": "errors/ClusterAllFailedError#ClusterAllFailedError"
          },
          8,
          "errors/ClusterAllFailedError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "number"
            ],
            "type": "errors/MaxRetriesPerRequestError#MaxRetriesPerRequestError"
          },
          7,
          "errors/MaxRetriesPerRequestError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "number"
            ],
            "type": "errors/MaxRetriesPerRequestError#MaxRetriesPerRequestError"
          },
          8,
          "errors/MaxRetriesPerRequestError.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "index"
          },
          1,
          "index.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "index"
          },
          71,
          "index.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "index"
          },
          76,
          "index.ts"
        ],
        [
          {
            "name": "get",
            "params": [],
            "type": "index"
          },
          78,
          "index.ts"
        ],
        [
          {
            "name": "set",
            "params": [
              "unknown"
            ],
            "type": "index"
          },
          84,
          "index.ts"
        ],
        [
          {
            "name": "print",
            "params": [
              "Error | null",
              "any"
            ],
            "type": "index"
          },
          95,
          "index.ts"
        ],
        [
          {
            "name": "print",
            "params": [
              "Error | null",
              "any"
            ],
            "type": "index"
          },
          97,
          "index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/RedisOptions"
          },
          205,
          "redis/RedisOptions.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/RedisOptions"
          },
          215,
          "redis/RedisOptions.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "redis/event_handler"
          },
          11,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          15,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          17,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          23,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          28,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          29,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          33,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          37,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          41,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          45,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          50,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          57,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          57,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          60,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          65,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          65,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          78,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "redis/event_handler"
          },
          84,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "redis/event_handler"
          },
          85,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "redis/event_handler"
          },
          91,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "redis/event_handler"
          },
          91,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "redis/event_handler"
          },
          93,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortError",
            "params": [
              "Respondable"
            ],
            "type": "redis/event_handler"
          },
          102,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "params": [
              "Deque<CommandItem>"
            ],
            "type": "redis/event_handler"
          },
          119,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "params": [
              "Deque<CommandItem>"
            ],
            "type": "redis/event_handler"
          },
          125,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "params": [
              "Deque<CommandItem>"
            ],
            "type": "redis/event_handler"
          },
          138,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "params": [
              "Deque<CommandItem>"
            ],
            "type": "redis/event_handler"
          },
          143,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "params": [
              "Deque<CommandItem>"
            ],
            "type": "redis/event_handler"
          },
          148,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          159,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          179,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          184,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          187,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          190,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          196,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          198,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          199,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          201,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          201,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          207,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          211,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          214,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          214,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "close",
            "params": [],
            "type": "redis/event_handler"
          },
          221,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "close",
            "params": [],
            "type": "redis/event_handler"
          },
          222,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "close",
            "params": [],
            "type": "redis/event_handler"
          },
          222,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          228,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          229,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          235,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          239,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          239,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          240,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Error"
            ],
            "type": "redis/event_handler"
          },
          241,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          246,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          248,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "redis/event_handler"
          },
          249,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          253,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          263,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          264,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          264,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          268,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          269,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          269,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          279,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          280,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          282,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          284,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          285,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          287,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          289,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          290,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          292,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          294,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          295,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          302,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          304,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          309,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          311,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          319,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          321,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          323,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          328,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          330,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          335,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "redis/event_handler"
          },
          336,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "transaction"
          },
          26,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "transaction"
          },
          31,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "transaction"
          },
          35,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          43,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          43,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          44,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          45,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "transaction"
          },
          46,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "transaction"
          },
          48,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "transaction"
          },
          52,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              ""
            ],
            "type": "transaction"
          },
          52,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          60,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          66,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          68,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          69,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          70,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "any[]"
            ],
            "type": "transaction"
          },
          73,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "any[]"
            ],
            "type": "transaction"
          },
          81,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          106,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          107,
          "transaction.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Callback"
            ],
            "type": "transaction"
          },
          107,
          "transaction.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "utils/Commander"
          },
          28,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "getBuiltinCommands",
            "params": [],
            "type": "utils/Commander#Commander"
          },
          34,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "addBuiltinCommand",
            "params": [
              "string"
            ],
            "type": "utils/Commander#Commander"
          },
          51,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "sendCommand",
            "params": [
              "Command",
              "WriteableStream",
              "unknown"
            ],
            "type": "utils/Commander#Commander"
          },
          91,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "utils/Commander"
          },
          97,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "utils/Commander"
          },
          98,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "utils/Commander"
          },
          100,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "ArgumentType[] | [...ArgumentType[], Callback]"
            ],
            "type": "utils/Commander"
          },
          135,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "ArgumentType[] | [...ArgumentType[], Callback]"
            ],
            "type": "utils/Commander"
          },
          139,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "ArgumentType[] | [...ArgumentType[], Callback]"
            ],
            "type": "utils/Commander"
          },
          145,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "ArgumentType[] | [...ArgumentType[], Callback]"
            ],
            "type": "utils/Commander"
          },
          152,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "any[]"
            ],
            "type": "utils/Commander"
          },
          178,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "any[]"
            ],
            "type": "utils/Commander"
          },
          188,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "applyMixin",
            "params": [
              "Constructor",
              "Constructor"
            ],
            "type": "utils/applyMixin"
          },
          6,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "params": [
              "Constructor",
              "Constructor"
            ],
            "type": "utils/applyMixin"
          },
          6,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "params": [
              ""
            ],
            "type": "utils/applyMixin"
          },
          7,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "params": [
              ""
            ],
            "type": "utils/applyMixin"
          },
          10,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "getStringValue",
            "params": [
              "any"
            ],
            "type": "utils/debug"
          },
          23,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "params": [
              "any"
            ],
            "type": "utils/debug"
          },
          26,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "params": [
              "any"
            ],
            "type": "utils/debug"
          },
          30,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genRedactedString",
            "params": [
              "string",
              "number"
            ],
            "type": "utils/debug"
          },
          48,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genDebugFunction",
            "params": [
              "string"
            ],
            "type": "utils/debug"
          },
          58,
          "utils/debug.ts"
        ],
        [
          {
            "name": "wrappedDebug",
            "params": [
              "any[]"
            ],
            "type": "utils/debug"
          },
          73,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genDebugFunction",
            "params": [
              "string"
            ],
            "type": "utils/debug"
          },
          76,
          "utils/debug.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "params": [
              "any",
              "BufferEncoding"
            ],
            "type": "utils/index"
          },
          20,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "params": [
              "any",
              "BufferEncoding"
            ],
            "type": "utils/index"
          },
          24,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "params": [
              "any",
              "BufferEncoding"
            ],
            "type": "utils/index"
          },
          28,
          "utils/index.ts"
        ],
        [
          {
            "name": "wrapMultiResult",
            "params": [
              "unknown[] | null"
            ],
            "type": "utils/index"
          },
          57,
          "utils/index.ts"
        ],
        [
          {
            "name": "wrapMultiResult",
            "params": [
              "unknown[] | null"
            ],
            "type": "utils/index"
          },
          59,
          "utils/index.ts"
        ],
        [
          {
            "name": "isInt",
            "params": [
              "any"
            ],
            "type": "utils/index"
          },
          82,
          "utils/index.ts"
        ],
        [
          {
            "name": "isInt",
            "params": [
              "any"
            ],
            "type": "utils/index"
          },
          83,
          "utils/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "utils/index"
          },
          116,
          "utils/index.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "utils/index"
          },
          118,
          "utils/index.ts"
        ],
        [
          {
            "name": "timeout",
            "params": [
              "Callback<T>",
              "number"
            ],
            "type": "utils/index"
          },
          121,
          "utils/index.ts"
        ],
        [
          {
            "name": "timeout",
            "params": [
              "Callback<T>",
              "number"
            ],
            "type": "utils/index"
          },
          121,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertObjectToArray",
            "params": [
              "Record<string, T>"
            ],
            "type": "utils/index"
          },
          137,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertObjectToArray",
            "params": [
              "Record<string, T>"
            ],
            "type": "utils/index"
          },
          140,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertMapToArray",
            "params": [
              "Map<K, V>"
            ],
            "type": "utils/index"
          },
          156,
          "utils/index.ts"
        ],
        [
          {
            "name": "toArg",
            "params": [
              "any"
            ],
            "type": "utils/index"
          },
          171,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "params": [
              "Error",
              "string",
              "string"
            ],
            "type": "utils/index"
          },
          186,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "params": [
              "Error",
              "string",
              "string"
            ],
            "type": "utils/index"
          },
          190,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "params": [
              "Error",
              "string",
              "string"
            ],
            "type": "utils/index"
          },
          198,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "params": [
              "Error",
              "string",
              "string"
            ],
            "type": "utils/index"
          },
          199,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "params": [
              "string"
            ],
            "type": "utils/index"
          },
          211,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "params": [
              "string"
            ],
            "type": "utils/index"
          },
          215,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "params": [
              "string"
            ],
            "type": "utils/index"
          },
          222,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "params": [
              "string"
            ],
            "type": "utils/index"
          },
          223,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "params": [
              "string"
            ],
            "type": "utils/index"
          },
          224,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "params": [
              "string"
            ],
            "type": "utils/index"
          },
          229,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "params": [
              "string"
            ],
            "type": "utils/index"
          },
          242,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "params": [
              "string"
            ],
            "type": "utils/index"
          },
          243,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "params": [
              "string"
            ],
            "type": "utils/index"
          },
          247,
          "utils/index.ts"
        ],
        [
          {
            "name": "resolveTLSProfile",
            "params": [
              "TLSOptions"
            ],
            "type": "utils/index"
          },
          269,
          "utils/index.ts"
        ],
        [
          {
            "name": "resolveTLSProfile",
            "params": [
              "TLSOptions"
            ],
            "type": "utils/index"
          },
          271,
          "utils/index.ts"
        ],
        [
          {
            "name": "sample",
            "params": [
              "T[]",
              ""
            ],
            "type": "utils/index"
          },
          285,
          "utils/index.ts"
        ],
        [
          {
            "name": "sample",
            "params": [
              "T[]",
              ""
            ],
            "type": "utils/index"
          },
          285,
          "utils/index.ts"
        ],
        [
          {
            "name": "shuffle",
            "params": [
              "T[]"
            ],
            "type": "utils/index"
          },
          297,
          "utils/index.ts"
        ],
        [
          {
            "name": "shuffle",
            "params": [
              "T[]"
            ],
            "type": "utils/index"
          },
          297,
          "utils/index.ts"
        ],
        [
          {
            "name": "zipMap",
            "params": [
              "K[]",
              "V[]"
            ],
            "type": "utils/index"
          },
          315,
          "utils/index.ts"
        ],
        [
          {
            "name": "zipMap",
            "params": [
              "K[]",
              "V[]"
            ],
            "type": "utils/index"
          },
          316,
          "utils/index.ts"
        ],
        [
          {
            "name": "zipMap",
            "params": [
              "",
              ""
            ],
            "type": "utils/index"
          },
          317,
          "utils/index.ts"
        ]
      ]
    },
    "cha-null": {
      "build": "bytecode",
      "null_model": true,
      "reference": "null",
      "rows": 310,
      "version": "CHA envelope (no resolution)"
    },
    "code-review-graph": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 1.11,
      "declared_unresolved": 715,
      "fanned_rows": 0,
      "rows": 1041,
      "seconds_breakdown": {
        "adapter_total": 2.37,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/ioredis/crg/data/graph.db",
      "unresolved_sites": [
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          129,
          "Command.ts"
        ],
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          129,
          "Command.ts"
        ],
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          132,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          182,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          197,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          199,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "getSlot",
            "type": "Command"
          },
          216,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          234,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          255,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          269,
          "Command.ts"
        ],
        [
          {
            "name": "transformReply",
            "type": "Command"
          },
          303,
          "Command.ts"
        ],
        [
          {
            "name": "setTimeout",
            "type": "Command"
          },
          317,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "type": "Command"
          },
          329,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "type": "Command"
          },
          337,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "type": "Command"
          },
          344,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          355,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          357,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          359,
          "Command.ts"
        ],
        [
          {
            "name": "_convertValue",
            "type": "Command"
          },
          375,
          "Command.ts"
        ],
        [
          {
            "name": "_convertValue",
            "type": "Command"
          },
          379,
          "Command.ts"
        ],
        [
          {
            "name": "_convertValue",
            "type": "Command"
          },
          382,
          "Command.ts"
        ],
        [
          {
            "name": "hsetArgumentTransformer",
            "type": "Command.ts"
          },
          404,
          "Command.ts"
        ],
        [
          {
            "name": "hsetArgumentTransformer",
            "type": "Command.ts"
          },
          407,
          "Command.ts"
        ],
        [
          {
            "name": "push",
            "type": "MixedBuffers"
          },
          448,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          453,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          456,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          457,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          458,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          459,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "DataHandler"
          },
          59,
          "DataHandler.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "DataHandler"
          },
          60,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnFatalError",
            "type": "DataHandler"
          },
          66,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnError",
            "type": "DataHandler"
          },
          80,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          99,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          103,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          107,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          110,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          118,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          118,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          119,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          123,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          125,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          127,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          128,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          131,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          134,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          135,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          136,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          139,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          140,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          143,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          147,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          148,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          150,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          151,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          154,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          160,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          167,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          174,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          179,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          187,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          196,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          207,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          219,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          220,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          221,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          225,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          226,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          226,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          227,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "type": "DataHandler"
          },
          232,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "type": "DataHandler"
          },
          240,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "type": "DataHandler"
          },
          242,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          252,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          253,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          259,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          260,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          263,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          268,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          269,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          273,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          274,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          275,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          283,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          286,
          "DataHandler.ts"
        ],
        [
          {
            "name": "generateMultiWithNodes",
            "type": "Pipeline.ts"
          },
          18,
          "Pipeline.ts"
        ],
        [
          {
            "name": "generateMultiWithNodes",
            "type": "Pipeline.ts"
          },
          22,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          52,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          52,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          59,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          70,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          78,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          126,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          126,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          135,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          168,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          199,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          199,
          "Pipeline.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Pipeline"
          },
          210,
          "Pipeline.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Pipeline"
          },
          210,
          "Pipeline.ts"
        ],
        [
          {
            "name": "addBatch",
            "type": "Pipeline"
          },
          228,
          "Pipeline.ts"
        ],
        [
          {
            "name": "addBatch",
            "type": "Pipeline"
          },
          229,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.multi",
            "type": "Pipeline.ts"
          },
          243,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          265,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          265,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          269,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          274,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          286,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          290,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          293,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          306,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          307,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          321,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          330,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "type": "Pipeline.ts"
          },
          362,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "type": "Pipeline.ts"
          },
          374,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "type": "Pipeline.ts"
          },
          376,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          127,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          144,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          144,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          145,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          153,
          "Redis.ts"
        ],
        [
          {
            "name": "autoPipelineQueueSize",
            "type": "Redis"
          },
          160,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          182,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          200,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          201,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          206,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          208,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          209,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          224,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          231,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          232,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          235,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          240,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          251,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          255,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          256,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          267,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          269,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          275,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          279,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          281,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          284,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          285,
          "Redis.ts"
        ],
        [
          {
            "name": "connectionReadyHandler",
            "type": "Redis"
          },
          289,
          "Redis.ts"
        ],
        [
          {
            "name": "connectionCloseHandler",
            "type": "Redis"
          },
          293,
          "Redis.ts"
        ],
        [
          {
            "name": "connectionCloseHandler",
            "type": "Redis"
          },
          294,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          296,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          297,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          302,
          "Redis.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Redis"
          },
          317,
          "Redis.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Redis"
          },
          323,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          395,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          397,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          398,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          425,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          428,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          435,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          451,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          452,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          466,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          476,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          476,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          482,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          499,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          510,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          512,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          515,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          534,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          537,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          538,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          547,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          553,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          554,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          621,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          622,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          625,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          649,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          658,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          668,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          675,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          721,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          723,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          724,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          734,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          736,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          739,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          742,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Redis"
          },
          755,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Redis"
          },
          763,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Redis"
          },
          763,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          786,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          793,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          794,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          801,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          804,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          805,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          817,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          817,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          819,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          820,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          823,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          825,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          828,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          833,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          835,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          836,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          843,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          851,
          "Redis.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          25,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          31,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          34,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          37,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          40,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          40,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          45,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          48,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          52,
          "ScanStream.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "CustomScriptCommand"
          },
          23,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "CustomScriptCommand"
          },
          24,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "CustomScriptCommand"
          },
          26,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "CustomScriptCommand"
          },
          29,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "CustomScriptCommand"
          },
          30,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          44,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          55,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          56,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          65,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          68,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          69,
          "Script.ts"
        ],
        [
          {
            "name": "channels",
            "type": "SubscriptionSet"
          },
          25,
          "SubscriptionSet.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          28,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          31,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          42,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          45,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          46,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          55,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          56,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          64,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          68,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          73,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "shouldUseAutoPipelining",
            "type": "autoPipelining.ts"
          },
          88,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "shouldUseAutoPipelining",
            "type": "autoPipelining.ts"
          },
          89,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "type": "autoPipelining.ts"
          },
          100,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "type": "autoPipelining.ts"
          },
          100,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "type": "autoPipelining.ts"
          },
          106,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          123,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          123,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          124,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          126,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          128,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          132,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          150,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          151,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          155,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          156,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          159,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          162,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          175,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          182,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          186,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          190,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          196,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          26,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          31,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          35,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          39,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "start",
            "type": "ClusterSubscriber"
          },
          53,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "stop",
            "type": "ClusterSubscriber"
          },
          62,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "onSubscriberEnd",
            "type": "ClusterSubscriber"
          },
          67,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "onSubscriberEnd",
            "type": "ClusterSubscriber"
          },
          75,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          85,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          90,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          96,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          104,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          131,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          138,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          146,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          148,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          150,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          163,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          172,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          185,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          186,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          190,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          191,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "getNodes",
            "type": "ConnectionPool"
          },
          26,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getNodes",
            "type": "ConnectionPool"
          },
          26,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getSampleInstance",
            "type": "ConnectionPool"
          },
          34,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          44,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          47,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          57,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          58,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          68,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          70,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          90,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          92,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          93,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          94,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          98,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          100,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          101,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          113,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          115,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          125,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          125,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          127,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          132,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          132,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "removeNode",
            "type": "ConnectionPool"
          },
          144,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "push",
            "type": "DelayQueue"
          },
          35,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "push",
            "type": "DelayQueue"
          },
          36,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "execute",
            "type": "DelayQueue"
          },
          53,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "execute",
            "type": "DelayQueue"
          },
          57,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          120,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          123,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          136,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          147,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          148,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          150,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          151,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          153,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          156,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          157,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          163,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          163,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          164,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          171,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          172,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          187,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          194,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          194,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          197,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          202,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          210,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          214,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "Cluster"
          },
          224,
          "cluster/index.ts"
        ],
        [
          {
            "name": "refreshListener",
            "type": "Cluster"
          },
          230,
          "cluster/index.ts"
        ],
        [
          {
            "name": "refreshListener",
            "type": "Cluster"
          },
          236,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          255,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          257,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          260,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          261,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          262,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          262,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          266,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          276,
          "cluster/index.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Cluster"
          },
          292,
          "cluster/index.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Cluster"
          },
          294,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          317,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          325,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          325,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          329,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          330,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          338,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          339,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          339,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          340,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          341,
          "cluster/index.ts"
        ],
        [
          {
            "name": "duplicate",
            "type": "Cluster"
          },
          368,
          "cluster/index.ts"
        ],
        [
          {
            "name": "duplicate",
            "type": "Cluster"
          },
          369,
          "cluster/index.ts"
        ],
        [
          {
            "name": "delayUntilReady",
            "type": "Cluster"
          },
          391,
          "cluster/index.ts"
        ],
        [
          {
            "name": "autoPipelineQueueSize",
            "type": "Cluster"
          },
          402,
          "cluster/index.ts"
        ],
        [
          {
            "name": "refreshSlotsCache",
            "type": "Cluster"
          },
          416,
          "cluster/index.ts"
        ],
        [
          {
            "name": "wrapper",
            "type": "Cluster"
          },
          429,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster"
          },
          448,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster"
          },
          458,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster"
          },
          462,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          476,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          479,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          486,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          486,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          495,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          496,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          500,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          503,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          504,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          511,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          514,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          518,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          527,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          530,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          539,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          552,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          560,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          563,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          564,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          584,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          600,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          602,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          608,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          652,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          657,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          663,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          667,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          670,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          681,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          690,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          693,
          "cluster/index.ts"
        ],
        [
          {
            "name": "clearNodesRefreshInterval",
            "type": "Cluster"
          },
          703,
          "cluster/index.ts"
        ],
        [
          {
            "name": "nextRound",
            "type": "Cluster"
          },
          714,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Cluster"
          },
          730,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Cluster"
          },
          732,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Cluster"
          },
          733,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          742,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          750,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          760,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          761,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          762,
          "cluster/index.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Cluster"
          },
          776,
          "cluster/index.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Cluster"
          },
          777,
          "cluster/index.ts"
        ],
        [
          {
            "name": "executeOfflineCommands",
            "type": "Cluster"
          },
          783,
          "cluster/index.ts"
        ],
        [
          {
            "name": "executeOfflineCommands",
            "type": "Cluster"
          },
          787,
          "cluster/index.ts"
        ],
        [
          {
            "name": "natMapper",
            "type": "Cluster"
          },
          801,
          "cluster/index.ts"
        ],
        [
          {
            "name": "natMapper",
            "type": "Cluster"
          },
          802,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          812,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          830,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          832,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          835,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          837,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          844,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          849,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          854,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          871,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          872,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          875,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          889,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          892,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          907,
          "cluster/index.ts"
        ],
        [
          {
            "name": "invokeReadyDelayedCallbacks",
            "type": "Cluster"
          },
          914,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          924,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          926,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          929,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          933,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          935,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          943,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          944,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          946,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          953,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          955,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          960,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          960,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          961,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster"
          },
          966,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster"
          },
          974,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster"
          },
          977,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster"
          },
          979,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "type": "Cluster"
          },
          994,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "type": "Cluster"
          },
          996,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "type": "Cluster"
          },
          1001,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "type": "Cluster"
          },
          1003,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "type": "Cluster"
          },
          1004,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1017,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1027,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1028,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1029,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1036,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1037,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1042,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1044,
          "cluster/index.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          32,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          37,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          38,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          38,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          45,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          48,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          50,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          57,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          76,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "groupSrvRecords",
            "type": "cluster/util.ts"
          },
          86,
          "cluster/util.ts"
        ],
        [
          {
            "name": "groupSrvRecords",
            "type": "cluster/util.ts"
          },
          93,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          103,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          107,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          108,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          111,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          115,
          "cluster/util.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          28,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          29,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          35,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          38,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          38,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          39,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          29,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          34,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          35,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          43,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          45,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          52,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "FailoverDetector"
          },
          60,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SentinelIterator"
          },
          20,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "reset",
            "type": "SentinelIterator"
          },
          34,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "reset",
            "type": "SentinelIterator"
          },
          34,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "add",
            "type": "SentinelIterator"
          },
          46,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "toString",
            "type": "SentinelIterator"
          },
          51,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "check",
            "type": "SentinelConnector"
          },
          86,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          122,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          134,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          138,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          139,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          162,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          170,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          171,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          172,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          172,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          174,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          175,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          175,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          178,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          194,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          196,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          214,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          216,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          220,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          220,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          225,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          227,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          235,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          239,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          245,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          253,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          254,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          262,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          264,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          268,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          268,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          274,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolve",
            "type": "SentinelConnector"
          },
          321,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolve",
            "type": "SentinelConnector"
          },
          330,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          356,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          358,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          361,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          375,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          389,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          391,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          396,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "addressResponseToAddress",
            "type": "connectors/SentinelConnector/index.ts"
          },
          440,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          43,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          54,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          56,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          62,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          64,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          67,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          71,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          75,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterAllFailedError"
          },
          8,
          "errors/ClusterAllFailedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MaxRetriesPerRequestError"
          },
          8,
          "errors/MaxRetriesPerRequestError.ts"
        ],
        [
          {
            "name": "get",
            "type": "index.ts"
          },
          78,
          "index.ts"
        ],
        [
          {
            "name": "set",
            "type": "index.ts"
          },
          84,
          "index.ts"
        ],
        [
          {
            "name": "print",
            "type": "index.ts"
          },
          95,
          "index.ts"
        ],
        [
          {
            "name": "print",
            "type": "index.ts"
          },
          97,
          "index.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          15,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          17,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          23,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          28,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          29,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          33,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          37,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          41,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          45,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          50,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          57,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          57,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          60,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          78,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          84,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          90,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          93,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          119,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          125,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          126,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          138,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          143,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          144,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          148,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          149,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          159,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          179,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          184,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          187,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          190,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          196,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          198,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          201,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          201,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          207,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          211,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          214,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "close",
            "type": "redis/event_handler.ts"
          },
          221,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "close",
            "type": "redis/event_handler.ts"
          },
          222,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "errorHandler",
            "type": "redis/event_handler.ts"
          },
          228,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "errorHandler",
            "type": "redis/event_handler.ts"
          },
          229,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          235,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          239,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          239,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          240,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          241,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          246,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          248,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          253,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          263,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          264,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          264,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          268,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          269,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          269,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          279,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          280,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          282,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          284,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          285,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          287,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          289,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          290,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          292,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          294,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          295,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          302,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          304,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          309,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          311,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          319,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          321,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          323,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          328,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          330,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          335,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          336,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          18,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          26,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          31,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          35,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          36,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          43,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          43,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          44,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          46,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          48,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          52,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          60,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          66,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          68,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          69,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          70,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          81,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          97,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          106,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          107,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          107,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          108,
          "transaction.ts"
        ],
        [
          {
            "name": "getBuiltinCommands",
            "type": "Commander"
          },
          34,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "addBuiltinCommand",
            "type": "Commander"
          },
          51,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateFunction",
            "type": "utils/Commander.ts"
          },
          135,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateFunction",
            "type": "utils/Commander.ts"
          },
          139,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateScriptingFunction",
            "type": "utils/Commander.ts"
          },
          178,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          6,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          6,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          7,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          10,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          22,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          23,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          25,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          26,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          30,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genRedactedString",
            "type": "utils/debug.ts"
          },
          48,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genDebugFunction",
            "type": "utils/debug.ts"
          },
          58,
          "utils/debug.ts"
        ],
        [
          {
            "name": "wrappedDebug",
            "type": "utils/debug.ts"
          },
          73,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genDebugFunction",
            "type": "utils/debug.ts"
          },
          76,
          "utils/debug.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          20,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          22,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          24,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          28,
          "utils/index.ts"
        ],
        [
          {
            "name": "wrapMultiResult",
            "type": "utils/index.ts"
          },
          57,
          "utils/index.ts"
        ],
        [
          {
            "name": "wrapMultiResult",
            "type": "utils/index.ts"
          },
          59,
          "utils/index.ts"
        ],
        [
          {
            "name": "isInt",
            "type": "utils/index.ts"
          },
          82,
          "utils/index.ts"
        ],
        [
          {
            "name": "isInt",
            "type": "utils/index.ts"
          },
          83,
          "utils/index.ts"
        ],
        [
          {
            "name": "run",
            "type": "utils/index.ts"
          },
          116,
          "utils/index.ts"
        ],
        [
          {
            "name": "run",
            "type": "utils/index.ts"
          },
          118,
          "utils/index.ts"
        ],
        [
          {
            "name": "timeout",
            "type": "utils/index.ts"
          },
          121,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertObjectToArray",
            "type": "utils/index.ts"
          },
          137,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertObjectToArray",
            "type": "utils/index.ts"
          },
          140,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertMapToArray",
            "type": "utils/index.ts"
          },
          156,
          "utils/index.ts"
        ],
        [
          {
            "name": "toArg",
            "type": "utils/index.ts"
          },
          171,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          186,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          190,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          198,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          199,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          211,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          215,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          222,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          223,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          224,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          229,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          242,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          243,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          247,
          "utils/index.ts"
        ],
        [
          {
            "name": "resolveTLSProfile",
            "type": "utils/index.ts"
          },
          269,
          "utils/index.ts"
        ],
        [
          {
            "name": "resolveTLSProfile",
            "type": "utils/index.ts"
          },
          271,
          "utils/index.ts"
        ],
        [
          {
            "name": "sample",
            "type": "utils/index.ts"
          },
          285,
          "utils/index.ts"
        ],
        [
          {
            "name": "sample",
            "type": "utils/index.ts"
          },
          285,
          "utils/index.ts"
        ],
        [
          {
            "name": "shuffle",
            "type": "utils/index.ts"
          },
          297,
          "utils/index.ts"
        ],
        [
          {
            "name": "shuffle",
            "type": "utils/index.ts"
          },
          297,
          "utils/index.ts"
        ],
        [
          {
            "name": "zipMap",
            "type": "utils/index.ts"
          },
          316,
          "utils/index.ts"
        ]
      ],
      "version": "code-review-graph 2.3.8"
    },
    "code-review-graph-dispatch": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 1.11,
      "declared_unresolved": 704,
      "fanned_rows": 11,
      "rows": 1056,
      "seconds_breakdown": {
        "adapter_total": 2.37,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/ioredis/crg/data/graph.db",
      "unresolved_sites": [
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          129,
          "Command.ts"
        ],
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          129,
          "Command.ts"
        ],
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          132,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          182,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          197,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          199,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "getSlot",
            "type": "Command"
          },
          216,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          234,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          255,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          269,
          "Command.ts"
        ],
        [
          {
            "name": "transformReply",
            "type": "Command"
          },
          303,
          "Command.ts"
        ],
        [
          {
            "name": "setTimeout",
            "type": "Command"
          },
          317,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "type": "Command"
          },
          329,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "type": "Command"
          },
          337,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "type": "Command"
          },
          344,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          355,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          357,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          359,
          "Command.ts"
        ],
        [
          {
            "name": "_convertValue",
            "type": "Command"
          },
          375,
          "Command.ts"
        ],
        [
          {
            "name": "_convertValue",
            "type": "Command"
          },
          379,
          "Command.ts"
        ],
        [
          {
            "name": "_convertValue",
            "type": "Command"
          },
          382,
          "Command.ts"
        ],
        [
          {
            "name": "hsetArgumentTransformer",
            "type": "Command.ts"
          },
          404,
          "Command.ts"
        ],
        [
          {
            "name": "hsetArgumentTransformer",
            "type": "Command.ts"
          },
          407,
          "Command.ts"
        ],
        [
          {
            "name": "push",
            "type": "MixedBuffers"
          },
          448,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          453,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          456,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          457,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          458,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          459,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "DataHandler"
          },
          59,
          "DataHandler.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "DataHandler"
          },
          60,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnFatalError",
            "type": "DataHandler"
          },
          66,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnError",
            "type": "DataHandler"
          },
          80,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          99,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          103,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          107,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          110,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          118,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          118,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          119,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          123,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          125,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          127,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          128,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          131,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          134,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          135,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          136,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          139,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          140,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          143,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          147,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          148,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          150,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          151,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          154,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          160,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          167,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          174,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          179,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          187,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          196,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          207,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          219,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          220,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          221,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          225,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          226,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          226,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          227,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "type": "DataHandler"
          },
          232,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "type": "DataHandler"
          },
          240,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "type": "DataHandler"
          },
          242,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          252,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          253,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          259,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          260,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          263,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          268,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          269,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          273,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          274,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          275,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          283,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          286,
          "DataHandler.ts"
        ],
        [
          {
            "name": "generateMultiWithNodes",
            "type": "Pipeline.ts"
          },
          18,
          "Pipeline.ts"
        ],
        [
          {
            "name": "generateMultiWithNodes",
            "type": "Pipeline.ts"
          },
          22,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          52,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          52,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          59,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          70,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          78,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          126,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          126,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          135,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          168,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          199,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          199,
          "Pipeline.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Pipeline"
          },
          210,
          "Pipeline.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Pipeline"
          },
          210,
          "Pipeline.ts"
        ],
        [
          {
            "name": "addBatch",
            "type": "Pipeline"
          },
          228,
          "Pipeline.ts"
        ],
        [
          {
            "name": "addBatch",
            "type": "Pipeline"
          },
          229,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.multi",
            "type": "Pipeline.ts"
          },
          243,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          265,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          269,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          274,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          286,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          290,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          293,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          306,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          307,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          321,
          "Pipeline.ts"
        ],
        [
          {
            "name": "Pipeline.prototype.exec",
            "type": "Pipeline.ts"
          },
          330,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "type": "Pipeline.ts"
          },
          362,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "type": "Pipeline.ts"
          },
          374,
          "Pipeline.ts"
        ],
        [
          {
            "name": "write",
            "type": "Pipeline.ts"
          },
          376,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          127,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          144,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          144,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          145,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          153,
          "Redis.ts"
        ],
        [
          {
            "name": "autoPipelineQueueSize",
            "type": "Redis"
          },
          160,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          182,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          200,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          201,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          208,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          224,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          231,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          232,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          235,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          240,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          251,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          255,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          256,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          267,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          269,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          275,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          279,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          281,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          284,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          285,
          "Redis.ts"
        ],
        [
          {
            "name": "connectionReadyHandler",
            "type": "Redis"
          },
          289,
          "Redis.ts"
        ],
        [
          {
            "name": "connectionCloseHandler",
            "type": "Redis"
          },
          293,
          "Redis.ts"
        ],
        [
          {
            "name": "connectionCloseHandler",
            "type": "Redis"
          },
          294,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          296,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          297,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          302,
          "Redis.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Redis"
          },
          317,
          "Redis.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Redis"
          },
          323,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          395,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          397,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          398,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          425,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          428,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          435,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          451,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          452,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          466,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          476,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          476,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          482,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          499,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          510,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          512,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          515,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          534,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          537,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          538,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          547,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          553,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          554,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          621,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          622,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          625,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          649,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          658,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          668,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          675,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          721,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          723,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          724,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          734,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          736,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          739,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          742,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Redis"
          },
          755,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Redis"
          },
          763,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Redis"
          },
          763,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          786,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          793,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          794,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          801,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          804,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          805,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          817,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          817,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          819,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          820,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          823,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          825,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          828,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          833,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          835,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          836,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          843,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          851,
          "Redis.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          25,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          31,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          34,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          37,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          40,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          40,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          45,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          48,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          52,
          "ScanStream.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "CustomScriptCommand"
          },
          23,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "CustomScriptCommand"
          },
          24,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "CustomScriptCommand"
          },
          26,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "CustomScriptCommand"
          },
          29,
          "Script.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "CustomScriptCommand"
          },
          30,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          44,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          55,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          56,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          65,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          68,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          69,
          "Script.ts"
        ],
        [
          {
            "name": "channels",
            "type": "SubscriptionSet"
          },
          25,
          "SubscriptionSet.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          28,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          31,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          42,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          45,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          46,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          55,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          56,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          64,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          68,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          73,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "shouldUseAutoPipelining",
            "type": "autoPipelining.ts"
          },
          88,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "shouldUseAutoPipelining",
            "type": "autoPipelining.ts"
          },
          89,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "type": "autoPipelining.ts"
          },
          100,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "type": "autoPipelining.ts"
          },
          100,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "type": "autoPipelining.ts"
          },
          106,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          123,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          123,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          124,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          126,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          128,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          132,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          150,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          151,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          155,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          156,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          159,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          162,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          175,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          182,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          186,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          190,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          196,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          26,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          31,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          35,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          39,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "start",
            "type": "ClusterSubscriber"
          },
          53,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "stop",
            "type": "ClusterSubscriber"
          },
          62,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "onSubscriberEnd",
            "type": "ClusterSubscriber"
          },
          67,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "onSubscriberEnd",
            "type": "ClusterSubscriber"
          },
          75,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          85,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          90,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          96,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          104,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          131,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          138,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          146,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          148,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          150,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          163,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          172,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          185,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          186,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          190,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          191,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "getNodes",
            "type": "ConnectionPool"
          },
          26,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getNodes",
            "type": "ConnectionPool"
          },
          26,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getSampleInstance",
            "type": "ConnectionPool"
          },
          34,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          44,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          47,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          57,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          58,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          68,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          70,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          90,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          92,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          93,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          94,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          98,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          100,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          101,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          113,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          115,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          125,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          125,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          127,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          132,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          132,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "removeNode",
            "type": "ConnectionPool"
          },
          144,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "push",
            "type": "DelayQueue"
          },
          35,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "push",
            "type": "DelayQueue"
          },
          36,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "execute",
            "type": "DelayQueue"
          },
          53,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "execute",
            "type": "DelayQueue"
          },
          57,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          120,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          123,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          136,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          147,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          148,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          150,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          151,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          153,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          156,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          157,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          163,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          163,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          164,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          171,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          172,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          187,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          194,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          194,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          197,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          202,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          210,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          214,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "Cluster"
          },
          224,
          "cluster/index.ts"
        ],
        [
          {
            "name": "refreshListener",
            "type": "Cluster"
          },
          230,
          "cluster/index.ts"
        ],
        [
          {
            "name": "refreshListener",
            "type": "Cluster"
          },
          236,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          255,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          257,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          260,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          261,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          262,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          262,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          266,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          276,
          "cluster/index.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Cluster"
          },
          292,
          "cluster/index.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Cluster"
          },
          294,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          317,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          325,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          325,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          329,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          330,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          338,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          339,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          339,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          340,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          341,
          "cluster/index.ts"
        ],
        [
          {
            "name": "duplicate",
            "type": "Cluster"
          },
          368,
          "cluster/index.ts"
        ],
        [
          {
            "name": "duplicate",
            "type": "Cluster"
          },
          369,
          "cluster/index.ts"
        ],
        [
          {
            "name": "autoPipelineQueueSize",
            "type": "Cluster"
          },
          402,
          "cluster/index.ts"
        ],
        [
          {
            "name": "wrapper",
            "type": "Cluster"
          },
          429,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster"
          },
          448,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster"
          },
          458,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster"
          },
          462,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          476,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          479,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          486,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          486,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          495,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          496,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          500,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          503,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          504,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          511,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          514,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          518,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          527,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          530,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          539,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          552,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          560,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          563,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          564,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          584,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster"
          },
          608,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          652,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          657,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          663,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          667,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          670,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          681,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          690,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          693,
          "cluster/index.ts"
        ],
        [
          {
            "name": "clearNodesRefreshInterval",
            "type": "Cluster"
          },
          703,
          "cluster/index.ts"
        ],
        [
          {
            "name": "nextRound",
            "type": "Cluster"
          },
          714,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Cluster"
          },
          730,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Cluster"
          },
          732,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Cluster"
          },
          733,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          742,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          750,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          760,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          761,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          762,
          "cluster/index.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Cluster"
          },
          776,
          "cluster/index.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Cluster"
          },
          777,
          "cluster/index.ts"
        ],
        [
          {
            "name": "executeOfflineCommands",
            "type": "Cluster"
          },
          783,
          "cluster/index.ts"
        ],
        [
          {
            "name": "executeOfflineCommands",
            "type": "Cluster"
          },
          787,
          "cluster/index.ts"
        ],
        [
          {
            "name": "natMapper",
            "type": "Cluster"
          },
          801,
          "cluster/index.ts"
        ],
        [
          {
            "name": "natMapper",
            "type": "Cluster"
          },
          802,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          812,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          830,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          832,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          837,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          844,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          849,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          854,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          875,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          889,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          892,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          907,
          "cluster/index.ts"
        ],
        [
          {
            "name": "invokeReadyDelayedCallbacks",
            "type": "Cluster"
          },
          914,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          924,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          926,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          929,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          933,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          935,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          943,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          944,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          946,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          953,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          955,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          960,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          960,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          961,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster"
          },
          966,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster"
          },
          974,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster"
          },
          977,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster"
          },
          979,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "type": "Cluster"
          },
          994,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "type": "Cluster"
          },
          996,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "type": "Cluster"
          },
          1001,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "type": "Cluster"
          },
          1003,
          "cluster/index.ts"
        ],
        [
          {
            "name": "dnsLookup",
            "type": "Cluster"
          },
          1004,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1017,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1027,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1028,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1029,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1036,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1037,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1042,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1044,
          "cluster/index.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          32,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          37,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          38,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          38,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          45,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          48,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          50,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          57,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          76,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "groupSrvRecords",
            "type": "cluster/util.ts"
          },
          86,
          "cluster/util.ts"
        ],
        [
          {
            "name": "groupSrvRecords",
            "type": "cluster/util.ts"
          },
          93,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          103,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          107,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          108,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          111,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          115,
          "cluster/util.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          28,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          29,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          35,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          38,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          38,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "connectors/AbstractConnector.ts"
          },
          39,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          29,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          34,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          35,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          43,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          45,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          52,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "FailoverDetector"
          },
          60,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SentinelIterator"
          },
          20,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "reset",
            "type": "SentinelIterator"
          },
          34,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "reset",
            "type": "SentinelIterator"
          },
          34,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "add",
            "type": "SentinelIterator"
          },
          46,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "toString",
            "type": "SentinelIterator"
          },
          51,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "check",
            "type": "SentinelConnector"
          },
          86,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          122,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          134,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          138,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          139,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          162,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          170,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          171,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          172,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          172,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          174,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          175,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          175,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          178,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          194,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connectToNext",
            "type": "SentinelConnector"
          },
          196,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          214,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          216,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          220,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          220,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          225,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          227,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          235,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          239,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          245,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          253,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          254,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          262,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          264,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          268,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          268,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          274,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolve",
            "type": "SentinelConnector"
          },
          321,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          356,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          358,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          361,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          375,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          389,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          391,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          396,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "addressResponseToAddress",
            "type": "connectors/SentinelConnector/index.ts"
          },
          440,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          43,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          54,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          56,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          62,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          64,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          67,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          71,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          75,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterAllFailedError"
          },
          8,
          "errors/ClusterAllFailedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MaxRetriesPerRequestError"
          },
          8,
          "errors/MaxRetriesPerRequestError.ts"
        ],
        [
          {
            "name": "get",
            "type": "index.ts"
          },
          78,
          "index.ts"
        ],
        [
          {
            "name": "set",
            "type": "index.ts"
          },
          84,
          "index.ts"
        ],
        [
          {
            "name": "print",
            "type": "index.ts"
          },
          95,
          "index.ts"
        ],
        [
          {
            "name": "print",
            "type": "index.ts"
          },
          97,
          "index.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          15,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          17,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          23,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          28,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          29,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          33,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          37,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          41,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          45,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          50,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          57,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          57,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          60,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          78,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          84,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          90,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          93,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          119,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          125,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          126,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          138,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          143,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          144,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          148,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          149,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          159,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          179,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          184,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          187,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          190,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          196,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          198,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          201,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          201,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          207,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          211,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          214,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "close",
            "type": "redis/event_handler.ts"
          },
          221,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "close",
            "type": "redis/event_handler.ts"
          },
          222,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "errorHandler",
            "type": "redis/event_handler.ts"
          },
          228,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "errorHandler",
            "type": "redis/event_handler.ts"
          },
          229,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          235,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          239,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          239,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          240,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          241,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          246,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          248,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          253,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          263,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          264,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          264,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          268,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          269,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          269,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          279,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          280,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          282,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          284,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          285,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          287,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          289,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          290,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          292,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          294,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          295,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          302,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          304,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          309,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          311,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          319,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          321,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          323,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          328,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          330,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          335,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          336,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          18,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          26,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          31,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          35,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          36,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          43,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          43,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          44,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          46,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          48,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          52,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          60,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          66,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          68,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          69,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          70,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          81,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          97,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          106,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          107,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          107,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          108,
          "transaction.ts"
        ],
        [
          {
            "name": "getBuiltinCommands",
            "type": "Commander"
          },
          34,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "addBuiltinCommand",
            "type": "Commander"
          },
          51,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateFunction",
            "type": "utils/Commander.ts"
          },
          135,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateFunction",
            "type": "utils/Commander.ts"
          },
          139,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateScriptingFunction",
            "type": "utils/Commander.ts"
          },
          178,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          6,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          6,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          7,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          10,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          22,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          23,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          25,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          26,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          30,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genRedactedString",
            "type": "utils/debug.ts"
          },
          48,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genDebugFunction",
            "type": "utils/debug.ts"
          },
          58,
          "utils/debug.ts"
        ],
        [
          {
            "name": "wrappedDebug",
            "type": "utils/debug.ts"
          },
          73,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genDebugFunction",
            "type": "utils/debug.ts"
          },
          76,
          "utils/debug.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          20,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          22,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          24,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          28,
          "utils/index.ts"
        ],
        [
          {
            "name": "wrapMultiResult",
            "type": "utils/index.ts"
          },
          57,
          "utils/index.ts"
        ],
        [
          {
            "name": "wrapMultiResult",
            "type": "utils/index.ts"
          },
          59,
          "utils/index.ts"
        ],
        [
          {
            "name": "isInt",
            "type": "utils/index.ts"
          },
          82,
          "utils/index.ts"
        ],
        [
          {
            "name": "isInt",
            "type": "utils/index.ts"
          },
          83,
          "utils/index.ts"
        ],
        [
          {
            "name": "run",
            "type": "utils/index.ts"
          },
          116,
          "utils/index.ts"
        ],
        [
          {
            "name": "run",
            "type": "utils/index.ts"
          },
          118,
          "utils/index.ts"
        ],
        [
          {
            "name": "timeout",
            "type": "utils/index.ts"
          },
          121,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertObjectToArray",
            "type": "utils/index.ts"
          },
          137,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertObjectToArray",
            "type": "utils/index.ts"
          },
          140,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertMapToArray",
            "type": "utils/index.ts"
          },
          156,
          "utils/index.ts"
        ],
        [
          {
            "name": "toArg",
            "type": "utils/index.ts"
          },
          171,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          186,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          190,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          198,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          199,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          211,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          215,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          222,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          223,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          224,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          229,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          242,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          243,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          247,
          "utils/index.ts"
        ],
        [
          {
            "name": "resolveTLSProfile",
            "type": "utils/index.ts"
          },
          269,
          "utils/index.ts"
        ],
        [
          {
            "name": "resolveTLSProfile",
            "type": "utils/index.ts"
          },
          271,
          "utils/index.ts"
        ],
        [
          {
            "name": "sample",
            "type": "utils/index.ts"
          },
          285,
          "utils/index.ts"
        ],
        [
          {
            "name": "sample",
            "type": "utils/index.ts"
          },
          285,
          "utils/index.ts"
        ],
        [
          {
            "name": "shuffle",
            "type": "utils/index.ts"
          },
          297,
          "utils/index.ts"
        ],
        [
          {
            "name": "shuffle",
            "type": "utils/index.ts"
          },
          297,
          "utils/index.ts"
        ],
        [
          {
            "name": "zipMap",
            "type": "utils/index.ts"
          },
          316,
          "utils/index.ts"
        ]
      ],
      "version": "code-review-graph 2.3.8"
    },
    "codegraph": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 0.88,
      "declared_unresolved": 551,
      "dispatch_expanded_sites": 0,
      "rows": 408,
      "seconds_breakdown": {
        "adapter_total": 1.18,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "synthesized_rows_skipped": 10,
      "unresolved_sites": [
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          129,
          "Command.ts"
        ],
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          129,
          "Command.ts"
        ],
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          132,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          182,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          197,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          199,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "getSlot",
            "type": "Command"
          },
          216,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          234,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          255,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          269,
          "Command.ts"
        ],
        [
          {
            "name": "transformReply",
            "type": "Command"
          },
          303,
          "Command.ts"
        ],
        [
          {
            "name": "setTimeout",
            "type": "Command"
          },
          315,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "type": "Command"
          },
          329,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "type": "Command"
          },
          344,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          355,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          357,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          359,
          "Command.ts"
        ],
        [
          {
            "name": "_convertValue",
            "type": "Command"
          },
          375,
          "Command.ts"
        ],
        [
          {
            "name": "push",
            "type": "MixedBuffers"
          },
          448,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          453,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          456,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          457,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          458,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          459,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "DataHandler"
          },
          59,
          "DataHandler.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "DataHandler"
          },
          60,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          103,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          107,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          118,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          123,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          125,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          131,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          135,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          136,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          143,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          147,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          148,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          154,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          167,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          179,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          187,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          219,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          220,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          221,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          225,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          226,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          226,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          227,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "type": "DataHandler"
          },
          232,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "type": "DataHandler"
          },
          242,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          252,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          253,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          260,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          263,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          268,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          269,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          273,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          274,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          286,
          "DataHandler.ts"
        ],
        [
          {
            "name": "generateMultiWithNodes",
            "type": "Pipeline.ts"
          },
          18,
          "Pipeline.ts"
        ],
        [
          {
            "name": "generateMultiWithNodes",
            "type": "Pipeline.ts"
          },
          22,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          47,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          52,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          52,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          59,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          70,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          78,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          126,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          126,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          135,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          160,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          168,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          170,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          174,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          199,
          "Pipeline.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Pipeline"
          },
          210,
          "Pipeline.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Pipeline"
          },
          210,
          "Pipeline.ts"
        ],
        [
          {
            "name": "addBatch",
            "type": "Pipeline"
          },
          228,
          "Pipeline.ts"
        ],
        [
          {
            "name": "addBatch",
            "type": "Pipeline"
          },
          229,
          "Pipeline.ts"
        ],
        [
          {
            "name": "execPipeline",
            "type": "Pipeline.ts"
          },
          362,
          "Pipeline.ts"
        ],
        [
          {
            "name": "execPipeline",
            "type": "Pipeline.ts"
          },
          374,
          "Pipeline.ts"
        ],
        [
          {
            "name": "execPipeline",
            "type": "Pipeline.ts"
          },
          376,
          "Pipeline.ts"
        ],
        [
          {
            "name": "execPipeline",
            "type": "Pipeline.ts"
          },
          376,
          "Pipeline.ts"
        ],
        [
          {
            "name": "execPipeline",
            "type": "Pipeline.ts"
          },
          378,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          124,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          127,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          144,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          144,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          153,
          "Redis.ts"
        ],
        [
          {
            "name": "autoPipelineQueueSize",
            "type": "Redis"
          },
          160,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          200,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          206,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          209,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          224,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          231,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          232,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          235,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          240,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          256,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          265,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          267,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          275,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          276,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          279,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          281,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          284,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          285,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          289,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          293,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          296,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          297,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          302,
          "Redis.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Redis"
          },
          317,
          "Redis.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Redis"
          },
          321,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          395,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          397,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          398,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          425,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          428,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          435,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          451,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          452,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          466,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          476,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          510,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          512,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          515,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          534,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          537,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          546,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          547,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          553,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          554,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          621,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          622,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          625,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          649,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          668,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          721,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          723,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          724,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          734,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          736,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          739,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          742,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Redis"
          },
          763,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Redis"
          },
          763,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          786,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          793,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          801,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          804,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          817,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          817,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          819,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          820,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          833,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          835,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          836,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          854,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ScanStream"
          },
          20,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          31,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          34,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          37,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          40,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          40,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          43,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          45,
          "ScanStream.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          23,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          24,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          26,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          29,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          30,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          44,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          55,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          56,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          65,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          68,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          69,
          "Script.ts"
        ],
        [
          {
            "name": "channels",
            "type": "SubscriptionSet"
          },
          25,
          "SubscriptionSet.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          28,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          31,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          45,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          46,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          55,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          56,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          64,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          68,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          73,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "shouldUseAutoPipelining",
            "type": "autoPipelining.ts"
          },
          88,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "shouldUseAutoPipelining",
            "type": "autoPipelining.ts"
          },
          89,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "type": "autoPipelining.ts"
          },
          100,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "type": "autoPipelining.ts"
          },
          100,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          123,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          123,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          124,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          132,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          150,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          151,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          155,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          156,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          162,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          175,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          190,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          193,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          196,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "clusterRetryStrategy",
            "type": "cluster/ClusterOptions.ts"
          },
          202,
          "cluster/ClusterOptions.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          26,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          35,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          85,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          86,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          90,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          131,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          138,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          185,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          186,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          190,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          191,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ConnectionPool"
          },
          21,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getNodes",
            "type": "ConnectionPool"
          },
          26,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getNodes",
            "type": "ConnectionPool"
          },
          26,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getSampleInstance",
            "type": "ConnectionPool"
          },
          34,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          44,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          47,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          58,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          58,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          70,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          90,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          92,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          93,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          94,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          98,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          100,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          101,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          115,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          125,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          125,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          132,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          132,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "push",
            "type": "DelayQueue"
          },
          35,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "execute",
            "type": "DelayQueue"
          },
          57,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "execute",
            "type": "DelayQueue"
          },
          57,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          85,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          119,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          120,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          123,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          147,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          148,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          150,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          151,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          153,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          156,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          157,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          163,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          163,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          171,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          194,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          194,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          230,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          255,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          260,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          261,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          262,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          262,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          266,
          "cluster/index.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Cluster"
          },
          292,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          317,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          325,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          329,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          330,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          338,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          339,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          339,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          340,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          341,
          "cluster/index.ts"
        ],
        [
          {
            "name": "duplicate",
            "type": "Cluster"
          },
          368,
          "cluster/index.ts"
        ],
        [
          {
            "name": "duplicate",
            "type": "Cluster"
          },
          369,
          "cluster/index.ts"
        ],
        [
          {
            "name": "autoPipelineQueueSize",
            "type": "Cluster"
          },
          402,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          444,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          453,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          455,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          458,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          462,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          463,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          476,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          479,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          486,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          486,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          495,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          496,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          500,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          504,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          511,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          527,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          530,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          539,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          552,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          560,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          563,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          564,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          584,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          608,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          652,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          657,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          663,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          667,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          670,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          681,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          690,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          693,
          "cluster/index.ts"
        ],
        [
          {
            "name": "clearNodesRefreshInterval",
            "type": "Cluster"
          },
          703,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resetNodesRefreshInterval",
            "type": "Cluster"
          },
          713,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resetNodesRefreshInterval",
            "type": "Cluster"
          },
          718,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resetNodesRefreshInterval",
            "type": "Cluster"
          },
          723,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Cluster"
          },
          732,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Cluster"
          },
          733,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          750,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          758,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          761,
          "cluster/index.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Cluster"
          },
          776,
          "cluster/index.ts"
        ],
        [
          {
            "name": "executeOfflineCommands",
            "type": "Cluster"
          },
          787,
          "cluster/index.ts"
        ],
        [
          {
            "name": "natMapper",
            "type": "Cluster"
          },
          802,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          830,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          832,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          835,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          871,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          872,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          889,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          892,
          "cluster/index.ts"
        ],
        [
          {
            "name": "invokeReadyDelayedCallbacks",
            "type": "Cluster"
          },
          914,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          924,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          933,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          935,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          960,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          960,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          961,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          961,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster::resolveSrv"
          },
          974,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster::resolveSrv"
          },
          977,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1017,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1027,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1028,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1029,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1036,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1037,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1042,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1044,
          "cluster/index.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          32,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          37,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          38,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          38,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          45,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          48,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          50,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          57,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          76,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "groupSrvRecords",
            "type": "cluster/util.ts"
          },
          86,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          103,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          107,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          108,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          111,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          115,
          "cluster/util.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "AbstractConnector"
          },
          28,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "AbstractConnector"
          },
          35,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "AbstractConnector"
          },
          38,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "AbstractConnector"
          },
          38,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          34,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          43,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          45,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          52,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SentinelIterator"
          },
          20,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "reset",
            "type": "SentinelIterator"
          },
          34,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "reset",
            "type": "SentinelIterator"
          },
          34,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "toString",
            "type": "SentinelIterator"
          },
          51,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SentinelConnector"
          },
          71,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          138,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          139,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          140,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          170,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          171,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          172,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          172,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          174,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          175,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          175,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          178,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          196,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          202,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          206,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          214,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          216,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          220,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          220,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          225,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          227,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          245,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          253,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          254,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          262,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          264,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          268,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          268,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          274,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolve",
            "type": "SentinelConnector"
          },
          321,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolve",
            "type": "SentinelConnector"
          },
          330,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          356,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          358,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          361,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          375,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          389,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          391,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          396,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "addressResponseToAddress",
            "type": "connectors/SentinelConnector/index.ts"
          },
          440,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "StandaloneConnector"
          },
          17,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          43,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          54,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          62,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          64,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          71,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterAllFailedError"
          },
          7,
          "errors/ClusterAllFailedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterAllFailedError"
          },
          8,
          "errors/ClusterAllFailedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MaxRetriesPerRequestError"
          },
          7,
          "errors/MaxRetriesPerRequestError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MaxRetriesPerRequestError"
          },
          8,
          "errors/MaxRetriesPerRequestError.ts"
        ],
        [
          {
            "name": "print",
            "type": "index.ts"
          },
          95,
          "index.ts"
        ],
        [
          {
            "name": "print",
            "type": "index.ts"
          },
          97,
          "index.ts"
        ],
        [
          {
            "name": "retryStrategy",
            "type": "redis/RedisOptions.ts"
          },
          205,
          "redis/RedisOptions.ts"
        ],
        [
          {
            "name": "sentinelRetryStrategy",
            "type": "redis/RedisOptions.ts"
          },
          215,
          "redis/RedisOptions.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          23,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          28,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          29,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          33,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          37,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          41,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          45,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          57,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          57,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          65,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          65,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          91,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          91,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          119,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          125,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          126,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          138,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          143,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          144,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          148,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          149,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          199,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          201,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          239,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          239,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          241,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          246,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          248,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          253,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          264,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          264,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          269,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          269,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          280,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          290,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          295,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          304,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          309,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          323,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          328,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          336,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          18,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          26,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          31,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          35,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          36,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          43,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          44,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          52,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          52,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          60,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          66,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          68,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          69,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          70,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          97,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          99,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          106,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          107,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          107,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          108,
          "transaction.ts"
        ],
        [
          {
            "name": "getBuiltinCommands",
            "type": "Commander"
          },
          34,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateFunction",
            "type": "utils/Commander.ts"
          },
          135,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateFunction",
            "type": "utils/Commander.ts"
          },
          139,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateScriptingFunction",
            "type": "utils/Commander.ts"
          },
          178,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          6,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          6,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          7,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          10,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          22,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          25,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          26,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          30,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genRedactedString",
            "type": "utils/debug.ts"
          },
          48,
          "utils/debug.ts"
        ],
        [
          {
            "name": "wrappedDebug",
            "type": "genDebugFunction"
          },
          73,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genDebugFunction",
            "type": "utils/debug.ts"
          },
          76,
          "utils/debug.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          22,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          24,
          "utils/index.ts"
        ],
        [
          {
            "name": "wrapMultiResult",
            "type": "utils/index.ts"
          },
          57,
          "utils/index.ts"
        ],
        [
          {
            "name": "wrapMultiResult",
            "type": "utils/index.ts"
          },
          59,
          "utils/index.ts"
        ],
        [
          {
            "name": "isInt",
            "type": "utils/index.ts"
          },
          82,
          "utils/index.ts"
        ],
        [
          {
            "name": "isInt",
            "type": "utils/index.ts"
          },
          83,
          "utils/index.ts"
        ],
        [
          {
            "name": "timeout",
            "type": "utils/index.ts"
          },
          116,
          "utils/index.ts"
        ],
        [
          {
            "name": "timeout",
            "type": "utils/index.ts"
          },
          118,
          "utils/index.ts"
        ],
        [
          {
            "name": "timeout",
            "type": "utils/index.ts"
          },
          121,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertObjectToArray",
            "type": "utils/index.ts"
          },
          137,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertObjectToArray",
            "type": "utils/index.ts"
          },
          140,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertMapToArray",
            "type": "utils/index.ts"
          },
          156,
          "utils/index.ts"
        ],
        [
          {
            "name": "toArg",
            "type": "utils/index.ts"
          },
          171,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          186,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          190,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          198,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          199,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          211,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          215,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          222,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          223,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          224,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          229,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          242,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          243,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          247,
          "utils/index.ts"
        ],
        [
          {
            "name": "resolveTLSProfile",
            "type": "utils/index.ts"
          },
          269,
          "utils/index.ts"
        ],
        [
          {
            "name": "resolveTLSProfile",
            "type": "utils/index.ts"
          },
          271,
          "utils/index.ts"
        ],
        [
          {
            "name": "sample",
            "type": "utils/index.ts"
          },
          285,
          "utils/index.ts"
        ],
        [
          {
            "name": "sample",
            "type": "utils/index.ts"
          },
          285,
          "utils/index.ts"
        ],
        [
          {
            "name": "shuffle",
            "type": "utils/index.ts"
          },
          297,
          "utils/index.ts"
        ],
        [
          {
            "name": "shuffle",
            "type": "utils/index.ts"
          },
          297,
          "utils/index.ts"
        ],
        [
          {
            "name": "zipMap",
            "type": "utils/index.ts"
          },
          316,
          "utils/index.ts"
        ],
        [
          {
            "name": "zipMap",
            "type": "utils/index.ts"
          },
          317,
          "utils/index.ts"
        ]
      ],
      "version": "codegraph 1.6.0"
    },
    "codegraph-dispatch": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 0.88,
      "declared_unresolved": 551,
      "dispatch_expanded_sites": 2,
      "rows": 412,
      "seconds_breakdown": {
        "adapter_total": 1.18,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "synthesized_rows_skipped": 10,
      "unresolved_sites": [
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          129,
          "Command.ts"
        ],
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          129,
          "Command.ts"
        ],
        [
          {
            "name": "getFlagMap",
            "type": "Command"
          },
          132,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          182,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          197,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          199,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Command"
          },
          202,
          "Command.ts"
        ],
        [
          {
            "name": "getSlot",
            "type": "Command"
          },
          216,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          234,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          255,
          "Command.ts"
        ],
        [
          {
            "name": "toWritable",
            "type": "Command"
          },
          269,
          "Command.ts"
        ],
        [
          {
            "name": "transformReply",
            "type": "Command"
          },
          303,
          "Command.ts"
        ],
        [
          {
            "name": "setTimeout",
            "type": "Command"
          },
          315,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "type": "Command"
          },
          329,
          "Command.ts"
        ],
        [
          {
            "name": "initPromise",
            "type": "Command"
          },
          344,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          355,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          357,
          "Command.ts"
        ],
        [
          {
            "name": "_iterateKeys",
            "type": "Command"
          },
          359,
          "Command.ts"
        ],
        [
          {
            "name": "_convertValue",
            "type": "Command"
          },
          375,
          "Command.ts"
        ],
        [
          {
            "name": "push",
            "type": "MixedBuffers"
          },
          448,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          453,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          456,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          457,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          458,
          "Command.ts"
        ],
        [
          {
            "name": "toBuffer",
            "type": "MixedBuffers"
          },
          459,
          "Command.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "DataHandler"
          },
          59,
          "DataHandler.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "DataHandler"
          },
          60,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          103,
          "DataHandler.ts"
        ],
        [
          {
            "name": "returnReply",
            "type": "DataHandler"
          },
          107,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          118,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          123,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          125,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          131,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          135,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          136,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          143,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          147,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          148,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          154,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          167,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          179,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleSubscriberReply",
            "type": "DataHandler"
          },
          187,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          219,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          220,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          221,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          222,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          225,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          226,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          226,
          "DataHandler.ts"
        ],
        [
          {
            "name": "handleMonitorReply",
            "type": "DataHandler"
          },
          227,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "type": "DataHandler"
          },
          232,
          "DataHandler.ts"
        ],
        [
          {
            "name": "shiftCommand",
            "type": "DataHandler"
          },
          242,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          252,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          253,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          260,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillSubCommand",
            "type": "DataHandler.ts"
          },
          263,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          268,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          269,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          273,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          274,
          "DataHandler.ts"
        ],
        [
          {
            "name": "fillUnsubCommand",
            "type": "DataHandler.ts"
          },
          286,
          "DataHandler.ts"
        ],
        [
          {
            "name": "generateMultiWithNodes",
            "type": "Pipeline.ts"
          },
          18,
          "Pipeline.ts"
        ],
        [
          {
            "name": "generateMultiWithNodes",
            "type": "Pipeline.ts"
          },
          22,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          47,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          52,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          52,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          59,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Pipeline"
          },
          70,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          78,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          126,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          126,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          135,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          160,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          168,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          170,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          174,
          "Pipeline.ts"
        ],
        [
          {
            "name": "fillResult",
            "type": "Pipeline"
          },
          199,
          "Pipeline.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Pipeline"
          },
          210,
          "Pipeline.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Pipeline"
          },
          210,
          "Pipeline.ts"
        ],
        [
          {
            "name": "addBatch",
            "type": "Pipeline"
          },
          228,
          "Pipeline.ts"
        ],
        [
          {
            "name": "addBatch",
            "type": "Pipeline"
          },
          229,
          "Pipeline.ts"
        ],
        [
          {
            "name": "execPipeline",
            "type": "Pipeline.ts"
          },
          362,
          "Pipeline.ts"
        ],
        [
          {
            "name": "execPipeline",
            "type": "Pipeline.ts"
          },
          374,
          "Pipeline.ts"
        ],
        [
          {
            "name": "execPipeline",
            "type": "Pipeline.ts"
          },
          376,
          "Pipeline.ts"
        ],
        [
          {
            "name": "execPipeline",
            "type": "Pipeline.ts"
          },
          376,
          "Pipeline.ts"
        ],
        [
          {
            "name": "execPipeline",
            "type": "Pipeline.ts"
          },
          378,
          "Pipeline.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          124,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          127,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          144,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          144,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Redis"
          },
          153,
          "Redis.ts"
        ],
        [
          {
            "name": "autoPipelineQueueSize",
            "type": "Redis"
          },
          160,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          200,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          206,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          209,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          224,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          231,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          232,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          235,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          240,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          256,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          265,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          267,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          275,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          276,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          279,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          281,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          284,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          285,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          289,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          293,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          296,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          297,
          "Redis.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Redis"
          },
          302,
          "Redis.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Redis"
          },
          317,
          "Redis.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Redis"
          },
          321,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          395,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          397,
          "Redis.ts"
        ],
        [
          {
            "name": "monitor",
            "type": "Redis"
          },
          398,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          425,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          428,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          435,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          451,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          452,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          466,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          476,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          510,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          512,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          515,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          534,
          "Redis.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Redis"
          },
          537,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          546,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          547,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          553,
          "Redis.ts"
        ],
        [
          {
            "name": "setSocketTimeout",
            "type": "Redis"
          },
          554,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          621,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          622,
          "Redis.ts"
        ],
        [
          {
            "name": "silentEmit",
            "type": "Redis"
          },
          625,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          649,
          "Redis.ts"
        ],
        [
          {
            "name": "handleReconnection",
            "type": "Redis"
          },
          668,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          721,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          723,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          724,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          734,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          736,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          739,
          "Redis.ts"
        ],
        [
          {
            "name": "parseOptions",
            "type": "Redis"
          },
          742,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Redis"
          },
          763,
          "Redis.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Redis"
          },
          763,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          786,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          793,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          801,
          "Redis.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Redis"
          },
          804,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          817,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          817,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          819,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          820,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          833,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          835,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          836,
          "Redis.ts"
        ],
        [
          {
            "name": "_readyCheck",
            "type": "Redis"
          },
          854,
          "Redis.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ScanStream"
          },
          20,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          31,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          34,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          37,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          40,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          40,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          43,
          "ScanStream.ts"
        ],
        [
          {
            "name": "_read",
            "type": "ScanStream"
          },
          45,
          "ScanStream.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          15,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          23,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          24,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          26,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          29,
          "Script.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Script"
          },
          30,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          44,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          55,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          56,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          65,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          68,
          "Script.ts"
        ],
        [
          {
            "name": "execute",
            "type": "Script"
          },
          69,
          "Script.ts"
        ],
        [
          {
            "name": "channels",
            "type": "SubscriptionSet"
          },
          25,
          "SubscriptionSet.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          28,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          31,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          45,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          46,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          55,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          56,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          64,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          68,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeAutoPipeline",
            "type": "autoPipelining.ts"
          },
          73,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "shouldUseAutoPipelining",
            "type": "autoPipelining.ts"
          },
          88,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "shouldUseAutoPipelining",
            "type": "autoPipelining.ts"
          },
          89,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "type": "autoPipelining.ts"
          },
          100,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "getFirstValueInFlattenedArray",
            "type": "autoPipelining.ts"
          },
          100,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          123,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          123,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          124,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          132,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          150,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          151,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          155,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          156,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          162,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          175,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          190,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          193,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "executeWithAutoPipelining",
            "type": "autoPipelining.ts"
          },
          196,
          "autoPipelining.ts"
        ],
        [
          {
            "name": "clusterRetryStrategy",
            "type": "cluster/ClusterOptions.ts"
          },
          202,
          "cluster/ClusterOptions.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          26,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterSubscriber"
          },
          35,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          85,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          86,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          90,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          131,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          138,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          164,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          185,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          186,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          190,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "selectSubscriber",
            "type": "ClusterSubscriber"
          },
          191,
          "cluster/ClusterSubscriber.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ConnectionPool"
          },
          21,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getNodes",
            "type": "ConnectionPool"
          },
          26,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getNodes",
            "type": "ConnectionPool"
          },
          26,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "getSampleInstance",
            "type": "ConnectionPool"
          },
          34,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          44,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          47,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          58,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          58,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          70,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          90,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          92,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          93,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          94,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          98,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          100,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "findOrCreate",
            "type": "ConnectionPool"
          },
          101,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          115,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          125,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          125,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          132,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "reset",
            "type": "ConnectionPool"
          },
          132,
          "cluster/ConnectionPool.ts"
        ],
        [
          {
            "name": "push",
            "type": "DelayQueue"
          },
          35,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "execute",
            "type": "DelayQueue"
          },
          57,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "execute",
            "type": "DelayQueue"
          },
          57,
          "cluster/DelayQueue.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          85,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          119,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          120,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          123,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          147,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          148,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          150,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          151,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          153,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          156,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          157,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          163,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          163,
          "cluster/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "Cluster"
          },
          171,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          194,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          194,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          230,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          255,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          260,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          261,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          262,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          262,
          "cluster/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "Cluster"
          },
          266,
          "cluster/index.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "Cluster"
          },
          292,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          317,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          325,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          329,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          330,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          338,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          339,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          339,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          340,
          "cluster/index.ts"
        ],
        [
          {
            "name": "quit",
            "type": "Cluster"
          },
          341,
          "cluster/index.ts"
        ],
        [
          {
            "name": "duplicate",
            "type": "Cluster"
          },
          368,
          "cluster/index.ts"
        ],
        [
          {
            "name": "duplicate",
            "type": "Cluster"
          },
          369,
          "cluster/index.ts"
        ],
        [
          {
            "name": "autoPipelineQueueSize",
            "type": "Cluster"
          },
          402,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          444,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          453,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          455,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          458,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          462,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryNode",
            "type": "Cluster::refreshSlotsCache"
          },
          463,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          476,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          479,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          486,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          486,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          495,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          496,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          500,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          504,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          511,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          527,
          "cluster/index.ts"
        ],
        [
          {
            "name": "sendCommand",
            "type": "Cluster"
          },
          530,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          539,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          552,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          560,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          563,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          564,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          584,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryConnection",
            "type": "Cluster::sendCommand"
          },
          608,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          652,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          657,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          663,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          667,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          670,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          681,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          690,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleError",
            "type": "Cluster"
          },
          693,
          "cluster/index.ts"
        ],
        [
          {
            "name": "clearNodesRefreshInterval",
            "type": "Cluster"
          },
          703,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resetNodesRefreshInterval",
            "type": "Cluster"
          },
          713,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resetNodesRefreshInterval",
            "type": "Cluster"
          },
          718,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resetNodesRefreshInterval",
            "type": "Cluster"
          },
          723,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Cluster"
          },
          732,
          "cluster/index.ts"
        ],
        [
          {
            "name": "setStatus",
            "type": "Cluster"
          },
          733,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          750,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          758,
          "cluster/index.ts"
        ],
        [
          {
            "name": "handleCloseEvent",
            "type": "Cluster"
          },
          761,
          "cluster/index.ts"
        ],
        [
          {
            "name": "flushQueue",
            "type": "Cluster"
          },
          776,
          "cluster/index.ts"
        ],
        [
          {
            "name": "executeOfflineCommands",
            "type": "Cluster"
          },
          787,
          "cluster/index.ts"
        ],
        [
          {
            "name": "natMapper",
            "type": "Cluster"
          },
          802,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          830,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          832,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          835,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          871,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          872,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          889,
          "cluster/index.ts"
        ],
        [
          {
            "name": "getInfoFromNode",
            "type": "Cluster"
          },
          892,
          "cluster/index.ts"
        ],
        [
          {
            "name": "invokeReadyDelayedCallbacks",
            "type": "Cluster"
          },
          914,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          924,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          933,
          "cluster/index.ts"
        ],
        [
          {
            "name": "readyCheck",
            "type": "Cluster"
          },
          935,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          960,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          960,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          961,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveSrv",
            "type": "Cluster"
          },
          961,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster::resolveSrv"
          },
          974,
          "cluster/index.ts"
        ],
        [
          {
            "name": "tryFirstOne",
            "type": "Cluster::resolveSrv"
          },
          977,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1017,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1027,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1028,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1029,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1036,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1037,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1042,
          "cluster/index.ts"
        ],
        [
          {
            "name": "resolveStartupNodeHostnames",
            "type": "Cluster"
          },
          1044,
          "cluster/index.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          32,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          37,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          38,
          "cluster/util.ts"
        ],
        [
          {
            "name": "nodeKeyToRedisOptions",
            "type": "cluster/util.ts"
          },
          38,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          45,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          48,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          50,
          "cluster/util.ts"
        ],
        [
          {
            "name": "normalizeNodeOptions",
            "type": "cluster/util.ts"
          },
          57,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          76,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "getUniqueHostnamesFromOptions",
            "type": "cluster/util.ts"
          },
          80,
          "cluster/util.ts"
        ],
        [
          {
            "name": "groupSrvRecords",
            "type": "cluster/util.ts"
          },
          86,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          103,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          107,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          108,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          111,
          "cluster/util.ts"
        ],
        [
          {
            "name": "weightSrvRecords",
            "type": "cluster/util.ts"
          },
          115,
          "cluster/util.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "AbstractConnector"
          },
          28,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "AbstractConnector"
          },
          35,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "AbstractConnector"
          },
          38,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "disconnect",
            "type": "AbstractConnector"
          },
          38,
          "connectors/AbstractConnector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          34,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          43,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          45,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "subscribe",
            "type": "FailoverDetector"
          },
          52,
          "connectors/SentinelConnector/FailoverDetector.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SentinelIterator"
          },
          20,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "reset",
            "type": "SentinelIterator"
          },
          34,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "reset",
            "type": "SentinelIterator"
          },
          34,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "toString",
            "type": "SentinelIterator"
          },
          51,
          "connectors/SentinelConnector/SentinelIterator.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SentinelConnector"
          },
          71,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          138,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          139,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          140,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          170,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          171,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          172,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          172,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          174,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          175,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          175,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          178,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          196,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          202,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "connect",
            "type": "SentinelConnector"
          },
          206,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          214,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          216,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          220,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          220,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          225,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "updateSentinels",
            "type": "SentinelConnector"
          },
          227,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          245,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          253,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveMaster",
            "type": "SentinelConnector"
          },
          254,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          262,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          264,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          268,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          268,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolveSlave",
            "type": "SentinelConnector"
          },
          274,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolve",
            "type": "SentinelConnector"
          },
          321,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "resolve",
            "type": "SentinelConnector"
          },
          330,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          356,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          358,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          361,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "initFailoverDetector",
            "type": "SentinelConnector"
          },
          375,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          389,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          391,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "selectPreferredSentinel",
            "type": "connectors/SentinelConnector/index.ts"
          },
          396,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "addressResponseToAddress",
            "type": "connectors/SentinelConnector/index.ts"
          },
          440,
          "connectors/SentinelConnector/index.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "StandaloneConnector"
          },
          17,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          43,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          54,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          62,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          64,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "connect",
            "type": "StandaloneConnector"
          },
          71,
          "connectors/StandaloneConnector.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterAllFailedError"
          },
          7,
          "errors/ClusterAllFailedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ClusterAllFailedError"
          },
          8,
          "errors/ClusterAllFailedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MaxRetriesPerRequestError"
          },
          7,
          "errors/MaxRetriesPerRequestError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MaxRetriesPerRequestError"
          },
          8,
          "errors/MaxRetriesPerRequestError.ts"
        ],
        [
          {
            "name": "print",
            "type": "index.ts"
          },
          95,
          "index.ts"
        ],
        [
          {
            "name": "print",
            "type": "index.ts"
          },
          97,
          "index.ts"
        ],
        [
          {
            "name": "retryStrategy",
            "type": "redis/RedisOptions.ts"
          },
          205,
          "redis/RedisOptions.ts"
        ],
        [
          {
            "name": "sentinelRetryStrategy",
            "type": "redis/RedisOptions.ts"
          },
          215,
          "redis/RedisOptions.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          23,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          28,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          29,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          33,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          37,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          41,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          45,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          57,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          57,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          65,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          65,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          91,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "connectHandler",
            "type": "redis/event_handler.ts"
          },
          91,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          119,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          125,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortIncompletePipelines",
            "type": "redis/event_handler.ts"
          },
          126,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          138,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          143,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          144,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          148,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "abortTransactionFragments",
            "type": "redis/event_handler.ts"
          },
          149,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          199,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "closeHandler",
            "type": "redis/event_handler.ts"
          },
          201,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          239,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          239,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          241,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          246,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          248,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          253,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          264,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          264,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          269,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          269,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          280,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          290,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          295,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          304,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          309,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          323,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          328,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "readyHandler",
            "type": "redis/event_handler.ts"
          },
          336,
          "redis/event_handler.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          18,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          26,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          31,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          35,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          36,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          43,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          44,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          52,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          52,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          60,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          66,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          68,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          69,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          70,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          97,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          99,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          106,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          107,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          107,
          "transaction.ts"
        ],
        [
          {
            "name": "addTransactionSupport",
            "type": "transaction.ts"
          },
          108,
          "transaction.ts"
        ],
        [
          {
            "name": "getBuiltinCommands",
            "type": "Commander"
          },
          34,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateFunction",
            "type": "utils/Commander.ts"
          },
          135,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateFunction",
            "type": "utils/Commander.ts"
          },
          139,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "generateScriptingFunction",
            "type": "utils/Commander.ts"
          },
          178,
          "utils/Commander.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          6,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          6,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          7,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "applyMixin",
            "type": "utils/applyMixin.ts"
          },
          10,
          "utils/applyMixin.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          22,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          25,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          26,
          "utils/debug.ts"
        ],
        [
          {
            "name": "getStringValue",
            "type": "utils/debug.ts"
          },
          30,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genRedactedString",
            "type": "utils/debug.ts"
          },
          48,
          "utils/debug.ts"
        ],
        [
          {
            "name": "wrappedDebug",
            "type": "genDebugFunction"
          },
          73,
          "utils/debug.ts"
        ],
        [
          {
            "name": "genDebugFunction",
            "type": "utils/debug.ts"
          },
          76,
          "utils/debug.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          22,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertBufferToString",
            "type": "utils/index.ts"
          },
          24,
          "utils/index.ts"
        ],
        [
          {
            "name": "wrapMultiResult",
            "type": "utils/index.ts"
          },
          57,
          "utils/index.ts"
        ],
        [
          {
            "name": "wrapMultiResult",
            "type": "utils/index.ts"
          },
          59,
          "utils/index.ts"
        ],
        [
          {
            "name": "isInt",
            "type": "utils/index.ts"
          },
          82,
          "utils/index.ts"
        ],
        [
          {
            "name": "isInt",
            "type": "utils/index.ts"
          },
          83,
          "utils/index.ts"
        ],
        [
          {
            "name": "timeout",
            "type": "utils/index.ts"
          },
          116,
          "utils/index.ts"
        ],
        [
          {
            "name": "timeout",
            "type": "utils/index.ts"
          },
          118,
          "utils/index.ts"
        ],
        [
          {
            "name": "timeout",
            "type": "utils/index.ts"
          },
          121,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertObjectToArray",
            "type": "utils/index.ts"
          },
          137,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertObjectToArray",
            "type": "utils/index.ts"
          },
          140,
          "utils/index.ts"
        ],
        [
          {
            "name": "convertMapToArray",
            "type": "utils/index.ts"
          },
          156,
          "utils/index.ts"
        ],
        [
          {
            "name": "toArg",
            "type": "utils/index.ts"
          },
          171,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          186,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          190,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          198,
          "utils/index.ts"
        ],
        [
          {
            "name": "optimizeErrorStack",
            "type": "utils/index.ts"
          },
          199,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          211,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          215,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          222,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          223,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          224,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          229,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          242,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          243,
          "utils/index.ts"
        ],
        [
          {
            "name": "parseURL",
            "type": "utils/index.ts"
          },
          247,
          "utils/index.ts"
        ],
        [
          {
            "name": "resolveTLSProfile",
            "type": "utils/index.ts"
          },
          269,
          "utils/index.ts"
        ],
        [
          {
            "name": "resolveTLSProfile",
            "type": "utils/index.ts"
          },
          271,
          "utils/index.ts"
        ],
        [
          {
            "name": "sample",
            "type": "utils/index.ts"
          },
          285,
          "utils/index.ts"
        ],
        [
          {
            "name": "sample",
            "type": "utils/index.ts"
          },
          285,
          "utils/index.ts"
        ],
        [
          {
            "name": "shuffle",
            "type": "utils/index.ts"
          },
          297,
          "utils/index.ts"
        ],
        [
          {
            "name": "shuffle",
            "type": "utils/index.ts"
          },
          297,
          "utils/index.ts"
        ],
        [
          {
            "name": "zipMap",
            "type": "utils/index.ts"
          },
          316,
          "utils/index.ts"
        ],
        [
          {
            "name": "zipMap",
            "type": "utils/index.ts"
          },
          317,
          "utils/index.ts"
        ]
      ],
      "version": "codegraph 1.6.0"
    },
    "codeql": {
      "build": "source only",
      "cache": "hit",
      "cold_seconds": 6.89,
      "rows": 622,
      "seconds_breakdown": {
        "adapter_total": 23.16,
        "own": 7.54,
        "shared": 9.46,
        "staging": null
      },
      "source": ".work/typescript/ioredis/codeql/q.csv",
      "version": "codeql 2.23.8 javascript-all 2.6.18"
    },
    "gitnexus": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 9.57,
      "rows": 269,
      "seconds_breakdown": {
        "adapter_total": 20.23,
        "export": 1.24,
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
      "rows": 286,
      "seconds_breakdown": {
        "adapter_total": 2.04,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/ioredis/gfy/src/graphify-out/graph.json",
      "version": "graphifyy 0.9.58"
    },
    "ideal": {
      "build": "oracle",
      "null_model": true,
      "reference": "ideal",
      "rows": 308,
      "version": "the correct answer for every link group (a ceiling, not a tool)"
    }
  },
  "tsx": "4.19.2",
  "typescript": "5.6.3"
}
```
