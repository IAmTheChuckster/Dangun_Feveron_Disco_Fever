"""List absolute long references (lea/move etc.) in the program to addresses in a RAM range, with counts.
Usage: python tools/find_refs.py prog.bin <lo hex> <hi hex>"""
import sys, collections

p = open(sys.argv[1], "rb").read()
lo, hi = int(sys.argv[2], 16), int(sys.argv[3], 16)
hits = collections.defaultdict(list)
for i in range(0, len(p) - 4, 2):
    v = int.from_bytes(p[i:i + 4], "big")
    if lo <= v <= hi:
        hits[v].append(i)
for v in sorted(hits):
    print(f"{v:06x}: {len(hits[v])} refs  " + " ".join(f"{a:06x}" for a in hits[v][:12]))
