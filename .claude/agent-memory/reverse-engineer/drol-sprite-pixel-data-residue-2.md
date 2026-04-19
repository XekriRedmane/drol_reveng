---
name: SPRITE_PIXEL_DATA_RESIDUE_2 decomposition complete
description: $854C-$8BFF decomposed into 9 IDLE + 9 ACTIVE + 7 HIT_SPR_POS + 5 PLAYER_GRID_SPR_A frames; IDLE/ACTIVE use W+1 width and per-frame leading zero pads
type: project
---

The final residue of [[SPRITE_PIXEL_DATA]] at [[$854C]]--[[$8BFF]] is
now decomposed frame by frame, ending the
[[SPRITE_PIXEL_DATA_RESIDUE_2]] era.

**Sub-tables:**
- PLAYER_SPR_IDLE_DATA_0..8 ($854C..$87F7) — 9 unique frames, $4C
  bytes each (19 rows x 4 bytes). Pointer table aliases [1]==[3] to
  $8598, so stance 4 and stance 6 share PLAYER_SPR_IDLE_DATA_1.
- PLAYER_SPR_ACTIVE_DATA_0..8 ($87F8..$8ABF) — 9 unique frames.
  Frames 0-1 are $4C bytes (19 rows), frames 2-8 are $50 bytes
  (20 rows). Pointer entry [1] aliases back to PLAYER_SPR_IDLE_DATA_8
  ($87AC).
- HIT_SPR_POS_DATA_0..6 ($8AC0..$8BD7) — 7 frames x $28 bytes
  (W=7 H=5, 8 bytes/row). Pair to HIT_SPR_NEG_DATA in RESIDUE_1.
- PLAYER_GRID_SPR_A_DATA_0..4 ($8BD8..$8BFF) — first 5 of 7 frames
  (8 bytes each). Frames 5..6 ($8C00/$8C08) live in the swappable
  level-data bank.

**Frame-size gotcha:** DRAW_SPRITE runs W+1=4 bytes/row for player
(not W=3). Many frames begin with a 4-byte leading zero row as
alignment padding; others end with a 4-byte trailing zero. This is
critical for per-frame decomposition — bytes between frames are NOT
uniform padding, they're part of the frame data.

**ACTIVE stride mystery:** Frames 0,1 = $4C bytes (19 rows), frames
2..8 = $50 bytes (20 rows). DRAW_PLAYER always sets H=$14 (20 rows)
on the active path, so frames 0,1 would run 1 row into the next
frame. Since the pointer table's live entries are [3..9] (= frames
2..8 in this layout), frames 0 and 1 are unused by runtime gameplay
— only present as residue from an earlier art pass.

**How to apply:**
- RESIDUE_2 is no longer a label — removed from @ %def.
- The label `SPRITE_PIXEL_DATA_RESIDUE_2` is gone; the sprite pixel
  data span $854C-$8BFF now has the per-frame labels above.
- Player sprite renderers already exist at
  `.claude/scripts/render_player_sprites.py` (idle + active) and
  `.claude/scripts/render_hit_sprites.py` (HIT_SPR_POS/NEG). No new
  renderer needed this round.
