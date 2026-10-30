"""J1（RPR-220）の切り欠きの角の外側に、シルクの点を打つ（2026-10-27）。

切り欠きは、フットプリントの外形（F.Fab に移してある）の斜めの線。その中点から外へ DOT_OUT [mm] の位置に、
半径 DOT_R の塗りつぶしの円を F.SilkS に置く。silk.py からも呼ぶ（silk.py は J1 のシルクの図形を F.Fab に移すので、そのあとで置く）。

  単独で使うとき: python j1_notch_dot.py <board.kicad_pcb>（KiCad の Python で）
"""
import math
import sys
import pcbnew

DOT_R = 0.3
DOT_OUT = 0.9
TAG = 'J1_NOTCH_DOT'


def add_notch_dot(board):
    f = board.FindFootprintByReference('J1')
    # 前に置いた点を消す（何度実行しても 1 つだけにする）
    for g in list(f.GraphicalItems()):
        if g.GetClass() == 'PCB_SHAPE' and g.GetShape() == pcbnew.SHAPE_T_CIRCLE and g.GetLayer() == pcbnew.F_SilkS:
            f.Remove(g)
    diag = None
    for g in f.GraphicalItems():
        if g.GetClass() == 'PCB_SHAPE' and g.GetShape() == pcbnew.SHAPE_T_SEGMENT and g.GetLayer() == pcbnew.F_Fab:
            s, e = g.GetStart(), g.GetEnd()
            if s.x != e.x and s.y != e.y:
                diag = (s, e)
    assert diag, 'J1 の切り欠きの線が見つからない'
    s, e = diag
    mx, my = (s.x + e.x) / 2, (s.y + e.y) / 2
    c = f.GetPosition()
    dx, dy = mx - c.x, my - c.y                       # 部品の中心から切り欠きへ向かう向き
    n = math.hypot(dx, dy)
    cx = mx + dx / n * pcbnew.FromMM(DOT_OUT)
    cy = my + dy / n * pcbnew.FromMM(DOT_OUT)
    dot = pcbnew.PCB_SHAPE(f, pcbnew.SHAPE_T_CIRCLE)
    dot.SetLayer(pcbnew.F_SilkS)
    dot.SetCenter(pcbnew.VECTOR2I(int(cx), int(cy)))
    dot.SetEnd(pcbnew.VECTOR2I(int(cx + pcbnew.FromMM(DOT_R)), int(cy)))
    dot.SetWidth(pcbnew.FromMM(0.1))
    dot.SetFilled(True)
    f.Add(dot)
    return pcbnew.ToMM(int(cx)), pcbnew.ToMM(int(cy))


if __name__ == '__main__':
    b = pcbnew.LoadBoard(sys.argv[1])
    print('J1 notch dot at', add_notch_dot(b))
    b.Save(sys.argv[1])
