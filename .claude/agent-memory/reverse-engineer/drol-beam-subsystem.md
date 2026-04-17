---
name: Drol beam subsystem ($130A)
description: BEAM_UPDATE at $130A is the player's laser-beam/tracer subsystem, gated on ZP_PROJ_GATE ($32) by difficulty tier.
type: project
---

`BEAM_UPDATE` ($130A) is the entry point for Drol's laser-beam
subsystem.  It's gated on `ZP_PROJ_GATE` ($32), which
`DIFFICULTY_UPDATE` sets to $FF at minimum/moderate tiers and $01 at
standard/maximum tiers.  So the beam is only available once the
score crosses 10000 points.

Three private sub-routines under BEAM_UPDATE:

- `BEAM_TARGET_TICK` ($1230): state machine for the beam's target.
  `BEAM_STATE` ($03FF) encodes idle / $0X chase / $8X attack with
  the target floor index in low nibble.  `BEAM_Y` ($03FE) advances
  $\pm 2$ per frame toward `FLOOR_Y_TABLE[floor_idx]`.
- `BEAM_TARGET_DRAW` ($1297): draws a vertical sprite trail from
  beam Y to target Y via DRAW_SPRITE; then checks 4 enemy slots at
  `ZP_ENEMY_FLAG/COL/Y` ($9B/$9F/$A3) and awards 100 BCD via
  SCORE_ADD on hit.
- `BEAM_TRACER_SPAWN` ($1376): on odd frames, seeds horizontal
  tracers into a 5-slot table at `TRACER_STATE` ($0237) /
  `TRACER_ROW` ($023C).

BEAM_UPDATE's main body walks the 5-slot tracer table: each active
slot's state byte is both its lifetime and its current screen X
column.  Each frame it decrements and writes a single $7F byte
directly into hi-res at `screen[TRACER_ROW,Y][new_X]`, using
`SMC_TRACER_ADDR_LO/HI` ($1359/$135A) patched inline.  When the
column enters the $12/$13 near-player window, a hit test against
`ZP_PLAYER_COL` ($06) and `TRACER_ROW,Y` (18-row band) may set
`ZP_HIT_FLAG` ($1E) = $FF.

**Why:** Relevant any time you're RE'ing an adjacent routine that
touches $03FE/$03FF, $0237-$0240, $9B/$9F/$A3, $83,X, $F8, $F9.
These overlap the tracer/enemy tables this subsystem owns.

**How to apply:** If another routine reads $03FE/$03FF or writes to
$0237,Y, it's almost certainly interacting with the beam
subsystem --- treat the names `BEAM_STATE`, `BEAM_Y`,
`TRACER_STATE`, `TRACER_ROW` as the authoritative aliases.  Note
that $9B is also `KEY_ESC` in the input dispatcher --- they
genuinely alias the same ZP byte for different subsystems.
