"""Pin the art engine into this game at one commit:  python3 tools/update_artkit.py <path to a Game-Engine-System-Design checkout>

Replaces artkit/ whole with the checkout's artkit/ and writes artkit/VENDORED.json:
  {"engine": "BrandoScrub/Game-Engine-System-Design", "commit": "<sha>", "dirty": false, "files": {"<path>": "<sha256>"}}
(the format gamekit's kits.js uses, so its tools read it too).  python3 tools/update_artkit.py --verify  checks the copy.
Never edit artkit/ here: change the engine, then update. After an update: tools/check.py, re-export what you mean to, commit."""
import hashlib, json, os, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, 'artkit'); ENGINE = 'BrandoScrub/Game-Engine-System-Design'
SKIP_DIRS = {'__pycache__', 'out', '.git', 'node_modules'}
skip_file = lambda n: n in ('.DS_Store', 'VENDORED.json') or n.endswith('.pyc')


def walk(root):
    out = []
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
        out += [os.path.relpath(os.path.join(d, f), root).replace(os.sep, '/') for f in sorted(files) if not skip_file(f)]
    return sorted(out)


def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def git(d, *a):
    try: return subprocess.run(['git', '-C', d, *a], capture_output=True, text=True, check=True).stdout.strip()
    except Exception: return None


def verify():
    vp = os.path.join(DST, 'VENDORED.json')
    if not os.path.exists(vp): return ['artkit/VENDORED.json missing']
    v = json.load(open(vp)); bad = []
    for rel, h in v['files'].items():
        p = os.path.join(DST, rel)
        if not os.path.exists(p): bad.append(f'artkit/{rel} missing')
        elif sha(p) != h: bad.append(f'artkit/{rel} edited in the game (change it in the engine, then update)')
    bad += [f'artkit/{r} not part of the pinned copy' for r in walk(DST) if r not in v['files']]
    return bad


def update(engine):
    src = os.path.join(os.path.abspath(engine), 'artkit')
    if not os.path.isdir(src) or os.path.exists(os.path.join(src, 'VENDORED.json')):
        sys.exit(f'{engine} is not an engine checkout (needs artkit/ and no artkit/VENDORED.json)')
    commit = git(engine, 'rev-parse', 'HEAD') or 'unknown'
    st = git(engine, 'status', '--porcelain', '--', 'artkit'); dirty = st is None or len(st) > 0
    shutil.rmtree(DST, ignore_errors=True); files = {}
    for rel in walk(src):
        os.makedirs(os.path.dirname(os.path.join(DST, rel)), exist_ok=True)
        shutil.copy2(os.path.join(src, rel), os.path.join(DST, rel)); files[rel] = sha(os.path.join(DST, rel))
    json.dump(dict(engine=ENGINE, commit=commit, dirty=dirty, files=files), open(os.path.join(DST, 'VENDORED.json'), 'w'), indent=1)
    open(os.path.join(DST, 'VENDORED.json'), 'a').write('\n')
    print(f"artkit now at {commit[:7]}{' (uncommitted engine changes)' if dirty else ''}: {len(files)} files")


if __name__ == '__main__':
    if len(sys.argv) != 2: sys.exit(__doc__)
    if sys.argv[1] == '--verify':
        bad = verify(); print('\n'.join(bad) or 'artkit matches its VENDORED.json'); sys.exit(1 if bad else 0)
    update(sys.argv[1])
