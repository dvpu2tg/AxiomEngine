/**
 * @name TypeScript call edges
 * @description Every call site and the function CodeQL resolves it to.
 * @kind table
 * @id benchmark/ts/call-edges
 *
 * CodeQL's JavaScript/TypeScript library resolves a call through `DataFlow::CallNode.getACallee()`,
 * which is a points-to style resolution rather than a type-checker query — a different mechanism
 * from the oracle's `getResolvedSignature`, which is what makes this a real comparison rather than
 * two readings of one answer.
 *
 * The container is spelled the way the benchmark spells it: `<module path>:<Declaration>` for a
 * method, and the bare module path for a top-level function, because in TypeScript a module IS its
 * path. `bench/language.py`'s alias table maps between that and anything reasonable a tool emits.
 */
import javascript

/** The module path of a file, relative to the database's source root. */
string moduleOf(File f) { result = f.getRelativePath() }

/** The class or INTERFACE a function is a member of. An interface member is not a ClassDefinition,
 *  and handling only classes put every interface method's container at the MODULE — which is a
 *  different container, so the edge missed and then read as a false positive. */
private TypeDefinition typeOf(Function fn) { fn = result.(ClassDefinition).getAMember().getInit() }

private ClassDefinition classOf(Function fn) { fn = result.getAMember().getInit() }

/** The nearest NAMED function a function is lexically inside — an arrow or function expression
 *  folds outward, matching the oracle's treatment of a closure body. */
private Function namedEnclosing(Function fn) {
  exists(fn.getName()) and result = fn
  or
  not exists(fn.getName()) and result = namedEnclosing(fn.getEnclosingContainer().(Function))
}

/** The container a function belongs to: its class, or — for a top-level function — its MODULE. */
string containerOf(Function fn) {
  result = moduleOf(fn.getFile()) + ":" + classOf(fn).getName()
  or
  not exists(classOf(fn)) and result = moduleOf(fn.getFile())
}

/** `constructor` for a constructor; the declared name otherwise; a line key for an anonymous fn. */
string nameOf(Function fn) {
  fn = classOf(fn).getConstructor().getInit() and result = "constructor"
  or
  not fn = classOf(fn).getConstructor().getInit() and
  (
    result = fn.getName()
    or
    not exists(fn.getName()) and result = "<anon@" + fn.getLocation().getStartLine() + ">"
  )
}

string paramsOf(Function fn) {
  result =
    concat(int i |
      i in [0 .. fn.getNumParameter() - 1]
    |
      fn.getParameter(i).getName(), "," order by i
    )
  or
  fn.getNumParameter() = 0 and result = ""
}

/** The caller's container and name for a call, whether it sits in a function or at module top level.
 *
 *  A call written at the top level of a module — `export const apSecond = apSecond_(Apply)`, which
 *  is how fp-ts builds every instance — has no enclosing Function, and the first version of this
 *  query required one: `call.getContainer().(Function)` matched nothing there, the row was never
 *  emitted, and 750 of fp-ts's uniquely-linked groups scored `missed` against a tool that had
 *  resolved them. The oracle names that caller `<module>`; so does this. */
predicate callerOf(DataFlow::InvokeNode call, string ctype, string cname, string cparams) {
  exists(Function fn |
    fn = namedEnclosing(call.getContainer().(Function)) and
    ctype = containerOf(fn) and cname = nameOf(fn) and cparams = paramsOf(fn)
  )
  or
  not exists(namedEnclosing(call.getContainer().(Function))) and
  ctype = moduleOf(call.getFile()) and cname = "<module>" and cparams = ""
}

/** CodeQL's OWN confidence term. `getACallee(int imprecision)` grades each resolution 0–3:
 *  0 = precise, 1 = through an imprecise but sound step, 2–3 = heuristic. The benchmark carries the
 *  BEST grade the tool gives each edge, verbatim, so the report can score each class on its own —
 *  the same treatment every other tool's label (`EXTRACTED`/`INFERRED`, `known_edge`/
 *  `multi_inferred`, `exact-match:0.9`, `import-resolved:0.85`) gets. */
int imprecisionOf(DataFlow::InvokeNode call, Function callee) {
  result = min(int i | callee = call.getACallee(i))
}

from DataFlow::InvokeNode call, Function callee, string callerType, string callerName, string callerParams
where
  // EVERY grade, not only the precise one: `getACallee()` is `getACallee(0)`, so the first version
  // of this query emitted only imprecision-0 edges and the label read 0 on all 3,061 kysely rows
  // (#41). The tool's graded answers are all carried, each with its grade, the same way GitNexus's
  // `reason:confidence` and codegraph's `resolvedBy:confidence` rows are all scored.
  callee = call.getACallee(_) and
  callerOf(call, callerType, callerName, callerParams) and
  exists(callee.getFile().getRelativePath())
select callerType, callerName, callerParams, containerOf(callee) as calleeType, nameOf(callee) as calleeName,
  paramsOf(callee) as calleeParams, moduleOf(call.getFile()) as file,
  call.getAstNode().getLocation().getStartLine() as line,
  "imprecision=" + imprecisionOf(call, callee) as confidence
