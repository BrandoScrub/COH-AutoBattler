"""Shared builders for the WW2 unit set (game side; uses artkit, changes nothing in it).
Metres in, units out (55 units a metre, DESIGN_METHOD.md step 4). x: rear (0) to front, y: across (0 = centre line,
+y = the vehicle's left), z: up. Everything is an artkit.machine.Machine part with a `why` and a mount."""
import math
from artkit import shapes as sh
from artkit.machine import Machine

M = 55.0
ACROSS, UP = (0, 1, 0), (0, 0, 1)


def P(x, y, z): return (x * M, y * M, z * M)


def solid(pts, mat='hull', smooth=False):
    g = sh.convex([P(*p) for p in pts], mat)
    return sh.soften(g) if smooth else g


def across(xz, y0, y1): return [(x, y, z) for x, z in xz for y in (y0, y1)]
def slab(x0, x1, y0, y1, z0, z1, mat='hull'): return solid([(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], mat)
def rod(p0, p1, r, mat='steel', seg=10): return sh.cyl(P(*p0), P(*p1), r * M, mat, seg=seg)
def disc(x, y, z0, z1, r, mat='steel', seg=14): return sh.cyl(P(x, y, z0), P(x, y, z1), r * M, mat, seg=seg)
def wheel(x, y, z, r, w, mat='rubber', seg=16): return sh.cyl(P(x, y - w / 2, z), P(x, y + w / 2, z), r * M, mat, seg=seg)


def _upper_chain(pts):
    """Indices of pts [(x, top)] on the upper convex chain, x descending (front to rear), ends excluded."""
    order = sorted(range(len(pts)), key=lambda i: -pts[i][0]); ch = []
    for i in order:
        while len(ch) >= 2:
            (ax, az), (bx, bz), (cx, cz) = pts[ch[-2]], pts[ch[-1]], pts[i]
            if (bx - ax) * (cz - az) - (bz - az) * (cx - ax) <= 1e-9: ch.pop()     # b is not above the line a-c
            else: break
        ch.append(i)
    return ch[1:-1]


def running_gear(m, on, lw, ty, tw, wheels, wr, front, rear, rollers=(), rr=0.09, rz=None, drive='front',
                 interleave=False, belly=0.42, band=0.07, tooth=0.04, pitch=0.16, hub=0.42):
    """Tracks both sides. lw: half-width of the tub the gear is mounted on; ty, tw: track centre line and width;
    wheels: road wheel x positions, wr their radius; front / rear: (x, z, r) of the end wheels; drive: which end has
    the sprocket; rollers: return roller x positions (radius rr, centre height rz); interleave: road wheels in two
    rows, overlapping in side view. Returns the track's highest point (the sponson floor must be above it)."""
    wz = band + tooth + wr
    for side, s in ((1, 'l'), (-1, 'r')):
        y = side * ty
        sp = lambda a, b: sorted((side * a, side * b))
        ends = {}
        for tag, (ex, ez, er) in (('front', front), ('rear', rear)):
            kind = 'sprocket' if tag == drive else 'idler'
            y0, y1 = sp(lw - 0.04, ty - tw * 0.3)
            m.add(f'{kind}_mount_{s}', sh.cyl(P(ex, y0, ez), P(ex, y1, ez), 0.5 * er * M, 'hull', seg=12),
                  ('final-drive housing: carries the drive out of the hull to the sprocket' if kind == 'sprocket'
                   else 'idler axle housing: holds the idler out from the hull and tensions the track'), on=on)
            m.add(f'{kind}_{s}', wheel(ex, y, ez, er, tw * 0.66, 'steel', 18),
                  (f'{tag} drive sprocket: pulls the track round' if kind == 'sprocket' else f'{tag} idler: guides the track back'),
                  on=f'{kind}_mount_{s}', turns=(P(ex, y, ez), ACROSS))
            m.add(f'{kind}_hub_{s}', sh.cyl(P(ex, y, ez), P(ex, y + side * (tw * 0.33 + 0.05), ez), 0.45 * er * M, 'steel', seg=12),
                  'hub on the outer face: an axle end, so it reads as a wheel', on=f'{kind}_{s}', turns=(P(ex, y, ez), ACROSS))
            ends[tag] = f'{kind}_{s}'
        names = []
        for k, x in enumerate(wheels):
            off = tw * 0.2 * (1 if k % 2 else -1) if interleave else 0.0
            w = tw * 0.34 if interleave else tw * 0.66
            yc = side * (ty + off)
            y0, y1 = sp(lw - 0.04, ty + off - w / 2 + 0.03)
            m.add(f'arm_{s}{k}', slab(x - 0.05, x + 0.05, y0, y1, wz - 0.05, max(wz + 0.05, belly + 0.06), 'steel'),
                  'suspension arm: holds the wheel axle out from the hull side (inboard, mostly hidden: kept so the wheel is mounted)',
                  on=on, small_ok=True)
            m.add(f'wheel_{s}{k}', wheel(x, yc, wz, wr, w), 'road wheel: carries the weight onto the track',
                  on=f'arm_{s}{k}', turns=(P(x, yc, wz), ACROSS))
            m.add(f'hub_{s}{k}', sh.cyl(P(x, yc, wz), P(x, yc + side * (w / 2 + 0.04), wz), hub * wr * M, 'steel', seg=12),
                  'wheel hub: a wheel, not a puck', on=f'wheel_{s}{k}', turns=(P(x, yc, wz), ACROSS))
            names.append((x, f'wheel_{s}{k}'))
        tops = []
        if rollers:
            for k, x in enumerate(rollers):
                y0, y1 = sp(lw - 0.04, ty - tw * 0.25)
                m.add(f'roller_stub_{s}{k}', slab(x - 0.05, x + 0.05, y0, y1, rz - 0.05, rz + 0.05, 'steel'),
                      'stub axle for the return roller', on=on, small_ok=True)
                m.add(f'roller_{s}{k}', wheel(x, y, rz, rr, tw * 0.5, 'steel', 12), 'return roller: holds up the top run of the track',
                      on=f'roller_stub_{s}{k}', turns=(P(x, y, rz), ACROSS))
            tops = [(x, rz, rr, f'roller_{s}{k}') for k, x in sorted(enumerate(rollers), key=lambda kv: -kv[1])]
        else:                                        # no rollers: the top run lies on the wheels that stand proud
            pts = [(front[0], front[1] + front[2])] + [(x, wz + wr) for x in wheels] + [(rear[0], rear[1] + rear[2])]
            tops = [(wheels[i - 1], wz, wr, '') for i in _upper_chain(pts)]
        names.sort()
        circ = ([(x * M, wz * M, wr * M) for x, _ in names] + [(front[0] * M, front[1] * M, front[2] * M)]
                + [(x * M, z * M, r * M) for x, z, r, _ in tops] + [(rear[0] * M, rear[1] * M, rear[2] * M)])
        wraps = [n for _, n in names] + [ends['front']] + [n for *_, n in tops] + [ends['rear']]
        y0, y1 = sp(ty - tw / 2, ty + tw / 2)
        m.belt(f'track_{s}', circ, y0 * M, y1 * M, band * M, 'rubber', teeth=(pitch * M, 0.07 * M, tooth * M),
               why='track: one band round sprocket, road wheels and idler; its link edges give it teeth',
               on=ends[drive], wraps=wraps)
    return max([front[1] + front[2], rear[1] + rear[2], wz + wr] + [z + r for _, z, r, _ in tops]) + band + tooth


def ring(m, rx, roof, r, on='upper_hull', y=0.0):
    m.add('ring_guard', sh.lathe([(r * M, 0), (r * M, 0.06 * M), (0, 0.06 * M)], 'hull', n=24).move(*P(rx, y, roof)),
          'raised collar round the turret ring: the turret sits in it, it does not float', on=on)
    return roof + 0.06


def cast_turret(m, rx, tz, profile, sx=1.0, why='cast turret: rounded because cast', y=0.0):
    body = sh.lathe([(r * M, z * M) for r, z in profile], 'hull', n=24).scaled(sx, 1.0, 1.0)
    m.add('turret', sh.soften(body).move(*P(rx, y, tz)), why, on='ring_guard', turns=(P(rx, y, tz), UP))


def plate_turret(m, rx, tz, a, b, c, h, inset, why='welded plate turret: flat faces with chamfered corners', y=0.0):
    """Octagonal plan (half-length a, half-width b, corner cut c), walls leaning in by `inset` at the roof."""
    plan = lambda a, b: [(sx * u, sy * v) for u, v in ((a, b - c), (a - c, b)) for sx in (1, -1) for sy in (1, -1)]
    pts = [(rx + u, y + v, tz) for u, v in plan(a, b)] + [(rx + u, y + v, tz + h) for u, v in plan(a - inset, b - inset)]
    m.add('turret', solid(pts), why, on='ring_guard', turns=(P(rx, y, tz), UP))


def gun(m, p0, length, r, on, brake=None, why='main gun: the long line that says where it points'):
    """Barrel from p0 along +x. brake: (radius, length) of a muzzle brake."""
    x, y, z = p0
    m.add('gun', rod(p0, (x + length, y, z), r, seg=10), why, on=on, small_ok=True)
    if brake:
        m.add('muzzle', rod((x + length - brake[1], y, z), (x + length, y, z), brake[0], seg=10),
              'muzzle brake: the fat end of the barrel, and the reason it reads at play size', on='gun')
    return (x + length, y, z)


def axle(m, name, x, r, w, ty, on='chassis', z=None, why='axle beam: carries the wheels and the drive'):
    z = r if z is None else z
    m.add(name, rod((x, -ty + w / 2, z), (x, ty - w / 2, z), 0.06), why, on=on, small_ok=True)
    for side, s in ((1, 'l'), (-1, 'r')):
        y = side * ty
        m.add(f'{name}_wheel_{s}', wheel(x, y, z, r, w), 'road wheel with a tyre: what it drives on', on=name, turns=(P(x, y, z), ACROSS))
        m.add(f'{name}_hub_{s}', sh.cyl(P(x, y, z), P(x, y + side * (w / 2 + 0.04), z), 0.42 * r * M, 'steel', seg=12),
              'wheel hub and rim: a wheel, not a puck', on=f'{name}_wheel_{s}', turns=(P(x, y, z), ACROSS))


def howitzer(name, wr, wy, ww, blen, br, elev, shield_h, trail, brake=None, recuperator=False):
    """A towed field howitzer on a split-trail carriage, facing +x, barrel raised `elev` degrees: the raised short fat
    barrel is what tells it from an anti-tank gun. wr, wy, ww: wheel radius, centre line, width. blen, br: barrel
    length ahead of the trunnions and radius. recuperator: a second cylinder over the barrel (the American mark)."""
    m = Machine(name)
    e = math.radians(elev); d = (math.cos(e), 0.0, math.sin(e)); n = (-math.sin(e), 0.0, math.cos(e))
    top = wr + 0.24; T = (0.0, 0.0, top + 0.20)
    at = lambda a, b=0.0: (T[0] + a * d[0] + b * n[0], 0.0, T[2] + a * d[2] + b * n[2])
    m.add('axle', rod((0, -wy + ww / 2, wr), (0, wy - ww / 2, wr), 0.07), 'axle: carries the piece on its wheels', small_ok=True)
    m.add('saddle', slab(-0.10, 0.31, -0.40, 0.40, wr - 0.08, top, 'steel'), 'saddle on the axle: carries trunnions, shield and trail hinges', on='axle')
    m.add('trunnion', slab(-0.12, 0.12, -0.17, 0.17, top, top + 0.32, 'steel'), 'trunnion block: the barrel pitches on it, which is how a howitzer lobs', on='saddle')
    m.add('breech', rod(at(-0.58), at(-0.14), 0.15), 'breech ring: the heavy end behind the trunnions', on='trunnion')
    m.add('gun', rod(at(-0.14), at(blen), br), 'short fat barrel, raised: the line that says indirect fire', on='trunnion', small_ok=True)
    if brake: m.add('muzzle', rod(at(blen - brake[1]), at(blen), brake[0]), 'muzzle brake: the fat tip', on='gun')
    if recuperator: m.add('recuperator', rod(at(0.0, 0.175), at(blen * 0.62, 0.175), 0.07), 'recoil cylinder riding over the barrel: the mark of this piece', on='trunnion', small_ok=True)
    for sd, s in ((1, 'l'), (-1, 'r')):
        m.add(f'wheel_{s}', wheel(0, sd * wy, wr, wr, ww), 'carriage wheel', on='axle', turns=(P(0, sd * wy, wr), ACROSS))
        m.add(f'hub_{s}', sh.cyl(P(0, sd * wy, wr), P(0, sd * (wy + ww / 2 + 0.04), wr), 0.4 * wr * M, 'steel', seg=12), 'hub', on=f'wheel_{s}', turns=(P(0, sd * wy, wr), ACROSS))
        y0, y1 = sorted((sd * 0.19, sd * (wy - ww / 2 - 0.04)))
        m.add(f'shield_{s}', slab(0.26, 0.31, y0, y1, wr - 0.05, shield_h), 'shield half: split so the barrel can rise between', on='saddle')
        m.add(f'trail_{s}', rod((-0.08, sd * 0.32, wr), (-trail, sd * 0.90, 0.075), 0.07), 'trail: spreads to brace the recoil', on='saddle', small_ok=True)
        y0, y1 = sorted((sd * 0.76, sd * 1.04))
        m.add(f'spade_{s}', slab(-trail - 0.14, -trail + 0.05, y0, y1, 0.0, 0.26, 'steel'), 'spade: digs in against the recoil', on=f'trail_{s}')
    return m
