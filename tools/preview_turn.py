"""Vehicles turning through every heading: python3 tools/preview_turn.py art docs/previews/<name>.gif key [key ...]
Top row of each unit: hull and turret turn together. Bottom row: the hull turns, the turret stays on one bearing."""
import sys, os, json
from PIL import Image, ImageDraw
import preview_units as PU


def put(bg, art, m, clip, layers, h, f, x, y):
    for L in layers:
        if L not in m['layers']: continue
        im = PU.cell(art, m, clip, L, h, f)
        if im is None: continue
        ax, ay = m['layers'][L]['anchor']; bg.alpha_composite(im, (round(x - ax), round(y - ay)))


def main(art, out, keys):
    A = json.load(open(os.path.join(art, 'assets.json')))
    boxes = {k: PU.box(A[k]) for k in keys}
    cw = max(b[0] for b in boxes.values()) + 10; ch = max(b[1] for b in boxes.values()) + 4
    frames = []
    H = max(A[k]['headings'] for k in keys)
    for t in range(H * 2):
        bg = Image.new('RGBA', (cw * 2, ch * len(keys) + 20), PU.GROUND + (255,)); d = ImageDraw.Draw(bg)
        for r, k in enumerate(keys):
            m = A[k]; n = m['headings']; h = (t * n // (H * 2)) % n; w, hh, ax, ay = boxes[k]
            mv = m['clips']['move']; f = t % mv['frames']
            for col, turret in ((0, h), (1, (n // 8) % n)):
                x, y = col * cw + (cw - w) // 2 + ax, r * ch + ay + 2
                put(bg, art, m, 'move', ('S',), h, f, x, y); put(bg, art, m, 'move', ('L', 'F'), h, f, x, y)
                put(bg, art, m, 'idle', ('U',), turret, 0, x, y)
            d.text((4, r * ch + 4), f'{k}  {n} headings', fill=(240, 232, 200, 255), font=PU.font(11))
        d.text((4, ch * len(keys) + 4), 'left: turret turns with the hull     right: turret holds one bearing', fill=(240, 232, 200, 255), font=PU.font(11))
        frames.append(bg.convert('P', palette=Image.ADAPTIVE, colors=96))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=120, loop=0, optimize=True)
    frames[5].convert('RGB').save(os.path.splitext(out)[0] + '.png')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
