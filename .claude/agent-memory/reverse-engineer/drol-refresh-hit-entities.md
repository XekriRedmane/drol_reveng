---
name: Drol REFRESH_HIT_ENTITIES and the 12-slot hit-entity array
description: $6321 REFRESH_HIT_ENTITIES is the 5th playfield-refresh routine; uses DRAW_SPRITE_OPAQUE (not INTERLACE_BLIT) to redraw 12-slot hit-entity ($66/$72/$8D) walking sprites
type: project
---

`REFRESH_HIT_ENTITIES` at `$6321` is the fifth and last playfield-refresh routine in the game-engine-A tick chain (siblings: REFRESH_LEFT_WALL/RIGHT_WALL/FLOOR_LINES/PILLARS). It redraws the currently-active hit-entities — the 12-slot array at `ENTITY_HIT_STATE $8D` whose parallel Y (world-Y) and row (screen-row) attributes live at `ENTITY_HIT_Y $66` and `ENTITY_HIT_ROW $72`. Called per frame from PLAYER_TICK_IDLE and PLAYER_TICK_MOVE_LEFT after CLEAR_DRAW_PAGE zeros the draw page.

**Surprise: uses DRAW_SPRITE_OPAQUE, not INTERLACE_BLIT.** Unlike the three playfield-refresh siblings which use INTERLACE_BLIT_P1/P2 (3-band perspective replication), REFRESH_HIT_ENTITIES paints one band with DRAW_SPRITE_OPAQUE — the same opaque blitter used by HUD digit tiles. This is because the draw page was just zeroed; opaque STA is the correct primitive when there's nothing underneath to preserve. Adds a THIRD caller to DRAW_SPRITE_OPAQUE (previously only DISPLAY_UPDATE and DRAW_DIGIT).

**Facing-direction convention:** `ENTITY_HIT_STATE,X` positive selects `HIT_SPR_POS_LO/HI` pair at `$753B/$763B`; negative (bit 7 set) selects `HIT_SPR_NEG_LO/HI` at `$7507/$7607`. Both pair tables are indexed by `ZP_SPRITE_XREF $4C` (the 0..7 walking-frame index shared with other playfield-refresh routines). Tables live in the swappable level-data region.

**Sprite dimensions:** 7 bytes wide × 5 rows tall, at screen column `ENTITY_HIT_Y,X - ZP_PLAYER_Y` (skipped when delta<0 or delta>=$2F), screen row `ENTITY_HIT_ROW,X`.

**Loop structure:** The 4-byte prologue at $631D (DEX/BPL HIT_DRAW_BODY/RTS) is a shared re-entry target. Main entry at $6321 (LDX ZP_HIT_MAX) only executes the LDX once; after each body iteration the code JMPs back to $631D which decrements X and re-enters at HIT_DRAW_BODY=$6323 (skipping the LDX reload). Skip branches (BCC/BCS when entity is off-screen) also land at $631D, ensuring every miss still decrements.

**Parallel hit-entity record (slot X, bounded by ZP_HIT_MAX=$41):**
- `ENTITY_HIT_Y,X = $66,X` — world-Y position (read by INPUT_DO_ASCEND/DESCEND and REFRESH_HIT_ENTITIES)
- `ENTITY_HIT_ROW,X = $72,X` — screen row for draw
- `ENTITY_HIT_STATE,X = $8D,X` — non-zero = active, bit 7 = direction

**How to apply:** When RE'ing code that touches `$66,X`, `$72,X`, or `$8D,X` with X<=$41 ($66,X is now ENTITY_HIT_Y), consult this parallel-array layout. The 12-slot hit-entity system is distinct from the 3 moving-hazard slots ($D4/$DC/$E0) AND from the 20-slot rescue-child ENTITY_ACTIVE ($03A8) system. All three systems coexist.
