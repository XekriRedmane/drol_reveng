---
name: Drol RWTS zero-page symbols
description: RWTS chapter uses $A0-$A3 as generic 16-bit scratch pointer pairs reused across 6 routines; DIVIDE uses $CE/$DA/$E6 as dividend/divisor/remainder
type: project
---

The RWTS chapter (output to rwts.asm, living at $BE00-$BFFF) uses
$A0/$A1 and $A2/$A3 as two generic 16-bit scratch pointer pairs,
reused by 6 routines for different purposes:

- RWTS_RELOAD: INC $A0/$A1 bumps the SCROLL_UP buffer pointer
- NIBBLE_READER: $A0 is nibble-combine scratch BYTE (not pointer);
  $A1 is destination-page counter; $A2/$A3 is decode destination
- SCREEN_RESTORE: $A0/$A1 is hi-res line/screen-hole dest pointer
- COPY_ROM_TO_LC: $A0/$A1 is simultaneously ROM source + LC dest
- SCROLL_UP/DN: $A0/$A1 is buffer pointer, $A2/$A3 is screen-row pointer

**Why:** This is the classic 6502 ZP-aliasing pattern — the same two
pointer pairs serve distinct purposes in distinct routines.

**How to apply:** In the RWTS chunks, use symbolic aliases from
rwts defines: ZP_RWTS_PTR ($A0), ZP_RWTS_PTR2 ($A2),
ZP_RWTS_SCRATCH ($A0, nibble-combine temp), ZP_RWTS_PAGECNT ($A1,
nibble page counter). In drol.asm (not rwts.asm), the same
addresses are aliased as ZP_STREAM = $A0 and ZP_UNPACK_DEST = $A2.
The stage_dead_scroll_up/dn dead-code twins in drol.asm must
remain raw $A0-$A3 because adding ZP_RWTS_PTR to drol defines
would duplicate the game's drol-defines ZP symbols.

DIVIDE at $BE7A uses three 16-bit word operands:
- ZP_DIV_DIVIDEND = $CE (shifted out and replaced by quotient)
- ZP_DIV_DIVISOR = $DA (stays put)
- ZP_DIV_REMAINDER = $E6 (accumulates via ROL chain)

These are Applesoft Ampersand-style patch entry points; the
routine is never called by the game itself — it's an Applesoft
extension installed by the reset handler that user BASIC code
could invoke.
