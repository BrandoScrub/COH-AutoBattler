"""More German vehicles: half-track, assault gun, truck, heavy tank, a field howitzer. Built with their secondary
detail from the start. One Machine each, check() empty. Briefs follow artkit/DESIGN_METHOD.md; real dimensions x 55."""
from artkit import shapes as sh
from artkit.machine import Machine
from .kit import *


def sdkfz251():
    """Brief
    is:       armoured personnel half-track (Sd.Kfz. 251), driver and a squad, shielded MG forward
    does:     carries panzergrenadiers behind sloped armour, fights alongside the tanks
    gameplay: 1 x 2 tiles, transport; reads as the angular counterpart of the American box: every plate sloped
    power:    engine under the sloped nose; drives the tracks only (the front axle just steers)
    moves:    steering wheels in front; long tracks with large overlapping wheels, front sprocket, rear idler
    built:    welded: a lower hull flaring out to a waist line, upper plates leaning back in; open troop bay
    serviced: rear doors; engine hatches on the nose
    references: Sd.Kfz. 251 Ausf. C/D survivors (the coffin section, overlapping wheels, MG shield over the cab)
    read_at_play_size: a pointed sloped nose on wheels, a faceted open hull on long tracks, helmets over the sides
    """
    m = Machine('German half-track (Sd.Kfz. 251)')
    m.add('chassis', slab(0.30, 5.40, -0.40, 0.40, 0.48, 0.94, 'steel'), 'chassis: front axle, track units and hull bolt to it')
    axle(m, 'front_axle', 4.90, 0.40, 0.20, 0.84, z=0.40)
    top = running_gear(m, 'chassis', 0.40, 0.82, 0.28, [0.98 + 0.42 * k for k in range(6)], 0.29, (3.60, 0.50, 0.25), (0.42, 0.47, 0.24),
                       interleave=True, belly=0.48, pitch=0.14)
    assert top < 0.92, top
    low = [(x, y, z) for x in (0.20, 3.90) for y, z in ((-0.72, 0.93), (0.72, 0.93), (-1.05, 1.28), (1.05, 1.28))]
    m.add('lower_body', solid(low), 'lower hull flaring out to the waist line: the lower half of the coffin section', on='chassis')
    for sd, s in ((1, 'l'), (-1, 'r')):
        w = [(x, sd * y, z) for x in (0.20, 3.20) for y, z in ((1.05, 1.28), (0.98, 1.28), (0.80, 1.74), (0.73, 1.74))]
        m.add(f'side_{s}', solid(w), 'upper side plate leaning in: the open bay wall', on='lower_body')
        y0, y1 = sorted((sd * 0.50, sd * 1.02))
        m.add(f'mudguard_{s}', slab(4.42, 5.38, y0, y1, 0.86, 0.92), 'mudguard over the front wheel', on='nose')
        y0, y1 = sorted((sd * 1.05, sd * 1.17))
        m.add(f'side_bin_{s}', slab(0.80, 2.60, y0, y1, 1.00, 1.26), 'stowage bins along the waist over the tracks', on='lower_body')
    m.add('tail', solid([(x, y, z) for x in (0.20, 0.27) for y, z in ((-0.98, 1.28), (0.98, 1.28), (-0.74, 1.74), (0.74, 1.74))]), 'rear plate with the doors', on='lower_body')
    m.add('cab', solid([(x, y, z) for x, w, h in ((3.20, 0.80, 1.74), (3.90, 0.74, 1.66)) for y in (-w, w) for z in (1.28, h)] + [(x, y, 1.28) for x in (3.20, 3.90) for y in (-1.05, 1.05)]),
          'roofed driving compartment at the front of the bay', on='lower_body')
    nose = [(3.90, y, z) for y, z in ((-0.72, 0.93), (0.72, 0.93), (-1.05, 1.28), (1.05, 1.28), (-0.74, 1.66), (0.74, 1.66))] + [(5.50, y, z) for y in (-0.42, 0.42) for z in (0.95, 1.22)]
    m.add('nose', solid(nose), 'sloped armoured nose over the engine, drawn to a point', on='chassis', contact=['lower_body', 'cab'])
    m.add('mg_shield', slab(3.24, 3.30, -0.34, 0.34, 1.74, 2.06, 'steel'), 'gun shield over the cab: the forward MG fires over it', on='cab')
    m.add('mg', rod((2.95, 0, 1.96), (3.95, 0, 1.96), 0.035), 'machine gun through the shield', on='mg_shield', small_ok=True)
    from .infantry import crewman, SIT
    for k, (x, y) in enumerate(((55, 20), (95, -20), (135, 20))):
        m.add(f'rider_{k}', crewman('de', SIT, (x, y, 70)), 'grenadier riding in the bay: helmets over the side say transport', on='lower_body', convex=False, small_ok=True)
    return m


