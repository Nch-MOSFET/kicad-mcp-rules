"""Fix-up router: python fixup2.py <dir>  (reads <dir>/out.kicad_pcb and the FAILED list in <dir>/log.txt,
routes the missing connections on top of the existing copper, writes <dir>/fixed.kicad_pcb)"""
import sys, os, re, ast, math
D_ = sys.argv[1]
os.environ['FROMBOARD'] = D_ + '/out.kicad_pcb'
src = open('C:/Users/<user>/Documents/KiCad_work/build_board.py', encoding='utf-8').read()
src = src[:src.index("own0 = own.copy()")]
sys.argv = ['x', 'vascular_age_meter/netlist.xml', D_ + '/tmp.kicad_pcb', 'C:/Users/<user>/Documents/KiCad_work/vascular_age_meter']
exec(src)
failed = ast.literal_eval(open(D_ + '/log.txt', encoding='utf-8').read().split('FAILED:')[-1].strip().split('\n')[0])
old = pcbnew.LoadBoard(D_ + '/out.kicad_pcb')
for t in old.GetTracks():
    net = netcode.get(t.GetNetname(), 0)
    if t.Type() == pcbnew.PCB_VIA_T:
        x, y = int(round(ToMM(t.GetPosition().x) / G)), int(round(ToMM(t.GetPosition().y) / G))
        for l in range(2): mark_disk(l, x, y, int(math.ceil(VIA_D / 2 / G)), net)
    else:
        l = 0 if t.GetLayer() == pcbnew.F_Cu else 1
        x0, y0, x1, y1 = ToMM(t.GetStart().x), ToMM(t.GetStart().y), ToMM(t.GetEnd().x), ToMM(t.GetEnd().y)
        n = int(max(abs(x1 - x0), abs(y1 - y0)) / (G / 2)) + 1; rc = int(math.ceil(ToMM(t.GetWidth()) / 2 / G))
        for i in range(n + 1): mark_disk(l, int(round((x0 + (x1 - x0) * i / n) / G)), int(round((y0 + (y1 - y0) * i / n) / G)), rc, net)
added = 0; still = []
for nm, pa, pb in failed:
    net = netcode[nm]; ref, pin = pb.split('.')
    tpad = [p for p in pads_by_net[nm] if p[0] == ref and p[1] == pin][0]
    tg = pad_cells(tpad); cx = (tpad[2] + tpad[4]) / 2 / G; cy = (tpad[3] + tpad[5]) / 2 / G
    tree = set((l, int(x), int(y)) for l in range(2) for y, x in zip(*np.nonzero(own[l] == net)))
    tree = {c for c in tree if abs(c[1] - cx) > 6 or abs(c[2] - cy) > 6}
    path = None
    for w in ((1.0, 0.7, 0.5) if nm in POWER_NETS else (0.5, 0.3, 0.2)):
        for margin in (0.34, 0.23):
            CAP = 2500000 if (w <= 0.3 and margin == 0.23) else 400000
            bt, vb = blocked(net, w, margin)
            for c in tg:
                for l in range(2): bt[l][c[1]][c[0]] = False
            path = astar(list(tree), tg, bt, vb)
            print(nm, pb, w, margin, bool(path), flush=True)
            if path: used = w; break
        if path: break
    if not path: still.append((nm, pa, pb)); continue
    commit(net, used, path)
    k = 0
    while k < len(path) - 1:
        l, x, y, dr = path[k]
        if path[k + 1][0] != l:
            v = pcbnew.PCB_VIA(old); v.SetPosition(pcbnew.VECTOR2I(MM(x * G), MM(y * G))); v.SetWidth(MM(VIA_D)); v.SetDrill(MM(VIA_DRILL))
            v.SetNetCode(old.GetNetcodeFromNetname(nm)); v.SetViaType(pcbnew.VIATYPE_THROUGH); old.Add(v); k += 1; continue
        j = k + 1; d0 = path[j][3]
        while j + 1 < len(path) and path[j + 1][0] == l and path[j + 1][3] == d0: j += 1
        if (x, y) != (path[j][1], path[j][2]):
            t = pcbnew.PCB_TRACK(old); t.SetStart(pcbnew.VECTOR2I(MM(x * G), MM(y * G))); t.SetEnd(pcbnew.VECTOR2I(MM(path[j][1] * G), MM(path[j][2] * G)))
            t.SetWidth(MM(used)); t.SetLayer(LAYERS[l]); t.SetNetCode(old.GetNetcodeFromNetname(nm)); old.Add(t); added += 1
        k = j
for f in old.GetFootprints():
    for p in f.Pads():
        if p.GetNetname() == 'GND': p.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
pcbnew.ZONE_FILLER(old).Fill(old.Zones())
pcbnew.SaveBoard(D_ + '/fixed.kicad_pcb', old)
print('added segments', added, 'STILL FAILED:', still, flush=True)
