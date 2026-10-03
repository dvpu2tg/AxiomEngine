// t05 — MODULES AND NAME COLLISION. Two modules declaring the same class name. A resolver keyed on
// the simple name alone answers one of them and cannot say which; the canonical container is
// `<module>:<Declaration>`, so the two are distinct and a tool that reports its file can be placed.

import { Config as CoreConfig } from './t05a-core.js';
import { Config as UtilConfig } from './t05b-util.js';

export function viaCore(): string { return new CoreConfig().name(); }
export function viaUtil(): string { return new UtilConfig().name(); }
