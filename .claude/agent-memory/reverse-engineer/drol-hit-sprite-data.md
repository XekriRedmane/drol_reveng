---
name: HIT_SPR_POS/NEG sprite data layout and locations
description: 7-frame hit-entity sprites (W=7/H=5, 40-byte stride); POS lives entirely in drol.bin $8AC0-$8BD7; NEG frame 0 in swappable $7AD4 and frames 1-6 in persistent $7AFC-$7BEB
type: project
---

HIT_SPR_POS_LO/HI ($7524/$7624) and HIT_SPR_NEG_LO/HI ($750E/$760E) are the pointer tables consumed by REFRESH_HIT_ENTITIES. Each points to a 7-frame strip of W=7 H=5 sprites, 40 bytes each ($28 stride).

**Location split for HIT_SPR_NEG:**
- Frame 0 at $7AD4 (tail of the swappable $7500-$7AFF level-1 bank)
- Frames 1-6 at $7AFC-$7BEB (straddle into the persistent $7B00-$8BFF bank)

**HIT_SPR_POS** at $8AC0-$8BD7 is entirely in persistent memory.

**Why:** The split across swap/persistent boundaries looks like deliberate packing — the first frame can be level-specific (only 40 bytes needed in level swap) while frames 1-6 are shared across all levels.

**How to apply:** When rendering, use drol.bin for both tables — drol.bin has the full set. level1.bin only carries HIT_SPR_NEG frame 0 + 4 bytes into frame 1. The render script is at `.claude/scripts/render_hit_sprites.py`.

The prose in `<<refresh hit entities>>` previously claimed "seven 7-pixel cells = 49 px"; corrected to 8 bytes per row (56 px) because DRAW_SPRITE_OPAQUE runs W+1 inner iterations, consistent with the 40-byte frame stride.
