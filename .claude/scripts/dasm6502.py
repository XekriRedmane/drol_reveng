#!/usr/bin/env python3
"""Disassemble 6502 machine code from a binary file.

Usage:
    python .claude/scripts/dasm6502.py --file FILE --base BASE START [END]

    --file FILE: binary file to read (e.g. reference/boot1.bin)
    --base BASE: hex load address of the file (e.g. 0800)
    START:       hex address to begin disassembly (e.g. 0801)
    END:         hex address (exclusive), defaults to next RTS/JMP/BRK + 1

Examples:
    python .claude/scripts/dasm6502.py --file reference/boot1.bin --base 0800 0801
    python .claude/scripts/dasm6502.py --file reference/boot1.bin --base 0800 0801 083C
"""

from __future__ import annotations

import argparse
import sys

# --- Opcode tables ---

# Implied (1 byte)
IMPLIED: dict[int, str] = {
    0x00: 'BRK', 0x08: 'PHP', 0x0A: 'ASL A', 0x18: 'CLC',
    0x28: 'PLP', 0x2A: 'ROL A', 0x38: 'SEC', 0x40: 'RTI',
    0x48: 'PHA', 0x4A: 'LSR A', 0x58: 'CLI', 0x60: 'RTS',
    0x68: 'PLA', 0x6A: 'ROR A', 0x78: 'SEI', 0x88: 'DEY',
    0x8A: 'TXA', 0x98: 'TYA', 0x9A: 'TXS', 0xA8: 'TAY',
    0xAA: 'TAX', 0xB8: 'CLV', 0xBA: 'TSX', 0xC8: 'INY',
    0xCA: 'DEX', 0xD8: 'CLD', 0xE8: 'INX', 0xEA: 'NOP',
    0xF8: 'SED',
}

# Immediate (2 bytes: opcode + #$XX)
IMMEDIATE: dict[int, str] = {
    0x09: 'ORA', 0x29: 'AND', 0x49: 'EOR', 0x69: 'ADC',
    0xA0: 'LDY', 0xA2: 'LDX', 0xA9: 'LDA', 0xC0: 'CPY',
    0xC9: 'CMP', 0xE0: 'CPX', 0xE9: 'SBC',
}

# Zero page (2 bytes: opcode + $XX)
ZEROPAGE: dict[int, str] = {
    0x05: 'ORA', 0x06: 'ASL', 0x24: 'BIT', 0x25: 'AND',
    0x26: 'ROL', 0x45: 'EOR', 0x46: 'LSR', 0x65: 'ADC',
    0x66: 'ROR', 0x84: 'STY', 0x85: 'STA', 0x86: 'STX',
    0xA4: 'LDY', 0xA5: 'LDA', 0xA6: 'LDX', 0xC4: 'CPY',
    0xC5: 'CMP', 0xC6: 'DEC', 0xE4: 'CPX', 0xE5: 'SBC',
    0xE6: 'INC',
}

# Zero page,X (2 bytes)
ZEROPAGE_X: dict[int, str] = {
    0x15: 'ORA', 0x16: 'ASL', 0x35: 'AND', 0x36: 'ROL',
    0x55: 'EOR', 0x56: 'LSR', 0x75: 'ADC', 0x76: 'ROR',
    0x94: 'STY', 0x95: 'STA', 0xB4: 'LDY', 0xB5: 'LDA',
    0xD5: 'CMP', 0xD6: 'DEC', 0xF5: 'SBC', 0xF6: 'INC',
}

# Zero page,Y (2 bytes)
ZEROPAGE_Y: dict[int, str] = {
    0x96: 'STX', 0xB6: 'LDX',
}

# Absolute (3 bytes: opcode + $XXXX)
ABSOLUTE: dict[int, str] = {
    0x0D: 'ORA', 0x0E: 'ASL', 0x20: 'JSR', 0x2C: 'BIT',
    0x2D: 'AND', 0x2E: 'ROL', 0x4C: 'JMP', 0x4D: 'EOR',
    0x4E: 'LSR', 0x6D: 'ADC', 0x6E: 'ROR', 0x8C: 'STY',
    0x8D: 'STA', 0x8E: 'STX', 0xAC: 'LDY', 0xAD: 'LDA',
    0xAE: 'LDX', 0xCC: 'CPY', 0xCD: 'CMP', 0xCE: 'DEC',
    0xEC: 'CPX', 0xED: 'SBC', 0xEE: 'INC',
}

# Absolute,X (3 bytes)
ABSOLUTE_X: dict[int, str] = {
    0x1D: 'ORA', 0x1E: 'ASL', 0x3D: 'AND', 0x3E: 'ROL',
    0x5D: 'EOR', 0x5E: 'LSR', 0x7D: 'ADC', 0x7E: 'ROR',
    0x9D: 'STA', 0xBC: 'LDY', 0xBD: 'LDA', 0xDD: 'CMP',
    0xDE: 'DEC', 0xFD: 'SBC', 0xFE: 'INC',
}

# Absolute,Y (3 bytes)
ABSOLUTE_Y: dict[int, str] = {
    0x19: 'ORA', 0x39: 'AND', 0x59: 'EOR', 0x79: 'ADC',
    0x99: 'STA', 0xB9: 'LDA', 0xBE: 'LDX', 0xD9: 'CMP',
    0xF9: 'SBC',
}

# (Indirect) - JMP only (3 bytes)
INDIRECT: dict[int, str] = {
    0x6C: 'JMP',
}

