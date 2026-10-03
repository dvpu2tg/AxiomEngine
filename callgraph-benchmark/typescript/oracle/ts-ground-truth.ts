// ─────────────────────────────────────────────────────────────────────────────────────────────
// GROUND TRUTH FOR THE TYPESCRIPT CALL-GRAPH BENCHMARK
//
// TypeScript has no bytecode, so there is no artefact to read the way the Java oracle reads class
// files. The nearest equivalent — and the only thing in the ecosystem with the authority of a
// reference implementation — is the compiler's own TYPE CHECKER. `checker.getResolvedSignature()`
// is the function `tsc` itself uses to decide which declaration a call reaches; it is the same
// answer the language service gives "go to definition", and it is what a type error is reported
// against.
//
// THE CONFLICT OF INTEREST, STATED UP FRONT
// -----------------------------------------
// One tool under test — axiomengine — parses TypeScript with the `typescript` package. That
// sounds fatal and is not, but the distinction has to be checked rather than assumed:
//
//   * it uses the compiler's PARSER (`ts.createSourceFile`, the AST) to read syntax;
//   * it does NOT call `getTypeChecker()` anywhere in its extraction path — verified by grep over
//     the parser's `src/`: the only occurrences are in comments and in its own test suite, where
//     the checker is used as an adjudicator to validate the parser's output.
//
// So the checker is not in that tool's production resolution path, and this oracle is independent
// of it in the way that matters. What remains is an INDIRECT alignment: that tool's authors
// developed against `getResolvedSignature` as a correctness gate, so its answers are more likely to
// agree with this oracle than a tool developed against nothing in particular. That is not
// neutralisable and it is not hidden — docs/CROSS-LANGUAGE.md states it beside the TypeScript
// table, and it is the reason the TypeScript result is reported as a diagnostic rather than as a
// ranking.
//
// THE BOUNDS, AND WHY `possible` MEANS SOMETHING DIFFERENT HERE THAN IN JAVA
// -------------------------------------------------------------------------
//   certain      — the declaration `getResolvedSignature` names. For a call the checker can resolve
//                  this is exactly one declaration, and a tool that misses it has missed a fact the
//                  compiler asserts.
//   possible     — what can RUN: every own container that declares a member of the same name and
//                  whose type the CHECKER says is assignable to the receiver's (declared heritage
//                  is a subset of that — `implements`/`extends` makes a type assignable). An
//                  interface member or abstract method is the declared target and is NOT in
//                  `possible` when an implementor exists; the site is then uniquely linked to the
//                  implementor. A property bound to a named function stands for that function.
//
//                  This is the STRUCTURAL envelope, restricted to same-named members: TypeScript
//                  is structurally typed and a class satisfies an interface without naming it. It
//                  admits a type whose member happens to be compatible although nothing in the
//                  program ever passes it — an over-approximation on that side — and it cannot see
//                  a call through a function-typed property (`indirect`, never scored) — an
//                  omission on the other. Issue #27 corrected the earlier description of this set
//                  as "declared heritage"; docs/CROSS-LANGUAGE.md states the consequence.
//   possible_rta — the same expansion restricted to classes the program actually instantiates with
//                  `new`. Same caveat.
//
// The one metric that means the same thing in both languages is the UNIQUELY-LINKED exact rate:
// when exactly one target is possible, did the tool name it? That is the cross-language headline.
//
// EXCLUDED — a call the checker resolves into a declaration the subject does not own: anything in
// `node_modules`, in a `.d.ts` ambient declaration, or in the TypeScript standard library. Those are
// boundary calls, recorded and never scored, exactly as a client -> library hand-off is in Java.
//
//   npx tsx ts-ground-truth.ts --project <tsconfig.json> --root <srcRoot>
//                              --mode sites|containers|methods|raw|collisions|excluded
// ─────────────────────────────────────────────────────────────────────────────────────────────
import * as ts from 'typescript';
import * as path from 'path';
import * as fs from 'fs';

type Mode = 'sites' | 'containers' | 'methods' | 'raw' | 'collisions' | 'excluded' | 'crosscheck'
          | 'files' | 'program' | 'coverage' | 'defaults' | 'heritage';

interface Args {
  project: string;
  root: string;
  mode: Mode;
}

function parseArgs(argv: string[]): Args {
  const a: Partial<Args> = { mode: 'sites' };
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case '--project': a.project = argv[++i]; break;
      case '--root': a.root = argv[++i]; break;
      case '--mode': a.mode = argv[++i] as Mode; break;
      default: throw new Error(`unknown arg ${argv[i]}`);
    }
  }
  if (!a.project) throw new Error('need --project <tsconfig.json>');
  a.root = path.resolve(a.root ?? path.dirname(a.project));
  return a as Args;
}

// ── the program ──────────────────────────────────────────────────────────────────────────────
function createProgram(tsconfigArg: string): ts.Program {
  const tsconfig = path.resolve(tsconfigArg);   // a relative config path makes `include` resolve wrongly
  const cfgFile = ts.readConfigFile(tsconfig, ts.sys.readFile);
  if (cfgFile.error) {
    throw new Error(ts.flattenDiagnosticMessageText(cfgFile.error.messageText, '\n'));
  }
  const parsed = ts.parseJsonConfigFileContent(
    cfgFile.config, ts.sys, path.dirname(tsconfig));
  // A config error is FATAL. `got`'s tsconfig extends `@sindresorhus/tsconfig`, which is not
  // installed; the parse "succeeded" with `module` undefined and the checker measured a different
  // program from the one the project defines, silently (issue #28 §3).
  const fatal = parsed.errors.filter((e) => e.category === ts.DiagnosticCategory.Error
    // "No inputs were found" is reported by tsc as an error too; an empty program fails gate 0 anyway
    && e.code !== 18003);
  if (fatal.length) {
    throw new Error('tsconfig error(s): ' + fatal.map((e) => ts.flattenDiagnosticMessageText(e.messageText, '\n')).join('; '));
  }
  return ts.createProgram({ rootNames: parsed.fileNames, options: parsed.options });
}

// ── naming ───────────────────────────────────────────────────────────────────────────────────
// The canonical container is `<module path relative to root>:<Declaration>`, and a module-level
// function's container is the bare module path. A module IS its path in TypeScript, so this is the
// same information a Java package name carries, written the way the language writes it.
class Namer {
  constructor(private readonly root: string, private readonly checker?: ts.TypeChecker) {}

  /**
   * The named type an object literal or class expression is being used AS.
   *
   * This is the TypeScript analogue of the Java oracle keying an anonymous class by its SUPERTYPE.
   * A Java anonymous class writes `new Runnable(){…}` and the supertype is in the syntax; a
   * TypeScript object literal writes `{ handle(m) {…} }` and the type it satisfies is in the
   * CONTEXT — the parameter it is passed to, the variable it is assigned to, the return type of the
   * function it is returned from. The checker knows it, so it is asked.
   *
   * Recovering it turns an opaque `<anon:obj@13>` into `$obj:Handler@13`: a key a tool naming the
   * interface can actually be matched against, and a key a READER can interpret. The line is kept
   * because two literals in one file can satisfy one interface, and the ground truth must still
   * tell them apart.
   */
  contextualName(node: ts.Node): string | undefined {
    if (!this.checker) return undefined;
    try {
      let t = ts.isObjectLiteralExpression(node)
        ? this.checker.getContextualType(node as ts.ObjectLiteralExpression)
        : undefined;
      if (!t) t = this.checker.getTypeAtLocation(node);
      if (!t) return undefined;
      // a union contextual type (`Handler | undefined`) names nothing on its own; take the first
      // constituent that has a symbol, which is the interface the literal is satisfying
      const parts = (t as any).types as ts.Type[] | undefined;
      for (const cand of parts && parts.length ? parts : [t]) {
        const sym = cand.aliasSymbol ?? cand.getSymbol();
        const n = sym?.getName();
        if (n && n !== "__type" && n !== "__object" && !n.startsWith("__")) return n;
      }
    } catch { /* the checker declined; fall through to the line key */ }
    return undefined;
  }

  moduleOf(sf: ts.SourceFile): string {
    return path.relative(this.root, sf.fileName).split(path.sep).join('/');
  }

  /** Is this declaration part of the subject, rather than a dependency or the standard library? */
  isOwn(sf: ts.SourceFile | undefined): boolean {
    if (!sf) return false;
    if (sf.isDeclarationFile) return false;
    // `resolveJsonModule` puts .json files in the program. They are data — no call sites, no
    // declarations a tool could name — and counting one as a source file made gate 4 report a file
    // the tools "failed" to index.
    if (!/\.(ts|tsx|mts|cts)$/.test(sf.fileName)) return false;
    const rel = path.relative(this.root, sf.fileName);
    return !rel.startsWith('..') && !path.isAbsolute(rel) && !rel.includes('node_modules');
  }

