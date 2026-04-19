---
name: WALL_L_SPR_DATA and WALL_SPR_DATA per-frame decomposition
description: 7-frame left/right wall sprites at $7DA4-$8177 and $8178-$854B; same pillar-style INTERLACE_BLIT format (4 cols x 35 rows, 140 bytes/frame, column-major)
type: project
---

The WALL_L_SPR_DATA_0..6 and WALL_SPR_DATA_0..6 frames are now carved out of the SPRITE_PIXEL_DATA blob:

- WALL_L_SPR_DATA: $7DA4-$8177, 7 frames x 140 bytes, consumed by REFRESH_LEFT_WALL via WALL_L_SPR_LO/HI[ZP_SPRITE_XREF].
- WALL_SPR_DATA: $8178-$854B, 7 frames x 140 bytes, consumed by REFRESH_RIGHT_WALL via WALL_SPR_LO/HI[ZP_SPRITE_XREF].

**Format:** Exactly the same as PILLAR_SPR_DATA — 4 columns x 35 rows column-major, rightmost column first, painted via INTERLACE_BLIT_P1/P2 into all three perspective bands (rows 72-106, 112-146, 152-186) simultaneously.

**Frame 0..3 vs 4..6 palette:** WALL_L frames 0-3 are green-dominant, frames 4-6 purple-dominant; the same pattern holds for WALL_SPR. Used to produce the left/right "tier-switch" color pulse at difficulty transitions.

**Remaining SPRITE_PIXEL_DATA residue:**
- SPRITE_PIXEL_DATA_RESIDUE_1 ($7AD4-$7DA3, 720 bytes): HIT_SPR_NEG (7 frames x $28) + FLOOR_SPR (11 frames x $28). These use DRAW_SPRITE_OPAQUE, not INTERLACE_BLIT, so the stride and format differ.
- SPRITE_PIXEL_DATA_RESIDUE_2 ($854C-$8BFF, 1716 bytes): PLAYER_SPR_IDLE/ACTIVE (10 frames x $4C, with pointer aliasing), HIT_SPR_POS (7 x $28), and grid-body tails.

**Renderer:** `.claude/scripts/render_wall_sprites.py` — uses the same `decode_column_major_sprite` + `render_sprite_to_hgr` helpers from `render_pillar_sprites.py`. Produces `images/wall_l_sprites.png` and `images/wall_sprites.png`.

**How to apply:** The column-major 4x35 INTERLACE_BLIT format is now reused by three sub-tables (PILLAR_SPR, WALL_L_SPR, WALL_SPR). Future pillar-style decompositions (if any appear in level-1 swappable banks) can reuse the same renderer template and frame-data pattern.
