# -*- coding: utf-8 -*-
"""compare two KiCad XML netlists: net name -> set of (ref, pin); 'unconnected-' nets ignored"""
import sys, xml.etree.ElementTree as ET
def load(p):
    r = ET.parse(p).getroot()
    return {n.get("name"): frozenset((d.get("ref"), d.get("pin")) for d in n.findall("node"))
            for n in r.find("nets") if not n.get("name").startswith("unconnected-")}
a, b = load(sys.argv[1]), load(sys.argv[2])
diff = [(k, a.get(k), b.get(k)) for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]
print("nets", len(a), len(b), "diff", len(diff))
for d in diff: print(" ", d)
