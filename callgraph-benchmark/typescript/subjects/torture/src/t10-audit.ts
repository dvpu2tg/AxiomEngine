// t10 — FOUR PLACES THE ORACLE ONCE EMITTED FALSE GROUND TRUTH (issue #52) and two callers it
// misnamed (issue #53). Each construct's expected row is stated beside it; EXPECTED.md is
// generated from the oracle and must agree.

export function incr(n: number): number { return n + 1; }
export function decr(n: number): number { return n - 1; }

export function chooseFn(cond: boolean): number {
  const chosen = cond ? incr : decr;
  return chosen(1);                          // (1) union of two callables -> indirect, never certain
}

export interface R { m(): number }
export class RImpl implements R { m(): number { return 1; } }
export class Other { m(): number { return 2; } }

export function viaUnionArm(x: R | Other): number {
  return x.m();                              // (2) R#m is DECLARED (certain), never in possible: RImpl#m and Other#m run
}

export class Base { run(): string { return 'base'; } }
export class Deeper extends Base { override run(): string { return 'deeper'; } }

export function rtaSeed(b: Base): string {
  return b.run();                            // (3) Base is never `new`-ed: possible {Base, Deeper}, rta {Deeper}
}
export function mkDeeper(): Deeper { return new Deeper(); }

export class SuperBase { constructor(n: number) { void n; } }
export class WithCtor extends SuperBase { constructor(n: number) { super(n); } }
export class Sub extends WithCtor { constructor(n: number) { super(n); } }

export function construct(): WithCtor {
  return new WithCtor(1);                    // (4) `new` does not dispatch: exactly WithCtor#constructor, unique
}

export function binaryFindPartition(arr: number[], pred: (v: number) => boolean): number {
  return arr.findIndex(pred);
}
export function helper(v: number): boolean { return v > 0; }

export function callerOfPredicate(arr: number[]): number {
  const index = binaryFindPartition(arr, (v) => helper(v));   // (5) the arrow folds into callerOfPredicate, not "index"
  return index;
}

export function elementAccess(table: { handler: (x: number) => number }, x: number): number {
  return table["handler"](x);                // (6) indirect, named `handler` as written
}
