---
name: Drol ZP $37 assumption
description: ZP address $37 in Drol is never explicitly written by game code; it relies on $C0 being present from boot-time ZP state
type: project
---

Drol's SFX_TONE uses `CMP ($36),Y`, which forms a pointer from $36/$37.
The high byte at $37 must be $C0 for sound to work (points at $C0xx
soft switches).

**Grep evidence:** `STA $37`, `STX $37`, `STY $37` do not appear
anywhere in drol.bin, loader.bin, rwts.bin, or boot1.bin disassembly.
$37 is also not in the range copied by INIT_LEVEL_STATE's buffer
restore ($02E2→$01..$1E only covers $01..$1E).

**Why:** the game assumes the boot process leaves $37 containing $C0.
This is plausibly true because the Apple II Disk II P5A boot PROM at
$C600 uses ZP $26..$3F as scratch during sector reading, and the last
byte written to $37 during boot ends up being $C0 (the page of the
slot's I/O soft-switches).  This was never formally verified by
tracing the boot PROM.

**How to apply:** if ever building a fresh Drol emulator that doesn't
go through the real Apple II boot ROM, $37 must be seeded to $C0 or
sound won't work (will silently read junk from somewhere else).  Also,
if future RE finds a `STA $37` somewhere we missed, update this memory
and reconsider the assumption.
