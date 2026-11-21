"""Find a text in the dfeveron program when the game uses its own character codes:
matches byte or 16-bit word sequences whose differences equal those of the letters (spaces ignored).
Usage: python tools/find_rel.py <romset.zip> "TEXT" """
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import patch

files = patch.read_input(sys.argv[1])
u33, u34 = files["cv01-u33.bin"], files["cv01-u34.bin"]
prog = bytearray(len(u33) * 2)
prog[0::2], prog[1::2] = u34, u33
word = sys.argv[2].replace(" ", "")
d = [ord(b) - ord(a) for a, b in zip(word, word[1:])]
for step, size in ((1, 1), (2, 2)):
    vals = prog if size == 1 else [int.from_bytes(prog[i:i + 2], "big") for i in range(0, len(prog) - 1, 2)]
    n = len(vals)
    for i in range(n - len(word)):
        if all(vals[i + k + 1] - vals[i + k] == d[k] for k in range(len(d))):
            addr = i * step
            off = vals[i] - ord(word[0])
            print(f"{'byte' if size == 1 else 'word'} match at {addr:06x}, code = ascii {off:+#x}")
            print("   ", prog[max(0, addr - 16):addr + 64].hex(" "))
