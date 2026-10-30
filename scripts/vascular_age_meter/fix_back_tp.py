# 裏面のテストポイント番号が基板からはみ出す場合、パッドの反対側（下）へ移す（KiCad の python）: python fix_back_tp.py <in> <out>
import sys, pcbnew
from pcbnew import ToMM, FromMM
b = pcbnew.LoadBoard(sys.argv[1])
for f in b.GetFootprints():
    if not f.GetReference().startswith('TP'): continue
    for t in f.GraphicalItems():
        if isinstance(t, pcbnew.PCB_TEXT) and t.GetLayer() == pcbnew.B_SilkS and t.GetText() in ('${REFERENCE}', '%R'):
            bb = t.GetBoundingBox()
            if ToMM(bb.GetTop()) < 0.6:
                c = f.GetPosition(); p = t.GetPosition()
                t.SetPosition(pcbnew.VECTOR2I(p.x, c.y + (c.y - p.y)))   # パッドの中心で上下に折り返す
                print('moved', f.GetReference(), 'back text to y=%.2f' % ToMM(t.GetPosition().y))
pcbnew.SaveBoard(sys.argv[2], b)
