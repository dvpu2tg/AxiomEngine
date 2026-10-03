# TypeScript call-graph benchmark — `cheerio`

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
| application types | 31 |
| application methods | 173 |
| call sites the checker resolved | 452 |
| … application-internal | 263 |
| … leaving the application (not scored, see §7) | 146 |
| … through a function value, target not statically known (not scored) | 43 |
| call expressions the checker could NOT resolve — no row of any kind; every recall denominator is short by this many, for every tool alike (#53) | 102 |
| … i.e. the checker resolved this % of the subject's call expressions (gate 0's floor is 55%) | 81.6 |
| … and this % resolve to a target INSIDE the subject — the scorable share; a library target clears the floor without adding one (#67) | 55.2 |
| **CERTAIN** edges (declared targets) — `recall_certain` denominator | 209 |
| **POSSIBLE** edges (declared-heritage + checker-assignable envelope — NOT sound, structural typing) — `recall_possible` denominator | 209 |
| **RTA** edges (instantiated-types envelope) — `recall_rta` denominator | 209 |
| link groups `(caller, callee-name)`, at Tier B | 206 |
| … **uniquely linked** (exactly one possible target) — the headline denominator | 204 |
| … uniquely linked at Tier A (overloads kept apart) | 203 |
| … genuinely ambiguous (dispatch admits several) | 2 |

Call sites by instruction: `CALL` 437, `NEW` 15.

## Headline — Tier B (`type#name`)

Tier B is the highest fidelity **every** tool under test can express, so it is the only tier
at which the whole field is comparable. The ground truth is projected to Tier B as well, so a
tool that cannot spell parameter types is not being asked to.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 2s | 0.981 | 0.981 | 0.505 | 0.505 | 0.505 | 0.667 | 0.702 | 107 | 47 (0 ambig, 46 out-of-scope, 25% of emitted, 0 unspellable, 1 §4-excluded), 60 duplicate |
| `code-review-graph` | source only | 2s | 0.718 | 0.756 | 0.745 | 0.611 | 0.611 | 0.751 | 0.748 | 205 | 266 (0 ambig, 239 out-of-scope, 47% of emitted, 11 unspellable, 16 §4-excluded), 86 duplicate |
| `code-review-graph-dispatch` | source only | 2s | 0.718 | 0.756 | 0.745 | 0.611 | 0.611 | 0.751 | 0.748 | 205 | 266 (0 ambig, 239 out-of-scope, 47% of emitted, 11 unspellable, 16 §4-excluded), 86 duplicate |
| `codegraph` | source only | 1s | 0.950 | 0.767 | 0.663 | 0.822 | 0.822 | 0.711 | 0.710 | 180 | 18 (0 ambig, 17 out-of-scope, 7% of emitted, 0 unspellable, 1 §4-excluded), 44 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.950 | 0.767 | 0.663 | 0.822 | 0.822 | 0.711 | 0.710 | 180 | 18 (0 ambig, 17 out-of-scope, 7% of emitted, 0 unspellable, 1 §4-excluded), 44 duplicate |
| `codeql` | source only | 14s | 0.851 | 0.851 | 0.466 | 0.466 | 0.466 | 0.602 | 0.627 | 114 | 122 (0 ambig, 87 out-of-scope, 32% of emitted, 0 unspellable, 35 §4-excluded), 119 duplicate |
| `gitnexus` | source only | 12s | 0.990 | 0.990 | 0.481 | 0.481 | 0.481 | 0.647 | 0.688 | 101 | 22 (0 ambig, 18 out-of-scope, 15% of emitted, 0 unspellable, 4 §4-excluded), 6 duplicate |
| `graphify` | source only | 1s | 0.922 | 0.922 | 0.567 | 0.567 | 0.567 | 0.702 | 0.721 | 128 | 17 (0 ambig, 16 out-of-scope, 11% of emitted, 0 unspellable, 1 §4-excluded) |
| *`cha-null`* | bytecode | 0s | 1.000 | 0.827 | 0.827 | 1.000 | 1.000 | 0.827 | 0.825 | 208 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 0.827 | 0.827 | 1.000 | 1.000 | 208 | 0 |

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

- `axiom`: 0 rows named a type that matches more than one application type, 46 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `code-review-graph`: 0 rows named a type that matches more than one application type, 239 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `code-review-graph-dispatch`: 0 rows named a type that matches more than one application type, 239 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codegraph`: 0 rows named a type that matches more than one application type, 17 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codegraph-dispatch`: 0 rows named a type that matches more than one application type, 17 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `codeql`: 0 rows named a type that matches more than one application type, 87 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `gitnexus`: 0 rows named a type that matches more than one application type, 18 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.
- `graphify`: 0 rows named a type that matches more than one application type, 16 named a type outside the application or one that could not be placed. Both are excluded from the numbers above rather than counted for or against — see `docs/PROTOCOL.md` §5.

## Uniquely-linked call resolution — the number that separates the tools

Of the 204 link groups where the language admits **exactly one**
target, what did each tool actually return? A set where one answer exists is not a win, and a
wrong single answer is worse than an honest set — so the five outcomes are kept apart rather
than folded into one rate.

| tool | exact | over_fan | partial | polluted | ancestor | wrong | unknown | unplaced | missed | n | exact rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | 103 | 0 | 0 | 0 | 0 | 0 | 91 | 0 | 10 | 204 | 50.5% |
| `cha-null` | 204 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 204 | 100.0% |
| `code-review-graph` | 147 | 0 | 0 | 5 | 0 | 27 | 8 | 0 | 17 | 204 | 72.1% |
| `code-review-graph-dispatch` | 147 | 0 | 0 | 5 | 0 | 27 | 8 | 0 | 17 | 204 | 72.1% |
| `codegraph` | 169 | 0 | 0 | 0 | 0 | 2 | 11 | 1 | 21 | 204 | 82.8% |
| `codegraph-dispatch` | 169 | 0 | 0 | 0 | 0 | 2 | 11 | 1 | 21 | 204 | 82.8% |
| `codeql` | 95 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 109 | 204 | 46.6% |
| `gitnexus` | 98 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 106 | 204 | 48.0% |
| `graphify` | 116 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 87 | 204 | 56.9% |
| `ideal` | 204 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 204 | 100.0% |

`exact` the one right method, alone · `over_fan` right method plus others, all sound ·
`polluted` right method plus something no envelope admits · `ancestor` named only a supertype
that declares the member (weaker, not fabricated) · `wrong` answered, none of it defensible ·
`missed` returned nothing.

## Genuinely ambiguous call resolution

The other 2 groups, where dispatch really does admit several
targets. Here `over_fan` is the *correct* behaviour and `exact` may mean the tool guessed one
branch and dropped the rest — so this table is read differently from the one above, and that
is exactly why they are not combined.

2 of these groups (5 call sites) are not dispatch either: several one-target
calls of the same name in one method — `new A()` and `new B()`, `getProject()` on two receivers —
pooled under one key (#70). Each call has exactly one target; a tool that names some of them
but not all reads `partial` here, all of them `exact`.

| tool | exact | over_fan | partial | polluted | ancestor | wrong | unknown | unplaced | missed | n | exact rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0.0% |
| `cha-null` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 100.0% |
| `code-review-graph` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 50.0% |
| `code-review-graph-dispatch` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 50.0% |
| `codegraph` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0.0% |
| `codegraph-dispatch` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0.0% |
| `codeql` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0.0% |
| `gitnexus` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0.0% |
| `graphify` | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0.0% |
| `ideal` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 100.0% |

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
| `axiom` | source only | 0.505 | 1.000 | 1.000 | 0.50× | 0.384 | 1.000 | 1.000 | 0.38× | 0.337 | 1.000 | 1.000 | 0.34× |
| `code-review-graph` | source only | 0.745 | 0.891 | 0.767 | 0.84× | 0.641 | 0.833 | 0.737 | 0.77× | 0.587 | 0.798 | 0.718 | 0.74× |
| `code-review-graph-dispatch` | source only | 0.745 | 0.891 | 0.767 | 0.84× | 0.641 | 0.833 | 0.737 | 0.77× | 0.587 | 0.798 | 0.718 | 0.74× |
| `codegraph` | source only | 0.663 | 0.767 | 0.939 | 0.87× | 0.610 | 0.682 | 0.890 | 0.89× | 0.575 | 0.493 | 0.775 | 1.17× |
| `codegraph-dispatch` | source only | 0.663 | 0.767 | 0.939 | 0.87× | 0.610 | 0.682 | 0.890 | 0.89× | 0.575 | 0.493 | 0.775 | 1.17× |
| `codeql` | source only | 0.466 | 0.951 | 0.951 | 0.49× | 0.362 | 0.956 | 0.956 | 0.38× | 0.318 | 0.957 | 0.957 | 0.33× |
| `gitnexus` | source only | 0.481 | 0.990 | 0.990 | 0.49× | 0.368 | 0.985 | 0.985 | 0.37× | 0.323 | 0.986 | 0.986 | 0.33× |
| `graphify` | source only | 0.567 | 0.929 | 0.929 | 0.61× | 0.451 | 0.931 | 0.931 | 0.48× | 0.401 | 0.924 | 0.929 | 0.43× |
| *`cha-null`* | bytecode | 0.827 | 0.827 | 1.000 | 1.00× | 0.836 | 0.779 | 1.000 | 1.07× | 0.840 | 0.570 | 1.000 | 1.47× |
| *`ideal`* | oracle | 1.000 | 1.000 | 0.852 | 1.00× | 1.000 | 1.000 | 0.859 | 1.00× | 1.000 | 1.000 | 0.862 | 1.00× |

## Tier A (`type#name(params)`) — overload selection

Only tools whose output carries parameter types can be scored here. A dash is **not** a zero:
it means the tool's output format does not express the distinction, so the question was never
put to it.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 2s | 0.339 | 0.339 | 0.182 | 0.182 | 0.182 | 0.237 | 0.245 | 112 | 47 (0 ambig, 46 out-of-scope, 25% of emitted, 0 unspellable, 1 §4-excluded), 60 duplicate |
| `code-review-graph` | source only | 2s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `code-review-graph-dispatch` | source only | 2s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `codegraph` | source only | 1s | 0.167 | 0.156 | 0.134 | 0.144 | 0.144 | 0.144 | 0.139 | 180 | 18 (0 ambig, 17 out-of-scope, 7% of emitted, 0 unspellable, 1 §4-excluded), 44 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.167 | 0.156 | 0.134 | 0.144 | 0.144 | 0.144 | 0.139 | 180 | 18 (0 ambig, 17 out-of-scope, 7% of emitted, 0 unspellable, 1 §4-excluded), 44 duplicate |
| `codeql` | source only | 14s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `gitnexus` | source only | 12s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| `graphify` | source only | 1s | — | — | — | — | — | — | — | — | *output format cannot express tier A (declared ceiling: B)* |
| *`cha-null`* | bytecode | 0s | 1.000 | 0.828 | 0.828 | 1.000 | 1.000 | 0.828 | 0.827 | 209 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 0.828 | 0.828 | 1.000 | 1.000 | 209 | 0 |

## Tier C (`name`) — the floor

Method name only, no owner. Reported so that a name-only tool has a number at all. Read it
knowing that any two same-named methods in the subject are indistinguishable here, which
inflates every tool's score — the link-group table is **not** reported at this tier, because
its key is the callee name and every tool would score 100% by construction.

| tool | needs | time | precision | **prec-strict** | recall vs certain | recall vs possible | recall vs RTA | F1-strict | MCC-strict | edges scored | excluded |
|---|:--|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `axiom` | source only | 2s | 0.981 | 0.981 | 0.507 | 0.507 | 0.507 | 0.669 | 0.703 | 105 | 47 (0 ambig, 46 out-of-scope, 25% of emitted, 0 unspellable, 1 §4-excluded), 60 duplicate |
| `code-review-graph` | source only | 2s | 0.898 | 0.898 | 0.911 | 0.911 | 0.911 | 0.905 | 0.903 | 206 | 255 (0 ambig, 239 out-of-scope, 47% of emitted, 0 unspellable, 16 §4-excluded), 86 duplicate |
| `code-review-graph-dispatch` | source only | 2s | 0.898 | 0.898 | 0.911 | 0.911 | 0.911 | 0.905 | 0.903 | 206 | 255 (0 ambig, 239 out-of-scope, 47% of emitted, 0 unspellable, 16 §4-excluded), 86 duplicate |
| `codegraph` | source only | 1s | 0.961 | 0.961 | 0.847 | 0.847 | 0.847 | 0.901 | 0.901 | 179 | 18 (0 ambig, 17 out-of-scope, 7% of emitted, 0 unspellable, 1 §4-excluded), 44 duplicate |
| `codegraph-dispatch` | source only | 1s | 0.961 | 0.961 | 0.847 | 0.847 | 0.847 | 0.901 | 0.901 | 179 | 18 (0 ambig, 17 out-of-scope, 7% of emitted, 0 unspellable, 1 §4-excluded), 44 duplicate |
| `codeql` | source only | 14s | 0.848 | 0.848 | 0.468 | 0.468 | 0.468 | 0.603 | 0.627 | 112 | 122 (0 ambig, 87 out-of-scope, 32% of emitted, 0 unspellable, 35 §4-excluded), 119 duplicate |
| `gitnexus` | source only | 12s | 0.990 | 0.990 | 0.483 | 0.483 | 0.483 | 0.649 | 0.689 | 99 | 22 (0 ambig, 18 out-of-scope, 15% of emitted, 0 unspellable, 4 §4-excluded), 6 duplicate |
| `graphify` | source only | 1s | 0.929 | 0.929 | 0.581 | 0.581 | 0.581 | 0.715 | 0.732 | 127 | 17 (0 ambig, 16 out-of-scope, 11% of emitted, 0 unspellable, 1 §4-excluded) |
| *`cha-null`* | bytecode | 0s | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 203 | 0 |
| *`ideal`* | oracle | — | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 203 | 0 |

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
| `axiom` | `known_edge` | 182 | 0.981 | 0.981 | 103 | 0 | 0 | 0 | 0 |
| `code-review-graph` | `extracted` | 512 | 0.718 | 0.756 | 147 | 0 | 5 | 0 | 27 |
| `code-review-graph-dispatch` | `extracted` | 512 | 0.718 | 0.756 | 147 | 0 | 5 | 0 | 27 |
| `codegraph` | `calls|exact-match` | 231 | 0.950 | 0.767 | 169 | 0 | 0 | 0 | 2 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.40` | 6 | 0.000 | 0.000 | 0 | 0 | 0 | 0 | 1 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.70` | 8 | 0.833 | 0.833 | 3 | 0 | 0 | 0 | 1 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.90` | 217 | 0.971 | 0.778 | 166 | 0 | 0 | 0 | 0 |
| `codegraph` | `instantiates|exact-match` | 6 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.90` | 6 | — | — | 0 | 0 | 0 | 0 | 0 |
| `codegraph` | `instantiates|fuzzy` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|fuzzy:0.50` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `calls|exact-match` | 231 | 0.950 | 0.767 | 169 | 0 | 0 | 0 | 2 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.40` | 6 | 0.000 | 0.000 | 0 | 0 | 0 | 0 | 1 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.70` | 8 | 0.833 | 0.833 | 3 | 0 | 0 | 0 | 1 |
|  | &nbsp;&nbsp;↳ `calls|exact-match:0.90` | 217 | 0.971 | 0.778 | 166 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `instantiates|exact-match` | 6 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|exact-match:0.90` | 6 | — | — | 0 | 0 | 0 | 0 | 0 |
| `codegraph-dispatch` | `instantiates|fuzzy` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `instantiates|fuzzy:0.50` | 1 | — | — | 0 | 0 | 0 | 0 | 0 |
| `codeql` | `imprecision=0` | 268 | 0.851 | 0.851 | 95 | 0 | 0 | 0 | 0 |
| `gitnexus` | `callable-value-flow` | 8 | — | — | 0 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `callable-value-flow:0.70` | 8 | — | — | 0 | 0 | 0 | 0 | 0 |
| `gitnexus` | `import-resolved` | 51 | 0.979 | 0.979 | 45 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `import-resolved:0.85` | 51 | 0.979 | 0.979 | 45 | 0 | 0 | 0 | 0 |
| `gitnexus` | `local-call` | 64 | 1.000 | 1.000 | 53 | 0 | 0 | 0 | 0 |
|  | &nbsp;&nbsp;↳ `local-call:0.85` | 64 | 1.000 | 1.000 | 53 | 0 | 0 | 0 | 0 |
| `graphify` | `extracted` | 145 | 0.922 | 0.922 | 116 | 0 | 0 | 0 | 1 |

- `axiom` wrote 557 rows labelled `ambiguous_unknown` with no target — the tool says it could not resolve the call (read as `unknown`, not `missed`, #69), not scored
- `axiom` wrote 6 rows labelled `multi_inferred` with no target — a target-less row in the tool's own vocabulary, not scored

## Provenance

```json
{
  "input_sha256": {
    "classes": "c749928ff37abbb82b0b82bfb06181c066f24640e91b3ddd73bda6ccfcf60116",
    "edges/axiom": "969d6eb6d815f4c85de343c799dc3269062b42d712f09234868258b30a3f443f",
    "edges/cha-null": "deb1f8cb2c808e14b72e21d8b9167ff6d0c9008b83dcdbb1aceb5d6f3edfd2eb",
    "edges/code-review-graph": "1e3ae0e8bddd699b3935327ba036d2f14a1b196fa752d3aefd686fc5f261baca",
    "edges/code-review-graph-dispatch": "92dff569e1874ccaf44ad703b95413c44b5a21311f25964da4e663e0af8c36b5",
    "edges/codegraph": "2a8f660c142872811bddedbed8fdf3ddde9310bbd0f1f65d06299e789a97e09d",
    "edges/codegraph-dispatch": "e29bfbb6cd644f562e9a8ccd8cdfe45c17c2aecdf099fcbbf45d380d8221d9b3",
    "edges/codeql": "bbc1c3069691f774d5f377c14c80e7ae41631174c69bd187848f599f5b750e82",
    "edges/gitnexus": "40a09f0d6973e2eede7c889b6f2ff854e03f88d3d487189c0a1da4541b533729",
    "edges/graphify": "f99e34dfa6c0b0327172195a1a223426fc460f722573883c2381b80b8618b09e",
    "edges/ideal": "c598db39c8a6d4a40da220d38b7f2b739db7c9acb03f423b20b622ab890f9b95",
    "excluded": "8837f2b67d1fa34ee792d0778709a322152e167f89c667c8e67f873403676108",
    "heritage": "877a2640f3c5b9abe10abca3f1ed0feea56e2ddee64ad2a8e529e471d6355a6f",
    "methods": "18571cc1376d8c39f1950269dd0a00e56e872f51e53ed328e73bd786f5758af4",
    "sites": "df2b7e1a26ccebed463221589f3a62299989b8652653dafa7376f63c9213d599"
  },
  "language": "typescript",
  "platform": "Linux x86_64",
  "python": "3.12.3",
  "staged_copy": {
    "files": 21,
    "sha256": "c5c349eab09bae41f01e078b9e3a38aa0ae311a8ee6b25935ab02796142985c1"
  },
  "subject": "cheerio",
  "tools": {
    "axiom": {
      "build": "source only",
      "cache": "hit",
      "cold_seconds": 0.86,
      "engine_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "function_type_targets_dropped": 22,
      "note": "typescript front end, empty library",
      "parser_commit": "2163292b85d77c55f0df25a847c5100838e41ecb",
      "rows": 182,
      "rows_by_status": {
        "ambiguous_unknown": 557,
        "known_edge": 198,
        "multi_inferred": 6
      },
      "rows_without_method": 557,
      "seconds_breakdown": {
        "adapter_total": 1.75,
        "own": 0.62,
        "shared": 0.93,
        "staging": null
      },
      "source": ".work/typescript/cheerio/axiom/out/raw/call-chain-edges.csv",
      "unresolved_sites": [
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          269,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          300,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getAttr",
            "params": [
              "AnyNode",
              "string | undefined",
              "boolean"
            ],
            "type": "src/api/attributes"
          },
          59,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          200,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          207,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          479,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          494,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "params": [
              "DataElement"
            ],
            "type": "src/api/attributes"
          },
          548,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readData",
            "params": [
              "DataElement",
              "string"
            ],
            "type": "src/api/attributes"
          },
          577,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readData",
            "params": [
              "DataElement",
              "string"
            ],
            "type": "src/api/attributes"
          },
          581,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "params": [
              "string"
            ],
            "type": "src/api/attributes"
          },
          602,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "data",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          717,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeAttr",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          862,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          942,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          1010,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          1087,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "css",
            "params": [
              "",
              ""
            ],
            "type": "src/api/css"
          },
          81,
          "src/api/css.ts"
        ],
        [
          {
            "name": "getCss",
            "params": [
              "AnyNode",
              "string | string[]"
            ],
            "type": "src/api/css"
          },
          165,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string"
            ],
            "type": "src/api/css"
          },
          209,
          "src/api/css.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          90,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          345,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          702,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "closest",
            "params": [
              "AnyNode | null"
            ],
            "type": "src/api/traversing"
          },
          366,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "nextAll",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          426,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "prevAll",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          504,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "params": [
              "AnyNode | ArrayLike<AnyNode>"
            ],
            "type": "src/parsers/parse5-adapter"
          },
          54,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "isArrayLike",
            "params": [
              "unknown"
            ],
            "type": "src/static"
          },
          292,
          "src/static.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          10,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          11,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          12,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          15,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          16,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          19,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          31,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          34,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          34,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          36,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          38,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          45,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          51,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          53,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          53,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          57,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          60,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          61,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          63,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "params": [
              "string",
              "string",
              "SuiteOptions<T>"
            ],
            "type": "benchmark/benchmark"
          },
          63,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          68,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          72,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          78,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          80,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          81,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          89,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          90,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          97,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          98,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          105,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          106,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          111,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          113,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          114,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          115,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "setup",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          121,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "setup",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          121,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          124,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          124,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          129,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          131,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          135,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          137,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          138,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          142,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          144,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          149,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          152,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          152,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          155,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          157,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          158,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          166,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          167,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          170,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          171,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          174,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          175,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          178,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          179,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          182,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          183,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          186,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          187,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          190,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          191,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          194,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          195,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          198,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          199,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          202,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          203,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          206,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          207,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          210,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          211,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          214,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          215,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          218,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          219,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          219,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          222,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          223,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          223,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          226,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          227,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          227,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          234,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          236,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          237,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          238,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          245,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          247,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          248,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          249,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          254,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          256,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          257,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          261,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          263,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          264,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          264,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          265,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [],
            "type": "benchmark/benchmark"
          },
          265,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          271,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          272,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          275,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          276,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<arrow>",
            "params": [
              ""
            ],
            "type": "benchmark/benchmark"
          },
          282,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          284,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "params": [
              "",
              ""
            ],
            "type": "benchmark/benchmark"
          },
          285,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          72,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          76,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          141,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          144,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          147,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          149,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "params": [
              "any"
            ],
            "type": "scripts/fetch-sponsors"
          },
          152,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "params": [
              "string"
            ],
            "type": "scripts/fetch-sponsors"
          },
          169,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "params": [
              "string"
            ],
            "type": "scripts/fetch-sponsors"
          },
          170,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "params": [
              "string"
            ],
            "type": "scripts/fetch-sponsors"
          },
          171,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "params": [
              "string"
            ],
            "type": "scripts/fetch-sponsors"
          },
          171,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "params": [
              "string"
            ],
            "type": "scripts/fetch-sponsors"
          },
          172,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "params": [
              "string"
            ],
            "type": "scripts/fetch-sponsors"
          },
          172,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchGitHubSponsors",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          181,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchGitHubSponsors",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          221,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          253,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          254,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          260,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          271,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          276,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [
              "",
              ""
            ],
            "type": "scripts/fetch-sponsors"
          },
          276,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [
              "",
              ""
            ],
            "type": "scripts/fetch-sponsors"
          },
          276,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          285,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          284,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          292,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          294,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          297,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          302,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          312,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          312,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          315,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          317,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          327,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          336,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          340,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          340,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          346,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          348,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          348,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          348,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          366,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [
              "Sponsor"
            ],
            "type": "scripts/fetch-sponsors"
          },
          355,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "scripts/fetch-sponsors"
          },
          369,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getAttr",
            "params": [
              "AnyNode",
              "string | undefined",
              "boolean"
            ],
            "type": "src/api/attributes"
          },
          50,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getAttr",
            "params": [
              "AnyNode",
              "string | undefined",
              "boolean"
            ],
            "type": "src/api/attributes"
          },
          61,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | null>",
              "| string | null | ((this: Element, i: number, attrib: string) => string | null)"
            ],
            "type": "src/api/attributes"
          },
          196,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          200,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          204,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getProp",
            "params": [
              "Element",
              "string",
              "boolean"
            ],
            "type": "src/api/attributes"
          },
          240,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "setProp",
            "params": [
              "Element",
              "string",
              "unknown",
              "boolean"
            ],
            "type": "src/api/attributes"
          },
          262,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          410,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          414,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          415,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          426,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          445,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          452,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          456,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          460,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          460,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          460,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          460,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          464,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "Cheerio<T>",
              "string | Record<string, string | Element[keyof Element] | boolean>",
              "| (( this: Element, i: number, prop: string | undefined, ) => string | Element[keyof Element] | boolean) | unknown"
            ],
            "type": "src/api/attributes"
          },
          476,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          483,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          491,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "setData",
            "params": [
              "DataElement",
              "string | Record<string, unknown>",
              "unknown"
            ],
            "type": "src/api/attributes"
          },
          532,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "params": [
              "DataElement"
            ],
            "type": "src/api/attributes"
          },
          549,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "params": [
              "DataElement"
            ],
            "type": "src/api/attributes"
          },
          553,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "params": [
              "DataElement"
            ],
            "type": "src/api/attributes"
          },
          555,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "params": [
              "string"
            ],
            "type": "src/api/attributes"
          },
          600,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "params": [
              "string"
            ],
            "type": "src/api/attributes"
          },
          601,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "params": [
              "string"
            ],
            "type": "src/api/attributes"
          },
          604,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "data",
            "params": [
              "Cheerio<T>",
              "string | Record<string, unknown>",
              "unknown"
            ],
            "type": "src/api/attributes"
          },
          704,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          773,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          777,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          780,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          782,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          786,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          786,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          790,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          790,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          796,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          797,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          797,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          798,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          803,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "params": [
              "Cheerio<T>",
              "string | string[]"
            ],
            "type": "src/api/attributes"
          },
          804,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeAttribute",
            "params": [
              "Element",
              "string"
            ],
            "type": "src/api/attributes"
          },
          819,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "splitNames",
            "params": [
              "string"
            ],
            "type": "src/api/attributes"
          },
          832,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "splitNames",
            "params": [
              "string"
            ],
            "type": "src/api/attributes"
          },
          832,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "params": [
              "Cheerio<T>",
              "string"
            ],
            "type": "src/api/attributes"
          },
          894,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "params": [
              "Cheerio<T>",
              "string"
            ],
            "type": "src/api/attributes"
          },
          894,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          895,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          899,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          903,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          904,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          944,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          944,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "params": [
              "R",
              "| string | ((this: Element, i: number, className: string) => string | undefined)"
            ],
            "type": "src/api/attributes"
          },
          952,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "params": [
              "R",
              "| string | ((this: Element, i: number, className: string) => string | undefined)"
            ],
            "type": "src/api/attributes"
          },
          958,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "params": [
              "R",
              "| string | ((this: Element, i: number, className: string) => string | undefined)"
            ],
            "type": "src/api/attributes"
          },
          969,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "params": [
              "R",
              "| string | ((this: Element, i: number, className: string) => string | undefined)"
            ],
            "type": "src/api/attributes"
          },
          972,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "params": [
              "R",
              "| string | ((this: Element, i: number, className: string) => string | undefined)"
            ],
            "type": "src/api/attributes"
          },
          974,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "params": [
              "R",
              "| string | ((this: Element, i: number, className: string) => string | undefined)"
            ],
            "type": "src/api/attributes"
          },
          974,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          1011,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          1011,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          1021,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          1031,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          1034,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "params": [
              ""
            ],
            "type": "src/api/attributes"
          },
          1045,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          1088,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "params": [
              "",
              ""
            ],
            "type": "src/api/attributes"
          },
          1090,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "params": [
              "R",
              "| string | (( this: Element, i: number, className: string, stateVal?: boolean, ) => string)",
              "boolean"
            ],
            "type": "src/api/attributes"
          },
          1100,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "params": [
              "R",
              "| string | (( this: Element, i: number, className: string, stateVal?: boolean, ) => string)",
              "boolean"
            ],
            "type": "src/api/attributes"
          },
          1108,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "params": [
              "R",
              "| string | (( this: Element, i: number, className: string, stateVal?: boolean, ) => string)",
              "boolean"
            ],
            "type": "src/api/attributes"
          },
          1115,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "params": [
              "R",
              "| string | (( this: Element, i: number, className: string, stateVal?: boolean, ) => string)",
              "boolean"
            ],
            "type": "src/api/attributes"
          },
          1119,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "params": [
              "R",
              "| string | (( this: Element, i: number, className: string, stateVal?: boolean, ) => string)",
              "boolean"
            ],
            "type": "src/api/attributes"
          },
          1122,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "params": [
              "R",
              "| string | (( this: Element, i: number, className: string, stateVal?: boolean, ) => string)",
              "boolean"
            ],
            "type": "src/api/attributes"
          },
          1126,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "css",
            "params": [
              "Cheerio<T>",
              "string | string[] | Record<string, string>",
              "| string | ((this: Element, i: number, style: string) => string | undefined)"
            ],
            "type": "src/api/css"
          },
          78,
          "src/api/css.ts"
        ],
        [
          {
            "name": "setCss",
            "params": [
              "Element",
              "string | Record<string, string>",
              "| string | ((this: Element, i: number, style: string) => string | undefined) | undefined",
              "number"
            ],
            "type": "src/api/css"
          },
          117,
          "src/api/css.ts"
        ],
        [
          {
            "name": "setCss",
            "params": [
              "Element",
              "string | Record<string, string>",
              "| string | ((this: Element, i: number, style: string) => string | undefined) | undefined",
              "number"
            ],
            "type": "src/api/css"
          },
          127,
          "src/api/css.ts"
        ],
        [
          {
            "name": "getCss",
            "params": [
              "AnyNode",
              "string | string[]"
            ],
            "type": "src/api/css"
          },
          159,
          "src/api/css.ts"
        ],
        [
          {
            "name": "stringify",
            "params": [
              "Record<string, string>"
            ],
            "type": "src/api/css"
          },
          186,
          "src/api/css.ts"
        ],
        [
          {
            "name": "stringify",
            "params": [
              "Record<string, string>"
            ],
            "type": "src/api/css"
          },
          186,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string"
            ],
            "type": "src/api/css"
          },
          201,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string"
            ],
            "type": "src/api/css"
          },
          210,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string"
            ],
            "type": "src/api/css"
          },
          213,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string"
            ],
            "type": "src/api/css"
          },
          218,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string"
            ],
            "type": "src/api/css"
          },
          218,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string"
            ],
            "type": "src/api/css"
          },
          219,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string"
            ],
            "type": "src/api/css"
          },
          219,
          "src/api/css.ts"
        ],
        [
          {
            "name": "extract",
            "params": [
              "Cheerio<T>",
              "M"
            ],
            "type": "src/api/extract"
          },
          70,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "params": [
              "Element"
            ],
            "type": "src/api/extract"
          },
          78,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "params": [
              "Element"
            ],
            "type": "src/api/extract"
          },
          78,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "params": [
              "Element"
            ],
            "type": "src/api/extract"
          },
          79,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "params": [
              "Element"
            ],
            "type": "src/api/extract"
          },
          79,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "params": [
              "Cheerio<T>",
              "M"
            ],
            "type": "src/api/extract"
          },
          82,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "params": [
              "Cheerio<T>",
              "M"
            ],
            "type": "src/api/extract"
          },
          82,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "params": [
              "Cheerio<T>",
              "M"
            ],
            "type": "src/api/extract"
          },
          82,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "params": [
              "Cheerio<T>",
              "M"
            ],
            "type": "src/api/extract"
          },
          86,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "serialize",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/forms"
          },
          28,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/forms"
          },
          31,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "retArr",
            "params": [
              ""
            ],
            "type": "src/api/forms"
          },
          33,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "retArr",
            "params": [
              ""
            ],
            "type": "src/api/forms"
          },
          33,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/forms"
          },
          37,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/forms"
          },
          37,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/forms"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/forms"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/forms"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/forms"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          62,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          63,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          64,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          64,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          66,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          66,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          84,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          85,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          87,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          91,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              ""
            ],
            "type": "src/api/forms"
          },
          96,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "params": [
              "",
              ""
            ],
            "type": "src/api/forms"
          },
          100,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode> | BasicAcceptedElems<AnyNode>[]",
              "boolean"
            ],
            "type": "src/api/manipulation"
          },
          44,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode> | BasicAcceptedElems<AnyNode>[]",
              "boolean"
            ],
            "type": "src/api/manipulation"
          },
          44,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode> | BasicAcceptedElems<AnyNode>[]",
              "boolean"
            ],
            "type": "src/api/manipulation"
          },
          49,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode> | BasicAcceptedElems<AnyNode>[]",
              "boolean"
            ],
            "type": "src/api/manipulation"
          },
          63,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode> | BasicAcceptedElems<AnyNode>[]",
              "boolean"
            ],
            "type": "src/api/manipulation"
          },
          63,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode> | BasicAcceptedElems<AnyNode>[]",
              "boolean"
            ],
            "type": "src/api/manipulation"
          },
          68,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode> | BasicAcceptedElems<AnyNode>[]",
              "boolean"
            ],
            "type": "src/api/manipulation"
          },
          68,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode> | BasicAcceptedElems<AnyNode>[]",
              "boolean"
            ],
            "type": "src/api/manipulation"
          },
          74,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          99,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          103,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          103,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          106,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "params": [
              "AnyNode[]",
              "number",
              "number",
              "AnyNode[]",
              "ParentNode"
            ],
            "type": "src/api/manipulation"
          },
          153,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "params": [
              "AnyNode[]",
              "number",
              "number",
              "AnyNode[]",
              "ParentNode"
            ],
            "type": "src/api/manipulation"
          },
          156,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "params": [
              "AnyNode[]",
              "number",
              "number",
              "AnyNode[]",
              "ParentNode"
            ],
            "type": "src/api/manipulation"
          },
          183,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "appendTo",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          211,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "appendTo",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          213,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "prependTo",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          244,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "prependTo",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          246,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          319,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          319,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          326,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          328,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          328,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          331,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          333,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrap",
            "params": [
              "",
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          412,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapInner",
            "params": [
              "",
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          470,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "params": [
              "Cheerio<T>",
              "string"
            ],
            "type": "src/api/manipulation"
          },
          518,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "params": [
              "Cheerio<T>",
              "string"
            ],
            "type": "src/api/manipulation"
          },
          518,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "params": [
              "Cheerio<T>",
              "string"
            ],
            "type": "src/api/manipulation"
          },
          518,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          521,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          521,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<T>"
            ],
            "type": "src/api/manipulation"
          },
          583,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<T>"
            ],
            "type": "src/api/manipulation"
          },
          583,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<T>"
            ],
            "type": "src/api/manipulation"
          },
          584,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<T>"
            ],
            "type": "src/api/manipulation"
          },
          610,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "params": [
              "Cheerio<T>",
              "AcceptedElems<T>"
            ],
            "type": "src/api/manipulation"
          },
          610,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          646,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          651,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          659,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          659,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          662,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          695,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          698,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          703,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          703,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          710,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          718,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          721,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          755,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          760,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          768,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          768,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          771,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          803,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          805,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          810,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          810,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          817,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          825,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "params": [
              "Cheerio<T>",
              "BasicAcceptedElems<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          828,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "remove",
            "params": [
              "Cheerio<T>",
              "string"
            ],
            "type": "src/api/manipulation"
          },
          856,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "remove",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          859,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          899,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          900,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          908,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          913,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "empty",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          937,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          989,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<AnyNode>"
            ],
            "type": "src/api/manipulation"
          },
          990,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          994,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          1000,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          1001,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "toString",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/manipulation"
          },
          1014,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          1069,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          1069,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "params": [
              "",
              ""
            ],
            "type": "src/api/manipulation"
          },
          1069,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          1075,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          1080,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/manipulation"
          },
          1100,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/manipulation"
          },
          1100,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "params": [
              ""
            ],
            "type": "src/api/manipulation"
          },
          1101,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/manipulation"
          },
          1105,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/manipulation"
          },
          1110,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "find",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<Element> | Element"
            ],
            "type": "src/api/traversing"
          },
          52,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<Element> | Element"
            ],
            "type": "src/api/traversing"
          },
          57,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<Element> | Element"
            ],
            "type": "src/api/traversing"
          },
          60,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<Element> | Element"
            ],
            "type": "src/api/traversing"
          },
          62,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<Element> | Element"
            ],
            "type": "src/api/traversing"
          },
          63,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          63,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<Element> | Element"
            ],
            "type": "src/api/traversing"
          },
          67,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "params": [
              "Cheerio<T>",
              "string",
              "number"
            ],
            "type": "src/api/traversing"
          },
          84,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "params": [
              "Cheerio<T>",
              "string",
              "number"
            ],
            "type": "src/api/traversing"
          },
          86,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "params": [
              "Cheerio<T>",
              "string",
              "number"
            ],
            "type": "src/api/traversing"
          },
          88,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "params": [
              "Cheerio<T>",
              "string",
              "number"
            ],
            "type": "src/api/traversing"
          },
          88,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "params": [
              "Cheerio<T>",
              "string",
              "number"
            ],
            "type": "src/api/traversing"
          },
          102,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "params": [
              "Cheerio<T>",
              "string",
              "number"
            ],
            "type": "src/api/traversing"
          },
          102,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<Element>"
            ],
            "type": "src/api/traversing"
          },
          136,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<Element>"
            ],
            "type": "src/api/traversing"
          },
          139,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "",
              ""
            ],
            "type": "src/api/traversing"
          },
          139,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matcher",
            "params": [
              "(elem: AnyNode) => Element[]",
              ""
            ],
            "type": "src/api/traversing"
          },
          152,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_singleMatcher",
            "params": [
              "(elem: AnyNode) => Element | null",
              ""
            ],
            "type": "src/api/traversing"
          },
          166,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "params": [
              "(elem: AnyNode) => Element | null",
              "((elems: Element[]) => Element[])[]"
            ],
            "type": "src/api/traversing"
          },
          187,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "innerMatcher",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          195,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Element"
            ],
            "type": "src/api/traversing"
          },
          211,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<function-expression>",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<Element> | null",
              "AcceptedFilters<Element>"
            ],
            "type": "src/api/traversing"
          },
          216,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_removeDuplicates",
            "params": [
              "T[]"
            ],
            "type": "src/api/traversing"
          },
          226,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_removeDuplicates",
            "params": [
              "T[]"
            ],
            "type": "src/api/traversing"
          },
          226,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "src/api/traversing"
          },
          248,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "parent",
            "params": [
              "",
              ""
            ],
            "type": "src/api/traversing"
          },
          249,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "src/api/traversing"
          },
          274,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "parents",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          277,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "parents",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          278,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "parents",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          284,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "parentsUntil",
            "params": [
              "",
              ""
            ],
            "type": "src/api/traversing"
          },
          310,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "parentsUntil",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          312,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<Element>"
            ],
            "type": "src/api/traversing"
          },
          348,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "params": [
              "Element"
            ],
            "type": "src/api/traversing"
          },
          358,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "params": [
              "AnyNode | null"
            ],
            "type": "src/api/traversing"
          },
          362,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "params": [
              "AnyNode | null"
            ],
            "type": "src/api/traversing"
          },
          362,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "params": [
              "AnyNode | null"
            ],
            "type": "src/api/traversing"
          },
          365,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "params": [
              "AnyNode | null"
            ],
            "type": "src/api/traversing"
          },
          368,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "params": [
              "AnyNode | null"
            ],
            "type": "src/api/traversing"
          },
          369,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<Element>"
            ],
            "type": "src/api/traversing"
          },
          377,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "src/api/traversing"
          },
          399,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "next",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          399,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "src/api/traversing"
          },
          422,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "nextAll",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          426,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "nextUntil",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          453,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "src/api/traversing"
          },
          476,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "prev",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          476,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "src/api/traversing"
          },
          500,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "prevAll",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          504,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "prevUntil",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          531,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "src/api/traversing"
          },
          557,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "siblings",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          559,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "siblings",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          559,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "siblings",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          559,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "src/api/traversing"
          },
          584,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "children",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          585,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "children",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          585,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/traversing"
          },
          607,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/traversing"
          },
          607,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "elems",
            "params": [
              "",
              ""
            ],
            "type": "src/api/traversing"
          },
          609,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "elems",
            "params": [
              "",
              ""
            ],
            "type": "src/api/traversing"
          },
          609,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/traversing"
          },
          612,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "each",
            "params": [
              "Cheerio<T>",
              "(this: T, i: number, el: T) => void | boolean"
            ],
            "type": "src/api/traversing"
          },
          646,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "params": [
              "Cheerio<T>",
              "(this: T, i: number, el: T) => M[] | M | null | undefined"
            ],
            "type": "src/api/traversing"
          },
          683,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "params": [
              "Cheerio<T>",
              "(this: T, i: number, el: T) => M[] | M | null | undefined"
            ],
            "type": "src/api/traversing"
          },
          685,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "params": [
              "Cheerio<T>",
              "(this: T, i: number, el: T) => M[] | M | null | undefined"
            ],
            "type": "src/api/traversing"
          },
          688,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "getFilterFn",
            "params": [
              "",
              ""
            ],
            "type": "src/api/traversing"
          },
          701,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "getFilterFn",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          704,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filter",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          782,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filter",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          783,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filterArray",
            "params": [
              "T[]",
              "AcceptedFilters<T>",
              "boolean",
              "Document"
            ],
            "type": "src/api/traversing"
          },
          794,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filterArray",
            "params": [
              "T[]",
              "AcceptedFilters<T>",
              "boolean",
              "Document"
            ],
            "type": "src/api/traversing"
          },
          795,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          814,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          816,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          817,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          822,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          862,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          865,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          865,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          866,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "params": [
              ""
            ],
            "type": "src/api/traversing"
          },
          866,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          869,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "params": [
              "Cheerio<T>",
              "AcceptedFilters<T>"
            ],
            "type": "src/api/traversing"
          },
          872,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "has",
            "params": [
              "Cheerio<AnyNode | Element>",
              "string | Cheerio<Element> | Element"
            ],
            "type": "src/api/traversing"
          },
          903,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "has",
            "params": [
              "",
              ""
            ],
            "type": "src/api/traversing"
          },
          907,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "has",
            "params": [
              "",
              ""
            ],
            "type": "src/api/traversing"
          },
          907,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "first",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/traversing"
          },
          926,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "last",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/traversing"
          },
          944,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "eq",
            "params": [
              "Cheerio<T>",
              "number"
            ],
            "type": "src/api/traversing"
          },
          973,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "get",
            "params": [
              "Cheerio<T>",
              "number"
            ],
            "type": "src/api/traversing"
          },
          1010,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "toArray",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/traversing"
          },
          1028,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<AnyNode> | AnyNode"
            ],
            "type": "src/api/traversing"
          },
          1057,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<AnyNode> | AnyNode"
            ],
            "type": "src/api/traversing"
          },
          1057,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<AnyNode> | AnyNode"
            ],
            "type": "src/api/traversing"
          },
          1060,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<AnyNode> | AnyNode"
            ],
            "type": "src/api/traversing"
          },
          1070,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "slice",
            "params": [
              "Cheerio<T>",
              "number",
              "number"
            ],
            "type": "src/api/traversing"
          },
          1100,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "slice",
            "params": [
              "Cheerio<T>",
              "number",
              "number"
            ],
            "type": "src/api/traversing"
          },
          1100,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "end",
            "params": [
              "Cheerio<T>"
            ],
            "type": "src/api/traversing"
          },
          1119,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<S> | S | S[]",
              "Cheerio<S> | string"
            ],
            "type": "src/api/traversing"
          },
          1143,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<S> | S | S[]",
              "Cheerio<S> | string"
            ],
            "type": "src/api/traversing"
          },
          1144,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<S> | S | S[]",
              "Cheerio<S> | string"
            ],
            "type": "src/api/traversing"
          },
          1144,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<S> | S | S[]",
              "Cheerio<S> | string"
            ],
            "type": "src/api/traversing"
          },
          1144,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "params": [
              "Cheerio<T>",
              "string | Cheerio<S> | S | S[]",
              "Cheerio<S> | string"
            ],
            "type": "src/api/traversing"
          },
          1145,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "addBack",
            "params": [
              "Cheerio<T>",
              "string"
            ],
            "type": "src/api/traversing"
          },
          1169,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "addBack",
            "params": [
              "Cheerio<T>",
              "string"
            ],
            "type": "src/api/traversing"
          },
          1169,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "src/cheerio"
          },
          135,
          "src/cheerio.ts"
        ],
        [
          {
            "name": "loadBuffer",
            "params": [
              "Buffer",
              "DecodeStreamOptions"
            ],
            "type": "src/index"
          },
          58,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "params": [
              "InternalOptions | undefined",
              "(err: Error | null | undefined, $: CheerioAPI) => void"
            ],
            "type": "src/index"
          },
          71,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "params": [
              "InternalOptions | undefined",
              "(err: Error | null | undefined, $: CheerioAPI) => void"
            ],
            "type": "src/index"
          },
          76,
          "src/index.ts"
        ],
        [
          {
            "name": "write",
            "params": [
              "",
              "",
              ""
            ],
            "type": "src/index"
          },
          80,
          "src/index.ts"
        ],
        [
          {
            "name": "write",
            "params": [
              "",
              "",
              ""
            ],
            "type": "src/index"
          },
          83,
          "src/index.ts"
        ],
        [
          {
            "name": "write",
            "params": [
              "",
              "",
              ""
            ],
            "type": "src/index"
          },
          84,
          "src/index.ts"
        ],
        [
          {
            "name": "final",
            "params": [
              ""
            ],
            "type": "src/index"
          },
          87,
          "src/index.ts"
        ],
        [
          {
            "name": "final",
            "params": [
              ""
            ],
            "type": "src/index"
          },
          88,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "params": [
              "InternalOptions | undefined",
              "(err: Error | null | undefined, $: CheerioAPI) => void"
            ],
            "type": "src/index"
          },
          100,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "params": [
              "InternalOptions | undefined",
              "(err: Error | null | undefined, $: CheerioAPI) => void"
            ],
            "type": "src/index"
          },
          102,
          "src/index.ts"
        ],
        [
          {
            "name": "decodeStream",
            "params": [
              "DecodeStreamOptions",
              "(err: Error | null | undefined, $: CheerioAPI) => void"
            ],
            "type": "src/index"
          },
          170,
          "src/index.ts"
        ],
        [
          {
            "name": "decodeStream",
            "params": [
              "DecodeStreamOptions",
              "(err: Error | null | undefined, $: CheerioAPI) => void"
            ],
            "type": "src/index"
          },
          173,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "params": [
              "string | URL",
              "CheerioRequestOptions"
            ],
            "type": "src/index"
          },
          229,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "params": [
              "",
              ""
            ],
            "type": "src/index"
          },
          230,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "params": [
              ""
            ],
            "type": "src/index"
          },
          232,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "params": [
              ""
            ],
            "type": "src/index"
          },
          233,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "params": [
              ""
            ],
            "type": "src/index"
          },
          236,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "params": [
              ""
            ],
            "type": "src/index"
          },
          236,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "params": [
              ""
            ],
            "type": "src/index"
          },
          237,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "params": [
              ""
            ],
            "type": "src/index"
          },
          243,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "params": [
              ""
            ],
            "type": "src/index"
          },
          260,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "params": [
              "",
              ""
            ],
            "type": "src/index"
          },
          266,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "params": [
              "",
              ""
            ],
            "type": "src/index"
          },
          266,
          "src/index.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "",
              "",
              "",
              ""
            ],
            "type": "src/load-parse"
          },
          11,
          "src/load-parse.ts"
        ],
        [
          {
            "name": "load",
            "params": [
              "",
              ""
            ],
            "type": "src/load-parse"
          },
          37,
          "src/load-parse.ts"
        ],
        [
          {
            "name": "load",
            "params": [
              "string | AnyNode | AnyNode[] | Buffer",
              "CheerioOptions | null",
              ""
            ],
            "type": "src/load"
          },
          133,
          "src/load.ts"
        ],
        [
          {
            "name": "load",
            "params": [
              "string | AnyNode | AnyNode[] | Buffer",
              "CheerioOptions | null",
              ""
            ],
            "type": "src/load"
          },
          137,
          "src/load.ts"
        ],
        [
          {
            "name": "_parse",
            "params": [
              "string | Document | AnyNode | AnyNode[] | Buffer",
              "InternalOptions",
              "boolean",
              "ParentNode | null"
            ],
            "type": "src/load#LoadedCheerio"
          },
          160,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "params": [
              "ArrayLike<T> | T | S",
              "BasicAcceptedElems<AnyNode> | null",
              "BasicAcceptedElems<Document>",
              "CheerioOptions"
            ],
            "type": "src/load"
          },
          182,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "params": [
              "ArrayLike<T> | T | S",
              "BasicAcceptedElems<AnyNode> | null",
              "BasicAcceptedElems<Document>",
              "CheerioOptions"
            ],
            "type": "src/load"
          },
          200,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "params": [
              "ArrayLike<T> | T | S",
              "BasicAcceptedElems<AnyNode> | null",
              "BasicAcceptedElems<Document>",
              "CheerioOptions"
            ],
            "type": "src/load"
          },
          204,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "params": [
              "ArrayLike<T> | T | S",
              "BasicAcceptedElems<AnyNode> | null",
              "BasicAcceptedElems<Document>",
              "CheerioOptions"
            ],
            "type": "src/load"
          },
          216,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "params": [
              "ArrayLike<T> | T | S",
              "BasicAcceptedElems<AnyNode> | null",
              "BasicAcceptedElems<Document>",
              "CheerioOptions"
            ],
            "type": "src/load"
          },
          228,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "params": [
              "ArrayLike<T> | T | S",
              "BasicAcceptedElems<AnyNode> | null",
              "BasicAcceptedElems<Document>",
              "CheerioOptions"
            ],
            "type": "src/load"
          },
          239,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "params": [
              "ArrayLike<T> | T | S",
              "BasicAcceptedElems<AnyNode> | null",
              "BasicAcceptedElems<Document>",
              "CheerioOptions"
            ],
            "type": "src/load"
          },
          251,
          "src/load.ts"
        ],
        [
          {
            "name": "load",
            "params": [
              "string | AnyNode | AnyNode[] | Buffer",
              "CheerioOptions | null",
              ""
            ],
            "type": "src/load"
          },
          255,
          "src/load.ts"
        ],
        [
          {
            "name": "flattenOptions",
            "params": [
              "CheerioOptions | null",
              "InternalOptions"
            ],
            "type": "src/options"
          },
          128,
          "src/options.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string | Document | AnyNode | AnyNode[] | Buffer",
              "InternalOptions",
              "boolean",
              "ParentNode | null"
            ],
            "type": "src/parse"
          },
          39,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string | Document | AnyNode | AnyNode[] | Buffer",
              "InternalOptions",
              "boolean",
              "ParentNode | null"
            ],
            "type": "src/parse"
          },
          40,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string | Document | AnyNode | AnyNode[] | Buffer",
              "InternalOptions",
              "boolean",
              "ParentNode | null"
            ],
            "type": "src/parse"
          },
          49,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string | Document | AnyNode | AnyNode[] | Buffer",
              "InternalOptions",
              "boolean",
              "ParentNode | null"
            ],
            "type": "src/parse"
          },
          49,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "params": [
              "string | Document | AnyNode | AnyNode[] | Buffer",
              "InternalOptions",
              "boolean",
              "ParentNode | null"
            ],
            "type": "src/parse"
          },
          55,
          "src/parse.ts"
        ],
        [
          {
            "name": "update",
            "params": [
              "AnyNode[] | AnyNode",
              "ParentNode | null"
            ],
            "type": "src/parse"
          },
          76,
          "src/parse.ts"
        ],
        [
          {
            "name": "update",
            "params": [
              "AnyNode[] | AnyNode",
              "ParentNode | null"
            ],
            "type": "src/parse"
          },
          91,
          "src/parse.ts"
        ],
        [
          {
            "name": "parseWithParse5",
            "params": [
              "string",
              "InternalOptions",
              "boolean",
              "ParentNode | null"
            ],
            "type": "src/parsers/parse5-adapter"
          },
          33,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "parseWithParse5",
            "params": [
              "string",
              "InternalOptions",
              "boolean",
              "ParentNode | null"
            ],
            "type": "src/parsers/parse5-adapter"
          },
          34,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "params": [
              "AnyNode | ArrayLike<AnyNode>"
            ],
            "type": "src/parsers/parse5-adapter"
          },
          55,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "params": [
              "AnyNode | ArrayLike<AnyNode>"
            ],
            "type": "src/parsers/parse5-adapter"
          },
          62,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "render",
            "params": [
              "CheerioAPI",
              "BasicAcceptedElems<AnyNode> | undefined",
              "InternalOptions"
            ],
            "type": "src/static"
          },
          28,
          "src/static.ts"
        ],
        [
          {
            "name": "text",
            "params": [
              "CheerioAPI | void",
              "ArrayLike<AnyNode>"
            ],
            "type": "src/static"
          },
          128,
          "src/static.ts"
        ],
        [
          {
            "name": "text",
            "params": [
              "CheerioAPI | void",
              "ArrayLike<AnyNode>"
            ],
            "type": "src/static"
          },
          133,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "params": [
              "CheerioAPI",
              "string | null",
              "unknown | boolean",
              ""
            ],
            "type": "src/static"
          },
          173,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "params": [
              "CheerioAPI",
              "string | null",
              "unknown | boolean",
              ""
            ],
            "type": "src/static"
          },
          175,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "params": [
              "CheerioAPI",
              "string | null",
              "unknown | boolean",
              ""
            ],
            "type": "src/static"
          },
          175,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "params": [
              "CheerioAPI",
              "string | null",
              "unknown | boolean",
              ""
            ],
            "type": "src/static"
          },
          185,
          "src/static.ts"
        ],
        [
          {
            "name": "root",
            "params": [
              "CheerioAPI"
            ],
            "type": "src/static"
          },
          204,
          "src/static.ts"
        ],
        [
          {
            "name": "extract",
            "params": [
              "CheerioAPI",
              "M"
            ],
            "type": "src/static"
          },
          252,
          "src/static.ts"
        ],
        [
          {
            "name": "extract",
            "params": [
              "CheerioAPI",
              "M"
            ],
            "type": "src/static"
          },
          252,
          "src/static.ts"
        ],
        [
          {
            "name": "camelCase",
            "params": [
              "string"
            ],
            "type": "src/utils"
          },
          24,
          "src/utils.ts"
        ],
        [
          {
            "name": "camelCase",
            "params": [
              "",
              ""
            ],
            "type": "src/utils"
          },
          24,
          "src/utils.ts"
        ],
        [
          {
            "name": "cssCase",
            "params": [
              "string"
            ],
            "type": "src/utils"
          },
          37,
          "src/utils.ts"
        ],
        [
          {
            "name": "cssCase",
            "params": [
              "string"
            ],
            "type": "src/utils"
          },
          37,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "params": [
              "string"
            ],
            "type": "src/utils"
          },
          81,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "params": [
              "string"
            ],
            "type": "src/utils"
          },
          85,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "params": [
              "string"
            ],
            "type": "src/utils"
          },
          91,
          "src/utils.ts"
        ],
        [
          {
            "name": "<module>",
            "params": [],
            "type": "vitest.config"
          },
          3,
          "vitest.config.ts"
        ]
      ]
    },
    "cha-null": {
      "build": "bytecode",
      "null_model": true,
      "reference": "null",
      "rows": 209,
      "version": "CHA envelope (no resolution)"
    },
    "code-review-graph": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 1.11,
      "declared_unresolved": 367,
      "fanned_rows": 0,
      "rows": 512,
      "seconds_breakdown": {
        "adapter_total": 1.59,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/cheerio/crg/data/graph.db",
      "unresolved_sites": [
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          31,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          34,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          36,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          42,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          45,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          53,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          53,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          57,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          60,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          61,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          63,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          113,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          114,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          115,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "setup",
            "type": "benchmark/benchmark.ts"
          },
          121,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "setup",
            "type": "benchmark/benchmark.ts"
          },
          121,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          124,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          124,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          131,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          137,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          138,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          144,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          157,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          158,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          236,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          237,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          238,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          247,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          248,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          249,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          256,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          257,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          263,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          264,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          264,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          265,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          265,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          284,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          285,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          50,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          59,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          61,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          200,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          200,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          204,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          207,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getProp",
            "type": "src/api/attributes.ts"
          },
          240,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "setProp",
            "type": "src/api/attributes.ts"
          },
          262,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          410,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          414,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          415,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          426,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          452,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          456,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          460,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          460,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          460,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          479,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          483,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          491,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          494,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "setData",
            "type": "src/api/attributes.ts"
          },
          532,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          548,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          549,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          553,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          555,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readData",
            "type": "src/api/attributes.ts"
          },
          577,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readData",
            "type": "src/api/attributes.ts"
          },
          581,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          600,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          601,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          602,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          604,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "data",
            "type": "src/api/attributes.ts"
          },
          704,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "data",
            "type": "src/api/attributes.ts"
          },
          717,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          773,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          777,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          780,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          782,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          786,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          790,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          796,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          797,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          797,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          803,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          804,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeAttribute",
            "type": "src/api/attributes.ts"
          },
          819,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "splitNames",
            "type": "src/api/attributes.ts"
          },
          832,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "splitNames",
            "type": "src/api/attributes.ts"
          },
          832,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeAttr",
            "type": "src/api/attributes.ts"
          },
          862,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          894,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          894,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          895,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          899,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          903,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          904,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          942,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          944,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          952,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          958,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          969,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          972,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          974,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          974,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1010,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1011,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1021,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1031,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1034,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1045,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1087,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1088,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1090,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1100,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1108,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1115,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1119,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1122,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1126,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "css",
            "type": "src/api/css.ts"
          },
          78,
          "src/api/css.ts"
        ],
        [
          {
            "name": "css",
            "type": "src/api/css.ts"
          },
          81,
          "src/api/css.ts"
        ],
        [
          {
            "name": "setCss",
            "type": "src/api/css.ts"
          },
          117,
          "src/api/css.ts"
        ],
        [
          {
            "name": "setCss",
            "type": "src/api/css.ts"
          },
          127,
          "src/api/css.ts"
        ],
        [
          {
            "name": "getCss",
            "type": "src/api/css.ts"
          },
          159,
          "src/api/css.ts"
        ],
        [
          {
            "name": "getCss",
            "type": "src/api/css.ts"
          },
          165,
          "src/api/css.ts"
        ],
        [
          {
            "name": "stringify",
            "type": "src/api/css.ts"
          },
          186,
          "src/api/css.ts"
        ],
        [
          {
            "name": "stringify",
            "type": "src/api/css.ts"
          },
          186,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          201,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          209,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          210,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          213,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          218,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          218,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          219,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          219,
          "src/api/css.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          70,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          78,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          79,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          82,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          82,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          82,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          83,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          86,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          87,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          28,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          31,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          33,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          37,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          37,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          62,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          63,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          64,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          64,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          66,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          66,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          84,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          85,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          87,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          90,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          91,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          96,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          100,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          44,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          44,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          49,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          63,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          63,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          68,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          68,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          74,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          99,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          103,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          103,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          107,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          153,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          156,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          183,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "appendTo",
            "type": "src/api/manipulation.ts"
          },
          211,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "appendTo",
            "type": "src/api/manipulation.ts"
          },
          213,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "prependTo",
            "type": "src/api/manipulation.ts"
          },
          244,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "prependTo",
            "type": "src/api/manipulation.ts"
          },
          246,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          319,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          319,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          326,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          328,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          331,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          333,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          345,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          353,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "type": "src/api/manipulation.ts"
          },
          518,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "type": "src/api/manipulation.ts"
          },
          518,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "type": "src/api/manipulation.ts"
          },
          518,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "type": "src/api/manipulation.ts"
          },
          521,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "type": "src/api/manipulation.ts"
          },
          583,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "type": "src/api/manipulation.ts"
          },
          584,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "type": "src/api/manipulation.ts"
          },
          610,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "type": "src/api/manipulation.ts"
          },
          610,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          646,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          651,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          659,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          659,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          695,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          698,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          702,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          703,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          703,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          710,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          718,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          721,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          755,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          760,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          768,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          768,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          803,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          805,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          810,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          810,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          817,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          825,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          828,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "remove",
            "type": "src/api/manipulation.ts"
          },
          856,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "remove",
            "type": "src/api/manipulation.ts"
          },
          859,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          899,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          900,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          908,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          913,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "empty",
            "type": "src/api/manipulation.ts"
          },
          937,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          989,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          990,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          994,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          1000,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          1001,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "toString",
            "type": "src/api/manipulation.ts"
          },
          1014,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1069,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1069,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1075,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1100,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1100,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1101,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1110,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          52,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          60,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          62,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          63,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          67,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          84,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          86,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          88,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          102,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          102,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          125,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          136,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          139,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          139,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          192,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          194,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          195,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          216,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_removeDuplicates",
            "type": "src/api/traversing.ts"
          },
          226,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          348,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          362,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          362,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          365,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          366,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          368,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          369,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          377,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          607,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          607,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          609,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          609,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          612,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "each",
            "type": "src/api/traversing.ts"
          },
          646,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "type": "src/api/traversing.ts"
          },
          683,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "type": "src/api/traversing.ts"
          },
          685,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "type": "src/api/traversing.ts"
          },
          688,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "getFilterFn",
            "type": "src/api/traversing.ts"
          },
          701,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "getFilterFn",
            "type": "src/api/traversing.ts"
          },
          704,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filter",
            "type": "src/api/traversing.ts"
          },
          782,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filter",
            "type": "src/api/traversing.ts"
          },
          783,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "type": "src/api/traversing.ts"
          },
          814,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "type": "src/api/traversing.ts"
          },
          816,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "type": "src/api/traversing.ts"
          },
          822,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          862,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          869,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          872,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "has",
            "type": "src/api/traversing.ts"
          },
          903,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "has",
            "type": "src/api/traversing.ts"
          },
          907,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "first",
            "type": "src/api/traversing.ts"
          },
          926,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "last",
            "type": "src/api/traversing.ts"
          },
          944,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "eq",
            "type": "src/api/traversing.ts"
          },
          973,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "get",
            "type": "src/api/traversing.ts"
          },
          1010,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "toArray",
            "type": "src/api/traversing.ts"
          },
          1028,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "type": "src/api/traversing.ts"
          },
          1057,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "type": "src/api/traversing.ts"
          },
          1057,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "type": "src/api/traversing.ts"
          },
          1060,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "type": "src/api/traversing.ts"
          },
          1070,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "slice",
            "type": "src/api/traversing.ts"
          },
          1100,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "slice",
            "type": "src/api/traversing.ts"
          },
          1100,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "end",
            "type": "src/api/traversing.ts"
          },
          1119,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1143,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1144,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1144,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1145,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "addBack",
            "type": "src/api/traversing.ts"
          },
          1169,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "loadBuffer",
            "type": "src/index.ts"
          },
          58,
          "src/index.ts"
        ],
        [
          {
            "name": "loadBuffer",
            "type": "src/index.ts"
          },
          63,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          71,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          72,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          72,
          "src/index.ts"
        ],
        [
          {
            "name": "write",
            "type": "src/index.ts"
          },
          84,
          "src/index.ts"
        ],
        [
          {
            "name": "final",
            "type": "src/index.ts"
          },
          87,
          "src/index.ts"
        ],
        [
          {
            "name": "final",
            "type": "src/index.ts"
          },
          88,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          102,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          102,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          102,
          "src/index.ts"
        ],
        [
          {
            "name": "decodeStream",
            "type": "src/index.ts"
          },
          173,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          230,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          233,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          236,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          236,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          243,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          260,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          266,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          266,
          "src/index.ts"
        ],
        [
          {
            "name": "getLoad",
            "type": "src/load.ts"
          },
          137,
          "src/load.ts"
        ],
        [
          {
            "name": "_parse",
            "type": "LoadedCheerio"
          },
          160,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          182,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          200,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          204,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          228,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          239,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          251,
          "src/load.ts"
        ],
        [
          {
            "name": "getLoad",
            "type": "src/load.ts"
          },
          255,
          "src/load.ts"
        ],
        [
          {
            "name": "flattenOptions",
            "type": "src/options.ts"
          },
          128,
          "src/options.ts"
        ],
        [
          {
            "name": "getParse",
            "type": "src/parse.ts"
          },
          39,
          "src/parse.ts"
        ],
        [
          {
            "name": "getParse",
            "type": "src/parse.ts"
          },
          40,
          "src/parse.ts"
        ],
        [
          {
            "name": "getParse",
            "type": "src/parse.ts"
          },
          44,
          "src/parse.ts"
        ],
        [
          {
            "name": "getParse",
            "type": "src/parse.ts"
          },
          49,
          "src/parse.ts"
        ],
        [
          {
            "name": "getParse",
            "type": "src/parse.ts"
          },
          49,
          "src/parse.ts"
        ],
        [
          {
            "name": "update",
            "type": "src/parse.ts"
          },
          76,
          "src/parse.ts"
        ],
        [
          {
            "name": "update",
            "type": "src/parse.ts"
          },
          91,
          "src/parse.ts"
        ],
        [
          {
            "name": "parseWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          33,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "parseWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          34,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          54,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          55,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          62,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "render",
            "type": "src/static.ts"
          },
          28,
          "src/static.ts"
        ],
        [
          {
            "name": "render",
            "type": "src/static.ts"
          },
          28,
          "src/static.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/static.ts"
          },
          128,
          "src/static.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/static.ts"
          },
          133,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "type": "src/static.ts"
          },
          173,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "type": "src/static.ts"
          },
          175,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "type": "src/static.ts"
          },
          175,
          "src/static.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/static.ts"
          },
          252,
          "src/static.ts"
        ],
        [
          {
            "name": "isArrayLike",
            "type": "src/static.ts"
          },
          292,
          "src/static.ts"
        ],
        [
          {
            "name": "camelCase",
            "type": "src/utils.ts"
          },
          24,
          "src/utils.ts"
        ],
        [
          {
            "name": "camelCase",
            "type": "src/utils.ts"
          },
          24,
          "src/utils.ts"
        ],
        [
          {
            "name": "cssCase",
            "type": "src/utils.ts"
          },
          37,
          "src/utils.ts"
        ],
        [
          {
            "name": "cssCase",
            "type": "src/utils.ts"
          },
          37,
          "src/utils.ts"
        ],
        [
          {
            "name": "domEach",
            "type": "src/utils.ts"
          },
          57,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          81,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          85,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          91,
          "src/utils.ts"
        ]
      ],
      "version": "code-review-graph 2.3.8"
    },
    "code-review-graph-dispatch": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 1.11,
      "declared_unresolved": 367,
      "fanned_rows": 0,
      "rows": 512,
      "seconds_breakdown": {
        "adapter_total": 1.59,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/cheerio/crg/data/graph.db",
      "unresolved_sites": [
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          31,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          34,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          36,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          42,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          45,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          53,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          53,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          57,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          60,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          61,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          63,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          113,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          114,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          115,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "setup",
            "type": "benchmark/benchmark.ts"
          },
          121,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "setup",
            "type": "benchmark/benchmark.ts"
          },
          121,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          124,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          124,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          131,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          137,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          138,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          144,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          157,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          158,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          236,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          237,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          238,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          247,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          248,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          249,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          256,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          257,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          263,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          264,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          264,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          265,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          265,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          284,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "test",
            "type": "benchmark/benchmark.ts"
          },
          285,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          50,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          59,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          61,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          200,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          200,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          204,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          207,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getProp",
            "type": "src/api/attributes.ts"
          },
          240,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "setProp",
            "type": "src/api/attributes.ts"
          },
          262,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          410,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          414,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          415,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          426,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          452,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          456,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          460,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          460,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          460,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          479,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          483,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          491,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          494,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "setData",
            "type": "src/api/attributes.ts"
          },
          532,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          548,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          549,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          553,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          555,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readData",
            "type": "src/api/attributes.ts"
          },
          577,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readData",
            "type": "src/api/attributes.ts"
          },
          581,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          600,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          601,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          602,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          604,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "data",
            "type": "src/api/attributes.ts"
          },
          704,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "data",
            "type": "src/api/attributes.ts"
          },
          717,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          773,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          777,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          780,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          782,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          786,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          790,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          796,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          797,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          797,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          803,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          804,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeAttribute",
            "type": "src/api/attributes.ts"
          },
          819,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "splitNames",
            "type": "src/api/attributes.ts"
          },
          832,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "splitNames",
            "type": "src/api/attributes.ts"
          },
          832,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeAttr",
            "type": "src/api/attributes.ts"
          },
          862,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          894,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          894,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          895,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          899,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          903,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          904,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          942,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          944,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          952,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          958,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          969,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          972,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          974,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          974,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1010,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1011,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1021,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1031,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1034,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1045,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1087,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1088,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1090,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1100,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1108,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1115,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1119,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1122,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1126,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "css",
            "type": "src/api/css.ts"
          },
          78,
          "src/api/css.ts"
        ],
        [
          {
            "name": "css",
            "type": "src/api/css.ts"
          },
          81,
          "src/api/css.ts"
        ],
        [
          {
            "name": "setCss",
            "type": "src/api/css.ts"
          },
          117,
          "src/api/css.ts"
        ],
        [
          {
            "name": "setCss",
            "type": "src/api/css.ts"
          },
          127,
          "src/api/css.ts"
        ],
        [
          {
            "name": "getCss",
            "type": "src/api/css.ts"
          },
          159,
          "src/api/css.ts"
        ],
        [
          {
            "name": "getCss",
            "type": "src/api/css.ts"
          },
          165,
          "src/api/css.ts"
        ],
        [
          {
            "name": "stringify",
            "type": "src/api/css.ts"
          },
          186,
          "src/api/css.ts"
        ],
        [
          {
            "name": "stringify",
            "type": "src/api/css.ts"
          },
          186,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          201,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          209,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          210,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          213,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          218,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          218,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          219,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          219,
          "src/api/css.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          70,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          78,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          79,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          82,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          82,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          82,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          83,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          86,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          87,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          28,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          31,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          33,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          37,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          37,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          61,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          62,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          63,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          64,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          64,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          66,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          66,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          84,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          85,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          87,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          90,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          91,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          96,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          100,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          44,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          44,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          49,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          63,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          63,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          68,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          68,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          74,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          99,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          103,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          103,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          107,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          153,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          156,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          183,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "appendTo",
            "type": "src/api/manipulation.ts"
          },
          211,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "appendTo",
            "type": "src/api/manipulation.ts"
          },
          213,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "prependTo",
            "type": "src/api/manipulation.ts"
          },
          244,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "prependTo",
            "type": "src/api/manipulation.ts"
          },
          246,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          319,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          319,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          326,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          328,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          331,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          333,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          345,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          353,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "type": "src/api/manipulation.ts"
          },
          518,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "type": "src/api/manipulation.ts"
          },
          518,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "type": "src/api/manipulation.ts"
          },
          518,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "unwrap",
            "type": "src/api/manipulation.ts"
          },
          521,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "type": "src/api/manipulation.ts"
          },
          583,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "type": "src/api/manipulation.ts"
          },
          584,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "type": "src/api/manipulation.ts"
          },
          610,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "type": "src/api/manipulation.ts"
          },
          610,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          646,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          651,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          659,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          659,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          695,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          698,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          702,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          703,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          703,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          710,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          718,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          721,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          755,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          760,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          768,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          768,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          803,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          805,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          810,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          810,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          817,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          825,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          828,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "remove",
            "type": "src/api/manipulation.ts"
          },
          856,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "remove",
            "type": "src/api/manipulation.ts"
          },
          859,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          899,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          900,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          908,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          913,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "empty",
            "type": "src/api/manipulation.ts"
          },
          937,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          989,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          990,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          994,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          1000,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          1001,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "toString",
            "type": "src/api/manipulation.ts"
          },
          1014,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1069,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1069,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1075,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1100,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1100,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1101,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1110,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          52,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          60,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          62,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          63,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          67,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          84,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          86,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          88,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          102,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          102,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          125,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          136,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          139,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          139,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          192,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          194,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          195,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          216,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_removeDuplicates",
            "type": "src/api/traversing.ts"
          },
          226,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          348,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          362,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          362,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          365,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          366,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          368,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          369,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          377,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          607,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          607,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          609,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          609,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          612,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "each",
            "type": "src/api/traversing.ts"
          },
          646,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "type": "src/api/traversing.ts"
          },
          683,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "type": "src/api/traversing.ts"
          },
          685,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "type": "src/api/traversing.ts"
          },
          688,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "getFilterFn",
            "type": "src/api/traversing.ts"
          },
          701,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "getFilterFn",
            "type": "src/api/traversing.ts"
          },
          704,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filter",
            "type": "src/api/traversing.ts"
          },
          782,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filter",
            "type": "src/api/traversing.ts"
          },
          783,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "type": "src/api/traversing.ts"
          },
          814,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "type": "src/api/traversing.ts"
          },
          816,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "type": "src/api/traversing.ts"
          },
          822,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          862,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          869,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          872,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "has",
            "type": "src/api/traversing.ts"
          },
          903,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "has",
            "type": "src/api/traversing.ts"
          },
          907,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "first",
            "type": "src/api/traversing.ts"
          },
          926,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "last",
            "type": "src/api/traversing.ts"
          },
          944,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "eq",
            "type": "src/api/traversing.ts"
          },
          973,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "get",
            "type": "src/api/traversing.ts"
          },
          1010,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "toArray",
            "type": "src/api/traversing.ts"
          },
          1028,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "type": "src/api/traversing.ts"
          },
          1057,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "type": "src/api/traversing.ts"
          },
          1057,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "type": "src/api/traversing.ts"
          },
          1060,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "type": "src/api/traversing.ts"
          },
          1070,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "slice",
            "type": "src/api/traversing.ts"
          },
          1100,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "slice",
            "type": "src/api/traversing.ts"
          },
          1100,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "end",
            "type": "src/api/traversing.ts"
          },
          1119,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1143,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1144,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1144,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1145,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "addBack",
            "type": "src/api/traversing.ts"
          },
          1169,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "loadBuffer",
            "type": "src/index.ts"
          },
          58,
          "src/index.ts"
        ],
        [
          {
            "name": "loadBuffer",
            "type": "src/index.ts"
          },
          63,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          71,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          72,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          72,
          "src/index.ts"
        ],
        [
          {
            "name": "write",
            "type": "src/index.ts"
          },
          84,
          "src/index.ts"
        ],
        [
          {
            "name": "final",
            "type": "src/index.ts"
          },
          87,
          "src/index.ts"
        ],
        [
          {
            "name": "final",
            "type": "src/index.ts"
          },
          88,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          102,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          102,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          102,
          "src/index.ts"
        ],
        [
          {
            "name": "decodeStream",
            "type": "src/index.ts"
          },
          173,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          230,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          233,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          236,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          236,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          243,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          260,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          266,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          266,
          "src/index.ts"
        ],
        [
          {
            "name": "getLoad",
            "type": "src/load.ts"
          },
          137,
          "src/load.ts"
        ],
        [
          {
            "name": "_parse",
            "type": "LoadedCheerio"
          },
          160,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          182,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          200,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          204,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          228,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          239,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "src/load.ts"
          },
          251,
          "src/load.ts"
        ],
        [
          {
            "name": "getLoad",
            "type": "src/load.ts"
          },
          255,
          "src/load.ts"
        ],
        [
          {
            "name": "flattenOptions",
            "type": "src/options.ts"
          },
          128,
          "src/options.ts"
        ],
        [
          {
            "name": "getParse",
            "type": "src/parse.ts"
          },
          39,
          "src/parse.ts"
        ],
        [
          {
            "name": "getParse",
            "type": "src/parse.ts"
          },
          40,
          "src/parse.ts"
        ],
        [
          {
            "name": "getParse",
            "type": "src/parse.ts"
          },
          44,
          "src/parse.ts"
        ],
        [
          {
            "name": "getParse",
            "type": "src/parse.ts"
          },
          49,
          "src/parse.ts"
        ],
        [
          {
            "name": "getParse",
            "type": "src/parse.ts"
          },
          49,
          "src/parse.ts"
        ],
        [
          {
            "name": "update",
            "type": "src/parse.ts"
          },
          76,
          "src/parse.ts"
        ],
        [
          {
            "name": "update",
            "type": "src/parse.ts"
          },
          91,
          "src/parse.ts"
        ],
        [
          {
            "name": "parseWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          33,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "parseWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          34,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          54,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          55,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          62,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "render",
            "type": "src/static.ts"
          },
          28,
          "src/static.ts"
        ],
        [
          {
            "name": "render",
            "type": "src/static.ts"
          },
          28,
          "src/static.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/static.ts"
          },
          128,
          "src/static.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/static.ts"
          },
          133,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "type": "src/static.ts"
          },
          173,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "type": "src/static.ts"
          },
          175,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "type": "src/static.ts"
          },
          175,
          "src/static.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/static.ts"
          },
          252,
          "src/static.ts"
        ],
        [
          {
            "name": "isArrayLike",
            "type": "src/static.ts"
          },
          292,
          "src/static.ts"
        ],
        [
          {
            "name": "camelCase",
            "type": "src/utils.ts"
          },
          24,
          "src/utils.ts"
        ],
        [
          {
            "name": "camelCase",
            "type": "src/utils.ts"
          },
          24,
          "src/utils.ts"
        ],
        [
          {
            "name": "cssCase",
            "type": "src/utils.ts"
          },
          37,
          "src/utils.ts"
        ],
        [
          {
            "name": "cssCase",
            "type": "src/utils.ts"
          },
          37,
          "src/utils.ts"
        ],
        [
          {
            "name": "domEach",
            "type": "src/utils.ts"
          },
          57,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          81,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          85,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          91,
          "src/utils.ts"
        ]
      ],
      "version": "code-review-graph 2.3.8"
    },
    "codegraph": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 0.75,
      "declared_unresolved": 262,
      "dispatch_expanded_sites": 0,
      "rows": 238,
      "seconds_breakdown": {
        "adapter_total": 0.9,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "synthesized_rows_skipped": 0,
      "unresolved_sites": [
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          31,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          34,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          36,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          43,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          45,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          46,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          53,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          53,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          55,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          57,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          57,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          60,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          61,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          63,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          63,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "type": "scripts/fetch-sponsors.mts"
          },
          141,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "type": "scripts/fetch-sponsors.mts"
          },
          144,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "type": "scripts/fetch-sponsors.mts"
          },
          147,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "type": "scripts/fetch-sponsors.mts"
          },
          152,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "type": "scripts/fetch-sponsors.mts"
          },
          171,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "type": "scripts/fetch-sponsors.mts"
          },
          171,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "type": "scripts/fetch-sponsors.mts"
          },
          172,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "type": "scripts/fetch-sponsors.mts"
          },
          172,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchGitHubSponsors",
            "type": "scripts/fetch-sponsors.mts"
          },
          181,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          50,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          59,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          61,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          200,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          200,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          204,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          207,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getProp",
            "type": "src/api/attributes.ts"
          },
          240,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "setProp",
            "type": "src/api/attributes.ts"
          },
          262,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          410,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          415,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          426,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          452,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          456,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          479,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          483,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          491,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          494,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "setData",
            "type": "src/api/attributes.ts"
          },
          532,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          548,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          549,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          553,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          555,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readData",
            "type": "src/api/attributes.ts"
          },
          577,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readData",
            "type": "src/api/attributes.ts"
          },
          581,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          600,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          601,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          602,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          604,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "data",
            "type": "src/api/attributes.ts"
          },
          704,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "data",
            "type": "src/api/attributes.ts"
          },
          717,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          773,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          797,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          798,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeAttribute",
            "type": "src/api/attributes.ts"
          },
          819,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "splitNames",
            "type": "src/api/attributes.ts"
          },
          832,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "splitNames",
            "type": "src/api/attributes.ts"
          },
          832,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeAttr",
            "type": "src/api/attributes.ts"
          },
          862,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          894,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          895,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          899,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          903,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          904,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          942,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          944,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          944,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          952,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          958,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          969,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          972,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          974,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          974,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1010,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1011,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1011,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1021,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1031,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1034,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1045,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1087,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1088,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1090,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1100,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1108,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1115,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1119,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1122,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1126,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "css",
            "type": "src/api/css.ts"
          },
          78,
          "src/api/css.ts"
        ],
        [
          {
            "name": "css",
            "type": "src/api/css.ts"
          },
          81,
          "src/api/css.ts"
        ],
        [
          {
            "name": "setCss",
            "type": "src/api/css.ts"
          },
          117,
          "src/api/css.ts"
        ],
        [
          {
            "name": "setCss",
            "type": "src/api/css.ts"
          },
          127,
          "src/api/css.ts"
        ],
        [
          {
            "name": "getCss",
            "type": "src/api/css.ts"
          },
          159,
          "src/api/css.ts"
        ],
        [
          {
            "name": "getCss",
            "type": "src/api/css.ts"
          },
          165,
          "src/api/css.ts"
        ],
        [
          {
            "name": "stringify",
            "type": "src/api/css.ts"
          },
          186,
          "src/api/css.ts"
        ],
        [
          {
            "name": "stringify",
            "type": "src/api/css.ts"
          },
          186,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          201,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          209,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          210,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          213,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          218,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          218,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          219,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          219,
          "src/api/css.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          70,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          83,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          87,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          31,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          33,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          33,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          37,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          37,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          63,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          64,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          66,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          85,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          87,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          90,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          91,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          96,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          100,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          63,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          63,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          68,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          74,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          99,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          103,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          107,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          153,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          156,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          183,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "appendTo",
            "type": "src/api/manipulation.ts"
          },
          213,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "prependTo",
            "type": "src/api/manipulation.ts"
          },
          246,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          326,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          328,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          333,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          345,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          353,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "type": "src/api/manipulation.ts"
          },
          584,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          646,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          651,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          659,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          710,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          718,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          755,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          760,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          768,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          817,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          825,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "remove",
            "type": "src/api/manipulation.ts"
          },
          859,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          899,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          906,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          908,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          913,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "empty",
            "type": "src/api/manipulation.ts"
          },
          937,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          989,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          994,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          1000,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          1003,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1064,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1069,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1069,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1075,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1082,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1100,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1101,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          57,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          63,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          63,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          86,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          102,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          125,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          139,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          139,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          187,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          192,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          194,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          195,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          211,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          216,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_removeDuplicates",
            "type": "src/api/traversing.ts"
          },
          226,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          358,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          362,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          362,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          365,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          366,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          368,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          369,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          607,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          609,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          609,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "each",
            "type": "src/api/traversing.ts"
          },
          646,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "type": "src/api/traversing.ts"
          },
          683,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "type": "src/api/traversing.ts"
          },
          685,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "getFilterFn",
            "type": "src/api/traversing.ts"
          },
          701,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "getFilterFn",
            "type": "src/api/traversing.ts"
          },
          704,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filterArray",
            "type": "src/api/traversing.ts"
          },
          794,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filterArray",
            "type": "src/api/traversing.ts"
          },
          795,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "type": "src/api/traversing.ts"
          },
          816,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "type": "src/api/traversing.ts"
          },
          822,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          865,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          866,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          866,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          869,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          869,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "toArray",
            "type": "src/api/traversing.ts"
          },
          1028,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "type": "src/api/traversing.ts"
          },
          1070,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "slice",
            "type": "src/api/traversing.ts"
          },
          1100,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1144,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1144,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "loadBuffer",
            "type": "src/index.ts"
          },
          58,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          71,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          72,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          83,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          84,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          87,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          88,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          102,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          102,
          "src/index.ts"
        ],
        [
          {
            "name": "decodeStream",
            "type": "src/index.ts"
          },
          173,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          230,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          233,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          236,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          236,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          260,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          266,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          266,
          "src/index.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "getLoad::load"
          },
          204,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "getLoad::load"
          },
          239,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "getLoad::load"
          },
          251,
          "src/load.ts"
        ],
        [
          {
            "name": "load",
            "type": "getLoad"
          },
          255,
          "src/load.ts"
        ],
        [
          {
            "name": "flattenOptions",
            "type": "src/options.ts"
          },
          128,
          "src/options.ts"
        ],
        [
          {
            "name": "parse",
            "type": "getParse"
          },
          39,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "type": "getParse"
          },
          40,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "type": "getParse"
          },
          44,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "type": "getParse"
          },
          49,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "type": "getParse"
          },
          49,
          "src/parse.ts"
        ],
        [
          {
            "name": "update",
            "type": "src/parse.ts"
          },
          76,
          "src/parse.ts"
        ],
        [
          {
            "name": "update",
            "type": "src/parse.ts"
          },
          91,
          "src/parse.ts"
        ],
        [
          {
            "name": "parseWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          33,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "parseWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          34,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          54,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          55,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          62,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "render",
            "type": "src/static.ts"
          },
          28,
          "src/static.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/static.ts"
          },
          133,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "type": "src/static.ts"
          },
          175,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "type": "src/static.ts"
          },
          185,
          "src/static.ts"
        ],
        [
          {
            "name": "root",
            "type": "src/static.ts"
          },
          204,
          "src/static.ts"
        ],
        [
          {
            "name": "isArrayLike",
            "type": "src/static.ts"
          },
          292,
          "src/static.ts"
        ],
        [
          {
            "name": "camelCase",
            "type": "src/utils.ts"
          },
          24,
          "src/utils.ts"
        ],
        [
          {
            "name": "camelCase",
            "type": "src/utils.ts"
          },
          24,
          "src/utils.ts"
        ],
        [
          {
            "name": "cssCase",
            "type": "src/utils.ts"
          },
          37,
          "src/utils.ts"
        ],
        [
          {
            "name": "cssCase",
            "type": "src/utils.ts"
          },
          37,
          "src/utils.ts"
        ],
        [
          {
            "name": "domEach",
            "type": "src/utils.ts"
          },
          57,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          81,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          85,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          91,
          "src/utils.ts"
        ]
      ],
      "version": "codegraph 1.6.0"
    },
    "codegraph-dispatch": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 0.75,
      "declared_unresolved": 262,
      "dispatch_expanded_sites": 0,
      "rows": 238,
      "seconds_breakdown": {
        "adapter_total": 0.9,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "synthesized_rows_skipped": 0,
      "unresolved_sites": [
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          31,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          34,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          36,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          43,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          45,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          46,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          53,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          53,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          55,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          57,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          57,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          60,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          61,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          63,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "benchmark",
            "type": "benchmark/benchmark.ts"
          },
          63,
          "benchmark/benchmark.ts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "type": "scripts/fetch-sponsors.mts"
          },
          141,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "type": "scripts/fetch-sponsors.mts"
          },
          144,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "type": "scripts/fetch-sponsors.mts"
          },
          147,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchOpenCollectiveSponsors",
            "type": "scripts/fetch-sponsors.mts"
          },
          152,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "type": "scripts/fetch-sponsors.mts"
          },
          171,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "type": "scripts/fetch-sponsors.mts"
          },
          171,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "type": "scripts/fetch-sponsors.mts"
          },
          172,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getMonthsActive",
            "type": "scripts/fetch-sponsors.mts"
          },
          172,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "fetchGitHubSponsors",
            "type": "scripts/fetch-sponsors.mts"
          },
          181,
          "scripts/fetch-sponsors.mts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          50,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          59,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getAttr",
            "type": "src/api/attributes.ts"
          },
          61,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          200,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          200,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          204,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "attr",
            "type": "src/api/attributes.ts"
          },
          207,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "getProp",
            "type": "src/api/attributes.ts"
          },
          240,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "setProp",
            "type": "src/api/attributes.ts"
          },
          262,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          410,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          415,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          426,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          452,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          456,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          479,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          483,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          491,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "prop",
            "type": "src/api/attributes.ts"
          },
          494,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "setData",
            "type": "src/api/attributes.ts"
          },
          532,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          548,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          549,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          553,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readAllData",
            "type": "src/api/attributes.ts"
          },
          555,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readData",
            "type": "src/api/attributes.ts"
          },
          577,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "readData",
            "type": "src/api/attributes.ts"
          },
          581,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          600,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          601,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          602,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "parseDataValue",
            "type": "src/api/attributes.ts"
          },
          604,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "data",
            "type": "src/api/attributes.ts"
          },
          704,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "data",
            "type": "src/api/attributes.ts"
          },
          717,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          773,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          797,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "val",
            "type": "src/api/attributes.ts"
          },
          798,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeAttribute",
            "type": "src/api/attributes.ts"
          },
          819,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "splitNames",
            "type": "src/api/attributes.ts"
          },
          832,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "splitNames",
            "type": "src/api/attributes.ts"
          },
          832,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeAttr",
            "type": "src/api/attributes.ts"
          },
          862,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          894,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          895,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          899,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          903,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "hasClass",
            "type": "src/api/attributes.ts"
          },
          904,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          942,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          944,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          944,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          952,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          958,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          969,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          972,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          974,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "addClass",
            "type": "src/api/attributes.ts"
          },
          974,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1010,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1011,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1011,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1021,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1031,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1034,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "removeClass",
            "type": "src/api/attributes.ts"
          },
          1045,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1087,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1088,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1090,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1100,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1108,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1115,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1119,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1122,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "toggleClass",
            "type": "src/api/attributes.ts"
          },
          1126,
          "src/api/attributes.ts"
        ],
        [
          {
            "name": "css",
            "type": "src/api/css.ts"
          },
          78,
          "src/api/css.ts"
        ],
        [
          {
            "name": "css",
            "type": "src/api/css.ts"
          },
          81,
          "src/api/css.ts"
        ],
        [
          {
            "name": "setCss",
            "type": "src/api/css.ts"
          },
          117,
          "src/api/css.ts"
        ],
        [
          {
            "name": "setCss",
            "type": "src/api/css.ts"
          },
          127,
          "src/api/css.ts"
        ],
        [
          {
            "name": "getCss",
            "type": "src/api/css.ts"
          },
          159,
          "src/api/css.ts"
        ],
        [
          {
            "name": "getCss",
            "type": "src/api/css.ts"
          },
          165,
          "src/api/css.ts"
        ],
        [
          {
            "name": "stringify",
            "type": "src/api/css.ts"
          },
          186,
          "src/api/css.ts"
        ],
        [
          {
            "name": "stringify",
            "type": "src/api/css.ts"
          },
          186,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          201,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          209,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          210,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          213,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          218,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          218,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          219,
          "src/api/css.ts"
        ],
        [
          {
            "name": "parse",
            "type": "src/api/css.ts"
          },
          219,
          "src/api/css.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          70,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          83,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "extract",
            "type": "src/api/extract.ts"
          },
          87,
          "src/api/extract.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          31,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          33,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          33,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          37,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serialize",
            "type": "src/api/forms.ts"
          },
          37,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          63,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          64,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          66,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          85,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          87,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          90,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          91,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          96,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "serializeArray",
            "type": "src/api/forms.ts"
          },
          100,
          "src/api/forms.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          63,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          63,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          68,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_makeDomArray",
            "type": "src/api/manipulation.ts"
          },
          74,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          99,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          103,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_insert",
            "type": "src/api/manipulation.ts"
          },
          107,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          153,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          156,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "uniqueSplice",
            "type": "src/api/manipulation.ts"
          },
          183,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "appendTo",
            "type": "src/api/manipulation.ts"
          },
          213,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "prependTo",
            "type": "src/api/manipulation.ts"
          },
          246,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          326,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          328,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          333,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          345,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "_wrap",
            "type": "src/api/manipulation.ts"
          },
          353,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "wrapAll",
            "type": "src/api/manipulation.ts"
          },
          584,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          646,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          651,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "after",
            "type": "src/api/manipulation.ts"
          },
          659,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          710,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertAfter",
            "type": "src/api/manipulation.ts"
          },
          718,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          755,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          760,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "before",
            "type": "src/api/manipulation.ts"
          },
          768,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          817,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "insertBefore",
            "type": "src/api/manipulation.ts"
          },
          825,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "remove",
            "type": "src/api/manipulation.ts"
          },
          859,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          899,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          906,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          908,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "replaceWith",
            "type": "src/api/manipulation.ts"
          },
          913,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "empty",
            "type": "src/api/manipulation.ts"
          },
          937,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          989,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          994,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          1000,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "html",
            "type": "src/api/manipulation.ts"
          },
          1003,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1064,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1069,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1069,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1075,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/api/manipulation.ts"
          },
          1082,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1100,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "clone",
            "type": "src/api/manipulation.ts"
          },
          1101,
          "src/api/manipulation.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          57,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          63,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "find",
            "type": "src/api/traversing.ts"
          },
          63,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          86,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_findBySelector",
            "type": "src/api/traversing.ts"
          },
          102,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          125,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          139,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_getMatcher",
            "type": "src/api/traversing.ts"
          },
          139,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          187,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          192,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          194,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          195,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          211,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_matchUntil",
            "type": "src/api/traversing.ts"
          },
          216,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "_removeDuplicates",
            "type": "src/api/traversing.ts"
          },
          226,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          358,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          362,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          362,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          365,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          366,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          368,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "closest",
            "type": "src/api/traversing.ts"
          },
          369,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          607,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          609,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "contents",
            "type": "src/api/traversing.ts"
          },
          609,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "each",
            "type": "src/api/traversing.ts"
          },
          646,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "type": "src/api/traversing.ts"
          },
          683,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "map",
            "type": "src/api/traversing.ts"
          },
          685,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "getFilterFn",
            "type": "src/api/traversing.ts"
          },
          701,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "getFilterFn",
            "type": "src/api/traversing.ts"
          },
          704,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filterArray",
            "type": "src/api/traversing.ts"
          },
          794,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "filterArray",
            "type": "src/api/traversing.ts"
          },
          795,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "type": "src/api/traversing.ts"
          },
          816,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "is",
            "type": "src/api/traversing.ts"
          },
          822,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          865,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          866,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          866,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          869,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "not",
            "type": "src/api/traversing.ts"
          },
          869,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "toArray",
            "type": "src/api/traversing.ts"
          },
          1028,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "index",
            "type": "src/api/traversing.ts"
          },
          1070,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "slice",
            "type": "src/api/traversing.ts"
          },
          1100,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1144,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "add",
            "type": "src/api/traversing.ts"
          },
          1144,
          "src/api/traversing.ts"
        ],
        [
          {
            "name": "loadBuffer",
            "type": "src/index.ts"
          },
          58,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          71,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          72,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          83,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          84,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          87,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          88,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          102,
          "src/index.ts"
        ],
        [
          {
            "name": "_stringStream",
            "type": "src/index.ts"
          },
          102,
          "src/index.ts"
        ],
        [
          {
            "name": "decodeStream",
            "type": "src/index.ts"
          },
          173,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          230,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          233,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          236,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          236,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          260,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          266,
          "src/index.ts"
        ],
        [
          {
            "name": "fromURL",
            "type": "src/index.ts"
          },
          266,
          "src/index.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "getLoad::load"
          },
          204,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "getLoad::load"
          },
          239,
          "src/load.ts"
        ],
        [
          {
            "name": "initialize",
            "type": "getLoad::load"
          },
          251,
          "src/load.ts"
        ],
        [
          {
            "name": "load",
            "type": "getLoad"
          },
          255,
          "src/load.ts"
        ],
        [
          {
            "name": "flattenOptions",
            "type": "src/options.ts"
          },
          128,
          "src/options.ts"
        ],
        [
          {
            "name": "parse",
            "type": "getParse"
          },
          39,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "type": "getParse"
          },
          40,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "type": "getParse"
          },
          44,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "type": "getParse"
          },
          49,
          "src/parse.ts"
        ],
        [
          {
            "name": "parse",
            "type": "getParse"
          },
          49,
          "src/parse.ts"
        ],
        [
          {
            "name": "update",
            "type": "src/parse.ts"
          },
          76,
          "src/parse.ts"
        ],
        [
          {
            "name": "update",
            "type": "src/parse.ts"
          },
          91,
          "src/parse.ts"
        ],
        [
          {
            "name": "parseWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          33,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "parseWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          34,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          54,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          55,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "renderWithParse5",
            "type": "src/parsers/parse5-adapter.ts"
          },
          62,
          "src/parsers/parse5-adapter.ts"
        ],
        [
          {
            "name": "render",
            "type": "src/static.ts"
          },
          28,
          "src/static.ts"
        ],
        [
          {
            "name": "text",
            "type": "src/static.ts"
          },
          133,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "type": "src/static.ts"
          },
          175,
          "src/static.ts"
        ],
        [
          {
            "name": "parseHTML",
            "type": "src/static.ts"
          },
          185,
          "src/static.ts"
        ],
        [
          {
            "name": "root",
            "type": "src/static.ts"
          },
          204,
          "src/static.ts"
        ],
        [
          {
            "name": "isArrayLike",
            "type": "src/static.ts"
          },
          292,
          "src/static.ts"
        ],
        [
          {
            "name": "camelCase",
            "type": "src/utils.ts"
          },
          24,
          "src/utils.ts"
        ],
        [
          {
            "name": "camelCase",
            "type": "src/utils.ts"
          },
          24,
          "src/utils.ts"
        ],
        [
          {
            "name": "cssCase",
            "type": "src/utils.ts"
          },
          37,
          "src/utils.ts"
        ],
        [
          {
            "name": "cssCase",
            "type": "src/utils.ts"
          },
          37,
          "src/utils.ts"
        ],
        [
          {
            "name": "domEach",
            "type": "src/utils.ts"
          },
          57,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          81,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          85,
          "src/utils.ts"
        ],
        [
          {
            "name": "isHtml",
            "type": "src/utils.ts"
          },
          91,
          "src/utils.ts"
        ]
      ],
      "version": "codegraph 1.6.0"
    },
    "codeql": {
      "build": "source only",
      "cache": "hit",
      "cold_seconds": 6.89,
      "rows": 268,
      "seconds_breakdown": {
        "adapter_total": 20.24,
        "own": 6.69,
        "shared": 7.15,
        "staging": null
      },
      "source": ".work/typescript/cheerio/codeql/q.csv",
      "version": "codeql 2.23.8 javascript-all 2.6.18"
    },
    "gitnexus": {
      "build": "source only",
      "cache": "warmed",
      "cold_seconds": 7.3,
      "rows": 123,
      "seconds_breakdown": {
        "adapter_total": 12.16,
        "export": 0.64,
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
      "rows": 145,
      "seconds_breakdown": {
        "adapter_total": 0.75,
        "own": null,
        "shared": null,
        "staging": 0.02
      },
      "source": ".work/typescript/cheerio/gfy/src/graphify-out/graph.json",
      "version": "graphifyy 0.9.58"
    },
    "ideal": {
      "build": "oracle",
      "null_model": true,
      "reference": "ideal",
      "rows": 209,
      "version": "the correct answer for every link group (a ceiling, not a tool)"
    }
  },
  "tsx": "4.19.2",
  "typescript": "5.6.3"
}
```
