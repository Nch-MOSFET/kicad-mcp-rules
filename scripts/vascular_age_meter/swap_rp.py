import re, uuid, sys, math
SCH = 'vascular_age_meter/vascular_age_meter.kicad_sch'
t = open(SCH, encoding='utf-8').read()
src = open('relayout.py', encoding='utf-8').read()
exec(src[src.index('def parse(s):'):src.index('sp = spans(t)')])   # parse, find, spans
lib_sym = open('vascular_age_meter/lib/rp2040_zero/rp2040_zero.kicad_sym', encoding='utf-8').read()
a = lib_sym.index('\t(symbol "rp2040_zero"'); d = 0; i = a; instr = False
while True:
    c = lib_sym[i]
    if instr:
        if c == '"': instr = False
    elif c == '"': instr = True
    elif c == '(': d += 1
    elif c == ')':
        d -= 1
        if d == 0: break
    i += 1
symtxt = lib_sym[a:i + 1].replace('(symbol "rp2040_zero"', '(symbol "rp2040_zero:rp2040_zero"', 1)
symtxt = '\n'.join('\t' + l for l in symtxt.split('\n'))     # one more indent level

sp = spans(t); parts = [(a, b, t[a:b]) for a, b in sp]
U = lambda: str(uuid.uuid4())
labels = {}; ncs = set()
for a_, b_, s in parts:
    if s.startswith('(label'):
        m = re.match(r'\(label "([^"]+)"\s+\(at ([\-\d.]+) ([\-\d.]+)', s); labels[(round(float(m.group(2)), 2), round(float(m.group(3)), 2))] = (m.group(1), a_)
    if s.startswith('(no_connect'):
        m = re.match(r'\(no_connect\s+\(at ([\-\d.]+) ([\-\d.]+)', s); ncs.add(((round(float(m.group(1)), 2), round(float(m.group(2)), 2)), a_))
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
drop = set(); jnet = {}; tmpl = None
for a_, b_, s in parts:
    if not re.match(r'\(symbol\s', s): continue
    node = parse(s)
    ref = [p for p in find(node, 'property') if p[1][1] == 'Reference'][0][2][1]
    if ref not in ('J2', 'J3'): continue
    if ref == 'J2': tmpl = s
    drop.add(a_)
    at = find(node, 'at')[0]; x, y = float(at[1]), float(at[2])
    for num, px, py in libpins(find(node, 'lib_id')[0][1][1]):
        k = (round(x + px, 2), round(y - py, 2))
        if k in labels: jnet[(ref, num)] = labels[k][0]; drop.add(labels[k][1])
        for (pk, pa) in ncs:
            if pk == k: jnet[(ref, num)] = None; drop.add(pa)
print('J2/J3 pin nets:', jnet)
# U2 pin -> net
unet = {}
for k in range(1, 10):
    unet[str(k)] = jnet.get(('J2', str(k)))
    unet[str(24 - k)] = jnet.get(('J3', str(k)))
for k in range(10, 15): unet[str(k)] = None
X, Y = 335.28, 165.1
inst = tmpl
inst = re.sub(r'\(lib_id "[^"]+"\)', '(lib_id "rp2040_zero:rp2040_zero")', inst, 1)
inst = re.sub(r'(\(lib_id "rp2040_zero:rp2040_zero"\)\s+\(at )[\-\d.]+ [\-\d.]+ [\-\d.]+', r'\g<1>%s %s 0' % (X, Y), inst, 1)
inst = re.sub(r'\(uuid "[^"]+"\)', '(uuid "%s")' % U(), inst, 1)
def setprop(sx, name, val, px, py, hide=False):
    pat = re.compile(r'\(property "%s" "[^"]*"\s+\(at [\-\d.]+ [\-\d.]+ [\-\d.]+\)' % name)
    return pat.sub('(property "%s" "%s"\n\t\t\t(at %s %s 0)' % (name, val, px, py), sx, 1)
inst = setprop(inst, 'Reference', 'U2', X + 16.51, Y - 5.08)
inst = setprop(inst, 'Value', 'RP2040-Zero', X + 16.51, Y + 33.02)
inst = setprop(inst, 'Footprint', 'rp2040_zero:rp2040zero', X, Y + 36)
inst = re.sub(r'\(reference "J2"\)', '(reference "U2")', inst)
# replace pin uuid list
inst = re.sub(r'\s*\(pin "\d+"\s+\(uuid "[^"]+"\)\s*\)', '', inst)
pins = ''.join('\n\t\t(pin "%d"\n\t\t\t(uuid "%s")\n\t\t)' % (k, U()) for k in range(1, 24))
j = inst.index('(instances'); j = inst.rfind('\n', 0, j)
inst = inst[:j] + pins + inst[j:]
# labels for U2 pins
out = ''
for num, px, py in [(str(k), 0.0, -2.54 * (k - 1)) for k in range(1, 13)] + [(str(k), 33.02, -2.54 * (k - 13)) for k in range(13, 24)]:
    x, y = round(X + px, 2), round(Y - py, 2); net = unet.get(num)
    if net is None:
        out += '\t(no_connect\n\t\t(at %.2f %.2f)\n\t\t(uuid "%s")\n\t)\n' % (x, y, U())
    else:
        ang, just = (180, 'right bottom') if px == 0 else (0, 'left bottom')
        out += '\t(label "%s"\n\t\t(at %.2f %.2f %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (net, x, y, ang, just, U())
# assemble
res = t[:parts[0][0]]
for a_, b_, s in parts:
    if a_ in drop: continue
    if s.startswith('(lib_symbols'):
        s = s.rstrip()[:-1].rstrip() + '\n' + symtxt + '\n\t)'
    res += '\t' + s + '\n' if not res.endswith('\t') else s + '\n'
res = res.rstrip()
# simpler: rebuild body
body = ''.join('\t' + (s if not s.startswith('(lib_symbols') else s.rstrip()[:-1].rstrip() + '\n' + symtxt + '\n\t)') + '\n' for a_, b_, s in parts if a_ not in drop)
final = t[:parts[0][0]].rstrip() + '\n' + body + '\t' + inst + '\n' + out + ')\n'
open(SCH, 'w', encoding='utf-8').write(final)
print('U2 nets', unet)
