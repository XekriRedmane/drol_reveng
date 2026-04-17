---
name: Drol SFX architecture
description: How Drol's sole sound routine SFX_TONE uses an indirect ZP pointer to mute via address redirection rather than a branch
type: project
---

Drol's only sound-effect generator is SFX_TONE at $67C1 (called from
~8 sites).  It is a classic Apple II nested delay-loop speaker-click:
A = pitch (inner delay cycles), X = duration (number of clicks).

**Key architectural trick:**
The speaker access is done indirectly via `CMP ($36),Y` (Y=0 after the
inner DEY/BNE loop).  The pointer at $36/$37 is constructed so that:

- $37 = $C0 (fixed; boot-state ZP, never written by game code)
- $36 = $30 (sound ON → pointer = $C030 = SW_SPEAKER, click!)
- $36 = $20 (sound OFF → pointer = $C020 = cassette-output soft switch, silent)

Ctrl-S (`INPUT_PROCESS`) flips bit 4 of $36 to mute/unmute.  Bit 4 is
exactly the XOR distance between $30 and $20, so `EOR #$10` cleanly
toggles between the two addresses.

The SFX_TONE loop always executes the CMP — there is no branch to skip
sound output when muted.  Silence is achieved by redirecting to an
unused soft switch.  This is cheaper than a branch and doesn't affect
timing between sound-on and sound-off (important for delay calls that
use SFX_TONE purely for timing).

**Why:** discovered while RE'ing $67C1 (called from LEVEL_INTRO_TICK,
attract loop, hazard handler, etc.) in 2026-04.  The `CMP ($36),Y`
addressing mode was the giveaway — readers of ZP $36 thought it was a
pointer, but it's actually a *deliberately constructed* pointer whose
low byte encodes the mute state.

**How to apply:** when seeing `CMP ($36),Y`, `LDA ($36),Y`, or similar
indirect reads in Drol, the target is the speaker.  ZP aliases:
`ZP_SFX_CLICK = $36`, `ZP_SFX_CLICK_SAVED = $38`, `SOUND_FLAG_MASK = $10`.
$38 is a preserved copy of $36 across attract/game transitions
(ATTRACT_LOOP restores $38→$36 on game start; LEVEL_COMPLETE's
`.no_more_lives` saves $36→$38 and forces $36=$20 silent for attract).
