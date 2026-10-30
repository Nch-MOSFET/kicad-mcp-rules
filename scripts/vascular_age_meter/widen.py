# 指定より細い配線を太くする（KiCad の python）: python widen.py <in> <out> <最小幅 mm>
import sys, pcbnew
from pcbnew import ToMM, FromMM
src, dst, w = sys.argv[1], sys.argv[2], float(sys.argv[3])
b = pcbnew.LoadBoard(src); n = 0
for t in b.GetTracks():
    if t.GetClass() == 'PCB_TRACK' and ToMM(t.GetWidth()) < w - 1e-6:
        t.SetWidth(FromMM(w)); n += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(dst, b); print('widened', n)
