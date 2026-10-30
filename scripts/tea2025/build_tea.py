# -*- coding: utf-8 -*-
"""Build the TEA2025 amp kit PCB (100 x 50 mm, 2 layers, M3 holes at the corners) from the KiCad XML netlist.
Placement: fixed table (signal flow left -> right: input jack, volume, TEA2025, output caps, speaker terminals;
power along the bottom). Routing: the grid A* router of KiCad_work/build_board.py (45-degree lines, few corners),
signal 0.5 mm, power 1.0 -> 0.7 -> 0.5 mm, GND as pours on both layers. Run with KiCad's python:
    python build_tea.py <netlist.xml> <out.kicad_pcb>          (env CHECKONLY=1: place + report only)
"""
import sys, os, math, heapq, collections
import xml.etree.ElementTree as ET
import numpy as np
import pcbnew
from pcbnew import FromMM as MM, ToMM

sys.stdout.reconfigure(encoding="utf-8")
NETLIST, OUT = sys.argv[1], sys.argv[2]
PRJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
W, H = 100.0, 50.0
G = 0.25
GAP = 2.5                      # courtyard-to-courtyard gap (user 2026-10-21: "まだゆとりがあるので部品同士を離して"; rule 04-8 default 1.2)
FIXED = {"H1", "H2", "H3", "H4", "J1", "J2", "J3", "J4", "J5"}   # edge connectors and holes stay where PLACE puts them
KEEPOUT = [(6.5, 2.0, 42.0, 10.6),   # board title / revision silk (silk_tea.py EXTRA)
           (87.5, 10.5, 91.7, 20.5), (87.5, 29.5, 91.7, 39.5)]   # L+/L-/R+/R- marks beside J3 / J2
VIA_D, VIA_DRILL = 0.8, 0.4
ZONE_CLR = 0.4                 # pour to pad/track clearance (easier hand soldering)
SIG_WIDTHS = [0.5]             # rule 05-2: never below 0.5 mm
PWR_WIDTHS = [1.0, 0.7, 0.5]
POWER_NETS = {"/VIN", "/VCC", "/OUT1", "/OUT2", "/SPK_L", "/SPK_R"}
GNDN = "/GND"
FULL_GND = {"U1"}              # GND pads connected solid to the pour (heat sinking of the TEA2025)
FPDIR = "C:/Program Files/KiCad/10.0/share/kicad/footprints/"
LIBS = {"TEA2025_amp": PRJ + "/lib/TEA2025_amp/TEA2025_amp.pretty"}

# footprint origin (x, y) in mm and rotation (deg, CCW)
PLACE = {
    "H1": (3.5, 3.5, 0), "H2": (96.5, 3.5, 0), "H3": (3.5, 46.5, 0), "H4": (96.5, 46.5, 0),
    # input
    "J1": (2.9, 25.0, 90),          # 3.5mm jack, opening to the left edge
    "RV1": (24.25, 23.5, 90),       # shaft centre; pins column at x = 35.25
    "C2": (41.0, 21.0, 90), "C1": (41.0, 27.25, 270),
    # amplifier
    "U1": (65.5, 18.5, 270),        # pin 1 at the right end of the top row
    "C11": (48.5, 13.0, 90), "C4": (56.75, 13.0, 90), "C6": (65.0, 13.0, 90),
    "C3": (52.75, 31.75, 270), "C5": (60.5, 32.75, 0),
    # output: column 1 (470u + films), column 2 (104 in parallel with C10 / C9)
    "C8": (72.75, 5.25, 0), "C10": (72.0, 14.25, 0), "C13": (72.0, 21.25, 0), "C9": (72.0, 28.25, 0), "C7": (72.5, 37.25, 0),
    "C15": (84.25, 15.5, 90), "C14": (84.25, 33.0, 90),
    "J3": (96.2, 18.0, 90), "J2": (96.2, 37.0, 90),
    # power (bottom edge)
    "J4": (15.7, 49.7, 90),         # DC jack, opening to the bottom edge
    "SW1": (32.5, 43.0, 270),
    "J5": (47.5, 46.3, 0),          # battery terminal, wire entry to the bottom edge; room for +/- on both sides
    "C12": (60.25, 44.5, 0), "R1": (71.25, 45.75, 0), "D1": (83.75, 46.0, 0),
}

# ------------------------------------------------------------------ netlist -> board
root = ET.parse(NETLIST).getroot()
comps = {}
for c in root.find("components"):
    flds = {fe.get("name"): (fe.text or "") for fe in c.find("fields")} if c.find("fields") is not None else {}
    comps[c.get("ref")] = (c.findtext("value"), c.findtext("footprint"), flds, c.findtext("tstamps"))
