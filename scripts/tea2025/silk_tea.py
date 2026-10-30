# -*- coding: utf-8 -*-
"""Silkscreen for the TEA2025 amp kit (run with KiCad's python):
    python silk_tea.py <in.kicad_pcb> <out.kicad_pcb>
- one label per part "REF VALUE" (user request: part values on the silk, so a kit can be built without a manual;
  ref and value in ONE text so they cannot be mixed up -- rule 06-4/5), 1.0 mm / 0.15 mm, within 3 mm of the part,
  never closer to another part than to its own, never over pads / silk / other parts / board edge
- terminal pin marks (+ / -), kit name and revision
Copper and footprint positions are not touched."""
import sys, math
import pcbnew
from pcbnew import FromMM as MM, ToMM

sys.stdout.reconfigure(encoding="utf-8")
IN, OUT = sys.argv[1], sys.argv[2]
board = pcbnew.LoadBoard(IN)
W, H = 100.0, 50.0
TH, TT = 1.0, 0.15               # text height / thickness (rule 06-3)
EDGE = 0.6
LABEL = {"J1": "INPUT", "J2": "SP L", "J3": "SP R", "J4": "DC9V CENTER+", "J5": "BATT 9V", "SW1": "POWER",
         "RV1": "VOL 10kA", "D1": "LED"}
SKIP = {"H1", "H2", "H3", "H4"}
# extra texts: (text, x, y, angle, height)
EXTRA = [("TEA2025 STEREO AMP KIT", 25.0, 5.0, 0, 1.8), ("Rev.A  2026", 25.0, 8.6, 0, 1.2)]
PINMARK = {("J2", "1"): "L+", ("J2", "2"): "L-", ("J3", "1"): "R+", ("J3", "2"): "R-",
           ("J5", "1"): "+", ("J5", "2"): "-"}
MARKSIDE = {"J2": "left", "J3": "left"}      # speaker terminals: marks beside the body, toward the board centre

fps = {f.GetReference(): f for f in board.GetFootprints()}


def box_of(item, pad=0.0):
    bb = item.GetBoundingBox()
    return (ToMM(bb.GetX()) - pad, ToMM(bb.GetY()) - pad, ToMM(bb.GetRight()) + pad, ToMM(bb.GetBottom()) + pad)


def court(f):
    cy = f.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() > 0 else f.GetBoundingBox(False)
    return (ToMM(bb.GetX()), ToMM(bb.GetY()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()))


def hit(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def dist_box(px, py, b):
    dx = max(b[0] - px, 0, px - b[2]); dy = max(b[1] - py, 0, py - b[3])
    return math.hypot(dx, dy)


def text_size(s, h=TH, t=TT):
    tx = pcbnew.PCB_TEXT(board); tx.SetText(s)
    tx.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h))); tx.SetTextThickness(MM(t))
    bb = tx.GetBoundingBox()
    return ToMM(bb.GetWidth()), h + t       # glyph height + stroke, not KiCad's line box (rule 06 note)


obst = []                                     # (box, owner)
for r, f in fps.items():
    for p in f.Pads(): obst.append((box_of(p, 0.25), r))
    for g in f.GraphicalItems():
        if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() != "PCB_TEXT" and g.GetClass() != "PCB_FIELD":
            obst.append((box_of(g, 0.15), r))
courts = {r: court(f) for r, f in fps.items()}
placed = []


def free(b, owner):
    if b[0] < EDGE or b[1] < EDGE or b[2] > W - EDGE or b[3] > H - EDGE: return False
    for ob, o in obst:
        if hit(b, ob): return False
    for pb in placed:
        if hit(b, pb): return False
    for r, c in courts.items():
        if r != owner and hit(b, c): return False
    return True


def add_text(f, s, x, y, ang, h=TH, t=TT):
    tx = pcbnew.PCB_TEXT(f)
    tx.SetText(s); tx.SetLayer(pcbnew.F_SilkS)
    tx.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h))); tx.SetTextThickness(MM(t))
    tx.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); tx.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    tx.SetTextAngleDegrees(ang); tx.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    tx.SetKeepUpright(True)
    f.Add(tx)


