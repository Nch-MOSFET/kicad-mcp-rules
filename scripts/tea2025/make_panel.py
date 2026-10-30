# -*- coding: utf-8 -*-
"""2-up panel for JLCPCB (100 x 100 mm), same style as JLC発注/血管年齢測定器: two 100 x 50 boards stacked, one
100 x 100 outline, cut guide line at y = 50 on F/B silkscreen (cut by hand after delivery, no V-cut).
Copper is kept 1.0 mm away from the cut line (GND pours shortened). Nets of the lower copy get the suffix "_B" so
the panel has no false unconnected items. Run with KiCad's python:
    python make_panel.py <single.kicad_pcb> <panel.kicad_pcb>
"""
import sys
import pcbnew
from pcbnew import FromMM as MM, ToMM

sys.stdout.reconfigure(encoding="utf-8")
IN, OUT = sys.argv[1], sys.argv[2]
W, H, DY = 100.0, 50.0, 50.0
CUT_CLR = 1.0                       # copper-free band on each side of the cut line
board = pcbnew.LoadBoard(IN)
off = pcbnew.VECTOR2I(0, MM(DY))

# nets for the lower copy
netB = {}
for name, ni in list(board.GetNetsByName().items()):
    name = str(name)
    if not name: continue
    nb = pcbnew.NETINFO_ITEM(board, name + "_B"); board.Add(nb); netB[name] = nb

def clone(item):
    try: return item.Duplicate(False)        # FOOTPRINT / ZONE take addToParentGroup in KiCad 10
    except TypeError: return item.Duplicate()

def dup(item):
    d = clone(item)
    try: d = d.Cast()
    except Exception: pass
    d.Move(off)
    return d

fps = list(board.GetFootprints()); tracks = list(board.GetTracks()); zones = list(board.Zones())
draws = [d for d in board.GetDrawings() if d.GetLayer() != pcbnew.Edge_Cuts]
edges = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]

for f in fps:
    d = dup(f)
    for p in d.Pads():
        n = p.GetNetname()
        if n in netB: p.SetNet(netB[n])
    board.Add(d)
for t in tracks:
    d = dup(t); d.SetNet(netB[t.GetNetname()]); board.Add(d)
for dr in draws:
    board.Add(dup(dr))

# zones: original (upper) ends CUT_CLR above the cut line, the copy starts CUT_CLR below it
for z in zones:
    for k, (y0, y1, net) in enumerate(((0.5, DY - CUT_CLR, None), (DY + CUT_CLR, H + DY - 0.5, netB[z.GetNetname()]))):
        if k == 0:
            nz = z
        else:
            nz = clone(z)
            try: nz = nz.Cast()
            except Exception: pass
            nz.SetNet(net); board.Add(nz)
        o = nz.Outline(); o.RemoveAllContours(); o.NewOutline()
        for (x, y) in [(0.5, y0), (W - 0.5, y0), (W - 0.5, y1), (0.5, y1)]:
            o.Append(MM(x), MM(y))

# outline 100 x 100 and the cut guide
for e in edges: board.Remove(e)
def seg(layer, x1, y1, x2, y2, w):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(layer); s.SetWidth(MM(w))
    s.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1))); s.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2))); board.Add(s)
for (a, b_, c, d_) in [(0, 0, W, 0), (W, 0, W, H + DY), (W, H + DY, 0, H + DY), (0, H + DY, 0, 0)]:
    seg(pcbnew.Edge_Cuts, a, b_, c, d_, 0.05)
for layer in (pcbnew.F_SilkS, pcbnew.B_SilkS):
    seg(layer, 0.5, DY, W - 0.5, DY, 0.15)     # ends 0.5 mm inside the edge (silk_edge_clearance)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(OUT, board)
bb = board.GetBoardEdgesBoundingBox()
print("panel", ToMM(bb.GetWidth()), "x", ToMM(bb.GetHeight()), "footprints", len(list(board.GetFootprints())),
      "tracks", len(board.GetTracks()), "zones", board.GetAreaCount())
