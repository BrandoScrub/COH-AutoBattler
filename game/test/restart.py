"""Start a match, quit to the menu, start another: input must still be handled exactly once."""
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(channel='chrome', args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 1400, 'height': 860}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
        await pg.goto('http://localhost:8765/game/index.html')
        await pg.wait_for_function("!document.querySelector('#start').disabled", timeout=120000)
        await pg.click('#mm-skirmish'); await pg.click('#start2'); await pg.wait_for_timeout(500)
        await pg.keyboard.press('F10'); await pg.wait_for_timeout(200); await pg.click('#quit'); await pg.wait_for_timeout(200)
        await pg.click('#mm-skirmish'); await pg.click('#start'); await pg.wait_for_timeout(500)
        await pg.mouse.move(700, 400)
        await pg.keyboard.press('Space'); await pg.wait_for_timeout(100)
        print('paused after one Space:', await pg.evaluate("HUD.ui.paused"))
        await pg.keyboard.press('Space')
        print('side', await pg.evaluate("G.players[0].side"), 'roster tiles', await pg.locator('.ru').count())
        print(errs or 'no errors')
        await b.close()
asyncio.run(main())
