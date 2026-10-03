# Subject: torture

Eleven families of Java construct in one small project, each file exercising one family, so a score
can say WHICH construct a tool loses rather than only that it lost something.

| | |
|---|---|
| source repo | `ANONYMIZED/axiomengine` |
| commit | `f4fe0b6559f3189ef4596e39fac89db2ed6c7e5f` |
| path | `test/java/torture/{client,lib}` |
| size | 15 files, 592 lines |

`client/` is compiled AGAINST `lib/` rather than together with it, so `dep.*` is genuinely external
and the client -> library hand-off is a real boundary rather than an artefact of throwing both trees
at one javac.

## A conflict of interest, stated

This subject was written by the authors of one of the tools under test. It was chosen because it is
the densest per-construct Java corpus available and because its families make the per-feature
breakdown possible — but a tool's own test corpus cannot be the basis of a claim about that tool.

Two things bound the risk, and neither removes it:

* the subject decides only WHICH CALLS are measured, never what the right answer is — that comes
  from the compiled bytecode, read by a reader no tool participates in;
* Phase 2 scores the same harness against large third-party projects (Spring Boot, Cassandra),
  pinned by commit SHA, which no tool under test had any hand in writing.

Until Phase 2 lands, a result on this subject is a per-construct diagnostic, not a ranking.

| family | what it puts under load |
|---|---|
| `F01` | deep hierarchy, covariant return (bridge), diamond of interface defaults, overload set arity cannot separate |
| `F02` | type-variable substitution through a subclass, recursive bound, generic method, a library generic the client parameterises |
| `F03` | `var` from a constructor, factory, chain, collection element, for-each, ternary, cast, lambda parameter, resource |
| `F04` | listener list, listener field, map of lambdas keyed at runtime, a library bus that dispatches, a client implementation of a library callback |
| `F05` | custom annotations, meta-annotation, repeatable, class-valued argument, annotation-driven entry point nothing calls |
| `F06` | all four method-reference forms, lambda in a field, a local, a map, a list, a call written inside a lambda body |
| `F07` | records and generated accessors, sealed hierarchy, pattern switch, record deconstruction, enum constant bodies |
| `F08` | inner, static nested, local and anonymous classes; unqualified calls resolving outward through two levels |
| `F09` | reflection, `Class.forName`, dynamic proxy, `ServiceLoader` — out of scope by construction, asserted DECLARED unknown rather than silently dropped |
| `F10` | reassignment, ternary, switch expression, cast, array element, twice-written field, parameter, return value |
| `F11` | a second package, to catch a resolver keyed on simple names |
