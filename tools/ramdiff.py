"""Compare two RAM dumps from tools/run_dump.sh (64 KB at 0x100000).
Usage: python tools/ramdiff.py a.bin b.bin [max_value]   -> bytes that differ (both <= max_value, default 255)
Also prints the P1 object ($105A16, 0x48 bytes) from both."""
import sys
a, b = open(sys.argv[1], "rb").read(), open(sys.argv[2], "rb").read()
mx = int(sys.argv[3]) if len(sys.argv) > 3 else 255
o = 0x5A16
print("A obj", a[o:o + 0x48].hex(" "))
print("B obj", b[o:o + 0x48].hex(" "))
diffs = [(0x100000 + i, a[i], b[i]) for i in range(len(a)) if a[i] != b[i] and a[i] <= mx and b[i] <= mx]
for addr, x, y in diffs[:80]:
    print(f"{addr:06x} {x:02x} {y:02x}")
print(len(diffs), "differences")
