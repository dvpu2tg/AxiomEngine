# The protocol

This is the normative document. Every number in `results/` is defined here, and a result that
cannot be traced back to a rule in this file is a bug in the harness, not a finding about a tool.

The benchmark measures one thing: **for each call written in the subject's source, which method
does a tool say it reaches, and is that right?** Everything below exists to make that question
answerable without the answer depending on which tool we happened to build the harness around.

---

## 1. Ground truth comes from compiled artefacts, not from source

`oracle/ClassfileGroundTruth.java` reads the invoke instructions out of the subject's `.class`
files using `java.lang.classfile` (JEP 484, final in JDK 24). The JDK parses its own artefact
format; no third-party analyzer, no parser shared with any tool under test.

This matters more than it sounds. Every tool in this benchmark analyses **source**. If ground truth
also came from a source analyser, the benchmark would be measuring agreement between two source
analysers — and whichever one the harness author understood best would win. Bytecode is the
compiler's answer to the same question, produced by a program that has to be right.

### 1.1 Where the bytecode comes from

| subject kind | ground truth | what the tools read |
|---|---|---|
| **local** (`torture`) | compiled here by `javac -g` | the same source tree |
| **maven** (everything at scale) | the project's **own published `.jar`** | the `-sources.jar` from the same coordinate |

Nothing is built at scale, deliberately. Compiling a real project with *our* JDK, *our* flags and
*our* compiler produces bytecode that is not the bytecode the project ships, and every difference —
a changed `-parameters`, a different `-source` level, ecj instead of javac — lands in the ground
truth as though it were a fact about the project. Reading the published artefact removes that
entire class of error, and makes a subject reproducible from two URLs and two SHA-256 hashes
instead of from a working build toolchain. A changed hash under a fixed coordinate stops the run.

### 1.2 The ground truth is verified before it is used

Four gates, all in `run/subject.sh`, all fatal:

| gate | what it rules out |
|---|---|
| `oracle/javap_reader.py` agrees instruction-for-instruction with the classfile reader | the bytecode was read wrong |
| `--mode collisions` is empty | two application types share a canonical name, so both bounds would be computed over a type that does not exist |
| `bench/selftest.py` detects eight deliberate mutations | the scorer cannot fail, and therefore proves nothing when it passes |
| `bench/correspondence.py` — source and bytecode describe the same program | the two artefacts are not one release |

The fourth gate matters more than it sounds, and it has a severe direction. **Bytecode without
source** means the oracle holds ground truth for code no tool could read: every edge in it is a
`missed` against *every tool at once*. That is a uniform recall deflation with no visible cause,
and it looks exactly like a real result. So the scored universe is restricted to the intersection —
`correspondence.py --emit-types` writes it, the oracle's `--only-types` consumes it — and a tool is
never charged for a type nobody gave it.

In TypeScript the fourth gate has no second artefact — the checker's program *is* the subject — so
it runs the other way: the tools are given exactly the file set the checker loaded, as a pruned
copy with a **synthesised tsconfig**. That config keeps the project's `compilerOptions` and its
`paths` mappings, re-rooted at the copy. It must: `paths` is how a project spells its own modules
(`@/errors` → `./src/errors` in type-graphql), and the first version of the synthesis dropped it as
a build-only key — every tool that resolves imports then saw ~200 dead internal imports, and CodeQL
read 38% recall on a subject it reads 89% on with the mapping kept. A mapping that points outside
the scored tree is dropped and printed. The harness punishing a project for its layout is precisely
the failure this benchmark exists to not commit; it is written down here because it was committed.

The first gate is at the **raw** layer — every invoke instruction exactly as the constant pool
spells it, before any exclusion or normalisation. That separation is deliberate: agreement there
proves the bytecode was *read* correctly, and agreement on the site records proves the *conventions*
were applied correctly. They are different failure modes, and only the first is checkable by a
second reader — which is why the conventions are written down here rather than trusted.

---

## 2. The three bounds

A call graph has more than one kind of truth. Collapsing them into one number silently picks one.

