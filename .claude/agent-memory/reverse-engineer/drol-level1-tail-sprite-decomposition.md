---
name: Level-1 tail sprite data decomposition ($B5FD-$BD9F)
description: 10-way split of the $B5FD-$BD9F HEX blob into labeled sprite-data sub-chunks driven by pointer tables
type: project
---

The $B5FD-$BD9F tail of the level-1 swappable region is now split
into 10 labeled sub-chunks (ATTRACT_SPR_0_DATA, ATTRACT_SPR_1_DATA,
EXTRA_LIFE_SPR_DATA, SPRITE_TABLE_A_BODY_DATA,
SPRITE_TABLE_A_STEP1_DATA, SPRITE_TABLE_A_FEET_DATA,
SPRITE_TABLE_A_STEP2_DATA, SPRITE_TABLE_B_DATA,
BRODERBUND_LOGO_SPR_DATA, LEVEL1_TAIL_RESIDUE).

**Why:** Previous rounds established the pointer-table EQUs
(SPRITE_TABLE_A_BODY_LO/HI at $B009/$B089, SPRITE_TABLE_B_LO/HI at
$B025/$B0A5, ATTRACT_SPR_LO/HI at $B006/$B086, etc.) but the
1955-byte pixel-data target region they pointed into remained a
single anonymous HEX blob. The sprite dimensions in ENEMY_A_DRAW /
ENEMY_B_DRAW / ATTRACT_ANIM_4 / LIFE_LOST_HANDLER fix all
boundaries exactly.

**How to apply:** The drol target still declares EXTRA_LIFE_SPR and
BRODERBUND_LOGO_SPR as cross-target EQUs at their fixed addresses
($B67D / $BCF1); the level1 target labels are suffixed with `_DATA`
to avoid `@ %def` collisions. Frame layouts:
- A_BODY: 7 frames x 76 bytes (4 bytes/row x 19 rows)
- A_STEP1/STEP2: 7 frames x 16 bytes (4 bytes/row x 4 rows)
- A_FEET: 7 frames x 12 bytes (4 bytes/row x 3 rows)
- B: 7 frames x 102 bytes (6 bytes/row x 17 rows)
- ATTRACT_SPR_0: 13 bytes/row x 8 rows (W=12)
- ATTRACT_SPR_1: 3 bytes/row x 8 rows (W=2)
- EXTRA_LIFE_SPR: 7 bytes/row x 14 rows (W=6)
- BRODERBUND_LOGO_SPR: 19 bytes/row x 8 rows (W=18)

LEVEL1_TAIL_RESIDUE ($BD89-$BD9F, 23 bytes) has no live consumer;
bytes disassemble to a dangling code fragment (TSX/DEY/BNE), likely
pre-release leftover.
