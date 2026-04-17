---
name: Drol attract/game/restart state machine topology
description: $7208 is LIFE_LOST_HANDLER (lives-out), $7255 RESTART_NEW_GAME, $7299 START_GAME_FROM_ATTRACT, $5EC5 RESTART_DISPATCH is dead code
type: project
---

The state machine between attract, gameplay, life-lost, and restart
is now fully labeled.  Key facts for future RE:

**Why:** Earlier prose called `$7208` `LEVEL_COMPLETE`, but `$5E` is
`ZP_LIVES_BCD` (HUD lives counter), not a level-complete flag --- so
the routine at $7208 is the lives-out game-over handler, not level
completion.  Correspondingly, the three callers of GAME_START_INIT
all sit in this state machine and each represents a distinct restart
scenario.

**How to apply:**  When tracing MAIN_LOOP exits or any "restart" /
"new game" flow, use these labels; the old `LEVEL_COMPLETE` name is
retired.  When evaluating whether `$44` `ZP_RESTART_FLAG` is live
state, remember that `RESTART_DISPATCH` is dead code so the flag is
effectively a dead store.

Final names and roles:

- `$7208 LIFE_LOST_HANDLER` --- fires on `ZP_LIVES_BCD < 0` (BCD
  underflow below $00 = $99, bit 7 set).  MAIN_LOOP's `$682F JMP
  $7208` is the exit arm.  Clears strobe, runs LEVEL_TRANSITION,
  pins SMC_ATTRACT_RTS=$60 ($6827 slot becomes RTS), then animates
  one extra life per iteration of `$8C` (ZP_EXTRA_LIVES), falling
  through to RESTART_NEW_GAME when `$8C == 0`.
- `$720E LIFE_LOST_RESUME` --- sub-entry skipping strobe/transition
  prologue; only reached by the dead RESTART_DISPATCH.
- `$7255 RESTART_NEW_GAME` --- sub-entry at LIFE_LOST_HANDLER's
  `.no_more_lives` branch.  `JSR GAME_START_INIT`, save+silence
  ZP_SFX_CLICK, enable SMC_RENDER, fall into ATTRACT_LOOP.
- `$7299 START_GAME_FROM_ATTRACT` --- sub-entry at end of
  ATTRACT_LOOP.  `JSR GAME_START_INIT`, restore ZP_SFX_CLICK, `JMP
  MAIN_LOOP`.
- `$6AA7 RESUME_GAMEPLAY_SMC` --- SMC-patch sub-entry inside
  LEVEL_INTRO_TICK's `.activate`.  13 bytes:
  `LDA #$06 / STA SMC_SR_YSRC / LDA #$20 / STA SMC_INPUT / STA
  SMC_RENDER / LDA #$13 / STA SMC_SR_HEIGHT / RTS`.  Targeted by
  `JMP RESUME_GAMEPLAY_SMC` at the tail of GAME_START_INIT.
- `$5EC5 RESTART_DISPATCH` --- 15 bytes, **statically dead code**.
  Reads `$44 ZP_RESTART_FLAG` to pick among three paths:
  flag<0 --> JMP MAIN_LOOP; flag==0 --> JMP LIFE_LOST_RESUME;
  flag>0 --> JSR GAME_RESTART ($13C2) then JMP MAIN_LOOP.  No
  JMP/JSR in any of boot1.bin, loader.bin, rwts.bin, or drol.bin
  targets this address (nor anywhere in $5E00-$5EFF, which appears
  to be a legacy RWTS fragment).  `ZP_RESTART_FLAG` is only read
  here --- the `$FF` written to it by GAME_START_INIT's tail is a
  dead store in the live engine.  `GAME_RESTART` ($13C2) is also
  unreached in practice, but kept as a documented sub-entry.

Three live GAME_START_INIT callers (all labeled sub-entries):
- `$6121` inside INPUT_PROCESS.check_restart (Ctrl-R key).
- `$7255` RESTART_NEW_GAME (extras stash exhausted).
- `$7299` START_GAME_FROM_ATTRACT (input at attract screen).

Two MAIN_LOOP game-over exits:
- `$682B LDA $5E / BPL / JMP $7208` --- lives out (HUD counter).
- `$6832 LDA $39 / BPL / JMP $BDA0` --- hit credits out
  (per-hit counter, $BDA0 in relocated RWTS $BE00-$BFFF region).
