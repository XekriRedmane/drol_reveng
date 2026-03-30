# find-gaps

Assemble main.nw, compare against the reference main.bin, and present undocumented gaps for the user to choose which to reverse engineer next.

## Usage

```
/find-gaps
```

No arguments.

## Instructions

### Step 1: Assemble

Run the build pipeline:

```bash
cd /project/ali_baba_re
python3 weave.py main.nw output 2>&1 | tail -5
cd output && dasm main.asm -f3 -omain.bin -lmain.lst -smain.sym 2>&1
```

If assembly fails, report the error and stop.

### Step 2: Verify

Run the verification script from the project root:

```bash
cd /project/ali_baba_re
python3 .claude/skills/assemble/verify.py
```

### Step 3: Present results

Display the results to the user in a clear format:

1. **Coverage summary**: X/Y bytes (Z%) documented, N gaps remaining
2. **Large gaps** (>= 500 bytes): show address range, size, and any known context from CLAUDE.md
3. **Medium gaps** (100-499 bytes): show address range, size
4. **Small gaps** (< 100 bytes): show count and total size

For medium and large gaps, add context by checking what labels exist just before and after each gap using the .sym file:

```bash
# For each gap start/end, find nearest symbols
grep -i 'XXXX' output/main.sym
```

### Step 4: Ask the user

Ask: "Which gap would you like to tackle?" and wait for their response.

### Notes

- The reference binary is `main.bin` at the project root
- The assembled output is `output/main.bin`
- Base address is $0500 (file offset = address - $0500)
- Large gaps in the $2000 range are hi-res staging data (low priority)
- Gaps in $9Axx-$A2xx are game message strings (low priority)
- Gaps in $7Axx-$7Dxx are menu option strings (low priority)
- Gaps in $A4xx-$B2xx are EALDR resident routines (need different Ghidra project)
- Code gaps in $0500-$9600 are the highest priority targets
