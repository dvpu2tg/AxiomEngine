// ─────────────────────────────────────────────────────────────────────────────────────────────
// GROUND TRUTH FOR THE JAVA CALL-GRAPH BENCHMARK
//
// Reads the invoke instructions out of ALREADY-COMPILED class files with `java.lang.classfile`
// (JEP 484, final in JDK 24). The JDK parses its own artefact format: no third-party analyzer, no
// javac invocation, nothing that could share a bug with any tool under test.
//
// WHY A CALL-SITE RECORD AND NOT AN EDGE LIST
// -------------------------------------------
// An edge list answers "is A -> B in the graph". It cannot answer the question this benchmark
// exists to answer: at THIS call site, where the language admits exactly one target, did the tool
// name that one method, or a set, or the wrong thing? That needs the site — its line, its opcode,
// its receiver's static type, and the two bounds computed for that site alone. So this reader emits
// one JSON record per scored call site and lets the scorer derive edge sets from it. Deriving the
// other way round is impossible.
//
// THE THREE BOUNDS, PER SITE
// --------------------------
//   certain      (G_lb) — the target the instruction DECLARES, re-pointed to the class that
//                         declares the member. For invokestatic/invokespecial this is the method
//                         that runs, full stop. For invokevirtual/invokeinterface it is the static
//                         type's member; the receiver may be a subtype at run time, so a tool that
//                         names a subtype is not wrong — see `possible`.
//   possible     (G_ub) — every method JVMS §5.4.6 SELECTS for some concrete application receiver
//                         that is the static type or a subtype of it, bridges followed to the
//                         override they forward to (issue #30): the CLASS-HIERARCHY (CHA) dispatch
//                         envelope, checked independently by gate 1c. An answer inside it is a
//                         real runtime possibility; only an answer OUTSIDE it is a demonstrable
//                         false positive, which is why precision is measured against this set. A
//                         call whose declared target is outside the application is a BOUNDARY:
//                         its application implementors are accepted, never the unique answer.
//   possible_rta (RTA)  — the same expansion restricted to types the application actually
//                         INSTANTIATES (a `new`, a constructor reference `T::new`, an enum
//                         constant — NOT a method-reference target, whose class the JVM does not
//                         instantiate). A tighter and far more realistic envelope: a CHA fan
//                         includes implementors nothing ever creates. RTA is UNSOUND in general —
//                         a type built by a dependency, by reflection or by a framework appears
//                         nowhere in the artefact — so it is reported as an additional, sharper
//                         reading and is never used as the precision denominator.
//
// A site whose `possible` set has exactly one member is a UNIQUELY-LINKED site: the language admits
// one answer and there is no excuse for naming a set. Those sites carry the benchmark's headline
// discriminator, and `unique_rta` says how many more become single-target once RTA is applied.
//
// NORMALISATION (docs/PROTOCOL.md is the single normative statement; bench/resolve.py maps every
// tool's notation onto this one, so no tool is asked to adopt it)
//   * the canonical type name is the FULL NESTING CHAIN, `pkg.Outer.Inner` — never flattened to
//     `pkg.Inner`, which is lossy: this subject alone has two distinct `Node` types
//   * anonymous classes keyed by SUPERTYPE (`Outer$anon:Runnable`), never by the compiler's counter
//   * an enum-constant body (an anonymous subclass of the enum) folds back to the ENUM
//   * a local class's compiler index is stripped (`Outer$1Local` -> `pkg.Outer.Local`)
//   * a lambda body folds into the method that lexically contains it, spelled with that method's
//     own parameters (`*` only when no invokedynamic names the body); the container is
//     read off the invokedynamic that REFERENCES the body, never off the body's name (javac emits
//     `lambda$<method>$<n>`, ecj emits `lambda$<n>` — name parsing cannot recover the container)
//   * parameter types are erased and simple-named, so a type variable reads as its bound
//
// EXCLUDED — an invoke instruction for which the source contains no call. Leaving one in does not
// lose a point, it scores every tool as having MISSED a call site that is not in the file, which is
// a wrong number rather than a missing one. See docs/PROTOCOL.md §4 for the full list and the
// evidence for each.
//
// usage:
//   java ClassfileGroundTruth.java --app <dir-or-jar>[,...] [--exclude-tests]
//                                  [--include-prefix <pkg>[,...]] [--only-types <file>]
//                                  [--mode sites|classes|methods|raw|collisions]
// ─────────────────────────────────────────────────────────────────────────────────────────────
import java.lang.classfile.*;
import java.lang.classfile.constantpool.MethodHandleEntry;
import java.lang.classfile.instruction.InvokeDynamicInstruction;
import java.lang.classfile.instruction.InvokeInstruction;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

public class ClassfileGroundTruth {

    record MethodKey(String name, List<String> params) {}

    static final Map<String, String>         SUPER        = new HashMap<>();  // internal -> internal
    static final Map<String, List<String>>   IFACES       = new HashMap<>();
    static final Map<String, Set<MethodKey>> DECL         = new HashMap<>();
    static final Map<String, Set<MethodKey>> SYNTH        = new HashMap<>();  // ACC_BRIDGE | ACC_SYNTHETIC
    static final Set<String>                 APP          = new LinkedHashSet<>();
    static final Set<String>                 ENUMS        = new HashSet<>();
    static final Set<String>                 DEFAULT_CTOR = new HashSet<>();
    static final Map<String, List<String>>   SUBS         = new HashMap<>();  // declaring type -> app subtypes
    static final Map<String, String>         LAMBDA_IN    = new HashMap<>();  // cls#body -> container method
    // RTA's instantiated set: every type the application actually constructs. A CHA fan includes
    // implementors that no code in the subject ever creates; RTA removes those, which is a much
    // tighter envelope and therefore a much sharper reading of a tool's over-approximation.
    static final Set<String>                 INSTANTIATED = new LinkedHashSet<>();
    // The source line a class is DECLARED at, read from its line-number tables. Used to key an
    // anonymous class: two anonymous classes in one outer implementing one interface collide
    // otherwise, and on netty-transport alone that is 23 collisions — a ground truth in which two
    // distinct types share a name, so both bounds are computed over a type that does not exist.
    // The compiler's counter (`Outer$1`, `Outer$2`) cannot be used: javac and ecj number
    // differently, so it is not a property of the program. A source LINE is.
    static final Map<String, Integer>        DECL_LINE    = new HashMap<>();
    // `this$0` / `val$x`: the synthetic fields javac adds to an inner, local or anonymous class to
    // hold the enclosing instance and each captured local. Every one of them also becomes a
    // CONSTRUCTOR PARAMETER that the source never wrote — see `sourceParams`.
    static final Map<String, List<String>>   CAPTURE_FLDS = new HashMap<>();  // class -> val$* types
    // the real (name, params) of the method a lambda body was written inside
    static final Map<String, String[]>       LAMBDA_OWNER = new HashMap<>();

    // ── THE JVMS VIEW (issue #30) ────────────────────────────────────────────────────────────
    // `possible` used to be "every subtype that itself DECLARES a member with the same erased
    // parameter list, bridges skipped". That is not what runs. JVMS §5.4.3.3 resolves the
    // instruction's symbolic reference to a declaration, and §5.4.6 SELECTS, for a receiver class
    // C, the method C or its superclass chain declares that OVERRIDES it (§5.4.5: private and
    // static never override; package-private overrides only from the same package), else the
    // maximally-specific non-abstract superinterface method. A generic override is reached through
    // its ACC_BRIDGE forwarder, so a bridge is followed to the method it calls. Measured against an
    // independent implementation on rxjava the old set omitted 8,172 runnable edges and included
    // 56,403 impossible ones, and both errors move the `unique` flag the headline is built on.
    // These tables hold what the JVMS view needs: every method with its FULL descriptor and flags.
    record MInfo(String cls, String name, String desc, int flags) {}
    static final Map<String, Map<String, MInfo>> METHODS     = new HashMap<>();  // cls -> name+desc
    static final Map<String, Integer>            CLASS_FLAGS = new HashMap<>();
    static final Map<String, MInfo>              BRIDGE_TO   = new HashMap<>();  // cls.name+desc -> real
    static final MInfo EXTERNAL = new MInfo("<external>", "", "", 0);
    // The ENCLOSING INSTANCE a constructor takes, read from the class file's own structure — the
    // InnerClasses / EnclosingMethod attributes — not from the `this$0` field, which javac ≥ 18
    // omits when the inner class never touches the outer instance while the constructor still
    // takes it (JDK-8271623; issue #26 §1). Value: the enclosing class's simple name.
    static final Map<String, String>             OUTER_INST  = new HashMap<>();
    static final Set<String>                     SYNTHETIC_CLASSES = new HashSet<>();
    static final Map<String, String[]>           ENCL_METHOD = new HashMap<>();   // cls -> {encl cls, name, desc}
    static final Map<String, String>             ENCL_INIT   = new HashMap<>();   // cls -> encl cls, for a class in an initializer block
    // What InnerClasses says about the class ITSELF (JVMS 4.7.6). A nested class's own class file
    // must carry an entry for itself, so the ABSENCE of one is the statement that a class is top
    // level — whatever `$` its name happens to contain (#97).
    static final Set<String>                     NEST_SELF   = new HashSet<>();   // has an entry for itself: nested
    static final Map<String, String>             NEST_OUTER  = new HashMap<>();   // cls -> outer internal (member classes)
    static final Map<String, String>             NEST_SIMPLE = new HashMap<>();   // cls -> inner_name; absent = anonymous
    // `access$N` (Java 8 bytecode): the synthetic accessor javac emits for a nested class's call to
    // a private member -> the member it forwards to; absent when the accessor reads or writes a
    // FIELD (no call is written). Issue #66 §1.
    static final Map<String, MInfo>              ACCESSOR_TO = new HashMap<>();

    // Edges an exclusion removed, and callers an exclusion removed entirely. Emitted by
    // `--mode excluded` so the SCORER can apply the same exclusions to every tool.
    //
    // WHY THIS EXISTS. docs/PROTOCOL.md §4 excludes constructs the source does not contain —
    // implicit super(), enum plumbing, javac lowering. Applying that to the oracle alone is only
    // half a rule: a tool that emits the excluded edge then has it counted as a FALSE POSITIVE,
    // and is marked imprecise for reporting something the benchmark decided not to measure. On
    // this subject that was 12 of CodeQL's 12 false positives — a precision figure that was
    // entirely an artefact of asymmetry. An exclusion must remove a construct from BOTH sides.
    static final TreeSet<String> EXCLUDED_EDGES   = new TreeSet<>();
    static final TreeSet<String> EXCLUDED_CALLERS = new TreeSet<>();

    static boolean excludeTests = false;
    static String  mode = "sites";
    static List<String> includePrefixes = new ArrayList<>();
    // Top-level types the TOOLS can actually see, from bench/correspondence.py. Ground truth for a
    // type with no source would be a `missed` against every tool simultaneously — a uniform recall
    // deflation that looks exactly like a real result. Empty means "no restriction".
    static final Set<String> ONLY_TYPES = new LinkedHashSet<>();

