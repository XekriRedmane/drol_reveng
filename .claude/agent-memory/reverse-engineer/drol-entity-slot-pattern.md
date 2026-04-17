---
name: Drol entity-slot tick+draw pattern
description: Three parallel entity slots ($DC/$E0/$D4 state bytes) share a tick+draw shape but cadence diverges dramatically (A/C down-count, B up-counts)
type: project
---

Drol's main loop calls six tightly-paired routines handling three moving-hazard slots in the contiguous ZP entity block $D4-$EC (copied from $029C by INIT_LEVEL_STATE).  All three use the same 4-byte record layout and the same click/state-gate/rearm template, but the tick arithmetic and handshake topology differ per slot:

| Slot    | State | 16-bit pos | Row  | Sound ctr | Sound tbl | Sound rtn       | Tick entry              | Draw entry    |
|---------|-------|------------|------|-----------|-----------|-----------------|-------------------------|---------------|
| enemy-A | $DC   | $DD/$DE    | $DF  | $B8       | $0229     | SFX_TONE        | $13D6 ENEMY_A_ADVANCE   | $1423 SPRITE_DRAW_1  |
| enemy-B | $E0   | $E1/$E2    | $E3  | $E4       | $0231     | SFX_TONE        | $1536 ENEMY_B_ADVANCE   | $1591 ENEMY_B_DRAW   |
| enemy-C | $D4   | $D5/$D6    | $D7  | $B7       | $0224     | SND_DELAY_DOWN  | $1646 ENEMY_C_ADVANCE   | $16AC PLAYER_RENDER  |

Main-loop order: ENEMY_C_ADVANCE, PLAYER_RENDER, ENEMY_A_ADVANCE, SPRITE_DRAW_1, ENEMY_B_ADVANCE, ENEMY_B_DRAW, BEAM_UPDATE.

**Cadence direction per slot:**
- Enemy-A and enemy-C subtract `ZP_ADVANCE_RATE` ($40, tier-controlled $01/$02/$03) from the 16-bit counter each frame, rearming on narrow crossings of $0000..$003D (A) or $0000..$003B (C).
- Enemy-B **adds** a small value each frame; the add amount is self-modified (at $1551, the ADC #imm operand byte) to be either $01 (initial/default) or $03, driven by `ZP_ANIM_COUNTER` ($1F). Rearm triggers when counter >= $035A.

**Cross-slot handshake topology (3-slot, confirmed after RE of ENEMY_B_DRAW):**
- A's rearm at $1411 writes $01 to $D4 (wakes C in steady mode).
- C's rearm writes $00 to $D4 (deactivates self).
- B's rearm writes neither $DC nor $D4.  B's *collision* path inside ENEMY_B_DRAW at $15FE writes $FF to its own $E0 (drift-mode self-deactivate) only --- B does NOT handshake A or C.
- C's *collision* path inside PLAYER_RENDER at $1757-$1763 writes $FF to both $D4 and $DC ($DC only if non-zero) --- this is the broadcast handshake, and it lives in PLAYER_RENDER (enemy-C draw), not in ENEMY_B_DRAW as earlier notes claimed.
- So the handshake topology is: A->C (via rearm), C->{A,C} (via collision), B self-only.  B has no outgoing handshake; A and B both absorb player hits (DEC $39) but only C arms the others.

**Drift mode means different things per slot:**
- Enemy-A drift (state bit 7): PRNG gate on $5F, skips most ticks (~3.5%/frame chance to advance).
- Enemy-B drift: INCs lo-byte counter only; on 256-frame wrap self-deactivates (state := $00). No PRNG gate, no row bobble.
- Enemy-C drift: vertical bobble (INC/DEC $D7) on 1-in-4 frames using $FD bit-4 phase, plus a separate up-counting drift entry at $16A5 that falls into rearm on lo-wrap.

**Row-anchor table at $84-$87:**
- Enemy-B reads $84,X with X = ($1F & 3), using all four entries $84/$85/$86/$87.
- Enemy-C reads $84,X with X computed as ($5F & 3) if non-zero else 1, using only $85/$86/$87 (subtracts $0A from the anchor).
- The base $84 is also the per-level intro Y seed (LEVEL_INTRO_TICK).

**$1F (`ZP_ANIM_COUNTER`) is triple-purposed:**
- Low byte of the PRNG state at $6674 (PRNG).
- Player animation frame counter (timer display update at $10AB, climb-pause in ATTRACT_ANIM_3).
- Enemy-B cadence gate and SMC-patch source ($1536).

**Why:** Recognizing this triplet structure turned a 976-byte opaque HEX blob ($13D6-$17A5) into six documentable routines, then carved ENEMY_B_ADVANCE out of the middle of SPRITE_DRAW_1 and ENEMY_B_DRAW out of the middle of the $1591 HEX blob. The triplet is now fully decomposed on the tick side and partly on the draw side; SPRITE_DRAW_1 ($1423) and PLAYER_RENDER ($16AC) remain HEX blobs sharing a parallel structure with ENEMY_B_DRAW.

**How to apply:** When RE'ing the remaining two draw routines, expect: (1) early `LDA $Xx; BEQ exit` state gate, with negative state jumping to a drift-mode draw tail; (2) clip-against-player-column logic using $4A/PERSPECTIVE_XOFF_LO (=$1A8F) and $4C (ZP_SPRITE_XREF), producing screen-relative X in $AF/$B0; (3) screen-X bound check against $9A (A) / $9C (B); (4) sprite parameter setup ($56/$57/$5B/$5D) + SMC patches at $65B3/$65B4 + JSR DRAW_SPRITE ($656F), reading from SPRITE_TABLE_LO/HI at base+offset indexed by PROJ_FRAME_IDX ($1B8F); (5) a hit-detection block with narrow X window + Y band, writing to the appropriate state byte --- A zeros $DC, B writes $FF to $E0, C writes $FF to both $D4 and $DC; (6) DEC $39 (ZP_GAME_OVER) + SCORE_ADD $0300 on hit; (7) a separate drift-mode draw tail below the collision body that draws a small puff sprite with sprite source address pulled from level-specific data.
