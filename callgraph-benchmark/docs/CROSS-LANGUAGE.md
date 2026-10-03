# Comparing across languages — what is valid and what is not

The Java and TypeScript tables share a harness, a schema, a scorer and a set of verdicts. That makes
them *consistent*. It does not make every column *comparable*, and the difference matters enough to
have its own page.

---

## What is shared, and therefore trustworthy across languages

`bench/` is language-neutral: the fidelity tiers, the link-group verdicts, the resolver's
ambiguity rules, the mutation self-test, the contingency tables, the report. Only
`bench/language.py` differs, and only in naming conventions — what a constructor is called, how a
namespace is written, whether generics erase.

So a difference between the two tables is a difference in the tools or in the languages. It is
never two independently drifted harnesses, which is the usual reason cross-language benchmark
numbers cannot be read side by side.

---

## The one metric that means the same thing in both

> **Uniquely-linked exact rate** — of the call sites where the language admits exactly one target,
> how many did the tool link to that one concrete method?

The question is identical in both languages, the denominators are constructed the same way, and the
five verdicts partition the answer the same way. **This is the cross-language headline.**

With one qualification about *which calls* it is computed over. In TypeScript a call through a
**function value** — a callback, a higher-order argument, a field holding a closure — resolves in
the checker to a function *type*, not an implementation. Those sites are recorded as `indirect` and
**not scored**: the share is printed in every TypeScript report's denominator table and in
`docs/RESULTS.md`'s subject header (`sites through a function value`) — 6.4% of scorable sites on
kysely and 17.2% on typedoc at the time of writing; the figure is generated, not quoted here, since
a hand-written one drifted (#54 §3). Excluding them is defensible (there is no target to score
against), but callbacks are the idiomatic core of TypeScript, so the TypeScript `exact` rate is
computed over the most Java-shaped subset of each program. Since #53 the same table also prints the
call expressions the checker could not resolve at all — 12.3% on typedoc — which produce no row of
any kind and shorten every recall denominator uniformly.

---

## What is NOT comparable, and why

### `recall_possible` — the envelopes are different objects

| | Java | TypeScript |
|---|---|---|
| dispatch | **nominal** | **structural** |
| `possible` | every method JVMS §5.4.6 *selects* for some concrete application receiver that is the static type or a subtype of it (bridges followed) — what can run | every own container that declares a same-named member and whose type the **checker** says is *assignable* to the receiver's — declared heritage is a subset; interfaces are never in it |
| is it sound? | for the application's own classes, yes — nothing outside the declared hierarchy can receive a nominal call; a receiver whose runtime class comes from a dependency is out of the universe either way | **no, in both directions**: it admits a type whose member happens to be compatible although nothing ever passes it, and it cannot see a call through a function-typed property (`indirect`, never scored) |