    public static void main(String[] argv) throws Exception {
        // ONE line separator everywhere. `println` writes System.lineSeparator(), which is
        // `\r\n` on Windows, and the ground truth is hashed into the run manifest: the same
        // content produced a different hash per platform and verify.sh could never pass
        // off-macOS (#45). The artefact itself is now platform-neutral.
        System.setOut(new java.io.PrintStream(new java.io.FileOutputStream(java.io.FileDescriptor.out), false,
                                              java.nio.charset.StandardCharsets.UTF_8) {
            @Override public void println(String x) { print(x); print('\n'); }
            @Override public void println(Object x) { print(String.valueOf(x)); print('\n'); }
            @Override public void println() { print('\n'); }
        });
        List<Path> roots = new ArrayList<>();
        for (int i = 0; i < argv.length; i++) {
            switch (argv[i]) {
                case "--app"             -> { for (String s : argv[++i].split(",")) roots.add(Path.of(s)); }
                case "--exclude-tests"   -> excludeTests = true;
                case "--mode"            -> mode = argv[++i];
                case "--include-prefix"  -> includePrefixes.addAll(Arrays.asList(argv[++i].split(",")));
                case "--only-types"      -> {
                    for (String ln : Files.readAllLines(Path.of(argv[++i])))
                        if (!ln.isBlank()) ONLY_TYPES.add(ln.trim());
                }
                default -> throw new IllegalArgumentException("unknown arg " + argv[i]);
            }
        }
        if (roots.isEmpty()) { System.err.println("need --app"); System.exit(2); }
        List<ClassModel> models = load(roots);

        switch (mode) {
            case "classes" -> { for (String c : new TreeSet<>(mapped(APP))) System.out.println(c); }
            // `internal<TAB>canonical`, for every application class the compiler names differently
            // from the key this oracle uses: an anonymous class (`Outer$1`), an enum-constant body
            // (`Op$1`) and a local class (`Outer$1Local`). The counter is not a NAME — javac and ecj
            // number them differently — which is why the key drops it. But a tool that reads the
            // class files, or that reports what a compiler told it, spells them exactly this way,
            // and refusing that spelling deletes its answer. The counter is a fact about THIS
            // artefact, and this oracle just read it, so the resolver can be handed the mapping
            // instead of every adapter re-deriving it (three of them already do, by hand).
            case "anonmap" -> {
                TreeSet<String> rows = new TreeSet<>();
                for (String c : APP) {
                    if (!inScope(c)) continue;
                    String canon = cname(c), internal = c.replace('/', '.');
                    if (!internal.equals(canon)) rows.add(internal + "\t" + canon);
                }
                for (String r : rows) System.out.println(r);
                System.err.println("# compiler-named classes: " + rows.size());
            }
            case "heritage" -> {
                // `container<TAB>kind<TAB>parent,parent` — what the RESOLVER needs to know whether a
                // container declares OR INHERITS a member, and whether it can be a caller at all
                // (an interface's abstract member cannot). Issue #36.
                TreeSet<String> rows = new TreeSet<>();
                for (String c : APP) {
                    if (!inScope(c)) continue;
                    int fl = CLASS_FLAGS.getOrDefault(c, 0);
                    String kind = (fl & 0x0200) != 0 ? "interface" : (fl & 0x4000) != 0 ? "enum"
                                : (fl & 0x0400) != 0 ? "abstract" : "class";
                    List<String> ps = new ArrayList<>();
                    String sup = SUPER.get(c);
                    if (sup != null && APP.contains(sup) && inScope(sup)) ps.add(cname(sup));
                    for (String i : IFACES.getOrDefault(c, List.of()))
                        if (APP.contains(i) && inScope(i)) ps.add(cname(i));
                    rows.add(cname(c) + "\t" + kind + "\t" + String.join(",", ps));
                }
                for (String r : rows) System.out.println(r);
            }
            case "methods" -> emitMethods();
            case "sites"   -> emitSites(models);
            case "raw"     -> emitRaw(models);
            case "collisions" -> emitCollisions();
            case "excluded" -> {
                emitSites(models);                      // populates the two sets as a side effect
                for (String c : EXCLUDED_CALLERS) System.out.println("CALLER\t" + c);
                for (String e : EXCLUDED_EDGES)   System.out.println("EDGE\t" + e);
                System.err.println("# excluded callers: " + EXCLUDED_CALLERS.size()
                                   + ", excluded app-internal edges: " + EXCLUDED_EDGES.size());
            }
            default -> { System.err.println("unknown --mode " + mode); System.exit(2); }
        }
    }

    static List<String> mapped(Collection<String> internals) {
        List<String> out = new ArrayList<>();
        for (String i : internals) if (inScope(i)) out.add(cname(i));
        return out;
    }

    // ── reading ──────────────────────────────────────────────────────────────────────────────
    /** Read and index every class file under the roots; the state every mode reads. */
    static List<ClassModel> load(List<Path> roots) throws IOException {
        List<byte[]> blobs = new ArrayList<>();
        for (Path r : roots) collect(r, blobs);
        List<ClassModel> models = new ArrayList<>(blobs.size());
        for (byte[] b : blobs) {
            try { models.add(ClassFile.of().parse(b)); } catch (Throwable t) { /* not a class file */ }
        }
        for (ClassModel cm : models) indexDeclLine(cm);
        for (ClassModel cm : models) index(cm);
        for (ClassModel cm : models) mapLambdaContainers(cm);
        for (ClassModel cm : models) collectInstantiated(cm);
        loadPlatformSupertypes();
        for (String c : APP) for (String a : ancestors(c)) SUBS.computeIfAbsent(a, k -> new ArrayList<>()).add(c);
        indexBridges(models);
        resolveEnclosingInstances();
        System.err.println("# class files read: " + blobs.size());
        System.err.println("# app classes: " + APP.size());
        return models;
    }

    // ── PLATFORM SUPERTYPES (issue #30, reopened) ─────────────────────────────────────────────
    // `ancestors()` walks SUPER/IFACES, which were filled only for the classes read — the
    // application's. So `IdentityStack extends java.util.Stack` recorded `Stack`, and that
    // `Stack extends Vector` was never known: a call on a `Vector` receiver omitted
    // `IdentityStack#contains` from the envelope, and the group was "uniquely linked" to another
    // implementor. The chain through a platform class is read from the running JDK's own class
    // files, on demand, recursively; those classes are indexed (SUPER, IFACES, METHODS, flags) but
    // are NOT application classes. A supertype in a DEPENDENCY jar is not readable this way and is
    // counted, because every such break in the chain is a place the envelope is still blind.
    static final Set<String> PLATFORM_LOADED = new HashSet<>();
    static int platformResolved = 0, supertypesUnresolved = 0;
    static final Set<String> UNRESOLVED_SUPERTYPES = new TreeSet<>();

    static void loadPlatformSupertypes() {
        Deque<String> q = new ArrayDeque<>();
        for (String c : new ArrayList<>(APP)) {
            String sup = SUPER.get(c);
            if (sup != null) q.add(sup);
            q.addAll(IFACES.getOrDefault(c, List.of()));
        }
        while (!q.isEmpty()) {
            String t = q.poll();
            if (t == null || APP.contains(t) || PLATFORM_LOADED.contains(t) || UNRESOLVED_SUPERTYPES.contains(t)) continue;
            byte[] bytes = platformBytes(t);
            if (bytes == null) { supertypesUnresolved++; UNRESOLVED_SUPERTYPES.add(t); continue; }
            ClassModel cm;
            try { cm = ClassFile.of().parse(bytes); } catch (Throwable e) { supertypesUnresolved++; UNRESOLVED_SUPERTYPES.add(t); continue; }
            PLATFORM_LOADED.add(t); platformResolved++;
            CLASS_FLAGS.put(t, cm.flags().flagsMask());
            cm.superclass().ifPresent(sc -> SUPER.put(t, sc.asInternalName()));
            List<String> ifs = new ArrayList<>();
            for (var i : cm.interfaces()) ifs.add(i.asInternalName());
            IFACES.put(t, ifs);
            Map<String, MInfo> table = METHODS.computeIfAbsent(t, k -> new HashMap<>());
            for (MethodModel m : cm.methods())
                table.put(m.methodName().stringValue() + m.methodType().stringValue(),
                          new MInfo(t, m.methodName().stringValue(), m.methodType().stringValue(), m.flags().flagsMask()));
            String sup = SUPER.get(t);
            if (sup != null) q.add(sup);
            q.addAll(ifs);
        }
        System.err.println("# external supertypes: " + platformResolved + " read from the platform, "
            + supertypesUnresolved + " unresolved (dependencies)" + (UNRESOLVED_SUPERTYPES.isEmpty() ? "" : ": " + UNRESOLVED_SUPERTYPES));
    }

    /** Read one platform type (and its supertype chain) on demand — a covariant `iterator()`
     *  return type, say — without adding it to the application. */
    static void readPlatformType(String t) {
        if (APP.contains(t) || PLATFORM_LOADED.contains(t) || UNRESOLVED_SUPERTYPES.contains(t)) return;
        byte[] bytes = platformBytes(t);
        if (bytes == null) { UNRESOLVED_SUPERTYPES.add(t); return; }
        ClassModel cm;
        try { cm = ClassFile.of().parse(bytes); } catch (Throwable e) { UNRESOLVED_SUPERTYPES.add(t); return; }
        PLATFORM_LOADED.add(t);
        CLASS_FLAGS.put(t, cm.flags().flagsMask());
        cm.superclass().ifPresent(sc -> SUPER.put(t, sc.asInternalName()));
        List<String> ifs = new ArrayList<>();
        for (var i : cm.interfaces()) ifs.add(i.asInternalName());
        IFACES.put(t, ifs);
        Map<String, MInfo> table = METHODS.computeIfAbsent(t, k -> new HashMap<>());
        for (MethodModel m : cm.methods())
            table.put(m.methodName().stringValue() + m.methodType().stringValue(),
                      new MInfo(t, m.methodName().stringValue(), m.methodType().stringValue(), m.flags().flagsMask()));
        String sup = SUPER.get(t);
        if (sup != null) readPlatformType(sup);
        for (String i : ifs) readPlatformType(i);
    }

    static byte[] platformBytes(String internal) {
        for (ClassLoader cl : new ClassLoader[]{ClassLoader.getPlatformClassLoader(), ClassLoader.getSystemClassLoader()}) {
            try (InputStream in = cl.getResourceAsStream(internal + ".class")) {
                if (in != null) return in.readAllBytes();
            } catch (IOException e) { /* try the next loader */ }
        }
        return null;
    }

