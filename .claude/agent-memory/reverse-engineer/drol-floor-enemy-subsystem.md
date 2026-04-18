---
name: Drol floor-enemy subsystem
description: Fourth enemy class at $6683/$673B (4 slots, ZP $9B/$9F/$A3), main-loop subsystem distinct from enemy A/B/C and rescue/special/companion
type: project
---

The 4-slot floor-enemy subsystem lives at:

- `FLOOR_ENEMY_ADVANCE` at `$6683` (184 bytes) - AI advance + spawn (was misnamed SCREEN_EFFECTS).
- `FLOOR_ENEMY_DRAW` at `$673B` (134 bytes) - per-slot perspective draw (was misnamed SCORE_DISPLAY).

**Why:** MAIN_LOOP has a 4-slot floor-enemy pair sandwiched between the rendering subsystems; pre-RE naming (SCREEN_EFFECTS / SCORE_DISPLAY) was based on MAIN_LOOP position not function. No "score display" JSR exists in MAIN_LOOP - digit drawing happens inside POST_FRAME via DRAW_DIGIT.

**How to apply:**
- Any code reading/writing `ZP_ENEMY_FLAG`/`ZP_ENEMY_COL`/`ZP_ENEMY_Y` ($9B/$9F/$A3) is touching the floor-enemy slots; pair draw+advance.
- Spawn direction is decided by probing the main loop's `SMC_MOVE_LEFT` opcode byte at `$67DD` (opcode $20 = JSR = moving left). Enemies always approach from the player's current motion direction.
- Draw uses 4 per-slot 7-entry sprite-pointer tables at $755C/$7563/$756A/$7571 (LO) and $765C/$7663/$766A/$7671 (HI), indexed by `PROJ_FRAME_IDX[ZP_ENEMY_COL,X]`.
- Collision semantics: beam/rescue/enemy-C can all clear a floor-enemy slot by writing $00 to $9B[X].
- Advance is now fully annotated with local labels: .slot_body .maybe_spawn .next_slot .spawn .spawn_do .spawn_right .advance_neg .advance_neg_body .advance_pos (+ .pos_dir_zero/_neg, .pos_store, .despawn_pos; .neg_dir_zero/_neg, .neg_store, .despawn_neg).
- Spawn one-shot is `ZP_JUMP_FLAG` ($05): the jump key sets it $FF, FLOOR_ENEMY_ADVANCE gates spawn on it being negative and clears it (so at most one new slot per jump-key press).
- Spawn-schedule table is `FLOOR_ENEMY_SPAWN_SCHED = $1CB8` (256 bytes, lives in the $188A-$1CED level-1 data blob). Indexed by ZP_PLAYER_COL; negative entry suppresses spawn for that column; non-negative entry seeds the row as `Y = schedule_index + 9`.
- Spawn scratch `ZP_ENEMY_SAVE_Y = $1C` (preserves Y across JSR SND_DELAY_DOWN).
- Advance step per frame depends on ZP_MOVE_DIR ($04): for positive slots +5/+7/+9 (right/idle/left), for negative slots -5/-7/-9 (left/idle/right) -- parallax, fastest closing when player moves opposite to slot direction.
- Despawn test: positive slots at col >= $8F; negative slots at (col - 2) >= $8D (i.e. wraps past 0 into high range).
