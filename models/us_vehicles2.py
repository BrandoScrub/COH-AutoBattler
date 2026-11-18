"""More American vehicles: half-track, tank destroyer, truck, a second light tank, a field howitzer. Built with their
secondary detail from the start (the first set's blockouts were agreed, and the same kit builds these). One Machine
each, check() empty. Briefs follow artkit/DESIGN_METHOD.md; real dimensions x 55."""
from artkit import shapes as sh
from artkit.machine import Machine
from .kit import *


def halftrack():
    """Brief
    is:       armoured personnel half-track (M3), driver and up to 12 men, pintle .50 cal
    does:     carries infantry behind thin armour, reinforces squads at the front
    gameplay: 1 x 2 tiles, transport; must read as open-topped with men in it, wheels in front, tracks behind
    power:    truck engine under a long hood; drives the front axle and the track sprockets
    moves:    steering wheels in front; a short rubber band track each side: front sprocket, four small bogie wheels,
              rear idler, one return roller
    built:    a truck chassis with a flat-plate armoured box: hood, cab, and an open troop bay with vertical sides
    serviced: hood sides lift; rear door; roller on the front bumper for climbing out of ditches
    references: M3 / M5 half-track survivors (vertical flat sides, the front roller, mine racks along the bay)
    read_at_play_size: a truck nose on wheels, an open steel box on short tracks, heads showing over the sides
    """
    m = Machine('US half-track (M3)')
    m.add('chassis', slab(0.40, 5.60, -0.45, 0.45, 0.50, 0.76, 'steel'), 'truck chassis: axle, track units and body bolt to it')
    axle(m, 'front_axle', 4.95, 0.42, 0.22, 0.83, z=0.42)
    top = running_gear(m, 'chassis', 0.45, 0.83, 0.30, [1.30, 1.63, 1.96, 2.29], 0.16, (2.78, 0.50, 0.29), (0.82, 0.50, 0.28),
                       rollers=[1.80], rr=0.08, rz=0.73, belly=0.50, pitch=0.14, hub=0.52)
    assert top < 0.95, top
    m.add('bed', slab(0.35, 4.10, -0.50, 0.50, 0.76, 0.98, 'steel'), 'frame under the troop bay and cab', on='chassis')
    m.add('floor', slab(0.35, 3.60, -1.08, 1.08, 0.96, 1.03), 'bay floor, out over the tracks', on='bed')
    for sd, s in ((1, 'l'), (-1, 'r')):
        y0, y1 = sorted((sd * 1.02, sd * 1.08))
        m.add(f'side_{s}', slab(0.35, 3.60, y0, y1, 1.03, 1.72), 'vertical armoured side of the open bay', on='floor')
        y0, y1 = sorted((sd * 1.08, sd * 1.20))
        m.add(f'mine_rack_{s}', slab(1.10, 2.90, y0, y1, 1.08, 1.30, 'steel'), 'mine rack along the side: a dark band that marks this vehicle', on=f'side_{s}')
        y0, y1 = sorted((sd * 0.52, sd * 1.02))
        m.add(f'fender_{s}', slab(4.42, 5.50, y0, y1, 0.90, 0.96), 'fender over the front wheel', on='hood')
    m.add('tail', slab(0.35, 0.41, -1.02, 1.02, 1.03, 1.72), 'rear plate with the door', on='floor')
    m.add('cab', slab(3.60, 4.10, -1.08, 1.08, 0.96, 1.50), 'cab: dashboard and doors', on='bed', contact=['floor'])
    m.add('windscreen', slab(4.02, 4.08, -1.02, 1.02, 1.50, 1.92, 'steel'), 'armoured windscreen plate, propped up', on='cab')
    m.add('hood', solid(across([(4.10, 0.76), (4.10, 1.48), (5.55, 1.36), (5.62, 0.76)], -0.50, 0.50)), 'long hood over the engine, flat plates', on='chassis')
    m.add('roller', rod((5.76, -0.62, 0.72), (5.76, 0.62, 0.72), 0.13), 'unditching roller across the nose: the mark of the American half-track', on='hood')
    m.add('mg_post', disc(2.75, 0, 1.03, 1.95, 0.045), 'pedestal for the heavy machine gun', on='floor', small_ok=True)
    m.add('mg', rod((2.55, 0, 2.0), (3.85, 0, 2.0), 0.045), '.50 cal over the cab: the line that says it is armed', on='mg_post', small_ok=True)
    from .infantry import crewman, SIT, STAND
    m.add('driver', crewman('us', SIT, (187, 30, 55), L=(204, 36, 76), R=(204, 24, 76)), 'driver on the left', on='floor', contact=['cab'], convex=False, small_ok=True)
    m.add('gunner', crewman('us', STAND, (134, 0, 55), L=(142, 4, 110), R=(141, -4, 109)), 'gunner standing at the .50', on='floor', contact=['mg'], convex=False, small_ok=True)
    for k, (x, y) in enumerate(((52, 30), (52, -30), (98, 30))):
        m.add(f'rider_{k}', crewman('us', SIT, (x, y, 55)), 'infantryman riding in the bay: heads over the side say transport', on='floor', convex=False, small_ok=True)
    return m


