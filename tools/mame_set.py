"""Turn a dfeveronfever.zip into a MAME-loadable folder <outdir>/dfeveron/ (original file names).
Usage: python tools/mame_set.py dfeveronfever.zip <outdir>"""
import os, sys, zipfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import patch

back = {v: k for k, v in patch.OUT_NAMES.items()}
d = os.path.join(sys.argv[2], "dfeveron")
os.makedirs(d, exist_ok=True)
with zipfile.ZipFile(sys.argv[1]) as z:
    for n in z.namelist():
        with open(os.path.join(d, back.get(n, n)), "wb") as f:
            f.write(z.read(n))
print("wrote", d)
