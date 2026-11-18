"""American vehicles, 1943-45: blockouts (primary and secondary masses), one Machine each, check() empty.
Briefs follow artkit/DESIGN_METHOD.md; real dimensions x 55. The medium tank is the engine's own M4A3 blockout."""
from artkit import shapes as sh
from artkit.machine import Machine
from .kit import *


def jeep():
    """Brief
    is:       1/4-ton 4x4 scout car (Willys MB), crew 2-3, pintle .30 cal machine gun
    does:     finds the enemy first, spots for others, runs from anything armoured
    gameplay: fastest unit, 1 x 1 tile, no armour; must read as open, small and quick, and which way it drives
    power:    petrol engine under the hood over the front axle; drive to both axles
    moves:    four wheels on two beam axles; the gun turns on a pintle post behind the front seats
    built:    pressed-steel tub on a ladder chassis; flat fenders; fold-down windscreen
    serviced: hood lifts; spare wheel on the tail
    references: Willys MB survivors (flat fenders, slotted grille, tub lower than the hood line), RTS jeeps (CoH)
    read_at_play_size: a low open tub, a hood and a windscreen frame on four wheels, a gun on a post
    """
    m = Machine('US scout jeep (Willys MB)')
    m.add('chassis', slab(0.15, 3.20, -0.30, 0.30, 0.32, 0.52, 'steel'), 'ladder chassis: everything bolts to it')
    axle(m, 'rear_axle', 0.62, 0.37, 0.16, 0.615); axle(m, 'front_axle', 2.65, 0.37, 0.16, 0.615)
    m.add('tub', slab(0.15, 2.05, -0.50, 0.50, 0.50, 0.98), 'open body tub between the wheels: crew sit in it', on='chassis')
    for sd, s in ((1, 'l'), (-1, 'r')):
        y0, y1 = sorted((sd * 0.50, sd * 0.78))
        m.add(f'rear_arch_{s}', slab(0.15, 1.15, y0, y1, 0.80, 0.98), 'wheel arch box over the rear wheel: the tub widens above the tyre', on='tub')
        y0, y1 = sorted((sd * 0.36, sd * 0.78))
        m.add(f'fender_{s}', slab(2.15, 3.15, y0, y1, 0.78, 0.85), 'flat fender over the front wheel: the jeep signature', on='hood')
        y0, y1 = sorted((sd * 0.08, sd * 0.46))
        m.add(f'seat_{s}', slab(1.22, 1.34, y0, y1, 0.98, 1.24, 'steel'), 'seat back: the human-scale cue (0.4 m wide)', on='tub')
    m.add('hood', solid(across([(2.05, 0.50), (2.05, 1.02), (3.08, 0.96), (3.08, 0.50)], -0.36, 0.36)), 'engine hood over the front axle, grille face in front', on='chassis')
    m.add('bumper', slab(3.20, 3.30, -0.72, 0.72, 0.42, 0.58, 'steel'), 'front bumper bar on the chassis rails', on='chassis')
    m.add('windscreen', slab(1.97, 2.03, -0.68, 0.68, 0.98, 1.52, 'steel'), 'windscreen frame: tells the eye where the front of the crew space is', on='tub')
    m.add('rear_seat', slab(0.28, 0.40, -0.44, 0.44, 0.98, 1.20, 'steel'), 'rear bench back', on='tub')
    m.add('spare', sh.cyl(P(0.02, -0.18, 0.74), P(0.15, -0.18, 0.74), 0.33 * M, 'rubber', seg=16), 'spare wheel on the tail: marks the rear', on='tub')
    m.add('pintle', disc(0.95, 0, 0.98, 1.50, 0.045), 'pintle post: the gun turns on it', on='tub', small_ok=True)
    m.add('mg', slab(0.72, 1.22, -0.06, 0.06, 1.50, 1.64, 'steel'), '.30 cal receiver on the pintle', on='pintle', small_ok=True)
    m.add('mg_barrel', rod((1.22, 0, 1.58), (1.80, 0, 1.58), 0.035), 'air-cooled barrel: the line that says it is armed', on='mg', small_ok=True)
    m.add('steering', sh.cyl(P(1.80, 0.27, 1.12), P(1.84, 0.27, 1.15), 0.19 * M, 'steel', seg=12), 'steering wheel on the left: where the driver is', on='tub')
    m.add('jerry_can', slab(0.0, 0.15, 0.22, 0.56, 0.52, 0.98, 'steel'), 'fuel can on the tail: range is this car\'s whole job', on='tub')
    from .infantry import crewman, SIT, STAND
    m.add('driver', crewman('us', SIT, (80, 15, 46), L=(100, 22, 64), R=(100, 8, 64)), 'driver, hands on the wheel: the scale cue, and what makes it a scout car and not a wreck',
          on='tub', contact=['seat_l', 'steering'], convex=False, small_ok=True)
    m.add('gunner', crewman('us', STAND, (26, 0, 30), L=(41, 4, 84), R=(40, -4, 83)), 'gunner standing at the pintle gun', on='tub', contact=['rear_seat', 'mg'], convex=False, small_ok=True)
    return m


