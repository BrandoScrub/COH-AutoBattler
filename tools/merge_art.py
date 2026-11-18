"""Merge exporter output folders into one art folder: python3 tools/merge_art.py <out> <in> [<in> ...] (tools/build_art.py does this for you)"""
import sys, os, json, shutil
out = sys.argv[1]; os.makedirs(out, exist_ok=True); A = {}
for src in sys.argv[2:]:
    A.update(json.load(open(os.path.join(src, 'assets.json'))))
    for root, _, files in os.walk(src):
        for f in files:
            if f == 'assets.json': continue
            d = os.path.join(out, os.path.relpath(root, src)); os.makedirs(d, exist_ok=True); shutil.copy(os.path.join(root, f), d)
json.dump(A, open(os.path.join(out, 'assets.json'), 'w'), separators=(',', ':'))
print(len(A), 'units in', out)
