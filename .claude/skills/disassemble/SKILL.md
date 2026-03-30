# disassemble

Reverse engineer a 6502 subroutine at a given address: disassemble it, understand its logic, verify the assembly, document it in main.nw, and name it in Ghidra.

## Usage

```
/disassemble $XXXX
```

Where `$XXXX` is the entry address of the routine (e.g., `$0C25`, `0x0C25`, or just `0C25`).

## Instructions

You are reverse engineering a 6502 Apple II game. Given a subroutine address, fully document it.

### Step 1: Get the disassembly

Use the disassembler script:

```
python3 .claude/scripts/dasm6502.py --file FILE --base BASE $START [$END]
```

Where FILE is the binary containing the routine, and BASE is its load address in hex. For example:

```
python3 .claude/scripts/dasm6502.py --file reference/boot1.bin --base 0800 0801
```

If END is omitted, it auto-detects the end at the next RTS/JMP/BRK.

For Ghidra context, also use `mcp__ghidra-server__disassemble_function` or `mcp__ghidra-server__get_function_by_address` to get xrefs and function boundaries.

### Step 2: Trace the logic

Work through the instructions step by step:
- Track register values (A, X, Y) and flags (C, Z, N, V).
- Identify the inputs (what registers/memory the routine reads on entry).
- Identify the outputs (what registers/memory it sets before returning).
- Note any side effects (memory writes, self-modification).
- For loops, determine the iteration count and exit condition.
- For branches, describe both paths.
- Watch for 6502 idioms:
  - `CLC; ADC #$XX` where $XX > $7F = subtract (unsigned complement)
  - `SEC; SBC` = subtract
  - `ASL/ROL` chains = multiply by powers of 2
  - `LSR/ROR` chains = divide by powers of 2
  - `AND #mask; CMP` = bit field extraction
  - `EOR #$FF; CLC; ADC #$01` = negate
  - Self-modifying code: `STA` into an instruction operand

### Step 3: Identify callers

Use `mcp__ghidra-server__get_xrefs_to` to find all callers. Note how many there are and sample a few to confirm your understanding of the routine's purpose. Check what values callers pass in A/X/Y and how they use the return values.

### Step 4: Choose a name

Pick a descriptive UPPER_SNAKE_CASE name for the routine based on what it does. Keep it concise. Examples:
- Arithmetic: `POS_TO_COLROW`, `MUL_BY_16`, `RANDOM`
- Lookups: `GET_MOB_DATA`, `COMPUTE_SCENE_PTR`
- Actions: `PRINT_FONTCHAR`, `SCROLL_STATUS_WINDOW`
- Predicates: `CHECK_LINE_OF_SIGHT`, `IS_ADJACENT`

### Step 5: Write the documentation in main.nw

Add a new subsection with the routine's documentation and assembly chunk. Follow this template:

```
\subsection{routine\_name (\$XXXX)}

One or two sentences describing what the routine does, its inputs, and outputs.
Add any important details about the algorithm or side effects.

<<chunk name>>=
    ORG     $XXXX
ROUTINE_NAME:
    SUBROUTINE

    [assembly code with comments]
@ %def ROUTINE_NAME
```

Guidelines for the assembly chunk:
- Use `SUBROUTINE` after every `ORG` to scope local labels.
- Use `.local_label` for branch targets within the routine.
- Comment each instruction or logical group, explaining *why* not just *what*.
- For self-modifying code, use `label = *+1` or `label = *+2` patterns.
- Align comments to a consistent column.
- Reference known EQU labels rather than raw addresses.

Place the new section near related routines (by address or by function). Add the chunk reference `<<chunk name>>` to the appropriate file chunk in ascending address order.

### Step 6: Verify the assembly

Assemble the new chunk and verify it produces bytes identical to the reference:

```
/assemble
```

If there are mismatches, review the disassembly. Common errors:
- Branch target off by N bytes → label in wrong position
- Zero-page vs absolute addressing → check original opcode byte
- Missing fall-through between adjacent routines
- Self-modifying code referencing wrong operand byte

### Step 7: Rename in Ghidra

Use `mcp__ghidra-server__batch_rename_function_components` (NOT `rename_function_by_address` which has a bug) to rename the function.

### Step 8: Update references

Search `main.nw` for any `JSR $XXXX` or `JMP $XXXX` references to the routine and replace with the new label name. Reassemble with `/assemble` to verify.

### Notes

- Do NOT decompile to C — work with the assembly directly.
