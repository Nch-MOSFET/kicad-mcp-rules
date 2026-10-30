import re, uuid, math, sys, collections
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()

def parse(s):
    i = 0
    def rd():
        nonlocal i
        while s[i] in ' \t\r\n': i += 1
        if s[i] == '(':
            i += 1; out = []
            while True:
                while s[i] in ' \t\r\n': i += 1
                if s[i] == ')': i += 1; return out
                out.append(rd())
        if s[i] == '"':
            j = i + 1
            while s[j] != '"':
                if s[j] == chr(92): j += 1
                j += 1
            v = s[i + 1:j]; i = j + 1; return ('S', v)
        j = i
        while s[j] not in ' \t\r\n()': j += 1
        v = s[i:j]; i = j; return v
    return rd()
def find(node, name): return [c for c in node if isinstance(c, list) and c and c[0] == name]

def spans(text, start=0):
    """top-level child forms (depth 1) of the root form"""
    out = []; d = 0; instr = False; i = 0; b = None
    while i < len(text):
        c = text[i]
        if instr:
            if c == chr(92): i += 1
            elif c == '"': instr = False
        else:
            if c == '"': instr = True
            elif c == '(':
                d += 1
                if d == 2: b = i
            elif c == ')':
                if d == 2: out.append((b, i + 1))
                d -= 1
        i += 1
    return out
sp = spans(t)
parts = [(a, b, t[a:b]) for a, b in sp]
head_end = parts[0][0]
lib_text = [p for p in parts if p[2].startswith('(lib_symbols')][0]
lib = parse(lib_text[2])
def libpins(libid, unit):
    for sym in find(lib, 'symbol'):
        if isinstance(sym[1], tuple) and sym[1][1] == libid:
            res = []
            for sub in find(sym, 'symbol'):
                m = re.search(r'_(\d+)_(\d+)$', sub[1][1])
                u = int(m.group(1)) if m else 0
                if u not in (0, unit): continue
                for pn in find(sub, 'pin'):
                    at = find(pn, 'at')[0]; num = find(pn, 'number')[0][1][1]
                    res.append((num, float(at[1]), float(at[2]), float(at[3])))
            return res
    raise SystemExit('no lib ' + libid)

def pinsch(libid, unit, x, y, rot):
    out = []; th = math.radians(rot)
    for num, px, py, ang in libpins(libid, unit):
        qx = px * math.cos(th) - py * math.sin(th); qy = px * math.sin(th) + py * math.cos(th)
        out.append((num, round(x + qx, 2), round(y - qy, 2), (ang + rot) % 360))
    return out

# ---- old labels
old_labels = {}
for a, b, s in parts:
    if s.startswith('(label'):
        m = re.match(r'\(label "([^"]+)"\s+\(at ([\-\d.]+) ([\-\d.]+)', s)
        old_labels[(round(float(m.group(2)), 2), round(float(m.group(3)), 2))] = m.group(1)
old_nc = set()
for a, b, s in parts:
    if s.startswith('(no_connect'):
        m = re.match(r'\(no_connect\s+\(at ([\-\d.]+) ([\-\d.]+)', s)
        old_nc.add((round(float(m.group(1)), 2), round(float(m.group(2)), 2)))

LAY = {}
exec(open('C:/Users/<user>/Documents/KiCad_work/layout_map.py', encoding='utf-8').read())   # fills LAY, FRAMES

