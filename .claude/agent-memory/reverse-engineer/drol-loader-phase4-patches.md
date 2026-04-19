---
name: Drol loader Phase 4 SMC patches
description: Three loader-time SMC patches — SMC_ATTRACT_EXIT_JMP redirects cold-boot + two IIc key-code CMPs
type: project
---

Loader `FIRST_BOOT`'s Phase 4 writes three self-modifying bytes inside
the freshly-loaded game image before `JMP (ZP_GAME_ENTRY)`:

- `SMC_ATTRACT_EXIT_JMP` ($72BA): JMP operand in START_ATTRACT.
  Unconditionally patched from `#<ATTRACT_LOOP` ($63) to
  `#<LIFE_LOST_HANDLER` ($08). The shipped `JMP ATTRACT_LOOP` byte
  sequence never executes as shipped — every cold boot lands in
  LIFE_LOST_HANDLER first (extras stash is zero, so it falls through to
  RESTART_NEW_GAME → GAME_START_INIT → ATTRACT_LOOP).

- `SMC_KEY_RIGHT` ($600E) and `SMC_KEY_LEFT` ($6022): immediate
  operands of the two arrow-key CMPs in INPUT_DISPATCH. Patched to
  `KEY_IIC_RIGHT` ($CC) / `KEY_IIC_LEFT` ($CB) only when
  `ROM_MACHID == MACHID_IIC` ($08). Apple IIc arrow keys emit 'K'/'L'
  with high bit set, not the standard II/IIe $88/$95.

**Why:** the game was originally built for II/IIe keycodes; IIc
keyboards required a one-byte patch per direction. The START_ATTRACT
redirect unifies the cold-boot entry with the end-of-life path so a
single routine (LIFE_LOST_HANDLER) handles both.

**How to apply:** when inspecting cold-boot flow, trust the patched
JMP target (LIFE_LOST_HANDLER), not the shipped bytes at $72B9-$72BB.
When documenting keyboard input on IIc, `KEY_LEFT`/`KEY_RIGHT` EQUs
are the II/IIe values only — the runtime compares against the IIc
codes after patch.