    static void collect(Path root, List<byte[]> into) throws IOException {
        if (Files.isRegularFile(root) && root.toString().endsWith(".jar")) {
            try (ZipFile z = new ZipFile(root.toFile())) {
                for (var e : Collections.list(z.entries())) {
                    if (!e.getName().endsWith(".class")) continue;
                    if (excludeTests && isTestPath(e.getName())) continue;
                    try (InputStream in = z.getInputStream(e)) { into.add(in.readAllBytes()); }
                }
            }
            return;
        }
        if (!Files.isDirectory(root)) return;
        List<Path> found = new ArrayList<>();
        try (var s = Files.walk(root)) {
            s.filter(Files::isRegularFile).filter(p -> p.toString().endsWith(".class")).forEach(found::add);
        }
        // Sorted so the emission order is a function of the tree, not of the filesystem's walk order.
        Collections.sort(found);
        for (Path p : found) {
            if (excludeTests && isTestPath(root.relativize(p).toString())) continue;
            into.add(Files.readAllBytes(p));
        }
    }

    static boolean isTestPath(String rel) {
        String r = rel.replace('\\', '/');
        for (String seg : r.split("/")) {
            if (seg.equals("test") || seg.equals("tests") || seg.equals("testFixtures")
                || seg.equals("e2e") || seg.equals("benchmarks")) return true;
        }
        String base = r.substring(r.lastIndexOf('/') + 1);
        String top = base.split("\\$")[0];
        return top.endsWith("Test.class") || top.endsWith("Tests.class") || top.endsWith("IT.class")
            || top.endsWith("TestCase.class") || top.startsWith("Test");
    }

    /** The lowest line number any of a class's methods mentions — for an anonymous class that is
     *  the `new X(){ … }` expression that declares it. */
    static void indexDeclLine(ClassModel cm) {
        int min = Integer.MAX_VALUE;
        for (MethodModel m : cm.methods()) {
            var code = m.code(); if (code.isEmpty()) continue;
            for (CodeElement e : code.get())
                if (e instanceof java.lang.classfile.instruction.LineNumber ln)
                    min = Math.min(min, ln.line());
        }
        if (min != Integer.MAX_VALUE) DECL_LINE.put(cm.thisClass().asInternalName(), min);
    }

    static void index(ClassModel cm) {
        String in = cm.thisClass().asInternalName();
        // A class javac synthesises — the `$SwitchMap$` holder an enum switch produces — declares
        // nothing the source declares; it is neither a type in the universe nor a caller (#26 §7).
        if ((cm.flags().flagsMask() & 0x1000) != 0) { SYNTHETIC_CLASSES.add(in); return; }
        APP.add(in);
        CLASS_FLAGS.put(in, cm.flags().flagsMask());
        Map<String, MInfo> table = METHODS.computeIfAbsent(in, k -> new HashMap<>());
        for (MethodModel m : cm.methods()) {
            String nd = m.methodName().stringValue() + m.methodType().stringValue();
            table.put(nd, new MInfo(in, m.methodName().stringValue(), m.methodType().stringValue(), m.flags().flagsMask()));
        }
        // the enclosing instance: a non-static member class (InnerClasses says so), or a local /
        // anonymous class written in an instance context (EnclosingMethod names a non-static method,
        // or an instance initialiser)
        String outerType = null;
        int innerAccess = cm.flags().flagsMask();   // a nested class's real access is in InnerClasses
        var inner = cm.findAttribute(Attributes.innerClasses());
        if (inner.isPresent()) {
            for (var ic : inner.get().classes()) {
                if (!ic.innerClass().asInternalName().equals(in)) continue;
                innerAccess = ic.flagsMask();
                NEST_SELF.add(in);
                // outer_class_info_index is zero for a local or anonymous class; inner_name_index is
                // zero for an anonymous one. Both absences are facts, and cname() reads them.
                ic.outerClass().ifPresent(o -> NEST_OUTER.put(in, o.asInternalName()));
                ic.innerName().ifPresent(n -> NEST_SIMPLE.put(in, n.stringValue()));
                if (ic.outerClass().isPresent() && (ic.flagsMask() & 0x0008) == 0)
                    outerType = ic.outerClass().get().asInternalName();
            }
        }
        var encl = cm.findAttribute(Attributes.enclosingMethod());
        if (outerType == null && encl.isPresent()) {
            String ec = encl.get().enclosingClass().asInternalName();
            var em = encl.get().enclosingMethod();
            // a local or anonymous class in a static method has no enclosing instance; in an
            // instance method or initialiser it has one — decided by the constructor's first
            // parameter below, because a class file for the enclosing class may not be at hand
            outerType = ec;
            if (em.isPresent()) {
                // resolved after all classes are indexed: see resolveEnclosingInstances
                ENCL_METHOD.put(in, new String[]{ec, em.get().name().stringValue(), em.get().type().stringValue()});
            } else {
                // an initializer block: static or instance is decided by where the class is
                // `new`-ed, once every class is indexed (issue #77 §2)
                ENCL_INIT.put(in, ec);
            }
        }
        if (outerType != null) OUTER_INST.put(in, simpleOf(outerType.replace('/', '.')));
        cm.superclass().ifPresent(s -> SUPER.put(in, s.asInternalName()));
        List<String> ifs = new ArrayList<>();
        for (var i : cm.interfaces()) ifs.add(i.asInternalName());
        IFACES.put(in, ifs);
        if ("java/lang/Enum".equals(SUPER.get(in))) ENUMS.add(in);
        List<String> caps = new ArrayList<>();
        for (var fld : cm.fields()) {
            String fn = fld.fieldName().stringValue();
            String ft = fieldTypeSimple(fld.fieldType().stringValue());
            if (fn.startsWith("val$")) caps.add(ft);
        }
        if (!caps.isEmpty()) CAPTURE_FLDS.put(in, caps);
        Set<MethodKey> d    = DECL.computeIfAbsent(in, k -> new HashSet<>());
        Set<MethodKey> syn  = SYNTH.computeIfAbsent(in, k -> new HashSet<>());
        Set<MethodKey> real = new HashSet<>();
        for (MethodModel m : cm.methods()) {
            MethodKey mk = new MethodKey(m.methodName().stringValue(), params(m.methodType().stringValue()));
            d.add(mk);
            int mf = m.flags().flagsMask();
            if ((mf & 0x0040) != 0 || (mf & 0x1000) != 0) syn.add(mk); else real.add(mk);
            if (m.methodName().equalsString("<init>") && isSynthesizedDefaultCtor(m, innerAccess)) DEFAULT_CTOR.add(in);
        }
        // A key that also names a REAL method is not synthetic. MethodKey carries no return type, so
        // a covariant-return override declares two methods sharing it — the real one and the bridge
        // beside it. Keying on the flag alone would make the real method unreachable.
        syn.removeAll(real);
    }

    /** `aload_0; invokespecial super.<init>()V; return` — exactly three instructions, nothing else. */
    static boolean isSynthesizedDefaultCtor(MethodModel m, int classAccess) {
        if (!m.methodType().stringValue().startsWith("()")) return false;
        // a synthesized default constructor has the CLASS's access; a written empty `private
        // Priv() {}` in a package-private class compiles to the same three instructions and is
        // the source's own (#66 §2)
        if ((m.flags().flagsMask() & 0x0007) != (classAccess & 0x0007)) return false;
        var code = m.code();
        if (code.isEmpty()) return false;
        int n = 0;
        for (CodeElement e : code.get()) { if (e instanceof Instruction) { n++; if (n > 3) return false; } }
        return n == 3;
    }

    // ── descriptors ──────────────────────────────────────────────────────────────────────────
    static final Map<Character, String> PRIM = Map.of('B',"byte",'C',"char",'D',"double",'F',"float",
                                                      'I',"int",'J',"long",'S',"short",'Z',"boolean");
    static List<String> params(String desc) {
        List<String> out = new ArrayList<>();
        int i = desc.indexOf('(') + 1, end = desc.lastIndexOf(')');
        while (i < end) {
            int arr = 0;
            while (desc.charAt(i) == '[') { arr++; i++; }
            String t;
            if (desc.charAt(i) == 'L') { int j = desc.indexOf(';', i); t = desc.substring(i + 1, j).replace('/', '.'); i = j + 1; }
            else { t = PRIM.get(desc.charAt(i)); i++; }
            out.add(simpleOf(t) + "[]".repeat(arr));
        }
        return out;
    }
    static String fieldTypeSimple(String desc) {
        int arr = 0; int i = 0;
        while (i < desc.length() && desc.charAt(i) == '[') { arr++; i++; }
        String t;
        if (desc.charAt(i) == 'L') t = desc.substring(i + 1, desc.length() - 1).replace('/', '.');
        else t = PRIM.getOrDefault(desc.charAt(i), "?");
        return simpleOf(t) + "[]".repeat(arr);
    }

    /**
     * A constructor's parameter list AS THE SOURCE WROTE IT.
     *
     * javac augments a constructor in three ways, none of which appears in the file:
     *   * an ENUM constructor gains a leading `(String name, int ordinal)` — mandated by the JLS,
     *     never written;
     *   * an INNER, LOCAL or ANONYMOUS class's constructor gains a leading enclosing instance,
     *     evidenced by the synthetic `this$0` field;
     *   * a LOCAL or ANONYMOUS class's constructor gains one trailing parameter per captured local,
     *     evidenced by the synthetic `val$x` fields.
     *
     * Scoring a source-based tool against the augmented list charges it for parameters that are not
     * in the code it read — `new Inner()` becomes a miss because the oracle demanded
     * `Inner#<init>(F08Nesting)`. That is a wrong number, not a strict one, so the augmentation is
     * removed on the oracle's side. The evidence is structural (the synthetic fields), not a guess.
     */
    static List<String> sourceParams(String owner, String name, List<String> ps) {
        if (!name.equals("<init>")) return ps;
        List<String> out = new ArrayList<>(ps);
        if (ENUMS.contains(owner) || ENUMS.contains(SUPER.get(owner))) {
            if (out.size() >= 2 && out.get(0).equals("String") && out.get(1).equals("int"))
                out = new ArrayList<>(out.subList(2, out.size()));
        }
        String outer = OUTER_INST.get(owner);
        if (outer != null && !out.isEmpty() && out.get(0).equals(outer)) out.remove(0);
        List<String> caps = CAPTURE_FLDS.get(owner);
        if (caps != null && out.size() >= caps.size()) {
            List<String> tail = out.subList(out.size() - caps.size(), out.size());
            if (new HashSet<>(tail).equals(new HashSet<>(caps))) tail.clear();
        }
        return out;
    }

    static String simpleOf(String qn) {
        String s = qn.substring(qn.lastIndexOf('.') + 1);
        return s.substring(s.lastIndexOf('$') + 1);
    }

