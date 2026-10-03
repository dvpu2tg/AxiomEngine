package other;

/** (j) of F12Lowering: package-private `A.m` overridden by public `B.m` in this package. */
public class A { int m() { return 1; } public static int call(A a) { return a.m(); } }
