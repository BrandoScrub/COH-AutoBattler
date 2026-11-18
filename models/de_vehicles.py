"""German vehicles, 1941-45: blockouts (primary and secondary masses), one Machine each, check() empty.
Briefs follow artkit/DESIGN_METHOD.md; real dimensions x 55. No national markings: those are decals for the pack."""
from artkit import shapes as sh
from artkit.machine import Machine
from .kit import *


def kradschuetzen():
    """Brief
    is:       heavy motorcycle with a driven sidecar (BMW R75 type), rider and gunner (figures separate), MG on the sidecar
    does:     the scout: fastest thing on a road, sees first, dies to anything
    gameplay: 1 x 1 tile, no armour; must read as a bike plus a boat-shaped sidecar, and which way it drives
    power:    flat-twin engine low in the frame, its cylinders sticking out each side; shaft drive to the rear wheel
    moves:    three wheels: two in line, one on the sidecar; front wheel steers in a fork
    built:    tube frame; sidecar tub on two cross tubes; fuel tank over the engine; machine gun on a post on the tub's nose
    references: BMW R75 / Zündapp KS750 survivors (boxer cylinders, big tank, spare wheel on the sidecar tail)
    read_at_play_size: two wheels in line with a tank between them, a boat beside it with a gun on its nose
    """
    m = Machine('German scout motorcycle and sidecar')
    R, W, BY = 0.34, 0.12, 0.40
    m.add('frame', slab(0.78, 1.50, 0.32, 0.48, 0.28, 0.62, 'steel'), 'tube frame: engine hangs in it, everything else bolts to it')
    for nm, y0, y1 in (('stay_a', 0.47, 0.52), ('stay_b', 0.28, 0.33)):
        m.add(nm, slab(0.36, 0.80, y0, y1, 0.29, 0.40, 'steel'), 'rear stay: holds the rear axle either side of the wheel', on='frame', small_ok=True)
    m.add('rear_wheel', wheel(0.40, BY, R, R, W), 'driven rear wheel', on='stay_a', turns=(P(0.40, BY, R), ACROSS))
    m.add('engine', slab(0.95, 1.30, 0.14, 0.66, 0.28, 0.52, 'steel'), 'flat-twin engine: a cylinder out each side, the mark of this bike', on='frame')
    m.add('tank', solid([(x, y, z) for x, w, z0, z1 in ((0.95, 0.10, 0.62, 0.80), (1.25, 0.13, 0.62, 0.86), (1.45, 0.09, 0.62, 0.82)) for y in (BY - w, BY + w) for z in (z0, z1)], smooth=True),
          'fuel tank over the engine: the biggest mass on the bike', on='frame')
    m.add('seat', slab(0.60, 0.95, 0.30, 0.50, 0.62, 0.74, 'steel'), 'saddle: the human-scale cue', on='frame')
    m.add('head', slab(1.45, 1.62, 0.31, 0.49, 0.62, 0.88, 'steel'), 'steering head: the fork turns in it', on='frame')
    for nm, y in (('fork_l', 0.50), ('fork_r', 0.30)):
        m.add(nm, rod((1.58, y, 0.84), (1.95, y, R), 0.035), 'fork leg: carries the front axle and steers it', on='head', small_ok=True)
    m.add('front_wheel', wheel(1.95, BY, R, R, W), 'front wheel in the fork', on='fork_l', turns=(P(1.95, BY, R), ACROSS))
    m.add('handlebar', rod((1.52, 0.12, 0.92), (1.52, 0.68, 0.92), 0.03), 'handlebar: wide, so it reads as a motorcycle from above', on='head', small_ok=True)
    m.add('headlamp', rod((1.62, BY, 0.78), (1.76, BY, 0.78), 0.085), 'headlamp: marks the front', on='head')
    for nm, x in (('cross_tube_a', 0.82), ('cross_tube_b', 1.35)):
        m.add(nm, slab(x, x + 0.10, -0.62, 0.32, 0.30, 0.40, 'steel'), 'cross tube: ties the sidecar to the bike frame', on='frame', small_ok=True)
    tub = [(0.45, y, z) for y in (-0.58, -0.04) for z in (0.40, 0.80)] + [(1.75, y, z) for y in (-0.58, -0.04) for z in (0.40, 0.82)] + \
          [(2.12, y, z) for y in (-0.44, -0.18) for z in (0.52, 0.72)]
    m.add('sidecar', solid(tub, smooth=True), 'sidecar tub, boat-nosed: the gunner sits in it', on='cross_tube_a', contact=['cross_tube_b'])
    m.add('sidecar_wheel', wheel(0.87, -0.68, R, R, W), 'sidecar wheel (driven on this type)', on='cross_tube_a', turns=(P(0.87, -0.68, R), ACROSS))
    m.add('spare', sh.cyl(P(0.33, -0.31, 0.62), P(0.45, -0.31, 0.62), 0.27 * M, 'rubber', seg=16), 'spare wheel on the tub tail: marks the rear', on='sidecar')
    m.add('mg_post', slab(1.72, 1.84, -0.37, -0.25, 0.80, 0.96, 'steel'), 'gun post on the tub nose', on='sidecar', small_ok=True)
    m.add('mg', rod((1.40, -0.31, 1.0), (2.40, -0.31, 1.0), 0.035), 'machine gun: the line that says it is armed', on='mg_post', small_ok=True)
    from .infantry import crewman, SIT, RIDE
    m.add('rider', crewman('de', RIDE, (54, 22, 14), L=(83, 34, 50), R=(83, 10, 50)), 'rider, leaning to the bars: without him the bike does not read',
          on='seat', contact=['frame', 'engine', 'tank', 'handlebar'], convex=False, small_ok=True)
    m.add('gunner', crewman('de', SIT, (58, -17, 21), L=(78, -14, 55), R=(77, -20, 54)), 'gunner in the sidecar behind the machine gun',
          on='sidecar', contact=['mg', 'cross_tube_a', 'cross_tube_b'], convex=False, small_ok=True)
    return m


