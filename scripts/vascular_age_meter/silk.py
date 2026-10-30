"""Make the silkscreen readable (KiCad python):
    python silk.py <in.kicad_pcb> <out.kicad_pcb> <netlist.xml> <gpio_pinmap.json>
- reference + value labels placed by a collision-free search (pads, silk outlines, other labels, board edge)
- pin names for the sensor socket, the OLED header and the RP2040-Zero (inside its outline)
- title on the front, GPIO table on the back
- schematic-parity fixes: net names '/NAME', test points excluded from BOM, Description fields
Copper (tracks, zones) is not touched except for re-filling the zones."""
import sys, json, math, re
import xml.etree.ElementTree as ET
import numpy as np
import pcbnew
from pcbnew import ToMM
MM = lambda v: pcbnew.FromMM(float(v))

IN, OUT, NETLIST, PINMAP = sys.argv[1:5]
b = pcbnew.LoadBoard(IN)
TH, TW = 1.0, 0.15            # JLCPCB: text height >= 1.0 mm, stroke >= 0.15 mm
EDGE = 0.35; PADCLR = 0.15; GAP = 0.2
bb = b.GetBoardEdgesBoundingBox(); BW, BH = ToMM(bb.GetRight()), ToMM(bb.GetBottom())

# ---------------------------------------------------------------- parity fixes
root = ET.parse(NETLIST).getroot()
sch_nets = {n.get('name') for n in root.find('nets')}
for name, ni in list(b.GetNetsByName().items()):
    name = str(name)
    if name and not name.startswith('/') and ('/' + name) in sch_nets:
        ni.SetNetname('/' + name)
desc = {c.get('ref'): (c.findtext('description') or '') for c in root.find('components')}
dsh = {c.get('ref'): (c.findtext('datasheet') or '') for c in root.find('components')}
inbom = {}
for c in root.find('components'):
    inbom[c.get('ref')] = not any(p.get('name') == 'exclude_from_bom' for p in c.findall('property'))
# nets the schematic gives to single unconnected pins; pads with duplicated numbers (switches) get the same net
pinnet = {}
for n in root.find('nets'):
    for nd in n.findall('node'): pinnet[(nd.get('ref'), nd.get('pin'))] = n.get('name')
nets_by_name = {str(k): v for k, v in b.GetNetsByName().items()}
def net_of(name):
    if name not in nets_by_name:
        ni = pcbnew.NETINFO_ITEM(b, name); b.Add(ni); nets_by_name[name] = ni
    return nets_by_name[name]
for f in b.GetFootprints():
    r = f.GetReference()
    for fl in f.GetFields():
        if fl.GetName() == 'Description' and r in desc: fl.SetText(desc[r])
    for fl in f.GetFields():
        if fl.GetName() == 'Datasheet' and r in dsh and dsh[r] not in ('', '~'): fl.SetText(dsh[r])
    if r in inbom: f.SetExcludedFromBOM(not inbom[r])
    if r.startswith('SW'): f.SetDuplicatePadNumbersAreJumpers(True)   # 4-leg tact switch: legs with the same number are joined inside
    for p in f.Pads():
        want = pinnet.get((r, str(p.GetNumber())))
        if want and p.GetNetname() != want:
            if p.GetNetname() == '' or p.GetNetname().lstrip('/') == want.lstrip('/'):
                p.SetNet(net_of(want))

# the sensor socket outline would run through its pin letters: drop it (the letters E/C/K/A show the orientation)
for f in b.GetFootprints():
    if f.GetReference() == 'J1':
        for g in list(f.GraphicalItems()):
            if g.GetClass() == 'PCB_SHAPE' and g.GetLayer() == pcbnew.F_SilkS: g.SetLayer(pcbnew.F_Fab)
# ---------------------------------------------------------------- occupancy grids (0.1 mm) per side
R = 0.1
NXg, NYg = int(BW / R) + 1, int(BH / R) + 1
occ = {'F': np.zeros((NYg, NXg), bool), 'B': np.zeros((NYg, NXg), bool)}
def rix(x0, y0, x1, y1):
    return (max(0, int(math.floor(y0 / R))), min(NYg, int(math.ceil(y1 / R))), max(0, int(math.floor(x0 / R))), min(NXg, int(math.ceil(x1 / R))))
def mark(side, rc, infl=0.0):
    i0, i1, j0, j1 = rix(rc[0] - infl, rc[1] - infl, rc[2] + infl, rc[3] + infl); occ[side][i0:i1, j0:j1] = True