  /**
   * The container a declaration belongs to.
   *
   * A method belongs to its class or interface; a module-level function belongs to its module. An
   * ANONYMOUS container — a class expression, an object literal with methods — is keyed by its
   * declaration LINE, for the same reason the Java oracle keys an anonymous class that way: any
   * counter would be an artefact of one implementation rather than a property of the source.
   */
  containerOf(decl: ts.Node): string | undefined {
    const sf = decl.getSourceFile();
    if (!this.isOwn(sf)) return undefined;
    const mod = this.moduleOf(sf);

    const parts: string[] = [];
    let node: ts.Node | undefined = decl.parent;
    while (node && !ts.isSourceFile(node)) {
      if (ts.isClassDeclaration(node) || ts.isInterfaceDeclaration(node)
          || ts.isEnumDeclaration(node) || ts.isModuleDeclaration(node)
          || ts.isTypeAliasDeclaration(node)) {
        const n = (node as any).name;
        parts.unshift(n ? n.getText() : this.anonKey(node));
      } else if (ts.isClassExpression(node) || ts.isObjectLiteralExpression(node)) {
        parts.unshift(this.anonKey(node));
      }
      node = node.parent;
    }
    return parts.length ? `${mod}:${parts.join('.')}` : mod;
  }

  /**
   * A class expression or object literal is keyed by THE NAME THE SOURCE BINDS IT TO, and only
   * falls back to a line when there is none.
   *
   * kysely's whole operation-node layer is written as
   *     export const AndNode = freeze({ is(...) {...}, create(...) {...} })
   * so the literal is genuinely named `AndNode` — every tool says `AndNode.create`, because that is
   * what the file says. Keying it `<anon:obj@13>` made 18% of the subject's uniquely-linked groups
   * unmatchable BY CONSTRUCTION, and drove every tool's score down together, which is the signature
   * of a harness fault rather than a tool one.
   *
   * The binding is found by walking out through the wrappers a literal is commonly passed through —
   * `freeze(...)`, a cast, a parenthesis — because the name is on the outside of those.
   */
  private anonKey(node: ts.Node): string {
    const sf = node.getSourceFile();
    let n: ts.Node = node;
    for (let i = 0; i < 6 && n.parent; i++) {
      const p: ts.Node = n.parent;
      if (ts.isCallExpression(p) || ts.isParenthesizedExpression(p) || ts.isAsExpression(p)
          || ts.isSatisfiesExpression(p) || ts.isTypeAssertionExpression(p)
          || ts.isNonNullExpression(p)) {
        n = p;
        continue;
      }
      if ((ts.isVariableDeclaration(p) || ts.isPropertyAssignment(p)
           || ts.isPropertyDeclaration(p)) && p.name && ts.isIdentifier(p.name)) {
        return p.name.text;
      }
      break;
    }
    const { line } = sf.getLineAndCharacterOfPosition(node.getStart(sf));
    const kind = ts.isObjectLiteralExpression(node) ? 'obj' : 'class';
    // No binding names it — so name it by the TYPE it is being used as, the way the Java oracle
    // names an anonymous class by its supertype.
    const ctx = this.contextualName(node);
    return ctx ? `$${kind}:${ctx}@${line + 1}` : `<anon:${kind}@${line + 1}>`;
  }
}

/** `constructor` for a constructor; the declared name otherwise; a stable key for an anonymous fn. */
function declName(decl: ts.Declaration, namer: Namer): string {
  if (ts.isConstructorDeclaration(decl)) return 'constructor';
  const name = (decl as any).name as ts.Node | undefined;
  if (name && (ts.isIdentifier(name as any) || ts.isStringLiteral(name as any)
               || ts.isPrivateIdentifier(name as any))) {
    return (name as any).text;
  }
  if (name) return name.getText();
  // an anonymous function expression or arrow assigned to something: the variable names it
  const p = bindingParent(decl);
  if (p && ts.isVariableDeclaration(p) && ts.isIdentifier(p.name)) return p.name.text;
  if (p && ts.isPropertyAssignment(p) && ts.isIdentifier(p.name)) return p.name.text;
  // A CLASS FIELD holding an arrow — `private onPointerDown = (e) => {…}`, the idiom every React
  // class component is written in; excalidraw's `App` has ~400 of them — is named by the field.
  // `enclosingFunction` already treated a PropertyDeclaration as a named binding, so leaving it
  // out HERE keyed those callers `App#<anon@7756>` while every tool (correctly) said
  // `App#onPointerDown`: 103 sites on one line-key, unmatchable by construction.
  if (p && ts.isPropertyDeclaration(p) && (ts.isIdentifier(p.name) || ts.isPrivateIdentifier(p.name))) {
    return p.name.text;
  }
  const sf = decl.getSourceFile();
  const { line } = sf.getLineAndCharacterOfPosition(decl.getStart(sf));
  return `<anon@${line + 1}>`;
}

/**
 * The parameter list as the CHECKER sees it.
 *
 * Java erases generics because its descriptors do; TypeScript does not, because the checker resolves
 * a call against the instantiated signature and that is the answer being scored. An optional
 * parameter keeps its `?`, because a tool that distinguishes `f(a)` from `f(a, b?)` is distinguishing
 * something real.
 */
function paramsOf(sig: ts.Signature, checker: ts.TypeChecker): string[] {
  return sig.parameters.map((p) => {
    const d = p.valueDeclaration ?? p.declarations?.[0];
    if (d && ts.isParameter(d) && d.type) return d.type.getText().replace(/\s+/g, '');
    const t = checker.getTypeOfSymbolAtLocation(p, d ?? sig.declaration!);
    return checker.typeToString(t).replace(/\s+/g, '');
  });
}

function ref(container: string, name: string, params: string[]): string {
  return `${container}#${name}(${params.join(',')})`;
}

// ── the heritage index: which own classes declare they implement/extend a given container ────
interface Index {
  /** container -> the member names it declares */
  members: Map<string, Set<string>>;
  /** container -> containers it declares it extends or implements */
  parents: Map<string, Set<string>>;
  /** container -> own containers that declare it as a parent (transitively) */
  subs: Map<string, Set<string>>;
  /** containers the program instantiates with `new` */
  instantiated: Set<string>;
  /** container -> the declaration node, so its TYPE can be asked for assignability */
  decl: Map<string, ts.Declaration>;
  /** member name -> every own container declaring a member of that name */
  byMember: Map<string, Set<string>>;
  /** `container#member` -> the ref of the FUNCTION a property is bound to by name
   *  (`{ handle: helperHandle }`): the method that runs is that function, not a member of the
   *  literal (issue #27 §3) */
  boundFn: Map<string, string>;
  /** `container#member` -> that member's own declaration node, so an envelope candidate is spelled
   *  with ITS parameters at Tier A, not the call's (#68, comment) */
  memberDecl: Map<string, ts.Declaration>;
  /** every own container seen */
  containers: Set<string>;
  /** container -> the declaration line, for collision reporting */
  declLine: Map<string, string>;
}

