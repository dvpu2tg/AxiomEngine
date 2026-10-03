#!/usr/bin/env bash
# WALA — the academic standard for exactly this problem — as an independently-written competitor
# on a declared `bytecode` budget (issue #6). Three configurations, three rows, reported apart:
#   wala-cha   class-hierarchy analysis        every subtype that declares the member
#   wala-rta   rapid type analysis             CHA pruned to instantiated types
#   wala-0cfa  context-insensitive points-to   the sharpest of the three
# The rows read the SAME class files the oracle reads and nothing else (dependencies absent, as
# for every tool on a Maven subject — for WALA that means a call into a missing class is simply
# absent, not a boundary row); every concrete application method is an entry point, because the
# benchmark scores a whole-program view, not reachability from main(). For 0-CFA every concrete
# APPLICATION subtype of each parameter is allocated at the entry (#25: WALA's default fabricates
# one arbitrary implementor per interface-typed parameter, which made that row a hierarchy-order
# sample); for CHA and RTA the entry receivers do not decide the graph — RTA's instantiated set is
# every `new` in the application once every method is reachable — and the subtype allocations
# made RTA run 50x longer on rxjava, so those two keep the default entry set. Reflection is off (ReflectionOptions.NONE). A method
# reference `Foo::bar` is read off the invokedynamic's bootstrap and emitted from the enclosing
# method, as the oracle records it.
#
# WALA 1.6.7 (Shrike) reads class files up to Java 21, so it runs on a JDK 21 (WALA_JAVA_HOME, or
# the newest 17–21 the machine has). A subject compiled for a newer target is reported absent.
set -euo pipefail
LANG_DIR="$1"; ROOT="$(cd "$LANG_DIR/.." && pwd)"; SUBJECT="$2"
CLASSES="${SUBJECT_CLASSES:?}"; CP="${SUBJECT_CP:-}"
W="$WORK/wala"; mkdir -p "$W"
JH="${WALA_JAVA_HOME:-$(/usr/libexec/java_home -v 21 2>/dev/null || /usr/libexec/java_home -v 17 2>/dev/null || true)}"
[ -n "$JH" ] && [ -x "$JH/bin/java" ] || { echo "  SKIP: no JDK 17–21 for WALA (set WALA_JAVA_HOME)"; exit 0; }
WCP="$ROOT/.tools/wala/cp.txt"
if [ ! -f "$WCP" ]; then
  # resolve WALA once through Maven; pinned in pom.xml
  ( cd "$LANG_DIR/adapters/wala" && mvn -q -B dependency:build-classpath -Dmdep.outputFile="$WCP" ) \
    || { echo "  SKIP: could not resolve WALA (mvn)"; exit 0; }
fi
CPW="$(cat "$WCP")"
if [ ! -f "$ROOT/.tools/wala/WalaCallGraph.class" ]; then
  "$JH/bin/javac" --release 17 -d "$ROOT/.tools/wala" -cp "$CPW" "$LANG_DIR/adapters/wala/WalaCallGraph.java"
fi
VERSION="wala $(basename "$(echo "$CPW" | tr ':' '\n' | grep 'com.ibm.wala.core-' | head -1)" .jar | sed 's/.*-//')"
for algo in cha rta 0cfa; do
  T0=$(python3 -c 'import time;print(time.time())')
  if ! "$JH/bin/java" -Xmx6g -cp "$ROOT/.tools/wala:$CPW" WalaCallGraph --app "$CLASSES" ${CP:+--cp "$CP"} \
        --algo "$algo" --out "$W/$algo.tsv" > "$W/$algo.log" 2>&1; then
    tail -3 "$W/$algo.log"; echo "  !! wala-$algo failed — reported as absent, never as zero"; continue
  fi
  EL=$(python3 -c "import time;print(round(time.time()-$T0,2))")
  printf 'wala-%s\t%s\n' "$algo" "$EL" >> "$WORK/timings.tsv"
  python3 "$LANG_DIR/adapters/wala/adapt.py" --tsv "$W/$algo.tsv" --subject "$SUBJECT" \
    --label "wala-$algo" --meta "$VERSION $(grep '^wala' "$W/$algo.log" | head -1 | sed 's/, [0-9]* ms build//')" --build bytecode \
    --edges "$WORK/edges/wala-$algo/$SUBJECT.jsonl"
done
