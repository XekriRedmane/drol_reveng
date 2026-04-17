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

ZP state:
- $AB ZP_SPECIAL_STATE / ZP_SPECIAL_A: $00 inactive, positive active, $FF drift
- $AC/$AD ZP_SPECIAL_POS (16-bit): position cycle $003E..$035A (also
  aliased as ZP_SPECIAL_X/Y in DRAW_ENTITIES phase 3 defines, where
  it's indexed as separate bytes)
- $AE ZP_SPECIAL_ROW: screen row anchor (ladder rows are $34/$5C/$84/$AC)
- $08 ZP_SPECIAL_HP: kills remaining before defeat (starts at 4)
- $B5 ZP_SPECIAL_SND_CTR: 12-step ascending-tone counter ($FF idle)
- $B6 ZP_SPECIAL_SND_CTR_B: 4-step defeat/catch jingle counter
- $AF/$B0 ZP_SCREEN_X / ZP_SCREEN_X_HI: scratch for perspective transform

Data:
- $0218 SND_PITCH_TBL_SPECIAL (12 bytes) for SND_DELAY_UP clicks
- $021F SND_PITCH_TBL_SPECIAL_B (4+ bytes) for SFX_TONE clicks ($B6)
- $AFDA/$B05A SPECIAL_PUFF_LO/HI — drift puff, Y-indexed
- $755B/$765B SPECIAL_PEEK_LO/HI — inactive-phase small marker sprite
- $7578..$758D / $7678..$768D — 4 level-data walk-cycle body sprites
  at offsets {0, 7, 14, 21}

Walk-cycle SMC dispatch (the 6 body-step handlers at $6C3F/6C59/6C73/
6C8D/6CA7/6CC1 = SPECIAL_BODY_STEP1..6):
- Each handler is 26 bytes: LDA #low(next); STA SMC_SPECIAL_BODY_LO;
  LDA #high; STA SMC_SPECIAL_BODY_HI; LDA pose,Y; STA SMC_DS_SRC_LO;
  LDA pose+$100,Y; STA SMC_DS_SRC_HI; JSR DRAW_SPRITE; RTS
- Offsets: 0, 7, 14, 21, 14, 7 (palindromic walk: poses 0-1-2-3-2-1)
- SMC operand bytes at $6BE9/$6BEA = SMC_SPECIAL_BODY_LO/HI, initial
  on-disk value $6C3F (STEP1).
- NOT reset by SPECIAL_REARM — animation phase persists across
  activations.

Why: this is the only entity slot in Drol that *kills* the floor
enemies by collision rather than hits them (contrast ENEMY_C_DRAW
which hits floor-enemies from the player side). The classic arcade
"helpful bonus" pattern.

How to apply: SPECIAL_DRAW uses DRAW_SPRITE (not DRAW_SPRITE_PLAYFIELD
— unlike DRAW_ENTITIES). The active-body draw goes through a
6-handler SMC ring at $6C3F-$6CDA, NOT a ladder-step dispatch (prior
docs were wrong about that). The inactive "peek" sprite lives at
$6CDB and draws a small $02x$06 marker.

## Correction to prior guess

The earlier memory assumption that "$6C49-$6CDA holds 7 ladder-step
handlers that rewrite the puff-draw SMC" was incorrect on two counts:
(1) there are 6 handlers, not 7; (2) they implement the body walk-cycle
animation (active phase), not the drift puff (the puff is drawn once
inline at $6BEB-$6BFF from $AFDA/$B05A, a single un-chained sprite).
The SMC-rewrite pattern is the classic Drol "JMP through patched
operand" walk cycle.
