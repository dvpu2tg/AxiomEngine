// t11 — the second envelope audit (issues #67, #68, #73, #74, #80). Expected rows are stated
// beside each construct and pinned by tests/test_oracle_typescript.py.

export class PlainBase { area(): number { return 1; } }
export class Labeled extends PlainBase { label = ''; }
export function inherited(l: Labeled): number { return l.area(); }     // (S2) -> PlainBase#area, unique

export interface Box<T> { get(): T }
export class NumBox { get(): number { return 1; } }
export function generic(b: Box<number>): number { return b.get(); }    // (S3) possible {NumBox#get}

export abstract class A5 { f(): number { return 0; } }
export abstract class B5 extends A5 { abstract override f(): number; }
export class C5 extends B5 { override f(): number { return 5; } }
export function abstractRedecl(b: B5): number { return b.f(); }        // (S5) possible {C5#f}, unique
export function mkC5(): C5 { return new C5(); }

export class Alpha { toString(): string { return 'a'; } }
export function libArm(x: Alpha | Date): string { return x.toString(); }   // (§3) boundary: a library arm runs

export class Repo { find(): number { return 1; } }
export class CachedRepo extends Repo { }
export function mkCached(): CachedRepo { return new CachedRepo(); }
export function viaInherited(r: Repo): number { return r.find(); }     // (§4) rta {Repo#find}: CachedRepo inherits it

export function boundFn<F, L extends unknown[], R>(fn: (f: F, ...a: L) => R, first: F): (...r: L) => R {
  return (...r: L) => fn(first, ...r);
}
export function headerTemplate(ctx: Ctx, n: number): number { return n; }
export class Ctx { header = boundFn(headerTemplate, this); }
export function page(ctx: Ctx): number { return ctx.header(1); }       // (#73) indirect, not <anon@N>

export class Deserializer { constructor(public app: Application) {} }
export class Application {
  deserializer = new Deserializer(this);                                // (#74) caller Application#constructor
  static registry = mkRegistry();                                       // (#74) caller Application#<clinit>
}
export function mkRegistry(): number { return 1; }

export class K { static make(): K { return new K(); } }
export class K2 extends K { static override make(): K2 { return new K2(); } }
export function statics(): K { return K.make(); }                       // (#80) possible {K#make} only

export class Bx<T> { set(v: T): void { void v; } }
export function unionSig(u: Bx<string> | Bx<number>): void { u.set(3 as never); }   // (#68 §2) one Bx#set(T)