nets = collections.OrderedDict()
for n in root.find("nets"):       # single-pin "unconnected-" nets are kept for schematic parity, not routed
    nets[n.get("name")] = [(nd.get("ref"), nd.get("pin")) for nd in n.findall("node")]

board = pcbnew.BOARD()
netinfo = {}
for name in nets:
    ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); netinfo[name] = ni
fps = {}
for ref, (val, fpid, flds, tstamp) in comps.items():
    lib, nm = fpid.split(":")
    f = pcbnew.FootprintLoad(LIBS.get(lib, FPDIR + lib + ".pretty"), nm)
    if f is None: raise SystemExit("footprint not found: " + fpid)
    f.SetReference(ref); f.SetValue(val); f.SetFPID(pcbnew.LIB_ID(lib, nm))
    for k, v in flds.items():        # schematic fields (MPN, Akizuki, Datasheet, ...) -> footprint, hidden
        if k == "Footprint": continue
        f.SetField(k, v)
        fld = f.GetField(k)
        if k not in ("Reference", "Value") and fld is not None: fld.SetVisible(False)
    f.SetPath(pcbnew.KIID_PATH("/" + tstamp)); f.SetSheetname("/"); f.SetSheetfile("TEA2025_amp.kicad_sch")
    board.Add(f); fps[ref] = f
for name, nodes in nets.items():
    for ref, pin in nodes:
        hit = [p for p in fps[ref].Pads() if p.GetNumber() == pin]
        if not hit: raise SystemExit("pad not found %s.%s" % (ref, pin))
        for p in hit: p.SetNet(netinfo[name])
for ref, f in fps.items():   # same-numbered pads are one terminal (jack tip legs, DC jack B slots) -- rule 05-8
    nums = [p.GetNumber() for p in f.Pads() if p.GetNumber()]
    if len(nums) != len(set(nums)): f.SetDuplicatePadNumbersAreJumpers(True)

ds = board.GetDesignSettings()
for attr, v in (("m_MinClearance", 0.2), ("m_TrackMinWidth", 0.2), ("m_ViasMinSize", 0.6), ("m_MinThroughDrill", 0.3),
                ("m_CopperEdgeClearance", 0.3)):
    try: setattr(ds, attr, MM(v))
    except Exception: pass

def edge(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
    s.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1))); s.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    board.Add(s)
for (a, b, c, d) in [(0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)]:
    edge(a, b, c, d)

# ------------------------------------------------------------------ placement + checks
for ref, f in fps.items():
    x, y, r = PLACE[ref]
    f.SetOrientationDegrees(r); f.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))

def cy_box(f):
    cy = f.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() > 0 else f.GetBoundingBox(False)
    return ToMM(bb.GetX()), ToMM(bb.GetY()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())

# spread: push courtyards apart to GAP (axis-aligned, damped), springs keep each part near its PLACE position
anchor = {r: (PLACE[r][0], PLACE[r][1]) for r in fps}
pos = dict(anchor)
off = {}
for r, f in fps.items():
    b0 = cy_box(f); off[r] = (b0[0] - anchor[r][0], b0[1] - anchor[r][1], b0[2] - anchor[r][0], b0[3] - anchor[r][1])
def pbox(r):
    x, y = pos[r]; o = off[r]; return (x + o[0], y + o[1], x + o[2], y + o[3])
items = sorted(fps)
mov = [r for r in items if r not in FIXED]
for it in range(3000):
    worst = 0.0
    boxes_now = {r: pbox(r) for r in items}
    for k in KEEPOUT: boxes_now[("KO",) + k] = k
    keys = list(boxes_now)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            fa = not isinstance(a, str) or a in FIXED; fb = not isinstance(b, str) or b in FIXED
            if fa and fb: continue
            A, B = boxes_now[a], boxes_now[b]
            g = GAP if (isinstance(a, str) and isinstance(b, str)) else 0.6     # keepouts only need a small margin
            ox = min(A[2], B[2]) - max(A[0], B[0]) + g
            oy = min(A[3], B[3]) - max(A[1], B[1]) + g
            if ox <= 0 or oy <= 0: continue
            worst = max(worst, min(ox, oy))
            cax, cay = (A[0] + A[2]) / 2, (A[1] + A[3]) / 2; cbx, cby = (B[0] + B[2]) / 2, (B[1] + B[3]) / 2
            dx, dy = ((ox if cax >= cbx else -ox), 0.0) if ox < oy else (0.0, (oy if cay >= cby else -oy))
            wa = 0.0 if fa else (1.0 if fb else 0.5); wb = 0.0 if fb else (1.0 if fa else 0.5)
            if not fa: pos[a] = (pos[a][0] + 0.5 * wa * dx, pos[a][1] + 0.5 * wa * dy)
            if not fb: pos[b] = (pos[b][0] - 0.5 * wb * dx, pos[b][1] - 0.5 * wb * dy)
    for r in mov:
        x, y = pos[r]; x += 0.004 * (anchor[r][0] - x); y += 0.004 * (anchor[r][1] - y)
        o = off[r]
        x = min(max(x, 0.6 - o[0]), W - 0.6 - o[2]); y = min(max(y, 0.6 - o[1]), H - 0.6 - o[3])
        pos[r] = (x, y)
    if worst < 0.005: break
