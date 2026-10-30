# -*- coding: utf-8 -*-
"""Write lib/TEA2025_amp/TEA2025_amp.kicad_sym with the TEA2025 symbol (pinout: ST TEA2025 Rev4 Fig.2 /
UTC TEA2025 QW-R107-033 pin configuration, identical). Normalise afterwards with: kicad-cli sym upgrade <file>"""
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "lib", "TEA2025_amp", "TEA2025_amp.kicad_sym")

PINS = [  # number, name, type, x, y, angle
    ("10", "IN1+", "input", -15.24, 10.16, 0), ("11", "FB1", "passive", -15.24, 7.62, 0),
    ("7", "IN2+", "input", -15.24, 2.54, 0), ("6", "FB2", "passive", -15.24, 0.0, 0),
    ("8", "SVR", "passive", -15.24, -5.08, 0), ("1", "BRIDGE", "passive", -15.24, -10.16, 0),
    ("15", "OUT1", "output", 15.24, 10.16, 180), ("14", "BOOT1", "passive", 15.24, 7.62, 180),
    ("2", "OUT2", "output", 15.24, 2.54, 180), ("3", "BOOT2", "passive", 15.24, 0.0, 180),
    ("16", "VS+", "power_in", 0.0, 17.78, 270),
    ("4", "GND", "power_in", -5.08, -27.94, 90), ("5", "GND", "power_in", -2.54, -27.94, 90),
    ("9", "GND(sub)", "power_in", 0.0, -27.94, 90), ("12", "GND", "power_in", 2.54, -27.94, 90),
    ("13", "GND", "power_in", 5.08, -27.94, 90),
]


def prop(k, v, x, y, hide=False):
    h = "\n\t\t\t(hide yes)" if hide else ""
    return ('\t\t(property "%s" "%s"\n\t\t\t(at %.2f %.2f 0)%s\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n'
            '\t\t\t\t)\n\t\t\t)\n\t\t)\n') % (k, v, x, y, h)


s = '(kicad_symbol_lib\n\t(version 20231120)\n\t(generator "tea2025_make_symbol")\n'
s += '\t(symbol "TEA2025"\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n'
s += prop("Reference", "U", -10.16, 20.32)
s += prop("Value", "TEA2025", 5.08, 20.32)
s += prop("Footprint", "Package_DIP:DIP-16_W7.62mm", 0, -33.02, True)
s += prop("Datasheet", "https://akizukidenshi.com/goodsaffix/tea2025.pdf", 0, -35.56, True)
s += prop("Description", "Stereo / bridge audio power amplifier, 3-12V, 2x2.3W (9V, 4ohm), DIP-16 12+2+2", 0, -38.1, True)
s += prop("ki_keywords", "audio amplifier stereo bridge power TEA2025", 0, 0, True)
s += ('\t\t(symbol "TEA2025_0_1"\n\t\t\t(rectangle\n\t\t\t\t(start -10.16 12.7)\n\t\t\t\t(end 10.16 -22.86)\n'
      '\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n\t\t\t\t(fill\n\t\t\t\t\t(type background)\n'
      '\t\t\t\t)\n\t\t\t)\n\t\t)\n')
s += '\t\t(symbol "TEA2025_1_1"\n'
for num, name, typ, x, y, ang in PINS:
    s += ('\t\t\t(pin %s line\n\t\t\t\t(at %.2f %.2f %d)\n\t\t\t\t(length 5.08)\n\t\t\t\t(name "%s"\n\t\t\t\t\t(effects\n'
          '\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t\t(number "%s"\n'
          '\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)\n') % (
        typ, x, y, ang, name, num)
s += '\t\t)\n\t\t(embedded_fonts no)\n\t)\n)\n'
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(s)
print("wrote", OUT)
