# Vendored, for cross-checking only

`ClassFileOracle.java` is copied from the `axiomengine` repository
(`test/java/tools/ClassFileOracle.java`), which is one of the tools under test.

**It is not the benchmark's ground truth.** `oracle/ClassfileGroundTruth.java` is, and it is written
independently and verified against `oracle/javap_reader.py` (§1.1 of `docs/PROTOCOL.md`).

This copy exists for one purpose: a third reading of the same class files, by a third implementation,
against which the benchmark's conventions layer can be compared. Agreement is evidence; it is not
authority, and a disagreement would be investigated on the merits rather than resolved in either
file's favour.

Using a tool's own oracle AS ground truth would be a conflict of interest. Using it as one of several
cross-checks is the opposite: it is the check most likely to catch a convention this benchmark got
wrong, because it was written by people solving the same problem independently.

| | |
|---|---|
| source repo | `ANONYMIZED/axiomengine` |
| commit | `f4fe0b6559f3189ef4596e39fac89db2ed6c7e5f` |
| path | `test/java/tools/ClassFileOracle.java` |
| sha256 | `994a6c84f5e9f41b775dadcb2a03ccd47084d35a8a93a0fd0c37c126d9c12377` |
| convention difference | flattens nested types to `pkg.SimpleName`; this benchmark keeps the full chain (`docs/PROTOCOL.md` §3), so comparisons project through that flattening |
