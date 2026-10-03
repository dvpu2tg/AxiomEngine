// WALA call graphs over the subject's bytecode — CHA, RTA and 0-CFA — as an independently-written
// competitor row on a declared `bytecode` budget (issue #6).
//
// Usage: java -cp <wala cp>:. WalaCallGraph --app <classes dir> [--cp <dir>] --algo cha|rta|0cfa
//                                            --out <tsv>
//
// Every APPLICATION method is an entry point (AllApplicationEntrypoints), because the benchmark
// scores a whole-program view rather than reachability from main(); the oracle does the same.
// Dependencies are absent, as they are for every other tool on a Maven subject.
//
// Output, one edge per line, tab-separated:
//     caller<TAB>callee<TAB>algo
// where a method is spelled `pkg.Outer$Inner#name(SimpleParam,…)` — the adapter reads it.
import com.ibm.wala.classLoader.IClass;
import com.ibm.wala.classLoader.IMethod;
import com.ibm.wala.core.util.config.AnalysisScopeReader;
import com.ibm.wala.core.java11.Java9AnalysisScopeReader;
import com.ibm.wala.ipa.callgraph.*;
import com.ibm.wala.ipa.callgraph.cha.CHACallGraph;
import com.ibm.wala.ipa.callgraph.impl.AllApplicationEntrypoints;
import com.ibm.wala.ipa.callgraph.impl.DefaultEntrypoint;
import com.ibm.wala.ipa.cha.IClassHierarchy;
import com.ibm.wala.shrike.shrikeCT.BootstrapMethodsReader;
import com.ibm.wala.shrike.shrikeCT.ConstantPoolParser;
import com.ibm.wala.ssa.IR;
import com.ibm.wala.ssa.SSAInstruction;
import com.ibm.wala.ssa.SSAInvokeDynamicInstruction;
import com.ibm.wala.types.Selector;
import com.ibm.wala.ipa.callgraph.impl.Util;
import com.ibm.wala.ipa.cha.ClassHierarchy;
import com.ibm.wala.ipa.cha.ClassHierarchyFactory;
import com.ibm.wala.types.ClassLoaderReference;
import com.ibm.wala.types.TypeReference;

import java.io.*;
import java.nio.file.*;
import java.util.*;

