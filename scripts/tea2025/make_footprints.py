# -*- coding: utf-8 -*-
"""Generate the custom footprints of the TEA2025 amp kit into lib/TEA2025_amp/TEA2025_amp.pretty.
All coordinates are top (component side) views in mm, KiCad Y down. Sources are written into each descr.
Run with any python, then normalise with: kicad-cli fp upgrade <pretty>
"""
import math, os, uuid

OUT = os.path.join(os.path.dirname(__file__), "..", "lib", "TEA2025_amp", "TEA2025_amp.pretty")
os.makedirs(OUT, exist_ok=True)


def u():
    return str(uuid.uuid4())


def text(kind, value, x, y, layer, hide=False):
    h = "\n\t\t(hide yes)" if hide else ""
    return ('\t(property "%s" "%s"\n\t\t(at %.3f %.3f 0)\n\t\t(layer "%s")%s\n\t\t(uuid "%s")\n'
            '\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n') % (kind, value, x, y, layer, h, u())


def rect(x0, y0, x1, y1, layer, w):
    return ('\t(fp_rect\n\t\t(start %.3f %.3f)\n\t\t(end %.3f %.3f)\n\t\t(stroke\n\t\t\t(width %.3f)\n\t\t\t(type solid)\n\t\t)\n'
            '\t\t(fill no)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)\n') % (x0, y0, x1, y1, w, layer, u())


def line(x0, y0, x1, y1, layer, w):
    return ('\t(fp_line\n\t\t(start %.3f %.3f)\n\t\t(end %.3f %.3f)\n\t\t(stroke\n\t\t\t(width %.3f)\n\t\t\t(type solid)\n\t\t)\n'
            '\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)\n') % (x0, y0, x1, y1, w, layer, u())


def circle(cx, cy, r, layer, w):
    return ('\t(fp_circle\n\t\t(center %.3f %.3f)\n\t\t(end %.3f %.3f)\n\t\t(stroke\n\t\t\t(width %.3f)\n\t\t\t(type solid)\n\t\t)\n'
            '\t\t(fill no)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)\n') % (cx, cy, cx + r, cy, w, layer, u())


def pad(num, x, y, sx, sy, drill, shape="circle"):
    """drill: number (round) or (dx, dy) for an oval slot"""
    if isinstance(drill, tuple):
        d = "(drill oval %.3f %.3f)" % drill
    else:
        d = "(drill %.3f)" % drill
    return ('\t(pad "%s" thru_hole %s\n\t\t(at %.3f %.3f)\n\t\t(size %.3f %.3f)\n\t\t%s\n'
            '\t\t(layers "*.Cu" "*.Mask")\n\t\t(remove_unused_layers no)\n\t\t(uuid "%s")\n\t)\n') % (num, shape, x, y, sx, sy, d, u())


def ref_text(x, y):
    return ('\t(fp_text user "${REFERENCE}"\n\t\t(at %.3f %.3f 0)\n\t\t(layer "F.Fab")\n\t\t(uuid "%s")\n'
            '\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1 1)\n\t\t\t\t(thickness 0.15)\n\t\t\t)\n\t\t)\n\t)\n') % (x, y, u())


