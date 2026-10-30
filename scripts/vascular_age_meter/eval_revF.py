# 配置の評価（KiCad の python）:  python eval_revF.py <board.kicad_pcb> ...
# 部品の外形（コートヤード）どうしの最小の間隔と、1.7 mm / 1.4 mm 未満の組の数、重なりの数を出す。
import sys, itertools
import pcbnew
from pcbnew import ToMM

def rect(f):
    try:
        cy = f.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount() > 0:
            b = cy.BBox(); return (ToMM(b.GetLeft()), ToMM(b.GetTop()), ToMM(b.GetRight()), ToMM(b.GetBottom()))
    except Exception: pass
    b = f.GetBoundingBox(False); return (ToMM(b.GetLeft()), ToMM(b.GetTop()), ToMM(b.GetRight()), ToMM(b.GetBottom()))

def gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0.0); dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    if dx == 0 and dy == 0:
        return -min(a[2], b[2]) + max(a[0], b[0]) if False else -1.0   # 重なり
    return max(dx, dy) if (dx == 0 or dy == 0) else (dx * dx + dy * dy) ** 0.5

for path in sys.argv[1:]:
    b = pcbnew.LoadBoard(path)
    fs = [f for f in b.GetFootprints() if f.GetReference() != 'U2' and not f.GetReference().startswith('TP5')]
    R = {f.GetReference(): rect(f) for f in fs}
    g = sorted((gap(R[x], R[y]), x, y) for x, y in itertools.combinations(R, 2))
    over = [t for t in g if t[0] < 0]
    lt14 = [t for t in g if 0 <= t[0] < 1.4]; lt17 = [t for t in g if 0 <= t[0] < 1.7]
    tracks = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK'); vias = sum(1 for t in b.GetTracks() if t.GetClass() == 'PCB_VIA')
    print('%s  overlap %d  <1.4mm %d  <1.7mm %d  min %.2f  tracks %d vias %d' % (path, len(over), len(lt14), len(lt17), g[0][0], tracks, vias))
    for t in (over + lt14)[:8]: print('    %.2f %s-%s' % t)
