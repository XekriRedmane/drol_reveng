# TODO

## Status snapshot (2026-04-17)

The **entity-draw triplet is complete**: all three enemy advance
routines and all three enemy draw routines are byte-perfect RE'd
(`$13D6`, `$1423`, `$1536`, `$1591`, `$1646`, `$16AC`).  See the
"Entity-slot triplet" section below for the topology summary.
With the triplet, `BEAM_UPDATE` ($130A), `DRAW_ENTITIES` ($683C),
`DISPLAY_UPDATE` ($10AB), `DIFFICULTY_UPDATE` ($719D),
`LEVEL_INTRO_TICK` ($699C), `SFX_TONE` ($67C1), `INPUT_DISPATCH`
($6000), `DRAW_PLAYER` ($64DF), `PLAYER_MOVE_TICK` ($64CB),
`GAME_START_INIT` ($13A4), and the three blitters (`DRAW_SPRITE`,
`DRAW_SPRITE_PLAYFIELD`, `DRAW_SPRITE_OPAQUE`) all documented, the
MAIN_LOOP dispatch is now fully named --- every `JSR` target in the
main loop either has its own ORG chunk or sits inside one of the
named hex blobs awaiting further carve-out.  The remaining
high-priority work is: the large `$6ABA-$719C` "game engine B tail"
blob (sound/animation/entity processing/level logic, 1763 bytes
still as HEX), and the remaining hex tail of `<<game engine A>>` at
$614B-$64CA (player movement-tick handlers and the
DO_ASCEND/DO_DESCEND/DO_MOVE_LEFT/DO_MOVE_RIGHT input handlers
called via SMC from MAIN_LOOP).

## Immediate: apply new code chunk rules

CLAUDE.md now requires raw hex addresses in code to use labels or EQUs.
Review existing chunks for violations:

- [ ] `<<boot1 entry>>`: `JMP $C65C` (PROM re-entry), `JMP $51C0` (loader entry), `STA $0400,X` (text page), raw copy-loop addresses ($5800, $BE00, $BF00, $5000, $D000)
- [ ] `<<rwts entry>>`: `JMP $XXXX` targets within the chunk are already labeled; check for any remaining raw data addresses
- [ ] `<<dispatch>>`: `JSR $4000` should use `GAME_INIT_NOP` or `GAME_INIT`, raw addresses like `$72BA`, `$6022`, `$600E`, `($004E)`
- [ ] `<<main loop>>`: all 25 JSR targets are raw hex — create EQU stubs or ORG stubs as routines are RE'd
- [ ] `<<attract loop>>`: `JSR $17A6`, `JSR $17E1`, `JSR $1813`, `JSR $1844`, `JSR $13A4` are raw hex

## Continue game RE

### High-priority routines (called from main loop)

- [x] `$6000` — `INPUT_DISPATCH`: keyboard/joystick input dispatcher.
- [x] `$699C` — `LEVEL_INTRO_TICK`: per-frame level-start state machine. Init
      (disables input/render SMC slots, clears state, $18=$12, $19=$40),
      countdown (odd-frame tick + flickering sprite draw + SFX_TONE pulse),
      wait-for-start (BCD-decrement $5E, poll keyboard / input-handler MSBs /
      timeout, then activate by restoring JSR opcodes + setting $1E=1).
      Introduced ZPs: ZP_INTRO_Y ($17), ZP_INTRO_COUNTDOWN ($18),
      ZP_INTRO_TIMEOUT ($19); SMC aliases SMC_SR_HEIGHT ($64F6),
      SMC_SR_YSRC ($64FA), SMC_SPRITE_MASK_OP/ARG ($65B7/$65B8); tables
      LEVEL_DATA_BASE ($0200), SPRITE_TABLE_LO/HI ($B000/$B080); stub
      SFX_TONE ($67C1).