An earlier version of this page said the TypeScript set was "declared heritage" and that a
structural implementation "is charged for" — the code had admitted structural implementors since
the kysely audit, and the page had not been updated (#27). It also called the Java envelope
"sound" while the oracle computed something that was neither sound nor tight (#30). Both are
stated correctly now, and both oracles apply the same stance: an interface member or abstract
method is the *declared* target (`certain`) and not a *runnable* one (`possible`), so a call with
exactly one implementor is uniquely linked to that implementor, and the scorer accepts naming
either. And both stop at the subject's edge: a call whose declared target is a platform or
dependency member (`map.get`, a dependency interface's method) is a `boundary` site in both
languages — no group, no unique link, no recall — because the receivers that actually run there
are outside the universe and an envelope over the application's implementors alone is not an
envelope. The Java oracle scored those as internal until the second #30 pass; the application
implementors it selects are kept as accepted answers, never as the one right one.

The consequence is unchanged in direction: the TypeScript `possible` is an approximation of a
different shape from the Java one, so `recall_possible` is comparable *between tools within a
language* and is **not** comparable across the two columns. The `torture` subjects each carry a
file that makes this visible (`t02-structural.ts`, `t08-envelope.ts`).

### Precision — the false-positive denominator differs with it

Precision is `|E ∩ (POSSIBLE ∪ DECLARING_ANCESTORS)| / |E|`. Since `POSSIBLE` means something
different in each language, so does "false positive". A TypeScript tool that correctly resolves a
structural implementation is NOT charged for it: the envelope admits every own container whose
type the checker says is assignable to the receiver's (#27). The other side of that coin is
**uniqueness itself**: the same program in both languages —

```
interface Runner { run(): void }   class Cat implements Runner { run(){} }   class Dog { run(){} }  // Dog never passed
function go(r: Runner) { r.run(); }
```

— is uniquely linked to `Cat#run` in Java (`Dog` does not implement `Runner`; naming it is a false
positive) and NOT uniquely linked in TypeScript (`Dog` is structurally a `Runner`, so
`possible = {Cat, Dog}` and the site leaves the headline; naming `Dog` is not charged). The
headline number is the same *question* in both languages; which calls it is asked over depends on
the envelope, and the envelope is nominal in one and structural in the other.

### Subject size and shape

`torture` (Java) is ~700 lines across 12 construct families; `torture` (TypeScript) is ~330 lines
across 5. They are diagnostics, not comparable corpora. Both languages now have five real projects;
the Java ones are read from published bytecode, the TypeScript ones from a pinned repository and
the checker, and the TypeScript envelope is 1.0–1.2× its certain set against Java's 1.0–24.3×
(the size table in the README carries the per-subject figures; these were 1.0–2.2× and 1.6–44× before the
second #30 pass made calls on JDK interfaces boundary sites).

---

## The ground truths are not equally strong, and the gates say so

| | Java | TypeScript |
|---|---|---|
| source of truth | the project's **own published bytecode**, read with `java.lang.classfile` | the **TypeScript compiler's type checker**, `getResolvedSignature` |
| independent second reader | **yes** — `javap`, sharing no code; agreement is instruction-for-instruction | **no** — TypeScript has exactly one implementation of its type system |
| what gate 1 proves | the bytecode was read correctly | **our use of the checker** is consistent across two of its entry points |
| what gate 1 does not prove | — | that the checker itself is right; no available technique does |

This is why the TypeScript result is reported as a **diagnostic** and the Java result as a
**measurement**.

### A conflict of interest, stated

One tool under test — `axiom-code-graph` — parses TypeScript with the `typescript` package, and its
own test suite uses `getResolvedSignature` as a correctness adjudicator (`test/typescript/
ground-truth/tsc-oracle.mjs` in that repo).

Checked rather than assumed: it uses the compiler's **parser**, and `getTypeChecker()` appears
nowhere in its extraction path — verified by grep over the parser's `src/`, where every occurrence
is in a comment or in its own tests. So the checker is not in that tool's production resolution
path, and this oracle is independent of it in the way that matters.

What remains is an **indirect alignment**: that tool's authors developed against the same oracle
this benchmark scores them with, so its answers are more likely to agree with it than a tool
developed against nothing in particular. That is not neutralisable. It is the second reason the
TypeScript table is a diagnostic rather than a ranking, and it should be read with the Java result,
where no such relationship exists.

---

## `needs` — what a tool required to produce its answer

Every score table carries a `needs` column, because it is a capability rather than a score and it
changes what the tool could see:

| value | meaning |
|---|---|
| `compiled build` | a working compile gave the tool full type information |
| `build-mode=none` | it indexed the source tree without a build |
| `source + platform IR` | source, plus a pre-built typed IR of the platform library staged as a type oracle |
| `source only` | it never builds and never stages anything |

A tool that needs a build is not usable where a build does not run — a partial checkout, a review
bot, a repository whose dependencies no longer resolve. A tool that does not build is not seeing the
same program. Both facts are real, neither is a defect, and a table that omits the column invites
the reader to compare them as though they were equal.

This is also why `axiom` is reported as two rows in Java: `axiom-nolib` on the same input budget as
the source-reading tools, and `axiom` with the platform IR staged. Only the first is ranked (it prints
as `AxiomEngine`); the second prints as `AxiomEngine + libraries` in its own table beside it
(PROTOCOL §7).
