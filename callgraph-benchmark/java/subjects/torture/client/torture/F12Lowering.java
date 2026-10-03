package torture;

import java.util.Iterator;
import java.util.function.Supplier;

/**
 * F12 — what javac's LOWERING does to written calls, and what the oracle must undo (issues #66,
 * #77, #78, #79). The unit test compiles this file at BOTH `--release 8` and the current release
 * and expects the same sites from both.
 *
 *  (a) Java 8: a nested class calling a private member of its outer goes through `access$N`;
 *      the written call is `Inner#peek() -> F12Lowering#secret()` at either release;
 *  (b) Java 8: `new Priv()` on a private constructor goes through a synthetic accessor
 *      `Priv(F12Lowering$1)`; the written call is `F12Lowering#mk() -> Priv#<init>()`;
 *  (c) a WRITTEN `new Base()` inside a subclass constructor is a call, not the implicit super();
 *  (d) `hasNext`/`next` on a user Iterator subtype are written calls; `for (x : bag)` over an
 *      Iterable whose `iterator()` has a covariant return is still the lowered triple;
 *  (e) a user overload `Color.valueOf(int)` on an enum is the source's own;
 *  (f) a static initializer block of a non-enum class is a caller (`<clinit>`);
 *  (g) a constructor reference `Sq::new` instantiates `Sq` for RTA;
 *  (h) an instance field initializer is ONE site, however many constructors the class has;
 *  (i) `Shw.pub()` resolves through a visibility bridge to `Hid#pub()`;
 *  (j) `C.m()` overrides package-private `A.m()` transitively through public `B.m()`;
 *  (k) a MULTI-LINE try-with-resources: javac's two `close()` calls land on the `try (` line and
 *      on the closing brace's line; neither is written, and `r.work()` inside the body is;
 *  (l) `new Base(1) { }` in a method: the anonymous class's own constructor chain to `Base` is
 *      javac's, not the source's — one site, under `viaAnon`, with `Base#<init>(int)` accepted.
 */
public final class F12Lowering {
    private int secret() { return 1; }
    class Inner { int peek() { return secret(); } }                     // (a)

    static final class Priv { private Priv() {} }
    static Priv mk() { return new Priv(); }                              // (b)

    static class Base { Base() {} Base(int n) { void_(n); } static void void_(int n) {} }
    static class Sub extends Base {
        Base other;
        Sub() { super(1); other = new Base(); }                          // (c) -> Base#<init>() is written
    }

    static final class MyIter implements Iterator<String> {
        public boolean hasNext() { return false; }
        public String next() { return ""; }
    }
    static String drain(MyIter m) { return m.hasNext() ? m.next() : ""; }   // (d) two written calls
    static final class Bag implements Iterable<String> {
        public MyIter iterator() { return new MyIter(); }
    }
    static int count(Bag bag) { int n = 0; for (String s : bag) n += s.length(); return n; }   // (d) lowered, excluded

    enum Color { RED; static Color valueOf(int i) { return RED; } }
    static Color pick() { return Color.valueOf(1); }                      // (e)

    static int seed;
    static { seed = helper("x"); }                                       // (f) F12Lowering#<clinit>() -> helper
    static int helper(String s) { return s.length(); }

    interface Shape { int area(); }
    static final class Sq implements Shape { public int area() { return 4; } }
    static final class Tri implements Shape { public int area() { return 3; } }
    static Supplier<Shape> mkSq() { return Sq::new; }                     // (g) Sq is instantiated
    static int area(Shape s) { return s.area(); }                         // rta {Sq#area}, Tri never new-ed

    static int compute() { return 1; }
    static final class Init {
        final int f = compute();                                         // (h) one site
        Init() {}
        Init(int x) {}
        Init(String s) { this(); }
    }

    abstract static class Hid { public void pub() {} }
    public static final class Shw extends Hid {}
    static void viaBridge(Shw s) { s.pub(); }                             // (i) -> Hid#pub()

    static int useA(other.A a) { return other.A.call(a); }                // (j) A.call: possible {A#m, B#m, C#m}
    static final class Res implements AutoCloseable { public void close() {} void work() {} }
    static void twr() {
        try (Res r = new Res()) {
            r.work();                                                   // (k) the one written call in the body
        }
    }
    static Base viaAnon() { return new Base(1) { }; }                      // (l)

    public static void main(String[] args) {
        twr(); viaAnon();
        new F12Lowering().new Inner().peek(); mk(); new Sub(); drain(new MyIter()); count(new Bag());
        pick(); mkSq(); area(new Sq()); new Init(); new Init(1); viaBridge(new Shw());
        useA(new far.C());
    }
}
