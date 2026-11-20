// Standing orders: one army's units are dealt the four orders in turn (the other plays the normal AI) and the test
// measures whether each order shows in what its units do. Prints one line per order and `orders ok` or what failed.
// usage: node game/test/roles.js [minutes] [games]
const path = require('path'), fs = require('fs');
const src = p => path.join(__dirname, '..', 'src', p);
global.U = require(src('util.js')); global.DATA = require(src('data.js')); global.MAP = require(src('map.js'));
global.FOG = require(src('fog.js')); global.COMBAT = require(src('combat.js')); global.SIM = require(src('sim.js')); global.AI = require(src('ai.js'));
const layout = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'art', 'crew_layout.json')));
const mins = +(process.argv[2] || 12), games = +(process.argv[3] || 4), roles = Object.keys(AI.ROLES), fails = [];
const T = {}; for (const r of roles) T[r] = { n: 0, onOwn: 0, onOpen: 0, cutOff: 0, onRes: 0, nearEnemy: 0, adv: 0, garr: 0 };
let walls = 0;
for (let g = 0; g < games; g++) {
  const G = SIM.create({ seed: 7, playerSide: g % 2 ? 'de' : 'us', crewLayout: layout, mode: 'spectate' });
  G.rng = U.rng(4242 + g);
  const hq = SIM.hqOf(G, 0), ehq = SIM.hqOf(G, 1), span = Math.hypot(ehq.x - hq.x, ehq.y - hq.y);
  while (G.t < mins * 60 && !G.over) {
    // slot 0 spends like the AI; its units are dealt the four orders in turn (builders: supply and defend)
    for (const e of G.ents) if (e.owner === 0 && e.type !== 'building' && !e.dead && !e.dealt) { e.dealt = true; e.role = e.def.builder ? (e.id % 2 ? 'supply' : 'defend') : roles[e.id % 4]; }
    AI.step(G, 0); AI.step(G, 1); SIM.step(G, SIM.DT);
    if ((G.t * 20 | 0) % 40 || G.t < 120) continue;   // sample every 2 s after the opening
    const foes = G.ents.filter(e => e.owner === 1 && !e.dead && e.type !== 'building');
    for (const e of G.ents) {
      if (e.owner !== 0 || e.dead || e.type === 'building' || e.retreating || e.def.builder) continue;
      if (Math.hypot(e.x - hq.x, e.y - hq.y) < 30) continue;   // refilling at base
      const t = T[e.role]; t.n++;
      const p = G.map.points.slice().sort((a, b) => U.dist2(a.x, a.y, e.x, e.y) - U.dist2(b.x, b.y, e.x, e.y))[0];
      if (U.dist2(p.x, p.y, e.x, e.y) < 20 * 20) { if (p.owner === 0) t.onOwn++; else { t.onOpen++; if (!SIM.connected(G, 0, p)) t.cutOff++; if (p.type === 'fuel' || p.type === 'munitions') t.onRes++; } }
      if (foes.some(f => U.dist2(f.x, f.y, e.x, e.y) < 30 * 30)) t.nearEnemy++;
      t.adv += ((e.x - hq.x) * (ehq.x - hq.x) + (e.y - hq.y) * (ehq.y - hq.y)) / (span * span);
      if (e.garrison != null) t.garr++;
    }
  }
  walls += G.map.covers.filter(c => c.kind === 'sandbags' && c.owner === 0).length;
}
const o = {};
for (const r of roles) { const t = T[r], f = v => t.n ? +(v / t.n).toFixed(2) : 0; o[r] = { samples: t.n, onOwnPoint: f(t.onOwn), onOpenPoint: f(t.onOpen), onCutOffPoint: f(t.cutOff), resourceShare: t.onOpen ? +(t.onRes / t.onOpen).toFixed(2) : 0, nearEnemy: f(t.nearEnemy), advance: f(t.adv), garrisoned: f(t.garr) }; console.log(r.padEnd(8), JSON.stringify(o[r])); if (!t.n) fails.push(r + ': no unit ever left the base'); }
console.log('sandbag sections laid by defending builders:', walls);
if (!(o.defend.onOwnPoint > o.capture.onOwnPoint && o.defend.onOwnPoint > o.hunt.onOwnPoint)) fails.push('defenders are not on their own points more than capturers and hunters');
if (!(o.hunt.nearEnemy > o.defend.nearEnemy && o.hunt.nearEnemy > o.supply.nearEnemy)) fails.push('hunters are not near the enemy more than defenders and suppliers');
if (!(o.capture.onOpenPoint > o.defend.onOpenPoint)) fails.push('capturers are not on points they do not hold more than defenders');
if (!(o.supply.resourceShare > o.capture.resourceShare)) fails.push('suppliers do not favour fuel and munitions points over capturers');
if (!(o.supply.onCutOffPoint < .05)) fails.push('suppliers go for points that would be cut off and pay nothing');
if (!(o.defend.garrisoned > o.capture.garrisoned)) fails.push('defenders do not hold houses more than capturers');
if (!(walls > 0)) fails.push('defending builders laid no sandbags');
console.log(fails.length ? fails.map(x => 'FAIL: ' + x).join('\n') : 'orders ok');
