"""Write a schedule that starts a 1P game and taps button 1 (normal shot) every few frames until a given frame,
weaving left/right a little. (Button 3 / rapid fire is disabled in this MAME setup's settings.)
Usage: python tools/make_tap_fire.py out.txt [last_frame]"""
import sys

out, last = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 200000
lines = ["1300 K", "1303 -", "1400 S", "1403 -", "1600 A", "1603 -", "1700 A", "1703 -", "1800 A", "1803 -"]
f, k = 1900, 0
dirs = ["", "L", "", "R"]
while f < last:
    d = dirs[(f // 240) % len(dirs)]
    lines.append(f"{f} A{d}")
    lines.append(f"{f + 2} {d or '-'}")
    f += 5
open(out, "w", newline="\n").write("\n".join(lines) + "\n")
print(len(lines), "lines")
