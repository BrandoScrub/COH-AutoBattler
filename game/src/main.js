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
    applyLayout.zoomed = false; applyLayout();
    HUD.flash(side === 'us' ? 'US Forces: take the victory points. Engineers build your base.' : 'Wehrmacht: take the victory points. Place buildings from the HQ, Pioneers raise them.');
    if (!running) { running = true; last = performance.now(); requestAnimationFrame(loop); }
  }
  /* touch mode: chosen in the menu, or automatic for coarse pointers and small screens */
  let ctl = 'auto', rotOk = false;
  try { ctl = localStorage.getItem('tw2-ctl') || 'auto'; } catch (e) {}
  const isTouch = () => ctl === 'touch' || (ctl === 'auto' && ((matchMedia && matchMedia('(pointer: coarse)').matches) || Math.min(innerWidth, innerHeight) < 500));
  function applyLayout() {
    const m = isTouch(), b = document.body;
    b.classList.toggle('mobile', m);
    b.classList.toggle('portrait', m && innerHeight > innerWidth && !rotOk);
    const s = m ? Math.min(1, innerWidth / 1060, innerHeight / 640) : 1;
    document.documentElement.style.setProperty('--s', Math.max(.45, s).toFixed(3));
    if (m && RENDER.cam && G && !applyLayout.zoomed) { RENDER.cam.k = .8; applyLayout.zoomed = true; }
  }
  function resize() { const c = $('#view'); c.width = innerWidth; c.height = innerHeight; RENDER.resize(innerWidth, innerHeight, 1); applyLayout(); }
  addEventListener('resize', resize);

  function loop(now) {
    requestAnimationFrame(loop);
    const dt = Math.min(.1, (now - last) / 1000); last = now;
    if (!G) return;
    if (!inMenu && !HUD.ui.paused && !G.over) {
      acc += dt * speed;
      let n = 0;
      while (acc >= SIM.DT && n++ < 8) { snap(G); AI.step(G, 1); SIM.step(G, SIM.DT); acc -= SIM.DT; }
      if (n > 8) acc = 0;
    }
    HUD.tick(dt);
    if (G.t !== fogT && ((G.t * 4) | 0) !== ((fogT * 4) | 0)) { RENDER.updateFogCanvas(G, 0); fogT = G.t; }
    const a = inMenu || HUD.ui.paused || G.over ? 1 : Math.min(1, acc / SIM.DT);
    lerpIn(G, a); RENDER.frame(G, HUD.ui, a); lerpOut(G);
    HUD.drawSelectBox();
    hudT -= dt; if (hudT <= 0) { HUD.update(); hudT = .1; }
    mmT -= dt; if (mmT <= 0) { HUD.drawMinimap(); mmT = .2; }
    if (G.over && !G.overShown) { G.overShown = true; showEnd(); }
  }
  /* Smooth drawing between simulation steps: remember where things were before each step, draw them partway
     from there to where they are now, then put the true values back so nothing outside drawing sees the blend. */
  function snap(G) {
    G.prevT = G.t;
    for (const e of G.ents) {
      if (e.dead || e.type === 'building') continue;
      e.pv = [e.x, e.y, e.heading, e.turret];
      if (e.models) for (const m of e.models) m.pv = [m.x, m.y, m.heading];
      if (e.crew) e.crew.pv = [e.crew.x, e.crew.y, e.crew.heading];
    }
  }
  let saved = [], savedT = null;
  function blend(o, keys, a) {
    const p = o.pv; if (!p) return;
    const keep = keys.map(k => o[k]);
    if (Math.abs(o.x - p[0]) + Math.abs(o.y - p[1]) > 4) return;   // a jump (spawn, teleport): draw where it is
    keys.forEach((k, i) => {
      if (p[i] == null || o[k] == null) return;
      o[k] = k === 'x' || k === 'y' ? p[i] + (o[k] - p[i]) * a : p[i] + U.angNorm(o[k] - p[i]) * a;
    });
    saved.push(o, keys, keep);
  }
  function lerpIn(G, a) {
    saved.length = 0; savedT = null;
    if (a >= 1 || G.prevT == null) return;
    savedT = G.t; G.t = G.prevT + (G.t - G.prevT) * a;
    for (const e of G.ents) {
      if (e.dead || e.type === 'building') continue;
      blend(e, ['x', 'y', 'heading', 'turret'], a);
      if (e.models) for (const m of e.models) if (m.alive) blend(m, ['x', 'y', 'heading'], a);
      if (e.crew) blend(e.crew, ['x', 'y', 'heading'], a);
    }
  }
  function lerpOut(G) {
    for (let i = 0; i < saved.length; i += 3) { const o = saved[i], keys = saved[i + 1], v = saved[i + 2]; keys.forEach((k, j) => { o[k] = v[j]; }); }
    saved.length = 0;
    if (savedT != null) { G.t = savedT; savedT = null; }
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
    $('#ctl').value = ctl;
    $('#ctl').addEventListener('change', ev => { ctl = ev.target.value; try { localStorage.setItem('tw2-ctl', ctl); } catch (e) {} applyLayout(); });
    $('#rotok').addEventListener('click', () => { rotOk = true; applyLayout(); });
    applyLayout();
    boot();
  });
  return { menu, inMenu: () => inMenu, start };
})();
