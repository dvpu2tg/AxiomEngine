// t02 — STRUCTURAL TYPING. The half of TypeScript that has no Java analogue: an object literal
// satisfies an interface WITHOUT naming it, so a sound dispatch envelope would be "every type in
// the program with a compatible member". The benchmark's `possible` is the DECLARED-HERITAGE
// envelope instead — see typescript/oracle/ts-ground-truth.ts — which means this family is where
// the oracle is knowingly an UNDER-approximation, and the file exists to make that visible rather
// than to hide it.

export interface Handler {
  handle(msg: string): string;
}

// declares the interface: inside the heritage envelope
export class LoudHandler implements Handler {
  handle(msg: string): string { return msg.toUpperCase(); }
}

// does NOT declare it, and is assignable anyway: OUTSIDE the heritage envelope, and reachable
export const quietHandler = {
  handle(msg: string): string { return msg.toLowerCase(); },
};

export function dispatch(h: Handler, msg: string): string { return h.handle(msg); }

export function viaDeclared(): string { return dispatch(new LoudHandler(), 'x'); }
export function viaStructural(): string { return dispatch(quietHandler, 'x'); }

// An INLINE object literal, passed straight to a parameter and bound to no name. Nothing in the
// syntax names it, so the oracle asks the checker what it is being used AS — the contextual type —
// and keys it `$obj:Handler@<line>`, the same way the Java oracle keys an anonymous class by its
// supertype. Without that it is an opaque line number no tool can match and no reader can interpret.
export function viaInline(): string {
  return dispatch({ handle: (m: string) => m.trim() }, 'x');
}
