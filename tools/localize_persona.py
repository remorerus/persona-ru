#!/usr/bin/env python3
"""Patch Persona's existing language tables while preserving analysis logic."""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(sys.argv[1])
MAP = Path(sys.argv[2])
translations = json.loads(MAP.read_text(encoding='utf-8'))
smali_files = sorted(ROOT.glob('smali*/com/rokid/gwansang/**/*.smali'))
main = ROOT / 'smali_classes2/com/rokid/gwansang/MainActivity.smali'

def decode_smali_literal(value: str) -> str:
    value = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), value)
    value = value.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
    value = value.replace("\\'", "'").replace('\\"', '"').replace('\\\\', '\\')
    return value

# Translate exact string constants only. This leaves rule conditions, metrics,
# thresholds, landmark processing and enum ordinals untouched.
for path in smali_files:
    lines = path.read_text(encoding='utf-8').splitlines(keepends=True)
    out = []
    for line in lines:
        match = re.search(r'(const-string(?:/jumbo)?\s+\w+,\s+")((?:[^"\\]|\\.)*)(")', line)
        if match:
            source = decode_smali_literal(match.group(2))
            target = translations.get(source)
            if source == 'Square':
                target = 'Квадратное лицо' if path.name == 'ArOverlayView.smali' else 'Квадратный тип'
            if target is not None:
                encoded = target.replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t').replace('"', '\\"')
                line = line[:match.start(2)] + encoded + line[match.end(2):]
        out.append(line)
    path.write_text(''.join(out), encoding='utf-8')

# Force the existing EN data branch, whose strings have just been translated.
# This avoids adding enum values or changing Kotlin switch/ordinal logic.
s = main.read_text(encoding='utf-8')
s = s.replace('const-string v0, "KO"\n\n    iput-object v0, p0, Lcom/rokid/gwansang/MainActivity;->currentLanguage:Ljava/lang/String;',
              'const-string v0, "EN"\n\n    iput-object v0, p0, Lcom/rokid/gwansang/MainActivity;->currentLanguage:Ljava/lang/String;', 1)
needle = '.method private final applyLanguage(Ljava/lang/String;)V\n    .locals 2\n'
replacement = needle + '\n    const-string v1, "EN"\n    move-object p1, v1\n'
if needle not in s:
    raise SystemExit('Could not find applyLanguage method')
s = s.replace(needle, replacement, 1)
needle = '    :goto_0\n    iput-object v2, p0, Lcom/rokid/gwansang/MainActivity;->currentLanguage:Ljava/lang/String;'
replacement = '    :goto_0\n    const-string v2, "EN"\n    iput-object v2, p0, Lcom/rokid/gwansang/MainActivity;->currentLanguage:Ljava/lang/String;'
if needle not in s:
    raise SystemExit('Could not find loadSettings language assignment')
s = s.replace(needle, replacement, 1)
main.write_text(s, encoding='utf-8')

# Restrict hardware focus navigation to Face (0) and Palm (1).
s, focus_changes = re.subn(
    r'(\\.field private static final MAX_FOCUS_INDEX:I = )0x7',
    r'\\g<1>0x2',
    s,
    count=1,
)
if focus_changes != 1:
    raise SystemExit('Could not restrict focus navigation to Face/Palm')
s, forward_changes = re.subn(r'rem-int/lit8 p1, p1, 0x7', 'rem-int/lit8 p1, p1, 0x2', s)
s, backward_changes = re.subn(r'add-int/lit8 p1, p1, 0x6', 'add-int/lit8 p1, p1, 0x1', s, count=1)
if forward_changes != 2 or backward_changes != 1:
    raise SystemExit(f'Unexpected focus navigation constants: forward={forward_changes}, backward={backward_changes}')
main.write_text(s, encoding='utf-8')

# Keep language-selector views inflated (binding IDs stay valid), but hide them.
layout = ROOT / 'res/layout/activity_main.xml'
xml = layout.read_text(encoding='utf-8')
xml = re.sub(r'(<LinearLayout[^>]*android:id="@id/languageSelectorBar"[^>]*)(>)',
             lambda m: m.group(1) + ' android:visibility="gone"' + m.group(2)
             if 'android:visibility=' not in m.group(1) else m.group(0), xml, count=1)
xml = xml.replace('android:text="Auto Save"', 'android:text="Автосохранение"')
layout.write_text(xml, encoding='utf-8')
print(f'Applied {len(translations)} Russian text mappings; analysis logic and model assets unchanged.')