- [x] `$719D` — `DIFFICULTY_UPDATE`: score-driven difficulty tier update
      (misnamed "SCROLL_CAMERA" previously --- the routine never touches
      scroll or camera state).  Runs only when `ZP_FRAME_COUNTER` ($FD)
      wraps to 0 (every 256 frames ~= 4s).  Builds a tier index from
      two BCD digits of the score (`ZP_SCORE_HI` low-nibble << 4 |
      `ZP_SCORE_MID` high-nibble >> 4) and dispatches to one of four
      presets that write slot-count maxima, tier thresholds, and the
      per-tick timer-advance rate.  Sub-entry `DIFFICULTY_RESET` ($71D6)
      is the minimum preset, also called by `GAME_START_INIT` to
      initialize.  Renamed `ZP_ENTITY_D1/D2/D3` ($D1/$D2/$D3) to
      `ZP_SCORE_HI/MID/LO` (these are the BCD score, not entity state;
      also confirmed by `SCORE_ADD`, `POST_FRAME`, `LEVEL_TRANSITION`).
      New ZP EQUs: `ZP_PROJ_GATE` ($32), `ZP_DIFF_THRESH_A/B` ($34/$35),
      `ZP_ADVANCE_RATE` ($40), `ZP_DIFF_TMP` ($5C), `ZP_FRAME_COUNTER`
      ($FD).  `$32` and `$40` are read by the not-yet-RE'd routines at
      `$130A` (BPL gate) and `$13F7` / `$1675` (SBC decrement).  `$40`
      consumer at `$13F7` is now documented as `ENEMY_A_ADVANCE` (see
      below); `$1675` remains open as `ENEMY_C_ADVANCE`.
