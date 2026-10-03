// GATE 1c — the envelope, checked by an independent implementation of JVMS §5.4.3.3 (resolution)
// and §5.4.6 (selection), written by the peer session that found issue #30 and kept separate from
// the oracle's own envelope code on purpose. It reuses ClassfileGroundTruth ONLY for reading and
// naming (class index, cname, sourceParams, lambda owners), recomputes `possible` for every
// virtual, interface and method-reference site from the class files, and diffs it against what
// the oracle EMITTED in gt.sites.jsonl. Any disagreement is printed and the exit code is 1.
//
// Usage: java -cp <oracle classes> EnvelopeCheck --app <classes> [--include-prefix …] [--only-types …]
//                                               --sites <gt.sites.jsonl>
import java.lang.classfile.*;
import java.lang.classfile.constantpool.MethodHandleEntry;
import java.lang.classfile.instruction.*;
import java.nio.file.*;
import java.util.*;

public class EnvelopeCheck {
  record M(String cls, String name, String desc, int flags) {}
  static Map<String, ClassModel> CM = new HashMap<>();
  // the checker's OWN hierarchy — application classes from the models it reads, platform
  // classes from the running JDK read by the checker itself — so a blind spot in the oracle's
  // SUPER/IFACES (#30, reopened: chains through JDK classes) is not shared
  static Map<String, String> SUP = new HashMap<>();
  static Map<String, List<String>> IFS = new HashMap<>();
  static Set<String> PLATFORM = new HashSet<>();
  static String superOf(String c) { return SUP.get(c); }
  static List<String> ancestorsOf(String c) {
    List<String> out = new ArrayList<>(); Set<String> seen = new HashSet<>();
    Deque<String> q = new ArrayDeque<>(); q.add(c);
    while (!q.isEmpty()) {
      String x = q.poll();
      String s = SUP.get(x);
      if (s != null && seen.add(s)) { out.add(s); q.add(s); }
      for (String i : IFS.getOrDefault(x, List.of())) if (seen.add(i)) { out.add(i); q.add(i); }
    }
    return out;
  }
  static void readPlatform(String t) {
    if (t == null || CM.containsKey(t) || PLATFORM.contains(t)) return;
    byte[] bytes = null;
    for (ClassLoader cl : new ClassLoader[]{ClassLoader.getPlatformClassLoader(), ClassLoader.getSystemClassLoader()}) {
      try (var in = cl.getResourceAsStream(t + ".class")) { if (in != null) { bytes = in.readAllBytes(); break; } } catch (Exception e) { /* next */ }
    }
    if (bytes == null) return;
    ClassModel cm;
    try { cm = ClassFile.of().parse(bytes); } catch (Throwable e) { return; }
    PLATFORM.add(t); CM.put(t, cm);
    cm.superclass().ifPresent(sc -> SUP.put(t, sc.asInternalName()));
    List<String> ifs = new ArrayList<>(); for (var i : cm.interfaces()) ifs.add(i.asInternalName()); IFS.put(t, ifs);
    Map<String, M> tb = new HashMap<>();
    for (var mm : cm.methods()) tb.put(mm.methodName().stringValue() + mm.methodType().stringValue(),
        new M(t, mm.methodName().stringValue(), mm.methodType().stringValue(), mm.flags().flagsMask()));
    METH.put(t, tb);
    readPlatform(SUP.get(t)); for (String i : ifs) readPlatform(i);
  }
  static Map<String, Map<String, M>> METH = new HashMap<>();
  static Map<String, M> BRIDGE_TARGET = new HashMap<>();
  static final M EXTERNAL = new M("<external>", "", "", 0);
  static final Set<String> OBJECT_METHODS = Set.of("toString()Ljava/lang/String;", "hashCode()I",
      "equals(Ljava/lang/Object;)Z", "clone()Ljava/lang/Object;", "finalize()V");

