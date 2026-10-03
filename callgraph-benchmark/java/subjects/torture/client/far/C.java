package far;

/** (j) of F12Lowering, JVMS §5.4.5 (b): `C.m` overrides package-private `other.A.m` transitively
 *  through public `other.B.m`, from another package. */
public class C extends other.B { @Override public int m() { return 3; } }
