"""Search the interleaved dfeveron program for a text string and show its surroundings.
Usage: python tools/find_text.py <romset.zip> "TEXT" """
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import patch

files = patch.read_input(sys.argv[1])
u33, u34 = files["cv01-u33.bin"], files["cv01-u34.bin"]
prog = bytearray(len(u33) * 2)
prog[0::2], prog[1::2] = u34, u33
needle = sys.argv[2].encode("latin-1")
i = prog.find(needle)
while i >= 0:
    s = max(0, i - 32)
    print(f"{i:06x}: {prog[s:i + len(needle) + 48].hex(' ')}")
    print(f"        {bytes(c if 32 <= c < 127 else 46 for c in prog[s:i + len(needle) + 48]).decode()}")
    i = prog.find(needle, i + 1)
