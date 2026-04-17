---
name: Drol hi-res framebuffer library at $0400-$0C97
description: $0400-$0C97 region is a 2200-byte library of interlaced hi-res paint/copy routines for both display pages, not game logic
type: project
---

The $0400-$0C97 region of drol.bin — which was originally stubbed as
"entity management, physics, rendering" — is actually a 2200-byte
library of hi-res framebuffer routines, NOT game logic.  It contains:

- `CLEAR_PAGE1` ($0400-$04A6) / `CLEAR_PAGE2` ($04A7-$054D): paired
  screen-clear routines for hi-res pages 1 ($2000-$3FFF) and 2
  ($4000-$5FFF).  Called from player-tick code ($61E8/$61EC).
- `STRIPE_COPY_PAGE1` ($054E-$070A) / `STRIPE_COPY_PAGE2` ($070B-$08C7):
  copy from `($FE),Y` into hi-res row-decimated stripes.  Column range
  `$58..$59`.  Called from $62XX.
- Small row painters at $08C8, $08DF, $08F6, $097A.
- `INTERLACE_RESTORE_P1` ($09FE-$0B4A) / `INTERLACE_RESTORE_P2`
  ($0B4B-$0C97): text-row restore from $0300,X buffer.
- `INTERLACE_FILL_P1` ($0A0F) / `INTERLACE_FILL_P2` ($0B5C): core
  helpers that fan-out a single byte to 60+ interlaced hi-res
  positions.  Called from within CLEAR_PAGE1/2.

Why: originally suspected to contain entity routines and projectile
logic.  It's actually display-list code used for level transitions
and screen refreshes.  RESCUE_DRAW ($0C98) is the exception — its
placement immediately after the library suggests it was the "glue"
between gameplay code and the blit library.

How to apply: when carving this region, expect pure display code
with no game-state reads.  The 33-way STA fanouts are a deliberate
decimation pattern that paints every ~2-row interlace group per
pass — fast enough to clear a hi-res page in ~$28 outer iterations.
Sibling routines always twin page-1/page-2 ($2XXX/$4XXX bases).