function buildIndex(program: ts.Program, checker: ts.TypeChecker, namer: Namer): Index {
  const idx: Index = {
    members: new Map(), parents: new Map(), subs: new Map(),
    instantiated: new Set(), containers: new Set(), declLine: new Map(),
    decl: new Map(), byMember: new Map(), boundFn: new Map(), memberDecl: new Map(),
  };

  const addMember = (c: string, m: string) => {
    if (!idx.members.has(c)) idx.members.set(c, new Set());
    idx.members.get(c)!.add(m);
    if (!idx.byMember.has(m)) idx.byMember.set(m, new Set());
    idx.byMember.get(m)!.add(c);
  };
  const addParent = (c: string, p: string) => {
    if (!idx.parents.has(c)) idx.parents.set(c, new Set());
    idx.parents.get(c)!.add(p);
  };

  const containerOfDecl = (d: ts.Declaration): string | undefined => {
    const sf = d.getSourceFile();
    if (!namer.isOwn(sf)) return undefined;
    const name = (d as any).name;
    const outer = namer.containerOf(d);
    if (outer === undefined) return undefined;
    const own = name ? name.getText() : undefined;
    if (!own) return undefined;
    return outer.includes(':') ? `${outer}.${own}` : `${outer}:${own}`;
  };

  for (const sf of program.getSourceFiles()) {
    if (!namer.isOwn(sf)) continue;

    const visit = (node: ts.Node): void => {
      if (ts.isClassDeclaration(node) || ts.isInterfaceDeclaration(node)) {
        const c = containerOfDecl(node);
        if (c) {
          idx.containers.add(c);
          idx.decl.set(c, node);
          const { line } = sf.getLineAndCharacterOfPosition(node.getStart(sf));
          idx.declLine.set(c, `${namer.moduleOf(sf)}:${line + 1}`);
          for (const m of node.members) {
            const n = (m as any).name;
            if (n) { addMember(c, n.getText()); if (!idx.memberDecl.has(`${c}#${n.getText()}`)) idx.memberDecl.set(`${c}#${n.getText()}`, m as ts.Declaration); }
            else if (ts.isConstructorDeclaration(m)) { addMember(c, 'constructor'); if (m.body) idx.memberDecl.set(`${c}#constructor`, m); }
          }
          for (const clause of node.heritageClauses ?? []) {
            for (const t of clause.types) {
              let sym = checker.getSymbolAtLocation(t.expression);
              // an IMPORTED parent resolves to the import specifier's alias, whose declaration is
              // the import, not the interface — every `implements X` across modules gave no parent
              // edge, and a GENERIC parent (`Named<T>`) is not rescued by assignability (#27, reopened)
              if (sym && (sym.flags & ts.SymbolFlags.Alias)) sym = checker.getAliasedSymbol(sym);
              const target = sym?.declarations?.[0];
              if (!target) continue;
              const pc = containerOfDecl(target as ts.Declaration);
              if (pc) addParent(c, pc);
            }
          }
        }
      }
      // AN OBJECT LITERAL WITH METHODS IS A CONTAINER, and in TypeScript it is a first-class one:
      // `dispatch({ handle: (m) => … })` satisfies `Handler` without naming it, and kysely's whole
      // node layer is `freeze({ create() {…} })`. Indexing only classes and interfaces left these
      // invisible to the structural expansion — so the envelope for a call on an interface omitted
      // the literals that actually receive it, and a tool that resolved one was scored `polluted`
      // for being right. An object literal is also always INSTANTIATED, by construction.
      if (ts.isObjectLiteralExpression(node)) {
        for (const m of node.properties) {
          const mn = (m as any).name;
          if (!mn) continue;
          const isFn = ts.isMethodDeclaration(m)
            || (ts.isPropertyAssignment(m)
                && (ts.isArrowFunction(m.initializer) || ts.isFunctionExpression(m.initializer)));
          // `{ handle: helperHandle }` (or shorthand `{ handle }`): the property holds a NAMED
          // function, and that function is what runs when the property is called
          let bound: string | undefined;
          if (!isFn && (ts.isPropertyAssignment(m) || ts.isShorthandPropertyAssignment(m))) {
            const init = ts.isPropertyAssignment(m) ? m.initializer : m.name;
            if (ts.isIdentifier(init) || ts.isPropertyAccessExpression(init)) {
              let sym = ts.isShorthandPropertyAssignment(m)
                ? checker.getShorthandAssignmentValueSymbol(m) : checker.getSymbolAtLocation(init);
              if (sym && (sym.flags & ts.SymbolFlags.Alias)) sym = checker.getAliasedSymbol(sym);
              const fd = sym?.declarations?.find((d) => ts.isFunctionDeclaration(d)
                || (ts.isVariableDeclaration(d) && !!d.initializer
                    && (ts.isArrowFunction(d.initializer) || ts.isFunctionExpression(d.initializer))));
              if (fd && namer.isOwn(fd.getSourceFile())) {
                const fc = namer.containerOf(fd);
                const fn = ts.isVariableDeclaration(fd) ? (fd.initializer as ts.SignatureDeclaration) : fd as ts.SignatureDeclaration;
                const fsig = checker.getSignatureFromDeclaration(fn);
                if (fc !== undefined) bound = ref(fc, declName(fd as ts.Declaration, namer), fsig ? paramsOf(fsig, checker) : []);
              }
            }
          }
          if (!isFn && !bound) continue;
          const c = namer.containerOf(m);
          if (c === undefined) continue;
          idx.containers.add(c);
          idx.decl.set(c, node as unknown as ts.Declaration);
          idx.instantiated.add(c);
          const { line } = sf.getLineAndCharacterOfPosition(node.getStart(sf));
          idx.declLine.set(c, `${namer.moduleOf(sf)}:${line + 1}`);
          addMember(c, mn.getText());
          idx.memberDecl.set(`${c}#${mn.getText()}`, m as ts.Declaration);
          if (bound) idx.boundFn.set(`${c}#${mn.getText()}`, bound);
        }
      }
      if (ts.isNewExpression(node)) {
        const sym = checker.getSymbolAtLocation(node.expression);
        const d = sym?.declarations?.[0];
        if (d) {
          const c = containerOfDecl(d as ts.Declaration);
          if (c) idx.instantiated.add(c);
        }
      }
      ts.forEachChild(node, visit);
    };
    ts.forEachChild(sf, visit);
  }

  // transitive: a container's subs are everything that reaches it through declared heritage
  for (const c of idx.containers) {
    const seen = new Set<string>();
    const stack = [...(idx.parents.get(c) ?? [])];
    while (stack.length) {
      const p = stack.pop()!;
      if (seen.has(p)) continue;
      seen.add(p);
      if (!idx.subs.has(p)) idx.subs.set(p, new Set());
      idx.subs.get(p)!.add(c);
      for (const g of idx.parents.get(p) ?? []) stack.push(g);
    }
  }
  return idx;
}

// ── the sites ────────────────────────────────────────────────────────────────────────────────
interface Site {
  site_id: string;
  caller: string;
  line: number;
  seq: number;
  op: string;
  receiver_static_type: string;
  callee_name: string;
  callee_params: string[];
  kind: 'internal' | 'boundary' | 'indirect';
  certain: string[];
  possible: string[];
  possible_rta: string[];
  declaring_ancestors: string[];
  unique: boolean;
  unique_rta: boolean;
}

/**
 * The declaration an arrow/function expression is bound to, looking THROUGH the wrappers a function
 * is idiomatically passed through on its way to a name: `handleMove = withBatchedUpdates((e) => …)`,
 * `const Comp = memo(() => …)`, `const f = ((x) => …) as Handler`. The name is on the outside of
 * the wrapper and it is the name every tool and every reader uses; without this walk the arrow was
 * unnamed, folded outward past the field, and 247 of excalidraw's App call sites were attributed to
 * `<module>`. Same wrapper list as `Namer.anonKey`, which does this for object literals.
 */
let CHECKER: ts.TypeChecker | undefined;   // set in main; bindingParent asks it one question

function bindingParent(fn: ts.Node): ts.Node | undefined {
  let n: ts.Node = fn;
  let crossedCall = false;
  for (let i = 0; i < 6 && n.parent; i++) {
    const p: ts.Node = n.parent;
    if (ts.isCallExpression(p) || ts.isParenthesizedExpression(p) || ts.isAsExpression(p)
        || ts.isSatisfiesExpression(p) || ts.isTypeAssertionExpression(p)
        || ts.isNonNullExpression(p)) {
      if (ts.isCallExpression(p)) crossedCall = true;
      n = p;
      continue;
    }
    // A binding reached THROUGH a call is the arrow's name only when the binding is itself a
    // function — `const handler = memo(() => …)`. `const index = binaryFindPartition(arr, v => …)`
    // binds a number: the arrow is an argument, not the value, and PROTOCOL §3.1 row 5 folds it
    // into the enclosing named function. 114 typedoc call sites were attributed to
    // `utils/array.ts#index(v)` — a name no tool can produce (#53).
    if (crossedCall && CHECKER
        && (ts.isVariableDeclaration(p) || ts.isPropertyAssignment(p) || ts.isPropertyDeclaration(p))) {
      try {
        const t = CHECKER.getTypeAtLocation((p as any).name ?? p);
        const callable = t.getCallSignatures().length > 0 || t.getConstructSignatures().length > 0;
        if (!callable) return undefined;
      } catch { return undefined; }
    }
    return p;
  }
  return undefined;
}

/** The function a node is lexically written inside, folding closures into their container. */
function enclosingFunction(node: ts.Node): ts.Node | undefined {
  let n: ts.Node | undefined = node.parent;
  while (n) {
    if (ts.isFunctionDeclaration(n) || ts.isMethodDeclaration(n) || ts.isConstructorDeclaration(n)
        || ts.isGetAccessorDeclaration(n) || ts.isSetAccessorDeclaration(n)
        || ts.isFunctionExpression(n) || ts.isArrowFunction(n)) {
      // An arrow or function expression assigned to a variable is a named function for our
      // purposes; one nested inside another function is a CLOSURE and folds outward, matching the
      // Java oracle's treatment of a lambda body.
      const p = bindingParent(n);
      const named = p && (ts.isVariableDeclaration(p) || ts.isPropertyAssignment(p)
                          || ts.isPropertyDeclaration(p));
      if (!ts.isArrowFunction(n) && !ts.isFunctionExpression(n)) return n;
      if (named) return n;
      n = n.parent;
      continue;
    }
    // A CLASS FIELD INITIALIZER or a `static { }` block runs inside the class, not the module:
    // `deserializer = new Deserializer(this)` executes in the constructor, a static initializer
    // when the class is defined — the Java convention (`<init>` / `<clinit>`), and what CodeQL
    // says. Attributing it to the module credited the tool that said `<module>` and charged the
    // one that named the constructor (#74). The node returned is the field or block itself; the
    // caller spelling is decided in callerOf.
    if (ts.isPropertyDeclaration(n) && n.initializer && node.pos >= n.initializer.pos) return n;
    if (ts.isClassStaticBlockDeclaration(n)) return n;
    if (ts.isSourceFile(n)) return undefined;
    n = n.parent;
  }
  return undefined;
}