def free(side, rc):
    if rc[0] < EDGE or rc[1] < EDGE or rc[2] > BW - EDGE or rc[3] > BH - EDGE: return False
    i0, i1, j0, j1 = rix(*rc)
    if occ[side][i0:i1, j0:j1].any(): return False
    if side == 'F':
        c = court[i0:i1, j0:j1]
        if np.any((c != 0) & (c != OWNER['id']) & (c != IGN['id'])): return False
    return True
court = np.zeros((NYg, NXg), np.int16)
OWNER = {'id': 0, 'near': True}
IGN = {'id': -99}
def box_of(item):
    q = item.GetBoundingBox(); r = (ToMM(q.GetLeft()), ToMM(q.GetTop()), ToMM(q.GetRight()), ToMM(q.GetBottom()))
    if item.GetClass() in ('PCB_TEXT', 'PCB_FIELD') and chr(10) not in item.GetShownText(True):
        # the KiCad box includes line spacing; use glyph height + stroke across the text line
        hh = (ToMM(item.GetTextSize().y) + ToMM(item.GetTextThickness())) / 2 + 0.05
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        ang = round(item.GetTextAngleDegrees()) % 180
        if ang == 0: r = (r[0], cy - hh, r[2], cy + hh)
        elif ang == 90: r = (cx - hh, r[1], cx + hh, r[3])
    return r

padocc = np.zeros((NYg, NXg), bool)
labocc = np.zeros((NYg, NXg), bool)
for f in b.GetFootprints():
    for p in f.Pads():
        for side in ('F', 'B'): mark(side, box_of(p), PADCLR)
        _q = box_of(p); i0, i1, j0, j1 = rix(_q[0] - PADCLR, _q[1] - PADCLR, _q[2] + PADCLR, _q[3] + PADCLR); padocc[i0:i1, j0:j1] = True
    for g in f.GraphicalItems():
        lay = g.GetLayer()
        side = 'F' if lay == pcbnew.F_SilkS else 'B' if lay == pcbnew.B_SilkS else None
        if side is None or g.GetClass() != 'PCB_SHAPE': continue
        w = ToMM(g.GetWidth()) / 2 + 0.05
        if g.GetShape() == pcbnew.SHAPE_T_RECT and f.GetReference() == 'J5':
            st, en = g.GetStart(), g.GetEnd()
            g.SetStart(pcbnew.VECTOR2I(min(st.x, en.x) - MM(0.45), min(st.y, en.y) - MM(0.45)))
            g.SetEnd(pcbnew.VECTOR2I(max(st.x, en.x) + MM(0.45), max(st.y, en.y) + MM(0.45)))
        if g.GetShape() == pcbnew.SHAPE_T_RECT:
            x0, y0 = ToMM(g.GetStart().x), ToMM(g.GetStart().y); x1, y1 = ToMM(g.GetEnd().x), ToMM(g.GetEnd().y)
            x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
            for rc in ((x0, y0, x1, y0), (x0, y1, x1, y1), (x0, y0, x0, y1), (x1, y0, x1, y1)): mark(side, rc, w)
        else:
            mark(side, box_of(g), 0.05)

# ---------------------------------------------------------------- label helpers
def style(t, h=TH):
    t.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h))); t.SetTextThickness(MM(max(TW, h * 0.15)))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetKeepUpright(True)
def rdist(rc, x, y):
    return math.hypot(max(rc[0] - x, 0, x - rc[2]), max(rc[1] - y, 0, y - rc[3]))
def nearest_ok(rc_t):
    """the label must be clearly closer to its own part than to any other part (no ambiguous labels)"""
    if OWNER['id'] <= 0 or not OWNER['near']: return True
    x, y = (rc_t[0] + rc_t[2]) / 2, (rc_t[1] + rc_t[3]) / 2
    own = RECTS[OWNER['id']]; d0 = rdist(own, x, y)
    return all(rdist(r_, x, y) > d0 + 0.25 for k_, r_ in RECTS.items() if k_ != OWNER['id'])
def try_at(t, side, x, y, ang):
    t.SetTextAngleDegrees(ang); t.SetTextPos(pcbnew.VECTOR2I(MM(x), MM(y)))
    rc = box_of(t)
    if free(side, rc) and nearest_ok(rc):
        mark(side, rc, GAP)
        if side == 'F':
            i0, i1, j0, j1 = rix(rc[0] - GAP, rc[1] - GAP, rc[2] + GAP, rc[3] + GAP); labocc[i0:i1, j0:j1] = True
        return True
    return False