| bound | definition |
|---|---|
| **CERTAIN** (`G_lb`) | the target the instruction *declares*, resolved as JVMS §5.4.3.3 resolves a symbolic reference (the superclass chain, then the maximally-specific superinterface). For `invokestatic` / `invokespecial` this is the method that runs. For `invokevirtual` / `invokeinterface` it is the declaration — which may be abstract. |
| **POSSIBLE** (`G_ub`) | what can **run**: for every concrete application class that is the receiver's static type or a subtype of it, the method JVMS §5.4.6 **selects** — the receiver's or its superclass chain's method that *overrides* the declaration under §5.4.5 (private and static never override; package-private only from the same package), else the maximally-specific non-abstract superinterface method — with an `ACC_BRIDGE` forwarder followed to the generic override it calls. A method reference dispatches virtually when its handle is `invokevirtual`/`invokeinterface`. An abstract declared target is in CERTAIN and **not** in POSSIBLE, so an interface with one implementor is uniquely linked to the implementor; where nothing in the application implements the declaration (a functional interface satisfied only by lambdas), the declaration stands as the one scorable answer. |
| **RTA** | the same selection over the receivers the application **instantiates** with `new` (and enum constants). Not a lambda's containing class, not the target of a `this(...)`/`super(...)` chain. |

Until issue #30 POSSIBLE was "every subtype that itself *declares* a member with the same erased
parameter list, bridges skipped" — which on rxjava omitted 8,172 runnable edges (generic bridges,
implementations inherited from a non-subtype, method references) and included 56,403 impossible
ones (members of non-subtypes, abstract re-declarations). Both errors moved the `unique` flag the
headline is built on. **Gate 1c** now recomputes every site's envelope with an independent
implementation of the same two JVMS sections and refuses the subject on any disagreement.

And one set that is not a bound:

| set | role |
|---|---|
| **DECLARING ANCESTORS** | supertypes of the receiver that declare the same member, and the declared target itself when it cannot run here. Naming one is a *convention*, not an error — a resolver may answer where a method is declared rather than where it is reached. These are **not** false positives and they are **not** recall. On a uniquely-linked group the scorer accepts the declared target *or* the runnable one as `exact`. |

### 2.1 Which bound each metric uses, and why

```
precision         = |E ∩ (POSSIBLE ∪ DECLARING_ANCESTORS)| / |E|     is anything you said impossible?
precision_strict  = |E ∩ CERTAIN| / |E|                              how much of it was the declared answer?
recall_certain    = |E ∩ CERTAIN|  / |CERTAIN|
recall_possible   = |E ∩ POSSIBLE| / |POSSIBLE|
recall_rta        = |E ∩ RTA|      / |RTA|
```

