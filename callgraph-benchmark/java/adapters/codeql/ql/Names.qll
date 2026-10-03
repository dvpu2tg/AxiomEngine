/**
 * Spelling CodeQL's model of a Java program in the benchmark's canonical notation.
 *
 * NONE OF THIS REPAIRS AN ANSWER. Every predicate here reads something CodeQL already knows and
 * writes it down the way `docs/PROTOCOL.md` §3 spells it. The distinction matters: the benchmark
 * would be worthless if an adapter could reconstruct a resolution its tool did not perform, and
 * equally worthless if a tool scored zero because it says `Box<Node>` where the oracle says `Box`.
 *
 * Three differences, each read rather than rewritten:
 *
 *   * `getQualifiedName()` on a parameterised type carries its type ARGUMENTS (`Box<Node>`). The
 *     oracle reads types out of an erased descriptor, so the erasure is the comparable form — and
 *     `getErasure()` is CodeQL's own answer to "what is this type, erased".
 *
 *   * an ANONYMOUS class is `<anonymous class>` — one name for every anonymous class in the
 *     program, so 18 distinct types collapsed to one string and none of them matched anything.
 *     CodeQL knows the supertype and the enclosing type; the canonical key is built from those,
 *     which is exactly how the oracle keys them (javac and ecj number anonymous classes
 *     differently, so the counter is not a name).
 *
 *   * a call written inside a LAMBDA is attributed to the lambda's synthetic method. The oracle
 *     folds a lambda body into the method that lexically contains it, so the same fold is applied
 *     here. Without it every call inside a lambda is attributed to a caller that exists on neither
 *     side, and scores as missed for CodeQL while being a call it resolved correctly.
 */
import java

/**
 * The callable `c` is lexically written inside — `c` itself when it is not a synthetic body.
 *
 * Covers BOTH functional forms. CodeQL models a lambda AND a method reference as a synthetic
 * callable (`FunctionalExpr.asMethod()`), so unwrapping only `LambdaExpr` leaves every method
 * reference attributed to a caller that exists on neither side of the comparison — and the
 * subject's four method-reference forms then score as missed for a tool that resolved all of them.
 */
Callable unlambda(Callable c) {
  not exists(FunctionalExpr f | f.asMethod() = c) and result = c
  or
  exists(FunctionalExpr f | f.asMethod() = c | result = unlambda(f.getEnclosingCallable()))
}

/**
 * `<obinit>` is CodeQL's synthetic initialiser holding a class's field initialisers. javac compiles
 * those into the constructor, and the oracle therefore attributes a call written in a field
 * initialiser to `<init>`. Left alone, CodeQL's extra hop produces a caller that exists on neither
 * side (`F06Functional#<obinit>`) AND a `<init> -> <obinit>` edge that is a synthetic hop rather
 * than a written call — the first scores as a miss, the second as a false positive, for a tool that
 * resolved the initialiser correctly.
 */
predicate isObInit(Callable c) { c.getName() = "<obinit>" }

/** The callable the SOURCE would name: a lambda body's container, and `<obinit>` as `<init>`. */
Callable sourceCaller(Callable c) {
  exists(Callable u | u = unlambda(c) |
    if isObInit(u)
    then
      // onto every constructor that does NOT delegate with `this(...)`: javac inlines the field
      // initialisers only into those (a `this(...)`-delegating constructor's bytecode has none —
      // issue #32 §4)
      result.getDeclaringType() = u.getDeclaringType() and result instanceof Constructor and
      not exists(ThisConstructorInvocationStmt t | t.getEnclosingCallable() = result)
    else result = u
  )
}

/**
 * The supertype an anonymous class is keyed by: its superclass when that is not `Object`,
 * otherwise the interface it implements. Mirrors the oracle's `supertypeOf`.
 */
RefType anonKey(AnonymousClass a) {
  result = a.getASupertype() and
  not result instanceof TypeObject
  or
  a.getASupertype() instanceof TypeObject and
  not exists(RefType s | s = a.getASupertype() and not s instanceof TypeObject) and
  result = a.getASupertype()
}

/** The canonical spelling of a type. */
string typeName(RefType t) {
  exists(RefType e | e = t.getErasure() |
    // an ENUM-CONSTANT BODY is not a type of its own: the source declares a constant with a body.
    e instanceof AnonymousClass and
    anonKey(e.(AnonymousClass)) instanceof EnumType and
    result = typeName(anonKey(e.(AnonymousClass)))
    or
    e instanceof AnonymousClass and
    not anonKey(e.(AnonymousClass)) instanceof EnumType and
    result =
      typeName(e.(AnonymousClass).getEnclosingType()) + "$anon:" +
        anonKey(e.(AnonymousClass)).getSourceDeclaration().getName()
    or
    not e instanceof AnonymousClass and
    result = e.getQualifiedName()
  )
}

/** The erased, simple-named form of a type — the spelling a class-file descriptor carries. */
string erasedName(Type t) {
  t instanceof RefType and result = t.(RefType).getErasure().(RefType).getName()
  or
  not t instanceof RefType and result = t.getName()
}

/** `<init>` for a constructor, matching the class-file spelling the oracle uses. */
string callableName(Callable c) {
  c instanceof Constructor and result = "<init>"
  or
  not c instanceof Constructor and result = c.getName()
}

/**
 * A callable's erased parameter list.
 *
 * The synthetic leading enclosing-instance parameter javac adds to an inner class's constructor is
 * absent from CodeQL's model (it is a source-level view), which is the same list `docs/PROTOCOL.md`
 * §4.1 de-synthesises on the oracle's side. The two therefore agree without either being adjusted
 * toward the other.
 */
string paramsOf(Callable c) {
  result =
    concat(int i |
      i in [0 .. c.getNumberOfParameters() - 1]
    |
      erasedName(c.getParameterType(i)), "," order by i
    )
  or
  c.getNumberOfParameters() = 0 and result = ""
}