def wolverine():
    """Brief
    is:       tank destroyer (M10), crew 5, 3-inch gun in an open-topped turret
    does:     kills tanks from range; thin armour and an open roof make it weak up close and to mortars
    gameplay: 2 x 1 tiles; Sherman running gear but angular: sloped sides, a five-sided open turret with wedges on its back
    power:    engine at the rear, drive forward to FRONT sprockets (the Sherman's)
    moves:    three two-wheel bogies a side, three return rollers, rear idler; turret on a ring; gun behind a wide shield
    built:    welded, every plate sloped; open-topped turret balanced by two wedge counterweights on its rear
    serviced: hull hatches ahead of the turret; the open turret top
    references: M10 survivors (sloped hull sides over Sherman bogies, the long turret with the duck-bill counterweights)
    read_at_play_size: a Sherman's tracks under a sloped-sided hull, an angular open turret with a long thin gun and a heavy tail
    """
    m = Machine('US tank destroyer (M10)')
    lw = 0.80
    up = [(x, y, 1.12) for x in (0.0, 5.62) for y in (-1.50, 1.50)] + [(x, y, 1.76) for x in (0.45, 4.30) for y in (-1.06, 1.06)]
    m.add('upper_hull', solid(up), 'upper hull, sides and glacis sloped in: thin plate made to count')
    m.add('lower_hull', solid(across([(0.30, 0.45), (0.10, 0.72), (0.10, 1.13), (5.62, 1.13), (5.90, 0.86), (5.72, 0.56), (5.20, 0.45)], -lw, lw)),
          'tub between the tracks; transmission in the nose', on='upper_hull')
    wheels = [b + dx for b in (1.25, 2.75, 4.25) for dx in (-0.34, 0.34)]
    top = running_gear(m, 'lower_hull', lw, 1.055, 0.42, wheels, 0.255, (5.20, 0.66, 0.30), (0.38, 0.50, 0.26), rollers=[1.30, 2.80, 4.30], rr=0.10, rz=0.87, belly=0.45)
    assert top < 1.12, top
    for sd, s in ((1, 'driver'), (-1, 'codriver')):
        m.add(f'{s}_hatch', disc(4.06, sd * 0.78, 1.76, 1.80, 0.20), 'crew hatch ahead of the turret: scale cue', on='upper_hull')
    m.add('engine_grille', slab(0.55, 1.55, -0.85, 0.85, 1.76, 1.80, 'steel'), 'engine deck grille: marks the rear', on='upper_hull')
    tz = ring(m, 2.90, 1.76, 0.98)
    plate_turret(m, 2.90, tz, 0.92, 0.88, 0.34, 0.62, 0.10, why='five-sided welded turret, open on top')
    m.add('well', slab(2.90 - 0.55, 2.90 + 0.45, -0.58, 0.58, tz + 0.62, tz + 0.64, 'steel'), 'the open top: a dark well where the crew stand', on='turret')
    for sd, s in ((1, 'l'), (-1, 'r')):
        cw = [(2.90 + x, sd * y, tz + z) for x, y0, y1, z0, z1 in ((-0.86, 0.08, 0.66, 0.16, 0.60), (-1.46, 0.12, 0.52, 0.30, 0.56)) for y in (y0, y1) for z in (z0, z1)]
        m.add(f'counterweight_{s}', solid(cw), 'wedge counterweight on the turret rear: balances the long gun; the duck-bill tail', on='turret')
    m.add('mantlet', solid([(2.90 + x, y, tz + z) for x, w, z0, z1 in ((0.86, 0.72, 0.08, 0.56), (1.16, 0.50, 0.14, 0.50)) for y in (-w, w) for z in (z0, z1)], 'steel'),
          'wide sloped gun shield', on='turret')
    gun(m, (4.06, 0, tz + 0.32), 3.05, 0.058, 'mantlet', brake=(0.085, 0.22), why='3-inch gun: long and thin with a small counterweight ring at the tip')
    m.add('aa_post', disc(2.90 - 0.80, 0, tz + 0.62, tz + 0.90, 0.04), 'pintle on the turret rear', on='turret', small_ok=True)
    m.add('aa_gun', rod((2.90 - 1.30, 0, tz + 0.94), (2.90 - 0.05, 0, tz + 0.94), 0.04), '.50 cal on the turret rear', on='aa_post', small_ok=True)
    return m


