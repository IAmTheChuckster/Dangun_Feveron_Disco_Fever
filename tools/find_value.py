"""Find RAM addresses whose value matches a sequence across several dumps (binary or BCD, byte or word).
Usage: python tools/find_value.py dump1.bin=5 dump2.bin=16 dump3.bin=21   (dumps from tools/run_dump.sh)"""
import sys

pairs = [a.rsplit("=", 1) for a in sys.argv[1:]]
dumps = [(open(p, "rb").read(), int(v)) for p, v in pairs]
bcd = lambda n: int(str(n), 16)
for size in (1, 2):
    for enc, f in (("bin", lambda n: n), ("bcd", bcd)):
        for i in range(0, len(dumps[0][0]) - size + 1, 1 if size == 1 else 2):
            if all(int.from_bytes(d[i:i + size], "big") == f(v) for d, v in dumps):
                print(f"{0x100000 + i:06x} size {size} {enc}")
