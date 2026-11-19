/* Boot, menus and the main loop. The simulation runs at a fixed 20 steps a second; drawing runs every frame. */
const MAIN = (() => {
  const ART = (window.ART_BASE || '../art/');
  let G = null, lib = {}, layout = null, assets = null, inMenu = true, last = 0, acc = 0, hudT = 0, mmT = 0, fogT = -1, running = false, speed = 1;
  const $ = s => document.querySelector(s);

  async function boot() {
    const status = $('#loadstatus');
    try {
      status.textContent = 'Loading unit art…';
      [assets, layout] = await Promise.all([fetch(ART + 'assets.json').then(r => r.json()), fetch(ART + 'crew_layout.json').then(r => r.json())]);
      let n = 0; const total = Object.keys(assets).length;
      await new Promise(res => ArtKit.load(ART, assets, lib, () => res()));
      // ArtKit.load fires once everything is in; count for the bar
      status.textContent = 'Ready';
      $('#start').disabled = false; $('#start2').disabled = false;
    } catch (err) { status.textContent = 'Could not load the art: ' + err.message; console.error(err); }
  }

  function start(side) {
    $('#menu').classList.add('hide'); $('#end').classList.add('hide');
    G = SIM.create({ seed: 7, playerSide: side, crewLayout: layout });
    window.G = G;
    const canvas = $('#view');
    if (!running) { RENDER.init(canvas, lib, G); } else { RENDER.init(canvas, lib, G); }
    HUD.init(G, canvas);
    HUD.ui.selected = new Set(G.ents.filter(e => e.owner === 0 && e.type === 'squad').map(e => e.id));
    resize();
    inMenu = false;
    HUD.flash(side === 'us' ? 'US Forces: take the victory points. Engineers build your base.' : 'Wehrmacht: take the victory points. Place buildings from the HQ, Pioneers raise them.');
    if (!running) { running = true; last = performance.now(); requestAnimationFrame(loop); }
  }
  function resize() { const c = $('#view'); c.width = innerWidth; c.height = innerHeight; RENDER.resize(innerWidth, innerHeight, 1); }
  addEventListener('resize', resize);

  function loop(now) {
    requestAnimationFrame(loop);
    const dt = Math.min(.1, (now - last) / 1000); last = now;
    if (!G) return;
    if (!inMenu && !HUD.ui.paused && !G.over) {
      acc += dt * speed;
      let n = 0;
      while (acc >= SIM.DT && n++ < 8) { AI.step(G, 1); SIM.step(G, SIM.DT); acc -= SIM.DT; }
    }
    HUD.tick(dt);
    if (G.t !== fogT && ((G.t * 4) | 0) !== ((fogT * 4) | 0)) { RENDER.updateFogCanvas(G, 0); fogT = G.t; }
    RENDER.frame(G, HUD.ui, 0);
    HUD.drawSelectBox();
    hudT -= dt; if (hudT <= 0) { HUD.update(); hudT = .1; }
    mmT -= dt; if (mmT <= 0) { HUD.drawMinimap(); mmT = .2; }
    if (G.over && !G.overShown) { G.overShown = true; showEnd(); }
  }
  function showEnd() {
    const won = G.over.winner === 0, e = $('#end');
    e.querySelector('h2').textContent = won ? 'Victory' : 'Defeat';
    e.querySelector('p').textContent = G.over.reason + ' at ' + U.fmtTime(G.t) + '.';
    e.classList.remove('hide');
  }
  function menu(show) {
    if (!G) return;
    inMenu = !!show; $('#pausemenu').classList.toggle('hide', !show);
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('#start').addEventListener('click', () => start('us'));
    $('#start2').addEventListener('click', () => start('de'));
    $('#resume').addEventListener('click', () => menu(false));
    $('#quit').addEventListener('click', () => { menu(false); $('#menu').classList.remove('hide'); inMenu = true; });
    $('#again').addEventListener('click', () => { $('#end').classList.add('hide'); $('#menu').classList.remove('hide'); inMenu = true; });
    $('#speed').addEventListener('change', ev => { speed = +ev.target.value; });
    boot();
  });
  return { menu, inMenu: () => inMenu, start };
})();
