---
name: Drol playfield-refresh wall/pillar routines
description: Three per-frame playfield-edge refresh routines at $61F0/$626A/$62E2 paint wall/pillar sprites via INTERLACE_RESTORE+BLIT and update HUD_LIVES_COL/HUD_SCORE_COL
type: project
---

Three routines inside `<<game engine A>>` call `INTERLACE_BLIT_P1/P2`:

- `REFRESH_RIGHT_WALL` ($61F0, 122 bytes) --- fires when `ZP_PLAYER_Y`
  near `$EF` (right edge of world).  Writes `HUD_LIVES_COL` ($65A7).
  Sprite from `WALL_SPR_LO/HI` = $7520/$7620 indexed by ZP $4C.
- `REFRESH_LEFT_WALL` ($626A, 96 bytes) --- mirror for left edge when
  `ZP_PLAYER_Y <= $11`.  Writes `HUD_SCORE_COL` ($65AB).  Sprite
  from `WALL_L_SPR_LO/HI` = $7519/$7619.
- `REFRESH_PILLARS` ($62E2, 59 bytes) --- 6-slot loop over ZP $60..$65
  (fixed world-Y landmark positions), paints 4-column pillar sprite
  from `PILLAR_SPR_LO/HI` = $7500/$7600.  Does NOT call
  `INTERLACE_RESTORE`; relies on earlier `CLEAR_DRAW_PAGE` pass.

**Why:** This is the last HEX blob tie-up for the playfield-refresh
subsystem.  These three routines + `CLEAR_DRAW_PAGE` + text-row
dispatch form the per-frame "clear + repaint playfield edges" chain.

**How to apply:** When RE'ing movement-tick handlers or HUD column
bounds, these refresh routines are where `HUD_SCORE_COL`/
`HUD_LIVES_COL` get their runtime updates.  The wall sprites and
pillar sprites live in `$7500-$7B9C` (level-swappable).  Frames $02-$07
of each table are the walking-animation cycle; frame $07 of the
PILLAR table crosses a stride boundary and decodes as garbage when
rendered as 4-column (suggests 1-column sprite variant).  ZP $60..$65
is never written by any code in drol.bin or level1.bin --- the 6-slot
pillar loop is effectively a no-op in the game's current
configuration.
