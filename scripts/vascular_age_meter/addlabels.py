import re, uuid, sys
path='vascular_age_meter.kicad_sch'
t=open(path,encoding='utf-8').read()

def parse(s):
    i=0; n=len(s)
    def rd():
        nonlocal i
        while s[i] in ' \t\r\n': i+=1
        if s[i]=='(':
            i+=1; out=[]
            while True:
                while s[i] in ' \t\r\n': i+=1
                if s[i]==')': i+=1; return out
                out.append(rd())
        if s[i]=='"':
            j=i+1
            while s[j]!='"':
                if s[j]==chr(92): j+=1
                j+=1
            v=s[i+1:j]; i=j+1; return ('S',v)
        j=i
        while s[j] not in ' \t\r\n()': j+=1
        v=s[i:j]; i=j; return v
    return rd()
tree=parse(t)
def find(node,name):
    return [c for c in node if isinstance(c,list) and c and c[0]==name]
lib=find(tree,'lib_symbols')[0]
def libpins(libid):
    for sym in find(lib,'symbol'):
        if isinstance(sym[1],tuple) and sym[1][1]==libid:
            pins=[]
            def walk(nd):
                for c in nd:
                    if isinstance(c,list):
                        if c and c[0]=='pin':
                            at=find(c,'at')[0]; num=find(c,'number')[0][1][1]
                            pins.append((num,float(at[1]),float(at[2])))
                        else: walk(c)
            walk(sym); return pins
    raise SystemExit('lib symbol not found '+libid)
inst={}
for sym in find(tree,'symbol'):
    lid=find(sym,'lib_id')
    if not lid: continue
    at=find(sym,'at')[0]
    ref=None; unit=1
    for p in find(sym,'property'):
        if p[1][1]=='Reference': ref=p[2][1]
    u=find(sym,'unit')
    if u: unit=int(u[0][1])
    inst.setdefault(ref,[]).append((lid[0][1][1],float(at[1]),float(at[2]),float(at[3]),unit))
def pinpos(ref,pin):
    libid,x,y,rot,unit=inst[ref][0]
    pins=[p for p in libpins(libid) if p[0]==str(pin)]
    _,px,py=pins[0]
    assert rot in (0.0,), (ref,rot)
    return round(x+px,2), round(y-py,2)
labels=[]; ncs=[]
def lab(ref,pin,net):
    x,y=pinpos(ref,pin); labels.append((net,x,y))
def nc(ref,pin):
    x,y=pinpos(ref,pin); ncs.append((x,y))
lab('R22','2','BASE2')
for q,d,b in (('Q1','DIG1','BASE1'),('Q2','DIG2','BASE2')):
    lab(q,'1','GND'); lab(q,'2',d); lab(q,'3',b)
lab('SW2','1','SW2N'); lab('SW2','2','GND')
J5={1:'SEG_E',2:'SEG_D',3:'SEG_C',5:'SEG_E',6:'SEG_D',7:'SEG_G',8:'SEG_C',10:'SEG_B',11:'SEG_A',12:'SEG_F',13:'DIG2',14:'DIG1',15:'SEG_B',16:'SEG_A',17:'SEG_G',18:'SEG_F'}
for k,v in J5.items(): lab('J5',str(k),v)
nc('J5','4'); nc('J5','9')
for k,v in {4:'DRV2',5:'DRV1',8:'SG',9:'SF'}.items(): lab('J2',str(k),v)
nc('J2','1')
for k,v in {1:'SA',2:'SB',3:'SC',4:'SD',8:'SW2N',9:'SE'}.items(): lab('J3',str(k),v)
out=''
for net,x,y in labels:
    out+='\t(label "%s"\n\t\t(at %.2f %.2f 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)\n'%(net,x,y,uuid.uuid4())
for x,y in ncs:
    out+='\t(no_connect\n\t\t(at %.2f %.2f)\n\t\t(uuid "%s")\n\t)\n'%(x,y,uuid.uuid4())
idx=t.rstrip().rfind(')')
t=t[:idx]+out+')\n'
open(path,'w',encoding='utf-8').write(t)
print('added',len(labels),'labels',len(ncs),'no-connects')
