"""Board update for the footprint review (2026-10-10). Copper of other parts is not touched.
 - J1  -> easyeda:LED-TH_4P_RPR-220, rotated 180 deg on the old socket centre (chamfer top-right, as on the sensor)
 - RV1, RV2 -> new vam_custom:GF063P_Vertical (triangular pins), row centre on the old middle pin
 - J5  -> refreshed vam_custom:HDSP-K123 (silk clear of pads, pin-1 corner chamfer)
 - TP5 -> new GND clip land 8x3 mm at the bottom-right corner
 - removes the VCC_A branch that went to the old socket pin 2 (that position is GND now)
Pad nets are taken from the schematic netlist.   python pcb_fp_update.py <in.kicad_pcb> <out.kicad_pcb> <netlist.xml>"""
import sys, math
import xml.etree.ElementTree as ET
import pcbnew
from pcbnew import ToMM
MM = lambda v: pcbnew.FromMM(float(v))
IN, OUT, NETLIST = sys.argv[1:4]
PRJ = 'C:/Users/<user>/Documents/KiCad_work/vascular_age_meter'
b = pcbnew.LoadBoard(IN)
root = ET.parse(NETLIST).getroot()
pinnet = {}
for n in root.find('nets'):
    for nd in n.findall('node'): pinnet[(nd.get('ref'), nd.get('pin'))] = n.get('name')
nets = {str(k): v for k, v in b.GetNetsByName().items()}
def net(name):
    if name not in nets:
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni); nets[name] = ni
    return nets[name]

def replace(ref, libdir, name, pos, orient, keep_texts=True, copy_ref=True):
    old = b.FindFootprintByReference(ref) if ref else None
    new = pcbnew.FootprintLoad(libdir, name)
    new.SetFPID(pcbnew.LIB_ID(libdir.split('/')[-1].replace('.pretty', ''), name))
    new.SetOrientationDegrees(orient); new.SetPosition(pcbnew.VECTOR2I(MM(pos[0]), MM(pos[1])))
    if old:
        new.SetPath(old.GetPath()); new.SetReference(old.GetReference()); new.SetValue(old.GetValue())
        for fl in old.GetFields():
            for g in new.GetFields():
                if g.GetName() == fl.GetName() and fl.GetName() in ('Datasheet', 'Description'): g.SetText(fl.GetText())
        if copy_ref:
            for src, dst in ((old.Reference(), new.Reference()), (old.Value(), new.Value())):
                dst.SetLayer(src.GetLayer()); dst.SetVisible(src.IsVisible()); dst.SetTextSize(src.GetTextSize())
                dst.SetTextThickness(src.GetTextThickness()); dst.SetTextAngle(src.GetTextAngle()); dst.SetPosition(src.GetPosition())
        if keep_texts:
            for g in old.GraphicalItems():
                if g.GetClass() == 'PCB_TEXT':
                    t = pcbnew.PCB_TEXT(new); t.SetText(g.GetText()); t.SetLayer(g.GetLayer())
                    t.SetTextSize(g.GetTextSize()); t.SetTextThickness(g.GetTextThickness())
                    t.SetHorizJustify(g.GetHorizJustify()); t.SetVertJustify(g.GetVertJustify())
                    t.SetTextAngle(g.GetTextAngle()); t.SetPosition(g.GetPosition()); new.Add(t)
        new.SetExcludedFromBOM(old.IsExcludedFromBOM())
    r = new.GetReference()
    for p in new.Pads():
        nm = pinnet.get((r, str(p.GetNumber())))
        if nm: p.SetNet(net(nm))
        if nm and nm.lstrip('/') == 'GND': p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
    b.Add(new)
    return old, new

removed = []
# J1: rotate 180 so that E (SENS) is top-right, A (LEDA) bottom-left, K (GND) top-left, C (VCC_A) bottom-right
j1 = b.FindFootprintByReference('J1')
cx = sum(ToMM(p.GetPosition().x) for p in j1.Pads()) / 4; cy = sum(ToMM(p.GetPosition().y) for p in j1.Pads()) / 4
old, new = replace('J1', PRJ + '/lib/easyeda/easyeda.pretty', 'LED-TH_4P_RPR-220', (cx, cy), 180, keep_texts=False)
new.Reference().SetLayer(pcbnew.F_Fab)
lab = pcbnew.PCB_TEXT(new); lab.SetText('J1 RPR-220'); lab.SetLayer(pcbnew.F_SilkS)
lab.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0))); lab.SetTextThickness(MM(0.15))
for g in old.GraphicalItems():
    if g.GetClass() == 'PCB_TEXT' and 'RPR' in g.GetText(): lab.SetPosition(g.GetPosition())