print("spread iterations", it, "residual", round(worst, 3))
for r in mov:
    x, y = round(pos[r][0] * 4) / 4, round(pos[r][1] * 4) / 4      # 0.25 mm grid
    fps[r].SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    if abs(x - anchor[r][0]) > 0.01 or abs(y - anchor[r][1]) > 0.01:
        print("  moved %-4s (%.2f, %.2f) -> (%.2f, %.2f)" % (r, anchor[r][0], anchor[r][1], x, y))

boxes = {r: cy_box(f) for r, f in fps.items()}
bad = 0
refs = sorted(boxes)
for i, a in enumerate(refs):
    for b in refs[i + 1:]:
        A, B = boxes[a], boxes[b]
        dx = max(B[0] - A[2], A[0] - B[2]); dy = max(B[1] - A[3], A[1] - B[3])
        gap = max(dx, dy)          # >0: separated by this much along one axis
        if gap < GAP:
            bad += 1; print("GAP %-4s %-4s %.2f" % (a, b, gap))
for r, (x0, y0, x1, y1) in boxes.items():
    if x0 < -0.01 or y0 < -0.01 or x1 > W + 0.01 or y1 > H + 0.01: print("OUTSIDE", r, (round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)))
    for p in fps[r].Pads():
        bb = p.GetBoundingBox(); e = min(ToMM(bb.GetX()), ToMM(bb.GetY()), W - ToMM(bb.GetRight()), H - ToMM(bb.GetBottom()))
        if e < 0.8: print("PAD-EDGE %s.%s %.2f" % (r, p.GetNumber(), e))
print("placement issues:", bad, flush=True)
if os.environ.get("CHECKONLY"):
    pcbnew.SaveBoard(OUT, board); raise SystemExit(0)

# ------------------------------------------------------------------ router (from KiCad_work/build_board.py)
nx, ny = int(W / G) + 1, int(H / G) + 1
own = np.zeros((2, ny, nx), dtype=np.int16)
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]
netcode = {name: ni.GetNetCode() for name, ni in netinfo.items()}

def mark_rect(l, x0, y0, x1, y1, net):
    ix0 = max(0, int(math.ceil(x0 / G))); ix1 = min(nx - 1, int(math.floor(x1 / G)))
    iy0 = max(0, int(math.ceil(y0 / G))); iy1 = min(ny - 1, int(math.floor(y1 / G)))
    if ix1 < ix0: ix0 = ix1 = min(nx - 1, int(round((x0 + x1) / 2 / G)))
    if iy1 < iy0: iy0 = iy1 = min(ny - 1, int(round((y0 + y1) / 2 / G)))
    sub = own[l, iy0:iy1 + 1, ix0:ix1 + 1]
    fr = sub == 0; cf = (sub != 0) & (sub != net) & (sub != -1)
    sub[fr] = net; sub[cf] = -2

_off = {}
def offsets(r):
    if r not in _off: _off[r] = [(dx, dy) for dy in range(-r, r + 1) for dx in range(-r, r + 1) if dx * dx + dy * dy <= r * r + 1]
    return _off[r]
def mark_disk(l, ix, iy, r, net):
    for dx, dy in offsets(r):
        x, y = ix + dx, iy + dy
        if 0 <= x < nx and 0 <= y < ny:
            o = own[l, y, x]
            if o == 0: own[l, y, x] = net
            elif o != net and o != -1: own[l, y, x] = -2
def dilate(mask, r):
    out = mask.copy()
    for dx, dy in offsets(r):
        if dx == 0 and dy == 0: continue
        yd = slice(max(0, dy), ny + min(0, dy)); ys = slice(max(0, -dy), ny + min(0, -dy))
        xd = slice(max(0, dx), nx + min(0, dx)); xs = slice(max(0, -dx), nx + min(0, -dx))
        out[yd, xd] |= mask[ys, xs]
    return out

