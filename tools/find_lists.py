"""Find object arrays in a RAM dump: 0x20- or 0x40-byte records with word0 bit 15 set and a plausible position.
Usage: python tools/find_lists.py ram.bin [stride hex]"""
import sys

r = open(sys.argv[1], "rb").read()
stride = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x20
w = lambda o: int.from_bytes(r[o:o + 2], "big")
for start in range(0, stride, 2):
    run, first = 0, None
    for o in range(start, len(r) - stride, stride):
        ok = w(o) & 0x8000 and 0 < w(o + 6) < 0x6000 and 0 < w(o + 8) < 0x5000
        if ok:
            run += 1
            first = first if first is not None else o
        elif first is not None and o - first > stride * 3:
            if run >= 6:
                print(f"{0x100000 + first:06x}..{0x100000 + o:06x} active={run}")
            run, first = 0, None
        elif first is not None and run == 0:
            first = None
