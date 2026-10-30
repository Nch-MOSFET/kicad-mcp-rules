# 直線の配線を足す（KiCad の python）: python add_track.py <in> <out> <net> <layer F|B> <width> x0,y0 x1,y1 ...
import sys, pcbnew
from pcbnew import FromMM
src, dst, net, lay, w = sys.argv[1:6]
pts = [tuple(float(v) for v in p.split(',')) for p in sys.argv[6:]]
b = pcbnew.LoadBoard(src)
ni = b.FindNet(net) or b.FindNet('/' + net)
L = pcbnew.F_Cu if lay == 'F' else pcbnew.B_Cu
for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
    t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(FromMM(x0), FromMM(y0))); t.SetEnd(pcbnew.VECTOR2I(FromMM(x1), FromMM(y1)))
    t.SetWidth(FromMM(float(w))); t.SetLayer(L); t.SetNet(ni); b.Add(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(dst, b); print('added', len(pts) - 1, 'segments on', net)
