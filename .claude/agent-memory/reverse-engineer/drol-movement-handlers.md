---
name: Drol movement action handlers
description: DO_ASCEND/DESCEND/MOVE_RIGHT/MOVE_LEFT at $6378-$64CA; SMC'd per-frame slots; ZP_ASC_FLOOR $0B, ZP_DSC_FLOOR $0C, ZP_FLOOR_MIRROR $0A, ZP_DSC_DIR $0D, ZP_ENT_RESCUED $1D
type: project
---

The 339-byte game-engine-A tail at $6378-$64CA is fully RE'd as four per-frame movement action handlers patched into MAIN_LOOP's SMC slots by INPUT_DO_ASCEND/DESCEND/INPUT_SET_LEFT/INPUT_SET_RIGHT:

- **DO_ASCEND** ($6378, 60 bytes): decrements ZP_PLAYER_COL by 4/frame toward FLOOR_CEIL[ZP_ASC_FLOOR]. Landing at ceiling plays SFX_TONE and decrements ZP_BEAM_TICK. Landing at FLOOR_THRESH propagates floor idx to ZP_BEAM_SEED_FLOOR/ZP_FLOOR_MIRROR/ZP_DSC_FLOOR, sets ZP_ENT_RESCUED=$FF, wipes all 12 ENTITY_HIT_STATE slots.
- **DO_DESCEND** ($63B4): increments ZP_PLAYER_COL by 4/frame toward FLOOR_THRESH[ZP_DSC_FLOOR]. Landing cleanup: propagates floor idx, sets ZP_DSC_DIR=$01 (just-landed), reseeds ZP_BEAM_TICK from ZP_DIFF_THRESH_B, wipes hit-entity slots, clears ZP_ACTION_DIR, patches SMC_DESCEND back to BIT ($2C) to stop firing, then probes SMC_MOVE_LEFT_OP ($67DD) / SMC_MOVE_RIGHT_OP ($67E0) to refresh ZP_LAST_DIR with KEY_LEFT ($88) / KEY_RIGHT ($95) so walk-animation resumes.
- **DO_MOVE_RIGHT** ($6409-$646C) and **DO_MOVE_LEFT** ($646D-$64CA): stance-cycle + wall-clamp + hit-slide. ZP_MOVE_DIR=$01 or $FF, ZP_PLAYER_STANCE clamped to walk range, ZP_FRAME_COUNTER AND $01 gates animation advance on odd frames.

**Key discoveries:**
- **Four parallel floor-index mirrors** at $09/$0A/$0B/$0C are NOT aliases. Each subsystem reads a different one: $09 ZP_BEAM_SEED_FLOOR (beam controller), $0A ZP_FLOOR_MIRROR, $0B ZP_ASC_FLOOR (DO_ASCEND), $0C ZP_DSC_FLOOR (DO_DESCEND). On landing, the completing handler writes its current floor to all three other mirrors so game-state agrees.
- **DO_DESCEND's tail physically interleaves with DO_MOVE_RIGHT.** $63B4-$6408 is DO_DESCEND body, $6409-$643B is DO_MOVE_RIGHT part 1, $643C-$6441 is DESC_LANDED_CLEAR (reached only from DO_DESCEND's BEQ $643C at $63FF), $6442-$646C is DO_MOVE_RIGHT part 2.
- **Hit-entity slot wipe pattern:** `LDX ZP_HIT_MAX; LDA #$FF; STA ENTITY_HIT_STATE,X; DEX; BPL` is the "mark all 12 hit-entities inactive" idiom, used on every floor-transition landing (both ascent and descent). $FF in ENTITY_HIT_STATE is bit-7-set = inactive (consumed by DRAW_ENTITIES phase-1 BPL .hit_restore).
- **ZP_ENT_RESCUED ($1D)** is a "rescue just succeeded or hit just landed" flag. Set $FF by INPUT_DO_ASCEND/DESCEND on entity-found, and by DO_ASCEND/DESCEND on floor-landing. Read by DRAW_PLAYER (suppresses flicker if 0 or negative) and by MR_HIT_SLIDE / ML_HIT_SLIDE (forces motion direction during post-hit slide).
- **SMC_DESCEND self-disables** ($67DA patched to BIT $2C) after landing, but SMC_ASCEND does not — because ascend can loop (continue holding A), while descend is one-shot to the next floor below.

**How to apply:** When RE'ing any routine that reads $0A/$0B/$0C/$1D or that writes FLOOR_CEIL/FLOOR_THRESH tables, cross-reference these handlers. The DESC_LANDED_CLEAR tail at $6442 is NOT part of DO_MOVE_RIGHT despite living inside its address range.