def stug():
    """Brief
    is:       assault gun (StuG III Ausf. G), crew 4, 75 mm L/48 in the hull front
    does:     cheap tank killer and infantry support: a good gun and a low shape, but no turret: it must turn to aim
    gameplay: 2 x 1 tiles; ONE layer: the gun points where the hull points; very low; the player reads that it has no turret
    power:    engine at the rear, drive forward to FRONT sprockets
    moves:    six road wheels a side on torsion bars, three return rollers, rear idler; gun traverses a few degrees only
    built:    a low hull with a boxy casemate over the front half, sides sloped; rounded cast gun shield (pig's head)
    serviced: commander's cupola left rear of the casemate; loader's hatch with a folding MG shield, right
    references: StuG III G survivors (the low casemate, the rounded shield, six evenly spaced wheels)
    read_at_play_size: a very low long hull on six wheels, a slab casemate, a long gun low at the front with a knob
    """
    m = Machine('German assault gun (StuG III)')
    lw = 1.0
    m.add('upper_hull', solid(across([(0.10, 1.22), (0.10, 1.46), (4.25, 1.46), (4.25, 1.22)], -1.45, 1.45)), 'low hull and track covers; engine deck behind')
    m.add('lower_hull', solid(across([(0.30, 0.45), (0.05, 0.75), (0.05, 1.23), (4.25, 1.23), (5.15, 1.02), (5.22, 0.72), (4.80, 0.45)], -lw, lw)),
          'tub between the tracks; sloped nose over the transmission', on='upper_hull')
    top = running_gear(m, 'lower_hull', lw, 1.24, 0.40, [1.00 + 0.64 * k for k in range(6)], 0.26, (4.95, 0.72, 0.34), (0.45, 0.62, 0.30),
                       rollers=[1.45, 2.60, 3.75], rr=0.10, rz=0.98, belly=0.45)
    assert top < 1.22, top
    case = [(x, y, 1.46) for x in (2.15, 4.20) for y in (-1.40, 1.40)] + [(x, y, 1.96) for x in (2.35, 3.95) for y in (-1.05, 1.05)]
    m.add('casemate', solid(case), 'fixed fighting compartment over the front half: no ring, no turret, sides sloped in', on='upper_hull')
    ax, az = 4.12, 1.70
    m.add('mantlet', solid([(ax + x, y, az + z) for x, w, h in ((-0.10, 0.36, 0.26), (0.30, 0.30, 0.22), (0.62, 0.16, 0.14)) for y in (-w, w) for z in (-h, h)], 'steel', smooth=True),
          "rounded cast gun shield (the pig's head): the gun pivots inside it", on='casemate')
    gun(m, (ax + 0.62, 0, az), 2.70, 0.055, 'mantlet', brake=(0.11, 0.30), why='75 mm L/48, low in the hull front')
    m.add('cupola', disc(2.75, 0.55, 1.96, 2.14, 0.30), "commander's cupola, left rear of the roof: scale cue", on='casemate')
    m.add('mg_shield', slab(3.30, 3.36, -0.85, -0.25, 1.96, 2.26, 'steel'), "folding shield for the loader's machine gun", on='casemate')
    m.add('mg', rod((3.10, -0.55, 2.16), (3.85, -0.55, 2.16), 0.035), 'roof machine gun through the shield', on='mg_shield', small_ok=True)
    for sd, s in ((1, 'l'), (-1, 'r')):
        y0, y1 = sorted((sd * 1.02, sd * 1.45))
        m.add(f'mudguard_{s}', slab(4.23, 5.28, y0, y1, 1.205, 1.25, 'steel'), 'track guard forward over the sprocket', on='upper_hull')
    m.add('rear_stowage', slab(0.20, 1.10, -1.0, 1.0, 1.46, 1.70, 'canvas'), 'kit lashed on the engine deck', on='upper_hull')
    m.add('muffler', rod((-0.04, -0.55, 1.34), (-0.04, 0.55, 1.34), 0.13, 'exhaust'), 'muffler across the tail: marks the rear', on='upper_hull')
    return m