def sdkfz222():
    """Brief
    is:       4x4 light armoured car (Sd.Kfz. 222), crew 3, 20 mm autocannon in a low open turret
    does:     armoured recon: shreds infantry and scout cars, runs from tanks
    gameplay: 1 x 2 tiles, thin armour, turret turns 360; hull and gun headings both read
    power:    engine at the rear; drive and steering on all four wheels
    moves:    four big wheels at the corners; turret on a ring
    built:    faceted welded hull: narrow between the wheels, widest just above them, narrowing again to the roof
              (every plate sloped: its signature); low many-sided turret with mesh grenade screens
    serviced: hatch on the rear deck; open turret top
    references: Sd.Kfz. 221/222 survivors (the diamond cross-section, wheels at the corners, short gun)
    read_at_play_size: a faceted coffin shape on four big wheels with a low turret and a short thin gun
    """
    m = Machine('German armoured car (Sd.Kfz. 222)')
    m.add('chassis', slab(0.50, 4.20, -0.35, 0.35, 0.38, 0.62, 'steel'), 'chassis and drive line')
    axle(m, 'rear_axle', 0.95, 0.45, 0.21, 0.81); axle(m, 'front_axle', 3.75, 0.45, 0.21, 0.81)
    m.add('lower_hull', solid(across([(0.35, 0.56), (0.35, 1.0), (4.60, 1.0), (4.60, 0.75), (4.30, 0.56)], -0.62, 0.62)), 'narrow tub between the wheels', on='chassis')
    m.add('mid_hull', solid([(x, y, z) for x in (1.50, 3.20) for y, z in ((-0.55, 0.50), (0.55, 0.50), (-0.95, 0.98), (0.95, 0.98))]),
          'the hull flares out between the axles: the lower half of the diamond section', on='lower_hull', contact=['chassis'])
    up = [(x, y, 0.96) for x in (0.30, 3.75) for y in (-0.95, 0.95)] + [(4.55, y, 0.98) for y in (-0.50, 0.50)] + [(x, y, 1.50) for x in (0.90, 3.20) for y in (-0.62, 0.62)]
    m.add('upper_hull', solid(up), 'upper hull: every plate sloped in to a narrow roof', on='lower_hull')
    m.add('deck_hatch', disc(1.30, 0, 1.50, 1.54, 0.22), 'engine deck hatch: access and human-scale cue', on='upper_hull')
    tz = ring(m, 2.45, 1.50, 0.60)
    plate_turret(m, 2.45, tz, 0.55, 0.55, 0.24, 0.36, 0.10, why='low many-sided open turret (closed in the blockout; mesh screens at detail)')
    m.add('mantlet', slab(2.45 + 0.45, 2.45 + 0.66, -0.20, 0.20, tz + 0.10, tz + 0.32, 'steel'), 'gun cradle front', on='turret')
    gun(m, (3.11, 0, tz + 0.22), 0.95, 0.035, 'mantlet', why='20 mm autocannon: short and thin, a line that carries')
    m.add('screens', solid([(2.45 + x, y, tz + 0.36) for x in (-0.40, 0.40) for y in (-0.42, 0.42)] + [(2.45 + x, 0, tz + 0.56) for x in (-0.36, 0.36)], 'steel'),
          'grenade screens over the open top, folded to a ridge: the mark of this car', on='turret')
    for sd, s in ((1, 'l'), (-1, 'r')):
        y0, y1 = sorted((sd * 0.62, sd * 0.70))
        m.add(f'spare_{s}' if sd > 0 else 'tool_box', (sh.cyl(P(2.35, 0.95, 1.16), P(2.35, 1.07, 1.16), 0.36 * M, 'rubber', seg=16) if sd > 0 else slab(1.70, 2.60, -1.06, -0.90, 1.00, 1.24)),
              ('spare wheel on the left flank' if sd > 0 else 'tool box on the right flank'), on='upper_hull')
    return m


