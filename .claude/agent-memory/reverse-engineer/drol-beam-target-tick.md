---
name: Drol BEAM_TARGET_TICK at $1230
description: Beam state machine per-frame advance; chase/attack phases with per-floor FLOOR_CEIL ($7E) ceiling table and ZP_BEAM_SEED_FLOOR ($09) floor-index mirror
type: project
---

$1230 BEAM_TARGET_TICK is one of three sub-handlers called from BEAM_UPDATE ($130A). Drives BEAM_STATE ($03FF) and BEAM_Y ($03FE) through idle/chase/attack phases. Attack-phase flag is `ORA #$F0` (sets bits 4-7), not just bit 7 as earlier prose claimed — state format is `$Fn` with n=target floor idx, tested via BMI + masked with AND #$0F.

**Why:** Earlier prose at $1230 had this as a HEX blob awaiting RE. Fully disassembled 103 bytes into 6 labeled sections (jingle tick, dispatch, idle/seed, attack, chase).

**How to apply:** The FLOOR_CEIL ($7E) per-floor ceiling-row table is also read by DO_ASCEND at $6378 (hex blob in game engine A tail $6378-$64CA), paired with FLOOR_THRESH ($83). When disassembling DO_ASCEND/DO_DESCEND later, preserve FLOOR_CEIL usage. ZP_BEAM_SEED_FLOOR ($09) is one of four parallel floor-index mirrors at $09/$0A/$0B/$0C — each subsystem reads a different mirror. $09 is beam-specific.
