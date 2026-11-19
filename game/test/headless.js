// Headless smoke test: load the sim in Node, fight a few engagements, print outcomes.
const path = require('path'), fs = require('fs');
const src = p => path.join(__dirname, '..', 'src', p);
global.U = require(src('util.js')); global.DATA = require(src('data.js')); global.MAP = require(src('map.js'));
global.FOG = require(src('fog.js')); global.COMBAT = require(src('combat.js')); global.SIM = require(src('sim.js'));
const layout = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'art', 'crew_layout.json')));
function duel(a, b, opts = {}) {
  const G = SIM.create({ seed: 7, crewLayout: layout });
  G.players.forEach(P => { P.res.mp = 1e5; P.res.mu = 1e5; P.res.fu = 1e5; });
  const sp = (id, owner, x, y) => (DATA.SQUADS[id] ? SIM.spawnSquad : SIM.spawnVehicle)(G, id, owner, x, y);
  const g = opts.gap || 30; let Y = 20;
  for (let y = 20; y < 180; y += 2) { let ok = true; for (let dy = -4; dy <= 4; dy += 2) if (!MAP.los(G.map, 100 - g / 2 - 3, y + dy, 100 + g / 2 + 3, y + dy)) ok = false; if (ok) { Y = y; break; } }
  const A = sp(a, 0, 100 - g / 2, Y), B = sp(b, 1, 100 + g / 2, Y);
  // reveal both for the test
  let t = 0;
  while (t < (opts.time || 90)) {
    SIM.step(G, SIM.DT); t += SIM.DT;
    if (A.dead || B.dead) break;
  }
  const hp = e => e.dead ? 'dead' : e.type === 'squad' ? e.models.filter(m => m.alive).length + '/' + e.maxModels + ' supp ' + e.supp.toFixed(2) : Math.round(e.hp) + '/' + e.maxHp;
  console.log(`${a} vs ${b} @${opts.gap || 30}m: after ${t.toFixed(1)}s  A ${hp(A)}  B ${hp(B)}`);
  return G;
}
duel('us_riflemen', 'de_grenadiers', { gap: 30 });
duel('us_riflemen', 'de_grenadiers', { gap: 10 });
duel('us_hmg', 'de_grenadiers', { gap: 30 });
duel('de_hmg', 'us_riflemen', { gap: 30 });
duel('us_sherman', 'de_pz4', { gap: 30 });
duel('us_bazooka', 'de_222', { gap: 25 });
duel('de_at_gun', 'us_sherman', { gap: 33 });
duel('us_sniper', 'de_grenadiers', { gap: 34, time: 40 });
duel('us_riflemen', 'de_grenadiers', { gap: 20 });
duel('us_mortar', 'de_hmg', { gap: 34 });
duel('us_m8', 'de_grenadiers', { gap: 25 });
// a full minute of the opening with no orders
const G = SIM.create({ seed: 7, crewLayout: layout });
for (let i = 0; i < 20 * 60; i++) SIM.step(G, SIM.DT);
console.log('1 min idle: res', G.players.map(P => Object.values(P.res).map(v => v | 0).join('/')), 'income', G.players.map(P => JSON.stringify(P.income)));
