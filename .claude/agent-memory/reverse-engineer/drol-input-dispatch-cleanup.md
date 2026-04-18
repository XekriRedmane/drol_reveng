---
name: INPUT_DISPATCH symbol cleanup
description: INPUT_DISPATCH/INPUT_DO_ASCEND/INPUT_DO_DESCEND at $6000-$6108 now use ZP_PLAYER_STANCE/ZP_ACTION_DIR/ZP_MOVE_DIR/ZP_PLAYER_COL/ZP_ASC_FLOOR/ZP_DSC_FLOOR/ZP_DSC_DIR/ZP_ENT_RESCUED/ENTITY_HIT_STATE/ENTITY_HIT_ROW/ENTITY_HIT_Y/FLOOR_THRESH instead of raw hex
type: project
---

Shared-ZP EQUs (ZP_ASC_FLOOR, ZP_FLOOR_MIRROR, ZP_DSC_FLOOR, ZP_DSC_DIR, ZP_ENT_RESCUED, ENTITY_HIT_Y) moved from `<<movement handlers defines>>` and `<<refresh hit entities defines>>` into `<<drol input defines>>` because INPUT_DO_ASCEND/INPUT_DO_DESCEND at $6000 seed them before DO_ASCEND/DO_DESCEND at $6378 and REFRESH_HIT_ENTITIES at $631D consume them.

**Why:** Chunk-placement rule requires the defines chunk for a label to sit immediately before the first chunk that uses it. With INPUT_DISPATCH now using symbolic names (previously raw $XX), the shared EQUs needed to move to the earliest caller's defines chunk.

**How to apply:** When adding new EQUs shared across multiple game-code chunks, put them in the defines chunk preceding the earliest user. For ZP state that bridges input handling and movement handling, `<<drol input defines>>` is the canonical location.
