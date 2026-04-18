---
name: Drol $5C00-$5FFF staging-buffers region
description: STAGE_STACK at $5C00 is a live SCREEN_ROW_COPY duplicate used as loader callback; rest of region is mostly dead residue
type: project
---

$5C00-$5FFF is the "staging buffers" region, a 1024-byte blob loaded
from the first two sectors of track 1 into the game address space.
Split into:

- **$5C00-$5C2A (43 bytes)**: STAGE_STACK — a byte-identical duplicate
  of SCREEN_ROW_COPY at $0100. The ONLY live entry point in the whole
  region. Called by loader.bin's SCREEN_PRE_RESTORE at $58A0 and its
  relocated copy at $BEA0 before the screen wipe/restore. The
  duplicate exists because the $0100 stack page gets overwritten by
  6502 stack operations during normal play, and the loader needs a
  stable copy at a known address.
- **$5C2B-$5CEF (197 bytes)**: Dead mirror of $012B-$01EF
  (JOYSTICK_HANDLER + KEY_HANDLER_EXT + ROW_COPY_CLICK + dead
  variants). This is the install-time source: FIRST_BOOT copies 240
  bytes from STAGE_STACK -> STACK_PAGE to seed $0100.
- **$5CF0-$5CFF**: 16 bytes of residue (NOT a mirror of $01F0 which
  is zero-padded).
- **$5D00-$5DEF**: STAGE_VECTORS — mirror of $0300-$03EF (TEXT_STRIP_SRC
  dither pattern + small data tables). FIRST_BOOT copies these 240
  bytes to VECTOR_PAGE at $0300.
- **$5DF0-$5DFF**: 16 bytes of residue.
- **$5E00-$5EC4 (197 bytes)**: STAGE_RESIDUE_DEAD — an orphan fragment
  of a Disk II nibble-level sector reader (reads $C089/$C08A/$C08B
  drive-phase soft-switches, $C08C data latch, $C08E ROM-read),
  falling through into RESTART_DISPATCH at $5EC5. Zero live callers.
- **$5EC5-$5ED3**: RESTART_DISPATCH (previously documented dead).
- **$5ED4-$5FFF**: More dead residue (another 300 bytes; previously
  documented).

**Why:** Understanding this region was confusing because the bytes look
like a code blob but only the first 43 bytes are live. The rest is
disk-image residue preserved verbatim for byte-exactness.

**How to apply:** When encountering "staging buffers" in the prose,
remember only STAGE_STACK ($5C00) entry is runtime-live. The region's
dual purpose (install-time source AND stable-callback entry) is the
design insight.
