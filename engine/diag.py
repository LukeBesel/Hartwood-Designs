"""Print check failures for a built kit: ../.venv/bin/python diag.py floral"""
import json, sys, collections
r = json.load(open(f'../kits/{sys.argv[1]}/{sys.argv[1]}_report.json'))
for c in r['checks']:
    if c['pass']:
        continue
    print('==', c['name'], c['summary'])
    det = c['details']
    if isinstance(det, dict):
        print(det); continue
    if c['name'] == 'Minimum feature check':
        cnt = collections.Counter(d['part'].rstrip('0123456789_') for d in det)
        print(cnt.most_common(30))
        for d in det[:int(sys.argv[2]) if len(sys.argv) > 2 else 12]:
            print('  ', d)
    else:
        for d in det[:int(sys.argv[2]) if len(sys.argv) > 2 else 40]:
            print('  ', d)
print('fragile:', [(f['part'], f['why']) for f in next(c for c in r['checks'] if c['name']=='Minimum feature check').get('fragile', [])][:40])