def panzer2():
    """Brief
    is:       light tank (Panzer II Ausf. F), crew 3, 20 mm autocannon
    does:     tracked scout and infantry support; outclassed by any tank gun
    gameplay: 1 x 2 tiles; small and boxy; hull and turret headings read
    power:    engine at the rear, drive forward to FRONT sprockets
    moves:    five medium road wheels a side on leaf springs, four return rollers, raised rear idler
    built:    welded box superstructure on a narrow tub; flat nose plate; small angular turret set a little to the left
    serviced: cupola on the turret roof
    references: Panzer II Ausf. F survivors (five evenly spaced wheels, vertical superstructure front, tiny turret)
    read_at_play_size: a small box on tracks with five wheels, an angular little turret and a thin short gun
    """
    m = Machine('German light tank (Panzer II)')
    lw = 0.76
    m.add('upper_hull', solid(across([(0.0, 1.13), (0.05, 1.48), (3.35, 1.48), (3.60, 1.13)], -1.10, 1.10)), 'box superstructure overhanging the tracks: crew and engine')
    m.add('lower_hull', solid(across([(0.25, 0.42), (0.10, 0.70), (0.10, 1.14), (3.60, 1.14), (4.55, 0.95), (4.62, 0.70), (4.20, 0.42)], -lw, lw)),
          'tub between the tracks; its sloped nose covers the transmission', on='upper_hull')
    top = running_gear(m, 'lower_hull', lw, 0.94, 0.30, [0.95 + 0.68 * k for k in range(5)], 0.275, (4.35, 0.68, 0.30), (0.40, 0.62, 0.29),
                       rollers=[1.20, 1.95, 2.75, 3.50], rr=0.09, rz=0.90)
    assert top < 1.13, top
    m.add('driver_visor', slab(3.35, 3.47, 0.25, 0.85, 1.22, 1.44, 'steel'), "driver's visor block on the front plate: gives it a face; scale cue", on='upper_hull')
    tz = ring(m, 2.30, 1.48, 0.68, y=0.08)
    plate_turret(m, 2.30, tz, 0.62, 0.60, 0.22, 0.42, 0.08, y=0.08)
    m.add('mantlet', slab(2.30 + 0.56, 2.30 + 0.76, 0.08 - 0.36, 0.08 + 0.36, tz + 0.08, tz + 0.36, 'steel'), 'gun shield', on='turret')
    gun(m, (3.06, 0.18, tz + 0.22), 0.85, 0.035, 'mantlet', why='20 mm autocannon: thin, a line that carries')
    m.add('cupola', disc(2.10, 0.08, tz + 0.42, tz + 0.54, 0.22), "commander's cupola: scale cue", on='turret')
    for sd, s in ((1, 'l'), (-1, 'r')):
        y0, y1 = sorted((sd * 0.78, sd * 1.10))
        m.add(f'mudguard_{s}', slab(3.58, 4.50, y0, y1, 1.115, 1.16, 'steel'), 'track guard running forward over the sprocket: the long flat fender line of German tanks', on='upper_hull')
    m.add('fender_box', slab(1.20, 2.00, -1.10, -0.80, 1.48, 1.66), 'stowage box on the right track guard', on='upper_hull')
    m.add('exhaust', rod((-0.07, -0.55, 1.24), (-0.07, 0.25, 1.24), 0.09, 'exhaust'), 'muffler across the tail plate: marks the rear', on='upper_hull')
    return m


