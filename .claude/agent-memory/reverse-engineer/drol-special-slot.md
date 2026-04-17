---
name: Drol special-sprite slot
description: DRAW_ENTITIES phase 3 + SPECIAL_TICK/DRAW pair — bonus creature that kills 4 floor-enemies then falls for +500
type: project
---

The **"special" sprite slot** in Drol (DRAW_ENTITIES phase 3, tick at
$6ABA SPECIAL_TICK, draw at $6B39 SPECIAL_DRAW) is a bonus creature
that walks horizontally across the playfield, colliding with and
killing entries in the 4-slot floor-enemy table at $9B/$9F/$A3 (same
table ENEMY_C_DRAW and the beam subsystem target). After 4 kills it
enters drift mode ($AB = $FF), falling with a ladder-row pause
pattern. The player catches the drifting puff for +$0500 BCD.

ZP state (paired names with the DRAW_ENTITIES defines):
- $AB ZP_SPECIAL_STATE / ZP_SPECIAL_A: $00 inactive, positive active, $FF drift
- $AC/$AD ZP_SPECIAL_POS (16-bit): position cycle $003E..$035A
- $AE ZP_SPECIAL_ROW: screen row (ladder rows are $34/$5C/$84/$AC)
- $08 ZP_SPECIAL_HP: kills remaining before defeat (starts at 4)
- $B5 ZP_SPECIAL_SND_CTR: 12-step ascending-tone counter ($FF idle)
- $B6: second sound slot used by SPECIAL_DRAW (not yet named)

Data:
- $0218 SND_PITCH_TBL_SPECIAL (12 bytes) for SND_DELAY_UP clicks
- $021F is the pitch table for $B6 / SPECIAL_DRAW (guess:
  SND_PITCH_TBL_SPECIAL_B, used with SFX_TONE duration $08)

Why: this is the only entity slot in Drol that *kills* the floor
enemies by collision rather than hits them (contrast ENEMY_C_DRAW
which hits floor-enemies from the player side). The classic arcade
"helpful bonus" pattern.

How to apply: when RE'ing $6B39 SPECIAL_DRAW, expect two phases
gated on $AB: positive = body sprite draw + floor-enemy collision;
negative = puff draw + player-catch collision. The SMC pair at
$6BE9/$6BEA is rewritten by 7 ladder-step handlers at
$6C49..$6CDA to swap puff-draw targets.
