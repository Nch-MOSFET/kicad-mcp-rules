# -*- coding: utf-8 -*-
"""Build vascular_age_meter PCB (100 x 50 mm, no mounting holes) from a KiCad XML netlist.
Placement: free-space packer. Routing: numpy grid, 8-direction A* with turn penalties (45-degree straight lines,
few corners). Run with KiCad's python:
    python build_board.py <netlist.xml> <out.kicad_pcb> <project_dir>
"""
import sys, math, heapq, collections, re
import xml.etree.ElementTree as ET
import numpy as np
import pcbnew
from pcbnew import FromMM as MM, ToMM

NETLIST, OUT, PRJ = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 100.0, 50.0
G = 0.25
MARGIN = float(__import__('os').environ.get('MARGIN', '1.4'))
VIA_D, VIA_DRILL = 0.8, 0.4
ZONE_CLR = 0.25
SIG_WIDTHS = [0.5, 0.4, 0.3, 0.2]
PWR_WIDTHS = [1.0, 0.7, 0.5, 0.3]
POWER_NETS = {"VCC_A", "3V3"}
FPDIR = "C:/Program Files/KiCad/10.0/share/kicad/footprints/"

# ------------------------------------------------------------------ netlist -> board
root = ET.parse(NETLIST).getroot()
comps = {}
for c in root.find("components"):
    comps[c.get("ref")] = (c.findtext("value"), c.findtext("footprint"))
nets = collections.OrderedDict()
for n in root.find("nets"):
    name = n.get("name").lstrip("/")
    if name.startswith("unconnected-"): continue
    nets[name] = [(nd.get("ref"), nd.get("pin")) for nd in n.findall("node")]

board = pcbnew.BOARD()
netinfo = {}
for name in nets:
    ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); netinfo[name] = ni
fps = {}
for ref, (val, fpid) in comps.items():
    lib, nm = fpid.split(":")
    libdir = (PRJ + "/vam_custom.pretty") if lib == "vam_custom" else (PRJ + "/lib/rp2040_zero/rp2040_zero.pretty") if lib == "rp2040_zero" else (FPDIR + lib + ".pretty")
    f = pcbnew.FootprintLoad(libdir, nm)
    if f is None: raise SystemExit("footprint not found: " + fpid)
    f.SetReference(ref); f.SetValue(val); f.SetFPID(pcbnew.LIB_ID(lib, nm))
    board.Add(f); fps[ref] = f
for name, nodes in nets.items():
    for ref, pin in nodes:
        pad = fps[ref].FindPadByNumber(pin)
        if pad is None: raise SystemExit("pad not found %s.%s" % (ref, pin))
        pad.SetNet(netinfo[name])

# design rules
ds = board.GetDesignSettings()
for attr, v in (("m_MinClearance", 0.2), ("m_TrackMinWidth", 0.2), ("m_ViasMinSize", 0.6), ("m_MinThroughDrill", 0.3),
                ("m_CopperEdgeClearance", 0.3)):
    try: setattr(ds, attr, MM(v))
    except Exception: pass

def line(x1, y1, x2, y2):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.1))
    s.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1))); s.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
    board.Add(s)
for (a, b, c, d) in [(0, 0, W, 0), (W, 0, W, H), (W, H, 0, H), (0, H, 0, 0)]:
    line(a, b, c, d)

# ------------------------------------------------------------------ placement
def cy_bbox(f):
    try:
        cy = f.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount() > 0: return cy.BBox()
    except Exception: pass
    return f.GetBoundingBox(False)

def box(f):
    bb = cy_bbox(f); p = f.GetPosition()
    return ToMM(bb.GetX() - p.x), ToMM(bb.GetY() - p.y), ToMM(bb.GetWidth()), ToMM(bb.GetHeight())

NX, NY = int(W / G), int(H / G)
occ = np.zeros((NY, NX), dtype=bool)
tall = np.zeros((NY, NX), dtype=bool)
def ridx(x0, y0, x1, y1):
    return (max(0, int(math.floor(y0 / G))), min(NY, int(math.ceil(y1 / G))),
            max(0, int(math.floor(x0 / G))), min(NX, int(math.ceil(x1 / G))))
def mark(a, x0, y0, x1, y1):
    i0, i1, j0, j1 = ridx(x0, y0, x1, y1); a[i0:i1, j0:j1] = True
def isfree(a, x0, y0, x1, y1):
    if x0 < 0.4 or y0 < 0.4 or x1 > W - 0.4 or y1 > H - 0.4: return False
    i0, i1, j0, j1 = ridx(x0, y0, x1, y1); return not a[i0:i1, j0:j1].any()

