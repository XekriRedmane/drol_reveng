"""Recreate main.bin from assembled main_test.bin.

The assembled binary has code/data at runtime addresses:
  - HRCG code + standard font at $9600-$A8FF
  - Disk I/O routines at $B300-$BFFF

During boot, the EALDR loads these into the HGR1 staging area ($2000-$3FFF),
and game_init ($6DA5) relocates them to runtime addresses:
  - $2000-$32FF -> $9600-$A8FF  (19 pages, HRCG code + standard font)
  - $3300-$3FFF -> $B300-$BFFF  (13 pages, disk I/O routines)
  - Then clears $2000-$3FFF

This script reverses that relocation, then re-applies it:
  1. Read assembled flat binary (ORG $0500)
  2. Reverse relocation: runtime addresses -> staging area ($2000-$3FFF)
  3. Re-apply game_init relocation: staging -> runtime, clear staging
  4. Output $0500-$BFFF and compare with extract_main.py's main.bin
"""

INPUT_FILE = "output/main_test.bin"
REFERENCE_FILE = "main.bin"
OUTPUT_FILE = "recreated_main.bin"

BASE_ADDR = 0x0500
END_ADDR = 0xC000
SIZE = END_ADDR - BASE_ADDR  # $BB00 = 47872


def main():
    with open(INPUT_FILE, "rb") as f:
        raw = bytearray(f.read())

    # The assembled flat binary starts at $0500 and includes
    # HRCG ($9600-$A8FF) and DISK_IO ($B300-$BFFF) at runtime addresses.
    mem = bytearray(SIZE)
    mem[:min(len(raw), SIZE)] = raw[:min(len(raw), SIZE)]

    # === Step 1: Reverse game_init relocation ===

    hrcg_rt = 0x9600 - BASE_ADDR   # runtime offset
    hrcg_st = 0x2000 - BASE_ADDR   # staging offset
    hrcg_len = 0x1300               # 19 pages

    io_rt = 0xB300 - BASE_ADDR     # runtime offset
    io_st = 0x3300 - BASE_ADDR     # staging offset
    io_len = 0x0D00                 # 13 pages

    # Move HRCG + std font: $9600-$A8FF -> $2000-$32FF
    mem[hrcg_st:hrcg_st + hrcg_len] = mem[hrcg_rt:hrcg_rt + hrcg_len]
    mem[hrcg_rt:hrcg_rt + hrcg_len] = bytearray(hrcg_len)

    # Move disk I/O: $B300-$BFFF -> $3300-$3FFF
    mem[io_st:io_st + io_len] = mem[io_rt:io_rt + io_len]
    mem[io_rt:io_rt + io_len] = bytearray(io_len)

    # Now mem has the pre-game_init layout:
    #   $2000-$32FF  HRCG code + standard font
    #   $3300-$3FFF  disk I/O routines
    #   $9600-$A8FF  zeroed
    #   $B300-$BFFF  zeroed

    # === Step 2: Re-apply game_init relocation ($6DA5) ===

    # Copy $2000-$32FF -> $9600-$A8FF (19 pages)
    mem[hrcg_rt:hrcg_rt + hrcg_len] = mem[hrcg_st:hrcg_st + hrcg_len]

    # Copy $3300-$3FFF -> $B300-$BFFF (13 pages)
    mem[io_rt:io_rt + io_len] = mem[io_st:io_st + io_len]

    # Clear $2000-$3FFF (game_init clears each byte after copying)
    clear_off = 0x2000 - BASE_ADDR
    mem[clear_off:clear_off + 0x2000] = bytearray(0x2000)

    # === Output and verify ===

    with open(OUTPUT_FILE, "wb") as f:
        f.write(mem)
    print(f"Wrote {len(mem)} bytes to {OUTPUT_FILE}")

    try:
        with open(REFERENCE_FILE, "rb") as f:
            ref = bytearray(f.read())
    except FileNotFoundError:
        print(f"{REFERENCE_FILE} not found - run extract_main.py first")
        return

    if mem == ref:
        print(f"MATCH: {OUTPUT_FILE} matches {REFERENCE_FILE}")
    else:
        mismatches = 0
        first_addr = None
        for i in range(min(len(mem), len(ref))):
            if mem[i] != ref[i]:
                if first_addr is None:
                    first_addr = BASE_ADDR + i
                mismatches += 1
        if mismatches <= 16:
            for i in range(min(len(mem), len(ref))):
                if mem[i] != ref[i]:
                    addr = BASE_ADDR + i
                    print(f"  ${addr:04X}: assembled={mem[i]:02X} reference={ref[i]:02X}")
        else:
            print(f"MISMATCH: {mismatches} differing bytes, "
                  f"first at ${first_addr:04X}")


if __name__ == "__main__":
    main()
