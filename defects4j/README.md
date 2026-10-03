# Defects4J results against Tree-sitter-based graph builders

Evidence for a test-impact benchmark on Defects4J: every bug (828, 16 projects) read by five source-only call-graph builders and scored against what Defects4J observed by running the tests — which tests a change reaches, and whether the tests that actually catch the bug are among them. The headline is the **748 held-out bugs**, scored once after the benchmark's rules were frozen; the other 80 are the development bugs the rules were written against, reported separately.

**Current release: [`d4j-2026-09-24-engine-ENGINE-COMMIT`](../../releases/tag/d4j-2026-09-24-engine-ENGINE-COMMIT)** — run 2026-09-24, 828 of 828 bugs scored.

## What ran

| tool | package | version | pinned |
|---|---|---|---|
| AxiomEngine | [anonymous-org/axiomengine](ANONYMIZED-URL) | commit `ENGINE-COMMIT` | no release version yet: pinned by the exact commit that ran |
| Code-Review-Graph | PyPI `code-review-graph` | 2.3.8 | installed from a committed requirements lock |
| Graphify | PyPI `graphifyy` | 0.9.58 | installed from a committed requirements lock |
| CodeGraph | npm `@colbymchenry/codegraph` | 1.6.0 | installed from a committed package-lock |
| GitNexus | npm `gitnexus` | 1.6.11 | installed from a committed package-lock |

| harness | commit |
|---|---|
| benchmark-test-impact (truth, walk, scorer; private) | `d9599b49ffe399d0602f5d8fcdf437cd63ae3f07` |
| callgraph-benchmark (tool adapters and resolver; private) | `dd3bf981e19d326bdb67c3b6c1f027a0cfeb8a14` |

Toolchain: openjdk version "24.0.2" 2025-07-15; Node v25.2.1; Python 3.12.3; Soufflé 2.5. Machine: GCP c3-standard-22 (Intel(R) Xeon(R) Platinum 8481C CPU @ 2.70GHz, 22 vCPU, Ubuntu 24.04.5 LTS). runall.py -j 16 (bugs in parallel; each bug runs its tools one after another; every tool warmed once before). Each commit above is also tagged `d4j-2026-09-24` in its repository.

## Results

A bug is **safe** for a selector when every test that fails on the bug is among the tests it selects. **Selection** is the share of the bug's test suite it selects, averaged over bugs. **vs Defects4J (median bug)** is, for the median bug, how many tests the selector picks for every test Defects4J's own class-level set picks (the tests Defects4J observed loading a modified class): 1.00x selects as many as that dynamic reference, below 1.00x fewer; it compares counts, not the tests themselves. **F1** is the harmonic mean of precision and relevant-test recall against that same set, so a test wrongly selected and a test wrongly skipped both count; **bugs safe** is beside it because those two mistakes do not cost the same.

**748 held-out bugs**, scored once with the rules frozen:

| selector | bugs safe | selection | vs Defects4J (median bug) | F1 |
|---|---:|---:|---:|---:|
| AxiomEngine | 94.9% (710/748) | 52.2% | 0.98x | 72.4 |
| GitNexus | 61.5% (460/748) | 27.4% | 0.56x | 54.3 |
| CodeGraph | 52.3% (391/748) | 21.2% | 0.25x | 44.8 |
| Graphify | 48.7% (364/748) | 17.0% | 0.11x | 41.3 |
| Code-Review-Graph | 21.9% (164/748) | 5.4% | 0.00x | 18.7 |
| Name-Match (grep) | 46.8% (350/748) | 2.8% | 0.03x | 32.5 |
| Defects4J observed (dynamic reference) | 100.0% (748/748) | 47.6% | 1.00x | 100.0 |
| Every test (reference) | 100.0% (748/748) | 100.0% | 2.07x | 64.5 |

The same selectors on the development bugs, and on all bugs together — **bugs safe**:

| selector | held-out (748) | development (80) | all (828) |
|---|---:|---:|---:|
| AxiomEngine | 94.9% (710) | 90.0% (72) | 94.4% (782) |
| GitNexus | 61.5% (460) | 73.8% (59) | 62.7% (519) |
| CodeGraph | 52.3% (391) | 55.0% (44) | 52.5% (435) |
| Graphify | 48.7% (364) | 58.8% (47) | 49.6% (411) |
| Code-Review-Graph | 21.9% (164) | 28.8% (23) | 22.6% (187) |
| Name-Match (grep) | 46.8% (350) | 45.0% (36) | 46.6% (386) |

For scale: running only the tests that fail on the bug would select 0.23% of the suite. RESULTS.md in the release has every table, including one row per bug. The two `-dispatch` variants of CodeGraph and Code-Review-Graph it also scores are left out here.

