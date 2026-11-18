"""Each side's paint and cloth: figure materials registered as <side>_<name>, and the renaming that puts them on."""
import numpy as np
from artkit.figure import material

# ---- figure materials per side (registered in the figure registry under <side>_<name>)
CLOTH = {
 'us': dict(tunic=((138, 128, 88), 'wool'), trousers=((120, 110, 76), 'wool'), puttee=((160, 148, 108), 'canvas'), helmet=((74, 82, 54), 'metal'),
            canvas=((150, 138, 96), 'canvas'), leather=((100, 68, 42), 'leather'), boot=((64, 46, 34), 'leather'), blanket=((120, 112, 80), 'wool'),
            brass=((120, 108, 70), 'metal'), tube=((74, 82, 54), 'metal'), tank=((74, 82, 54), 'metal'), hazard=((74, 82, 54), 'metal'), hide=((100, 68, 42), 'leather')),
 'de': dict(tunic=((108, 116, 104), 'wool'), trousers=((102, 108, 100), 'wool'), puttee=((102, 108, 100), 'wool'), helmet=((72, 80, 76), 'metal'),
            canvas=((128, 124, 100), 'canvas'), leather=((52, 42, 36), 'leather'), boot=((38, 34, 32), 'leather'), blanket=((110, 110, 104), 'wool'),
            brass=((110, 104, 84), 'metal'), tube=((170, 146, 98), 'metal'), tank=((90, 96, 90), 'metal'), hazard=((90, 96, 90), 'metal'), hide=((52, 42, 36), 'leather')),
}
for _s, _t in CLOTH.items():
    for _n, (_c, _k) in _t.items(): material(f'{_s}_{_n}', _c, _k)


def _rename(g, table):
    return g.set(mat=np.array([table.get(m, m) for m in g.mat], object))


def dress(u, side):
    """A trooper's parts in his side's materials."""
    t = {n: f'{side}_{n}' for n in CLOTH[side]}
    u.parts = [(b, _rename(g, t), n, w) for b, g, n, w in u.parts]
    return u


def paint(m, side):
    """A machine in its side's paint (hull plate, stowage); steel, rubber and wood are shared."""
    t = {'hull': f'{side}_hull', 'canvas': f'{side}_canvas'}
    for p in m.parts.values(): p.geom = _rename(p.geom, t)
    return m


