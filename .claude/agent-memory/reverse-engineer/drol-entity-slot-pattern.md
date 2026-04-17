---
name: Drol entity-slot tick+draw pattern
description: Three parallel entity slots ($DC/$E0/$D4 state bytes) share a reusable tick+draw pattern with ADVANCE_RATE as decrement
type: project
---

Drol's main loop calls six tightly-paired routines handling three moving-hazard slots in the contiguous ZP entity block $D4-$EC (copied from $029C by INIT_LEVEL_STATE).  All three use the same 4-byte record layout and the same advance-then-rearm tick structure:

| Slot    | State | 16-bit pos | Row  | Sound ctr | Sound tbl | Tick entry | Draw entry    |
|---------|-------|------------|------|-----------|-----------|------------|---------------|
| enemy-A | $DC   | $DD/$DE    | $DF  | $B8       | $0229     | $13D6 ENEMY_A_ADVANCE | $1423 SPRITE_DRAW_1  |
| enemy-B | $E0   | $E1/$E2    | $E3  | $E4       | $0231     | $1536 SPRITE_DRAW_2   | $1591 SPRITE_DRAW_3  |
| enemy-C | $D4   | $D5/$D6    | $D7  | $B7       | $0224     | $1646 PLAYER_STATE    | $16AC PLAYER_RENDER  |

Main-loop order: PLAYER_STATE, PLAYER_RENDER, ENEMY_A_ADVANCE (formerly "BG_RESTORE"), SPRITE_DRAW_1, SPRITE_DRAW_2, SPRITE_DRAW_3, BEAM_UPDATE.

**Why:** Recognizing this triplet structure turned a 976-byte opaque HEX blob ($13D6-$17A5) into six documentable routines.  Enemy-A's rearm writes $01 to $D4 (enemy-C state) --- cross-slot handshake, not independent.

**How to apply:** When RE'ing SPRITE_DRAW_2 ($1536) or PLAYER_STATE ($1646), expect the same tick+rearm shape as ENEMY_A_ADVANCE (click via SFX_TONE from pitch table, state gate, SBC ZP_ADVANCE_RATE on 16-bit counter, narrow-band rearm window).  The draw counterparts at $1423/$1591/$16AC use an identical screen-clip / sprite-dispatch structure keyed on $4A/$1A8F.  "PLAYER_STATE"/"PLAYER_RENDER" naming is probably a misnomer --- $D4 is an enemy-C slot, not the player proper.  Verify by cross-referencing how $D4 interacts with player-capture code ($17CF writes #$FF there).
