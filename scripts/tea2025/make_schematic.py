# -*- coding: utf-8 -*-
"""Generate TEA2025_amp.kicad_sch (A3, net labels only, framed functional blocks).
Circuit: TEA2025 stereo application (ST TEA2025 Rev4 Fig.4 / UTC QW-R107-033 Fig.5) + 470uF/0.1uF supply bypass,
power switch, power LED, DC jack and battery terminal in parallel."""
import math, os, re, sys, uuid

sys.path.insert(0, os.path.dirname(__file__))
import sexp

PRJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(PRJ, "TEA2025_amp.kicad_sch")
OWNLIB = os.path.join(PRJ, "lib", "TEA2025_amp", "TEA2025_amp.kicad_sym")
ROOT = str(uuid.uuid5(uuid.NAMESPACE_URL, "tea2025_amp_root"))
_n = [0]


def U():
    _n[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "tea2025_amp_%d" % _n[0]))


# ------------------------------------------------------------------ parts
# ref, lib_id, value, footprint, x, y, rot, unit, labels {pin: net or None(=no_connect)}, extra props
FP = "TEA2025_amp:"
PARTS = [
    # ---- input
    ("J1", "Connector_Audio:AudioJack3", "MJ-8435", FP + "Jack_3.5mm_Marushin_MJ-8435_Horizontal", 33.02, 60.96, 0, 1,
     {"S": "GND", "T": "IN_L", "R": "IN_R"}, {"MPN": "MJ-8435", "Akizuki": "109060"}),
    ("RV1", "Device:R_Potentiometer_Dual_Separate", "10kA", FP + "Potentiometer_Alps_RK12L_Dual_Vertical", 71.12, 50.8, 0, 1,
     {"1": "GND", "2": "VOL_L", "3": "IN_L"}, {"MPN": "RK12L12C0A0E", "Akizuki": "117473"}),
    ("RV1", "Device:R_Potentiometer_Dual_Separate", "10kA", FP + "Potentiometer_Alps_RK12L_Dual_Vertical", 71.12, 81.28, 0, 2,
     {"4": "GND", "5": "VOL_R", "6": "IN_R"}, {"MPN": "RK12L12C0A0E", "Akizuki": "117473"}),
    ("C1", "Device:C", "0.1µ", FP + "C_Rect_L7.5mm_W3.5mm_P5.00mm_MEM", 101.6, 50.8, 90, 1,
     {"1": "VOL_L", "2": "IN1"}, {"MPN": "104 フィルム P5.08（部室在庫）／購入なら MEM104J101RB-5", "Akizuki": "114597"}),
    ("C2", "Device:C", "0.1µ", FP + "C_Rect_L7.5mm_W3.5mm_P5.00mm_MEM", 101.6, 81.28, 90, 1,
     {"1": "VOL_R", "2": "IN2"}, {"MPN": "104 フィルム P5.08（部室在庫）／購入なら MEM104J101RB-5", "Akizuki": "114597"}),
    # ---- amplifier
    ("U1", "TEA2025_amp:TEA2025", "TEA2025", "Package_DIP:DIP-16_W7.62mm", 205.74, 96.52, 0, 1,
     {"10": "IN1", "11": "FB1", "7": "IN2", "6": "FB2", "8": "SVR", "1": None, "15": "OUT1", "14": "BOOT1",
      "2": "OUT2", "3": "BOOT2", "16": "VCC", "4": "GND", "5": "GND", "9": "GND", "12": "GND", "13": "GND"},
     {"MPN": "TEA2025L-D16", "Akizuki": "114023"}),
    ("C3", "Device:C_Polarized", "100µ", FP + "CP_Radial_D5.0mm_P5.08mm", 147.32, 58.42, 0, 1,
     {"1": "FB1", "2": "GND"}, {"MPN": "16PX100MEFC5X11 (16V)", "Akizuki": "110271"}),
    ("C4", "Device:C_Polarized", "100µ", FP + "CP_Radial_D5.0mm_P5.08mm", 162.56, 58.42, 0, 1,
     {"1": "FB2", "2": "GND"}, {"MPN": "16PX100MEFC5X11 (16V)", "Akizuki": "110271"}),
    ("C5", "Device:C_Polarized", "100µ", FP + "CP_Radial_D5.0mm_P5.08mm", 238.76, 58.42, 0, 1,
     {"1": "BOOT1", "2": "OUT1"}, {"MPN": "16PX100MEFC5X11 (16V)", "Akizuki": "110271"}),
    ("C6", "Device:C_Polarized", "100µ", FP + "CP_Radial_D5.0mm_P5.08mm", 254.0, 58.42, 0, 1,
     {"1": "BOOT2", "2": "OUT2"}, {"MPN": "16PX100MEFC5X11 (16V)", "Akizuki": "110271"}),
    ("C11", "Device:C_Polarized", "100µ", FP + "CP_Radial_D5.0mm_P5.08mm", 177.8, 58.42, 0, 1,
     {"1": "SVR", "2": "GND"}, {"MPN": "16PX100MEFC5X11 (16V)", "Akizuki": "110271"}),
    # ---- output
    ("C7", "Device:C_Polarized", "470µ", FP + "CP_Radial_D8.0mm_P5.08mm", 322.58, 55.88, 90, 1,
     {"1": "OUT1", "2": "SPK_L"}, {"MPN": "16PX470MEFC8X11.5 (16V)", "Akizuki": "110273"}),
    ("C9", "Device:C", "0.1µ", FP + "C_Rect_L7.5mm_W3.5mm_P5.00mm_MEM", 322.58, 76.2, 0, 1,
     {"1": "OUT1", "2": "GND"}, {"MPN": "104 フィルム P5.08（部室在庫）／購入なら MEM104J101RB-5", "Akizuki": "114597"}),
    ("C14", "Device:C", "0.1µ", FP + "C_Rect_L7.5mm_W3.5mm_P5.00mm_MEM", 340.36, 76.2, 0, 1,
     {"1": "OUT1", "2": "GND"}, {"MPN": "104 フィルム P5.08（部室在庫）／購入なら MEM104J101RB-5", "Akizuki": "114597"}),
    ("J2", "Connector:Screw_Terminal_01x02", "SP L", FP + "TerminalBlock_Alphaplus_TB111-2_P5.08mm", 381.0, 55.88, 0, 1,
     {"1": "SPK_L", "2": "GND"}, {"MPN": "TB111-2-2-U-1-1", "Akizuki": "101306"}),
    ("C8", "Device:C_Polarized", "470µ", FP + "CP_Radial_D8.0mm_P5.08mm", 322.58, 109.22, 90, 1,
     {"1": "OUT2", "2": "SPK_R"}, {"MPN": "16PX470MEFC8X11.5 (16V)", "Akizuki": "110273"}),
    ("C10", "Device:C", "0.1µ", FP + "C_Rect_L7.5mm_W3.5mm_P5.00mm_MEM", 322.58, 129.54, 0, 1,
     {"1": "OUT2", "2": "GND"}, {"MPN": "104 フィルム P5.08（部室在庫）／購入なら MEM104J101RB-5", "Akizuki": "114597"}),
    ("C15", "Device:C", "0.1µ", FP + "C_Rect_L7.5mm_W3.5mm_P5.00mm_MEM", 340.36, 129.54, 0, 1,
     {"1": "OUT2", "2": "GND"}, {"MPN": "104 フィルム P5.08（部室在庫）／購入なら MEM104J101RB-5", "Akizuki": "114597"}),
    ("J3", "Connector:Screw_Terminal_01x02", "SP R", FP + "TerminalBlock_Alphaplus_TB111-2_P5.08mm", 381.0, 109.22, 0, 1,
     {"1": "SPK_R", "2": "GND"}, {"MPN": "TB111-2-2-U-1-1", "Akizuki": "101306"}),
    # ---- power
    ("J4", "Connector:Barrel_Jack_Switch", "MJ-179PH", FP + "DCJack_Marushin_MJ-179PH", 38.1, 213.36, 0, 1,
     {"1": "VIN", "2": "GND", "3": None}, {"MPN": "MJ-179PH", "Akizuki": "106568"}),
    ("J5", "Connector:Screw_Terminal_01x02", "BATT", FP + "TerminalBlock_Alphaplus_TB111-2_P5.08mm", 53.34, 246.38, 0, 1,
     {"1": "VIN", "2": "GND"}, {"MPN": "TB111-2-2-U-1-1", "Akizuki": "101306"}),
    ("SW1", "Switch:SW_SPST", "POWER", FP + "Amazon_sw", 101.6, 210.82, 0, 1,
     {"1": "VIN", "2": "VCC"}, {"MPN": "Audiofan alternate push switch 12x12 (Amazon B0CQ1SKJPN)", "Akizuki": ""}),
    ("C12", "Device:C_Polarized", "470µ", FP + "CP_Radial_D8.0mm_P5.08mm", 137.16, 215.9, 0, 1,
     {"1": "VCC", "2": "GND"}, {"MPN": "16PX470MEFC8X11.5 (16V)", "Akizuki": "110273"}),
    ("C13", "Device:C", "0.1µ", FP + "C_Rect_L7.5mm_W3.5mm_P5.00mm_MEM", 154.94, 215.9, 0, 1,
     {"1": "VCC", "2": "GND"}, {"MPN": "104 フィルム P5.08（部室在庫）／購入なら MEM104J101RB-5", "Akizuki": "114597"}),
    ("R1", "Device:R", "3.3k", "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P7.62mm_Horizontal", 175.26, 208.28, 0, 1,
     {"1": "VCC", "2": "LED_A"}, {"MPN": "CF25J3K3B (1/4W)", "Akizuki": "125332"}),
    ("D1", "Device:LED", "RED", "LED_THT:LED_D3.0mm", 175.26, 236.22, 90, 1,
     {"2": "LED_A", "1": "GND"}, {"MPN": "OSR5JA3Z74A", "Akizuki": "111577"}),
    ("#FLG01", "power:PWR_FLAG", "PWR_FLAG", "", 213.36, 210.82, 0, 1, {"1": "VCC"}, {}),
    ("#FLG02", "power:PWR_FLAG", "PWR_FLAG", "", 231.14, 210.82, 0, 1, {"1": "GND"}, {}),
    ("#FLG03", "power:PWR_FLAG", "PWR_FLAG", "", 248.92, 210.82, 0, 1, {"1": "VIN"}, {}),
    # ---- mounting holes
    ("H1", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", 320.04, 203.2, 0, 1, {}, {}),
    ("H2", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", 340.36, 203.2, 0, 1, {}, {}),
    ("H3", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", 360.68, 203.2, 0, 1, {}, {}),
    ("H4", "Mechanical:MountingHole", "M3", "MountingHole:MountingHole_3.2mm_M3", 381.0, 203.2, 0, 1, {}, {}),
]

BLOCKS = [  # x0, y0, x1, y1, title, notes
    (15, 25, 120, 100, "入力（3.5mm ジャック・2連ボリューム）", ["T=L, R=R, S=GND。ボリュームは 1 番側が GND"]),
    (125, 25, 290, 160, "アンプ（TEA2025 ステレオ）", ["推奨回路どおり（Rf なし、利得 約46dB）", "入力 C1/C2 は 104（推奨 0.22µF、低域の下限 約53Hz）", "1 番 BRIDGE はステレオでは未接続"]),
    (295, 25, 405, 160, "出力（スピーカー端子）", ["C9∥C14、C10∥C15 は 104×2＝0.2µF（推奨 0.15µF 以上）", "出力 470µF で直流カット（8Ω で約42Hz）"]),
    (15, 170, 290, 270, "電源（DC ジャック・電池端子・電源スイッチ・LED）",
     ["DC ジャックと電池端子は並列（同時に接続しない）", "J4 の 3 番（切替接点）は使わない", "9V 推奨（3〜12V）"]),
    (295, 170, 405, 230, "取付穴（M3）", []),
]

LIBFILES = {"TEA2025_amp": OWNLIB}


def lib_block(lib_id):
    lib, nm = lib_id.split(":")
    blk = sexp.load_symbol(lib, nm, LIBFILES.get(lib))
    blk = blk.replace('(symbol "%s"' % nm, '(symbol "%s"' % lib_id, 1)
    return blk


def rot(px, py, r):
    """lib (Y up) -> schematic offset (Y down), symbol rotated r degrees CCW"""
    c, s = round(math.cos(math.radians(r))), round(math.sin(math.radians(r)))
    vx, vy = px * c - py * s, px * s + py * c
    return vx, -vy


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def prop(k, v, x, y, ang=0, hide=False, justify=None):
    j = "\n\t\t\t\t(justify %s)" % justify if justify else ""
    h = "\n\t\t\t(hide yes)" if hide else ""
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s %d)%s\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)%s\n'
            '\t\t\t)\n\t\t)\n') % (k, v, fmt(x), fmt(y), ang, h, j)


