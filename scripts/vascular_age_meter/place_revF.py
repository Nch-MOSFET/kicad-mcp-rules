# fixed items  (floor-plan variants; env VAR = A | A2 | B | C)
import os, random, json
VAR = os.environ.get('VAR', 'A')
CONG = float(os.environ.get('CONG', '3.0'))        # weight of routing-congestion (RUDY) penalty
PINSWAP = os.environ.get('PINSWAP', '1') == '1'     # allow re-assigning digital GPIOs on the RP2040-Zero
# Rev.F: 大物（センサ・マイコン・表示器・スイッチ・GND ランド）は Rev.E の位置にそろえて固定する（FIXEDFROM の基板から読む）
_fx = pcbnew.LoadBoard(os.environ['FIXEDFROM'])
for _r in ("J1", "U2", "J5", "SW1", "SW2", "TP5"):
    _o = _fx.FindFootprintByReference(_r)
    fps[_r].SetOrientation(_o.GetOrientation()); fps[_r].SetPosition(_o.GetPosition())
# モジュール（18 x 23.5 mm）の範囲。足の列の中心から ±9 mm、上端から 23.9 mm まで（外形のシルクは使わない）
_xs = [ToMM(_p.GetPosition().x) for _p in fps["U2"].Pads()]
_cx = (min(_xs) + max(_xs)) / 2
RP = (_cx - 9.0, 0.4, _cx + 9.0, 23.9)
print("RP keep-out", RP, flush=True)
UNDER_OK = set()   # user rule: nothing (not even resistors) under the RP2040-Zero module
FIXED = ["J1", "U2", "J5", "SW1", "SW2", "TP5"]
MOV = [r for r in fps if r not in FIXED]
ROT4 = (0, 90, 180, 270)                            # use rotation actively
# functional regions (x-range); parts outside get a penalty
G_ANA = {"R1", "R2", "RV1", "TP1", "C1", "R3", "R4", "RV2", "C2", "TP2", "R13", "R7", "R8", "C5", "TP3",
         "R9", "R10", "R11", "R12", "C7", "C8", "C9", "C10", "R14", "TP4", "C6", "U1",
         "R5", "R15"}          # Rev.F（役割の順の番号）: 張り付き解除の R5、SENS -> ADC の R15
G_MID = {"R6", "C3", "C4", "C11", "C12", "C13"}
G_DSP = {"R16", "R17", "R18", "R19", "R20", "R21", "R22", "R23", "R24", "Q1", "Q2"}
if True:
    REG = {'ana': (0, float(os.environ.get('ANAX', '44'))), 'mid': (22, float(os.environ.get('MIDX', '64'))), 'dsp': (56, 100)}
else:
    REG = {'ana': (0, 40), 'mid': (55, 100), 'dsp': (28, 78)}
def region_of(r):
    if r in G_ANA: return REG['ana']
    if r in G_MID: return REG['mid']
    if r in G_DSP: return REG['dsp']
    return (0, W)
# ---- per-part geometry tables
def pad_offsets(ref, rot):
    f = fps[ref]; f.SetOrientationDegrees(rot)
    p0 = f.GetPosition(); d = {}; allp = []
    for pd in f.Pads():
        q = pd.GetPosition(); off = (ToMM(q.x - p0.x), ToMM(q.y - p0.y)); allp.append(off)
        nm = pd.GetNetname()
        if not nm or nm == "GND": continue
        d.setdefault(nm, []).append(off)
    return d, allp
geo = {}
for r in MOV:
    geo[r] = {}
    for rot in ROT4:
        fps[r].SetOrientationDegrees(rot)
        d, allp = pad_offsets(r, rot)
        geo[r][rot] = (box(fps[r]), d, allp)
fixed_rect = {}; fixed_pads = {}; fixed_allpads = []
for r in FIXED:
    f = fps[r]; bb = cy_bbox(f)
    fixed_rect[r] = (ToMM(bb.GetX()), ToMM(bb.GetY()), ToMM(bb.GetX() + bb.GetWidth()), ToMM(bb.GetY() + bb.GetHeight()))
    d = {}
    for pd in f.Pads():
        q = pd.GetPosition(); xy = (ToMM(q.x), ToMM(q.y)); fixed_allpads.append(xy)
        nm = pd.GetNetname()
        if not nm or nm == "GND": continue
        d.setdefault(nm, []).append(xy)
    fixed_pads[r] = d
