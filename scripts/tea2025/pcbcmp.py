# -*- coding: utf-8 -*-
"""compare copper + footprint placement of two boards (rule 07-3)"""
import sys, pcbnew
def snap(p):
    b = pcbnew.LoadBoard(p)
    t = sorted((x.GetClass(), x.GetStart().x, x.GetStart().y, x.GetEnd().x, x.GetEnd().y, (x.GetWidth(pcbnew.F_Cu) if x.GetClass() == "PCB_VIA" else x.GetWidth()), x.GetLayer(), x.GetNetname()) for x in b.GetTracks())
    f = sorted((x.GetReference(), x.GetPosition().x, x.GetPosition().y, x.GetOrientationDegrees()) for x in b.GetFootprints())
    return t, f
a, b = snap(sys.argv[1]), snap(sys.argv[2])
print("tracks/vias same:", a[0] == b[0], len(a[0]), "| footprints same:", a[1] == b[1], len(a[1]))