new.Add(lab); removed.append(old)
# RV1 / RV2: same orientation (-90): pin 1 above, pin 3 below, wiper (pin 2) to the right
for ref in ('RV1', 'RV2'):
    f = b.FindFootprintByReference(ref); mid = f.FindPadByNumber('2').GetPosition()
    old, new = replace(ref, PRJ + '/vam_custom.pretty', 'GF063P_Vertical', (ToMM(mid.x), ToMM(mid.y)), -90)
    removed.append(old)
# J5: same place, refreshed graphics
f = b.FindFootprintByReference('J5')
old, new = replace('J5', PRJ + '/vam_custom.pretty', 'HDSP-K123', (ToMM(f.GetPosition().x), ToMM(f.GetPosition().y)), f.GetOrientationDegrees())
removed.append(old)
# TP5: GND clip land at the bottom-right corner
bb = b.GetBoardEdgesBoundingBox(); W, H = ToMM(bb.GetRight()), ToMM(bb.GetBottom())
tp = pcbnew.FootprintLoad(PRJ + '/vam_custom.pretty', 'TestPoint_Pad_GND_Clip_8x3')
tp.SetFPID(pcbnew.LIB_ID('vam_custom', 'TestPoint_Pad_GND_Clip_8x3'))
tp.SetReference('TP5'); tp.SetValue('TP_GND')
tp.SetPosition(pcbnew.VECTOR2I(MM(W - 0.55 - 4.0), MM(H - 0.55 - 1.5)))
for c in root.find('components'):
    if c.get('ref') == 'TP5':
        tp.SetPath(pcbnew.KIID_PATH('/' + c.findtext('tstamps').strip()))
for p in tp.Pads():
    p.SetNet(net(pinnet[('TP5', '1')])); p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
g = pcbnew.PCB_TEXT(tp); g.SetText('GND'); g.SetLayer(pcbnew.F_SilkS)
g.SetTextSize(pcbnew.VECTOR2I(MM(1.0), MM(1.0))); g.SetTextThickness(MM(0.15))
g.SetPosition(pcbnew.VECTOR2I(MM(W - 0.55 - 4.0), MM(H - 0.55 - 3.0 - 1.0))); tp.Add(g)
tp.Reference().SetLayer(pcbnew.F_Fab)
b.Add(tp)
for o in removed: b.Remove(o)
pcbnew.SaveBoard(OUT, b)

# remove the VCC_A copper that ran to the old socket pin 2 (now the GND pin of the sensor)
b = pcbnew.LoadBoard(OUT)
j1 = b.FindFootprintByReference('J1')
kpad = [p for p in j1.Pads() if p.GetNumber() == '2'][0]
vcc = [t for t in b.GetTracks() if t.GetNetname().lstrip('/') == 'VCC_A' and t.Type() != pcbnew.PCB_VIA_T]
kill = []
seg = [t for t in vcc if math.dist((ToMM(t.GetStart().x), ToMM(t.GetStart().y)), (ToMM(kpad.GetPosition().x), ToMM(kpad.GetPosition().y))) < 2.0
       or math.dist((ToMM(t.GetEnd().x), ToMM(t.GetEnd().y)), (ToMM(kpad.GetPosition().x), ToMM(kpad.GetPosition().y))) < 2.0]
# walk the branch from the old pin towards the rest of the net while it has no other branches
pts = lambda t: [(t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)]
cur = seg[:]
while cur:
    t = cur.pop()
    if t in kill: continue
    kill.append(t)
    for e in pts(t):
        nb = [o for o in vcc if o not in kill and e in pts(o)]
        if len(nb) == 1 and ToMM(e[1]) < 9.5 and ToMM(e[0]) < 7.0: cur.append(nb[0])
for t in kill: b.Remove(t)
print('VCC_A segments removed:', len(kill))
pcbnew.SaveBoard(OUT, b)
b = pcbnew.LoadBoard(OUT); pcbnew.ZONE_FILLER(b).Fill(b.Zones()); pcbnew.SaveBoard(OUT, b)
