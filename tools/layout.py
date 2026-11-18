"""Write <art>/crew_layout.json: who stands where round each crew weapon. python3 tools/layout.py [art]"""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from models import roster
L = {}
for side in roster.SIDES: L.update(roster.layout(side))
json.dump(dict(note='x, y in artkit units (160 a tile) in the weapon\'s own frame: +x the way it faces, +y its left; heading in degrees relative to the weapon', weapons=L),
          open(os.path.join(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'art'), 'crew_layout.json'), 'w'), indent=1)
print('wrote', len(L), 'layouts')
