# -*- coding: utf-8 -*-
"""print pads / fab / courtyard extents of footprints:  python fpinfo.py <libdir> <name> [...]"""
import sys, pcbnew
from pcbnew import ToMM
sys.stdout.reconfigure(encoding="utf-8")
args = sys.argv[1:]
for i in range(0, len(args), 2):
    lib, nm = args[i], args[i + 1]
    f = pcbnew.FootprintLoad(lib, nm)
    print("==", nm, "attr", f.GetAttributes())
    for p in f.Pads():
        pos = p.GetPosition(); sz = p.GetSize(); dr = p.GetDrillSize()
        print("  pad %-3s at (%.3f, %.3f) size %.2fx%.2f drill %.2fx%.2f shape %s" % (p.GetNumber(), ToMM(pos.x), ToMM(pos.y), ToMM(sz.x), ToMM(sz.y), ToMM(dr.x), ToMM(dr.y), p.GetShape()))
    for lay, name in ((pcbnew.F_Fab, "fab"), (pcbnew.F_CrtYd, "crtyd"), (pcbnew.F_SilkS, "silk")):
        xs, ys = [], []
        for g in f.GraphicalItems():
            if g.GetLayer() == lay:
                bb = g.GetBoundingBox(); xs += [ToMM(bb.GetX()), ToMM(bb.GetRight())]; ys += [ToMM(bb.GetY()), ToMM(bb.GetBottom())]
        if xs: print("  %-5s x %.2f..%.2f  y %.2f..%.2f" % (name, min(xs), max(xs), min(ys), max(ys)))
