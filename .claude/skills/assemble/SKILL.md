# assemble

Tangle main.nw and assemble using dasm. Reports any errors.

## Usage

```
/assemble
```

## Instructions

Run these commands in sequence:

1. Tangle: `python weave.py main.nw output`
2. Assemble boot1: `cd output && dasm boot1.asm -f3 -oboot1.bin -lboot1.lst -sboot1.sym`

Report the result:
- If assembly succeeds with no errors, say so.
- If there are unresolved symbols, list them all.
- If there is an "Origin Reverse-indexed" error, run `python .claude/skills/assemble/reorder_chunks.py boot1` to auto-fix, then retry.
- If there are other errors (excluding "unreferenced chunk" warnings from weave.py), list them.

## Verify against reference binaries

After assembling, verify output matches the reference binaries (run relative to project root):

```
python .claude/skills/assemble/verify.py boot1
```

Targets and their reference binaries:

| Target | Output | Reference | Base address |
|--------|--------|-----------|-------------|
| boot1 | output/boot1.bin | reference/boot1.bin | $0800 |

## Reorder chunks

If chunk references get out of ORG order (causing "Origin Reverse-indexed" errors) (run relative to project root):

```
python .claude/skills/assemble/reorder_chunks.py boot1
```
