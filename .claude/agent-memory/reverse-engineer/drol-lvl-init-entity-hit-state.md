---
name: LVL_INIT_ENTITY_HIT_STATE $FF seed
description: The 12-byte $FF span at $02BA-$02C5 is NOT dasm fill — it's real LVL_INIT_SPRITE payload seeding ENTITY_HIT_STATE (ZP $8D-$98) to all-inactive on every level restart
type: project
---

$02BA-$02C5 on disk is 12 bytes of $FF that form LVL_INIT_SPRITE[$05..$10],
which INIT_LEVEL_STATE copies into ZP $8D-$98 (the 12-slot
ENTITY_HIT_STATE array).  Seeds every hit-entity slot to $FF ("inactive")
at cold start and on every level restart.

**Why:** earlier prose in `<<lvl init sprite tail data>>` called this span
"dasm FF-fill (unreferenced by the game)".  That was wrong --- the bytes
ARE consumed by INIT_LEVEL_STATE because the source LDX starts at $2C
and counts down to $00, covering all 45 bytes at $02B5-$02E1 including
the $02BA-$02C5 $FF span.  INIT_LEVEL_STATE reads from $02B5+X, so X=$05
reads $02BA, through X=$10 reads $02C5.

**How to apply:** when a cold-start ZP array needs a per-level seed that
differs from its ZP_SAVE image, look for gaps in the LVL_INIT_*
source layout.  The gap may look like dasm fill but can be load-bearing.
Symbol: LVL_INIT_ENTITY_HIT_STATE (label on the dedicated DS 12,$FF
chunk at $02BA).
