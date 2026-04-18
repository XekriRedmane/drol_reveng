---
name: Drol jump-flag as floor-enemy spawn one-shot
description: ZP_JUMP_FLAG ($05) double-duty: jump key signal AND floor-enemy spawn gate; a jump press spawns at most one new floor-enemy if level schedule permits
type: project
---

`ZP_JUMP_FLAG` at `$05` is written $FF by both `JOYSTICK_HANDLER` (button press) and `INPUT_DISPATCH.check_jump` (space key). It is read and cleared by `FLOOR_ENEMY_ADVANCE` ($6683) at two points:
1. `BIT ZP_JUMP_FLAG / BMI .spawn` -- gates spawn of a new floor enemy on the flag being negative ($FF).
2. At the end of the X=3..0 slot loop, if no slot consumed it, `LDA #$00 / STA ZP_JUMP_FLAG` clears it anyway.
The `.spawn` path also does `LDA #$00 / STA ZP_JUMP_FLAG` up front so that only one slot per jump-press consumes the one-shot.

**Why:** This is a surprising mechanic -- a single ZP byte is shared between "the player pressed jump" and "floor-enemy spawn is armed". There is no dedicated "spawn timer"; the game uses the jump key as the spawn trigger. The level-data table `FLOOR_ENEMY_SPAWN_SCHED = $1CB8` (indexed by ZP_PLAYER_COL) then decides whether the spawn actually happens at the player's current column, and if so also seeds the new enemy's row as `schedule_index + 9`. Also note that LEVEL_INTRO_TICK's init clears $05 too, so jumps before the level starts are swallowed.

**How to apply:**
- Any code writing $FF to $05 is a "jump-press" signal that *also* arms one floor-enemy spawn.
- The floor-enemy spawn schedule `$1CB8` is per-level data; in level 1 it is baked into the `$188A-$1CED` data blob. In other levels it would load different bytes to the same address.
- Don't assume $05 is "just" the jump flag -- it is both. Any future code that clears $05 has the side effect of disarming a floor-enemy spawn.