def candidates(rc, tw, th, ang_pref, maxd=3.0, inside=True):
    x0, y0, x1, y1 = rc; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    out = []
    for ang in (ang_pref, 90 - ang_pref):
        w, h = (tw, th) if ang == 0 else (th, tw)
        base = [(cx, y0 - h / 2 - 0.15), (cx, y1 + h / 2 + 0.15), (x0 - w / 2 - 0.15, cy), (x1 + w / 2 + 0.15, cy)]
        out += [(p[0], p[1], ang, 0.0 if ang == ang_pref else 0.6) for p in base]
        if inside: out.append((cx, cy, ang, 1.05))
        for d in np.arange(0.0, maxd + 0.01, 0.5):        # rings around the courtyard
            ex0, ey0, ex1, ey1 = x0 - d - w / 2, y0 - d - h / 2, x1 + d + w / 2, y1 + d + h / 2
            per = []
            for x in np.arange(ex0, ex1 + 0.01, 0.5): per += [(x, ey0), (x, ey1)]
            for y in np.arange(ey0, ey1 + 0.01, 0.5): per += [(ex0, y), (ex1, y)]
            per.sort(key=lambda p: abs(p[0] - cx) + abs(p[1] - cy))
            out += [(p[0], p[1], ang, d + (0.0 if ang == ang_pref else 0.6)) for p in per]
    out.sort(key=lambda c: c[3])
    return out
def place(t, side, rc, ang_pref, maxd=3.0, inside=True):
    style(t)
    t.SetTextAngleDegrees(0); r0 = box_of(t); tw, th = r0[2] - r0[0], r0[3] - r0[1]
    for (x, y, ang, _) in candidates(rc, tw, th, ang_pref, maxd, inside):
        if try_at(t, side, x, y, ang): return True
    return False
def fp_rect(f):
    try:
        cy = f.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount() > 0:
            q = cy.BBox(); return (ToMM(q.GetLeft()), ToMM(q.GetTop()), ToMM(q.GetRight()), ToMM(q.GetBottom()))
    except Exception: pass
    return box_of(f)
def add_text(parent, text, layer, h=TH, mirrored=False):
    t = pcbnew.PCB_TEXT(parent); t.SetText(text); t.SetLayer(layer); style(t, h)
    if mirrored: t.SetMirrored(True)
    parent.Add(t); return t

fps = {f.GetReference(): f for f in b.GetFootprints()}
fid = {r: k + 1 for k, r in enumerate(sorted(fps))}
IGN['id'] = fid['J1']      # its outline is not printed, so labels may sit in its courtyard
RECTS = {}
for r, f in fps.items():
    i0, i1, j0, j1 = rix(*fp_rect(f)); court[i0:i1, j0:j1] = fid[r]; RECTS[fid[r]] = fp_rect(f)
# hide every value on silk first; references are re-placed below
for f in fps.values():
    f.Value().SetLayer(pcbnew.F_Fab)
    for t in list(f.GraphicalItems()):
        if t.GetClass() == 'PCB_TEXT' and t.GetLayer() == pcbnew.F_SilkS and t.GetText() in ('${REFERENCE}', '%R'):
            t.SetLayer(pcbnew.F_Fab)

# ---------------------------------------------------------------- RP2040-Zero: pin names inside its outline (visible before the module is fitted)
u2 = fps['U2']; OWNER['id'] = fid['U2']
names = {}      # user rule: no MCU pin names on the silkscreen
for num, nm in names.items():
    p = u2.FindPadByNumber(str(num)); x, y = ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)
    t = add_text(u2, nm, pcbnew.F_SilkS)
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT if num <= 9 else pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    t.SetTextPos(pcbnew.VECTOR2I(MM(x + (1.35 if num <= 9 else -1.35)), MM(y)))
    if num in (9, 15):                       # bottom pads 10-14 are next to these: put the name outside the outline
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT if num == 9 else pcbnew.GR_TEXT_H_ALIGN_LEFT)
        t.SetTextPos(pcbnew.VECTOR2I(MM(x + (-2.4 if num == 9 else 2.4)), MM(y)))
        if not free('F', box_of(t)):
            t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetTextPos(pcbnew.VECTOR2I(MM(x), MM(y + 2.75)))
            if not free('F', box_of(t)): u2.Remove(t); print('no label for U2 pad', num); continue
    mark('F', box_of(t), GAP)
p1 = u2.FindPadByNumber('1'); ux = ToMM(p1.GetPosition().x) + 7.62; uy = ToMM(p1.GetPosition().y)
t = add_text(u2, 'USB-C', pcbnew.F_SilkS); t.SetTextPos(pcbnew.VECTOR2I(MM(ux), MM(uy - 0.2))); mark('F', box_of(t), GAP)
t = add_text(u2, 'U2 RP2040-Zero', pcbnew.F_SilkS); t.SetTextAngleDegrees(90); t.SetTextPos(pcbnew.VECTOR2I(MM(ux), MM(uy + 11.0))); mark('F', box_of(t), GAP)
u2.Reference().SetVisible(False)
mark('F', fp_rect(u2), 0.0)                         # the module covers this area: nothing else goes here

