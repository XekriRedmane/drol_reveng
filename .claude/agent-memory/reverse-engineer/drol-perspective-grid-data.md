---
name: Drol perspective-grid lookup tables ($188A-$1CED)
description: 1124-byte data region split into 7 labeled sub-tables (FLOOR_BASE_ROW, PERSPECTIVE_XOFF_HI/LO, PROJ_FRAME_IDX, PROJ_SCREEN_COL, FLOOR_ENEMY_SPAWN_SCHED + 5-byte pre-pad)
type: project
---

The `$188A-$1CED` region in drol.bin holds 7 back-to-back lookup tables (not "game logic" — the old chunk name was placeholder). All are persistent (tracks 1-2) and drive the perspective-grid rendering:

| Address | Label | Size | Role |
|---|---|---|---|
| $188A | FLOOR_BASE_ROW_PAD | 5 | Pad (indices 0..4 never read) |
| $188F | FLOOR_BASE_ROW | 256 | Floor-column -> base row (plateaus of 7) |
| $198F | PERSPECTIVE_XOFF_HI | 256 | Y-to-X transform, high byte |
| $1A8F | PERSPECTIVE_XOFF_LO | 256 | Y-to-X transform, low byte |
| $1B8F | PROJ_FRAME_IDX | 165 | idx mod 7 |
| $1C34 | PROJ_SCREEN_COL | 132 | (7*idx+3)/25 |
| $1CB8 | FLOOR_ENEMY_SPAWN_SCHED | 54 | ZP_PLAYER_COL -> spawn row seed |

**Why:** DRAW_ENTITIES phases 3/4/5, RESCUE_DRAW meet-player, ENEMY_B/C_DRAW drift-mode tails, projectile hazard, and FLOOR_ENEMY_ADVANCE all share these tables. Previously a single 1124-byte HEX blob.

**How to apply:** When an address falls in $188A-$1CED, look up which table it's inside. The five EQUs for these addresses have been removed — the labels live in the data chunks.

**Pitfall caught:** Noweb `<<chunk>>` inside asm comments gets expanded — had to rewrite "defined as labels in <<x>>" to avoid the tangler inserting the chunk body into the comment. CLAUDE.md forbids this.
