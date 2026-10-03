// t04 — OVERLOADS AND GENERICS. TypeScript overloads are DECLARATION signatures over one
// implementation, so `getResolvedSignature` names the ARM, not the implementation — a distinction
// only a checker-backed tool can make, and the one place Tier A is genuinely discriminating.

export function pick(x: string): string;
export function pick(x: number): string;
export function pick(x: string | number): string { return typeof x === 'string' ? 's' : 'n'; }

export function callsStringArm(): string { return pick('a'); }
export function callsNumberArm(): string { return pick(1); }

export class Box<T> {
  constructor(private readonly v: T) {}
  get(): T { return this.v; }
  map<U>(f: (t: T) => U): Box<U> { return new Box(f(this.v)); }
}

export function viaGeneric(): number { return new Box(1).get(); }
export function viaGenericMethod(): string { return new Box(1).map((n) => String(n)).get(); }