    // ── name normalisation ───────────────────────────────────────────────────────────────────
    //
    // THE CANONICAL NAME IS THE FULL NESTING CHAIN — `pkg.Outer.Inner`, not `pkg.Inner`.
    //
    // Flattening a nested type to its simple name is a convention some call-graph IRs adopt, and it
    // is LOSSY: this 592-line subject alone has two distinct types (`F02Generics$Node` and
    // `F07Modern$Node`) that flatten to the same name. Adopting it here would do two unacceptable
    // things at once. It would corrupt the GROUND TRUTH, because the two types' members would merge
    // and both bounds would be computed over a type that does not exist. And it would punish every
    // tool that handles nesting correctly, by making its correct answer differ from the oracle's.
    //
    // So the oracle keeps the chain, and a tool that flattens is handled where it belongs — in
    // bench/resolve.py, where `pkg.Node` maps to two candidates, is reported AMBIGUOUS and is
    // excluded from the score with the count printed beside it. The tool's convention becomes a
    // measured cost in its own column instead of a distortion in everyone's numbers.
    //
    // Two nesting forms still need a key that no compiler numbering can shift:
    //   * an ANONYMOUS class is keyed by its supertype (`pkg.Outer$anon:Runnable`) — javac and ecj
    //     number them differently, so the counter is not a name
    //   * a LOCAL class's counter prefix is stripped (`Outer$1Local` -> `pkg.Outer.Local`)
    // Both can, in principle, still collide. `--mode collisions` reports every canonical name that
    // more than one class file answers to, and the run script fails on a non-empty report rather
    // than scoring against a ground truth that cannot tell two types apart.
    static final Map<String, String> NAME_CACHE = new HashMap<>();
    static String cname(String internal) {
        String c = NAME_CACHE.get(internal);
        if (c != null) return c;
        String res = computeCname(internal);
        NAME_CACHE.put(internal, res);
        return res;
    }
    static String computeCname(String internal) {
        // InnerClasses decides nesting for a class whose class file we read (JVMS 4.7.6): a nested
        // class must carry an entry for ITSELF, a top-level one carries none. The position of a `$`
        // decides nothing — it is a letter the JLS admits in any identifier, and gson's top-level
        // `$Gson$Types` carries two. Reading it as a separator canonicalised that class to a
        // spelling with a doubled dot, which is not a type anyone can write, and put it outside the
        // scored universe for every tool at once (#97). A class we never read keeps the old reading,
        // which is all there is to go on for a name that arrives on an edge from somewhere else.
        if (!APP.contains(internal) && !SYNTHETIC_CLASSES.contains(internal)) return dollarCname(internal);
        if (!NEST_SELF.contains(internal)) return internal.replace('/', '.');   // top level
        String enclosing = NEST_OUTER.get(internal);
        if (enclosing == null) {            // a local or anonymous class: EnclosingMethod names it
            String[] em = ENCL_METHOD.get(internal);
            enclosing = em != null ? em[0] : ENCL_INIT.get(internal);
        }
        if (enclosing == null) return dollarCname(internal);   // nested, but nothing names the outer
        final String outer = enclosing;
        final String simple = NEST_SIMPLE.get(internal);
        if (simple == null) {
            // ANONYMOUS — inner_name is absent. Keyed by its supertype, because javac and ecj
            // number anonymous classes differently and the counter is not a name.
            String sup = supertypeOf(internal);
            // an enum-constant body is an anonymous subclass of the enum; it IS the enum constant,
            // and the source contains no separate type for it
            if (ENUMS.contains(sup)) return cname(sup);
            Integer line = DECL_LINE.get(internal);
            String key = cname(outer) + "$anon:" + simpleOf(sup.replace('/', '.'));
            // The line disambiguates; it is omitted when the class file carries no line numbers
            // (compiled without -g:lines), where the collision check will catch any remaining clash.
            return line == null ? key : key + "@" + line;
        }
        // A LOCAL class's internal name carries a counter the source does not (`Outer$1Local`);
        // inner_name is the name as written, so no counter has to be stripped by hand. Two local
        // classes of one name in one outer (guava's `Streams$1Splitr` … `$4Splitr`) would still
        // collide; those, and only those, are keyed by their declaration line (#26 §7).
        String segment = internal.substring(internal.lastIndexOf('$') + 1);
        if (!segment.equals(simple) && APP.stream().anyMatch(o -> !o.equals(internal)
                && o.startsWith(outer + "$") && simple.equals(NEST_SIMPLE.get(o))
                && !o.substring(outer.length() + 1).equals(simple))) {
            Integer line = DECL_LINE.get(internal);
            if (line != null) return cname(outer) + "." + simple + "@" + line;
        }
        return cname(outer) + "." + simple;
    }

    /** The `$`-position reading, for a class whose class file this run never read. */
    static String dollarCname(String internal) {
        int idx = internal.lastIndexOf('$');
        if (idx < 0) return internal.replace('/', '.');               // top level
        String outer = internal.substring(0, idx);
        String seg   = internal.substring(idx + 1);
        if (!seg.isEmpty() && seg.chars().allMatch(Character::isDigit)) {
            String sup = supertypeOf(internal);
            // an enum-constant body is an anonymous subclass of the enum; it IS the enum constant,
            // and the source contains no separate type for it
            if (ENUMS.contains(sup)) return cname(sup);
            Integer line = DECL_LINE.get(internal);
            String key = cname(outer) + "$anon:" + simpleOf(sup.replace('/', '.'));
            // The line disambiguates; it is omitted when the class file carries no line numbers
            // (compiled without -g:lines), where the collision check will catch any remaining clash.
            return line == null ? key : key + "@" + line;
        }
        String local = seg.replaceFirst("^\\d+(?=[A-Za-z_$])", "");
        // A LOCAL class (`Outer$1Local`) drops its counter, which is not a property of the source.
        // Two local classes of one name in one outer (guava's `Streams$1Splitr` … `$4Splitr`) would
        // then collide; those, and only those, are keyed by their declaration line as an anonymous
        // class is (#26 §7).
        if (!local.equals(seg) && APP.stream().anyMatch(o -> !o.equals(internal) && o.startsWith(outer + "$")
                && o.substring(outer.length() + 1).replaceFirst("^\\d+(?=[A-Za-z_$])", "").equals(local)
                && !o.substring(outer.length() + 1).equals(local))) {
            Integer line = DECL_LINE.get(internal);
            if (line != null) return cname(outer) + "." + local + "@" + line;
        }
        return cname(outer) + "." + local;
    }

    /** A compiler-numbered class: `Outer$1`. Anonymous, or an enum-constant body. */
    static boolean isAnonymous(String internal) {
        int idx = internal.lastIndexOf('$');
        if (idx < 0) return false;
        String seg = internal.substring(idx + 1);
        return !seg.isEmpty() && seg.chars().allMatch(Character::isDigit);
    }

    static boolean isEnumConstantBody(String internal) {
        int idx = internal.lastIndexOf('$');
        if (idx < 0) return false;
        String seg = internal.substring(idx + 1);
        if (seg.isEmpty() || !seg.chars().allMatch(Character::isDigit)) return false;
        return ENUMS.contains(supertypeOf(internal));
    }

    /** Canonical names that more than one class file answers to. A non-empty report is a defect in
     *  the naming scheme, not a property of the subject, and scoring must not proceed past it. */
    static void emitCollisions() {
        Map<String, TreeSet<String>> byName = new TreeMap<>();
        for (String c : APP) {
            if (!inScope(c)) continue;
            // An ENUM-CONSTANT BODY is not a separate type: the source declares a constant with a
            // body, not a class, and folding it onto the enum is the convention, not an accident.
            // Counting the fold as a collision would make the check fire on every enum that has
            // one — a permanently red check nobody can act on, which is worse than no check.
            if (isEnumConstantBody(c)) continue;
            byName.computeIfAbsent(cname(c), k -> new TreeSet<>()).add(c.replace('/', '.'));
        }
        int n = 0;
        for (var e : byName.entrySet()) {
            if (e.getValue().size() < 2) continue;
            n++;
            System.out.println(e.getKey() + " <- " + String.join(", ", e.getValue()));
        }
        System.err.println("# canonical-name collisions: " + n);
    }
    static String supertypeOf(String internal) {
        String s = SUPER.get(internal);
        if (s != null && !s.equals("java/lang/Object")) return s;
        List<String> ifs = IFACES.getOrDefault(internal, List.of());
        return ifs.isEmpty() ? (s == null ? "java/lang/Object" : s) : ifs.get(0);
    }
    static List<String> ancestors(String internal) {
        List<String> out = new ArrayList<>(); Set<String> seen = new HashSet<>();
        Deque<String> q = new ArrayDeque<>(); q.add(internal);
        while (!q.isEmpty()) {
            String c = q.poll();
            String s = SUPER.get(c);
            if (s != null && seen.add(s)) { out.add(s); q.add(s); }
            for (String i : IFACES.getOrDefault(c, List.of())) if (seen.add(i)) { out.add(i); q.add(i); }
        }
        return out;
    }
    static boolean inScope(String internal) {
        if (!includePrefixes.isEmpty()) {
            String q = internal.replace('/', '.');
            boolean hit = false;
            for (String p : includePrefixes) if (q.startsWith(p)) { hit = true; break; }
            if (!hit) return false;
        }
        if (!ONLY_TYPES.isEmpty() && !ONLY_TYPES.contains(topLevelOf(cname(internal)))) return false;
        return true;
    }

    /** `pkg.Outer.Inner` and `pkg.Outer$anon:Sup@12` both belong to the top-level type `pkg.Outer`. */
    static String topLevelOf(String canonical) {
        String c = canonical.split("\\$anon:")[0];
        String[] parts = c.split("\\.");
        for (int i = 0; i < parts.length; i++)
            if (isTypeSegment(parts[i]))
                return String.join(".", Arrays.copyOfRange(parts, 0, i + 1));
        return c;
    }

    /** A type segment is capitalised after any leading `$`/`_`, which are letters to the JLS: gson's
     *  `$Gson$Types` is a type, and its members nest under it rather than standing in for it (#97). */
    static boolean isTypeSegment(String seg) {
        int k = 0;
        while (k < seg.length() && (seg.charAt(k) == '$' || seg.charAt(k) == '_')) k++;
        return k < seg.length() && Character.isUpperCase(seg.charAt(k));
    }

    // ── exclusions ───────────────────────────────────────────────────────────────────────────
    static final Set<String> SYN_NAMES = Set.of("$values", "values", "valueOf", "$deserializeLambda$");
    static final Set<String> BOX = Set.of("java/lang/Integer","java/lang/Long","java/lang/Short",
        "java/lang/Byte","java/lang/Character","java/lang/Boolean","java/lang/Double","java/lang/Float");
    static final Set<String> PRIMS = new HashSet<>(PRIM.values());
    static final Set<String> UNBOX = Set.of("intValue","longValue","shortValue","byteValue",
        "charValue","booleanValue","doubleValue","floatValue");
    /** `values` / `valueOf` are JLS plumbing ON AN ENUM; on any other type they are ordinary methods
     *  the source declares (`LinkedHashtable.values()` in apache-ant — #26 §3). */
    static boolean excludedName(String owner, String n) {
        return n.equals("$values") || n.equals("$deserializeLambda$") || n.startsWith("access$");
    }
    /** The JLS-mandated enum members, by SHAPE: `values()` with no parameter and
     *  `valueOf(String)`. A user-written overload `valueOf(int)` on an enum is the source's own and
     *  stays (#66 §6). */
    static boolean enumPlumbing(String owner, String n, List<String> ps) {
        if (!ENUMS.contains(owner)) return false;
        return (n.equals("values") && ps.isEmpty()) || (n.equals("valueOf") && ps.equals(List.of("String")));
    }

