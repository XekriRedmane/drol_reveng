---
name: Drol top-center HUD strip painter
description: $08F6/$097A PAINT_HUD_STRIP_P1/P2 paint 16-col x 31-row HUD decoration from HUD_STRIP_SRC ($A30D) via $636C TEXT_ROW_DISPATCH
type: project
---

`PAINT_HUD_STRIP_P1` at `$08F6` and its page-2 twin `PAINT_HUD_STRIP_P2`
at `$097A` paint a 16-column x 31-row decoration at hi-res columns
12..27, rows 1..31 (row 0 deliberately skipped). Each routine reads
112 bytes from `HUD_STRIP_SRC = $A30D..$A37C` in swappable level-data
region, expanded as:

- b0 -> rows 1..7 (7 identical rows)
- b1 -> row 8
- b2 -> rows 9..15
- b3 -> row 16
- b4 -> rows 17..23
- b5 -> row 24
- b6 -> rows 25..31

Per column: 7 fetches, 7 INYs. X runs $0F..$00 (right-to-left column
order); Y runs monotonically $00..$6F across the outer loop (not reset
per column). 16 iterations × 7 Y-steps = 112 source bytes.

Dispatched by `TEXT_ROW_DISPATCH = $636C`: 12-byte BIT-gated wrapper
(`BIT ZP_PAGE_FLAG / BMI page2 / JSR P1 / RTS / JSR P2 / RTS`). Called
once per frame from each of the three `PLAYER_TICK_*` movement handlers,
after `CLEAR_DRAW_PAGE` and before the playfield-refresh chain.

**Role in frame pipeline:** Second step in the tick chain
`CLEAR_DRAW_PAGE -> TEXT_ROW_DISPATCH -> REFRESH_LEFT_WALL ->
REFRESH_RIGHT_WALL -> REFRESH_FLOOR_LINES -> REFRESH_PILLARS ->
REFRESH_HIT_ENTITIES`. The HUD strip is repainted every frame onto
whichever hi-res page is the draw page.

**Source data is per-level:** `HUD_STRIP_SRC` lives in the swappable
$8C00-$BDFF region, so the top HUD decoration is level-specific.
Rendered in images/hud_icon_a30d.png (render script
.claude/scripts/render_a30d_icon.py).

**How to apply:** When RE'ing other routines that reference `$A30D` or
the $A30D-$A37C range, this is the only writer/reader. When RE'ing the
per-level sprite sheet, this 112-byte strip is the top-center decoration.
