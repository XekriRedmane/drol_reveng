---
name: Drol DIGIT_TILE_DATA at $B4B1
description: Ten HUD digit glyphs (W=1, H=6, 12 bytes each) in level1.bin; pointer tables DIGIT_TILE_LO/HI one page below SPRITE_TABLE_LO/HI
type: project
---

DIGIT_TILE_DATA ($B4B1-$B528, 120 bytes) holds the ten HUD digit
glyphs 0..9 used by POST_FRAME (score) and DISPLAY_UPDATE (timer).
Each glyph is 12 bytes = 2 bytes-per-row (W=1) * 6 rows (H=6),
blitted via DRAW_SPRITE_OPAQUE so the glyph overwrites the HUD strip's
$55/$2A dither.

**Why:** Raw hex inside the `level1 pages 8C-BD` blob had no symbolic
identity, so readers had to guess why certain byte ranges in level1 were
referenced by DIGIT_TILE_LO/HI pointers at $AFF6/$B076 in drol.bin.

**How to apply:**
- Digit i resolves to $B4B1 + i*12; the pointer tables are at
  $AFF6 (LO) and $B076 (HI) which are in the main SPRITE_TABLE_LO/HI
  pointer-bank family (one 'page' below $B000/$B080 base).
- Data ends at $B528 - BEAM_SPR starts at $B529, so be careful if
  extending the table.
- Bytes have the high bit set to select the blue/orange palette; most
  are $8A/$82/$C0..$D5 which renders as blue digits on the HUD dither.
- Renderer: .claude/scripts/render_digit_tiles.py; PNG at
  images/digit_tiles.png.
