# TypeScript call-graph benchmark — `type-graphql`

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
| application types | 195 |
| application methods | 209 |
| call sites the checker resolved | 613 |
| … application-internal | 292 |
| … leaving the application (not scored, see §7) | 283 |
| … through a function value, target not statically known (not scored) | 38 |
| call expressions the checker could NOT resolve — no row of any kind; every recall denominator is short by this many, for every tool alike (#53) | 66 |
| … i.e. the checker resolved this % of the subject's call expressions (gate 0's floor is 55%) | 90.3 |
| … and this % resolve to a target INSIDE the subject — the scorable share; a library target clears the floor without adding one (#67) | 48.8 |
| **CERTAIN** edges (declared targets) — `recall_certain` denominator | 257 |
| **POSSIBLE** edges (declared-heritage + checker-assignable envelope — NOT sound, structural typing) — `recall_possible` denominator | 256 |
| **RTA** edges (instantiated-types envelope) — `recall_rta` denominator | 207 |
| link groups `(caller, callee-name)`, at Tier B | 253 |
| … **uniquely linked** (exactly one possible target) — the headline denominator | 250 |
| … uniquely linked at Tier A (overloads kept apart) | 250 |
| … genuinely ambiguous (dispatch admits several) | 3 |

Call sites by instruction: `CALL` 565, `NEW` 48.

## Headline — Tier B (`type#name`)

Tier B is the highest fidelity **every** tool under test can express, so it is the only tier
at which the whole field is comparable. The ground truth is projected to Tier B as well, so a
tool that cannot spell parameter types is not being asked to.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 2s | 0.954 | 0.955 | 0.899 | 0.898 | 0.874 | 0.926 | 0.926 | 242 | 3 (0 ambig, 0 out-of-scope, 0 unspellable, 3 §4-excluded), 37 duplicate |
| `code-review-graph` | source only | 2s | 0.716 | 0.717 | 0.642 | 0.641 | 0.638 | 0.678 | 0.676 | 230 | 327 (0 ambig, 312 out-of-scope, 53% of emitted, 11 unspellable, 4 §4-excluded), 99 duplicate |
| `code-review-graph-dispatch` | source only | 2s | 0.716 | 0.717 | 0.642 | 0.641 | 0.638 | 0.678 | 0.676 | 230 | 327 (0 ambig, 312 out-of-scope, 53% of emitted, 11 unspellable, 4 §4-excluded), 99 duplicate |
| `codegraph` | source only | 1s | 0.949 | 0.949 | 0.872 | 0.875 | 0.874 | 0.909 | 0.909 | 236 | 13 (0 ambig, 10 out-of-scope, 3% of emitted, 0 unspellable, 3 §4-excluded), 43 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.949 | 0.949 | 0.872 | 0.875 | 0.874 | 0.909 | 0.909 | 236 | 13 (0 ambig, 10 out-of-scope, 3% of emitted, 0 unspellable, 3 §4-excluded), 43 duplicate |
| `codeql` | source only | 14s | 0.921 | 0.921 | 0.903 | 0.906 | 0.908 | 0.912 | 0.911 | 252 | 23 (0 ambig, 0 out-of-scope, 0 unspellable, 23 §4-excluded), 48 duplicate |
| `gitnexus` | source only | 21s | 1.000 | 1.000 | 0.424 | 0.422 | 0.459 | 0.596 | 0.650 | 109 | 17 (0 ambig, 13 out-of-scope, 10% of emitted, 0 unspellable, 4 §4-excluded), 11 duplicate |
| `graphify` | source only | 1s | 0.943 | 0.943 | 0.774 | 0.777 | 0.894 | 0.850 | 0.853 | 211 | 2 (0 ambig, 0 out-of-scope, 0 unspellable, 2 §4-excluded) |
| *`cha-null`* | bytecode | 0s | 1.000 | 1.000 | 0.996 | 1.000 | 1.000 | 0.998 | 0.998 | 256 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 257 | 0 |

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

- `code-review-graph`: 0 rows named a type that matches more than one application type, 312 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `code-review-graph-dispatch`: 0 rows named a type that matches more than one application type, 312 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codegraph`: 0 rows named a type that matches more than one application type, 10 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codegraph-dispatch`: 0 rows named a type that matches more than one application type, 10 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `gitnexus`: 0 rows named a type that matches more than one application type, 13 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.

## Uniquely-linked call resolution — the number that separates the tools

Of the 250 link groups where the language admits **exactly one**
target, what did each tool actually return? A set where one answer exists is not a win, and a
wrong single answer is worse than an honest set — so the five outcomes are kept apart rather
than folded into one rate.

| tool | exact | over_fan | partial | polluted | ancestor | wrong | unknown | unplaced | missed | n | exact rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | 224 | 0 | 0 | 0 | 0 | 0 | 8 | 0 | 18 | 250 | 89.6% |
| `cha-null` | 250 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 250 | 100.0% |
| `code-review-graph` | 164 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 84 | 250 | 65.6% |
| `code-review-graph-dispatch` | 164 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 84 | 250 | 65.6% |
| `codegraph` | 218 | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 28 | 250 | 87.2% |
| `codegraph-dispatch` | 218 | 0 | 0 | 0 | 0 | 0 | 2 | 2 | 28 | 250 | 87.2% |
| `codeql` | 227 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 23 | 250 | 90.8% |
| `gitnexus` | 102 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 148 | 250 | 40.8% |
| `graphify` | 193 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 57 | 250 | 77.2% |
| `ideal` | 250 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 250 | 100.0% |

`exact` the one right method, alone · `over_fan` right method plus others, all sound ·
`polluted` right method plus something no envelope admits · `ancestor` named only a supertype
that declares the member (weaker, not fabricated) · `wrong` answered, none of it defensible ·
`missed` returned nothing.

## Genuinely ambiguous call resolution

The other 3 groups, where dispatch really does admit several
targets. Here `over_fan` is the *correct* behaviour and `exact` may mean the tool guessed one
branch and dropped the rest — so this table is read differently from the one above, and that
is exactly why they are not combined.

3 of these groups (6 call sites) are not dispatch either: several one-target
calls of the same name in one method — `new A()` and `new B()`, `getProject()` on two receivers —
pooled under one key (#70). Each call has exactly one target; a tool that names some of them
but not all reads `partial` here, all of them `exact`.

| tool | exact | over_fan | partial | polluted | ancestor | wrong | unknown | unplaced | missed | n | exact rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 100.0% |
| `cha-null` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 100.0% |
| `code-review-graph` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 3 | 0.0% |
| `code-review-graph-dispatch` | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 3 | 0.0% |
| `codegraph` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 100.0% |
| `codegraph-dispatch` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 100.0% |
| `codeql` | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 66.7% |
| `gitnexus` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 100.0% |
| `graphify` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 100.0% |
| `ideal` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 100.0% |

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
| `axiom` | source only | 0.899 | 1.000 | 0.996 | 0.90× | 0.810 | 1.000 | 0.990 | 0.81× | 0.763 | 1.000 | 0.983 | 0.76× |
| `code-review-graph` | source only | 0.642 | 0.982 | 0.976 | 0.65× | 0.613 | 0.986 | 0.973 | 0.62× | 0.599 | 0.985 | 0.964 | 0.61× |
| `code-review-graph-dispatch` | source only | 0.642 | 0.982 | 0.976 | 0.65× | 0.613 | 0.986 | 0.973 | 0.62× | 0.599 | 0.985 | 0.964 | 0.61× |
| `codegraph` | source only | 0.872 | 0.949 | 0.949 | 0.92× | 0.838 | 0.910 | 0.910 | 0.92× | 0.839 | 0.877 | 0.877 | 0.96× |
| `codegraph-dispatch` | source only | 0.872 | 0.949 | 0.949 | 0.92× | 0.838 | 0.910 | 0.910 | 0.92× | 0.839 | 0.877 | 0.877 | 0.96× |
| `codeql` | source only | 0.903 | 1.000 | 1.000 | 0.90× | 0.872 | 1.000 | 1.000 | 0.87× | 0.866 | 1.000 | 1.000 | 0.87× |
| `gitnexus` | source only | 0.424 | 1.000 | 0.991 | 0.42× | 0.344 | 1.000 | 0.988 | 0.34× | 0.280 | 1.000 | 0.990 | 0.28× |
| `graphify` | source only | 0.774 | 0.943 | 0.943 | 0.82× | 0.774 | 0.905 | 0.905 | 0.85× | 0.773 | 0.869 | 0.869 | 0.89× |
| *`cha-null`* | bytecode | 0.996 | 1.000 | 1.000 | 1.00× | 0.991 | 1.000 | 1.000 | 0.99× | 0.987 | 1.000 | 1.000 | 0.99× |
| *`ideal`* | oracle | 1.000 | 1.000 | 0.996 | 1.00× | 1.000 | 1.000 | 0.992 | 1.00× | 1.000 | 1.000 | 0.987 | 1.00× |

## Tier A (`type#name(params)`) — overload selection

Only tools whose output carries parameter types can be scored here. A dash is **not** a zero:
it means the tool's output format does not express the distinction, so the question was never
put to it.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 2s | 0.453 | 0.455 | 0.436 | 0.434 | 0.469 | 0.445 | 0.442 | 246 | 3 (0 ambig, 0 out-of-scope, 0 unspellable, 3 §4-excluded), 37 duplicate |
| `code-review-graph` | source only | 2s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `code-review-graph-dispatch` | source only | 2s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `codegraph` | source only | 1s | 0.926 | 0.926 | 0.735 | 0.738 | 0.705 | 0.820 | 0.825 | 204 | 47 (0 ambig, 10 out-of-scope, 3% of emitted, 34 unspellable, 3 §4-excluded), 43 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.926 | 0.926 | 0.735 | 0.738 | 0.705 | 0.820 | 0.825 | 204 | 47 (0 ambig, 10 out-of-scope, 3% of emitted, 34 unspellable, 3 §4-excluded), 43 duplicate |
| `codeql` | source only | 14s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `gitnexus` | source only | 21s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `graphify` | source only | 1s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| *`cha-null`* | bytecode | 0s | 1.000 | 1.000 | 0.996 | 1.000 | 1.000 | 0.998 | 0.998 | 256 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 257 | 0 |

## Tier C (`name`) — the floor

Method name only, no owner. Reported so that a name-only tool has a number at all. Read it
knowing that any two same-named methods in the subject are indistinguishable here, which
inflates every tool's score — the link-group table is **not** reported at this tier, because
its key is the callee name and every tool would score 100% by construction.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 2s | 0.970 | 0.970 | 0.930 | 0.930 | 0.914 | 0.950 | 0.949 | 234 | 3 (0 ambig, 0 out-of-scope, 0 unspellable, 3 §4-excluded), 37 duplicate |
| `code-review-graph` | source only | 2s | 0.707 | 0.707 | 0.672 | 0.672 | 0.667 | 0.689 | 0.686 | 232 | 316 (0 ambig, 312 out-of-scope, 53% of emitted, 0 unspellable, 4 §4-excluded), 99 duplicate |
| `code-review-graph-dispatch` | source only | 2s | 0.707 | 0.707 | 0.672 | 0.672 | 0.667 | 0.689 | 0.686 | 232 | 316 (0 ambig, 312 out-of-scope, 53% of emitted, 0 unspellable, 4 §4-excluded), 99 duplicate |
| `codegraph` | source only | 1s | 0.948 | 0.948 | 0.906 | 0.906 | 0.899 | 0.927 | 0.926 | 233 | 13 (0 ambig, 10 out-of-scope, 3% of emitted, 0 unspellable, 3 §4-excluded), 43 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.948 | 0.948 | 0.906 | 0.906 | 0.899 | 0.927 | 0.926 | 233 | 13 (0 ambig, 10 out-of-scope, 3% of emitted, 0 unspellable, 3 §4-excluded), 43 duplicate |
| `codeql` | source only | 14s | 0.968 | 0.968 | 0.992 | 0.992 | 0.990 | 0.980 | 0.980 | 250 | 23 (0 ambig, 0 out-of-scope, 0 unspellable, 23 §4-excluded), 48 duplicate |
| `gitnexus` | source only | 21s | 1.000 | 1.000 | 0.430 | 0.430 | 0.465 | 0.602 | 0.654 | 105 | 17 (0 ambig, 13 out-of-scope, 10% of emitted, 0 unspellable, 4 §4-excluded), 11 duplicate |
| `graphify` | source only | 1s | 0.942 | 0.942 | 0.803 | 0.803 | 0.919 | 0.867 | 0.869 | 208 | 2 (0 ambig, 0 out-of-scope, 0 unspellable, 2 §4-excluded) |
| *`cha-null`* | bytecode | 0s | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 244 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 244 | 0 |

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
| `axiom` | `known_edge` | 279 | 0.954 | 0.954 | 224 | 0 | 0 | 0 | 0 |
| `axiom` | `multi_inferred` | 2 | 1.000 | 1.000 | 0 | 0 | 0 | 0 | 0 |
| `code-review-graph` | `extracted` | 588 | 0.716 | 0.717 | 164 | 0 | 0 | 0 | 0 |
| `code-review-graph-dispatch` | `extracted` | 588 | 0.716 | 0.717 | 164 | 0 | 0 | 0 | 0 |
| `codegraph` | `calls|exact-match` | 117 | 0.947 | 0.947 | 89 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.90` | 117 | 0.947 | 0.947 | 89 | 0 | 0 | 0 | 0 |
| `codegraph` | `calls|import` | 129 | 0.944 | 0.944 | 101 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|import:0.90` | 129 | 0.944 | 0.944 | 101 | 0 | 0 | 0 | 0 |
| `codegraph` | `calls|instance-method` | 7 | 0.750 | 0.750 | 2 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.70` | 6 | 0.667 | 0.667 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.90` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
| `codegraph` | `instantiates|exact-match` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.90` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
| `codegraph` | `instantiates|import` | 36 | 1.000 | 1.000 | 26 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|import:0.90` | 36 | 1.000 | 1.000 | 26 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|exact-match` | 117 | 0.947 | 0.947 | 89 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.90` | 117 | 0.947 | 0.947 | 89 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|import` | 129 | 0.944 | 0.944 | 101 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|import:0.90` | 129 | 0.944 | 0.944 | 101 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|instance-method` | 7 | 0.750 | 0.750 | 2 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.70` | 6 | 0.667 | 0.667 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `calls|instance-method:0.90` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `instantiates|exact-match` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.90` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `instantiates|import` | 36 | 1.000 | 1.000 | 26 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|import:0.90` | 36 | 1.000 | 1.000 | 26 | 0 | 0 | 0 | 0 |
| `codeql` | `imprecision=0` | 323 | 0.921 | 0.921 | 227 | 0 | 0 | 0 | 0 |
| `gitnexus` | `callable-value-flow` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `callable-value-flow:0.80` | 1 | 1.000 | 1.000 | 1 | 0 | 0 | 0 | 0 |
| `gitnexus` | `global` | 23 | 1.000 | 1.000 | 14 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `global:0.85` | 23 | 1.000 | 1.000 | 14 | 0 | 0 | 0 | 0 |
| `gitnexus` | `import-resolved` | 70 | 1.000 | 1.000 | 62 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `import-resolved:0.85` | 70 | 1.000 | 1.000 | 62 | 0 | 0 | 0 | 0 |
| `gitnexus` | `local-call` | 28 | 1.000 | 1.000 | 25 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `local-call:0.85` | 28 | 1.000 | 1.000 | 25 | 0 | 0 | 0 | 0 |
| `gitnexus` | `property-dispatch` | 10 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `property-dispatch:0.70` | 10 | — | — | 0 | 0 | 0 | 0 | 0 |
| `graphify` | `extracted` | 211 | 0.943 | 0.943 | 191 | 0 | 0 | 0 | 0 |
| `graphify` | `inferred` | 2 | 1.000 | 1.000 | 2 | 0 | 0 | 0 | 0 |

- `axiom` wrote 390 rows labelled `ambiguous_unknown` with no target — the tool says it could not resolve the call (read as `unknown`, not `missed`, #69), not scored
- `axiom` wrote 1 rows labelled `intrinsic_terminal` with no target — a language intrinsic with no method body, not scored

## Provenance

```json
{
  "input_sha256": {
    "classes": "c95d92e1d8db4fabfa738ad99eb8e85d897b18e3bf886c45406e9e18e8c963b1",
    "edges/axiom": "34482fa64b9bade461b0f844f9b05483ca88e17ed8a43adfd976e6efee1a5df9",
    "edges/cha-null": "9236c73eb8aea31306f6fea598a2d53d3e2f6eaec39e4e13bb924e90d1cd15e4",
    "edges/code-review-graph": "852bc0a8f3cb4bfa9a2494ec92f30446d02c00e8c938506f45576d9a7411ec37",
    "edges/code-review-graph-dispatch": "1a7c7c38b577337aea92e03b7429bb8b8b808d8a2c530113e54c2f3c23b12163",
    "edges/codegraph": "38969a9d6ba08a4667608a9939ed7b2ba71dd4cc24fef998cf03388148105555",
    "edges/codegraph-dispatch": "1193a1d4924651c55d76d7ff3970ee3677b9c5fa3ec25d3cb842e88d1a9333ef",
    "edges/codeql": "42540fe707f8888ba6fb43d7844cced3399d0fa1be138f18198d788b81219771",
    "edges/gitnexus": "699fa460dd42aa4349682d0f6d34504a53f3d2d36e9f48eb86fdfeb72aa3d446",
    "edges/graphify": "53b4fb59235db650ba60bac8f418e3eea13797653953614eafa994d152df4363",
    "edges/ideal": "018d92ebcf194e5a42c82f7670e5640fe9e1e5d8cdf46035fd0bb1905cf2e668",
    "excluded": "ee60dc789a833c3c8d1bf3563e17bffc064a46b5e60aa77012bdfeef91900a6d",
    "heritage": "b086818609699ed9ddd1f1dac24d59931fe93120fb7f052b67196af5c0e21c72",
    "methods": "56bd121a0e89eb23acab0c9d1ae28743137a5a4b00bd23f36ce9c8e3060ea64c",
    "sites": "4a151d749254d4aebcac74c9320385bd6e1d311ba94e8b2dba22eb03a8ea157d"
  },
  "language": "typescript",
  "platform": "Linux x86_64",
  "python": "3.12.3",
  "staged_copy": {
    "files": 115,
    "sha256": "e49670a3148c49a0a05727806fdc7a9fe2190e2727a7b84e52999805190233c3"
  },
  "subject": "type-graphql",
  "tools": {
    "axiom": {
      "build": "source only",
      "cache": "hit",
      "cold_seconds": 0.86,
      "engine_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "function_type_targets_dropped": 11,
      "note": "typescript front end, empty library",
      "parser_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "rows": 281,
      "rows_by_status": {
        "ambiguous_unknown": 390,
        "intrinsic_terminal": 1,
        "known_edge": 290,
        "multi_inferred": 2
      },
      "rows_without_method": 391,
      "seconds_breakdown": {
        "adapter_total": 1.92,
        "own": 0.7,
        "shared": 1.0,
        "staging": null
      },
      "source": ".work/typescript/type-graphql/axiom/out/raw/call-chain-edges.csv",
      "unresolved_sites": [
        [
          {
            "name": "getArrayFromOverloadedRest",
            "params": [
              "Array<T | readonly T[]>"
            ],
            "type": "helpers/decorators"
          },
          39,
          "helpers/decorators.ts"
        ],
        [
          {
            "name": "getType",
            "params": [],
            "type": "helpers/findType"
          },
          71,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "convertToType",
            "params": [
              "any",
              "object"
            ],
            "type": "helpers/types"
          },
          97,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "params": [
              "any",
              "object"
            ],
            "type": "helpers/types"
          },
          105,
          "helpers/types.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "params": [
              "TypeValue"
            ],
            "type": "resolvers/convert-args"
          },
          33,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "params": [
              "TransformationTree",
              "any"
            ],
            "type": "resolvers/convert-args"
          },
          89,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "inputFields",
            "params": [
              "",
              ""
            ],
            "type": "resolvers/convert-args"
          },
          102,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertValuesToInstances",
            "params": [
              "TypeValue",
              "any"
            ],
            "type": "resolvers/convert-args"
          },
          128,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "getParams",
            "params": [
              "ParamMetadata[]",
              "ResolverData<any>",
              "ValidateSettings",
              "ValidatorFn | undefined"
            ],
            "type": "resolvers/helpers"
          },
          84,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "validateArg",
            "params": [
              "any | undefined",
              "TypeValue",
              "ResolverData",
              "ValidateSettings",
              "ValidateSettings | undefined",
              "ValidatorFn | undefined",
              "ValidatorFn | undefined"
            ],
            "type": "resolvers/validate-arg"
          },
          46,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          779,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "Field",
            "params": [
              "",
              "",
              ""
            ],
            "type": "decorators/Field"
          },
          31,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "Field",
            "params": [
              "",
              "",
              ""
            ],
            "type": "decorators/Field"
          },
          32,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "InterfaceType",
            "params": [
              "string | InterfaceTypeOptions",
              "InterfaceTypeOptions"
            ],
            "type": "decorators/InterfaceType"
          },
          27,
          "decorators/InterfaceType.ts"
        ],
        [
          {
            "name": "ObjectType",
            "params": [
              "string | ObjectTypeOptions",
              "ObjectTypeOptions"
            ],
            "type": "decorators/ObjectType"
          },
          19,
          "decorators/ObjectType.ts"
        ],
        [
          {
            "name": "Resolver",
            "params": [],
            "type": "decorators/Resolver"
          },
          16,
          "decorators/Resolver.ts"
        ],
        [
          {
            "name": "Subscription",
            "params": [
              "",
              ""
            ],
            "type": "decorators/Subscription"
          },
          40,
          "decorators/Subscription.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "\"input\" | \"output\"",
              "string",
              "string",
              "number",
              "string"
            ],
            "type": "errors/CannotDetermineGraphQLTypeError#CannotDetermineGraphQLTypeError"
          },
          20,
          "errors/CannotDetermineGraphQLTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "\"input\" | \"output\"",
              "string",
              "string",
              "number",
              "string"
            ],
            "type": "errors/CannotDetermineGraphQLTypeError#CannotDetermineGraphQLTypeError"
          },
          21,
          "errors/CannotDetermineGraphQLTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "string",
              "unknown",
              "unknown"
            ],
            "type": "errors/ConflictingDefaultValuesError#ConflictingDefaultValuesError"
          },
          8,
          "errors/ConflictingDefaultValuesError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "string",
              "unknown",
              "unknown"
            ],
            "type": "errors/ConflictingDefaultValuesError#ConflictingDefaultValuesError"
          },
          14,
          "errors/ConflictingDefaultValuesError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "readonly GraphQLError[]"
            ],
            "type": "errors/GeneratingSchemaError#GeneratingSchemaError"
          },
          8,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "readonly GraphQLError[]"
            ],
            "type": "errors/GeneratingSchemaError#GeneratingSchemaError"
          },
          11,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "readonly GraphQLError[]"
            ],
            "type": "errors/GeneratingSchemaError#GeneratingSchemaError"
          },
          12,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClassMetadata"
            ],
            "type": "errors/InterfaceResolveTypeError#InterfaceResolveTypeError"
          },
          5,
          "errors/InterfaceResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ClassMetadata"
            ],
            "type": "errors/InterfaceResolveTypeError#InterfaceResolveTypeError"
          },
          10,
          "errors/InterfaceResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string"
            ],
            "type": "errors/InvalidDirectiveError#InvalidDirectiveError"
          },
          3,
          "errors/InvalidDirectiveError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string"
            ],
            "type": "errors/InvalidDirectiveError#InvalidDirectiveError"
          },
          4,
          "errors/InvalidDirectiveError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [],
            "type": "errors/MissingPubSubError#MissingPubSubError"
          },
          3,
          "errors/MissingPubSubError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [],
            "type": "errors/MissingPubSubError#MissingPubSubError"
          },
          8,
          "errors/MissingPubSubError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "Function",
              "string"
            ],
            "type": "errors/MissingSubscriptionTopicsError#MissingSubscriptionTopicsError"
          },
          3,
          "errors/MissingSubscriptionTopicsError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "Function",
              "string"
            ],
            "type": "errors/MissingSubscriptionTopicsError#MissingSubscriptionTopicsError"
          },
          5,
          "errors/MissingSubscriptionTopicsError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "string",
              "number",
              "string"
            ],
            "type": "errors/NoExplicitTypeError#NoExplicitTypeError"
          },
          12,
          "errors/NoExplicitTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "string",
              "number",
              "string"
            ],
            "type": "errors/NoExplicitTypeError#NoExplicitTypeError"
          },
          14,
          "errors/NoExplicitTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [],
            "type": "errors/ReflectMetadataMissingError#ReflectMetadataMissingError"
          },
          3,
          "errors/ReflectMetadataMissingError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [],
            "type": "errors/ReflectMetadataMissingError#ReflectMetadataMissingError"
          },
          8,
          "errors/ReflectMetadataMissingError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [],
            "type": "errors/SymbolKeysNotSupportedError#SymbolKeysNotSupportedError"
          },
          3,
          "errors/SymbolKeysNotSupportedError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [],
            "type": "errors/SymbolKeysNotSupportedError#SymbolKeysNotSupportedError"
          },
          5,
          "errors/SymbolKeysNotSupportedError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "UnionMetadata"
            ],
            "type": "errors/UnionResolveTypeError#UnionResolveTypeError"
          },
          5,
          "errors/UnionResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "UnionMetadata"
            ],
            "type": "errors/UnionResolveTypeError#UnionResolveTypeError"
          },
          10,
          "errors/UnionResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "string"
            ],
            "type": "errors/UnmetGraphQLPeerDependencyError#UnmetGraphQLPeerDependencyError"
          },
          3,
          "errors/UnmetGraphQLPeerDependencyError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "string"
            ],
            "type": "errors/UnmetGraphQLPeerDependencyError#UnmetGraphQLPeerDependencyError"
          },
          9,
          "errors/UnmetGraphQLPeerDependencyError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "string",
              "boolean | NullableListOptions | undefined"
            ],
            "type": "errors/WrongNullableListOptionError#WrongNullableListOptionError"
          },
          9,
          "errors/WrongNullableListOptionError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "string",
              "string",
              "boolean | NullableListOptions | undefined"
            ],
            "type": "errors/WrongNullableListOptionError#WrongNullableListOptionError"
          },
          14,
          "errors/WrongNullableListOptionError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ValidationError[]"
            ],
            "type": "errors/graphql/ArgumentValidationError#ArgumentValidationError"
          },
          14,
          "errors/graphql/ArgumentValidationError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              "ValidationError[]"
            ],
            "type": "errors/graphql/ArgumentValidationError#ArgumentValidationError"
          },
          21,
          "errors/graphql/ArgumentValidationError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "errors/graphql/AuthenticationError#AuthenticationError"
          },
          10,
          "errors/graphql/AuthenticationError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "errors/graphql/AuthenticationError#AuthenticationError"
          },
          16,
          "errors/graphql/AuthenticationError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "errors/graphql/AuthorizationError#AuthorizationError"
          },
          10,
          "errors/graphql/AuthorizationError.ts"
        ],
        [
          {
            "name": "constructor",
            "params": [
              ""
            ],
            "type": "errors/graphql/AuthorizationError#AuthorizationError"
          },
          16,
          "errors/graphql/AuthorizationError.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "params": [
              "",
              ""
            ],
            "type": "helpers/auth-middleware"
          },
          16,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "params": [
              "",
              ""
            ],
            "type": "helpers/auth-middleware"
          },
          29,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "outputFile",
            "params": [
              "string",
              "any"
            ],
            "type": "helpers/filesystem"
          },
          7,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "params": [
              "string",
              "any"
            ],
            "type": "helpers/filesystem"
          },
          12,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "params": [
              "string",
              "any"
            ],
            "type": "helpers/filesystem"
          },
          12,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "params": [
              "string",
              "any"
            ],
            "type": "helpers/filesystem"
          },
          13,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "params": [
              "string",
              "any"
            ],
            "type": "helpers/filesystem"
          },
          19,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "params": [
              "string",
              "any"
            ],
            "type": "helpers/filesystem"
          },
          24,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "params": [
              "string",
              "any"
            ],
            "type": "helpers/filesystem"
          },
          24,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "params": [
              "string",
              "any"
            ],
            "type": "helpers/filesystem"
          },
          25,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "findTypeValueArrayDepth",
            "params": [
              "RecursiveArray<TypeValue>",
              "RecursiveArray<TypeValue>",
              ""
            ],
            "type": "helpers/findType"
          },
          33,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "params": [
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams"
            ],
            "type": "helpers/findType"
          },
          51,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "params": [
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams"
            ],
            "type": "helpers/findType"
          },
          64,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "params": [
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams",
              "GetTypeParams"
            ],
            "type": "helpers/findType"
          },
          90,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "wrapTypeInNestedList",
            "params": [
              "GraphQLType",
              "number",
              "boolean"
            ],
            "type": "helpers/types"
          },
          20,
          "helpers/types.ts"
        ],
        [
          {
            "name": "wrapTypeInNestedList",
            "params": [
              "GraphQLType",
              "number",
              "boolean"
            ],
            "type": "helpers/types"
          },
          25,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertTypeIfScalar",
            "params": [
              "any"
            ],
            "type": "helpers/types"
          },
          32,
          "helpers/types.ts"
        ],
        [
          {
            "name": "wrapWithTypeOptions",
            "params": [
              "Function",
              "string",
              "T",
              "TypeOptions",
              "boolean"
            ],
            "type": "helpers/types"
          },
          80,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "params": [
              "any",
              "object"
            ],
            "type": "helpers/types"
          },
          106,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "params": [
              "any",
              "object"
            ],
            "type": "helpers/types"
          },
          109,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "params": [
              "any",
              "object"
            ],
            "type": "helpers/types"
          },
          109,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "params": [
              "T"
            ],
            "type": "helpers/types"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "params": [
              "T"
            ],
            "type": "helpers/types"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "enumKeys",
            "params": [
              ""
            ],
            "type": "helpers/types"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "enumKeys",
            "params": [
              ""
            ],
            "type": "helpers/types"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "params": [
              "T"
            ],
            "type": "helpers/types"
          },
          114,
          "helpers/types.ts"
        ],
        [
          {
            "name": "collectQueryHandlerMetadata",
            "params": [
              "ResolverMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          84,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectMutationHandlerMetadata",
            "params": [
              "ResolverMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          88,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectSubscriptionHandlerMetadata",
            "params": [
              "SubscriptionResolverMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          92,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectFieldResolverMetadata",
            "params": [
              "FieldResolverMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          96,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectObjectMetadata",
            "params": [
              "ObjectClassMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          100,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectInputMetadata",
            "params": [
              "ClassMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          104,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectArgsMetadata",
            "params": [
              "ClassMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          108,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectInterfaceMetadata",
            "params": [
              "InterfaceClassMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          112,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectAuthorizedFieldMetadata",
            "params": [
              "AuthorizedMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          116,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectAuthorizedResolverMetadata",
            "params": [
              "AuthorizedClassMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          120,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectEnumMetadata",
            "params": [
              "EnumMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          124,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectUnionMetadata",
            "params": [
              "UnionMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          128,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectUnionMetadata",
            "params": [
              "UnionMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          129,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectMiddlewareMetadata",
            "params": [
              "MiddlewareMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          137,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectResolverMiddlewareMetadata",
            "params": [
              "ResolverMiddlewareMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          141,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectResolverClassMetadata",
            "params": [
              "ResolverClassMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          145,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectClassFieldMetadata",
            "params": [
              "FieldMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          149,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectHandlerParamMetadata",
            "params": [
              "ParamMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          153,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveClassMetadata",
            "params": [
              "DirectiveClassMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          157,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveFieldMetadata",
            "params": [
              "DirectiveFieldMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          161,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveArgumentMetadata",
            "params": [
              "DirectiveArgumentMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          165,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectExtensionsClassMetadata",
            "params": [
              "ExtensionsClassMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          169,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectExtensionsFieldMetadata",
            "params": [
              "ExtensionsFieldMetadata"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          173,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          177,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          178,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          179,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          180,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          181,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "params": [
              "ClassMetadata[]"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          224,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          226,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          227,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          229,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          234,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          237,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          243,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          243,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          251,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          251,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "params": [
              "BaseResolverMetadata[]"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          262,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          263,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          267,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          273,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          276,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          282,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          282,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              "FieldResolverMetadata[]",
              "SchemaGeneratorOptions"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          294,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          296,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          296,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          302,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          305,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          305,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          308,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          309,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          311,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          316,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          322,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          325,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          347,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "params": [],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          365,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          366,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          371,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          382,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findFieldRoles",
            "params": [
              "Function",
              "string"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          389,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findFieldRoles",
            "params": [
              "Function",
              "string"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          391,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "params": [
              "Function",
              "string"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          402,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "params": [
              "Function",
              "string"
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          402,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "params": [
              ""
            ],
            "type": "metadata/metadata-storage#MetadataStorage"
          },
          405,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "mapSuperResolverHandlers",
            "params": [
              "T[]",
              "Function",
              "ResolverClassMetadata"
            ],
            "type": "metadata/utils"
          },
          16,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapSuperFieldResolverHandlers",
            "params": [
              "FieldResolverMetadata[]",
              "Function",
              "ResolverClassMetadata"
            ],
            "type": "metadata/utils"
          },
          34,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "params": [
              "ResolverMiddlewareMetadata[]"
            ],
            "type": "metadata/utils"
          },
          49,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "params": [
              "ResolverMiddlewareMetadata[]"
            ],
            "type": "metadata/utils"
          },
          49,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "params": [
              "",
              ""
            ],
            "type": "metadata/utils"
          },
          53,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "resolvers/convert-args"
          },
          22,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "getInputType",
            "params": [
              "TypeValue"
            ],
            "type": "resolvers/convert-args"
          },
          25,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "getArgsType",
            "params": [
              "TypeValue"
            ],
            "type": "resolvers/convert-args"
          },
          29,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "params": [
              "TypeValue"
            ],
            "type": "resolvers/convert-args"
          },
          34,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "params": [
              "TypeValue"
            ],
            "type": "resolvers/convert-args"
          },
          39,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "params": [
              "ClassMetadata"
            ],
            "type": "resolvers/convert-args"
          },
          45,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "params": [
              "ClassMetadata"
            ],
            "type": "resolvers/convert-args"
          },
          50,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "params": [
              "ClassMetadata"
            ],
            "type": "resolvers/convert-args"
          },
          50,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "params": [
              "ClassMetadata"
            ],
            "type": "resolvers/convert-args"
          },
          51,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "superFields",
            "params": [
              ""
            ],
            "type": "resolvers/convert-args"
          },
          52,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "params": [
              "ClassMetadata"
            ],
            "type": "resolvers/convert-args"
          },
          56,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "resolvers/convert-args"
          },
          62,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "resolvers/convert-args"
          },
          63,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "params": [
              "TypeValue"
            ],
            "type": "resolvers/convert-args"
          },
          80,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "params": [
              "TransformationTree",
              "any"
            ],
            "type": "resolvers/convert-args"
          },
          91,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "params": [
              "TransformationTree",
              "any"
            ],
            "type": "resolvers/convert-args"
          },
          94,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "inputFields",
            "params": [
              "",
              ""
            ],
            "type": "resolvers/convert-args"
          },
          104,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertValuesToInstances",
            "params": [
              "TypeValue",
              "any"
            ],
            "type": "resolvers/convert-args"
          },
          130,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "params": [
              "ArgsParamMetadata",
              "ArgsDictionary"
            ],
            "type": "resolvers/convert-args"
          },
          140,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "params": [
              "ArgsParamMetadata",
              "ArgsDictionary"
            ],
            "type": "resolvers/convert-args"
          },
          146,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "params": [
              "ArgsParamMetadata",
              "ArgsDictionary"
            ],
            "type": "resolvers/convert-args"
          },
          149,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "transformedFields",
            "params": [
              "",
              ""
            ],
            "type": "resolvers/convert-args"
          },
          153,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "params": [
              "BaseResolverMetadata"
            ],
            "type": "resolvers/create"
          },
          26,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "params": [
              "",
              "",
              "",
              ""
            ],
            "type": "resolvers/create"
          },
          36,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "params": [],
            "type": "resolvers/create"
          },
          45,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "params": [
              ""
            ],
            "type": "resolvers/create"
          },
          47,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "params": [],
            "type": "resolvers/create"
          },
          51,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "params": [],
            "type": "resolvers/create"
          },
          64,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "params": [
              ""
            ],
            "type": "resolvers/create"
          },
          66,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "params": [],
            "type": "resolvers/create"
          },
          70,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "params": [
              "FieldResolverMetadata"
            ],
            "type": "resolvers/create"
          },
          82,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "params": [
              "FieldResolverMetadata"
            ],
            "type": "resolvers/create"
          },
          91,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "params": [],
            "type": "resolvers/create"
          },
          111,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "params": [
              ""
            ],
            "type": "resolvers/create"
          },
          112,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "params": [],
            "type": "resolvers/create"
          },
          115,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createBasicFieldResolver",
            "params": [
              "FieldMetadata"
            ],
            "type": "resolvers/create"
          },
          124,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "wrapResolverWithAuthChecker",
            "params": [],
            "type": "resolvers/create"
          },
          150,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "getParams",
            "params": [
              "ParamMetadata[]",
              "ResolverData<any>",
              "ValidateSettings",
              "ValidatorFn | undefined"
            ],
            "type": "resolvers/helpers"
          },
          18,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "params": [
              "ParamMetadata[]",
              "ResolverData<any>",
              "ValidateSettings",
              "ValidatorFn | undefined"
            ],
            "type": "resolvers/helpers"
          },
          18,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramValues",
            "params": [
              ""
            ],
            "type": "resolvers/helpers"
          },
          26,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramValues",
            "params": [
              ""
            ],
            "type": "resolvers/helpers"
          },
          37,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramValues",
            "params": [
              ""
            ],
            "type": "resolvers/helpers"
          },
          59,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramValues",
            "params": [
              ""
            ],
            "type": "resolvers/helpers"
          },
          68,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramValues",
            "params": [
              ""
            ],
            "type": "resolvers/helpers"
          },
          70,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramValues",
            "params": [],
            "type": "resolvers/helpers"
          },
          76,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramValues",
            "params": [
              ""
            ],
            "type": "resolvers/helpers"
          },
          78,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "params": [
              "ParamMetadata[]",
              "ResolverData<any>",
              "ValidateSettings",
              "ValidatorFn | undefined"
            ],
            "type": "resolvers/helpers"
          },
          85,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "applyAuthChecker",
            "params": [
              "Array<Middleware<any>>",
              "AuthChecker<any, any> | undefined",
              "IOCContainer",
              "AuthMode",
              "any[] | undefined"
            ],
            "type": "resolvers/helpers"
          },
          98,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "dispatchHandler",
            "params": [
              "number"
            ],
            "type": "resolvers/helpers"
          },
          114,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "dispatchHandler",
            "params": [
              "number"
            ],
            "type": "resolvers/helpers"
          },
          128,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "validateArg",
            "params": [
              "any | undefined",
              "TypeValue",
              "ResolverData",
              "ValidateSettings",
              "ValidateSettings | undefined",
              "ValidatorFn | undefined",
              "ValidatorFn | undefined"
            ],
            "type": "resolvers/validate-arg"
          },
          23,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "params": [
              "any | undefined",
              "TypeValue",
              "ResolverData",
              "ValidateSettings",
              "ValidateSettings | undefined",
              "ValidatorFn | undefined",
              "ValidatorFn | undefined"
            ],
            "type": "resolvers/validate-arg"
          },
          47,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "params": [
              "any | undefined",
              "TypeValue",
              "ResolverData",
              "ValidateSettings",
              "ValidateSettings | undefined",
              "ValidatorFn | undefined",
              "ValidatorFn | undefined"
            ],
            "type": "resolvers/validate-arg"
          },
          48,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "params": [
              "any | undefined",
              "TypeValue",
              "ResolverData",
              "ValidateSettings",
              "ValidateSettings | undefined",
              "ValidatorFn | undefined",
              "ValidatorFn | undefined"
            ],
            "type": "resolvers/validate-arg"
          },
          48,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "params": [
              ""
            ],
            "type": "resolvers/validate-arg"
          },
          50,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "params": [
              "any | undefined",
              "TypeValue",
              "ResolverData",
              "ValidateSettings",
              "ValidateSettings | undefined",
              "ValidatorFn | undefined",
              "ValidatorFn | undefined"
            ],
            "type": "resolvers/validate-arg"
          },
          53,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "params": [
              "DirectiveMetadata"
            ],
            "type": "schema/definition-node"
          },
          22,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "params": [
              "DirectiveMetadata"
            ],
            "type": "schema/definition-node"
          },
          22,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "params": [
              "DirectiveMetadata"
            ],
            "type": "schema/definition-node"
          },
          31,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "params": [
              "DirectiveMetadata"
            ],
            "type": "schema/definition-node"
          },
          38,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "params": [
              "DirectiveMetadata"
            ],
            "type": "schema/definition-node"
          },
          38,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "schema/definition-node"
          },
          44,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "params": [
              "DirectiveMetadata"
            ],
            "type": "schema/definition-node"
          },
          51,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "params": [
              "DirectiveMetadata"
            ],
            "type": "schema/definition-node"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "params": [
              "DirectiveMetadata"
            ],
            "type": "schema/definition-node"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "params": [
              "DirectiveMetadata"
            ],
            "type": "schema/definition-node"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getObjectTypeDefinitionNode",
            "params": [
              "string",
              "DirectiveMetadata[]"
            ],
            "type": "schema/definition-node"
          },
          91,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputObjectTypeDefinitionNode",
            "params": [
              "string",
              "DirectiveMetadata[]"
            ],
            "type": "schema/definition-node"
          },
          110,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getFieldDefinitionNode",
            "params": [
              "string",
              "GraphQLOutputType",
              "DirectiveMetadata[]"
            ],
            "type": "schema/definition-node"
          },
          136,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getFieldDefinitionNode",
            "params": [
              "string",
              "GraphQLOutputType",
              "DirectiveMetadata[]"
            ],
            "type": "schema/definition-node"
          },
          129,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputValueDefinitionNode",
            "params": [
              "string",
              "GraphQLInputType",
              "DirectiveMetadata[]"
            ],
            "type": "schema/definition-node"
          },
          162,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputValueDefinitionNode",
            "params": [
              "string",
              "GraphQLInputType",
              "DirectiveMetadata[]"
            ],
            "type": "schema/definition-node"
          },
          155,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInterfaceTypeDefinitionNode",
            "params": [
              "string",
              "DirectiveMetadata[]"
            ],
            "type": "schema/definition-node"
          },
          181,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "schema/schema-generator"
          },
          120,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          125,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          134,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          140,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          141,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          147,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          150,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          150,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "checkForErrors",
            "params": [
              "SchemaGeneratorOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          162,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          198,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          203,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          204,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          204,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          207,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          210,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          214,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          219,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          225,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          225,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          232,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          241,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          245,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          248,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          248,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          262,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          263,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          267,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          268,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          275,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          281,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaces",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          282,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaces",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          286,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          298,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          299,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          299,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          299,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          309,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "implementedInterfaces",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          310,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          312,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          313,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          317,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          319,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          322,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filteredFieldResolversMetadata",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          323,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          325,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          326,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          328,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          331,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          344,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          378,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          380,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          383,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          390,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          390,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          394,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          397,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "implementingObjectTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          398,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          404,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          481,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          409,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaces",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          411,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          417,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          418,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          418,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          418,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          428,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "implementedInterfacesMetadata",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          429,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          431,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          432,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          436,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          438,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          440,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fieldResolverMetadata",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          442,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          445,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          448,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          454,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          483,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          489,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          499,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          500,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          502,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          507,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          510,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          515,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          517,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          524,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "fields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          524,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildRootQueryType",
            "params": [
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          560,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildRootMutationType",
            "params": [
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          575,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildRootSubscriptionType",
            "params": [
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          590,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "params": [
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          597,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "autoRegisteredObjectTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          598,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "autoRegisteredObjectTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          599,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "autoRegisteredObjectTypesInfo",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          608,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "params": [
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          618,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "params": [
              "ResolverMetadata[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          625,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          626,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          629,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          635,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "params": [
              "SubscriptionResolverMetadata[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          663,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "params": [
              "",
              "",
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          674,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "params": [
              "",
              "",
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          683,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "params": [
              "",
              "",
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          687,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "params": [
              "",
              "",
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          690,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "params": [
              "",
              "",
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          696,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "params": [
              "",
              "",
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          697,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "params": [
              "",
              "",
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          705,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "params": [
              "",
              "",
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          707,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          709,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "Function",
              "string",
              "ParamMetadata[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          732,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          736,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          739,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          744,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          744,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          761,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "argumentType",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          762,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          765,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          775,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          777,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          780,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "params": [
              "",
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          784,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "mapArgFields",
            "params": [
              "ClassMetadata",
              "GraphQLFieldConfigArgumentMap"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          796,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "mapArgFields",
            "params": [
              "ClassMetadata",
              "GraphQLFieldConfigArgumentMap"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          797,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "mapArgFields",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          798,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "mapArgFields",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          804,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "mapArgFields",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          804,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "params": [
              "Function",
              "string",
              "TypeValue",
              "TypeOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          829,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "params": [
              "Function",
              "string",
              "TypeValue",
              "TypeOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          835,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "params": [
              "Function",
              "string",
              "TypeValue",
              "TypeOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          837,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "params": [
              "Function",
              "string",
              "TypeValue",
              "TypeOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          842,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "params": [
              "Function",
              "string",
              "TypeValue",
              "TypeOptions"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          848,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLInputType",
            "params": [
              "Function",
              "string",
              "TypeValue",
              "TypeOptions",
              "number",
              "string"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          872,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLInputType",
            "params": [
              "Function",
              "string",
              "TypeValue",
              "TypeOptions",
              "number",
              "string"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          878,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getResolveTypeFunction",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          906,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterHandlersByResolvers",
            "params": [
              "T[]",
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          915,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterHandlersByResolvers",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          915,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "params": [
              "Array<ObjectTypeInfo | InterfaceTypeInfo | InputObjectTypeInfo>",
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "params": [
              "Array<ObjectTypeInfo | InterfaceTypeInfo | InputObjectTypeInfo>",
              "Function[]"
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "params": [
              ""
            ],
            "type": "schema/schema-generator#SchemaGenerator"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "params": [
              "GraphQLInputObjectType"
            ],
            "type": "schema/utils"
          },
          11,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "params": [
              "GraphQLInputObjectType"
            ],
            "type": "schema/utils"
          },
          12,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "params": [
              "GraphQLInputObjectType"
            ],
            "type": "schema/utils"
          },
          12,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "params": [
              "GraphQLObjectType | GraphQLInterfaceType"
            ],
            "type": "schema/utils"
          },
          30,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "params": [
              "GraphQLObjectType | GraphQLInterfaceType"
            ],
            "type": "schema/utils"
          },
          31,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "params": [
              "GraphQLObjectType | GraphQLInterfaceType"
            ],
            "type": "schema/utils"
          },
          31,
          "schema/utils.ts"
        ],
        [
          {
            "name": "typeFields",
            "params": [
              "",
              ""
            ],
            "type": "schema/utils"
          },
          37,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getEmitSchemaDefinitionFileOptions",
            "params": [
              "BuildSchemaOptions"
            ],
            "type": "utils/buildSchema"
          },
          20,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "getEmitSchemaDefinitionFileOptions",
            "params": [
              "BuildSchemaOptions"
            ],
            "type": "utils/buildSchema"
          },
          20,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "loadResolvers",
            "params": [
              "BuildSchemaOptions"
            ],
            "type": "utils/buildSchema"
          },
          40,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "createTypeDefsAndResolversMap",
            "params": [
              "GraphQLSchema"
            ],
            "type": "utils/buildTypeDefsAndResolvers"
          },
          6,
          "utils/buildTypeDefsAndResolvers.ts"
        ],
        [
          {
            "name": "get",
            "params": [
              "SupportedType<T>"
            ],
            "type": "utils/container#DefaultContainer"
          },
          23,
          "utils/container.ts"
        ],
        [
          {
            "name": "get",
            "params": [
              "SupportedType<T>"
            ],
            "type": "utils/container#DefaultContainer"
          },
          25,
          "utils/container.ts"
        ],
        [
          {
            "name": "get",
            "params": [
              "SupportedType<T>"
            ],
            "type": "utils/container#DefaultContainer"
          },
          26,
          "utils/container.ts"
        ],
        [
          {
            "name": "generateTypeResolver",
            "params": [
              "GraphQLAbstractType",
              "GraphQLSchema"
            ],
            "type": "utils/createResolversMap"
          },
          23,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateTypeResolver",
            "params": [
              "",
              "",
              ""
            ],
            "type": "utils/createResolversMap"
          },
          27,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateFieldsResolvers",
            "params": [
              "GraphQLFieldMap<any, any>"
            ],
            "type": "utils/createResolversMap"
          },
          36,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateFieldsResolvers",
            "params": [
              "GraphQLFieldMap<any, any>"
            ],
            "type": "utils/createResolversMap"
          },
          36,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "params": [
              "GraphQLSchema"
            ],
            "type": "utils/createResolversMap"
          },
          51,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "params": [
              "GraphQLSchema"
            ],
            "type": "utils/createResolversMap"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "params": [
              "GraphQLSchema"
            ],
            "type": "utils/createResolversMap"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "params": [
              "GraphQLSchema"
            ],
            "type": "utils/createResolversMap"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "params": [
              ""
            ],
            "type": "utils/createResolversMap"
          },
          53,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "params": [
              "",
              ""
            ],
            "type": "utils/createResolversMap"
          },
          61,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "params": [
              "",
              ""
            ],
            "type": "utils/createResolversMap"
          },
          67,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "params": [
              "",
              ""
            ],
            "type": "utils/createResolversMap"
          },
          74,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "params": [
              "",
              ""
            ],
            "type": "utils/createResolversMap"
          },
          75,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "getSchemaFileContent",
            "params": [
              "GraphQLSchema",
              "PrintSchemaOptions"
            ],
            "type": "utils/emitSchemaDefinitionFile"
          },
          21,
          "utils/emitSchemaDefinitionFile.ts"
        ],
        [
          {
            "name": "getSchemaFileContent",
            "params": [
              "GraphQLSchema",
              "PrintSchemaOptions"
            ],
            "type": "utils/emitSchemaDefinitionFile"
          },
          22,
          "utils/emitSchemaDefinitionFile.ts"
        ],
        [
          {
            "name": "ensureInstalledCorrectGraphQLPackage",
            "params": [],
            "type": "utils/graphql-version"
          },
          10,
          "utils/graphql-version.ts"
        ]
      ]
    },
    "cha-null": {
      "build": "bytecode",
      "null_model": true,
      "reference": "null",
      "rows": 256,
      "version": "CHA envelope (no resolution)"
    },
    "code-review-graph": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 1.09,
      "declared_unresolved": 367,
      "fanned_rows": 0,
      "rows": 588,
      "seconds_breakdown": {
        "adapter_total": 1.63,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/type-graphql/crg/data/graph.db",
      "unresolved_sites": [
        [
          {
            "name": "Arg",
            "type": "decorators/Arg.ts"
          },
          34,
          "decorators/Arg.ts"
        ],
        [
          {
            "name": "Args",
            "type": "decorators/Args.ts"
          },
          19,
          "decorators/Args.ts"
        ],
        [
          {
            "name": "target",
            "type": "decorators/ArgsType.ts"
          },
          5,
          "decorators/ArgsType.ts"
        ],
        [
          {
            "name": "Authorized",
            "type": "decorators/Authorized.ts"
          },
          22,
          "decorators/Authorized.ts"
        ],
        [
          {
            "name": "Authorized",
            "type": "decorators/Authorized.ts"
          },
          33,
          "decorators/Authorized.ts"
        ],
        [
          {
            "name": "Ctx",
            "type": "decorators/Ctx.ts"
          },
          11,
          "decorators/Ctx.ts"
        ],
        [
          {
            "name": "Directive",
            "type": "decorators/Directive.ts"
          },
          23,
          "decorators/Directive.ts"
        ],
        [
          {
            "name": "Directive",
            "type": "decorators/Directive.ts"
          },
          30,
          "decorators/Directive.ts"
        ],
        [
          {
            "name": "Directive",
            "type": "decorators/Directive.ts"
          },
          37,
          "decorators/Directive.ts"
        ],
        [
          {
            "name": "Extensions",
            "type": "decorators/Extensions.ts"
          },
          15,
          "decorators/Extensions.ts"
        ],
        [
          {
            "name": "Extensions",
            "type": "decorators/Extensions.ts"
          },
          21,
          "decorators/Extensions.ts"
        ],
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          31,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          32,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          42,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          55,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "FieldResolver",
            "type": "decorators/FieldResolver.ts"
          },
          50,
          "decorators/FieldResolver.ts"
        ],
        [
          {
            "name": "Info",
            "type": "decorators/Info.ts"
          },
          11,
          "decorators/Info.ts"
        ],
        [
          {
            "name": "target",
            "type": "decorators/InputType.ts"
          },
          16,
          "decorators/InputType.ts"
        ],
        [
          {
            "name": "InterfaceType",
            "type": "decorators/InterfaceType.ts"
          },
          27,
          "decorators/InterfaceType.ts"
        ],
        [
          {
            "name": "target",
            "type": "decorators/InterfaceType.ts"
          },
          29,
          "decorators/InterfaceType.ts"
        ],
        [
          {
            "name": "Mutation",
            "type": "decorators/Mutation.ts"
          },
          19,
          "decorators/Mutation.ts"
        ],
        [
          {
            "name": "ObjectType",
            "type": "decorators/ObjectType.ts"
          },
          19,
          "decorators/ObjectType.ts"
        ],
        [
          {
            "name": "target",
            "type": "decorators/ObjectType.ts"
          },
          22,
          "decorators/ObjectType.ts"
        ],
        [
          {
            "name": "Query",
            "type": "decorators/Query.ts"
          },
          16,
          "decorators/Query.ts"
        ],
        [
          {
            "name": "target",
            "type": "decorators/Resolver.ts"
          },
          20,
          "decorators/Resolver.ts"
        ],
        [
          {
            "name": "Root",
            "type": "decorators/Root.ts"
          },
          26,
          "decorators/Root.ts"
        ],
        [
          {
            "name": "Subscription",
            "type": "decorators/Subscription.ts"
          },
          40,
          "decorators/Subscription.ts"
        ],
        [
          {
            "name": "Subscription",
            "type": "decorators/Subscription.ts"
          },
          43,
          "decorators/Subscription.ts"
        ],
        [
          {
            "name": "UseMiddleware",
            "type": "decorators/UseMiddleware.ts"
          },
          20,
          "decorators/UseMiddleware.ts"
        ],
        [
          {
            "name": "UseMiddleware",
            "type": "decorators/UseMiddleware.ts"
          },
          31,
          "decorators/UseMiddleware.ts"
        ],
        [
          {
            "name": "createParameterDecorator",
            "type": "decorators/createParameterDecorator.ts"
          },
          48,
          "decorators/createParameterDecorator.ts"
        ],
        [
          {
            "name": "registerEnumType",
            "type": "decorators/enums.ts"
          },
          8,
          "decorators/enums.ts"
        ],
        [
          {
            "name": "createUnionType",
            "type": "decorators/unions.ts"
          },
          21,
          "decorators/unions.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "CannotDetermineGraphQLTypeError"
          },
          21,
          "errors/CannotDetermineGraphQLTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ConflictingDefaultValuesError"
          },
          14,
          "errors/ConflictingDefaultValuesError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "GeneratingSchemaError"
          },
          8,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "GeneratingSchemaError"
          },
          12,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InterfaceResolveTypeError"
          },
          10,
          "errors/InterfaceResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InvalidDirectiveError"
          },
          4,
          "errors/InvalidDirectiveError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingPubSubError"
          },
          8,
          "errors/MissingPubSubError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingSubscriptionTopicsError"
          },
          5,
          "errors/MissingSubscriptionTopicsError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "NoExplicitTypeError"
          },
          14,
          "errors/NoExplicitTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ReflectMetadataMissingError"
          },
          8,
          "errors/ReflectMetadataMissingError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SymbolKeysNotSupportedError"
          },
          5,
          "errors/SymbolKeysNotSupportedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnionResolveTypeError"
          },
          10,
          "errors/UnionResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnmetGraphQLPeerDependencyError"
          },
          9,
          "errors/UnmetGraphQLPeerDependencyError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "WrongNullableListOptionError"
          },
          14,
          "errors/WrongNullableListOptionError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ArgumentValidationError"
          },
          21,
          "errors/graphql/ArgumentValidationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthenticationError"
          },
          16,
          "errors/graphql/AuthenticationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthorizationError"
          },
          16,
          "errors/graphql/AuthorizationError.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "type": "helpers/auth-middleware.ts"
          },
          16,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "type": "helpers/auth-middleware.ts"
          },
          29,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "getArrayFromOverloadedRest",
            "type": "helpers/decorators.ts"
          },
          39,
          "helpers/decorators.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          7,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          12,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          12,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          13,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          19,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          24,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          24,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          25,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "findTypeValueArrayDepth",
            "type": "helpers/findType.ts"
          },
          33,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "type": "helpers/findType.ts"
          },
          51,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "type": "helpers/findType.ts"
          },
          64,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "getType",
            "type": "helpers/findType.ts"
          },
          70,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "getType",
            "type": "helpers/findType.ts"
          },
          71,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "isThrowing",
            "type": "helpers/isThrowing.ts"
          },
          3,
          "helpers/isThrowing.ts"
        ],
        [
          {
            "name": "convertTypeIfScalar",
            "type": "helpers/types.ts"
          },
          32,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          97,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          105,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          106,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          109,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "key",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "key",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          114,
          "helpers/types.ts"
        ],
        [
          {
            "name": "collectQueryHandlerMetadata",
            "type": "MetadataStorage"
          },
          84,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectMutationHandlerMetadata",
            "type": "MetadataStorage"
          },
          88,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectSubscriptionHandlerMetadata",
            "type": "MetadataStorage"
          },
          92,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          96,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectObjectMetadata",
            "type": "MetadataStorage"
          },
          100,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectInputMetadata",
            "type": "MetadataStorage"
          },
          104,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectArgsMetadata",
            "type": "MetadataStorage"
          },
          108,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectInterfaceMetadata",
            "type": "MetadataStorage"
          },
          112,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectAuthorizedFieldMetadata",
            "type": "MetadataStorage"
          },
          116,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectAuthorizedResolverMetadata",
            "type": "MetadataStorage"
          },
          120,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectEnumMetadata",
            "type": "MetadataStorage"
          },
          124,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectUnionMetadata",
            "type": "MetadataStorage"
          },
          128,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectUnionMetadata",
            "type": "MetadataStorage"
          },
          129,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectMiddlewareMetadata",
            "type": "MetadataStorage"
          },
          137,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectResolverMiddlewareMetadata",
            "type": "MetadataStorage"
          },
          141,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectResolverClassMetadata",
            "type": "MetadataStorage"
          },
          145,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectClassFieldMetadata",
            "type": "MetadataStorage"
          },
          149,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectHandlerParamMetadata",
            "type": "MetadataStorage"
          },
          153,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveClassMetadata",
            "type": "MetadataStorage"
          },
          157,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveFieldMetadata",
            "type": "MetadataStorage"
          },
          161,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveArgumentMetadata",
            "type": "MetadataStorage"
          },
          165,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectExtensionsClassMetadata",
            "type": "MetadataStorage"
          },
          169,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectExtensionsFieldMetadata",
            "type": "MetadataStorage"
          },
          173,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          177,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          178,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          179,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          180,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          181,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "type": "MetadataStorage"
          },
          224,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          226,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          227,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "field",
            "type": "MetadataStorage"
          },
          229,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "field",
            "type": "MetadataStorage"
          },
          234,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "field",
            "type": "MetadataStorage"
          },
          237,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "field",
            "type": "MetadataStorage"
          },
          243,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "field",
            "type": "MetadataStorage"
          },
          243,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          251,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          251,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "type": "MetadataStorage"
          },
          262,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          263,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          267,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          273,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          276,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          282,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          282,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          294,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          296,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          296,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          302,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          305,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          308,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          309,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          316,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          322,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "resolverCls",
            "type": "MetadataStorage"
          },
          325,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          347,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "type": "MetadataStorage"
          },
          365,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          366,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          371,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          382,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findFieldRoles",
            "type": "MetadataStorage"
          },
          389,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findFieldRoles",
            "type": "MetadataStorage"
          },
          391,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "type": "MetadataStorage"
          },
          402,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "type": "MetadataStorage"
          },
          402,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "entry",
            "type": "MetadataStorage"
          },
          405,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "mapSuperResolverHandlers",
            "type": "metadata/utils.ts"
          },
          16,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapSuperFieldResolverHandlers",
            "type": "metadata/utils.ts"
          },
          34,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          49,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          49,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          53,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "getInputType",
            "type": "resolvers/convert-args.ts"
          },
          25,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "getArgsType",
            "type": "resolvers/convert-args.ts"
          },
          29,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          33,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          34,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          39,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          45,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          50,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          51,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "field",
            "type": "resolvers/convert-args.ts"
          },
          52,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          56,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          62,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "field",
            "type": "resolvers/convert-args.ts"
          },
          63,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          80,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          89,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          91,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          94,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          94,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          102,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          104,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertValuesToInstances",
            "type": "resolvers/convert-args.ts"
          },
          128,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertValuesToInstances",
            "type": "resolvers/convert-args.ts"
          },
          130,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          136,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          140,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          146,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          149,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          153,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgToInstance",
            "type": "resolvers/convert-args.ts"
          },
          165,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          26,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          36,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "targetInstance",
            "type": "resolvers/create.ts"
          },
          45,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "resolvedParams",
            "type": "resolvers/create.ts"
          },
          47,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "targetInstance",
            "type": "resolvers/create.ts"
          },
          51,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          64,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "resolvedParams",
            "type": "resolvers/create.ts"
          },
          66,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          70,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          91,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          111,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "resolvedParams",
            "type": "resolvers/create.ts"
          },
          112,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          115,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createBasicFieldResolver",
            "type": "resolvers/create.ts"
          },
          124,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "wrapResolverWithAuthChecker",
            "type": "resolvers/create.ts"
          },
          150,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          18,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          18,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          26,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          37,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          59,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          68,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          70,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          76,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          78,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          84,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          85,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "applyAuthChecker",
            "type": "resolvers/helpers.ts"
          },
          98,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "applyMiddlewares",
            "type": "resolvers/helpers.ts"
          },
          109,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "dispatchHandler",
            "type": "resolvers/helpers.ts"
          },
          128,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "dispatchHandler",
            "type": "resolvers/helpers.ts"
          },
          134,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          23,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          46,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          47,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          48,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          48,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "argItem",
            "type": "resolvers/validate-arg.ts"
          },
          50,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          53,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          22,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          22,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          31,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          38,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          38,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "argKey",
            "type": "schema/definition-node.ts"
          },
          44,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          51,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getObjectTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          91,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputObjectTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          110,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getFieldDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          129,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getFieldDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          136,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputValueDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          155,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputValueDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          162,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInterfaceTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          181,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          125,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          129,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          141,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          146,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          150,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          150,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          198,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "type": "schema/schema-generator.ts"
          },
          203,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "type": "schema/schema-generator.ts"
          },
          204,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "type": "schema/schema-generator.ts"
          },
          204,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectTypeCls",
            "type": "schema/schema-generator.ts"
          },
          207,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "type": "schema/schema-generator.ts"
          },
          210,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "instance",
            "type": "schema/schema-generator.ts"
          },
          225,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "instance",
            "type": "schema/schema-generator.ts"
          },
          225,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "instance",
            "type": "schema/schema-generator.ts"
          },
          232,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          241,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "enumMetadata",
            "type": "schema/schema-generator.ts"
          },
          248,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "enumMetadata",
            "type": "schema/schema-generator.ts"
          },
          248,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          262,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          263,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "type": "schema/schema-generator.ts"
          },
          267,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "type": "schema/schema-generator.ts"
          },
          268,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          281,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceClass",
            "type": "schema/schema-generator.ts"
          },
          282,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          298,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          299,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          299,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          309,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          310,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          312,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          313,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          317,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          319,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          322,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          323,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          325,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          331,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          378,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          380,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "type": "schema/schema-generator.ts"
          },
          383,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          390,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          390,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          394,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          397,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          398,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          409,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceClass",
            "type": "schema/schema-generator.ts"
          },
          411,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          417,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          418,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          418,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          428,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          429,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          431,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          432,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          436,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          438,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          440,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          448,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "instance",
            "type": "schema/schema-generator.ts"
          },
          483,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "instance",
            "type": "schema/schema-generator.ts"
          },
          489,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          499,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "inputType",
            "type": "schema/schema-generator.ts"
          },
          500,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "type": "schema/schema-generator.ts"
          },
          502,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "inputType",
            "type": "schema/schema-generator.ts"
          },
          515,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "inputType",
            "type": "schema/schema-generator.ts"
          },
          524,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "schema/schema-generator.ts"
          },
          597,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typeInfo",
            "type": "schema/schema-generator.ts"
          },
          598,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceClass",
            "type": "schema/schema-generator.ts"
          },
          599,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceClass",
            "type": "schema/schema-generator.ts"
          },
          608,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "schema/schema-generator.ts"
          },
          618,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "type": "schema/schema-generator.ts"
          },
          625,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "type": "schema/schema-generator.ts"
          },
          629,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          663,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          683,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          687,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          690,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          691,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          696,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          697,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "topic",
            "type": "schema/schema-generator.ts"
          },
          697,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          705,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          707,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          732,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          739,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          744,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          744,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          761,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          762,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          775,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          777,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          779,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          780,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "mapArgFields",
            "type": "schema/schema-generator.ts"
          },
          797,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "field",
            "type": "schema/schema-generator.ts"
          },
          804,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "schema/schema-generator.ts"
          },
          829,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "schema/schema-generator.ts"
          },
          835,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "schema/schema-generator.ts"
          },
          837,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "schema/schema-generator.ts"
          },
          842,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "schema/schema-generator.ts"
          },
          848,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLInputType",
            "type": "schema/schema-generator.ts"
          },
          872,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLInputType",
            "type": "schema/schema-generator.ts"
          },
          878,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getResolveTypeFunction",
            "type": "schema/schema-generator.ts"
          },
          902,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getResolveTypeFunction",
            "type": "schema/schema-generator.ts"
          },
          906,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterHandlersByResolvers",
            "type": "schema/schema-generator.ts"
          },
          915,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "query",
            "type": "schema/schema-generator.ts"
          },
          915,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "type": "schema/schema-generator.ts"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "type": "schema/schema-generator.ts"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          11,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          12,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          12,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          30,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          31,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          31,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          37,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getEmitSchemaDefinitionFileOptions",
            "type": "utils/buildSchema.ts"
          },
          20,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "getEmitSchemaDefinitionFileOptions",
            "type": "utils/buildSchema.ts"
          },
          20,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "buildSchema",
            "type": "utils/buildSchema.ts"
          },
          59,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "buildSchemaSync",
            "type": "utils/buildSchema.ts"
          },
          70,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "createTypeDefsAndResolversMap",
            "type": "utils/buildTypeDefsAndResolvers.ts"
          },
          6,
          "utils/buildTypeDefsAndResolvers.ts"
        ],
        [
          {
            "name": "get",
            "type": "DefaultContainer"
          },
          23,
          "utils/container.ts"
        ],
        [
          {
            "name": "get",
            "type": "DefaultContainer"
          },
          26,
          "utils/container.ts"
        ],
        [
          {
            "name": "getInstance",
            "type": "IOCContainer"
          },
          56,
          "utils/container.ts"
        ],
        [
          {
            "name": "getInstance",
            "type": "IOCContainer"
          },
          60,
          "utils/container.ts"
        ],
        [
          {
            "name": "generateTypeResolver",
            "type": "utils/createResolversMap.ts"
          },
          23,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateTypeResolver",
            "type": "utils/createResolversMap.ts"
          },
          27,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateFieldsResolvers",
            "type": "utils/createResolversMap.ts"
          },
          36,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateFieldsResolvers",
            "type": "utils/createResolversMap.ts"
          },
          36,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          51,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "typeName",
            "type": "utils/createResolversMap.ts"
          },
          53,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          61,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          67,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          74,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          75,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "getSchemaFileContent",
            "type": "utils/emitSchemaDefinitionFile.ts"
          },
          21,
          "utils/emitSchemaDefinitionFile.ts"
        ],
        [
          {
            "name": "getSchemaFileContent",
            "type": "utils/emitSchemaDefinitionFile.ts"
          },
          22,
          "utils/emitSchemaDefinitionFile.ts"
        ],
        [
          {
            "name": "ensureInstalledCorrectGraphQLPackage",
            "type": "utils/graphql-version.ts"
          },
          10,
          "utils/graphql-version.ts"
        ]
      ],
      "version": "code-review-graph 2.3.8"
    },
    "code-review-graph-dispatch": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 1.09,
      "declared_unresolved": 367,
      "fanned_rows": 0,
      "rows": 588,
      "seconds_breakdown": {
        "adapter_total": 1.63,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/type-graphql/crg/data/graph.db",
      "unresolved_sites": [
        [
          {
            "name": "Arg",
            "type": "decorators/Arg.ts"
          },
          34,
          "decorators/Arg.ts"
        ],
        [
          {
            "name": "Args",
            "type": "decorators/Args.ts"
          },
          19,
          "decorators/Args.ts"
        ],
        [
          {
            "name": "target",
            "type": "decorators/ArgsType.ts"
          },
          5,
          "decorators/ArgsType.ts"
        ],
        [
          {
            "name": "Authorized",
            "type": "decorators/Authorized.ts"
          },
          22,
          "decorators/Authorized.ts"
        ],
        [
          {
            "name": "Authorized",
            "type": "decorators/Authorized.ts"
          },
          33,
          "decorators/Authorized.ts"
        ],
        [
          {
            "name": "Ctx",
            "type": "decorators/Ctx.ts"
          },
          11,
          "decorators/Ctx.ts"
        ],
        [
          {
            "name": "Directive",
            "type": "decorators/Directive.ts"
          },
          23,
          "decorators/Directive.ts"
        ],
        [
          {
            "name": "Directive",
            "type": "decorators/Directive.ts"
          },
          30,
          "decorators/Directive.ts"
        ],
        [
          {
            "name": "Directive",
            "type": "decorators/Directive.ts"
          },
          37,
          "decorators/Directive.ts"
        ],
        [
          {
            "name": "Extensions",
            "type": "decorators/Extensions.ts"
          },
          15,
          "decorators/Extensions.ts"
        ],
        [
          {
            "name": "Extensions",
            "type": "decorators/Extensions.ts"
          },
          21,
          "decorators/Extensions.ts"
        ],
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          31,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          32,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          42,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          55,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "FieldResolver",
            "type": "decorators/FieldResolver.ts"
          },
          50,
          "decorators/FieldResolver.ts"
        ],
        [
          {
            "name": "Info",
            "type": "decorators/Info.ts"
          },
          11,
          "decorators/Info.ts"
        ],
        [
          {
            "name": "target",
            "type": "decorators/InputType.ts"
          },
          16,
          "decorators/InputType.ts"
        ],
        [
          {
            "name": "InterfaceType",
            "type": "decorators/InterfaceType.ts"
          },
          27,
          "decorators/InterfaceType.ts"
        ],
        [
          {
            "name": "target",
            "type": "decorators/InterfaceType.ts"
          },
          29,
          "decorators/InterfaceType.ts"
        ],
        [
          {
            "name": "Mutation",
            "type": "decorators/Mutation.ts"
          },
          19,
          "decorators/Mutation.ts"
        ],
        [
          {
            "name": "ObjectType",
            "type": "decorators/ObjectType.ts"
          },
          19,
          "decorators/ObjectType.ts"
        ],
        [
          {
            "name": "target",
            "type": "decorators/ObjectType.ts"
          },
          22,
          "decorators/ObjectType.ts"
        ],
        [
          {
            "name": "Query",
            "type": "decorators/Query.ts"
          },
          16,
          "decorators/Query.ts"
        ],
        [
          {
            "name": "target",
            "type": "decorators/Resolver.ts"
          },
          20,
          "decorators/Resolver.ts"
        ],
        [
          {
            "name": "Root",
            "type": "decorators/Root.ts"
          },
          26,
          "decorators/Root.ts"
        ],
        [
          {
            "name": "Subscription",
            "type": "decorators/Subscription.ts"
          },
          40,
          "decorators/Subscription.ts"
        ],
        [
          {
            "name": "Subscription",
            "type": "decorators/Subscription.ts"
          },
          43,
          "decorators/Subscription.ts"
        ],
        [
          {
            "name": "UseMiddleware",
            "type": "decorators/UseMiddleware.ts"
          },
          20,
          "decorators/UseMiddleware.ts"
        ],
        [
          {
            "name": "UseMiddleware",
            "type": "decorators/UseMiddleware.ts"
          },
          31,
          "decorators/UseMiddleware.ts"
        ],
        [
          {
            "name": "createParameterDecorator",
            "type": "decorators/createParameterDecorator.ts"
          },
          48,
          "decorators/createParameterDecorator.ts"
        ],
        [
          {
            "name": "registerEnumType",
            "type": "decorators/enums.ts"
          },
          8,
          "decorators/enums.ts"
        ],
        [
          {
            "name": "createUnionType",
            "type": "decorators/unions.ts"
          },
          21,
          "decorators/unions.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "CannotDetermineGraphQLTypeError"
          },
          21,
          "errors/CannotDetermineGraphQLTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ConflictingDefaultValuesError"
          },
          14,
          "errors/ConflictingDefaultValuesError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "GeneratingSchemaError"
          },
          8,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "GeneratingSchemaError"
          },
          12,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InterfaceResolveTypeError"
          },
          10,
          "errors/InterfaceResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InvalidDirectiveError"
          },
          4,
          "errors/InvalidDirectiveError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingPubSubError"
          },
          8,
          "errors/MissingPubSubError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingSubscriptionTopicsError"
          },
          5,
          "errors/MissingSubscriptionTopicsError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "NoExplicitTypeError"
          },
          14,
          "errors/NoExplicitTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ReflectMetadataMissingError"
          },
          8,
          "errors/ReflectMetadataMissingError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SymbolKeysNotSupportedError"
          },
          5,
          "errors/SymbolKeysNotSupportedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnionResolveTypeError"
          },
          10,
          "errors/UnionResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnmetGraphQLPeerDependencyError"
          },
          9,
          "errors/UnmetGraphQLPeerDependencyError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "WrongNullableListOptionError"
          },
          14,
          "errors/WrongNullableListOptionError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ArgumentValidationError"
          },
          21,
          "errors/graphql/ArgumentValidationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthenticationError"
          },
          16,
          "errors/graphql/AuthenticationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthorizationError"
          },
          16,
          "errors/graphql/AuthorizationError.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "type": "helpers/auth-middleware.ts"
          },
          16,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "type": "helpers/auth-middleware.ts"
          },
          29,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "getArrayFromOverloadedRest",
            "type": "helpers/decorators.ts"
          },
          39,
          "helpers/decorators.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          7,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          12,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          12,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          13,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          19,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          24,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          24,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          25,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "findTypeValueArrayDepth",
            "type": "helpers/findType.ts"
          },
          33,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "type": "helpers/findType.ts"
          },
          51,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "type": "helpers/findType.ts"
          },
          64,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "getType",
            "type": "helpers/findType.ts"
          },
          70,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "getType",
            "type": "helpers/findType.ts"
          },
          71,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "isThrowing",
            "type": "helpers/isThrowing.ts"
          },
          3,
          "helpers/isThrowing.ts"
        ],
        [
          {
            "name": "convertTypeIfScalar",
            "type": "helpers/types.ts"
          },
          32,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          97,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          105,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          106,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          109,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "key",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "key",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          114,
          "helpers/types.ts"
        ],
        [
          {
            "name": "collectQueryHandlerMetadata",
            "type": "MetadataStorage"
          },
          84,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectMutationHandlerMetadata",
            "type": "MetadataStorage"
          },
          88,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectSubscriptionHandlerMetadata",
            "type": "MetadataStorage"
          },
          92,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          96,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectObjectMetadata",
            "type": "MetadataStorage"
          },
          100,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectInputMetadata",
            "type": "MetadataStorage"
          },
          104,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectArgsMetadata",
            "type": "MetadataStorage"
          },
          108,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectInterfaceMetadata",
            "type": "MetadataStorage"
          },
          112,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectAuthorizedFieldMetadata",
            "type": "MetadataStorage"
          },
          116,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectAuthorizedResolverMetadata",
            "type": "MetadataStorage"
          },
          120,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectEnumMetadata",
            "type": "MetadataStorage"
          },
          124,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectUnionMetadata",
            "type": "MetadataStorage"
          },
          128,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectUnionMetadata",
            "type": "MetadataStorage"
          },
          129,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectMiddlewareMetadata",
            "type": "MetadataStorage"
          },
          137,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectResolverMiddlewareMetadata",
            "type": "MetadataStorage"
          },
          141,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectResolverClassMetadata",
            "type": "MetadataStorage"
          },
          145,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectClassFieldMetadata",
            "type": "MetadataStorage"
          },
          149,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectHandlerParamMetadata",
            "type": "MetadataStorage"
          },
          153,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveClassMetadata",
            "type": "MetadataStorage"
          },
          157,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveFieldMetadata",
            "type": "MetadataStorage"
          },
          161,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveArgumentMetadata",
            "type": "MetadataStorage"
          },
          165,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectExtensionsClassMetadata",
            "type": "MetadataStorage"
          },
          169,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectExtensionsFieldMetadata",
            "type": "MetadataStorage"
          },
          173,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          177,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          178,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          179,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          180,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          181,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "type": "MetadataStorage"
          },
          224,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          226,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          227,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "field",
            "type": "MetadataStorage"
          },
          229,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "field",
            "type": "MetadataStorage"
          },
          234,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "field",
            "type": "MetadataStorage"
          },
          237,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "field",
            "type": "MetadataStorage"
          },
          243,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "field",
            "type": "MetadataStorage"
          },
          243,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          251,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          251,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "type": "MetadataStorage"
          },
          262,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          263,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          267,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          273,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          276,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          282,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          282,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          294,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          296,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          296,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          302,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          305,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          308,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          309,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          316,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          322,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "resolverCls",
            "type": "MetadataStorage"
          },
          325,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          347,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "type": "MetadataStorage"
          },
          365,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          366,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          371,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "def",
            "type": "MetadataStorage"
          },
          382,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findFieldRoles",
            "type": "MetadataStorage"
          },
          389,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findFieldRoles",
            "type": "MetadataStorage"
          },
          391,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "type": "MetadataStorage"
          },
          402,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "type": "MetadataStorage"
          },
          402,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "entry",
            "type": "MetadataStorage"
          },
          405,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "mapSuperResolverHandlers",
            "type": "metadata/utils.ts"
          },
          16,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapSuperFieldResolverHandlers",
            "type": "metadata/utils.ts"
          },
          34,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          49,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          49,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          53,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "getInputType",
            "type": "resolvers/convert-args.ts"
          },
          25,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "getArgsType",
            "type": "resolvers/convert-args.ts"
          },
          29,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          33,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          34,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          39,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          45,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          50,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          51,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "field",
            "type": "resolvers/convert-args.ts"
          },
          52,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          56,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          62,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "field",
            "type": "resolvers/convert-args.ts"
          },
          63,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          80,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          89,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          91,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          94,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          94,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          102,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          104,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertValuesToInstances",
            "type": "resolvers/convert-args.ts"
          },
          128,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertValuesToInstances",
            "type": "resolvers/convert-args.ts"
          },
          130,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          136,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          140,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          146,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          149,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          153,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgToInstance",
            "type": "resolvers/convert-args.ts"
          },
          165,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          26,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          36,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "targetInstance",
            "type": "resolvers/create.ts"
          },
          45,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "resolvedParams",
            "type": "resolvers/create.ts"
          },
          47,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "targetInstance",
            "type": "resolvers/create.ts"
          },
          51,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          64,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "resolvedParams",
            "type": "resolvers/create.ts"
          },
          66,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          70,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          91,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          111,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "resolvedParams",
            "type": "resolvers/create.ts"
          },
          112,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          115,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createBasicFieldResolver",
            "type": "resolvers/create.ts"
          },
          124,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "wrapResolverWithAuthChecker",
            "type": "resolvers/create.ts"
          },
          150,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          18,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          18,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          26,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          37,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          59,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          68,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          70,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          76,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "paramInfo",
            "type": "resolvers/helpers.ts"
          },
          78,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          84,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          85,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "applyAuthChecker",
            "type": "resolvers/helpers.ts"
          },
          98,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "applyMiddlewares",
            "type": "resolvers/helpers.ts"
          },
          109,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "dispatchHandler",
            "type": "resolvers/helpers.ts"
          },
          128,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "dispatchHandler",
            "type": "resolvers/helpers.ts"
          },
          134,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          23,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          46,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          47,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          48,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          48,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "argItem",
            "type": "resolvers/validate-arg.ts"
          },
          50,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          53,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          22,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          22,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          31,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          38,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          38,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "argKey",
            "type": "schema/definition-node.ts"
          },
          44,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          51,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getObjectTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          91,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputObjectTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          110,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getFieldDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          129,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getFieldDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          136,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputValueDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          155,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputValueDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          162,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInterfaceTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          181,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          125,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          129,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          141,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          146,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          150,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "schema/schema-generator.ts"
          },
          150,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          198,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "type": "schema/schema-generator.ts"
          },
          203,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "type": "schema/schema-generator.ts"
          },
          204,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "type": "schema/schema-generator.ts"
          },
          204,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectTypeCls",
            "type": "schema/schema-generator.ts"
          },
          207,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typesThunk",
            "type": "schema/schema-generator.ts"
          },
          210,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "instance",
            "type": "schema/schema-generator.ts"
          },
          225,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "instance",
            "type": "schema/schema-generator.ts"
          },
          225,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "instance",
            "type": "schema/schema-generator.ts"
          },
          232,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          241,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "enumMetadata",
            "type": "schema/schema-generator.ts"
          },
          248,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "enumMetadata",
            "type": "schema/schema-generator.ts"
          },
          248,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          262,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          263,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "type": "schema/schema-generator.ts"
          },
          267,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "type": "schema/schema-generator.ts"
          },
          268,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          281,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceClass",
            "type": "schema/schema-generator.ts"
          },
          282,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          298,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          299,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          299,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          309,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          310,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          312,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          313,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          317,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          319,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          322,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          323,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          325,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          331,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          378,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          380,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "type": "schema/schema-generator.ts"
          },
          383,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          390,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          390,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectType",
            "type": "schema/schema-generator.ts"
          },
          394,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          397,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "objectTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          398,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          409,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceClass",
            "type": "schema/schema-generator.ts"
          },
          411,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          417,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          418,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          418,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          428,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          429,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          431,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          432,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          436,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          438,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          440,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceType",
            "type": "schema/schema-generator.ts"
          },
          448,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "instance",
            "type": "schema/schema-generator.ts"
          },
          483,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "instance",
            "type": "schema/schema-generator.ts"
          },
          489,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "schema/schema-generator.ts"
          },
          499,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "inputType",
            "type": "schema/schema-generator.ts"
          },
          500,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getSuperClassType",
            "type": "schema/schema-generator.ts"
          },
          502,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "inputType",
            "type": "schema/schema-generator.ts"
          },
          515,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "inputType",
            "type": "schema/schema-generator.ts"
          },
          524,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "schema/schema-generator.ts"
          },
          597,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "typeInfo",
            "type": "schema/schema-generator.ts"
          },
          598,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceClass",
            "type": "schema/schema-generator.ts"
          },
          599,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "interfaceClass",
            "type": "schema/schema-generator.ts"
          },
          608,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "schema/schema-generator.ts"
          },
          618,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "type": "schema/schema-generator.ts"
          },
          625,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "type": "schema/schema-generator.ts"
          },
          629,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          663,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          683,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          687,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          690,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          691,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          696,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          697,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "topic",
            "type": "schema/schema-generator.ts"
          },
          697,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          705,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "schema/schema-generator.ts"
          },
          707,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          732,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          739,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          744,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          744,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          761,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          762,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          775,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          777,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          779,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "schema/schema-generator.ts"
          },
          780,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "mapArgFields",
            "type": "schema/schema-generator.ts"
          },
          797,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "field",
            "type": "schema/schema-generator.ts"
          },
          804,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "schema/schema-generator.ts"
          },
          829,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "schema/schema-generator.ts"
          },
          835,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "schema/schema-generator.ts"
          },
          837,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "schema/schema-generator.ts"
          },
          842,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "schema/schema-generator.ts"
          },
          848,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLInputType",
            "type": "schema/schema-generator.ts"
          },
          872,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLInputType",
            "type": "schema/schema-generator.ts"
          },
          878,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getResolveTypeFunction",
            "type": "schema/schema-generator.ts"
          },
          902,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getResolveTypeFunction",
            "type": "schema/schema-generator.ts"
          },
          906,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterHandlersByResolvers",
            "type": "schema/schema-generator.ts"
          },
          915,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "query",
            "type": "schema/schema-generator.ts"
          },
          915,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "type": "schema/schema-generator.ts"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "type": "schema/schema-generator.ts"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "it",
            "type": "schema/schema-generator.ts"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          11,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          12,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          12,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          30,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          31,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          31,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          37,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getEmitSchemaDefinitionFileOptions",
            "type": "utils/buildSchema.ts"
          },
          20,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "getEmitSchemaDefinitionFileOptions",
            "type": "utils/buildSchema.ts"
          },
          20,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "buildSchema",
            "type": "utils/buildSchema.ts"
          },
          59,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "buildSchemaSync",
            "type": "utils/buildSchema.ts"
          },
          70,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "createTypeDefsAndResolversMap",
            "type": "utils/buildTypeDefsAndResolvers.ts"
          },
          6,
          "utils/buildTypeDefsAndResolvers.ts"
        ],
        [
          {
            "name": "get",
            "type": "DefaultContainer"
          },
          23,
          "utils/container.ts"
        ],
        [
          {
            "name": "get",
            "type": "DefaultContainer"
          },
          26,
          "utils/container.ts"
        ],
        [
          {
            "name": "getInstance",
            "type": "IOCContainer"
          },
          56,
          "utils/container.ts"
        ],
        [
          {
            "name": "getInstance",
            "type": "IOCContainer"
          },
          60,
          "utils/container.ts"
        ],
        [
          {
            "name": "generateTypeResolver",
            "type": "utils/createResolversMap.ts"
          },
          23,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateTypeResolver",
            "type": "utils/createResolversMap.ts"
          },
          27,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateFieldsResolvers",
            "type": "utils/createResolversMap.ts"
          },
          36,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateFieldsResolvers",
            "type": "utils/createResolversMap.ts"
          },
          36,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          51,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "typeName",
            "type": "utils/createResolversMap.ts"
          },
          53,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          61,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          67,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          74,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          75,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "getSchemaFileContent",
            "type": "utils/emitSchemaDefinitionFile.ts"
          },
          21,
          "utils/emitSchemaDefinitionFile.ts"
        ],
        [
          {
            "name": "getSchemaFileContent",
            "type": "utils/emitSchemaDefinitionFile.ts"
          },
          22,
          "utils/emitSchemaDefinitionFile.ts"
        ],
        [
          {
            "name": "ensureInstalledCorrectGraphQLPackage",
            "type": "utils/graphql-version.ts"
          },
          10,
          "utils/graphql-version.ts"
        ]
      ],
      "version": "code-review-graph 2.3.8"
    },
    "codegraph": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 0.74,
      "declared_unresolved": 335,
      "dispatch_expanded_sites": 0,
      "rows": 290,
      "seconds_breakdown": {
        "adapter_total": 0.94,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "synthesized_rows_skipped": 0,
      "unresolved_sites": [
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          31,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          32,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "InterfaceType",
            "type": "decorators/InterfaceType.ts"
          },
          27,
          "decorators/InterfaceType.ts"
        ],
        [
          {
            "name": "ObjectType",
            "type": "decorators/ObjectType.ts"
          },
          19,
          "decorators/ObjectType.ts"
        ],
        [
          {
            "name": "Subscription",
            "type": "decorators/Subscription.ts"
          },
          40,
          "decorators/Subscription.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "CannotDetermineGraphQLTypeError"
          },
          20,
          "errors/CannotDetermineGraphQLTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "CannotDetermineGraphQLTypeError"
          },
          21,
          "errors/CannotDetermineGraphQLTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ConflictingDefaultValuesError"
          },
          8,
          "errors/ConflictingDefaultValuesError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ConflictingDefaultValuesError"
          },
          14,
          "errors/ConflictingDefaultValuesError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "GeneratingSchemaError"
          },
          8,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "GeneratingSchemaError"
          },
          11,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "GeneratingSchemaError"
          },
          12,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InterfaceResolveTypeError"
          },
          5,
          "errors/InterfaceResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InterfaceResolveTypeError"
          },
          10,
          "errors/InterfaceResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InvalidDirectiveError"
          },
          3,
          "errors/InvalidDirectiveError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InvalidDirectiveError"
          },
          4,
          "errors/InvalidDirectiveError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingPubSubError"
          },
          3,
          "errors/MissingPubSubError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingPubSubError"
          },
          8,
          "errors/MissingPubSubError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingSubscriptionTopicsError"
          },
          3,
          "errors/MissingSubscriptionTopicsError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingSubscriptionTopicsError"
          },
          5,
          "errors/MissingSubscriptionTopicsError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "NoExplicitTypeError"
          },
          12,
          "errors/NoExplicitTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "NoExplicitTypeError"
          },
          14,
          "errors/NoExplicitTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ReflectMetadataMissingError"
          },
          3,
          "errors/ReflectMetadataMissingError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ReflectMetadataMissingError"
          },
          8,
          "errors/ReflectMetadataMissingError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SymbolKeysNotSupportedError"
          },
          3,
          "errors/SymbolKeysNotSupportedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SymbolKeysNotSupportedError"
          },
          5,
          "errors/SymbolKeysNotSupportedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnionResolveTypeError"
          },
          5,
          "errors/UnionResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnionResolveTypeError"
          },
          10,
          "errors/UnionResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnmetGraphQLPeerDependencyError"
          },
          3,
          "errors/UnmetGraphQLPeerDependencyError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnmetGraphQLPeerDependencyError"
          },
          9,
          "errors/UnmetGraphQLPeerDependencyError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "WrongNullableListOptionError"
          },
          9,
          "errors/WrongNullableListOptionError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "WrongNullableListOptionError"
          },
          14,
          "errors/WrongNullableListOptionError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ArgumentValidationError"
          },
          14,
          "errors/graphql/ArgumentValidationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ArgumentValidationError"
          },
          21,
          "errors/graphql/ArgumentValidationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthenticationError"
          },
          10,
          "errors/graphql/AuthenticationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthenticationError"
          },
          16,
          "errors/graphql/AuthenticationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthorizationError"
          },
          10,
          "errors/graphql/AuthorizationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthorizationError"
          },
          16,
          "errors/graphql/AuthorizationError.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "type": "helpers/auth-middleware.ts"
          },
          16,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "type": "helpers/auth-middleware.ts"
          },
          18,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "type": "helpers/auth-middleware.ts"
          },
          29,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "getArrayFromOverloadedRest",
            "type": "helpers/decorators.ts"
          },
          39,
          "helpers/decorators.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          7,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          12,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          12,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          13,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          19,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          24,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          24,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          25,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "findTypeValueArrayDepth",
            "type": "helpers/findType.ts"
          },
          33,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "type": "helpers/findType.ts"
          },
          51,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "type": "helpers/findType.ts"
          },
          70,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "type": "helpers/findType.ts"
          },
          71,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "isThrowing",
            "type": "helpers/isThrowing.ts"
          },
          3,
          "helpers/isThrowing.ts"
        ],
        [
          {
            "name": "convertTypeIfScalar",
            "type": "helpers/types.ts"
          },
          32,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          97,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          105,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          106,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          109,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          114,
          "helpers/types.ts"
        ],
        [
          {
            "name": "collectQueryHandlerMetadata",
            "type": "MetadataStorage"
          },
          84,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectMutationHandlerMetadata",
            "type": "MetadataStorage"
          },
          88,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectSubscriptionHandlerMetadata",
            "type": "MetadataStorage"
          },
          92,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          96,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectObjectMetadata",
            "type": "MetadataStorage"
          },
          100,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectInputMetadata",
            "type": "MetadataStorage"
          },
          104,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectArgsMetadata",
            "type": "MetadataStorage"
          },
          108,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectInterfaceMetadata",
            "type": "MetadataStorage"
          },
          112,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectAuthorizedFieldMetadata",
            "type": "MetadataStorage"
          },
          116,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectAuthorizedResolverMetadata",
            "type": "MetadataStorage"
          },
          120,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectEnumMetadata",
            "type": "MetadataStorage"
          },
          124,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectUnionMetadata",
            "type": "MetadataStorage"
          },
          128,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectUnionMetadata",
            "type": "MetadataStorage"
          },
          129,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectMiddlewareMetadata",
            "type": "MetadataStorage"
          },
          137,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectResolverMiddlewareMetadata",
            "type": "MetadataStorage"
          },
          141,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectResolverClassMetadata",
            "type": "MetadataStorage"
          },
          145,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectClassFieldMetadata",
            "type": "MetadataStorage"
          },
          149,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectHandlerParamMetadata",
            "type": "MetadataStorage"
          },
          153,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveClassMetadata",
            "type": "MetadataStorage"
          },
          157,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveFieldMetadata",
            "type": "MetadataStorage"
          },
          161,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveArgumentMetadata",
            "type": "MetadataStorage"
          },
          165,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectExtensionsClassMetadata",
            "type": "MetadataStorage"
          },
          169,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectExtensionsFieldMetadata",
            "type": "MetadataStorage"
          },
          173,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          177,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          178,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          179,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          180,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          181,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "type": "MetadataStorage"
          },
          224,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "type": "MetadataStorage"
          },
          227,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "type": "MetadataStorage"
          },
          243,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "type": "MetadataStorage"
          },
          251,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "type": "MetadataStorage"
          },
          262,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "type": "MetadataStorage"
          },
          263,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "type": "MetadataStorage"
          },
          282,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          294,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          296,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          302,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          305,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          305,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          308,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          309,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          316,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          322,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          325,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          347,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "type": "MetadataStorage"
          },
          365,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "type": "MetadataStorage"
          },
          366,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "type": "MetadataStorage"
          },
          371,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "type": "MetadataStorage"
          },
          382,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findFieldRoles",
            "type": "MetadataStorage"
          },
          389,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findFieldRoles",
            "type": "MetadataStorage"
          },
          391,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "type": "MetadataStorage"
          },
          402,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "type": "MetadataStorage"
          },
          402,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "type": "MetadataStorage"
          },
          405,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "mapSuperResolverHandlers",
            "type": "metadata/utils.ts"
          },
          16,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapSuperFieldResolverHandlers",
            "type": "metadata/utils.ts"
          },
          34,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          49,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          49,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          53,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "getInputType",
            "type": "resolvers/convert-args.ts"
          },
          25,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "getArgsType",
            "type": "resolvers/convert-args.ts"
          },
          29,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          33,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          39,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          45,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          50,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          52,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          56,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          62,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          63,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          80,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          89,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          91,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          94,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          94,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          102,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          104,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertValuesToInstances",
            "type": "resolvers/convert-args.ts"
          },
          128,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertValuesToInstances",
            "type": "resolvers/convert-args.ts"
          },
          130,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          136,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          140,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          146,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          149,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          153,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgToInstance",
            "type": "resolvers/convert-args.ts"
          },
          165,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          26,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          36,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          45,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          47,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          51,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          64,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          66,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          70,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          82,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          91,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          111,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          112,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          115,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createBasicFieldResolver",
            "type": "resolvers/create.ts"
          },
          124,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "wrapResolverWithAuthChecker",
            "type": "resolvers/create.ts"
          },
          145,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          18,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          18,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          26,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          37,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          59,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          68,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          70,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          84,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          85,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "applyAuthChecker",
            "type": "resolvers/helpers.ts"
          },
          98,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "applyMiddlewares",
            "type": "resolvers/helpers.ts"
          },
          109,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "dispatchHandler",
            "type": "applyMiddlewares"
          },
          128,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "dispatchHandler",
            "type": "applyMiddlewares"
          },
          134,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          44,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          46,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          47,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          48,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          48,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          50,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          53,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          22,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          22,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          31,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          38,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          38,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          44,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          51,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getObjectTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          91,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputObjectTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          110,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getFieldDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          129,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getFieldDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          136,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputValueDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          155,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputValueDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          162,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInterfaceTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          181,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "SchemaGenerator"
          },
          125,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "SchemaGenerator"
          },
          141,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "SchemaGenerator"
          },
          150,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "SchemaGenerator"
          },
          150,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          198,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          203,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          204,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          204,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          207,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          210,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          225,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          225,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          232,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          241,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          248,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          248,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          262,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          263,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          267,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          268,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          281,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          282,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          296,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          298,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          299,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          299,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          310,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          312,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          313,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          317,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          319,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          322,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          323,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          325,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          326,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          331,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          366,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          378,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          380,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          383,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          390,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          394,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          398,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          409,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          411,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          415,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          417,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          418,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          418,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          429,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          431,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          432,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          436,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          438,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          440,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          442,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          448,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          472,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          483,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          489,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          499,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          500,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          502,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          515,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          524,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          543,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "SchemaGenerator"
          },
          598,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "SchemaGenerator"
          },
          599,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "SchemaGenerator"
          },
          608,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "SchemaGenerator"
          },
          618,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "type": "SchemaGenerator"
          },
          625,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "type": "SchemaGenerator"
          },
          629,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          663,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          674,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          683,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          687,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          690,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          691,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          696,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          697,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          697,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          705,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          709,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          732,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          739,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          744,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          761,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          762,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          775,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          777,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          779,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          780,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "mapArgFields",
            "type": "SchemaGenerator"
          },
          797,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "mapArgFields",
            "type": "SchemaGenerator"
          },
          804,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "SchemaGenerator"
          },
          829,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "SchemaGenerator"
          },
          835,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "SchemaGenerator"
          },
          837,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "SchemaGenerator"
          },
          842,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "SchemaGenerator"
          },
          848,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLInputType",
            "type": "SchemaGenerator"
          },
          872,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLInputType",
            "type": "SchemaGenerator"
          },
          878,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getResolveTypeFunction",
            "type": "SchemaGenerator"
          },
          906,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterHandlersByResolvers",
            "type": "SchemaGenerator"
          },
          915,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterHandlersByResolvers",
            "type": "SchemaGenerator"
          },
          915,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "type": "SchemaGenerator"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "type": "SchemaGenerator"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "type": "SchemaGenerator"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          11,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          12,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          12,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          30,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          31,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          31,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          37,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getEmitSchemaDefinitionFileOptions",
            "type": "utils/buildSchema.ts"
          },
          20,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "getEmitSchemaDefinitionFileOptions",
            "type": "utils/buildSchema.ts"
          },
          20,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "createTypeDefsAndResolversMap",
            "type": "utils/buildTypeDefsAndResolvers.ts"
          },
          6,
          "utils/buildTypeDefsAndResolvers.ts"
        ],
        [
          {
            "name": "get",
            "type": "DefaultContainer"
          },
          23,
          "utils/container.ts"
        ],
        [
          {
            "name": "get",
            "type": "DefaultContainer"
          },
          26,
          "utils/container.ts"
        ],
        [
          {
            "name": "generateTypeResolver",
            "type": "utils/createResolversMap.ts"
          },
          23,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateTypeResolver",
            "type": "utils/createResolversMap.ts"
          },
          27,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateFieldsResolvers",
            "type": "utils/createResolversMap.ts"
          },
          36,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateFieldsResolvers",
            "type": "utils/createResolversMap.ts"
          },
          36,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          51,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          53,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          61,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          67,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          74,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          75,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "getSchemaFileContent",
            "type": "utils/emitSchemaDefinitionFile.ts"
          },
          21,
          "utils/emitSchemaDefinitionFile.ts"
        ],
        [
          {
            "name": "getSchemaFileContent",
            "type": "utils/emitSchemaDefinitionFile.ts"
          },
          22,
          "utils/emitSchemaDefinitionFile.ts"
        ],
        [
          {
            "name": "ensureInstalledCorrectGraphQLPackage",
            "type": "utils/graphql-version.ts"
          },
          10,
          "utils/graphql-version.ts"
        ]
      ],
      "version": "codegraph 1.6.0"
    },
    "codegraph-dispatch": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 0.74,
      "declared_unresolved": 335,
      "dispatch_expanded_sites": 0,
      "rows": 290,
      "seconds_breakdown": {
        "adapter_total": 0.94,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "synthesized_rows_skipped": 0,
      "unresolved_sites": [
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          31,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "Field",
            "type": "decorators/Field.ts"
          },
          32,
          "decorators/Field.ts"
        ],
        [
          {
            "name": "InterfaceType",
            "type": "decorators/InterfaceType.ts"
          },
          27,
          "decorators/InterfaceType.ts"
        ],
        [
          {
            "name": "ObjectType",
            "type": "decorators/ObjectType.ts"
          },
          19,
          "decorators/ObjectType.ts"
        ],
        [
          {
            "name": "Subscription",
            "type": "decorators/Subscription.ts"
          },
          40,
          "decorators/Subscription.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "CannotDetermineGraphQLTypeError"
          },
          20,
          "errors/CannotDetermineGraphQLTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "CannotDetermineGraphQLTypeError"
          },
          21,
          "errors/CannotDetermineGraphQLTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ConflictingDefaultValuesError"
          },
          8,
          "errors/ConflictingDefaultValuesError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ConflictingDefaultValuesError"
          },
          14,
          "errors/ConflictingDefaultValuesError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "GeneratingSchemaError"
          },
          8,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "GeneratingSchemaError"
          },
          11,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "GeneratingSchemaError"
          },
          12,
          "errors/GeneratingSchemaError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InterfaceResolveTypeError"
          },
          5,
          "errors/InterfaceResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InterfaceResolveTypeError"
          },
          10,
          "errors/InterfaceResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InvalidDirectiveError"
          },
          3,
          "errors/InvalidDirectiveError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "InvalidDirectiveError"
          },
          4,
          "errors/InvalidDirectiveError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingPubSubError"
          },
          3,
          "errors/MissingPubSubError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingPubSubError"
          },
          8,
          "errors/MissingPubSubError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingSubscriptionTopicsError"
          },
          3,
          "errors/MissingSubscriptionTopicsError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "MissingSubscriptionTopicsError"
          },
          5,
          "errors/MissingSubscriptionTopicsError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "NoExplicitTypeError"
          },
          12,
          "errors/NoExplicitTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "NoExplicitTypeError"
          },
          14,
          "errors/NoExplicitTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ReflectMetadataMissingError"
          },
          3,
          "errors/ReflectMetadataMissingError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ReflectMetadataMissingError"
          },
          8,
          "errors/ReflectMetadataMissingError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SymbolKeysNotSupportedError"
          },
          3,
          "errors/SymbolKeysNotSupportedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "SymbolKeysNotSupportedError"
          },
          5,
          "errors/SymbolKeysNotSupportedError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnionResolveTypeError"
          },
          5,
          "errors/UnionResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnionResolveTypeError"
          },
          10,
          "errors/UnionResolveTypeError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnmetGraphQLPeerDependencyError"
          },
          3,
          "errors/UnmetGraphQLPeerDependencyError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "UnmetGraphQLPeerDependencyError"
          },
          9,
          "errors/UnmetGraphQLPeerDependencyError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "WrongNullableListOptionError"
          },
          9,
          "errors/WrongNullableListOptionError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "WrongNullableListOptionError"
          },
          14,
          "errors/WrongNullableListOptionError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ArgumentValidationError"
          },
          14,
          "errors/graphql/ArgumentValidationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "ArgumentValidationError"
          },
          21,
          "errors/graphql/ArgumentValidationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthenticationError"
          },
          10,
          "errors/graphql/AuthenticationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthenticationError"
          },
          16,
          "errors/graphql/AuthenticationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthorizationError"
          },
          10,
          "errors/graphql/AuthorizationError.ts"
        ],
        [
          {
            "name": "constructor",
            "type": "AuthorizationError"
          },
          16,
          "errors/graphql/AuthorizationError.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "type": "helpers/auth-middleware.ts"
          },
          16,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "type": "helpers/auth-middleware.ts"
          },
          18,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "AuthMiddleware",
            "type": "helpers/auth-middleware.ts"
          },
          29,
          "helpers/auth-middleware.ts"
        ],
        [
          {
            "name": "getArrayFromOverloadedRest",
            "type": "helpers/decorators.ts"
          },
          39,
          "helpers/decorators.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          7,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          12,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          12,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFile",
            "type": "helpers/filesystem.ts"
          },
          13,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          19,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          24,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          24,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "outputFileSync",
            "type": "helpers/filesystem.ts"
          },
          25,
          "helpers/filesystem.ts"
        ],
        [
          {
            "name": "findTypeValueArrayDepth",
            "type": "helpers/findType.ts"
          },
          33,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "type": "helpers/findType.ts"
          },
          51,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "type": "helpers/findType.ts"
          },
          70,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "findType",
            "type": "helpers/findType.ts"
          },
          71,
          "helpers/findType.ts"
        ],
        [
          {
            "name": "isThrowing",
            "type": "helpers/isThrowing.ts"
          },
          3,
          "helpers/isThrowing.ts"
        ],
        [
          {
            "name": "convertTypeIfScalar",
            "type": "helpers/types.ts"
          },
          32,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          97,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          105,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          106,
          "helpers/types.ts"
        ],
        [
          {
            "name": "convertToType",
            "type": "helpers/types.ts"
          },
          109,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          113,
          "helpers/types.ts"
        ],
        [
          {
            "name": "getEnumValuesMap",
            "type": "helpers/types.ts"
          },
          114,
          "helpers/types.ts"
        ],
        [
          {
            "name": "collectQueryHandlerMetadata",
            "type": "MetadataStorage"
          },
          84,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectMutationHandlerMetadata",
            "type": "MetadataStorage"
          },
          88,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectSubscriptionHandlerMetadata",
            "type": "MetadataStorage"
          },
          92,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          96,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectObjectMetadata",
            "type": "MetadataStorage"
          },
          100,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectInputMetadata",
            "type": "MetadataStorage"
          },
          104,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectArgsMetadata",
            "type": "MetadataStorage"
          },
          108,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectInterfaceMetadata",
            "type": "MetadataStorage"
          },
          112,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectAuthorizedFieldMetadata",
            "type": "MetadataStorage"
          },
          116,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectAuthorizedResolverMetadata",
            "type": "MetadataStorage"
          },
          120,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectEnumMetadata",
            "type": "MetadataStorage"
          },
          124,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectUnionMetadata",
            "type": "MetadataStorage"
          },
          128,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectUnionMetadata",
            "type": "MetadataStorage"
          },
          129,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectMiddlewareMetadata",
            "type": "MetadataStorage"
          },
          137,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectResolverMiddlewareMetadata",
            "type": "MetadataStorage"
          },
          141,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectResolverClassMetadata",
            "type": "MetadataStorage"
          },
          145,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectClassFieldMetadata",
            "type": "MetadataStorage"
          },
          149,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectHandlerParamMetadata",
            "type": "MetadataStorage"
          },
          153,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveClassMetadata",
            "type": "MetadataStorage"
          },
          157,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveFieldMetadata",
            "type": "MetadataStorage"
          },
          161,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectDirectiveArgumentMetadata",
            "type": "MetadataStorage"
          },
          165,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectExtensionsClassMetadata",
            "type": "MetadataStorage"
          },
          169,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "collectExtensionsFieldMetadata",
            "type": "MetadataStorage"
          },
          173,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          177,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          178,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          179,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          180,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "build",
            "type": "MetadataStorage"
          },
          181,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "type": "MetadataStorage"
          },
          224,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "type": "MetadataStorage"
          },
          227,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "type": "MetadataStorage"
          },
          243,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildClassMetadata",
            "type": "MetadataStorage"
          },
          251,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "type": "MetadataStorage"
          },
          262,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "type": "MetadataStorage"
          },
          263,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildResolversMetadata",
            "type": "MetadataStorage"
          },
          282,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          294,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          296,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          302,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          305,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          305,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          308,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          309,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          316,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          322,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          325,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildFieldResolverMetadata",
            "type": "MetadataStorage"
          },
          347,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "type": "MetadataStorage"
          },
          365,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "type": "MetadataStorage"
          },
          366,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "type": "MetadataStorage"
          },
          371,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "buildExtendedResolversMetadata",
            "type": "MetadataStorage"
          },
          382,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findFieldRoles",
            "type": "MetadataStorage"
          },
          389,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findFieldRoles",
            "type": "MetadataStorage"
          },
          391,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "type": "MetadataStorage"
          },
          402,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "type": "MetadataStorage"
          },
          402,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "findExtensions",
            "type": "MetadataStorage"
          },
          405,
          "metadata/metadata-storage.ts"
        ],
        [
          {
            "name": "mapSuperResolverHandlers",
            "type": "metadata/utils.ts"
          },
          16,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapSuperFieldResolverHandlers",
            "type": "metadata/utils.ts"
          },
          34,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          49,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          49,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "mapMiddlewareMetadataToArray",
            "type": "metadata/utils.ts"
          },
          53,
          "metadata/utils.ts"
        ],
        [
          {
            "name": "getInputType",
            "type": "resolvers/convert-args.ts"
          },
          25,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "getArgsType",
            "type": "resolvers/convert-args.ts"
          },
          29,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          33,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          39,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          45,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          50,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          52,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          56,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          62,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateTransformationTree",
            "type": "generateInstanceTransformationTree"
          },
          63,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "generateInstanceTransformationTree",
            "type": "resolvers/convert-args.ts"
          },
          80,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          89,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          91,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          94,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          94,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          102,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertToInput",
            "type": "resolvers/convert-args.ts"
          },
          104,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertValuesToInstances",
            "type": "resolvers/convert-args.ts"
          },
          128,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertValuesToInstances",
            "type": "resolvers/convert-args.ts"
          },
          130,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          136,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          140,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          146,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          149,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgsToInstance",
            "type": "resolvers/convert-args.ts"
          },
          153,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "convertArgToInstance",
            "type": "resolvers/convert-args.ts"
          },
          165,
          "resolvers/convert-args.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          26,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          36,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          45,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          47,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          51,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          64,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          66,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createHandlerResolver",
            "type": "resolvers/create.ts"
          },
          70,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          82,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          91,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          111,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          112,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createAdvancedFieldResolver",
            "type": "resolvers/create.ts"
          },
          115,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "createBasicFieldResolver",
            "type": "resolvers/create.ts"
          },
          124,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "wrapResolverWithAuthChecker",
            "type": "resolvers/create.ts"
          },
          145,
          "resolvers/create.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          18,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          18,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          26,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          37,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          59,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          68,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          70,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          84,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "getParams",
            "type": "resolvers/helpers.ts"
          },
          85,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "applyAuthChecker",
            "type": "resolvers/helpers.ts"
          },
          98,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "applyMiddlewares",
            "type": "resolvers/helpers.ts"
          },
          109,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "dispatchHandler",
            "type": "applyMiddlewares"
          },
          128,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "dispatchHandler",
            "type": "applyMiddlewares"
          },
          134,
          "resolvers/helpers.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          44,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          46,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          47,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          48,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          48,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          50,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "validateArg",
            "type": "resolvers/validate-arg.ts"
          },
          53,
          "resolvers/validate-arg.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          22,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          22,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          31,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          38,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          38,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          44,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          51,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getDirectiveNode",
            "type": "schema/definition-node.ts"
          },
          59,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getObjectTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          91,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputObjectTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          110,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getFieldDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          129,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getFieldDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          136,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputValueDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          155,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInputValueDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          162,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "getInterfaceTypeDefinitionNode",
            "type": "schema/definition-node.ts"
          },
          181,
          "schema/definition-node.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "SchemaGenerator"
          },
          125,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "SchemaGenerator"
          },
          141,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "SchemaGenerator"
          },
          150,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateFromMetadata",
            "type": "SchemaGenerator"
          },
          150,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          198,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          203,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          204,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          204,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          207,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          210,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          225,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          225,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          232,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          241,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          248,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          248,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          262,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          263,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          267,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          268,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          281,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          282,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          296,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          298,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          299,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          299,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          310,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          312,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          313,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          317,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          319,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          322,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          323,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          325,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          326,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          331,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          366,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          378,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          380,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          383,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          390,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          394,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          398,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          409,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          411,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          415,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          417,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          418,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          418,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          429,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          431,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          432,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          436,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          438,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          440,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          442,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          448,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          472,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          483,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          489,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          499,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          500,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          502,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          515,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          524,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildTypesInfo",
            "type": "SchemaGenerator"
          },
          543,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "SchemaGenerator"
          },
          598,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "SchemaGenerator"
          },
          599,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "SchemaGenerator"
          },
          608,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "buildOtherTypes",
            "type": "SchemaGenerator"
          },
          618,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "type": "SchemaGenerator"
          },
          625,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerFields",
            "type": "SchemaGenerator"
          },
          629,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          663,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          674,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          683,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          687,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          690,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          691,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          696,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          697,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          697,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          705,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateSubscriptionsFields",
            "type": "SchemaGenerator"
          },
          709,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          732,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          739,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          744,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          761,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          762,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          775,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          777,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          779,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "generateHandlerArgs",
            "type": "SchemaGenerator"
          },
          780,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "mapArgFields",
            "type": "SchemaGenerator"
          },
          797,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "mapArgFields",
            "type": "SchemaGenerator"
          },
          804,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "SchemaGenerator"
          },
          829,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "SchemaGenerator"
          },
          835,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "SchemaGenerator"
          },
          837,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "SchemaGenerator"
          },
          842,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLOutputType",
            "type": "SchemaGenerator"
          },
          848,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLInputType",
            "type": "SchemaGenerator"
          },
          872,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getGraphQLInputType",
            "type": "SchemaGenerator"
          },
          878,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getResolveTypeFunction",
            "type": "SchemaGenerator"
          },
          906,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterHandlersByResolvers",
            "type": "SchemaGenerator"
          },
          915,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterHandlersByResolvers",
            "type": "SchemaGenerator"
          },
          915,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "type": "SchemaGenerator"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "type": "SchemaGenerator"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "filterTypesInfoByOrphanedTypesAndExtractType",
            "type": "SchemaGenerator"
          },
          922,
          "schema/schema-generator.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          11,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          12,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromInputType",
            "type": "schema/utils.ts"
          },
          12,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          30,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          31,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          31,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getFieldMetadataFromObjectType",
            "type": "schema/utils.ts"
          },
          37,
          "schema/utils.ts"
        ],
        [
          {
            "name": "getEmitSchemaDefinitionFileOptions",
            "type": "utils/buildSchema.ts"
          },
          20,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "getEmitSchemaDefinitionFileOptions",
            "type": "utils/buildSchema.ts"
          },
          20,
          "utils/buildSchema.ts"
        ],
        [
          {
            "name": "createTypeDefsAndResolversMap",
            "type": "utils/buildTypeDefsAndResolvers.ts"
          },
          6,
          "utils/buildTypeDefsAndResolvers.ts"
        ],
        [
          {
            "name": "get",
            "type": "DefaultContainer"
          },
          23,
          "utils/container.ts"
        ],
        [
          {
            "name": "get",
            "type": "DefaultContainer"
          },
          26,
          "utils/container.ts"
        ],
        [
          {
            "name": "generateTypeResolver",
            "type": "utils/createResolversMap.ts"
          },
          23,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateTypeResolver",
            "type": "utils/createResolversMap.ts"
          },
          27,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateFieldsResolvers",
            "type": "utils/createResolversMap.ts"
          },
          36,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "generateFieldsResolvers",
            "type": "utils/createResolversMap.ts"
          },
          36,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          51,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          52,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          53,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          61,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          67,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          74,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "createResolversMap",
            "type": "utils/createResolversMap.ts"
          },
          75,
          "utils/createResolversMap.ts"
        ],
        [
          {
            "name": "getSchemaFileContent",
            "type": "utils/emitSchemaDefinitionFile.ts"
          },
          21,
          "utils/emitSchemaDefinitionFile.ts"
        ],
        [
          {
            "name": "getSchemaFileContent",
            "type": "utils/emitSchemaDefinitionFile.ts"
          },
          22,
          "utils/emitSchemaDefinitionFile.ts"
        ],
        [
          {
            "name": "ensureInstalledCorrectGraphQLPackage",
            "type": "utils/graphql-version.ts"
          },
          10,
          "utils/graphql-version.ts"
        ]
      ],
      "version": "codegraph 1.6.0"
    },
    "codeql": {
      "build": "source only",
      "cache": "hit",
      "cold_seconds": 6.94,
      "rows": 323,
      "seconds_breakdown": {
        "adapter_total": 20.26,
        "own": 6.81,
        "shared": 7.11,
        "staging": null
      },
      "source": ".work/typescript/type-graphql/codeql/q.csv",
      "version": "codeql 2.23.8 javascript-all 2.6.18"
    },
    "gitnexus": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 7.32,
      "rows": 132,
      "seconds_breakdown": {
        "adapter_total": 21.45,
        "export": 0.67,
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
      "rows": 213,
      "seconds_breakdown": {
        "adapter_total": 1.15,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/type-graphql/gfy/src/graphify-out/graph.json",
      "version": "graphifyy 0.9.58"
    },
    "ideal": {
      "build": "oracle",
      "null_model": true,
      "reference": "ideal",
      "rows": 257,
      "version": "the correct answer for every link group (a ceiling, not a tool)"
    }
  },
  "tsx": "4.19.2",
  "typescript": "5.6.3"
}
```
