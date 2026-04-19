---
name: PILLAR_SLOT_Y at ZP $60-$65
description: 6-byte read-only ZP array of world-Y landmark positions consumed by REFRESH_PILLARS; never written at runtime
type: project
---

[[PILLAR_SLOT_Y]] (ZP [[$60]]--[[$65]]) is a 6-slot read-only table of
world-Y landmark positions. [[REFRESH_PILLARS]] reads each slot,
subtracts [[ZP_PLAYER_Y]] to compute a screen column, and paints a
4-column pillar sprite there when the delta is in [[$00]]..[[$2A]].

**Why:** The slots are never written by any code in [[drol.bin]] or
[[level1.bin]]; they inherit their values from [[ZP_SAVE]] (the
loader's cold-start zero-page image) which places the six landmarks
in the playfield frame.

**How to apply:** Any time a future RE pass encounters `$60,X`-style
ZP reads of 6 consecutive bytes in playfield code, that's this
landmark table; replace with `PILLAR_SLOT_Y,X`. The [[$60]]--[[$65]]
slots are distinct from every other six-byte ZP block — they're
fixed playfield geometry, not active entity state.
