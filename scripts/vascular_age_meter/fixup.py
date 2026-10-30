import sys
src=open('build_board.py',encoding='utf-8').read()
src=src[:src.index("own0 = own.copy()")]
sys.argv=['x','vascular_age_meter/netlist.xml','e_1_1.2/p.kicad_pcb','C:/Users/<user>/Documents/KiCad_work/vascular_age_meter']
exec(src)
old=pcbnew.LoadBoard('e_1_1.2/out.kicad_pcb')
def cell(v): return int(round(ToMM(v)/G))
cnt=0
for t in old.GetTracks():
    net=netcode.get(t.GetNetname(),0)
    if t.Type()==pcbnew.PCB_VIA_T:
        x,y=cell(t.GetPosition().x),cell(t.GetPosition().y)
        for l in range(2): mark_disk(l,x,y,int(math.ceil(VIA_D/2/G)),net)
    else:
        l=0 if t.GetLayer()==pcbnew.F_Cu else 1
        x0,y0,x1,y1=ToMM(t.GetStart().x),ToMM(t.GetStart().y),ToMM(t.GetEnd().x),ToMM(t.GetEnd().y)
        n=int(max(abs(x1-x0),abs(y1-y0))/(G/2))+1
        rc=int(math.ceil(ToMM(t.GetWidth())/2/G))
        for i in range(n+1):
            mark_disk(l,int(round((x0+(x1-x0)*i/n)/G)),int(round((y0+(y1-y0)*i/n)/G)),rc,net)
    cnt+=1
print('loaded',cnt)
segs,vias=[],[]
for nm,tr in [('SD','R17'),('SEG_B','R15')]:
    net=netcode[nm]; pads=pads_by_net[nm]
    tree=set((l,int(x),int(y)) for l in range(2) for y,x in zip(*np.nonzero(own[l]==net)))
    tpad=[p for p in pads if p[0]==tr][0]
    tg=pad_cells(tpad); cx=(tpad[2]+tpad[4])/2/G; cy=(tpad[3]+tpad[5])/2/G; tree={c for c in tree if abs(c[1]-cx)>6 or abs(c[2]-cy)>6}; path=None
    for w in (0.5,0.3,0.2):
        for margin in (0.34,0.23):
            CAP=2500000 if (w==0.2 and margin==0.23) else 400000
            bt,vb=blocked(net,w,margin)
            for c in tg:
                for l in range(2): bt[l][c[1]][c[0]]=False
            path=astar(list(tree),tg,bt,vb)
            print(nm,w,margin,bool(path),flush=True)
            if path: used=w;break
        if path: break
    if path:
        commit(net,used,path)
        k=0
        while k<len(path)-1:
            l,x,y,dr=path[k]
            if path[k+1][0]!=l: vias.append((net,x,y)); k+=1; continue
            j=k+1; d0=path[j][3]
            while j+1<len(path) and path[j+1][0]==l and path[j+1][3]==d0: j+=1
            segs.append((net,used,l,(x,y),(path[j][1],path[j][2]))); k=j
for net,w,l,a,b in segs:
    if a==b: continue
    t=pcbnew.PCB_TRACK(old); t.SetStart(pcbnew.VECTOR2I(MM(a[0]*G),MM(a[1]*G))); t.SetEnd(pcbnew.VECTOR2I(MM(b[0]*G),MM(b[1]*G)))
    t.SetWidth(MM(w)); t.SetLayer(LAYERS[l]); t.SetNetCode(net); old.Add(t)
for net,x,y in vias:
    v=pcbnew.PCB_VIA(old); v.SetPosition(pcbnew.VECTOR2I(MM(x*G),MM(y*G))); v.SetWidth(MM(VIA_D)); v.SetDrill(MM(VIA_DRILL)); v.SetNetCode(net); v.SetViaType(pcbnew.VIATYPE_THROUGH); old.Add(v)
pcbnew.ZONE_FILLER(old).Fill(old.Zones())
pcbnew.SaveBoard('e_1_1.2/fixed.kicad_pcb',old)
print('saved',len(segs),len(vias))
