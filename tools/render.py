"""Review sheets (DESIGN_METHOD.md step 7): grey blockouts at play size and close, several headings, vehicle camera."""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
import numpy as np, importlib
from artkit.style import Style
from artkit.core.materials import Materials, Material
from artkit.core.light import Rules
from artkit.core.geom import RZ
from artkit.core.space import Camera
from artkit.sprite import picture, sheet

CAM = Camera.from_pack({'view': 'iso', 'plates': False})
LINES = Rules(ink_width=0.75, ink_inner=0.5, ink_step=4, ink_crease=35, ink_crease_width=0.35)
ST = Style.load('frontier_outpost')
DARK = ('steel', 'dark', 'shroud', 'boot', 'leather'); BLACK = ('rubber',)

def mats(base=(170, 170, 170), table=None):
    c = lambda v: Material(np.broadcast_to(np.array(v, np.float32) / 255, (8, 8, 3)).copy(), 'tile', 0.05)
    table = table or {}
    def fb(n):
        n = n.split('@')[0]
        if n in table: return c(table[n])
        if n in BLACK: return c((70, 70, 70))
        if n in DARK: return c((110, 110, 110))
        return c(base)
    return Materials(fallback=fb)

GREY = mats()

def turn(g, deg):
    lo, hi = g.bounds(); c = (np.asarray(lo) + np.asarray(hi)) / 2; c[2] = 0
    return g.about(c, RZ(deg))

def shot(g, scale, m=GREY, lines='L'): return picture(g, ST, scale=scale, mats=m, lighting=LINES if lines == 'L' else lines, camera=CAM)[0]

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for mod in sys.argv[2:]:
        V = importlib.import_module('models.' + mod)
        ims, labs = [], []
        for role, name, fn in V.ALL:
            m = fn(); has_t = 'turret' in m.parts
            for hd, tu in ((300, 0), (20, 70 if has_t else 0), (160, 0)):
                g = turn(m.geometry({'turret': tu} if tu else None), hd)
                ims.append(shot(g, 1.0)); labs.append(f'{name}  hull {hd}' + (f' gun {tu}' if tu else ''))
        sheet(ims, labs, cols=3).save(f'{out}/{mod}_close.png')
        ims = [shot(turn(fn().geometry(), hd), 0.4) for _, _, fn in V.ALL for hd in (300, 45, 135, 225)]
        sheet(ims, None, cols=8, zoom=2).save(f'{out}/{mod}_play.png')
        print('wrote', mod)