def truck():
    """Brief
    is:       2.5-ton 6x6 cargo truck (GMC CCKW), driver and mate
    does:     hauls supplies and men; in the game the supply or resource unit
    gameplay: 1 x 2 tiles, unarmed, soft; must read as a truck: hood, cab, canvas-covered bed, three axles
    power:    petrol engine under the hood; drive to all three axles
    moves:    steering axle in front, two axles close together under the bed
    built:    ladder chassis; pressed-steel hood and open cab with a canvas top; steel cargo body with a canvas tilt on bows
    references: CCKW survivors (flat wide fenders, the tandem rear axles, the arched tilt)
    read_at_play_size: a long hood, a cab, a rounded canvas back, six wheels
    """
    m = Machine('US cargo truck (CCKW)')
    m.add('chassis', slab(0.20, 6.10, -0.40, 0.40, 0.50, 0.78, 'steel'), 'ladder chassis')
    for n, x in (('rear_axle', 1.05), ('mid_axle', 2.17), ('front_axle', 5.35)): axle(m, n, x, 0.45, 0.27, 0.87)
    m.add('bed_frame', slab(0.25, 3.85, -0.45, 0.45, 0.78, 0.98, 'steel'), 'sub-frame under the cargo body', on='chassis')
    m.add('bed', slab(0.22, 3.88, -1.10, 1.10, 0.96, 1.10), 'cargo floor, out over the rear wheels', on='bed_frame')
    for sd, s in ((1, 'l'), (-1, 'r')):
        y0, y1 = sorted((sd * 1.04, sd * 1.10))
        m.add(f'side_{s}', slab(0.22, 3.88, y0, y1, 1.10, 1.62), 'cargo body side', on='bed')
        y0, y1 = sorted((sd * 0.52, sd * 1.06))
        m.add(f'fender_{s}', slab(4.92, 5.95, y0, y1, 0.95, 1.01), 'flat fender over the front wheel', on='hood')
    m.add('tailgate', slab(0.22, 0.28, -1.04, 1.04, 1.10, 1.62), 'tailgate', on='bed')
    tilt = [(x, y, z) for x in (0.24, 3.86) for y, z in ((-1.08, 1.62), (1.08, 1.62), (-1.02, 2.20), (1.02, 2.20), (-0.60, 2.52), (0.60, 2.52), (0, 2.58))]
    m.add('tilt', solid(tilt, 'canvas', smooth=True), 'canvas tilt over the bows: the rounded back that says cargo truck', on='side_l', contact=['side_r'])
    m.add('cab', slab(3.95, 4.90, -0.92, 0.92, 0.78, 1.55), 'open cab: seats, doors', on='chassis')
    m.add('cab_top', solid([(x, y, z) for x in (3.95, 4.80) for y, z in ((-0.90, 1.55), (0.90, 1.55), (-0.84, 2.00), (0.84, 2.00))], 'canvas', smooth=True), 'canvas cab top', on='cab')
    m.add('hood', solid(across([(4.90, 0.78), (4.90, 1.52), (6.05, 1.40), (6.12, 0.78)], -0.50, 0.50)), 'hood over the engine, grille face in front', on='chassis')
    m.add('bumper', slab(6.12, 6.24, -1.0, 1.0, 0.55, 0.75, 'steel'), 'bumper with the winch behind it', on='chassis')
    m.add('fuel_tank', rod((3.0, 0.48, 0.62), (3.75, 0.48, 0.62), 0.16), 'fuel tank slung on the chassis side', on='chassis')
    m.add('spare', sh.cyl(P(3.87, -0.50, 1.46), P(3.94, -0.50, 1.46), 0.38 * M, 'rubber', seg=16), 'spare wheel behind the cab', on='cab')
    return m


