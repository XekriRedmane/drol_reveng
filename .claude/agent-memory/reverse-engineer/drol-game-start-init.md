---
name: Drol GAME_START_INIT + surprising ZP aliases corrected
description: $13A4 attract→game reset; $6AA7 is NOT load-level (it's SMC-patch to resume gameplay); $5E is lives-BCD not level-state; $65AB/$65A7 are column bounds not HUD values
type: project
---

GAME_START_INIT at $13A4 is the attract→game and in-game restart reset.
Callers: $6121 (start key handler), $7255, $7299 (restart paths inside
game-engine HEX blob).  Second entry point GAME_RESTART at $13C2 is
called from $5ECB; it skips player-Y and HUD-column reseed.

**Why:** Several ZP/memory addresses touched by this routine were
previously guessed labels that turned out to be wrong in a misleading
way.  The corrections matter because multiple other routines
(BEAM_UPDATE, POST_FRAME, LEVEL_INTRO_TICK) depend on the correct
semantics.

**How to apply:** When you see these addresses in future RE, use the
corrected names.  In particular, don't interpret $5E decrement as a
level-timer — it's lives loss.  Don't interpret $6AA7 as a level loader —
it's the SMC-patch that flips MAIN_LOOP from attract mode to game mode.

Corrections applied in this RE:
- `$6AA7` was `LOAD_LEVEL` → is `RESUME_GAMEPLAY_SMC`.  13-byte routine
  that patches SMC_SR_YSRC=$06, SMC_INPUT=$20 (JSR), SMC_RENDER=$20,
  SMC_SR_HEIGHT=$13.  Same effect LEVEL_INTRO_TICK inlines on
  activation.  NOT a level loader.
- `$5E` was `ZP_LEVEL_STATE` → is `ZP_LIVES_BCD`.  Initial $04 (4 lives).
  BCD-decremented at $6A1E and $9397 when player dies.  POST_FRAME
  draws its two nibbles as sprite digits at HUD columns 4 and 6 every
  frame.  When it goes negative, $682B jumps to $7208 (game over).
- `$65AB`/`$65A7` were `SCORE_DISPLAY_VAL`/`LIVES_DISPLAY_VAL` → are
  `HUD_SCORE_COL`/`HUD_LIVES_COL`.  These are the left and right
  playfield column bounds.  BEAM_UPDATE's tracer draw is gated on
  `HUD_SCORE_COL <= col < HUD_LIVES_COL`.  Initial values 0 and $28
  open the full 40-column strip.  The routine at $6200 adjusts these
  bounds along with ZP_CLEAR_COL as the lives HUD grows/shrinks.
- `$2E` was `ZP_LIVES` → is `ZP_CLEAR_COL`.  Initial $27 (col 39 =
  playfield rightmost column).  Used as loop counter in the hi-res
  screen-clear routines at $0400/$04A7 (`LDX $2E; STA page,X`).
- `$44` was `ZP_HIGH_SCORE_FLAG` → is `ZP_RESTART_FLAG`.  Only read at
  $5EC5 where it selects among three restart paths.  Initial $FF.
- `$46` is write-only in the game code (stored at $13CE, never read).
  Likely dead code or a signal the code never actually uses.
