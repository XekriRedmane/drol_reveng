# chunk-placement

Check and fix data chunk label placement: every label must be in the chunk immediately before its first code use.

## Usage

```
/chunk-placement [chunk-name]
```

With a chunk name, checks that one chunk. Without arguments, checks all data chunks in the file.

## Definition: data chunk

A **data chunk** is a chunk that contains only: ORG, labels, APSTR, HEX, DC.B, DC.W, and comments. No CPU instructions, no macros.

## Checking placement

Run the check script to find violations:

```
python .claude/skills/chunk-placement/check_placement.py              # all
python .claude/skills/chunk-placement/check_placement.py "chunk name" # one
```

## Instructions

### For a specific chunk

1. **List labels**: Find all labels defined in the chunk (from its `@ %def` line).

2. **Find first use**: For each label, search main.nw for the first code line that references it (LDA, STA, LDX, LDY, STX, STY, JSR, JMP, stow, STOW, STOB, MOVB, MOVW, INCW, ADC, SBC, CMP, INC, DEC, ORA, AND, EOR, BIT, ASL, LSR, ROL, ROR). Identify which `<<chunk name>>=` definition contains that line.

3. **Check placement**: Is the data chunk's definition immediately before that code chunk's definition in the document? ("Immediately before" means the data chunk definition appears in the prose right before the code chunk definition, with only explanatory text between them — no other chunk definitions.)

4. **If correctly placed**: Report "OK" for that label.

5. **If not correctly placed**: Split the data chunk at this label boundary. Create a new chunk:
   - Give it a descriptive name based on the label(s) it contains
   - Set its ORG to the label's address
   - Include the label and its data (up to the next label that belongs elsewhere)
   - Add a `@ %def` line listing the labels in the new chunk
   - Remove those labels from the original chunk's `@ %def`
   - Place the new chunk definition immediately before the first code chunk that uses it, with explanatory prose
   - Add the new chunk ref to `<<main.asm>>` (the reorder script will sort it)

6. **After all splits**: Run `python .claude/skills/assemble/reorder_chunks.py main` to fix ORG ordering, then assemble and verify.

### For all data chunks

Scan main.nw for all chunk definitions that contain only data (DC.B, DC.W, HEX, APSTR — no CPU instructions). For each one, apply the procedure above.

### Key rules

- **Always prefer labels over EQUs.** If an EQU exists for the same address as a label, remove the EQU.
- **Before assuming a calling convention** (e.g., does a routine want a length byte or string body?), **read the called routine's code**.
- **Chunk definitions** go in the prose before their first use. **Chunk references** in `<<main.asm>>` follow ORG address order.
- **Don't create duplicate labels.** Search for existing EQUs/labels at the same address first.
- **Verify after each change**: assemble and run `python .claude/skills/assemble/verify.py`.
