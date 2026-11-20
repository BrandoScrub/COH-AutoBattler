"""Play the opening through real input: select the HQ, order the first base building from its card (it is placed
automatically and the builders raise it), pick the order new units start on, train infantry, then change a unit's
standing order from its card. Checks that the player cannot move a unit by hand."""
import sys, asyncio
from playwright.async_api import async_playwright
SIDE = sys.argv[1] if len(sys.argv) > 1 else 'de'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome', args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 1600, 'height': 900})
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e) + ' @ ' + (e.stack or '').split(chr(10))[1:3].__str__()))
        await pg.goto('http://localhost:8765/game/index.html')
        await pg.wait_for_function("!document.querySelector('#start').disabled", timeout=120000)
        await pg.click('#mm-skirmish'); await pg.click('#start' if SIDE == 'us' else '#start2'); await pg.wait_for_timeout(600)
        await pg.mouse.move(800, 400)
        print('selected at start', await pg.evaluate("() => [...HUD.ui.selected].map(id => G.byId.get(id).defId)"))
        await pg.screenshot(path='/tmp/shots/flow-hq.png')
        await pg.keyboard.press('z')                      # bottom-left slot of the HQ card: the first base building
        await pg.wait_for_timeout(300)
        st = "() => G.ents.filter(e => e.owner === 0).map(e => e.defId + (e.type === 'building' ? ':' + e.built.toFixed(2) : ':' + e.order.type + '/' + e.role))"
        print('after ordering the building', await pg.evaluate(st), '| banner:', await pg.evaluate("() => document.querySelector('.banner').textContent"))
        # a right click on the field with the builders selected must not move them
        await pg.evaluate("() => { HUD.ui.selected = new Set(G.ents.filter(e => e.owner === 0 && e.type === 'squad').map(e => e.id)); }")
        before = await pg.evaluate("() => G.ents.filter(e => e.owner === 0 && e.type === 'squad').map(e => e.order.type)")
        await pg.mouse.click(1100, 300, button='right'); await pg.wait_for_timeout(200)
        after = await pg.evaluate("() => G.ents.filter(e => e.owner === 0 && e.type === 'squad').map(e => e.order.type)")
        print('right click leaves orders alone', before == after, before, after)
        await pg.evaluate("() => { for (let i = 0; i < 20 * 25; i++) { AI.step(G, 1); AI.step(G, 0, true); SIM.step(G, SIM.DT); } }")
        print('25 s later', await pg.evaluate(st))
        # select the new building, set new units to Hunt (middle row, second slot: S), train two with Q
        await pg.evaluate("() => { const b = G.ents.find(e => e.type === 'building' && e.owner === 0 && !e.def.retreat); HUD.ui.selected = new Set([b.id]); G.players[0].res.mp = 800; }")
        await pg.wait_for_timeout(300)
        await pg.keyboard.press('s'); await pg.keyboard.press('q'); await pg.keyboard.press('q')
        await pg.wait_for_timeout(400)
        await pg.screenshot(path='/tmp/shots/flow-queue.png')
        print('queue', await pg.evaluate("() => G.ents.filter(e => e.type === 'building' && e.owner === 0).map(b => b.defId + ' [' + b.queue.map(q => q.unit + '/' + q.role).join(',') + ']')"))
        await pg.evaluate("() => { for (let i = 0; i < 20 * 50; i++) { AI.step(G, 1); AI.step(G, 0, true); SIM.step(G, SIM.DT); } }")
        print('50 s later', await pg.evaluate(st))
        # select a trained squad and switch it to Defend (top row, third slot: E)
        await pg.evaluate("() => { const u = G.ents.find(e => e.owner === 0 && e.type === 'squad' && !e.def.builder); HUD.ui.selected = new Set([u.id]); RENDER.cam.x = u.x; RENDER.cam.y = u.y; }")
        await pg.wait_for_timeout(300)
        await pg.keyboard.press('e'); await pg.wait_for_timeout(300)
        await pg.screenshot(path='/tmp/shots/flow-unit.png')
        print('unit order after E', await pg.evaluate("() => [...HUD.ui.selected].map(id => G.byId.get(id).defId + '/' + G.byId.get(id).role)"))
        print(errs or 'no page errors')
        await b.close()
asyncio.run(main())