public class WalaCallGraph {
  public static void main(String[] a) throws Exception {
    String app = null, cp = null, algo = "cha", out = null;
    for (int i = 0; i < a.length; i++) {
      switch (a[i]) {
        case "--app": app = a[++i]; break;
        case "--cp": cp = a[++i]; break;
        case "--algo": algo = a[++i]; break;
        case "--out": out = a[++i]; break;
        default: throw new IllegalArgumentException(a[i]);
      }
    }
    // the Java 9+ reader resolves `stdlib` to the running JDK's jrt modules; the base reader
    // expects rt.jar and fails to load java.lang.Object on any modern JDK
    AnalysisScopeReader reader = Java9AnalysisScopeReader.instance;
    AnalysisScope scope = reader.makePrimordialScope(null);
    reader.addClassPathToScope(app, scope, ClassLoaderReference.Application);
    if (cp != null && Files.isDirectory(Path.of(cp))) {
      // the classpath tree is context, not subject: Extension loader, so it is not an entry point
      reader.addClassPathToScope(cp, scope, ClassLoaderReference.Extension);
    }
    ClassHierarchy cha = ClassHierarchyFactory.makeWithRoot(scope);
    CHA = cha;
    // Every concrete application method is an entry point, with every concrete APPLICATION
    // subtype of each parameter type allocated for it (plus the declared type where concrete).
    // AllApplicationEntrypoints fabricates one arbitrary implementor per interface-typed
    // parameter, which for RTA and 0-CFA made the row a hierarchy-order sample rather than the
    // whole-program view the benchmark scores (#25); WALA's SubtypesEntrypoint allocates every
    // subtype in the JDK too, which on a parameter typed Object is the whole platform and did
    // not finish. Application subtypes are the set the oracle's envelope is built from.
    // For RTA the fabricated receivers are immaterial — its instantiated set is every `new` in
    // the application once every method is reachable — and the subtype allocations made it run
    // 50x longer on rxjava without finishing, so RTA keeps WALA's default entry set; 0-CFA, where
    // the receivers decide the graph, gets the application subtypes.
    List<Entrypoint> entries = new ArrayList<>();
    for (IClass c : cha) {
      if (!isApp(c)) continue;
      for (IMethod m : c.getDeclaredMethods()) {
        if (m.isAbstract() || m.isNative()) continue;
        entries.add(algo.equals("0cfa") ? new AppSubtypesEntrypoint(m, cha) : new DefaultEntrypoint(m, cha));
      }
    }
    long t0 = System.nanoTime();
    CallGraph cg;
    if (algo.equals("cha")) {
      CHACallGraph g = new CHACallGraph(cha, true);
      g.init(entries);
      cg = g;
    } else {
      AnalysisOptions options = new AnalysisOptions(scope, entries);
      options.setReflectionOptions(AnalysisOptions.ReflectionOptions.NONE);
      IAnalysisCacheView cache = CACHE;
      CallGraphBuilder<?> builder = algo.equals("rta")
          ? Util.makeRTABuilder(options, cache, cha)
          : Util.makeZeroCFABuilder(com.ibm.wala.classLoader.Language.JAVA, options, cache, cha);
      cg = builder.makeCallGraph(options, null);
    }
    long ms = (System.nanoTime() - t0) / 1_000_000;
    int edges = 0, refs = 0;
    try (PrintWriter w = new PrintWriter(new BufferedWriter(new FileWriter(out)))) {
      Set<String> seen = new HashSet<>();
      for (CGNode n : cg) {
        IMethod m = n.getMethod();
        if (!isApp(m.getDeclaringClass())) continue;
        String caller = spell(m);
        for (Iterator<CGNode> it = cg.getSuccNodes(n); it.hasNext();) {
          CGNode t = it.next();
          IMethod tm = t.getMethod();
          if (tm.isSynthetic() && !isApp(tm.getDeclaringClass())) continue;
          String line = caller + "\t" + spell(tm) + "\t" + algo;
          if (seen.add(line)) { w.println(line); edges++; }
        }
      }
      // METHOD REFERENCES (#25). `Foo::bar` compiles to an invokedynamic whose LambdaMetafactory
      // bootstrap names the implementation method in the constant pool. WALA's CHA graph has no
      // target for an invokedynamic and its propagation builders route it through a synthetic
      // summary class in its own loader, so the enclosing method never showed the edge. The oracle
      // records a METHODREF site as a call from the enclosing method to the referenced method,
      // and so does this: read WALA's own IR for every application method, and for each
      // LambdaMetafactory bootstrap emit that edge. A lambda BODY (`lambda$m$0`) is not a method
      // reference and is not emitted here; its calls are its own node's, folded by the resolver.
      for (IClass c : cha) {
        if (!isApp(c)) continue;
        for (IMethod m : c.getDeclaredMethods()) {
          if (m.isAbstract() || m.isNative()) continue;
          IR ir;
          try { ir = CACHE.getIR(m); } catch (Throwable e) { continue; }
          if (ir == null) continue;
          for (SSAInstruction ins : ir.getInstructions()) {
            if (!(ins instanceof SSAInvokeDynamicInstruction)) continue;
            BootstrapMethodsReader.BootstrapMethod bs = ((SSAInvokeDynamicInstruction) ins).getBootstrap();
            if (bs == null || !bs.methodClass().equals("java/lang/invoke/LambdaMetafactory")) continue;
            if (bs.callArgumentCount() < 2) continue;
            try {
              ConstantPoolParser pool = bs.getCP();
              int idx = bs.callArgumentIndex(1);
              String cls = pool.getCPHandleClass(idx), name = pool.getCPHandleName(idx), desc = pool.getCPHandleType(idx);
              if (name.startsWith("lambda$")) continue;
              String target = spellHandle(cls, name, desc);
              if (target == null) continue;
              String line = spell(m) + "\t" + target + "\t" + algo;
              if (seen.add(line)) { w.println(line); edges++; refs++; }
            } catch (Throwable e) { /* an unreadable constant pool entry: no edge, not a crash */ }
          }
        }
      }
    }
    System.err.println("wala " + algo + ": " + cg.getNumberOfNodes() + " nodes, " + edges
        + " application-caller edges (" + refs + " method references), " + ms + " ms build");
  }

