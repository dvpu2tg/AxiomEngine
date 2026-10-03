# benchmark-test-impact

**Given a fix, which tests should run?** Test-impact analysis on Defects4J, scored for every
graph builder that reads source without a build — AxiomEngine, codegraph, code-review-graph,
GitNexus, Graphify — against what Defects4J observed by running the tests.

This is the second question put to the same call graphs that
[callgraph-benchmark](ANONYMIZED-URL) scores edge by edge
against bytecode. Every tool's output is read here through **that** benchmark's adapters and
resolver (pinned as the submodule `callgraph-benchmark/`): the same translation of each tool's
notation, the same exclusions, the same `Type#name` spellings, the same rule that an ambiguous row
is dropped and counted rather than guessed. Those readers went through eight audit passes and
ninety issues there; this repository does not re-derive them.

## How

* **Subjects.** Bugs of the Defects4J projects hosted on GitHub whose fixed commits exist
  upstream (`registry.json`: Lang, Gson, Jsoup, Csv, Cli, JacksonCore, Codec, Time, Compress).
  A bug's FIXED tree is one shallow fetch of the commit Defects4J records (`bugs.json` pins it);
  no Defects4J install, no Perl, no compilation. `fetch.py` takes the bug's metadata from
  `rjust/defects4j` master: `trigger_tests`, `relevant_tests`, `modified_classes`,
  `patches/*.src.patch`. `per_project` in the registry sets how many bugs per project.
* **The change.** `truth.py` reads the fix's hunks (the Defects4J patch runs fixed → buggy, so
  its `-` lines are the fixed tree's) onto method spans from a source scan (`javascan.py`:
  every type, every method with its line span, annotations and superclass, spelled as
  callgraph-benchmark's oracle spells them — checked against it on that benchmark's torture
  subject). The changed methods are the innermost methods covering a changed line; a changed
  line outside every method (a field initializer) is charged to `<init>` / `<clinit>`; blank
  and comment lines change nothing.
* **The tests.** Every JUnit 3/4/5 test method in the test root, with the concrete class it runs
  in (an abstract test class's tests run in each concrete subclass). A test is impacted when its
  method, or a fixture that runs before it (`setUp`, `@Before*`, the test class's constructor or
  static initializer, own or inherited), transitively calls a changed method in the tool's graph.
* **The reading.** Each tool indexes the module's main and test sources through its
  callgraph-benchmark adapter; `score.py` reads the canonical edge file through
  `bench/resolve.py` against the scanned universe. AxiomEngine is run both with the platform IR
  (`AxiomEngine`) and without (`AxiomEngine-nolib`), as there.
* **The node key.** The closure runs over `Type#name/arity`, not `Type#name`: a tool that
  reports a parameter list names ONE overload and is read as naming it, and a tool that reports
  none names the method by name and is read as every overload of it (`Jsoup#parse(String)` and
  `Jsoup#parse(File, String)` are two nodes; on `Type#name` they were one, and 251 Jsoup-20
  tests reached `DataUtil#parseByteData` through an overload none of them calls). The
  consequence is that the key binds only the tools that report parameters — on a typical bug
  100% of AxiomEngine's rows and 84% of codegraph's carry one, and 0% of the other three's — so
  every row is also scored under the plain `Type#name`, with the parameter lists dropped from
  every tool alike, and both are printed (`overload_blind` in `scores.json`, the **Both node
  keys** table in the results). A ranking that depends on which key is used is a fact about the
  reading, and belongs in a column rather than in a scorer's docstring.
* **The score.** `trigger recall` — of the tests Defects4J found failing on the buggy version
  and passing on the fixed one (they certainly execute the change), the share the answer
  contains; `safe` — bugs where it contained all of them; `precision` — impacted tests whose
  class Defects4J saw load a modified class (a test in no such class cannot reach the change: a
  false positive at class granularity whatever the graph says); `selection` — share of the
  suite selected. Ranked by recall, then selection. Three reference rows: `d4j-relevant` (every
  test in a relevant class — the dynamic class-level answer), `name-match` (tests in classes
  named after a modified class — the grep answer), `all-tests`.

```
git submodule update --init          # the readers and adapters (install the tools there:
                                     #   callgraph-benchmark/java/adapters/*/install.sh)
python3 runall.py -j 2               # every bug in bugs.json not yet scored, 2 at a time; then the tables
python3 runall.py --score-only       # re-score from the kept edge files (a scorer change)
bash run.sh Lang-1                   # one bug: fetch, truth, tools, score
python3 -m pytest tests              # the walk's properties, and the tables against results/
python3 validate.py                  # the checks below; VALIDATED or the failures
python3 relations.py                 # does each adapter read every call-carrying relation its tool emits?
python3 audit.py -n 10               # a human check: sampled credited chains with each call site's source line, and misses
python3 tables.py --write            # RESULTS.md + the block below
```

## Validation

A number here is not cited until `validate.py` says VALIDATED over every scored bug. Per bug it
checks that the fix mapped to at least one method and that every triggering test exists in the
scanned universe (else the miss would be charged to every tool); that Defects4J's own
class-level answer contains the triggering tests (flagged when it does not — no static
class-level answer can beat the observation there); that **every triggering test a tool is
credited with has a recorded chain** from the test (or a fixture of its class) to a changed
method whose every step is a resolved edge of that tool's own edge file — the chains are in
`results/<bug>/scores.json` under `trigger_paths`, so a credit can be checked against the
source; the share of each tool's rows the resolver could read (a tool scored on half of what it
said is printed as such); that re-scoring from the kept edge files reproduces `scores.json` byte
for byte; that the scorer finds nothing on an empty graph, everything on direct edges, and a
class's tests on a fixture edge; and, where `v1/` scored the same bug, whether v1's AxiomEngine
trigger verdict agrees — disagreements are listed, not hidden (v1 read the buggy checkout and
mapped the change differently).

`relations.py` checks the step BEFORE the edge file exists. `validate.py` and `fairness.py` both
begin there, so neither can see an adapter dropping a call-carrying relation of the tool's own
store: the edge file is still internally consistent, still resolves at a normal rate, still
re-scores byte for byte, and `fairness.py` then charges every resulting miss to `not in graph`
because the edges were never in the file it re-reads. So `relations.py` reads the kept native
stores (`.work/<bug>/native/<tool>.tgz`, and the same archives a release ships) and holds every
relation an adapter leaves to a declared verdict — `declaration`, `heritage`, `file`, `annotation`,
`mention`, `type_mention` or `pending` — each falsifiable against what the store itself records: a
`mention` joining two callables is a call, a `type_mention` is a name that denotes a TYPE and must
prove it row by row (codegraph resolves one onto the type's constructor node, so both ends read as
methods though nothing is called), a `pending` one is owed, and a relation in neither set fails, so
a tool release cannot add calls unnoticed. The contract is a table in `relations.py` rather than an
inference from adapter code — so it can drift, and it did: `codegraph` was declared to read
`{"calls"}` while 9.2% of its released rows are `instantiates`. Where an adapter tags a row with
the relation it came from, the declaration is now checked against the edge file the run wrote.

`audit.py` is the human half: it samples credited (bug, tool, triggering test) chains and prints
every step with the call site the tool reported and that line of source — `p = doPeek();`,
`return tag.getName();` — and, for misses, where the tool's graph stops. A chain whose steps
are not calls in the source is a scoring mistake whatever the validator says; none has been
found so far.

`tests/` is the half that needs nothing fetched: how a resolved reference becomes node(s) of the
walk (a parameter list names one overload, none names every overload), the walk's properties (an
empty graph finds no test, a fixture edge finds the class's tests, an override continues from the
declaration it overrides and only at its own arity, an enum constant folds onto its enum), and the
guard that refuses a `truth.json` written by another generation of `truth.py`, and a check that
the committed `RESULTS.md` and README block are the ones `results/` renders now — the figures that
get cited are the ones most easily left behind, and nothing else regenerates them. That last one is
silent without it — foreign keys parse and compare and are simply never equal to a node, so the
fixture branch goes dead and every tool's number comes out lower with no error.

`results/<bug>/scores.json` holds each bug's rows with the impacted tests listed, so a miss can
be looked at; `.work/` (trees, edge files, logs) is not committed. `CALLGRAPH_BENCHMARK=<path>`
points at a checkout other than the submodule; `AXIOM_ENGINE` / `AXIOM_JDK_IR` at the engine
and platform IR, as in callgraph-benchmark.

## What this does not measure

Overriding through a dispatch edge the tool did not draw, reflection, and tests that reach the
change through a suite or a rule are misses for every static graph alike; `d4j-relevant` shows
where Defects4J's own class-level observation reaches a triggering test no static graph does.
Precision is class-level: a test in a relevant class that never calls the changed method still
counts as precise. Method spans are read from source by a scanner, not a compiler; the changed
methods are printed per bug so that reading can be checked.

## v1

`v1/` is the first version of this benchmark: a full Defects4J install (Perl, JDK 11), the
BUGGY checkout, 318 bugs over 17 projects, AxiomEngine read straight from its `graph.sqlite`
(with `dispatch_candidates`), Graphify through its own `affected` traversal, and a STARTS-style
class-level static baseline, scored at test-CLASS granularity. Its scripts and per-bug results
(`v1/work/*/result.json`) are kept as they were; its README is `v1/README.md`. The pipeline at
the root replaces it because it reads every tool the same validated way, at test-method
granularity, and needs nothing installed but the tools.

## Results

<!-- tia:begin -->
**By project** — `safe / n · selection`: bugs where every triggering test was selected, and the mean share of the suite selected.

| project | n | AxiomEngine safe · sel | code-review-graph safe · sel | code-review-graph-dispatch safe · sel | codegraph safe · sel | codegraph-dispatch safe · sel | gitnexus safe · sel | graphify safe · sel | *d4j-relevant* safe · sel | *name-match* safe · sel |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Cli | 39 | 39/39 · 50% | 22/39 · 12% | 22/39 · 12% | 18/39 · 18% | 21/39 · 33% | 37/39 · 49% | 29/39 · 46% | 39/39 · 57% | 13/39 · 10% |
| Closure | 174 | 163/174 · 79% | 24/174 · 11% | 36/174 · 19% | 37/174 · 22% | 39/174 · 24% | 61/174 · 36% | 29/174 · 7% | 174/174 · 49% | 79/174 · 2% |
| Codec | 18 | 17/18 · 17% | 7/18 · 6% | 7/18 · 6% | 10/18 · 8% | 10/18 · 8% | 14/18 · 14% | 10/18 · 9% | 18/18 · 21% | 16/18 · 12% |
| Collections | 28 | 23/28 · 45% | 6/28 · 1% | 6/28 · 3% | 19/28 · 14% | 19/28 · 14% | 17/28 · 15% | 17/28 · 4% | 28/28 · 1% | 26/28 · 1% |
| Compress | 47 | 46/47 · 29% | 20/47 · 9% | 20/47 · 10% | 35/47 · 14% | 35/47 · 16% | 44/47 · 22% | 37/47 · 15% | 47/47 · 34% | 29/47 · 2% |
| Csv | 16 | 16/16 · 37% | 9/16 · 24% | 9/16 · 24% | 12/16 · 34% | 12/16 · 34% | 14/16 · 32% | 9/16 · 23% | 16/16 · 76% | 10/16 · 20% |
| Gson | 18 | 18/18 · 66% | 0/18 · 0% | 2/18 · 1% | 9/18 · 9% | 9/18 · 9% | 8/18 · 9% | 11/18 · 22% | 18/18 · 69% | 8/18 · 5% |
| JacksonCore | 26 | 26/26 · 45% | 6/26 · 0% | 6/26 · 0% | 24/26 · 42% | 24/26 · 42% | 22/26 · 34% | 23/26 · 36% | 26/26 · 66% | 6/26 · 0% |
| JacksonDatabind | 110 | 107/110 · 84% | 4/110 · 0% | 4/110 · 1% | 60/110 · 39% | 61/110 · 39% | 29/110 · 14% | 62/110 · 35% | 110/110 · 81% | 5/110 · 0% |
| JacksonXml | 6 | 3/6 · 26% | 2/6 · 14% | 2/6 · 14% | 2/6 · 13% | 2/6 · 13% | 2/6 · 16% | 1/6 · 2% | 6/6 · 81% | 0/6 · 0% |
| Jsoup | 93 | 93/93 · 68% | 17/93 · 3% | 17/93 · 5% | 52/93 · 31% | 52/93 · 31% | 71/93 · 58% | 40/93 · 25% | 93/93 · 71% | 43/93 · 6% |
| JxPath | 22 | 21/22 · 88% | 0/22 · 0% | 0/22 · 7% | 12/22 · 49% | 19/22 · 69% | 21/22 · 86% | 16/22 · 59% | 22/22 · 79% | 1/22 · 0% |
| Lang | 61 | 61/61 · 1% | 38/61 · 1% | 40/61 · 1% | 41/61 · 0% | 41/61 · 0% | 51/61 · 1% | 53/61 · 1% | 61/61 · 10% | 54/61 · 3% |
| Math | 106 | 105/106 · 9% | 13/106 · 1% | 13/106 · 1% | 79/106 · 4% | 82/106 · 5% | 95/106 · 7% | 51/106 · 3% | 106/106 · 8% | 68/106 · 1% |
| Mockito | 38 | 19/38 · 31% | 7/38 · 11% | 7/38 · 11% | 9/38 · 9% | 9/38 · 10% | 10/38 · 20% | 10/38 · 14% | 38/38 · 57% | 9/38 · 1% |
| Time | 26 | 25/26 · 41% | 12/26 · 9% | 14/26 · 12% | 16/26 · 17% | 16/26 · 22% | 23/26 · 36% | 13/26 · 18% | 26/26 · 65% | 19/26 · 3% |
| combined | 828 | 782/828 · 51% | 187/828 · 6% | 205/828 · 8% | 435/828 · 21% | 451/828 · 23% | 519/828 · 27% | 411/828 · 18% | 828/828 · 48% | 386/828 · 3% |

### Held-out

