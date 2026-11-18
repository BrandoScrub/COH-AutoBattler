"""Model review and OBJ files: python3 tools/build.py <out>. Grey sheets (close, three views) of every vehicle and squad, a play-size line-up,
base-colour rosters, and an OBJ + MTL per model (metres, y up)."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
import numpy as np
from PIL import Image
from artkit.core.geom import Geometry
from render import mats, shot, turn, sheet, GREY
from models import us_vehicles, de_vehicles, us_vehicles2, de_vehicles2, infantry

COL = {
 'us': dict(base=(104, 108, 68), table=dict(steel=(62, 64, 60), rubber=(40, 40, 40), tunic=(138, 128, 88), trousers=(120, 110, 76), puttee=(160, 148, 108),
            helmet=(74, 82, 54), canvas=(150, 138, 96), leather=(100, 68, 42), boot=(64, 46, 34), skin=(214, 168, 132), wood=(112, 72, 42), brass=(120, 108, 70),
            tube=(74, 82, 54), tank=(74, 82, 54), hazard=(74, 82, 54), blanket=(120, 112, 80), hose2=(40, 36, 34), shroud=(52, 56, 62), hide=(100, 68, 42), pilot=(255, 170, 60))),
 'de': dict(base=(182, 156, 102), table=dict(steel=(84, 80, 70), rubber=(44, 44, 44), tunic=(108, 116, 104), trousers=(102, 108, 100), puttee=(102, 108, 100),
            helmet=(72, 80, 76), canvas=(128, 124, 100), leather=(52, 42, 36), boot=(38, 34, 32), skin=(214, 168, 132), wood=(112, 72, 42), brass=(110, 104, 84),
            tube=(170, 146, 98), tank=(90, 96, 90), hazard=(90, 96, 90), blanket=(110, 110, 104), hose2=(40, 36, 34), shroud=(52, 56, 62), hide=(52, 42, 36), pilot=(255, 170, 60))),
}
VEH = {'us': us_vehicles.ALL + us_vehicles2.ALL, 'de': de_vehicles.ALL + de_vehicles2.ALL}
NAME = {'us': 'American', 'de': 'German'}


def models(side):
    """[(label, geometry, is_figure)] for a side: six vehicles, then five squads."""
    out = [(f'{role}: {name}', fn().geometry(), False) for role, name, fn in VEH[side]]
    out += [(name, Geometry.join([g for _, g in ms]), True) for name, ms in infantry.squads(side)]
    return out


def write_obj(path, g, colours, base):
    """Plain OBJ + MTL: one material per artkit material name, flat colours; metres, y up."""
    names = sorted(set(g.mat)); mtl = os.path.splitext(path)[0] + '.mtl'
    with open(mtl, 'w') as f:
        for n in names:
            c = np.array(colours.get(n.split('@')[0], base)) / 255
            f.write(f'newmtl {n}\nKd {c[0]:.3f} {c[1]:.3f} {c[2]:.3f}\n')
    with open(path, 'w') as f:
        f.write(f'mtllib {os.path.basename(mtl)}\n')
        P = g.P.reshape(-1, 3) / 55.0
        for x, y, z in P: f.write(f'v {x:.4f} {z:.4f} {-y:.4f}\n')
        for n in names:
            f.write(f'usemtl {n}\n')
            for i in np.nonzero(g.mat == n)[0]: f.write(f'f {3 * i + 1} {3 * i + 2} {3 * i + 3}\n')


def main(out):
    os.makedirs(out + '/obj', exist_ok=True)
    play = []
    for side in ('us', 'de'):
        C = COL[side]; cm = mats(C['base'], C['table']); ms = models(side)
        # grey blockouts, close, three views
        nv = len(VEH[side])
        for tag, part in (('vehicles', ms[:nv]), ('infantry', ms[nv:])):
            ims, labs = [], []
            for label, g, fig in part:
                for hd in (300, 20, 160):
                    ims.append(shot(turn(g, hd), 1.2 if fig else 1.0, GREY, None if fig else 'L')); labs.append(f'{label}, heading {hd}')
            sheet(ims, labs, cols=3).save(f'{out}/{side}_{tag}_blockout.png')
        # base colours, one view each
        ims = [shot(turn(g, 330 if not fig else 20), 1.0 if fig else 0.8, cm, None if fig else 'L') for _, g, fig in ms]
        sheet(ims, [l for l, _, _ in ms], cols=2).save(f'{out}/{side}_roster_colour.png')
        play += [shot(turn(g, 330), 0.4, cm, None if fig else 'L') for _, g, fig in ms]
        for label, g, _ in ms:
            key = side + '_' + label.split(': ')[-1].lower().replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
            write_obj(f'{out}/obj/{key}.obj', g, C['table'], C['base'])
        print(side, 'done')
    sheet(play, None, cols=6, zoom=2).save(f'{out}/play_size_lineup.png')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'dist')
