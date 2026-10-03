// t07 — A PATH ALIAS. `@/…` is mapped by the tsconfig's `paths` to `./src/…`. A tool that is not
// given the mapping cannot resolve this import, types nothing through it, and loses every call
// below — which is what happened to every import-resolving tool on type-graphql (#14). The
// synthesised tsconfig the tools receive must carry the mapping, re-rooted.

import { Config } from '@/t05a-core';
import { helper } from '@/t03-functions';

export function viaAlias(): string { return new Config().name(); }
export function viaAliasFn(): number { return helper(41); }