out = []
placed_pins = []   # (net or None(nc), x, y, angle)
uid = lambda: str(uuid.uuid4())
for a, b, s in parts:
    if s.startswith('(label') or s.startswith('(no_connect') or s.startswith('(rectangle') or s.startswith('(text'):
        continue
    if not re.match(r'\(symbol\s', s):
        out.append((a, s)); continue
    if s.startswith('(lib_symbols'):
        out.append((a, s)); continue
    node = parse(s)
    lid = find(node, 'lib_id')[0][1][1]
    at = find(node, 'at')[0]; ox, oy = float(at[1]), float(at[2])
    unit = int(find(node, 'unit')[0][1]) if find(node, 'unit') else 1
    ref = [p for p in find(node, 'property') if p[1][1] == 'Reference'][0][2][1]
    key = ref + ('#%d' % unit if ref == 'U1' else '')
    nx, ny = LAY[key][:2]; rot = LAY[key][2] if len(LAY[key]) > 2 else 0
    # old pins -> net names
    pins_old = pinsch(lid, unit, ox, oy, 0)
    pin_net = {}
    for num, px, py, ang in pins_old:
        if (px, py) in old_labels: pin_net[num] = old_labels[(px, py)]
        elif (px, py) in old_nc: pin_net[num] = None
    # rewrite instance text
    dx, dy = nx - ox, ny - oy
    def shift(m):
        return '(at %s %s %s)' % (round(float(m.group(1)) + dx, 2), round(float(m.group(2)) + dy, 2), m.group(3))
    s2 = re.sub(r'\(at ([\-\d.]+) ([\-\d.]+) ([\-\d.]+)\)', shift, s)
    # set symbol rotation (first at after lib_id)
    i0 = s2.index('(lib_id')
    mm = re.compile(r'\(at ([\-\d.]+) ([\-\d.]+) ([\-\d.]+)\)').search(s2, i0)
    s2 = s2[:mm.start()] + '(at %s %s %s)' % (nx, ny, rot) + s2[mm.end():]
    pp = pinsch(lid, unit, nx, ny, rot)
    xs = [p[1] for p in pp]; ys = [p[2] for p in pp]
    cx = round((min(xs) + max(xs)) / 2, 2)
    pa = 90 if rot else 0
    def setprop(sx, name, px, py, ang):
        pat = re.compile(r'(\(property "%s" "[^"]*"\s+\(at )[\-\d.]+ [\-\d.]+ [\-\d.]+(\))' % name)
        return pat.sub(lambda m: m.group(1) + '%s %s %s' % (px, py, ang) + m.group(2), sx, count=1)
    s2 = setprop(s2, 'Reference', cx, round(min(ys) - 3.0, 2), pa)
    s2 = setprop(s2, 'Value', cx, round(max(ys) + 3.0, 2), pa)
    out.append((a, s2))
    for num, px, py, ang in pinsch(lid, unit, nx, ny, rot):
        if num in pin_net: placed_pins.append((pin_net[num], px, py, ang))

res = t[:head_end]
body = ''.join(chr(9) + s + chr(10) for a, s in out).replace('(paper "A4")', '(paper "A3")')
extra = ''
for net, x, y, ang in placed_pins:
    if net is None:
        extra += '\t(no_connect\n\t\t(at %.2f %.2f)\n\t\t(uuid "%s")\n\t)\n' % (x, y, uid())
    else:
        la = (ang + 180) % 360
        just = 'left bottom' if la in (0, 90) else 'right bottom'
        extra += '\t(label "%s"\n\t\t(at %.2f %.2f %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (net, x, y, la, just, uid())
for (x0, y0, x1, y1, title) in FRAMES:
    extra += '\t(rectangle\n\t\t(start %.2f %.2f)\n\t\t(end %.2f %.2f)\n\t\t(stroke\n\t\t\t(width 0.25)\n\t\t\t(type dash)\n\t\t)\n\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (x0, y0, x1, y1, uid())
    extra += '\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %.2f %.2f 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 2.5 2.5)\n\t\t\t\t(bold yes)\n\t\t\t)\n\t\t\t(justify left top)\n\t\t)\n\t\t(uuid "%s")\n\t)\n' % (title, x0 + 2, y0 + 2, uid())
open(dst, 'w', encoding='utf-8').write(res + '\n' + body + extra + ')\n')
print('labels', sum(1 for p in placed_pins if p[0]), 'nc', sum(1 for p in placed_pins if p[0] is None))