# ---- GPIO swap set (digital-only functions on the RP2040-Zero; I2C pins and ADC pins stay)
# マイコンのピンは、同じ働きができるピン同士で入れ替えてよい（KiCad-MCP ルール 04-6、2026-10-18）
#   ADC の信号は ADC に使えるパッド（U2 の 4〜7 = GP29〜26）の中だけ。デジタルの信号はどのパッドでもよい。
SWAP_NETS = ["DRV1", "DRV2", "SA", "SB", "SC", "SD", "SE", "SF", "SG", "SWN", "SW2N", "FAST_RESTORE",
             "ADC0_OUTA", "ADC1_PLF", "ADC3_SENS"]
ADC_NETS = {"ADC0_OUTA", "ADC1_PLF", "ADC3_SENS"}
ADC_PADS = {"4", "5", "6", "7"}
u2pad = {}                                           # net -> pad number on U2 (current)
for pd in fps["U2"].Pads():
    if pd.GetNetname() in SWAP_NETS: u2pad[pd.GetNetname()] = str(pd.GetNumber())
u2xy = {str(pd.GetNumber()): (ToMM(pd.GetPosition().x), ToMM(pd.GetPosition().y)) for pd in fps["U2"].Pads()}
net_names = [n for n in nets if n != "GND" and len(set(r for r, _ in nets[n])) >= 2]
net_refs = {n: sorted(set(r for r, _ in nets[n])) for n in net_names}
part_nets = collections.defaultdict(list)
for n in net_names:
    for r in net_refs[n]:
        if r in MOV: part_nets[r].append(n)
nweight = {n: (0.5 if n in POWER_NETS else 1.0) for n in net_names}
pos = {}; rotn = {}
def rect_of(r):
    (ox, oy, w, h) = geo[r][rotn[r]][0]
    x, y = pos[r]; return (x + ox, y + oy, x + ox + w, y + oy + h)
def net_pts(n):
    xs = []; ys = []
    for r in net_refs[n]:
        if r in fixed_pads:
            for (x, y) in fixed_pads[r].get(n, []): xs.append(x); ys.append(y)
        else:
            for (dx, dy) in geo[r][rotn[r]][1].get(n, []): xs.append(pos[r][0] + dx); ys.append(pos[r][1] + dy)
    return xs, ys
def net_bbox(n):
    xs, ys = net_pts(n); return (min(xs), min(ys), max(xs), max(ys))
def net_cost(n):
    b = net_bbox(n); return nweight[n] * ((b[2] - b[0]) + (b[3] - b[1]))
# ---- congestion map (RUDY): wire demand per cell vs. capacity
CS = 2.0
CNX, CNY = int(math.ceil(W / CS)), int(math.ceil(H / CS))
CAPC = CS * (CS / 0.75) * float(os.environ.get("CAPF", "1.0"))                        # mm of wire a 2x2 mm cell can take (F.Cu + part of B.Cu)
PADD = 1.6                                           # a pad blocks this much wire length in its cell
D = np.zeros((CNY, CNX))
def cidx(x, y): return min(CNY - 1, max(0, int(y / CS))), min(CNX - 1, max(0, int(x / CS)))
def rudy_add(b, s):
    x0, y0, x1, y1 = b
    w = max(x1 - x0, CS); h = max(y1 - y0, CS)
    i0, j0 = cidx(x0, y0); i1, j1 = cidx(x1, y1)
    D[i0:i1 + 1, j0:j1 + 1] += s * (w + h) * (CS * CS) / (w * h)
    return (i0, j0, i1, j1)
def pads_add(r, s):
    cells = []
    for (dx, dy) in geo[r][rotn[r]][2]:
        i, j = cidx(pos[r][0] + dx, pos[r][1] + dy); D[i, j] += s * PADD; cells.append((i, j))
    return cells
