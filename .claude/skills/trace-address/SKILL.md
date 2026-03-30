# trace-address

Trace all uses of a data address in the Ali Baba binary to determine its purpose and assign a label.

## Usage

```
/trace-address $XXXX
```

Where `$XXXX` is a hex address (e.g., `$5A74`, `0x5A74`, or just `5A74`).

## Instructions

You are analyzing a 6502 Apple II game binary. Given a data address, determine what it stores and suggest an EQU label.

### Step 1: Check existing context

Search `main.nw` for any existing references or comments about the address. Note any existing labels like `DAT_XXXX`.

### Step 2: Get all Ghidra xrefs

Use `mcp__ghidra-server__get_xrefs_to` on the address to find all cross-references in `main.bin`.

### Step 3: Catch refs Ghidra missed

Ghidra may miss references in unanalyzed code. Search `main.bin` for the raw byte patterns:
- `8D LL HH` (STA absolute) — writes
- `AD LL HH` (LDA absolute) — reads
- `AE LL HH` (LDX absolute) — reads
- `AC LL HH` (LDY absolute) — reads
- `CD LL HH` (CMP absolute) — reads
- `CE LL HH` (DEC absolute) — read/write
- `EE LL HH` (INC absolute) — read/write
- `2C LL HH` (BIT absolute) — reads
- `0D/2D/4D/6D LL HH` (ORA/AND/EOR/ADC absolute) — reads

where `LL` = low byte and `HH` = high byte of the target address.

Compare with Ghidra's xref list. For any addresses Ghidra missed, use `mcp__ghidra-server__get_function_by_address` to identify the containing function (if any).

### Step 4: Analyze each reference

For each reference site:
1. Use `mcp__ghidra-server__disassemble_function` to get surrounding context.
2. If no function exists at that address, use `mcp__ghidra-server__read_memory` and manually disassemble.
3. Classify as READ or WRITE.
4. Note what value is being written or how the read value is used (branch condition, index, arithmetic, etc.).
5. Note the enclosing function's purpose if known.

### Step 5: Summarize and recommend

Present a table of all references:

| Address | Function | Access | Context |
|---------|----------|--------|---------|

Then state:
- What values get written (constants? computed values?)
- How reads are used (branch conditions? lookups?)
- Your conclusion on the variable's purpose
- Recommended EQU label name (UPPER_SNAKE_CASE, concise, descriptive)

### Step 6: Apply (if user agrees)

If the user confirms the label:
1. Add an EQU definition in a `<<defines>>=` chunk in `main.nw`, near related definitions if possible.
2. Add `@ %def LABEL_NAME` after the chunk.
3. Replace all raw `$XXXX` and any `DAT_XXXX` references in `main.nw` with the new label.
4. Regenerate with `python weave.py main.nw`.

### Notes

- The game uses `$F4/$F5` and `$F8/$F9` as pointers to combatant data structures. Mob pointers have bit 7 set in the high byte.
- `$5Axx` is the game's variable workspace.
- `$1317` is the PRNG function (random number generator).
- Refer to CLAUDE.md and memory files for known function names and memory map.
