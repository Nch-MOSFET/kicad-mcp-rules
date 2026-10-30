"""Schematic update for the footprint review (2026-10-10):
 - J1: generic 2x2 connector -> easyeda RPR-220 symbol (pins 1=Anode 2=Cathode 3=Emitter 4=Collector),
   footprint easyeda:LED-TH_4P_RPR-220. Nets follow the datasheet: A=LEDA, K=GND, E=SENS, C=VCC_A.
 - TP5: new GND test land (top-side 8x3 mm pad at the board corner for an alligator clip)."""
import re, uuid, math
SCH = 'C:/Users/<user>/Documents/KiCad_work/vascular_age_meter/vascular_age_meter.kicad_sch'
SYMLIB = 'C:/Users/<user>/Documents/KiCad_work/vascular_age_meter/lib/easyeda/easyeda.kicad_sym'
t = open(SCH, encoding='utf-8').read()
src = open('C:/Users/<user>/Documents/KiCad_work/relayout.py', encoding='utf-8').read()
exec(src[src.index('def parse(s):'):src.index('sp = spans(t)')])     # parse, find, spans
U = lambda: str(uuid.uuid4())

def lib_block(text, name):
    a = text.index('\t(symbol "%s"' % name); d = 0; i = a; instr = False
    while True:
        c = text[i]
        if instr:
            if c == '"': instr = False
        elif c == '"': instr = True
        elif c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: return text[a:i + 1]
        i += 1
symlib = open(SYMLIB, encoding='utf-8').read()
rpr = lib_block(symlib, 'RPR-220').replace('(symbol "RPR-220"', '(symbol "easyeda:RPR-220"', 1)
rpr = '\n'.join('\t' + l for l in rpr.split('\n'))
lib_pins = {}
for m in re.finditer(r'\(pin \w+ \w+\s+\(at ([\-\d.]+) ([\-\d.]+) ([\-\d.]+)\)[\s\S]*?\(number "(\d+)"', rpr):
    lib_pins[m.group(4)] = (float(m.group(1)), float(m.group(2)), float(m.group(3)))

parts = [(a, b, t[a:b]) for a, b in spans(t)]
labels = {}
for a, b, s in parts:
    if s.startswith('(label'):
        m = re.match(r'\(label "([^"]+)"\s+\(at ([\-\d.]+) ([\-\d.]+)', s)
        labels[(round(float(m.group(2)), 2), round(float(m.group(3)), 2))] = (m.group(1), a)
lib = parse([p for p in parts if p[2].startswith('(lib_symbols')][0][2])
def libpins(libid):
    for sym in find(lib, 'symbol'):
        if isinstance(sym[1], tuple) and sym[1][1] == libid:
            out = []
            def walk(nd):
                for c in nd:
                    if isinstance(c, list):
                        if c and c[0] == 'pin':
                            at = find(c, 'at')[0]; out.append((find(c, 'number')[0][1][1], float(at[1]), float(at[2])))
                        else: walk(c)
            walk(sym); return out
drop = set(); j1 = None; tp_tmpl = None
for a, b, s in parts:
    if not re.match(r'\(symbol\s', s): continue
    node = parse(s); ref = [p for p in find(node, 'property') if p[1][1] == 'Reference'][0][2][1]
    if ref == 'TP3': tp_tmpl = s
    if ref != 'J1': continue
    j1 = (s, node); drop.add(a)
    at = find(node, 'at')[0]; x, y = float(at[1]), float(at[2])
    for num, px, py in libpins(find(node, 'lib_id')[0][1][1]):
        k = (round(x + px, 2), round(y - py, 2))
        if k in labels: drop.add(labels[k][1])
s_old, node = j1
at = find(node, 'at')[0]; X, Y = float(at[1]), float(at[2])
NET = {'1': 'LEDA', '2': 'GND', '3': 'SENS', '4': 'VCC_A'}
inst = s_old
inst = re.sub(r'\(lib_id "[^"]+"\)', '(lib_id "easyeda:RPR-220")', inst, count=1)
inst = re.sub(r'\(uuid "[^"]+"\)', '(uuid "%s")' % U(), inst, count=1)
def setprop(sx, name, val):
    return re.sub(r'\(property "%s" "[^"]*"' % name, '(property "%s" "%s"' % (name, val), sx, count=1)
inst = setprop(inst, 'Value', 'RPR-220')
inst = setprop(inst, 'Footprint', 'easyeda:LED-TH_4P_RPR-220')
inst = re.sub(r'\s*\(pin "\d+"\s+\(uuid "[^"]+"\)\s*\)', '', inst)
pins = ''.join('\n\t\t(pin "%s"\n\t\t\t(uuid "%s")\n\t\t)' % (k, U()) for k in sorted(lib_pins))
j = inst.index('(instances'); j = inst.rfind('\n', 0, j); inst = inst[:j] + pins + inst[j:]
def label(net, x, y, ang):
    just = 'left bottom' if ang in (0, 90) else 'right bottom'
    return '\t(label "%s"\n\t\t(at %.2f %.2f %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (net, x, y, ang, just, U())
extra = ''
for num, (px, py, pa) in lib_pins.items():
    extra += label(NET[num], round(X + px, 2), round(Y - py, 2), int((pa + 180) % 360))
# TP5 (GND clip land) from the TP3 instance
tp = tp_tmpl
m = re.search(r'\(lib_id "[^"]+"\)\s+\(at ([\-\d.]+) ([\-\d.]+) ([\-\d.]+)\)', tp)
ox, oy = float(m.group(1)), float(m.group(2)); TX, TY = 400.05, 82.55
dx, dy = TX - ox, TY - oy
tp = re.sub(r'\(at ([\-\d.]+) ([\-\d.]+) ([\-\d.]+)\)', lambda mm: '(at %s %s %s)' % (round(float(mm.group(1)) + dx, 2), round(float(mm.group(2)) + dy, 2), mm.group(3)), tp)
tp = re.sub(r'\(uuid "[^"]+"\)', lambda mm: '(uuid "%s")' % U(), tp)
tp = setprop(tp, 'Reference', 'TP5'); tp = setprop(tp, 'Value', 'TP_GND')
tp = setprop(tp, 'Footprint', 'vam_custom:TestPoint_Pad_GND_Clip_8x3')
tp = re.sub(r'\(reference "TP3"\)', '(reference "TP5")', tp)
tpl = [p for p in libpins(re.search(r'\(lib_id "([^"]+)"', tp).group(1))][0]
extra += label('GND', round(TX + tpl[1], 2), round(TY - tpl[2], 2), 90)
body = ''.join('\t' + (s if not s.startswith('(lib_symbols') else s.rstrip()[:-1].rstrip() + '\n' + rpr + '\n\t)') + '\n'
               for a, b, s in parts if a not in drop)
out = t[:parts[0][0]].rstrip() + '\n' + body + '\t' + inst + '\n' + '\t' + tp + '\n' + extra + ')\n'
open(SCH, 'w', encoding='utf-8').write(out)
print('J1 ->', NET, '; TP5 added at', TX, TY)
