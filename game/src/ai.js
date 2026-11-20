/* Unit AI for both armies. Every unit carries a standing order (`role`) and works it out for itself:
     capture  take points the army does not hold, enemy-held ones first
     hunt     go after enemy units as one party; with none in sight, push on the last place they were seen
     defend   hold the army's own points on the border, in houses and behind sandbags
     supply   take and keep the points that pay income, nearest home first
   The opposing AI also spends its own resources (units and buildings in tech order) and hands out orders; the
   player spends and picks orders by hand and never moves a unit directly (`manual`). Either way each unit pulls
   back when it is losing, sets up team weapons facing the enemy, throws grenades at enemies in cover and points
   anti-tank weapons at enemy vehicles. It sees through the same fog as the player. */
const AI = (() => {
  const D = DATA;
  /* unit wishes by phase: [unit, weight]; tech follows FACTIONS[side].buildings */
  const PLAN = {
    de: { early: [['de_grenadiers', 3], ['de_hmg', 2.2], ['de_mortar', 1.2], ['de_pioneers', .4], ['de_bike', .5]], mid: [['de_grenadiers', 2], ['de_hmg', 1.2], ['de_mortar', 1.2], ['de_schreck', 1.5], ['de_222', 2], ['de_pz2', 1.5], ['de_panzergrenadiers', 2], ['de_at_gun', 1.2], ['de_stug', 2], ['de_251', .4], ['de_sniper', .5]], late: [['de_pz4', 3], ['de_stug', 2], ['de_panzergrenadiers', 2], ['de_grenadiers', 1.5], ['de_at_gun', 1], ['de_pz2', 1]] },
    us: { early: [['us_riflemen', 3], ['us_hmg', 2], ['us_mortar', 1.2], ['us_engineers', .4], ['us_jeep', .6]], mid: [['us_riflemen', 2], ['us_hmg', 1.2], ['us_mortar', 1.2], ['us_bazooka', 1.5], ['us_m8', 2], ['us_at_gun', 1.2], ['us_halftrack', .4], ['us_sniper', .5], ['us_chaffee', 1.5]], late: [['us_sherman', 3], ['us_m10', 2], ['us_riflemen', 2], ['us_at_gun', 1], ['us_bazooka', 1]] },
  };
  const CAP = { de_bike: 1, us_jeep: 1, de_mortar: 2, us_mortar: 2, de_hmg: 2, us_hmg: 2, de_sniper: 1, us_sniper: 1, de_251: 1, us_halftrack: 1 };
  /* standIn: the four standing orders are this game's own; CoH3 has no counterpart */
  const ROLES = {
    capture: { name: 'Capture', icon: 'roleCapture', tip: 'Take points you do not hold, enemy-held ones first.' },
    hunt: { name: 'Hunt', icon: 'roleHunt', tip: 'Go after enemy units together with your other hunters. With none in sight, push on where they were last seen.' },
    defend: { name: 'Defend', icon: 'roleDefend', tip: 'Hold your own points on the border: infantry take houses, team weapons set up facing the enemy, engineers lay sandbags.' },
    supply: { name: 'Supply', icon: 'roleSupply', tip: 'Take and keep the points that pay munitions and fuel, nearest home first. Engineers also repair vehicles.' },
  };
  /* fighting vehicles (fuel cost, not a transport) wanted before teching to tier 3 and 4: without this the AI saved its
     fuel for the next building for the whole game and never fielded a vehicle */
  const VEH_BEFORE_TECH = [0, 0, 1, 2];
  const isFightingVehicle = def => def && def.armor && (def.cost.fu || 0) > 0 && !def.reinforces;
  /* manual: a human spends for this army and picks each unit's order; the units still act on their own */
  function step(G, slot, manual) {
    const S = (G.ai || (G.ai = {}))[slot] || (G.ai[slot] = {}), me = G.players[slot];
    if ((S.t || 0) > G.t) return;
    S.t = G.t + 1;
    const mine = G.ents.filter(e => !e.dead && e.owner === slot);
    if (manual) finishBuildings(mine); else spend(G, me, mine, S);
    command(G, me, mine, S, manual);
  }
  /* builders go and finish any building still going up */
  function finishBuildings(mine) {
    const builders = mine.filter(e => e.type === 'squad' && e.def.builder && !e.retreating);
    for (const b of mine) if (b.type === 'building' && b.built < 1) for (const p of builders) if (p.order.type !== 'build') { p.buildQueue = [{ kind: 'building', id: b.id }]; p.order = { type: 'build' }; }
  }
  /* place a base building for `slot` on a free spot by its HQ and send a builder; returns why not, or null */
  function build(G, slot, defId) {
    const me = G.players[slot], why = SIM.buildReqMissing(G, slot, defId) || (!SIM.canAfford(me, D.BUILDINGS[defId].cost) ? 'Not enough resources' : null);
    if (why) return why;
    const builders = G.ents.filter(e => !e.dead && e.owner === slot && e.type === 'squad' && e.def.builder && !e.retreating);
    if (!builders.length) return 'No ' + SIM.unitDef(me.F.builder).name + ' to build it: train one at the HQ';
    const spot = findSpot(G, slot, defId); if (!spot) return 'No room by the HQ';
    builders.sort((a, b) => (a.order.type === 'build') - (b.order.type === 'build'));
    SIM.issue(G, [builders[0].id], { type: 'build', what: defId, x: spot.x, y: spot.y });
    return null;
  }
  /* the order a new unit starts on when nobody picked one */
  function defaultRole(G, me, e, manual) {
    if (e.def.builder) return 'supply';
    if (manual) return me.newRole || 'capture';
    const r = G.rng();
    if (e.type === 'squad' && e.def.crewWeapon) return r < .55 ? 'defend' : 'capture';
    if (e.type === 'vehicle') return r < .5 ? 'hunt' : 'capture';
    return r < .55 ? 'capture' : r < .75 ? 'hunt' : r < .9 ? 'defend' : 'supply';
  }

  function spend(G, me, mine, S) {
    const builders = mine.filter(e => e.type === 'squad' && e.def.builder);
    const buildings = mine.filter(e => e.type === 'building');
    // tech: next building in order, once a few squads are out
    const army = mine.filter(e => e.type !== 'building' && !(e.def && e.def.builder)).length;
    const tech = me.F.buildings, owned = new Set(buildings.map(b => b.defId));
    const next = tech.find(b => !owned.has(b) && !SIM.buildReqMissing(G, me.slot, b));
    const ti = next ? tech.indexOf(next) : -1;
    // fighting vehicles out or on order, and the ones the finished buildings can make
    const queuedUnits = buildings.flatMap(b => b.queue.map(q => q.unit));
    const vehicles = mine.filter(e => e.type === 'vehicle' && isFightingVehicle(e.def)).length + queuedUnits.filter(u => isFightingVehicle(SIM.unitDef(u))).length;
    const vehOpts = PLAN[me.side].mid.concat(PLAN[me.side].late).map(([u]) => u).filter((u, i, a) => a.indexOf(u) === i && isFightingVehicle(SIM.unitDef(u)) && buildings.some(b => b.built >= 1 && b.def.produce.includes(u)));
    const vehShort = vehOpts.length > 0 && ti >= 0 && vehicles < VEH_BEFORE_TECH[ti] && G.t < [0, 0, 600, 840][ti];
    const wantTech = next && !vehShort && (army >= [0, 4, 6, 8][ti] || G.t > [0, 220, 330, 480][ti]);
    if (wantTech && builders.length && SIM.canAfford(me, D.BUILDINGS[next].cost) && !buildings.some(b => b.built < 1)) {
      const spot = findSpot(G, me.slot, next);
      if (spot) SIM.issue(G, [builders[0].id], { type: 'build', what: next, x: spot.x, y: spot.y });
    }
    // help finish buildings
    for (const b of buildings) if (b.built < 1) for (const p of builders) if (p.order.type !== 'build') { p.buildQueue = [{ kind: 'building', id: b.id }]; p.order = { type: 'build' }; }
    // no builder left: replace one first, ahead of everything else (it can't tech without one)
    const builderQueued = buildings.some(b => b.queue.some(q => SIM.unitDef(q.unit).builder));
    if (!builders.length && !builderQueued) {
      const hqB = buildings.find(b => b.built >= 1 && b.def.produce.includes(me.F.builder));
      if (hqB && !hqB.queue.length && !SIM.prodBlock(G, hqB, me.F.builder)) { SIM.issue(G, [hqB.id], { type: 'produce', unit: me.F.builder }); return; }
    }
    // keep money for tech when it is close, but only what the tech is actually waiting on: saving manpower while fuel is
    // still far short just banks it (the old rule left 200+ manpower idle and starved the army)
    let reserve = { mp: 0, fu: 0 };
    if (wantTech && (builders.length || builderQueued)) {
      const c = D.BUILDINGS[next].cost, fuShort = (c.fu || 0) - me.res.fu, fuRate = Math.max(1, me.income ? me.income.fu : 6) / 60;
      reserve = { mp: fuShort > 0 && fuShort / fuRate > 45 ? 0 : (c.mp || 0), fu: c.fu || 0 };
    }
    // saving for a vehicle instead: pick one the buildings can make and keep its fuel (and its manpower once the fuel is
    // nearly there), so infantry spending doesn't eat it
    let saveFor = null;
    if (!wantTech && vehOpts.length && (vehShort || vehicles < 1 + (G.t > 600 ? 2 : 0) + (owned.has(tech[3]) ? 1 : 0))) {
      if (!S.saveFor || !vehOpts.includes(S.saveFor)) S.saveFor = vehOpts[Math.floor(G.rng() * vehOpts.length)];
      saveFor = S.saveFor;
      const c = SIM.unitDef(saveFor).cost, fuShort = (c.fu || 0) - me.res.fu, fuRate = Math.max(1, me.income ? me.income.fu : 6) / 60;
      reserve = { mp: fuShort > 0 && fuShort / fuRate > 30 ? 0 : (c.mp || 0), fu: c.fu || 0 };
    } else S.saveFor = null;
    const phase = G.t < 240 ? 'early' : (owned.has(tech[3]) ? 'late' : 'mid');
    const wishes = PLAN[me.side][phase].concat(phase === 'late' ? PLAN[me.side].mid.map(([u, w]) => [u, w * .4]) : []);
    // counter enemy armour
    const enemyV = G.ents.filter(e => !e.dead && e.owner !== me.slot && e.type === 'vehicle' && FOG.visible(G, me.slot, e)).length;
    for (const b of buildings) {
      if (b.built < 1 || b.queue.length >= 1) continue;
      if (saveFor && b.def.produce.includes(saveFor)) {
        if (SIM.canAfford(me, SIM.unitDef(saveFor).cost) && !SIM.prodBlock(G, b, saveFor)) { SIM.issue(G, [b.id], { type: 'produce', unit: saveFor }); S.saveFor = null; saveFor = null; reserve = { mp: 0, fu: 0 }; }
        continue;   // this building waits for the vehicle
      }
      const opts = wishes.filter(([u]) => b.def.produce.includes(u)).map(([u, w]) => {
        const def = SIM.unitDef(u);
        let ww = w;
        if (enemyV && (def.weapons || []).some(x => D.W[x] && (D.W[x].kind === 'at' || (D.W[x].kind === 'cannon' && D.W[x].pen[0] > 150)))) ww *= 1 + enemyV;
        if (def.builder && builders.length + (builderQueued ? 1 : 0) >= (G.t > 300 ? 2 : 1)) ww = 0;
        const have = mine.filter(e => e.defId === u).length + G.ents.filter(x => x.type === 'building' && x.owner === me.slot && x.queue.some(q => q.unit === u)).length;
        const cap = CAP[u] != null ? CAP[u] : 99; if (have >= cap) ww = 0;
        // fewer of what we already have: a mix of infantry, team weapons and vehicles, not one squad type spammed
        ww /= 1 + have * (def.armor ? .35 : .6);
        return [u, ww];
      }).filter(([, w]) => w > 0);
      if (!opts.length) continue;
      // keep the last pick until it is bought: re-rolling every second while saving up meant the cheapest unit in the
      // list was nearly always the one bought (mortars and MGs before riflemen)
      const picks = S.picks || (S.picks = {});
      let pick = opts.some(([u]) => u === picks[b.id]) ? picks[b.id] : null;
      if (!pick) {
        let tot = opts.reduce((a, [, w]) => a + w, 0), r = G.rng() * tot; pick = opts[0][0];
        for (const [u, w] of opts) { r -= w; if (r <= 0) { pick = u; break; } }
        picks[b.id] = pick;
      }
      const def = SIM.unitDef(pick), cost = def.cost;
      const after = { mp: me.res.mp - (cost.mp || 0), fu: me.res.fu - (cost.fu || 0) };
      if (after.mp < (reserve.mp || 0) * .8 || after.fu < (reserve.fu || 0) * .8 && (cost.fu || 0)) continue;
      const block = SIM.prodBlock(G, b, pick);
      if (!block) { SIM.issue(G, [b.id], { type: 'produce', unit: pick }); delete picks[b.id]; }
      else if (block === 'Population cap reached') delete picks[b.id];
    }
    // upgrades with spare munitions
    for (const e of mine) if (e.type === 'squad' && e.def.upgrades && me.res.mu > 120 && !e.upgrading && SIM.nearReinforcePoint(G, e)) {
      const up = e.def.upgrades.find(u => !e.upgrades.has(u.id) && !(u.swap && u.swap.sprite === 'flamethrower' && G.rng() < .7));
      if (up) SIM.issue(G, [e.id], { type: 'upgrade', id: up.id });
    }
  }
  function findSpot(G, slot, defId) {
    const hq = SIM.hqOf(G, slot); if (!hq) return null;
    const dir = slot ? -1 : 1, def = D.BUILDINGS[defId], m = G.map;
    // a clear strip all round, so buildings never box each other in: vehicles from a Motor Pool walled in by the HQ and
    // the Weapon Support Center couldn't drive out
    const PAD = 7;
    const clearAround = (x, y) => {
      for (let yy = Math.floor(y - def.size[1] / 2 - PAD); yy < Math.ceil(y + def.size[1] / 2 + PAD); yy++) for (let xx = Math.floor(x - def.size[0] / 2 - PAD); xx < Math.ceil(x + def.size[0] / 2 + PAD); xx++) {
        if (xx < 0 || yy < 0 || xx >= m.w || yy >= m.h) return false;
        if (m.block[yy * m.w + xx] & MAP.BV) return false;
      }
      return true;
    };
    for (const padded of [true, false]) for (let r = 16; r < 52; r += 4) for (let a = 0; a < 16; a++) {
      const ang = a / 16 * U.TAU, x = hq.x + Math.cos(ang) * r, y = hq.y + Math.sin(ang) * r;
      // keep behind the HQ (away from the enemy) where possible
      if ((x - y) * dir > (hq.x - hq.y) * dir + 18) continue;
      if (!SIM.canPlace(G, slot, defId, x, y) && !SIM.sealsBase(G, slot, defId, x, y) && (!padded || clearAround(x, y))) return { x, y };
    }
    return null;
  }

  function command(G, me, mine, S, manual) {
    const slot = me.slot, enemy = 1 - slot, pts = G.map.points;
    const hq = SIM.hqOf(G, slot); if (!hq) return;
    const enemyHq = SIM.hqOf(G, enemy);
    const visibleEnemies = G.ents.filter(e => !e.dead && e.owner === enemy && e.type !== 'building' && FOG.visible(G, slot, e));
    // value of each point to us
    const goals = pts.map(p => {
      let v = p.type === 'victory' ? 3.2 : p.type === 'fuel' ? 2.4 : p.type === 'munitions' ? 2 : 1.3;
      if (p.owner === slot) v *= .45; else if (p.owner === enemy) v *= 1.15;
      if (!SIM.connected(G, slot, p) && p.type !== 'victory') v *= .5;   // a cut-off point pays nothing (victory points still count)
      const threat = visibleEnemies.filter(e => U.dist2(e.x, e.y, p.x, p.y) < 30 * 30).length;
      if (p.owner === slot && threat) v *= 2.5;
      // on the border: a neighbouring sector is not ours
      const border = p.owner === slot && [...G.map.sectors[p.sector].neigh].some(n => G.map.sectors[n].owner !== slot);
      return { p, v, threat, border, assigned: 0 };
    });
    const units = mine.filter(e => e.type !== 'building');
    // the hunting party shares one quarry: the enemy in sight nearest the party's middle; else where one was last seen
    const hunters = units.filter(e => e.role === 'hunt' && !e.retreating);
    let quarry = null;
    if (hunters.length) {
      const cx = hunters.reduce((a, e) => a + e.x, 0) / hunters.length, cy = hunters.reduce((a, e) => a + e.y, 0) / hunters.length;
      let bd = 1e9; for (const o of visibleEnemies) { const d = U.dist2(o.x, o.y, cx, cy); if (d < bd) { bd = d; quarry = o; } }
      if (quarry) S.lastSeen = { x: quarry.x, y: quarry.y, t: G.t };
      else if (S.lastSeen && (G.t - S.lastSeen.t > 90 || hunters.some(e => U.dist2(e.x, e.y, S.lastSeen.x, S.lastSeen.y) < 10 * 10))) S.lastSeen = null;
    }
    for (const e of units) {
      if (!e.role || !ROLES[e.role]) e.role = defaultRole(G, me, e, manual);
      // pull back when losing
      if (e.type === 'squad') {
        const al = e.models.filter(m => m.alive).length;
        if (!e.retreating && ((al <= Math.ceil(e.maxModels / (e.def.builder ? 2 : 3)) || e.def.builder && al < e.maxModels && G.t - e.lastHit < 3) && G.t - e.lastHit < 5 || e.suppState === 2 && G.rng() < .3)) { SIM.issue(G, [e.id], { type: 'retreat' }); continue; }
        if (e.retreating) continue;
        // just back from a retreat: wait to refill
        if (al < e.maxModels && SIM.nearReinforcePoint(G, e) && me.res.mp > e.def.reinforce) { if (e.order.type !== 'idle') SIM.issue(G, [e.id], { type: 'stop' }); continue; }
      } else if (e.type === 'vehicle' && e.hp < e.maxHp * .3 && G.t - e.lastHit < 6) { if (e.order.type !== 'move') SIM.issue(G, [e.id], { type: 'retreat' }); continue; }
      if (e.def.builder && (e.order.type === 'build' || e.order.type === 'repair')) continue;
      // repair damaged vehicles near base
      if (e.def.builder) { const hurt = units.find(v => v.type === 'vehicle' && v.hp < v.maxHp * .7 && U.dist2(v.x, v.y, e.x, e.y) < 40 * 40); if (hurt) { SIM.issue(G, [e.id], { type: 'repair', target: hurt.id }); continue; } }
      // anti-tank: go for visible vehicles
      const atWeapon = e.type === 'squad' ? e.models.some(m => m.alive && m.weapon && D.W[m.weapon].kind === 'at') || (SIM.weaponOf(e) && SIM.weaponOf(e).kind === 'at') : D.W[e.def.weapons[0]].kind === 'cannon' && D.W[e.def.weapons[0]].pen[0] >= 150;
      if (atWeapon) {
        const tv = visibleEnemies.filter(v => v.type === 'vehicle').sort((a, b) => U.dist2(a.x, a.y, e.x, e.y) - U.dist2(b.x, b.y, e.x, e.y))[0];
        if (tv && U.dist2(tv.x, tv.y, e.x, e.y) < 60 * 60) { if (e.order.type !== 'attack' || e.order.target !== tv.id) { if (e.crew) { if (e.crew.state === 'packed') SIM.issue(G, [e.id], { type: 'setup', heading: Math.atan2(tv.y - e.y, tv.x - e.x) }); } else SIM.issue(G, [e.id], { type: 'attack', target: tv.id }); } continue; }
      }
      // team weapons: a gun still packed and walking stops and sets up when enemy infantry come into its range, instead
      // of walking into them (it only set up on arrival before)
      if (e.crew && e.crew.state === 'packed' && e.order.type !== 'retreat') {
        const cw = SIM.weaponOf(e);
        if (cw && cw.kind !== 'at') {
          const far = cw.rng[2] * (cw.kind === 'indirect' ? .95 : .85), near = cw.minRange || 0;
          const tgt = visibleEnemies.filter(o => o.type === 'squad' && !o.retreating).map(o => ({ o, d: Math.hypot(o.x - e.x, o.y - e.y) })).filter(t => t.d < far && t.d > near + 3).sort((a, b) => a.d - b.d)[0];
          if (tgt) { SIM.issue(G, [e.id], { type: 'setup', heading: Math.atan2(tgt.o.y - e.y, tgt.o.x - e.x) }); continue; }
        }
      }
      // grenades at enemies in cover
      if (e.type === 'squad' && e.def.abilities && (me.res.mu > 40 || e.crew)) {   // the HE barrage is free
        const ab = e.def.abilities.find(a => a !== 'barrage' && a !== 'breach' && !D.ABILITIES[a].smoke && (e.cooldowns[a] || 0) < G.t);
        if (ab) {
          const A = D.ABILITIES[ab];
          const tgt = visibleEnemies.find(o => o.type === 'squad' && U.dist2(o.x, o.y, e.x, e.y) < (A.range - 2) ** 2 && U.dist2(o.x, o.y, e.x, e.y) > ((A.minRange || 6) + 1) ** 2 && (COMBAT.squadCover(G, o) === 'heavy' || o.def.crewWeapon));
          if (tgt && G.rng() < .5) { const m = tgt.models.find(q => q.alive); SIM.issue(G, [e.id], { type: 'ability', id: ab, x: m.x, y: m.y }); continue; }
        }
        // smoke off an enemy machine gun that has us suppressed
        if (e.def.abilities.includes('smokeGrenade') && e.suppState >= 1 && (e.cooldowns.smokeGrenade || 0) < G.t && me.res.mu >= 30) {
          const mg = visibleEnemies.find(o => o.type === 'squad' && o.crew && o.crew.state === 'deployed' && SIM.weaponOf(o).kind === 'mg' && U.dist2(o.x, o.y, e.x, e.y) < 24 * 24);
          if (mg) { SIM.issue(G, [e.id], { type: 'ability', id: 'smokeGrenade', x: mg.crew.x, y: mg.crew.y }); continue; }
        }
        if (e.def.abilities.includes('smokeBarrage') && (e.cooldowns.smokeBarrage || 0) < G.t && e.crew && e.crew.state === 'deployed' && me.res.mu >= 40) {
          const mg = visibleEnemies.find(o => o.type === 'squad' && o.crew && o.crew.state === 'deployed' && SIM.weaponOf(o).kind === 'mg' && units.some(f => f.type === 'squad' && f.suppState === 2 && U.dist2(f.x, f.y, o.x, o.y) < 40 * 40) && U.dist2(o.x, o.y, e.x, e.y) < 85 * 85 && U.dist2(o.x, o.y, e.x, e.y) > 30 * 30);
          if (mg) { SIM.issue(G, [e.id], { type: 'ability', id: 'smokeBarrage', x: mg.crew.x, y: mg.crew.y }); continue; }
        }
        // breach an enemy garrison close by
        if (e.def.abilities.includes('breach') && (e.cooldowns.breach || 0) < G.t && me.res.mu >= 30) {
          const gs = visibleEnemies.find(o => o.type === 'squad' && o.garrison != null && U.dist2(o.x, o.y, e.x, e.y) < 35 * 35);
          if (gs && G.rng() < .6) { SIM.issue(G, [e.id], { type: 'ability', id: 'breach', x: gs.x, y: gs.y }); continue; }
        }
        if (e.def.abilities.includes('barrage') && (e.cooldowns.barrage || 0) < G.t && e.crew && e.crew.state === 'deployed') {
          // shell team weapons first, then squads dug in (garrisons, heavy cover) that small arms can't shift
          const inReach = o => o.type === 'squad' && !o.retreating && U.dist2(o.x, o.y, e.x, e.y) < 85 * 85 && U.dist2(o.x, o.y, e.x, e.y) > 30 * 30;
          const tgt = visibleEnemies.find(o => inReach(o) && o.def.crewWeapon) || visibleEnemies.find(o => inReach(o) && (o.garrison != null || COMBAT.squadCover(G, o) === 'heavy'));
          if (tgt) { SIM.issue(G, [e.id], { type: 'ability', id: 'barrage', x: tgt.x, y: tgt.y }); continue; }
        }
      }
      // crew abandoned guns and pick up dropped weapons nearby when no enemy is close to them
      if (SIM.canPickUp(e) && e.order.type !== 'pickup' && G.drops && G.drops.length && G.rng() < .5) {
        const d = G.drops.find(d => U.dist2(d.x, d.y, e.x, e.y) < 22 * 22 && (d.kind === 'team' ? e.models.filter(m => m.alive).length >= 3 : (e.picked || 0) < 2) && FOG.seen(G, slot, d.x, d.y) && !visibleEnemies.some(o => U.dist2(o.x, o.y, d.x, d.y) < 15 * 15));
        if (d) { SIM.issue(G, [e.id], { type: 'pickup', drop: d.id }); continue; }
      }
      // climb into abandoned vehicles nearby
      if (SIM.canPickUp(e) && e.order.type !== 'recrew' && e.models.filter(m => m.alive).length >= 3 && G.rng() < .5) {
        const v = G.ents.find(v => !v.dead && v.type === 'vehicle' && v.owner < 0 && U.dist2(v.x, v.y, e.x, e.y) < 25 * 25 && FOG.seen(G, slot, v.x, v.y) && !visibleEnemies.some(o => U.dist2(o.x, o.y, v.x, v.y) < 15 * 15));
        if (v) { SIM.issue(G, [e.id], { type: 'recrew', target: v.id }); continue; }
      }
      // a garrison mostly holds its house
      if (e.garrison != null && !e.reRole && G.rng() > .04) continue;
      // busy moving or fighting: let it be, but re-target now and then
      const busy = (e.path && e.path.length) || e.order.type === 'attack' || (e.crew && e.crew.state !== 'packed' && G.t - e.lastFire < 8) || (G.t - e.lastFire < 3);
      if (busy && !e.reRole && G.rng() > .08) continue;
      if (e.crew && e.crew.state !== 'packed' && !e.reRole) {
        // a set-up gun stays put while it has enemies in reach; otherwise it moves on now and then
        const cw = SIM.weaponOf(e), reach = cw ? cw.rng[2] : 40;
        if (visibleEnemies.some(o => U.dist2(o.x, o.y, e.crew.x, e.crew.y) < reach * reach) || G.rng() > .05) continue;
      }
      // work the standing order: where to go for it
      let role = e.role;
      const own = goals.filter(g => g.p.owner === slot), open = goals.filter(g => g.p.owner !== slot);
      if (role === 'supply' && !open.some(g => SIM.connected(G, slot, g.p))) role = 'defend';   // nothing left to take that would pay
      if (role === 'defend' && !own.length) role = 'capture';
      if (role === 'capture' && !open.length) role = 'defend';
      let best = null, bs = -1e9, tx, ty;
      if (role === 'hunt') {
        const q = quarry || S.lastSeen || open.filter(g => g.p.owner === enemy).map(g => g.p).sort((a, b) => U.dist2(a.x, a.y, e.x, e.y) - U.dist2(b.x, b.y, e.x, e.y))[0] || enemyHq;
        if (!q) continue;
        if (quarry && U.dist2(q.x, q.y, e.x, e.y) < 14 * 14) continue;   // in contact: the squad fights it out where it stands
        tx = q.x + G.rng.range(-3, 3); ty = q.y + G.rng.range(-3, 3);
      } else {
        for (const g of role === 'defend' ? own : open) {
          const d = Math.hypot(g.p.x - e.x, g.p.y - e.y), t = g.p.type;
          // builders take only points close to home: losing the only builder stalls the whole tech tree
          if (e.def.builder && role !== 'defend' && Math.hypot(g.p.x - hq.x, g.p.y - hq.y) > 75) continue;
          let s;
          if (role === 'capture') s = g.v * (g.p.owner === enemy ? 1.3 : 1) * 40 - d * .35 - g.assigned * 25 + (e.type === 'vehicle' && t === 'victory' ? 20 : 0);
          else if (role === 'supply') { if (!SIM.connected(G, slot, g.p)) continue; s = (t === 'fuel' ? 3 : t === 'munitions' ? 2.6 : t === 'standard' ? 1.6 : 1) * 40 - d * .35 - Math.hypot(g.p.x - hq.x, g.p.y - hq.y) * .2 - g.assigned * 25; }
          else s = (t === 'victory' ? 3 : t === 'standard' ? 1.4 : 2.2) * (g.border ? 2 : .6) * (g.threat ? 2.5 : 1) * 40 - d * .35 - g.assigned * 30;
          if (s > bs) { bs = s; best = g; }
        }
        if (!best) continue;
        best.assigned++;
      }
      e.reRole = false;
      const p = best ? best.p : { x: tx, y: ty };
      // team weapons sit a little back from the spot, facing the enemy
      const toward = enemyHq ? Math.atan2(enemyHq.y - p.y, enemyHq.x - p.x) : 0;
      if (best) { tx = p.x + G.rng.range(-4, 4); ty = p.y + G.rng.range(-4, 4); }
      if (e.crew) { tx = p.x - Math.cos(toward) * 8; ty = p.y - Math.sin(toward) * 8; }
      if (role === 'defend') {
        // engineers on the spot wall it once: a sandbag line across the enemy's side
        if (e.def.builder && U.dist2(p.x, p.y, e.x, e.y) < 12 * 12 && !(p.fort && p.fort[slot])) {
          (p.fort || (p.fort = {}))[slot] = true;
          const fx = p.x + Math.cos(toward) * 7, fy = p.y + Math.sin(toward) * 7, sx = -Math.sin(toward) * 6, sy = Math.cos(toward) * 6;
          SIM.issue(G, [e.id], { type: 'build', what: 'sandbags', x: fx - sx, y: fy - sy, x2: fx + sx, y2: fy + sy }); continue;
        }
        // defenders stand on the enemy's side of the point
        if (!e.crew) { tx += Math.cos(toward) * 4; ty += Math.sin(toward) * 4; }
      }
      // infantry hold a point from a house beside it: defenders mostly, the others sometimes
      if (best && e.type === 'squad' && !e.def.builder && !e.crew && G.rng() < (role === 'defend' ? .7 : .3) && (role === 'defend' || best.p.owner === slot)) {
        const h = G.map.houses.find(h => !h.dead && h.occ == null && U.dist2(h.x, h.y, p.x, p.y) < (role === 'defend' ? 20 : 14) ** 2);
        if (h) { SIM.issue(G, [e.id], { type: 'garrison', house: h.id }); continue; }
      }
      if (U.dist2(tx, ty, e.x, e.y) < 6 * 6) continue;   // already there
      SIM.issue(G, [e.id], { type: e.crew ? 'move' : 'attackMove', x: tx, y: ty, face: toward });
    }
  }
  return { step, build, ROLES };
})();
if (typeof module !== 'undefined') module.exports = AI;
