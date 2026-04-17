---
name: Drol floor-line refresh
description: REFRESH_FLOOR_LINES at $62CA paints 4 reserved hi-res rows (67/107/147/187) via FLOOR_LINES_P1/P2 row painters; animation table is all-zero in all 4 shipped levels
type: project
---

REFRESH_FLOOR_LINES at $62CA is the fourth playfield-refresh callee in PLAYER_TICK_IDLE, sandwiched between REFRESH_RIGHT_WALL and REFRESH_PILLARS. Unlike the other three it does NOT call INTERLACE_BLIT/INTERLACE_RESTORE — instead it tail-calls FLOOR_LINES_P1 ($08C8) or FLOOR_LINES_P2 ($08DF), each of which broadcasts a 40-byte source row (from ZP_BLIT_SRC) onto four evenly-spaced hi-res rows: row 67 ($2C28/$4C28), row 107 ($2EA8/$4EA8), row 147 ($2D50/$4D50), row 187 ($2FD0/$4FD0). Source is 12-frame animation table at FLOOR_SPR_LO/HI ($750E/$760E) indexed by ZP_WALK_FRAME ($4B).

**Why:** These 4 rows are the ONLY bytes in all of drol.bin written to by FLOOR_LINES_P1/P2 — no other code touches them. The 480-byte source table at $7BEC..$7DCB is all-zero in all 4 shipped Drol levels, so the routine effectively clears these 4 reserved floor-reference rows every frame (a per-frame spot-clean). The animation-indexed hook is a generic level-data extension point never populated.

**How to apply:** When analyzing the floor/HUD/playfield refresh pipeline, remember that the 4 floor reference rows (67/107/147/187) get repainted every frame by this routine, which may erase transient effects from prior frames. If any future routine paints to those exact row addresses, its output will be immediately overwritten. The 4 rows sit one row above each INTERLACE_BLIT perspective band (bands start 72/112/152) plus one near-bottom row (187) — likely visible as horizontal reference stripes in the perspective floor.
