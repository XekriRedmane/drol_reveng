---
name: STAGE_RESIDUE_DEAD decomposition
description: $5E00-$5EC4 dead-code disassembly; nibble-reader + GAME_START_INIT-clone tail with BIT-abs mid-entry trick on STA ZP_SCORE_1 operand
type: project
---

`STAGE_RESIDUE_DEAD` at $5E00-$5EC4 (197 bytes, drol.bin) is now fully
disassembled with labeled phases instead of a HEX blob. Three key
findings:

**Phase structure**: nibble sector-reader head ($5E00-$5E8C), a 7x
`DEAD_BA00_OVL` retry delay ($5E85-$5E8C; $BA00 is sprite data at
run-time — this call is nonsense, confirming the code is dead), a
mid-instruction entry into live NIBBLE_READER via `NIBBLE_READER_OVL`
= $BE5A ($5E94), and a GAME_START_INIT-style restart tail
($5EAB-$5EC4) that falls through into RESTART_DISPATCH.

**BIT-abs mid-entry trick**: The restart tail has two entry points.
`.restart_full` at $5EA6 zeroes all three BCD-score digits. The other
entry `.restart_skip` at $5EAB lands on the **operand byte** of
`STA ZP_SCORE_1` — the `$2C $85 $2D` bytes decode as `BIT $2D85` (a
3-byte NOP) when entered there, skipping the zero of ZP_SCORE_2 but
still executing the HUD-column seed. Requires `DC.B $85; .label: DC.B
<ZP_SCORE_1; STA ZP_SCORE_2` layout to name the operand.

**Why**: Develops a gentler restart path for the NIBBLE_READER_OVL
return. If Z=1 on PLP and flags are negative, it does the full restart
(including bridge calls to SCREEN_ROW_COPY and STAGE_RWTS_RELOAD).
Otherwise it skips the bridge and the third-digit zero.

**How to apply**: When RE-ing dead code that calls $BA00 or other
live-layout addresses, expect the calls to land in data at runtime —
flag as nonsense. When a BNE/BPL offset differs from the "natural"
label position by exactly N bytes, suspect a BIT-abs mid-instruction
entry; check whether the target byte would decode as $2C or similar
BIT opcode. Local labels can be placed on operand bytes via `DC.B`
emit + label on the next byte.

Additional labels introduced this round: DISK_Q6_OFF/Q6_ON/Q7_OFF
($C08A/B/E Disk II softswitches); STAGE_DISK_DATA/STAGE_DISK_MOTOR_ON
(cross-target re-EQUs of loader's DISK_DATA/DISK_MOTOR_ON for use in
drol.asm); STAGE_RWTS_RELOAD ($BE00 cross-target); NIBBLE_READER_OVL
= $BE5A; DEAD_BA00_OVL = $BA00; TXT_RETRY_04F8/05F8/06F8; ZP_DEAD_*
aliases; .restart_full/.restart_skip locals.
