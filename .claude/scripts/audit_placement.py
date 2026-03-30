"""Audit main.nw for misplaced defines blocks and orphaned prose."""

import re
import sys

CHUNK_DEF = re.compile(r'^<<([-._  0-9A-Za-z]*)>>=\s*$')
PERCENT_DEF = re.compile(r'^@ %def\b')
CHAPTER_RE = re.compile(r'\\chapter\{([^}]+)\}')


def audit_defines(lines):
    """Find <<defines>>= blocks whose labels are used only in distant chapters."""

    # Track chapters per line
    line_chapters = []
    current_chapter = '(preamble)'
    for line in lines:
        m = CHAPTER_RE.search(line)
        if m:
            current_chapter = m.group(1)
        line_chapters.append(current_chapter)

    # Find all <<defines>>= and <<zero page defines>>= blocks
    defines_blocks = []
    for i, line in enumerate(lines):
        m = CHUNK_DEF.match(line)
        if m and m.group(1) in ('defines', 'zero page defines'):
            labels = []
            for j in range(i + 1, min(i + 50, len(lines))):
                equ_m = re.match(r'^(\w+)\s+EQU\b', lines[j])
                if equ_m:
                    labels.append(equ_m.group(1))
                if PERCENT_DEF.match(lines[j]):
                    break
            if labels:
                defines_blocks.append((i, labels, line_chapters[i]))

    # For each label, find code usages
    misplaced = []
    for def_idx, labels, def_chapter in defines_blocks:
        for label in labels:
            usages = []
            pattern = re.compile(r'\b' + re.escape(label) + r'\b')
            for i, line in enumerate(lines):
                if i == def_idx or i == def_idx + 1:
                    continue
                if PERCENT_DEF.match(line):
                    continue
                if line.strip().startswith(label) and 'EQU' in line:
                    continue
                if pattern.search(line) and not line.strip().startswith('@ %def'):
                    usages.append((i, line_chapters[i]))

            if not usages:
                continue

            usage_chapters = set(ch for _, ch in usages)
            if def_chapter not in usage_chapters:
                nearest = min(usages, key=lambda x: abs(x[0] - def_idx))
                dist = abs(nearest[0] - def_idx)
                if dist > 100:
                    misplaced.append((
                        label, def_idx + 1, def_chapter,
                        nearest[0] + 1, sorted(usage_chapters), dist
                    ))

    misplaced.sort(key=lambda x: -x[5])
    return misplaced


def audit_prose(lines):
    """Find prose paragraphs that reference routines from distant chapters."""

    line_chapters = []
    current_chapter = '(preamble)'
    for line in lines:
        m = CHAPTER_RE.search(line)
        if m:
            current_chapter = m.group(1)
        line_chapters.append(current_chapter)

    # Collect all defined labels and their chapters
    label_chapters = {}
    for i, line in enumerate(lines):
        if PERCENT_DEF.match(line):
            parts = line.strip().replace('@ %def', '').split()
            for label in parts:
                if label not in label_chapters:
                    label_chapters[label] = line_chapters[i]

    # Find prose paragraphs that mention labels from other chapters
    # Look for [[ ]] references in @ prose lines
    ref_pattern = re.compile(r'\[\[([A-Z][A-Z0-9_]+)\]\]')
    issues = []

    in_prose = False
    prose_start = 0
    prose_text = []
    prose_chapter = ''

    for i, line in enumerate(lines):
        is_prose = (line.startswith('@ ') and not PERCENT_DEF.match(line)) or \
                   (not line.startswith('<<') and not line.startswith('    ') and
                    not PERCENT_DEF.match(line) and not CHUNK_DEF.match(line) and
                    line.strip() and not line.strip().startswith('@'))

        if is_prose:
            if not in_prose:
                prose_start = i
                prose_text = []
                prose_chapter = line_chapters[i]
                in_prose = True
            prose_text.append(line)
        else:
            if in_prose and prose_text:
                # Check this prose block for cross-chapter references
                full_text = ''.join(prose_text)
                refs = ref_pattern.findall(full_text)
                foreign_refs = []
                for ref in refs:
                    if ref in label_chapters:
                        ref_ch = label_chapters[ref]
                        if ref_ch != prose_chapter and ref_ch != '(preamble)':
                            # Check distance
                            # Find where the label is defined
                            for j, ln in enumerate(lines):
                                if PERCENT_DEF.match(ln) and ref in ln:
                                    dist = abs(j - prose_start)
                                    if dist > 500:
                                        foreign_refs.append((ref, ref_ch, dist))
                                    break

                if foreign_refs:
                    preview = prose_text[0].strip()[:80]
                    issues.append((prose_start + 1, prose_chapter, foreign_refs, preview))

            in_prose = False

    return issues


if __name__ == '__main__':
    with open('main.nw', 'r', encoding='cp1252') as f:
        lines = f.readlines()

    print("=== MISPLACED <<defines>>= BLOCKS ===")
    print("(Label defined in one chapter but used only in other chapters)\n")
    misplaced = audit_defines(lines)
    for label, def_line, def_ch, near_line, usage_chs, dist in misplaced:
        print(f"  L{def_line:5d} {label:30s}")
        print(f"         defined in: {def_ch}")
        print(f"         used in:    {', '.join(usage_chs)}")
        print(f"         nearest usage: L{near_line} (distance: {dist} lines)")
        print()

    print(f"Total: {len(misplaced)} misplaced defines\n")

    print("=== ORPHANED PROSE ===")
    print("(Prose referencing routines defined in distant chapters)\n")
    issues = audit_prose(lines)
    for line_num, chapter, refs, preview in issues:
        print(f"  L{line_num:5d} in [{chapter}]:")
        print(f"         {preview}")
        for ref, ref_ch, dist in refs:
            print(f"         refs {ref} (defined in [{ref_ch}], {dist} lines away)")
        print()

    print(f"Total: {len(issues)} prose blocks with distant references")