def greyhound():
    """Brief
    is:       6x6 light armoured car (M8), crew 4, 37 mm gun in an open-topped turret
    does:     fast armoured recon: hunts infantry and scout cars, keeps away from tanks
    gameplay: 1 x 2 tiles, thin armour, turret turns 360; hull heading and gun heading both read
    power:    engine at the rear under the deck, drive to all three axles
    moves:    six wheels: one steering axle in front, two close together at the rear; turret on a ring
    built:    welded hull: a narrow tub between the wheels, a wider upper hull above them; cast round turret
    serviced: driver hoods where roof meets glacis; open turret top
    references: M8 survivors (two rear axles close together, long sloped nose, small round open turret)
    read_at_play_size: a long low wedge on six big wheels with a small round turret and a thin gun
    """
    m = Machine('US armoured car (M8)')
    m.add('chassis', slab(0.40, 4.50, -0.45, 0.45, 0.42, 0.72, 'steel'), 'chassis and drive line: axles hang from it')
    for n, x in (('rear_axle', 0.85), ('mid_axle', 2.07), ('front_axle', 4.05)): axle(m, n, x, 0.50, 0.25, 0.965)
    m.add('lower_hull', solid(across([(0.30, 0.65), (0.10, 1.06), (4.45, 1.06), (4.85, 0.85), (4.60, 0.62)], -0.78, 0.78)),
          'armoured tub between the wheels', on='chassis')
    up = [(0.10, y, 1.06) for y in (-1.20, 1.20)] + [(4.30, y, 1.06) for y in (-1.20, 1.20)] + [(4.50, y, 1.06) for y in (-0.80, 0.80)]
    up += [(0.35, y, 1.60) for y in (-0.95, 0.95)] + [(3.30, y, 1.60) for y in (-0.95, 0.95)]
    m.add('upper_hull', solid(up), 'upper hull over the wheels: sloped sides, long glacis; crew and engine', on='lower_hull')
    for sd, s in ((1, 'driver'), (-1, 'codriver')):
        y0, y1 = sorted((sd * 0.15, sd * 0.75))
        m.add(f'{s}_hood', solid(across([(3.28, 1.50), (3.28, 1.62), (3.80, 1.62), (4.05, 1.20)], y0, y1)),
              'raised driver hood on the glacis: his head needs the room; the human-scale cue (0.6 m)', on='upper_hull')
    tz = ring(m, 2.38, 1.60, 0.86)
    cast_turret(m, 2.38, tz, [(0.78, 0), (0.84, 0.08), (0.82, 0.44), (0.70, 0.50), (0, 0.50)], why='round open-topped turret (closed in the blockout)')
    m.add('mantlet', slab(2.38 + 0.70, 2.38 + 1.00, -0.34, 0.34, tz + 0.10, tz + 0.42, 'steel'), 'gun shield: the gun pivots behind it', on='turret')
    gun(m, (2.38 + 1.00, 0, tz + 0.27), 1.45, 0.04, 'mantlet', why='37 mm gun: thin, but the line that says where it points')
    for sd, s in ((1, 'l'), (-1, 'r')):
        y0, y1 = sorted((sd * 0.78, sd * 1.00))
        m.add(f'side_bin_{s}', slab(2.66, 3.44, y0, y1, 0.64, 1.04), 'stowage bin between the front and middle wheels (mines and kit rode here)', on='lower_hull')
    m.add('aa_post', disc(2.38 - 0.62, 0, tz + 0.50, tz + 0.74, 0.04), 'pintle at the turret rear for the heavy machine gun', on='turret', small_ok=True)
    m.add('aa_gun', rod((2.38 - 0.95, 0, tz + 0.78), (2.38 + 0.30, 0, tz + 0.78), 0.04), '.50 cal on the turret rear: a second line over the turret, an American mark', on='aa_post', small_ok=True)
    return m


