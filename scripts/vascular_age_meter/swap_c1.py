"""Replace every C1 footprint (CP_Radial_D5.0mm_P2.50mm) with CP_Radial_D5.0mm_P2.00mm,
keeping position, orientation, pad 1 location, nets, fields and the schematic link.
    python swap_c1.py <board.kicad_pcb>"""
import sys
import pcbnew
from pcbnew import ToMM
P = sys.argv[1]
LIB = 'C:/Program Files/KiCad/10.0/share/kicad/footprints/Capacitor_THT.pretty'
NEW = 'CP_Radial_D5.0mm_P2.00mm'
b = pcbnew.LoadBoard(P)
olds = [f for f in b.GetFootprints() if f.GetReference() == 'C1']
for old in olds:
    new = pcbnew.FootprintLoad(LIB, NEW)
    new.SetFPID(pcbnew.LIB_ID('Capacitor_THT', NEW))
    new.SetOrientation(old.GetOrientation())
    new.SetPosition(old.GetPosition())          # footprint origin = pad 1 in both
    new.SetPath(old.GetPath())
    new.SetReference(old.GetReference()); new.SetValue(old.GetValue())
    for src, dst in ((old.Reference(), new.Reference()), (old.Value(), new.Value())):
        dst.SetLayer(src.GetLayer()); dst.SetVisible(src.IsVisible())
        dst.SetTextSize(src.GetTextSize()); dst.SetTextThickness(src.GetTextThickness())
        dst.SetTextAngle(src.GetTextAngle()); dst.SetPosition(src.GetPosition())
    for fl in old.GetFields():
        if fl.GetName() in ('Datasheet', 'Description'):
            for g in new.GetFields():
                if g.GetName() == fl.GetName(): g.SetText(fl.GetText())
    new.SetExcludedFromBOM(old.IsExcludedFromBOM()); new.SetExcludedFromPosFiles(old.IsExcludedFromPosFiles())
    for p in old.Pads():
        q = new.FindPadByNumber(p.GetNumber())
        q.SetNet(p.GetNet()); q.SetLocalZoneConnection(p.GetLocalZoneConnection())
    b.Add(new)
    print('C1 at (%.2f, %.2f): pad2 %.2f -> %.2f' % (ToMM(old.GetPosition().x), ToMM(old.GetPosition().y),
          ToMM(old.FindPadByNumber('2').GetPosition().x), ToMM(new.FindPadByNumber('2').GetPosition().x)))
for old in olds: b.Remove(old)
pcbnew.SaveBoard(P, b)
b = pcbnew.LoadBoard(P)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(P, b)
print('replaced', len(olds))
