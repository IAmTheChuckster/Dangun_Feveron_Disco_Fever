"""Disassemble the interleaved dfeveron program (68000) with capstone.
Usage: python tools/disasm.py <romset.zip|prog.bin> <start hex> <length hex>"""
import os, sys
import capstone
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import patch

src = sys.argv[1]
if src.endswith(".zip"):
    f = patch.read_input(src)
    prog = bytearray(0x100000); prog[0::2], prog[1::2] = f["cv01-u34.bin"], f["cv01-u33.bin"]
else:
    prog = open(src, "rb").read()
start, length = int(sys.argv[2], 16), int(sys.argv[3], 16)
md = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_BIG_ENDIAN | capstone.CS_MODE_M68K_000)
for i in md.disasm(bytes(prog[start:start + length]), start):
    print(f"{i.address:06x}  {i.bytes.hex():20} {i.mnemonic} {i.op_str}")
