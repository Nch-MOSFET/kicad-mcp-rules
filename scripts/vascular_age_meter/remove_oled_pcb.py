"""Remove the OLED header J4 from the board, with the copper that only served it:
SDA / SCL tracks and vias, and the branch of 3V3 that ended at J4 (dangling after the removal)."""
import sys
import pcbnew
from pcbnew import ToMM
IN, OUT = sys.argv[1], sys.argv[2]
b = pcbnew.LoadBoard(IN)
j4 = b.FindFootprintByReference('J4')
j4pads = [(p.GetPosition(), p.GetNetname()) for p in j4.Pads()]
b.Remove(j4)
dead = [t for t in b.GetTracks() if t.GetNetname().lstrip('/') in ('SDA', 'SCL')]
for t in dead: b.Remove(t)
print('SDA/SCL items removed', len(dead))
net3 = [n for n in (p[1] for p in j4pads) if n.lstrip('/') == '3V3'][0]
pcbnew.SaveBoard(OUT, b)

def dangling(b):
    """3V3 tracks/vias with an end that touches nothing else of the same net"""
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetname() == net3]
    trs = [t for t in b.GetTracks() if t.GetNetname() == net3]
    out = []
    for t in trs:
        if t.Type() == pcbnew.PCB_VIA_T:
            pos = t.GetPosition()
            n = sum(1 for o in trs if o is not t and o.Type() != pcbnew.PCB_VIA_T and (o.GetStart() == pos or o.GetEnd() == pos))
            if n <= 1: out.append(t)
            continue
        for pt in (t.GetStart(), t.GetEnd()):
            ok = any(p.HitTest(pt) for p in pads) or any(
                (o is not t) and ((o.Type() == pcbnew.PCB_VIA_T and o.HitTest(pt)) or (o.Type() != pcbnew.PCB_VIA_T and (o.GetStart() == pt or o.GetEnd() == pt)))
                for o in trs)
            if not ok: out.append(t); break
    return out
pruned = 0
for _ in range(50):
    b = pcbnew.LoadBoard(OUT)
    d = dangling(b)
    if not d: break
    for t in d: b.Remove(t)
    pruned += len(d)
    pcbnew.SaveBoard(OUT, b)
print('3V3 dangling items removed', pruned)
b = pcbnew.LoadBoard(OUT)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(OUT, b)