    /** Is the next invoke instruction after `i` a call of `name`? (javac emits the enhanced-for
     *  `hasNext()` test directly after `iterator()`; a written `c.iterator()` is followed by whatever
     *  consumes the iterator.) */
    static boolean nextInvokeIs(List<CodeElement> els, int i, String name) {
        for (int j = i + 1; j < els.size(); j++) {
            CodeElement e = els.get(j);
            if (e instanceof InvokeInstruction ii) return ii.name().stringValue().equals(name);
            if (e instanceof InvokeDynamicInstruction) return false;
        }
        return false;
    }
    /** A try-with-resources `close()`: the method holds an `addSuppressed`, and this owner's
     *  `close()` occurs at least twice at this line (normal + exceptional path). */
    static boolean twrClose(List<CodeElement> els, int i, int line, String owner) {
        boolean suppressed = false; int closes = 0; int cur = -1;
        for (CodeElement e : els) {
            if (e instanceof java.lang.classfile.instruction.LineNumber ln) { cur = ln.line(); continue; }
            if (!(e instanceof InvokeInstruction ii)) continue;
            if (ii.name().equalsString("addSuppressed")) suppressed = true;
            if (ii.name().equalsString("close") && ii.type().stringValue().startsWith("()")
                && ii.owner().asInternalName().equals(owner) && cur == line) closes++;
        }
        if (!suppressed) return false;
        if (closes >= 2) return true;
        // A MULTI-LINE try-with-resources puts the normal-path `close()` on the closing brace's
        // line and the exceptional one on the `try (` line (#26 §5, reopened). Both are javac's
        // `if (r != null) r.close()`: the invoke is preceded by `aload r; ifnull; aload r`. A
        // written `r.close()` has no null test in front of it.
        // Where javac knows the resource is non-null (`try (Res r = new Res())`) there is no
        // null test: the generated `close()` is then the one followed by the `goto` that jumps
        // over the handler (normal path) or to the rethrow (exceptional path). A written
        // `r.close()` is followed by the statement after it; the one shape this cannot tell apart
        // is a written `close()` as the last statement of an if-branch inside a
        // try-with-resources method, which is accepted as the trade.
        List<Instruction> prev = new ArrayList<>();
        for (int j = i - 1; j >= 0 && prev.size() < 3; j--)
            if (els.get(j) instanceof Instruction in) prev.add(0, in);
        boolean nullChecked = prev.size() == 3
            && prev.get(0) instanceof java.lang.classfile.instruction.LoadInstruction l0
            && prev.get(1) instanceof java.lang.classfile.instruction.BranchInstruction br
            && br.opcode() == Opcode.IFNULL
            && prev.get(2) instanceof java.lang.classfile.instruction.LoadInstruction l2
            && l0.slot() == l2.slot();
        if (nullChecked) return true;
        for (int j = i + 1; j < els.size(); j++)
            if (els.get(j) instanceof Instruction in) return in.opcode() == Opcode.GOTO || in.opcode() == Opcode.GOTO_W;
        return false;
    }

    /** `dup / invokestatic Objects.requireNonNull / pop / invokedynamic` — the bound-method-reference
     *  receiver null check, which nothing else emits. A written `Objects.requireNonNull(x)` survives. */
    static boolean boundRefNullCheck(List<CodeElement> els, int i) {
        Instruction prev = null;
        for (int j = i - 1; j >= 0 && prev == null; j--) if (els.get(j) instanceof Instruction in) prev = in;
        List<Instruction> after = new ArrayList<>();
        for (int j = i + 1; j < els.size() && after.size() < 2; j++)
            if (els.get(j) instanceof Instruction in) after.add(in);
        return prev != null && prev.opcode() == Opcode.DUP
            && after.size() == 2 && after.get(0).opcode() == Opcode.POP
            && after.get(1) instanceof InvokeDynamicInstruction;
    }

    /**
     * RTA's instantiated set, read from the bytecode rather than assumed.
     *
     * A `new` instruction is the direct evidence, and two further sources are included because
     * leaving them out would make the RTA envelope UNSOUND in ways a call graph would be right to
     * disagree with:
     *
     *   * an ANONYMOUS or LOCAL class is constructed by a `new` like any other — already covered,
     *     but listed because its constructor is the only place it appears;
     *   * an ENUM CONSTANT is instantiated in `<clinit>`, which the emit loop skips as a caller
     *     but which is still a real instantiation.
     *
     * NOT a lambda's or method reference's owning class: the JVM instantiates the synthesised
     * functional-interface proxy, not the class that contains the body, so a class reached only
     * through `r::get` and never `new`-ed is not in the RTA set — the reference can only be on
     * `null`. (An earlier version of this comment said the opposite of what the code below and
     * docs/PROTOCOL.md §2 say; issue #47.)
     *
     * RTA is nonetheless UNSOUND in general: a type instantiated by a dependency, by reflection or
     * by a framework appears nowhere here. That is why it is reported as an additional, tighter
     * reading and never used as the precision denominator — see docs/PROTOCOL.md §6.
     */
    static void collectInstantiated(ClassModel cm) {
        String cls = cm.thisClass().asInternalName();
        for (MethodModel m : cm.methods()) {
            var code = m.code(); if (code.isEmpty()) continue;
            for (CodeElement e : code.get()) {
                if (e instanceof java.lang.classfile.instruction.NewObjectInstruction n) {
                    INSTANTIATED.add(n.className().asInternalName());
                    NEW_IN.computeIfAbsent(n.className().asInternalName(), k -> new HashSet<>())
                          .add(cls + "." + m.methodName().stringValue());
                }
                // a CONSTRUCTOR REFERENCE (`Sq::new`, REF_newInvokeSpecial) instantiates the class
                // when it runs, exactly as a `new` does (#66 §8)
                if (e instanceof InvokeDynamicInstruction idi && handleKind(idi) == 8) {
                    String[] t = lambdaTargetRaw(idi);
                    if (t != null && t[1].equals("<init>")) INSTANTIATED.add(t[0]);
                }
                // NOT a lambda's or method reference's owning class (the JVM instantiates the
                // synthesised functional-interface proxy, not the class that contains the body),
                // and NOT the target of a `this(...)`/`super(...)` chain (a superclass constructor
                // running does not make the superclass an instantiated type) — #26 §6.
            }
        }
        if (ENUMS.contains(cls)) INSTANTIATED.add(cls);
    }

    static void mapLambdaContainers(ClassModel cm) {
        String cls = cm.thisClass().asInternalName();
        for (MethodModel m : cm.methods()) {
            var code = m.code(); if (code.isEmpty()) continue;
            for (CodeElement e : code.get()) {
                if (!(e instanceof InvokeDynamicInstruction idi)) continue;
                String[] t = lambdaTargetRaw(idi);
                if (t == null || !t[0].equals(cls) || !t[1].startsWith("lambda$")) continue;
                LAMBDA_IN.putIfAbsent(cls + "#" + t[1], m.methodName().stringValue());
                // The container's real signature, so a folded lambda body reads as the method the
                // source actually declares. Recording only the NAME forced the caller to be spelled
                // `wire(*)`, which matches nothing a source-based tool can emit — every call written
                // inside a lambda then scored as missed, for all tools, at Tier A only. That is a
                // measurement artefact with the exact shape of a real finding, which is what makes
                // it dangerous.
                LAMBDA_OWNER.putIfAbsent(cls + "#" + t[1], new String[]{
                    m.methodName().stringValue(),
                    String.join(",", sourceParams(cls, m.methodName().stringValue(),
                                                  params(m.methodType().stringValue())))});
            }
        }
    }
    static String lambdaContainer(String cls, String name) {
        String[] o = lambdaOwner(cls, name);
        return o == null ? null : o[0];
    }
    /** {name, comma-joined source params} of the method a lambda body was written inside. */
    static String[] lambdaOwner(String cls, String name) {
        String cur = name;
        for (int i = 0; i < 8; i++) {                 // bounded: a cycle cannot be a container
            String[] o = LAMBDA_OWNER.get(cls + "#" + cur);
            String next = LAMBDA_IN.get(cls + "#" + cur);
            if (o == null || next == null) return null;
            if (!next.startsWith("lambda$")) return o;
            cur = next;
        }
        return null;
    }
    /** Bootstrap arg 1 of a LambdaMetafactory indy is the implementation MethodHandle — the target a
     *  METHOD REFERENCE lowers to. It appears in no invoke instruction, so an oracle that skips
     *  invokedynamic cannot see a single method-reference edge and scores every one as fabricated. */
    static String[] lambdaTarget(InvokeDynamicInstruction idi) {
        String[] raw = lambdaTargetRaw(idi);
        if (raw == null) return null;
        // A LAMBDA BODY is folded into its container on both sides, so it is not a target. A
        // CONSTRUCTOR reference (`Item::new`) IS one: the source names the constructor, and a tool
        // that resolves it is resolving something that is written in the file. Excluding it made
        // every such edge score as a false positive for the tools that got it right.
        if (raw[1].startsWith("lambda$")) return null;
        return raw;
    }
    static int handleKind(InvokeDynamicInstruction idi) {
        try {
            var args = idi.invokedynamic().bootstrap().arguments();
            if (args.size() < 2 || !(args.get(1) instanceof MethodHandleEntry mh)) return -1;
            return mh.kind();
        } catch (Throwable t) { return -1; }
    }
    static String[] lambdaTargetRaw(InvokeDynamicInstruction idi) {
        try {
            var bsm = idi.invokedynamic().bootstrap();
            if (!bsm.bootstrapMethod().reference().owner().asInternalName()
                    .equals("java/lang/invoke/LambdaMetafactory")) return null;   // excludes StringConcatFactory
            var args = bsm.arguments();
            if (args.size() < 2 || !(args.get(1) instanceof MethodHandleEntry mh)) return null;
            var ref = mh.reference();
            return new String[]{ref.owner().asInternalName(), ref.name().stringValue(), ref.type().stringValue()};
        } catch (Throwable t) { return null; }
    }

