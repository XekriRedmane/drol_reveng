---
name: Drol movement dispatch topology
description: How player horizontal motion is encoded in $04 and dispatched via PLAYER_MOVE_TICK to the three PLAYER_TICK_* handlers
type: project
---

PLAYER_MOVE_TICK at $64CB is a 20-byte tri-state dispatcher on
ZP_MOVE_DIR ($04): $00=idle/$FF=left/$01=right.  It routes to three
per-frame tick handlers at $614B-$61EF (all fully RE'd, see
drol-player-tick-handlers.md):

- `PLAYER_TICK_MOVE_LEFT` ($614B): 7-step sub-frame pacing via
  ZP_SPRITE_XREF gates DEC ZP_PLAYER_Y; advances ZP_WALK_FRAME
  (mod 10, +2) and ZP_SPRITE_XREF (+2 with $FE/$FF wrap seeds at
  states 5/6).  Falls through into PLAYER_TICK_IDLE.
- `PLAYER_TICK_IDLE` ($6184): 7 per-frame JSR calls
  (CLEAR_DRAW_PAGE, TEXT_ROW_DISPATCH, REFRESH_LEFT_WALL,
  REFRESH_RIGHT_WALL, REFRESH_FLOOR_LINES, REFRESH_PILLARS,
  REFRESH_HIT_ENTITIES), then RTS.
- `PLAYER_TICK_MOVE_RIGHT` ($619A): mirror of left; INC ZP_PLAYER_Y
  gated by ZP_SPRITE_XREF pacing, -2 advance with $07/$08 wrap
  seeds at states 0/1; inline tick chain swaps the walls
  (RIGHT before LEFT) then JMPs to PLAYER_IDLE_TICK_TAIL ($6190)
  to rejoin REFRESH_FLOOR_LINES onward.

**Why:** The $6184 idle handler is the core per-frame tick; moving
left/right variants optionally advance the player's world position
($4A = ZP_PLAYER_Y, but in Drol this index also controls horizontal
perspective scaling via PERSPECTIVE_XOFF_LO/HI tables at $1A8F/$198F)
and step walking-animation frames at $4B/$4C.  Horizontal motion is
paced at 4/7 of frame rate via the ZP_SPRITE_XREF sub-frame counter.

**How to apply:** When tracing frame dispatch: MAIN_LOOP ->
PLAYER_MOVE_TICK -> PLAYER_TICK_* -> the 7 refresh routines.
IDLE paints walls LEFT then RIGHT; MOVE_RIGHT reverses them.  All
7 routines in the chain are now RE'd.

ZP_MOVE_DIR ($04) is set by DO_MOVE_RIGHT ($6409, sets $04=$01) and
DO_MOVE_LEFT ($646D, sets $04=$FF).  Both now fully RE'd --- see
drol-movement-handlers.md for the four DO_* action handlers at
$6378-$64CA.  Cleared on direction change, clamp, rescue, and by
INIT_LEVEL_STATE / LEVEL_INTRO_TICK init.  Also read by HAZARD_CHECK
($0E5A) as a parallax cue: projectiles moving opposite the player's
horizontal motion gain +2 pixels per frame.

The prior `ZP_FAST_FLAG` name in HAZARD_CHECK was a misreading ---
$04 is not a difficulty speed flag, it's player horizontal move
direction.  The "fast" behavior is incidental parallax.
