# AxiomEngine — Paper Artifact

Anonymous artifact accompanying the paper *AxiomEngine: A Semantic Code
Intelligence Graph for Coding Agents* (double-blind review). It contains three
components, one per folder.

## `axiomengine/`

Source code of the engine. Per-file fact extraction (a tree-sitter front end
for most languages and the TypeScript compiler's parser for TypeScript and
JavaScript), the per-language declarative rule sets (Java, TypeScript, Python;
JavaScript and C# in beta), the Soufflé build, the graph store, and the
command-line and tool-calling interface with the two query primitives,
`impact` and `path`. Build and usage instructions are under `docs/`.

## `callgraph-benchmark/`

The call-resolution benchmark (RQ1). Ten open-source subjects, five Java and
five TypeScript, with compiler-derived oracles: Java ground truth from
compiled bytecode and TypeScript ground truth from the TypeScript type
checker. Includes the harnesses for the engine and the four lightweight
baseline builders, and per-call results for the 33,257 Java and 9,829
TypeScript single-target call groups scored in the paper.

## `defects4j/`

The change-impact study (RQ2). Per-bug test selections and scores for all 828
Defects4J bugs (80 development, 748 held-out) for the engine, the four
baseline builders, and the reference selectors, together with the scoring
code. `release/` holds the run manifest, provenance, aggregate results, and
validation logs. The full per-bug run archives (roughly 50 GB of compressed
working trees, split per project) are published as release assets rather than
tracked files, because of their size:
<https://github.com/dvpu2tg/AxiomEngine/releases/tag/d4j-run-archives>.
The release also carries the run manifest, provenance, results, checksums, and
logs under their original names.

## Environment

Results in the paper were produced with OpenJDK 24.0.2, Node v25.2.1,
Python 3.12.3, and Soufflé 2.5.
