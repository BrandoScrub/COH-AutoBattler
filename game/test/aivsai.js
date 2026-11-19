// AI against AI for a set number of minutes; prints the state every two minutes.
const path = require('path'), fs = require('fs');
const src = p => path.join(__dirname, '..', 'src', p);
global.U = require(src('util.js')); global.DATA = require(src('data.js')); global.MAP = require(src('map.js'));
global.FOG = require(src('fog.js')); global.COMBAT = require(src('combat.js')); global.SIM = require(src('sim.js')); global.AI = require(src('ai.js'));
const layout = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'art', 'crew_layout.json')));
const side = process.argv[2] || 'us', mins = +(process.argv[3] || 16), seed = +(process.argv[4] || 7);
const G = SIM.create({ seed, playerSide: side, crewLayout: layout });
const t0 = Date.now();
let next = 120;
while (G.t < mins * 60 && !G.over) {
  AI.step(G, 0); AI.step(G, 1); SIM.step(G, SIM.DT);
  if (G.t >= next) {
    next += 120;
    const s = G.players.map(P => {
      const u = G.ents.filter(e => !e.dead && e.owner === P.slot && e.type !== 'building');
      const b = G.ents.filter(e => !e.dead && e.owner === P.slot && e.type === 'building').map(b => b.defId.split('_')[1] + (b.built < 1 ? '*' : ''));
      return `${P.side} vp ${P.vp | 0} pts ${G.map.points.filter(p => p.owner === P.slot).length} res ${P.res.mp | 0}/${P.res.mu | 0}/${P.res.fu | 0} pop ${P.pop} units ${u.length} [${u.map(e => e.defId.split('_').slice(1).join('_')).join(',')}] bld ${b.join(',')}`;
    });
    console.log(U.fmtTime(G.t), '\n  ' + s.join('\n  '));
  }
}
console.log('over', G.over, 'sim time', U.fmtTime(G.t), 'wall ms', Date.now() - t0);