<a href="ANONYMIZED-URL"><img src="axiomengine-logo.jpg" alt="AxiomEngine" width="320"></a>

To see it in action: [ANONYMIZED-URL](ANONYMIZED-URL)

## The release assets

One zstd-compressed archive per project, `<project>.tar.zst`; the large ones are split into `.partNN` pieces (GitHub's 2 GB asset limit). Unpack with `zstd -dc Cli.tar.zst | tar -x`, or for a split one `cat Closure.tar.zst.part* | zstd -d | tar -x`. Each archive holds, per bug: the Defects4J metadata and the scored truth (`meta/`), every builder's canonical edge file (`edges/<tool>/<bug>.jsonl`), every builder's own database exactly as the tool wrote it (`native/<tool>.tgz`), timings and logs. `MANIFEST.json` carries each bug's sha256 and `SHA256SUMS` the assets'. `PROVENANCE.json` records what ran. `isolation-audit.txt` lists anything written outside a bug's own directory during the run, and `sequential-check.json` compares two bugs per project run again one at a time against the parallel run.

### Download

| project | bugs | archive | size |
|---|---:|---|---:|
| Cli | 39 | [Cli.tar.zst](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Cli.tar.zst) | 0.26 GB |
| Closure | 174 | `Closure.tar.zst` in 18 parts: [00](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part00) [01](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part01) [02](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part02) [03](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part03) [04](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part04) [05](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part05) [06](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part06) [07](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part07) [08](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part08) [09](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part09) [10](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part10) [11](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part11) [12](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part12) [13](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part13) [14](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part14) [15](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part15) [16](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part16) [17](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Closure.tar.zst.part17) | 35.11 GB |
| Codec | 18 | [Codec.tar.zst](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Codec.tar.zst) | 0.23 GB |
| Collections | 28 | `Collections.tar.zst` in 2 parts: [00](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Collections.tar.zst.part00) [01](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Collections.tar.zst.part01) | 2.12 GB |
| Compress | 47 | [Compress.tar.zst](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Compress.tar.zst) | 1.23 GB |
| Csv | 16 | [Csv.tar.zst](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Csv.tar.zst) | 0.09 GB |
| Gson | 18 | [Gson.tar.zst](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Gson.tar.zst) | 0.52 GB |
| JacksonCore | 26 | [JacksonCore.tar.zst](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/JacksonCore.tar.zst) | 0.77 GB |
| JacksonDatabind | 110 | `JacksonDatabind.tar.zst` in 7 parts: [00](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/JacksonDatabind.tar.zst.part00) [01](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/JacksonDatabind.tar.zst.part01) [02](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/JacksonDatabind.tar.zst.part02) [03](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/JacksonDatabind.tar.zst.part03) [04](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/JacksonDatabind.tar.zst.part04) [05](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/JacksonDatabind.tar.zst.part05) [06](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/JacksonDatabind.tar.zst.part06) | 12.57 GB |
| JacksonXml | 6 | [JacksonXml.tar.zst](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/JacksonXml.tar.zst) | 0.07 GB |
| Jsoup | 93 | [Jsoup.tar.zst](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Jsoup.tar.zst) | 1.83 GB |
| JxPath | 22 | [JxPath.tar.zst](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/JxPath.tar.zst) | 0.47 GB |
| Lang | 61 | `Lang.tar.zst` in 2 parts: [00](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Lang.tar.zst.part00) [01](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Lang.tar.zst.part01) | 3.60 GB |
| Math | 106 | `Math.tar.zst` in 6 parts: [00](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Math.tar.zst.part00) [01](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Math.tar.zst.part01) [02](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Math.tar.zst.part02) [03](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Math.tar.zst.part03) [04](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Math.tar.zst.part04) [05](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Math.tar.zst.part05) | 11.54 GB |
| Mockito | 38 | `Mockito.tar.zst` in 2 parts: [00](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Mockito.tar.zst.part00) [01](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Mockito.tar.zst.part01) | 2.40 GB |
| Time | 26 | `Time.tar.zst` in 2 parts: [00](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Time.tar.zst.part00) [01](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/Time.tar.zst.part01) | 2.99 GB |

Alongside them: [MANIFEST.json](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/MANIFEST.json), [PROVENANCE.json](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/PROVENANCE.json), [README.md](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/README.md), [RESULTS.md](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/RESULTS.md), [SHA256SUMS](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/SHA256SUMS), [fairness.log](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/fairness.log), [isolation-audit.txt](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/isolation-audit.txt), [localize.log](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/localize.log), [sequential-check.json](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/sequential-check.json), [validate.log](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/validate.log).

Total 75.8 GB in 58 files. Check a download against [SHA256SUMS](../../releases/download/d4j-2026-09-24-engine-ENGINE-COMMIT/SHA256SUMS) with `sha256sum -c SHA256SUMS --ignore-missing`.

