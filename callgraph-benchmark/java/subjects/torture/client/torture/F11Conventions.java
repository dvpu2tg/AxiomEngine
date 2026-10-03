package torture;

import java.util.AbstractList;
import java.util.List;
import java.util.function.Supplier;

/**
 * F11 — the conventions no bytecode reader can check, each with its JVMS-derived expectation
 * (issues #30 second pass, #47).
 *
 *  (a) a PRIVATE superclass method is never a declaring ancestor: `OuterSub#own()` calling
 *      `secret()` targets `OuterSub#secret()`, and `Outer#secret()` is NOT an accepted answer;
 *  (b) a call whose declared target is OUTSIDE the application — `list.size()` on a
 *      `java.util.List` — is a BOUNDARY site even though `Ints` implements `List` through
 *      `AbstractList`: no group, and `Ints#size()` is an accepted answer, never the unique one;
 *  (c) a class reached only through a bound METHOD reference (`r::get`) and never `new`-ed is
 *      not in the RTA set: `use(Src)` has `possible {NewSrc#get(), RefSrc#get()}` and
 *      `rta {NewSrc#get()}` — a CONSTRUCTOR reference (`RefSrc::new`) would instantiate it (#66);
 *  (d) a record's generated `equals` is a real member: `same(P, P)` calling `a.equals(b)`
 *      targets `P#equals(Object)` (kept, PROTOCOL §4).
 */
public final class F11Conventions {
    static class Outer {
        private int secret() { return 1; }
        int viaOuter() { return secret(); }
    }
    static class OuterSub extends Outer {
        int secret() { return 2; }              // a NEW method, not an override: Outer#secret is private
        int own() { return secret(); }          // (a) -> OuterSub#secret(), ancestor set must not hold Outer#secret
    }

    static class Ints extends AbstractList<Integer> {
        @Override public Integer get(int i) { return i; }
        @Override public int size() { return 3; }
    }
    static int total(List<Integer> list) { return list.size(); }     // (b) boundary: java.util.List#size

    interface Src { int get(); }
    static class NewSrc implements Src { public int get() { return 1; } }
    static class RefSrc implements Src { public int get() { return 2; } }
    static int use(Src s) { return s.get(); }                            // (c)
    static Supplier<Integer> mkRef(RefSrc r) { return r::get; }
    static Src mkNew() { return new NewSrc(); }

    record P(int x) {}
    static boolean same(P a, P b) { return a.equals(b); }                // (d) P#equals(Object)

    public static void main(String[] args) {
        new OuterSub().own();
        total(new Ints());
        use(mkNew());
        mkRef(null);
        same(new P(1), new P(1));
    }
}
