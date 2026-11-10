"""Classify each name occurrence: verified, suspected misread (with suggestion), or unresolved."""
import csv, json, sys, os, difflib
from collections import defaultdict, Counter
outdir=sys.argv[1]
occ=list(csv.DictReader(open(os.path.join(outdir,'name_occurrences.csv'))))
gv=json.load(open(os.path.join(outdir,'gnverifier_results.json')))
eng=set(w.strip().lower() for w in open('/usr/share/dict/words'))
def english(w):
    if w in eng: return True
    for suf,rep in (('ies','y'),('es',''),('s',''),('ed',''),('ed','e'),('ing',''),('ing','e'),('ly','')):
        if w.endswith(suf) and w[:-len(suf)]+rep in eng: return True
    return False
# trusted names: verifier Exact, or Fuzzy target names
trusted=Counter(); trusted_by_druid=defaultdict(Counter)
for o in occ:
    v=gv.get(o['name'])
    if v and v['matchType']=='Exact':
        trusted[o['name']]+=1; trusted_by_druid[o['druid']][o['name']]+=1
for v in gv.values():
    if v['matchType']=='Fuzzy' and len(v['matched'].split())==2: trusted[v['matched']]+=0
tlist=list(trusted)
def nearest(name, pool, cutoff):
    m=difflib.get_close_matches(name,pool,n=1,cutoff=cutoff); return m[0] if m else ''
cache={}
for o in occ:
    d=o['druid']; n=o['name']; local=list(trusted_by_druid[d])
    status=sugg=basis=''
    if o['form']=='binomial':
        v=gv.get(n,{}); mt=v.get('matchType','NoMatch')
        if mt=='Exact': status='verified'
        elif mt=='Fuzzy' and len(v['matched'].split())==2: status,sugg,basis='suspected_misread',v['matched'],f"verifier fuzzy ed={v['editDistance']}"
        else:
            if mt=='PartialExact' and english(o['epithet']): status='not_a_name'
            else:
                s=nearest(n,local,0.80)
                if s: status,sugg,basis='suspected_misread',s,'close to verified name in same paper'
                else:
                    key=('c',n)
                    if key not in cache: cache[key]=nearest(n,tlist,0.85)
                    s=cache[key]
                    if s: status,sugg,basis='suspected_misread',s,'close to verified name elsewhere in corpus'
                    elif mt=='PartialExact': status,basis='genus_only','genus verified; epithet not found'
                    else: status='unresolved'
    else:  # abbreviated "L. scutulata": compare with same-paper verified names sharing the initial
        cands=[t for t in local if t[0]==o['genus'][0]]
        exact=[t for t in cands if t.split(' ',1)[1]==o['epithet']]
        if exact: status,sugg,basis='verified',exact[0],'expands to verified name in same paper'
        else:
            eps={t.split(' ',1)[1]:t for t in cands}
            m=difflib.get_close_matches(o['epithet'],list(eps),n=1,cutoff=0.75)
            if m: status,sugg,basis='suspected_misread',eps[m[0]],'abbrev; epithet close to verified name in same paper'
            else:
                eps2={t.split(' ',1)[1] for t in tlist if t[0]==o['genus'][0]}
                if o['epithet'] in eps2: status,basis='verified','epithet matches a verified name with same initial'
                else: status='unresolved'
    o.update(status=status,suggestion=sugg,basis=basis,page_type='text' if o['page_words'] and int(o['page_words'])>=150 else 'sparse (figure/table/short)')
with open(os.path.join(outdir,'name_findings.csv'),'w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(occ[0].keys())); w.writeheader(); w.writerows(occ)
real=[o for o in occ if o['status']!='not_a_name']
print('occurrences (excl. not_a_name):',len(real)); print(Counter(o['status'] for o in real))
print('by page type:')
for pt in ['text','sparse (figure/table/short)']:
    c=Counter(o['status'] for o in real if o['page_type']==pt); tot=sum(c.values())
    print(' ',pt,tot,{k:f"{v} ({v/tot:.1%})" for k,v in c.most_common()})
sm=[o for o in real if o['status']=='suspected_misread']
print('suspected misreads:',len(sm),'in druids',len({o['druid'] for o in sm}),'pages',len({o['page'] for o in sm}))
print('basis',Counter(o['basis'].split(' ed=')[0] for o in sm))
