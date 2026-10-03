// t08 — WHAT THE ENVELOPE ADMITS (issue #27). Five programs the peer audit wrote against the
// oracle; EXPECTED.md states what `possible` holds for each call. The rule the oracle applies:
// `possible` = the declared target + every own container that declares the member and whose
// type the CHECKER says is assignable to the receiver's (declared heritage is a subset of that).

// (a) structural: `Structural` never writes `implements Handler`, and IS in the envelope
export interface Handler { handle(msg: string): void; }
export class Declared implements Handler { handle(msg: string): void { void msg; } }
export class Structural { handle(msg: string): void { void msg; } }
export const literal = { handle(msg: string): void { void msg; } };
export function dispatch(h: Handler): void { h.handle("x"); }

// (b) a union receiver: BOTH constituents are declared targets, so the group is not unique
export class Alpha { run(): string { return "a"; } }
export class Beta  { run(n?: number): number { return n ?? 1; } }
export function viaUnion(x: Alpha | Beta): string | number { return x.run(); }

// (c) a property bound to a NAMED function: `helperHandle` is what runs
export function helperHandle(msg: string): void { void msg; }
export const propFn = { handle: helperHandle };
export function viaPropFn(): void { dispatch(propFn); }

// (d) a property-signature interface: the call is through a function value — `indirect`, named
//     `handle` (as written), never scored; `FnImpl#handle` is a nominal implementor the oracle
//     cannot name for this call, which is the TypeScript blind spot, stated
export interface FnHandler { handle: (msg: string) => void; }
export class FnImpl implements FnHandler { handle(msg: string): void { void msg; } }
export function dispatchFn(h: FnHandler): void { h.handle("y"); }

// (e) overloads: both arms spell `find(T)`; Tier B is the headline and is unaffected
export class Repo {
  find<T extends string>(id: T): string;
  find<T extends number>(id: T): number;
  find(id: string | number): string | number { return id; }
}
export function viaOverload(r: Repo): string { return r.find("a"); }
