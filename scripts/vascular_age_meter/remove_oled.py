"""Remove the OLED (J4) from the schematic: delete the symbol and the labels on its pins,
and put no-connect flags on the RP2040-Zero pins that only went to the OLED (SDA / SCL)."""
import re, uuid, math
SCH = 'C:/Users/<user>/Documents/KiCad_work/vascular_age_meter/vascular_age_meter.kicad_sch'
t = open(SCH, encoding='utf-8').read()
src = open('C:/Users/<user>/Documents/KiCad_work/relayout.py', encoding='utf-8').read()
exec(src[src.index('def parse(s):'):src.index('sp = spans(t)')])     # parse, find, spans
parts = [(a, b, t[a:b]) for a, b in spans(t)]
lib = parse([p for p in parts if p[2].startswith('(lib_symbols')][0][2])
def libpins(libid, unit):
    for sym in find(lib, 'symbol'):
        if isinstance(sym[1], tuple) and sym[1][1] == libid:
            res = []
            for sub in find(sym, 'symbol'):
                m = re.search(r'_(\d+)_(\d+)$', sub[1][1]); u = int(m.group(1)) if m else 0
                if u not in (0, unit): continue
                for pn in find(sub, 'pin'):
                    at = find(pn, 'at')[0]; res.append((find(pn, 'number')[0][1][1], float(at[1]), float(at[2]), float(at[3])))
            return res
def pinxy(node):
    lid = find(node, 'lib_id')[0][1][1]; at = find(node, 'at')[0]; x, y, rot = float(at[1]), float(at[2]), float(at[3])
    unit = int(find(node, 'unit')[0][1]) if find(node, 'unit') else 1
    th = math.radians(rot); out = {}
    for num, px, py, ang in libpins(lid, unit):
        qx = px * math.cos(th) - py * math.sin(th); qy = px * math.sin(th) + py * math.cos(th)
        out[num] = (round(x + qx, 2), round(y - qy, 2))
    return out
labels = {}
for a, b, s in parts:
    if s.startswith('(label'):
        m = re.match(r'\(label "([^"]+)"\s+\(at ([\-\d.]+) ([\-\d.]+)', s)
        labels[(round(float(m.group(2)), 2), round(float(m.group(3)), 2))] = (m.group(1), a)
drop = set(); nc_add = []
for a, b, s in parts:
    if not re.match(r'\(symbol\s', s): continue
    node = parse(s); ref = [p for p in find(node, 'property') if p[1][1] == 'Reference'][0][2][1]
    if ref == 'J4':
        drop.add(a)
        for num, xy in pinxy(node).items():
            if xy in labels: drop.add(labels[xy][1])
    if ref == 'U2':
        for num, xy in pinxy(node).items():
            if xy in labels and labels[xy][0] in ('SDA', 'SCL'):
                drop.add(labels[xy][1]); nc_add.append(xy)
print('removed', len(drop), 'items; no-connects added', len(nc_add))
body = ''.join('\t' + s + '\n' for a, b, s in parts if a not in drop)
body = body.replace("'7. スイッチ / OLED'", "'7. スイッチ'").replace('"7. スイッチ / OLED"', '"7. スイッチ"')
extra = ''.join('\t(no_connect\n\t\t(at %.2f %.2f)\n\t\t(uuid "%s")\n\t)\n' % (x, y, uuid.uuid4()) for x, y in nc_add)
open(SCH, 'w', encoding='utf-8').write(t[:parts[0][0]].rstrip() + '\n' + body + extra + ')\n')
