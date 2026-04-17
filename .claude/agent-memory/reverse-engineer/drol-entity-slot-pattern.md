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
| enemy-C | $D4   | $D5/$D6    | $D7  | $B7       | $0224     | SND_DELAY_DOWN  | $1646 ENEMY_C_ADVANCE   | $16AC ENEMY_C_DRAW   |

Main-loop order: ENEMY_C_ADVANCE, ENEMY_C_DRAW, ENEMY_A_ADVANCE, SPRITE_DRAW_1, ENEMY_B_ADVANCE, ENEMY_B_DRAW, BEAM_UPDATE.

**Cadence direction per slot:**
- Enemy-A and enemy-C subtract `ZP_ADVANCE_RATE` ($40, tier-controlled $01/$02/$03) from the 16-bit counter each frame, rearming on narrow crossings of $0000..$003D (A) or $0000..$003B (C).
- Enemy-B **adds** a small value each frame; the add amount is self-modified (at $1551, the ADC #imm operand byte) to be either $01 (initial/default) or $03, driven by `ZP_ANIM_COUNTER` ($1F). Rearm triggers when counter >= $035A.

**Cross-slot handshake topology (3-slot, confirmed after RE of ENEMY_B_DRAW and ENEMY_C_DRAW):**
- A's rearm at $1411 writes $01 to $D4 (wakes C in steady mode).
- C's rearm writes $00 to $D4 (deactivates self).
- B's rearm writes neither $DC nor $D4.  B's *collision* path inside ENEMY_B_DRAW at $15FE writes $FF to its own $E0 (drift-mode self-deactivate) only --- B does NOT handshake A or C.
- C's *collision* path inside ENEMY_C_DRAW at $1757-$1763 writes $FF to both $D4 and $DC ($DC only if non-zero) --- this is the broadcast handshake, and it lives in ENEMY_C_DRAW, not in ENEMY_B_DRAW.
- **Crucially:** enemy-C's hit target is NOT the player (unlike enemy-B's at $15EE which reads ZP_PLAYER_COL=$06).  Enemy-C hits against the 4-slot floor-enemy table at $9B/$9F/$A3 (ZP_ENEMY_FLAG/COL/Y), the same slots the beam subsystem targets.  On hit, enemy-C consumes the floor-enemy slot (writes $00 to $9B,X), awards +$0100 BCD (100 points, not 300), and does NOT decrement ZP_GAME_OVER.
- So the handshake topology is: A->C (via rearm), C->{A,C} (via C-vs-floor-enemy collision), B self-only.  B has no outgoing handshake.  Only enemy-B absorbs player hits (DEC $39).  Enemy-A likely does too (presumed, per pattern — SPRITE_DRAW_1 at $1423 not yet RE'd).  Enemy-C's hit path is entirely enemy-vs-enemy, not enemy-vs-player.

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

**Why:** Recognizing this triplet structure turned a 976-byte opaque HEX blob ($13D6-$17A5) into six documentable routines.  ENEMY_B_ADVANCE carved out of SPRITE_DRAW_1, ENEMY_B_DRAW carved out of the $1591 HEX blob, and ENEMY_C_DRAW disassembled from the $16AC blob.  SPRITE_DRAW_1 ($1423, enemy-A draw) is the last remaining HEX blob from the triplet.

**How to apply:** When RE'ing SPRITE_DRAW_1 ($1423), expect the same shell as ENEMY_B_DRAW/ENEMY_C_DRAW: (1) state gate on $DC with BEQ-exit / BPL-steady / JMP-drift_draw; (2) clip via PERSPECTIVE_XOFF_LO/HI indexed by ZP_PLAYER_Y, screen-X in $AF/$B0; (3) screen-X bound check (probably $9C-ish); (4) sprite params ($56/$57/$5B/$5D), SMC patches at $65B3/$65B4, JSR DRAW_SPRITE.  **Differences expected for enemy-A:** the per-slot sprite-table bases are $B009/$B010/$B017/$B01E (four variants per level spec), the hit target is likely the player (like enemy-B), and on hit it's known to write $00 to ZP_ENEMY_A_STATE (not $FF like B and C).  The score reward and DEC $39 for enemy-A still need confirmation from the $1528 region (per prior note).

**Draw-size tabulation for the triplet:**
- Enemy-A body: TBD (probably $05x$11-ish), bases $B009/$B010/$B017/$B01E.
- Enemy-B body: $05x$11 from $B025/$B0A5.  Drift puff: $02x$06 from $755A/$765A.
- Enemy-C body: $02x$0B from $AFE1/$B061.  Steady tail: $01x$07 from $7549/$7649 (indexed, per-level).  Drift puff: $02x$06 from $7559/$7659 (un-indexed).  Only enemy-C has a secondary steady-mode sprite --- A and B each draw a single body sprite.

**Hit-test contrasts:**
- Enemy-B: player collision, awards +$0300, DEC $39.
- Enemy-C: floor-enemy collision (not player!), uses $9B/$9F/$A3 beam-enemy table, awards +$0100, does NOT DEC $39.  Only C writes across-slot ($FF to $DC if active).
- Enemy-A: TBD — likely mirrors B (player collision) per initial framing but needs confirmation.
