/* HUD and controls. This is an autobattler: the player spends resources (units, base buildings, upgrades) and gives
   each unit a standing order (capture, hunt, defend, supply; see ai.js), and the units move and fight on their own.
   Nothing here moves a unit directly; the one direct order left is Retreat.
   Laid out after the annotated CoH3 boards in docs/reference/coh3:
   status top-left, victory ticker top-centre, roster top-right, minimap bottom-left, resources + production tabs +
   unit panel + 4x3 command card bottom-right, command-point dial on the right edge. The command card binds keys by
   slot position (QWER / ASDF / ZXCV), so every unit uses the same finger for the same slot. */
const HUD = (() => {
  const KEYS = ['Q', 'W', 'E', 'R', 'A', 'S', 'D', 'F', 'Z', 'X', 'C', 'V'];
  const D = DATA;
  const ui = { selected: new Set(), hover: null, hoverPoint: null, mode: null, page: 'main', ghost: null, coverPreview: null, paused: false, noFog: false, lastClick: 0 };
  let G, el = {}, canvasEl, iconCache = {}, cardSlots = [], lastPanelKey = '', tip = null;

  const $ = s => document.querySelector(s);
  /* write a node's HTML only when it changed: rebuilding unchanged HUD parts ten times a second costs layout and image work on phones */
  function put(node, html) { if (node._h !== html) { node.innerHTML = html; node._h = html; } }
  function h(tag, cls, html) { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  const fmt = v => Math.floor(v).toString();
  const costStr = c => [c.mp ? `<span class="c-mp">${c.mp}</span>` : '', c.mu ? `<span class="c-mu">${c.mu}</span>` : '', c.fu ? `<span class="c-fu">${c.fu}</span>` : ''].join(' ');

  /* ---------------- button icons drawn once ---------------- */
  function icon(name, draw, w = 44, hgt = 44) {
    if (iconCache[name]) return iconCache[name];
    const c = document.createElement('canvas'); c.width = w; c.height = hgt; const g = c.getContext('2d');
    g.translate(w / 2, hgt / 2); g.strokeStyle = g.fillStyle = '#e8dcc0'; g.lineWidth = 3; g.lineCap = 'round'; g.lineJoin = 'round';
    draw(g);
    return iconCache[name] = c.toDataURL();
  }
  const ICONS = {
    attackMove: g => { g.beginPath(); g.arc(0, 0, 11, 0, 7); g.moveTo(-17, 0); g.lineTo(-6, 0); g.moveTo(6, 0); g.lineTo(17, 0); g.moveTo(0, -17); g.lineTo(0, -6); g.moveTo(0, 6); g.lineTo(0, 17); g.stroke(); },
    stop: g => { g.fillRect(-10, -10, 20, 20); },
    retreat: g => { g.fillStyle = '#ff5a4a'; g.beginPath(); g.moveTo(-14, 0); g.lineTo(2, -13); g.lineTo(2, -5); g.lineTo(14, -5); g.lineTo(14, 5); g.lineTo(2, 5); g.lineTo(2, 13); g.closePath(); g.fill(); },
    reverse: g => { g.beginPath(); g.moveTo(10, -10); g.lineTo(-8, -10); g.moveTo(-3, -15); g.lineTo(-9, -10); g.lineTo(-3, -5); g.moveTo(-10, 10); g.lineTo(8, 10); g.moveTo(3, 5); g.lineTo(9, 10); g.lineTo(3, 15); g.stroke(); },
    build: g => { g.save(); g.rotate(-.7); g.fillRect(-3, -4, 6, 20); g.fillRect(-10, -14, 20, 10); g.restore(); },
    repair: g => { g.lineWidth = 4; g.beginPath(); g.moveTo(-10, 10); g.lineTo(6, -6); g.stroke(); g.beginPath(); g.arc(8, -8, 6, 0, 7); g.stroke(); },
    back: g => { g.fillStyle = '#e8dcc0'; g.beginPath(); g.moveTo(-14, 0); g.lineTo(0, -12); g.lineTo(0, -5); g.lineTo(14, -5); g.lineTo(14, 5); g.lineTo(0, 5); g.lineTo(0, 12); g.closePath(); g.fill(); },
    grenade: g => { g.beginPath(); g.ellipse(0, 3, 9, 11, 0, 0, 7); g.fill(); g.fillStyle = '#333'; g.fillRect(-8, -1, 16, 2); g.fillRect(-1, -10, 2, 24); g.fillStyle = '#e8dcc0'; g.fillRect(-3, -15, 6, 6); },
    barrage: g => { for (let i = -1; i <= 1; i++) { g.beginPath(); g.moveTo(i * 9, -14); g.lineTo(i * 9, 6); g.stroke(); g.beginPath(); g.arc(i * 9, 10, 3, 0, 7); g.fill(); } },
    setup: g => { g.beginPath(); g.moveTo(-12, 10); g.lineTo(0, -4); g.lineTo(12, 10); g.moveTo(0, -4); g.lineTo(0, -14); g.stroke(); },
    rally: g => { g.strokeStyle = '#ddd'; g.beginPath(); g.moveTo(-8, 14); g.lineTo(-8, -14); g.stroke(); g.fillStyle = '#ff5a4a'; g.beginPath(); g.moveTo(-8, -14); g.lineTo(12, -8); g.lineTo(-8, -2); g.closePath(); g.fill(); },
    reinforce: g => { g.fillStyle = '#c33'; g.beginPath(); g.arc(0, 0, 15, 0, 7); g.fill(); g.fillStyle = '#fff'; g.fillRect(-3, -10, 6, 20); g.fillRect(-10, -3, 20, 6); },
    sandbags: g => { g.fillStyle = '#c9b88c'; for (let r = 0; r < 2; r++) for (let i = 0; i < 3 - r; i++) { g.beginPath(); g.ellipse(-12 + i * 12 + r * 6, 8 - r * 9, 7, 5, 0, 0, 7); g.fill(); g.strokeStyle = '#5a4a30'; g.lineWidth = 1; g.stroke(); } },
    wire: g => { g.lineWidth = 1.5; g.beginPath(); for (let i = 0; i <= 12; i++) { const x = -16 + i * 2.7, y = Math.sin(i * 1.7) * 6; i ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); g.lineWidth = 3; g.beginPath(); g.moveTo(-14, -10); g.lineTo(-14, 12); g.moveTo(14, -10); g.lineTo(14, 12); g.stroke(); },
    tanktrap: g => { g.lineWidth = 4; g.beginPath(); g.moveTo(-12, 12); g.lineTo(12, -12); g.moveTo(-12, -12); g.lineTo(12, 12); g.moveTo(0, -15); g.lineTo(0, 15); g.stroke(); },
    flame: g => { g.fillStyle = '#ff9a3a'; g.beginPath(); g.moveTo(0, -15); g.quadraticCurveTo(14, 0, 6, 14); g.quadraticCurveTo(0, 6, -6, 14); g.quadraticCurveTo(-14, 0, 0, -15); g.fill(); },
    lmg: g => { g.lineWidth = 3; g.beginPath(); g.moveTo(-15, 3); g.lineTo(15, -3); g.moveTo(5, -1); g.lineTo(3, 10); g.moveTo(-3, 1); g.lineTo(-6, 10); g.stroke(); },
    smoke: g => { g.fillStyle = '#c9c9c4'; for (const [x, y, r] of [[-7, 4, 8], [4, 2, 9], [-1, -7, 8], [9, -6, 6]]) { g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); } g.fillStyle = '#555'; g.fillRect(-12, 10, 6, 6); },
    breach: g => { g.fillStyle = '#8a6a44'; g.fillRect(-8, -14, 16, 26); g.fillStyle = '#222'; g.fillRect(-5, -10, 10, 22); g.fillStyle = '#ffb03a'; g.beginPath(); for (let i = 0; i < 10; i++) { const a = i * Math.PI / 5, r = i % 2 ? 5 : 11; g.lineTo(9 + Math.cos(a) * r, 2 + Math.sin(a) * r); } g.fill(); },
    unload: g => { g.fillStyle = '#c9b88c'; g.beginPath(); g.moveTo(-14, -2); g.lineTo(-4, -12); g.lineTo(6, -2); g.lineTo(6, 12); g.lineTo(-14, 12); g.closePath(); g.fill(); g.fillStyle = '#5ad6ff'; g.beginPath(); g.moveTo(16, 4); g.lineTo(6, -4); g.lineTo(6, 0); g.lineTo(-2, 0); g.lineTo(-2, 8); g.lineTo(6, 8); g.lineTo(6, 12); g.closePath(); g.fill(); },
    roleCapture: g => { g.strokeStyle = '#ddd'; g.beginPath(); g.moveTo(-9, 15); g.lineTo(-9, -15); g.stroke(); g.fillStyle = '#e6b450'; g.beginPath(); g.moveTo(-9, -15); g.lineTo(14, -8); g.lineTo(-9, -1); g.closePath(); g.fill(); },
    roleHunt: g => { g.strokeStyle = '#ff6a5a'; g.beginPath(); g.arc(0, 0, 11, 0, 7); g.moveTo(-17, 0); g.lineTo(-5, 0); g.moveTo(5, 0); g.lineTo(17, 0); g.moveTo(0, -17); g.lineTo(0, -5); g.moveTo(0, 5); g.lineTo(0, 17); g.stroke(); g.fillStyle = '#ff6a5a'; g.beginPath(); g.arc(0, 0, 2.5, 0, 7); g.fill(); },
    roleDefend: g => { g.fillStyle = '#6cb6ff'; g.beginPath(); g.moveTo(-12, -13); g.lineTo(12, -13); g.lineTo(12, 2); g.quadraticCurveTo(10, 12, 0, 16); g.quadraticCurveTo(-10, 12, -12, 2); g.closePath(); g.fill(); },
    roleSupply: g => { g.fillStyle = '#8fca5a'; g.fillRect(-13, -4, 26, 17); g.strokeStyle = '#2c4a18'; g.lineWidth = 2; g.strokeRect(-13, -4, 26, 17); g.beginPath(); g.moveTo(0, -4); g.lineTo(0, 13); g.stroke(); g.fillStyle = '#b9e58a'; g.fillRect(-9, -13, 18, 8); },
    lock: g => { g.strokeStyle = '#999'; g.beginPath(); g.arc(0, -4, 7, Math.PI, 0); g.stroke(); g.fillStyle = '#999'; g.fillRect(-10, -4, 20, 15); },
  };
  const ico = name => icon(name, ICONS[name] || ICONS.stop);
  function unitIcon(id) {
    const key = 'u:' + id; if (iconCache[key]) return iconCache[key];
    const def = D.SQUADS[id] || D.VEHICLES[id]; const c = document.createElement('canvas'); c.width = 64; c.height = 64;
    const fake = D.SQUADS[id] ? { type: 'squad', def, owner: G.players.findIndex(P => P.side === def.side), crew: null } : { type: 'vehicle', def, owner: G.players.findIndex(P => P.side === def.side) };
    if (!RENDER.portrait(G, fake, c)) return '';
    return iconCache[key] = c.toDataURL();
  }
  function buildingIcon(id) {
    const key = 'b:' + id; if (iconCache[key]) return iconCache[key];
    const def = D.BUILDINGS[id], side = def.side, c = document.createElement('canvas'); c.width = 64; c.height = 64; const g = c.getContext('2d');
    g.fillStyle = side === 'us' ? '#7c7a5e' : '#77705f'; g.beginPath(); g.moveTo(8, 34); g.lineTo(32, 46); g.lineTo(56, 34); g.lineTo(56, 22); g.lineTo(32, 34); g.lineTo(8, 22); g.closePath(); g.fill();
    g.fillStyle = side === 'us' ? '#58603e' : '#5b5145'; g.beginPath(); g.moveTo(8, 22); g.lineTo(32, 10); g.lineTo(56, 22); g.lineTo(32, 34); g.closePath(); g.fill();
    g.save(); g.translate(32, 25); g.scale(1.1, 1.1); g.fillStyle = g.strokeStyle = '#eee'; (RENDER.GLYPHS[def.glyph] || RENDER.GLYPHS.house)(g); g.restore();
    return iconCache[key] = c.toDataURL();
  }

  /* ---------------- build the DOM ---------------- */
  /* every order the player gives goes through here; watching an AI match, nothing is ordered */
  const PLAYER_ORDERS = new Set(['produce', 'cancel', 'upgrade', 'retreat', 'role']);
  function issue(...a) { if (G.spectate || !PLAYER_ORDERS.has(a[2].type)) return; return SIM.issue(...a); }
  const roleOf = e => AI.ROLES[e.role] ? e.role : null;
  function init(game, canvas) {
    G = game; canvasEl = canvas; if (!G.players[0].newRole) G.players[0].newRole = 'capture';
    const root = $('#hud'); root.innerHTML = '';
    el.ticker = h('div', 'ticker', `<div class="vp vp0"><b></b><i><s></s></i></div><div class="stars"></div><div class="vp vp1"><i><s></s></i><b></b></div><div class="clock"></div>`);
    el.alerts = h('div', 'alerts');
    el.roster = h('div', 'roster', '<div class="r-units"></div><div class="r-structs"></div>');
    el.mm = h('div', 'mmwrap', `<div class="mmframe"><canvas width="236" height="236"></canvas><div class="north">N</div></div>
      <div class="mmbtns"><button data-a="menu" title="Menu (F10)">&#9776;</button><button data-a="selv" title="Select all vehicles">${'<img src="' + glyphIcon('tank') + '">'}</button><button data-a="seli" title="Select all infantry">${'<img src="' + glyphIcon('infantry') + '">'}</button><button data-a="height" title="Height view (H)">&#9650;</button><span class="logo">COH<br>AUTO</span><button data-a="pause" title="Tactical pause (Space)">&#10074;&#10074;</button></div>`);
    el.bg = h('div', 'bgstrip', `<div class="bgtile" title="Battlegroups: the structure is in place (choose one of three, two branches, pick-one pairs). Content arrives when the battlegroups are designed."><span>BATTLE<br>GROUP</span></div><div class="dial" title="Command points: earned from veterancy experience; spend them on battlegroup abilities once battlegroups exist."><b>0</b><svg viewBox="0 0 40 40"><circle cx="20" cy="20" r="17" /></svg></div>`);
    el.bottom = h('div', 'bottom', `
      <div class="resrow"><div class="res mp"><i></i><b></b><small></small></div><div class="res mu"><i></i><b></b><small></small></div><div class="res fu"><i></i><b></b><small></small></div><div class="res pop"><i></i><b></b><small></small></div></div>
      <div class="tabs"></div>
      <div class="panel"><canvas class="portrait" width="128" height="128"></canvas><div class="pbody"></div></div>
      <div class="slotcol"></div>
      <div class="card"></div>`);
    el.tip = h('div', 'tip');
    el.banner = h('div', 'banner');
    root.append(el.ticker, el.alerts, el.roster, el.mm, el.bg, el.bottom, el.tip, el.banner);
    el.spec = null;
    if (G.spectate) {
      // watching the AI: both armies' purses and a speed switch under the score ticker
      el.spec = h('div', 'specbar', `<div class="sp0"></div><div class="spd">${[1, 2, 4, 8].map(x => `<button data-x="${x}">${x}x</button>`).join('')}</div><div class="sp1"></div>`);
      el.spec.addEventListener('click', ev => { const b = ev.target.closest('[data-x]'); if (b) MAIN.setSpeed(+b.dataset.x); });
      root.append(el.spec);
    }
    el.mmc = el.mm.querySelector('canvas');
    el.card = el.bottom.querySelector('.card');
    for (let i = 0; i < 12; i++) {
      const b = h('button', 'slot', `<img><span class="k">${KEYS[i]}</span><span class="cd"></span><span class="cost"></span>`);
      b.addEventListener('click', () => pressSlot(i));
      b.addEventListener('mouseenter', () => { if (!ui.touch) showTip(i, b); }); b.addEventListener('mouseleave', () => { if (!ui.touch) hideTip(); });
      b.addEventListener('pointerdown', ev => { if (ev.pointerType !== 'touch') return; clearTimeout(b._lp); b._lpDone = false; b._lp = setTimeout(() => { b._lpDone = true; showTip(i, b); }, 450); });
      b.addEventListener('pointerup', ev => { if (ev.pointerType !== 'touch') return; clearTimeout(b._lp); if (b._lpDone) setTimeout(hideTip, 1600); });
      b.addEventListener('click', ev => { if (b._lpDone) { ev.stopImmediatePropagation(); b._lpDone = false; } }, true);
      el.card.appendChild(b); cardSlots.push(b);
    }
    el.mm.querySelectorAll('.mmbtns button').forEach(b => b.addEventListener('click', () => mmButton(b.dataset.a)));
    el.bottom.querySelector('.tabs').addEventListener('click', ev => { const t = ev.target.closest('[data-b]'); if (t) selectBuildingType(t.dataset.b); });
    el.roster.addEventListener('click', ev => { const t = ev.target.closest('[data-id]'); if (!t) return; const id = +t.dataset.id; if (ev.shiftKey) ui.selected.add(id); else { ui.selected = new Set([id]); } ui.page = 'main'; if (ev.detail === 2) centreOn(G.byId.get(id)); });
    el.alerts.addEventListener('click', ev => { const t = ev.target.closest('[data-x]'); if (t) { RENDER.cam.x = +t.dataset.x; RENDER.cam.y = +t.dataset.y; } });
    el.bottom.querySelector('.slotcol').addEventListener('click', ev => { const t = ev.target.closest('[data-act]'); if (t) slotColAct(t.dataset.act); });
    el.bottom.querySelector('.panel').addEventListener('click', ev => { const t = ev.target.closest('[data-q]'); if (t) { const b = primary(); if (b && b.type === 'building') issue(G, [b.id], { type: 'cancel', index: +t.dataset.q }); } });
    bindInput(); bindTouch();
  }
  function glyphIcon(gl) { return icon('g:' + gl, g => { g.scale(1.5, 1.5); (RENDER.GLYPHS[gl])(g); }, 36, 36); }

  /* ---------------- selection helpers ---------------- */
  const selEnts = () => [...ui.selected].map(id => G.byId.get(id)).filter(e => e && !e.dead);
  function primary() { const s = selEnts(); return s[0] || null; }
  function centreOn(e) { if (!e) return; RENDER.cam.x = e.x; RENDER.cam.y = e.y; }
  function centreOnGroup(ids) { const es = ids.map(id => G.byId.get(id)).filter(e => e && !e.dead); if (!es.length) return; RENDER.cam.x = es.reduce((a, e) => a + e.x, 0) / es.length; RENDER.cam.y = es.reduce((a, e) => a + e.y, 0) / es.length; }
  function groupOf(id) { const g = G.players[0].groups; for (const k in g) if (g[k].includes(id)) return k; return null; }
  ui.groupOf = groupOf;
  function selectBuildingType(defId) { const b = G.ents.filter(e => e.type === 'building' && e.owner === 0 && e.defId === defId && !e.dead); if (!b.length) return; ui.selected = new Set([b[0].id]); ui.page = 'main'; }

  /* ---------------- command card ---------------- */
  function cardFor() {
    const sel = G.spectate ? [] : selEnts().filter(e => e.owner === 0), out = new Array(12).fill(null);
    if (!sel.length) return out;
    const e = sel[0], P = G.players[0], roles = Object.keys(AI.ROLES);
    if (e.type === 'building') {
      if (e.built < 1) return out;
      // top row: the units it trains; they start on the order picked in the middle row
      e.def.produce.slice(0, 4).forEach((u, i) => {
        const def = SIM.unitDef(u), why = SIM.prodBlock(G, e, u), r = def.builder ? 'supply' : P.newRole;
        out[i] = { img: unitIcon(u), label: def.name, tip: `<b>${def.name}</b><div class="role">${def.role}</div>${def.standIn ? '<div class="note">Stand-in: ' + def.standIn + '</div>' : ''}<div>${costStr(def.cost)} &middot; ${def.pop} pop &middot; ${def.time}s</div><div class="note">Starts on: ${AI.ROLES[r].name}</div>`, cost: def.cost, disabled: !!why, why, act: () => issue(G, [e.id], { type: 'produce', unit: u, role: r }) };
      });
      // middle row: the order new units start on (all buildings share it)
      roles.forEach((r, i) => { const R = AI.ROLES[r]; out[4 + i] = { img: ico(R.icon), label: 'New units: ' + R.name, tip: `<b>New units: ${R.name}</b><div>${R.tip}</div><div class="note">Units trained from now on start on this order. Tap a unit to change its order later.</div>`, on: P.newRole === r, act: () => { P.newRole = r; flash('New units start on ' + R.name); } }; });
      // bottom row, HQ only: the next base buildings; a free spot by the HQ is picked and the builders raise it
      if (e.def.retreat) P.F.buildings.forEach((bid, i) => {
        const def = D.BUILDINGS[bid], why = SIM.buildReqMissing(G, 0, bid) || (!SIM.canAfford(P, def.cost) ? 'Not enough resources' : null);
        if (why === 'Already built') return;
        out[8 + i] = { img: buildingIcon(bid), label: def.name, tip: `<b>${def.name}</b><div>Produces: ${def.produce.map(u => SIM.unitDef(u).name).join(', ')}</div><div>${costStr(def.cost)} &middot; ${def.time}s build</div><div class="note">Placed by the HQ for you; ${SIM.unitDef(P.F.builder).name}s raise it.</div>`, cost: def.cost, disabled: !!why, why, act: () => { const err = AI.build(G, 0, bid); flash(err || def.name + ' ordered'); } };
      });
      return out;
    }
    // units: top row is the standing order (applies to everything selected); the unit works it by itself
    const ids = sel.filter(s => s.type !== 'building').map(s => s.id);
    roles.forEach((r, i) => { const R = AI.ROLES[r]; out[i] = { img: ico(R.icon), label: R.name, tip: `<b>${R.name}</b><div>${R.tip}</div>`, on: sel.every(s => s.role === r), act: () => { issue(G, ids, { type: 'role', role: r }); flash((ids.length > 1 ? ids.length + ' units: ' : e.def.name + ': ') + R.name); } }; });
    out[4] = { img: ico('retreat'), label: 'Retreat', tip: '<b>Retreat</b><div>Fall back to the headquarters. It cannot be called off. Units also retreat on their own when they are losing.</div>', act: () => issue(G, ids, { type: 'retreat' }) };
    if (e.type === 'squad') {
      let u = 8;
      for (const up of e.def.upgrades || []) {
        const done = e.upgrades.has(up.id), busy = e.upgrading, why = done ? 'Fitted' : busy ? 'Upgrading' : !SIM.canAfford(P, up.cost) ? 'Not enough munitions' : !SIM.nearReinforcePoint(G, e) ? 'Must be near a base building' : null;
        out[u++] = { img: ico(up.swap && up.swap.sprite === 'flamethrower' ? 'flame' : 'lmg'), label: up.name, tip: `<b>${up.name}</b><div>${costStr(up.cost)} &middot; ${up.time}s</div>`, cost: up.cost, disabled: !!why, why, done, act: () => issue(G, [e.id], { type: 'upgrade', id: up.id }) };
      }
    }
    return out;
  }
  function pressSlot(i) { const s = cardFor()[i]; if (!s || s.disabled) { if (s && s.why) flash(s.why); return; } s.act(); }
  function slotColAct(a) {
    const P = G.players[0];
    if (a === 'reinforce') { P.autoReinforce = !P.autoReinforce; flash('Automatic reinforcement ' + (P.autoReinforce ? 'on' : 'off')); }
  }
  function flash(text) { el.banner.textContent = text; el.banner.classList.add('on'); clearTimeout(flash.t); flash.t = setTimeout(() => el.banner.classList.remove('on'), 1600); }
  function showTip(i, b) { const s = cardFor()[i]; if (!s) return; tip = i; el.tip.innerHTML = s.tip + (s.why && s.disabled ? `<div class="why">${s.why}</div>` : '') + `<span class="hk">${KEYS[i]}</span>`; el.tip.classList.add('on'); }
  function hideTip() { tip = null; el.tip.classList.remove('on'); }

  /* ---------------- update (10x a second) ---------------- */
  function update() {
    // a selected squad that crewed a gun: the new gun team joins the selection (and replaces the squad if it is gone)
    if (G.became) for (const id of [...ui.selected]) { const nid = G.became[id]; if (nid != null) { ui.selected.add(nid); if (!G.byId.get(id)) ui.selected.delete(id); delete G.became[id]; } }
    const P = G.players[0], E = G.players[1];
    // ticker
    const vpS = D.ECON.vpStart;
    el.ticker.querySelector('.vp0 b').textContent = Math.ceil(P.vp); el.ticker.querySelector('.vp1 b').textContent = Math.ceil(E.vp);
    el.ticker.querySelector('.vp0 s').style.width = (P.vp / vpS * 100) + '%'; el.ticker.querySelector('.vp1 s').style.width = (E.vp / vpS * 100) + '%';
    put(el.ticker.querySelector('.stars'), G.map.points.filter(p => p.type === 'victory').map(p => `<span class="star o${p.owner}">&#9733;</span>`).join(''));
    el.ticker.querySelector('.clock').textContent = U.fmtTime(G.t);
    if (el.spec) {
      const line = Q => `<b style="color:${Q.F.colour}">${Q.F.name}</b> ${fmt(Q.res.mp)} mp &middot; ${fmt(Q.res.mu)} mu &middot; ${fmt(Q.res.fu)} fu &middot; pop ${Q.pop}/${Q.popCap}`;
      put(el.spec.querySelector('.sp0'), line(P)); put(el.spec.querySelector('.sp1'), line(E));
      el.spec.querySelectorAll('[data-x]').forEach(b => b.classList.toggle('on', +b.dataset.x === MAIN.speed()));
    }
    // resources
    const rs = el.bottom.querySelectorAll('.res');
    [['mp', 'mp'], ['mu', 'mu'], ['fu', 'fu']].forEach(([k], i) => { rs[i].querySelector('b').textContent = fmt(P.res[k]); const inc = P.income[k]; rs[i].querySelector('small').textContent = inc > .05 ? '+' + Math.round(inc) : ''; });
    rs[3].querySelector('b').textContent = P.pop + '/' + P.popCap; rs[3].classList.toggle('capped', P.pop >= P.popCap);
    // tabs: one per production building type, lit when owned
    const tabs = el.bottom.querySelector('.tabs');
    const types = [P.F.hq, ...P.F.buildings], sel = primary();
    put(tabs, '<div class="tab blank"></div>' + types.map(t => { const own = G.ents.some(b => b.type === 'building' && b.owner === 0 && b.defId === t && !b.dead); return `<div class="tab ${own ? 'own' : ''} ${sel && sel.defId === t ? 'on' : ''}" data-b="${t}" title="${D.BUILDINGS[t].name}"><img src="${glyphIcon(D.BUILDINGS[t].glyph)}"></div>`; }).join(''));
    updateAlerts(); updateRoster(); updatePanel(); updateCard();
    // command points dial (veterancy XP feeds it; nothing to spend yet)
    const xp = G.ents.filter(e => e.owner === 0 && e.type !== 'building').reduce((a, e) => a + (e.xp || 0), 0) + (P.xpBank || 0);
    const cp = Math.floor(xp / 1200), frac = (xp % 1200) / 1200;
    el.bg.querySelector('.dial b').textContent = cp; el.bg.querySelector('.dial circle').style.strokeDashoffset = (107 * (1 - frac)).toFixed(1);
  }
  function updateAlerts() {
    const P = G.players[0], now = G.t;
    const list = P.alerts.filter(a => now - a.t < 9).slice(-5);
    put(el.alerts, list.map(a => `<div class="al ${a.kind}" data-x="${a.x}" data-y="${a.y}"><i></i>${a.text}</div>`).join(''));
  }
  function updateRoster() {
    const units = G.ents.filter(e => e.owner === 0 && !e.dead && e.type !== 'building');
    units.sort((a, b) => (a.type === 'vehicle' ? 0 : 1) - (b.type === 'vehicle' ? 0 : 1) || a.id - b.id);
    const html = units.map(e => {
      const n = e.type === 'squad' ? e.models.filter(m => m.alive).length : '';
      const st = e.type === 'squad' ? (e.retreating ? '<em class="ret"></em>' : e.suppState ? '<em class="sup">!</em>' : G.t - e.lastHit < 4 ? '<em class="hit">!</em>' : '') : (G.t - e.lastHit < 4 ? '<em class="hit">!</em>' : '');
      const hpf = e.type === 'vehicle' ? e.hp / e.maxHp : e.models.reduce((a, m) => a + (m.alive ? m.hp : 0), 0) / (e.def.hp * e.maxModels);
      return `<div class="ru ${ui.selected.has(e.id) ? 'sel' : ''}" data-id="${e.id}" title="${e.def.name}"><img src="${glyphIcon(e.def.glyph)}">${n !== '' ? `<b>${n}</b>` : ''}${e.vet ? `<u>${'&#9733;'.repeat(e.vet)}</u>` : ''}${groupOf(e.id) ? `<span class="grp">${groupOf(e.id)}</span>` : ''}${roleOf(e) ? `<span class="rl r-${e.role}">${AI.ROLES[e.role].name[0]}</span>` : ''}${st}<i style="width:${Math.round(hpf * 100)}%"></i></div>`;
    }).join('');
    if (html !== el.roster._u) { el.roster.querySelector('.r-units').innerHTML = html; el.roster._u = html; }
    const bs = G.ents.filter(e => e.owner === 0 && !e.dead && e.type === 'building');
    const h2 = bs.map(b => `<div class="rs ${ui.selected.has(b.id) ? 'sel' : ''}" data-id="${b.id}" title="${b.def.name}"><img src="${glyphIcon(b.def.glyph)}">${b.built < 1 ? `<i style="width:${Math.round(b.built * 100)}%"></i>` : b.queue.length ? `<i style="width:${Math.round(b.queue[0].t / b.queue[0].total * 100)}%" class="q"></i>` : ''}</div>`).join('');
    if (h2 !== el.roster._s) { el.roster.querySelector('.r-structs').innerHTML = h2; el.roster._s = h2; }
  }
  function updatePanel() {
    const body = el.bottom.querySelector('.pbody'), pc = el.bottom.querySelector('.portrait'), sc = el.bottom.querySelector('.slotcol');
    const sel = selEnts();
    if (!sel.length) { put(body, '<div class="empty">Nothing selected</div>'); pc.getContext('2d').clearRect(0, 0, 128, 128); put(sc, ''); lastPanelKey = ''; return; }
    if (sel.length > 1) {
      const key = 'multi:' + sel.map(e => e.id).join(',');
      put(body, `<div class="multi">${sel.slice(0, 18).map(e => `<div class="mt o${e.owner}" title="${e.def.name}"><img src="${glyphIcon(e.def.glyph || 'house')}"><b>${e.type === 'squad' ? e.models.filter(m => m.alive).length : ''}</b></div>`).join('')}</div>`);
      if (key !== lastPanelKey) { pc.getContext('2d').clearRect(0, 0, 128, 128); lastPanelKey = key; }
      put(sc, ''); return;
    }
    const e = sel[0], P = G.players[e.owner] || { F: { name: 'Abandoned' } }, own = e.owner === 0;
    const key = e.id + ':' + (e.crew ? e.crew.state : '') + ':' + (e.type === 'building' ? e.built >= 1 : '');
    if (key !== lastPanelKey) { if (e.type === 'building') drawBuildingPortrait(pc, e); else RENDER.portrait(G, e, pc); lastPanelKey = key; }
    const name = `<div class="own" style="color:${RENDER.TEAM[e.owner] || '#bbb'}">${own ? 'You' : e.owner < 0 ? 'Nobody' : 'Enemy'} &middot; ${P.F.name}</div><h3>${e.def.name}</h3>`;
    if (e.type === 'building') {
      const hp = Math.max(0, e.hp / e.maxHp);
      put(body, name + (e.def.reinforce ? '<div class="hl">Can reinforce infantry.</div>' : '') +
        `<div class="desc">${e.built < 1 ? 'Under construction: ' + Math.round(e.built * 100) + '%' : 'Produces: ' + e.def.produce.map(u => SIM.unitDef(u).name).join(', ') + '.'}</div>` +
        (own && e.queue.length ? `<div class="queue">${e.queue.map((q, i) => `<div class="qi" data-q="${i}" title="Click to cancel"><img src="${unitIcon(q.unit)}"><i style="width:${i ? 0 : Math.round(q.t / q.total * 100)}%"></i></div>`).join('')}</div>` : '') +
        `<div class="hp"><i style="width:${hp * 100}%"></i><span>${Math.ceil(e.hp)} / ${e.maxHp}</span></div>`);
      put(sc, own && e.def.retreat ? `<button class="toggle ${P.autoReinforce ? 'on' : ''}" data-act="reinforce" title="Automatic reinforcement: squads that have lost men refill near base buildings and pay manpower for each man. Toggle off to keep the manpower."><img src="${ico('reinforce')}"><span class="k">T</span></button>` : '');
      return;
    }
    const th = e.def.vet || [1000, 3000, 6000], next = th[Math.min(2, e.vet)], prev = e.vet ? th[e.vet - 1] : 0;
    const xpf = e.vet >= 3 ? 1 : (e.xp - prev) / (next - prev);
    let strength = '', hpf;
    if (e.type === 'squad') { const al = e.models.filter(m => m.alive); strength = `<span class="str">&#128100; ${al.length}/${e.maxModels}</span>`; hpf = al.reduce((a, m) => a + m.hp, 0) / (al.length ? al.length * al[0].maxHp : 1); }
    else hpf = e.hp / e.maxHp;
    const cov = e.type === 'squad' ? COMBAT.squadCover(G, e) : null;
    const state = e.type === 'squad' ? (e.retreating ? 'Retreating' : e.garrison != null ? 'In a building' : e.suppState === 2 ? 'Pinned' : e.suppState === 1 ? 'Suppressed' : e.crew ? ({ packed: 'Packed up', setting: 'Setting up', deployed: 'Set up', tearing: 'Packing up' })[e.crew.state] : e.building ? 'Building' : e.upgrading ? 'Upgrading: ' + Math.round(e.upgrading.t / e.upgrading.total * 100) + '%' : '') : (e.owner < 0 ? 'Abandoned: infantry nearby will recrew it' : e.crit ? [e.crit.engine === 2 ? 'Immobilised' : e.crit.engine === 1 ? 'Engine damaged' : '', e.crit.gun ? 'Main gun destroyed' : '', e.crit.shockT > G.t ? 'Crew shocked' : ''].filter(Boolean).join(' · ') || (e.order.type === 'reverse' ? 'Reversing' : '') : e.order.type === 'reverse' ? 'Reversing' : '');
    const weapons = e.type === 'squad' ? [...new Set(e.models.filter(m => m.alive && m.weapon).map(m => D.W[m.weapon].name).concat(e.def.crewWeapon ? [D.W[e.def.weapons[0]].name] : []))] : e.def.weapons.map(w => D.W[w].name);
    put(body, name + (own && roleOf(e) ? `<div class="ord r-${e.role}">Order: ${AI.ROLES[e.role].name}</div>` : '') + `<div class="role">${e.def.role}</div>${e.def.standIn ? '<div class="note">Stand-in: ' + e.def.standIn + '</div>' : ''}` +
      `<div class="vet"><span class="vs">${[0, 1, 2].map(i => `<b class="${i < e.vet ? 'on' : ''}">&#9733;</b>`).join('')}</span><span class="xpbar"><i style="width:${Math.round(U.clamp(xpf, 0, 1) * 100)}%"></i></span><span class="xpt">XP: ${Math.floor(e.xp)}/${e.vet >= 3 ? th[2] : next}</span></div>` +
      `<div class="line">${strength}${(() => { const h = MAP.hAt(G.map, e.x, e.y); return h >= 1.5 ? `<span class="elev" title="Elevation: sees further; from 2.5 m above a target it fires over the target's cover">&#9650; ${h.toFixed(0)} m</span>` : ''; })()}${cov ? `<span class="cov" style="color:${D.COVER[cov].colour}">&#9960; ${cov === 'none' ? 'no' : cov} cover</span>` : ''}${state ? `<span class="state">${state}</span>` : ''}</div>` +
      `<div class="weap">${weapons.join(' &middot; ')}</div>` +
      (e.type === 'vehicle' ? `<div class="armor">Armour ${e.def.armor.join(' / ')} (front / side / rear)</div>` : '') +
      `<div class="hp"><i style="width:${Math.round(hpf * 100)}%"></i></div>`);
    put(sc, (e.upgrades && e.upgrades.size ? [...e.upgrades].map(u => `<div class="eq" title="${(e.def.upgrades.find(x => x.id === u) || {}).name}"><img src="${ico(u === 'flame' ? 'flame' : 'lmg')}"></div>`).join('') : ''));
  }
  function drawBuildingPortrait(cv, b) {
    const g = cv.getContext('2d'); g.clearRect(0, 0, cv.width, cv.height);
    const im = new Image(); im.onload = () => g.drawImage(im, 0, 0, cv.width, cv.height); im.src = buildingIcon(b.defId);
  }
  function updateCard() {
    const slots = cardFor();
    slots.forEach((s, i) => {
      const b = cardSlots[i];
      b.classList.toggle('empty', !s); b.classList.toggle('dis', !!(s && s.disabled)); b.classList.toggle('done', !!(s && s.done));
      b.classList.toggle('armed', !!(s && s.on));
      const img = b.querySelector('img');
      if (!s) { img.removeAttribute('src'); b.querySelector('.cd').textContent = ''; put(b.querySelector('.cost'), ''); return; }
      if (img.getAttribute('src') !== s.img) img.src = s.img;
      b.querySelector('.cd').textContent = s.cd > 0 ? Math.ceil(s.cd) : '';
      put(b.querySelector('.cost'), s.cost && !s.done ? costStr(s.cost) : '');
    });
    if (tip != null) { const s = slots[tip]; if (!s) hideTip(); }
  }

  /* ---------------- minimap (rotated 45 degrees to match the camera) ---------------- */
  /* a diamond: the map turned 45 degrees like the camera, not squashed */
  function mmQ() { return el.mmc.width / (2 * G.map.w) * .98; }
  function mmToScreen(x, y) { const q = mmQ(), mx = x - G.map.w / 2, my = y - G.map.h / 2; return [el.mmc.width / 2 + (mx - my) * q, el.mmc.height / 2 + (mx + my) * q]; }
  function mmToWorld(px, py) { const q = mmQ(), a = (px - el.mmc.width / 2) / q, b = (py - el.mmc.height / 2) / q; return [(a + b) / 2 + G.map.w / 2, (b - a) / 2 + G.map.h / 2]; }
  function drawMinimap() {
    const c = el.mmc, g = c.getContext('2d'), m = G.map;
    g.clearRect(0, 0, c.width, c.height);
    if (!el.mmBase) {
      // terrain base, once
      const b = document.createElement('canvas'); b.width = c.width; b.height = c.height; const bg = b.getContext('2d');
      bg.fillStyle = '#4a4a38';
      const pts = [[0, 0], [m.w, 0], [m.w, m.h], [0, m.h]].map(([x, y]) => mmToScreen(x, y));
      bg.beginPath(); pts.forEach(([x, y], i) => i ? bg.lineTo(x, y) : bg.moveTo(x, y)); bg.closePath(); bg.fill();
      // height: lighter on the rises, a contour every 1.5 m
      if (m.hgt) for (let y = 0; y < m.h; y += 2) for (let x = 0; x < m.w; x += 2) {
        const h = MAP.hAt(m, x + 1, y + 1); if (h < .8) continue;
        const [a, bb] = mmToScreen(x + 1, y + 1), edge = Math.floor(MAP.hAt(m, x + 3, y + 1) / 1.5) !== Math.floor(h / 1.5) || Math.floor(MAP.hAt(m, x + 1, y + 3) / 1.5) !== Math.floor(h / 1.5);
        bg.fillStyle = edge ? 'rgba(30,26,16,.35)' : `rgba(230,215,160,${Math.min(.35, h * .055)})`; bg.fillRect(a - 1.3, bb - 1.3, 2.6, 2.6);
      }
      bg.strokeStyle = '#a89878'; bg.lineWidth = 2;
      for (const rd of m.roads) { bg.beginPath(); rd.forEach(([x, y], i) => { const [a, bb] = mmToScreen(x, y); i ? bg.lineTo(a, bb) : bg.moveTo(a, bb); }); bg.stroke(); }
      bg.fillStyle = '#2f3a22'; for (const t of m.trees) { const [a, bb] = mmToScreen(t.x, t.y); bg.fillRect(a - 1, bb - 1, 2.5, 2.5); }
      bg.fillStyle = '#c9b89a'; for (const hh of m.houses) { const [a, bb] = mmToScreen(hh.x, hh.y); bg.fillRect(a - 2.5, bb - 2.5, 5, 5); }
      el.mmBase = b;
    }
    g.drawImage(el.mmBase, 0, 0);
    // territory tint, sector by sector, on the 2 m grid sampled coarse
    const step = 4;
    for (let y = 0; y < m.h; y += step) for (let x = 0; x < m.w; x += step) {
      const S = MAP.sectorAt(m, x + 2, y + 2); if (S.owner < 0) continue;
      const [a, b] = mmToScreen(x + 2, y + 2);
      g.fillStyle = S.owner === 0 ? (S.supplied ? 'rgba(74,163,255,.32)' : 'rgba(74,163,255,.14)') : (S.supplied ? 'rgba(255,90,74,.32)' : 'rgba(255,90,74,.14)');
      g.fillRect(a - 2.6, b - 2.6, 5.2, 5.2);
    }
    // fog
    const P = G.players[0], gw = m.w / FOG.C;
    g.fillStyle = 'rgba(10,12,16,.45)';
    for (let i = 0; i < P.vis.length; i++) if (P.vis[i] !== 2) { const x = (i % gw) * FOG.C + 2, y = ((i / gw) | 0) * FOG.C + 2; const [a, b] = mmToScreen(x, y); g.fillRect(a - 2.1, b - 2.1, 4.2, 4.2); }
    // points (always shown, even in fog)
    for (const p of m.points) { const [a, b] = mmToScreen(p.x, p.y); RENDER.pointIcon(g, p, a, b, .55, null); }
    // units
    for (const e of G.ents) {
      if (e.dead || (e.owner !== 0 && !ui.noFog && !FOG.visible(G, 0, e))) continue;
      const [a, b] = mmToScreen(e.x, e.y);
      g.fillStyle = e.owner === 0 ? (ui.selected.has(e.id) ? '#fff' : '#5ab4ff') : '#ff5a4a';
      if (e.type === 'building') g.fillRect(a - 3.5, b - 3.5, 7, 7); else if (e.type === 'vehicle') g.fillRect(a - 2.5, b - 2.5, 5, 5); else { g.beginPath(); g.arc(a, b, 2.2, 0, 7); g.fill(); }
    }
    // alerts
    for (const al of P.alerts) if (G.t - al.t < 4 && (al.kind === 'attack' || al.kind === 'lost')) { const [a, b] = mmToScreen(al.x, al.y); g.strokeStyle = '#fff'; g.lineWidth = 2; const s = 6 + (G.t * 6 % 4); g.strokeRect(a - s, b - s, s * 2, s * 2); }
    // camera footprint
    const corners = [[0, 0], [RENDER.W, 0], [RENDER.W, RENDER.H - 230], [0, RENDER.H - 230]].map(([x, y]) => RENDER.toWorld(x, y)).map(([x, y]) => mmToScreen(x, y));
    g.strokeStyle = 'rgba(255,255,255,.85)'; g.lineWidth = 1.2; g.beginPath(); corners.forEach(([x, y], i) => i ? g.lineTo(x, y) : g.moveTo(x, y)); g.closePath(); g.stroke();
  }
  /* event position on the minimap in canvas pixels, whatever size the HUD is drawn at */
  function mmEventWorld(e) { const r = el.mmc.getBoundingClientRect(); return mmToWorld((e.clientX - r.left) * el.mmc.width / r.width, (e.clientY - r.top) * el.mmc.height / r.height); }
  function toggleHeight() { ui.heightView = !ui.heightView; flash(ui.heightView ? 'Height view: green low, red high, a line every metre (H to hide)' : 'Height view off'); const b = el.mm.querySelector('[data-a=height]'); if (b) b.classList.toggle('on', ui.heightView); }
  function mmButton(a) {
    if (a === 'selv') ui.selected = new Set(G.ents.filter(e => e.owner === 0 && e.type === 'vehicle' && !e.dead).map(e => e.id));
    else if (a === 'seli') ui.selected = new Set(G.ents.filter(e => e.owner === 0 && e.type === 'squad' && !e.dead).map(e => e.id));
    else if (a === 'pause') togglePause();
    else if (a === 'height') toggleHeight();
    else if (a === 'menu') MAIN.menu(true);
    ui.page = 'main';
  }
  function togglePause() { ui.paused = !ui.paused; flash(ui.paused ? 'Paused: spend and set orders, Space to resume' : 'Resumed'); }

  /* ---------------- input ---------------- */
  const mouse = { x: -1, y: -1, down: false, drag: null, rdown: null, inCanvas: false, moved: false };
  /* the house under the cursor: test the ground point and the points behind the walls and roof as drawn */
  function houseAtScreen(sx, sy) {
    for (const z of [0, 1.5, 3, 4.5, 6]) { const [wx, wy] = RENDER.toWorld(sx, sy + z * 24 * RENDER.cam.k); const h = MAP.houseAt(G.map, wx, wy, .3); if (h && FOG.explored(G, 0, h.x, h.y)) return h; }
    return null;
  }
  function entAt(sx, sy) {
    let best = null, bd = ui.touch ? 46 * 46 : 30 * 30;
    for (const e of G.ents) {
      if (e.dead) continue;
      if (e.owner !== 0 && e.type !== 'building' && !ui.noFog && !FOG.visible(G, 0, e)) continue;
      if (e.type === 'building' && e.owner !== 0 && !ui.noFog && !FOG.explored(G, 0, e.x, e.y)) continue;
      if (e.type === 'squad') { for (const m of e.models) { if (!m.alive) continue; const [x, y] = RENDER.toScreen(m.x, m.y, .8); const d = (x - sx) ** 2 + (y - sy) ** 2; if (d < bd * .5) { bd = d * 2; best = e; } } if (e.crew && e.crew.state !== 'packed') { const [x, y] = RENDER.toScreen(e.crew.x, e.crew.y, .5); const d = (x - sx) ** 2 + (y - sy) ** 2; if (d < bd) { bd = d; best = e; } } }
      else if (e.type === 'vehicle') { const [x, y] = RENDER.toScreen(e.x, e.y, 1); const d = (x - sx) ** 2 + (y - sy) ** 2, r = e.def.length * 12 * RENDER.cam.k; if (d < Math.max(bd, r * r)) { bd = d; best = e; } }
      else { const [wx, wy] = RENDER.toWorld(sx, sy); if (Math.abs(wx - e.x) < e.w / 2 + 1 && Math.abs(wy - e.y) < e.d / 2 + 1) { best = e; bd = 0; } }
    }
    // a click on a garrisoned house picks the squad inside (yours, or an enemy you can see)
    if (!best) { const h = houseAtScreen(sx, sy), o = h && h.occ != null ? G.byId.get(h.occ) : null; if (o && !o.dead && (o.owner === 0 || FOG.visible(G, 0, o))) best = o; }
    return best;
  }
  function pointAt(sx, sy) { const [wx, wy] = RENDER.toWorld(sx, sy); for (const p of G.map.points) { const [x, y] = RENDER.toScreen(p.x, p.y, 8.5); if ((x - sx) ** 2 + (y - sy) ** 2 < 15 * 15 || U.dist2(wx, wy, p.x, p.y) < 2.5 * 2.5) return p; } return null; }
  function overHud(t) { return t !== canvasEl; }
  let pageBound = false;
  function bindInput() {
    el.mmc.addEventListener('contextmenu', e => e.preventDefault());
    bindMinimapMouse();
    if (pageBound) return;
    canvasEl.addEventListener('contextmenu', e => e.preventDefault());
    canvasEl.addEventListener('mousedown', e => {
      mouse.x = e.clientX; mouse.y = e.clientY;
      if (e.button === 0) { mouse.down = true; mouse.drag = { x: e.clientX, y: e.clientY, shift: e.shiftKey }; if (ui.mode && ui.mode.type === 'line') { const [wx, wy] = RENDER.toWorld(e.clientX, e.clientY); ui.mode.start = { x: wx, y: wy }; } }
      if (e.button === 2) mouse.rdown = { x: e.clientX, y: e.clientY, t: performance.now() };
      if (e.button === 1) { mouse.pan = { x: e.clientX, y: e.clientY, cx: RENDER.cam.x, cy: RENDER.cam.y }; e.preventDefault(); }
    });
    window.addEventListener('mousemove', e => {
      mouse.x = e.clientX; mouse.y = e.clientY; mouse.inCanvas = !overHud(e.target); mouse.inWindow = true; mouse.moved = true;
      if (mouse.pan) { const k = RENDER.cam.k, dx = (e.clientX - mouse.pan.x) / (22 * k), dy = (e.clientY - mouse.pan.y) / (11 * k); RENDER.cam.x = mouse.pan.cx - (dx + dy) / 2; RENDER.cam.y = mouse.pan.cy - (dy - dx) / 2; RENDER.clampCam(G); }
    });
    window.addEventListener('mouseup', e => {
      if (e.button === 1) mouse.pan = null;
      if (e.button === 0 && mouse.down) { mouse.down = false; if (!overHud(e.target) || mouse.drag && Math.hypot(e.clientX - mouse.drag.x, e.clientY - mouse.drag.y) > 6) leftUp(e); mouse.drag = null; }
      if (e.button === 2 && mouse.rdown) { if (!overHud(e.target)) rightUp(e); mouse.rdown = null; }
    });
    canvasEl.addEventListener('wheel', e => { e.preventDefault(); const before = RENDER.toWorld(e.clientX, e.clientY); RENDER.cam.k *= e.deltaY < 0 ? 1.1 : 1 / 1.1; RENDER.clampCam(G); const after = RENDER.toWorld(e.clientX, e.clientY); RENDER.cam.x += before[0] - after[0]; RENDER.cam.y += before[1] - after[1]; }, { passive: false });
    window.addEventListener('mouseup', () => { mouse.mmDrag = false; });
    window.addEventListener('keydown', keyDown);
    document.addEventListener('mouseleave', () => { mouse.inCanvas = false; mouse.inWindow = false; });
    window.addEventListener('keyup', e => { keys.delete(e.key); });
    // alt-tab with an arrow key held used to leave the camera scrolling forever: drop held keys and drags on blur
    window.addEventListener('blur', () => { keys.clear(); mouse.pan = null; mouse.inWindow = false; });
  }
  function bindMinimapMouse() {
    el.mmc.addEventListener('mousedown', e => {
      const [wx, wy] = mmEventWorld(e);
      if (e.button === 0) { RENDER.cam.x = wx; RENDER.cam.y = wy; mouse.mmDrag = true; }
    });
    el.mmc.addEventListener('mousemove', e => { if (mouse.mmDrag && e.buttons & 1) { const [wx, wy] = mmEventWorld(e); RENDER.cam.x = wx; RENDER.cam.y = wy; } });
  }
  const keys = new Set();
  function keyDown(e) {
    if (MAIN.inMenu()) { if (e.key === 'Escape') MAIN.menu(false); return; }
    const k = e.key;
    keys.add(k);
    if (k === 'Escape') { if (ui.mode) ui.mode = null; else if (ui.page !== 'main') ui.page = 'main'; else ui.selected.clear(); ui.ghost = null; return; }
    if (k === ' ') { togglePause(); e.preventDefault(); return; }
    if (k === 'F10') { MAIN.menu(true); e.preventDefault(); return; }
    if (k === 'Home') { centreOn(SIM.hqOf(G, 0)); return; }
    if ((k === 'h' || k === 'H') && !e.ctrlKey && !e.metaKey) { toggleHeight(); return; }
    // number row by physical key, so Shift+1 is still 1 (on most layouts Shift+1 types '!')
    const digit = /^Digit[0-9]$/.test(e.code || '') ? e.code[5] : /^[0-9]$/.test(k) ? k : null;
    if (digit) {
      const P = G.players[0], g = digit;
      if (e.repeat) return;
      if (e.ctrlKey || e.metaKey) { e.preventDefault(); for (const q in P.groups) P.groups[q] = P.groups[q].filter(id => !ui.selected.has(id)); P.groups[g] = [...ui.selected].filter(id => { const x = G.byId.get(id); return x && x.owner === 0; }); flash('Group ' + g + ' set'); }
      else {
        const ids = (P.groups[g] || []).filter(id => G.byId.get(id));
        if (ids.length) {
          if (e.shiftKey) ids.forEach(id => ui.selected.add(id));   // Shift+number: add the group to the selection
          else { if (performance.now() - (keyDown.last || 0) < 350 && keyDown.lastK === g) centreOnGroup(ids); ui.selected = new Set(ids); }
          ui.page = 'main';
        }
        keyDown.last = performance.now(); keyDown.lastK = g;
      }
      return;
    }
    if ((k === 'a' || k === 'A') && (e.ctrlKey || e.metaKey)) { e.preventDefault(); ui.selected = new Set(G.ents.filter(x => x.owner === 0 && !x.dead && x.type !== 'building').map(x => x.id)); ui.page = 'main'; return; }
    if (k === 't' || k === 'T') { const p = primary(); if (p && p.type === 'building' && p.def.retreat) { slotColAct('reinforce'); return; } }
    const idx = KEYS.indexOf(k.toUpperCase());
    // a held key used to repeat the order (five tanks queued from one press of a production key)
    if (idx >= 0 && !e.ctrlKey && !e.metaKey) { e.preventDefault(); if (!e.repeat) pressSlot(idx); return; }
    if (k === '+' || k === '=') { RENDER.cam.k *= 1.1; RENDER.clampCam(G); } if (k === '-') { RENDER.cam.k /= 1.1; RENDER.clampCam(G); }
    if (k === 'F12' && e.shiftKey) ui.noFog = !ui.noFog;
  }
  function leftUp(e) {
    // box or click select
    const d = mouse.drag;
    if (d && Math.hypot(e.clientX - d.x, e.clientY - d.y) > 6) {
      const x0 = Math.min(d.x, e.clientX), x1 = Math.max(d.x, e.clientX), y0 = Math.min(d.y, e.clientY), y1 = Math.max(d.y, e.clientY);
      const inBox = (x, y) => { const [sx, sy] = RENDER.toScreen(x, y); return sx >= x0 && sx <= x1 && sy >= y0 && sy <= y1; };
      const got = G.ents.filter(en => !en.dead && en.owner === 0 && en.type !== 'building' && (en.type === 'squad' ? en.models.some(md => md.alive && inBox(md.x, md.y)) || (en.crew && en.crew.state !== 'packed' && inBox(en.crew.x, en.crew.y)) : inBox(en.x, en.y)));
      if (!d.shift) ui.selected.clear(); got.forEach(g => ui.selected.add(g.id)); ui.page = 'main'; return;
    }
    const t = entAt(e.clientX, e.clientY), now = performance.now();
    if (t) {
      if (now - ui.lastClick < 320 && ui.lastId === t.id && t.owner === 0) {
        // double click: every unit of that kind on screen
        const same = G.ents.filter(o => !o.dead && o.owner === 0 && o.defId === t.defId && (() => { const [sx, sy] = RENDER.toScreen(o.x, o.y); return sx > 0 && sx < RENDER.W && sy > 0 && sy < RENDER.H; })());
        ui.selected = new Set(same.map(o => o.id));
      } else if (e.shiftKey && t.owner === 0) { if (ui.selected.has(t.id)) ui.selected.delete(t.id); else ui.selected.add(t.id); }
      else ui.selected = new Set([t.id]);
      ui.lastClick = now; ui.lastId = t.id; ui.page = 'main';
    } else if (!e.shiftKey) ui.selected.clear();
  }
  /* right click only backs out of a pending pick: units are never ordered about by hand */
  function rightUp(e) { if (ui.mode) { ui.mode = null; ui.ghost = null; } }
  /* ---------------- touch: tap to select, drag to pan, pinch to zoom ---------------- */
  const touch = { pts: new Map(), start: null, moved: false, pinch: null, lastTap: 0 };
  function fake(x, y, shift) { return { clientX: x, clientY: y, shiftKey: !!shift, target: canvasEl }; }
  /* a tap selects (your unit or building, or an enemy to look at); a tap on open ground clears the selection */
  function tapAt(x, y) { mouse.drag = null; leftUp(fake(x, y, ui.multi && !!entAt(x, y))); }
  function bindTouch() {
    bindTouchHud();
    if (pageBound) return;
    pageBound = true;
    canvasEl.style.touchAction = 'none';
    canvasEl.addEventListener('pointerdown', e => {
      if (e.pointerType !== 'touch') return;
      e.preventDefault(); ui.touch = true;
      touch.pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (ui.mode) { mouse.x = e.clientX; mouse.y = e.clientY; mouse.inCanvas = true; }
      if (touch.pts.size === 1) {
        touch.start = { x: e.clientX, y: e.clientY, t: performance.now(), cx: RENDER.cam.x, cy: RENDER.cam.y }; touch.moved = false;
        clearTimeout(touch.lp); touch.longed = false;
        if (ui.boxMode) { mouse.down = true; mouse.drag = { x: e.clientX, y: e.clientY, shift: ui.multi }; mouse.x = e.clientX; mouse.y = e.clientY; }
      } else if (touch.pts.size === 2) {
        clearTimeout(touch.lp); mouse.down = false; mouse.drag = null;
        const [a, b] = [...touch.pts.values()];
        touch.pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), k: RENDER.cam.k, mid: RENDER.toWorld((a.x + b.x) / 2, (a.y + b.y) / 2) };
        touch.moved = true;
      }
    });
    canvasEl.addEventListener('pointermove', e => {
      if (e.pointerType !== 'touch' || !touch.pts.has(e.pointerId)) return;
      touch.pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (touch.pts.size >= 2 && touch.pinch) {
        const [a, b] = [...touch.pts.values()], d = Math.hypot(a.x - b.x, a.y - b.y);
        RENDER.cam.k = touch.pinch.k * d / Math.max(10, touch.pinch.d); RENDER.clampCam(G);
        const now = RENDER.toWorld((a.x + b.x) / 2, (a.y + b.y) / 2);
        RENDER.cam.x += touch.pinch.mid[0] - now[0]; RENDER.cam.y += touch.pinch.mid[1] - now[1];
        return;
      }
      const s = touch.start; if (!s) return;
      if (Math.hypot(e.clientX - s.x, e.clientY - s.y) > 10) { touch.moved = true; clearTimeout(touch.lp); }
      if (!touch.moved) return;
      if (ui.boxMode) { mouse.x = e.clientX; mouse.y = e.clientY; return; }
      if (ui.mode && (ui.mode.type === 'place' || ui.mode.type === 'line' && ui.mode.start)) { mouse.x = e.clientX; mouse.y = e.clientY; mouse.inCanvas = true; return; }   // drag the outline, not the camera
      const k = RENDER.cam.k, dx = (e.clientX - s.x) / (22 * k), dy = (e.clientY - s.y) / (11 * k);
      RENDER.cam.x = s.cx - (dx + dy) / 2; RENDER.cam.y = s.cy - (dy - dx) / 2; RENDER.clampCam(G);
    });
    const end = e => {
      if (e.pointerType !== 'touch' || !touch.pts.has(e.pointerId)) return;
      touch.pts.delete(e.pointerId); clearTimeout(touch.lp);
      if (touch.pts.size) { const [p] = [...touch.pts.values()]; touch.start = { x: p.x, y: p.y, t: 0, cx: RENDER.cam.x, cy: RENDER.cam.y }; touch.pinch = null; return; }
      touch.pinch = null;
      if (ui.boxMode && mouse.drag) { if (touch.moved) leftUp(fake(e.clientX, e.clientY, ui.multi)); mouse.down = false; mouse.drag = null; if (touch.moved) { ui.boxMode = false; syncToolbar(); return; } }
      if (e.type === 'pointerup' && ui.mode && ui.mode.type === 'place' && touch.moved) { tapAt(mouse.x, mouse.y); touch.start = null; return; }   // drag-to-place: lift to build
      if (e.type === 'pointerup' && ui.mode && ui.mode.type === 'line' && ui.mode.start && touch.moved) { tapAt(mouse.x, mouse.y); touch.start = null; return; }
      if (e.type === 'pointerup' && !touch.moved && !touch.longed && touch.start) tapAt(touch.start.x, touch.start.y);
      touch.start = null;
    };
    canvasEl.addEventListener('pointerup', end); canvasEl.addEventListener('pointercancel', end);
  }
  function bindTouchHud() {
    // minimap: tap moves the camera, tap with units selected after a tap on the camera does not order (use the field)
    el.mmc.addEventListener('pointerdown', e => { if (e.pointerType !== 'touch') return; e.preventDefault(); ui.touch = true; const [wx, wy] = mmEventWorld(e); RENDER.cam.x = wx; RENDER.cam.y = wy; el.mmc._drag = true; });
    el.mmc.addEventListener('pointermove', e => { if (e.pointerType !== 'touch' || !el.mmc._drag) return; const [wx, wy] = mmEventWorld(e); RENDER.cam.x = wx; RENDER.cam.y = wy; });
    el.mmc.addEventListener('pointerup', () => { el.mmc._drag = false; });
    el.mmc.style.touchAction = 'none';
    // touch toolbar
    el.tbar = h('div', 'tbar', `<button data-t="box" title="Box select: drag on the field">&#9634;<small>Box</small></button><button data-t="multi" title="Add to selection">+<small>Add</small></button><button data-t="clear" title="Deselect">&#10005;<small>Clear</small></button><button data-t="hq" title="Jump to HQ">&#8962;<small>HQ</small></button><button data-t="full" title="Full screen">&#9974;<small>Full</small></button>`);
    $('#hud').appendChild(el.tbar);
    el.tbar.addEventListener('click', ev => {
      const b = ev.target.closest('[data-t]'); if (!b) return;
      const t = b.dataset.t;
      if (t === 'box') ui.boxMode = !ui.boxMode;
      else if (t === 'multi') ui.multi = !ui.multi;
      else if (t === 'clear') { ui.selected.clear(); ui.mode = null; ui.page = 'main'; }
      else if (t === 'hq') centreOn(SIM.hqOf(G, 0));
      else if (t === 'full') { try { const d = document.documentElement; if (document.fullscreenElement) document.exitFullscreen(); else (d.requestFullscreen || d.webkitRequestFullscreen).call(d).catch(() => flash('Full screen is not allowed here')); } catch (x) { flash('Full screen is not allowed here'); } }
      syncToolbar();
    });
    syncToolbar();
  }
  function syncToolbar() { if (!el.tbar) return; el.tbar.querySelector('[data-t=box]').classList.toggle('on', !!ui.boxMode); el.tbar.querySelector('[data-t=multi]').classList.toggle('on', !!ui.multi); }

  /* per-frame input work: edge pan, arrow keys, hover, ghosts, cover preview */
  let lastSig = '';
  function tick(dt) {
    const sig = [...ui.selected].join(',') + '|' + (ui.mode ? ui.mode.type : '') + '|' + ui.page;
    if (sig !== lastSig) { lastSig = sig; update(); }
    const c = RENDER.cam, sp = 60 / c.k * dt;
    let dx = 0, dy = 0;
    if (keys.has('ArrowLeft')) dx -= 1; if (keys.has('ArrowRight')) dx += 1; if (keys.has('ArrowUp')) dy -= 1; if (keys.has('ArrowDown')) dy += 1;
    const edge = 6;
    if (!ui.touch && mouse.moved && mouse.inWindow && !MAIN.inMenu() && document.hasFocus()) { if (mouse.x < edge) dx -= 1; if (mouse.x > RENDER.W - edge) dx += 1; if (mouse.y < edge) dy -= 1; if (mouse.y > RENDER.H - edge) dy += 1; }
    if (dx || dy) { c.x += (dx + dy) * sp * .5; c.y += (dy - dx) * sp * .5; }
    RENDER.clampCam(G);
    const t = mouse.inCanvas ? entAt(mouse.x, mouse.y) : null; ui.hover = t ? t.id : null;
    const p = mouse.inCanvas ? pointAt(mouse.x, mouse.y) : null; ui.hoverPoint = p ? p.id : null;
    const m = ui.mode; ui.ghost = null;
    ui.hoverDrop = null; ui.coverPreview = null;
    // cursor
    canvasEl.style.cursor = m ? 'crosshair' : 'default';
  }

  /* selection rectangle: a DOM box over the canvas */
  function drawSelectBox() {
    const box = el.selbox || (el.selbox = document.body.appendChild(h('div', 'selbox')));
    const d = mouse.drag;
    if (!d || !mouse.down || ui.mode || Math.hypot(mouse.x - d.x, mouse.y - d.y) < 6) { box.style.display = 'none'; return; }
    Object.assign(box.style, { display: 'block', left: Math.min(d.x, mouse.x) + 'px', top: Math.min(d.y, mouse.y) + 'px', width: Math.abs(mouse.x - d.x) + 'px', height: Math.abs(mouse.y - d.y) + 'px' });
  }

  return { init, update, tick, drawMinimap, drawSelectBox, ui, flash, keys };
})();