**Precision carries two bounds, for the same reason recall does.** `precision` counts a false
positive only outside the envelope, so over-approximation *inside* it is free — and a tool that
emits the entire CHA envelope at every site, resolving nothing, scored 1.000 on it and topped the
headline table on all three Java subjects (issue #1). `precision_strict` is the other bound. They
are read as a pair: a soundly-fanning tool sits high on the first and low on the second, and that
gap *is* its over-approximation. Neither is a target on its own — a flow-sensitive tool that names
the override which actually runs is sharper than the bytecode and the strict bound gives it no
credit, which is why every table also carries the **CHA null model** as a floor row (italic, never
ranked) and the self-test asserts the null model cannot match a resolving tool on the strict bound.

Precision is measured against the **envelope**, never against CERTAIN. `Base b = new Unit(); b.area()`
compiles to an `invokevirtual` naming `Base#area`; a tool that flow-types the receiver answers
`Unit#area`, the method that actually runs. Scoring that against CERTAIN would mark it a false
positive at the moment it got *sharper than the bytecode*.

Recall is reported against all three bounds because they move in opposite directions under
over-approximation. A tool that fans every virtual call to its whole hierarchy scores well on
`recall_possible` and badly on precision; a tool that resolves only static calls scores well on
precision and badly on `recall_possible`. Neither number alone can be gamed; the pair can't be.

**RTA is unsound in general** — a type instantiated by a dependency, by reflection, or by a
framework appears nowhere in the artefact. It is reported as a tighter, more realistic reading and
is never used as the precision denominator.

### 2.2 Accuracy is not reported

At this class imbalance it is meaningless: a tool that returns **nothing** scores ~0.998, because
~99.8% of the `(method × method)` universe is a non-edge. MCC uses all four cells and collapses to
0 for that tool, which is the honest answer. The universe is printed with every MCC value.

**F1 and MCC are printed in their strict form.** Built on `precision`, both are maxed by the null
model wherever the envelope covers the sites — on 6 of 10 subjects in the first audit (issue #1),
because an answer inside the envelope is never a false positive there. The tables print `F1-strict`
and `MCC-strict`, which count every emitted row that is not the declared target as a false positive
(the `prec-strict` denominator); the permissive pair stays in the JSON. On a subject that does not
dispatch at all (fp-ts: envelope = declared set, null strict 1.000) the envelope IS the declared
answer and the null model maxes the strict pair too — a fact about the subject, marked in the
tables as *dispatch-light*, not a defect of the column.

---

## 3. Canonical names

The canonical type name is the **full nesting chain** — `pkg.Outer.Inner`, never flattened to
`pkg.Inner`.

Flattening is a convention some call-graph IRs adopt and it is **lossy**: the 592-line torture
subject alone contains two distinct types (`F02Generics.Node`, `F07Modern.Node`) that flatten to
one name. Adopting it would corrupt the ground truth — the two types' members would merge, and both
bounds would be computed over a type that does not exist — *and* punish every tool that handles
nesting correctly. A tool that flattens is handled in `bench/resolve.py` instead (§5).

Two forms need a key no compiler numbering can shift:

* an **anonymous** class is keyed by its supertype, `pkg.Outer$anon:Runnable`. javac and ecj number
  anonymous classes differently, so the counter is not a name.
* a **local** class's counter prefix is stripped: `Outer$1Local` → `pkg.Outer.Local`.

An **enum-constant body** folds onto its enum: the source declares a constant with a body, not a
type. This is a deliberate fold and `--mode collisions` excludes it.

A **lambda body** folds into the method that lexically contains it, with that method's real
signature. The container is read off the `invokedynamic` that *references* the body, never off the
body's name — javac emits `lambda$<method>$<n>` but ecj emits `lambda$<n>`, and name parsing cannot
recover the container from the latter.

Parameter types are **erased and simple-named**, matching the descriptor: a type variable reads as
its bound, `List<String>` reads as `List`, varargs reads as an array.

### 3.1 TypeScript: how a function with no name is named

TypeScript has no `lambda$` — an arrow function is anonymous, and most of a real program's callers
are arrows. The oracle names one by **the binding the source gives it**, or folds it:

| written as | named | container |
|---|---|---|
| `const f = (x) => …` | `f` | the module (or the class the declaration is inside) |
| `{ perform: (x) => … }` — an object-literal property | `perform` | the literal, keyed by the name it is bound to |
| `class A { onClick = (e) => … }` — a class field | `onClick` | `A` |
| any of the above behind a wrapper — `memo(() => …)`, `withBatchedUpdates((e) => …)`, `(() => …) as H` | the binding outside the wrapper, **when that binding is itself a function**; `const index = find(arr, (v) => …)` binds a number, and the arrow folds outward (#53) | as above |
| a call in a class field initializer, `deserializer = new Deserializer(this)` | caller `A#constructor` (the declared constructor's parameters, or none) — it runs in the constructor, as Java's `<init>` | `A` |
| a call in a static field initializer or a `static { }` block | caller `A#<clinit>`, as Java (#74) | `A` |
| a call through a closure a helper returns and a field stores (`header = bind(fn, this)`), or through a construct-signature alias | `indirect` — a call through a function value, neutral (#73) | — |
| an arrow nested inside a function, bound to nothing | **folded into the enclosing named function**, like a Java lambda body | that function's |
| an arrow at module top level, bound to nothing | `<module>` | the module |

Every adapter is expected to name the same way from what its tool *records*. CodeQL's `Function.getName()`
is the inferred binding and its query folds outward. axiom's IR names every arrow `<arrow>` and
states the binding separately — a variable's `boundFunctionLinkHash`, a field's or variable's
initializer through the expression tree, and the `enclosingMemberLinkHash` a closure is nested in;
`typescript/adapters/axiom/adapt.py` reads those three and nothing else, so an object-literal
property arrow — whose name the IR does not record — stays `<arrow>` and scores as the tool
reported it. GitNexus names the variable a call goes *through* rather than the function that runs,
which is a different answer, and is emitted as such (`typescript/adapters/gitnexus/adapt.py`).

Getting this wrong on either side is the single largest error source the TypeScript benchmark has
had: the class-field rule alone was 103 sites on one line-key in excalidraw's `App`, and reading
the IR's bindings moved axiom on fp-ts from 4% to 67% and then, with the fold, to 90%.

---

## 4. What is excluded, and the evidence for each

An invoke instruction for which the source contains **no call**. Leaving one in does not merely
cost a point — it scores every tool as having *missed a call site that is not in the file*, which is
a wrong number rather than a missing one.

| excluded | evidence it is not in the source |
|---|---|
| bridge / `ACC_SYNTHETIC` methods, `access$N` | generated for covariant returns and outer access |
| `values()` / `valueOf(String)` **on an enum** (by shape: a user overload `valueOf(int)` survives, #66 §6), `$values`, an **enum's** `<clinit>` | JLS-mandated members — on any other type a method of that name is the source's own (`LinkedHashtable.values()` in apache-ant; #26 §3). A non-enum class's `<clinit>` — a `static { }` block or a static field initializer — is written source and IS a caller (#66 §7) |
| `access$N` (Java 8 bytecode) | a synthetic accessor for a nested class's call to a private member: the call is re-pointed to the member it forwards to; a field accessor (no call) is excluded symmetrically (#66 §1). A synthetic private-constructor accessor (`Inner(Outer, Outer$1)`) and a visibility bridge are followed the same way (#66 §2, #77 §1) |
| the copies of an instance field initializer javac places in every non-delegating constructor | one written call, scored once, under the first constructor that carries it (#78 §1) |
| an anonymous class's constructor chain to its supertype | `new Base(args) { … }` is scored in the enclosing method as a call to the anonymous constructor with `Base#<init>` accepted; the synthetic chain is not a second site (#78 §2) |
| string concatenation (`makeConcatWithConstants`, `StringBuilder`, `String.valueOf(Object)`) | `a + b` lowering |
| boxing (`Integer.valueOf(int)`) and **unboxing** (`intValue()`) | assignment-context conversion |
| the enhanced-for triple (`iterator`/`hasNext`/`next`) | keyed on the **mechanism**: the `iterator()` javac follows *immediately* with the loop's `hasNext()` test, and `hasNext`/`next` on an `Iterator`. A written `c.iterator()` passed on or returned is followed by something else and **stays** (44 on apache-ant; #26 §4). `hasNext`/`next` written by hand in a manual loop are dropped with the lowered ones — undecidable from the instruction, the third trade-off in §4.3 |
| try-with-resources: `Throwable.addSuppressed` and the **pair** of `close()` calls javac generates (normal + exceptional path, both at the try header's line, in a method holding the `addSuppressed`) | a written `close()` is alone on its line and stays (#26 §5); the exclusion is symmetric, so a tool that models try-with-resources is not charged |
| the `Objects.requireNonNull` a **bound method reference** emits | the shape `dup / invokestatic requireNonNull / pop / invokedynamic` is exact and nothing else produces it, so an explicitly written `requireNonNull(x)` **survives** |
| a compiler-synthesized default constructor, and the `super()` it emits | its body is exactly `aload_0; invokespecial super.<init>()V; return` — a structural test, no source tree needed |
| an **implicit** `super()` in a written constructor | see the trade-off below |
| `java.lang.Enum.<init>(String,int)`, and an enum-constant body's chain to its enum | JLS plumbing |

**Deliberately NOT excluded: a record's generated `equals` / `hashCode` / `toString`.** They are
JLS-mandated members no source writes, exactly like an enum's `values`, and the asymmetry is
stated rather than hidden (#47): the enum rule removes members whose *call sites* are also
generated plumbing (`$values`, `<clinit>`, the switch-map lookups) or are spelled by the source as
the enum's own API; a record's `a.equals(b)` is a call the source writes, to a method javac emits
with a real body, and every tool and both bytecode readers see it. Removing the member would
remove a written call. No scored site targets one on the current subjects (spring-boot has 17
such members and 0 sites); a record-heavy subject will, and this line is what applies then.

A **private or static** method of a superclass is never a declaring ancestor: a call on the
subclass cannot reach it, so naming it is wrong, not vague (#47).

### 4.1 Constructor parameters are de-synthesized (on both sides)

javac augments a constructor in three ways the source never wrote, and scoring a source-based tool
against the augmented list charges it for parameters that are not in the code it read — `new Inner()`
becomes a miss because the oracle demanded `Inner#<init>(Outer)`.

| augmentation | evidence, read structurally from the class file |
|---|---|
| an **enum** constructor gains a leading `(String, int)` | the class extends `java.lang.Enum` |
| an **inner / local / anonymous** class's constructor gains a leading enclosing instance | the class file's `InnerClasses` (a non-static member class) or `EnclosingMethod` (a local/anonymous class in an instance context) attribute, confirmed by the constructor's first parameter type. **Not** the `this$0` field: javac ≥ 18 omits it when the inner class never uses the outer instance while the constructor still takes it (JDK-8271623), and the torture subject's own `new Middle().new Deep()` was scored as `Deep#<init>(Middle)` (#26 §1) |
| a **local / anonymous** class's constructor gains one trailing parameter per captured local | the synthetic `val$x` fields |

All three are removed from the *emitted* spelling. Hierarchy lookups still use the declared list,
because that is what the class file is keyed on.

### 4.2 Exclusions are symmetric — they remove a construct from BOTH sides

An exclusion that applies only to the oracle is not an exclusion, it is a penalty. A tool that
reports an implicit `super()` is reporting a real instruction; the benchmark simply decided not to
measure it. Charging that as a false positive marks the tool imprecise for answering a question
nobody asked.

So `oracle/ClassfileGroundTruth.java --mode excluded` emits the application-internal edges and the
callers that §4 removed, and `bench/score.py` removes matching rows from **every tool's output**
before scoring, counting them as `§4-excluded` in the report.

This was not a theoretical concern. Before the mechanism existed, **all twelve** of CodeQL's
false positives on the torture subject were constructs the oracle had excluded — a precision figure
that was entirely an artefact of the asymmetry.

**And an exclusion must never delete an answer the ground truth still asks about.** `Foo#<init>()`
and `Foo#<init>(int)` are one string at Tier B, so excluding a synthesised default constructor also
deleted every answer about a hand-written one; and a lambda folded onto a `<clinit>` put scored sites
under a caller that was simultaneously on the exclusion list (issue #3). Both lists are now keyed at
full signature fidelity, filtered against the live ground truth at both tiers, and the Tier B forms
are admitted only where no scored site or possible edge spells the same way.

### 4.3 Two exclusions are trade-offs, stated rather than hidden

* An **explicitly written bare `super();`** compiles identically to the implicit one and is dropped
  with it. Undecidable from the instruction. Excluding it mis-scores the rare written form;
  keeping it charges *every constructor in the corpus* with a call the source does not contain.
* An explicitly written **`x.intValue()`** is dropped with unboxing, for the same reason.

Both trade a small, bounded error for a large, systematic one. The direction is stated so a reader
can disagree with it knowingly.

---

## 5. Fidelity tiers — why no tool is punished for its output structure

The tools do not agree on what a call edge *is*:

```
java.lang.classfile / CodeQL   torture.Shape#area(int)     owner + name + erased params
axiomengine               torture.Shape#area(int)     owner + name + params
tree-sitter indexers           Shape.area                  owner + name, no params
some graph exporters           area                        a bare symbol name
```

Scoring all four against a signature-exact oracle would report the last two as near-zero. That
number would be an artefact of the comparison, not a finding about the tool.

**So every comparison happens at a declared tier, and the ground truth is projected to that tier
too.**

| tier | spelling | what it measures |
|---|---|---|
| **A** | `type#name(params)` | overload selection — the only tier where it is visible |
| **B** | `type#name` | the highest fidelity *every* tool can express → **the headline** |
| **C** | `name` | the floor; name collisions inflate it, and the link-group table is **not** reported here (its key *is* the callee name, so every tool would score 100% by construction) |

A tool declares its ceiling in its adapter. Above that ceiling it is reported **`n/a`, never `0`** —
a blank and a zero mean opposite things.

**What Tier A's parameter list is.** Java: the erased descriptor, simple-named (`List`, not
`List<String>`), with javac's synthetic parameters removed (§4.1). TypeScript: the **declared
annotation text** of the resolved declaration's parameters, with all whitespace removed
(`T|ReadonlyArray<T>`) — never a checker-instantiated signature, which a union receiver can
synthesise into a method no source declares (`Bx#set(never)`, #68 §2). The resolver applies the
same whitespace fold to a tool's parameters, so Tier A measures overload selection, not
typography (#68 §1). The projection to a tier is symmetric and mechanical.

### 5.1 Reading a tool's notation is not charity; guessing would be

`bench/resolve.py` maps each tool's spelling onto the canonical one. `torture.F01Polymorphism$Base`,
`torture.F01Polymorphism.Base`, `Base`, and (file `torture/F01Polymorphism.java`, symbol `Base`) all
denote one type, and all resolve. A **unique** simple name resolves, because in a subject with one
`Base`, `Base` denotes it — that is reading notation, not repairing it.

A reference that matches **more than one** application type is reported `AMBIGUOUS`; one that
matches none is `UNKNOWN`. Both are **excluded from the score and counted in the report**, never
resolved in the tool's favour and never counted against it. Picking whichever candidate made the
edge a true positive would be scoring our own tie-breaker; calling every ambiguous row a false
positive would charge a tool for a package name it never claimed to omit.

What stops exclusion from being a free pass: the counts sit in the same table row as the score they
affect. A clean precision computed over 11 of 400 rows cannot be read as a clean precision.

A tool that reports a **file** gets it used for disambiguation, not merely as a fallback: Java
requires the public top-level type to be named after its file, so `torture/F02Generics.java` narrows
a flattened `torture.Node` to one candidate without any guessing. The file that decides a callee is
the **callee's own** (`callee_file` — the file the tool's node for the target lives in; gitnexus and
code-review-graph carry one for every target). The **call site's** file decides a callee only in
Java and only for a candidate nested in that file's top-level class, which is what Java name
lookup finds first for a simple name written there (JLS §6.4.1: a member type shadows an import);
a candidate that merely lives in the same package, or in another file, is not decided by where the
call was written, and TypeScript is never decided this way (an import can alias). Before either
file is consulted the method name has already dropped the candidates that neither declare nor
**inherit** the member — a container that inherits `visit` is as good an owner of `visit` as one
that declares it (#36).

A **method is placed by the container the tool named and the method name, one level down.**
fp-ts builds every instance as `return { map: …, ap: (fa, fb) => pipe(…) }` — a literal bound to
nothing, keyed by the oracle `Applicative.ts:$obj:ApplicativeComposition@308`, a key no tool can
spell; every tool that names the function says `Applicative.ts#ap`. ioredis writes
`const reject = () => …` inside a method of `Cluster`; the oracle's container is `Cluster`,
CodeQL's the module. In both the tool named the enclosing container and the name, and the name
is declared by exactly one container nested in it — so that is what the spelling denotes, the way
a unique simple name denotes its type. Two nested containers declaring the name stay `AMBIGUOUS`;
a name the container declares itself is never re-placed. The same rule reads a Java `Outer#run`
onto the one nested or anonymous class inside `Outer` that declares `run`.

A **callee with no owner is read like a bare type name.** code-review-graph records half of
apache-ant's calls as a bare `getProject` / `isReference` with no class. Where exactly one
application container declares a method of that name, the name denotes it — the same rule that
lets a unique simple type name resolve; where several do (`getProject`, `log`) the row stays
owner-less, unspellable at Tier B, counted in the `excluded` column. A caller is never read this
way.

An **inherited member is read the way the language reads it.** `square.tag()` where `Square`
extends `Base` and only `Base` declares `tag`: the source, the bytecode's symbolic reference and
four of the tools spell the target `Square#tag`; JVMS §5.4.3.3 (and a TypeScript prototype
lookup) resolve that spelling to `Base#tag`, which is what CERTAIN holds. The resolver performs
the same lookup for a CALLEE — nearest declaring ancestor, superclass before interfaces,
`AMBIGUOUS` when two are equally near — because scoring the language's own notation as `wrong`
charged those tools for a spelling, not an answer. A caller is never re-placed this way: a
method body is in the class that declares it.

An **ambiguous caller is placed by its line, too.** When the container a tool named matches
several application types that all declare or inherit the method — a nested class and its
enclosing class, an interface and its implementation — and the tool reported a line, the
candidate that has a caller of that name at that line in the ground truth is the one meant; with
none or two, the row stays `AMBIGUOUS` (#17).

A **multi-candidate row is fan-out.** A tool that answers a site with several targets under one
label — axiom's `multi_inferred`, codegraph's `interface-dispatch`, CodeQL's `getACallee(_)` at
every imprecision grade — is read as one edge per candidate, each carrying the label. The
benchmark does not pick the tool's best candidate for it: the set is the answer, and a uniquely
linked group answered with a set is `over_fan`, not `exact`. The per-label table in each report
attributes every group's verdict to exactly one label so the label columns sum to the tool's own
totals (#41).

An **unnamed caller is placed by its line.** A tool that could not name a function — axiom's
`<arrow>` for an object-literal property arrow, whose name its IR does not record — still says
which file and line the call is on. Where the oracle records exactly one caller at that line, that
is the function; where it records two, the row stays unplaced. Without this the row was a false
positive AND a miss, and deleting it raised the tool's precision — abstaining scored better than
answering, which is the one outcome this protocol is written to prevent (#22).

A **path is not a basename.** A tool that reports only a file name (`Array.ts`) is placed by it;
a tool that reports a path (`dtslint/Array.ts`) has named a file, and a file outside the universe
is unmapped — it is not read as the subject's `Array.ts` because the basenames coincide. The
resolver did exactly that for the test trees the tools index as context since #20, and charged
every top-level call in fp-ts's dtslint tests to the tool: CodeQL's precision there read 0.30
until the rule was made explicit.

A **type-less** reference is scoped **by name**, not discarded. Requiring a type would delete every
row of a name-only tool before scoring it, and report as "found nothing" what is actually "the
harness threw the answer away for being spelled without an owner". `bench/selftest.py` asserts
against this.

---

## 6. The link-group metric — the number that separates the tools

`precision 0.98` says nothing about the question that decides whether a graph is usable: **when the
language admits exactly one target, did the tool name that one method, or hand back a set?**

A **link group** is `(caller, callee-name)` — every call written in one method to one method name.
A group whose POSSIBLE set has exactly one member is **uniquely linked**. Each tool's answer is
scored as exactly one of:

| verdict | meaning |
|---|---|
| `exact` | that one target, alone — the only clean win |
| `over_fan` | that target plus others, all inside POSSIBLE ∪ DECLARING_ANCESTORS — sound but imprecise |
| `polluted` | that target plus something no envelope admits |
| `ancestor` | only a supertype that DECLARES the member — the language-level answer, vague rather than wrong; not exact, no recall |
| `wrong` | targets emitted, none of them right — a silent wrong answer |
| `unknown` | nothing scored, but the tool wrote a row saying it could not resolve a call at one of the group's lines (axiom's `ambiguous_unknown`, handed over as `meta.unresolved_sites`) — a declared gap a consumer can route around (#69) |
| `unplaced` | the tool answered, but every row for the group was excluded by the resolver (ambiguous container, owner-less spelling, target outside the universe) — neutral for precision, not found for the group (#69) |
| `missed` | nothing emitted — a silent gap |
| `partial` | (ambiguous table only) a name-pooled group — several one-target calls of one name in one method, no dispatch — of which the tool named some but not all (#70) |

An exclusion is therefore neutral for precision and read as *not found* for recall and for the
group; §5.1's "never counted against it" holds for the false-positive side only, and the
`unplaced` bucket says how often the other side happened. The unit of the headline is the
`(caller, callee-name)` group with one possible target; a method calling two different one-target
methods of the same name (`new A()` and `new B()`) forms one pooled group that is not uniquely
linked by name — those groups and their call sites are counted beside each report's ambiguous
table, and naming all of their declared targets is `exact` there.

**A call whose declared target is outside the application is a boundary, in both languages.**
`map.get(k)` on a `java.util.Map`; `layout.getId()` on a dependency's interface. The envelope
this oracle can compute runs over the APPLICATION's concrete receivers only — every JDK or
dependency implementation of `Map` that actually runs there is invisible to it — so an envelope
for such a site is computed over half the receivers, and "uniquely linked" means nothing. The
first version scored these as internal sites with an empty CERTAIN and the application
implementors as POSSIBLE (14% of maven-core's uniquely-linked groups); once the oracle read the
JDK's intermediate superclasses (#30), one anonymous `AbstractMap` subclass in maven-core became
the *unique* target of every `Map.get` in the code base, the tool that guesses application-only
CHA was credited for each, and the tool that answered `Map#get` was charged. The TypeScript
oracle had always stopped at the subject's edge. Both now do: the site is `boundary`, forms no
group, earns no recall and has no unique link; the application implementors are kept as ACCEPTED
answers — naming one is not a false positive, naming none is not a miss — and a row naming the
external declared method is out of the universe and unmapped, like every boundary row.

**A call through a function value is neutral on both sides, by line.** The oracle records such a
site as `indirect` and does not score it; the neutral zone keyed by `(caller, name-as-written)`
matched a tool that reported the name as written and missed one that resolved the value through
data flow and named the function that runs (`debug(...)` → `wrappedDebug`). A row whose caller and
line coincide with an indirect site, naming no direct call at that line, is now neutral too.
CodeQL's precision on fp-ts read 0.50 under the old rule and 0.95 under this one; on ioredis 0.57
and 0.79. The rule needs a line from the adapter; a tool that emits none is scored as before.

Grouping on `(caller, callee-name)` rather than on a source line is deliberate: it needs no line
numbers, so a tool that emits none is measured on exactly the same footing as one that does.

**Groups are formed at the tier being scored.** Keyed at Tier A and matched at Tier B, two overloads
of one caller merged on the answer side and stayed split on the truth side, so a tool that resolved
both correctly read `polluted` on both — a ceiling of 94.9% on netty-transport that belonged to the
scorer, not to any tool (issue #2). The headline denominator is therefore counted at the headline
tier, and a **ceiling gate** in the self-test asserts that a tool answering every group correctly
scores 100% with empty error buckets at every tier.

**Genuinely ambiguous groups are reported in a separate table**, and read differently: there
`over_fan` is the *correct* behaviour, and `exact` may mean the tool guessed one branch and dropped
the rest. Combining the two tables would reward the opposite behaviour in each.

---

## 7. Scope

Only **application-internal** links are scored — both endpoints in a type the subject declares.
Everything else is dropped from *both* sides. A tool that also models the JDK is neither rewarded
nor charged for it; the subject's own code is the one thing every tool here is trying to do.

Boundary sites (a call leaving the application) are **counted and reported** — a tool that invents
an application-internal target for one *is* wrong — but they contribute to no recall denominator.

**Every ranked comparison is library-free.** Dropping boundary links does not make the inputs
equal: an *internal* call whose receiver comes out of a library call (`list.get(0).foo()`) can be
typed only by a tool that was given the library. A run that was — AxiomEngine with the JDK's platform
IR, CodeQL compiled against a classpath — is therefore never ranked beside source-only tools. It is
published in its own table beside the same tool's library-free run, so what the library bought is
visible and nothing else is affected. The split is read from the budget each row records
(`bench/readme_tables.py` `LIBRARY_BUILDS`), not from a list of tools.

---

## 8. Determinism

Deterministic tools are run once. The canonical edge file is written **sorted**, so a tool that
enumerates its graph in hash order still produces a byte-identical file across runs; a benchmark
that cannot diff two runs cannot detect drift.

Agent- or LLM-driven tools are run **N times** and reported in a separate tier with per-run
variance. They are never averaged into the deterministic table.

Every input is SHA-256'd into `results/<subject>/scores.json`. A results directory whose manifest
does not reproduce is one that cannot be trusted, and the manifest exists to make that checkable
rather than assumed. **What is hashed is the LF-normalised content** — `\r\n` is read as `\n`
before hashing, and every writer in the harness (the Java oracle, the Python edge writers) emits
`\n` regardless of platform — so the hash is a claim about content, not about the separator a
JVM or a text stream chose on Windows (#45). The Java ground truth was shown to reproduce
byte-for-byte across macOS/arm64 and Windows/AMD64, JDK 24.0.1 and 24.0.2, once that was fixed.

Nothing machine-specific is written into a hashed file: `write_edges` spells an edge file's
`_meta.source` relative to the repository, so the same run from two checkouts hashes the same
(#104). And a tool is pinned with everything under it: each installs exactly the committed lock
beside its `install.sh` (`requirements.lock` with `pip install --no-deps`, `package-lock.json` with
`npm ci`), because the tree-sitter grammar versions decide which calls it extracts, and pinning
only the package left them to float (#103).

---

## 9. Dev and held-out subjects

A benchmark whose normalisation rules were tuned until the numbers looked right is not a
measurement, it is a fit. Every convention in this document was written while looking at a **dev**
subject.

| split | subjects | rule |
|---|---|---|
| **dev** | `torture`, `netty-transport`, `maven-core`, `spring-boot` | the harness may be iterated against these |
| **held out** | `hibernate-core`, `tomcat-embed-core` | scored once; a bad result is a **finding to report**, not a rule to adjust |

The guard is structural, not editorial: `bench/subject_info.py` refuses to resolve a held-out
subject unless `--allow-heldout` is passed, and `run/subject.sh` passes it only for an explicit
`--heldout` on the command line. A split that can be crossed by accident is worth nothing.

If a convention has to change because of something a held-out subject exposed, that change is a
change to the *protocol*, it invalidates the dev numbers too, and both are re-run and re-reported
together. It is not a quiet fix.

## 10. Known limitations

Stated because a benchmark you cannot see the edges of is not usable.

* **The torture subject is 592 lines.** It is a construct microbenchmark — it shows *which* language
  feature a tool loses, which an aggregate cannot. It cannot separate tools at scale. Large
  subjects (Spring Boot, Cassandra) are pinned by commit SHA and scored by the same harness.
* **Reflection is out of scope by construction** for every tool, and the subject's `F09` family
  asserts those sites are *declared* unknown rather than silently dropped.
* **RTA is unsound** (§2.1) and is never a precision denominator.
* **`recall_possible` is not a target to maximise.** Emitting the entire CHA envelope at every site
  would score 1.000 on it. Read it against precision and against the `exact` rate, never alone.
* **Two exclusions are documented trade-offs** (§4.2), not decidable facts.
