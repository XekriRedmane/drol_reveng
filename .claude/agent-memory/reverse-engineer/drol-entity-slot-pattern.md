---
name: Drol entity-slot tick+draw pattern
description: Three parallel enemy slots ($DC/$E0/$D4 state bytes) share the tick+draw shell but diverge in cadence, sprite structure, and handshake topology
type: project
---

Drol's main loop calls six tightly-paired routines handling three moving-hazard slots in the contiguous ZP entity block $D4-$EC (copied from $029C by INIT_LEVEL_STATE).  All three use the same 4-byte record layout and the same click/state-gate/rearm template, but the tick arithmetic, sprite structure, hit target, and handshake topology differ per slot:

| Slot    | State | 16-bit pos | Row  | Sound ctr | Sound tbl | Sound rtn       | Tick entry              | Draw entry              |
|---------|-------|------------|------|-----------|-----------|-----------------|-------------------------|-------------------------|
| enemy-A | $DC   | $DD/$DE    | $DF  | $B8       | $0229     | SFX_TONE        | $13D6 ENEMY_A_ADVANCE   | $1423 ENEMY_A_DRAW      |
| enemy-B | $E0   | $E1/$E2    | $E3  | $E4       | $0231     | SFX_TONE        | $1536 ENEMY_B_ADVANCE   | $1591 ENEMY_B_DRAW      |
| enemy-C | $D4   | $D5/$D6    | $D7  | $B7       | $0224     | SND_DELAY_DOWN  | $1646 ENEMY_C_ADVANCE   | $16AC ENEMY_C_DRAW      |

Main-loop order: ENEMY_C_ADVANCE, ENEMY_C_DRAW, ENEMY_A_ADVANCE, ENEMY_A_DRAW, ENEMY_B_ADVANCE, ENEMY_B_DRAW, BEAM_UPDATE.