def label(net, x, y, outward):
    ang = int(outward) % 360
    just = "left bottom" if ang in (0, 90) else "right bottom"
    return ('\t(label "%s"\n\t\t(at %s %s %d)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
            '\t\t\t(justify %s)\n\t\t)\n\t\t(uuid "%s")\n\t)\n') % (net, fmt(x), fmt(y), ang, just, U())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    libs = {}
    for p in PARTS:
        if p[1] not in libs: libs[p[1]] = lib_block(p[1])
    pinmap = {lid: {q[0]: q for q in sexp.pins(b)} for lid, b in libs.items()}

    s = '(kicad_sch\n\t(version 20250114)\n\t(generator "eeschema")\n\t(generator_version "9.0")\n\t(uuid "%s")\n\t(paper "A3")\n' % ROOT
    s += ('\t(title_block\n\t\t(title "TEA2025 ステレオアンプキット")\n\t\t(date "2026-10-21")\n\t\t(rev "A")\n'
          '\t\t(comment 1 "100x50mm 2層 / 全部品 DIP / JLCPCB")\n\t)\n')
    s += "\t(lib_symbols\n"
    for lid, b in libs.items():
        s += "\n".join("\t" + ln for ln in b.split("\n")) + "\n"
    s += "\t)\n"

    for x0, y0, x1, y1, title, notes in BLOCKS:
        s += ('\t(rectangle\n\t\t(start %s %s)\n\t\t(end %s %s)\n\t\t(stroke\n\t\t\t(width 0.3)\n\t\t\t(type dash)\n\t\t)\n'
              '\t\t(fill\n\t\t\t(type none)\n\t\t)\n\t\t(uuid "%s")\n\t)\n') % (x0, y0, x1, y1, U())
        s += ('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 2.5 2.5)\n'
              '\t\t\t\t(bold yes)\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)\n') % (title, x0 + 2, y0 + 5, U())
        for i, nt in enumerate(notes):
            s += ('\t(text "%s"\n\t\t(exclude_from_sim no)\n\t\t(at %s %s 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.5 1.5)\n'
                  '\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "%s")\n\t)\n') % (nt, x0 + 2, y1 - 3 - 3 * (len(notes) - 1 - i), U())

    for ref, lid, val, fp, x, y, r, unit, labels, extra in PARTS:
        pins = pinmap[lid]
        is_pwr = lid.startswith("power:")
        vertical_2pin = len(pins) == 2 and r == 0 and lid.startswith("Device:") and lid != "Device:LED"
        if is_pwr:
            rp, vp = (x, y - 5.08, 0, "", True), (x, y - 3.81, 0, "", False)
        elif vertical_2pin:
            rp, vp = (x + 2.54, y - 1.27, 0, "left", False), (x + 2.54, y + 1.27, 0, "left", False)
        elif r == 90 and lid == "Device:LED":
            rp, vp = (x + 5.08, y - 1.27, 90, "left", False), (x + 5.08, y + 1.27, 90, "left", False)
        elif r == 90 and len(pins) == 2:
            rp, vp = (x, y - 4.445, 90, "", False), (x, y + 4.445, 90, "", False)
        elif lid == "TEA2025_amp:TEA2025":
            rp, vp = (x - 10.16, y - 20.32, 0, "left", False), (x + 2.54, y - 20.32, 0, "left", False)
        else:
            rp, vp = (x, y - 7.62, 0, "", False), (x, y + 7.62, 0, "", False)
        if lid.startswith("Mechanical:"):
            rp, vp = (x, y - 5.08, 0, "", False), (x, y + 5.08, 0, "", False)
        if lid == "Device:R_Potentiometer_Dual_Separate":
            rp, vp = (x - 2.54, y - 1.27, 0, "right", False), (x - 2.54, y + 1.27, 0, "right", False)
        inb = "no" if (is_pwr or lid.startswith("Mechanical:")) else "yes"
        s += ('\t(symbol\n\t\t(lib_id "%s")\n\t\t(at %s %s %d)\n\t\t(unit %d)\n\t\t(exclude_from_sim no)\n\t\t(in_bom %s)\n'
              '\t\t(on_board %s)\n\t\t(dnp no)\n\t\t(uuid "%s")\n') % (lid, fmt(x), fmt(y), r, unit, inb, "no" if is_pwr else "yes", U())
        s += prop("Reference", ref, rp[0], rp[1], rp[2], rp[4], rp[3] or None)
        s += prop("Value", val, vp[0], vp[1], vp[2], vp[4], vp[3] or None)
        s += prop("Footprint", fp, x, y, 0, True)
        ds = {"U1": "https://akizukidenshi.com/goodsaffix/tea2025.pdf"}.get(ref, "~")
        s += prop("Datasheet", ds, x, y, 0, True)
        for k, v in extra.items():
            s += prop(k, v, x, y, 0, True)
        for num, q in pins.items():
            if q[5] in (0, unit):
                s += '\t\t(pin "%s"\n\t\t\t(uuid "%s")\n\t\t)\n' % (num, U())
        s += ('\t\t(instances\n\t\t\t(project "TEA2025_amp"\n\t\t\t\t(path "/%s"\n\t\t\t\t\t(reference "%s")\n'
              '\t\t\t\t\t(unit %d)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n') % (ROOT, ref, unit)
        # labels / no-connects at the pin ends
        for num, net in labels.items():
            q = pins[num]
            dx, dy = rot(q[2], q[3], r)
            px, py = x + dx, y + dy
            if net is None:
                s += '\t(no_connect\n\t\t(at %s %s)\n\t\t(uuid "%s")\n\t)\n' % (fmt(px), fmt(py), U())
            else:
                outward = (q[4] + 180 + r) % 360
                if is_pwr: outward = 270
                s += label(net, px, py, outward)
    s += '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n'
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
