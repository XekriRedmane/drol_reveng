---
name: Drol INTERLACE_BLIT routines
description: INTERLACE_BLIT_P1/P2 at $054E/$070B are 3-band perspective sprite blitters (streaming version of INTERLACE_FILL)
type: project
---

`INTERLACE_BLIT_P1` at `$054E` (445 bytes) and `INTERLACE_BLIT_P2` at
`$070B` (445 bytes) are the streaming analogue of
`INTERLACE_FILL_P1/P2`: instead of broadcasting constant A, each source
byte from `(ZP_BLIT_SRC),Y` paints the same relative row in all three
perspective bands (rows 72-106, 112-146, 152-186).

- Source layout: column-major flat stream, 35 bytes per column, rightmost
  column first.  Y walks forward across the whole call (never reset
  between columns) so column N's bytes sit at `(ZP_BLIT_SRC)+N*35`.
- X walks from `ZP_BLIT_X_START` ($59, inclusive) down to
  `ZP_BLIT_X_END` ($58, exclusive).
- Per-column: 35 unrolled `LDA (src),Y / STA band0,X / STA band1,X /
  STA band2,X / INY` groups.
- Prologue guard: `CPX #$28` — if X off-screen (>=40), skip paint but
  advance Y by 35 (keeps source/column alignment).

Why: Playfield sprite blitter for the Drol 3-floor perspective playfield.
Three caller sites at $625F / $62C6 / $6317 all use the `BIT $00; BMI`
page-flag gate to select P1 or P2.  Sprite data referenced via
pointer tables at $7500/$7600 (lo/hi split).  Typical sprite sizes are
1 col (40 bytes), 2 cols (76 bytes), 4 cols (140 bytes).

How to apply: When analyzing code that sets $FE/$FF then JSRs into the
$054E/$070B area, it's a 3-band sprite blit — expect the caller to
first JSR `INTERLACE_RESTORE_P{1,2}` (to clear the text strip) then
JSR `INTERLACE_BLIT_P{1,2}` (to paint the new sprite).  The paired
helpers reuse ZP `$2B/$2C` as text-strip column bounds and `$58/$59`
as playfield column bounds.
