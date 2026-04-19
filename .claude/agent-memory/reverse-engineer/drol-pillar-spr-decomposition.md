---
name: PILLAR_SPR_DATA per-frame decomposition at $7700-$7AD3
description: 7 labeled pillar sprite frames carved out of the SPRITE_PIXEL_DATA HEX blob; format and renderer template established for remaining sub-tables
type: project
---

The first 980 bytes of SPRITE_PIXEL_DATA ([[$7700]]--[[$7AD3]]) is now decomposed into 7 labeled frames `PILLAR_SPR_DATA_0` through `PILLAR_SPR_DATA_6`.

**Format per frame:**
- 4 columns x 35 rows column-major (140 bytes = $8C)
- Bytes [0..$22] -> right-most painted screen column
- Bytes [$23..$45] -> column 1 left
- Bytes [$46..$68] -> column 2 left
- Bytes [$69..$8B] -> left-most painted column
- Each source byte paints into 3 perspective bands simultaneously (rows 72-106, 112-146, 152-186) via INTERLACE_BLIT_P1/P2
- Visible footprint: 28 pixels wide tri-strip

**Consumers:**
- `REFRESH_PILLARS` at `$62E2` (drol.bin) uses `PILLAR_SPR_LO/HI[ZP_SPRITE_XREF]` to pick a frame, then `INTERLACE_BLIT_P1/P2` broadcasts across 3 bands for each of 6 fixed world-Y landmark slots.

**Renderer:** `.claude/scripts/render_pillar_sprites.py` - paints each frame into band 0 of a mock HGR page and crops to tile; `.claude/scripts/render_interlace_blit.py:render_hgr_page` does the NTSC palette decode.  Output: `images/pillar_sprites.png` (7 frames side-by-side).

**How to apply:** This is the first of several sub-decompositions of the remaining `$7AD4`-`$8BFF` SPRITE_PIXEL_DATA blob.  Other per-frame targets with known W/H:
- HIT_SPR_NEG (7 frames x $28 bytes = W=7/H=5 via DRAW_SPRITE_OPAQUE, already rendered)
- FLOOR_SPR (11 frames x $28 bytes)
- WALL_L_SPR (7 frames x $8C bytes, same format as PILLAR_SPR via INTERLACE_BLIT)
- WALL_SPR (7 frames x $8C bytes, same format)
- PLAYER_SPR_IDLE / _ACTIVE (non-monotonic pointers — multiple slots share frames)
- HIT_SPR_POS (7 frames x $28 bytes, already rendered)

The 140-byte stride INTERLACE_BLIT format established here directly applies to the two WALL sprite tables.

**Gotcha:** `@ %def LABEL` on its own line terminates a noweb chunk.  Keep a single consolidated `@ %def ...` at the chunk end listing all sub-labels; never use one `@ %def` per label inside a multi-label chunk.
