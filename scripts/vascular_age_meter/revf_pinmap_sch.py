# -*- coding: utf-8 -*-
"""基板の配置で入れ替えた GPIO の割り当て（pinmap.json: ネット名 -> U2 のパッド番号）を、回路図の U2 のピンのラベルに反映する。
通常の Python で:  python revf_pinmap_sch.py <in.kicad_sch> <out.kicad_sch> <pinmap.json>
U2（rp2040_zero）は (335.28, 165.10) に置いてあり、左の列はパッド 1〜9 が x = 335.28、右の列はパッド 13〜23 が x = 368.30。
ピンの間隔は 2.54 mm（パッド 1 / 13 が y = 165.10）。
"""
import re, sys, json

src, dst, pm = sys.argv[1:4]
s = open(src, encoding='utf-8').read()
pinmap = json.load(open(pm, encoding='utf-8'))
X0, XR, Y0, P = 335.28, 368.30, 165.10, 2.54
def pin_xy(pad):
    pad = int(pad)
    return ('%.2f' % X0, '%.2f' % (Y0 + (pad - 1) * P)) if pad <= 12 else ('%.2f' % XR, '%.2f' % (Y0 + (pad - 13) * P))
want = {pin_xy(pad): net for net, pad in pinmap.items()}
done = set()
def f(m):
    xy = (m.group(2), m.group(3))
    if xy in want:
        done.add(xy)
        return '(label "%s"%s' % (want[xy], m.group(1))
    return m.group(0)
s = re.sub(r'\(label "[^"]+"(\s*\(at ([\d.]+) ([\d.]+) )', f, s)
missing = [want[k] for k in want if k not in done]
if missing: raise SystemExit('labels not found at U2 pins for: %s' % missing)
open(dst, 'w', encoding='utf-8', newline='\n').write(s)
print('relabelled', len(done), 'U2 pins')
