---
name: Drol EXTRA_LIFE_SPR at $B67D
description: LIFE_LOST_HANDLER's hardcoded extra-life glyph sprite in level-1 swappable data; lives right after ATTRACT_SPR[1]
type: project
---

$B67D is the extra-life glyph sprite drawn by LIFE_LOST_HANDLER once per remaining ZP_EXTRA_LIVES during the game-over animation. Hardcoded `LDA #$7D / STA SPRITE_PTR_LO / LDA #$B6 / STA SPRITE_PTR_HI` (now using `#<EXTRA_LIFE_SPR` / `#>EXTRA_LIFE_SPR`).

**Why:** The sprite is a third consumer of level-1's $B5xx-$B6xx sprite block (after ATTRACT_SPR2 and ATTRACT_SPR), but it's NOT in the pointer tables at $B002/$B006/$B082/$B086 — it's directly referenced by a pair of immediate loads in LIFE_LOST_HANDLER. Lives at $B665+$18=$B67D (right after ATTRACT_SPR[1]'s 24-byte body).

**How to apply:**
- Dimensions: W=6, H=14 (ZP_SPRITE_W=$06, ZP_SPRITE_H=$0E in the caller); bytes/row = W+1 = 7; total 98 bytes.
- Rendered in `images/extra_life_spr.png` via `.claude/scripts/render_extra_life_spr.py`.
- Render shows the familiar 3-column stripe pattern used by DROL-style character glyphs.
- The EQU EXTRA_LIFE_SPR lives in `<<life lost handler defines>>` and is exported via `@ %def EXTRA_LIFE_SPR` at the end of that chunk.
