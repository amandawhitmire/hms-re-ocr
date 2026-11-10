import csv, os, re, sys, json
from collections import Counter, defaultdict
root = sys.argv[1]; out = sys.argv[2]
rows = list(csv.DictReader(open(os.path.join(root,'metadata-hms-student-corpus.csv'), newline='', encoding='utf-8-sig')))
meta = {}
dup_ids = [i for i,c in Counter(r['id'] for r in rows).items() if c>1]
for r in rows: meta[r['id'].strip()] = r
ddir = os.path.join(root,'druids')
druids = sorted(d for d in os.listdir(ddir) if os.path.isdir(os.path.join(ddir,d)))
nondirs = sorted(d for d in os.listdir(ddir) if not os.path.isdir(os.path.join(ddir,d)))
print("CSV rows:", len(rows), "unique ids:", len(meta), "dup ids:", dup_ids)
print("columns:", list(rows[0].keys()))
print("druid folders:", len(druids), "non-dir entries in druids/:", nondirs)
notincsv = [d for d in druids if d not in meta]
print("folders NOT in CSV:", notincsv)
print("druid name pattern failures:", [d for d in druids if not re.fullmatch(r'[b-df-hjkmnp-tv-z]{2}\d{3}[b-df-hjkmnp-tv-z]{2}\d{4}', d)])
pat = re.compile(r'^(?P<d>[a-z]{2}\d{3}[a-z]{2}\d{4})_(?P<p>\d+)\.(?P<e>json|txt|xml)$')
report = []
issues = defaultdict(list)
for d in druids:
    files = os.listdir(os.path.join(ddir,d))
    pages = defaultdict(dict); odd=[]
    for f in files:
        if f.startswith('.'): continue
        m = pat.match(f)
        if not m or m['d']!=d: odd.append(f); continue
        pages[m['p']][m['e']] = os.path.getsize(os.path.join(ddir,d,f))
    nums = sorted(int(p) for p in pages)
    gaps = sorted(set(range(1,max(nums)+1))-set(nums)) if nums else []
    incomplete = [p for p,e in pages.items() if set(e)!={'json','txt','xml'}]
    empty_txt = [p for p,e in pages.items() if e.get('txt',1)==0]
    empty_any = [p for p,e in pages.items() if any(v==0 for v in e.values())]
    csvp = meta.get(d,{}).get('pages','')
    try: csvp_i = int(csvp)
    except: csvp_i = None
    report.append(dict(id=d, ocr_pages=len(pages), csv_pages=csvp, diff=(len(pages)-csvp_i) if csvp_i is not None else '',
        first=nums[0] if nums else '', last=nums[-1] if nums else '', gaps=' '.join(map(str,gaps)),
        incomplete=' '.join(sorted(incomplete)), empty_txt=len(empty_txt), empty_any=' '.join(sorted(empty_any)), odd_files=' '.join(sorted(odd)),
        txt_bytes=sum(e.get('txt',0) for e in pages.values()),
        date=meta.get(d,{}).get('date',''), access=meta.get(d,{}).get('access',''), type=meta.get(d,{}).get('type','')))
with open(out,'w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(report[0].keys())); w.writeheader(); w.writerows(report)
tot=sum(r['ocr_pages'] for r in report)
print("total pages:", tot)
for k in ['gaps','incomplete','empty_any','odd_files']:
    bad=[r for r in report if r[k]]
    print(f"druids with {k}: {len(bad)}", [(r['id'],r[k][:80]) for r in bad[:10]])
print("druids with any empty txt pages:", sum(1 for r in report if r['empty_txt']), "total empty txt pages:", sum(r['empty_txt'] for r in report))
print("druids not starting at page 1:", [(r['id'],r['first']) for r in report if r['first']!=1])
diffs=Counter()
for r in report:
    if r['diff']=='' : diffs['csv pages blank/non-numeric']+=1
    elif r['diff']==0: diffs['match']+=1
    elif r['diff']>0: diffs['ocr > csv']+=1
    else: diffs['ocr < csv']+=1
print("page count vs CSV:", dict(diffs))
mm=[r for r in report if r['diff']!='' and r['diff']!=0]
mm.sort(key=lambda r:abs(r['diff']), reverse=True)
print("largest mismatches:", [(r['id'],r['ocr_pages'],r['csv_pages']) for r in mm[:15]])
print("diff distribution:", sorted(Counter(r['diff'] for r in mm).items())[:40])
print("non-numeric csv pages values (OCR druids):", Counter(r['csv_pages'] for r in report if r['diff']=='').most_common(10))
print("access among OCR druids:", Counter(r['access'] for r in report), "type:", Counter(r['type'] for r in report))
yrs=[int(r['date'][:4]) for r in report if r['date'][:4].isdigit()]
print("years:", min(yrs), max(yrs), "decades:", sorted(Counter(y//10*10 for y in yrs).items()))
allyrs=[int(r['date'][:4]) for r in rows if r['date'][:4].isdigit()]
print("CSV all decades:", sorted(Counter(y//10*10 for y in allyrs).items()))
print("CSV druids without OCR:", len(set(meta)-set(druids)))
