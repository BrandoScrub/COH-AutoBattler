"""Draw the exported units the way the runtime does (shadow layer, hull / legs layer at its anchor, turret / torso
layer at its own anchor), from assets.json alone: python3 tools/preview_units.py art docs/previews
Writes headings sheets (8 headings standing) and animated GIFs (move then fire) per side."""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

GROUND = (112, 104, 74)
MEN = ('rifleman', 'leader', 'flamethrower', 'sapper', 'rocket_gunner', 'mortar_gunner', 'mg_gunner', 'loader_box', 'loader_bomb', 'loader_rocket',
       'at_gunner', 'at_loader', 'at_commander', 'pusher', 'mg_carrier', 'tripod_carrier', 'tube_carrier', 'baseplate_carrier', 'sniper', 'lmg', 'assault_trooper')
_img = {}


def cell(art, man, clip, L, h, f):
    c = man['clips'][clip]
    if L not in c.get('rects', c.get('files', {})):
        c = next((k for k in man['clips'].values() if L in k.get('rects', k.get('files', {}))), None)
        if c is None: return None
    fw, fh = man['layers'][L]['frame']; f = min(f, c['frames'] - 1)
    out = np.zeros((fh, fw, 4), np.uint8)
    if 'rects' in c:
        a = c['rects'][L]; i = (h * c['frames'] + f) * 7; pg, x, y, w, hh, ox, oy = a[i:i + 7]
        if w:
            p = os.path.join(art, man['pack'][pg])
            if p not in _img: _img[p] = np.asarray(Image.open(p).convert('RGBA'))
            out[oy:oy + hh, ox:ox + w] = _img[p][y:y + hh, x:x + w]
    else:
        p = os.path.join(art, c['files'][L])
        if p not in _img: _img[p] = np.asarray(Image.open(p).convert('RGBA'))
        out = _img[p][h * fh:(h + 1) * fh, f * fw:(f + 1) * fw]
    return Image.fromarray(out, 'RGBA')


def draw(canvas, art, man, clip, h, f, x, y):
    for L in ('S', 'L', 'F', 'U'):
        if L not in man['layers']: continue
        im = cell(art, man, clip, L, h, f if L != 'S' or 'S' in man['clips'][clip].get('rects', man['clips'][clip].get('files', {})) else 0)
        if im is None: continue
        ax, ay = man['layers'][L]['anchor']; canvas.alpha_composite(im, (round(x - ax), round(y - ay)))


def box(man):
    """Cell size and anchor that hold every layer."""
    ax = max(l['anchor'][0] for l in man['layers'].values()); ay = max(l['anchor'][1] for l in man['layers'].values())
    r = max(l['frame'][0] - l['anchor'][0] for l in man['layers'].values()); d = max(l['frame'][1] - l['anchor'][1] for l in man['layers'].values())
    return int(ax + r) + 2, int(ay + d) + 2, ax + 1, ay + 1


def font(n=13):
    try: return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', n)
    except OSError: return ImageFont.load_default()


def headings(art, A, keys, out, zoom=2, per_row=8):
    rows = []
    for k in keys:
        m = A[k]; w, h, ax, ay = box(m); H = m['headings']
        im = Image.new('RGBA', (w * per_row, h + 18), GROUND + (255,))
        for i in range(min(per_row, H)): draw(im, art, m, 'idle', (i * H // min(per_row, H)) % H, 0, i * w + ax, ay)
        ImageDraw.Draw(im).text((4, h + 2), k, fill=(240, 232, 200, 255), font=font(11))
        rows.append(im)
    W = max(r.size[0] for r in rows); sheet = Image.new('RGBA', (W, sum(r.size[1] for r in rows)), GROUND + (255,)); y = 0
    for r in rows: sheet.alpha_composite(r, (0, y)); y += r.size[1]
    sheet.resize((sheet.size[0] * zoom, sheet.size[1] * zoom), Image.NEAREST).save(out)


def gif(art, A, keys, out, cols=3, heads=(7, 1, 4), ticks=40, fps=10, zoom=1, per_line=1):
    """Each unit at a few headings: its travelling clip, then its fire clip."""
    cells = [(k,) + box(A[k]) for k in keys]
    cw = max(c[1] for c in cells); ch = max(c[2] for c in cells) + 16
    n = len(cells); lines = -(-n // per_line)
    frames = []
    for t in range(ticks):
        bg = Image.new('RGBA', (cw * cols * per_line, ch * lines), GROUND + (255,)); d = ImageDraw.Draw(bg)
        for i, (k, w, h, ax, ay) in enumerate(cells):
            m = A[k]; C = m['clips']; bx = (i % per_line) * cw * cols; by = (i // per_line) * ch
            trav = next((c for c in ('move', 'walk') if c in C), 'idle'); second = 'fire' if 'fire' in C else trav
            clip = trav if t < ticks // 2 else second; c = C[clip]; tt = t if t < ticks // 2 else t - ticks // 2
            f = int(tt * c['fps'] / fps); f = f % c['frames'] if c['loop'] else (f % (c['frames'] + 5) if f % (c['frames'] + 5) < c['frames'] else c['frames'] - 1)
            for j, hd in enumerate(heads):
                draw(bg, art, m, clip, hd * m['headings'] // 8, f, bx + j * cw + (cw - w) // 2 + ax, by + (ch - 16 - h) + ay)
            d.text((bx + 4, by + ch - 15), f'{k}: {clip}', fill=(240, 232, 200, 255), font=font(11))
        if zoom != 1: bg = bg.resize((bg.size[0] * zoom, bg.size[1] * zoom), Image.NEAREST)
        frames.append(bg.convert('P', palette=Image.ADAPTIVE, colors=96))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=1000 // fps, loop=0, optimize=True)


if __name__ == '__main__':
    art, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    A = json.load(open(os.path.join(art, 'assets.json')))
    only = sys.argv[3:]; TAG = 'new_' if only else ''
    for side in ('us', 'de'):
        K = [k for k in A if k.startswith(side + '_') and (not only or any(o in k for o in only))]
        men = [k for k in K if k.split('_', 1)[1] in MEN]; machines = [k for k in K if k not in men]
        headings(art, A, machines, f'{out}/{side}_{TAG}vehicles_headings.png', zoom=1, per_row=16)
        headings(art, A, men, f'{out}/{side}_{TAG}infantry_headings.png', zoom=2)
        gif(art, A, machines, f'{out}/{side}_{TAG}vehicles.gif', per_line=2)
        gif(art, A, men, f'{out}/{side}_{TAG}infantry.gif', zoom=2, per_line=2)
        print(side, len(machines), 'machines,', len(men), 'men')
