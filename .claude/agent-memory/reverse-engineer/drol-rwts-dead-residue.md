---
name: Drol RWTS dead-code residue
description: $BEFD "JMP $1255" is 3-byte padding after COPY_ROM_TO_LC RTS; $BF4F "JMP $28A0" is dead delegation whose operand bytes serve as LDY #$28 at SCROLL_UP
type: project
---

Two 3-byte `JMP` sequences in the RWTS/reset region that look like code but
are functionally dead. Both previously carried stub EQUs (`GAME_ROUTINE_1255`,
`GAME_SCROLL_HANDLER`) as if their targets were real routines; neither
target is.

**$BEFD: `JMP $1255` (3 bytes after COPY_ROM_TO_LC's RTS).**
Pure padding between the RTS at $BEFC and RESET_R at $BF00. $1255 lands
inside BEAM_TARGET_TICK's `.seed` body — specifically the $03 LSB of
`STX BEAM_STATE` ($8E FF 03) followed by the RTS at $1256. Executing
`JMP $1255` would run `.byte $03` (illegal NMOS opcode). No JSR/JMP
anywhere in the binary targets $1255 other than this dead JMP. Now
emitted as `HEX 4C 55 12` with a comment explaining the residue.

**$BF4F: `JMP $28A0` (3 bytes inside SCROLL_UP_PRE).**
SCROLL_UP_PRE at $BF4B would delegate to the "game scroll handler" at
$28A0 (hi-res page 1 framebuffer address — not a real routine) if
called with A != $FF. But SCROLL_UP_PRE has no callers in the shipped
game; only SCROLL_UP = SCROLL_UP_PRE + 5 is called. The JMP's operand
bytes ($A0 $28) are reused as `LDY #$28` when entered at SCROLL_UP.
Now emitted as `HEX 4C A0 28` with prose explaining the byte-overlap
trick. The delegation is "abandoned feature" residue.

**Why:** Both stub EQUs made the surrounding code look like it had
callees into the game engine at those addresses. Removing the EQUs and
emitting raw bytes with comments makes the dead-code reality visible.

**How to apply:** When tackling new areas and finding `JMP $XXXX` to
an address that seems out-of-place, verify (a) whether the call site
is reachable, (b) whether the target decodes as sane code, and (c)
whether the byte sequence is actually being used as data (overlap
trick). Don't reflexively create stub EQUs — document as raw bytes if
the target isn't real.

**Related fix:** `STA $03F3` / `STA $03F4` in RESET_BANG were raw
addresses; now use `SOFTEV+1` / `SOFTEV_CHK` (added to rwts defines).
Comment was also wrong ("Low byte (= $08, harmless value)") — the
value is $07 (last page counter from the clear-memory loop's
fall-through), and $03F3 is the **high** byte of SOFTEV not the low.
The write invalidates SOFTEV+SOFTEV_CHK to force a cold boot path.