  static String pkg(String c) { int i = c.lastIndexOf('/'); return i < 0 ? "" : c.substring(0, i); }
  static boolean isIface(String c) { var m = CM.get(c); return m != null && (m.flags().flagsMask() & 0x0200) != 0; }
  static boolean isAbstract(String c) { var m = CM.get(c); return m == null || (m.flags().flagsMask() & 0x0600) != 0; }
  static M decl(String c, String nd) { var t = METH.get(c); return t == null ? null : t.get(nd); }
  static M resolve(String c, String nd) {
    for (String k = c; k != null && CM.containsKey(k); k = superOf(k)) {
      M m = decl(k, nd); if (m != null) return m;
    }
    List<M> ms = maxSpecific(c, nd, false); return ms.isEmpty() ? null : ms.get(0);
  }
  static List<M> maxSpecific(String c, String nd, boolean nonAbstractOnly) {
    List<M> cands = new ArrayList<>();
    for (String a : ancestorsOf(c)) {
      if (!isIface(a)) continue;
      M m = decl(a, nd); if (m == null) continue;
      if ((m.flags() & 0x000A) != 0) continue;
      cands.add(m);
    }
    List<M> out = new ArrayList<>();
    for (M m : cands) {
      boolean shadowed = false;
      for (M o : cands) if (o != m && ancestorsOf(o.cls()).contains(m.cls())) shadowed = true;
      if (!shadowed) out.add(m);
    }
    if (nonAbstractOnly) out.removeIf(m -> (m.flags() & 0x0400) != 0);
    return out;
  }
  static boolean overrides(M mc, M mr) {
    if ((mc.flags() & 0x000A) != 0) return false;
    int f = mr.flags();
    if ((f & 0x0005) != 0) return true;
    if ((f & 0x0002) != 0) return false;
    if (pkg(mc.cls()).equals(pkg(mr.cls()))) return true;
    for (String k = superOf(mc.cls()); k != null && CM.containsKey(k); k = superOf(k)) {
      M mid = decl(k, mr.name() + mr.desc());
      // §5.4.5 (b), transitively: mC overrides mB which overrides mA (#79 §1)
      if (mid != null && mid != mr && overrides(mid, mr) && overrides(mc, mid)) return true;
    }
    return false;
  }
  static M select(String c, M mr) {
    if ((mr.flags() & 0x0002) != 0) return mr;
    String nd = mr.name() + mr.desc();
    for (String k = c; k != null; k = superOf(k)) {
      if (!CM.containsKey(k)) {
        if (k.equals("java/lang/Object") && !OBJECT_METHODS.contains(nd)) break;
        return EXTERNAL;
      }
      M m = decl(k, nd);
      if (m != null && (m == mr || overrides(m, mr))) return m;
    }
    List<M> ms = maxSpecific(c, nd, true);
    return ms.isEmpty() ? null : ms.get(0);
  }
  static M unbridge(M m) {
    if (m == null || m == EXTERNAL || (m.flags() & 0x0040) == 0) return m;
    M t = BRIDGE_TARGET.get(m.cls() + "." + m.name() + m.desc());
    return t == null ? m : unbridge(t);
  }
  static String spell(M m) {
    return ClassfileGroundTruth.cname(m.cls()) + "#" + m.name() + "("
      + String.join(",", ClassfileGroundTruth.sourceParams(m.cls(), m.name(), ClassfileGroundTruth.params(m.desc()))) + ")";
  }

