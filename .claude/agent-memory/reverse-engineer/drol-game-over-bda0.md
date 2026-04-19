---
name: Drol GAME_OVER at $BDA0
description: End-of-game handler in level1.bin; disk-reload + page-2 dissolve + 3-way restart dispatch on ZP_RESTART_FLAG
type: project
---

GAME_OVER at $BDA0 (level1.bin, outside drol.bin) is the tail MAIN_LOOP
falls to when ZP_GAME_OVER goes negative. Called via JMP from $6836.

**Why:** The routine splits into four phases (screen dissolve, reload
level, reseed score/HUD/player state, 192-row page-2->page-1 wipe with
per-row speaker click, 3-way continuation dispatch on ZP_RESTART_FLAG).

**How to apply:**
- The routine uses ZP_HGR_SRC ($29) as the *write* pointer and ZP_HGR_DST
  ($2F) as the *read* pointer — opposite roles from START_ATTRACT.
- ZP_RESTART_FLAG ($44) is a dual-role byte (also ZP_JOY_FLAG). GAME_OVER
  dispatches:
  - `== 0` -> JMP LIFE_LOST_RESUME ($720E, skips KBDSTROBE + LEVEL_TRANSITION)
  - `< 0` (bit 7 set: joystick or $FF from GAME_START_INIT) -> JMP MAIN_LOOP
  - `> 0` -> JSR GAME_RESTART (resets lives/score/flag to $FF), JMP MAIN_LOOP
- Side effect: GAME_RESTART sets $44 = $FF, so subsequent GAME_OVER entries
  take the joystick/direct-return branch.
- level1.asm needs cross-target EQU aliases for every drol.asm/rwts.asm
  symbol it references. The `<<level1 defines>>` chunk at line ~21058
  holds the shared declaration block; keep in sync with authoritative
  defines in drol chapters.
