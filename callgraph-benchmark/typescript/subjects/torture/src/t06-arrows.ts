// t06 — HOW AN ANONYMOUS FUNCTION IS NAMED. Every row here is a construct that a real subject
// turned out to be built from and that one side of the comparison once named wrongly (#15).
// The expected caller of each `target()` call is written next to it; docs/PROTOCOL.md §3.1 is the
// rule, and this file is the enumeration a reader can check the oracle's output against.

export function target(): number { return 1; }
function wrap<T>(f: T): T { return f; }

// (a) an arrow bound to a const: named `arrowConst`
export const arrowConst = (): number => target();

// (b) an arrow behind a wrapper call: the binding is outside the wrapper — named `wrapped`
export const wrapped = wrap((): number => target());

// (c) an arrow behind a cast: named `casted`
export const casted = ((): number => target()) as () => number;

export class Widget {
  // (d) a class-field arrow — the React idiom — named `Widget#onClick`, NOT `<anon@line>`
  onClick = (): number => target();

  // (e) a class-field arrow behind a wrapper: `Widget#onMove`, NOT `<module>`
  onMove = wrap((): number => target());

  // (f) a closure nested in a method: folds into `Widget#run`
  run(): number[] { return [1].map(() => target()); }

  // (g) a NAMED arrow nested in a method: `Widget#inner` — its container is the class
  viaInner(): number {
    const inner = (): number => target();
    return inner();
  }
}

// (h) an object literal bound to a const: `Ops#apply` (the literal is keyed by its binding)
export const Ops = wrap({
  apply(): number { return target(); },
  // (i) a property arrow in that literal: `Ops#applyArrow`
  applyArrow: (): number => target(),
});

// (j) an object literal RETURNED, bound to nothing: keyed by its contextual type and line,
//     `$obj:Instance@<line>#run`. A tool that says `t06-arrows.ts#run` is placed there by the
//     resolver when the module declares no `run` of its own and exactly one literal does.
export interface Instance { run(): number }
export function getInstance(): Instance {
  return {
    run: (): number => target(),
  };
}

// (k) a top-level closure bound to nothing: the caller is `<module>`
[1].forEach(() => target());