  static ClassHierarchy CHA;
  static final IAnalysisCacheView CACHE = new AnalysisCacheImpl();

  /** The referenced method of a `Foo::bar` handle, spelled like every other target; null if the
   *  class is not in the hierarchy (a dependency: absent, as every other tool's rows into it). */
  static String spellHandle(String cls, String name, String desc) {
    IClass c = CHA.lookupClass(TypeReference.findOrCreate(ClassLoaderReference.Application, "L" + cls));
    if (c == null) c = CHA.lookupClass(TypeReference.findOrCreate(ClassLoaderReference.Extension, "L" + cls));
    if (c == null) c = CHA.lookupClass(TypeReference.findOrCreate(ClassLoaderReference.Primordial, "L" + cls));
    if (c == null) return null;
    IMethod m = c.getMethod(Selector.make(name + desc));
    if (m == null) return null;
    return spell(m);
  }

  /** DefaultEntrypoint, with each parameter's receiver set = the declared type if concrete, plus
   *  every concrete application subtype of it. */
  static final class AppSubtypesEntrypoint extends DefaultEntrypoint {
    AppSubtypesEntrypoint(IMethod m, IClassHierarchy cha) { super(m, cha); }

    @Override
    protected TypeReference[] makeParameterTypes(IMethod method, int i) {
      TypeReference nominal = method.getParameterType(i);
      if (nominal.isPrimitiveType() || nominal.isArrayType()) return new TypeReference[] {nominal};
      IClass c = getCha().lookupClass(nominal);
      if (c == null) return new TypeReference[] {nominal};
      // only a parameter whose declared type is the APPLICATION's own is expanded: a parameter
      // typed by a platform interface (`Function`, `Consumer`, `Object`) has every operator in
      // rxjava as an implementor, and allocating them all at every entry made 0-CFA thrash for
      // an hour without finishing. The declared type stands for those, as WALA's default does.
      if (!isApp(c)) return new TypeReference[] {nominal};
      LinkedHashSet<TypeReference> out = new LinkedHashSet<>();
      if (!c.isAbstract() && !c.isInterface()) out.add(nominal);
      Collection<IClass> subs = c.isInterface() ? getCha().getImplementors(nominal) : getCha().computeSubClasses(nominal);
      for (IClass s : subs) {
        if (s.isAbstract() || s.isInterface()) continue;
        if (!isApp(s)) continue;
        out.add(s.getReference());
      }
      if (out.isEmpty()) out.add(nominal);
      return out.toArray(new TypeReference[0]);
    }
  }

  static boolean isApp(IClass c) {
    return c.getClassLoader().getReference().equals(ClassLoaderReference.Application);
  }

  /** `pkg.Outer$Inner#name(Simple,…)` — internal `$` nesting kept; the resolver reads it.
   *  An ANONYMOUS class (`Outer$1`) is spelled by its supertype, `Outer$anon:Runnable`, the way the
   *  oracle keys it (minus the line, which no bytecode reader has); a LOCAL class's counter
   *  prefix (`Outer$1Local`) is stripped to `Outer$Local`. Both are the oracle's own conventions,
   *  docs/PROTOCOL.md §3, applied here so the row is read rather than dropped. */
  static String spell(IMethod m) {
    IClass c = m.getDeclaringClass();
    // an ENUM CONSTANT BODY folds onto its enum, as the oracle folds it (docs/PROTOCOL.md §3)
    IClass sup = c.getSuperclass();
    if (sup != null && ((sup.getModifiers() & 0x4000) != 0) && isAnonLeaf(c)) {
      return className(sup) + "#" + nameOf(m) + "(" + params(m) + ")";
    }
    return className(c) + "#" + nameOf(m) + "(" + params(m) + ")";
  }