def put(ref, x, y, rot=0, tl=True):
    """place so that the courtyard top-left is at (x, y)"""
    f = fps[ref]; f.SetOrientationDegrees(rot)
    ox, oy, w, h = box(f)
    f.SetPosition(pcbnew.VECTOR2I(MM(x - ox), MM(y - oy)))
    mark(occ, x - MARGIN / 2, y - MARGIN / 2, x + w + MARGIN / 2, y + h + MARGIN / 2)
    return w, h

def put_center(ref, cx, cy, rot=0):
    f = fps[ref]; f.SetOrientationDegrees(rot)
    ox, oy, w, h = box(f)
    return put(ref, cx - w / 2, cy - h / 2, rot)

import os
FROMBOARD = os.environ.get('FROMBOARD')
if FROMBOARD:      # reuse the placement (and GPIO map) of an existing board, e.g. for fix-up routing
    _ob = pcbnew.LoadBoard(FROMBOARD)
    for _f in _ob.GetFootprints():
        _r = _f.GetReference()
        if _r in fps:
            fps[_r].SetOrientation(_f.GetOrientation()); fps[_r].SetPosition(_f.GetPosition())
            for _p in _f.Pads():
                _q = fps[_r].FindPadByNumber(_p.GetNumber())
                if _q is not None and _p.GetNetname() in netinfo: _q.SetNet(netinfo[_p.GetNetname()])
else:
    exec(open('C:/Users/<user>/Documents/KiCad_work/place_v2_block.py', encoding='utf-8').read())
print("placed all parts", flush=True)

# ------------------------------------------------------------------ router
nx, ny = int(W / G) + 1, int(H / G) + 1
own = np.zeros((2, ny, nx), dtype=np.int16)
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]
netcode = {name: i + 1 for i, name in enumerate(nets)}
for name, ni in netinfo.items(): netcode[name] = ni.GetNetCode()

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

EB = int(math.ceil(0.3 / G))
for l in range(2):
    own[l, :EB, :] = -1; own[l, -EB:, :] = -1; own[l, :, :EB] = -1; own[l, :, -EB:] = -1

GNDN = "GND"
pads_by_net = {}
for ref, f in fps.items():
    for p in f.Pads():
        bb = p.GetBoundingBox()
        x0, y0 = ToMM(bb.GetX()), ToMM(bb.GetY()); x1, y1 = x0 + ToMM(bb.GetWidth()), y0 + ToMM(bb.GetHeight())
        nm = p.GetNetname(); code = netcode.get(nm, 0)
        for l in range(2):
            if code == 0: mark_rect(l, x0, y0, x1, y1, -2)
            else: mark_rect(l, x0, y0, x1, y1, code)
        if code > 0: pads_by_net.setdefault(nm, []).append((ref, str(p.GetNumber()), x0, y0, x1, y1))

def pad_cells(pad, shrink=0.12):
    """grid cells that lie on the pad copper (inscribed ellipse, so round pads do not get corner cells)"""
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
            else:
                c = 1.0 + (0.25 if ((l == 0 and dy != 0) or (l == 1 and dx != 0)) else 0.0)
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
order = [n for n in pads_by_net if n != GNDN and len(pads_by_net[n]) >= 2]
order.sort(key=lambda n: (0 if n in POWER_NETS else 1, hpwl(n)))

own0 = own.copy()
prio = collections.Counter()
best = None
for attempt in range(int(os.environ.get('ATT', '3'))):
    own[:] = own0
    segs, vias, failed = [], [], []
    order.sort(key=lambda n: (-prio[n], 0 if n in POWER_NETS else 1, (-hpwl(n) if os.environ.get('ORDER') == 'long' else hpwl(n))))
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
def zone(layer):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNetCode(gndcode)
    z.SetLocalClearance(MM(ZONE_CLR)); z.SetMinThickness(MM(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3)); z.SetThermalReliefSpokeWidth(MM(0.3))
    o = z.Outline(); o.NewOutline()
    for (x, y) in [(0.6, 0.6), (W - 0.6, 0.6), (W - 0.6, H - 0.6), (0.6, H - 0.6)]:
        o.Append(MM(x), MM(y))
    board.Add(z)
zone(pcbnew.F_Cu); zone(pcbnew.B_Cu)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(OUT, board)
cnt = collections.Counter(round(s[1], 2) for s in segs if s[3] != s[4])
print("segments", len(segs), "vias", len(vias), "widths", dict(cnt))
print("FAILED:", failed)
