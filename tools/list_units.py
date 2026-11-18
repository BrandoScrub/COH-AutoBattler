"""Print the unit table for README.md from art/assets.json: python3 tools/list_units.py [art]
Run it after any export and paste the output over the "Every unit key" section."""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
from models import roster

A = json.load(open(os.path.join(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'art'), 'assets.json')))
what = {}
for s in roster.SIDES:
    for k, role, name, _ in roster.vehicles(s): what[k] = ('crew weapon' if roster.headings_for(k) == 8 else 'vehicle', name)
    for k, name, *_ in roster.men(s) + roster.crews(s) + roster.more_men(s): what[k] = ('man', name)
print('| Key | Kind | What | Headings | Layers | Clips |\n|---|---|---|---|---|---|')
for kind in ('vehicle', 'crew weapon', 'man'):
    for k in sorted(A, key=lambda k: (k[3:], k[:2])):
        if what[k][0] != kind: continue
        m = A[k]; print(f"| `{k}` | {kind} | {what[k][1]} | {m['headings']} | {' '.join(sorted(m['layers']))} | {', '.join(m['clips'])} |")
