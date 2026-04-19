---
name: Drol Apple II soft-switch EQU symbols
description: SW_CASSOUT ($C020) and SW_PAGE2 ($C055) EQUs; plus guidance for adding new I/O soft-switch symbols
type: project
---

SW_CASSOUT ($C020) and SW_PAGE2 ($C055) are EQUs defined in the main
`<<drol defines>>` soft-switches block.  Together with the prior set
(KEYBOARD/KBDSTROBE/SW_SPEAKER/SW_PAGE1/SW_PUSH_BTN0/SW_PUSH_BTN1),
they cover every $C0XX soft-switch read/written by live code paths:

- SW_CASSOUT = $C020: cassette-output toggle.  The game uses it as a
  silent-read target when sound is muted — Ctrl-S flips bit 4 of
  ZP_SFX_CLICK between #<SW_SPEAKER ($30) and #<SW_CASSOUT ($20).
- SW_PAGE2  = $C055: hi-res page 2 soft-switch.  DISPLAY_PAGE_FLIP's
  SMC-patched LDA operand alternates between SW_PAGE1 and SW_PAGE2.

**Why:** CLAUDE.md says raw I/O addresses in code must use symbolic
names.  These two were the only live-path C0XX reads left naked.

**How to apply:** When a new soft-switch appears in a RE'd routine,
add it to the same soft-switches block (line ~2430 in main.nw), with
the Apple II standard name (e.g. SW_PAGE1, SW_PADDLE_TRIG).  Use the
"SW_" prefix consistently.  For sound-related values, write comments
as `#<SW_SPEAKER` / `#<SW_CASSOUT` (not raw `$30`/`$20`) so that
readers can see at a glance which branch of the mute state is intended.

**ZP_DEAD_SLOT_46** ($46) is also defined now: GAME_RESTART has a
single `STX $46` with no reader anywhere in the 5 assembled binaries.
Named so the header plate and prose table can refer to a symbol
instead of leaving raw `$46` in the text.
