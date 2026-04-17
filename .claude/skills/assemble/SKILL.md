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
3. Assemble loader: `dasm loader.asm -f3 -oloader.bin -lloader.lst -sloader.sym`
4. Assemble rwts: `dasm rwts.asm -f3 -orwts.bin -lrwts.lst -srwts.sym`
5. Assemble drol: `dasm drol.asm -f3 -odrol.bin -ldrol.lst -sdrol.sym`
6. Assemble level1: `dasm level1.asm -f3 -olevel1.bin -llevel1.lst -slevel1.sym`

Report the result:
- If assembly succeeds with no errors, say so.
- If there are unresolved symbols, list them all.
- If there is an "Origin Reverse-indexed" error, run `python .claude/skills/assemble/reorder_chunks.py boot1` to auto-fix, then retry.
- If there are other errors (excluding "unreferenced chunk" warnings from weave.py), list them.

## Verify against reference binaries

After assembling, verify output matches the reference binaries (run relative to project root):

```
python .claude/skills/assemble/verify.py boot1
python .claude/skills/assemble/verify.py loader
python .claude/skills/assemble/verify.py rwts
python .claude/skills/assemble/verify.py drol
python .claude/skills/assemble/verify.py level1
```

Targets and their reference binaries:

| Target | Output | Reference | Base address |
|--------|--------|-----------|-------------|
| boot1 | output/boot1.bin | reference/boot1.bin | $0800 |
| loader | output/loader.bin | reference/loader.bin | $5000 |
| rwts | output/rwts.bin | reference/rwts.bin | $BE00 |
| drol | output/drol.bin | reference/drol.bin | $0100 |
| level1 | output/level1.bin | reference/level1.bin | $0000 |

## Reorder chunks

If chunk references get out of ORG order (causing "Origin Reverse-indexed" errors) (run relative to project root):

```
python .claude/skills/assemble/reorder_chunks.py boot1
```