EB = int(math.ceil(0.5 / G))
for l in range(2):
    own[l, :EB, :] = -1; own[l, -EB:, :] = -1; own[l, :, :EB] = -1; own[l, :, -EB:] = -1

pads_by_net = {}
for ref, f in fps.items():
    for p in f.Pads():
        bb = p.GetBoundingBox()
        x0, y0 = ToMM(bb.GetX()), ToMM(bb.GetY()); x1, y1 = x0 + ToMM(bb.GetWidth()), y0 + ToMM(bb.GetHeight())
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:      # mounting hole: keep 0.5 mm around the drill
            x0 -= 0.5; y0 -= 0.5; x1 += 0.5; y1 += 0.5
        nm = p.GetNetname(); code = netcode.get(nm, 0)
        for l in range(2): mark_rect(l, x0, y0, x1, y1, code if code > 0 else -2)
        if code > 0: pads_by_net.setdefault(nm, []).append((ref, str(p.GetNumber()), x0, y0, x1, y1))

def pad_cells(pad, shrink=0.12):
    _, _, x0, y0, x1, y1 = pad
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; rx, ry = max((x1 - x0) / 2 - shrink, 0.01), max((y1 - y0) / 2 - shrink, 0.01)
    cells = [(ix, iy) for iy in range(int(math.ceil((y0 + shrink) / G)), int(math.floor((y1 - shrink) / G)) + 1)
             for ix in range(int(math.ceil((x0 + shrink) / G)), int(math.floor((x1 - shrink) / G)) + 1)
             if ((ix * G - cx) / rx) ** 2 + ((iy * G - cy) / ry) ** 2 <= 1.0]
    return cells or [(int(round(cx / G)), int(round(cy / G)))]

def blocked(net, width, margin):
    rt = int(math.ceil((width / 2 + margin) / G)); rv = int(math.ceil((VIA_D / 2 + margin) / G))
    bt, bv = [], []
    for l in range(2):
        fg = (own[l] != 0) & (own[l] != net)
        bt.append(dilate(fg, rt)); bv.append(dilate(fg, rv))
    return [b.tolist() for b in bt], (bv[0] | bv[1]).tolist()

DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
SQ2 = 1.41421356
CAP = 60000
HW = 2.2
def astar(starts, targets, bt, vb):
    tset = set(targets)
    tx = sum(t[0] for t in targets) / len(targets); ty = sum(t[1] for t in targets) / len(targets)
    def hh(ix, iy):
        dx, dy = abs(ix - tx), abs(iy - ty); return max(dx, dy) + 0.414 * min(dx, dy)
    dist, prev, pq = {}, {}, []
    nexp = 0
    for (l, ix, iy) in starts:
        s = (l, ix, iy, -1); dist[s] = 0.0; heapq.heappush(pq, (HW * hh(ix, iy), 0.0, s))
    while pq:
        f_, d, cur = heapq.heappop(pq)
        if d > dist.get(cur, 1e18): continue
        nexp += 1
        if nexp > CAP: return None
        l, ix, iy, dr = cur
        if (ix, iy) in tset:
            path = [cur]
            while cur in prev:
                cur = prev[cur]; path.append(cur)
            return path[::-1]
        for k, (dx, dy) in enumerate(DIRS):
            if dr != -1:
                diff = min(abs(k - dr), 8 - abs(k - dr))
                if diff > 2: continue
                turn = 0.0 if diff == 0 else (1.2 if diff == 1 else 2.6)
            else: turn = 0.0
            nix, niy = ix + dx, iy + dy
            if nix < 0 or niy < 0 or nix >= nx or niy >= ny or bt[l][niy][nix]: continue
            if dx != 0 and dy != 0 and (bt[l][iy][nix] or bt[l][niy][ix]): continue
            if dx != 0 and dy != 0: c = SQ2
            else: c = 1.0 + (0.25 if ((l == 0 and dy != 0) or (l == 1 and dx != 0)) else 0.0)
            nd = d + c + turn; n = (l, nix, niy, k)
            if nd < dist.get(n, 1e18):
                dist[n] = nd; prev[n] = cur; heapq.heappush(pq, (nd + HW * hh(nix, niy), nd, n))
        if not vb[iy][ix] and not bt[1 - l][iy][ix]:
            n = (1 - l, ix, iy, -1); nd = d + 9.0
            if nd < dist.get(n, 1e18):
                dist[n] = nd; prev[n] = cur; heapq.heappush(pq, (nd + HW * hh(ix, iy), nd, n))
    return None

