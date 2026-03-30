# re-next

Find the next unlabeled address in main.nw and reverse engineer it — identifying its purpose, documenting it, verifying the assembly, and renaming it in Ghidra.

## Usage

```
/re-next
```

No arguments. The skill scans main.nw to find the best candidate automatically.

## Instructions

You are reverse engineering a 6502 Apple II game. This skill finds the next raw hex address worth reverse engineering, then fully documents it.

### Phase 1: Find a candidate

Scan `main.nw` for raw hex addresses that haven't been labeled yet. Look for patterns like:

- `JSR $XXXX` or `JMP $XXXX` — unlabeled subroutine calls
- `LDA $XXXX` / `STA $XXXX` — unlabeled data addresses
- Comments mentioning `$XXXX` addresses without corresponding EQU or label definitions

**Prioritization criteria** (in order):

1. **Most referenced** — addresses that appear many times are higher value
2. **Called from already-documented routines** — understanding callees deepens understanding of callers
3. **Adjacent to already-documented code** — fills gaps in the disassembly
4. **Data addresses in $5Axx** — game variables that clarify game state

**Exclusions** — skip these:

- Addresses that already have labels (EQU, or defined as a label in an assembly chunk)
- ROM addresses ($C000-$FFFF) — these are Apple II system routines
- Addresses in EALDR range ($A000-$BFFF) — different Ghidra project needed
- I/O addresses ($C0xx)

**Search method:**

1. Grep `main.nw` for `\$[0-9A-Fa-f]{4}` patterns
2. Cross-reference against existing EQU definitions and label definitions
3. Count occurrences of each unlabeled address
4. Pick the highest-value candidate based on the prioritization criteria
5. Present the candidate to the user with a brief rationale before proceeding

### Phase 2: Classify the candidate

Determine whether the address is a **subroutine** or a **data location**:

- If referenced by `JSR` or `JMP` → subroutine → use the `/disassemble` workflow (Phase 3A)
- If referenced by `LDA`/`STA`/`LDX`/`LDY`/`CMP`/`INC`/`DEC`/`BIT` → data → use the `/trace-address` workflow (Phase 3B)
- If both, prefer subroutine (the data references may be entry points or self-modifying code)

### Phase 3A: Reverse engineer a subroutine

Follow the full `/disassemble` workflow:

1. **Get disassembly** from Ghidra (`disassemble_function` + `get_function_by_address`). If not a known function, use `read_memory` and disassemble manually.

2. **Trace the logic** step by step — track registers, identify inputs/outputs/side effects, note 6502 idioms.

3. **Identify callers** via `get_xrefs_to`. Sample a few to confirm understanding.

4. **Choose a name** — descriptive UPPER_SNAKE_CASE.

5. **Write documentation** in main.nw:
   - Add a `\subsection` with prose description
   - Add any needed EQU defines in `<<defines>>=` or `<<zero page defines>>=` chunks
   - Write the assembly chunk with comments explaining *why* not *what*
   - Use `SUBROUTINE` after `ORG`, `.local` labels for branch targets
   - Reference existing EQU labels instead of raw addresses where possible
   - Place near related routines (by address or function)
   - Add chunk reference to `<<main.asm>>=` file chunk in address order

6. **Verify assembly** — assemble the chunk in isolation with dasm and compare byte-for-byte against `main.bin`. See `assembly-pitfalls.md` in the memory directory for common errors.

7. **Rename in Ghidra** via `batch_rename_function_components` (NOT `rename_function_by_address`).

8. **Update references** — replace raw `$XXXX` in `main.nw` with the new label. Regenerate with `python weave.py main.nw`.

### Phase 3B: Trace a data address

Follow the full `/trace-address` workflow:

1. **Check existing context** in main.nw for comments about the address.

2. **Get Ghidra xrefs** via `get_xrefs_to`.

3. **Search for raw byte patterns** in `main.bin` to catch refs Ghidra missed (STA/LDA/LDX/LDY/CMP/INC/DEC/BIT with the address bytes).

4. **Analyze each reference** — classify as READ/WRITE, note values and usage context.

5. **Summarize** — present a reference table, conclude on the variable's purpose, recommend an EQU label.

6. **Apply** — add EQU definition, replace raw addresses, regenerate.

### Notes

- `main.bin` is 41984 bytes, loaded at $0500, so file offset = address - $0500.
- The `<<main.asm>>=` file chunk lists all code chunks. New chunks must be inserted at the correct address-order position.
- Check CLAUDE.md for the memory map and known function names.
- Check the memory directory for known patterns and conventions.
- Do NOT decompile to C — work with the assembly directly.
- If the candidate is in EALDR range ($A000-$BFFF), inform the user that the Ghidra project needs switching before proceeding.