def panzer4():
    """Brief
    is:       medium tank (Panzer IV Ausf. H), crew 5, long 75 mm gun
    does:     the workhorse: fights other mediums, supports infantry
    gameplay: 2 x 1 tiles; boxy where the Sherman is round; long gun with a muzzle brake; turret aims on its own
    power:    engine at the rear, drive shaft forward to FRONT sprockets
    moves:    eight small road wheels a side (in pairs on leaf springs), four return rollers, raised rear idler
    built:    welded: vertical-sided superstructure wider than the tub, a stepped nose (glacis lower than the driver's
              front plate), angular turret with a stowage bin on its back and a drum cupola at the rear of the roof
    serviced: hatches on the roof corners ahead of the turret; cupola
    references: Panzer IV Ausf. G/H survivors (eight small wheels, the stepped front, bin behind the turret)
    read_at_play_size: a long box on many small wheels, a stepped front, an angular turret with a box on its back, long gun with a knob
    """
    m = Machine('German medium tank (Panzer IV)')
    lw = 0.98
    m.add('upper_hull', solid(across([(0.15, 1.25), (0.15, 1.70), (4.15, 1.70), (4.30, 1.25)], -1.42, 1.42)), 'vertical-sided superstructure overhanging the tracks')
    m.add('lower_hull', solid(across([(0.35, 0.45), (0.05, 0.75), (0.05, 1.26), (4.30, 1.26), (5.65, 1.02), (5.72, 0.72), (5.30, 0.45)], -lw, lw)),
          'tub between the tracks; the low glacis ahead of the superstructure is its roof', on='upper_hull')
    top = running_gear(m, 'lower_hull', lw, 1.21, 0.40, [1.05 + 0.50 * k for k in range(8)], 0.235, (5.45, 0.74, 0.36), (0.45, 0.66, 0.33),
                       rollers=[1.35, 2.45, 3.55, 4.65], rr=0.11, rz=1.01, belly=0.45)
    assert top < 1.25, top
    for sd, s in ((1, 'driver'), (-1, 'radio')):
        m.add(f'{s}_hatch', disc(3.86, sd * 1.02, 1.70, 1.74, 0.20), 'crew hatch on the roof corner: scale cue', on='upper_hull')
    tz = ring(m, 3.02, 1.70, 0.98)
    plate_turret(m, 3.02, tz, 0.85, 0.90, 0.35, 0.50, 0.12)
    m.add('bin', slab(3.02 - 1.38, 3.02 - 0.85, -0.55, 0.55, tz + 0.10, tz + 0.42), 'stowage bin on the turret rear: balances the gun, and a mark of this tank', on='turret')
    m.add('mantlet', slab(3.02 + 0.80, 3.02 + 1.05, -0.45, 0.45, tz + 0.08, tz + 0.42, 'steel'), 'flat gun shield', on='turret')
    m.add('collar', rod((4.07, 0, tz + 0.26), (4.40, 0, tz + 0.26), 0.12), 'recoil sleeve where the gun leaves the shield', on='mantlet')
    gun(m, (4.40, 0, tz + 0.26), 2.65, 0.055, 'collar', brake=(0.11, 0.30), why='75 mm L/48')
    m.add('cupola', disc(3.02 - 0.45, 0, tz + 0.50, tz + 0.74, 0.30), "commander's drum cupola at the rear of the roof", on='turret')
    for sd, s in ((1, 'l'), (-1, 'r')):
        y0, y1 = sorted((sd * 1.00, sd * 1.42))
        m.add(f'mudguard_{s}', slab(4.28, 5.78, y0, y1, 1.235, 1.28, 'steel'), 'track guard forward over the sprocket: the long fender line', on='upper_hull')
    m.add('muffler', rod((-0.12, -0.65, 1.00), (-0.12, 0.65, 1.00), 0.16, 'exhaust'), 'big muffler drum across the tail plate: marks the rear', on='lower_hull')
    m.add('spare_tracks', solid(across([(4.45, 1.245), (5.45, 1.065), (5.47, 1.13), (4.47, 1.31)], -0.55, 0.55), 'steel'), 'spare track links laid on the glacis: extra armour, and a dark band across the nose', on='lower_hull')
    m.add('bow_gun', rod((4.20, -0.62, 1.48), (4.58, -0.62, 1.46), 0.04), 'bow machine gun in the front plate', on='upper_hull', small_ok=True)
    return m


