# TODO

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
- [ ] `$10AB` — Display update
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
      companion slot handled by `ENEMY_C_ADVANCE`/`PLAYER_RENDER`),
      reloads counter to $0361, and sets `ZP_ENEMY_A_ROW` ($DF) :=
      `ZP_ENEMY_C_ROW` ($D7) + 7.  Retires the `BG_RESTORE`
      misnomer --- this routine does no background restore.  Carved
      $13D6--$1422 out of the old 976-byte `<<sprite player code>>`
      HEX blob; the tail at $1423 is now labelled `SPRITE_DRAW_1`
      (stub EQU removed).
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
      itself) --- there is NO C$\rightarrow$\{A,B\} handshake, so
      enemy-C is purely a one-shot puff awakened by enemy-A's rearm
      ($1411 writes $01 to $D4) or by enemy-B's firing path
      ($1759 writes $FF for drift mode).  This confirms the
      three-slot entity model with topology A$\rightarrow$C and
      B$\rightarrow$\{A,C\}.  Reload value $0352, rearm window
      $0000..$003B, row reload reads from a 3-entry table at
      $85/$86/$87 (addressed as $84,X for X $\in \{1,2,3\}$ with
      X~=~1 selected 2/4 of the time).  Carved $1646--$16AB out of
      the surviving `<<sprite player code>>` HEX blob; the tail at
      $16AC is now `<<sprite player code 16AC>>` with `PLAYER_RENDER`
      label (the misnomer remains pending RE of the draw routine).
      Retires `PLAYER_STATE = $1646` EQU stub.  Introduces ZPs
      `ZP_ENEMY_C_SND_CTR` ($B7), `ZP_ENEMY_C_POS` ($D5),
      `SND_PITCH_TBL_C` ($0224), `ENEMY_C_ROW_TBL` ($84).
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

### Triplet of entity-slot tick routines

- [x] `$13D6` `ENEMY_A_ADVANCE` --- enemy-A slot ($DC/$DD/$DE/$DF, $B8 sound).
- [ ] `$1536` `SPRITE_DRAW_2` (likely `ENEMY_B_ADVANCE`) --- enemy-B slot
      ($E0/$E1/$E2/$E3, $E4 sound, $0231 pitch table).  Disassembled bytes
      are structurally similar (LDX $E4; BMI; LDA $0231,X; LDX #$0A; JSR
      $67C1; DEC $E4; LDA $E0; ...) but the tick ADDS $01 instead of
      subtracting `ZP_ADVANCE_RATE`, suggesting a slow free-running counter
      with a different rearm trigger ($E1 >= $5A and $1F == 0/2 gate).
      Worth full RE next to confirm.
- [x] `$1646` `ENEMY_C_ADVANCE` --- enemy-C slot ($D4/$D5/$D6/$D7, $B7
      sound).  Done; see above.

### Game flow routines

- [ ] `$7208` — Level complete handler (jumped to when $5E < 0)
- [ ] `$BDA0` — Game over handler (jumped to when $39 < 0)
- [ ] `$13A4` — Game start initialization (called on attract→game transition)

### Attract-mode subroutines

- [ ] `$17A6`, `$17E1`, `$1813`, `$1844` — Attract animation routines
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