  static boolean isAnonLeaf(IClass c) {
    String n = c.getName().toString();
    int d = n.lastIndexOf('$');
    if (d < 0 || d + 1 >= n.length()) return false;
    for (int i = d + 1; i < n.length(); i++) if (!Character.isDigit(n.charAt(i))) return false;
    return true;
  }

  /** `pkg.Outer$Inner`, with EVERY numeric segment converted, outermost first (#25): an anonymous
   *  class by its supertype (`Outer$anon:Runnable`), a local class without its counter
   *  (`Outer$1Local` -> `Outer$Local`), nested ones chained (`Outer$anon:A$anon:B`) the way the
   *  oracle keys them, minus the line no bytecode reader has. Each prefix is looked up in the class
   *  hierarchy for its supertype. */
  static String className(IClass c) {
    String internal = c.getName().toString().substring(1);          // pkg/Outer$1$2
    int slash = internal.lastIndexOf('/');
    String pkg = slash >= 0 ? internal.substring(0, slash + 1) : "";
    String leaf = internal.substring(slash + 1);
    String[] parts = leaf.split("\\$", -1);
    StringBuilder raw = new StringBuilder(parts[0]);       // the internal prefix, for lookups
    StringBuilder out = new StringBuilder(parts[0]);       // the spelled prefix
    for (int i = 1; i < parts.length; i++) {
      String seg = parts[i];
      raw.append('$').append(seg);
      int k = 0;
      while (k < seg.length() && Character.isDigit(seg.charAt(k))) k++;
      if (k == 0) { out.append('$').append(seg); continue; }
      String rest = seg.substring(k);
      if (!rest.isEmpty()) { out.append('$').append(rest); continue; }        // local class
      IClass here = CHA.lookupClass(TypeReference.findOrCreate(c.getClassLoader().getReference(), "L" + pkg + raw));
      String supName = "Object";
      if (here != null) {
        IClass sup = here.getSuperclass();
        if (sup != null && !sup.getName().toString().equals("Ljava/lang/Object")) {
          supName = sup.getName().getClassName().toString();
        } else if (!here.getDirectInterfaces().isEmpty()) {
          supName = here.getDirectInterfaces().iterator().next().getName().getClassName().toString();
        }
      }
      out.append("$anon:").append(supName);
    }
    return (pkg + out).replace('/', '.');
  }

  static String nameOf(IMethod m) {
    return m.isInit() ? "<init>" : m.isClinit() ? "<clinit>" : m.getName().toString();
  }

  static String params(IMethod m) {
    StringBuilder ps = new StringBuilder();
    for (int i = 0; i < m.getNumberOfParameters(); i++) {
      if (!m.isStatic() && i == 0) continue;
      if (ps.length() > 0) ps.append(',');
      ps.append(simple(m.getParameterType(i)));
    }
    return ps.toString();
  }

  static String simple(TypeReference t) {
    int dims = 0;
    while (t.isArrayType()) { dims++; t = t.getArrayElementType(); }
    String n = t.isPrimitiveType() ? primitive(t) : t.getName().getClassName().toString();
    StringBuilder b = new StringBuilder(n);
    for (int i = 0; i < dims; i++) b.append("[]");
    return b.toString();
  }

  static String primitive(TypeReference t) {
    if (t.equals(TypeReference.Int)) return "int";
    if (t.equals(TypeReference.Long)) return "long";
    if (t.equals(TypeReference.Boolean)) return "boolean";
    if (t.equals(TypeReference.Byte)) return "byte";
    if (t.equals(TypeReference.Char)) return "char";
    if (t.equals(TypeReference.Short)) return "short";
    if (t.equals(TypeReference.Float)) return "float";
    if (t.equals(TypeReference.Double)) return "double";
    if (t.equals(TypeReference.Void)) return "void";
    return t.getName().toString();
  }
}
