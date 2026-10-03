/**
 * @name Viable call edges (virtual dispatch)
 * @description Every call site and every callable CodeQL's dispatch library considers viable.
 * @kind table
 * @id benchmark/java/viable-call-edges
 *
 * The same tool asked the other question: not "what does this call declare" but "what could it
 * reach". Reported as its own row in the results table and never merged with the static one.
 */
import java
import Names
import semmle.code.java.dispatch.VirtualDispatch

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
    callee = viableCallable(call) and
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