def blitz():
    """Brief
    is:       3-ton 4x2 cargo truck (Opel Blitz), driver and mate
    does:     hauls supplies and men; the supply or resource unit
    gameplay: 1 x 2 tiles, unarmed, soft; reads as a civilian-looking truck: rounded hood, closed cab, open wooden bed with a load
    power:    petrol engine under the rounded hood; drive to the rear axle (twin tyres)
    moves:    steering axle in front, one driven axle at the rear
    built:    ladder chassis; pressed rounded hood and steel cab; wooden drop-side bed
    references: Opel Blitz 3.6 survivors (rounded nose and cab, wooden bed, long rear overhang)
    read_at_play_size: a rounded nose and cab, a flat wooden bed with drums and crates, four wheels
    """
    m = Machine('German cargo truck (Opel Blitz)')
    m.add('chassis', slab(0.20, 5.60, -0.38, 0.38, 0.50, 0.74, 'steel'), 'ladder chassis')
    axle(m, 'rear_axle', 1.45, 0.43, 0.42, 0.80); axle(m, 'front_axle', 4.95, 0.43, 0.22, 0.82)
    m.add('bed_frame', slab(0.25, 3.50, -0.42, 0.42, 0.74, 0.96, 'steel'), 'sub-frame under the bed', on='chassis')
    m.add('bed', slab(0.20, 3.55, -1.10, 1.10, 0.94, 1.06, 'wood'), 'wooden bed floor, out over the rear wheels', on='bed_frame')
    for sd, s in ((1, 'l'), (-1, 'r')):
        y0, y1 = sorted((sd * 1.03, sd * 1.10))
        m.add(f'side_{s}', slab(0.20, 3.55, y0, y1, 1.06, 1.52, 'wood'), 'wooden drop side', on='bed')
        fen = [(x, sd * y, z) for x, z in ((4.58, 0.93), (4.72, 1.02), (5.30, 1.02), (5.52, 0.92), (4.58, 0.98), (5.52, 0.97)) for y in (0.48, 1.0)]
        m.add(f'fender_{s}', solid(fen), 'curved wing over the front wheel', on='hood')
    for nm, x in (('tailboard', 0.20), ('headboard', 3.48)):
        m.add(nm, slab(x, x + 0.07, -1.03, 1.03, 1.06, 1.52 if nm == 'tailboard' else 1.75, 'wood'), 'end board of the bed', on='bed')
    for k, (x, y) in enumerate(((0.75, 0.55), (0.75, -0.50), (1.45, 0.52))):
        m.add(f'drum_{k}', disc(x, y, 1.06, 1.94, 0.29, 'steel', seg=14), 'fuel drum: the load that says supply truck', on='bed')
    m.add('crates', slab(1.95, 3.35, -0.85, 0.85, 1.06, 1.68, 'wood'), 'crates stacked behind the cab', on='bed')
    m.add('cab', solid([(x, y, z) for x, w, h in ((3.62, 0.92, 2.02), (4.35, 0.92, 2.02), (4.55, 0.86, 1.56)) for y in (-w, w) for z in (0.74, h)], smooth=True), 'closed steel cab, rounded', on='chassis')
    m.add('hood', solid([(x, y, z) for x, w, h in ((4.55, 0.48, 1.52), (5.30, 0.44, 1.46), (5.62, 0.36, 1.30)) for y in (-w, w) for z in (0.74, h)], smooth=True),
          'rounded hood narrowing to the grille', on='chassis', contact=['cab'])
    m.add('bumper', slab(5.62, 5.72, -0.95, 0.95, 0.52, 0.68, 'steel'), 'bumper bar', on='chassis')
    return m


