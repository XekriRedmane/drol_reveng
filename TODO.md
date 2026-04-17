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

- [ ] `$6000` — Input dispatcher (keyboard/joystick handler)
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
- [ ] `$719D` — Scroll / camera
- [ ] `$683C` — Page flip routine
- [x] `$67C1` — `SFX_TONE`: speaker-click tone / delay generator.
      Classic nested delay loop; A = pitch, X = duration; clicks the
      speaker via `CMP ($36),Y` where ($36,$37) is an indirect pointer
      built so that bit 4 of $36 toggles between $C030 (speaker, sound
      on) and $C020 (silent cassette output, sound off).  Renamed
      `ZP_SOUND_A`/`_B` to `ZP_SFX_CLICK` / `ZP_SFX_CLICK_SAVED`.
- [ ] `$10AB` — Display update
- [ ] `$130A` — Page flip preparation
- [x] `$656F` — `DRAW_SPRITE`: transparent (OR) blit to hidden hi-res page. Sibling variants at `$65D5` (narrow column range, OR blit) and `$662C` (`BLIT_TILE`, opaque STA blit) still to do.

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
- [ ] `$683C-$699B` — Game engine B head (page-flip / attract-draw dispatchers, HEX)
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
