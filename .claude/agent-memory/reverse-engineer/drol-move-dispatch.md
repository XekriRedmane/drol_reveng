---
name: Drol movement dispatch topology
description: How player horizontal motion is encoded in $04 and dispatched via PLAYER_MOVE_TICK, plus the location of the still-HEX-blobbed movement handlers inside game engine A
type: project
---

PLAYER_MOVE_TICK at $64CB is a 20-byte tri-state dispatcher on
ZP_MOVE_DIR ($04): $00=idle/$FF=left/$01=right.  It routes to three
per-frame tick handlers that still live inside the `<<game engine A>>`
HEX blob at $614B-$64CA:

- `PLAYER_TICK_MOVE_LEFT` ($614B): DEC $4A, cycle $4B (mod 12, step -2),
  $4C state-machine with $FE/$FF/$02 transitions.  Falls through to idle.
- `PLAYER_TICK_IDLE` ($6184): 7 per-frame JSR calls
  ($61E4, $636C, $626A, $61F0, $62CA, $62E2, $6321).
- `PLAYER_TICK_MOVE_RIGHT` ($619A): INC $4A, cycle $4B (mod 12, step -2 w/
  wrap at $0A->$FF, $09->$FE), $4C state with $07/$08/$FE transitions.
  JMPs to $6190 to join the last 3 per-frame calls.

**Why:** The $6184 idle handler is the core per-frame tick; moving
left/right variants optionally advance the player's world position
($4A = ZP_PLAYER_Y, but in Drol this index also controls horizontal
perspective scaling via PERSPECTIVE_XOFF_LO/HI tables at $1A8F/$198F)
and step walking-animation frames at $4B/$4C.

**How to apply:** When RE'ing the remaining game engine A tail
($614B-$64CA, 896 bytes), remember that the movement handlers aren't
a clean linear region --- $614B falls through into $6184, and $619A
JMPs into the middle of $6184's 7-call sequence, so carving them out
cleanly will require preserving these control-flow quirks.  The 7
per-frame routines at $61E4, $636C, $626A, $61F0, $62CA, $62E2, $6321
are the next logical RE targets inside the blob.

ZP_MOVE_DIR ($04) is set by DO_MOVE_RIGHT ($6409, sets $04=$01) and
DO_MOVE_LEFT ($646D, sets $04=$FF), both also still inside the game
engine A hex tail.  Cleared on direction change, clamp, rescue, and
by INIT_LEVEL_STATE / LEVEL_INTRO_TICK init.  Also read by
HAZARD_CHECK ($0E5A) as a parallax cue: projectiles moving opposite
the player's horizontal motion gain +2 pixels per frame.

The prior `ZP_FAST_FLAG` name in HAZARD_CHECK was a misreading ---
$04 is not a difficulty speed flag, it's player horizontal move
direction.  The "fast" behavior is incidental parallax.
