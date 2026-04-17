---
name: Drol companion slot subsystem
description: COMPANION_UPDATE at $6CFE — two-slot hostile walker that patrols floors, climbs on rescue-entity proximity, hits player
type: project
---

Drol's `COMPANION_UPDATE` at $6CFE is the per-frame tick+draw routine for a two-slot subsystem named "companion" after DRAW_ENTITIES phase 4's naming. Despite the label, these slots are **hostile** walker-creatures (monsters/enemies), not helpers — they damage the player on contact.

**Why:** The name "companion" is inherited from DRAW_ENTITIES phase 4 prose and kept for consistency with the $11/$13/$15 ZP array names `ZP_COMPANION_COL/OFF/ROW`. The tick's behavior contradicts the "companion" connotation: it sets `ZP_HIT_FLAG` ($1E) on player overlap.

**How to apply:** When documenting routines in this region or cross-referencing, remember:
- $B3,X (slot 0 = $B3, slot 1 = $B4) is `ZP_COMPANION_STATE`: $00 inactive → auto-activate, +ve active, $FF drift (climbing).
- $B1,X is `ZP_COMPANION_DIR`: $01 right, $FF left, $00 treated as right.
- $11/$13,X is 16-bit world-X (LO/HI) — same bytes aliased as `ZP_COMPANION_COL/OFF` in DRAW_ENTITIES phase 4's marker draw.
- $15,X is row Y.
- Gate `ZP_COMPANION_GATE` ($33): positive = active, $FF = suppressed.
- DIFFICULTY_UPDATE sets $33 = $01 on all non-minimum tiers (score >= 4000); minimum tier/DIFFICULTY_RESET sets $FF.
- Both slots auto-activate whenever gate is open — nothing externally writes $B3,X. Companions are permanently present once unlocked.
- Drift trigger: hit-entity (in $8D,X table, bounded by $41) with matching `ENTITY_HIT_ROW` ($72,X) when companion screen-X is in [$40, $47).
- Drift handler advances row by 4 per frame until hitting a floor-anchor row ($63/$8B/$B3), then re-arms to active.
- Player-catch hit-box: screen-X in [$40, $50) AND player row ($06) within [row-8, row+$12) of companion row.
- 3-pose SMC walk cycle per direction. Pose tables:
  - +dir: $75B7/$75BE/$75C5 (low pointers), $76B7/$76BE/$76C5 (high)
  - -dir: $75A2/$75A9/$75B0 (low pointers), $76A2/$76A9/$76B0 (high)
  - SMC trampolines: JMP at $6E30 (+dir), $6EA9 (-dir). Operand bytes $6E31/$6E32, $6EAA/$6EAB patched by each pose handler to point to next pose.
- Row reload on rearm: `FLOOR_THRESH` ($83,X) with X = `ZP_PLAYER_FLOOR` ($0A), plus $0B.