def stuart():
    """Brief
    is:       light tank (M5A1), crew 4, 37 mm gun
    does:     fast tracked scout and infantry killer; loses to any real anti-tank gun
    gameplay: 1 x 2 tiles; smaller and taller-looking than the medium, quick; hull and turret headings read
    power:    twin engines at the rear under a raised deck; drive shaft forward to FRONT sprockets
    moves:    two two-wheel bogies a side, a big trailing idler on the ground at the rear, three return rollers
    built:    welded hull with a sloped glacis; turret with a radio bustle
    serviced: two hatches on the roof ahead of the turret; raised engine deck
    references: M5A1 survivors (stepped rear deck, short track base, tall narrow stance)
    read_at_play_size: a short tall box on tracks with a stepped back and a small turret with a thin gun
    """
    m = Machine('US light tank (M5A1)')
    lw = 0.74
    m.add('upper_hull', solid(across([(0.10, 1.14), (0.10, 1.56), (3.20, 1.56), (4.10, 1.14)], -1.12, 1.12)),
          'fighting and engine compartments, overhanging the tracks; sloped glacis in front')
    m.add('lower_hull', solid(across([(0.35, 0.40), (0.18, 0.62), (0.18, 1.15), (4.10, 1.15), (4.28, 0.78), (3.95, 0.40)], -lw, lw)),
          'tub between the tracks that carries the suspension; its nose holds the transmission', on='upper_hull')
    top = running_gear(m, 'lower_hull', lw, 0.93, 0.30, [1.42, 2.08, 2.62, 3.28], 0.255, (4.00, 0.72, 0.27), (0.60, 0.47, 0.36),
                       rollers=[1.20, 2.35, 3.40], rr=0.09, rz=0.92, belly=0.40)
    assert top < 1.14, top
    m.add('engine_deck', slab(0.10, 1.45, -0.95, 0.95, 1.56, 1.70), 'raised deck over the twin engines: the stepped back that marks this tank', on='upper_hull')
    for sd, s in ((1, 'driver'), (-1, 'codriver')):
        m.add(f'{s}_hatch', disc(2.98, sd * 0.62, 1.56, 1.60, 0.21), 'crew hatch: access, and the human-scale cue', on='upper_hull')
    tz = ring(m, 2.20, 1.56, 0.68)
    cast_turret(m, 2.20, tz, [(0.60, 0), (0.64, 0.08), (0.64, 0.36), (0.56, 0.50), (0.30, 0.53), (0, 0.54)], why='small turret, rounded plate')
    m.add('bustle', solid([(2.20 + x, y, tz + z) for x, w in ((-0.45, 0.44), (-1.02, 0.36)) for y in (-w, w) for z in (0.16, 0.46)]),
          'radio bustle at the back: balances the gun', on='turret')
    m.add('mantlet', slab(2.20 + 0.52, 2.20 + 0.80, -0.30, 0.30, tz + 0.12, tz + 0.44, 'steel'), 'gun shield', on='turret')
    gun(m, (3.00, 0, tz + 0.28), 1.25, 0.04, 'mantlet', why='37 mm gun: thin, a line that carries')
    m.add('cupola', disc(2.05, -0.28, tz + 0.52, tz + 0.60, 0.20), "commander's hatch on the turret roof", on='turret')
    m.add('rear_box', slab(-0.14, 0.10, -0.70, 0.70, 1.20, 1.52), 'stowage box across the tail', on='upper_hull')
    m.add('aa_post', disc(2.20 - 0.10, 0.52, tz + 0.40, tz + 0.72, 0.035), 'pintle on the turret side', on='turret', small_ok=True)
    m.add('aa_gun', rod((2.20 - 0.55, 0.52, tz + 0.76), (2.20 + 0.50, 0.52, tz + 0.76), 0.035), '.30 cal anti-aircraft gun: a line over the turret', on='aa_post', small_ok=True)
    m.add('bow_gun', rod((3.62, -0.55, 1.36), (4.02, -0.55, 1.30), 0.035), 'bow machine gun through the glacis', on='upper_hull', small_ok=True)
    return m