# ---------------------------------------------------------------- connector pin names
def pin_labels(ref, labels, ang=0, prefer_h=False):
    """put each pin name just outside its pad, on the side pointing away from the footprint centre"""
    f = fps[ref]; ok = True; OWNER['id'] = fid[ref]; OWNER['near'] = False
    rc = fp_rect(f); fcx, fcy = (rc[0] + rc[2]) / 2, (rc[1] + rc[3]) / 2
    for num, nm in labels.items():
        p = f.FindPadByNumber(str(num)); x, y = ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)
        t = add_text(f, nm, pcbnew.F_SilkS); style(t)
        dx, dy = x - fcx, y - fcy; L = math.hypot(dx, dy) or 1.0; dx, dy = dx / L, dy / L
        pr = ToMM(p.GetSize().x) / 2
        dirs = [(dx, dy), (math.copysign(1, dx), 0), (0, math.copysign(1, dy)), (0, -1), (0, 1), (1, 0), (-1, 0)]
        if prefer_h: dirs = [(math.copysign(1, dx), 0), (0, math.copysign(1, dy))]
        done = False
        for a in ([ang] if ang else [0, 90]):
            t.SetTextAngleDegrees(a); t.SetTextPos(pcbnew.VECTOR2I(MM(0), MM(0))); r0 = box_of(t)
            hw, hh = (r0[2] - r0[0]) / 2, (r0[3] - r0[1]) / 2
            for (ux_, uy_) in dirs:
                for extra in (0.0, 0.3, 0.6, 0.9):
                    dist = pr + 0.35 + extra + (hw if abs(ux_) >= abs(uy_) else hh)
                    if try_at(t, 'F', x + ux_ * dist, y + uy_ * dist, a): done = True; break
                if done: break
            if done: break
        if not done: f.Remove(t); ok = False; print('pin label failed', ref, num, nm)
    OWNER['near'] = True
    return ok
OWNER['id'] = fid['J1']
_j1 = fps['J1']; _jr = fp_rect(_j1); _jcx = (_jr[0] + _jr[2]) / 2
for _num, _nm in {1: 'A', 2: 'K', 3: 'E', 4: 'C'}.items():   # RPR-220 のデータシート: 1 アノード、2 カソード、3 エミッタ、4 コレクタ
    _p = _j1.FindPadByNumber(str(_num)); _x, _y = ToMM(_p.GetPosition().x), ToMM(_p.GetPosition().y)
    t = add_text(_j1, _nm, pcbnew.F_SilkS); _sx = 1 if _x > _jcx else -1
    t.SetTextPos(pcbnew.VECTOR2I(MM(0), MM(0))); _r0 = box_of(t); _hw = (_r0[2] - _r0[0]) / 2
    t.SetTextPos(pcbnew.VECTOR2I(MM(_x + _sx * (ToMM(_p.GetSize().x) / 2 + PADCLR + 0.05 + _hw)), MM(_y))); _r = box_of(t)
    i0, i1, j0, j1 = rix(*_r)
    if _r[0] >= 0.2 and not padocc[i0:i1, j0:j1].any() and not labocc[i0:i1, j0:j1].any():
        mark('F', _r, GAP); i0, i1, j0, j1 = rix(_r[0] - GAP, _r[1] - GAP, _r[2] + GAP, _r[3] + GAP); labocc[i0:i1, j0:j1] = True
    else: _j1.Remove(t); print('J1 letter failed', _nm, _r)
# J1 の切り欠きの角の外側にシルクの点（外形は F.Fab に移したので、向きの目印として。2026-10-27）
sys.path.insert(0, __file__.rsplit('\\', 1)[0].rsplit('/', 1)[0])
from j1_notch_dot import add_notch_dot
print('J1 notch dot', add_notch_dot(b))
# Rev.F: GND のテストランド（両面）の表の文字。裏の「GND」はフットプリントに入っている
if 'TP5' in fps:
    OWNER['id'] = fid['TP5']; _t5 = fps['TP5']; _t5.Reference().SetLayer(pcbnew.F_Fab); _t5.Value().SetLayer(pcbnew.F_Fab)
    t = add_text(_t5, 'GND', pcbnew.F_SilkS)
    if not place(t, 'F', fp_rect(_t5), 0, 3.0, False): _t5.Remove(t); print('GND label failed')
