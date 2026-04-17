---
name: Drol difficulty tier ZP variables
description: Six ZP bytes ($31/$32/$33/$34/$35/$40) form the difficulty-tier state, written by DIFFICULTY_UPDATE ($719D) and read across the engine.
type: project
---

`DIFFICULTY_UPDATE` at $719D writes a tier preset to six shared ZP bytes
each time the frame counter wraps ($FD = 0, every ~256 frames).  The bytes
are read by multiple engine routines:

- `$31` = `ZP_PROJ_MAX` (max projectile slot index, read by HAZARD_CHECK at $0E5A — BMI guard means $FF = no projectiles)
- `$32` = `ZP_PROJ_GATE` (gate, read at entry of BEAM_UPDATE $130A — $FF = subsystem off; beam disabled at minimum/moderate tiers, enabled at standard/maximum)
- `$33` = `ZP_COMPANION_GATE` (companion slot gate, read by DRAW_ENTITIES phase 4)
- `$34` = `ZP_DIFF_THRESH_A` (primary tier threshold — consumer not yet identified)
- `$35` = `ZP_DIFF_THRESH_B` (secondary tier threshold — consumer not yet identified)
- `$40` = `ZP_ADVANCE_RATE` (16-bit timer decrement rate, read by $13F7 and $1675 as `SBC $40` against event counters at $DD/$DE and $D5/$D6)

Tier preset table (from DIFFICULTY_UPDATE):

| Tier (score) | Index | $31 | $32 | $33 | $34 | $35 | $40 |
|--------------|-------|-----|-----|-----|-----|-----|-----|
| Min (<4000)  | <$04  | $FF | $FF | $FF | $00 | $50 | $01 |
| Moderate     | $04-$0F | $00 | $FF | $01 | $40 | --- | --- |
| Standard     | $10-$17 | $01 | $01 | $01 | $80 | --- | $02 |
| Max (18000+) | $18+  | $03 | $01 | $01 | $F0 | $30 | $03 |

(--- means preset leaves prior value.)

**Why:** When RE'ing routines at $130A, $13F4, $1670, or any other that
reads $31-$35 or $40, consult this table to understand the semantics of
each value.

**How to apply:** If a routine does `LDA $32; BPL skip; RTS` the "gate"
semantics come from the difficulty-tier preset. If a routine does
`SBC $40` on a 16-bit counter, the countdown rate is tier-dependent.