    // ── JVMS resolution and selection (issue #30) ───────────────────────────────────────────
    /** A bridge method's body is one invoke of the method it forwards to, in the same class. */
    static void indexBridges(List<ClassModel> models) {
        for (ClassModel cm : models) {
            String c = cm.thisClass().asInternalName();
            if (!APP.contains(c)) continue;
            for (MethodModel mm : cm.methods()) {
                int mf = mm.flags().flagsMask();
                String mn = mm.methodName().stringValue();
                if (mm.code().isEmpty()) continue;
                // `access$N`: a static synthetic accessor whose body is one call (a method accessor)
                // or a field get/put (no call at all). Java 8 bytecode routes a nested class's call
                // to a private member of its outer class through one; the written call is to the
                // member (#66 §1).
                if (mn.startsWith("access$") && (mf & 0x1000) != 0) {
                    InvokeInstruction only = null; int n = 0;
                    for (CodeElement e : mm.code().get()) if (e instanceof InvokeInstruction ii) { only = ii; n++; }
                    if (n == 1 && only != null) {
                        MInfo tgt = declOf(only.owner().asInternalName(), only.name().stringValue() + only.type().stringValue());
                        if (tgt != null) ACCESSOR_TO.put(c + "." + mn + mm.methodType().stringValue(), tgt);
                    }
                    continue;
                }
                if ((mf & 0x0040) == 0 && !((mf & 0x1000) != 0 && mn.equals("<init>"))) continue;
                // a BRIDGE (generic / covariant: same class, same name; VISIBILITY: the superclass's
                // method of the same name and descriptor, #77 §1) and a synthetic PRIVATE-CONSTRUCTOR
                // ACCESSOR (`Inner(Outer, Outer$1)` forwarding to `Inner(Outer)`, #66 §2): the body
                // is one invoke of the method it forwards to
                for (CodeElement e : mm.code().get())
                    if (e instanceof InvokeInstruction ii && ii.name().stringValue().equals(mn)
                        && !(mn.equals("<init>") && !ii.owner().asInternalName().equals(c))) {
                        MInfo tgt = declOf(ii.owner().asInternalName(), ii.name().stringValue() + ii.type().stringValue());
                        if (tgt == null && (mf & 0x0040) != 0) tgt = resolveRef(ii.owner().asInternalName(), ii.name().stringValue() + ii.type().stringValue());
                        if (tgt != null && !(tgt.cls().equals(c) && tgt.desc().equals(mm.methodType().stringValue())))
                            BRIDGE_TO.put(c + "." + mn + mm.methodType().stringValue(), tgt);
                    }
            }
        }
    }
    /** A local/anonymous class in a STATIC enclosing method has no enclosing instance. */
    static void resolveEnclosingInstances() {
        for (var e : ENCL_METHOD.entrySet()) {
            String[] em = e.getValue();
            Map<String, MInfo> t = METHODS.get(em[0]);
            MInfo m = t == null ? null : t.get(em[1] + em[2]);
            if (m != null && (m.flags() & 0x0008) != 0) OUTER_INST.remove(e.getKey());
        }
        // A local class in a STATIC initializer block has no enclosing instance either, and its
        // constructor's first parameter of the outer type is the source's own (#77 §2). The
        // EnclosingMethod attribute names no method for an initializer, so the block's kind is read
        // from where the class is instantiated: only inside `<clinit>` means static.
        for (var e : ENCL_INIT.entrySet()) {
            Set<String> where = NEW_IN.getOrDefault(e.getKey(), Set.of());
            if (!where.isEmpty() && where.stream().allMatch(w -> w.equals(e.getValue() + ".<clinit>")))
                OUTER_INST.remove(e.getKey());
        }
    }
    /** class -> the `owner.method` bodies that `new` it (for the static-initializer decision above). */
    static final Map<String, Set<String>> NEW_IN = new HashMap<>();
    static boolean isInterface(String c) { Integer f = CLASS_FLAGS.get(c); return f != null && (f & 0x0200) != 0; }
    static boolean isAbstractClass(String c) { Integer f = CLASS_FLAGS.get(c); return f == null || (f & 0x0600) != 0; }
    static String pkgOf(String c) { int i = c.lastIndexOf('/'); return i < 0 ? "" : c.substring(0, i); }
    static MInfo declOf(String c, String nd) { Map<String, MInfo> t = METHODS.get(c); return t == null ? null : t.get(nd); }

    /** §5.4.3.3 / §5.4.3.4: the declaration a symbolic reference resolves to, within the application. */
    static MInfo resolveRef(String owner, String nd) {
        for (String k = owner; k != null && METHODS.containsKey(k); k = SUPER.get(k)) {
            MInfo m = declOf(k, nd);
            if (m != null) return m;
        }
        List<MInfo> ms = maxSpecific(owner, nd, false);
        return ms.isEmpty() ? null : ms.get(0);
    }
    static List<MInfo> maxSpecific(String c, String nd, boolean nonAbstractOnly) {
        List<MInfo> cands = new ArrayList<>();
        for (String a : ancestors(c)) {
            if (!isInterface(a)) continue;
            MInfo m = declOf(a, nd);
            if (m == null || (m.flags() & 0x000A) != 0) continue;         // private / static
            cands.add(m);
        }
        List<MInfo> out = new ArrayList<>();
        for (MInfo m : cands) {
            boolean shadowed = false;
            for (MInfo o : cands) if (o != m && ancestors(o.cls()).contains(m.cls())) shadowed = true;
            if (!shadowed) out.add(m);
        }
        if (nonAbstractOnly) out.removeIf(m -> (m.flags() & 0x0400) != 0);
        return out;
    }
    /** §5.4.5: does `mc` override `mr`? */
    static boolean overridesM(MInfo mc, MInfo mr) {
        if ((mc.flags() & 0x000A) != 0) return false;
        int f = mr.flags();
        if ((f & 0x0005) != 0) return true;
        if ((f & 0x0002) != 0) return false;
        if (pkgOf(mc.cls()).equals(pkgOf(mr.cls()))) return true;
        // §5.4.5 (b): mC overrides mA when it overrides some mB that overrides mA — `C extends B
        // extends A`, A.m package-private, B.m public in A's package, C in another package (#79 §1)
        for (String k = SUPER.get(mc.cls()); k != null && METHODS.containsKey(k); k = SUPER.get(k)) {
            MInfo mid = declOf(k, mr.name() + mr.desc());
            if (mid != null && mid != mr && overridesM(mid, mr) && overridesM(mc, mid)) return true;
        }
        return false;
    }
    static final Set<String> OBJECT_METHODS = Set.of("toString()Ljava/lang/String;", "hashCode()I",
        "equals(Ljava/lang/Object;)Z", "clone()Ljava/lang/Object;", "finalize()V");
    /** §5.4.6 selection for receiver class C; EXTERNAL when the chain leaves the application. */
    static MInfo selectM(String c, MInfo mr) {
        if ((mr.flags() & 0x0002) != 0) return mr;
        String nd = mr.name() + mr.desc();
        for (String k = c; k != null; k = SUPER.get(k)) {
            if (!METHODS.containsKey(k)) {
                if (k.equals("java/lang/Object") && !OBJECT_METHODS.contains(nd)) break;
                return EXTERNAL;
            }
            MInfo m = declOf(k, nd);
            if (m != null && (m == mr || overridesM(m, mr))) return m;
        }
        List<MInfo> ms = maxSpecific(c, nd, true);
        return ms.isEmpty() ? null : ms.get(0);
    }
    static MInfo unbridge(MInfo m) {
        if (m == null || m == EXTERNAL || (m.flags() & 0x1040) == 0) return m;
        MInfo t = BRIDGE_TO.get(m.cls() + "." + m.name() + m.desc());
        return t == null ? m : unbridge(t);
    }
    static String spellM(MInfo m) {
        return cname(m.cls()) + "#" + m.name() + "("
            + String.join(",", sourceParams(m.cls(), m.name(), params(m.desc()))) + ")";
    }

    // ── the declared method universe, so a scorer can scope both sides identically ────────────
    static void emitMethods() {
        TreeSet<String> out = new TreeSet<>();
        for (String c : APP) {
            if (!inScope(c)) continue;
            for (MethodKey k : DECL.getOrDefault(c, Set.of())) {
                if (SYNTH.getOrDefault(c, Set.of()).contains(k)) continue;
                if (excludedName(c, k.name()) || enumPlumbing(c, k.name(), k.params())) continue;
                // `<clinit>` is a caller for a NON-enum class: a static initializer block or a static
                // field initializer is written source (#66 §7); an enum's is plumbing
                if (k.name().equals("<clinit>") && ENUMS.contains(c)) continue;
                if (k.name().startsWith("lambda$")) continue;
                if (k.name().equals("<init>") && DEFAULT_CTOR.contains(c) && k.params().isEmpty()) continue;
                // the SAME spelling the sites use — the source's parameter list, not javac's
                // augmented one (#26 §2)
                out.add(cname(c) + "#" + k.name() + "(" + String.join(",", sourceParams(c, k.name(), k.params())) + ")");
            }
        }
        for (String s : out) System.out.println(s);
        System.err.println("# methods: " + out.size());
    }

    // ── RAW instructions, for the independent-reader cross-check ─────────────────────────────
    // Every invoke instruction exactly as the constant pool spells it: no exclusion, no
    // re-pointing, no name normalisation, no lambda folding. This is the layer at which an
    // independent reader (oracle/javap_reader.py, which shares no code with java.lang.classfile)
    // can be compared instruction for instruction. Agreement here proves the BYTECODE was read
    // correctly; agreement on --mode sites proves the CONVENTIONS were applied correctly. The two
    // are different failure modes and a benchmark has to rule out both.
    //
    // invokedynamic is emitted as the raw BSM target when the bootstrap is LambdaMetafactory,
    // tagged `METHODREF_RAW`, because javap prints the same bootstrap table and the two can be
    // lined up; other bootstraps are emitted as `INVOKEDYNAMIC` naming the call site.
    static void emitRaw(List<ClassModel> models) {
        TreeSet<String> out = new TreeSet<>();
        for (ClassModel cm : models) {
            String cls = cm.thisClass().asInternalName();
            for (MethodModel m : cm.methods()) {
                var code = m.code(); if (code.isEmpty()) continue;
                String from = cls + "." + m.methodName().stringValue() + m.methodType().stringValue();
                for (CodeElement e : code.get()) {
                    if (e instanceof InvokeInstruction ii) {
                        out.add(from + " | " + ii.opcode().name() + " | "
                                + ii.owner().asInternalName() + "." + ii.name().stringValue()
                                + ii.type().stringValue());
                    } else if (e instanceof InvokeDynamicInstruction idi) {
                        String[] t = lambdaTargetRaw(idi);
                        if (t != null) out.add(from + " | METHODREF_RAW | " + t[0] + "." + t[1] + t[2]);
                        else out.add(from + " | INVOKEDYNAMIC | " + idi.name().stringValue()
                                     + idi.typeSymbol().descriptorString());
                    }
                }
            }
        }
        for (String s : out) System.out.println(s);
        System.err.println("# raw invokes (deduplicated): " + out.size());
    }