def chaffee():
    """Brief
    is:       light tank (M24), crew 5, lightweight 75 mm gun
    does:     late-war light tank: a medium's gun on a fast, thinly armoured hull
    gameplay: 1 x 2 tiles; lower and sleeker than the M5, five big wheels; reads as modern beside it
    power:    twin engines at the rear, drive forward to FRONT sprockets
    moves:    five large road wheels a side on torsion bars, three return rollers, rear idler
    built:    welded hull with sloped glacis and sides; a wide low turret with a bustle
    references: M24 survivors (the low wide turret, large evenly spaced wheels, long sloped nose)
    read_at_play_size: a low sleek hull on five big wheels with a wide turret and a medium-length gun
    """
    m = Machine('US light tank (M24)')
    lw = 0.95
    up = [(x, y, 1.20) for x in (0.10, 4.75) for y in (-1.45, 1.45)] + [(x, y, 1.62) for x in (0.35, 3.55) for y in (-1.28, 1.28)]
    m.add('upper_hull', solid(up), 'low hull over the tracks, glacis and sides sloped')
    m.add('lower_hull', solid(across([(0.30, 0.45), (0.05, 0.75), (0.05, 1.21), (4.75, 1.21), (4.98, 0.92), (4.80, 0.60), (4.40, 0.45)], -lw, lw)), 'tub between the tracks', on='upper_hull')
    top = running_gear(m, 'lower_hull', lw, 1.22, 0.41, [1.00 + 0.72 * k for k in range(5)], 0.32, (4.62, 0.72, 0.30), (0.36, 0.62, 0.30),
                       rollers=[1.40, 2.45, 3.50], rr=0.10, rz=0.95, belly=0.45)
    assert top < 1.20, top
    for sd, s in ((1, 'driver'), (-1, 'codriver')):
        m.add(f'{s}_hatch', disc(3.30, sd * 0.90, 1.62, 1.66, 0.20), 'crew hatch: scale cue', on='upper_hull')
    m.add('engine_grille', slab(0.45, 1.30, -0.95, 0.95, 1.62, 1.66, 'steel'), 'engine deck grilles: marks the rear', on='upper_hull')
    tz = ring(m, 2.40, 1.62, 0.92)
    cast_turret(m, 2.40, tz, [(0.78, 0), (0.84, 0.08), (0.84, 0.40), (0.74, 0.56), (0.40, 0.60), (0, 0.61)], sx=1.05, why='wide low turret')
    m.add('bustle', solid([(2.40 + x, y, tz + z) for x, w in ((-0.60, 0.56), (-1.30, 0.46)) for y in (-w, w) for z in (0.14, 0.50)]), 'bustle: radio, and balance for the gun', on='turret')
    m.add('mantlet', slab(2.40 + 0.74, 2.40 + 1.00, -0.42, 0.42, tz + 0.10, tz + 0.48, 'steel'), 'gun shield', on='turret')
    gun(m, (3.40, 0, tz + 0.30), 2.25, 0.05, 'mantlet', why='lightweight 75 mm')
    m.add('cupola', disc(2.40 - 0.25, -0.42, tz + 0.58, tz + 0.74, 0.24), "commander's cupola", on='turret')
    m.add('aa_post', disc(2.40 - 0.95, 0, tz + 0.50, tz + 0.80, 0.04), 'pintle on the bustle', on='bustle', small_ok=True)
    m.add('aa_gun', rod((2.40 - 1.40, 0, tz + 0.84), (2.40 - 0.20, 0, tz + 0.84), 0.04), '.50 cal on the turret rear', on='aa_post', small_ok=True)
    m.add('bow_gun', rod((3.90, -0.62, 1.48), (4.25, -0.62, 1.40), 0.035), 'bow machine gun', on='upper_hull', small_ok=True)
    return m


def howitzer_105():
    """Brief
    is:       105 mm howitzer M2A1 on a split-trail carriage, crew figures separate
    does:     indirect fire: shells an area from far behind the line
    gameplay: 1 x 2 tiles emplaced, does not move in play; reads as artillery, not anti-tank: short fat raised barrel
    moves:    barrel pitches on trunnions; trails spread; recoil cylinders above the barrel
    references: M2A1 / M101 survivors (the recoil cylinder riding over a short barrel, a tall shield in two halves)
    read_at_play_size: a tall split shield, a short thick barrel pointing up, a V of trails
    """
    return howitzer('US 105 mm howitzer M2A1', 0.46, 0.96, 0.20, 1.75, 0.085, 22, 1.50, 2.9, recuperator=True)


ALL = [('half track', 'M3 half-track', halftrack), ('tank destroyer', 'M10', wolverine), ('truck', 'CCKW 2.5-ton truck', truck),
       ('light tank m24', 'M24 Chaffee', chaffee), ('howitzer', '105 mm M2A1', howitzer_105)]