OWNER['id'] = fid['J5']; p5 = fps['J5'].FindPadByNumber('1')
t = add_text(fps['J5'], '1', pcbnew.F_SilkS)
place(t, 'F', box_of(p5), 0, 1.5)

# ---------------------------------------------------------------- references and values (one label per part: "R11 180k")
order = sorted(fps, key=lambda r: -((fp_rect(fps[r])[2] - fp_rect(fps[r])[0]) * (fp_rect(fps[r])[3] - fp_rect(fps[r])[1])))
PRIO = ['J1', 'C10', 'C8']   # Rev.F の番号（Rev.E の C11, C9）
order = PRIO + [r for r in order if r not in PRIO and not r.startswith('TP')]   # TP は下で（TP5 は上で）
WITH_VALUE = lambda r: r.startswith(('Q', 'U1', 'J5', 'SW'))   # part numbers (and switch function names) only, no R/C values
SPECIAL = {'J1': ['J1 RPR-220', 'RPR-220', 'J1']}
nref = 0; fails = []; refonly = []
TPS = ['TP1', 'TP3', 'TP2', 'TP4']
for r in [x for x in order if x in PRIO] + TPS + [x for x in order if x not in PRIO]:
    if r == 'U2': continue
    if r in TPS:
        f = fps[r]; f.Reference().SetLayer(pcbnew.F_Fab); f.Value().SetLayer(pcbnew.F_Fab)
        if not pin_labels(r, {1: r}, ang=90 if r in ('TP1', 'TP3') else 0) and r in ('TP1', 'TP3'): pin_labels(r, {1: r})
        continue
    f = fps[r]; rc = fp_rect(f); OWNER['id'] = fid[r]
    vert = (rc[3] - rc[1]) > (rc[2] - rc[0]) * 1.3
    f.Reference().SetLayer(pcbnew.F_Fab); f.Value().SetLayer(pcbnew.F_Fab)
    if r in SPECIAL: texts = SPECIAL[r]
    elif r.startswith('TP') and False:
        nmv = {'TP_SENS': 'SENS', 'TP_OUT': 'OUT', 'TP_BIAS': 'BIAS', 'TP_F': 'PULSE'}.get(f.GetValue(), f.GetValue())
        texts = ['%s %s' % (r, nmv), nmv, r]
    elif WITH_VALUE(r): texts = ['${REFERENCE} ${VALUE}', '${REFERENCE}']
    else: texts = ['${REFERENCE}']
    inside = r not in ('J5',)
    t = add_text(f, texts[0], pcbnew.F_SilkS); ok = False
    for k, txt in enumerate(texts):
        t.SetText(txt)
        if place(t, 'F', rc, 90 if vert else 0, 5.0 if r.startswith(('TP', 'J1')) else 3.0, inside):
            ok = True
            if k > 0: refonly.append(r)
            break
    if ok: nref += 1
    else: f.Remove(t); fails.append(r)


# ---------------------------------------------------------------- title (front) and GPIO table (back)
def place_free(text, layer, side, h, mirrored=False):
    OWNER['id'] = -1
    t = pcbnew.PCB_TEXT(b); t.SetText(text); t.SetLayer(layer); style(t, h)
    if mirrored: t.SetMirrored(True)
    t.SetTextAngleDegrees(0); t.SetTextPos(pcbnew.VECTOR2I(MM(0), MM(0)))
    r0 = box_of(t); w, hh = r0[2] - r0[0], r0[3] - r0[1]
    best = None
    for y in np.arange(EDGE + hh / 2, BH - EDGE - hh / 2, 0.5):
        for x in np.arange(EDGE + w / 2, BW - EDGE - w / 2, 0.5):
            t.SetTextPos(pcbnew.VECTOR2I(MM(x), MM(y)))
            if free(side, box_of(t)):
                best = (x, y); break
        if best: break
    if not best: return None
    t.SetTextPos(pcbnew.VECTOR2I(MM(best[0]), MM(best[1]))); mark(side, box_of(t), GAP); b.Add(t); return best
title_at = place_free('VASCULAR AGE METER  Rev.F', pcbnew.F_SilkS, 'F', 1.2) or \
           place_free('VASCULAR AGE METER  Rev.F', pcbnew.B_SilkS, 'B', 1.5, mirrored=True)
back_at = None   # user rule: no MCU pin names (GPIO table removed)
table = ''
for z in b.Zones(): pass
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(OUT, b)
print('labels', nref, 'shortened', refonly, 'no label', fails, 'title', title_at, 'back table', back_at)