    // ── the sites ────────────────────────────────────────────────────────────────────────────
    static final Map<String, Integer> PENDING_NEW = new HashMap<>();
    static final Map<String, Integer> SEQ_BY_CALLER = new HashMap<>();
    static final Map<String, String> INIT_COPIES = new HashMap<>();
    /** Does `desc` return `java.util.Iterator` or a subtype of it? */
    static boolean returnsIterator(String desc) {
        int i = desc.lastIndexOf(')');
        String ret = desc.substring(i + 1);
        if (!ret.startsWith("L")) return false;
        String t = ret.substring(1, ret.length() - 1);
        if (t.equals("java/util/Iterator")) return true;
        if (!SUPER.containsKey(t) && !IFACES.containsKey(t)) readPlatformType(t);
        return ancestors(t).contains("java/util/Iterator");
    }
    static void emitSites(List<ClassModel> models) {
        List<String> rows = new ArrayList<>();
        int siteSeq;
        for (ClassModel cm : models) {
            String cls = cm.thisClass().asInternalName();
            if (!inScope(cls)) continue;
            for (MethodModel m : cm.methods()) {
                int f = m.flags().flagsMask();
                String mname = m.methodName().stringValue();
                // A lambda body is ACC_SYNTHETIC, so a blanket synthetic skip drops every call
                // written inside a lambda. Exempt it: those calls are calls the source really makes.
                boolean lambdaBody = mname.startsWith("lambda$");
                if (!lambdaBody && ((f & 0x0040) != 0 || (f & 0x1000) != 0)) continue;
                if ((mname.equals("<clinit>") && ENUMS.contains(cls)) || excludedName(cls, mname)
                    || enumPlumbing(cls, mname, params(m.methodType().stringValue()))) {
                    EXCLUDED_CALLERS.add(cname(cls) + "#" + mname + "("
                        + String.join(",", sourceParams(cls, mname, params(m.methodType().stringValue())))
                        + ")");
                    continue;
                }
                if (mname.equals("<init>") && DEFAULT_CTOR.contains(cls)
                    && m.methodType().stringValue().startsWith("()")) {
                    // AT FULL SIGNATURE FIDELITY. Written as a bare `Type#<init>`, this exclusion
                    // matched a hand-written `Type#<init>(int)` too once projected to Tier B — so
                    // excluding a compiler-synthesised default constructor also deleted every
                    // answer about a real one, while the ground truth went on asking about those
                    // call sites. The result was link groups unwinnable for every tool at once.
                    EXCLUDED_CALLERS.add(cname(cls) + "#<init>()");
                    continue;
                }
                var code = m.code(); if (code.isEmpty()) continue;

                String callerName = mname;
                String callerParams = String.join(",", sourceParams(cls, mname, params(m.methodType().stringValue())));
                if (lambdaBody) {
                    String[] o = lambdaOwner(cls, mname);
                    if (o != null) {
                        callerName = o[0].equals("new") ? "<init>" : o[0];
                        callerParams = o[1];
                    } else {
                        // No indy references the body — another compiler's naming, or a body reached
                        // only reflectively. Fall back to the name, and mark the parameters UNKNOWN
                        // (`*`) rather than inventing one: `*` is compared as a wildcard at Tier A
                        // by bench/model.py, so the row still scores instead of being a guaranteed
                        // miss for every tool.
                        String base = mname.substring("lambda$".length());
                        int k = base.lastIndexOf('$');
                        String c = k > 0 ? base.substring(0, k) : base;
                        callerName = c.equals("new") ? "<init>" : c;
                        callerParams = "*";
                    }
                }
                String caller = cname(cls) + "#" + callerName + "(" + callerParams + ")";

                int line = -1;
                // the sequence number is per CALLER, across a lambda body folded onto it, so a
                // site id is unique (#79 §3: 47 duplicate ids on apache-ant)
                siteSeq = SEQ_BY_CALLER.getOrDefault(caller, 0);
                List<CodeElement> els = code.get().elementList();
                PENDING_NEW.clear();
                boolean writtenNew;
                for (int ei = 0; ei < els.size(); ei++) {
                    CodeElement e = els.get(ei);
                    if (e instanceof java.lang.classfile.instruction.LineNumber ln) { line = ln.line(); continue; }
                    if (e instanceof java.lang.classfile.instruction.NewObjectInstruction no) {
                        PENDING_NEW.merge(no.className().asInternalName(), 1, Integer::sum); continue;
                    }
                    String owner, name, desc, opName;
                    boolean virtualish;
                    if (e instanceof InvokeDynamicInstruction idi) {
                        String[] t = lambdaTarget(idi);
                        if (t == null) continue;
                        owner = t[0]; name = t[1]; desc = t[2];
                        // `Shape::area` / `s::area` dispatch virtually when the handle is
                        // REF_invokeVirtual / REF_invokeInterface (#30 §3)
                        int hk = handleKind(idi);
                        opName = "METHODREF"; virtualish = hk == 5 || hk == 9;
                    } else if (e instanceof InvokeInstruction ii) {
                        owner = ii.owner().asInternalName();
                        name  = ii.name().stringValue();
                        desc  = ii.type().stringValue();
                        opName = ii.opcode().name();
                        virtualish = ii.opcode() == Opcode.INVOKEVIRTUAL || ii.opcode() == Opcode.INVOKEINTERFACE;
                    } else continue;

                    // a WRITTEN `new X(...)`: the NEW instruction precedes its `<init>`; the count
                    // tells a written `new Base()` inside a constructor from the implicit `super()`
                    // that has no NEW in front of it (#66 §3)
                    if (name.equals("<init>") && !opName.equals("METHODREF")) {
                        Integer pending = PENDING_NEW.get(owner);
                        writtenNew = pending != null && pending > 0;
                        if (writtenNew) PENDING_NEW.put(owner, pending - 1);
                    } else writtenNew = false;
                    if (name.startsWith("access$")) {
                        MInfo real = ACCESSOR_TO.get(owner + "." + name + desc);
                        if (real == null) { noteExcluded(caller, owner, name, sourceParams(owner, name, params(desc))); continue; }
                        // the written call is to the private member the accessor forwards to
                        owner = real.cls(); name = real.name(); desc = real.desc();
                        opName = (real.flags() & 0x0008) != 0 ? "INVOKESTATIC" : name.equals("<init>") ? "INVOKESPECIAL" : "INVOKEVIRTUAL";
                        virtualish = false;
                    }
                    List<String> ps = sourceParams(owner, name, params(desc));
                    if (excludedName(owner, name)) continue;
                    // a WRITTEN `Color.values()` / `Color.valueOf(s)` is a call the source makes to a
                    // member the JLS generates: removed from the truth, and from every tool's answer
                    // too (§4.2), so a tool that reports it is not charged (#66, comment)
                    if (enumPlumbing(owner, name, ps)) { noteExcluded(caller, owner, name, ps); continue; }
                    // ── IMPLICIT super() ────────────────────────────────────────────────────
                    // `Square(double s) { this.s = s; }` compiles with `invokespecial Base.<init>()`
                    // at the top of the body. The source writes no such call, and charging every
                    // constructor in a corpus with one would swamp the measurement.
                    //
                    // An EXPLICITLY written bare `super();` compiles identically and is dropped with
                    // it — undecidable from the instruction, and the same trade the boxing and
                    // enhanced-for exclusions already make. A `super(args)` call HAS arguments, so
                    // `Unit() { super(1); }` survives; that is the case real code writes.
                    if (name.equals("<init>") && mname.equals("<init>") && ps.isEmpty() && !writtenNew
                        && owner.equals(SUPER.get(cls))) { noteExcluded(caller, owner, name, ps); continue; }
                    // an ANONYMOUS class's constructor is javac's, and its `super(args)` is the
                    // `new Base(args) { … }` the enclosing method already scores as a call to the
                    // anonymous class's own constructor (with `Base#<init>` accepted as its
                    // ancestor). Scoring the chain again under a caller no source writes charged
                    // every source tool a miss (#78 §2). Removed from both sides.
                    if (name.equals("<init>") && mname.equals("<init>") && !writtenNew && isAnonymous(cls)
                        && owner.equals(SUPER.get(cls))) { noteExcluded(caller, owner, name, ps); continue; }
                    // An ENUM's own `<init>` chains to `java.lang.Enum.<init>(String,int)`, which is
                    // pure JLS plumbing, and an enum-constant BODY's constructor chains to the
                    // enum's. Neither appears in the file.
                    if (name.equals("<init>") && owner.equals("java/lang/Enum")) continue;
                    if (name.equals("<init>") && isEnumConstantBody(cls) && owner.equals(SUPER.get(cls)))
                        { noteExcluded(caller, owner, name, ps); continue; }
                    if (owner.startsWith("java/lang/invoke")) continue;
                    // string concatenation lowering
                    if (name.equals("makeConcatWithConstants") || owner.equals("java/lang/StringBuilder")) continue;
                    if (owner.equals("java/lang/String") && name.equals("valueOf") && ps.equals(List.of("Object"))) continue;
                    // boxing / unboxing
                    if (BOX.contains(owner) && name.equals("valueOf") && ps.size() == 1 && PRIMS.contains(ps.get(0))) continue;
                    if (BOX.contains(owner) && UNBOX.contains(name) && ps.isEmpty()) continue;
                    // the enhanced-for iterator triple, keyed on the MECHANISM not on java.util. Only the
                    // LOWERED `iterator()` — the one javac follows immediately with the loop's
                    // `hasNext()` test — is dropped; a written `c.iterator()` passed to a constructor or
                    // returned is a real call and stays (44 of them on apache-ant, #26 §4).
                    // (a covariant `iterator()` returning a subtype of Iterator is the same
                    // lowering, #66 §5; and the loop's `hasNext`/`next` are always owned by
                    // `java/util/Iterator` itself — on a subtype they are the source's own, #66 §4)
                    if (name.equals("iterator") && ps.isEmpty() && returnsIterator(desc)
                        && nextInvokeIs(els, ei, "hasNext")) { noteExcluded(caller, owner, name, ps); continue; }
                    if ((name.equals("hasNext") || name.equals("next")) && ps.isEmpty()
                        && owner.equals("java/util/Iterator")) continue;
                    // try-with-resources: the `addSuppressed` and the pair of `close()` calls javac
                    // generates on the normal and exceptional paths — both at the try header's line,
                    // in a method that also holds the `addSuppressed`. A `close()` the source writes is
                    // alone on its line and stays (#26 §5).
                    if (name.equals("addSuppressed") && ps.equals(List.of("Throwable"))) continue;
                    if (name.equals("close") && ps.isEmpty() && twrClose(els, ei, line, owner))
                        { noteExcluded(caller, owner, name, ps); continue; }
                    // the bound-method-reference receiver null check (decidable — see above)
                    if (owner.equals("java/util/Objects") && name.equals("requireNonNull")
                        && boundRefNullCheck(els, ei)) continue;

                    // ── the declared target, by JVMS §5.4.3.3 resolution ─────────────────────
                    // The constant pool names the receiver's STATIC type, which need not declare the
                    // member it names. `Set#addAll` is declared on AbstractCollection; a tool that
                    // answers where the method is declared is not wrong, so both sides resolve here.
                    List<String> declPs = params(desc);
                    String nd = name + desc;
                    MInfo mr = METHODS.containsKey(owner) ? resolveRef(owner, nd) : null;
                    // a reference that resolves to a BRIDGE or a synthetic accessor names, in the
                    // source, the method it forwards to: `Shw.pub()` is `Hid#pub()` (visibility
                    // bridge, #77 §1), `Inner(Outer, Outer$1)` is `Inner(Outer)` (#66 §2), and a
                    // generic bridge `compareTo(Object)` is the `compareTo(T)` the source declares
                    if (mr != null && (mr.flags() & 0x1040) != 0 && BRIDGE_TO.containsKey(mr.cls() + "." + mr.name() + mr.desc())) {
                        mr = unbridge(mr);
                        owner = mr.cls(); name = mr.name(); desc = mr.desc(); nd = name + desc;
                        ps = sourceParams(owner, name, params(desc)); declPs = params(desc);
                    }
                    boolean declaredInApp = mr != null && APP.contains(mr.cls());
                    String dc = declaredInApp ? mr.cls() : owner;
                    if (mr == null) mr = new MInfo(owner, name, desc, 0x0001 | 0x0400);   // external: a public abstract stand-in
                    // A member another compiler generates is not a written call. Tested against the
                    // DECLARING class, which is what the emitted target names.
                    if (declaredInApp && SYNTH.getOrDefault(dc, Set.of()).contains(new MethodKey(name, declPs))
                        && BRIDGE_TO.get(dc + "." + nd) == null)
                        { noteExcluded(caller, dc, name, ps); continue; }

                    String sig = "#" + name + "(" + String.join(",", ps) + ")";

                    // ── the three bounds (issue #30) ─────────────────────────────────────────
                    //   certain   the declared target — what the instruction names, resolved
                    //   possible  every method JVMS §5.4.6 SELECTS for some concrete application
                    //             receiver that is the static type or a subtype of it, bridges
                    //             followed to the override they forward to; for a non-virtual
                    //             instruction, the declared target alone
                    //   rta       the same, over the receivers the application instantiates
                    // `possible` holds what can RUN: an abstract declared target is in `certain`
                    // and not in `possible`, so an interface with one implementor IS uniquely
                    // linked — to the implementor — and naming either is accepted by the scorer.
                    TreeSet<String> certain  = new TreeSet<>();
                    TreeSet<String> possible = new TreeSet<>();
                    TreeSet<String> rta      = new TreeSet<>();
                    TreeSet<String> ancestorsOf = new TreeSet<>();
                    if (declaredInApp && inScope(dc)) certain.add(cname(dc) + sig);
                    if (virtualish && !name.equals("<init>")) {
                        for (String c : APP) {
                            if (!(c.equals(owner) || ancestors(c).contains(owner))) continue;
                            if (isAbstractClass(c)) continue;
                            MInfo sel = selectM(c, mr);
                            if (sel == null || sel == EXTERNAL) continue;
                            MInfo real = unbridge(sel);
                            if (!APP.contains(real.cls()) || !inScope(real.cls())) continue;
                            String sp = spellM(real);
                            possible.add(sp);
                            if (INSTANTIATED.contains(c)) rta.add(sp);
                        }
                    } else if (declaredInApp && inScope(dc)) {
                        MInfo real = unbridge(mr);
                        if (real != null && real != EXTERNAL && APP.contains(real.cls()) && inScope(real.cls())
                            && (real.flags() & 0x0400) == 0) {
                            possible.add(spellM(real));
                            rta.add(spellM(real));
                        }
                    }
                    // A call whose only implementations are LAMBDAS (a functional interface the
                    // application never implements with a class) selects nothing in the application:
                    // the runnable target is a lambda body, which this oracle folds into its
                    // container and does not model as a target (the declared blind spot). The
                    // declaration is then the one answer a tool can be scored on, so the site stays
                    // scorable with `possible = {declared}` rather than silently leaving the universe.
                    if (possible.isEmpty() && !certain.isEmpty()) { possible.addAll(certain); rta.addAll(certain); }
                    // ── THE DECLARING-ANCESTOR SET ────────────────────────────────────────────
                    // A tool may name the type that DECLARES the member rather than the receiver's
                    // static type, or a supertype that also declares it; and for an anonymous class's
                    // constructor, the type the SOURCE names (`new ChannelInitializer<>() {…}`).
                    // Neither is a false positive; neither is `exact`.
                    if (name.equals("<init>") && APP.contains(owner) && isAnonymous(owner)) {
                        String sup = supertypeOf(owner);
                        if (APP.contains(sup) && inScope(sup))
                            for (MethodKey k : DECL.getOrDefault(sup, Set.of()))
                                if (k.name().equals("<init>")
                                    && !SYNTH.getOrDefault(sup, Set.of()).contains(k))
                                    ancestorsOf.add(cname(sup) + "#<init>("
                                        + String.join(",", sourceParams(sup, "<init>", k.params())) + ")");
                    }
                    if (!name.equals("<init>")) {
                        Set<String> abases = new LinkedHashSet<>(List.of(owner));
                        if (declaredInApp) abases.add(dc);
                        for (String base : abases)
                            for (String anc : ancestors(base)) {
                                MInfo am = declOf(anc, nd);
                                // not a bridge, and NOT private or static (0x000A, the mask
                                // §5.4.5 uses in overridesM): a private superclass method can
                                // never be the target of a call on the subclass, so naming it
                                // is wrong, not vague (#47 — `Outer#secret` beside `OuterSub#secret`)
                                if (am != null && APP.contains(anc) && inScope(anc)
                                    && (am.flags() & 0x0040) == 0 && (am.flags() & 0x000A) == 0)
                                    ancestorsOf.add(spellM(am));
                            }
                        // the declared target itself, when it cannot run here — abstract, or a
                        // concrete method of an abstract class every concrete subclass overrides —
                        // is an ancestor answer: naming the declaration is never wrong
                        if (declaredInApp && inScope(dc) && !possible.contains(cname(dc) + sig)) ancestorsOf.add(cname(dc) + sig);
                    }

                    // ── A CALL WHOSE DECLARED TARGET IS OUTSIDE THE APPLICATION IS A BOUNDARY ──
                    // `map.get(k)` on a `java.util.Map`: the selection above ran over the
                    // APPLICATION's concrete receivers only, and every JDK implementation of `Map`
                    // — the ones that actually run here — was skipped as EXTERNAL. An envelope
                    // computed over half the receivers is not an envelope: on maven-core it named
                    // one anonymous `AbstractMap` subclass as the UNIQUE target of every `Map.get`
                    // in the code base, credited the tool that guesses application-only CHA and
                    // charged the one that answered `Map#get`. The TypeScript oracle already stops
                    // at the subject's edge for the same reason; this is the same stance. The
                    // application implementors are kept as ACCEPTED answers (declaring_ancestors):
                    // naming one is not wrong, naming none is not a miss, and the site is neither
                    // uniquely linked nor a recall denominator (issue #30, second reopening).
                    if (!declaredInApp) {
                        ancestorsOf.addAll(possible);
                        possible.clear();
                        rta.clear();
                    }
                    // A site with no declared app target leaves the application. It is recorded —
                    // `kind: "boundary"` — because the count of boundary sites is what makes a
                    // recall denominator auditable. It contributes to no app-internal recall
                    // denominator.
                    String kind = (certain.isEmpty() && possible.isEmpty()) ? "boundary" : "internal";

                    ancestorsOf.removeAll(possible);   // a type in both is already a real target
                    // javac copies an instance field initializer and every `{ }` block into each
                    // constructor that does not delegate with `this(...)`: one written call became
                    // one site per constructor (#78 §1). The copy is recognised by its identity —
                    // same class, line, instruction and target in another constructor — and scored
                    // once, under the first constructor that carries it.
                    if (mname.equals("<init>") && !lambdaBody) {
                        String copyKey = cls + "|" + line + "|" + opName + "|" + owner + "." + name + desc;
                        String firstCtor = INIT_COPIES.putIfAbsent(copyKey, caller);
                        if (firstCtor != null && !firstCtor.equals(caller)) continue;
                    }
                    rows.add(siteJson(caller, line, siteSeq++, opName,
                                      cname(owner), name, ps, kind, certain, possible, rta, ancestorsOf));
                }
                SEQ_BY_CALLER.put(caller, siteSeq);
            }
        }
        Collections.sort(rows);
        if (!mode.equals("excluded")) {
            for (String r : rows) System.out.println(r);
            System.err.println("# sites: " + rows.size());
        }
    }