def write(name, descr, tags, body, ref_xy, val_xy, fab_ref_xy):
    s = '(footprint "%s"\n\t(version 20240108)\n\t(generator "tea2025_make_footprints")\n\t(layer "F.Cu")\n' % name
    s += '\t(descr "%s")\n\t(tags "%s")\n' % (descr, tags)
    s += text("Reference", "REF**", ref_xy[0], ref_xy[1], "F.SilkS")
    s += text("Value", name, val_xy[0], val_xy[1], "F.Fab")
    s += text("Footprint", "", 0, 0, "F.Fab", hide=True)
    s += text("Datasheet", "", 0, 0, "F.Fab", hide=True)
    s += text("Description", "", 0, 0, "F.Fab", hide=True)
    s += "\t(attr through_hole)\n"
    s += body + ref_text(*fab_ref_xy) + ")\n"
    with open(os.path.join(OUT, name + ".kicad_mod"), "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("wrote", name)


FAB, SILK, CRT = 0.10, 0.12, 0.05

# ---------------------------------------------------------------- MJ-179PH DC jack (Marushin)
# origin: jack axis at the front face; opening toward -X. Drawing MJ179PH(B): S slot 1x3 at 7.7, J slot 1x3.5 at 13.7,
# B slot 3x1 at x 10.75 and 4.9 from the axis. The reference print shows B on the -Y side, but the front view puts the
# B terminal on the right when looking into the opening (= +Y here). B is not used in this kit, so a slot is provided on
# BOTH sides; the jack fits either way.
b = ""
b += pad("1", 13.7, 0, 2.0, 4.5, (1.0, 3.5), "oval")      # J: center pin (+)
b += pad("2", 7.7, 0, 2.0, 4.0, (1.0, 3.0), "oval")       # S: sleeve spring (GND)
b += pad("3", 10.75, 4.9, 4.0, 2.0, (3.0, 1.0), "oval")   # B: break contact (unused)
b += pad("3", 10.75, -4.9, 4.0, 2.0, (3.0, 1.0), "oval")  # B: mirrored position (see descr)
b += rect(0, -4.5, 13.5, 4.5, "F.Fab", FAB) + rect(13.5, -1.5, 14.5, 1.5, "F.Fab", FAB)
b += line(0, -4.62, 8.35, -4.62, "F.SilkS", SILK) + line(0, 4.62, 8.35, 4.62, "F.SilkS", SILK)
b += line(0, -4.62, 0, 4.62, "F.SilkS", SILK)
b += line(13.62, -4.62, 13.62, -2.65, "F.SilkS", SILK) + line(13.62, 4.62, 13.62, 2.65, "F.SilkS", SILK)
b += rect(-0.25, -6.15, 15.0, 6.15, "F.CrtYd", CRT)
write("DCJack_Marushin_MJ-179PH", "Marushin MJ-179PH 2.1mm DC jack (Akizuki 106568). Drawing MJ179PH(B) foot print reference: "
      "S slot 1x3 @7.7, J slot 1x3.5 @13.7, B slot 3x1 @10.75 / 4.9 off axis. B side ambiguous between front view and "
      "reference print, so B slots on both sides (B unused). Origin = front face on the axis, opening to -X.",
      "DC jack barrel 2.1mm MJ-179PH", b, (7, -7.2), (7, 7.2), (7, 0))

# ---------------------------------------------------------------- MJ-8435 3.5mm stereo jack (Marushin)
# PC board hole layout, view from the insertion side. origin: body front face (behind the 2.5mm rim) on the axis,
# opening toward -Y. Tip spring (2) x2 at 5.5 (5.5 apart), sleeve (1) and ring (3) at 11, 4.4 apart.
# Holes 1.3x1 / 1.3x0.8 rectangular -> round 1.4 / 1.3.
b = ""
b += pad("T", -2.75, 5.5, 2.2, 2.2, 1.4) + pad("T", 2.75, 5.5, 2.2, 2.2, 1.4)
b += pad("S", -2.2, 11.0, 2.2, 2.2, 1.3) + pad("R", 2.2, 11.0, 2.2, 2.2, 1.3)
b += rect(-3.0, 0, 3.0, 11.5, "F.Fab", FAB) + rect(-3.0, -2.5, 3.0, 0, "F.Fab", FAB)
b += line(-3.12, -2.62, 3.12, -2.62, "F.SilkS", SILK) + line(-3.12, -2.62, -3.12, 4.1, "F.SilkS", SILK)
b += line(3.12, -2.62, 3.12, 4.1, "F.SilkS", SILK) + line(-3.12, 6.9, -3.12, 9.6, "F.SilkS", SILK)
b += line(3.12, 6.9, 3.12, 9.6, "F.SilkS", SILK)
b += rect(-4.1, -2.85, 4.1, 12.35, "F.CrtYd", CRT)
write("Jack_3.5mm_Marushin_MJ-8435_Horizontal", "Marushin MJ-8435 3.5mm stereo jack (Akizuki 109060). Drawing MJ-8435 "
      "PC board hole layout (view from insertion side): tip 2-1.3x1 @y5.5 x+-2.75, sleeve(1)/ring(3) 2-1.3x0.8 @y11 x-+2.2. "
      "Origin = body front face on the axis, 2.5mm rim toward -Y.",
      "audio jack 3.5mm stereo MJ-8435", b, (0, -3.8), (0, 13.4), (0, 2.5))

# ---------------------------------------------------------------- Alps RK12L12 dual, vertical (shaft up)
# Alps catalog p.323 No.1 Vertical, hole layout viewed from insertion side: 6x d0.8 at 2.0 pitch, two 2x2.1 lugs 13 apart,
# 11 above the pin row. Terminal order (outer R1 = 1,2,3 / inner R2 = 1,2,3): (2)(1) 1 2 3 (3).
# Pads: R1 -> 1,2,3 ; R2 -> 4,5,6 (Device:R_Potentiometer_Dual). Origin = shaft centre (= lug line).
b = ""
xs = {"2": -5.0, "1": -3.0, "4": -1.0, "5": 1.0, "6": 3.0, "3": 5.0}
for n, x in xs.items():
    b += pad(n, x, 11.0, 1.4, 1.4, 0.8, "rect" if n == "1" else "circle")
b += pad("", -6.5, 0, 2.8, 2.8, 2.1) + pad("", 6.5, 0, 2.8, 2.8, 2.1)
b += rect(-6.0, -6.0, 6.0, 9.5, "F.Fab", FAB) + circle(0, 0, 3.0, "F.Fab", FAB)
b += line(-6.12, -6.12, 6.12, -6.12, "F.SilkS", SILK) + line(-6.12, -6.12, -6.12, -1.75, "F.SilkS", SILK)
b += line(6.12, -6.12, 6.12, -1.75, "F.SilkS", SILK) + line(-6.12, 1.75, -6.12, 9.62, "F.SilkS", SILK)
b += line(6.12, 1.75, 6.12, 9.62, "F.SilkS", SILK) + line(-6.12, 9.62, 6.12, 9.62, "F.SilkS", SILK)
b += circle(0, 0, 3.1, "F.SilkS", SILK)
b += rect(-8.15, -6.35, 8.15, 11.95, "F.CrtYd", CRT)
write("Potentiometer_Alps_RK12L_Dual_Vertical", "Alps RK12L12C0A0E dual 10kA, vertical, 25mm shaft (Akizuki 117473). "
      "Catalog RK12L p.323 No.1: 6-d0.8 holes P2.0, lugs 2x2.1 13 apart, 11 from pin row. Order (2)(1)1 2 3(3); "
      "pads 1-3 = outer element R1, 4-6 = inner element R2. Origin = shaft centre.",
      "potentiometer dual vertical Alps RK12L", b, (0, -7.3), (0, 13.2), (0, 4.5))

# ---------------------------------------------------------------- Alphaplus TB111-2 screw terminal 5.08
# Drawing TB111-2-x-x-x-x: pitch 5.08, holes d1.3, body 7.6 deep, pins 4.2 from the rear, length 10.16 (+0.5 latches).
# Wire entry toward +Y. Origin = pin 1.
b = pad("1", 0, 0, 2.6, 2.6, 1.3, "rect") + pad("2", 5.08, 0, 2.6, 2.6, 1.3)
b += rect(-2.54, -4.2, 7.62, 3.4, "F.Fab", FAB) + line(-2.54, 2.4, 7.62, 2.4, "F.Fab", FAB)
b += rect(-2.66, -4.32, 7.74, 3.52, "F.SilkS", SILK) + line(-2.66, 2.5, 7.74, 2.5, "F.SilkS", SILK)
b += rect(-3.29, -4.45, 8.37, 3.65, "F.CrtYd", CRT)
write("TerminalBlock_Alphaplus_TB111-2_P5.08mm", "Alphaplus TB111-2-2-U-1-1 screw terminal 2P 5.08mm (Akizuki 101306). "
      "Drawing TB111-2-x-x-x-x: holes d1.30, body 10.16x7.6, pins 4.2 from rear. Wire entry toward +Y. Origin = pin 1.",
      "terminal block screw 5.08 TB111", b, (2.54, -5.4), (2.54, 4.7), (2.54, -2.6))

# ---------------------------------------------------------------- MEM film capacitor 7.5 x 3.5 P5.0
# Faithful Link MEM series (Akizuki 114597/114598/114599): 0.1/0.15uF 7.5x6.5x2.5, 0.22uF 7.2x7.5x3.5, P5.0, lead 0.5-0.6.
# Copy of KiCad C_Rect_L7.2mm_W3.5mm_P5.00mm with L 7.5 and drill 0.9 (lead 0.6 + 0.3).
b = pad("1", 0, 0, 1.6, 1.6, 0.9) + pad("2", 5.0, 0, 1.6, 1.6, 0.9)
b += rect(-1.25, -1.75, 6.25, 1.75, "F.Fab", FAB) + rect(-1.37, -1.87, 6.37, 1.87, "F.SilkS", SILK)
b += rect(-1.6, -2.1, 6.6, 2.1, "F.CrtYd", CRT)
write("C_Rect_L7.5mm_W3.5mm_P5.00mm_MEM", "Faithful Link MEM metallized polyester film cap, 7.5x3.5 (max of 0.1/0.15/0.22uF 100V), "
      "P5.0. Based on KiCad C_Rect_L7.2mm_W3.5mm_P5.00mm, changed: L 7.2->7.5, drill 0.75->0.9.",
      "capacitor film MEM P5.00", b, (2.5, -3.0), (2.5, 3.0), (2.5, 0))

# ---------------------------------------------------------------- radial electrolytics, lead pitch 5.08 mm (user 2026-10-21)
# Rubycon PX (Akizuki 110271 / 110273): D5 lead d0.5 (F 2.0), D8 lead d0.6 (F 3.5); leads are formed to 5.08 mm.
# Based on KiCad CP_Radial_D5.0mm_P2.50mm / CP_Radial_D8.0mm_P5.00mm, changed: pitch -> 5.08, body centred at 2.54.
def arc(cx, cy, r, a0, a1, layer, w):
    am = (a0 + a1) / 2
    p = lambda a: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    (x0, y0), (xm, ym), (x1, y1) = p(a0), p(am), p(a1)
    return ('\t(fp_arc\n\t\t(start %.3f %.3f)\n\t\t(mid %.3f %.3f)\n\t\t(end %.3f %.3f)\n\t\t(stroke\n\t\t\t(width %.3f)\n'
            '\t\t\t(type solid)\n\t\t)\n\t\t(layer "%s")\n\t\t(uuid "%s")\n\t)\n') % (x0, y0, xm, ym, x1, y1, w, layer, u())


def plus(x, y, s, layer, w):
    return line(x - s, y, x + s, y, layer, w) + line(x, y - s, x, y + s, layer, w)


for d, name in ((5.0, "CP_Radial_D5.0mm_P5.08mm"), (8.0, "CP_Radial_D8.0mm_P5.08mm")):
    r = d / 2; cx = 2.54
    b = pad("1", 0, 0, 1.6, 1.6, 0.8, "rect") + pad("2", 5.08, 0, 1.6, 1.6, 0.8)
    b += circle(cx, 0, r, "F.Fab", FAB) + plus(cx - r * 0.55, -r * 0.45, 0.4, "F.Fab", FAB)
    rs = r + 0.12
    if d == 5.0:
        # the pads sit on the body outline: break the silk circle 1.0 mm around both pad centres
        k = (1.0 - cx * cx - rs * rs) / (2 * cx * rs)          # cos(angle) where the circle is 1.0 mm from pad 1
        ang = math.degrees(math.acos(k))                         # pad 1 side: |angle| <= ang ; pad 2 side: >= 180-ang
        b += arc(cx, 0, rs, 180 - ang, ang, "F.SilkS", SILK) + arc(cx, 0, rs, -ang, -(180 - ang), "F.SilkS", SILK)
        b += plus(-1.2, -2.3, 0.5, "F.SilkS", SILK)
        b += rect(-1.05, -r - 0.27, 5.08 + 1.05, r + 0.27, "F.CrtYd", CRT)
    else:
        b += circle(cx, 0, rs, "F.SilkS", SILK) + plus(-2.3, -2.6, 0.5, "F.SilkS", SILK)
        b += circle(cx, 0, r + 0.25, "F.CrtYd", CRT)
    write(name, "Radial electrolytic D%.1fmm, lead pitch 5.08mm (formed leads). Rubycon PX 16V (Akizuki %s). Based on KiCad %s, "
          "pitch changed to 5.08mm and body centred between the pads." % (d, "110271" if d == 5.0 else "110273",
          "CP_Radial_D5.0mm_P2.50mm" if d == 5.0 else "CP_Radial_D8.0mm_P5.00mm"),
          "CP electrolytic radial P5.08", b, (cx, -r - 1.2), (cx, r + 1.2), (cx, 0))

# ---------------------------------------------------------------- Amazon 12x12 alternate push switch (club library)
# From the user's library 電子工作クラブ:Amazon_sw (used on 電子工作クラブ_追加基板): pads at y +-6.4, oval 3x2.54, drill 1.2.
# Changes: attr smd -> through_hole, courtyard and fab outline added. Product: Audiofan alternate push switch 2pin
# 12x12x9mm (Amazon B0CQ1SKJPN), pins on two opposite faces.
b = pad("1", 0, 6.4, 3.0, 2.54, 1.2, "oval") + pad("2", 0, -6.4, 3.0, 2.54, 1.2, "oval")
b += rect(-6, -6, 6, 6, "F.Fab", FAB) + circle(0, 0, 3.5, "F.Fab", FAB)
b += line(-6.12, -6.12, -1.9, -6.12, "F.SilkS", SILK) + line(1.9, -6.12, 6.12, -6.12, "F.SilkS", SILK)
b += line(-6.12, 6.12, -1.9, 6.12, "F.SilkS", SILK) + line(1.9, 6.12, 6.12, 6.12, "F.SilkS", SILK)
b += line(-6.12, -6.12, -6.12, 6.12, "F.SilkS", SILK) + line(6.12, -6.12, 6.12, 6.12, "F.SilkS", SILK)
b += rect(-6.35, -7.92, 6.35, 7.92, "F.CrtYd", CRT)
write("Amazon_sw", "Audiofan 12x12x9mm alternate push switch 2pin (Amazon B0CQ1SKJPN). Copied from user library "
      "電子工作クラブ:Amazon_sw (pads +-6.4, oval 3x2.54, drill 1.2); attr set to through_hole, courtyard/fab added.",
      "switch push alternate 12x12", b, (0, -9.0), (0, 9.0), (0, 0))
