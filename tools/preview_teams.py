"""Crew weapons with their crews, placed by art/crew_layout.json, deployed (firing) and moving, at three weapon
headings: python3 tools/preview_teams.py art docs/previews. Draws as a game would: all shadows, then sprites back to front."""
import sys, os, json, math
from PIL import Image, ImageDraw
import preview_units as PU

S = 0.4


def scene(art, A, weapon, crew, H, t, clipset, fps=10):
    """[(depth, key, clip, heading index, frame, sx, sy)] for a weapon (or None) and its crew at weapon heading H."""
    items = []
    def frame(key, clip):
        c = A[key]['clips'][clip]; f = int(t * c['fps'] / fps)
        return f % c['frames'] if c['loop'] else min(f % (c['frames'] + 6), c['frames'] - 1)
    def pick(key):
        return next(c for c in clipset if c in A[key]['clips'])
    if weapon: items.append((0.0, weapon, pick(weapon), H // 45 % 8, 0, 0))
    c, s = math.cos(math.radians(H)), math.sin(math.radians(H))
    for i, m in enumerate(crew):
        x, y = m.get('x', -40 - 45 * i if not weapon else 0), m.get('y', (-1) ** i * 22 if not weapon else 0)
        wx, wy = c * x - s * y, s * x + c * y
        items.append((wx + wy, m['unit'], pick(m['unit']), ((H + m.get('heading', 0)) // 45) % 8, (wx - wy) * S, (wx + wy) / 2 * S))
    return [(d, k, cl, h, frame(k, cl), sx, sy) for d, k, cl, h, sx, sy in sorted(items)]


def main(art, out):
    os.makedirs(out, exist_ok=True)
    A = json.load(open(os.path.join(art, 'assets.json'))); L = json.load(open(os.path.join(art, 'crew_layout.json')))['weapons']
    cw, ch = 300, 200
    for side in ('us', 'de'):
        rows = []
        for w in (f'{side}_anti_tank_gun', f'{side}_tripod_mg', f'{side}_mortar'):
            rows.append((w + ', deployed', w, L[w]['crew'], ('fire', 'idle')))
            mv = L[w]['moving']; rows.append((w + ', moving', mv['weapon'], mv['crew'], ('walk', 'move', 'idle')))
        rk = f'{side}_rocket_gunner'; rows.append((rk + ' and loader', None, [dict(unit=rk, x=0, y=0)] + L[rk]['crew'], ('fire', 'idle')))
        frames = []
        for t in range(30):
            bg = Image.new('RGBA', (cw * 3, ch * len(rows)), PU.GROUND + (255,)); d = ImageDraw.Draw(bg)
            for r, (label, weapon, crew, clips) in enumerate(rows):
                for j, H in enumerate((0, 135, 270)):
                    sc = scene(art, A, weapon, crew, H, t, clips); ox, oy = j * cw + cw // 2, r * ch + ch // 2 + 10
                    for layer in ('S', None):
                        for _, k, cl, h, f, sx, sy in sc:
                            m = A[k]
                            for Ln in (('S',) if layer else ('L', 'F', 'U')):
                                if Ln not in m['layers']: continue
                                im = PU.cell(art, m, cl, Ln, h, f)
                                if im is None: continue
                                ax, ay = m['layers'][Ln]['anchor']; bg.alpha_composite(im, (round(ox + sx - ax), round(oy + sy - ay)))
                d.text((4, r * ch + ch - 15), label, fill=(240, 232, 200, 255), font=PU.font(11))
            frames.append(bg.resize((bg.size[0] * 2, bg.size[1] * 2), Image.NEAREST).convert('P', palette=Image.ADAPTIVE, colors=96))
        frames[0].save(f'{out}/{side}_crews.gif', save_all=True, append_images=frames[1:], duration=100, loop=0, optimize=True)
        frames[4].convert('RGB').save(f'{out}/{side}_crews.png')
        print(side, 'done')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