def at57(deployed=True):
    """Brief
    is:       57 mm anti-tank gun M1 on a split-trail carriage, crew of 5 (figures separate)
    does:     ambushes vehicles from cover; helpless when flanked or moved
    gameplay: 1 x 2 tiles deployed; faces one way, slow to turn: the shield and the trails say which way
    power:    hand loaded; towed by a truck or half-track by the trail eyes
    moves:    rolls on two wheels; trails spread and dig in with spades to take the recoil; barrel slides in a cradle
    built:    axle and saddle, cradle with recoil cylinder under the barrel, flat shield in two halves either side of it
    references: 57 mm M1 / 6-pounder survivors (flat-topped shield between the wheels, long thin barrel, no brake)
    read_at_play_size: a low flat shield between two wheels, a long barrel, a V of trails behind
    """
    m = Machine('US 57 mm anti-tank gun M1')
    m.add('axle', rod((0, -0.80, 0.42), (0, 0.80, 0.42), 0.06), 'axle: carries the gun on its wheels', small_ok=True)
    for sd, s in ((1, 'l'), (-1, 'r')):
        m.add(f'wheel_{s}', wheel(0, sd * 0.88, 0.42, 0.42, 0.16), 'carriage wheel', on='axle', turns=(P(0, sd * 0.88, 0.42), ACROSS))
        m.add(f'hub_{s}', sh.cyl(P(0, sd * 0.88, 0.42), P(0, sd * 1.0, 0.42), 0.17 * M, 'steel', seg=12), 'hub', on=f'wheel_{s}', turns=(P(0, sd * 0.88, 0.42), ACROSS))
        y0, y1 = sorted((sd * 0.10, sd * 0.76))
        m.add(f'shield_{s}', slab(0.28, 0.33, y0, y1, 0.40, 1.26), 'shield half: stops rifle fire; split so the barrel can elevate between', on='saddle')
        m.add(f'trail_{s}', rod((-0.15, sd * 0.30, 0.46), (-2.55, sd * (0.85 if deployed else 0.16), 0.07), 0.06), 'trail: spreads to brace the recoil', on='saddle', small_ok=True)
        y0, y1 = sorted((sd * 0.72, sd * 0.98)) if deployed else sorted((sd * 0.03, sd * 0.29))
        m.add(f'spade_{s}', slab(-2.68, -2.50, y0, y1, 0.0, 0.24, 'steel'), 'spade: digs in so the gun does not roll back', on=f'trail_{s}')
    m.add('saddle', slab(-0.22, 0.29, -0.36, 0.36, 0.36, 0.62, 'steel'), 'saddle on the axle: carries cradle, shield and trail hinges', on='axle')
    m.add('cradle', slab(-0.10, 0.95, -0.085, 0.085, 0.62, 0.74, 'steel'), 'cradle with the recoil cylinder: the barrel slides back in it', on='saddle', small_ok=True)
    m.add('breech', slab(-0.55, -0.10, -0.11, 0.11, 0.62, 0.86, 'steel'), 'breech block: the heavy end, behind the trunnions', on='cradle')
    m.add('barrel', rod((-0.10, 0, 0.80), (2.30, 0, 0.80), 0.045), '57 mm barrel, 2.8 m: the line that points', on='breech', small_ok=True)
    return m