report = []
# terminal pin marks: outside the pad, away from the part centre
for (r, num), s in PINMARK.items():
    f = fps[r]; c = courts[r]; cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
    pad = [p for p in f.Pads() if p.GetNumber() == num][0]
    px, py = ToMM(pad.GetPosition().x), ToMM(pad.GetPosition().y)
    pb = box_of(pad)
    ok = False
    if MARKSIDE.get(r) == "left":
        mw, mh = text_size(s, 1.5, 0.25)
        x, y = c[0] - 0.3 - mw / 2, py; b = (x - mw / 2, y - mh / 2, x + mw / 2, y + mh / 2)
        if free(b, r):
            placed.append(b); add_text(f, s, x, y, 0, 1.5, 0.25); ok = True
    for d in ((0.5, 0.9, 1.4, 2.0) if not ok else ()):
        for (dx, dy) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            x = px + dx * ((pb[2] - pb[0]) / 2 + d + 0.6); y = py + dy * ((pb[3] - pb[1]) / 2 + d + 0.6)
            b = (x - 0.8, y - 0.8, x + 0.8, y + 0.8)
            if free(b, r):
                placed.append(b); add_text(f, s, x, y, 0, 1.5, 0.25); ok = True; break
        if ok: break
    report.append("mark %s.%s %s %s" % (r, num, s, "ok" if ok else "NO PLACE"))

for r in sorted(fps, key=lambda q: (q[0], int("".join(c for c in q if c.isdigit()) or 0))):
    if r in SKIP:
        fps[r].Reference().SetVisible(False); fps[r].Value().SetVisible(False); continue
    f = fps[r]
    f.Reference().SetVisible(False); f.Value().SetVisible(False)
    shown = "%s %s" % (r, LABEL.get(r, f.GetValue()))
    src = "${REFERENCE} " + (LABEL[r] if r in LABEL else "${VALUE}")
    tw, th = text_size(shown)
    c = courts[r]; cx, cy = (c[0] + c[2]) / 2, (c[1] + c[3]) / 2
    cands = []
    for ang in (0, 90):
        w, h = (tw, th) if ang == 0 else (th, tw)
        for gap in (0.2, 0.6, 1.0, 1.5, 2.0, 2.6):
            for k in [i / 8 for i in range(0, 9)]:
                xs = c[0] + w / 2 + (c[2] - c[0] - w) * k if c[2] - c[0] > w else cx
                ys = c[1] + h / 2 + (c[3] - c[1] - h) * k if c[3] - c[1] > h else cy
                cands += [(xs, c[1] - gap - h / 2, ang), (xs, c[3] + gap + h / 2, ang),
                          (c[0] - gap - w / 2, ys, ang), (c[2] + gap + w / 2, ys, ang)]
    best = None
    for (x, y, ang) in cands:
        w, h = (tw, th) if ang == 0 else (th, tw)
        b = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
        own_d = dist_box(x, y, c)
        if own_d > 3.0 + max(w, h) / 2: continue                  # within 3 mm (rule 06-4)
        if not free(b, r): continue
        others = min(dist_box(x, y, cc) for rr, cc in courts.items() if rr != r and rr not in SKIP)
        if others <= own_d: continue                               # closer to another part (rule 06-5)
        score = own_d + (1.5 if ang == 90 else 0) - 0.3 * min(others - own_d, 3)
        if best is None or score < best[0]: best = (score, x, y, ang, b)
    if best is None:
        report.append("NO PLACE " + shown); continue
    _, x, y, ang, b = best
    placed.append((b[0] - 0.25, b[1] - 0.25, b[2] + 0.25, b[3] + 0.25))
    add_text(f, src, x, y, ang)
    report.append("%-6s %-18s (%.1f, %.1f) %d" % (r, shown, x, y, ang))

for s, x, y, ang, h in EXTRA:
    tw, th = text_size(s, h, 0.25 if h >= 1.5 else TT)
    b = (x - tw / 2, y - th / 2, x + tw / 2, y + th / 2)
    if not free(b, None): report.append("EXTRA overlaps: " + s)
    t = pcbnew.PCB_TEXT(board); t.SetText(s); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h))); t.SetTextThickness(MM(0.25 if h >= 1.5 else TT))
    t.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y))); board.Add(t); placed.append(b)

pcbnew.SaveBoard(OUT, board)
print("\n".join(report))
