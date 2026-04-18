---
name: Drol player-tick handlers + CLEAR_DRAW_PAGE
description: PLAYER_TICK_MOVE_LEFT/IDLE/MOVE_RIGHT at $614B/$6184/$619A + CLEAR_DRAW_PAGE at $61E4; 7-step sub-frame pacing via ZP_SPRITE_XREF
type: project
---

Player-tick handlers carved out of the old `<<game engine A prologue>>` HEX blob (165 bytes at $614B-$61EF, 2026-04-17).

**Entry points called by PLAYER_MOVE_TICK ($64CB):**
- `PLAYER_TICK_MOVE_LEFT` ($614B): Y < $01 clamp -> JMP PLAYER_TICK_IDLE; else 7-step pacing cycle decrements ZP_PLAYER_Y on 4 of 7 states, advances ZP_WALK_FRAME (+2, mod 10) and ZP_SPRITE_XREF (+2 with $FE/$FF wrap seeds), then falls through into PLAYER_TICK_IDLE.
- `PLAYER_TICK_IDLE` ($6184): canonical 7-routine tick chain - CLEAR_DRAW_PAGE, TEXT_ROW_DISPATCH, REFRESH_LEFT_WALL, REFRESH_RIGHT_WALL, REFRESH_FLOOR_LINES, REFRESH_PILLARS, REFRESH_HIT_ENTITIES, RTS.
- `PLAYER_TICK_MOVE_RIGHT` ($619A): Y >= $D7 clamp -> jump to tick; else INC ZP_PLAYER_Y on 4 of 7 pacing states, advance ZP_WALK_FRAME (-2) and ZP_SPRITE_XREF (-2 with $07/$08 wrap seeds); inline tick chain SWAPS the walls (right before left) then `JMP PLAYER_IDLE_TICK_TAIL` ($6190) to rejoin IDLE's FLOOR_LINES onward.

**Sub-frame pacing (ZP_SPRITE_XREF dual-use):** ZP $4C is both the walking-sprite index (0..7) used by REFRESH_HIT_ENTITIES and a 7-step pacing counter for horizontal motion. Seeded to $02 by INIT_LEVEL_STATE.
- Left-walk cycle: {2,4,6,1,3,5,0}; Y decrements on {2,3,5,6}.
- Right-walk cycle: {0,5,3,1,6,4,2}; Y increments on {4,5,0,1}.
- Net: horizontal motion paced at 4/7 of frame rate.

**Why:** Understanding this carve completes the mainline per-frame tick chain — every routine called from MAIN_LOOP via PLAYER_MOVE_TICK is now RE'd with named labels.

**How to apply:** When tracing frame dispatch, the order is MAIN_LOOP -> PLAYER_MOVE_TICK -> PLAYER_TICK_* -> the 7 refresh routines. IDLE paints walls LEFT/RIGHT; MOVE_RIGHT reverses them (RIGHT/LEFT) for painter's-algorithm trailing-overwrite.

**CLEAR_DRAW_PAGE ($61E4):** 12-byte page-flag-gated wrapper — `BIT ZP_PAGE_FLAG; BMI .page2; JSR CLEAR_PAGE1; RTS; .page2: JSR CLEAR_PAGE2; RTS`. Called once per frame to zero the hidden hi-res page.

**PLAYER_IDLE_TICK_TAIL = $6190:** EQU alias for the REFRESH_FLOOR_LINES call inside PLAYER_TICK_IDLE; the target of the JMP at $61E1 in PLAYER_TICK_MOVE_RIGHT.
