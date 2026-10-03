/**
 * @name Static call edges
 * @description Every call site and the callable CodeQL statically resolves it to.
 * @kind table
 * @id benchmark/java/static-call-edges
 *
 * CodeQL's answer unprompted: `Call.getCallee()`, the declared target, with no dispatch expansion.
 * The analogue of the benchmark's CERTAIN bound. `ViableCallEdges.ql` asks the same tool the other
 * question — what could this call reach — and the two are reported as separate rows, because
 * merging them would let the permissive configuration set recall and the conservative one set
 * precision.
 *
 * A METHOD REFERENCE (`Item::name`) is included. CodeQL models it as a synthetic callable whose
 * body calls the referenced method, so it already appears as a `Call`; the `unlambda` fold in
 * Names.qll attributes it to the method that lexically wrote it, which is where the oracle puts it
 * too. Omitting them would drop every one of the subject's method-reference edges.
 */
import java
import Names

/**
 * A call site, unified over the two syntactic forms that reach a callable: a `Call`, and a METHOD
 * REFERENCE, which CodeQL models as a `MemberRefExpr` rather than a `Call`. The oracle reads a
 * method reference out of the `LambdaMetafactory` bootstrap argument and records it as an edge, so
 * a query that only looked at `Call` would be scored as missing every one of them.
 */
predicate edge(Callable caller, Callable callee, string file, int line) {
  not isObInit(callee) and
  exists(Call call |
    caller = sourceCaller(call.getEnclosingCallable()) and
    callee = call.getCallee() and
    file = call.getLocation().getFile().getRelativePath() and
    line = call.getLocation().getStartLine()
  )
  or
  exists(MemberRefExpr r |
    caller = sourceCaller(r.getEnclosingCallable()) and
    callee = r.getReferencedCallable() and
    file = r.getLocation().getFile().getRelativePath() and
    line = r.getLocation().getStartLine()
  )
}

from Callable caller, Callable callee, string loc, int ln
where edge(caller, callee, loc, ln) and caller.fromSource()
select typeName(caller.getDeclaringType()) as callerType, callableName(caller) as callerName,
  paramsOf(caller) as callerParams, typeName(callee.getDeclaringType()) as calleeType,
  callableName(callee) as calleeName, paramsOf(callee) as calleeParams,
  loc as file, ln as line