The bugs no rule was written against (the registry's `heldout`: the active bugs following the DEV ones, by id), scored once with the rules frozen. **These are the numbers to cite.**

**748 Defects4J bugs** (Cli, Closure, Codec, Collections, Compress, Csv, Gson, JacksonCore, JacksonDatabind, JacksonXml, Jsoup, JxPath, Lang, Math, Mockito, Time). For each bug-fixing commit, every tool's call graph was asked *which tests does this change reach?* Two things make an answer good: it must contain the test that actually catches the bug (Defects4J knows which — it fails before the fix and passes after), and it should be no bigger than it has to be. Defects4J also recorded, by running the suite, which test classes really load the changed code — the `d4j-relevant` row — so a selection can be compared with what really ran. The last column, `read`, is how much of each tool's own output the reading could use: an unresolvable row is dropped and counted rather than guessed at, so a low figure means the row beside it was computed from a fraction of what that tool actually emitted.

| tool | caught the bug's test?<br><sub>bugs where every triggering test was selected</sub> | tests selected<br><sub>share of the suite, mean</sub> | selection vs. what really ran<br><sub>against Defects4J's dynamic answer, median</sub> | covered what really ran?<br><sub>relevant classes with a test selected</sub> | read<br><sub>share of the tool's own rows the reading could use</sub> | in one line |
|---|---:|---:|---:|---:|---:|---|
| 1. **`AxiomEngine`** | 710 / 748 | 52.2% | 0.98× | 80.5% | 90.6% | skips the test that catches the bug on 38 of 748 bugs — not safe, whatever it saves |
| 2. `gitnexus` | 460 / 748 | 27.4% | 0.56× | 54.2% | 87.3% | skips the test that catches the bug on 288 of 748 bugs — not safe, whatever it saves |
| 3. `codegraph-dispatch` | 405 / 748 | 23.1% | 0.35× | 49.0% | 87.3% | skips the test that catches the bug on 343 of 748 bugs — not safe, whatever it saves |
| 4. `codegraph` | 391 / 748 | 21.2% | 0.25× | 45.5% | 88.1% | skips the test that catches the bug on 357 of 748 bugs — not safe, whatever it saves |
| 5. `graphify` | 364 / 748 | 17.0% | 0.11× | 38.7% | 87.7% | skips the test that catches the bug on 384 of 748 bugs — not safe, whatever it saves |
| 6. `code-review-graph-dispatch` | 181 / 748 | 7.8% | 0.01× | 19.5% | 47.5% | skips the test that catches the bug on 567 of 748 bugs — not safe, whatever it saves |
| 7. `code-review-graph` | 164 / 748 | 5.4% | 0.00× | 15.6% | 44.3% | skips the test that catches the bug on 584 of 748 bugs — not safe, whatever it saves |
| *`d4j-relevant`* | 748 / 748 | 47.6% | 1.00× | 99.7% | — | what Defects4J observed by running the tests — the answer to match |
| *`name-match`* | 350 / 748 | 2.8% | 0.03× | 18.0% | — | grep for the class name: small, and wrong on a third of the bugs |
| *`all-tests`* | 748 / 748 | 100.0% | 2.07× | 99.7% | — | run everything: always safe, never minimal |

**Both node keys.** `Type#name/arity` is what `score.py` uses: a tool reporting a parameter list names one overload, a tool reporting none is read as every overload of the name. `Type#name` is the same rows with the parameter lists dropped from every tool alike. Only a tool that reports parameters can move between the two, and `params` is the share of its rows that carry one.

| tool | bugs | params | safe<br><sub>`Type#name/arity`</sub> | safe<br><sub>`Type#name`</sub> | selection<br><sub>`Type#name/arity`</sub> | selection<br><sub>`Type#name`</sub> |
|---|---:|---:|---:|---:|---:|---:|
| **`AxiomEngine`** | 748 | 100.0% | 94.9% | 95.2% (+2) | 52.2% | 53.7% |
| `gitnexus` | 748 | 7.9% | 61.5% | 67.0% (+41) | 27.4% | 32.7% |
| `codegraph-dispatch` | 748 | 94.0% | 54.1% | 69.0% (+111) | 23.1% | 33.7% |
| `codegraph` | 748 | 92.5% | 52.3% | 68.7% (+123) | 21.2% | 33.0% |
| `graphify` | 748 | 0.0% | 48.7% | 48.7% | 17.0% | 17.0% |
| `code-review-graph-dispatch` | 748 | 0.0% | 24.2% | 24.2% | 7.8% | 7.8% |
| `code-review-graph` | 748 | 0.0% | 21.9% | 21.9% | 5.4% | 5.4% |

<details><summary>every column</summary>

**Test impact on 748 Defects4J bugs** (Cli, Closure, Codec, Collections, Compress, Csv, Gson, JacksonCore, JacksonDatabind, JacksonXml, Jsoup, JxPath, Lang, Math, Mockito, Time): for each fix, the tests a tool's call graph says the change reaches, against the tests Defects4J observed. `trigger recall` — the triggering tests (fail on buggy, pass on fixed) the answer contains; `safe` — bugs where it contained all of them; `precision` — impacted tests whose class Defects4J saw load a modified class; `relevant recall` — of the tests in those classes, the share selected (an answer that finds the one triggering test but a third of the relevant tests is not safe in general); `selection` — share of the suite selected; FP / FN — impacted tests outside the relevant classes / relevant tests not impacted, per bug; `read` — of the rows the tool emitted, the share the resolver could use (a row whose caller or callee is ambiguous, unknown or owner-less is dropped and counted, never guessed), pooled over the tool's bugs: a tool scored on a fraction of what it said is read here rather than only in validate.py. Ranked by trigger recall, then relevant recall, then selection. Reference rows: the dynamic class-level answer, the grep answer, the whole suite. Every tool is read the same way — its `calls` edges through callgraph-benchmark's resolver, plus the dispatch step — not through its own impact command (v1 drove Graphify through its own `affected` traversal, whose name-seeding failed on most Lang bugs; here Graphify is credited for the edges it emitted).

| | | | RIGHT | | | | READ | MINIMAL | | | | | |
| rank | tool | bugs | safe<br><sub>every triggering test found</sub> | trigger recall<br><sub>mean</sub> | relevant recall<br><sub>of the tests in relevant classes</sub> | relevant classes covered<br><sub>≥1 test impacted (v1's definition)</sub> | read<br><sub>rows the resolver could use</sub> | selection<br><sub>share of suite</sub> | selection when safe<br><sub>share of suite, safe bugs only</sub> | vs dynamic answer<br><sub>impacted / relevant tests, median</sub> | precision<br><sub>vs relevant classes</sub> | FP / bug | FN / bug |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **`AxiomEngine`** | 748 | 94.9% | 95.5% | 71.2% | 80.5% | 90.6% | 52.2% | 54.5% | 0.98× | 73.7% | 724.3 | 196.9 |
| 2 | `gitnexus` | 748 | 61.5% | 64.5% | 42.4% | 54.2% | 87.3% | 27.4% | 32.6% | 0.56× | 75.3% | 329.0 | 758.9 |
| 3 | `codegraph-dispatch` | 748 | 54.1% | 58.0% | 34.3% | 49.0% | 87.3% | 23.1% | 32.6% | 0.35× | 75.7% | 231.2 | 866.6 |
| 4 | `codegraph` | 748 | 52.3% | 55.9% | 31.7% | 45.5% | 88.1% | 21.2% | 31.3% | 0.25× | 76.3% | 206.4 | 884.1 |
| 5 | `graphify` | 748 | 48.7% | 51.4% | 27.6% | 38.7% | 87.7% | 17.0% | 28.8% | 0.11× | 81.7% | 67.9 | 994.3 |
| 6 | `code-review-graph-dispatch` | 748 | 24.2% | 26.1% | 14.0% | 19.5% | 47.5% | 7.8% | 15.6% | 0.01× | 81.3% | 124.5 | 983.2 |
| 7 | `code-review-graph` | 748 | 21.9% | 23.7% | 10.5% | 15.6% | 44.3% | 5.4% | 13.8% | 0.00× | 85.2% | 58.1 | 1059.1 |
| — | *`d4j-relevant`* | 748 | 100.0% | 100.0% | 100.0% | 99.7% | — | 47.6% | 47.6% | 1.00× | 100.0% | 0.0 | 0.0 |
| — | *`name-match`* | 748 | 46.8% | 50.9% | 19.5% | 18.0% | — | 2.8% | 4.0% | 0.03× | 97.0% | 1.4 | 1157.4 |
| — | *`all-tests`* | 748 | 100.0% | 100.0% | 100.0% | 99.7% | — | 100.0% | 100.0% | 2.07× | 47.6% | 1613.5 | 0.0 |

</details>

Per bug: `triggering tests found / total · impacted tests`. A bug whose triggering test the dynamic class-level answer itself misses (`d4j-relevant` < total) is one where the test is declared outside the classes that load the modified class — inherited, or run through a suite — and is reported as such.

| bug | changed | trigger | tests | `AxiomEngine` | `code-review-graph` | `code-review-graph-dispatch` | `codegraph` | `codegraph-dispatch` | `gitnexus` | `graphify` | *`d4j-relevant`* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Cli-10 | 1 | 1 | 113 | 1/1 · 86 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 23 | 1/1 · 86 | 0/1 · 80 | 1/1 · 90 |
| Cli-11 | 1 | 1 | 120 | 1/1 · 11 | 1/1 · 11 | 1/1 · 11 | 1/1 · 6 | 1/1 · 6 | 1/1 · 11 | 1/1 · 11 | 1/1 · 25 |
| Cli-12 | 1 | 3 | 133 | 3/3 · 92 | 0/3 · 0 | 0/3 · 0 | 0/3 · 0 | 0/3 · 23 | 3/3 · 92 | 3/3 · 84 | 3/3 · 36 |
| Cli-13 | 3 | 1 | 479 | 1/1 · 76 | 1/1 · 53 | 1/1 · 53 | 1/1 · 98 | 1/1 · 98 | 1/1 · 81 | 0/1 · 18 | 1/1 · 427 |
| Cli-14 | 1 | 1 | 481 | 1/1 · 70 | 1/1 · 55 | 1/1 · 55 | 1/1 · 79 | 1/1 · 79 | 1/1 · 66 | 0/1 · 2 | 1/1 · 288 |
| Cli-15 | 1 | 2 | 484 | 2/2 · 150 | 2/2 · 58 | 2/2 · 58 | 0/2 · 5 | 2/2 · 149 | 2/2 · 34 | 2/2 · 61 | 2/2 · 361 |
| Cli-16 | 18 | 7 | 489 | 7/7 · 419 | 7/7 · 63 | 7/7 · 63 | 7/7 · 463 | 7/7 · 463 | 7/7 · 416 | 6/7 · 453 | 7/7 · 451 |
| Cli-17 | 1 | 1 | 145 | 1/1 · 103 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 23 | 1/1 · 103 | 1/1 · 95 | 1/1 · 98 |
| Cli-18 | 2 | 1 | 146 | 1/1 · 104 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 23 | 1/1 · 104 | 1/1 · 96 | 1/1 · 99 |
| Cli-19 | 1 | 1 | 147 | 1/1 · 105 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 23 | 1/1 · 105 | 1/1 · 97 | 1/1 · 100 |
| Cli-20 | 1 | 1 | 148 | 1/1 · 106 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 23 | 1/1 · 106 | 1/1 · 98 | 1/1 · 101 |
| Cli-21 | 25 | 1 | 506 | 1/1 · 283 | 1/1 · 70 | 1/1 · 70 | 1/1 · 482 | 1/1 · 482 | 1/1 · 283 | 1/1 · 458 | 1/1 · 435 |
| Cli-22 | 8 | 2 | 181 | 2/2 · 139 | 0/2 · 0 | 0/2 · 0 | 2/2 · 118 | 2/2 · 133 | 2/2 · 139 | 2/2 · 135 | 2/2 · 112 |
| Cli-23 | 1 | 2 | 184 | 2/2 · 18 | 2/2 · 18 | 2/2 · 18 | 0/2 · 2 | 0/2 · 2 | 2/2 · 17 | 1/2 · 17 | 2/2 · 35 |
| Cli-24 | 1 | 1 | 186 | 1/1 · 20 | 1/1 · 20 | 1/1 · 20 | 0/1 · 2 | 0/1 · 2 | 1/1 · 19 | 1/1 · 19 | 1/1 · 37 |
| Cli-25 | 1 | 1 | 186 | 1/1 · 20 | 1/1 · 20 | 1/1 · 20 | 0/1 · 2 | 0/1 · 2 | 1/1 · 19 | 1/1 · 19 | 1/1 · 37 |
| Cli-26 | 1 | 1 | 187 | 1/1 · 77 | 1/1 · 77 | 1/1 · 77 | 1/1 · 42 | 1/1 · 42 | 1/1 · 68 | 1/1 · 17 | 1/1 · 147 |
| Cli-27 | 1 | 3 | 247 | 3/3 · 158 | 0/3 · 0 | 0/3 · 0 | 0/3 · 0 | 3/3 · 106 | 3/3 · 158 | 3/3 · 153 | 3/3 · 180 |
| Cli-28 | 1 | 1 | 327 | 1/1 · 220 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 168 | 1/1 · 220 | 1/1 · 215 | 1/1 · 236 |
| Cli-29 | 1 | 1 | 339 | 1/1 · 233 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 169 | 1/1 · 233 | 1/1 · 212 | 1/1 · 301 |
| Cli-30 | 2 | 9 | 353 | 9/9 · 245 | 0/9 · 0 | 0/9 · 0 | 0/9 · 0 | 0/9 · 158 | 9/9 · 245 | 1/9 · 212 | 9/9 · 313 |
| Cli-31 | 43 | 1 | 354 | 1/1 · 348 | 1/1 · 260 | 1/1 · 260 | 1/1 · 256 | 1/1 · 276 | 1/1 · 348 | 1/1 · 289 | 1/1 · 352 |
| Cli-32 | 1 | 2 | 359 | 2/2 · 29 | 2/2 · 29 | 2/2 · 29 | 1/2 · 2 | 1/2 · 2 | 2/2 · 28 | 1/2 · 22 | 2/2 · 46 |
| Cli-33 | 2 | 1 | 360 | 1/1 · 22 | 1/1 · 22 | 1/1 · 22 | 0/1 · 0 | 0/1 · 0 | 1/1 · 21 | 1/1 · 21 | 1/1 · 47 |
| Cli-34 | 42 | 2 | 361 | 2/2 · 350 | 2/2 · 262 | 2/2 · 262 | 2/2 · 257 | 2/2 · 277 | 2/2 · 350 | 2/2 · 291 | 2/2 · 359 |
| Cli-35 | 1 | 1 | 424 | 1/1 · 307 | 0/1 · 0 | 0/1 · 0 | 0/1 · 1 | 0/1 · 210 | 1/1 · 307 | 0/1 · 265 | 1/1 · 404 |
| Cli-36 | 25 | 1 | 368 | 1/1 · 338 | 1/1 · 51 | 1/1 · 51 | 1/1 · 338 | 1/1 · 338 | 1/1 · 338 | 1/1 · 338 | 1/1 · 348 |
| Cli-37 | 1 | 1 | 370 | 1/1 · 191 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 158 | 1/1 · 218 | 1/1 · 188 | 1/1 · 65 |
| Cli-38 | 1 | 1 | 371 | 1/1 · 192 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 158 | 1/1 · 219 | 1/1 · 189 | 1/1 · 66 |
| Cli-39 | 2 | 2 | 390 | 2/2 · 12 | 2/2 · 12 | 2/2 · 12 | 2/2 · 12 | 2/2 · 12 | 0/2 · 0 | 2/2 · 12 | 2/2 · 18 |
| Cli-40 | 1 | 1 | 409 | 1/1 · 29 | 1/1 · 29 | 1/1 · 29 | 1/1 · 29 | 1/1 · 29 | 0/1 · 0 | 1/1 · 29 | 1/1 · 35 |
| Cli-7 | 7 | 1 | 477 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 |
| Cli-8 | 1 | 1 | 110 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 | 1/1 · 2 | 1/1 · 2 | 1/1 · 9 | 1/1 · 9 | 1/1 · 21 |
| Cli-9 | 1 | 2 | 111 | 2/2 · 85 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 1/2 · 22 | 2/2 · 85 | 1/2 · 80 | 2/2 · 89 |
| Closure-10 | 1 | 1 | 7657 | 1/1 · 7285 | 0/1 · 1 | 0/1 · 2398 | 0/1 · 0 | 0/1 · 0 | 0/1 · 3891 | 0/1 · 0 | 1/1 · 6513 |
| Closure-100 | 2 | 9 | 5657 | 0/9 · 0 | 0/9 · 0 | 0/9 · 0 | 0/9 · 0 | 4/9 · 3769 | 0/9 · 1784 | 0/9 · 0 | 9/9 · 71 |
| Closure-101 | 1 | 1 | 4552 | 1/1 · 21 | 0/1 · 0 | 0/1 · 0 | 1/1 · 846 | 1/1 · 846 | 0/1 · 0 | 1/1 · 21 | 1/1 · 21 |
| Closure-102 | 1 | 1 | 4520 | 1/1 · 2355 | 0/1 · 0 | 0/1 · 0 | 0/1 · 1 | 0/1 · 1 | 0/1 · 1112 | 0/1 · 462 | 1/1 · 778 |
| Closure-103 | 2 | 3 | 4517 | 3/3 · 3570 | 0/3 · 0 | 1/3 · 863 | 2/3 · 2809 | 2/3 · 2809 | 2/3 · 1111 | 0/3 · 0 | 3/3 · 1488 |
| Closure-104 | 1 | 1 | 4513 | 1/1 · 3661 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1198 | 0/1 · 0 | 1/1 · 4375 |
| Closure-105 | 1 | 1 | 4485 | 1/1 · 3543 | 0/1 · 861 | 0/1 · 861 | 1/1 · 2798 | 1/1 · 2798 | 0/1 · 1106 | 0/1 · 0 | 1/1 · 106 |
| Closure-106 | 2 | 4 | 2596 | 4/4 · 2550 | 0/4 · 0 | 0/4 · 0 | 0/4 · 0 | 0/4 · 0 | 0/4 · 600 | 0/4 · 0 | 4/4 · 1209 |
| Closure-107 | 1 | 1 | 8447 | 1/1 · 114 | 1/1 · 114 | 1/1 · 114 | 0/1 · 2 | 0/1 · 2 | 1/1 · 40 | 0/1 · 0 | 1/1 · 115 |
| Closure-108 | 19 | 1 | 8446 | 1/1 · 8017 | 0/1 · 0 | 0/1 · 2536 | 0/1 · 856 | 0/1 · 880 | 0/1 · 4239 | 0/1 · 935 | 1/1 · 452 |
| Closure-109 | 1 | 2 | 8419 | 2/2 · 7991 | 0/2 · 6 | 0/2 · 6 | 0/2 · 37 | 0/2 · 37 | 2/2 · 4224 | 2/2 · 440 | 2/2 · 6115 |
| Closure-11 | 1 | 2 | 7651 | 2/2 · 7280 | 2/2 · 2079 | 2/2 · 2340 | 0/2 · 807 | 0/2 · 817 | 2/2 · 3890 | 0/2 · 0 | 2/2 · 6583 |
| Closure-110 | 2 | 2 | 8363 | 2/2 · 8050 | 0/2 · 3407 | 0/2 · 3552 | 0/2 · 3710 | 0/2 · 3768 | 0/2 · 4430 | 0/2 · 932 | 2/2 · 8109 |
| Closure-111 | 1 | 1 | 8361 | 1/1 · 8048 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4430 | 0/1 · 0 | 1/1 · 2498 |
| Closure-112 | 1 | 2 | 8328 | 2/2 · 7935 | 0/2 · 0 | 2/2 · 2505 | 0/2 · 0 | 0/2 · 0 | 2/2 · 4191 | 0/2 · 0 | 2/2 · 3222 |
| Closure-113 | 1 | 1 | 8325 | 1/1 · 7932 | 0/1 · 0 | 0/1 · 2502 | 0/1 · 851 | 0/1 · 875 | 0/1 · 4188 | 0/1 · 0 | 1/1 · 2642 |
| Closure-114 | 1 | 1 | 8324 | 1/1 · 7931 | 0/1 · 0 | 0/1 · 2502 | 0/1 · 851 | 0/1 · 875 | 0/1 · 4188 | 0/1 · 0 | 1/1 · 638 |
| Closure-115 | 1 | 5 | 8316 | 5/5 · 7923 | 0/5 · 0 | 0/5 · 2497 | 0/5 · 851 | 0/5 · 875 | 0/5 · 4182 | 0/5 · 0 | 5/5 · 690 |
| Closure-116 | 1 | 8 | 8319 | 8/8 · 7926 | 0/8 · 0 | 0/8 · 2497 | 2/8 · 853 | 2/8 · 877 | 2/8 · 4184 | 0/8 · 0 | 8/8 · 693 |
| Closure-117 | 1 | 1 | 8305 | 1/1 · 7912 | 0/1 · 0 | 1/1 · 2501 | 0/1 · 853 | 0/1 · 877 | 1/1 · 4177 | 0/1 · 0 | 1/1 · 7146 |
| Closure-118 | 1 | 2 | 8298 | 2/2 · 7905 | 0/2 · 0 | 2/2 · 2495 | 0/2 · 857 | 0/2 · 881 | 2/2 · 4175 | 0/2 · 0 | 2/2 · 7139 |
| Closure-119 | 1 | 1 | 8296 | 1/1 · 7903 | 0/1 · 0 | 0/1 · 2493 | 0/1 · 857 | 0/1 · 881 | 0/1 · 4173 | 0/1 · 683 | 1/1 · 912 |
| Closure-12 | 1 | 1 | 7618 | 1/1 · 7247 | 0/1 · 0 | 0/1 · 2320 | 0/1 · 0 | 0/1 · 0 | 1/1 · 3865 | 0/1 · 0 | 1/1 · 351 |
| Closure-120 | 1 | 1 | 8286 | 1/1 · 7902 | 0/1 · 0 | 0/1 · 2487 | 0/1 · 856 | 0/1 · 880 | 0/1 · 4175 | 0/1 · 934 | 1/1 · 7131 |
| Closure-121 | 1 | 1 | 8286 | 1/1 · 7902 | 0/1 · 0 | 0/1 · 2487 | 0/1 · 856 | 0/1 · 880 | 0/1 · 4175 | 0/1 · 934 | 1/1 · 461 |
| Closure-122 | 1 | 3 | 8273 | 3/3 · 7889 | 0/3 · 54 | 0/3 · 54 | 0/3 · 0 | 0/3 · 0 | 3/3 · 4171 | 0/3 · 0 | 3/3 · 7199 |
| Closure-123 | 1 | 1 | 8268 | 1/1 · 7889 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4174 | 0/1 · 0 | 1/1 · 4489 |
| Closure-124 | 1 | 1 | 8232 | 1/1 · 7850 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 4143 | 0/1 · 0 | 1/1 · 316 |
| Closure-125 | 1 | 1 | 8198 | 1/1 · 7816 | 0/1 · 0 | 1/1 · 2475 | 0/1 · 852 | 0/1 · 877 | 1/1 · 4137 | 0/1 · 0 | 1/1 · 7058 |
| Closure-126 | 1 | 2 | 8018 | 2/2 · 7636 | 0/2 · 0 | 0/2 · 2449 | 0/2 · 843 | 0/2 · 868 | 0/2 · 4086 | 0/2 · 0 | 2/2 · 318 |
| Closure-127 | 2 | 6 | 8016 | 6/6 · 7634 | 0/6 · 0 | 0/6 · 2449 | 0/6 · 843 | 0/6 · 868 | 0/6 · 4086 | 0/6 · 0 | 6/6 · 336 |
| Closure-128 | 1 | 1 | 8000 | 1/1 · 7622 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4089 | 0/1 · 0 | 1/1 · 4280 |
| Closure-129 | 1 | 1 | 7999 | 1/1 · 7617 | 0/1 · 0 | 0/1 · 2445 | 0/1 · 842 | 0/1 · 868 | 1/1 · 4080 | 0/1 · 0 | 1/1 · 6779 |
| Closure-13 | 1 | 1 | 7611 | 1/1 · 7240 | 0/1 · 0 | 0/1 · 0 | 0/1 · 805 | 0/1 · 815 | 1/1 · 3858 | 0/1 · 668 | 1/1 · 608 |
| Closure-130 | 1 | 1 | 7971 | 1/1 · 7589 | 0/1 · 0 | 0/1 · 0 | 0/1 · 61 | 0/1 · 867 | 0/1 · 4071 | 0/1 · 673 | 1/1 · 577 |
| Closure-131 | 1 | 2 | 7970 | 2/2 · 7593 | 0/2 · 2226 | 0/2 · 2445 | 0/2 · 842 | 0/2 · 868 | 0/2 · 4079 | 0/2 · 0 | 2/2 · 2987 |
| Closure-132 | 1 | 1 | 7970 | 1/1 · 7588 | 0/1 · 0 | 0/1 · 0 | 0/1 · 841 | 0/1 · 867 | 0/1 · 4071 | 0/1 · 0 | 1/1 · 396 |
| Closure-133 | 1 | 1 | 7964 | 1/1 · 7584 | 0/1 · 0 | 0/1 · 0 | 0/1 · 30 | 0/1 · 30 | 1/1 · 4069 | 1/1 · 403 | 1/1 · 5506 |
| Closure-134 | 8 | 2 | 4433 | 2/2 · 3507 | 1/2 · 844 | 1/2 · 844 | 1/2 · 2771 | 1/2 · 2771 | 0/2 · 1102 | 0/2 · 542 | 2/2 · 1200 |
| Closure-135 | 49 | 2 | 4472 | 2/2 · 4301 | 1/2 · 1690 | 1/2 · 1690 | 1/2 · 2792 | 1/2 · 2792 | 1/2 · 2275 | 1/2 · 2111 | 2/2 · 4316 |
| Closure-136 | 2 | 4 | 4533 | 4/4 · 3586 | 0/4 · 865 | 0/4 · 865 | 1/4 · 2816 | 1/4 · 2816 | 0/4 · 1114 | 0/4 · 0 | 4/4 · 101 |
| Closure-137 | 25 | 5 | 4539 | 5/5 · 3592 | 0/5 · 865 | 0/5 · 865 | 0/5 · 2818 | 0/5 · 2818 | 0/5 · 1114 | 0/5 · 550 | 5/5 · 3654 |
| Closure-138 | 2 | 5 | 4546 | 5/5 · 3627 | 2/5 · 982 | 2/5 · 982 | 3/5 · 45 | 3/5 · 45 | 4/5 · 1162 | 3/5 · 45 | 5/5 · 1278 |
| Closure-139 | 4 | 3 | 4550 | 3/3 · 3603 | 0/3 · 0 | 0/3 · 0 | 2/3 · 2827 | 2/3 · 2827 | 0/3 · 1134 | 0/3 · 550 | 3/3 · 818 |
| Closure-14 | 1 | 3 | 7605 | 3/3 · 7155 | 0/3 · 2057 | 0/3 · 2316 | 0/3 · 0 | 0/3 · 0 | 2/3 · 3852 | 0/3 · 0 | 3/3 · 3339 |
| Closure-140 | 3 | 1 | 4551 | 1/1 · 3627 | 0/1 · 0 | 0/1 · 0 | 0/1 · 2827 | 0/1 · 2827 | 0/1 · 1117 | 0/1 · 551 | 1/1 · 3692 |
| Closure-141 | 2 | 8 | 4559 | 8/8 · 3612 | 2/8 · 41 | 2/8 · 910 | 0/8 · 0 | 0/8 · 0 | 2/8 · 1119 | 2/8 · 461 | 8/8 · 3674 |
| Closure-142 | 2 | 2 | 4617 | 2/2 · 4135 | 0/2 · 868 | 0/2 · 868 | 1/2 · 2861 | 1/2 · 2861 | 1/2 · 1630 | 1/2 · 895 | 2/2 · 2599 |
| Closure-143 | 2 | 3 | 4624 | 3/3 · 3655 | 0/3 · 868 | 0/3 · 868 | 1/3 · 2864 | 1/3 · 2864 | 1/3 · 1147 | 1/3 · 23 | 3/3 · 91 |
| Closure-144 | 22 | 84 | 5749 | 76/84 · 4819 | 58/84 · 2666 | 58/84 · 2666 | 72/84 · 2896 | 74/84 · 3806 | 73/84 · 3215 | 0/84 · 35 | 84/84 · 5574 |
| Closure-145 | 1 | 2 | 5752 | 2/2 · 4755 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 2/2 · 689 | 2/2 · 2798 |
| Closure-146 | 1 | 1 | 5788 | 0/1 · 4 | 0/1 · 0 | 0/1 · 0 | 0/1 · 4 | 0/1 · 4 | 0/1 · 4 | 0/1 · 4 | 1/1 · 5614 |
| Closure-147 | 2 | 3 | 5800 | 3/3 · 4764 | 0/3 · 0 | 0/3 · 0 | 1/3 · 2915 | 1/3 · 3835 | 1/3 · 1808 | 0/3 · 0 | 3/3 · 101 |
| Closure-148 | 38 | 6 | 5810 | 6/6 · 4811 | 5/6 · 10 | 5/6 · 10 | 1/6 · 3821 | 1/6 · 3841 | 5/6 · 1824 | 5/6 · 196 | 6/6 · 92 |
| Closure-149 | 40 | 1 | 5943 | 1/1 · 5702 | 1/1 · 2725 | 1/1 · 2725 | 1/1 · 3923 | 1/1 · 3928 | 0/1 · 3325 | 1/1 · 3111 | 1/1 · 5008 |
| Closure-15 | 1 | 1 | 7599 | 0/1 · 0 | 0/1 · 0 | 0/1 · 2314 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 333 |
| Closure-150 | 1 | 2 | 6107 | 2/2 · 5047 | 0/2 · 1771 | 0/2 · 1778 | 2/2 · 3964 | 2/2 · 3984 | 0/2 · 1856 | 0/2 · 0 | 2/2 · 2280 |
| Closure-151 | 11 | 1 | 6121 | 1/1 · 39 | 1/1 · 39 | 1/1 · 39 | 1/1 · 1049 | 1/1 · 1049 | 0/1 · 16 | 1/1 · 39 | 1/1 · 39 |
| Closure-152 | 1 | 3 | 6200 | 3/3 · 5884 | 0/3 · 29 | 0/3 · 29 | 3/3 · 4059 | 3/3 · 4079 | 3/3 · 3328 | 0/3 · 676 | 3/3 · 6021 |
| Closure-153 | 11 | 2 | 6268 | 2/2 · 5169 | 0/2 · 0 | 0/2 · 0 | 1/2 · 4119 | 1/2 · 4139 | 1/2 · 1928 | 0/2 · 741 | 2/2 · 5294 |
| Closure-154 | 33 | 1 | 6685 | 1/1 · 5526 | 1/1 · 1891 | 1/1 · 1898 | 1/1 · 4376 | 1/1 · 4396 | 0/1 · 1993 | 1/1 · 2334 | 1/1 · 5654 |
| Closure-155 | 29 | 7 | 6816 | 7/7 · 6434 | 0/7 · 2897 | 0/7 · 2914 | 5/7 · 4478 | 5/7 · 4498 | 0/7 · 3622 | 0/7 · 3436 | 7/7 · 5759 |
| Closure-156 | 5 | 2 | 6833 | 2/2 · 3341 | 0/2 · 0 | 0/2 · 0 | 0/2 · 1357 | 0/2 · 1357 | 0/2 · 2013 | 0/2 · 634 | 2/2 · 332 |
| Closure-157 | 8 | 12 | 6862 | 12/12 · 5917 | 0/12 · 1899 | 0/12 · 1906 | 12/12 · 4499 | 12/12 · 4519 | 8/12 · 2209 | 4/12 · 843 | 12/12 · 5919 |
| Closure-158 | 58 | 2 | 6874 | 2/2 · 67 | 0/2 · 2 | 0/2 · 2 | 2/2 · 4522 | 2/2 · 4542 | 0/2 · 20 | 2/2 · 67 | 2/2 · 5812 |
| Closure-159 | 1 | 1 | 6909 | 1/1 · 3402 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 2018 | 0/1 · 636 | 1/1 · 283 |
| Closure-16 | 4 | 2 | 7599 | 2/2 · 7149 | 0/2 · 2057 | 0/2 · 2314 | 0/2 · 803 | 0/2 · 803 | 2/2 · 3849 | 0/2 · 0 | 2/2 · 390 |
| Closure-160 | 1 | 1 | 7066 | 1/1 · 6706 | 0/1 · 2844 | 0/1 · 2844 | 1/1 · 4534 | 1/1 · 4534 | 0/1 · 3613 | 1/1 · 3479 | 1/1 · 5976 |
| Closure-161 | 1 | 1 | 7164 | 1/1 · 5897 | 0/1 · 0 | 0/1 · 0 | 0/1 · 713 | 0/1 · 713 | 0/1 · 2064 | 0/1 · 0 | 1/1 · 180 |
| Closure-162 | 4 | 1 | 7235 | 1/1 · 5958 | 0/1 · 2068 | 0/1 · 3076 | 0/1 · 739 | 0/1 · 739 | 1/1 · 2096 | 0/1 · 889 | 1/1 · 5172 |
| Closure-163 | 35 | 3 | 7193 | 3/3 · 6012 | 0/3 · 2004 | 0/3 · 2244 | 0/3 · 3292 | 0/3 · 3292 | 0/3 · 2118 | 0/3 · 927 | 3/3 · 403 |
| Closure-164 | 1 | 3 | 7396 | 3/3 · 7097 | 3/3 · 3158 | 3/3 · 3238 | 3/3 · 3482 | 3/3 · 3533 | 3/3 · 3871 | 3/3 · 3717 | 3/3 · 6761 |
| Closure-165 | 17 | 1 | 7528 | 1/1 · 7231 | 1/1 · 3076 | 1/1 · 3169 | 1/1 · 3377 | 1/1 · 3428 | 1/1 · 3981 | 1/1 · 3624 | 1/1 · 7278 |
| Closure-166 | 1 | 2 | 7610 | 2/2 · 7239 | 0/2 · 0 | 0/2 · 2317 | 0/2 · 0 | 0/2 · 0 | 2/2 · 3856 | 0/2 · 0 | 2/2 · 7349 |
| Closure-167 | 6 | 3 | 7612 | 3/3 · 7241 | 0/3 · 0 | 2/3 · 2318 | 1/3 · 30 | 1/3 · 30 | 3/3 · 3859 | 0/3 · 29 | 3/3 · 7351 |
| Closure-168 | 1 | 1 | 7619 | 1/1 · 7248 | 1/1 · 2062 | 1/1 · 2321 | 0/1 · 807 | 0/1 · 817 | 1/1 · 3866 | 0/1 · 0 | 1/1 · 6556 |
| Closure-169 | 16 | 2 | 7727 | 2/2 · 7419 | 2/2 · 3152 | 2/2 · 3232 | 2/2 · 3467 | 2/2 · 3525 | 2/2 · 4118 | 2/2 · 3717 | 2/2 · 7457 |
| Closure-17 | 1 | 1 | 7597 | 1/1 · 7147 | 1/1 · 2057 | 1/1 · 2314 | 0/1 · 803 | 0/1 · 803 | 1/1 · 3847 | 0/1 · 0 | 1/1 · 6536 |
| Closure-170 | 2 | 1 | 8088 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 376 |
| Closure-171 | 2 | 3 | 8241 | 3/3 · 7857 | 0/3 · 0 | 1/3 · 2477 | 0/3 · 850 | 0/3 · 874 | 1/3 · 4145 | 0/3 · 0 | 3/3 · 7096 |
| Closure-172 | 1 | 1 | 8274 | 1/1 · 7890 | 0/1 · 0 | 1/1 · 2487 | 0/1 · 856 | 0/1 · 880 | 1/1 · 4172 | 0/1 · 0 | 1/1 · 7117 |
| Closure-173 | 3 | 3 | 8294 | 3/3 · 7906 | 0/3 · 0 | 0/3 · 0 | 0/3 · 0 | 0/3 · 0 | 2/3 · 4181 | 0/3 · 0 | 3/3 · 4504 |
| Closure-174 | 3 | 3 | 8315 | 3/3 · 7922 | 0/3 · 0 | 0/3 · 2497 | 0/3 · 851 | 0/3 · 875 | 0/3 · 4182 | 0/3 · 932 | 3/3 · 7102 |
| Closure-175 | 23 | 5 | 8417 | 5/5 · 7989 | 0/5 · 7 | 0/5 · 2530 | 2/5 · 854 | 2/5 · 878 | 2/5 · 4222 | 2/5 · 683 | 5/5 · 695 |
| Closure-176 | 1 | 1 | 8439 | 1/1 · 8010 | 0/1 · 0 | 1/1 · 2531 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4234 | 0/1 · 0 | 1/1 · 3250 |
| Closure-18 | 1 | 1 | 7596 | 1/1 · 3810 | 0/1 · 283 | 0/1 · 283 | 0/1 · 46 | 0/1 · 46 | 1/1 · 3846 | 0/1 · 862 | 1/1 · 6538 |
| Closure-19 | 1 | 1 | 7595 | 1/1 · 7145 | 0/1 · 0 | 0/1 · 2313 | 0/1 · 46 | 0/1 · 46 | 1/1 · 3845 | 0/1 · 46 | 1/1 · 6535 |
| Closure-20 | 1 | 1 | 7587 | 1/1 · 7137 | 0/1 · 0 | 0/1 · 0 | 0/1 · 799 | 0/1 · 799 | 0/1 · 3840 | 0/1 · 0 | 1/1 · 369 |
| Closure-21 | 1 | 1 | 7587 | 1/1 · 7137 | 0/1 · 2055 | 0/1 · 2312 | 0/1 · 799 | 0/1 · 799 | 0/1 · 3840 | 0/1 · 0 | 1/1 · 6526 |
| Closure-22 | 1 | 1 | 7587 | 1/1 · 7137 | 0/1 · 2055 | 0/1 · 2312 | 0/1 · 799 | 0/1 · 799 | 0/1 · 3840 | 0/1 · 0 | 1/1 · 6526 |
| Closure-23 | 1 | 1 | 7567 | 1/1 · 6340 | 0/1 · 0 | 0/1 · 0 | 0/1 · 796 | 0/1 · 796 | 0/1 · 2313 | 0/1 · 0 | 1/1 · 372 |
| Closure-24 | 1 | 1 | 7530 | 1/1 · 6323 | 0/1 · 0 | 0/1 · 2309 | 0/1 · 790 | 0/1 · 790 | 0/1 · 2299 | 0/1 · 944 | 1/1 · 380 |
| Closure-25 | 1 | 1 | 7527 | 1/1 · 6320 | 0/1 · 0 | 0/1 · 2308 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2296 | 0/1 · 0 | 1/1 · 2896 |
| Closure-26 | 8 | 7 | 7525 | 7/7 · 6318 | 0/7 · 2052 | 2/7 · 2308 | 0/7 · 786 | 0/7 · 786 | 2/7 · 2294 | 2/7 · 848 | 7/7 · 6486 |
| Closure-27 | 3 | 3 | 7522 | 3/3 · 3 | 3/3 · 3 | 3/3 · 3 | 3/3 · 3 | 3/3 · 3 | 3/3 · 3 | 3/3 · 3 | 3/3 · 6875 |
| Closure-28 | 9 | 2 | 7519 | 2/2 · 6398 | 0/2 · 52 | 0/2 · 52 | 1/2 · 3319 | 1/2 · 3319 | 1/2 · 2291 | 1/2 · 653 | 2/2 · 668 |
| Closure-29 | 1 | 5 | 7518 | 5/5 · 6314 | 0/5 · 0 | 0/5 · 2307 | 0/5 · 786 | 0/5 · 786 | 1/5 · 2291 | 0/5 · 940 | 5/5 · 291 |
| Closure-30 | 6 | 3 | 7472 | 3/3 · 6275 | 0/3 · 2047 | 0/3 · 2446 | 0/3 · 947 | 0/3 · 947 | 3/3 · 2246 | 0/3 · 666 | 3/3 · 337 |
| Closure-31 | 1 | 1 | 7466 | 1/1 · 3716 | 1/1 · 424 | 1/1 · 424 | 0/1 · 195 | 0/1 · 195 | 0/1 · 2245 | 1/1 · 1003 | 1/1 · 6435 |
| Closure-32 | 1 | 4 | 7465 | 4/4 · 6792 | 0/4 · 0 | 0/4 · 0 | 0/4 · 0 | 0/4 · 0 | 3/4 · 2751 | 3/4 · 379 | 4/4 · 5079 |
| Closure-33 | 1 | 1 | 7461 | 1/1 · 6262 | 0/1 · 0 | 1/1 · 2441 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2243 | 0/1 · 0 | 1/1 · 7218 |
| Closure-34 | 3 | 1 | 7454 | 1/1 · 6338 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4015 |
| Closure-35 | 1 | 1 | 7422 | 1/1 · 6228 | 0/1 · 0 | 1/1 · 2415 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2219 | 0/1 · 0 | 1/1 · 2821 |
| Closure-36 | 1 | 1 | 7421 | 1/1 · 6227 | 0/1 · 0 | 1/1 · 2414 | 1/1 · 931 | 1/1 · 931 | 1/1 · 2218 | 1/1 · 1084 | 1/1 · 384 |
| Closure-37 | 2 | 1 | 7413 | 1/1 · 6368 | 0/1 · 2027 | 1/1 · 2413 | 1/1 · 930 | 1/1 · 930 | 0/1 · 2362 | 1/1 · 1083 | 1/1 · 6543 |
| Closure-38 | 1 | 1 | 7405 | 1/1 · 6294 | 0/1 · 52 | 0/1 · 52 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4004 |
| Closure-39 | 1 | 2 | 7394 | 2/2 · 7096 | 2/2 · 2363 | 2/2 · 3188 | 2/2 · 3466 | 2/2 · 3517 | 2/2 · 3864 | 2/2 · 3665 | 2/2 · 7151 |
| Closure-40 | 1 | 2 | 7393 | 2/2 · 6206 | 0/2 · 2019 | 1/2 · 2404 | 1/2 · 927 | 1/2 · 927 | 1/2 · 2206 | 0/2 · 0 | 2/2 · 522 |
| Closure-41 | 2 | 3 | 7386 | 3/3 · 6199 | 3/3 · 2018 | 3/3 · 2401 | 0/3 · 0 | 0/3 · 0 | 2/3 · 2200 | 0/3 · 0 | 3/3 · 6359 |
| Closure-42 | 1 | 1 | 7245 | 1/1 · 6208 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2270 | 0/1 · 0 | 1/1 · 6282 |
| Closure-43 | 31 | 2 | 7244 | 2/2 · 6060 | 2/2 · 2017 | 2/2 · 2262 | 0/2 · 786 | 0/2 · 786 | 0/2 · 2125 | 0/2 · 937 | 2/2 · 6218 |
| Closure-44 | 1 | 1 | 7201 | 1/1 · 6097 | 0/1 · 52 | 0/1 · 52 | 1/1 · 3264 | 1/1 · 3264 | 0/1 · 0 | 0/1 · 0 | 1/1 · 3828 |
| Closure-45 | 2 | 1 | 7197 | 1/1 · 3592 | 0/1 · 0 | 0/1 · 0 | 0/1 · 49 | 0/1 · 49 | 0/1 · 2118 | 0/1 · 657 | 1/1 · 177 |
| Closure-46 | 1 | 3 | 7249 | 3/3 · 6952 | 0/3 · 2004 | 0/3 · 2244 | 3/3 · 806 | 3/3 · 806 | 3/3 · 3716 | 3/3 · 960 | 3/3 · 2095 |
| Closure-47 | 2 | 16 | 7236 | 8/16 · 6076 | 0/16 · 0 | 0/16 · 0 | 8/16 · 16 | 8/16 · 16 | 8/16 · 16 | 8/16 · 16 | 16/16 · 6215 |
| Closure-48 | 1 | 1 | 7214 | 1/1 · 6036 | 1/1 · 1997 | 1/1 · 2234 | 0/1 · 769 | 0/1 · 769 | 0/1 · 2116 | 0/1 · 0 | 1/1 · 6193 |
| Closure-49 | 3 | 66 | 7319 | 66/66 · 6020 | 0/66 · 1990 | 11/66 · 3126 | 0/66 · 764 | 0/66 · 764 | 17/66 · 2111 | 17/66 · 912 | 66/66 · 1838 |
| Closure-50 | 1 | 2 | 7306 | 2/2 · 6008 | 0/2 · 0 | 0/2 · 0 | 0/2 · 760 | 0/2 · 760 | 0/2 · 2107 | 0/2 · 0 | 2/2 · 101 |
| Closure-51 | 2 | 1 | 7290 | 1/1 · 6068 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 3820 |
| Closure-52 | 1 | 1 | 7270 | 1/1 · 6056 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 3800 |
| Closure-53 | 1 | 1 | 7248 | 1/1 · 5969 | 0/1 · 0 | 0/1 · 3086 | 0/1 · 745 | 0/1 · 745 | 0/1 · 2105 | 0/1 · 895 | 1/1 · 116 |
| Closure-54 | 3 | 3 | 7231 | 3/3 · 6907 | 2/3 · 3027 | 2/3 · 3074 | 3/3 · 3324 | 3/3 · 3373 | 3/3 · 3740 | 3/3 · 3553 | 3/3 · 6962 |
| Closure-55 | 1 | 1 | 7207 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 730 | 0/1 · 2084 | 0/1 · 0 | 1/1 · 96 |
| Closure-56 | 1 | 3 | 7197 | 3/3 · 6006 | 0/3 · 0 | 0/3 · 0 | 1/3 · 729 | 1/3 · 729 | 1/3 · 2139 | 0/3 · 0 | 3/3 · 6083 |
| Closure-57 | 1 | 1 | 7178 | 1/1 · 5906 | 0/1 · 0 | 0/1 · 0 | 1/1 · 720 | 1/1 · 720 | 1/1 · 2071 | 1/1 · 1 | 1/1 · 6060 |
| Closure-58 | 1 | 1 | 7175 | 1/1 · 5904 | 0/1 · 2038 | 0/1 · 3041 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2069 | 0/1 · 0 | 1/1 · 177 |
| Closure-59 | 1 | 1 | 7150 | 1/1 · 6781 | 0/1 · 2853 | 0/1 · 2853 | 0/1 · 3165 | 0/1 · 3165 | 0/1 · 3643 | 1/1 · 3502 | 1/1 · 6039 |
| Closure-6 | 2 | 3 | 7762 | 3/3 · 7387 | 3/3 · 2054 | 3/3 · 2377 | 2/3 · 819 | 2/3 · 831 | 3/3 · 3951 | 0/3 · 0 | 3/3 · 6671 |
| Closure-60 | 2 | 2 | 7126 | 2/2 · 5868 | 1/2 · 2027 | 2/2 · 3020 | 1/2 · 715 | 1/2 · 715 | 2/2 · 2050 | 0/2 · 0 | 2/2 · 5991 |
| Closure-61 | 1 | 3 | 7120 | 3/3 · 5959 | 0/3 · 2072 | 0/3 · 3065 | 0/3 · 0 | 0/3 · 0 | 0/3 · 2065 | 0/3 · 0 | 3/3 · 5984 |
| Closure-62 | 1 | 2 | 7120 | 2/2 · 158 | 0/2 · 0 | 0/2 · 0 | 2/2 · 3199 | 2/2 · 3199 | 2/2 · 2099 | 2/2 · 74 | 2/2 · 6047 |
| Closure-64 | 1 | 1 | 7102 | 1/1 · 5849 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1451 | 1/1 · 1451 | 1/1 · 2089 | 1/1 · 771 | 1/1 · 6001 |
| Closure-65 | 1 | 1 | 7099 | 1/1 · 5918 | 0/1 · 1 | 0/1 · 1 | 1/1 · 2090 | 1/1 · 2090 | 1/1 · 2042 | 1/1 · 875 | 1/1 · 3729 |
| Closure-66 | 1 | 2 | 7079 | 2/2 · 5829 | 2/2 · 1916 | 2/2 · 3015 | 2/2 · 2084 | 2/2 · 2084 | 2/2 · 2041 | 0/2 · 0 | 2/2 · 5982 |
| Closure-67 | 1 | 1 | 7071 | 1/1 · 5821 | 0/1 · 1914 | 0/1 · 3013 | 1/1 · 2077 | 1/1 · 2077 | 0/1 · 2039 | 0/1 · 0 | 1/1 · 131 |
| Closure-68 | 3 | 1 | 7065 | 1/1 · 6390 | 0/1 · 6 | 0/1 · 6 | 0/1 · 2204 | 0/1 · 2204 | 1/1 · 2596 | 1/1 · 373 | 1/1 · 4606 |
| Closure-69 | 1 | 3 | 7072 | 3/3 · 5829 | 3/3 · 1929 | 3/3 · 3025 | 0/3 · 2073 | 0/3 · 2073 | 2/3 · 2042 | 0/3 · 0 | 3/3 · 5982 |
| Closure-7 | 1 | 2 | 7723 | 2/2 · 7348 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 2/2 · 3926 | 0/2 · 0 | 2/2 · 6645 |
| Closure-70 | 1 | 5 | 7056 | 5/5 · 5815 | 5/5 · 1920 | 5/5 · 1927 | 2/5 · 2067 | 2/5 · 2067 | 2/5 · 2036 | 0/5 · 0 | 5/5 · 5965 |
| Closure-71 | 1 | 2 | 6996 | 2/2 · 5773 | 0/2 · 1898 | 0/2 · 1905 | 0/2 · 2050 | 0/2 · 2050 | 0/2 · 2021 | 0/2 · 0 | 2/2 · 5921 |
| Closure-72 | 2 | 1 | 6965 | 1/1 · 5742 | 0/1 · 1898 | 0/1 · 1905 | 0/1 · 2039 | 0/1 · 2039 | 0/1 · 2021 | 0/1 · 0 | 1/1 · 420 |
| Closure-73 | 1 | 1 | 6910 | 1/1 · 5767 | 0/1 · 1 | 0/1 · 1 | 1/1 · 2023 | 1/1 · 2023 | 1/1 · 2020 | 1/1 · 849 | 1/1 · 3597 |
| Closure-74 | 2 | 3 | 6891 | 3/3 · 5700 | 0/3 · 0 | 0/3 · 0 | 2/3 · 2017 | 2/3 · 2017 | 2/3 · 2017 | 0/3 · 0 | 3/3 · 170 |
| Closure-75 | 2 | 1 | 6856 | 1/1 · 5668 | 0/1 · 1 | 0/1 · 1 | 1/1 · 4492 | 1/1 · 4512 | 0/1 · 2015 | 0/1 · 0 | 1/1 · 5761 |
| Closure-76 | 2 | 4 | 6753 | 4/4 · 5589 | 0/4 · 1896 | 0/4 · 1903 | 0/4 · 0 | 0/4 · 0 | 0/4 · 2007 | 0/4 · 821 | 4/4 · 107 |
| Closure-77 | 1 | 1 | 6744 | 1/1 · 5635 | 0/1 · 1 | 0/1 · 1 | 1/1 · 4433 | 1/1 · 4453 | 1/1 · 2004 | 1/1 · 833 | 1/1 · 3473 |
| Closure-78 | 1 | 1 | 6742 | 1/1 · 5578 | 0/1 · 0 | 0/1 · 0 | 0/1 · 4430 | 0/1 · 4450 | 0/1 · 2002 | 0/1 · 0 | 1/1 · 156 |
| Closure-79 | 2 | 5 | 6703 | 5/5 · 5544 | 0/5 · 1889 | 0/5 · 1896 | 4/5 · 4391 | 4/5 · 4411 | 2/5 · 1989 | 0/5 · 655 | 5/5 · 5672 |
| Closure-8 | 2 | 1 | 7662 | 1/1 · 7290 | 0/1 · 2082 | 0/1 · 2344 | 0/1 · 808 | 0/1 · 818 | 0/1 · 3894 | 0/1 · 0 | 1/1 · 282 |
| Closure-80 | 2 | 2 | 6697 | 2/2 · 5645 | 1/2 · 1941 | 2/2 · 1957 | 0/2 · 0 | 0/2 · 0 | 2/2 · 2011 | 0/2 · 0 | 2/2 · 5631 |
| Closure-81 | 1 | 1 | 6642 | 1/1 · 5675 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4359 | 1/1 · 4379 | 1/1 · 2175 | 0/1 · 0 | 1/1 · 5723 |
| Closure-82 | 1 | 2 | 6574 | 2/2 · 6304 | 2/2 · 2920 | 2/2 · 2943 | 2/2 · 4313 | 2/2 · 4333 | 2/2 · 3481 | 2/2 · 3377 | 2/2 · 6355 |
| Closure-83 | 1 | 1 | 6501 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 53 |
| Closure-84 | 3 | 1 | 6484 | 1/1 · 5521 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4235 | 1/1 · 4255 | 1/1 · 2147 | 0/1 · 0 | 1/1 · 5569 |
| Closure-85 | 2 | 2 | 6471 | 2/2 · 5323 | 0/2 · 1849 | 0/2 · 1856 | 1/2 · 4231 | 1/2 · 4251 | 0/2 · 1960 | 0/2 · 0 | 2/2 · 77 |
| Closure-86 | 1 | 7 | 6425 | 7/7 · 5386 | 1/7 · 1900 | 1/7 · 1907 | 0/7 · 0 | 0/7 · 0 | 1/7 · 1975 | 0/7 · 0 | 7/7 · 5371 |
| Closure-87 | 1 | 1 | 6330 | 1/1 · 5220 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4145 | 1/1 · 4165 | 0/1 · 1919 | 0/1 · 0 | 1/1 · 112 |
| Closure-88 | 1 | 7 | 6323 | 7/7 · 5218 | 0/7 · 1843 | 0/7 · 1850 | 0/7 · 0 | 0/7 · 0 | 0/7 · 1919 | 1/7 · 749 | 7/7 · 92 |
| Closure-89 | 2 | 8 | 6236 | 8/8 · 2926 | 0/8 · 0 | 0/8 · 0 | 6/8 · 1125 | 6/8 · 1125 | 0/8 · 1894 | 0/8 · 600 | 8/8 · 443 |
| Closure-9 | 2 | 1 | 7659 | 1/1 · 7288 | 1/1 · 2081 | 1/1 · 2343 | 1/1 · 809 | 1/1 · 819 | 1/1 · 3893 | 1/1 · 1 | 1/1 · 117 |
| Closure-90 | 2 | 2 | 6209 | 2/2 · 5893 | 0/2 · 29 | 0/2 · 29 | 2/2 · 4068 | 2/2 · 4088 | 2/2 · 3337 | 0/2 · 676 | 2/2 · 6030 |
| Closure-91 | 1 | 1 | 6185 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4064 | 0/1 · 1874 | 0/1 · 0 | 1/1 · 96 |
| Closure-92 | 1 | 1 | 6171 | 1/1 · 2951 | 0/1 · 0 | 0/1 · 0 | 0/1 · 4039 | 0/1 · 4059 | 0/1 · 1872 | 0/1 · 0 | 1/1 · 1807 |
| Closure-94 | 1 | 3 | 6154 | 1/3 · 1 | 1/3 · 1 | 1/3 · 1 | 1/3 · 1 | 1/3 · 4044 | 1/3 · 1866 | 0/3 · 0 | 3/3 · 5154 |
| Closure-95 | 1 | 2 | 6112 | 2/2 · 5052 | 1/2 · 1775 | 1/2 · 1782 | 0/2 · 0 | 0/2 · 0 | 0/2 · 1858 | 0/2 · 719 | 2/2 · 2285 |
| Closure-96 | 1 | 1 | 6019 | 1/1 · 4959 | 1/1 · 1768 | 1/1 · 1775 | 1/1 · 3926 | 1/1 · 3945 | 0/1 · 1858 | 0/1 · 0 | 1/1 · 5080 |
| Closure-97 | 1 | 1 | 5837 | 1/1 · 4799 | 0/1 · 0 | 0/1 · 0 | 0/1 · 2923 | 0/1 · 3848 | 0/1 · 1819 | 0/1 · 0 | 1/1 · 82 |
| Closure-98 | 5 | 1 | 5697 | 1/1 · 4686 | 0/1 · 1683 | 0/1 · 1683 | 0/1 · 2878 | 1/1 · 3785 | 0/1 · 1797 | 0/1 · 683 | 1/1 · 373 |
| Closure-99 | 1 | 3 | 5695 | 0/3 · 0 | 0/3 · 0 | 0/3 · 0 | 0/3 · 0 | 2/3 · 3784 | 0/3 · 1797 | 0/3 · 0 | 3/3 · 75 |
| Codec-10 | 1 | 1 | 358 | 1/1 · 53 | 0/1 · 1 | 0/1 · 1 | 0/1 · 31 | 0/1 · 31 | 1/1 · 54 | 0/1 · 0 | 1/1 · 13 |
| Codec-11 | 10 | 5 | 404 | 5/5 · 107 | 0/5 · 4 | 0/5 · 4 | 5/5 · 82 | 5/5 · 82 | 5/5 · 105 | 5/5 · 81 | 5/5 · 33 |
| Codec-12 | 6 | 12 | 436 | 12/12 · 35 | 12/12 · 16 | 12/12 · 16 | 12/12 · 16 | 12/12 · 16 | 12/12 · 35 | 0/12 · 0 | 12/12 · 35 |
| Codec-13 | 4 | 2 | 599 | 2/2 · 8 | 2/2 · 155 | 2/2 · 155 | 0/2 · 125 | 0/2 · 125 | 1/2 · 1 | 0/2 · 0 | 2/2 · 248 |
| Codec-14 | 8 | 1 | 600 | 1/1 · 279 | 0/1 · 2 | 0/1 · 2 | 1/1 · 70 | 1/1 · 70 | 1/1 · 280 | 1/1 · 69 | 1/1 · 30 |
| Codec-15 | 1 | 1 | 664 | 1/1 · 116 | 0/1 · 0 | 0/1 · 0 | 0/1 · 52 | 0/1 · 52 | 0/1 · 55 | 0/1 · 4 | 1/1 · 32 |
| Codec-16 | 5 | 1 | 665 | 1/1 · 247 | 0/1 · 103 | 0/1 · 103 | 1/1 · 121 | 1/1 · 135 | 1/1 · 64 | 0/1 · 127 | 1/1 · 31 |
| Codec-17 | 1 | 1 | 704 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 317 |
| Codec-18 | 1 | 2 | 707 | 2/2 · 11 | 0/2 · 15 | 0/2 · 15 | 2/2 · 3 | 2/2 · 3 | 2/2 · 4 | 2/2 · 3 | 2/2 · 320 |
| Codec-6 | 1 | 1 | 311 | 0/1 · 8 | 1/1 · 16 | 1/1 · 16 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4 | 1/1 · 4 | 1/1 · 10 |
| Codec-7 | 1 | 2 | 312 | 2/2 · 4 | 2/2 · 4 | 2/2 · 4 | 2/2 · 4 | 2/2 · 4 | 2/2 · 4 | 2/2 · 4 | 2/2 · 85 |
| Codec-8 | 1 | 1 | 313 | 1/1 · 9 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 5 | 1/1 · 5 | 1/1 · 86 |
| Codec-9 | 1 | 1 | 331 | 1/1 · 76 | 1/1 · 28 | 1/1 · 28 | 0/1 · 5 | 0/1 · 5 | 1/1 · 73 | 1/1 · 74 | 1/1 · 87 |
| Collections-10 | 19 | 2 | 5891 | 2/2 · 5565 | 0/2 · 2 | 0/2 · 29 | 2/2 · 3565 | 2/2 · 3769 | 2/2 · 4887 | 2/2 · 1206 | 2/2 · 33 |
| Collections-11 | 1 | 1 | 5894 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 62 |
| Collections-12 | 1 | 1 | 5894 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 16 |
| Collections-13 | 1 | 1 | 5895 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 17 |
| Collections-14 | 1 | 1 | 5896 | 1/1 · 5560 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2938 | 1/1 · 2938 | 1/1 · 4571 | 0/1 · 78 | 1/1 · 45 |
| Collections-15 | 1 | 1 | 5897 | 1/1 · 5534 | 0/1 · 0 | 0/1 · 0 | 1/1 · 5 | 1/1 · 5 | 1/1 · 10 | 1/1 · 5 | 1/1 · 69 |
| Collections-16 | 2 | 1 | 5898 | 1/1 · 5535 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1 | 1/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 70 |
| Collections-17 | 2 | 1 | 5402 | 1/1 · 5116 | 0/1 · 6 | 0/1 · 14 | 1/1 · 4674 | 1/1 · 4674 | 1/1 · 14 | 0/1 · 6 | 1/1 · 197 |
| Collections-18 | 1 | 1 | 5519 | 1/1 · 4486 | 0/1 · 0 | 0/1 · 2417 | 1/1 · 2 | 1/1 · 2 | 1/1 · 3 | 1/1 · 2 | 1/1 · 66 |
| Collections-19 | 1 | 1 | 5541 | 1/1 · 5322 | 0/1 · 0 | 0/1 · 0 | 1/1 · 5 | 1/1 · 5 | 1/1 · 11 | 1/1 · 6 | 1/1 · 74 |
| Collections-20 | 1 | 1 | 5620 | 1/1 · 144 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 63 |
| Collections-21 | 1 | 1 | 5340 | 1/1 · 4327 | 0/1 · 0 | 0/1 · 0 | 0/1 · 1 | 0/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 75 |
| Collections-22 | 1 | 1 | 5562 | 1/1 · 4 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4273 | 1/1 · 5 | 1/1 · 258 |
| Collections-23 | 1 | 2 | 5589 | 2/2 · 4538 | 0/2 · 0 | 0/2 · 0 | 2/2 · 2481 | 2/2 · 2481 | 2/2 · 4289 | 2/2 · 3382 | 2/2 · 53 |
| Collections-24 | 13 | 2 | 5591 | 2/2 · 5396 | 2/2 · 2307 | 2/2 · 2357 | 2/2 · 2330 | 2/2 · 2330 | 0/2 · 2365 | 2/2 · 1837 | 2/2 · 126 |
| Collections-25 | 1 | 1 | 6431 | 1/1 · 5316 | 1/1 · 1 | 1/1 · 1 | 1/1 · 3478 | 1/1 · 3478 | 0/1 · 0 | 1/1 · 1 | 1/1 · 287 |
| Collections-26 | 1 | 1 | 6502 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 74 |
| Collections-27 | 1 | 1 | 6498 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 101 |
| Collections-28 | 16 | 1 | 6737 | 1/1 · 6564 | 0/1 · 0 | 0/1 · 0 | 1/1 · 9 | 1/1 · 9 | 1/1 · 7 | 1/1 · 10 | 1/1 · 164 |
| Collections-6 | 1 | 1 | 5863 | 1/1 · 62 | 0/1 · 0 | 0/1 · 2 | 1/1 · 1 | 1/1 · 1 | 1/1 · 62 | 1/1 · 60 | 1/1 · 54 |
| Collections-7 | 15 | 3 | 5874 | 3/3 · 13 | 2/3 · 12 | 2/3 · 12 | 3/3 · 3014 | 3/3 · 3014 | 3/3 · 14 | 3/3 · 14 | 3/3 · 14 |
| Collections-8 | 2 | 1 | 5875 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 111 |
| Collections-9 | 1 | 1 | 5876 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 15 |
| Compress-10 | 1 | 1 | 327 | 1/1 · 36 | 0/1 · 0 | 0/1 · 0 | 1/1 · 36 | 1/1 · 36 | 1/1 · 92 | 1/1 · 17 | 1/1 · 35 |
| Compress-11 | 1 | 1 | 338 | 1/1 · 41 | 1/1 · 64 | 1/1 · 64 | 0/1 · 0 | 0/1 · 0 | 1/1 · 53 | 0/1 · 7 | 1/1 · 157 |
| Compress-12 | 1 | 1 | 340 | 1/1 · 76 | 1/1 · 76 | 1/1 · 76 | 0/1 · 41 | 0/1 · 41 | 1/1 · 72 | 1/1 · 67 | 1/1 · 164 |
| Compress-13 | 1 | 2 | 343 | 2/2 · 184 | 0/2 · 0 | 0/2 · 0 | 2/2 · 160 | 2/2 · 160 | 2/2 · 184 | 2/2 · 107 | 2/2 · 103 |
| Compress-14 | 1 | 1 | 344 | 1/1 · 105 | 0/1 · 4 | 0/1 · 4 | 1/1 · 66 | 1/1 · 66 | 1/1 · 101 | 1/1 · 76 | 1/1 · 85 |
| Compress-15 | 1 | 1 | 372 | 1/1 · 18 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 104 |
| Compress-16 | 1 | 1 | 374 | 1/1 · 42 | 1/1 · 65 | 1/1 · 65 | 0/1 · 0 | 0/1 · 0 | 1/1 · 54 | 0/1 · 7 | 1/1 · 165 |
| Compress-17 | 1 | 1 | 375 | 1/1 · 118 | 0/1 · 8 | 0/1 · 8 | 0/1 · 7 | 0/1 · 7 | 1/1 · 114 | 1/1 · 106 | 1/1 · 102 |
| Compress-18 | 1 | 1 | 381 | 1/1 · 74 | 0/1 · 26 | 0/1 · 26 | 1/1 · 63 | 1/1 · 63 | 1/1 · 74 | 1/1 · 74 | 1/1 · 174 |
| Compress-19 | 1 | 1 | 415 | 1/1 · 46 | 0/1 · 1 | 0/1 · 1 | 1/1 · 46 | 1/1 · 46 | 1/1 · 102 | 1/1 · 23 | 1/1 · 135 |
| Compress-20 | 3 | 1 | 422 | 1/1 · 62 | 0/1 · 5 | 0/1 · 29 | 1/1 · 35 | 1/1 · 35 | 1/1 · 56 | 1/1 · 62 | 1/1 · 184 |
| Compress-21 | 1 | 8 | 485 | 8/8 · 15 | 0/8 · 0 | 0/8 · 0 | 8/8 · 15 | 8/8 · 15 | 8/8 · 15 | 8/8 · 15 | 8/8 · 15 |
| Compress-22 | 6 | 1 | 491 | 1/1 · 236 | 0/1 · 9 | 0/1 · 14 | 1/1 · 26 | 1/1 · 26 | 1/1 · 37 | 0/1 · 0 | 1/1 · 55 |
| Compress-23 | 1 | 1 | 492 | 1/1 · 24 | 0/1 · 0 | 0/1 · 0 | 1/1 · 21 | 1/1 · 21 | 1/1 · 24 | 0/1 · 0 | 1/1 · 25 |
| Compress-24 | 1 | 1 | 493 | 1/1 · 141 | 1/1 · 8 | 1/1 · 8 | 1/1 · 7 | 1/1 · 7 | 1/1 · 137 | 1/1 · 129 | 1/1 · 123 |
| Compress-25 | 1 | 1 | 495 | 1/1 · 96 | 0/1 · 69 | 0/1 · 69 | 1/1 · 70 | 1/1 · 70 | 1/1 · 85 | 1/1 · 15 | 1/1 · 247 |
| Compress-26 | 1 | 2 | 530 | 2/2 · 266 | 0/2 · 106 | 0/2 · 106 | 0/2 · 110 | 0/2 · 110 | 2/2 · 155 | 2/2 · 145 | 2/2 · 264 |
| Compress-27 | 1 | 1 | 531 | 1/1 · 143 | 1/1 · 8 | 1/1 · 8 | 1/1 · 7 | 1/1 · 7 | 1/1 · 140 | 1/1 · 130 | 1/1 · 127 |
| Compress-28 | 1 | 1 | 532 | 1/1 · 268 | 1/1 · 105 | 1/1 · 108 | 1/1 · 66 | 1/1 · 219 | 1/1 · 105 | 1/1 · 92 | 1/1 · 275 |
| Compress-29 | 140 | 3 | 585 | 3/3 · 422 | 3/3 · 313 | 3/3 · 313 | 3/3 · 374 | 3/3 · 410 | 3/3 · 187 | 3/3 · 163 | 3/3 · 304 |
| Compress-30 | 1 | 1 | 589 | 1/1 · 1 | 0/1 · 11 | 0/1 · 17 | 0/1 · 0 | 0/1 · 0 | 1/1 · 61 | 1/1 · 1 | 1/1 · 93 |
| Compress-31 | 1 | 2 | 589 | 2/2 · 147 | 1/2 · 8 | 1/2 · 8 | 1/2 · 7 | 1/2 · 7 | 2/2 · 151 | 2/2 · 135 | 2/2 · 136 |
| Compress-32 | 1 | 1 | 598 | 1/1 · 109 | 1/1 · 109 | 1/1 · 109 | 1/1 · 68 | 1/1 · 68 | 1/1 · 113 | 1/1 · 97 | 1/1 · 294 |
| Compress-33 | 8 | 1 | 598 | 1/1 · 409 | 1/1 · 12 | 1/1 · 18 | 1/1 · 7 | 1/1 · 7 | 1/1 · 17 | 1/1 · 6 | 1/1 · 42 |
| Compress-34 | 19 | 1 | 598 | 1/1 · 290 | 0/1 · 1 | 0/1 · 1 | 1/1 · 202 | 1/1 · 202 | 1/1 · 231 | 1/1 · 96 | 1/1 · 149 |
| Compress-35 | 1 | 1 | 604 | 1/1 · 143 | 0/1 · 1 | 0/1 · 1 | 0/1 · 1 | 0/1 · 1 | 1/1 · 147 | 0/1 · 130 | 1/1 · 140 |
| Compress-36 | 1 | 1 | 612 | 1/1 · 35 | 0/1 · 0 | 0/1 · 0 | 1/1 · 43 | 1/1 · 43 | 1/1 · 35 | 1/1 · 35 | 1/1 · 103 |
| Compress-37 | 1 | 1 | 614 | 1/1 · 118 | 1/1 · 118 | 1/1 · 118 | 1/1 · 76 | 1/1 · 76 | 1/1 · 122 | 1/1 · 105 | 1/1 · 303 |
| Compress-38 | 1 | 1 | 615 | 1/1 · 328 | 1/1 · 146 | 1/1 · 146 | 1/1 · 224 | 1/1 · 355 | 1/1 · 183 | 1/1 · 132 | 1/1 · 129 |
| Compress-39 | 10 | 1 | 617 | 1/1 · 286 | 1/1 · 158 | 1/1 · 158 | 1/1 · 135 | 1/1 · 135 | 1/1 · 196 | 1/1 · 182 | 1/1 · 162 |
| Compress-40 | 1 | 2 | 622 | 2/2 · 287 | 0/2 · 5 | 0/2 · 5 | 2/2 · 14 | 2/2 · 14 | 2/2 · 33 | 2/2 · 14 | 2/2 · 50 |
| Compress-41 | 1 | 2 | 654 | 2/2 · 88 | 1/2 · 26 | 1/2 · 50 | 1/2 · 60 | 1/2 · 60 | 2/2 · 76 | 2/2 · 83 | 2/2 · 310 |
| Compress-42 | 3 | 1 | 685 | 1/1 · 3 | 1/1 · 2 | 1/1 · 2 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 169 |
| Compress-43 | 4 | 1 | 813 | 1/1 · 140 | 1/1 · 28 | 1/1 · 28 | 1/1 · 127 | 1/1 · 128 | 0/1 · 125 | 0/1 · 74 | 1/1 · 424 |
| Compress-44 | 1 | 3 | 848 | 3/3 · 60 | 0/3 · 0 | 0/3 · 49 | 3/3 · 34 | 3/3 · 34 | 3/3 · 440 | 0/3 · 0 | 3/3 · 54 |
| Compress-45 | 1 | 1 | 848 | 1/1 · 91 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 82 | 1/1 · 90 | 1/1 · 146 |
| Compress-46 | 1 | 1 | 853 | 1/1 · 4 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 177 |
| Compress-47 | 3 | 1 | 919 | 1/1 · 271 | 0/1 · 32 | 0/1 · 56 | 1/1 · 64 | 1/1 · 346 | 0/1 · 75 | 0/1 · 13 | 1/1 · 401 |
| Compress-6 | 2 | 1 | 150 | 1/1 · 80 | 0/1 · 0 | 0/1 · 0 | 1/1 · 70 | 1/1 · 70 | 1/1 · 80 | 1/1 · 69 | 1/1 · 80 |
| Compress-7 | 1 | 1 | 170 | 1/1 · 65 | 1/1 · 2 | 1/1 · 2 | 1/1 · 51 | 1/1 · 51 | 1/1 · 65 | 1/1 · 50 | 1/1 · 61 |
| Compress-8 | 1 | 1 | 172 | 1/1 · 67 | 1/1 · 3 | 1/1 · 3 | 1/1 · 52 | 1/1 · 52 | 1/1 · 67 | 1/1 · 52 | 1/1 · 63 |
| Compress-9 | 14 | 1 | 297 | 1/1 · 191 | 1/1 · 57 | 1/1 · 57 | 1/1 · 56 | 1/1 · 56 | 1/1 · 66 | 1/1 · 60 | 1/1 · 138 |
| Csv-10 | 1 | 1 | 194 | 1/1 · 43 | 0/1 · 0 | 0/1 · 0 | 1/1 · 66 | 1/1 · 66 | 1/1 · 43 | 0/1 · 2 | 1/1 · 151 |
| Csv-11 | 1 | 1 | 201 | 1/1 · 68 | 0/1 · 0 | 0/1 · 0 | 0/1 · 56 | 0/1 · 56 | 1/1 · 63 | 0/1 · 49 | 1/1 · 160 |
| Csv-12 | 39 | 1 | 200 | 1/1 · 174 | 1/1 · 174 | 1/1 · 174 | 1/1 · 183 | 1/1 · 183 | 1/1 · 166 | 1/1 · 138 | 1/1 · 185 |
| Csv-13 | 46 | 2 | 228 | 2/2 · 202 | 2/2 · 205 | 2/2 · 205 | 2/2 · 217 | 2/2 · 217 | 2/2 · 194 | 1/2 · 165 | 2/2 · 212 |
| Csv-14 | 1 | 6 | 256 | 6/6 · 79 | 0/6 · 62 | 0/6 · 62 | 0/6 · 0 | 0/6 · 0 | 0/6 · 11 | 0/6 · 4 | 6/6 · 242 |
| Csv-15 | 1 | 1 | 294 | 1/1 · 102 | 0/1 · 70 | 0/1 · 70 | 0/1 · 0 | 0/1 · 0 | 1/1 · 60 | 0/1 · 4 | 1/1 · 279 |
| Csv-16 | 15 | 1 | 298 | 1/1 · 101 | 1/1 · 82 | 1/1 · 82 | 1/1 · 104 | 1/1 · 104 | 1/1 · 80 | 1/1 · 73 | 1/1 · 149 |
| Csv-6 | 1 | 1 | 188 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 109 |
| Csv-7 | 1 | 1 | 189 | 1/1 · 63 | 0/1 · 0 | 0/1 · 0 | 1/1 · 55 | 1/1 · 55 | 1/1 · 51 | 1/1 · 48 | 1/1 · 148 |
| Csv-8 | 2 | 1 | 191 | 1/1 · 163 | 1/1 · 113 | 1/1 · 113 | 1/1 · 172 | 1/1 · 172 | 1/1 · 151 | 0/1 · 63 | 1/1 · 176 |
| Csv-9 | 1 | 1 | 192 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 111 |
| Gson-10 | 1 | 1 | 996 | 1/1 · 410 | 0/1 · 0 | 0/1 · 0 | 0/1 · 11 | 0/1 · 11 | 0/1 · 12 | 0/1 · 0 | 1/1 · 690 |
| Gson-11 | 1 | 1 | 1005 | 1/1 · 530 | 0/1 · 1 | 0/1 · 1 | 0/1 · 3 | 0/1 · 3 | 0/1 · 64 | 1/1 · 368 | 1/1 · 771 |
| Gson-12 | 1 | 2 | 1008 | 2/2 · 532 | 0/2 · 1 | 0/2 · 1 | 2/2 · 38 | 2/2 · 38 | 2/2 · 104 | 2/2 · 408 | 2/2 · 774 |
| Gson-13 | 1 | 1 | 1009 | 1/1 · 533 | 0/1 · 1 | 0/1 · 1 | 1/1 · 504 | 1/1 · 504 | 1/1 · 227 | 1/1 · 509 | 1/1 · 894 |
| Gson-14 | 2 | 7 | 1017 | 7/7 · 855 | 4/7 · 4 | 7/7 · 17 | 0/7 · 0 | 0/7 · 0 | 4/7 · 73 | 0/7 · 0 | 7/7 · 723 |
| Gson-15 | 1 | 1 | 1019 | 1/1 · 442 | 0/1 · 0 | 0/1 · 0 | 1/1 · 45 | 1/1 · 45 | 0/1 · 29 | 1/1 · 31 | 1/1 · 828 |
| Gson-16 | 1 | 2 | 1021 | 2/2 · 861 | 0/2 · 0 | 2/2 · 15 | 0/2 · 0 | 0/2 · 0 | 0/2 · 74 | 0/2 · 0 | 2/2 · 725 |
| Gson-17 | 1 | 2 | 1023 | 2/2 · 539 | 0/2 · 1 | 0/2 · 1 | 2/2 · 16 | 2/2 · 16 | 2/2 · 60 | 0/2 · 368 | 2/2 · 590 |
| Gson-18 | 1 | 1 | 1025 | 1/1 · 864 | 0/1 · 0 | 0/1 · 15 | 0/1 · 0 | 0/1 · 0 | 0/1 · 76 | 0/1 · 0 | 1/1 · 727 |
| Gson-6 | 1 | 2 | 986 | 2/2 · 833 | 0/2 · 0 | 0/2 · 10 | 0/2 · 0 | 0/2 · 0 | 0/2 · 72 | 0/2 · 0 | 2/2 · 684 |
| Gson-7 | 2 | 3 | 989 | 3/3 · 523 | 0/3 · 1 | 0/3 · 1 | 1/3 · 21 | 1/3 · 21 | 3/3 · 82 | 1/3 · 18 | 3/3 · 880 |
| Gson-8 | 4 | 2 | 992 | 2/2 · 839 | 0/2 · 0 | 0/2 · 0 | 2/2 · 6 | 2/2 · 6 | 2/2 · 67 | 2/2 · 3 | 2/2 · 442 |
| Gson-9 | 3 | 1 | 993 | 1/1 · 431 | 0/1 · 0 | 0/1 · 0 | 1/1 · 43 | 1/1 · 43 | 0/1 · 26 | 1/1 · 34 | 1/1 · 789 |
| JacksonCore-10 | 2 | 4 | 332 | 4/4 · 212 | 0/4 · 0 | 0/4 · 0 | 4/4 · 202 | 4/4 · 202 | 1/4 · 205 | 4/4 · 215 | 4/4 · 292 |
| JacksonCore-11 | 1 | 1 | 337 | 1/1 · 217 | 0/1 · 0 | 0/1 · 0 | 1/1 · 207 | 1/1 · 207 | 0/1 · 0 | 1/1 · 220 | 1/1 · 297 |
| JacksonCore-12 | 6 | 1 | 346 | 1/1 · 221 | 0/1 · 0 | 0/1 · 0 | 1/1 · 211 | 1/1 · 211 | 1/1 · 220 | 1/1 · 224 | 1/1 · 305 |
| JacksonCore-13 | 12 | 1 | 348 | 1/1 · 127 | 0/1 · 0 | 0/1 · 0 | 1/1 · 112 | 1/1 · 112 | 1/1 · 18 | 1/1 · 13 | 1/1 · 311 |
| JacksonCore-14 | 2 | 1 | 348 | 1/1 · 285 | 1/1 · 3 | 1/1 · 3 | 1/1 · 277 | 1/1 · 277 | 0/1 · 0 | 1/1 · 219 | 1/1 · 311 |
| JacksonCore-15 | 1 | 1 | 350 | 1/1 · 223 | 0/1 · 0 | 0/1 · 0 | 1/1 · 218 | 1/1 · 218 | 1/1 · 222 | 1/1 · 226 | 1/1 · 14 |
| JacksonCore-16 | 8 | 1 | 381 | 1/1 · 250 | 1/1 · 2 | 1/1 · 2 | 1/1 · 244 | 1/1 · 244 | 1/1 · 249 | 1/1 · 250 | 1/1 · 2 |
| JacksonCore-17 | 3 | 1 | 355 | 1/1 · 131 | 0/1 · 9 | 0/1 · 9 | 1/1 · 279 | 1/1 · 279 | 1/1 · 12 | 0/1 · 83 | 1/1 · 318 |
| JacksonCore-18 | 32 | 1 | 359 | 1/1 · 293 | 0/1 · 13 | 0/1 · 13 | 1/1 · 280 | 1/1 · 280 | 1/1 · 287 | 1/1 · 289 | 1/1 · 322 |
| JacksonCore-19 | 2 | 1 | 360 | 1/1 · 229 | 0/1 · 0 | 0/1 · 0 | 1/1 · 216 | 1/1 · 216 | 1/1 · 228 | 1/1 · 232 | 1/1 · 318 |
| JacksonCore-20 | 1 | 2 | 388 | 2/2 · 2 | 0/2 · 0 | 0/2 · 0 | 2/2 · 2 | 2/2 · 2 | 2/2 · 2 | 2/2 · 2 | 2/2 · 384 |
| JacksonCore-21 | 1 | 3 | 448 | 3/3 · 288 | 0/3 · 0 | 0/3 · 0 | 3/3 · 281 | 3/3 · 281 | 3/3 · 286 | 3/3 · 289 | 3/3 · 16 |
| JacksonCore-22 | 4 | 12 | 514 | 12/12 · 353 | 0/12 · 0 | 0/12 · 0 | 12/12 · 291 | 12/12 · 291 | 12/12 · 351 | 12/12 · 296 | 12/12 · 20 |
| JacksonCore-23 | 1 | 1 | 607 | 1/1 · 1 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1 | 1/1 · 1 | 1/1 · 549 |
| JacksonCore-24 | 4 | 8 | 609 | 8/8 · 168 | 0/8 · 0 | 0/8 · 0 | 8/8 · 163 | 8/8 · 164 | 8/8 · 168 | 8/8 · 167 | 8/8 · 549 |
| JacksonCore-25 | 1 | 1 | 602 | 1/1 · 404 | 0/1 · 0 | 0/1 · 0 | 1/1 · 304 | 1/1 · 304 | 1/1 · 402 | 1/1 · 314 | 1/1 · 542 |
| JacksonCore-26 | 1 | 1 | 614 | 1/1 · 87 | 0/1 · 0 | 0/1 · 0 | 1/1 · 87 | 1/1 · 87 | 1/1 · 87 | 1/1 · 89 | 1/1 · 554 |
| JacksonCore-6 | 1 | 1 | 245 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 |
| JacksonCore-7 | 1 | 2 | 265 | 2/2 · 82 | 0/2 · 1 | 0/2 · 1 | 2/2 · 61 | 2/2 · 61 | 0/2 · 0 | 0/2 · 0 | 2/2 · 117 |
| JacksonCore-8 | 1 | 1 | 271 | 1/1 · 165 | 1/1 · 1 | 1/1 · 1 | 1/1 · 159 | 1/1 · 159 | 1/1 · 165 | 1/1 · 168 | 1/1 · 213 |
| JacksonCore-9 | 3 | 2 | 281 | 2/2 · 2 | 0/2 · 0 | 0/2 · 0 | 2/2 · 2 | 2/2 · 2 | 2/2 · 2 | 2/2 · 2 | 2/2 · 246 |
| JacksonDatabind-10 | 6 | 1 | 1367 | 1/1 · 1248 | 0/1 · 0 | 0/1 · 0 | 0/1 · 5 | 0/1 · 5 | 0/1 · 41 | 0/1 · 5 | 1/1 · 1335 |
| JacksonDatabind-100 | 1 | 1 | 2174 | 1/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1 | 1/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2027 |
| JacksonDatabind-101 | 1 | 1 | 2175 | 1/1 · 1942 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1464 | 1/1 · 1464 | 0/1 · 149 | 1/1 · 1173 | 1/1 · 2027 |
| JacksonDatabind-102 | 1 | 1 | 2176 | 1/1 · 1943 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 115 | 0/1 · 0 | 1/1 · 2028 |
| JacksonDatabind-103 | 21 | 1 | 2177 | 1/1 · 1944 | 0/1 · 42 | 0/1 · 42 | 1/1 · 1857 | 1/1 · 1857 | 0/1 · 1016 | 1/1 · 1750 | 1/1 · 2095 |
| JacksonDatabind-104 | 3 | 2 | 2183 | 0/2 · 0 | 0/2 · 0 | 0/2 · 21 | 0/2 · 0 | 0/2 · 0 | 0/2 · 231 | 0/2 · 0 | 2/2 · 2045 |
| JacksonDatabind-105 | 3 | 1 | 2185 | 1/1 · 1952 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1475 | 1/1 · 1475 | 0/1 · 229 | 1/1 · 1315 | 1/1 · 1325 |
| JacksonDatabind-106 | 2 | 2 | 2188 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 1 | 0/2 · 1 | 0/2 · 0 | 0/2 · 0 | 2/2 · 2040 |
| JacksonDatabind-107 | 1 | 1 | 2187 | 1/1 · 1954 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1477 | 1/1 · 1477 | 0/1 · 150 | 1/1 · 1178 | 1/1 · 475 |
| JacksonDatabind-108 | 2 | 1 | 2194 | 1/1 · 1963 | 0/1 · 0 | 0/1 · 0 | 0/1 · 7 | 0/1 · 7 | 0/1 · 9 | 0/1 · 7 | 1/1 · 2135 |
| JacksonDatabind-109 | 14 | 1 | 2198 | 1/1 · 1967 | 0/1 · 0 | 0/1 · 0 | 0/1 · 62 | 0/1 · 62 | 0/1 · 140 | 0/1 · 59 | 1/1 · 2049 |
| JacksonDatabind-11 | 1 | 2 | 1369 | 2/2 · 1277 | 0/2 · 38 | 0/2 · 119 | 2/2 · 883 | 2/2 · 883 | 1/2 · 607 | 2/2 · 872 | 2/2 · 1339 |
| JacksonDatabind-110 | 5 | 1 | 2191 | 1/1 · 1958 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1481 | 1/1 · 1481 | 0/1 · 229 | 1/1 · 1321 | 1/1 · 217 |
| JacksonDatabind-111 | 7 | 1 | 2192 | 1/1 · 1959 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1482 | 1/1 · 1482 | 1/1 · 230 | 1/1 · 1322 | 1/1 · 2043 |
| JacksonDatabind-112 | 1 | 1 | 2194 | 1/1 · 1961 | 0/1 · 0 | 0/1 · 21 | 0/1 · 0 | 0/1 · 0 | 1/1 · 232 | 0/1 · 0 | 1/1 · 2044 |
| JacksonDatabind-12 | 1 | 1 | 1274 | 1/1 · 1164 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 730 | 1/1 · 1229 |
| JacksonDatabind-13 | 2 | 1 | 1377 | 1/1 · 1257 | 0/1 · 0 | 0/1 · 0 | 1/1 · 735 | 1/1 · 735 | 0/1 · 57 | 1/1 · 765 | 1/1 · 1346 |
| JacksonDatabind-14 | 2 | 1 | 1378 | 1/1 · 1258 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1336 |
| JacksonDatabind-15 | 10 | 1 | 1379 | 1/1 · 1259 | 0/1 · 0 | 0/1 · 0 | 0/1 · 5 | 0/1 · 5 | 0/1 · 41 | 0/1 · 5 | 1/1 · 1348 |
| JacksonDatabind-16 | 1 | 1 | 1389 | 1/1 · 1270 | 0/1 · 0 | 0/1 · 0 | 0/1 · 838 | 0/1 · 838 | 1/1 · 1389 | 0/1 · 0 | 1/1 · 1355 |
| JacksonDatabind-17 | 1 | 1 | 1280 | 1/1 · 1168 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 581 | 1/1 · 734 | 1/1 · 1236 |
| JacksonDatabind-18 | 17 | 3 | 1439 | 3/3 · 1313 | 3/3 · 3 | 3/3 · 3 | 3/3 · 1092 | 3/3 · 1092 | 3/3 · 13 | 3/3 · 7 | 3/3 · 26 |
| JacksonDatabind-19 | 1 | 3 | 1443 | 3/3 · 1347 | 0/3 · 39 | 0/3 · 131 | 3/3 · 933 | 3/3 · 933 | 0/3 · 694 | 3/3 · 922 | 3/3 · 1416 |
| JacksonDatabind-20 | 39 | 1 | 1396 | 1/1 · 1299 | 0/1 · 106 | 0/1 · 189 | 1/1 · 955 | 1/1 · 955 | 1/1 · 125 | 1/1 · 827 | 1/1 · 1360 |
| JacksonDatabind-21 | 74 | 1 | 1453 | 1/1 · 1331 | 0/1 · 13 | 0/1 · 13 | 1/1 · 880 | 1/1 · 880 | 1/1 · 1452 | 1/1 · 877 | 1/1 · 1419 |
| JacksonDatabind-22 | 5 | 1 | 1463 | 1/1 · 1336 | 0/1 · 0 | 0/1 · 0 | 0/1 · 37 | 0/1 · 37 | 0/1 · 0 | 0/1 · 37 | 1/1 · 1433 |
| JacksonDatabind-23 | 31 | 1 | 1474 | 1/1 · 1338 | 0/1 · 0 | 0/1 · 13 | 0/1 · 37 | 0/1 · 37 | 0/1 · 96 | 0/1 · 37 | 1/1 · 1444 |
| JacksonDatabind-24 | 1 | 1 | 1484 | 1/1 · 1152 | 0/1 · 0 | 0/1 · 0 | 1/1 · 754 | 1/1 · 754 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1454 |
| JacksonDatabind-25 | 4 | 1 | 1485 | 1/1 · 1348 | 0/1 · 14 | 0/1 · 16 | 1/1 · 898 | 1/1 · 898 | 0/1 · 115 | 1/1 · 865 | 1/1 · 1455 |
| JacksonDatabind-26 | 47 | 1 | 1486 | 1/1 · 1349 | 0/1 · 29 | 0/1 · 29 | 1/1 · 808 | 1/1 · 808 | 1/1 · 198 | 1/1 · 846 | 1/1 · 1456 |
| JacksonDatabind-27 | 1 | 1 | 1487 | 1/1 · 1350 | 0/1 · 0 | 0/1 · 0 | 1/1 · 772 | 1/1 · 772 | 0/1 · 89 | 1/1 · 816 | 1/1 · 1457 |
| JacksonDatabind-28 | 1 | 1 | 1492 | 1/1 · 1355 | 0/1 · 0 | 0/1 · 0 | 1/1 · 776 | 1/1 · 776 | 0/1 · 89 | 1/1 · 820 | 1/1 · 164 |
| JacksonDatabind-29 | 2 | 1 | 1499 | 1/1 · 1362 | 0/1 · 0 | 0/1 · 0 | 1/1 · 781 | 1/1 · 781 | 0/1 · 90 | 1/1 · 826 | 1/1 · 33 |
| JacksonDatabind-30 | 52 | 1 | 1500 | 1/1 · 1368 | 0/1 · 28 | 0/1 · 128 | 1/1 · 1170 | 1/1 · 1170 | 0/1 · 111 | 0/1 · 866 | 1/1 · 1469 |
| JacksonDatabind-31 | 8 | 1 | 1502 | 1/1 · 1369 | 0/1 · 14 | 0/1 · 14 | 1/1 · 791 | 1/1 · 791 | 1/1 · 108 | 1/1 · 836 | 1/1 · 1471 |
| JacksonDatabind-32 | 2 | 1 | 1503 | 1/1 · 1365 | 0/1 · 0 | 0/1 · 0 | 0/1 · 783 | 0/1 · 783 | 1/1 · 91 | 1/1 · 829 | 1/1 · 1472 |
| JacksonDatabind-33 | 1 | 1 | 1506 | 1/1 · 1367 | 0/1 · 0 | 0/1 · 0 | 0/1 · 934 | 0/1 · 934 | 0/1 · 218 | 0/1 · 931 | 1/1 · 1475 |
| JacksonDatabind-34 | 1 | 1 | 1542 | 1/1 · 14 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 8 | 0/1 · 0 | 1/1 · 1509 |
| JacksonDatabind-35 | 1 | 1 | 1400 | 1/1 · 1278 | 0/1 · 0 | 0/1 · 0 | 1/1 · 747 | 1/1 · 747 | 0/1 · 60 | 1/1 · 778 | 1/1 · 277 |
| JacksonDatabind-36 | 21 | 1 | 1545 | 1/1 · 1446 | 1/1 · 16 | 1/1 · 263 | 1/1 · 823 | 1/1 · 823 | 1/1 · 206 | 1/1 · 3 | 1/1 · 1512 |
| JacksonDatabind-37 | 1 | 1 | 1551 | 1/1 · 1408 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 119 | 0/1 · 0 | 1/1 · 1518 |
| JacksonDatabind-38 | 4 | 3 | 1556 | 3/3 · 4 | 0/3 · 16 | 0/3 · 27 | 3/3 · 4 | 3/3 · 4 | 3/3 · 758 | 3/3 · 1029 | 3/3 · 1522 |
| JacksonDatabind-39 | 1 | 1 | 1514 | 1/1 · 1374 | 0/1 · 0 | 0/1 · 0 | 0/1 · 787 | 0/1 · 787 | 1/1 · 92 | 1/1 · 834 | 1/1 · 235 |
| JacksonDatabind-40 | 4 | 1 | 1559 | 1/1 · 1416 | 0/1 · 0 | 0/1 · 0 | 0/1 · 819 | 0/1 · 819 | 1/1 · 96 | 1/1 · 867 | 1/1 · 1007 |
| JacksonDatabind-41 | 1 | 1 | 1561 | 1/1 · 1418 | 0/1 · 18 | 0/1 · 18 | 0/1 · 0 | 0/1 · 0 | 1/1 · 758 | 1/1 · 1032 | 1/1 · 1527 |
| JacksonDatabind-42 | 1 | 1 | 1515 | 1/1 · 1375 | 0/1 · 0 | 0/1 · 0 | 1/1 · 788 | 1/1 · 788 | 0/1 · 92 | 1/1 · 835 | 1/1 · 1081 |
| JacksonDatabind-43 | 1 | 1 | 1568 | 1/1 · 1423 | 0/1 · 0 | 0/1 · 0 | 1/1 · 825 | 1/1 · 825 | 0/1 · 96 | 1/1 · 873 | 1/1 · 954 |
| JacksonDatabind-44 | 1 | 1 | 1568 | 1/1 · 1423 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 123 | 0/1 · 0 | 1/1 · 1532 |
| JacksonDatabind-45 | 1 | 1 | 1569 | 1/1 · 1424 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 98 | 0/1 · 0 | 1/1 · 1533 |
| JacksonDatabind-46 | 1 | 1 | 1517 | 1/1 · 1 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1482 |
| JacksonDatabind-47 | 1 | 2 | 1591 | 2/2 · 1445 | 0/2 · 0 | 0/2 · 0 | 1/2 · 41 | 1/2 · 41 | 0/2 · 0 | 1/2 · 41 | 2/2 · 1551 |
| JacksonDatabind-48 | 2 | 1 | 1592 | 1/1 · 1448 | 0/1 · 0 | 0/1 · 0 | 0/1 · 957 | 0/1 · 957 | 0/1 · 143 | 0/1 · 955 | 1/1 · 1552 |
| JacksonDatabind-49 | 1 | 1 | 1519 | 1/1 · 1378 | 0/1 · 0 | 0/1 · 0 | 0/1 · 39 | 0/1 · 39 | 0/1 · 4 | 0/1 · 39 | 1/1 · 45 |
| JacksonDatabind-50 | 6 | 1 | 1646 | 1/1 · 1496 | 0/1 · 0 | 0/1 · 0 | 1/1 · 881 | 1/1 · 881 | 1/1 · 102 | 1/1 · 930 | 1/1 · 1556 |
| JacksonDatabind-51 | 1 | 1 | 1648 | 1/1 · 1498 | 0/1 · 0 | 0/1 · 0 | 1/1 · 883 | 1/1 · 883 | 1/1 · 103 | 1/1 · 932 | 1/1 · 341 |
| JacksonDatabind-52 | 2 | 1 | 1648 | 1/1 · 1498 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 130 | 0/1 · 0 | 1/1 · 1559 |
| JacksonDatabind-53 | 56 | 1 | 1594 | 1/1 · 1524 | 0/1 · 77 | 0/1 · 77 | 1/1 · 1263 | 1/1 · 1263 | 1/1 · 1593 | 1/1 · 1176 | 1/1 · 1554 |
| JacksonDatabind-54 | 1 | 1 | 1652 | 1/1 · 1501 | 0/1 · 0 | 0/1 · 0 | 0/1 · 1102 | 0/1 · 1102 | 0/1 · 0 | 0/1 · 42 | 1/1 · 956 |
| JacksonDatabind-55 | 5 | 1 | 1600 | 1/1 · 1453 | 0/1 · 0 | 0/1 · 0 | 0/1 · 42 | 0/1 · 42 | 0/1 · 101 | 0/1 · 41 | 1/1 · 358 |
| JacksonDatabind-56 | 2 | 1 | 1601 | 1/1 · 1454 | 0/1 · 0 | 0/1 · 0 | 1/1 · 842 | 1/1 · 842 | 0/1 · 97 | 1/1 · 890 | 1/1 · 1146 |
| JacksonDatabind-57 | 1 | 1 | 1601 | 1/1 · 15 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 15 | 1/1 · 3 | 1/1 · 1549 |
| JacksonDatabind-58 | 1 | 1 | 1602 | 1/1 · 1455 | 0/1 · 0 | 0/1 · 0 | 1/1 · 946 | 1/1 · 946 | 0/1 · 124 | 1/1 · 944 | 1/1 · 1561 |
| JacksonDatabind-59 | 56 | 1 | 1681 | 1/1 · 1574 | 0/1 · 44 | 0/1 · 57 | 1/1 · 1159 | 1/1 · 1159 | 1/1 · 860 | 1/1 · 1155 | 1/1 · 1640 |
| JacksonDatabind-6 | 1 | 2 | 1266 | 2/2 · 1158 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 1 | 0/2 · 1 | 2/2 · 1221 |
| JacksonDatabind-60 | 19 | 2 | 1683 | 2/2 · 1529 | 0/2 · 15 | 0/2 · 15 | 2/2 · 1126 | 2/2 · 1126 | 2/2 · 692 | 0/2 · 42 | 2/2 · 1590 |
| JacksonDatabind-61 | 3 | 1 | 1684 | 1/1 · 1530 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 789 | 1/1 · 1034 | 1/1 · 1643 |
| JacksonDatabind-62 | 1 | 1 | 1606 | 1/1 · 1459 | 0/1 · 14 | 0/1 · 14 | 0/1 · 0 | 0/1 · 0 | 0/1 · 125 | 0/1 · 0 | 1/1 · 1565 |
| JacksonDatabind-63 | 1 | 3 | 1688 | 1/3 · 1 | 2/3 · 2 | 2/3 · 2 | 1/3 · 1 | 1/3 · 1 | 0/3 · 0 | 1/3 · 1 | 3/3 · 1600 |
| JacksonDatabind-64 | 1 | 1 | 1688 | 1/1 · 1534 | 0/1 · 0 | 0/1 · 0 | 0/1 · 1130 | 0/1 · 1130 | 0/1 · 0 | 0/1 · 42 | 1/1 · 972 |
| JacksonDatabind-66 | 1 | 1 | 1705 | 1/1 · 1551 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1145 | 1/1 · 1145 | 0/1 · 107 | 1/1 · 960 | 1/1 · 1615 |
| JacksonDatabind-67 | 1 | 1 | 1706 | 1/1 · 1552 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 140 | 0/1 · 0 | 1/1 · 1616 |
| JacksonDatabind-68 | 7 | 2 | 1708 | 2/2 · 1554 | 0/2 · 0 | 0/2 · 0 | 2/2 · 1148 | 2/2 · 1148 | 0/2 · 107 | 2/2 · 963 | 2/2 · 1618 |
| JacksonDatabind-69 | 3 | 1 | 1610 | 1/1 · 1462 | 0/1 · 0 | 0/1 · 0 | 1/1 · 952 | 1/1 · 952 | 0/1 · 126 | 1/1 · 950 | 1/1 · 1160 |
| JacksonDatabind-7 | 1 | 1 | 1267 | 1/1 · 1159 | 0/1 · 7 | 0/1 · 7 | 0/1 · 0 | 0/1 · 0 | 0/1 · 59 | 0/1 · 0 | 1/1 · 1222 |
| JacksonDatabind-70 | 1 | 1 | 1718 | 1/1 · 1563 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 142 | 0/1 · 0 | 1/1 · 1061 |
| JacksonDatabind-71 | 1 | 1 | 1611 | 1/1 · 1463 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 126 | 0/1 · 0 | 1/1 · 1570 |
| JacksonDatabind-72 | 15 | 1 | 1612 | 1/1 · 1464 | 0/1 · 14 | 0/1 · 14 | 1/1 · 1009 | 1/1 · 1009 | 0/1 · 213 | 1/1 · 986 | 1/1 · 980 |
| JacksonDatabind-73 | 2 | 2 | 1723 | 2/2 · 1568 | 0/2 · 12 | 0/2 · 12 | 2/2 · 1162 | 2/2 · 1162 | 0/2 · 251 | 2/2 · 1086 | 2/2 · 1613 |
| JacksonDatabind-74 | 1 | 1 | 1730 | 1/1 · 1575 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1168 | 1/1 · 1168 | 0/1 · 109 | 1/1 · 975 | 1/1 · 373 |
| JacksonDatabind-75 | 3 | 1 | 1733 | 1/1 · 1578 | 0/1 · 0 | 0/1 · 0 | 0/1 · 1168 | 0/1 · 1168 | 0/1 · 105 | 0/1 · 48 | 1/1 · 1646 |
| JacksonDatabind-76 | 1 | 4 | 1746 | 4/4 · 1591 | 0/4 · 0 | 0/4 · 0 | 4/4 · 1180 | 4/4 · 1180 | 0/4 · 116 | 4/4 · 980 | 4/4 · 1083 |
| JacksonDatabind-77 | 2 | 1 | 1617 | 1/1 · 1469 | 0/1 · 0 | 0/1 · 0 | 1/1 · 959 | 1/1 · 959 | 0/1 · 126 | 1/1 · 957 | 1/1 · 1573 |
| JacksonDatabind-78 | 22 | 1 | 1756 | 1/1 · 1597 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1186 | 1/1 · 1186 | 0/1 · 154 | 1/1 · 1051 | 1/1 · 1662 |
| JacksonDatabind-79 | 12 | 1 | 1618 | 1/1 · 1472 | 0/1 · 14 | 0/1 · 15 | 0/1 · 994 | 0/1 · 994 | 1/1 · 1617 | 0/1 · 991 | 1/1 · 1574 |
| JacksonDatabind-8 | 1 | 1 | 1359 | 1/1 · 1241 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 76 | 1/1 · 799 | 1/1 · 982 |
| JacksonDatabind-80 | 2 | 1 | 2019 | 1/1 · 1799 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 942 | 0/1 · 0 | 1/1 · 1882 |
| JacksonDatabind-81 | 3 | 1 | 2020 | 1/1 · 1799 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1339 | 1/1 · 1339 | 0/1 · 203 | 1/1 · 1241 | 1/1 · 1883 |
| JacksonDatabind-82 | 1 | 1 | 1764 | 1/1 · 1605 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1190 | 1/1 · 1190 | 0/1 · 154 | 1/1 · 1055 | 1/1 · 1668 |
| JacksonDatabind-83 | 1 | 1 | 1765 | 1/1 · 1606 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1191 | 1/1 · 1191 | 0/1 · 116 | 1/1 · 991 | 1/1 · 1270 |
| JacksonDatabind-84 | 18 | 1 | 1766 | 1/1 · 1659 | 0/1 · 50 | 0/1 · 63 | 1/1 · 1231 | 1/1 · 1231 | 0/1 · 897 | 1/1 · 1227 | 1/1 · 1687 |
| JacksonDatabind-85 | 1 | 1 | 1766 | 1/1 · 1607 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 106 | 0/1 · 0 | 1/1 · 1670 |
| JacksonDatabind-86 | 18 | 2 | 1768 | 2/2 · 1661 | 0/2 · 50 | 0/2 · 63 | 2/2 · 1232 | 2/2 · 1232 | 1/2 · 899 | 2/2 · 1228 | 2/2 · 1689 |
| JacksonDatabind-87 | 23 | 1 | 1769 | 1/1 · 1687 | 0/1 · 18 | 0/1 · 298 | 1/1 · 1208 | 1/1 · 1208 | 1/1 · 249 | 0/1 · 3 | 1/1 · 1681 |
| JacksonDatabind-88 | 1 | 1 | 1784 | 1/1 · 1624 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1212 | 1/1 · 1212 | 0/1 · 117 | 0/1 · 0 | 1/1 · 247 |
| JacksonDatabind-9 | 1 | 1 | 1361 | 1/1 · 1243 | 0/1 · 0 | 0/1 · 0 | 0/1 · 5 | 0/1 · 5 | 0/1 · 4 | 0/1 · 5 | 1/1 · 316 |
| JacksonDatabind-90 | 45 | 1 | 1797 | 1/1 · 1632 | 0/1 · 16 | 0/1 · 17 | 1/1 · 1223 | 1/1 · 1223 | 0/1 · 156 | 1/1 · 1079 | 1/1 · 1695 |
| JacksonDatabind-91 | 1 | 1 | 1798 | 1/1 · 1633 | 0/1 · 20 | 0/1 · 21 | 1/1 · 1224 | 1/1 · 1224 | 0/1 · 156 | 1/1 · 1080 | 1/1 · 1696 |
| JacksonDatabind-92 | 22 | 1 | 1621 | 1/1 · 1473 | 0/1 · 0 | 0/1 · 0 | 1/1 · 962 | 1/1 · 962 | 0/1 · 126 | 1/1 · 960 | 1/1 · 1577 |
| JacksonDatabind-93 | 1 | 1 | 1800 | 1/1 · 1635 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1226 | 1/1 · 1226 | 0/1 · 156 | 0/1 · 0 | 1/1 · 1091 |
| JacksonDatabind-94 | 4 | 1 | 1624 | 1/1 · 1476 | 0/1 · 0 | 0/1 · 0 | 1/1 · 965 | 1/1 · 965 | 0/1 · 126 | 1/1 · 963 | 1/1 · 978 |
| JacksonDatabind-95 | 3 | 1 | 1811 | 1/1 · 1658 | 0/1 · 7 | 0/1 · 7 | 1/1 · 1237 | 1/1 · 1237 | 1/1 · 170 | 1/1 · 1145 | 1/1 · 1757 |
| JacksonDatabind-96 | 1 | 1 | 2167 | 1/1 · 1933 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1457 | 1/1 · 1457 | 0/1 · 225 | 1/1 · 1303 | 1/1 · 2023 |
| JacksonDatabind-97 | 1 | 1 | 2168 | 1/1 · 1934 | 0/1 · 0 | 0/1 · 0 | 0/1 · 51 | 0/1 · 51 | 0/1 · 3 | 0/1 · 51 | 1/1 · 2024 |
| JacksonDatabind-98 | 1 | 1 | 2171 | 1/1 · 1937 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 149 | 0/1 · 1169 | 1/1 · 52 |
| JacksonDatabind-99 | 1 | 1 | 1811 | 1/1 · 1704 | 1/1 · 49 | 1/1 · 50 | 1/1 · 1237 | 1/1 · 1237 | 0/1 · 164 | 0/1 · 1135 | 1/1 · 1722 |
| JacksonXml-6 | 50 | 5 | 209 | 0/5 · 17 | 0/5 · 18 | 0/5 · 18 | 0/5 · 12 | 0/5 · 12 | 0/5 · 12 | 0/5 · 12 | 5/5 · 179 |
| Jsoup-10 | 1 | 1 | 237 | 1/1 · 194 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 191 | 0/1 · 0 | 1/1 · 196 |
| Jsoup-11 | 4 | 4 | 240 | 4/4 · 121 | 0/4 · 0 | 0/4 · 0 | 3/4 · 56 | 3/4 · 56 | 0/4 · 0 | 0/4 · 2 | 4/4 · 172 |
| Jsoup-12 | 2 | 1 | 304 | 1/1 · 126 | 0/1 · 0 | 0/1 · 0 | 1/1 · 75 | 1/1 · 75 | 0/1 · 0 | 0/1 · 3 | 1/1 · 174 |
| Jsoup-13 | 1 | 4 | 280 | 4/4 · 236 | 0/4 · 0 | 0/4 · 0 | 0/4 · 0 | 0/4 · 0 | 4/4 · 231 | 0/4 · 0 | 4/4 · 239 |
| Jsoup-14 | 2 | 2 | 286 | 2/2 · 239 | 0/2 · 0 | 0/2 · 0 | 2/2 · 236 | 2/2 · 236 | 2/2 · 234 | 0/2 · 0 | 2/2 · 227 |
| Jsoup-15 | 1 | 1 | 291 | 1/1 · 244 | 0/1 · 0 | 0/1 · 0 | 1/1 · 241 | 1/1 · 241 | 1/1 · 239 | 0/1 · 0 | 1/1 · 232 |
| Jsoup-16 | 2 | 2 | 301 | 2/2 · 251 | 0/2 · 43 | 0/2 · 47 | 2/2 · 4 | 2/2 · 4 | 2/2 · 246 | 0/2 · 0 | 2/2 · 239 |
| Jsoup-17 | 6 | 1 | 303 | 1/1 · 250 | 0/1 · 47 | 0/1 · 49 | 1/1 · 250 | 1/1 · 250 | 1/1 · 245 | 0/1 · 0 | 1/1 · 237 |
| Jsoup-18 | 2 | 3 | 306 | 3/3 · 256 | 0/3 · 0 | 0/3 · 0 | 3/3 · 252 | 3/3 · 252 | 3/3 · 251 | 3/3 · 240 | 3/3 · 243 |
| Jsoup-19 | 1 | 1 | 312 | 1/1 · 17 | 0/1 · 0 | 0/1 · 0 | 1/1 · 17 | 1/1 · 17 | 1/1 · 17 | 1/1 · 17 | 1/1 · 17 |
| Jsoup-20 | 1 | 1 | 333 | 1/1 · 37 | 1/1 · 1 | 1/1 · 3 | 1/1 · 247 | 1/1 · 247 | 1/1 · 233 | 1/1 · 237 | 1/1 · 20 |
| Jsoup-21 | 3 | 2 | 335 | 2/2 · 175 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 2 | 2/2 · 246 |
| Jsoup-22 | 6 | 3 | 340 | 3/3 · 281 | 3/3 · 18 | 3/3 · 18 | 3/3 · 168 | 3/3 · 168 | 3/3 · 275 | 2/3 · 26 | 3/3 · 306 |
| Jsoup-23 | 2 | 1 | 341 | 1/1 · 281 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 275 | 0/1 · 0 | 1/1 · 280 |
| Jsoup-24 | 1 | 1 | 342 | 1/1 · 282 | 0/1 · 0 | 0/1 · 0 | 1/1 · 28 | 1/1 · 28 | 1/1 · 276 | 0/1 · 0 | 1/1 · 276 |
| Jsoup-25 | 18 | 1 | 347 | 1/1 · 300 | 0/1 · 24 | 0/1 · 59 | 1/1 · 144 | 1/1 · 164 | 1/1 · 297 | 0/1 · 0 | 1/1 · 296 |
| Jsoup-26 | 1 | 1 | 361 | 1/1 · 20 | 0/1 · 0 | 0/1 · 0 | 1/1 · 20 | 1/1 · 20 | 1/1 · 20 | 1/1 · 20 | 1/1 · 21 |
| Jsoup-27 | 1 | 2 | 363 | 2/2 · 42 | 2/2 · 3 | 2/2 · 5 | 2/2 · 260 | 2/2 · 260 | 2/2 · 258 | 2/2 · 254 | 2/2 · 20 |
| Jsoup-28 | 5 | 6 | 366 | 6/6 · 299 | 0/6 · 0 | 0/6 · 0 | 0/6 · 0 | 0/6 · 0 | 6/6 · 292 | 2/6 · 5 | 6/6 · 316 |
| Jsoup-29 | 1 | 1 | 368 | 1/1 · 13 | 1/1 · 14 | 1/1 · 14 | 1/1 · 14 | 1/1 · 14 | 1/1 · 14 | 1/1 · 13 | 1/1 · 320 |
| Jsoup-30 | 5 | 1 | 370 | 1/1 · 298 | 0/1 · 0 | 0/1 · 0 | 1/1 · 23 | 1/1 · 23 | 1/1 · 290 | 1/1 · 22 | 1/1 · 22 |
| Jsoup-31 | 6 | 1 | 372 | 1/1 · 300 | 0/1 · 0 | 0/1 · 0 | 0/1 · 34 | 0/1 · 34 | 1/1 · 292 | 1/1 · 254 | 1/1 · 315 |
| Jsoup-32 | 1 | 1 | 383 | 1/1 · 6 | 0/1 · 0 | 0/1 · 0 | 1/1 · 3 | 1/1 · 3 | 1/1 · 6 | 1/1 · 2 | 1/1 · 350 |
| Jsoup-33 | 1 | 1 | 416 | 1/1 · 342 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 333 | 0/1 · 0 | 1/1 · 357 |
| Jsoup-34 | 1 | 2 | 418 | 2/2 · 356 | 1/2 · 3 | 1/2 · 3 | 1/2 · 7 | 1/2 · 7 | 0/2 · 1 | 1/2 · 13 | 2/2 · 360 |
| Jsoup-35 | 1 | 1 | 419 | 1/1 · 344 | 0/1 · 0 | 0/1 · 0 | 0/1 · 36 | 0/1 · 36 | 1/1 · 335 | 0/1 · 0 | 1/1 · 344 |
| Jsoup-36 | 6 | 6 | 434 | 6/6 · 63 | 5/6 · 7 | 5/6 · 9 | 6/6 · 325 | 6/6 · 325 | 5/6 · 316 | 6/6 · 312 | 6/6 · 27 |
| Jsoup-37 | 1 | 1 | 434 | 1/1 · 146 | 0/1 · 0 | 0/1 · 46 | 1/1 · 41 | 1/1 · 41 | 1/1 · 339 | 1/1 · 14 | 1/1 · 400 |
| Jsoup-38 | 1 | 1 | 435 | 1/1 · 357 | 0/1 · 0 | 0/1 · 0 | 0/1 · 36 | 0/1 · 36 | 1/1 · 340 | 0/1 · 0 | 1/1 · 352 |
| Jsoup-39 | 1 | 1 | 439 | 1/1 · 58 | 1/1 · 2 | 1/1 · 4 | 1/1 · 325 | 1/1 · 325 | 1/1 · 293 | 1/1 · 304 | 1/1 · 40 |
| Jsoup-40 | 1 | 2 | 440 | 2/2 · 365 | 0/2 · 0 | 0/2 · 0 | 1/2 · 40 | 1/2 · 40 | 2/2 · 348 | 0/2 · 0 | 2/2 · 361 |
| Jsoup-41 | 1 | 1 | 476 | 1/1 · 2 | 0/1 · 20 | 0/1 · 85 | 1/1 · 36 | 1/1 · 36 | 1/1 · 378 | 1/1 · 1 | 1/1 · 440 |
| Jsoup-42 | 1 | 2 | 478 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 394 |
| Jsoup-43 | 1 | 2 | 494 | 2/2 · 411 | 2/2 · 7 | 2/2 · 7 | 1/2 · 36 | 1/2 · 36 | 2/2 · 386 | 1/2 · 35 | 2/2 · 458 |
| Jsoup-44 | 2 | 1 | 496 | 1/1 · 408 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 387 | 0/1 · 0 | 1/1 · 412 |
| Jsoup-45 | 1 | 1 | 503 | 1/1 · 415 | 0/1 · 0 | 0/1 · 0 | 0/1 · 42 | 0/1 · 42 | 1/1 · 394 | 0/1 · 0 | 1/1 · 416 |
| Jsoup-46 | 1 | 1 | 506 | 1/1 · 425 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 402 | 0/1 · 34 | 1/1 · 410 |
| Jsoup-47 | 1 | 1 | 510 | 1/1 · 428 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 404 | 0/1 · 34 | 1/1 · 413 |
| Jsoup-48 | 1 | 1 | 513 | 1/1 · 66 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 0/1 · 350 | 0/1 · 0 | 1/1 · 26 |
| Jsoup-49 | 1 | 1 | 523 | 1/1 · 437 | 1/1 · 35 | 1/1 · 99 | 0/1 · 0 | 0/1 · 0 | 1/1 · 408 | 1/1 · 35 | 1/1 · 487 |
| Jsoup-50 | 1 | 1 | 527 | 1/1 · 88 | 0/1 · 3 | 0/1 · 6 | 1/1 · 378 | 1/1 · 378 | 0/1 · 326 | 1/1 · 340 | 1/1 · 161 |
| Jsoup-51 | 1 | 1 | 528 | 1/1 · 443 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 418 | 0/1 · 6 | 1/1 · 436 |
| Jsoup-52 | 4 | 7 | 537 | 7/7 · 449 | 1/7 · 4 | 1/7 · 100 | 3/7 · 416 | 3/7 · 416 | 7/7 · 418 | 3/7 · 373 | 7/7 · 447 |
| Jsoup-53 | 1 | 1 | 539 | 1/1 · 456 | 0/1 · 48 | 0/1 · 48 | 0/1 · 42 | 0/1 · 42 | 0/1 · 5 | 0/1 · 21 | 1/1 · 411 |
| Jsoup-54 | 1 | 1 | 542 | 1/1 · 453 | 0/1 · 0 | 0/1 · 0 | 0/1 · 33 | 0/1 · 33 | 1/1 · 422 | 0/1 · 32 | 1/1 · 4 |
| Jsoup-55 | 1 | 1 | 561 | 1/1 · 460 | 0/1 · 0 | 0/1 · 0 | 1/1 · 431 | 1/1 · 431 | 1/1 · 430 | 0/1 · 0 | 1/1 · 441 |
| Jsoup-56 | 17 | 1 | 568 | 1/1 · 479 | 0/1 · 0 | 0/1 · 100 | 1/1 · 447 | 1/1 · 451 | 1/1 · 442 | 1/1 · 419 | 1/1 · 466 |
| Jsoup-57 | 1 | 1 | 570 | 1/1 · 2 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1 | 1/1 · 1 | 1/1 · 2 | 0/1 · 0 | 1/1 · 474 |
| Jsoup-58 | 4 | 2 | 583 | 2/2 · 3 | 0/2 · 4 | 0/2 · 102 | 2/2 · 35 | 2/2 · 35 | 2/2 · 439 | 2/2 · 55 | 2/2 · 474 |
| Jsoup-59 | 1 | 2 | 586 | 2/2 · 476 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 2/2 · 477 |
| Jsoup-6 | 1 | 2 | 227 | 2/2 · 187 | 0/2 · 0 | 0/2 · 0 | 1/2 · 3 | 1/2 · 3 | 2/2 · 184 | 2/2 · 183 | 2/2 · 186 |
| Jsoup-60 | 2 | 2 | 588 | 2/2 · 490 | 0/2 · 53 | 0/2 · 53 | 2/2 · 297 | 2/2 · 297 | 2/2 · 10 | 2/2 · 27 | 2/2 · 444 |
| Jsoup-61 | 1 | 2 | 592 | 2/2 · 488 | 0/2 · 1 | 0/2 · 1 | 1/2 · 40 | 1/2 · 40 | 2/2 · 448 | 1/2 · 38 | 2/2 · 552 |
| Jsoup-62 | 1 | 1 | 600 | 1/1 · 489 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 454 | 0/1 · 0 | 1/1 · 469 |
| Jsoup-63 | 3 | 3 | 615 | 3/3 · 499 | 0/3 · 0 | 0/3 · 0 | 3/3 · 466 | 3/3 · 466 | 3/3 · 461 | 3/3 · 381 | 3/3 · 495 |
| Jsoup-64 | 1 | 2 | 619 | 2/2 · 503 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 2/2 · 465 | 0/2 · 0 | 2/2 · 479 |
| Jsoup-65 | 4 | 1 | 635 | 1/1 · 513 | 0/1 · 0 | 0/1 · 0 | 1/1 · 480 | 1/1 · 480 | 1/1 · 475 | 0/1 · 0 | 1/1 · 510 |
| Jsoup-66 | 5 | 1 | 645 | 1/1 · 551 | 1/1 · 183 | 1/1 · 211 | 1/1 · 525 | 1/1 · 525 | 1/1 · 492 | 1/1 · 251 | 1/1 · 530 |
| Jsoup-67 | 69 | 1 | 652 | 1/1 · 549 | 0/1 · 0 | 0/1 · 0 | 1/1 · 528 | 1/1 · 528 | 1/1 · 536 | 0/1 · 420 | 1/1 · 537 |
| Jsoup-68 | 1 | 1 | 658 | 1/1 · 531 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 546 |
| Jsoup-69 | 7 | 1 | 668 | 1/1 · 567 | 1/1 · 82 | 1/1 · 153 | 1/1 · 109 | 1/1 · 109 | 1/1 · 502 | 1/1 · 174 | 1/1 · 555 |
| Jsoup-7 | 2 | 1 | 232 | 1/1 · 188 | 0/1 · 40 | 0/1 · 41 | 0/1 · 0 | 0/1 · 0 | 1/1 · 185 | 1/1 · 182 | 1/1 · 191 |
| Jsoup-70 | 1 | 1 | 668 | 1/1 · 566 | 0/1 · 18 | 0/1 · 116 | 0/1 · 0 | 0/1 · 0 | 0/1 · 21 | 0/1 · 133 | 1/1 · 565 |
| Jsoup-71 | 9 | 2 | 670 | 2/2 · 571 | 0/2 · 1 | 0/2 · 116 | 0/2 · 15 | 0/2 · 15 | 0/2 · 15 | 0/2 · 138 | 2/2 · 549 |
| Jsoup-72 | 1 | 2 | 674 | 2/2 · 568 | 0/2 · 0 | 0/2 · 0 | 1/2 · 14 | 1/2 · 14 | 2/2 · 529 | 1/2 · 23 | 2/2 · 569 |
| Jsoup-73 | 6 | 1 | 676 | 1/1 · 573 | 1/1 · 6 | 1/1 · 6 | 1/1 · 5 | 1/1 · 5 | 0/1 · 5 | 1/1 · 135 | 1/1 · 5 |
| Jsoup-74 | 2 | 1 | 677 | 1/1 · 575 | 0/1 · 49 | 0/1 · 119 | 0/1 · 51 | 0/1 · 51 | 1/1 · 75 | 1/1 · 153 | 1/1 · 573 |
| Jsoup-75 | 1 | 1 | 697 | 1/1 · 594 | 0/1 · 0 | 0/1 · 4 | 0/1 · 1 | 0/1 · 1 | 0/1 · 1 | 0/1 · 140 | 1/1 · 596 |
| Jsoup-76 | 1 | 1 | 699 | 1/1 · 570 | 0/1 · 0 | 0/1 · 0 | 1/1 · 534 | 1/1 · 534 | 1/1 · 529 | 0/1 · 0 | 1/1 · 565 |
| Jsoup-77 | 1 | 1 | 702 | 1/1 · 573 | 0/1 · 0 | 0/1 · 0 | 1/1 · 537 | 1/1 · 537 | 1/1 · 532 | 1/1 · 444 | 1/1 · 595 |
| Jsoup-78 | 1 | 1 | 705 | 1/1 · 574 | 0/1 · 5 | 0/1 · 8 | 1/1 · 538 | 1/1 · 538 | 0/1 · 422 | 0/1 · 444 | 1/1 · 231 |
| Jsoup-79 | 14 | 1 | 706 | 1/1 · 609 | 1/1 · 166 | 1/1 · 182 | 1/1 · 561 | 1/1 · 564 | 1/1 · 551 | 1/1 · 526 | 1/1 · 609 |
| Jsoup-8 | 2 | 1 | 233 | 1/1 · 72 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 186 | 0/1 · 0 | 1/1 · 192 |
| Jsoup-80 | 1 | 1 | 709 | 1/1 · 578 | 0/1 · 0 | 0/1 · 0 | 1/1 · 542 | 1/1 · 542 | 0/1 · 0 | 1/1 · 448 | 1/1 · 601 |
| Jsoup-81 | 1 | 1 | 712 | 1/1 · 582 | 0/1 · 5 | 0/1 · 8 | 1/1 · 546 | 1/1 · 546 | 0/1 · 427 | 1/1 · 442 | 1/1 · 236 |
| Jsoup-82 | 1 | 1 | 717 | 1/1 · 586 | 0/1 · 5 | 0/1 · 8 | 1/1 · 547 | 1/1 · 547 | 0/1 · 424 | 1/1 · 443 | 1/1 · 241 |
| Jsoup-83 | 3 | 2 | 718 | 2/2 · 587 | 0/2 · 0 | 0/2 · 0 | 2/2 · 548 | 2/2 · 548 | 2/2 · 542 | 0/2 · 0 | 2/2 · 623 |
| Jsoup-84 | 1 | 1 | 719 | 1/1 · 614 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 523 | 1/1 · 6 |
| Jsoup-85 | 1 | 1 | 724 | 1/1 · 624 | 0/1 · 0 | 0/1 · 0 | 1/1 · 588 | 1/1 · 588 | 1/1 · 42 | 0/1 · 0 | 1/1 · 631 |
| Jsoup-86 | 1 | 1 | 727 | 1/1 · 591 | 0/1 · 5 | 0/1 · 8 | 1/1 · 552 | 1/1 · 552 | 1/1 · 429 | 0/1 · 0 | 1/1 · 618 |
| Jsoup-87 | 45 | 1 | 728 | 1/1 · 639 | 0/1 · 93 | 0/1 · 148 | 1/1 · 598 | 1/1 · 607 | 1/1 · 588 | 0/1 · 0 | 1/1 · 644 |
| Jsoup-88 | 1 | 1 | 731 | 1/1 · 638 | 1/1 · 49 | 1/1 · 49 | 1/1 · 601 | 1/1 · 601 | 1/1 · 513 | 0/1 · 0 | 1/1 · 637 |
| Jsoup-89 | 1 | 1 | 732 | 1/1 · 623 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 0/1 · 0 | 1/1 · 638 |
| Jsoup-9 | 4 | 1 | 233 | 1/1 · 195 | 0/1 · 0 | 0/1 · 0 | 1/1 · 8 | 1/1 · 8 | 1/1 · 192 | 1/1 · 187 | 1/1 · 189 |
| Jsoup-90 | 1 | 1 | 736 | 1/1 · 133 | 0/1 · 12 | 0/1 · 12 | 0/1 · 601 | 0/1 · 601 | 0/1 · 484 | 0/1 · 0 | 1/1 · 63 |
| Jsoup-91 | 37 | 3 | 740 | 3/3 · 661 | 0/3 · 19 | 0/3 · 128 | 1/3 · 583 | 1/3 · 583 | 0/3 · 541 | 1/3 · 495 | 3/3 · 666 |
| Jsoup-92 | 7 | 3 | 750 | 3/3 · 651 | 0/3 · 86 | 0/3 · 193 | 3/3 · 596 | 3/3 · 596 | 3/3 · 534 | 3/3 · 559 | 3/3 · 664 |
| Jsoup-93 | 1 | 1 | 751 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 | 1/1 · 642 |
| JxPath-10 | 1 | 1 | 341 | 1/1 · 340 | 0/1 · 0 | 0/1 · 31 | 1/1 · 270 | 1/1 · 288 | 1/1 · 324 | 1/1 · 287 | 1/1 · 139 |
| JxPath-11 | 2 | 2 | 341 | 2/2 · 340 | 0/2 · 0 | 0/2 · 0 | 2/2 · 274 | 2/2 · 292 | 2/2 · 339 | 0/2 · 0 | 2/2 · 88 |
| JxPath-12 | 1 | 1 | 343 | 1/1 · 342 | 0/1 · 0 | 0/1 · 31 | 0/1 · 0 | 1/1 · 290 | 1/1 · 341 | 1/1 · 293 | 1/1 · 331 |
| JxPath-13 | 44 | 1 | 344 | 1/1 · 343 | 0/1 · 2 | 0/1 · 31 | 1/1 · 284 | 1/1 · 295 | 1/1 · 343 | 1/1 · 294 | 1/1 · 332 |
| JxPath-14 | 3 | 1 | 350 | 1/1 · 349 | 0/1 · 0 | 0/1 · 31 | 1/1 · 273 | 1/1 · 297 | 1/1 · 333 | 1/1 · 296 | 1/1 · 276 |
| JxPath-15 | 1 | 2 | 352 | 2/2 · 351 | 0/2 · 0 | 0/2 · 31 | 2/2 · 275 | 2/2 · 299 | 2/2 · 335 | 2/2 · 298 | 2/2 · 341 |
| JxPath-16 | 2 | 4 | 361 | 4/4 · 360 | 0/4 · 0 | 0/4 · 32 | 0/4 · 0 | 4/4 · 308 | 4/4 · 360 | 4/4 · 311 | 4/4 · 349 |
| JxPath-17 | 2 | 2 | 361 | 2/2 · 360 | 0/2 · 0 | 0/2 · 0 | 2/2 · 287 | 2/2 · 312 | 2/2 · 360 | 0/2 · 0 | 2/2 · 97 |
| JxPath-18 | 6 | 2 | 361 | 2/2 · 360 | 0/2 · 0 | 0/2 · 32 | 2/2 · 283 | 2/2 · 308 | 2/2 · 344 | 2/2 · 307 | 2/2 · 350 |
| JxPath-19 | 4 | 2 | 373 | 2/2 · 370 | 0/2 · 2 | 0/2 · 34 | 2/2 · 163 | 2/2 · 173 | 2/2 · 370 | 0/2 · 58 | 2/2 · 361 |
| JxPath-20 | 2 | 1 | 382 | 1/1 · 379 | 0/1 · 2 | 0/1 · 34 | 0/1 · 163 | 1/1 · 327 | 1/1 · 363 | 1/1 · 326 | 1/1 · 140 |
| JxPath-21 | 1 | 2 | 384 | 2/2 · 381 | 0/2 · 2 | 0/2 · 34 | 1/2 · 196 | 2/2 · 333 | 2/2 · 381 | 2/2 · 332 | 2/2 · 348 |
| JxPath-22 | 1 | 1 | 386 | 1/1 · 383 | 0/1 · 2 | 0/1 · 34 | 0/1 · 240 | 1/1 · 335 | 1/1 · 383 | 1/1 · 334 | 1/1 · 372 |
| JxPath-6 | 1 | 1 | 338 | 1/1 · 337 | 0/1 · 0 | 0/1 · 31 | 0/1 · 0 | 0/1 · 0 | 1/1 · 321 | 0/1 · 0 | 1/1 · 327 |
| JxPath-7 | 11 | 1 | 339 | 1/1 · 338 | 0/1 · 0 | 0/1 · 31 | 1/1 · 268 | 1/1 · 286 | 1/1 · 322 | 1/1 · 285 | 1/1 · 137 |
| JxPath-8 | 1 | 1 | 340 | 1/1 · 339 | 0/1 · 0 | 0/1 · 31 | 1/1 · 269 | 1/1 · 287 | 1/1 · 323 | 1/1 · 286 | 1/1 · 138 |
| JxPath-9 | 9 | 1 | 340 | 1/1 · 340 | 0/1 · 0 | 0/1 · 31 | 1/1 · 317 | 1/1 · 317 | 1/1 · 324 | 1/1 · 286 | 1/1 · 329 |
| Lang-10 | 1 | 2 | 2203 | 2/2 · 99 | 0/2 · 0 | 0/2 · 0 | 0/2 · 8 | 0/2 · 8 | 2/2 · 91 | 0/2 · 0 | 2/2 · 163 |
| Lang-11 | 1 | 1 | 2142 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 | 0/1 · 0 | 0/1 · 0 | 0/1 · 6 | 1/1 · 10 | 1/1 · 11 |
| Lang-12 | 1 | 2 | 2141 | 2/2 · 9 | 2/2 · 9 | 2/2 · 9 | 0/2 · 0 | 0/2 · 0 | 2/2 · 6 | 2/2 · 9 | 2/2 · 10 |
| Lang-13 | 3 | 1 | 2139 | 1/1 · 8 | 0/1 · 0 | 0/1 · 0 | 1/1 · 8 | 1/1 · 8 | 1/1 · 8 | 1/1 · 8 | 1/1 · 208 |
| Lang-14 | 1 | 1 | 2077 | 1/1 · 17 | 0/1 · 12 | 0/1 · 12 | 1/1 · 26 | 1/1 · 26 | 1/1 · 5 | 1/1 · 2 | 1/1 · 834 |
| Lang-15 | 2 | 2 | 2051 | 2/2 · 6 | 1/2 · 62 | 1/2 · 226 | 1/2 · 20 | 1/2 · 26 | 2/2 · 4 | 2/2 · 6 | 2/2 · 10 |
| Lang-16 | 1 | 1 | 2046 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 164 |
| Lang-17 | 1 | 1 | 1903 | 1/1 · 34 | 1/1 · 18 | 1/1 · 18 | 0/1 · 0 | 0/1 · 0 | 1/1 · 20 | 1/1 · 18 | 1/1 · 45 |
| Lang-19 | 1 | 2 | 1877 | 2/2 · 33 | 0/2 · 17 | 0/2 · 17 | 2/2 · 3 | 2/2 · 3 | 2/2 · 22 | 2/2 · 20 | 2/2 · 32 |
| Lang-20 | 1 | 2 | 1876 | 2/2 · 10 | 2/2 · 16 | 2/2 · 16 | 0/2 · 0 | 0/2 · 0 | 2/2 · 5 | 2/2 · 10 | 2/2 · 585 |
| Lang-21 | 1 | 1 | 1827 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 116 |
| Lang-22 | 1 | 2 | 1825 | 2/2 · 13 | 2/2 · 24 | 2/2 · 24 | 2/2 · 8 | 2/2 · 8 | 2/2 · 23 | 2/2 · 24 | 2/2 · 25 |
| Lang-23 | 19 | 1 | 1825 | 1/1 · 8 | 0/1 · 13 | 0/1 · 13 | 1/1 · 8 | 1/1 · 8 | 1/1 · 8 | 1/1 · 8 | 1/1 · 8 |
| Lang-24 | 1 | 1 | 1822 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 110 |
| Lang-26 | 1 | 1 | 1790 | 1/1 · 39 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 30 | 1/1 · 37 | 1/1 · 93 |
| Lang-27 | 1 | 1 | 1785 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 110 |
| Lang-28 | 1 | 1 | 1763 | 1/1 · 29 | 0/1 · 16 | 0/1 · 16 | 1/1 · 1 | 1/1 · 1 | 1/1 · 19 | 1/1 · 17 | 1/1 · 20 |
| Lang-29 | 1 | 1 | 1760 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 636 |
| Lang-30 | 4 | 10 | 1733 | 10/10 · 53 | 10/10 · 42 | 10/10 · 42 | 10/10 · 40 | 10/10 · 40 | 6/10 · 13 | 10/10 · 42 | 10/10 · 582 |
| Lang-31 | 1 | 2 | 1721 | 2/2 · 31 | 2/2 · 20 | 2/2 · 20 | 2/2 · 4 | 2/2 · 4 | 1/2 · 1 | 2/2 · 20 | 2/2 · 571 |
| Lang-32 | 12 | 1 | 1670 | 1/1 · 45 | 0/1 · 42 | 1/1 · 43 | 1/1 · 42 | 1/1 · 42 | 1/1 · 41 | 1/1 · 14 | 1/1 · 45 |
| Lang-33 | 1 | 1 | 1670 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 255 |
| Lang-34 | 2 | 27 | 1670 | 27/27 · 138 | 0/27 · 25 | 27/27 · 176 | 27/27 · 28 | 27/27 · 28 | 27/27 · 129 | 27/27 · 28 | 27/27 · 344 |
| Lang-35 | 1 | 1 | 1644 | 1/1 · 17 | 0/1 · 57 | 0/1 · 79 | 1/1 · 17 | 1/1 · 17 | 0/1 · 6 | 1/1 · 17 | 1/1 · 795 |
| Lang-36 | 2 | 2 | 1628 | 2/2 · 3 | 2/2 · 3 | 2/2 · 3 | 2/2 · 3 | 2/2 · 3 | 2/2 · 3 | 2/2 · 3 | 2/2 · 110 |
| Lang-37 | 1 | 1 | 1627 | 1/1 · 8 | 1/1 · 10 | 1/1 · 10 | 1/1 · 8 | 1/1 · 8 | 0/1 · 0 | 1/1 · 8 | 1/1 · 657 |
| Lang-38 | 1 | 1 | 1624 | 1/1 · 38 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 36 | 1/1 · 59 |
| Lang-39 | 1 | 1 | 1618 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 0/1 · 1 | 0/1 · 1 | 1/1 · 2 | 1/1 · 2 | 1/1 · 523 |
| Lang-40 | 1 | 1 | 1642 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 516 |
| Lang-41 | 2 | 2 | 1623 | 2/2 · 153 | 1/2 · 35 | 1/2 · 183 | 0/2 · 0 | 0/2 · 0 | 0/2 · 6 | 2/2 · 25 | 2/2 · 241 |
| Lang-42 | 1 | 1 | 1903 | 1/1 · 12 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 12 | 0/1 · 8 | 1/1 · 54 |
| Lang-43 | 1 | 1 | 1902 | 1/1 · 7 | 0/1 · 6 | 0/1 · 6 | 1/1 · 5 | 1/1 · 5 | 1/1 · 7 | 0/1 · 0 | 1/1 · 7 |
| Lang-44 | 1 | 1 | 1879 | 1/1 · 3 | 0/1 · 0 | 0/1 · 0 | 1/1 · 6 | 1/1 · 6 | 1/1 · 3 | 0/1 · 0 | 1/1 · 20 |
| Lang-45 | 1 | 1 | 1877 | 1/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 82 |
| Lang-46 | 3 | 1 | 1829 | 1/1 · 5 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 5 | 1/1 · 5 | 1/1 · 87 |
| Lang-47 | 2 | 2 | 2689 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 0/2 · 2 | 2/2 · 7 | 2/2 · 206 |
| Lang-49 | 1 | 1 | 2610 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 25 |
| Lang-50 | 2 | 2 | 1814 | 2/2 · 3 | 2/2 · 10 | 2/2 · 10 | 0/2 · 0 | 0/2 · 0 | 2/2 · 3 | 2/2 · 3 | 2/2 · 35 |
| Lang-51 | 1 | 1 | 1725 | 1/1 · 3 | 1/1 · 6 | 1/1 · 6 | 1/1 · 6 | 1/1 · 6 | 1/1 · 2 | 1/1 · 6 | 1/1 · 190 |
| Lang-52 | 1 | 1 | 1725 | 1/1 · 4 | 1/1 · 3 | 1/1 · 3 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4 | 1/1 · 4 | 1/1 · 74 |
| Lang-53 | 1 | 1 | 1718 | 1/1 · 7 | 1/1 · 6 | 1/1 · 6 | 1/1 · 7 | 1/1 · 7 | 1/1 · 5 | 1/1 · 7 | 1/1 · 31 |
| Lang-54 | 1 | 1 | 1710 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 12 |
| Lang-55 | 1 | 1 | 1710 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 6 |
| Lang-56 | 24 | 1 | 1691 | 1/1 · 20 | 0/1 · 37 | 0/1 · 37 | 1/1 · 41 | 1/1 · 41 | 1/1 · 19 | 1/1 · 18 | 1/1 · 33 |
| Lang-57 | 1 | 11 | 1690 | 11/11 · 11 | 11/11 · 11 | 11/11 · 11 | 11/11 · 11 | 11/11 · 11 | 11/11 · 11 | 11/11 · 11 | 11/11 · 11 |
| Lang-58 | 1 | 1 | 1689 | 1/1 · 3 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 3 | 0/1 · 0 | 1/1 · 256 |
| Lang-59 | 1 | 1 | 1687 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 0/1 · 1 | 1/1 · 3 | 1/1 · 186 |
| Lang-60 | 2 | 1 | 1684 | 1/1 · 24 | 1/1 · 15 | 1/1 · 15 | 1/1 · 4 | 1/1 · 4 | 1/1 · 18 | 1/1 · 24 | 1/1 · 185 |
| Lang-61 | 1 | 2 | 1683 | 2/2 · 23 | 2/2 · 14 | 2/2 · 14 | 0/2 · 0 | 0/2 · 0 | 2/2 · 17 | 2/2 · 23 | 2/2 · 184 |
| Lang-62 | 1 | 1 | 1681 | 1/1 · 32 | 1/1 · 32 | 1/1 · 32 | 1/1 · 28 | 1/1 · 28 | 1/1 · 32 | 1/1 · 8 | 1/1 · 47 |
| Lang-63 | 1 | 1 | 1671 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4 | 1/1 · 4 | 1/1 · 16 |
| Lang-64 | 2 | 1 | 1666 | 1/1 · 141 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 3 | 0/1 · 0 | 0/1 · 0 | 1/1 · 75 |
| Lang-65 | 1 | 1 | 1633 | 1/1 · 6 | 1/1 · 5 | 1/1 · 5 | 1/1 · 6 | 1/1 · 6 | 1/1 · 4 | 1/1 · 6 | 1/1 · 30 |
| Lang-7 | 2 | 1 | 2266 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 166 |
| Lang-8 | 2 | 2 | 2210 | 2/2 · 129 | 0/2 · 0 | 0/2 · 0 | 0/2 · 26 | 0/2 · 26 | 2/2 · 125 | 0/2 · 0 | 2/2 · 154 |
| Lang-9 | 1 | 2 | 2205 | 2/2 · 101 | 0/2 · 0 | 0/2 · 0 | 0/2 · 8 | 0/2 · 8 | 2/2 · 93 | 0/2 · 0 | 2/2 · 165 |
| Math-10 | 1 | 1 | 4498 | 1/1 · 3 | 0/1 · 0 | 0/1 · 0 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 0/1 · 0 | 1/1 · 369 |
| Math-100 | 2 | 1 | 1179 | 1/1 · 4 | 0/1 · 0 | 0/1 · 0 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 0/1 · 0 | 1/1 · 48 |
| Math-101 | 1 | 2 | 1177 | 2/2 · 2 | 0/2 · 0 | 0/2 · 0 | 0/2 · 24 | 0/2 · 24 | 2/2 · 26 | 0/2 · 24 | 2/2 · 70 |
| Math-102 | 1 | 6 | 1146 | 6/6 · 38 | 0/6 · 0 | 0/6 · 0 | 6/6 · 41 | 6/6 · 41 | 6/6 · 41 | 3/6 · 28 | 6/6 · 30 |
| Math-103 | 1 | 1 | 1013 | 1/1 · 240 | 0/1 · 4 | 0/1 · 4 | 1/1 · 62 | 1/1 · 62 | 1/1 · 211 | 0/1 · 0 | 1/1 · 20 |
| Math-104 | 5 | 1 | 1002 | 1/1 · 277 | 1/1 · 37 | 1/1 · 37 | 1/1 · 81 | 1/1 · 133 | 1/1 · 254 | 1/1 · 42 | 1/1 · 133 |
| Math-105 | 1 | 1 | 887 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 |
| Math-106 | 1 | 1 | 875 | 1/1 · 8 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 8 | 1/1 · 8 | 1/1 · 8 | 1/1 · 16 |
| Math-11 | 1 | 1 | 4476 | 1/1 · 2 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 10 |
| Math-12 | 12 | 3 | 4462 | 3/3 · 2291 | 0/3 · 4 | 0/3 · 4 | 3/3 · 272 | 3/3 · 272 | 3/3 · 1029 | 3/3 · 734 | 3/3 · 707 |
| Math-13 | 1 | 1 | 4450 | 1/1 · 93 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 8 | 0/1 · 0 | 1/1 · 89 |
| Math-14 | 2 | 1 | 4449 | 1/1 · 229 | 0/1 · 0 | 0/1 · 0 | 0/1 · 100 | 0/1 · 100 | 0/1 · 173 | 0/1 · 0 | 1/1 · 92 |
| Math-15 | 50 | 1 | 4179 | 1/1 · 3824 | 0/1 · 447 | 0/1 · 492 | 1/1 · 3327 | 1/1 · 3405 | 0/1 · 3149 | 1/1 · 2997 | 1/1 · 3042 |
| Math-16 | 50 | 2 | 4177 | 2/2 · 3822 | 2/2 · 446 | 2/2 · 491 | 2/2 · 3325 | 2/2 · 3403 | 2/2 · 3148 | 2/2 · 2996 | 2/2 · 3040 |
| Math-17 | 1 | 1 | 4091 | 1/1 · 1609 | 1/1 · 82 | 1/1 · 157 | 1/1 · 525 | 1/1 · 571 | 1/1 · 847 | 1/1 · 82 | 1/1 · 88 |
| Math-18 | 3 | 1 | 4086 | 1/1 · 89 | 0/1 · 0 | 0/1 · 0 | 1/1 · 107 | 1/1 · 107 | 1/1 · 77 | 0/1 · 0 | 1/1 · 26 |
| Math-19 | 1 | 1 | 4080 | 1/1 · 88 | 0/1 · 0 | 0/1 · 0 | 1/1 · 106 | 1/1 · 106 | 1/1 · 76 | 0/1 · 0 | 1/1 · 25 |
| Math-20 | 1 | 1 | 4079 | 1/1 · 87 | 0/1 · 0 | 0/1 · 0 | 1/1 · 105 | 1/1 · 105 | 1/1 · 75 | 0/1 · 0 | 1/1 · 24 |
| Math-21 | 1 | 2 | 4041 | 2/2 · 9 | 0/2 · 0 | 0/2 · 0 | 2/2 · 9 | 2/2 · 9 | 2/2 · 9 | 0/2 · 0 | 2/2 · 24 |
| Math-22 | 2 | 2 | 4033 | 2/2 · 22 | 0/2 · 0 | 0/2 · 0 | 2/2 · 22 | 2/2 · 22 | 2/2 · 22 | 2/2 · 22 | 2/2 · 98 |
| Math-23 | 1 | 1 | 4011 | 1/1 · 99 | 0/1 · 0 | 0/1 · 0 | 1/1 · 10 | 1/1 · 10 | 1/1 · 13 | 0/1 · 3 | 1/1 · 17 |
| Math-24 | 1 | 1 | 4010 | 1/1 · 98 | 0/1 · 0 | 0/1 · 0 | 1/1 · 9 | 1/1 · 9 | 1/1 · 12 | 0/1 · 3 | 1/1 · 16 |
| Math-25 | 1 | 1 | 3976 | 1/1 · 6 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 7 |
| Math-26 | 1 | 1 | 3895 | 1/1 · 556 | 0/1 · 0 | 0/1 · 39 | 1/1 · 120 | 1/1 · 132 | 1/1 · 222 | 1/1 · 140 | 1/1 · 213 |
| Math-27 | 1 | 1 | 3895 | 1/1 · 2 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1 | 1/1 · 1 | 1/1 · 2 | 1/1 · 1 | 1/1 · 213 |
| Math-28 | 1 | 1 | 3894 | 1/1 · 26 | 0/1 · 0 | 0/1 · 0 | 0/1 · 24 | 0/1 · 24 | 1/1 · 26 | 0/1 · 0 | 1/1 · 26 |
| Math-29 | 2 | 3 | 3717 | 3/3 · 170 | 0/3 · 0 | 0/3 · 0 | 3/3 · 61 | 3/3 · 61 | 3/3 · 71 | 3/3 · 72 | 3/3 · 78 |
| Math-30 | 1 | 1 | 3660 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 0/1 · 0 | 1/1 · 3 |
| Math-31 | 1 | 2 | 3534 | 2/2 · 1128 | 0/2 · 197 | 0/2 · 197 | 0/2 · 0 | 0/2 · 0 | 2/2 · 1056 | 1/2 · 178 | 2/2 · 317 |
| Math-32 | 1 | 1 | 3525 | 1/1 · 51 | 0/1 · 0 | 0/1 · 0 | 0/1 · 15 | 0/1 · 15 | 1/1 · 51 | 0/1 · 2 | 1/1 · 23 |
| Math-33 | 1 | 1 | 3507 | 1/1 · 25 | 0/1 · 1 | 0/1 · 1 | 1/1 · 25 | 1/1 · 25 | 1/1 · 25 | 0/1 · 1 | 1/1 · 28 |
| Math-34 | 1 | 1 | 3491 | 1/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 24 |
| Math-35 | 1 | 4 | 3482 | 4/4 · 12 | 0/4 · 0 | 0/4 · 0 | 4/4 · 12 | 4/4 · 12 | 4/4 · 12 | 0/4 · 4 | 4/4 · 12 |
| Math-36 | 2 | 2 | 3472 | 2/2 · 233 | 0/2 · 18 | 0/2 · 18 | 2/2 · 8 | 2/2 · 8 | 2/2 · 9 | 2/2 · 21 | 2/2 · 94 |
| Math-37 | 2 | 4 | 3501 | 4/4 · 8 | 0/4 · 0 | 0/4 · 0 | 4/4 · 8 | 4/4 · 8 | 4/4 · 8 | 4/4 · 4 | 4/4 · 264 |
| Math-38 | 1 | 1 | 3211 | 1/1 · 83 | 0/1 · 0 | 0/1 · 0 | 0/1 · 71 | 0/1 · 71 | 1/1 · 83 | 0/1 · 0 | 1/1 · 19 |
| Math-39 | 1 | 1 | 3210 | 1/1 · 162 | 0/1 · 0 | 0/1 · 0 | 1/1 · 35 | 1/1 · 70 | 1/1 · 145 | 1/1 · 128 | 1/1 · 69 |
| Math-40 | 1 | 1 | 3150 | 1/1 · 498 | 0/1 · 1 | 0/1 · 1 | 0/1 · 15 | 0/1 · 15 | 1/1 · 438 | 0/1 · 0 | 1/1 · 90 |
| Math-41 | 1 | 1 | 3145 | 1/1 · 223 | 0/1 · 27 | 0/1 · 35 | 0/1 · 0 | 1/1 · 132 | 1/1 · 192 | 1/1 · 145 | 1/1 · 236 |
| Math-42 | 1 | 1 | 3124 | 1/1 · 23 | 0/1 · 0 | 0/1 · 0 | 1/1 · 23 | 1/1 · 23 | 1/1 · 23 | 0/1 · 0 | 1/1 · 27 |
| Math-43 | 1 | 6 | 3104 | 6/6 · 96 | 0/6 · 0 | 0/6 · 0 | 6/6 · 90 | 6/6 · 90 | 6/6 · 88 | 6/6 · 92 | 6/6 · 78 |
| Math-44 | 1 | 1 | 3070 | 1/1 · 158 | 0/1 · 0 | 0/1 · 0 | 1/1 · 120 | 1/1 · 153 | 1/1 · 153 | 0/1 · 132 | 1/1 · 164 |
| Math-45 | 1 | 1 | 3025 | 1/1 · 888 | 0/1 · 11 | 0/1 · 12 | 1/1 · 265 | 1/1 · 277 | 1/1 · 511 | 0/1 · 188 | 1/1 · 461 |
| Math-46 | 1 | 2 | 2948 | 2/2 · 499 | 0/2 · 1 | 0/2 · 32 | 1/2 · 12 | 1/2 · 12 | 0/2 · 434 | 1/2 · 14 | 2/2 · 199 |
| Math-47 | 36 | 2 | 2948 | 2/2 · 1133 | 1/2 · 983 | 1/2 · 988 | 2/2 · 2368 | 2/2 · 2373 | 2/2 · 639 | 2/2 · 172 | 2/2 · 199 |
| Math-48 | 1 | 1 | 2946 | 1/1 · 479 | 0/1 · 1 | 0/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 424 | 0/1 · 0 | 1/1 · 36 |
| Math-49 | 2 | 1 | 2905 | 1/1 · 3 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2 | 1/1 · 2 | 0/1 · 0 | 1/1 · 2 | 1/1 · 35 |
| Math-50 | 1 | 1 | 2903 | 1/1 · 475 | 0/1 · 1 | 0/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 420 | 0/1 · 0 | 1/1 · 36 |
| Math-51 | 1 | 1 | 2892 | 1/1 · 475 | 0/1 · 1 | 0/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 420 | 0/1 · 0 | 1/1 · 36 |
| Math-52 | 1 | 1 | 2869 | 1/1 · 4 | 0/1 · 13 | 0/1 · 13 | 1/1 · 15 | 1/1 · 15 | 1/1 · 15 | 1/1 · 16 | 1/1 · 28 |
| Math-53 | 1 | 1 | 2474 | 1/1 · 404 | 0/1 · 2 | 0/1 · 17 | 1/1 · 350 | 1/1 · 350 | 1/1 · 365 | 1/1 · 17 | 1/1 · 179 |
| Math-54 | 2 | 1 | 2369 | 1/1 · 406 | 1/1 · 40 | 1/1 · 71 | 1/1 · 71 | 1/1 · 71 | 1/1 · 112 | 1/1 · 65 | 1/1 · 64 |
| Math-55 | 1 | 1 | 2350 | 1/1 · 7 | 1/1 · 16 | 1/1 · 16 | 1/1 · 16 | 1/1 · 16 | 1/1 · 16 | 1/1 · 16 | 1/1 · 88 |
| Math-56 | 1 | 1 | 2349 | 1/1 · 2 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 5 |
| Math-57 | 1 | 1 | 2339 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 |
| Math-58 | 1 | 1 | 2308 | 1/1 · 8 | 0/1 · 0 | 0/1 · 0 | 1/1 · 8 | 1/1 · 24 | 1/1 · 8 | 1/1 · 8 | 1/1 · 8 |
| Math-59 | 1 | 1 | 2241 | 1/1 · 1194 | 0/1 · 69 | 0/1 · 69 | 1/1 · 658 | 1/1 · 673 | 0/1 · 600 | 1/1 · 817 | 1/1 · 1727 |
| Math-6 | 7 | 28 | 4858 | 28/28 · 240 | 0/28 · 0 | 0/28 · 0 | 0/28 · 0 | 0/28 · 0 | 28/28 · 207 | 0/28 · 0 | 28/28 · 230 |
| Math-60 | 1 | 1 | 2224 | 1/1 · 700 | 0/1 · 14 | 0/1 · 14 | 1/1 · 45 | 1/1 · 45 | 1/1 · 494 | 0/1 · 0 | 1/1 · 26 |
| Math-61 | 1 | 1 | 2372 | 1/1 · 49 | 0/1 · 0 | 0/1 · 0 | 1/1 · 49 | 1/1 · 49 | 1/1 · 49 | 0/1 · 0 | 1/1 · 12 |
| Math-62 | 1 | 1 | 2371 | 1/1 · 2 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2 | 1/1 · 2 | 1/1 · 7 | 1/1 · 2 | 1/1 · 2 |
| Math-63 | 1 | 1 | 2287 | 1/1 · 1 | 0/1 · 7 | 0/1 · 38 | 1/1 · 23 | 1/1 · 23 | 0/1 · 2 | 1/1 · 16 | 1/1 · 907 |
| Math-64 | 1 | 2 | 2279 | 2/2 · 80 | 0/2 · 0 | 0/2 · 0 | 2/2 · 80 | 2/2 · 80 | 2/2 · 83 | 0/2 · 34 | 2/2 · 57 |
| Math-65 | 2 | 1 | 2278 | 1/1 · 44 | 0/1 · 0 | 0/1 · 0 | 1/1 · 44 | 1/1 · 44 | 1/1 · 44 | 0/1 · 0 | 1/1 · 77 |
| Math-66 | 4 | 4 | 2266 | 4/4 · 24 | 0/4 · 0 | 0/4 · 0 | 4/4 · 7 | 4/4 · 7 | 4/4 · 24 | 4/4 · 7 | 4/4 · 10 |
| Math-67 | 2 | 1 | 2260 | 1/1 · 2 | 0/1 · 0 | 0/1 · 0 | 1/1 · 2 | 1/1 · 2 | 1/1 · 6 | 1/1 · 6 | 1/1 · 2 |
| Math-68 | 2 | 2 | 2191 | 2/2 · 70 | 0/2 · 0 | 0/2 · 0 | 2/2 · 70 | 2/2 · 70 | 2/2 · 73 | 0/2 · 24 | 2/2 · 44 |
| Math-69 | 1 | 2 | 2191 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 7 | 2/2 · 17 |
| Math-7 | 1 | 1 | 4849 | 1/1 · 163 | 0/1 · 0 | 0/1 · 0 | 0/1 · 122 | 1/1 · 158 | 1/1 · 158 | 1/1 · 137 | 1/1 · 169 |
| Math-70 | 1 | 1 | 2189 | 1/1 · 1 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 10 | 1/1 · 51 | 1/1 · 16 |
| Math-71 | 2 | 2 | 2174 | 2/2 · 113 | 0/2 · 0 | 0/2 · 0 | 2/2 · 103 | 2/2 · 103 | 2/2 · 121 | 0/2 · 91 | 2/2 · 116 |
| Math-72 | 1 | 1 | 2145 | 1/1 · 175 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 122 | 1/1 · 50 | 1/1 · 214 |
| Math-73 | 1 | 1 | 2145 | 1/1 · 175 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 121 | 1/1 · 50 | 1/1 · 214 |
| Math-74 | 1 | 1 | 2136 | 1/1 · 62 | 0/1 · 0 | 0/1 · 0 | 0/1 · 57 | 0/1 · 57 | 1/1 · 99 | 0/1 · 84 | 1/1 · 56 |
| Math-75 | 1 | 1 | 2140 | 1/1 · 5 | 1/1 · 4 | 1/1 · 4 | 1/1 · 5 | 1/1 · 5 | 1/1 · 3 | 1/1 · 5 | 1/1 · 8 |
| Math-76 | 2 | 2 | 2140 | 2/2 · 13 | 0/2 · 0 | 0/2 · 0 | 2/2 · 8 | 2/2 · 8 | 2/2 · 13 | 2/2 · 8 | 2/2 · 17 |
| Math-77 | 2 | 2 | 2134 | 2/2 · 2 | 0/2 · 0 | 0/2 · 0 | 2/2 · 2 | 2/2 · 2 | 2/2 · 2 | 1/2 · 1 | 2/2 · 346 |
| Math-78 | 1 | 1 | 2111 | 1/1 · 116 | 0/1 · 0 | 0/1 · 0 | 1/1 · 111 | 1/1 · 111 | 1/1 · 113 | 1/1 · 1 | 1/1 · 118 |
| Math-79 | 1 | 1 | 2109 | 1/1 · 5 | 0/1 · 0 | 0/1 · 0 | 1/1 · 5 | 1/1 · 5 | 0/1 · 0 | 0/1 · 3 | 1/1 · 866 |
| Math-8 | 1 | 1 | 4766 | 1/1 · 1 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 174 | 0/1 · 51 | 1/1 · 22 |
| Math-80 | 1 | 1 | 2107 | 1/1 · 36 | 0/1 · 0 | 0/1 · 0 | 1/1 · 36 | 1/1 · 36 | 1/1 · 36 | 0/1 · 0 | 1/1 · 36 |
| Math-81 | 3 | 1 | 2106 | 1/1 · 35 | 0/1 · 0 | 0/1 · 0 | 1/1 · 35 | 1/1 · 35 | 1/1 · 35 | 0/1 · 0 | 1/1 · 35 |
| Math-82 | 1 | 1 | 2061 | 1/1 · 14 | 0/1 · 0 | 0/1 · 0 | 1/1 · 13 | 1/1 · 13 | 1/1 · 14 | 0/1 · 0 | 1/1 · 14 |
| Math-83 | 2 | 1 | 2060 | 1/1 · 17 | 0/1 · 0 | 0/1 · 0 | 0/1 · 12 | 0/1 · 12 | 1/1 · 17 | 0/1 · 0 | 1/1 · 17 |
| Math-84 | 1 | 2 | 2059 | 2/2 · 15 | 0/2 · 0 | 0/2 · 0 | 2/2 · 15 | 2/2 · 15 | 2/2 · 15 | 0/2 · 1 | 2/2 · 5 |
| Math-85 | 1 | 1 | 1983 | 1/1 · 36 | 0/1 · 6 | 0/1 · 6 | 0/1 · 0 | 0/1 · 0 | 1/1 · 34 | 0/1 · 18 | 1/1 · 92 |
| Math-86 | 1 | 2 | 1894 | 2/2 · 12 | 0/2 · 0 | 0/2 · 0 | 2/2 · 12 | 2/2 · 12 | 2/2 · 12 | 0/2 · 0 | 2/2 · 12 |
| Math-87 | 1 | 1 | 1893 | 1/1 · 16 | 0/1 · 0 | 0/1 · 0 | 1/1 · 16 | 1/1 · 16 | 1/1 · 16 | 0/1 · 0 | 1/1 · 16 |
| Math-88 | 1 | 1 | 1893 | 1/1 · 11 | 0/1 · 0 | 0/1 · 0 | 1/1 · 11 | 1/1 · 11 | 1/1 · 11 | 0/1 · 0 | 1/1 · 15 |
| Math-89 | 1 | 1 | 1691 | 1/1 · 28 | 0/1 · 0 | 0/1 · 0 | 1/1 · 28 | 1/1 · 28 | 1/1 · 5 | 1/1 · 28 | 1/1 · 7 |
| Math-9 | 1 | 1 | 4742 | 1/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 0/1 · 0 | 1/1 · 35 |
| Math-90 | 1 | 1 | 1691 | 1/1 · 28 | 0/1 · 0 | 0/1 · 0 | 1/1 · 28 | 1/1 · 28 | 1/1 · 5 | 1/1 · 28 | 1/1 · 7 |
| Math-91 | 1 | 1 | 1671 | 1/1 · 7 | 0/1 · 0 | 0/1 · 0 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 62 |
| Math-92 | 3 | 1 | 1507 | 1/1 · 326 | 0/1 · 12 | 0/1 · 12 | 1/1 · 90 | 1/1 · 130 | 1/1 · 279 | 1/1 · 38 | 1/1 · 547 |
| Math-93 | 3 | 1 | 1503 | 1/1 · 16 | 1/1 · 2 | 1/1 · 2 | 1/1 · 14 | 1/1 · 14 | 1/1 · 14 | 1/1 · 14 | 1/1 · 546 |
| Math-94 | 1 | 1 | 1500 | 1/1 · 146 | 1/1 · 5 | 1/1 · 5 | 1/1 · 41 | 1/1 · 49 | 1/1 · 151 | 1/1 · 36 | 1/1 · 546 |
| Math-95 | 1 | 1 | 1300 | 1/1 · 33 | 0/1 · 4 | 0/1 · 4 | 0/1 · 32 | 0/1 · 32 | 0/1 · 31 | 0/1 · 16 | 1/1 · 23 |
| Math-96 | 1 | 1 | 1271 | 0/1 · 54 | 0/1 · 1 | 0/1 · 1 | 0/1 · 9 | 0/1 · 9 | 0/1 · 163 | 0/1 · 52 | 1/1 · 171 |
| Math-97 | 1 | 1 | 1095 | 1/1 · 118 | 0/1 · 0 | 0/1 · 0 | 1/1 · 79 | 1/1 · 79 | 1/1 · 133 | 1/1 · 44 | 1/1 · 129 |
| Math-98 | 2 | 2 | 1094 | 2/2 · 6 | 0/2 · 0 | 0/2 · 0 | 2/2 · 6 | 2/2 · 6 | 2/2 · 6 | 2/2 · 6 | 2/2 · 133 |
| Math-99 | 2 | 2 | 1552 | 2/2 · 389 | 2/2 · 32 | 2/2 · 32 | 2/2 · 143 | 2/2 · 191 | 2/2 · 338 | 2/2 · 86 | 2/2 · 560 |
| Mockito-10 | 4 | 1 | 1385 | 0/1 · 21 | 0/1 · 3 | 0/1 · 3 | 0/1 · 18 | 0/1 · 18 | 0/1 · 21 | 0/1 · 13 | 1/1 · 1086 |
| Mockito-11 | 2 | 2 | 1375 | 2/2 · 9 | 0/2 · 29 | 0/2 · 34 | 2/2 · 5 | 2/2 · 5 | 2/2 · 5 | 2/2 · 5 | 2/2 · 906 |
| Mockito-12 | 1 | 10 | 988 | 10/10 · 976 | 10/10 · 976 | 10/10 · 976 | 1/10 · 3 | 1/10 · 3 | 1/10 · 3 | 1/10 · 3 | 10/10 · 20 |
| Mockito-13 | 1 | 1 | 983 | 0/1 · 3 | 0/1 · 0 | 0/1 · 0 | 0/1 · 3 | 0/1 · 3 | 0/1 · 3 | 0/1 · 3 | 1/1 · 739 |
| Mockito-14 | 2 | 1 | 970 | 1/1 · 329 | 0/1 · 16 | 0/1 · 21 | 0/1 · 28 | 0/1 · 143 | 0/1 · 145 | 0/1 · 128 | 1/1 · 733 |
| Mockito-15 | 1 | 1 | 1039 | 0/1 · 1000 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 1000 | 0/1 · 0 | 1/1 · 23 |
| Mockito-16 | 3 | 1 | 882 | 1/1 · 881 | 1/1 · 881 | 1/1 · 881 | 0/1 · 11 | 0/1 · 11 | 0/1 · 214 | 1/1 · 881 | 1/1 · 657 |
| Mockito-17 | 14 | 1 | 878 | 1/1 · 877 | 1/1 · 877 | 1/1 · 877 | 1/1 · 877 | 1/1 · 877 | 0/1 · 231 | 1/1 · 877 | 1/1 · 660 |
| Mockito-18 | 1 | 1 | 1424 | 1/1 · 25 | 0/1 · 3 | 0/1 · 3 | 1/1 · 19 | 1/1 · 19 | 1/1 · 25 | 1/1 · 19 | 1/1 · 1113 |
| Mockito-19 | 8 | 1 | 1424 | 1/1 · 1161 | 0/1 · 0 | 0/1 · 0 | 0/1 · 1 | 0/1 · 1 | 1/1 · 1158 | 0/1 · 0 | 1/1 · 1179 |
| Mockito-20 | 1 | 8 | 1428 | 8/8 · 1281 | 2/8 · 17 | 2/8 · 22 | 2/8 · 28 | 2/8 · 28 | 8/8 · 1227 | 8/8 · 1168 | 8/8 · 1310 |
| Mockito-21 | 3 | 1 | 1406 | 1/1 · 1277 | 0/1 · 30 | 0/1 · 35 | 0/1 · 6 | 0/1 · 6 | 1/1 · 11 | 0/1 · 6 | 1/1 · 17 |
| Mockito-22 | 1 | 1 | 1362 | 1/1 · 2 | 1/1 · 1 | 1/1 · 1 | 1/1 · 19 | 1/1 · 19 | 1/1 · 2 | 1/1 · 1 | 1/1 · 568 |
| Mockito-23 | 12 | 1 | 1352 | 0/1 · 21 | 0/1 · 3 | 0/1 · 3 | 0/1 · 18 | 0/1 · 18 | 0/1 · 21 | 0/1 · 13 | 1/1 · 1057 |
| Mockito-24 | 1 | 2 | 1351 | 1/2 · 23 | 0/2 · 3 | 0/2 · 3 | 1/2 · 20 | 1/2 · 20 | 1/2 · 23 | 1/2 · 15 | 2/2 · 1058 |
| Mockito-25 | 7 | 6 | 1319 | 0/6 · 21 | 0/6 · 3 | 0/6 · 3 | 0/6 · 18 | 0/6 · 18 | 0/6 · 21 | 0/6 · 13 | 6/6 · 1031 |
| Mockito-26 | 6 | 4 | 1247 | 4/4 · 315 | 0/4 · 54 | 0/4 · 54 | 4/4 · 85 | 4/4 · 85 | 3/4 · 52 | 4/4 · 43 | 4/4 · 765 |
| Mockito-27 | 1 | 1 | 1144 | 1/1 · 1049 | 0/1 · 0 | 0/1 · 0 | 0/1 · 1044 | 0/1 · 1044 | 0/1 · 1068 | 0/1 · 1043 | 1/1 · 1086 |
| Mockito-28 | 1 | 1 | 1053 | 0/1 · 1012 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 1012 | 0/1 · 0 | 1/1 · 28 |
| Mockito-29 | 1 | 1 | 1046 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 58 |
| Mockito-30 | 2 | 1 | 1041 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 982 |
| Mockito-31 | 1 | 1 | 1040 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 783 |
| Mockito-32 | 1 | 1 | 1005 | 1/1 · 983 | 1/1 · 983 | 1/1 · 983 | 1/1 · 983 | 1/1 · 983 | 1/1 · 983 | 1/1 · 983 | 1/1 · 954 |
| Mockito-33 | 1 | 2 | 1001 | 0/2 · 170 | 0/2 · 7 | 0/2 · 7 | 0/2 · 76 | 0/2 · 76 | 0/2 · 86 | 0/2 · 54 | 2/2 · 685 |
| Mockito-34 | 1 | 2 | 883 | 1/2 · 21 | 0/2 · 0 | 0/2 · 0 | 1/2 · 21 | 1/2 · 21 | 1/2 · 5 | 1/2 · 21 | 2/2 · 615 |
| Mockito-35 | 3 | 4 | 852 | 4/4 · 33 | 3/4 · 11 | 3/4 · 11 | 3/4 · 12 | 3/4 · 12 | 0/4 · 1 | 3/4 · 11 | 4/4 · 636 |
| Mockito-36 | 1 | 2 | 847 | 1/2 · 11 | 0/2 · 2 | 0/2 · 2 | 1/2 · 8 | 1/2 · 8 | 1/2 · 11 | 1/2 · 8 | 2/2 · 811 |
| Mockito-37 | 2 | 2 | 846 | 2/2 · 168 | 0/2 · 2 | 0/2 · 2 | 1/2 · 24 | 1/2 · 24 | 1/2 · 22 | 1/2 · 22 | 2/2 · 306 |
| Mockito-38 | 1 | 2 | 747 | 1/2 · 12 | 1/2 · 6 | 1/2 · 6 | 1/2 · 12 | 1/2 · 12 | 1/2 · 12 | 1/2 · 12 | 2/2 · 102 |
| Mockito-6 | 19 | 7 | 1413 | 7/7 · 113 | 7/7 · 113 | 7/7 · 113 | 7/7 · 107 | 7/7 · 107 | 0/7 · 51 | 7/7 · 93 | 7/7 · 1089 |
| Mockito-7 | 1 | 1 | 1412 | 0/1 · 33 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 33 | 0/1 · 0 | 1/1 · 46 |
| Mockito-8 | 1 | 1 | 1411 | 1/1 · 37 | 1/1 · 19 | 1/1 · 19 | 1/1 · 34 | 1/1 · 34 | 1/1 · 37 | 1/1 · 16 | 1/1 · 45 |
| Mockito-9 | 1 | 3 | 1409 | 0/3 · 21 | 0/3 · 3 | 0/3 · 3 | 0/3 · 18 | 0/3 · 18 | 0/3 · 21 | 0/3 · 13 | 3/3 · 1107 |
| Time-10 | 16 | 2 | 3955 | 2/2 · 3754 | 2/2 · 577 | 2/2 · 690 | 2/2 · 1520 | 2/2 · 1914 | 2/2 · 3552 | 2/2 · 193 | 2/2 · 371 |
| Time-11 | 2 | 1 | 3950 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 8 |
| Time-12 | 4 | 8 | 3937 | 8/8 · 28 | 0/8 · 0 | 0/8 · 0 | 8/8 · 34 | 8/8 · 34 | 8/8 · 28 | 8/8 · 18 | 8/8 · 1674 |
| Time-13 | 2 | 1 | 3917 | 1/1 · 82 | 0/1 · 0 | 0/1 · 0 | 1/1 · 71 | 1/1 · 71 | 1/1 · 80 | 0/1 · 46 | 1/1 · 972 |
| Time-14 | 1 | 8 | 3907 | 8/8 · 96 | 0/8 · 466 | 0/8 · 647 | 0/8 · 0 | 0/8 · 1847 | 8/8 · 3360 | 8/8 · 1848 | 8/8 · 3877 |
| Time-15 | 1 | 1 | 3895 | 1/1 · 3580 | 1/1 · 477 | 1/1 · 653 | 1/1 · 1485 | 1/1 · 1936 | 1/1 · 2 | 1/1 · 202 | 1/1 · 3640 |
| Time-16 | 1 | 7 | 3894 | 7/7 · 17 | 0/7 · 459 | 7/7 · 647 | 7/7 · 12 | 7/7 · 12 | 7/7 · 947 | 0/7 · 0 | 7/7 · 2596 |
| Time-17 | 1 | 1 | 3884 | 1/1 · 3 | 1/1 · 3 | 1/1 · 3 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 3865 |
| Time-18 | 1 | 1 | 3874 | 1/1 · 3531 | 0/1 · 450 | 0/1 · 631 | 0/1 · 1367 | 0/1 · 1835 | 1/1 · 3332 | 1/1 · 1834 | 1/1 · 2546 |
| Time-19 | 1 | 1 | 3872 | 1/1 · 3529 | 1/1 · 457 | 1/1 · 631 | 1/1 · 1369 | 1/1 · 1837 | 1/1 · 3330 | 1/1 · 1832 | 1/1 · 3853 |
| Time-20 | 1 | 1 | 3869 | 1/1 · 3526 | 0/1 · 0 | 0/1 · 0 | 1/1 · 140 | 1/1 · 140 | 1/1 · 933 | 0/1 · 0 | 1/1 · 2577 |
| Time-22 | 1 | 2 | 3871 | 2/2 · 638 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 2/2 · 790 | 0/2 · 0 | 2/2 · 1875 |
| Time-23 | 1 | 1 | 3869 | 1/1 · 3523 | 1/1 · 463 | 1/1 · 642 | 1/1 · 3396 | 1/1 · 3541 | 1/1 · 3661 | 1/1 · 3253 | 1/1 · 3810 |
| Time-24 | 1 | 7 | 3867 | 7/7 · 3521 | 7/7 · 461 | 7/7 · 640 | 0/7 · 0 | 0/7 · 0 | 7/7 · 952 | 0/7 · 0 | 7/7 · 1038 |
| Time-25 | 1 | 3 | 3851 | 3/3 · 3505 | 0/3 · 455 | 0/3 · 629 | 1/3 · 1335 | 1/3 · 1802 | 3/3 · 3315 | 2/3 · 1778 | 3/3 · 3792 |
| Time-26 | 7 | 8 | 3847 | 8/8 · 3501 | 2/8 · 458 | 3/8 · 629 | 6/8 · 1328 | 6/8 · 1795 | 8/8 · 3311 | 8/8 · 1776 | 8/8 · 3788 |
| Time-27 | 1 | 1 | 3790 | 1/1 · 693 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 32 | 0/1 · 6 | 1/1 · 739 |
| Time-6 | 2 | 5 | 3999 | 5/5 · 3638 | 0/5 · 578 | 1/5 · 657 | 5/5 · 1437 | 5/5 · 1915 | 5/5 · 3445 | 1/5 · 1872 | 5/5 · 2663 |
| Time-7 | 1 | 2 | 3981 | 2/2 · 27 | 2/2 · 578 | 2/2 · 696 | 2/2 · 22 | 2/2 · 22 | 2/2 · 988 | 0/2 · 0 | 2/2 · 2703 |
| Time-8 | 1 | 1 | 3971 | 1/1 · 20 | 1/1 · 20 | 1/1 · 20 | 1/1 · 20 | 1/1 · 20 | 1/1 · 62 | 1/1 · 20 | 1/1 · 3950 |
| Time-9 | 44 | 1 | 3971 | 1/1 · 3640 | 1/1 · 3145 | 1/1 · 3151 | 1/1 · 3584 | 1/1 · 3706 | 1/1 · 3820 | 1/1 · 3370 | 1/1 · 3950 |

### Dev

The bugs the rules in `truth.py` / `score.py` were written while looking at.

**80 Defects4J bugs** (Cli, Closure, Codec, Collections, Compress, Csv, Gson, JacksonCore, JacksonDatabind, JacksonXml, Jsoup, JxPath, Lang, Math, Mockito, Time). For each bug-fixing commit, every tool's call graph was asked *which tests does this change reach?* Two things make an answer good: it must contain the test that actually catches the bug (Defects4J knows which — it fails before the fix and passes after), and it should be no bigger than it has to be. Defects4J also recorded, by running the suite, which test classes really load the changed code — the `d4j-relevant` row — so a selection can be compared with what really ran. The last column, `read`, is how much of each tool's own output the reading could use: an unresolvable row is dropped and counted rather than guessed at, so a low figure means the row beside it was computed from a fraction of what that tool actually emitted.

| tool | caught the bug's test?<br><sub>bugs where every triggering test was selected</sub> | tests selected<br><sub>share of the suite, mean</sub> | selection vs. what really ran<br><sub>against Defects4J's dynamic answer, median</sub> | covered what really ran?<br><sub>relevant classes with a test selected</sub> | read<br><sub>share of the tool's own rows the reading could use</sub> | in one line |
|---|---:|---:|---:|---:|---:|---|
| 1. **`AxiomEngine`** | 72 / 80 | 43.4% | 0.88× | 74.8% | 92.0% | skips the test that catches the bug on 8 of 80 bugs — not safe, whatever it saves |
| 2. `gitnexus` | 59 / 80 | 27.4% | 0.53× | 58.8% | 88.1% | skips the test that catches the bug on 21 of 80 bugs — not safe, whatever it saves |
| 3. `graphify` | 47 / 80 | 23.6% | 0.40× | 52.5% | 87.1% | skips the test that catches the bug on 33 of 80 bugs — not safe, whatever it saves |
| 4. `codegraph-dispatch` | 46 / 80 | 19.0% | 0.36× | 48.3% | 89.3% | skips the test that catches the bug on 34 of 80 bugs — not safe, whatever it saves |
| 5. `codegraph` | 44 / 80 | 16.3% | 0.24× | 44.0% | 89.3% | skips the test that catches the bug on 36 of 80 bugs — not safe, whatever it saves |
| 6. `code-review-graph-dispatch` | 24 / 80 | 8.4% | 0.01× | 25.9% | 39.2% | skips the test that catches the bug on 56 of 80 bugs — not safe, whatever it saves |
| 7. `code-review-graph` | 23 / 80 | 6.8% | 0.00× | 21.9% | 36.1% | skips the test that catches the bug on 57 of 80 bugs — not safe, whatever it saves |
| *`d4j-relevant`* | 80 / 80 | 53.7% | 1.00× | 100.0% | — | what Defects4J observed by running the tests — the answer to match |
| *`name-match`* | 36 / 80 | 5.0% | 0.03× | 21.3% | — | grep for the class name: small, and wrong on a third of the bugs |
| *`all-tests`* | 80 / 80 | 100.0% | 1.48× | 100.0% | — | run everything: always safe, never minimal |

**Both node keys.** `Type#name/arity` is what `score.py` uses: a tool reporting a parameter list names one overload, a tool reporting none is read as every overload of the name. `Type#name` is the same rows with the parameter lists dropped from every tool alike. Only a tool that reports parameters can move between the two, and `params` is the share of its rows that carry one.

| tool | bugs | params | safe<br><sub>`Type#name/arity`</sub> | safe<br><sub>`Type#name`</sub> | selection<br><sub>`Type#name/arity`</sub> | selection<br><sub>`Type#name`</sub> |
|---|---:|---:|---:|---:|---:|---:|
| **`AxiomEngine`** | 80 | 100.0% | 90.0% | 90.0% | 43.4% | 44.3% |
| `gitnexus` | 80 | 7.7% | 73.8% | 75.0% (+1) | 27.4% | 29.0% |
| `graphify` | 80 | 0.0% | 58.8% | 58.8% | 23.6% | 23.6% |
| `codegraph-dispatch` | 80 | 93.1% | 57.5% | 70.0% (+10) | 19.0% | 29.6% |
| `codegraph` | 80 | 91.2% | 55.0% | 70.0% (+12) | 16.3% | 28.3% |
| `code-review-graph-dispatch` | 80 | 0.0% | 30.0% | 30.0% | 8.4% | 8.4% |
| `code-review-graph` | 80 | 0.0% | 28.7% | 28.7% | 6.8% | 6.8% |

<details><summary>every column</summary>

**Test impact on 80 Defects4J bugs** (Cli, Closure, Codec, Collections, Compress, Csv, Gson, JacksonCore, JacksonDatabind, JacksonXml, Jsoup, JxPath, Lang, Math, Mockito, Time): for each fix, the tests a tool's call graph says the change reaches, against the tests Defects4J observed. `trigger recall` — the triggering tests (fail on buggy, pass on fixed) the answer contains; `safe` — bugs where it contained all of them; `precision` — impacted tests whose class Defects4J saw load a modified class; `relevant recall` — of the tests in those classes, the share selected (an answer that finds the one triggering test but a third of the relevant tests is not safe in general); `selection` — share of the suite selected; FP / FN — impacted tests outside the relevant classes / relevant tests not impacted, per bug; `read` — of the rows the tool emitted, the share the resolver could use (a row whose caller or callee is ambiguous, unknown or owner-less is dropped and counted, never guessed), pooled over the tool's bugs: a tool scored on a fraction of what it said is read here rather than only in validate.py. Ranked by trigger recall, then relevant recall, then selection. Reference rows: the dynamic class-level answer, the grep answer, the whole suite. Every tool is read the same way — its `calls` edges through callgraph-benchmark's resolver, plus the dispatch step — not through its own impact command (v1 drove Graphify through its own `affected` traversal, whose name-seeding failed on most Lang bugs; here Graphify is credited for the edges it emitted).

| | | | RIGHT | | | | READ | MINIMAL | | | | | |
| rank | tool | bugs | safe<br><sub>every triggering test found</sub> | trigger recall<br><sub>mean</sub> | relevant recall<br><sub>of the tests in relevant classes</sub> | relevant classes covered<br><sub>≥1 test impacted (v1's definition)</sub> | read<br><sub>rows the resolver could use</sub> | selection<br><sub>share of suite</sub> | selection when safe<br><sub>share of suite, safe bugs only</sub> | vs dynamic answer<br><sub>impacted / relevant tests, median</sub> | precision<br><sub>vs relevant classes</sub> | FP / bug | FN / bug |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | **`AxiomEngine`** | 80 | 90.0% | 90.8% | 60.0% | 74.8% | 92.0% | 43.4% | 47.8% | 0.88× | 81.8% | 483.2 | 245.8 |
| 2 | `gitnexus` | 80 | 73.8% | 75.5% | 44.2% | 58.8% | 88.1% | 27.4% | 34.0% | 0.53× | 85.9% | 227.1 | 413.7 |
| 3 | `graphify` | 80 | 58.8% | 61.9% | 37.6% | 52.5% | 87.1% | 23.6% | 33.9% | 0.40× | 89.5% | 45.1 | 485.8 |
| 4 | `codegraph-dispatch` | 80 | 57.5% | 60.1% | 31.6% | 48.3% | 89.3% | 19.0% | 26.5% | 0.36× | 85.1% | 55.3 | 453.6 |
| 5 | `codegraph` | 80 | 55.0% | 57.6% | 28.6% | 44.0% | 89.3% | 16.3% | 24.7% | 0.24× | 84.6% | 43.8 | 460.8 |
| 6 | `code-review-graph-dispatch` | 80 | 30.0% | 32.2% | 17.2% | 25.9% | 39.2% | 8.4% | 15.5% | 0.01× | 87.8% | 66.5 | 537.8 |
| 7 | `code-review-graph` | 80 | 28.7% | 30.3% | 15.4% | 21.9% | 36.1% | 6.8% | 15.3% | 0.00× | 96.4% | 0.5 | 549.8 |
| — | *`d4j-relevant`* | 80 | 100.0% | 100.0% | 100.0% | 100.0% | — | 53.7% | 53.7% | 1.00× | 100.0% | 0.0 | 0.0 |
| — | *`name-match`* | 80 | 45.0% | 49.4% | 23.1% | 21.3% | — | 5.0% | 8.6% | 0.03× | 99.6% | 0.7 | 527.2 |
| — | *`all-tests`* | 80 | 100.0% | 100.0% | 100.0% | 100.0% | — | 100.0% | 100.0% | 1.48× | 53.7% | 1292.2 | 0.0 |

</details>

Per bug: `triggering tests found / total · impacted tests`. A bug whose triggering test the dynamic class-level answer itself misses (`d4j-relevant` < total) is one where the test is declared outside the classes that load the modified class — inherited, or run through a suite — and is reported as such.

| bug | changed | trigger | tests | `AxiomEngine` | `code-review-graph` | `code-review-graph-dispatch` | `codegraph` | `codegraph-dispatch` | `gitnexus` | `graphify` | *`d4j-relevant`* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Cli-1 | 13 | 1 | 95 | 1/1 · 74 | 1/1 · 72 | 1/1 · 72 | 1/1 · 68 | 1/1 · 73 | 1/1 · 74 | 1/1 · 74 | 1/1 · 77 |
| Cli-2 | 1 | 1 | 96 | 1/1 · 75 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 35 | 1/1 · 75 | 1/1 · 73 | 1/1 · 69 |
| Cli-3 | 1 | 1 | 101 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 |
| Cli-4 | 1 | 2 | 103 | 2/2 · 81 | 0/2 · 0 | 0/2 · 0 | 0/2 · 0 | 0/2 · 39 | 2/2 · 81 | 0/2 · 77 | 2/2 · 85 |
| Cli-5 | 1 | 2 | 105 | 2/2 · 85 | 1/2 · 55 | 1/2 · 55 | 2/2 · 74 | 2/2 · 80 | 2/2 · 85 | 2/2 · 83 | 2/2 · 88 |
| Closure-1 | 1 | 8 | 7915 | 8/8 · 7539 | 0/8 · 0 | 0/8 · 0 | 0/8 · 60 | 0/8 · 853 | 2/8 · 4047 | 0/8 · 673 | 8/8 · 374 |
| Closure-2 | 1 | 1 | 7868 | 1/1 · 7492 | 1/1 · 2104 | 1/1 · 2431 | 0/1 · 841 | 0/1 · 853 | 1/1 · 4044 | 0/1 · 0 | 1/1 · 6755 |
| Closure-3 | 2 | 3 | 7869 | 3/3 · 7493 | 0/3 · 0 | 0/3 · 2426 | 0/3 · 846 | 0/3 · 858 | 3/3 · 4045 | 0/3 · 917 | 3/3 · 358 |
| Closure-4 | 1 | 3 | 7863 | 3/3 · 7487 | 0/3 · 31 | 0/3 · 31 | 3/3 · 3488 | 3/3 · 3500 | 3/3 · 4039 | 0/3 · 761 | 3/3 · 6883 |
| Closure-5 | 1 | 1 | 7786 | 1/1 · 7411 | 0/1 · 0 | 0/1 · 2379 | 0/1 · 834 | 0/1 · 846 | 0/1 · 3969 | 0/1 · 911 | 1/1 · 314 |
| Codec-1 | 3 | 5 | 206 | 5/5 · 77 | 0/5 · 31 | 0/5 · 31 | 5/5 · 26 | 5/5 · 26 | 5/5 · 73 | 5/5 · 44 | 5/5 · 90 |
| Codec-2 | 1 | 2 | 224 | 2/2 · 67 | 0/2 · 20 | 0/2 · 20 | 2/2 · 17 | 2/2 · 17 | 0/2 · 56 | 0/2 · 58 | 2/2 · 50 |
| Codec-3 | 1 | 1 | 276 | 1/1 · 36 | 1/1 · 12 | 1/1 · 12 | 0/1 · 22 | 0/1 · 22 | 1/1 · 36 | 1/1 · 17 | 1/1 · 21 |
| Codec-4 | 1 | 2 | 292 | 2/2 · 50 | 0/2 · 42 | 0/2 · 42 | 2/2 · 67 | 2/2 · 67 | 2/2 · 86 | 1/2 · 83 | 2/2 · 72 |
| Codec-5 | 1 | 2 | 303 | 2/2 · 66 | 0/2 · 30 | 0/2 · 30 | 1/2 · 12 | 1/2 · 12 | 1/2 · 11 | 1/2 · 13 | 2/2 · 83 |
| Collections-1 | 2 | 4 | 5856 | 2/4 · 35 | 0/4 · 0 | 0/4 · 0 | 2/4 · 32 | 2/4 · 32 | 2/4 · 35 | 2/4 · 31 | 4/4 · 53 |
| Collections-2 | 38 | 1 | 5857 | 1/1 · 10 | 1/1 · 11 | 1/1 · 11 | 1/1 · 481 | 1/1 · 481 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 |
| Collections-3 | 1 | 1 | 5859 | 1/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 171 | 1/1 · 171 | 1/1 · 1 | 1/1 · 1 | 1/1 · 138 |
| Collections-4 | 2 | 3 | 5861 | 3/3 · 4797 | 0/3 · 0 | 0/3 · 2 | 3/3 · 62 | 3/3 · 62 | 3/3 · 4241 | 3/3 · 24 | 3/3 · 23 |
| Collections-5 | 1 | 1 | 5862 | 1/1 · 5505 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 4 | 0/1 · 4 | 1/1 · 68 |
| Compress-1 | 1 | 1 | 73 | 0/1 · 12 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 26 |
| Compress-2 | 7 | 1 | 84 | 1/1 · 50 | 1/1 · 26 | 1/1 · 26 | 0/1 · 32 | 0/1 · 32 | 1/1 · 26 | 1/1 · 26 | 1/1 · 53 |
| Compress-3 | 12 | 1 | 121 | 1/1 · 72 | 1/1 · 46 | 1/1 · 46 | 1/1 · 38 | 1/1 · 38 | 1/1 · 47 | 1/1 · 44 | 1/1 · 82 |
| Compress-4 | 4 | 10 | 121 | 10/10 · 49 | 0/10 · 46 | 0/10 · 46 | 9/10 · 34 | 9/10 · 34 | 10/10 · 58 | 9/10 · 34 | 10/10 · 83 |
| Compress-5 | 1 | 1 | 146 | 1/1 · 52 | 0/1 · 23 | 0/1 · 42 | 1/1 · 32 | 1/1 · 55 | 1/1 · 42 | 1/1 · 42 | 1/1 · 101 |
| Csv-1 | 1 | 1 | 55 | 1/1 · 36 | 0/1 · 5 | 0/1 · 5 | 1/1 · 37 | 1/1 · 37 | 1/1 · 37 | 1/1 · 33 | 1/1 · 50 |
| Csv-2 | 1 | 1 | 132 | 1/1 · 9 | 1/1 · 23 | 1/1 · 23 | 1/1 · 9 | 1/1 · 9 | 1/1 · 10 | 1/1 · 9 | 1/1 · 63 |
| Csv-3 | 1 | 3 | 134 | 3/3 · 58 | 0/3 · 0 | 0/3 · 0 | 3/3 · 61 | 3/3 · 61 | 3/3 · 57 | 3/3 · 47 | 3/3 · 77 |
| Csv-4 | 1 | 1 | 178 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 2 | 1/1 · 125 |
| Csv-5 | 1 | 1 | 182 | 1/1 · 27 | 1/1 · 63 | 1/1 · 63 | 0/1 · 25 | 0/1 · 25 | 0/1 · 17 | 0/1 · 25 | 1/1 · 139 |
| Gson-1 | 2 | 1 | 720 | 1/1 · 460 | 0/1 · 17 | 0/1 · 17 | 1/1 · 231 | 1/1 · 233 | 0/1 · 76 | 1/1 · 454 | 1/1 · 449 |
| Gson-2 | 3 | 1 | 967 | 1/1 · 816 | 0/1 · 1 | 0/1 · 1 | 0/1 · 14 | 0/1 · 14 | 0/1 · 65 | 1/1 · 350 | 1/1 · 728 |
| Gson-3 | 3 | 2 | 971 | 2/2 · 820 | 0/2 · 1 | 0/2 · 10 | 0/2 · 3 | 0/2 · 3 | 2/2 · 69 | 2/2 · 343 | 2/2 · 667 |
| Gson-4 | 6 | 3 | 984 | 3/3 · 867 | 0/3 · 2 | 0/3 · 2 | 3/3 · 552 | 3/3 · 552 | 3/3 · 304 | 3/3 · 526 | 3/3 · 911 |
| Gson-5 | 1 | 1 | 984 | 1/1 · 523 | 0/1 · 1 | 0/1 · 1 | 1/1 · 7 | 1/1 · 7 | 1/1 · 65 | 1/1 · 362 | 1/1 · 9 |
| JacksonCore-1 | 3 | 1 | 207 | 1/1 · 49 | 0/1 · 0 | 0/1 · 0 | 1/1 · 45 | 1/1 · 48 | 1/1 · 49 | 1/1 · 49 | 1/1 · 170 |
| JacksonCore-2 | 8 | 2 | 215 | 2/2 · 138 | 0/2 · 0 | 0/2 · 0 | 2/2 · 130 | 2/2 · 130 | 2/2 · 138 | 2/2 · 141 | 2/2 · 184 |
| JacksonCore-3 | 1 | 1 | 221 | 1/1 · 146 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 17 | 0/1 · 0 | 1/1 · 139 |
| JacksonCore-4 | 1 | 1 | 241 | 1/1 · 159 | 1/1 · 2 | 1/1 · 2 | 1/1 · 153 | 1/1 · 153 | 1/1 · 159 | 1/1 · 2 | 1/1 · 199 |
| JacksonCore-5 | 1 | 1 | 244 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 | 1/1 · 4 |
| JacksonDatabind-1 | 1 | 1 | 1119 | 1/1 · 523 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 595 |
| JacksonDatabind-2 | 2 | 1 | 1252 | 1/1 · 1146 | 1/1 · 9 | 1/1 · 9 | 1/1 · 676 | 1/1 · 676 | 1/1 · 75 | 1/1 · 680 | 1/1 · 1208 |
| JacksonDatabind-3 | 2 | 1 | 1255 | 1/1 · 1149 | 0/1 · 0 | 0/1 · 0 | 1/1 · 673 | 1/1 · 673 | 0/1 · 59 | 1/1 · 677 | 1/1 · 1211 |
| JacksonDatabind-4 | 2 | 1 | 1260 | 1/1 · 1152 | 0/1 · 0 | 0/1 · 0 | 1/1 · 675 | 1/1 · 675 | 0/1 · 59 | 1/1 · 679 | 1/1 · 1215 |
| JacksonDatabind-5 | 1 | 1 | 1261 | 1/1 · 1153 | 0/1 · 14 | 0/1 · 14 | 0/1 · 745 | 0/1 · 745 | 0/1 · 101 | 0/1 · 721 | 1/1 · 1216 |
| JacksonXml-1 | 1 | 3 | 160 | 0/3 · 6 | 0/3 · 11 | 0/3 · 11 | 0/3 · 11 | 0/3 · 11 | 0/3 · 2 | 0/3 · 2 | 3/3 · 134 |
| JacksonXml-2 | 26 | 1 | 164 | 1/1 · 88 | 1/1 · 107 | 1/1 · 107 | 0/1 · 23 | 0/1 · 23 | 0/1 · 10 | 0/1 · 9 | 1/1 · 108 |
| JacksonXml-3 | 1 | 1 | 163 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 1 | 1/1 · 136 |
| JacksonXml-4 | 1 | 1 | 168 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 138 |
| JacksonXml-5 | 1 | 1 | 193 | 1/1 · 171 | 0/1 · 0 | 0/1 · 0 | 1/1 · 101 | 1/1 · 101 | 1/1 · 155 | 0/1 · 0 | 1/1 · 163 |
| Jsoup-1 | 1 | 1 | 139 | 1/1 · 126 | 0/1 · 0 | 0/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 126 | 1/1 · 126 | 1/1 · 129 |
| Jsoup-2 | 1 | 1 | 140 | 1/1 · 127 | 0/1 · 0 | 0/1 · 1 | 0/1 · 0 | 0/1 · 0 | 1/1 · 127 | 1/1 · 127 | 1/1 · 129 |
| Jsoup-3 | 48 | 3 | 146 | 3/3 · 144 | 3/3 · 69 | 3/3 · 69 | 3/3 · 144 | 3/3 · 144 | 3/3 · 144 | 3/3 · 133 | 3/3 · 146 |
| Jsoup-4 | 4 | 2 | 193 | 2/2 · 168 | 0/2 · 0 | 0/2 · 0 | 2/2 · 4 | 2/2 · 4 | 2/2 · 168 | 2/2 · 168 | 2/2 · 170 |
| Jsoup-5 | 1 | 1 | 194 | 1/1 · 166 | 0/1 · 37 | 0/1 · 37 | 0/1 · 0 | 0/1 · 0 | 1/1 · 166 | 1/1 · 166 | 1/1 · 168 |
| JxPath-1 | 2 | 2 | 308 | 2/2 · 307 | 0/2 · 0 | 0/2 · 31 | 0/2 · 0 | 2/2 · 254 | 2/2 · 295 | 2/2 · 258 | 2/2 · 296 |
| JxPath-2 | 2 | 1 | 308 | 1/1 · 42 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 42 | 1/1 · 42 | 1/1 · 42 | 1/1 · 297 |
| JxPath-3 | 2 | 1 | 315 | 1/1 · 65 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 0/1 · 0 | 1/1 · 65 | 0/1 · 0 | 1/1 · 301 |
| JxPath-4 | 7 | 6 | 327 | 6/6 · 326 | 0/6 · 0 | 0/6 · 31 | 6/6 · 252 | 6/6 · 273 | 6/6 · 326 | 6/6 · 273 | 6/6 · 315 |
| JxPath-5 | 1 | 1 | 336 | 0/1 · 4 | 0/1 · 0 | 0/1 · 0 | 0/1 · 4 | 0/1 · 4 | 0/1 · 4 | 0/1 · 4 | 1/1 · 324 |
| Lang-1 | 1 | 1 | 2296 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 | 1/1 · 10 | 1/1 · 173 |
| Lang-3 | 1 | 1 | 2291 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 | 1/1 · 9 | 1/1 · 172 |
| Lang-4 | 3 | 1 | 2290 | 1/1 · 44 | 0/1 · 24 | 0/1 · 24 | 1/1 · 4 | 1/1 · 4 | 1/1 · 31 | 1/1 · 28 | 1/1 · 137 |
| Lang-5 | 1 | 1 | 2276 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 5 | 1/1 · 13 |
| Lang-6 | 1 | 1 | 2268 | 1/1 · 38 | 1/1 · 21 | 1/1 · 21 | 0/1 · 0 | 0/1 · 0 | 1/1 · 24 | 1/1 · 22 | 1/1 · 142 |
| Math-1 | 2 | 2 | 5117 | 2/2 · 2372 | 0/2 · 22 | 1/2 · 196 | 2/2 · 185 | 2/2 · 206 | 2/2 · 324 | 2/2 · 203 | 2/2 · 313 |
| Math-2 | 1 | 1 | 5090 | 1/1 · 89 | 0/1 · 0 | 0/1 · 0 | 0/1 · 1 | 0/1 · 1 | 1/1 · 110 | 0/1 · 1 | 1/1 · 16 |
| Math-3 | 1 | 1 | 4954 | 1/1 · 12 | 0/1 · 0 | 0/1 · 148 | 1/1 · 1189 | 1/1 · 1395 | 1/1 · 1707 | 1/1 · 814 | 1/1 · 2197 |
| Math-4 | 2 | 2 | 4938 | 2/2 · 14 | 0/2 · 0 | 0/2 · 0 | 2/2 · 14 | 2/2 · 14 | 2/2 · 56 | 0/2 · 0 | 2/2 · 52 |
| Math-5 | 1 | 1 | 4867 | 1/1 · 2178 | 0/1 · 0 | 0/1 · 0 | 1/1 · 6 | 1/1 · 6 | 1/1 · 16 | 0/1 · 4 | 1/1 · 257 |
| Mockito-1 | 1 | 26 | 1425 | 1/26 · 38 | 0/26 · 0 | 0/26 · 0 | 1/26 · 35 | 1/26 · 35 | 1/26 · 26 | 1/26 · 31 | 26/26 · 965 |
| Mockito-2 | 2 | 3 | 1442 | 3/3 · 26 | 0/3 · 0 | 0/3 · 0 | 3/3 · 30 | 3/3 · 30 | 3/3 · 28 | 0/3 · 4 | 3/3 · 31 |
| Mockito-3 | 2 | 9 | 1425 | 1/9 · 38 | 0/9 · 0 | 0/9 · 0 | 1/9 · 35 | 1/9 · 35 | 1/9 · 26 | 1/9 · 31 | 9/9 · 965 |
| Mockito-4 | 3 | 4 | 1433 | 4/4 · 1183 | 3/4 · 3 | 3/4 · 3 | 0/4 · 20 | 0/4 · 20 | 4/4 · 1180 | 0/4 · 11 | 4/4 · 1315 |
| Mockito-5 | 1 | 1 | 1423 | 0/1 · 18 | 0/1 · 0 | 0/1 · 0 | 0/1 · 18 | 0/1 · 18 | 0/1 · 18 | 0/1 · 9 | 1/1 · 26 |
| Time-1 | 2 | 1 | 4042 | 1/1 · 165 | 0/1 · 45 | 0/1 · 45 | 1/1 · 153 | 1/1 · 153 | 1/1 · 170 | 0/1 · 93 | 1/1 · 4011 |
| Time-2 | 3 | 1 | 4042 | 1/1 · 165 | 1/1 · 45 | 1/1 · 45 | 1/1 · 153 | 1/1 · 153 | 1/1 · 170 | 1/1 · 93 | 1/1 · 4011 |
| Time-3 | 10 | 5 | 4039 | 5/5 · 42 | 0/5 · 0 | 5/5 · 689 | 5/5 · 29 | 5/5 · 29 | 5/5 · 29 | 5/5 · 42 | 5/5 · 1307 |
| Time-4 | 1 | 1 | 4015 | 1/1 · 28 | 1/1 · 28 | 1/1 · 28 | 1/1 · 18 | 1/1 · 18 | 1/1 · 28 | 1/1 · 18 | 1/1 · 770 |
| Time-5 | 1 | 3 | 4014 | 3/3 · 21 | 3/3 · 21 | 3/3 · 21 | 0/3 · 0 | 0/3 · 0 | 3/3 · 21 | 0/3 · 0 | 3/3 · 1950 |

**How to read a row.** A row is the tool's `calls` edges read by this repository, not the output of the tool's own impact command. Three rules are ours, not the tool's: the reverse closure is **unbounded** (a tool may bound its own); the scorer adds a **class-hierarchy override step**, which no source-only tool draws; and a callee reported **without a parameter list is credited as every overload** of that name, so a tool that reports no parameters is given reach it never claimed. All three are generous. Where a tool ships its own traversal, its own answer is the smaller one — `graphify.affected`, for instance, is a 12-relation walk bounded at `depth=2`. See `relations.py` for what each adapter reads.
<!-- tia:end -->