function main(): void {
  const args = parseArgs(process.argv.slice(2));
  const program = createProgram(args.project);
  const checker = program.getTypeChecker();
  CHECKER = checker;
  const namer = new Namer(args.root, checker);
  const idx = buildIndex(program, checker, namer);

  const own = program.getSourceFiles().filter((sf) => namer.isOwn(sf));
  process.stderr.write(`# source files: ${own.length}\n`);
  process.stderr.write(`# containers: ${idx.containers.size}\n`);

  if (args.mode === 'coverage') {
    // HOW MUCH OF THE SUBJECT THE CHECKER CAN ACTUALLY READ.
    //
    // The Java harness prints, before any score, how much of the library a client calls is present
    // in the staged IR — because every percentage under it is conditional on that, and a
    // low-coverage run is measuring the staging rather than the rules. This is the same figure for
    // TypeScript: of every call expression in the subject's own files, how many did
    // `getResolvedSignature` resolve at all?
    //
    // Dependencies are NOT installed (see subjects/fetch.py), so a call into one is unresolved and
    // that is fine — it is a boundary call either way. What this catches is a subject whose OWN
    // code the checker cannot read: a tsconfig that excludes half the tree, a solution-style config
    // with no roots, a project that does not typecheck. Scoring one of those would produce a table
    // that looks entirely normal and means nothing.
    let total = 0, resolved = 0, ownTarget = 0;
    for (const sf of own) {
      const visit = (node: ts.Node): void => {
        // the same call-like set the site walk uses — tagged templates included (#67 §7)
        if (ts.isCallExpression(node) || ts.isNewExpression(node) || ts.isTaggedTemplateExpression(node)) {
          total++;
          const sig = checker.getResolvedSignature(node as ts.CallLikeExpression);
          if (sig?.declaration) {
            resolved++;
            if (namer.isOwn(sig.declaration.getSourceFile())) ownTarget++;
          } else if (sig && (ts.isNewExpression(node) || (ts.isCallExpression(node)
                     && node.expression.kind === ts.SyntaxKind.SuperKeyword))) {
            // `new C()` / `super()` on a class with NO declared constructor: the checker returns a
            // construct signature with no declaration, but the call is fully resolved — the class
            // is known (the oracle records these as NOCTOR). Counted as resolved; it was counted as
            // unresolved and moved gate 0 on a 1–2 point margin (issue #28 §2).
            const ct = checker.getTypeAtLocation(ts.isNewExpression(node) ? node.expression : node.expression);
            const cs = ct.getSymbol();
            if (cs && cs.declarations?.some((d) => ts.isClassDeclaration(d) || ts.isClassExpression(d))) {
              resolved++;
              if (cs.declarations.some((d) => namer.isOwn(d.getSourceFile()))) ownTarget++;
            }
          }
        }
        ts.forEachChild(node, visit);
      };
      ts.forEachChild(sf, visit);
    }
    const pct = total ? (100 * resolved / total) : 0;
    process.stdout.write(`call_expressions\t${total}\n`);
    process.stdout.write(`resolved\t${resolved}\n`);
    process.stdout.write(`resolved_pct\t${pct.toFixed(1)}\n`);
    process.stdout.write(`target_in_subject\t${ownTarget}\n`);
    process.stderr.write(`# checker resolved ${resolved}/${total} call expressions `
                         + `(${pct.toFixed(1)}%), ${ownTarget} into the subject's own code\n`);
    return;
  }

  if (args.mode === 'defaults') {
    // `<module>\t<canonical container>` for every module whose DEFAULT EXPORT is a class or
    // function. An ES module has at most one default export, so a tool that names a default-
    // exported class `default` — `Command#default` for `export default class Command` — has named
    // it unambiguously by language definition, and the resolver can read that rather than report
    // 40% of its rows as unmapped. ioredis is written this way throughout.
    let n = 0;
    for (const sf of own) {
      for (const st of sf.statements) {
        const mods = ts.canHaveModifiers(st) ? ts.getModifiers(st) ?? [] : [];
        const isDefault = mods.some((m) => m.kind === ts.SyntaxKind.DefaultKeyword)
          && mods.some((m) => m.kind === ts.SyntaxKind.ExportKeyword);
        let target: string | undefined;
        if (isDefault && (ts.isClassDeclaration(st) || ts.isFunctionDeclaration(st))) {
          target = st.name ? namer.containerOf(st.members?.[0] ?? st) : undefined;
          if (ts.isClassDeclaration(st) && st.name) target = `${namer.moduleOf(sf)}:${st.name.text}`;
          if (ts.isFunctionDeclaration(st)) target = namer.moduleOf(sf);
        } else if (ts.isExportAssignment(st) && !st.isExportEquals && ts.isIdentifier(st.expression)) {
          // `export default Foo;`
          const sym = checker.getSymbolAtLocation(st.expression);
          const d = sym?.declarations?.[0];
          if (d && (ts.isClassDeclaration(d) || ts.isInterfaceDeclaration(d)) && d.name
              && namer.isOwn(d.getSourceFile())) {
            target = `${namer.moduleOf(d.getSourceFile())}:${d.name.text}`;
          }
        }
        if (target) { process.stdout.write(`${namer.moduleOf(sf)}\t${target}\n`); n++; }
      }
    }
    process.stderr.write(`# modules with a default-exported container: ${n}\n`);
    return;
  }

  if (args.mode === 'files') {
    // Every file the CHECKER loaded and considers part of the subject. Gate 4 compares this with
    // the files a tool would walk: a file in one list and not the other breaks the comparison, and
    // the direction that matters is a tool indexing code the oracle has no truth for.
    const rels = own.map((sf) => namer.moduleOf(sf)).sort();
    for (const r of rels) process.stdout.write(r + '\n');
    process.stderr.write(`# checker files: ${rels.length}\n`);
    return;
  }

  if (args.mode === 'program') {
    // Every SOURCE file in the checker's program that is not the subject's own — the sibling
    // packages of a monorepo, resolved through `paths` — as paths relative to the root (`../…`).
    // Gate 4 gives the tools these files too, as context that is never scored, so the tools and
    // the checker see the same program (issue #20). Declaration files and node_modules are not
    // source and are not listed.
    const rels: string[] = [];
    for (const sf of program.getSourceFiles()) {
      if (sf.isDeclarationFile || namer.isOwn(sf)) continue;
      if (!/\.(ts|tsx|mts|cts)$/.test(sf.fileName) || sf.fileName.includes('node_modules')) continue;
      rels.push(path.relative(args.root, sf.fileName).split(path.sep).join('/'));
    }
    rels.sort();
    for (const r of rels) process.stdout.write(r + '\n');
    process.stderr.write(`# program files outside the subject: ${rels.length}\n`);
    return;
  }

  const emitContainers = (sites: Site[]): void => {
    // THE UNIVERSE IS DERIVED FROM THE SITES, not enumerated by syntax kind alongside them.
    //
    // Enumerating declarations separately means two code paths have to agree about what a container
    // is, and on kysely they did not: an OBJECT LITERAL with methods (`freeze({ create() {…} })`)
    // is a container in the sites and was absent from this list, so 101 containers that scored
    // references name were outside the universe and every edge touching one was dropped from BOTH
    // sides. The mutation self-test caught it as a "perfect" tool scoring 0.698.
    //
    // Deriving it from the sites makes the two consistent by construction.
    const all = new Set<string>(idx.containers);
    for (const sf of own) all.add(namer.moduleOf(sf));
    const containerOfRef = (r: string): string => r.split('#')[0];
    for (const s of sites) {
      all.add(containerOfRef(s.caller));
      for (const t of [...s.certain, ...s.possible, ...s.possible_rta, ...s.declaring_ancestors]) {
        all.add(containerOfRef(t));
      }
    }
    for (const c of [...all].sort()) process.stdout.write(c + '\n');
    process.stderr.write(`# containers (incl. modules + literals): ${all.size}\n`);
  };

  if (args.mode === 'collisions') {
    // Two distinct declarations that produce one canonical container name. The anonymous key
    // carries a line, so this should be empty; it is checked rather than assumed, for the same
    // reason the Java gate exists.
    const byName = new Map<string, Set<string>>();
    for (const c of idx.containers) {
      const where = idx.declLine.get(c) ?? '?';
      if (!byName.has(c)) byName.set(c, new Set());
      byName.get(c)!.add(where);
    }
    let n = 0;
    for (const [name, wheres] of [...byName].sort()) {
      if (wheres.size < 2) continue;
      n++;
      process.stdout.write(`${name} <- ${[...wheres].sort().join(', ')}\n`);
    }
    process.stderr.write(`# canonical-name collisions: ${n}\n`);
    return;
  }

  const emitMethods = (sites: Site[]): void => {
    const out = new Set<string>();
    for (const sf of own) {
      const visit = (node: ts.Node): void => {
        // The method universe MUST be exactly the set `enclosingFunction` can return, or a caller
        // exists in the sites and not in the universe — and `in_universe` then drops every row that
        // names it. At Tier C, where scoping is by NAME, that silently deletes a whole population:
        // `export const arrow = (x) => …` is a caller in the sites and was absent here, so two
        // functions' worth of edges vanished from both sides and the self-test caught it.
        const bp = (ts.isArrowFunction(node) || ts.isFunctionExpression(node))
          ? bindingParent(node) : undefined;
        const namedFnExpr = !!bp
          && (ts.isVariableDeclaration(bp) || ts.isPropertyAssignment(bp)
              || ts.isPropertyDeclaration(bp));
        if (ts.isFunctionDeclaration(node) || ts.isMethodDeclaration(node)
            || ts.isConstructorDeclaration(node) || ts.isMethodSignature(node)
            || ts.isGetAccessorDeclaration(node) || ts.isSetAccessorDeclaration(node)
            || namedFnExpr) {
          const c = namer.containerOf(node);
          if (c !== undefined) {
            const sig = checker.getSignatureFromDeclaration(node as ts.SignatureDeclaration);
            const ps = sig ? paramsOf(sig, checker) : [];
            out.add(ref(c, declName(node as ts.Declaration, namer), ps));
          }
        }
        ts.forEachChild(node, visit);
      };
      ts.forEachChild(sf, visit);
    }
    // and everything the SITES name, for the reason spelled out in emitContainers: a `<module>`
    // caller (top-level code) and an `<anon@N>` callback are both scored references, and neither is
    // reachable by walking declaration kinds.
    for (const s of sites) {
      out.add(s.caller);
      for (const t of [...s.certain, ...s.possible, ...s.possible_rta, ...s.declaring_ancestors]) {
        out.add(t);
      }
    }
    for (const m of [...out].sort()) process.stdout.write(m + '\n');
    process.stderr.write(`# methods: ${out.size}\n`);
  };

  // classes the subject declares but that declare no constructor of their own
  const noCtorClasses = new Set<string>();
  for (const c of idx.containers) {
    // classes only: an interface or an object literal has no constructor to be missing, and
    // listing them widened the neutral zone with constructors that cannot exist (#53 §4)
    const d = idx.decl.get(c);
    if (!d || !(ts.isClassDeclaration(d) || ts.isClassExpression(d))) continue;
    if (!idx.members.get(c)?.has('constructor')) noCtorClasses.add(c);
  }

  // ── the checker-backed assignability oracle, memoised ────────────────────────────────────
  const typeCache = new Map<string, ts.Type | undefined>();
  const typeOfContainer = (c: string): ts.Type | undefined => {
    if (typeCache.has(c)) return typeCache.get(c);
    const d = idx.decl.get(c);
    let t: ts.Type | undefined;
    if (d) {
      if (ts.isObjectLiteralExpression(d as unknown as ts.Node)) {
        // an object literal has no DECLARED type — its type is the type OF THE EXPRESSION
        try { t = checker.getTypeAtLocation(d as unknown as ts.Node); } catch { t = undefined; }
      } else {
        const sym = (d as any).symbol as ts.Symbol | undefined;
        if (sym) {
          try { t = checker.getDeclaredTypeOfSymbol(sym); } catch { t = undefined; }
        }
      }
    }
    typeCache.set(c, t);
    return t;
  };
  const assignCache = new Map<string, boolean>();
  const assignable = (cand: string, target: string, targetType: ts.Type): boolean => {
    const k = cand + '\u0000' + target;
    const hit = assignCache.get(k);
    if (hit !== undefined) return hit;
    const ct = typeOfContainer(cand);
    let ok = false;
    if (ct) {
      try { ok = checker.isTypeAssignableTo(ct, targetType); } catch { ok = false; }
    }
    assignCache.set(k, ok);
    return ok;
  };

  const rawRows = new Set<string>();
  const excludedEdges = new Set<string>();
  const sites: Site[] = [];

  for (const sf of own) {
    const mod = namer.moduleOf(sf);
    const seqByCaller = new Map<string, number>();

    const visit = (node: ts.Node): void => {
      const isCall = ts.isCallExpression(node) || ts.isNewExpression(node)
                     || ts.isTaggedTemplateExpression(node);
      if (isCall) {
        const sig = checker.getResolvedSignature(node as ts.CallLikeExpression);
        const decl = sig?.declaration;
        const { line } = sf.getLineAndCharacterOfPosition(node.getStart(sf));

        const encl = enclosingFunction(node);
        let caller: string | undefined;
        if (encl && (ts.isPropertyDeclaration(encl) || ts.isClassStaticBlockDeclaration(encl))) {
          // a class field initializer runs in the CONSTRUCTOR (spelled with the declared
          // constructor's parameters, or none when the class declares no constructor); a static
          // field or `static { }` block in the class's static initializer, `<clinit>` (#74)
          const cls = encl.parent;
          const c = ts.isClassLike(cls) ? namer.containerOf(encl) : undefined;
          if (c !== undefined) {
            const isStatic = ts.isClassStaticBlockDeclaration(encl)
              || (ts.canHaveModifiers(encl) && !!ts.getModifiers(encl)?.some((m) => m.kind === ts.SyntaxKind.StaticKeyword));
            if (isStatic) {
              caller = ref(c, '<clinit>', []);
            } else {
              const ctor = ts.isClassLike(cls)
                ? cls.members.find((m) => ts.isConstructorDeclaration(m) && !!m.body) as ts.ConstructorDeclaration | undefined
                : undefined;
              const csig = ctor ? checker.getSignatureFromDeclaration(ctor) : undefined;
              caller = ref(c, 'constructor', csig ? paramsOf(csig, checker) : []);
            }
          }
        } else if (encl) {
          const c = namer.containerOf(encl);
          if (c !== undefined) {
            const esig = checker.getSignatureFromDeclaration(encl as ts.SignatureDeclaration);
            caller = ref(c, declName(encl as ts.Declaration, namer),
                         esig ? paramsOf(esig, checker) : []);
          }
        } else {
          // top-level code: the module itself is the caller, which is what a module side effect is
          caller = ref(mod, '<module>', []);
        }

        // A resolved "declaration" that is a function TYPE — `f: (t: T) => U` — is not a callable
        // the subject defines. The checker is telling us the call goes through a function VALUE and
        // that the value's identity is not decidable here. Scoring the type node as a target would
        // invent a method that appears in no source file, and every tool would score `missed`
        // against it. Recorded as `indirect`, counted, never scored — the TypeScript analogue of
        // the Java oracle's declared blind spot.
        // A `super.m()` or `super(...)` call is NON-VIRTUAL: it names exactly the inherited
        // implementation and cannot dispatch to an override further down. Expanding the heritage
        // envelope for one would add targets the language forbids, and would then score a tool that
        // correctly named the single target as having under-fanned.
        const callee = ts.isCallExpression(node) ? node.expression : undefined;
        const isSuper = !!callee && (
          callee.kind === ts.SyntaxKind.SuperKeyword
          || (ts.isPropertyAccessExpression(callee)
              && callee.expression.kind === ts.SyntaxKind.SuperKeyword));

        // A member declared inside a TYPE LITERAL — `container as Options & { getValue(n): unknown }`
        // — belongs to no container; keying it under the enclosing class invented
        // `ArgumentsReader#getValue` and scored the tool that named `Options#getValue` as wrong
        // (issue #39). The call is redirected to the receiver's APPARENT type: the member's
        // declarations that live in real containers become the declared targets; with none, the
        // site is `indirect` (neutral), never an invented target.
        const inTypeLiteral = (d: ts.Node): boolean => {
          for (let n: ts.Node | undefined = d.parent; n && !ts.isSourceFile(n); n = n.parent) {
            if (ts.isTypeLiteralNode(n)) return true;
            if (ts.isClassDeclaration(n) || ts.isInterfaceDeclaration(n) || ts.isClassExpression(n)
                || ts.isObjectLiteralExpression(n) || ts.isModuleDeclaration(n)) return false;
          }
          return false;
        };
        let decl2: ts.Declaration | undefined = decl as ts.Declaration | undefined;
        let literalRedirect = false;
        if (decl && inTypeLiteral(decl)) {
          literalRedirect = true;
          decl2 = undefined;
          const callee0 = ts.isCallExpression(node) ? node.expression : undefined;
          if (callee0 && ts.isPropertyAccessExpression(callee0)) {
            try {
              const rt = checker.getApparentType(checker.getTypeAtLocation(callee0.expression));
              const prop = checker.getPropertyOfType(rt, callee0.name.text);
              const real = (prop?.declarations ?? []).find((d) => namer.isOwn(d.getSourceFile()) && !inTypeLiteral(d)
                && (ts.isMethodDeclaration(d) || ts.isMethodSignature(d) || ts.isPropertyDeclaration(d) || ts.isPropertySignature(d)));
              if (real) decl2 = real;
            } catch { decl2 = undefined; }
          }
        }
        // A callee whose TYPE is a union of two or more callables — `const chosen = cond ? incr
        // : decr; chosen(1)` — resolves, in the checker, to one arm's declaration; scoring that as
        // a certain, uniquely linked call to `incr` silently discarded `decr` and charged the
        // tool that reported both (#52 §1). It is a call through a function value: indirect.
        // The same test from the other side: a callee IDENTIFIER whose symbol is a variable
        // holding anything but a function written there — `const chosen = cond ? incr : decr`
        // (the checker reduces two identical function types to one and resolves to one arm),
        // `const f = pick()`, `let g = h` — is a call through a function value, not a call to the
        // declaration the checker happens to name.
        let unionOfCallables = false;
        if (callee && ts.isIdentifier(callee) && decl && namer.isOwn(decl.getSourceFile())) {
          try {
            const ct = checker.getTypeAtLocation(callee);
            if (ct.isUnion()) {
              const arms = ct.types.filter((t) => t.getCallSignatures().length > 0);
              unionOfCallables = arms.length > 1;
            }
            const sym = checker.getSymbolAtLocation(callee);
            const vd = sym?.valueDeclaration;
            // `const { run } = obj; run()` — a destructured binding holds a function VALUE (#73)
            if (vd && ts.isBindingElement(vd)) unionOfCallables = true;
            if (vd && ts.isVariableDeclaration(vd) && vd.initializer) {
              let init: ts.Expression = vd.initializer;
              while (ts.isParenthesizedExpression(init) || ts.isAsExpression(init)
                     || ts.isSatisfiesExpression(init) || ts.isNonNullExpression(init)
                     || ts.isTypeAssertionExpression(init)) init = init.expression;
              const writtenFn = ts.isArrowFunction(init) || ts.isFunctionExpression(init)
                || ts.isClassExpression(init);
              if (!writtenFn && decl !== vd) unionOfCallables = true;
            }
          } catch { unionOfCallables = false; }
        }
        const isNew = ts.isNewExpression(node);
        // a closure with no name of its own — the arrow `bind()` returns and a field stores, a
        // construct-signature type alias — is a call through a function VALUE: keying it
        // `<anon@N>` made 33 typedoc groups unwinnable for every real tool (#73)
        const anonymousClosure = !!decl && (
          ((ts.isArrowFunction(decl) || ts.isFunctionExpression(decl)) && (() => {
            const bp = bindingParent(decl);
            return !(bp && (ts.isVariableDeclaration(bp) || ts.isPropertyAssignment(bp) || ts.isPropertyDeclaration(bp)));
          })())
          || ts.isConstructorTypeNode(decl));
        // …and only for a declaration the SUBJECT owns: `new Error()`, `new Map()`, `String(x)`
        // resolve to construct/call signatures in lib.*.d.ts and are boundary calls, not calls
        // through a function value (123 of kysely's 241 "indirect" sites were library
        // constructors, #67 §1)
        const ownDecl = !!decl && namer.isOwn(decl.getSourceFile());
        const indirect = !!decl && ownDecl && (ts.isFunctionTypeNode(decl) || ts.isConstructSignatureDeclaration(decl)
                                    || ts.isCallSignatureDeclaration(decl) || (literalRedirect && !decl2)
                                    || unionOfCallables || anonymousClosure);
        if (caller && decl) {
          const calleeSf = decl.getSourceFile();
          const op = ts.isNewExpression(node) ? 'NEW'
                   : ts.isTaggedTemplateExpression(node) ? 'TAGGED' : 'CALL';
          const name = declName(decl as ts.Declaration, namer);
          // Tier A spells the DECLARATION's parameters: the resolved signature of a call on a
          // union receiver is checker-synthesised (`Bx#set(never)`), a method no source declares
          // (#68 §2). An overload's chosen declaration carries that overload's own list.
          let ps = paramsOf(sig!, checker);
          if (decl && namer.isOwn(decl.getSourceFile())
              && (ts.isMethodDeclaration(decl) || ts.isMethodSignature(decl) || ts.isFunctionDeclaration(decl)
                  || ts.isConstructorDeclaration(decl) || ts.isArrowFunction(decl) || ts.isFunctionExpression(decl))) {
            try {
              const dsig = checker.getSignatureFromDeclaration(decl);
              if (dsig) ps = paramsOf(dsig, checker);
            } catch { /* keep the resolved signature's parameters */ }
          }

          rawRows.add(`${caller} | ${op} | ${namer.isOwn(calleeSf) ? namer.moduleOf(calleeSf) : '<external>'}`
                      + `:${name}(${ps.join(',')})`);

          // the expansion of ONE declared target: declared heritage, then structural
          // assignability (see the header), with a property bound to a named function
          // standing for that function (#27 §3)
          // spelled with the CANDIDATE's own declared parameters where it declares the member —
          // `SelectQueryBuilderImpl#select(SE)` was the call's type arguments copied onto an
          // override, a method no source declares (#68, comment); the call's list only when the
          // candidate's declaration carries no signature (an untyped property)
          const ownParams = (cand: string, n: string, cps: string[]): string[] => {
            const d = idx.memberDecl.get(`${cand}#${n}`);
            if (!d) return cps;
            try {
              if (ts.isMethodDeclaration(d) || ts.isMethodSignature(d) || ts.isConstructorDeclaration(d)) {
                const sg = checker.getSignatureFromDeclaration(d);
                if (sg) return paramsOf(sg, checker);
              }
              const init = (d as any).initializer as ts.Expression | undefined;
              if (init && (ts.isArrowFunction(init) || ts.isFunctionExpression(init))) {
                const sg = checker.getSignatureFromDeclaration(init);
                if (sg) return paramsOf(sg, checker);
              }
            } catch { /* fall through */ }
            return cps;
          };
          const memberTarget = (cand: string, n: string, cps: string[]): string =>
            idx.boundFn.get(`${cand}#${n}`) ?? ref(cand, n, ownParams(cand, n, cps));
          let recvExprType: ts.Type | null | undefined = null;
          if (callee && ts.isPropertyAccessExpression(callee)) {
            try { recvExprType = checker.getTypeAtLocation(callee.expression); } catch { recvExprType = null; }
            // a union or a type parameter is not one receiver type; the declared container's
            // type is used for those as before
            if (recvExprType && (recvExprType.isUnion() || recvExprType.isTypeParameter())) recvExprType = null;
          }
          // an interface's member cannot run: an interface reached through heritage or
          // assignability is never a `possible` target (an abstract class's abstract member is
          // filtered the same way where the checker can tell)
          const runnable = (cand: string, n?: string): boolean => {
            const d = idx.decl.get(cand);
            if (d && ts.isInterfaceDeclaration(d)) return false;
            // an ABSTRACT re-declaration (`abstract class B extends A { abstract f() }`) cannot
            // run any more than an interface member can (#67 §2, the TypeScript twin of #30)
            if (n && d && ts.isClassLike(d)) {
              const m = d.members.find((x) => (x as any).name && ts.isIdentifier((x as any).name) && (x as any).name.text === n);
              if (m && ts.canHaveModifiers(m) && ts.getModifiers(m)?.some((k) => k.kind === ts.SyntaxKind.AbstractKeyword)) return false;
              // a concrete member of an ABSTRACT class runs only through a concrete subclass that
              // inherits it without re-declaring it
              const isAbstractClass = ts.canHaveModifiers(d) && !!ts.getModifiers(d)?.some((k) => k.kind === ts.SyntaxKind.AbstractKeyword);
              if (isAbstractClass && !inheritedByConcrete(cand, n)) return false;
            }
            return true;
          };
          const nearestDeclaring = (start: string, n: string): string | undefined => {
            const seen = new Set<string>(); let level = [...(idx.parents.get(start) ?? [])];
            while (level.length) {
              const next: string[] = [];
              for (const x of level) {
                if (seen.has(x)) continue; seen.add(x);
                if (idx.members.get(x)?.has(n)) return x;
                next.push(...(idx.parents.get(x) ?? []));
              }
              level = next;
            }
            return undefined;
          };
          const inheritedByConcrete = (c: string, n: string): boolean => {
            for (const sub of idx.subs.get(c) ?? []) {
              const sd = idx.decl.get(sub);
              const abstractSub = !!sd && ts.canHaveModifiers(sd) && !!ts.getModifiers(sd)?.some((k) => k.kind === ts.SyntaxKind.AbstractKeyword);
              const iface = !!sd && ts.isInterfaceDeclaration(sd);
              if (abstractSub || iface || idx.members.get(sub)?.has(n)) continue;
              if (nearestDeclaring(sub, n) === c) return true;
            }
            return false;
          };
          // RTA: the target runs on an instantiated receiver — the declaring container itself,
          // or an instantiated subclass that INHERITS the member (nothing between them
          // re-declares it). Requiring the declaring container to be `new`-ed dropped 191
          // typedoc sites reached through `new Application` (#67 §4).
          const runsOnInstantiated = (c: string, n: string): boolean => {
            if (idx.instantiated.has(c)) return true;
            for (const sub of idx.subs.get(c) ?? []) {
              if (!idx.instantiated.has(sub) || idx.members.get(sub)?.has(n)) continue;
              if (nearestDeclaring(sub, n) === c) return true;   // the nearest declaring ancestor is `c`
            }
            return false;
          };
          const expand = (cc: string, n: string, cps: string[]) => {
            const possible = new Set<string>();
            const rta = new Set<string>();
            const ancestors = new Set<string>();
            // `new C()` names its constructor exactly — there is no dispatch to expand over, and
            // expanding it flipped `unique` off on 32 kysely/typedoc constructor sites (#52 §4)
            for (const sub of (isSuper || isNew ? [] : idx.subs.get(cc) ?? [])) {
              if (!(idx.members.get(sub)?.has(n)) || !runnable(sub, n)) continue;
              const t = memberTarget(sub, n, cps);
              possible.add(t);
              if (runsOnInstantiated(sub, n)) rta.add(t);
            }
            // ── STRUCTURAL DISPATCH ────────────────────────────────────────────────────────
            // TypeScript is structurally typed: a class satisfies an interface WITHOUT writing
            // `implements`, and idiomatic TypeScript does exactly that. On kysely,
            // `MysqlConnection` never names `DatabaseConnection` — so a declared-heritage
            // envelope contained only the interface itself, and a tool that correctly resolved
            // the concrete implementation was scored `polluted` for being right. The envelope
            // therefore asks the CHECKER the question the language poses: is this candidate's
            // type assignable to the receiver's? Candidates are restricted to containers
            // declaring a member of the same name.
            if (!isSuper && !isNew && !n.startsWith('<')) {
              // the receiver EXPRESSION's type where there is one — `b: Box<number>` — so a
              // structural implementor of an instantiated generic interface is found; the
              // declared `Box<T>` alone admitted nothing (#67 §2 S3)
              let siteType: ts.Type | undefined;
              if (callee && ts.isPropertyAccessExpression(callee) && recvExprType !== null) {
                siteType = recvExprType;
              }
              const recvType = siteType ?? typeOfContainer(cc);
              if (recvType) {
                for (const cand of idx.byMember.get(n) ?? []) {
                  if (cand === cc || !runnable(cand, n)) continue;
                  const t = memberTarget(cand, n, cps);
                  if (possible.has(t)) continue;
                  if (!assignable(cand, siteType ? cc + '@' + checker.typeToString(recvType) : cc, recvType)) continue;
                  possible.add(t);
                  if (runsOnInstantiated(cand, n)) rta.add(t);
                }
              }
            }
            for (const parent of idx.parents.get(cc) ?? []) {
              if (idx.members.get(parent)?.has(n)) ancestors.add(ref(parent, n, cps));
            }
            return { possible, rta, ancestors };
          };

          if (indirect) {
            // Named by the property or identifier AS WRITTEN (`debug(...)`, `h.handle(...)`), not
            // by `declName` of the function-type node (`<anon@12>`), so the neutral zone keyed on
            // (caller, name) can match a tool that reports the name (#27 §4).
            const written = callee && ts.isPropertyAccessExpression(callee) ? callee.name.text
                          : callee && ts.isIdentifier(callee) ? callee.text
                          // `table["handler"](x)`: the name as written is the literal (#53 §3)
                          : callee && ts.isElementAccessExpression(callee)
                              ? (ts.isStringLiteralLike(callee.argumentExpression) ? callee.argumentExpression.text
                                 : callee.argumentExpression.getText())              // `handlers[kind]` -> `kind` (#53 §3)
                          : ts.isTaggedTemplateExpression(node)
                              ? (ts.isIdentifier(node.tag) ? node.tag.text
                                 : ts.isPropertyAccessExpression(node.tag) ? node.tag.name.text : name)
                          : ts.isNewExpression(node) && ts.isIdentifier(node.expression) ? node.expression.text
                          : name;
            const seq = seqByCaller.get(caller) ?? 0;
            seqByCaller.set(caller, seq + 1);
            sites.push({
              site_id: `${caller}@${line + 1}#${seq}`,
              caller, line: line + 1, seq, op,
              receiver_static_type: '<function-value>',
              callee_name: written, callee_params: ps,
              kind: 'indirect',
              certain: [], possible: [], possible_rta: [], declaring_ancestors: [],
              unique: false, unique_rta: false,
            });
          } else if (namer.isOwn(calleeSf)) {
            const tdecl = decl2 ?? (decl as ts.Declaration);
            const cc = namer.containerOf(tdecl);
            if (cc !== undefined) {
              const target = ref(cc, declName(tdecl, namer), ps);
              const certain = new Set<string>([target]);
              const possible = new Set<string>([target]);
              // RTA holds what the program INSTANTIATES: the declared target is seeded only when
              // its receiver can exist — the container is not a class (a module function), the
              // member is static, the call is `new`, or the class is instantiated somewhere.
              // Seeding it unconditionally put `Base#run()` in `possible_rta` for a `Base` nothing
              // constructs (#52 §3), against every tool that was right to leave it out.
              const isStaticDecl = ts.canHaveModifiers(tdecl)
                && !!ts.getModifiers(tdecl)?.some((m) => m.kind === ts.SyntaxKind.StaticKeyword);
              const ccDecl = idx.decl.get(cc);
              const classReceiver = !!ccDecl && (ts.isClassDeclaration(ccDecl) || ts.isClassExpression(ccDecl));
              const rta = new Set<string>(
                (!classReceiver || isStaticDecl || isNew || runsOnInstantiated(cc, name)) ? [target] : []);
              const ancestors = new Set<string>();
              const notRunnable = (d: ts.Declaration): boolean =>
                ts.isMethodSignature(d) || ts.isPropertySignature(d)
                || (!!d.parent && ts.isInterfaceDeclaration(d.parent))
                || (ts.canHaveModifiers(d) && !!ts.getModifiers(d)?.some((m) => m.kind === ts.SyntaxKind.AbstractKeyword));
              const unionDeclared: [string, ts.Declaration][] = [];
              // a STATIC member is looked up on the constructor object the source names: no
              // dispatch, `possible = certain` (#80)
              const e0 = isStaticDecl ? { possible: new Set<string>(), rta: new Set<string>(), ancestors: new Set<string>() }
                                      : expand(cc, name, ps);
              let externalArm = false;
              for (const t of e0.possible) possible.add(t);
              for (const t of e0.rta) rta.add(t);
              for (const t of e0.ancestors) ancestors.add(t);

              // A UNION RECEIVER (`x: Alpha | Beta; x.run()`): the checker's resolved signature
              // names one constituent's member, but the call dispatches on the runtime type and
              // every constituent's member is a declared target (#27 §2). Each is resolved and
              // expanded on its own.
              if (callee && ts.isPropertyAccessExpression(callee)) {
                let recv: ts.Type | undefined;
                try { recv = checker.getTypeAtLocation(callee.expression); } catch { recv = undefined; }
                const parts = recv && recv.isUnion() ? recv.types : [];
                for (const part of parts) {
                  const prop = part.getProperty(name);
                  for (const d of prop?.declarations ?? []) {
                    // an arm the subject does not own (`x: Alpha | Date; x.toString()`) runs
                    // library code: the site is not uniquely linked to the own arm (#67 §3)
                    if (!namer.isOwn(d.getSourceFile())) { externalArm = true; continue; }
                    if (!(ts.isMethodDeclaration(d) || ts.isMethodSignature(d)
                          || ts.isPropertyDeclaration(d) || ts.isPropertySignature(d))) continue;
                    const dcc = namer.containerOf(d);
                    if (dcc === undefined) continue;
                    let dps: string[] = ps;
                    try {
                      // the arm's own declaration: the union-synthesised signature minted
                      // `Box#set(never)`, a method no source declares (#68 §2)
                      const dsig = (ts.isMethodDeclaration(d) || ts.isMethodSignature(d))
                        ? checker.getSignatureFromDeclaration(d) : undefined;
                      if (dsig) dps = paramsOf(dsig, checker);
                      else {
                        const pt = checker.getTypeOfSymbolAtLocation(prop!, callee);
                        const csig = checker.getSignaturesOfType(pt, ts.SignatureKind.Call)[0];
                        if (csig) dps = paramsOf(csig, checker);
                      }
                    } catch { /* keep the resolved arm's params */ }
                    const dt = ref(dcc, name, dps);
                    // through the same runnable test as the resolved arm: an interface member
                    // reached through a union arm was landing in `possible` (#52 §2)
                    certain.add(dt); possible.add(dt);
                    if (idx.instantiated.has(dcc)) rta.add(dt);
                    unionDeclared.push([dt, d]);
                    const ex = expand(dcc, name, dps);
                    for (const t of ex.possible) possible.add(t);
                    for (const t of ex.rta) rta.add(t);
                    for (const t of ex.ancestors) ancestors.add(t);
                  }
                }
              }
              // `possible` holds what can RUN. An interface member or an abstract method is the
              // DECLARED target (`certain`) and cannot run; where an implementor exists it leaves
              // `possible`, so an interface with one implementor is uniquely linked to it — the
              // same stance the Java oracle takes since #30. Where nothing implements it in the
              // subject, the declaration stays as the one answer a tool can be scored on.
              if (notRunnable(tdecl) && possible.size > 1) {
                possible.delete(target); rta.delete(target); ancestors.add(target);
              }
              for (const [dt, d] of unionDeclared) {
                if (notRunnable(d) && possible.size > 1) {
                  possible.delete(dt); rta.delete(dt); ancestors.add(dt);
                }
              }
              for (const p of possible) ancestors.delete(p);
              // a union arm outside the subject: the call can run library code, so the site is a
              // BOUNDARY with the own arms as accepted answers — the same stance Java takes for a
              // declared target outside the application (#67 §3)
              if (externalArm) {
                for (const t of possible) ancestors.add(t);
                for (const t of certain) ancestors.add(t);
                certain.clear(); possible.clear(); rta.clear();
              }

              const seq = seqByCaller.get(caller) ?? 0;
              seqByCaller.set(caller, seq + 1);
              sites.push({
                site_id: `${caller}@${line + 1}#${seq}`,
                caller, line: line + 1, seq, op,
                receiver_static_type: externalArm ? '<external>' : cc,
                callee_name: name, callee_params: ps,
                kind: externalArm ? 'boundary' : 'internal',
                certain: [...certain].sort(), possible: [...possible].sort(), possible_rta: [...rta].sort(),
                declaring_ancestors: [...ancestors].sort(),
                unique: possible.size === 1, unique_rta: rta.size === 1,
              });
            }
          } else {
            // the call leaves the subject: recorded so the count is auditable, scored against
            // nothing, exactly like a Java client -> library hand-off
            const seq = seqByCaller.get(caller) ?? 0;
            seqByCaller.set(caller, seq + 1);
            sites.push({
              site_id: `${caller}@${line + 1}#${seq}`,
              caller, line: line + 1, seq, op,
              receiver_static_type: '<external>',
              callee_name: name, callee_params: ps,
              kind: 'boundary',
              certain: [], possible: [], possible_rta: [], declaring_ancestors: [],
              unique: false, unique_rta: false,
            });
          }
        }
      }
      ts.forEachChild(node, visit);
    };
    ts.forEachChild(sf, visit);
  }

  if (args.mode === 'crosscheck') {
    // GATE 1, AND IT IS WEAKER THAN THE JAVA ONE — SAID PLAINLY.
    //
    // Java has two independent readers of the same artefact (`java.lang.classfile` and `javap`),
    // so its gate 1 proves the bytecode was read correctly. TypeScript has exactly ONE
    // implementation of its type system; there is no second checker to disagree with. What can be
    // checked is that OUR USE of it is consistent: `getResolvedSignature(call).declaration` and
    // `getSymbolAtLocation(callee).declarations` are different entry points into the checker, and
    // for a call with a single declaration they must name the same one.
    //
    // That rules out a misuse of the API — the failure mode actually available to us — and does
    // NOT rule out a bug in the checker itself. No available technique does, which is why the
    // TypeScript numbers are reported as a diagnostic rather than as a ranking.
    let checked = 0, disagree = 0;
    for (const sf of own) {
      const visit = (node: ts.Node): void => {
        if (ts.isCallExpression(node)) {
          const sig = checker.getResolvedSignature(node);
          const viaSig = sig?.declaration;
          const expr = node.expression;
          // `super(...)`: the symbol at `super` is the CONTAINING class, the signature is the BASE
          // constructor. Two different questions again, so comparing them says nothing — the same
          // reason a call through a function value is excluded above.
          if (expr.kind === ts.SyntaxKind.SuperKeyword) {
            ts.forEachChild(node, visit);
            return;
          }
          let sym = checker.getSymbolAtLocation(
            ts.isPropertyAccessExpression(expr) ? expr.name : expr);
          // AN IMPORTED IDENTIFIER RESOLVES TO ITS IMPORT ALIAS, whose only declaration is the
          // `import { freeze } from './object-utils'` line — not the function. Comparing that
          // against `getResolvedSignature`, which names the real declaration, reports a
          // disagreement on EVERY cross-module call. That is this gate misreading the API, which
          // is exactly the class of fault it exists to catch, so it caught its own.
          if (sym && (sym.flags & ts.SymbolFlags.Alias) !== 0) {
            try { sym = checker.getAliasedSymbol(sym); } catch { /* not an alias after all */ }
          }
          const decls = sym?.declarations ?? [];
          // THE GATE ONLY MEANS SOMETHING WHERE THE TWO ENTRY POINTS ANSWER THE SAME QUESTION.
          //
          // `getResolvedSignature` answers "which function does this call reach".
          // `getSymbolAtLocation` answers "what does this identifier name". Those coincide only
          // when the callee identifier IS a function or method declaration. When it is a VARIABLE
          // holding one —
          //     const combine = cond ? AndNode.create : OrNode.create;  combine(...)
          // — the first does real work the second cannot replicate, and comparing them reports a
          // disagreement on every function value in the project. kysely produced ten of those and
          // not one was a fault in the checker or in our use of it; the fault was this check being
          // specified loosely. Restricting it to direct declarations is what makes a failure here
          // mean something.
          const directDecl = !!sym && (sym.flags & (ts.SymbolFlags.Function
                                                    | ts.SymbolFlags.Method
                                                    | ts.SymbolFlags.Class)) !== 0;
          if (viaSig && directDecl && decls.length === 1 && namer.isOwn(viaSig.getSourceFile())) {
            checked++;
            if (decls[0] !== viaSig) {
              const x = viaSig, y = decls[0];
              const sameFile = x.getSourceFile() === y.getSourceFile();
              // The two entry points legitimately name DIFFERENT NODES for the same code:
              //   * `const f = (x) => …` — the symbol names the VariableDeclaration, the signature
              //     names the ArrowFunction inside it. One span contains the other.
              //   * an OVERLOAD — the symbol names the implementation, the signature names the arm.
              // Neither is a disagreement about which code runs. Only two spans that neither
              // contain each other nor share a name are.
              const contains = sameFile
                && ((x.getStart() <= y.getStart() && x.getEnd() >= y.getEnd())
                    || (y.getStart() <= x.getStart() && y.getEnd() >= x.getEnd()));
              const sameName = (x as any).name?.getText?.() === (y as any).name?.getText?.();
              if (!contains && !(sameFile && sameName)) {
                disagree++;
                process.stdout.write(
                  `DISAGREE ${x.getSourceFile().fileName}:${x.getStart()}`
                  + ` vs ${y.getSourceFile().fileName}:${y.getStart()}\n`);
              }
            }
          }
        }
        ts.forEachChild(node, visit);
      };
      ts.forEachChild(sf, visit);
    }
    process.stderr.write(`# crosschecked call sites: ${checked}, disagreements: ${disagree}\n`);
    if (disagree > 0) process.exitCode = 1;
    return;
  }

  if (args.mode === 'containers') { emitContainers(sites); return; }
  if (args.mode === 'heritage') {
    // `container<TAB>kind<TAB>parent,parent` for the resolver (issue #36): whether a container
    // declares OR INHERITS a member, and whether it is an interface (never a caller).
    const rows: string[] = [];
    for (const c of [...idx.containers].sort()) {
      const d = idx.decl.get(c);
      // DECLARATION MERGING: ioredis writes `class Redis extends Commander` and, 800 lines later,
      // `interface Redis extends EventEmitter` — one symbol, two declarations. The kind is
      // `class` if ANY declaration of the symbol is a class: keying it by the last declaration
      // seen made `Redis` an interface, "never a caller", and 21 of CodeQL's ioredis groups
      // whose caller it names went from exact to missed.
      const sym = d && (d as ts.Declaration).name && ts.isIdentifier((d as ts.Declaration).name as ts.Node)
        ? checker.getSymbolAtLocation((d as ts.Declaration).name as ts.Node) : undefined;
      const decls = sym?.declarations ?? (d ? [d] : []);
      const anyClass = decls.some((x) => ts.isClassDeclaration(x) || ts.isClassExpression(x));
      const kind = !d ? 'container' : anyClass ? 'class' : ts.isInterfaceDeclaration(d) ? 'interface'
                 : 'object';
      rows.push(`${c}\t${kind}\t${[...(idx.parents.get(c) ?? [])].sort().join(',')}`);
    }
    for (const r of rows) process.stdout.write(r + '\n');
    process.stderr.write(`# heritage rows: ${rows.length}\n`);
    return;
  }
  if (args.mode === 'methods') { emitMethods(sites); return; }

  if (args.mode === 'raw') {
    for (const r of [...rawRows].sort()) process.stdout.write(r + '\n');
    process.stderr.write(`# raw resolved calls (deduplicated): ${rawRows.size}\n`);
    return;
  }
  if (args.mode === 'excluded') {
    // TWO NEUTRAL ZONES. Both are places where the benchmark declares it has no ground truth, and
    // a tool that answers anyway must be charged for NOTHING — neither credited nor penalised.
    // Charging it is the worse error: it reports a tool as imprecise exactly where the tool is
    // more capable than the oracle, which inverts the finding.
    //
    //   INDIRECT — a call through a function VALUE. The checker names the function TYPE and cannot
    //   say which implementation was passed, so there is no target to score against. A points-to
    //   analysis CAN answer these (CodeQL resolved a dispatch table and a function-valued field on
    //   this subject), and every one of those answers was landing as a false positive.
    //
    //   NO DECLARED CONSTRUCTOR — `new LoudHandler()` where the class declares none. There is no
    //   declaration for the oracle to point at, so it emits no edge; a tool that synthesises the
    //   constructor is not wrong. The Java side excludes the compiler-synthesised default
    //   constructor symmetrically for exactly this reason.
    for (const s of sites) {
      if (s.kind === 'indirect') {
        process.stdout.write(`INDIRECT\t${s.caller}\t${s.callee_name}\n`);
      }
    }
    for (const c of [...noCtorClasses].sort()) process.stdout.write(`NOCTOR\t${c}\n`);
    process.stderr.write(`# indirect sites: ${sites.filter((x) => x.kind === 'indirect').length}`
                         + `, classes with no declared constructor: ${noCtorClasses.size}\n`);
    return;
  }

  sites.sort((a, b) => (a.site_id < b.site_id ? -1 : a.site_id > b.site_id ? 1 : 0));
  for (const s of sites) process.stdout.write(JSON.stringify(s) + '\n');
  process.stderr.write(`# sites: ${sites.length}\n`);
}

main();