def tiger():
    """Brief
    is:       heavy tank (Tiger I), crew 5, 88 mm gun
    does:     the breakthrough tank: thick flat armour and a gun that kills anything; slow, costly, few
    gameplay: 2 x 1 tiles and the biggest thing on the field; a square box where the Panther is a wedge
    power:    engine at the rear, drive forward to FRONT sprockets
    moves:    eight axles of large overlapping road wheels a side, very wide tracks, rear idler, no return rollers
    built:    welded flat plate, almost nothing sloped: vertical sides, a vertical driver's plate over a short nose;
              a horseshoe turret with a wide flat gun shield and a bin on its back
    serviced: hatches on the roof corners; drum cupola left rear; two upright mufflers on the tail
    references: Tiger I survivors (the box hull wider than long-looking, the stepped front, the fat barrel sleeve)
    read_at_play_size: a wide square hull on very wide tracks, a round-backed turret, a thick long gun with a big knob
    """
    m = Machine('German heavy tank (Tiger I)')
    lw = 1.0
    m.add('upper_hull', solid(across([(0.10, 1.32), (0.10, 1.82), (4.85, 1.82), (4.85, 1.32)], -1.78, 1.78)), 'square superstructure, wider than the tub: vertical plates')
    m.add('lower_hull', solid(across([(0.30, 0.50), (0.05, 0.80), (0.05, 1.33), (4.85, 1.46), (5.85, 1.33), (6.00, 0.95), (5.60, 0.50)], -lw, lw)),
          'tub between the tracks; a short nose stepping down ahead of the driver', on='upper_hull')
    top = running_gear(m, 'lower_hull', lw, 1.42, 0.72, [1.10 + 0.55 * k for k in range(8)], 0.40, (5.75, 0.80, 0.37), (0.45, 0.66, 0.30),
                       interleave=True, belly=0.50, pitch=0.18)
    assert top < 1.32, top
    for sd, s in ((1, 'driver'), (-1, 'radio')):
        m.add(f'{s}_hatch', disc(4.35, sd * 1.15, 1.82, 1.86, 0.22), 'crew hatch on the roof corner: scale cue', on='upper_hull')
        y0, y1 = sorted((sd * 1.06, sd * 1.78))
        m.add(f'mudguard_{s}', slab(4.83, 6.22, y0, y1, 1.30, 1.345, 'steel'), 'track guard forward over the sprocket', on='upper_hull')
        m.add(f'muffler_{s}', disc(-0.12, sd * 0.48, 0.98, 1.78, 0.16, 'exhaust', seg=12), 'upright muffler in its shroud on the tail plate', on='lower_hull')
        y0, y1 = sorted((sd * 0.35, sd * 1.45))
        m.add(f'fan_{s}', slab(0.35, 1.45, y0, y1, 1.82, 1.86, 'steel'), 'engine deck grille', on='upper_hull')
    m.add('visor', slab(4.85, 4.93, 0.55, 1.05, 1.56, 1.74, 'steel'), "driver's visor block in the front plate: gives it a face", on='upper_hull')
    m.add('bow_gun', rod((4.85, -0.80, 1.62), (5.22, -0.80, 1.60), 0.04), 'bow machine gun in its ball mount', on='upper_hull', small_ok=True)
    tz = ring(m, 3.00, 1.82, 1.14)
    cast_turret(m, 3.00, tz, [(1.02, 0), (1.06, 0.05), (1.06, 0.72), (0.98, 0.77), (0, 0.79)], sx=1.06, why='horseshoe turret: one plate bent round, flat roof')
    m.add('bin', solid([(3.00 + x, y, tz + z) for x, w in ((-1.02, 0.62), (-1.52, 0.46)) for y in (-w, w) for z in (0.16, 0.56)]), 'stowage bin on the turret rear', on='turret')
    m.add('mantlet', slab(3.00 + 1.00, 3.00 + 1.26, -0.96, 0.96, tz + 0.08, tz + 0.70, 'steel'), 'wide flat gun shield across the whole turret front', on='turret')
    m.add('collar', rod((4.26, 0, tz + 0.40), (4.80, 0, tz + 0.40), 0.17), 'thick barrel sleeve: the fat root of the 88', on='mantlet')
    gun(m, (4.80, 0, tz + 0.40), 3.55, 0.072, 'collar', brake=(0.15, 0.44), why='88 mm L/56')
    m.add('cupola', disc(3.00 - 0.40, 0.50, tz + 0.79, tz + 1.03, 0.33), "commander's drum cupola, left rear", on='turret')
    return m


def howitzer_lefh():
    """Brief
    is:       10.5 cm light field howitzer (leFH 18M) on a split-trail carriage, crew figures separate
    does:     indirect fire from behind the line
    gameplay: 1 x 2 tiles emplaced; tells from the American piece by big wheels, a longer barrel and a muzzle brake
    moves:    barrel pitches on trunnions; trails spread; recoil gear under the barrel
    references: leFH 18 survivors (large pressed wheels, low shield, brake on the 18M)
    read_at_play_size: two big wheels, a low shield, a raised barrel with a knob, a V of trails
    """
    return howitzer('German 10.5 cm howitzer leFH 18', 0.62, 1.00, 0.16, 2.35, 0.075, 20, 1.52, 3.1, brake=(0.13, 0.36))


ALL = [('half track', 'Sd.Kfz. 251', sdkfz251), ('assault gun', 'StuG III G', stug), ('truck', 'Opel Blitz', blitz),
       ('heavy tank tiger', 'Tiger I', tiger), ('howitzer', '10.5 cm leFH 18', howitzer_lefh)]