  public static void main(String[] a) throws Exception {
    List<Path> roots = new ArrayList<>(); Path sites = null;
    for (int i = 0; i < a.length; i++) {
      switch (a[i]) {
        case "--app" -> { for (String s : a[++i].split(",")) roots.add(Path.of(s)); }
        case "--include-prefix" -> ClassfileGroundTruth.includePrefixes.addAll(Arrays.asList(a[++i].split(",")));
        case "--only-types" -> { for (String ln : Files.readAllLines(Path.of(a[++i]))) if (!ln.isBlank()) ClassfileGroundTruth.ONLY_TYPES.add(ln.trim()); }
        case "--sites" -> sites = Path.of(a[++i]);
        default -> throw new IllegalArgumentException(a[i]);
      }
    }
    List<ClassModel> models = ClassfileGroundTruth.load(roots);
    for (var cm : models) {
      String c = cm.thisClass().asInternalName();
      if (!ClassfileGroundTruth.APP.contains(c)) continue;
      CM.put(c, cm);
      cm.superclass().ifPresent(sc -> SUP.put(c, sc.asInternalName()));
      List<String> ifs = new ArrayList<>(); for (var i : cm.interfaces()) ifs.add(i.asInternalName()); IFS.put(c, ifs);
      Map<String, M> t = new HashMap<>();
      for (var mm : cm.methods()) t.put(mm.methodName().stringValue() + mm.methodType().stringValue(),
          new M(c, mm.methodName().stringValue(), mm.methodType().stringValue(), mm.flags().flagsMask()));
      METH.put(c, t);
    }
    for (String c : new ArrayList<>(CM.keySet())) { readPlatform(SUP.get(c)); for (String i : IFS.getOrDefault(c, List.of())) readPlatform(i); }
    for (var cm : models) {
      String c = cm.thisClass().asInternalName();
      if (!CM.containsKey(c)) continue;
      for (var mm : cm.methods()) {
        if ((mm.flags().flagsMask() & 0x0040) == 0 || mm.code().isEmpty()) continue;
        // a bridge's body is one invoke of the method it forwards to: in the same class (generic /
        // covariant) or in the superclass (a VISIBILITY bridge, #77 §1) — followed either way
        for (var e : mm.code().get()) if (e instanceof InvokeInstruction ii
            && ii.name().stringValue().equals(mm.methodName().stringValue())) {
          String nd = ii.name().stringValue() + ii.type().stringValue();
          M tgt = decl(ii.owner().asInternalName(), nd);
          if (tgt == null) tgt = resolve(ii.owner().asInternalName(), nd);
          if (tgt != null && !(tgt.cls().equals(c) && tgt.desc().equals(mm.methodType().stringValue())))
            BRIDGE_TARGET.put(c + "." + mm.methodName().stringValue() + mm.methodType().stringValue(), tgt);
        }
      }
    }
    // the oracle's emitted sites: (caller, line, op, receiver, callee) -> possible
    Map<String, List<Set<String>>> emitted = new HashMap<>();
    for (String ln : Files.readAllLines(sites)) {
      if (ln.isBlank()) continue;
      String caller = field(ln, "caller"), op = field(ln, "op"), recv = field(ln, "receiver_static_type"), callee = field(ln, "callee_name");
      String line = ln.replaceAll(".*\"line\":(\\d+).*", "$1");
      Set<String> poss = new TreeSet<>(arrField(ln, "possible"));
      // a site whose declared target is external is a BOUNDARY: the oracle moves the application
      // implementors it selected into `declaring_ancestors` (accepted, never unique). The JVMS
      // selection below still computes them, so compare against that union there.
      if (arrField(ln, "certain").isEmpty() && poss.isEmpty()) poss.addAll(arrField(ln, "declaring_ancestors"));
      emitted.computeIfAbsent(caller + "\t" + line + "\t" + op + "\t" + recv + "\t" + callee, k -> new ArrayList<>()).add(poss);
    }
    int checked = 0, disagreements = 0, unmatched = 0;
    List<String> all = new ArrayList<>();
    for (String c : CM.keySet()) if (!PLATFORM.contains(c)) all.add(c);
    for (var cm : models) {
      String cls = cm.thisClass().asInternalName();
      if (!CM.containsKey(cls) || !ClassfileGroundTruth.inScope(cls)) continue;
      for (var mm : cm.methods()) {
        String mname = mm.methodName().stringValue(); int f = mm.flags().flagsMask();
        boolean lam = mname.startsWith("lambda$");
        if (!lam && (f & 0x1040) != 0) continue;
        if (mm.code().isEmpty()) continue;
        String cn = mname, cp = String.join(",", ClassfileGroundTruth.sourceParams(cls, mname, ClassfileGroundTruth.params(mm.methodType().stringValue())));
        if (lam) { String[] o = ClassfileGroundTruth.lambdaOwner(cls, mname); if (o != null) { cn = o[0].equals("new") ? "<init>" : o[0]; cp = o[1]; } else continue; }
        String caller = ClassfileGroundTruth.cname(cls) + "#" + cn + "(" + cp + ")";
        int line = -1;
        for (var e : mm.code().get()) {
          if (e instanceof LineNumber ln) { line = ln.line(); continue; }
          String owner, name, desc, kind;
          if (e instanceof InvokeInstruction ii && (ii.opcode() == Opcode.INVOKEVIRTUAL || ii.opcode() == Opcode.INVOKEINTERFACE)) {
            owner = ii.owner().asInternalName(); name = ii.name().stringValue(); desc = ii.type().stringValue(); kind = ii.opcode().name();
          } else if (e instanceof InvokeDynamicInstruction idi) {
            String[] t = ClassfileGroundTruth.lambdaTargetRaw(idi);
            if (t == null || t[1].startsWith("lambda$")) continue;
            var mh = (MethodHandleEntry) idi.invokedynamic().bootstrap().arguments().get(1);
            int k = mh.kind(); if (k != 5 && k != 9) continue;
            owner = t[0]; name = t[1]; desc = t[2]; kind = "METHODREF";
          } else continue;
          M mr = CM.containsKey(owner) ? resolve(owner, name + desc) : null;
          // declared in the APPLICATION, not merely resolvable: a platform declaration
          // (`java.lang.Enum#ordinal` behind `c.ordinal()`) is a boundary, and the oracle
          // records it as such (#66, gate 1c false alarm without --include-prefix)
          boolean declaredInApp = mr != null && !PLATFORM.contains(mr.cls());
          if (mr == null) mr = new M(owner, name, desc, 0x0001 | 0x0400);
          TreeSet<String> jvm = new TreeSet<>();
          for (String c : all) {
            if (!(c.equals(owner) || ancestorsOf(c).contains(owner))) continue;
            if (isAbstract(c)) continue;
            M sel = select(c, mr);
            if (sel == null || sel == EXTERNAL) continue;
            M real = unbridge(sel);
            if (!ClassfileGroundTruth.inScope(real.cls())) continue;
            jvm.add(spell(real));
          }
          // the oracle's stated stance for a call no application class implements: the declaration
          if (jvm.isEmpty() && declaredInApp && ClassfileGroundTruth.inScope(mr.cls())) jvm.add(spell(mr));
          String key = caller + "\t" + line + "\t" + kind + "\t" + ClassfileGroundTruth.cname(owner) + "\t" + name;
          List<Set<String>> got = emitted.get(key);
          if (got == null || got.isEmpty()) { unmatched++; continue; }   // an excluded site, or one the oracle dropped: not this gate's question
          Set<String> orc = got.remove(0);
          checked++;
          if (!orc.equals(jvm)) {
            disagreements++;
            if (disagreements <= 25) {
              TreeSet<String> onlyO = new TreeSet<>(orc); onlyO.removeAll(jvm);
              TreeSet<String> onlyJ = new TreeSet<>(jvm); onlyJ.removeAll(orc);
              System.out.println(key.replace('\t', ' ') + "\n    oracle only: " + onlyO + "\n    JVMS only:   " + onlyJ);
            }
          }
        }
      }
    }
    System.err.println("# envelope check: " + checked + " sites compared, " + disagreements + " disagree, "
        + unmatched + " sites not in the emitted file (excluded)");
    System.exit(disagreements == 0 ? 0 : 1);
  }

  static String field(String json, String k) {
    String pat = "\"" + k + "\":\"";
    int i = json.indexOf(pat); if (i < 0) return "";
    int j = json.indexOf('"', i + pat.length());
    return json.substring(i + pat.length(), j);
  }
  static List<String> arrField(String json, String k) {
    String pat = "\"" + k + "\":[";
    int i = json.indexOf(pat); if (i < 0) return List.of();
    List<String> out = new ArrayList<>();
    int p = i + pat.length();
    while (p < json.length()) {                     // quoted strings up to the `]` OUTSIDE quotes
      char c = json.charAt(p);
      if (c == ']') break;
      if (c == '"') {
        int q2 = json.indexOf('"', p + 1); if (q2 < 0) break;
        out.add(json.substring(p + 1, q2)); p = q2 + 1;
      } else p++;
    }
    return out;
  }
}
