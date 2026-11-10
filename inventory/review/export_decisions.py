"""Write the review choices (saved JSON documents from the review page's database) to decisions.csv.
usage: export_decisions.py DIR_OF_DOC_JSON  -> inventory/review/decisions.csv"""
import csv, json, os, sys
src = sys.argv[1]; here = os.path.dirname(os.path.abspath(__file__))
items = {i['id']: i for i in json.load(open(os.path.join(here, 'items.json')))}
cols = ['id', 'page', 'druid', 'band', 'ocr', 'suggestion', 'wc', 'decision', 'pageShows', 'searchName', 'note', 'decidedSeparately', 'updatedAt']
rows = []
for f in sorted(os.listdir(src)):
    doc = json.load(open(os.path.join(src, f))); d = doc.get('data', doc); iid = doc.get('id', f[:-5])
    it = items.get(iid)
    if not it: continue
    sn = d.get('preferredName') or (it['suggestion'] if d.get('useClosest') else '')
    rows.append(dict(id=iid, page=it['page'], druid=it['druid'], band=it['group'], ocr=it['ocr'], suggestion=it['suggestion'], wc=it['wc'],
                     decision=d.get('decision', ''), pageShows=d.get('pageShows', ''), searchName=sn, note=d.get('note', ''),
                     decidedSeparately='yes' if d.get('separate') else '', updatedAt=d.get('updatedAt', '')))
with open(os.path.join(here, 'decisions.csv'), 'w', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), 'saved records;', Counter(r['decision'] or '(none)' for r in rows))