**Cadence direction per slot:**
- Enemy-A and enemy-C subtract `ZP_ADVANCE_RATE` ($40, tier-controlled $01/$02/$03) from the 16-bit counter each frame, rearming on narrow crossings of $0000..$003D (A) or $0000..$003B (C).
- Enemy-B **adds** a small value each frame; the add amount is self-modified (at $1551, the ADC #imm operand byte) to be either $01 (initial/default) or $03, driven by `ZP_ANIM_COUNTER` ($1F). Rearm triggers when counter >= $035A.

**Cross-slot handshake topology (3-slot, FULLY CONFIRMED after all three draw routines RE'd):**
- A's rearm at $1411 writes $01 to $D4 (wakes C in steady mode).
- C's rearm writes $00 to $D4 (deactivates self).
- B's rearm writes neither $DC nor $D4.  B's *collision* path inside ENEMY_B_DRAW at $15FE writes $FF to its own $E0 (drift-mode self-deactivate) only --- B does NOT handshake A or C.
- C's *collision* path inside ENEMY_C_DRAW at $1757-$1763 writes $FF to both $D4 and $DC ($DC only if non-zero) --- this is the broadcast handshake, and it lives in ENEMY_C_DRAW, not in ENEMY_B_DRAW.
- A's *collision* path inside ENEMY_A_DRAW at $1520-$1534 writes $00 to its own $DC (immediate deactivation, not $FF drift like B) --- A does NOT handshake anywhere else.  A also DECs $39 (player-life credit) like B.

Topology summary: A->C (rearm, $01), C->{A,C} (hit, $FF), A->A (hit, $00), B->B (hit, $FF).  Only A and B hit the player; C hits the 4-slot floor-enemy table.

**BPL polarity is inverted on enemy-A:**
- Enemy-B and enemy-C dispatch as `BEQ .exit / BPL .steady / (fall through) JMP .drift_draw`, so positive = steady main draw.
- Enemy-A dispatches as `BEQ .exit / BPL .walk_phase / (fall through) .stance`, so positive = animated, negative = stance (no drift puff at all).  Enemy-A drift just collapses the animation; there is no puff sprite.

**Drift mode means different things per slot:**
- Enemy-A drift (state bit 7, set by ENEMY_C_DRAW's hit broadcast): draw stance without animation.  In the tick, PRNG gate on $5F skips most ticks (~3.5%/frame chance to advance).
- Enemy-B drift: INCs lo-byte counter only; on 256-frame wrap self-deactivates (state := $00). No PRNG gate, no row bobble.  Draw uses the puff at $755A/$765A.
- Enemy-C drift: vertical bobble (INC/DEC $D7) on 1-in-4 frames using $FD bit-4 phase, plus a separate up-counting drift entry at $16A5 that falls into rearm on lo-wrap.  Draw uses the puff at $7559/$7659.

**Walking animation on enemy-A only:**
- ENEMY_A_DRAW extracts `ZP_FRAME_COUNTER & $06 >> 1` (range 0..3) on the positive-state path.  Phases 0 and 2 use the stance sprite ($B017/$B097); phases 1 and 3 animate walking feet ($B01E/$B09E and $B010/$B090), drawing the body one row higher.  The four-frame cycle produces a visible gait.  ZP_ENEMY_A_LEG_PHASE = $0F is the scratch ZP for the current frame's phase.
- Enemies B and C have no such animation --- they each draw a single body sprite (B) or body+tail (C) without frame animation.

**Sprite-size tabulation for the triplet:**
- Enemy-A body: $03x$13 from $B009/$B089.  Stance feet: $03x$03 from $B017/$B097.  Walk feet variants: $03x$04 from $B010/$B090 or $B01E/$B09E.  No drift puff.
- Enemy-B body: $05x$11 from $B025/$B0A5.  Drift puff: $02x$06 from $755A/$765A.  No secondary sprite.
- Enemy-C body: $02x$0B from $AFE1/$B061.  Steady tail: $01x$07 from $7549/$7649 (indexed, per-level).  Drift puff: $02x$06 from $7559/$7659 (un-indexed).

**Right-edge clip differs per slot:** A uses $9A, B uses $9C, C uses $94.

**Hit-test contrasts:**
- Enemy-A: player collision, X window [$42, $4F), Y window [player-$14, player+$10].  Awards +$0300, DEC $39.  Writes $00 to own state.  One `$07 -> ZP_ENEMY_A_SND_CTR` death click on hit.
- Enemy-B: player collision, X window [$42, $55), Y window [player-$0E, player+$0D].  Awards +$0300, DEC $39.  Writes $FF to own state (drift).
- Enemy-C: floor-enemy collision (not player!), uses $9B/$9F/$A3 beam-enemy table, X in (enemy_col-$08, enemy_col], Y in (enemy_y-$0A, enemy_y+$04].  Awards +$0100, does NOT DEC $39.  Only C writes across-slot ($FF to $DC if active).

**Row-anchor table at $84-$87:**
- Enemy-B reads $84,X with X = ($1F & 3), using all four entries $84/$85/$86/$87.
- Enemy-C reads $84,X with X computed as ($5F & 3) if non-zero else 1, using only $85/$86/$87 (subtracts $0A from the anchor).
- The base $84 is also the per-level intro Y seed (LEVEL_INTRO_TICK).

**$1F (`ZP_ANIM_COUNTER`) is triple-purposed:**
- Low byte of the PRNG state at $6674 (PRNG).
- Player animation frame counter (timer display update at $10AB, climb-pause in ATTRACT_ANIM_3).
- Enemy-B cadence gate and SMC-patch source ($1536).

**$FD (`ZP_FRAME_COUNTER`) is dual-purposed:**
- Free-running frame counter (incremented in MAIN_LOOP).  Wrap-to-zero gates DIFFICULTY_UPDATE.
- Bits 1-2 drive enemy-A's walking-frame animation in ENEMY_A_DRAW.
- Bit 4 drives enemy-C's drift-mode vertical bobble.

**How to apply:** When RE'ing any routine that references $D4-$EC, $B7/$B8, $9B-$A7, or $0229/$0231/$0224, consult this table first.  The triplet's idioms (DRAW_SPRITE SMC at $65B3/$65B4, PERSPECTIVE_XOFF_LO/HI at $1A8F/$198F, ZP_CLIP_X_LO/HI at $AF/$B0, ZP_SPRITE_XREF at $4C) are the same across all three draws, so matching instruction patterns is fast.  If a new routine writes to $DC or $D4, trace it back to the triplet — it's probably a handshake and worth adding to the topology summary above.