- [x] `$683C` — `DRAW_ENTITIES`: final per-frame drawing dispatcher in
      MAIN_LOOP (misnamed "page flip" previously --- no display-page
      toggle here; that's `DISPLAY_PAGE_FLIP` at $6138).  Five phases:
      phase 1 restores one hit-entity's BG using 12-slot tables at
      `HIT_BG_HI/LO/BYTE0/BYTE1` ($0328/$0334/$034C/$0340), with a +$20
      page offset applied when `ZP_PAGE_FLAG` is negative; phase 2 draws
      the player (gated on $0E); phase 3 draws a "special" sprite
      (gated on $AB); phase 4 draws two "companion" slots (gated on
      $33) from ZP tables at $11/$13/$15; phase 5 iterates the 20-slot
      `ENTITY_ACTIVE` table at $03A8 with parallel tables
      `ENTITY_FLOOR_COL` ($0358), `ENTITY_XOFF_IDX` ($036C),
      `ENTITY_FLOOR_POS` ($0380).  All four draw phases set sprite
      params ($56/$57/$5B/$5D) and JSR `DRAW_SPRITE_PLAYFIELD`
      ($65D5, now disassembled), patching the sprite-data source
      operands at `SMC_PFB_SRC_LO/HI` ($6615/$6616).  Introduced lookup-table
      labels: `FLOOR_TO_ROW` ($1D40), `FLOOR_SPRITE_IDX` ($1E00),
      `FLOOR_SCREEN_COL` ($1F00), `FLOOR_BASE_ROW` ($188F).
- [x] `$67C1` — `SFX_TONE`: speaker-click tone / delay generator.
      Classic nested delay loop; A = pitch, X = duration; clicks the
      speaker via `CMP ($36),Y` where ($36,$37) is an indirect pointer
      built so that bit 4 of $36 toggles between $C030 (speaker, sound
      on) and $C020 (silent cassette output, sound off).  Renamed
      `ZP_SOUND_A`/`_B` to `ZP_SFX_CLICK` / `ZP_SFX_CLICK_SAVED`.
- [x] `$10AB` — `DISPLAY_UPDATE`: timer-animation HUD tile draw.
      Draws the timer element via `DRAW_SPRITE_OPAQUE`, gated on
      `ZP_ANIM_COUNTER` ($1F).
- [x] `$13D6` — `ENEMY_A_ADVANCE`: per-frame tick for the first of
      three ``moving hazard'' slots at $D4--$EC.  Emits an SFX click
      from `SND_PITCH_TBL_A` ($0229) gated on `ZP_ENEMY_A_SND_CTR`
      ($B8), then decrements the 16-bit advance counter
      `ZP_ENEMY_A_POS` ($DD/$DE) by `ZP_ADVANCE_RATE` ($40).  Gated by
      `ZP_ENEMY_A_STATE` ($DC): $00 off; positive = steady tick;
      negative = PRNG-gated drift (tick only when `ZP_PRNG_A` $5F <
      $09, ~3.5% per frame).  On narrow-band crossing ($0000..$003D),
      rearms: promotes drift->steady, writes $01 to
      `ZP_ENEMY_C_STATE` ($D4 --- cross-slot handshake that wakes the
      companion slot handled by `ENEMY_C_ADVANCE`/`ENEMY_C_DRAW`),
      reloads counter to $0361, and sets `ZP_ENEMY_A_ROW` ($DF) :=
      `ZP_ENEMY_C_ROW` ($D7) + 7.  Retires the `BG_RESTORE`
      misnomer --- this routine does no background restore.  Carved
      $13D6--$1422 out of the old 976-byte `<<sprite player code>>`
      HEX blob; the tail at $1423 is now `ENEMY_A_DRAW`.
- [x] `$1423` — `ENEMY_A_DRAW`: per-frame draw + player-collision
      for the enemy-A slot, completing the entity-draw triplet
      alongside `ENEMY_B_DRAW` and `ENEMY_C_DRAW`.  Two-sprite
      composite (body + feet) with a four-frame walking animation
      driven by `ZP_FRAME_COUNTER` bits 1-2 (phases 0,2 = stance;
      phases 1,3 = walk variants drawn at row-1 with 3x4 feet
      sprites from `SPRITE_TABLE_A_STEP1/2`).  Drift mode
      (state < 0, set externally by `ENEMY_C_DRAW`'s hit broadcast)
      collapses the animation to a fixed stance; there is no drift
      puff, unlike B and C.  Right-edge X clip is $9A (vs.\ B's $9C,
      C's $94); hit window is [$42, $4F) for X and
      [player-$14, player+$10] for Y (a $24-row band, 4 rows taller
      than B's $1B).  On player-overlap: writes $00 to
      `ZP_ENEMY_A_STATE` (immediate deactivation, not $FF drift like
      B), loads `ZP_ENEMY_A_SND_CTR` with $07 (one death click),
      decrements `ZP_GAME_OVER` ($39) --- the `DEC $39` at $1528
      that prior docs referenced --- and awards +$0300 BCD via
      `SCORE_ADD`, matching B's 300-point reward.  No cross-slot
      handshake writes.  Retires the `SPRITE_DRAW_1 = $1423` EQU
      stub and carves the last of the old `<<sprite player code>>`
      HEX blob.  Introduces ZP EQU `ZP_ENEMY_A_LEG_PHASE` ($0F,
      scratch alias distinct from the RWTS `ZP_TGT_TRACK`) and
      sprite-table EQUs `SPRITE_TABLE_A_BODY_LO/HI` ($B009/$B089),
      `SPRITE_TABLE_A_STEP1_LO/HI` ($B010/$B090),
      `SPRITE_TABLE_A_FEET_LO/HI` ($B017/$B097),
      `SPRITE_TABLE_A_STEP2_LO/HI` ($B01E/$B09E).
- [x] `$1646` — `ENEMY_C_ADVANCE`: per-frame tick for the third
      ``moving hazard'' slot, sibling of `ENEMY_A_ADVANCE` with the
      same tick+rearm shape but three notable differences.  (1)
      Click is `SND_DELAY_DOWN` ($1091) at duration $08 reading from
      `SND_PITCH_TBL_C` ($0224) gated on `ZP_ENEMY_C_SND_CTR` ($B7)
      --- a softer descending-tone chirp distinct from enemy-A's
      `SFX_TONE`.  (2) Drift mode (state bit~7 set) does NOT
      PRNG-gate the tick; instead it bobs `ZP_ENEMY_C_ROW` $\pm$1 on
      1-in-4 frames using `ZP_FRAME_COUNTER` bit~4 as the up/down
      phase, producing a vertical wobble.  Drift entry at $16A5
      counts the lo counter UP and falls into rearm on overflow.
      (3) Rearm writes $00 to `ZP_ENEMY_C_STATE` (deactivates
      itself) --- the topology edges live in `ENEMY_C_DRAW` instead
      (see below), giving three-slot model A$\rightarrow$C (rearm)
      and C$\rightarrow$\{A,C\} (hit).  Reload value $0352, rearm
      window $0000..$003B, row reload reads from a 3-entry table at
      $85/$86/$87 (addressed as $84,X for X $\in \{1,2,3\}$ with
      X~=~1 selected 2/4 of the time).  Carved $1646--$16AB out of
      the surviving `<<sprite player code>>` HEX blob.
      Retires `PLAYER_STATE = $1646` EQU stub.  Introduces ZPs
      `ZP_ENEMY_C_SND_CTR` ($B7), `ZP_ENEMY_C_POS` ($D5),
      `SND_PITCH_TBL_C` ($0224), `ENEMY_C_ROW_TBL` ($84).
- [x] `$16AC` — `ENEMY_C_DRAW`: per-frame draw + enemy-slot collision
      for enemy-C, replacing the `PLAYER_RENDER` stub (mis-named in
      the stub era --- this routine does not render the player).
      Steady-mode draws TWO sprites: a $02x$0B body from
      `SPRITE_TABLE_C_LO/HI` ($AFE1/$B061) and a $01x$07 ``tail''
      one column left and $0B rows below from the level-specific
      `ENEMY_C_TAIL_LO/HI` pointer-table ($7549/$7649, indexed by
      PROJ_FRAME_IDX).  Hit-test is against the 4-slot floor-enemy
      table at $9B/$9F/$A3 (same slots the beam subsystem targets),
      NOT the player --- walks X=3..0 for first active slot, checks
      clip_X vs ZP_ENEMY_COL and row vs ZP_ENEMY_Y.  On hit:
      $FF$\rightarrow$$D4 (self drift), $FF$\rightarrow$$DC if
      active (A into drift), retires the floor-enemy ($00$\rightarrow$$9B,X),
      rewinds position, awards +$0100 BCD, reloads click counter to
      $04.  No DEC ZP_GAME_OVER --- this hit path is not a
      life-loss event.  Drift-mode tail draws a $02x$06 puff from
      `ENEMY_C_PUFF_LO/HI` ($7559/$7659, un-indexed, one byte
      earlier than enemy-B's $755A/$765A puff).  Corrects prior
      prose that attributed the $1757--$1763 broadcast to
      `SPRITE_DRAW_3`/enemy-B firing.  Retires `PLAYER_RENDER`
      label.  Introduces EQUs `SPRITE_TABLE_C_LO/HI`,
      `ENEMY_C_TAIL_LO/HI`, `ENEMY_C_PUFF_LO/HI`.
- [x] `$130A` — `BEAM_UPDATE`: player laser-beam subsystem, gated on
      `ZP_PROJ_GATE` ($32).  Inactive at difficulty tiers minimum and
      moderate ($32 = $FF); active at standard and maximum ($32 = $01).
      Dispatches three sub-routines: `BEAM_TARGET_TICK` ($1230) state
      machine, `BEAM_TARGET_DRAW` ($1297) sprite-trail draw plus
      enemy-collision check (awards 100 BCD on hit), and
      `BEAM_TRACER_SPAWN` ($1376) per-floor tracer scheduler.  Then
      walks a 5-slot tracer table (`TRACER_STATE` $0237,
      `TRACER_ROW` $023C) and for each active slot decrements the
      state/X-column, draws a single $7F byte directly into hi-res at
      the row/col with HUD-bound clipping, and runs a hit test when
      the X-column enters the $12/$13 near-player window (sets
      `ZP_HIT_FLAG` $1E=$FF).  Uses SMC operands `SMC_TRACER_ADDR_LO`
      ($1359) / `SMC_TRACER_ADDR_HI` ($135A) patched inline.  Retires
      "Page flip preparation" stub name (real page flip is at $6138
      `DISPLAY_PAGE_FLIP`).
- [x] `$1536` — `ENEMY_B_ADVANCE`: enemy-B slot up-counter; see triplet section below.
- [x] `$1591` — `ENEMY_B_DRAW`: enemy-B sprite draw + player-collision
      handler, replacing the `SPRITE_DRAW_3` stub.  Steady-mode
      draws a $05x$11 body sprite from `SPRITE_TABLE_B_LO/HI`
      ($B025/$B0A5); drift-mode draws a $02x$06 puff sprite from the
      per-level pointer pair at `ENEMY_B_PUFF_LO/HI` ($755A/$765A).
      The player-overlap body at $15FE writes $FF to
      `ZP_ENEMY_B_STATE` only (putting B into drift mode for
      deferred self-deactivation), awards +300 BCD via
      `SCORE_ADD`, and decrements `ZP_GAME_OVER` ($39).
      **Correction to prior docs**: the B->{A,C} handshake is
      *not* in this routine --- the $1757-$1763 writes to $D4/$DC
      live in `PLAYER_RENDER` (enemy-C draw).  Enemy-B's collision
      only touches its own state $E0.  Introduces ZP EQUs
      `ZP_CLIP_X_LO` ($AF), `ZP_CLIP_X_HI` ($B0), `ZP_SPRITE_XREF`
      ($4C), `ZP_GAME_OVER` ($39); data EQUs `PERSPECTIVE_XOFF_LO`
      ($1A8F), `PERSPECTIVE_XOFF_HI` ($198F), `SPRITE_TABLE_B_LO`
      ($B025), `SPRITE_TABLE_B_HI` ($B0A5), `ENEMY_B_PUFF_LO`
      ($755A), `ENEMY_B_PUFF_HI` ($765A).  Retires the
      `SPRITE_DRAW_3 = $1591` EQU stub and carves $1591-$1645 out
      of the `<<sprite player code 1591>>` HEX blob.
- [x] `$64DF` — `DRAW_PLAYER`: main-loop player sprite renderer
      (retires the `SPRITE_RENDER` EQU stub).  Two paths selected
      by the action flag `ZP_ACTION_DIR` ($02 = $00 idle / $01
      ascend / $FF descend).  Idle path: single $03x$13 body from
      `PLAYER_SPR_IDLE_LO/HI` ($7527/$7627) indexed by
      `ZP_PLAYER_STANCE` ($03, clamped $03..$09), drawn at column
      $14 with Y from `ZP_PLAYER_COL` ($06) via the live SMC
      operand `SMC_SR_YSRC` ($64FA).  Action path: if `ZP_HIT_FLAG`
      ($1E) is positive and the stance is $03 or $09 (top/bottom
      floor), first draws a $00x$06 "teleport flicker" sprite
      whose source bytes come from the routine's *own code image*
      at `PLAYER_STATIC_LO/HI` ($6500/$6600 indexed by `$FD`), with
      the live `SMC_SPRITE_MASK_OP/ARG` slot in `DRAW_SPRITE`
      patched to `AND #$83` or `AND #$B0`.  Then the main body
      draws from `PLAYER_SPR_ACTIVE_LO/HI` ($7531/$7631) at
      $03x$14 (one row taller than idle).  Corrects the prior
      mis-naming `SMC_COLLISION_A/B` ($64FA/$64F6) which were
      actually `SMC_SR_YSRC` / `SMC_SR_HEIGHT` --- the self-mod
      operand bytes for `DRAW_PLAYER`'s idle path, patched by
      `LEVEL_INTRO_TICK` and restored by `LEVEL_COMPLETE`.
      Discovered: the "static" texture used for the teleport
      flicker has no dedicated data region; it is the routine's
      own opcodes interpreted as bytes (a code-as-data trick).
      **Note on `DRAW_ENTITIES` phase~2**: despite prior prose,
      the phase-2 draw is *not* the big centre-screen player
      sprite --- that is drawn by `DRAW_PLAYER` here, not from
      `DRAW_ENTITIES`.  Phase~2 is a small $01x$04 perspective-grid
      sprite drawn at `FLOOR_SCREEN_COL[$4A+$10]` using separate
      sprite-pointer tables at $7542/$7642/$7552/$7652; it
      represents the player (or a starting-position indicator)
      in the receding-floor perspective view, gated by `$0E` as
      an intro/wait-phase suppression flag (set to $FF during the
      countdown and $01 during wait-for-start/gameplay by
      `LEVEL_INTRO_TICK`).  New ZP EQUs: `ZP_ACTION_DIR` ($02),
      `ZP_PLAYER_STANCE` ($03).  New data EQUs:
      `PLAYER_SPR_IDLE_LO/HI`, `PLAYER_SPR_ACTIVE_LO/HI`,
      `PLAYER_STATIC_LO/HI`.  SMC aliases `SMC_SR_HEIGHT` /
      `SMC_SR_YSRC` relocated from the level-intro defines chunk
      to the draw-player defines chunk (where they are physically
      declared).  Carved out of `<<game engine A>>`, which now
      ends at $64DE (was $656E, 1060 bytes; now 916 bytes).
- [x] `$64CB` — `PLAYER_MOVE_TICK`: per-frame player-movement
      dispatcher, first JSR from MAIN_LOOP (retires the
      `COLLISION_DETECT` EQU stub --- misnomer: the routine is a
      tri-state dispatcher, not collision logic).  Dispatches on
      `ZP_MOVE_DIR` ($04, formerly misnamed `ZP_FAST_FLAG`):
      $00 idle --> JSR `PLAYER_TICK_IDLE` ($6184);
      negative ($FF) --> JSR `PLAYER_TICK_MOVE_LEFT` ($614B);
      positive ($01) --> JSR `PLAYER_TICK_MOVE_RIGHT` ($619A).
      All three tick handlers live inside the `<<game engine A>>`
      blob; the left and right variants advance `ZP_PLAYER_Y` ($4A)
      by one in the appropriate direction and cycle the walking-
      animation state at $4B/$4C before falling through (left) or
      re-joining (right via `JMP`) the 7-call per-frame update
      chain that `PLAYER_TICK_IDLE` runs on its own.
      $04 is set to $01 / $FF by the `DO_MOVE_RIGHT` / `DO_MOVE_LEFT`
      input handlers at $6409/$646D (still inside the game engine
      A hex tail), and cleared on direction change, clamp, rescue
      (by INPUT_DO_ASCEND/DESCEND), INIT_LEVEL_STATE, or LEVEL_INTRO
      init.  Also read by `HAZARD_CHECK` as a parallax cue:
      projectiles moving opposite the player's horizontal motion
      gain +2 pixels of speed per frame, giving a pseudo-parallax
      effect.  Only 20 bytes; carved from the tail of
      `<<game engine A>>` whose hex blob now ends at $64CA (was
      $64DE, 916 bytes; now 896 bytes).  New ZP EQU:
      `ZP_MOVE_DIR` ($04, replaces the misleading `ZP_FAST_FLAG`).
      New handler EQUs: `PLAYER_TICK_IDLE` ($6184),
      `PLAYER_TICK_MOVE_LEFT` ($614B),
      `PLAYER_TICK_MOVE_RIGHT` ($619A).
- [x] `$656F` — `DRAW_SPRITE`: transparent (OR) blit to hidden hi-res page.
- [x] `$65D5` — `DRAW_SPRITE_PLAYFIELD`: sibling of DRAW_SPRITE.
      Identical structure, but inner-loop column check rejects col
      `$0B` (left playfield wall) and cols `>= $1C` (right HISCORE HUD
      panel + offscreen), confining gameplay sprites to the
      playfield region.  No flicker SMC slot, no dead-code tail.
      Sole callers are the four JSR sites inside DRAW_ENTITIES
      (player / special / companion / entity list).
- [x] `$662C` — `DRAW_SPRITE_OPAQUE`: third blitter in the triplet.
      Opaque (plain STA) blit --- no source-zero skip, no ORA step,
      simple col `>= $28` offscreen check.  Used only for HUD tiles
      (timer animation from DISPLAY_UPDATE, score/hiscore/level BCD
      digits from POST_FRAME/DRAW_DIGIT).  Retires the last 72-byte
      `<<game engine A tail>>` HEX blob.  SMC source-pointer operand
      bytes exported as `SMC_TILE_SRC_LO/HI` ($6662/$6663) ---
      replaces the old `TILE_DATA_LO/HI` + `BLIT_TILE` EQU stubs.

### Entity-slot triplet (tick + draw) --- COMPLETE

All three advance (tick) routines and all three draw routines are
now fully RE'd.  Together they form the `entity-draw triplet`
dispatched from `MAIN_LOOP` in the sequence:

```
ENEMY_C_ADVANCE -> ENEMY_C_DRAW
ENEMY_A_ADVANCE -> ENEMY_A_DRAW
ENEMY_B_ADVANCE -> ENEMY_B_DRAW
```

with `BEAM_UPDATE` immediately after.  The three slots share the
perspective clip + `DRAW_SPRITE`-with-SMC idiom but differ in
sprite structure, hit target, and score reward:

| Slot  | Tick              | Draw              | Hit target        | Score | `$39` |
|-------|-------------------|-------------------|-------------------|-------|-------|
| A     | `$13D6` SBC       | `$1423` walk-anim | player            | +300  | yes   |
| B     | `$1536` ADC (up)  | `$1591` single    | player            | +300  | yes   |
| C     | `$1646` SBC       | `$16AC` body+tail | 4-slot floor-enemy | +100  | no    |

Handshake topology (enemy-X writing to enemy-Y's state byte):

```
A --wake $01--> C       (in ENEMY_A_ADVANCE rearm)
C --drift $FF--> A, C   (in ENEMY_C_DRAW hit)
A --zero $00--> A       (in ENEMY_A_DRAW hit, immediate deactivation)
B --drift $FF--> B      (in ENEMY_B_DRAW hit, deferred deactivation)
```

Individual TODO entries:

- [x] `$13D6` `ENEMY_A_ADVANCE` --- see detailed entry above.
- [x] `$1423` `ENEMY_A_DRAW` --- see detailed entry above.
- [x] `$1536` `ENEMY_B_ADVANCE` --- enemy-B slot ($E0/$E1/$E2/$E3, $E4
      sound, $0231 pitch table).  Counts UP (ADC, not SBC), with the
      per-frame increment patched by self-modifying code at
      `SMC_ENEMY_B_ADD` ($1551, the `ADC #imm` operand byte).  The
      gate inspects `ZP_ANIM_COUNTER` ($1F, the player animation frame
      index): if $1F in {1, 3} the SMC byte is rewritten to $1F so the
      next frame adds 1 or 3 (tripling the advance when the player is
      in anim frame 3).  Rearm triggers when counter >= $035A: reload
      to $003E, reseat row from $84,X with X = $1F & 3 (four-entry
      table, vs.\ enemy-C which uses only three entries).  Drift
      mode INCs lo-byte only and self-deactivates on 256-frame wrap.
      Retired `SPRITE_DRAW_2 = $1536` EQU stub.  Introduces
      ZPs `ZP_ENEMY_B_STATE` ($E0), `ZP_ENEMY_B_POS` ($E1/$E2),
      `ZP_ENEMY_B_ROW` ($E3), `ZP_ENEMY_B_SND_CTR` ($E4), and
      `SND_PITCH_TBL_B` ($0231).
- [x] `$1591` `ENEMY_B_DRAW` --- see detailed entry above.
- [x] `$1646` `ENEMY_C_ADVANCE` --- see detailed entry above.
- [x] `$16AC` `ENEMY_C_DRAW` --- see detailed entry above.

### Game flow routines

- [ ] `$7208` — Game-over handler (jumped to when `ZP_LIVES_BCD` $5E goes negative)
- [ ] `$BDA0` — Game over handler (jumped to when $39 < 0)
- [x] `$13A4` — `GAME_START_INIT`: resets BCD score triple, BCD lives
      counter ($5E=$04), HUD column bounds ($65AB/$65A7), restart flag
      ($44=$FF), player Y ($4A=$6B), and the two-entry sub-routine chain
      (DIFFICULTY_RESET + INIT_LEVEL_STATE).  Tail-calls
      `RESUME_GAMEPLAY_SMC` at $6AA7 to re-patch the main-loop SMC
      slots (SMC_SR_YSRC=$06, SMC_INPUT/SMC_RENDER=JSR, SMC_SR_HEIGHT=$13)
      that flip the engine from attract to game mode.  Exposes a
      sub-entry `GAME_RESTART` at $13C2 used by $5ECB that skips the
      player-position + HUD-column reseed.  **Key corrections:**
      (1) `$6AA7` was previously stubbed as `LOAD_LEVEL` --- it is
      actually `RESUME_GAMEPLAY_SMC`, a 13-byte SMC-patch routine,
      not a level loader.  (2) `$5E` was previously named
      `ZP_LEVEL_STATE` --- it is actually `ZP_LIVES_BCD`, the BCD
      on-screen lives counter drawn by POST_FRAME at HUD cols 4/6.
      (3) `$65AB`/`$65A7` were previously `SCORE_DISPLAY_VAL` /
      `LIVES_DISPLAY_VAL` --- they are actually `HUD_SCORE_COL` /
      `HUD_LIVES_COL`, the left/right playfield column bounds that
      gate the beam-tracer draw in BEAM_UPDATE.  (4) `$2E` was
      previously `ZP_LIVES` --- it is actually `ZP_CLEAR_COL`, the
      screen-clear loop counter / playfield right-edge column.
      (5) `$44` was previously `ZP_HIGH_SCORE_FLAG` --- it is a
      cold-start / restart dispatch flag tested at $5EC5 (value
      $FF=cold path, 0/negative select alternative restart paths).
      (6) `$46` is write-only in the game code --- likely a dead
      store or a signal to a not-yet-RE'd routine.

### Attract-mode subroutines

- [x] `$17A6`, `$17E1`, `$1813`, `$1844` — Attract animation routines
      (all four `ATTRACT_ANIM_1..4` documented as prose + assembly).
- [ ] `$67D7` entry through BIT instructions — document the dual-entry pattern

### Undocumented regions

- [ ] `$4713-$47FF` — Screen init routines (currently HEX blob, has code at $471C+)
- [ ] `$4800-$67CA` — Large gap between game init and main loop (sprites, tables, game code)
- [x] `$683C-$699B` — Game engine B head: now documented as `DRAW_ENTITIES`
      (see above).  No longer a HEX blob.
- [ ] `$6ABA-$719C` — Game engine B tail (sound, animation, entity processing,
      level logic, HEX — 1763 bytes)
- [ ] `$72A0-$72A2` — 3 bytes between attract loop exit and copy routine (JMP $67CB at $72A0)

## Fix reference binary build process

- [ ] Create a script to build `reference/drol.bin` from `drol.dsk` with DOS 3.3 sector skew
- [ ] Document the build process so the reference binary can be regenerated

## Structural

- [ ] Decide chapter organization: by memory region vs. by function
- [ ] The "RWTS" naming for $BE00-$BFFF needs revisiting — most routines are non-disk
- [ ] Consider splitting game code into chapters: initialization, main loop, input, rendering, entities, level data
