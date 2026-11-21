"""Find a text by its letter-repeat pattern (same letter = same code, different letter = different code),
for any encoding. Searches 8-, 16- and 32-bit elements at strides 1, 2 and 4 elements.
Usage: python tools/find_pattern.py <file-or-romset.zip> "TEXT"   (spaces are part of the pattern)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import patch

src, text = sys.argv[1], sys.argv[2]
if src.endswith(".zip"):
    f = patch.read_input(src)
    data = bytearray(len(f["cv01-u33.bin"]) * 2)
    data[0::2], data[1::2] = f["cv01-u34.bin"], f["cv01-u33.bin"]
else:
    data = open(src, "rb").read()
L = len(text)
for size in (1, 2, 4):
    vals = [int.from_bytes(data[i:i + size], "big") for i in range(0, len(data) - size + 1, size)]
    for stride in (1, 2, 4, 8, 16):
        span = (L - 1) * stride
        for i in range(len(vals) - span):
            m = {}; rev = {}; ok = True
            for k, ch in enumerate(text):
                v = vals[i + k * stride]
                if m.setdefault(ch, v) != v or rev.setdefault(v, ch) != ch:
                    ok = False; break
            if ok:
                print(f"size {size} stride {stride} at {i * size:06x}: " +
                      " ".join(f"{ch}={m[ch]:x}" for ch in dict.fromkeys(text)))
