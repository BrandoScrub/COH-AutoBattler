"""Stage a firefight in the middle of the map and photograph it."""
import sys, asyncio
from playwright.async_api import async_playwright
SIDE = sys.argv[1] if len(sys.argv) > 1 else 'us'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome', args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 1600, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/game/index.html')
        await pg.wait_for_function("!document.querySelector('#start').disabled", timeout=120000)
        await pg.click('#mm-skirmish'); await pg.click('#start' if SIDE == 'us' else '#start2'); await pg.wait_for_timeout(500)
        await pg.evaluate("""() => {
          const us = G.players[0].side, de = G.players[1].side, P = (a, b) => a + '_' + b;
          const A = [['riflemen', 'grenadiers'], ['hmg', 'hmg'], ['sherman', 'pz4'], ['at_gun', 'at_gun'], ['m8', '222']];
          const sp = (id, o, x, y) => (DATA.SQUADS[id] ? SIM.spawnSquad : SIM.spawnVehicle)(G, id, o, x, y);
          const mine = [], theirs = [];
          A.forEach(([u, d], i) => {
            const myId = us === 'us' ? 'us_' + u : 'de_' + d, enId = us === 'us' ? 'de_' + d : 'us_' + u;
            if (DATA.SQUADS[myId] || DATA.VEHICLES[myId]) mine.push(sp(myId, 0, 84 + i * 4, 116 - i * 4));
            if (DATA.SQUADS[enId] || DATA.VEHICLES[enId]) theirs.push(sp(enId, 1, 112 + i * 4, 88 - i * 4));
          });
          G.players[0].res.mu = 300;
          RENDER.cam.x = 100; RENDER.cam.y = 100; RENDER.cam.k = 1.05;
          HUD.ui.selected = new Set([mine[0].id]);
          SIM.issue(G, mine.map(e => e.id), { type: 'attackMove', x: 100, y: 100 });
          SIM.issue(G, theirs.map(e => e.id), { type: 'attackMove', x: 100, y: 100 });
          window._stage = { mine: mine.map(e => e.id), theirs: theirs.map(e => e.id) };
        }""")
        for i, wait in enumerate([6000, 6000, 8000]):
            await pg.wait_for_timeout(wait)
            await pg.screenshot(path=f'/tmp/shots/battle{i}.png')
        print(await pg.evaluate("() => _stage.mine.concat(_stage.theirs).map(id => { const e = G.byId.get(id); return e ? e.defId + ':' + (e.type === 'squad' ? e.models.filter(m => m.alive).length : Math.round(e.hp)) : 'dead'; })"))
        print(errs or 'no page errors')
        await b.close()
asyncio.run(main())