def commit(net, width, path):
    rc = int(math.ceil(width / 2 / G)); rvc = int(math.ceil(VIA_D / 2 / G))
    for i, (l, ix, iy, dr) in enumerate(path):
        mark_disk(l, ix, iy, rc, net)
        if i > 0 and path[i - 1][0] != l:
            for ll in range(2): mark_disk(ll, ix, iy, rvc, net)

def hpwl(nm):
    ps = pads_by_net[nm]
    xs = [(p[2] + p[4]) / 2 for p in ps]; ys = [(p[3] + p[5]) / 2 for p in ps]
    return (max(xs) - min(xs)) + (max(ys) - min(ys))
order = [n for n in pads_by_net if n != GNDN and not n.startswith("unconnected-") and len(pads_by_net[n]) >= 2]

own0 = own.copy()
prio = collections.Counter()
best = None
for attempt in range(int(os.environ.get('ATT', '3'))):
    own[:] = own0
    segs, vias, failed = [], [], []
    order.sort(key=lambda n: (-prio[n], 0 if n in POWER_NETS else 1, hpwl(n)))
    for nm in order:
        net = netcode[nm]; pads = pads_by_net[nm]
        ladder = PWR_WIDTHS if nm in POWER_NETS else SIG_WIDTHS
        tree = set((l, ix, iy) for l in range(2) for (ix, iy) in pad_cells(pads[0]))
        remaining = list(range(1, len(pads)))
        while remaining:
            def dmin(i):
                cx = (pads[i][2] + pads[i][4]) / 2 / G; cy = (pads[i][3] + pads[i][5]) / 2 / G
                return min(abs(t[1] - cx) + abs(t[2] - cy) for t in tree)
            i = min(remaining, key=dmin); tg = pad_cells(pads[i]); path = None; used = None
            for w in ladder:
                for margin in (0.46, 0.34, 0.27, 0.23):
                    CAP = 300000 if (w == ladder[-1] and margin == 0.23) else 60000
                    bt, vb = blocked(net, w, margin)
                    for c in tg:
                        for l in range(2): bt[l][c[1]][c[0]] = False
                    path = astar(list(tree), tg, bt, vb)
                    if path: used = w; break
                if path: break
            if path is None:
                failed.append((nm, pads[0][0] + "." + pads[0][1], pads[i][0] + "." + pads[i][1]))
            else:
                commit(net, used, path)
                for (l, ix, iy, dr) in path: tree.add((l, ix, iy))
                for l in range(2):
                    for c in tg: tree.add((l, c[0], c[1]))
                k = 0
                while k < len(path) - 1:
                    l, x, y, dr = path[k]
                    if path[k + 1][0] != l:
                        vias.append((net, x, y)); k += 1; continue
                    j = k + 1
                    d0 = path[j][3]
                    while j + 1 < len(path) and path[j + 1][0] == l and path[j + 1][3] == d0 and path[j + 1][3] != -1:
                        j += 1
                    segs.append((net, used, l, (x, y), (path[j][1], path[j][2]))); k = j
            remaining.remove(i)
        print("routed", nm, flush=True)
    print("attempt", attempt, "failed", len(failed), flush=True)
    if best is None or len(failed) < len(best[2]): best = (segs, vias, failed)
    if not failed: break
    for f in failed: prio[f[0]] += 1
segs, vias, failed = best
for net, w, l, a, b in segs:
    if a == b: continue
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(a[0] * G), MM(a[1] * G))); t.SetEnd(pcbnew.VECTOR2I(MM(b[0] * G), MM(b[1] * G)))
    t.SetWidth(MM(w)); t.SetLayer(LAYERS[l]); t.SetNetCode(net); board.Add(t)
for net, x, y in vias:
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x * G), MM(y * G)))
    v.SetWidth(MM(VIA_D)); v.SetDrill(MM(VIA_DRILL)); v.SetNetCode(net); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    board.Add(v)

gndcode = netcode[GNDN]
for ref in FULL_GND:
    for p in fps[ref].Pads():
        if p.GetNetname() == GNDN: p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
def zone(layer):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNetCode(gndcode)
    z.SetLocalClearance(MM(ZONE_CLR)); z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.4)); z.SetThermalReliefSpokeWidth(MM(0.5))
    o = z.Outline(); o.NewOutline()
    for (x, y) in [(0.5, 0.5), (W - 0.5, 0.5), (W - 0.5, H - 0.5), (0.5, H - 0.5)]:
        o.Append(MM(x), MM(y))
    board.Add(z)
zone(pcbnew.F_Cu); zone(pcbnew.B_Cu)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(OUT, board)
cnt = collections.Counter(round(s[1], 2) for s in segs if s[3] != s[4])
print("segments", len(segs), "vias", len(vias), "widths", dict(cnt))
print("FAILED:", failed)
