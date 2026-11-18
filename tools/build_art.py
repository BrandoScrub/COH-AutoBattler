"""Make the game's unit art with the pinned artkit: every unit data/units.json names, drawn by models/.

  python3 tools/build_art.py                     every unit (about an hour on two processes)
  python3 tools/build_art.py us_heavy de_scout   only units whose key contains one of these
  python3 tools/build_art.py -j 4 ...            processes to use (default 2)

Each unit is exported through artkit.export.Exporter into a scratch folder, then merged into art/: its old pages are
replaced, assets.json updated. A full build also drops units data no longer names. Then art/crew_layout.json is
rewritten. data/units.json and models/ must agree: a key with no model, or a model with no data entry, is an error.
A unit's "headings" comes from its data entry. Machines are exported only if their check() is empty."""
import json, os, shutil, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
ART = os.path.join(ROOT, 'art')
DATA = json.load(open(os.path.join(ROOT, 'data', 'units.json')))


def worker(out, keys):
    from artkit.style import Style
    from artkit.export import Exporter
    from models import roster
    cat = roster.catalogue()
    ex = Exporter(Style.load(os.path.join(ROOT, 'styles', 'ww2')), out, log=lambda *a: None)
    for k in keys:
        t = time.time(); e = DATA[k]; c = cat[k]
        if c['kind'] == 'man':
            u, clips = c['make'](); u.headings = e['headings']; ex.rig(k, u, clips)
        else:
            rig, clips = c['make'](h=e['headings'])
            issues = rig.m.check()
            if issues: sys.exit(f'{k}: Machine.check() is not empty: {issues[:3]}')
            ex.rig(k, rig, clips)
        print(f'  {k}: {e["name"]} ({time.time() - t:.0f}s)', flush=True)
    ex.save(pack=True)


def merge(srcs, full):
    A = json.load(open(os.path.join(ART, 'assets.json'))) if os.path.exists(os.path.join(ART, 'assets.json')) else {}
    drop = lambda key: [os.remove(os.path.join(ART, p)) for p in A.pop(key, {}).get('pack', []) if os.path.exists(os.path.join(ART, p))]
    for src in srcs:
        new = json.load(open(os.path.join(src, 'assets.json')))
        for k, v in new.items():
            drop(k)
            for p in v.get('pack', []):
                os.makedirs(os.path.dirname(os.path.join(ART, p)), exist_ok=True); shutil.copy(os.path.join(src, p), os.path.join(ART, p))
            A[k] = v
    if full:
        for k in [k for k in A if k not in DATA]: drop(k); print('  dropped', k, '(not in data/units.json)')
    A = {k: A[k] for k in list(DATA) + sorted(set(A) - set(DATA)) if k in A}      # stable: data/units.json order
    json.dump(A, open(os.path.join(ART, 'assets.json'), 'w'), separators=(',', ':'))
    return A


def main(args):
    jobs = 2
    if '-j' in args: i = args.index('-j'); jobs = int(args[i + 1]); args = args[:i] + args[i + 2:]
    from models import roster
    cat = roster.catalogue()
    missing, extra = sorted(set(DATA) - set(cat)), sorted(set(cat) - set(DATA))
    if missing: sys.exit(f'data/units.json names units models/ cannot draw: {missing}')
    if extra: sys.exit(f'models/ draws units data/units.json does not name: {extra}')
    keys = [k for k in DATA if not args or any(a in k for a in args)]
    if not keys: sys.exit('no unit key matches ' + ' '.join(args))
    keys.sort(key=lambda k: -DATA[k]['headings'] * (3 if DATA[k]['kind'] == 'vehicle' else 1))   # big ones first, spread over workers
    parts = [keys[i::jobs] for i in range(jobs) if keys[i::jobs]]
    print(f'exporting {len(keys)} units on {len(parts)} processes')
    tmp = tempfile.mkdtemp(prefix='build_art_'); procs = []
    for i, part in enumerate(parts):
        procs.append(subprocess.Popen([sys.executable, __file__, '--worker', os.path.join(tmp, str(i))] + part))
    if any(p.wait() for p in procs): sys.exit('an export failed; art/ is unchanged')
    A = merge([os.path.join(tmp, str(i)) for i in range(len(parts))], full=not args)
    shutil.rmtree(tmp)
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'layout.py'), ART], check=True)
    print(f'art/: {len(A)} units')


if __name__ == '__main__':
    if sys.argv[1:2] == ['--worker']: worker(sys.argv[2], sys.argv[3:])
    else: main(sys.argv[1:])
