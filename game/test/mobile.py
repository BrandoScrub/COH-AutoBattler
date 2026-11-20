"""Phone check: landscape iPhone viewport with touch. Taps select, card buttons set orders and spend, drag pans, pinch zooms; no tap moves a unit."""
import asyncio, sys
from playwright.async_api import async_playwright
URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8765/game/index.html'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome', args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        ctx = await b.new_context(viewport={'width': 844, 'height': 390}, device_scale_factor=2, is_mobile=True, has_touch=True)
        pg = await ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        cdp = await ctx.new_cdp_session(pg)
        async def touch(kind, pts):
            await cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [{'x': x, 'y': y, 'id': i} for i, (x, y) in enumerate(pts)]})
        async def tap(x, y): await touch('touchStart', [(x, y)]); await pg.wait_for_timeout(60); await touch('touchEnd', [])
        await pg.goto(URL)
        await pg.wait_for_function("!document.querySelector('#start').disabled", timeout=120000)
        await pg.screenshot(path='/tmp/shots/m0-menu.png')
        await pg.tap('#mm-skirmish'); await pg.wait_for_timeout(200); await pg.screenshot(path='/tmp/shots/m0b-skirmish.png'); await pg.tap('#start'); await pg.wait_for_timeout(800)
        await pg.evaluate("() => { HUD.ui.paused = true; }")
        print('mobile class', await pg.evaluate("document.body.className"), await pg.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--s')"))
        await pg.screenshot(path='/tmp/shots/m1-start.png')
        # the HQ card: tap the first base building (bottom row, first slot); it is placed for the player
        await pg.tap('.card .slot:nth-child(9)'); await pg.wait_for_timeout(300)
        print('after HQ building tap', await pg.evaluate("() => G.ents.filter(e => e.owner === 0 && e.type === 'building').map(b => b.defId + ':' + b.built.toFixed(2))"), '| banner:', await pg.evaluate("() => document.querySelector('.banner').textContent"))
        await pg.screenshot(path='/tmp/shots/m2-build.png')
        # new units start on Defend (middle row, third slot)
        await pg.tap('.card .slot:nth-child(7)'); await pg.wait_for_timeout(200)
        print('new units start on', await pg.evaluate("() => G.players[0].newRole"))
        # tap empty ground with the engineers selected -> nothing is ordered, the selection clears
        await pg.evaluate("() => { HUD.ui.selected = new Set(G.ents.filter(e => e.owner === 0 && e.type === 'squad').map(e => e.id)); }")
        sel = await pg.evaluate("() => [...HUD.ui.selected]")
        o0 = await pg.evaluate("(ids) => ids.map(id => G.byId.get(id).order.type)", sel)
        await tap(600, 150); await pg.wait_for_timeout(300)
        print('ground tap leaves orders alone', o0 == await pg.evaluate("(ids) => ids.map(id => G.byId.get(id).order.type)", sel), '| selection now', await pg.evaluate("() => HUD.ui.selected.size"))
        # clear, then tap on the engineers to select them
        await pg.evaluate("() => { HUD.ui.selected.clear(); }")
        await pg.wait_for_timeout(200)
        pos = await pg.evaluate("() => { const s = G.ents.find(e => e.type === 'squad' && e.owner === 0); const m = s.models.find(q => q.alive); return RENDER.toScreen(m.x, m.y, .8); }")
        await tap(pos[0], pos[1]); await pg.wait_for_timeout(300)
        print('selected after tap on unit', await pg.evaluate("() => [...HUD.ui.selected].map(id => G.byId.get(id).defId)"))
        # drag pans
        c0 = await pg.evaluate("() => [RENDER.cam.x, RENDER.cam.y]")
        await touch('touchStart', [(500, 200)])
        for i in range(1, 8): await touch('touchMove', [(500 - i * 25, 200 - i * 8)]); await pg.wait_for_timeout(16)
        await touch('touchEnd', [])
        c1 = await pg.evaluate("() => [RENDER.cam.x, RENDER.cam.y]")
        print('pan moved camera', [round(a - b, 1) for a, b in zip(c1, c0)], 'selection kept', await pg.evaluate("() => HUD.ui.selected.size"))
        # pinch zooms
        k0 = await pg.evaluate("() => RENDER.cam.k")
        await touch('touchStart', [(400, 200), (460, 200)])
        for i in range(1, 8): await touch('touchMove', [(400 - i * 12, 200), (460 + i * 12, 200)]); await pg.wait_for_timeout(16)
        await touch('touchEnd', [])
        print('pinch zoom', round(k0, 2), '->', await pg.evaluate("() => +RENDER.cam.k.toFixed(2)"))
        # a unit's card: tap Hunt (top row, second slot), then long-press a button to read it
        await pg.tap('.card .slot:nth-child(2)'); await pg.wait_for_timeout(300)
        print('unit order after Hunt tap', await pg.evaluate("() => [...HUD.ui.selected].map(id => G.byId.get(id).defId + '/' + G.byId.get(id).role)"))
        await pg.screenshot(path='/tmp/shots/m2b-unit.png')
        # minimap tap moves the camera
        box = await pg.locator('.mmframe canvas').bounding_box()
        await tap(box['x'] + box['width'] * .8, box['y'] + box['height'] * .5); await pg.wait_for_timeout(200)
        print('cam after minimap tap', await pg.evaluate("() => [RENDER.cam.x|0, RENDER.cam.y|0]"))
        # portrait prompt
        await pg.set_viewport_size({'width': 390, 'height': 844}); await pg.wait_for_timeout(300)
        print('portrait class', await pg.evaluate("document.body.className"))
        await pg.screenshot(path='/tmp/shots/m3-portrait.png')
        await pg.set_viewport_size({'width': 844, 'height': 390}); await pg.wait_for_timeout(300)
        await pg.evaluate("() => { HUD.ui.paused = false; G.players[0].res.mp = 2000; const hq = SIM.hqOf(G, 0); for (let i = 0; i < 20 * 150; i++) { if (i % 600 === 0) for (const b of G.ents) if (b.type === 'building' && b.owner === 0 && b.built >= 1 && !b.def.retreat) SIM.issue(G, [b.id], { type: 'produce', unit: b.def.produce[0], role: ['capture', 'hunt', 'defend'][i / 600 % 3 | 0] }); AI.step(G, 1); AI.step(G, 0, true); SIM.step(G, SIM.DT); } const e = G.ents.filter(e => e.owner === 0 && e.type === 'squad' && !e.dead).pop(); if (e) { RENDER.cam.x = e.x; RENDER.cam.y = e.y; HUD.ui.selected = new Set([e.id]); } }")
        await pg.wait_for_timeout(800)
        await pg.screenshot(path='/tmp/shots/m4-play.png')
        print(errs or 'no page errors')
        await b.close()
asyncio.run(main())
