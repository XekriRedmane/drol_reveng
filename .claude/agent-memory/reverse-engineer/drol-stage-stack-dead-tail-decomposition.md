---
name: STAGE_STACK_DEAD_TAIL sub-labels mirror $012B-$01EF
description: $5C2B-$5CEF staging-area dead residue now decomposed into 7 labeled sub-chunks matching the live stack-page code layout byte-for-byte
type: project
---

The dead residue at $5C2B-$5CFF (inside the STAGE_STACK chunk) now has per-sub-region labels that mirror the live $012B-$01EF stack-page code image:

- STAGE_DEAD_JOYSTICK_HANDLER ($5C2B, 105 bytes) mirrors JOYSTICK_HANDLER
- STAGE_DEAD_KEY_HANDLER_EXT ($5C94, 35 bytes) mirrors KEY_HANDLER_EXT
- STAGE_DEAD_ROW_COPY_CLICK ($5CB7, 13 bytes) mirrors ROW_COPY_CLICK
- STAGE_DEAD_ROW_COPY_CLICK_DEAD_RTS ($5CC4, 1 byte) mirrors the bare RTS
- STAGE_DEAD_ROW_COPY_CLICK_RANDOM ($5CC5, 36 bytes) mirrors ROW_COPY_CLICK_RANDOM
- STAGE_DEAD_ROW_COPY_CLICK_GATE ($5CE9, 6 bytes) mirrors ROW_COPY_CLICK_GATE
- STAGE_DEAD_CLICK_GATE_FALL ($5CEF, 1 byte) mirrors the dangling LDA #$00 prologue (only the $A9 opcode byte; the live mirror continues with $00 + 15 bytes of zero padding but the staging image diverges at $5CF0)
- STAGE_DEAD_TAIL_RESIDUE ($5CF0, 16 bytes) is NOT a mirror --- bytes `0A 85 5C A2 10 A4 5C B9 13 02 20 9E 10 A9 20 20` disassemble as a tone-emitter fragment using RESCUE_DRIFT_PITCH ($0213) and JSR SND_DELAY_UP; looks like a pre-release wipe-click variant that was never wired. No JSR/JMP in any shipped binary reaches $5CF0.

**Why:** Parallels the existing $5D00-$5DEF STAGE_VECTORS decomposition (13 sub-chunks) that mirrors $0300-$03EF. The $5CF0-$5CFF "install-time residue" comment previously masked recognizable code bytes.

**How to apply:** When adding docs about the staging area or touching this chunk, use the sub-labels rather than raw hex addresses. The divergence point is $5CEF-vs-$5CF0: up to $5CEF is byte-for-byte mirror, from $5CF0 down is tone-emitter code (never executed).
