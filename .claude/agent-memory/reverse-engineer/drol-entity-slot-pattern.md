---
name: Drol entity-slot tick+draw pattern
description: Three parallel entity slots ($DC/$E0/$D4 state bytes) share a reusable tick+draw pattern with ADVANCE_RATE as decrement
type: project
---

Drol's main loop calls six tightly-paired routines handling three moving-hazard slots in the contiguous ZP entity block $D4-$EC (copied from $029C by INIT_LEVEL_STATE).  All three use the same 4-byte record layout and the same advance-then-rearm tick structure:

| Slot    | State | 16-bit pos | Row  | Sound ctr | Sound tbl | Sound rtn       | Tick entry              | Draw entry    |
|---------|-------|------------|------|-----------|-----------|-----------------|-------------------------|---------------|
| enemy-A | $DC   | $DD/$DE    | $DF  | $B8       | $0229     | SFX_TONE        | $13D6 ENEMY_A_ADVANCE   | $1423 SPRITE_DRAW_1  |
| enemy-B | $E0   | $E1/$E2    | $E3  | $E4       | $0231     | SFX_TONE        | $1536 SPRITE_DRAW_2 (likely ENEMY_B_ADVANCE) | $1591 SPRITE_DRAW_3  |
| enemy-C | $D4   | $D5/$D6    | $D7  | $B7       | $0224     | SND_DELAY_DOWN  | $1646 ENEMY_C_ADVANCE   | $16AC PLAYER_RENDER  |

Main-loop order: ENEMY_C_ADVANCE, PLAYER_RENDER, ENEMY_A_ADVANCE, SPRITE_DRAW_1, SPRITE_DRAW_2, SPRITE_DRAW_3, BEAM_UPDATE.

**Cross-slot handshake topology (3-slot, NOT 4-slot):**
- A's rearm writes $01 to $D4 (wakes C in steady mode) at $1411.
- C's rearm writes $00 to $D4 (deactivates self).  No outgoing handshake.
- B's draw/firing path at $1757 writes $FF to $D4 (wakes C in drift mode) and $FF to $DC (wakes A in drift mode).
- B's rearm at $1576 writes $00 to $E0 (deactivates self).  No outgoing handshake either.
- So: A and B both feed C; C is purely driven; A also "self-arms" via its own rearm path.

**Drift mode means different things per slot:**
- Enemy-A drift (state bit~7): PRNG gate on $5F, skips most ticks (~3.5%/frame chance to advance).
- Enemy-B drift: not yet RE'd.
- Enemy-C drift: vertical bobble (INC/DEC $D7) on 1-in-4 frames using $FD bit-4 phase, plus a separate up-counting drift entry at $16A5.

**Why:** Recognizing this triplet structure turned a 976-byte opaque HEX blob ($13D6-$17A5) into six documentable routines.

**How to apply:** When RE'ing SPRITE_DRAW_2 ($1536), expect the same tick+rearm shape as enemy-A/C with B-specific quirks --- but the disassembly shows it ADDs to $E1 instead of subtracting, gates on $1F (joystick state?) values 0/2/4, and rearms when $E1 >= $5A.  This is a different cadence model.  The draw counterparts at $1423/$1591/$16AC all use an identical screen-clip / sprite-dispatch structure keyed on $4A/$1A8F.

The "PLAYER_STATE"/"PLAYER_RENDER" naming was a misnomer --- $D4 is enemy-C, not the player proper.  PLAYER_STATE has been renamed ENEMY_C_ADVANCE; PLAYER_RENDER's name is kept for now since the draw routine isn't fully RE'd, but it is the enemy-C draw, not player draw.
