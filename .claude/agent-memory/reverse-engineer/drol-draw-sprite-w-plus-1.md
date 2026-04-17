---
name: DRAW_SPRITE ZP_SPRITE_W is W-1 convention
description: ZP_SPRITE_W parameter for DRAW_SPRITE is one less than actual bytes per row (inner BPL loop runs W+1 iterations)
type: project
---

ZP_SPRITE_W ($56) passed to DRAW_SPRITE ($656F) and DRAW_SPRITE_PLAYFIELD
is **one less than the actual bytes per row**. The inner byte loop stores W
into ZP_SPRITE_ROW_REMAIN then runs:

```
    ... body ...
    DEC ZP_SPRITE_ROW_REMAIN
    BPL .col_loop
```

BPL branches while counter is >=0, so it runs W, W-1, ..., 1, 0 — that's
W+1 iterations, i.e. the sprite occupies W+1 bytes per row.

Verified across every sprite family by pointer-table stride arithmetic:
- player idle (W=3): 4 bytes/row x $13 rows = 76B = delta between adjacent pointers
- SPECIAL body (W=6): 7 bytes/row x $14 rows = 140B = $8E99-$8E0D
- enemy-A body (W=3): 4 bytes/row x $13 rows = 76B = delta $4C
- enemy-B body (W=5): 6 bytes/row x $11 rows = 102B = delta $66
- projectiles (W=2): 3 bytes/row x 3 rows = 9B = delta $09
- all others match

**Why:** This matters whenever decoding sprite bytes into pixels or
computing pointer-table strides. Using width_bytes=W produces garbage
output (off-by-one-column noise across all rows).

**How to apply:** For any sprite render or size check that involves
ZP_SPRITE_W, use (W+1) for bytes per row. The `render_sprite_lib.py`
decoder takes the W parameter and internally does `bytes_per_row = W + 1`.
