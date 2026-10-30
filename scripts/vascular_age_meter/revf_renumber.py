# -*- coding: utf-8 -*-
"""Rev.F: 部品番号を回路の役割（信号の流れ）の順に振り直す（2026-10-18）。通常の Python で実行:
    python revf_renumber.py <in.kicad_sch> <out.kicad_sch> <map.json>
順番: 1 センサ・LED → 2 前段の反転増幅 → 3 電源とバイアス → 4 脈波 LPF → 5 マイコンの ADC 入力 → 6 7 セグ → 7 スイッチ
U・Q・J・SW・RV・TP は Rev.E のまま（すでに役割の順になっている）。
"""
import re, sys, json

MAP = {
    # 1 センサ・LED
    'R2': 'R1',     # 100Ω  LED の電流制限（3V3 -> LEDA）
    'R3': 'R2',     # 1k    センサのエミッタ抵抗（RV1 と直列）
    # 2 前段の反転増幅（U1A）
    'C3': 'C1',     # 22u   入力の AC 結合（SENS -> NCIN）
    'R4': 'R3',     # 33k   入力抵抗（NCIN -> INV）
    'R5': 'R4',     # 1M    帰還抵抗（RV2 と直列）
    'C4': 'C2',     # 1000p 帰還のコンデンサ
    'R23': 'R5',    # 1k    張り付き解除（GP4 -> NCIN）
    # 3 電源とバイアス（U1B）
    'R1': 'R6',     # 100Ω  VCC_A のフィルタ（3V3 -> VCC_A）
    'C1': 'C3',     # 47u   VCC_A の平滑（電解）
    'C2': 'C4',     # 0.1u  VCC_A のパスコン
    'C7': 'C6',     # 0.1u  VCC_A のパスコン（オペアンプの近く）
    'R6': 'R7',     # 100k  バイアスの分圧（上）
    'R7': 'R8',     # 100k  バイアスの分圧（下）
    # C5 22u バイアスの平滑 はそのまま
    # 4 脈波 LPF（U1C, U1D）  R9-R12 はそのまま
    'C8': 'C7', 'C9': 'C8',      # LPF1
    'C10': 'C9', 'C11': 'C10',   # LPF2
    # 5 マイコンの ADC 入力（RC フィルタ）
    'R8': 'R13', 'C6': 'C11',    # ADC0 <- OUTA
    'R13': 'R14',                # ADC1 <- PLF（C12 はそのまま）
    'R24': 'R15',                # ADC3 <- SENS（C13 はそのまま）
    # 6 7 セグ
    'R14': 'R16', 'R15': 'R17', 'R16': 'R18', 'R17': 'R19', 'R18': 'R20', 'R19': 'R21', 'R20': 'R22',   # セグメント a-g
    'R21': 'R23', 'R22': 'R24',  # 桁のトランジスタのベース
}

src, dst, mapout = sys.argv[1:4]
s = open(src, encoding='utf-8').read()
olds = set(MAP); news = set(MAP.values())
assert len(news) == len(MAP), 'duplicate target'
# 2 段階で置き換える（R1 -> R6 と R6 -> R7 がぶつからないように）
def sub_all(text, a, b):
    text, n1 = re.subn(r'\(property "Reference" "%s"' % re.escape(a), '(property "Reference" "%s"' % b, text)
    text, n2 = re.subn(r'\(reference "%s"\)' % re.escape(a), '(reference "%s")' % b, text)
    return text, n1, n2
for a in MAP:
    s, n1, n2 = sub_all(s, a, '@@' + a)
    if n1 != 1 or n2 != 1: raise SystemExit('unexpected count for %s: %d %d' % (a, n1, n2))
for a, b in MAP.items():
    s, n1, n2 = sub_all(s, '@@' + a, b)
open(dst, 'w', encoding='utf-8', newline='\n').write(s)
json.dump(MAP, open(mapout, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('renumbered', len(MAP), 'parts')
