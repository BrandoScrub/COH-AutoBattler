"""Open the game in headless Chrome, start a match, play a little, save screenshots and report console errors."""
import sys, time, asyncio
from playwright.async_api import async_playwright
URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8765/game/index.html'
OUT = sys.argv[2] if len(sys.argv) > 2 else '/tmp/shots'
SIDE = sys.argv[3] if len(sys.argv) > 3 else 'us'
import os; os.makedirs(OUT, exist_ok=True)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome', args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 1600, 'height': 900})
        errs = []
        pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append(f'pageerror: {e}'))
        await pg.goto(URL)
        await pg.wait_for_function("document.querySelector('#start') && !document.querySelector('#start').disabled", timeout=120000)
        await pg.screenshot(path=f'{OUT}/0-menu.png')
        await pg.click('#start' if SIDE == 'us' else '#start2')
        await pg.wait_for_timeout(1500)
        await pg.screenshot(path=f'{OUT}/1-start.png')
        # fast-forward the sim inside the page
        for i, secs in enumerate([60, 120, 180]):
            await pg.evaluate(f"""() => {{ for (let i = 0; i < {secs} * 20; i++) {{ AI.step(G, 1); AI.step(G, 0); SIM.step(G, SIM.DT); }} }}""")
            # look at the busiest spot
            await pg.evaluate("""() => { const es = G.ents.filter(e => !e.dead && e.type !== 'building' && e.owner === 0); if (es.length) { const e = es[es.length - 1]; RENDER.cam.x = e.x; RENDER.cam.y = e.y; HUD.ui.selected = new Set([e.id]); } }""")
            await pg.wait_for_timeout(700)
            await pg.screenshot(path=f'{OUT}/{i + 2}-t{secs}.png')
        info = await pg.evaluate("() => ({ t: G.t, ents: G.ents.length, over: G.over, renderer: RENDER.ctx.constructor && RENDER.ctx.constructor.name })")
        print('INFO', info)
        print('\n'.join(errs[:40]) or 'no console errors')
        await b.close()
asyncio.run(main())
