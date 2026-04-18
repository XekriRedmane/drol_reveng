---
name: Drol $5ED4-$5FFF dead twin of RWTS
description: The 300-byte tail of the staging area is a pre-release twin of $BED4-$BFFF; all dead, SM refs point at the live handler
type: project
---

The 300 bytes at [[$5ED4]]--[[$5FFF]] in drol.bin are a near-twin of
[[$BED4]]--[[$BFFF]] in rwts.bin.  Now broken out into six labelled
chunks: STAGE_DEAD_RELOAD / STAGE_DEAD_RESET / STAGE_DEAD_LDR_TRACK /
STAGE_DEAD_SCROLL_UP_PRE / STAGE_DEAD_SCROLL_DN / STAGE_DEAD_ADDR_TBL.

**Why:** The pre-release plan appears to have been to copy
$5E00-$5FFF into $BE00-$BFFF via COPY_ROM_TO_LC, matching the other
boot-chain relocations.  That plan was dropped (rwts.bin is now
assembled directly at $BE00 and relocated wholesale by the loader),
but the staging bytes were never stripped.  $5F48-$5FFF is an exact
byte-for-byte duplicate of $BF48-$BFFF; $5F00-$5F47 matches the
live RESET handler body at $BF00-$BF47 except for one byte
($5F21 = $BE vs $BF21 = $BD — the clear-memory page-start selfmod).
Only $5ED4-$5EFF (44 bytes) is genuinely unique code not found in
rwts.bin.

**How to apply:** When encountering raw hex blobs in the staging
area or residue of relocated code, look for pre-relocation twins
elsewhere in the image.  Self-modifying references inside a "dead
twin" often still point at the LIVE handler's SM byte (e.g.
STAGE_DEAD_RESET's DEC $BF21 / LDA $BF21 at $5F25/$5F2B reference
the live RESET_R's SM byte, not the twin's own $5F21).  This is a
telltale sign the twin was cloned but its internal self-refs were
never updated.  Do not treat these as live code; verify no JSR/JMP
targets any address in the block before declaring dead.