def pershing():
    """Brief
    is:       heavy tank (M26), crew 5, 90 mm gun
    does:     the late-game answer to heavy German armour: thick front, big gun, slow to arrive
    gameplay: 2 x 1 tiles; clearly bigger, lower and wider than the M4; long gun with a muzzle brake
    power:    engine and transmission both at the REAR: rear sprockets, front idlers
    moves:    six large road wheels a side on torsion bars, five return rollers; turret on a ring; gun on trunnions
    built:    cast and welded hull with a long sloped glacis; big cast turret with a long bustle
    serviced: driver hatches either side of the glacis top; cupola and loader hatch on the turret
    references: M26 survivors (low wide hull, six evenly spaced wheels, long overhanging bustle, double-baffle brake)
    read_at_play_size: a wide low hull on six big wheels, a big rounded turret set forward, a very long gun with a fat tip
    """
    m = Machine('US heavy tank (M26)')
    lw = 1.05
    m.add('upper_hull', solid(across([(0.10, 1.22), (0.10, 1.68), (1.00, 1.75), (4.65, 1.75), (6.00, 1.22)], -1.72, 1.72)),
          'low wide hull overhanging the tracks; long glacis')
    m.add('lower_hull', solid(across([(0.25, 0.45), (0.05, 0.80), (0.05, 1.23), (6.00, 1.23), (6.25, 0.95), (6.10, 0.62), (5.60, 0.45)], -lw, lw), smooth=False),
          'tub between the tracks: torsion bars across its floor', on='upper_hull')
    top = running_gear(m, 'lower_hull', lw, 1.42, 0.61, [1.25 + 0.72 * k for k in range(6)], 0.33, (5.72, 0.72, 0.31), (0.45, 0.72, 0.33),
                       rollers=[1.60, 2.33, 3.05, 3.77, 4.50], rr=0.12, rz=0.96, drive='rear', belly=0.45)
    assert top < 1.22, top
    for sd, s in ((1, 'driver'), (-1, 'codriver')):
        m.add(f'{s}_hatch', disc(4.45, sd * 0.95, 1.75, 1.79, 0.23), 'crew hatch: access and human-scale cue', on='upper_hull')
    tz = ring(m, 3.25, 1.75, 1.10)
    cast_turret(m, 3.25, tz, [(0.98, 0), (1.05, 0.10), (1.05, 0.45), (0.95, 0.68), (0.60, 0.78), (0, 0.80)], sx=1.06, why='big cast turret: rounded because cast')
    m.add('bustle', solid([(3.25 + x, y, tz + z) for x, w, z0, z1 in ((-0.70, 0.66, 0.12, 0.66), (-1.75, 0.55, 0.16, 0.62), (-1.92, 0.42, 0.24, 0.54))
                           for y in (-w, w) for z in (z0, z1)], smooth=True), 'long bustle: ammunition, and weight to balance the 90 mm', on='turret')
    m.add('mantlet', solid([(3.25 + x, y, tz + z) for x, w, z0, z1 in ((0.95, 0.62, 0.10, 0.62), (1.30, 0.50, 0.16, 0.56)) for y in (-w, w) for z in (z0, z1)], 'steel', smooth=True),
          'cast gun shield on the trunnions', on='turret')
    m.add('collar', rod((4.55, 0, tz + 0.36), (4.95, 0, tz + 0.36), 0.13), 'collar where the gun leaves the shield', on='mantlet')
    gun(m, (4.95, 0, tz + 0.36), 3.85, 0.07, 'collar', brake=(0.13, 0.42), why='90 mm gun, 4.7 m')
    m.add('cupola', disc(3.05, -0.52, tz + 0.74, tz + 0.96, 0.30), "commander's cupola: scale cue", on='turret')
    m.add('loader_hatch', disc(3.10, 0.50, tz + 0.75, tz + 0.82, 0.24), "loader's hatch", on='turret')
    m.add('engine_grille', slab(1.05, 2.02, -1.15, 1.15, 1.75, 1.80, 'steel'), 'engine deck grilles: where the engine breathes; marks the rear half', on='upper_hull')
    for sd, s in ((1, 'l'), (-1, 'r')):
        y0, y1 = sorted((sd * 1.20, sd * 1.66))
        m.add(f'fender_bin_{s}', slab(2.30, 4.30, y0, y1, 1.75, 1.92), 'stowage bins along the fender', on='upper_hull')
    m.add('aa_post', disc(3.25 - 1.35, 0, tz + 0.60, tz + 0.98, 0.04), 'pintle on the bustle roof', on='bustle', small_ok=True)
    m.add('aa_gun', rod((3.25 - 1.85, 0, tz + 1.02), (3.25 - 0.50, 0, tz + 1.02), 0.04), '.50 cal on the turret: a line over the roof', on='aa_post', small_ok=True)
    m.add('bow_gun', rod((5.10, -0.60, 1.60), (5.55, -0.60, 1.50), 0.04), 'bow machine gun through the glacis', on='upper_hull', small_ok=True)
    return m


def sherman():
    from artkit.demo.blockouts import m4_medium_tank
    return m4_medium_tank.machine()


ALL = [('scout', 'Jeep (Willys MB)', jeep), ('armoured car', 'M8 Greyhound', greyhound), ('light tank', 'M5A1 Stuart', stuart),
       ('medium tank', 'M4A3 Sherman', sherman), ('anti-tank gun', '57 mm M1', at57), ('heavy tank', 'M26 Pershing', pershing)]
