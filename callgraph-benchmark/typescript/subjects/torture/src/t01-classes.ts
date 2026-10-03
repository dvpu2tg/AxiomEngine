// t01 — CLASSES AND DECLARED HERITAGE. The nominal half of TypeScript: `extends`, `implements`,
// override, `super`, abstract. This is the population where a declared-heritage envelope is the
// right answer, and where a name-keyed resolver gets the override wrong.

export interface Shape {
  area(): number;
  tag(): string;
}

export abstract class Base implements Shape {
  abstract area(): number;
  tag(): string { return 'base'; }
  // calls an abstract member on `this` — the target is every concrete override
  describe(): string { return `${this.tag()}:${this.area()}`; }
}

export class Square extends Base {
  constructor(private readonly s: number) { super(); }
  area(): number { return this.s * this.s; }
  // `super.tag()` is NON-VIRTUAL: exactly one target, never a fan back to the override
  override tag(): string { return `sq/${super.tag()}`; }
}

export class Unit extends Square {
  constructor() { super(1); }
  override area(): number { return 1; }
}

// the receiver is the ABSTRACT base: the sound answer is the set of concrete overrides
export function viaBase(b: Base): number { return b.area(); }
// the receiver is the INTERFACE: the same question one level wider
export function viaInterface(s: Shape): number { return s.area(); }
// declared type is the base, allocated type is the leaf — a flow-typing tool answers Unit
export function viaAllocated(): number { const b: Base = new Unit(); return b.area(); }
// an inherited concrete method calling an abstract one
export function viaInherited(q: Square): string { return q.describe(); }