for (x, y) in fixed_allpads:
    i, j = cidx(x, y); D[i, j] += PADD
def cong_pen(sub): return float(np.sum(np.maximum(sub - CAPC, 0.0) ** 2))
M2 = MARGIN
def ov_pair(a, b):
    dx = min(a[2], b[2]) - max(a[0], b[0]) + M2
    dy = min(a[3], b[3]) - max(a[1], b[1]) + M2
    return dx * dy * 6.0 if (dx > 0 and dy > 0) else 0.0
def ov_part(r):
    a = rect_of(r); e = 0.0
    for q in FIXED: e += ov_pair(a, fixed_rect[q])
    for q in MOV:
        if q != r: e += ov_pair(a, rect_of(q))
    if a[0] < 0.5 or a[1] < 0.5 or a[2] > W - 0.5 or a[3] > H - 0.5:
        e += 400.0 + 200 * (max(0.5 - a[0], 0) + max(0.5 - a[1], 0) + max(a[2] - W + 0.5, 0) + max(a[3] - H + 0.5, 0))   # Rev.F: 基板の端は強く禁止
    dx = min(a[2], RP[2]) - max(a[0], RP[0]); dy = min(a[3], RP[3]) - max(a[1], RP[1])
    if dx > 0 and dy > 0: e += dx * dy * 6.0
    lo, hi = region_of(r)
    e += 20.0 * (max(0.0, lo - a[0]) + max(0.0, a[2] - hi))
    return e
def local_energy(rs, nets_):
    return sum(ov_part(r) for r in rs) + sum(net_cost(n) for n in nets_)
# ---- initial positions: random inside the part's region
random.seed(int(os.environ.get('SEED', '7')))
for r in MOV:
    rotn[r] = random.choice(ROT4)
    lo, hi = region_of(r)
    pos[r] = (random.uniform(max(lo, 3), min(hi, W) - 3), random.uniform(3, H - 3))
for n in net_names: rudy_add(net_bbox(n), +1)
for r in MOV: pads_add(r, +1)
def total_ov(): return sum(ov_part(r) for r in MOV)
N = int(os.environ.get('NIT', '700000')); T0, T1 = 6.0, 0.02
swap_pins = sorted(u2pad.values(), key=int)
for it in range(N):
    T = T0 * (T1 / T0) ** (it / N)
    mv = random.random()
    if PINSWAP and mv < 0.06:
        n1, n2 = random.sample(SWAP_NETS, 2)
        if (n1 in ADC_NETS and u2pad[n2] not in ADC_PADS) or (n2 in ADC_NETS and u2pad[n1] not in ADC_PADS):
            continue                                   # ADC の信号は ADC のピンにしか移せない
        rs = []; nets_ = [n1, n2]
        def apply_fn():
            p1, p2 = u2pad[n1], u2pad[n2]; u2pad[n1], u2pad[n2] = p2, p1
            fixed_pads["U2"][n1] = [u2xy[u2pad[n1]]]; fixed_pads["U2"][n2] = [u2xy[u2pad[n2]]]
        undo_fn = apply_fn
    elif mv < 0.20:
        r = random.choice(MOV); q = random.choice(MOV)
        if q == r: continue
        rs = [r, q]; nets_ = sorted(set(part_nets[r]) | set(part_nets[q]))
        def apply_fn():
            pos[r], pos[q] = pos[q], pos[r]
        undo_fn = apply_fn
    else:
        r = random.choice(MOV); rs = [r]; nets_ = part_nets[r]
        oldst = (pos[r], rotn[r])
        if mv < 0.38:
            nr = random.choice([x for x in ROT4 if x != rotn[r]]); np_ = pos[r]
        else:
            s = max(0.5, 8 * (1 - it / N)); nr = rotn[r]
            np_ = (round((pos[r][0] + random.gauss(0, s)) * 4) / 4, round((pos[r][1] + random.gauss(0, s)) * 4) / 4)
        def apply_fn(np_=np_, nr=nr):
            pos[r] = np_; rotn[r] = nr
        def undo_fn(oldst=oldst):
            pos[r], rotn[r] = oldst
    # --- evaluate
    old_boxes = [net_bbox(n) for n in nets_]
    e0 = local_energy(rs, nets_)
    old_pc = [c for r_ in rs for c in [cidx(pos[r_][0] + dx, pos[r_][1] + dy) for (dx, dy) in geo[r_][rotn[r_]][2]]]
    apply_fn()
    new_boxes = [net_bbox(n) for n in nets_]
    new_pc = [c for r_ in rs for c in [cidx(pos[r_][0] + dx, pos[r_][1] + dy) for (dx, dy) in geo[r_][rotn[r_]][2]]]
    e1 = local_energy(rs, nets_)
    cells = [cidx(b[0], b[1]) + cidx(b[2], b[3]) for b in old_boxes + new_boxes] + [c + c for c in old_pc + new_pc]
    if cells:
        ws = (slice(min(c[0] for c in cells), max(c[2] for c in cells) + 1), slice(min(c[1] for c in cells), max(c[3] for c in cells) + 1))
        pb = cong_pen(D[ws])
        for b in old_boxes: rudy_add(b, -1)
        for b in new_boxes: rudy_add(b, +1)
        for (i, j) in old_pc: D[i, j] -= PADD
        for (i, j) in new_pc: D[i, j] += PADD
        pa = cong_pen(D[ws])
    else:
        pb = pa = 0.0
    d = (e1 - e0) + CONG * (pa - pb)
    if d > 0 and random.random() >= math.exp(-d / T):
        if cells:
            for b in new_boxes: rudy_add(b, -1)
            for b in old_boxes: rudy_add(b, +1)
            for (i, j) in new_pc: D[i, j] -= PADD
            for (i, j) in old_pc: D[i, j] += PADD
        undo_fn()
    if it % 50000 == 0:
        print("anneal", it, "T=%.2f" % T, "ov=%.1f" % total_ov(), "wl=%.0f" % sum(net_cost(n) for n in net_names),
              "cong=%.1f" % cong_pen(D), "t=%.0f" % __import__("time").time(), flush=True)