def pak40(deployed=True):
    """Brief
    is:       75 mm anti-tank gun (Pak 40) on a split-trail carriage, crew of 5 (figures separate)
    does:     kills tanks from ambush; helpless when flanked
    gameplay: 1 x 2 tiles deployed; faces one way, slow to turn; lower and longer than the American 57 mm
    power:    hand loaded; towed by a half-track
    moves:    two wheels; trails spread and dig in; barrel recoils in a cradle
    built:    low shield of angled plates swept back at the sides, in two halves either side of the barrel;
              long barrel with a big muzzle brake
    references: Pak 40 survivors (very low, shield wings angled back, the double-baffle brake)
    read_at_play_size: a low wide angled shield, a very long barrel with a fat tip, a V of trails
    """
    m = Machine('German 75 mm anti-tank gun (Pak 40)')
    m.add('axle', rod((0, -0.84, 0.40), (0, 0.84, 0.40), 0.06), 'axle: carries the gun on its wheels', small_ok=True)
    for sd, s in ((1, 'l'), (-1, 'r')):
        m.add(f'wheel_{s}', wheel(0, sd * 0.92, 0.40, 0.40, 0.16), 'carriage wheel', on='axle', turns=(P(0, sd * 0.92, 0.40), ACROSS))
        m.add(f'hub_{s}', sh.cyl(P(0, sd * 0.92, 0.40), P(0, sd * 1.04, 0.40), 0.17 * M, 'steel', seg=12), 'hub', on=f'wheel_{s}', turns=(P(0, sd * 0.92, 0.40), ACROSS))
        sh_pts = [(x, sd * y, z) for x0, y, z1 in ((0.31, 0.12, 1.18), (0.31, 0.50, 1.18), (0.10, 0.80, 1.02)) for x in (x0, x0 + 0.06) for z in (0.42, z1)]
        m.add(f'shield_{s}', solid(sh_pts), 'shield half: angled plates swept back at the side; split so the barrel can move between', on='saddle')
        m.add(f'trail_{s}', rod((-0.18, sd * 0.32, 0.44), (-3.00, sd * (0.95 if deployed else 0.17), 0.07), 0.065), 'trail: spreads to brace the recoil', on='saddle', small_ok=True)
        y0, y1 = sorted((sd * 0.82, sd * 1.08)) if deployed else sorted((sd * 0.04, sd * 0.30))
        m.add(f'spade_{s}', slab(-3.14, -2.95, y0, y1, 0.0, 0.26, 'steel'), 'spade: digs in against the recoil', on=f'trail_{s}')
    m.add('saddle', slab(-0.26, 0.32, -0.40, 0.40, 0.34, 0.60, 'steel'), 'saddle on the axle: carries cradle, shield and trail hinges', on='axle')
    m.add('cradle', slab(-0.10, 1.15, -0.10, 0.10, 0.60, 0.74, 'steel'), 'cradle with the recoil cylinders: the barrel slides back in it', on='saddle', small_ok=True)
    m.add('breech', slab(-0.75, -0.10, -0.14, 0.14, 0.60, 0.90, 'steel'), 'breech block: the heavy end', on='cradle')
    m.add('gun', rod((-0.10, 0, 0.82), (2.95, 0, 0.82), 0.05), '75 mm barrel, 3.4 m: the line that points', on='breech', small_ok=True)
    m.add('muzzle', rod((2.58, 0, 0.82), (2.98, 0, 0.82), 0.10), 'muzzle brake: the fat tip that marks this gun', on='gun')
    return m


