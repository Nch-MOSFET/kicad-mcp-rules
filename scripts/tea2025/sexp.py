# -*- coding: utf-8 -*-
"""Minimal S-expression helpers for KiCad files (symbol extraction, pin listing)."""
import re

KICAD_SYM = "C:/Program Files/KiCad/10.0/share/kicad/symbols/"


def block_end(t, i):
    """index just after the ')' that closes the '(' at t[i] (strings are skipped)."""
    depth, j, n = 0, i, len(t)
    while j < n:
        c = t[j]
        if c == '"':
            j += 1
            while t[j] != '"':
                if t[j] == '\\': j += 1
                j += 1
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0: return j + 1
        j += 1
    raise ValueError("unbalanced")


def top_symbols(text):
    """{name: block_text} for the symbols directly under (kicad_symbol_lib ...)."""
    out = {}
    for m in re.finditer(r'\n\t\(symbol "([^"]+)"', text):
        s = m.start() + 1
        out[m.group(1)] = text[s:block_end(text, s)]
    return out


def load_symbol(lib, name, libfile=None):
    """symbol block, with 'extends' resolved by returning the parent renamed (KiCad needs flat symbols in sch)."""
    path = libfile or (KICAD_SYM + lib + ".kicad_sym")
    syms = top_symbols(open(path, encoding="utf-8").read())
    blk = syms[name]
    m = re.search(r'\(extends "([^"]+)"\)', blk)
    if m:
        raise ValueError("extends not supported: %s -> %s" % (name, m.group(1)))
    return blk


def pins(blk):
    """[(number, name, x, y, angle, unit)] in symbol-local coordinates (Y up)."""
    res = []
    for um in re.finditer(r'\(symbol "[^"]+_(\d+)_(\d+)"', blk):
        unit = int(um.group(1))
        s = um.start(); sub = blk[s:block_end(blk, s)]
        for pm in re.finditer(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) ?([-\d.]*)\)', sub):
            ps = pm.start(); pb = sub[ps:block_end(sub, ps)]
            nm = re.search(r'\(name "([^"]*)"', pb).group(1)
            no = re.search(r'\(number "([^"]*)"', pb).group(1)
            res.append((no, nm, float(pm.group(1)), float(pm.group(2)), float(pm.group(3) or 0), unit))
    return res


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for spec in sys.argv[1:]:
        lib, nm = spec.split(":")
        try:
            b = load_symbol(lib, nm)
            print(spec, pins(b))
        except Exception as e:
            print(spec, "ERR", e)