# ---- repair remaining overlaps by exhaustive search for the offending parts
def full_rebuild():
    D[:] = 0
    for (x, y) in fixed_allpads:
        i, j = cidx(x, y); D[i, j] += PADD
    for n in net_names: rudy_add(net_bbox(n), +1)
    for r in MOV: pads_add(r, +1)
for rnd in range(3):
    bad = [r for r in MOV if ov_part(r) > 0.01]
    if not bad: break
    for r in bad:
        best = None
        for rot in ROT4:
            rotn[r] = rot
            yy = 0.75
            while yy < H:
                xx = 0.75
                while xx < W:
                    pos[r] = (xx, yy); e = local_energy([r], part_nets[r])
                    if best is None or e < best[0]: best = (e, xx, yy, rot)
                    xx += 0.5
                yy += 0.5
        pos[r] = (best[1], best[2]); rotn[r] = best[3]
        print("repair", r, "->", pos[r], rotn[r], "E=%.1f" % best[0], flush=True)
    full_rebuild()
ovf = sum(ov_part(r) for r in MOV)
hard = [r for r in MOV if ov_part(r) > 0.01]
print("final overlap penalty", round(ovf, 2), "wl", round(sum(net_cost(n) for n in net_names)), "cong", round(cong_pen(D), 1),
      "maxdemand/cap %.2f" % (D.max() / CAPC), flush=True)
if hard: print("WARNING: placement has overlaps", hard, flush=True)
for r in MOV:
    f = fps[r]; f.SetOrientationDegrees(rotn[r]); f.SetPosition(pcbnew.VECTOR2I(MM(pos[r][0]), MM(pos[r][1])))
# ---- apply GPIO re-assignment to the board pads
if PINSWAP:
    for nm, pn in u2pad.items():
        fps["U2"].FindPadByNumber(pn).SetNet(netinfo[nm])
    json.dump(u2pad, open(OUT + ".pinmap.json", "w"), indent=1)
    print("U2 pin map", u2pad, flush=True)

