import re

opcode_first = {
    'LDA': [0xA9,0xA5,0xAD,0xB1,0xB5,0xBD,0xB9,0xA1],
    'STA': [0x85,0x8D,0x91,0x95,0x9D,0x99],
    'LDX': [0xA2,0xA6,0xAE,0xBE], 'LDY': [0xA0,0xA4,0xAC,0xBC],
    'STX': [0x86,0x8E], 'STY': [0x84,0x8C],
    'JSR': [0x20], 'JMP': [0x4C,0x6C],
    'CMP': [0xC9,0xC5,0xCD,0xDD,0xD9], 'CPX': [0xE0,0xE4,0xEC], 'CPY': [0xC0,0xC4,0xCC],
    'ADC': [0x69,0x65,0x6D,0x71,0x7D,0x79], 'SBC': [0xE9,0xE5,0xED],
    'AND': [0x29,0x25,0x2D], 'ORA': [0x09,0x05,0x0D], 'EOR': [0x49,0x45,0x4D],
    'INC': [0xE6,0xEE], 'DEC': [0xC6,0xCE],
    'BIT': [0x24,0x2C], 'ASL': [0x0A,0x06,0x0E], 'LSR': [0x4A,0x46,0x4E],
    'ROL': [0x2A,0x26,0x2E], 'ROR': [0x6A,0x66,0x6E],
    'TAX': [0xAA], 'TAY': [0xA8], 'TXA': [0x8A], 'TYA': [0x98],
    'INX': [0xE8], 'INY': [0xC8], 'DEX': [0xCA], 'DEY': [0x88],
    'PHA': [0x48], 'PLA': [0x68], 'PHP': [0x08], 'PLP': [0x28],
    'SEC': [0x38], 'CLC': [0x18], 'SEI': [0x78], 'CLI': [0x58],
    'RTS': [0x60], 'RTI': [0x40], 'NOP': [0xEA],
    'BEQ': [0xF0], 'BNE': [0xD0], 'BCS': [0xB0], 'BCC': [0x90],
    'BMI': [0x30], 'BPL': [0x10], 'BVS': [0x70], 'BVC': [0x50],
    'STZ': [0x64,0x9C], 'BRA': [0x80],
}

text = open('main.nw', 'r').read()
orig = open('main.bin', 'rb').read()
lines = text.split('\n')

ok_count = 0
mismatch_count = 0

for i, line in enumerate(lines):
    m = re.match(r'\s+ORG\s+\$([0-9A-Fa-f]{4})', line)
    if not m:
        continue
    addr = int(m.group(1), 16)
    ln = i + 1
    if addr < 0x0500 or (addr - 0x0500) >= len(orig):
        continue

    first_mnem = None
    hex_data = None
    for j in range(i + 1, min(i + 15, len(lines))):
        l = lines[j].strip()
        if not l or l.startswith(';') or l.startswith('@') or l.startswith('\\'):
            continue
        if re.match(r'^[A-Za-z_][\w.]*:', l) or l == 'SUBROUTINE':
            continue
        if re.match(r'^\.[\w]+:?\s*$', l):
            continue
        if re.match(r'^[A-Za-z_]\w*\s*=', l):
            continue
        parts = l.split()
        if parts[0].upper() == 'HEX':
            hex_data = parts[1][:2]
            first_mnem = 'HEX'
            break
        first_mnem = parts[0].upper()
        break

    if not first_mnem:
        continue

    off = addr - 0x0500
    actual = orig[off]
    actual_hex = ' '.join(f'{orig[off+k]:02X}' for k in range(min(6, len(orig)-off)))

    if first_mnem == 'HEX':
        expected = int(hex_data, 16)
        if expected != actual:
            print(f'MISMATCH line {ln}: ORG ${addr:04X} - HEX ${expected:02X} vs binary ${actual:02X}  [{actual_hex}]')
            mismatch_count += 1
        else:
            ok_count += 1
        continue

    if first_mnem not in opcode_first:
        print(f'UNKNOWN  line {ln}: ORG ${addr:04X} - mnemonic "{first_mnem}" not in table  [{actual_hex}]')
        continue

    if actual not in opcode_first[first_mnem]:
        print(f'MISMATCH line {ln}: ORG ${addr:04X} - "{first_mnem}" expects {[f"${x:02X}" for x in opcode_first[first_mnem]]} but binary has ${actual:02X}  [{actual_hex}]')
        mismatch_count += 1
    else:
        ok_count += 1

print(f'\n{ok_count} OK, {mismatch_count} mismatches')
