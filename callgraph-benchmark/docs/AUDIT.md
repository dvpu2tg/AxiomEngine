# The audit — what was filed against this benchmark, and what each finding changed

Thirty-two issues have been filed against this benchmark's own measurements. This page is the
record. The README carries the two-line version.

## Issues #1–#8: the scorer

Four changed numbers:

* **The null model was winning** (#1). Emitting the entire CHA envelope at every site scored 1.000
  precision and topped the headline on every Java subject. `prec-strict` is the fix, and the
  italic floor row is what keeps it visible. **This reverses a claim made here earlier**: axiom's
  `R possible` lead on `torture` (0.937 vs CodeQL's 0.757) was credited as dispatch coverage; its
  `prec-strict` there is 0.757 against the null model's 0.767. That column was inflation.
* **The headline had a scorer-owned ceiling** (#2): groups keyed at Tier A, answers matched at
  Tier B, so a *correct* tool capped at 94.9% on netty-transport. Groups are now formed at the tier
  scored; denominators moved (2,150 → 1,908 on netty) and are counted at the headline tier.
* **Exclusions deleted answers still being asked for** (#3), at both tiers. A self-test **ceiling
  gate** now asserts a correct tool scores 100% with empty error buckets, and it caught residuals on
  apache-ant (a `/*package-private*/ class` a column-0 regex could not see) and fp-ts (a neutral
  zone swallowing a scored group) that nothing else would have.
* **axiom's `needs` column read `source only`** (#4) while it was staged with 63 platform-IR
  modules — the budget flag was computed and never passed. It fails closed now: a closed vocabulary,
  required on every adapter.

And one that the audit predicted (#7.3, *adapter effort is a confound*): axiom scored **4%** on
fp-ts because its IR names every arrow function `<arrow>` and records the binding in a separate
column the adapter was not reading. Reading it: **67%**. Sixteen-fold, from the adapter alone.
Every per-tool convention the adapters implement is now something a reader should expect to find
listed, and a low score on a new subject is checked against the adapter before the tool.

## Issues #9–#12: disclosure and the null model

* **TypeScript reports claimed bytecode provenance** (#9). The provenance block is per language
  now — the TypeScript one says "the compiler's type checker, `getResolvedSignature`", and the
  function-value exclusion (6–17% of sites, `indirect`) is printed in every denominator table.
* **Confidence labels were carried and never reported** (#10). Each label's rows are now scored
  on their own in a table; on rxjava 145 of graphify's 148 wrong answers sat in its
  *higher*-confidence `EXTRACTED` class, and 111 of axiom's 113 polluted rows are `multi_inferred`.
* **The gitnexus adapter dropped the callee's file** (#11) — 9,342 rows excluded as ambiguous on
  rxjava, 9,332 of which the tool had resolved. `Edge.callee_file` carries it now.
* **`codeql-dispatch` ranked first while scoring below the null model** (#12). On a
  uniquely-linked group the envelope *is* the one right answer, so an enumerator scores `exact` by
  construction. The rule that separates the two is now the tool's own output composition: a row is
  **envelope-class** when the share of its rows that are possible-but-not-declared reproduces at
  least 90% of the envelope's own fan share and its `prec-strict` does not beat the null model's.
  The first version of that rule used `prec-strict` alone, and on kysely (envelope 1.2×, null
  strict 0.805) it tagged five of six tools as enumeration — tools with fan shares of 0.006, i.e.
  tools with plain false positives. A false positive outside the envelope is a wrong answer; it is
  not evidence the tool listed the envelope.

## Issues #14–#15: the TypeScript harness punishing projects for their layout

* **Gate 4 dropped tsconfig `paths`** (#14). type-graphql imports itself as `@/errors`; the
  synthesised config popped the mapping as a build-only key, and every import-resolving tool saw
  ~200 dead internal imports. CodeQL 38.5% → 89.1% recall with the mapping kept and re-rooted;
  graphify 37.7 → 65.0; code-review-graph 20.6 → 41.2. gitnexus does not read tsconfig and did not
  move. No other scored subject uses `paths`.
* **Arrow-function naming was wrong on both sides** (#15). The oracle keyed a class-field arrow
  (`onPointerDown = (e) => …`) by line, so excalidraw's `App` had 103 sites on `App#<anon@7756>`
  that every tool correctly naming `App#onPointerDown` missed; and it folded an arrow behind a
  wrapper (`withBatchedUpdates((e) => …)`) past its field to `<module>`. The axiom adapter, for its
  part, read only the variable binding out of an IR that also states field bindings and the
  enclosing member of a closure. Both fixed to the one table in `docs/PROTOCOL.md` §3.1, applied
  to every tool: gitnexus rose on kysely too. The same pass found `function ctor(…)` in typedoc
  being rewritten to `constructor` by the Java alias list (ceiling gate), a doubly-nested
  anonymous class in netty that the flatten mutation could not resolve (self-test), and axiom's
  `<function-type>` targets — the tool's own statement that a call goes through a function value,
  which the oracle records as `indirect` and does not score — being charged as false positives.

  Effect on axiom, uniquely-linked exact at Tier B, as committed in bc1d8e1 (the numbers first
  quoted in issue #15 were an intermediate state before the object-literal and `<function-type>`
  rules — #23 records the discrepancy): kysely 61.9 → 77.7, typedoc 67.7 → 85.8, fp-ts
  66.7 → 89.8, ioredis 63.1 → 75.5, excalidraw 46.5 → 80.8, type-graphql 25.6 → 86.5.
  Effect on the others: excalidraw codeql 55.2 → 71.5, code-review-graph 54.4 → 71.1; kysely
  gitnexus 60.0 → 63.1. The size of the move is the point: a naming convention on either side of
  the comparison was worth more than any difference between the tools, and every TypeScript number
  published before this pass was measuring the harness.

### rxjava, and why `R possible` is not a quality score

rxjava's CHA envelope was **696,686 edges against 15,638 certain — 44×** at the time (380,323 and 24× after the second #30 pass) — because its functional
interfaces have hundreds of implementers each. Every resolving tool reads 0.01–0.05 on
`R possible`; `codeql-dispatch`, which emits roughly the envelope, reads 0.884. On this subject the
column measures how close a tool is to the null model. `R certain` and `exact` carry the
information: `codeql` 99.1% / axiom 98.5% / `codeql-dispatch` 98.5% — the last with `prec-strict`
0.017 against the null model's 0.021, i.e. enumeration. The fan-out tool on this subject is
gitnexus (47,524 edges for 15,638 calls, strict 0.26), not graphify.

## Issues #16–#20: "why are the others low?" — because, on TypeScript, the harness was

The user asked why every tool but one scored low on TypeScript and whether the measurement was
at fault. It was, for the tool that mattered most for the comparison:

* **CodeQL's TypeScript query dropped every module-level caller** (#16). `call.getContainer().(Function)`
  matched nothing for a call at module top level, which is how fp-ts builds every instance: 750
  uniquely-linked groups `missed` with the caller absent from the output entirely.
* **A method nested in the container the tool named was unmatchable** (#17): fp-ts's returned
  object literals (`Applicative.ts:$obj:…@308#ap` in the oracle, `Applicative.ts#ap` from every
  tool) and ioredis's named arrows inside class methods. The resolver now places a method by the
  container named and the name, one level down, when exactly one nested container declares it —
  the same reading as a unique simple name. Applied to every tool.
* **The indirect-call neutral zone matched by name-as-written** (#18), so a tool that resolved a
  function value through data flow and named the function that runs was charged a false positive
  for agreeing with the oracle: CodeQL 0.50 → 0.94 precision on fp-ts, 0.57 → 0.80 on ioredis.
* **An external declared target gave one verdict to two behaviours** (#19): naming the declared
  method on a dependency's interface and naming nothing both read `missed`. 14% of maven-core's
  uniquely-linked groups are of this kind. The declared target is now the group's declaring
  ancestor: CodeQL's `getCallee` on maven-core reads 291 `ancestor` / 17 `missed` where it read
  308 `missed`; `exact` is unchanged for every tool.
* **Confidence terms were not being carried for three tools** (#10, reopened): codegraph's
  `resolvedBy`/`confidence`, GitNexus's `reason`/`confidence`, CodeQL's `imprecision` grade. All
  three are carried verbatim now and scored per label; a tool's own "I did not resolve this" rows
  (axiom's `ambiguous_unknown`) are counted and listed beside the table.
* **The tsconfig synthesis was still wrong** (#14, reopened): the comment stripper read
  `"@/*": ["./src/*"] … "src/**/*.ts"` as one block comment and silently handed the tools a config
  with no compilerOptions; `extends` was dropped, so excalidraw's tools had neither `jsx` nor its
  path mappings. Fixed; and the monorepo-sibling limitation that remains is #20, open.

The TypeScript torture subject gained two families for this — `t06-arrows.ts`, one row per way an
anonymous function gets its name, and `t07-paths.ts`, a path alias — and every torture subject now
ships `EXPECTED.md`, the oracle's own site table rendered for a reader to check construct by
construct before the same oracle is trusted on 35,000 sites of apache-ant.

Effect on CodeQL, uniquely-linked exact at Tier B: kysely 59.3 → 74.6, typedoc 70.8 → 76.2,
fp-ts 67.9 → 96.2, ioredis 66.0 → 83.7, excalidraw 71.5 → 76.1. axiom moved by at most a point.
The margin the previous version of this page reported was, to that extent, the harness's.

## Issues #5, #6, #20, #22, #23: the open items, closed

* **Call chains** (#5). `reach@k` — the ordered pairs joined by a call path of length 1..k — is
  scored for k = 1, 2, 3 against the closures of both bounds: `R@k`, the harsh `P@k` (against the
  declared graph's closure), the permissive `P-env@k`, and `blowup@k`, the size of the tool's
  answer over the true one. k = 1 is the edge metric. In every `report.md`.
* **The null model's other end, and a real CHA competitor** (#6). An `ideal` reference row (the
  correct answer for every link group; `needs: oracle`) brackets every column from above the way
  `cha-null` does from below — and it does not read 1.000 on `prec-strict`, because a group whose
  declared target is external is answered with its one implementer. WALA 1.6.7 runs as three rows
  on a declared `bytecode` budget — `wala-cha`, `wala-rta`, `wala-0cfa` — over the same class
  files the oracle reads, every application method an entry point, dependencies absent as for
  every tool on a Maven subject. On JDK 21 (Shrike reads class files up to Java 21; local subjects
  are compiled `--release 21` for that reason).
* **Monorepo siblings** (#20). The tools now index from the program's common ancestor when the
  checker's program has files outside the subject — excalidraw's `packages/`, typedoc's and
  fp-ts's test trees — with the subject's directory stripped from their module paths by the
  scorer (`--module-prefix`). Gate 4 now means what it says: the tools are given the program the
  checker loaded.
* **Unnamed callers were charged and the charge could not stand** (#22, found by the peer
  session). axiom names an object-literal property arrow `<arrow>` because its IR does not record
  the property name; the row still carries file and line, and deleting such rows *raised* its
  precision — abstaining beat answering, which the protocol forbids. A `<arrow>` caller is now
  placed on the one oracle caller at that line, the same reading as the neutral zone by line
  (#18); a line with two callers stays unplaced. ioredis axiom 75.5 → 89.8, excalidraw
  80.9 → 89.8, fp-ts 89.9 → 90.8 (the fp-ts codeql row moved 96.2 → 95.3 from #20's layout,
  not from this). TypeScript after the third pass: axiom 87.1 mean against codeql 81.2.
* **Record-keeping** (#23, peer session). Seven "after" numbers in the closed issues were
  intermediate states; the AUDIT paragraph above now quotes the committed ones and says so.
  `typescript/run/verify.sh` exists (the README had promised it); the Java verifier's re-score
  was missing `--timings` and so could never be byte-identical — fixed. Every committed
  `scores.json` carries the `chains` block.

## Issue #25: the WALA driver, reviewed by the peer session

Three findings on `java/adapters/wala/WalaCallGraph.java`, two verified on output:

* **Every method reference was dropped.** WALA's CHA graph has no target for an invokedynamic and
  its propagation builders route `Foo::bar` through a synthetic summary class in its own loader,
  so the enclosing method never showed the edge: torture has 8 METHODREF sites and `wala-cha`
  missed exactly 8 groups. The driver now reads WALA's own IR for every application method and,
  for each LambdaMetafactory bootstrap, emits the edge from the enclosing method to the
  referenced method — the oracle's own convention for a METHODREF site.
* **Nested anonymous classes were half-spelled** (`ServerBootstrap$1$anon:Runnable`): only the
  last numeric segment was converted. Every numeric segment is now converted outermost-first
  through the class hierarchy (`Outer$anon:A$anon:B`); netty's 365 rows with a raw `$N` are gone.
* **Entry points.** `AllApplicationEntrypoints` fabricates one arbitrary implementor per
  interface-typed parameter, which made the RTA and 0-CFA rows a hierarchy-order sample. WALA's
  `SubtypesEntrypoint` allocates every JDK subtype too and did not finish on a parameter typed
  `Object`; the driver now allocates every concrete *application* subtype of each parameter (plus
  the declared type where concrete) for the 0-CFA row — the row whose graph the receivers decide.
  CHA is hierarchy-driven and RTA's instantiated set is every `new` in the application once every
  method is reachable, so those keep WALA's default entries (the subtype allocations made RTA run
  50× longer on rxjava). Reflection is off and dependencies are absent, and the adapter says so.

## Issues #26–#32: the oracles themselves, and what "verified" had not covered

The peer session audited the two oracles and the adapters against the specifications they claim
to implement — the JVMS for Java, the compiler for TypeScript — rather than against each other.
Gate 1 (two readers of the bytecode) and gate 1b (a third reader of `certain`) had never checked
the **envelope**, and the conventions layer had errors gate 1 cannot see by construction.

* **The Java envelope was not the CHA envelope** (#30). `possible` was "every subtype that itself
  declares a member with the same erased parameter list, bridges skipped". Against an independent
  implementation of JVMS §5.4.3.3 + §5.4.6 on rxjava it omitted **8,172 runnable edges** (generic
  overrides reachable only through their `ACC_BRIDGE` forwarder; implementations inherited from a
  non-subtype; method-reference dispatch) and included **56,403 impossible site-targets** (members
  of non-subtypes of the receiver; abstract re-declarations); 16 of 20 sampled ambiguous groups
  were wrong. Both errors move the `unique` flag the headline is built on. Rewritten as JVMS
  resolution + selection with bridge following; **gate 1c** (`java/oracle/EnvelopeCheck.java`,
  the peer's checker) recomputes every site's envelope independently and refuses the subject on
  any disagreement. Every Java subject passes it.
* **Seven Java conventions were wrong** (#26): the enclosing-instance parameter was read from the
  `this$0` field javac ≥ 18 omits (the torture subject itself scored `Deep#<init>(Middle)`);
  the universe was not de-synthesised while the sites were; `values`/`valueOf` were dropped by bare
  name on any type; a written `c.iterator()` was dropped with the lowered enhanced-for one (44 on
  apache-ant); try-with-resources `close()` pairs were scored although no source writes them (49
  on apache-ant); RTA missed default methods and counted a lambda's containing class as
  instantiated; synthetic `$SwitchMap$` classes were in the universe. All fixed; local classes of
  one name in one outer are keyed by line.
* **The TypeScript envelope was documented as declared heritage and computed as structural
  assignability** (#27), in the oracle's own header and in `docs/CROSS-LANGUAGE.md`; a union
  receiver's second constituent was outside the envelope of a "uniquely linked" group; a property
  bound to a named function was not a container; an `indirect` site was named `<anon@12>` and could
  never match the neutral zone. All four fixed, the docs rewritten to say what the code does, and
  `t08-envelope.ts` added with the peer's five programs.
* **Gate 0 and gate 4 refused good subjects** (#28, #29): implicit constructors counted as
  unresolved; tsconfig parse errors were silently ignored (got was measured under `module=None`);
  the TypeScript file comparison depended on the shell's locale (typedoc failed under
  `en_US.UTF-8`); `package-info.class` counted as bytecode without source (commons-lang3,
  jackson-databind, guava refused with zero real missing types). All fixed; the registry can carry
  `project_overrides`, and **ts-morph** clears gate 0 at 95.1% with an `exclude` and a `paths`
  mapping to a declaration file the repository commits — moved from blocked to dev.
* **Provenance and adapters** (#31, #32): the TypeScript index adapters recorded no version;
  installers wrote to `java/.tools`; codegraph's TypeScript rows declared Tier A while a Java
  signature parser returned `None` for every TypeScript signature (2,397 of 2,455 kysely rows
  unspellable at A) — a TypeScript signature reader now; graphify's `new X()` edges were
  untranslatable; the axiom Java adapter renamed any method sharing its class's name to `<init>`
  although the IR states the kind; CodeQL's `<obinit>` was mapped onto `this(...)`-delegating
  constructors too. All fixed.
* **WALA** is out of the comparison at the user's request (Java-only; #25's findings were fixed
  before the row was withdrawn). The adapter stays in the tree; it is not in the default tool set.

## Issues #33–#44 and the reopenings: the resolver, the labels, and what the tables let through

The peer re-audited main after #33 merged and reopened seven closed issues with new evidence,
then filed nine more. The pattern this time was not the oracles but the *layer between* a tool's
row and the verdict — the resolver — and the tables' own arithmetic.

* **The resolver returned RESOLVED when it should not have** (#36, #37, #17 reopened). A callee
  was narrowed by the *caller's* file, so `Node` became the `Node` in that file whether or not it
  declared `visit`, and the row was scored against a method that does not exist; a fully
  qualified `java.nio.file.Path` was read as `org.apache.tools.ant.types.Path` by simple name;
  interface members were candidates for the nested-container rule; an ambiguous caller stayed
  ambiguous although the tool had given the line. Now: the callee is placed by its own file
  only; a foreign package prefix is never re-read; the method name splits an ambiguous container
  *before* the file does, over declared-or-inherited members from a heritage file the oracles
  write (`gt.heritage.txt`, a fourth ground-truth input with its own hash); an ambiguous caller
  with a line is placed by the one candidate that has a caller of that name at that line; and a
  callee spelled on the receiver's type (`Square#tag`, declared only by `Base`) is resolved the
  way JVMS §5.4.3.3 and a prototype lookup resolve it. All in `docs/PROTOCOL.md` §5.1.
* **The Java oracle stopped at the JDK boundary** (#30 reopened). A class extending
  `AbstractList` did not see `AbstractCollection`'s members as inherited: JDK intermediate
  superclasses were absent from the hierarchy, so +859 internal sites on apache-ant had no
  certain target and became neutral. The oracle now reads every external supertype chain from
  the platform class loader (never into the application universe), and gate 1c's checker does
  the same independently — 25,321 sites compared on apache-ant, 0 disagree. Reading the JDK
  hierarchy exposed the next fault: with `AbstractMap` visible, one anonymous subclass in
  maven-core became the *unique* target of every `Map.get` in the code base — an envelope over
  the application's receivers alone, credited to the tool that guesses application-only CHA and
  charged to the one that answered `Map#get`. A call whose declared target is outside the
  application is now a `boundary` site in Java as it always was in TypeScript: no group, no
  unique link; the application implementors stay accepted answers.
* **The TypeScript oracle invented containers** (#39, #27 reopened). A member declared inside a
  type literal (`container as Options & { getValue(n): unknown }`) was keyed under the class
  enclosing the cast, so `ArgumentsReader#getValue` existed in the truth and the tool naming
  `Options#getValue` was wrong. The site is now redirected to the receiver's apparent type, or
  `indirect` when no real container declares the member (`t09-typelit.ts`). An imported
  generic parent (`extends Base<T>` from another module) was not followed through its alias.
* **The tables' own arithmetic** (#12, #1, #10/#41 reopened). The envelope-class rule used `<=`,
  and a dispatch row 0.0009 above the null model's strict precision ranked first unmarked on
  rxjava with a depth-3 reach 247× the truth: the rule is now a margin (strict < 1.5× null, fan
  ≥ 80% of the envelope's), applied to every row alike. F1 and MCC were maxed by the null model
  on 6 of 10 subjects because they are built on the permissive precision: the tables print the
  strict pair. The per-label table was dropped above 8 labels (no table for codegraph on rxjava,
  where `exact-match:0.7` held 1,650 of 1,819 wrong), double-counted groups, had no
  `polluted`/`over_fan` columns, and read every CodeQL TypeScript row as `imprecision=0` because
  the query asked `getACallee()` = `getACallee(0)`. Now: every labelled tool, labels grouped by
  term with rounded score sub-buckets, each group attributed to exactly one label so the columns
  sum to the tool's totals, and `getACallee(_)` with every grade carried.
* **What an adapter should not translate** (#40, #32 reopened). codegraph's
  `synthesizedBy: interface-impl` rows — a heritage relation, not a call — were scored as calls
  (1,078 on rxjava); its `A.m.<I$anon@N>` anonymous-class notation was unreadable. Both fixed.
* **What the selftest did not try** (#35, #43, #44). Every edge emitted twice scored identically
  and said nothing; a reversed graph was caught but 22 rows landed in `§4-excluded`; a fabricated
  caller on a type the application does not declare was excluded, not charged. Seven corruption
  checks added (17 in all): duplicates are stated (`duplicate_rows`), the out-of-scope count is
  printed as a share of what was emitted, and the fabricated-edge mutation picks an application
  alien (it chose `java.lang.Object#equals` on commons-lang3 and failed the gate for nothing).
  The Java constructor aliases renamed guava's real `TypeToken#constructor(Constructor)` to
  `<init>`; only `<init>`/`<constructor>` remain.
* **Provenance and time** (#38, #42). Held-out subjects had no pins — the first runner would have
  chosen the commit — and the Java fetcher recorded the first hash it saw. Every held-out subject
  is pinned to a release tag and tarball/jar SHA-256 chosen before any run, in its own commit;
  the fetcher fails closed. `seconds` included axiom's one-time Soufflé compile (82 s on a
  195-line file, 4 s on kysely): each tool is warmed before its timed run and the cold cost is
  recorded as `cold_seconds` with whether the cache was hit.

## Issues #45–#57: portability, the oracles' remaining conventions, and the tables' own honesty

Thirteen more, filed by the peer against `8830f1d` and the pass above. Every one is fixed on this
branch; the unit tests under `tests/` (gate 3a, 47 checks) pin each one as a fixture.

* **Nothing reproduced off macOS** (#45, #54, #56). Every manifest hash covered bytes whose line
  separator the JVM chose, so `verify.sh` could never pass on Windows for a reason unrelated to
  trust; the Java oracle now writes `\n` everywhere and the harness hashes LF-normalised content
  (§8 says so). `subject_info.py` emitted backslash paths that `sed` read as escapes and gate 4
  refused the torture subject; POSIX separators now. `javap_reader` decoded javap's stdout with
  the platform codec and, under cp936, an empty file reached gate 1 as "the two readers
  disagree" on commons-lang3 (9,473 identical instructions); latin-1, and the reader's stderr is
  kept. TypeScript results recorded `java`/`javac` and never the pinned `tsc`; they record
  `typescript` and `tsx` now.
* **The tables' own arithmetic, again** (#48, #49, #50, #51). The README said "every one is
  closed" while 17 were open; the sentence is gone and the audit trail is this file. The
  envelope-class rule fired on 0 of 82 cells; the null model's row is now printed as the floor
  it is, the † marker is a composition test with a margin, and *sharpness-adjusted exact* —
  exact% × `min(1, prec-strict / ideal prec-strict)`, the peer's proposal — is printed small
  beside every cell. It was the ranking column for one merge (#58) and was reverted the same
  day: it charges a tool for naming the overrides that can really run and charges nothing for
  edges never emitted, so a row with 65% exact and blowup 0.5× outranked one with 83% exact.
  The ranking is exact%, the benchmark's own question. The chains matrix printed `P@3 · blowup`, one number twice (P × blowup ≡ recall), and
  a blowup below 1× — a tool finding a third of the reachable set — looked like the best row;
  it prints recall now, and says what a blowup below 1× means. The Tier-B merge artefact #2
  removed from the unique table had moved into the ambiguous one: two declared runnable
  targets are no longer a fan, the count of merged groups is printed beside the ambiguous
  table, and the ceiling gate covers that table too.
* **What the gates could not see** (#46, #47, #52, #53). Gate 1b's one percentage was 92%
  notation; it buckets residuals now (spelling / convention / unexplained) and prints every
  unexplained one — 39 + 55 on apache-ant, each inspected so far a third-reader error. The Java
  oracle's RTA javadoc contradicted its code; a private superclass method was a declaring
  ancestor; records' generated members are kept, and §4 says why. The TypeScript oracle scored a
  variable holding a union of two functions as a certain call to one of them, let an interface
  member into `possible` through a union arm, seeded RTA with an uninstantiated declared
  target, expanded `new C()` over subclasses (32 kysely/typedoc constructor sites lost `unique`),
  named 114 typedoc callers after a *number* an arrow's result was assigned to, named an
  element-access call `<anon@N>`, and listed interfaces as classes with no constructor. All
  fixed; `t10-audit.ts` and `F11Conventions.java` carry the expectations, written before the
  oracles ran. And 804 of typedoc's call expressions (12.3%) that the checker cannot resolve
  produced no row and no count — the count is now in every TypeScript report and in RESULTS.md.
* **A subject blocked for the harness's own reason** (#55). cheerio's tsconfig sets
  `lib: ["ES2015.Core"]`, which replaces the default library; without `node_modules` the checker
  had no `Array`, `Object` or `Promise`, and the block blamed third-party types. With the same
  `project_overrides` mechanism ts-morph uses (specs excluded, `lib: ["ES2022","DOM"]`) it
  resolves 81.6% install-free and is a dev subject, reported in RESULTS.md.
* **Gate 3 scaled with the envelope, not the project** (#57): 253 s on rxjava, one pure function
  of the ground truth re-derived fifteen times. Memoised per ground truth and tier, and the
  resolver memoised per reference: 49 s.

* **A callee with no owner was unreadable** (follow-up to #32, found by the fairness check
  after this pass). code-review-graph records half of apache-ant's calls as a bare method name
  — `isReference`, `getProject` — and 26,962 of its 87,748 Java rows were unspellable at Tier B.
  Where exactly one application container declares that name, the name now denotes it, the
  same rule a bare type name has always had (§5.1); where several do, the row stays owner-less
  and counted. code-review-graph's Java found count rose from 20,741 to 23,436 (63.2 → 71.4%)
  and its precision fell (0.83 → 0.78): the bare names that were JDK calls are charged now
  instead of dropped. No other tool's numbers moved.

## Issues #66–#80 and the second reopenings: the lowerings, the envelopes, and what `missed` meant

The peer's sixth pass audited both oracles against JVMS-derived and checker-derived torture
packages compiled at two Java releases, the harness's timing, provenance and reading rules, and
the tables' definitions. Twenty-one issues; every one is fixed on this branch and pinned in
`tests/` (gate 3a), which now runs the Java conventions file at `--release 8` and at the current
release and requires identical sites.

* **Java lowering the oracle had not undone** (#66, #26, #77, #78, #79). On Java 8 bytecode —
  what apache-ant and rxjava ship — a nested class's call to a private member goes through
  `access$N` and `new Priv()` through a synthetic constructor accessor; both were dropped as
  synthetic, 108 written calls on apache-ant. A written `new Base()` inside a subclass
  constructor was read as the implicit `super()`; `hasNext`/`next` on a user Iterator subtype
  were dropped; a covariant `iterator()` was kept as a phantom site; a user `valueOf(int)` on an
  enum was excluded by name; a non-enum class's `static { }` block was not a caller (261 calls
  on apache-ant); a constructor reference did not instantiate for RTA; a multi-line
  try-with-resources scored both generated `close()` calls; a visibility bridge dropped the
  written call; a local class in a static initializer lost a real parameter; an instance field
  initializer was one site per constructor; an anonymous class's constructor chain was a second
  site under a caller no source writes; a transitive override (§5.4.5 b) was missing from the
  envelope and from the checker alike; site ids collided. All fixed; `F12Lowering.java` carries
  each expectation, and the envelope checker no longer counts a platform declaration as
  application-declared.
* **The TypeScript envelope, second pass** (#67, #68, #73, #74, #80, #53 §3). Library
  constructors were "calls through a function value" (123 of kysely's 241); a structural
  implementor of an instantiated generic interface was not found; an abstract re-declaration was
  runnable; a union with a library arm was uniquely linked to the own arm; RTA required the
  declaring class itself to be `new`-ed (191 typedoc sites); Tier A compared the oracle's
  whitespace-stripped parameters against the tool's spaced ones (383 of axiom's 551 Tier-A losses
  on kysely) and minted `Bx#set(never)` from a union receiver; a closure returned by a helper and
  stored in a field was a certain target keyed `<anon@N>` (33 typedoc groups no tool could win);
  a class field initializer belonged to the module (100 typedoc sites credited to the tool that
  said `<module>` and charged to the one that said `Application#constructor`); a static call
  dispatched over the class hierarchy; element-access and tagged-template calls were named
  `<anon@N>`. All fixed; `t11-envelope2.ts` carries the expectations.
* **What a verdict meant** (#69, #70, #12, #36). `missed` was three outcomes: 96% of axiom's
  kysely misses were calls it had flagged `ambiguous_unknown`, and answers the resolver excluded
  read as silence. `unknown` and `unplaced` now sit beside `missed`, summing to the same
  denominator; the adapters hand over the tool's own unresolved rows. A method calling `new A()`
  and `new B()` formed one "ambiguous" group in which naming one constructor read `exact`;
  those name-pooled groups are counted and a half answer is `partial`. † rows were ranked as
  leads; they are ranked with those cells left out, and ↓ marks a strict precision below the
  null model's for any reason. The call-site file narrowed a callee to the wrong nested class
  12 times on rxjava; it now narrows only to a class nested in the caller's own top-level class,
  and never in TypeScript, where an import can alias.
* **The harness** (#8, #71, #72, #75, #76). Two rows from one adapter each carried the whole
  adapter's wall-clock; the adapters record shared / own / staging phases and each row is charged
  shared + own, staging to nobody, and every tool has a warm-up. The CodeQL query library was
  unpinned (`"*"`) with no lock file, so a fresh CLI resolved a library it could not load and
  both CodeQL rows vanished silently; pinned (`java-all 7.8.2`, `javascript-all 2.6.18`) with
  lock files, a failed install is fatal, and the library version is recorded beside the CLI's.
  GitNexus's "line" was the caller's declaration row; it carries no call line now, so the
  line rules simply do not apply to it. A run passed without the tool under test; it refuses
  unless told the omission is intended. `prior_internal_use` reaches the report. The `axiom` row
  is absent, not `axiom-nolib` under another name, when no platform IR is staged. `typeRoots` /
  `types` are kept in the tools' tsconfig. The five compared TypeScript subjects are one choice:
  the pooled figure over all eight committed subjects is printed under the matrix, where the
  lead reverses.
* **Prose** (#27, #66, #67, #72): the structural-envelope sentence in CROSS-LANGUAGE said the
  opposite of the code and omitted that uniqueness itself depends on the envelope; stale counts
  and ratios in three documents and the oracle's header were replaced or removed.

## Issues #81–#83: the engine moved, two runners at once, and a copy that failed half-way

* **#81** — the engine repository was reshaped into one tree (parser + graph, #469) and its
  pipeline now writes `graph.sqlite` and deletes the raw Soufflé relations unless `--debug`; both
  axiom adapters read the old path, the row silently vanished, and the run passed. The adapters
  run the pipeline from `graph/pipeline/` (falling back to `src/pipeline/`) with `--debug`,
  read `raw/call-chain-edges.csv` when the root copy is absent, and refuse to produce a row from
  a layout they do not recognise; the parser is taken from inside the engine tree. Every axiom
  row was re-run against engine `febf8b4` (parser and engine one commit now).
* **#82** — two runners started together raced on tsx's compile cache inside gate 3a and one
  failed with its stderr swallowed. The oracle is invoked with `--no-cache` everywhere and the
  test's failure message carries the stderr.
* **#83** — the tools' copy of a TypeScript subject was made with unchecked `cp`s and gate 4
  compared the checker against the ORIGINAL tree, so a copy the disk cut short scored every tool
  on a partial program (axiom 89.8% → 45.6% on excalidraw with nothing in the report). Every copy
  is checked, the copy is compared file-for-file with what the checker loaded, and its file
  count and sorted-list SHA-256 travel into `run.staged_copy` in `scores.json`.

## Pass 8: the seven questions, a sixth Java subject, and two adapter faults found by it

* **Task scores** (`bench/tasks.py`). exact% counts edges; a consumer of a call graph asks
  questions. Seven of them are scored on the same Tier-B edges and truth: callees of a method
  and callers of a method (per-node F1), whether a path A→B exists (500 sampled declared pairs
  within 3 hops, joined by the tool within 6), blast radius (Jaccard of 3-hop transitive
  callers, 300 sampled), "nothing calls X" (precision and recall of the uncalled claim), the
  dispatch set at genuinely ambiguous sites (Jaccard against the runnable set — the envelope
  scores 1.0 by construction, `ideal` scores what a one-target answer scores), and file→file
  dependencies (F1). Samples are seeded; the README pools each column over the five subjects
  weighted by n.
* **gson** (`com.google.code.gson:gson:2.11.0`, pinned 2026-09-14) is the sixth Java subject,
  kept out of the five compared (chosen before) and folded into the full-set line under the
  matrix. Running it exposed two faults in the Java `axiom` adapter, not the engine: an edge whose
  caller the engine names without a line (`TypeAdapters$anon:TypeAdapter`) was placed by name
  and fell to the wrong anonymous class — every edge is now placed by its call line; and calls
  in field initializers arrived with a `FIELD_REGISTRY_*` owner and were dropped — they are
  charged to `<clinit>` for static fields and `<init>` otherwise, from `all-fields.csv`. Both
  fixes are pinned in `tests/test_adapters.py`. Re-adapting every Java row against engine
  `febf8b4` moved the pooled `axiom` figure from 95.1% to 96.3% (394 groups that were the
  adapter's misses); no other row moved. gson itself: `codeql` 97.9%, `axiom` 92.5%,
  `code-review-graph` 86.7%, `graphify` 74.2%; the remaining `axiom` misses there are the
  engine's (anonymous-class constructors in field initializers, `InstanceCreator#createInstance`
  through generics, `JsonReader#push` fanned to `JsonTreeReader#push`).
* **Labels.** The tool id `axiom` stays in adapters, edge files and `scores.json`; the generated
  tables print the product's name, `AxiomEngine` (`bench/readme_tables.py` `DISPLAY`).

## Issue #36, third reopening: the file that decides a callee, and inheritance in the name split

The reporter re-ran sixteen constructed resolver cases against `87ecdd5` with the scorer's own
call (`resolve(callee, callee_file, callee=True, context_file=call_site_file)`) and found four
still resolving to a container the tool had not named: J3, J5, J8, T4.

* **J5 / T4 — the second name split ignored inheritance.** `resolve` splits an ambiguous
  container by the method name twice: once before the file is consulted (declare-or-inherit,
  #36 first fix) and once after (declare only — written for fp-ts, where the module `Option` and
  the interface `Option` share a spelling and only the module declares `map`). The second pass
  dropped `p.A.Node`, which inherits `visit` from `p.Base`, and resolved to `p.B.Node` with no
  ambiguity reported. It now uses the same declare-or-inherit test. On real output the change is
  what the reporter predicted: graphify on apache-ant moves 127 groups to `unplaced`, **106 of
  which had been charged `wrong`** and 21 `exact` — the declared-only split had been a guess
  that was wrong five times for each time it was right. fp-ts is unchanged (an interface
  inherits nothing that declares `map`).
* **J8 — not a fault.** The case gives the resolver no heritage; with the heritage row the
  scorer always supplies (`p.Outer extends p.BaseOuter`), `Outer#run` resolves to the inherited
  `BaseOuter#run`, which the one-level-down rule already checks with `declares_or_inherits`.
* **J3 — the caller's file, and what the 12 rxjava rows were.** The rule on `87ecdd5` narrows a
  Java callee by the call site's file only to a candidate nested in that file's top-level class
  — the type a simple name written there denotes by JLS §6.4.1 (a member type shadows an import)
  — and never in TypeScript. Replaying it over every callee row of every tool on torture,
  maven-core, apache-ant and rxjava: it decides 685 axiom rows on rxjava (670 in the group's
  accepted set, 0 where another candidate was), 882 graphify rows (809 / 0), and the twelve
  code-review-graph rows the report names. Those twelve are not the scorer's guess: the tool's
  own target node for `downstream.onComplete()` at `CompletableOnErrorReturn.java:96` is
  `CompletableOnErrorReturn.java::OnErrorReturnMaybeObserver.onComplete` — it linked the call to
  the same-named class in the caller's file, a `CompletableObserver` that is not the
  `MaybeObserver` being called. The tool said which file; the adapter had not passed it. Both
  code-review-graph adapters now carry the target node's `file_path` as `callee_file` (every
  Function node has one — 8,880 of 8,880 on rxjava), so the callee's own file decides, the
  call-site rule never fires for this tool, and the twelve are charged as what they are. The
  rule stays for the rows where it is the only file there is; PROTOCOL §5.1 now states both
  files and which decides what. code-review-graph: +9 / +22 / +14 / +14 exact on maven-core /
  spring-boot / apache-ant / rxjava (rows that were `unplaced` because the call-site file could
  not decide them), +4 on the TypeScript torture.
* Pinned: `tests/test_resolve.py` (inherited member counts as declared, Java and TypeScript;
  the callee's own file decides and the inheritance is then read), `tests/test_adapters.py`
  (both code-review-graph adapters on a synthetic `graph.db`: `callee_file` is the target
  node's file, for a method and for a constructor call).

## Issue #88: the Java AxiomEngine rows never hit the engine's library cache

The engine keys its staged-library cache on the `--library` string, each module's path and its
CSVs' size+mtime. `warm.sh` passed the platform IR root itself; `run.sh` built a per-subject
symlink farm under `.work/java/<subject>/axiom/libroot` and passed that. Same files, two paths,
two keys: the warm-up warmed a key no timed run used, all ten timed Java solves in the
reporter's pass missed (`axiom-nolib` too — its empty farm was per-subject as well), each
re-staged 473 MB into `seconds`, and 22 duplicate `libfacts-*` directories filled the disk
(5.4 GB when this was fixed). `run.sh` now passes the platform root as itself, parses a
subject's stub library once into a content-addressed directory (stub sources + parser commit,
so its mtimes hold between runs) and joins the two with the engine's comma-separated
`--library`; `axiom-nolib` gets the stub or one fixed empty root. Each solve greps its own log
and records a `libcache:<label>` timing part, which `run.py` reports as
`run.tools.<label>.seconds_breakdown.library_cache` beside the warm-up's `cache`, so a time that
includes staging says so (a part, not the row's note: verify.sh's re-run always hits, and the
row must stay byte-identical). Checked: torture (stub + platform) misses
once and hits on the next run; maven-core's `axiom` hits on its first timed run, from the
warm-up's key; exact counts unchanged. The reporter's engine-side suggestion — key the cache on
module contents, not the root path — is the durable fix; raised as axiom-code-graph#588.

**Verified after the #36 reopening** (2026-09-14, same toolchain): 84 unit tests; every subject in
both languages re-scored from the kept edge files with the code-review-graph rows re-adapted;
`verify.sh` VERIFIED on `torture`, `maven-core` (Java) and `torture` (TypeScript).

**Verified after the eighth pass** (2026-09-14, same toolchain, parser and engine `febf8b4`):
`bash bench/test.sh` 81 tests; every row in both languages re-scored from the kept edge files
(`bench/rescore.sh`); `verify.sh` VERIFIED on `torture`, `gson`, `maven-core` (Java) and
`torture`, `ioredis` (TypeScript). The gate's first run caught two faults in this pass before
they were committed: the task sampler shuffled pairs drawn from set-iteration order, so a
fresh process (a different hash seed) drew a different sample and `scores.json` changed over
identical inputs — the pairs are sorted before the seeded shuffle, pinned by a three-process
test; and the `axiom` adapter recorded its source as the path it was given, so a hand run with
a relative `--out` and the runner's absolute one were not byte-identical — the path is spelled
relative to the repository.

**Verified after the sixth pass** (2026-09-13, Darwin arm64, JDK 24.0.1, TypeScript 5.6.3, CodeQL
2.23.8 with `java-all 7.8.2` / `javascript-all 2.6.18`, parser and engine `febf8b4`):
`verify.sh` VERIFIED on `torture`, `maven-core`, `netty-transport`, `spring-boot` (Java) and
`torture`, `ioredis`, `kysely`, `fp-ts`, `type-graphql` (TypeScript); every subject through every
gate, 74 unit tests.

**Verified after the fifth pass** (2026-09-13, Darwin arm64, JDK 24.0.1, TypeScript 5.6.3, parser
`b9e719b`, engine `8ae9a1e`): `verify.sh` reported VERIFIED on `torture`, `maven-core`,
`netty-transport`, `spring-boot` (Java) and on `torture`, `ioredis`, `kysely`, `fp-ts`,
`type-graphql` (TypeScript). Every subject in both languages went through every gate, including
the new gate 3a (`tests/`, 47 checks).

## Pass 9 (#103): every table regenerated on a dedicated VM, library-free headline

The tables had not been regenerated after five adapter and resolver commits (5084fde, 269ac83,
b7e5557, bb580b4, d06b8c2), so the committed scores did not reproduce (#103). Reading the old rows
with the adapters of the committed-scores revision showed that every tool's own output DID
reproduce (code-review-graph, codegraph, gitnexus and graphify, row for row on
typescript/torture). The drift was the harness changing underneath the tables, not the tools.
Every tool is now pinned with everything under it, from a committed lock (#109, #111, #112).

Found while preparing the run, each fixed before it:

- **CodeQL downloaded dependencies** (#117). Buildless Java extraction fetches jars it guesses
  from imports, including rxjava's own published artifact; the same CLI and packs gave 20,717 or
  26,584 rows on rxjava depending on the network. The extractor now runs with no network.
- **A library-enabled row was ranked** (#115, #116). The Java `AxiomEngine` headline row was the run
  given the JDK's platform IR. Every ranked table is now library-free; library runs are shown
  beside, unranked.
- **Members of a `$`-named class** (#113). #110 put gson's `$Gson$Types` in scope and its first
  real run failed gate 4: four "first capital segment" rules read `$Gson$Types` as a package.
- **verify.sh and rescore.sh scored with fewer inputs than subject.sh** (#114): `--anonmap`
  (Java) and `--prior-internal-use` (TypeScript).
- **Task scores depended on set order** before Python 3.12 (#93), and **gitnexus's `seconds`
  included its adapter's export paging** (#98).

**The run** (2026-09-24): benchmark `d08fd2c`, parser and engine `2163292b`, on GCP
c3-standard-22 (Intel Xeon Platinum 8481C, 22 vCPU, 88 GB, Ubuntu 24.04), JDK 24.0.2, Node
25.2.1, Python 3.12, CodeQL 2.23.8, Soufflé 2.5. The 16 committed dev subjects ran one at a
time with every tool, so `seconds` is uncontended. The VM was deleted afterwards.

**Verified:** `verify.sh` VERIFIED on all seven Java subjects and on eight of nine TypeScript
subjects. **excalidraw is NOT VERIFIED**, for one reason: gitnexus 1.6.11 labels one edge
(`App.<init> → App.isInteractionEnabled`) with a different confidence on different clean runs.
In 5 runs it gave 3 distinct outputs, each with the same edge set (#121). Every edge-based score
on excalidraw is unaffected, and every other tool there reproduced byte for byte.

**What moved, and why.** gitnexus rose on netty-transport (70.8 → 76.1%) with identical rows:
before #96 the resolver dropped its 320 javac-style anonymous-class rows (`AbstractChannel$1`)
unread. Of the 135 groups recovered, 115 are exact and 19 wrong. gson's universe grew from 774
to 832 groups (#110, #113). AxiomEngine moved with the engine (2163292b). CodeQL reproduced its
committed numbers exactly once it had no network.

## The pattern

The verifier caught this harness's own pagination bug before it published a false claim about
GitNexus; the ceiling gate caught seven harness faults during the audit; the TypeScript pass found
three more in one afternoon. **Most failures this benchmark has found were in the benchmark.** That
is the expected shape of this work, and it is why every claim in the README points at a gate.
