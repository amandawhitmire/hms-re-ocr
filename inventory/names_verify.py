"""Send unique binomial strings to the Global Names Verifier (WoRMS 9, Catalogue of Life 1, GBIF 11). Caches results."""
import csv, json, sys, time, os, urllib.request
outdir=sys.argv[1]; cache=os.path.join(outdir,'gnverifier_results.json')
res=json.load(open(cache)) if os.path.exists(cache) else {}
names=sorted({r['name'] for r in csv.DictReader(open(os.path.join(outdir,'name_occurrences.csv'))) if r['form']=='binomial'} - set(res))
print('to verify',len(names))
for i in range(0,len(names),500):
    batch=names[i:i+500]
    body=json.dumps({'nameStrings':batch,'dataSources':[9,1,11],'withAllMatches':False}).encode()
    req=urllib.request.Request('https://verifier.globalnames.org/api/v1/verifications',data=body,headers={'Content-Type':'application/json','User-Agent':'hms-ocr-quality-check'})
    for attempt in range(4):
        try:
            out=json.load(urllib.request.urlopen(req,timeout=120)); break
        except Exception as e:
            print('retry',i,e); time.sleep(10*(attempt+1))
    else: sys.exit('failed at batch %d'%i)
    for n in out['names']:
        b=n.get('bestResult') or {}
        res[n['name']]=dict(matchType=n['matchType'],matched=b.get('matchedCanonicalSimple',''),current=b.get('currentCanonicalSimple',''),
            editDistance=b.get('editDistance',''),source=b.get('dataSourceTitleShort',''),status=b.get('taxonomicStatus',''),dataSourcesNum=n.get('dataSourcesNum',''))
    json.dump(res,open(cache,'w'))
    print(i+len(batch),'done'); time.sleep(1)
from collections import Counter
print(Counter(v['matchType'] for v in res.values()))
