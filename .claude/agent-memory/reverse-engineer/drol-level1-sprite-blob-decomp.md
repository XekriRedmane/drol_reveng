---
name: Level-1 $8CF5-$B4B0 sprite-data blob decomposition
description: 10172-byte monolithic HEX blob decomposed into ~200 labeled sub-chunks covering FLOOR_ENEMY, SPECIAL_BODY, SPECIAL_GRID, COMPANION, HUD_STRIP, ENTITY_GRID, RESCUE, PROJ_SPR, SPECIAL_PUFF, SPRITE_TABLE_C, SCROLL_EDGE sprite families
type: project
---

The level-1 $8CF5-$B4B0 span is now decomposed into per-frame sprite-data
labels, ending the "Remaining raw bytes $8CF5-$BDFF" era.

**Sub-table map (all 7 frames per family unless noted):**
- FLOOR_ENEMY_SPR_S3..S0_DATA ($8CF5..$8E0C): 4 slots x 7 x 10 bytes, W=1 H=5
- SPECIAL_BODY_POSE0..3_DATA ($8E0D..$9D5C): 4 poses x 7 x 140 bytes, W=6 H=$14
- SPECIAL_GRID_SPR_A/B_DATA ($9D5D..$9DB0): 2 x 7 x 6 bytes, W=1 H=3
- COMPANION_NEG/POS_POSE1..3_DATA ($9DB1..$A2F0): 6 tables x 7 x 32 bytes, W=3 H=8
- COMPANION_GRID_SPR_DATA_0..6 ($A2F1..$A30C): 7 x 4 bytes (frame 7 aliases HUD_STRIP_SRC)
- HUD_STRIP_SRC_DATA ($A30D, 112 bytes): 16 cols x 7 bytes/col
- ENTITY_GRID_SPR_DATA_0..6 ($A37D..$A3C2): 7 x 10 bytes
- RESCUE_SPR_NEG/POS_END/MID_DATA ($A3C3..$AF92): 4 tables x 7 x (104 or 112) bytes
- PROJ_SPR_R_DATA_0..6 ($AF93..$AFD1) + _7_RESIDUE ($AFD2, 1 byte)
- SPRITE_POINTER_TABLES_TAIL ($AFD3..$B0FF, 301 bytes): pointer-table EQU storage (PROJ_SPR_L_LO/HI, SPECIAL_PUFF_LO/HI, SPRITE_TABLE_C_LO/HI, SCROLL_EDGE_L/R_SPR_LO/HI, DIGIT_TILE_LO/HI, SPRITE_TABLE_LO/HI)
- PROJ_SPR_L_DATA_0..6 ($B100..$B13E): 7 x 9 bytes
- SPECIAL_PUFF_DATA_0..6 ($B13F..$B34B): 7 x 75 bytes, W=4 H=$0F
- SPRITE_TABLE_C_DATA_0..6 ($B34C..$B432): 7 x 33 bytes, W=2 H=$0B
- SCROLL_EDGE_L/R_SPR_DATA_0..6 ($B433..$B4B0): 2 x 7 x 9 bytes

**Overlap quirks:**
- COMPANION_GRID_SPR[7] ($A30D) overlaps HUD_STRIP_SRC first 4 bytes.
- PROJ_SPR_R[7] ($AFD2) is 9 bytes but only the lead byte ($AFD2) is
  unique; $AFD3-$AFDA overlap the PROJ_SPR_L_LO / SPECIAL_PUFF_LO
  pointer tables. Frame 7 never drawn (PROJ_FRAME_IDX 0..6).
- PROJ_SPR_L[7] = $B13F = SPECIAL_PUFF_DATA_0. Frame 7 never drawn.

**Format quirk:** DRAW_SPRITE runs (W+1) bytes per row, H rows. So
W=1 H=5 is 10 bytes (not 5); W=6 H=$14 is 140 bytes (7 bytes/row x 20).

**Why left pointer-tables as raw HEX:** Promoting PROJ_SPR_L_LO,
SPECIAL_PUFF_LO, SPRITE_TABLE_C_LO, SCROLL_EDGE_L/R_SPR_LO,
DIGIT_TILE_LO, SPRITE_TABLE_LO/HI from EQUs to ORG labels would have
required removing all existing EQUs and updating every reference.
Kept as EQUs, labelled as SPRITE_POINTER_TABLES_TAIL span (301 bytes).

**Blob size was misreported:** The old comment said "12555 bytes
$8CF5-$BDFF" but the actual blob was 10172 bytes $8CF5-$B4B0. Beyond
$B4B0 is DIGIT_TILE_DATA (already decomposed).

**How to apply:** When rendering or inspecting any of these sprite
families, use the per-frame labels (e.g. `SPECIAL_BODY_POSE0_DATA_3`
for pose-0 frame 3) rather than raw addresses. Render scripts in
`.claude/scripts/render_sprite_tables.py` already decode all families.