    /** Record an app-internal edge a documented exclusion removed, so the scorer can remove it from
     *  every tool's output too rather than charging the tool for emitting it. */
    static void noteExcluded(String caller, String ownerInternal, String name, List<String> ps) {
        if (!APP.contains(ownerInternal) || !inScope(ownerInternal)) return;
        EXCLUDED_EDGES.add(caller + " -> " + cname(ownerInternal)
                           + "#" + name + "(" + String.join(",", ps) + ")");
    }

    static String siteJson(String caller, int line, int seq, String op, String recvType,
                           String name, List<String> ps, String kind,
                           Set<String> certain, Set<String> possible, Set<String> rta,
                           Set<String> ancestorsOf) {
        StringBuilder b = new StringBuilder();
        // site_id leads the row so the natural string sort above is a stable, content-defined order.
        b.append('{');
        kv(b, "site_id", caller + "@" + line + "#" + seq); b.append(',');
        kv(b, "caller", caller);                            b.append(',');
        b.append("\"line\":").append(line).append(',');
        b.append("\"seq\":").append(seq).append(',');
        kv(b, "op", op);                                    b.append(',');
        kv(b, "receiver_static_type", recvType);            b.append(',');
        kv(b, "callee_name", name);                         b.append(',');
        b.append("\"callee_params\":").append(arr(ps));      b.append(',');
        kv(b, "kind", kind);                                b.append(',');
        b.append("\"certain\":").append(arr(certain));       b.append(',');
        b.append("\"possible\":").append(arr(possible));     b.append(',');
        b.append("\"possible_rta\":").append(arr(rta));      b.append(',');
        b.append("\"declaring_ancestors\":").append(arr(ancestorsOf)); b.append(',');
        b.append("\"unique\":").append(possible.size() == 1); b.append(',');
        b.append("\"unique_rta\":").append(rta.size() == 1);
        b.append('}');
        return b.toString();
    }
    static void kv(StringBuilder b, String k, String v) {
        b.append('"').append(k).append("\":").append(q(v));
    }
    static String arr(Collection<String> xs) {
        StringBuilder b = new StringBuilder("[");
        boolean first = true;
        for (String x : xs) { if (!first) b.append(','); b.append(q(x)); first = false; }
        return b.append(']').toString();
    }
    static String q(String s) {
        StringBuilder b = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"'  -> b.append("\\\"");
                case '\\' -> b.append("\\\\");
                case '\n' -> b.append("\\n");
                case '\r' -> b.append("\\r");
                case '\t' -> b.append("\\t");
                default   -> { if (c < 0x20) b.append(String.format("\\u%04x", (int) c)); else b.append(c); }
            }
        }
        return b.append('"').toString();
    }
}
