// t03 — FUNCTION VALUES. Arrow functions, function expressions, a callback passed as a parameter,
// a function stored in a field and in a map. TypeScript has no compiler-generated closure name, so
// a call written INSIDE a closure is attributed by the oracle to the function that lexically
// contains it — the same fold the Java oracle applies to a lambda body.

export function helper(x: number): number { return x + 1; }

export const arrow = (x: number): number => helper(x);

export const expr = function named(x: number): number { return helper(x); };

// a call written inside a closure: folds outward to `usesClosure`
export function usesClosure(xs: number[]): number[] {
  return xs.map((x) => helper(x));
}

// a function VALUE arriving as a parameter — resolvable only by following the caller
export function higherOrder(f: (n: number) => number, x: number): number { return f(x); }
export function callsHigherOrder(): number { return higherOrder(helper, 1); }

// a dispatch table: the target is chosen at runtime by a key
const table: Record<string, (n: number) => number> = { a: helper, b: arrow };
export function viaTable(k: string, x: number): number { return table[k](x); }

class Holder {
  fn: (n: number) => number = helper;
  call(x: number): number { return this.fn(x); }
}
export function viaField(x: number): number { return new Holder().call(x); }