def panther():
    """Brief
    is:       heavy-medium tank (Panther Ausf. G), crew 5, long 75 mm L/70
    does:     the late-game armour: frontally very hard to kill, long reach; weak from the side
    gameplay: 2 x 1 tiles; bigger than the Panzer IV and sloped where that is boxy; very long gun
    power:    engine at the rear, drive shaft forward to FRONT sprockets
    moves:    eight axles of large overlapping road wheels a side in two rows (no return rollers: the top run lies on
              the wheels), rear idler; turret on a ring; gun behind a rounded shield
    built:    welded: one long sloped glacis, sides sloped in over the tracks; turret with sloped sides and a
              rounded (half-cylinder) gun shield; drum cupola left rear
    serviced: hatches on the roof ahead of the turret; cupola
    references: Panther Ausf. G survivors (big dished overlapping wheels, the single glacis plane, turret set back)
    read_at_play_size: a long wedge-fronted hull on big overlapping wheels, turret set back, an extremely long gun with a knob
    """
    m = Machine('German heavy-medium tank (Panther)')
    lw = 0.92
    up = [(x, y, 1.30) for x in (0.15, 5.55) for y in (-1.63, 1.63)] + [(x, y, 1.80) for x in (0.30, 4.75) for y in (-1.27, 1.27)]
    m.add('upper_hull', solid(up), 'upper hull: glacis and sides sloped in, overhanging the tracks')
    m.add('lower_hull', solid(across([(0.30, 0.50), (0.05, 0.80), (0.05, 1.31), (5.55, 1.31), (6.20, 0.92), (5.70, 0.50)], -lw, lw)),
          'tub between the tracks; its nose carries the glacis down to the transmission', on='upper_hull')
    top = running_gear(m, 'lower_hull', lw, 1.31, 0.66, [1.15 + 0.56 * k for k in range(8)], 0.43, (5.95, 0.80, 0.36), (0.45, 0.66, 0.30),
                       interleave=True, belly=0.50)
    assert top < 1.30, top
    for sd, s in ((1, 'driver'), (-1, 'radio')):
        m.add(f'{s}_hatch', disc(4.42, sd * 0.78, 1.80, 1.84, 0.20), 'crew hatch ahead of the turret: scale cue', on='upper_hull')
    tz = ring(m, 3.15, 1.80, 1.12)
    plate_turret(m, 3.15, tz, 1.05, 1.02, 0.36, 0.78, 0.20, why='welded turret, sides sloped in')
    m.add('mantlet', sh.cyl(P(4.20, -0.74, tz + 0.40), P(4.20, 0.74, tz + 0.40), 0.33 * M, 'steel', seg=14),
          'rounded gun shield, a half-cylinder across the turret front: the gun pivots inside it', on='turret')
    m.add('collar', rod((4.48, 0, tz + 0.40), (4.85, 0, tz + 0.40), 0.12), 'sleeve where the gun leaves the shield', on='mantlet')
    gun(m, (4.85, 0, tz + 0.40), 4.05, 0.06, 'collar', brake=(0.12, 0.36), why='75 mm L/70, over 5 m')
    m.add('cupola', disc(3.15 - 0.42, 0.44, tz + 0.78, tz + 1.02, 0.32), "commander's drum cupola, left rear", on='turret')
    for sd, s in ((1, 'l'), (-1, 'r')):
        y0, y1 = sorted((sd * 0.98, sd * 1.63))
        m.add(f'mudguard_{s}', slab(5.53, 6.40, y0, y1, 1.275, 1.32, 'steel'), 'track guard forward over the sprocket', on='upper_hull')
        y0, y1 = sorted((sd * 0.45, sd * 1.15))
        m.add(f'tail_bin_{s}', slab(-0.18, 0.06, y0, y1, 0.80, 1.32), 'stowage bin on the tail plate: the pair of them mark the rear', on='lower_hull')
        m.add(f'exhaust_{s}', rod((-0.03, sd * 0.20, 0.90), (-0.03, sd * 0.20, 1.48), 0.07, 'exhaust'), 'upright exhaust pipe between the bins', on='lower_hull', small_ok=True)
        m.add(f'fan_{s}', disc(0.95, sd * 0.72, 1.80, 1.84, 0.32), 'round fan cover on the engine deck', on='upper_hull')
    m.add('bow_gun', rod((5.05, -0.70, 1.62), (5.40, -0.70, 1.52), 0.04), 'bow machine gun in its ball mount', on='upper_hull', small_ok=True)
    return m


ALL = [('scout', 'Motorcycle and sidecar', kradschuetzen), ('armoured car', 'Sd.Kfz. 222', sdkfz222), ('light tank', 'Panzer II', panzer2),
       ('medium tank', 'Panzer IV', panzer4), ('anti-tank gun', 'Pak 40', pak40), ('heavy tank', 'Panther', panther)]