# (Indirect,X) (2 bytes)
INDIRECT_X: dict[int, str] = {
    0x01: 'ORA', 0x21: 'AND', 0x41: 'EOR', 0x61: 'ADC',
    0x81: 'STA', 0xA1: 'LDA', 0xC1: 'CMP', 0xE1: 'SBC',
}

# (Indirect),Y (2 bytes)
INDIRECT_Y: dict[int, str] = {
    0x11: 'ORA', 0x31: 'AND', 0x51: 'EOR', 0x71: 'ADC',
    0x91: 'STA', 0xB1: 'LDA', 0xD1: 'CMP', 0xF1: 'SBC',
}

# Relative branches (2 bytes: opcode + signed offset)
BRANCH: dict[int, str] = {
    0x10: 'BPL', 0x30: 'BMI', 0x50: 'BVC', 0x70: 'BVS',
    0x90: 'BCC', 0xB0: 'BCS', 0xD0: 'BNE', 0xF0: 'BEQ',
}

# Terminal instructions (stop auto-detection of end)
TERMINAL = {0x60, 0x4C, 0x6C, 0x00, 0x40}  # RTS, JMP abs, JMP ind, BRK, RTI


def parse_addr(s: str) -> int:
    """Parse a hex address string like '$7780', '0x7780', or '7780'."""
    s = s.strip().lstrip('$').removeprefix('0x').removeprefix('0X')
    return int(s, 16)


def disassemble(data: bytes, base: int, start: int, end: int) -> None:
    """Disassemble and print 6502 code from start to end (exclusive)."""
    i = start - base
    while i < end - base and i < len(data):
        addr = base + i
        b = data[i]

        def out(s: str) -> None:
            print(f'    {s:34s}; ${addr:04X}')

        if b in IMPLIED:
            out(IMPLIED[b])
            i += 1
        elif b in IMMEDIATE:
            out(f'{IMMEDIATE[b]} #${data[i+1]:02X}')
            i += 2
        elif b in ZEROPAGE:
            out(f'{ZEROPAGE[b]} ${data[i+1]:02X}')
            i += 2
        elif b in ZEROPAGE_X:
            out(f'{ZEROPAGE_X[b]} ${data[i+1]:02X},X')
            i += 2
        elif b in ZEROPAGE_Y:
            out(f'{ZEROPAGE_Y[b]} ${data[i+1]:02X},Y')
            i += 2
        elif b in ABSOLUTE:
            a16 = data[i+1] | (data[i+2] << 8)
            out(f'{ABSOLUTE[b]} ${a16:04X}')
            i += 3
        elif b in ABSOLUTE_X:
            a16 = data[i+1] | (data[i+2] << 8)
            out(f'{ABSOLUTE_X[b]} ${a16:04X},X')
            i += 3
        elif b in ABSOLUTE_Y:
            a16 = data[i+1] | (data[i+2] << 8)
            out(f'{ABSOLUTE_Y[b]} ${a16:04X},Y')
            i += 3
        elif b in INDIRECT:
            a16 = data[i+1] | (data[i+2] << 8)
            out(f'JMP (${a16:04X})')
            i += 3
        elif b in INDIRECT_X:
            out(f'{INDIRECT_X[b]} (${data[i+1]:02X},X)')
            i += 2
        elif b in INDIRECT_Y:
            out(f'{INDIRECT_Y[b]} (${data[i+1]:02X}),Y')
            i += 2
        elif b in BRANCH:
            offset = data[i+1]
            if offset >= 0x80:
                offset -= 0x100
            target = addr + 2 + offset
            out(f'{BRANCH[b]} ${target:04X}')
            i += 2
        else:
            out(f'.byte ${b:02X}')
            i += 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Disassemble 6502 machine code from a binary file.')
    parser.add_argument('--file', required=True,
                        help='Binary file to read (e.g. reference/boot1.bin)')
    parser.add_argument('--base', required=True,
                        help='Hex load address of the file (e.g. 0800)')
    parser.add_argument('start',
                        help='Hex address to begin disassembly (e.g. 0801)')
    parser.add_argument('end', nargs='?', default=None,
                        help='Hex end address (exclusive); '
                             'defaults to next RTS/JMP/BRK + 1')
    args = parser.parse_args()

    base = parse_addr(args.base)
    start = parse_addr(args.start)

    with open(args.file, 'rb') as f:
        data = f.read()

    if args.end is not None:
        end = parse_addr(args.end)
    else:
        # Auto-detect end: scan until terminal instruction
        i = start - base
        while i < len(data):
            b = data[i]
            if b in IMPLIED:
                if b in TERMINAL:
                    i += 1
                    break
                i += 1
            elif (b in IMMEDIATE or b in ZEROPAGE or b in ZEROPAGE_X
                  or b in ZEROPAGE_Y or b in INDIRECT_X or b in INDIRECT_Y
                  or b in BRANCH):
                i += 2
            elif b in ABSOLUTE or b in ABSOLUTE_X or b in ABSOLUTE_Y or b in INDIRECT:
                if b in TERMINAL or (b == 0x4C):  # JMP absolute
                    i += 3
                    break
                i += 3
            else:
                i += 1
        end = base + i

    print(f'; Disassembly ${start:04X}-${end - 1:04X} ({end - start} bytes)')
    print()
    disassemble(data, base, start, end)


if __name__ == '__main__':
    main()
