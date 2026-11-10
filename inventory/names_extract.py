"""Extract taxonomic-name candidates (binomials and abbreviated binomials) from ALTO. Read-only on druids/."""
import os, sys, re, csv, json, xml.etree.ElementTree as ET
from collections import Counter, defaultdict
root, outdir = sys.argv[1], sys.argv[2]
NS='{http://www.loc.gov/standards/alto/ns-v4#}'
ddir=os.path.join(root,'druids')
eng=set(w.strip().lower() for w in open('/usr/share/dict/words'))
def english(w):
    w=w.lower()
    if w in eng: return True
    for suf,rep in (('ies','y'),('es',''),('s',''),('ed',''),('ed','e'),('ing',''),('ing','e'),('ly','')):
        if w.endswith(suf) and w[:-len(suf)]+rep in eng: return True
    return False
GEN=re.compile(r'^[A-Z][a-z]{2,}$'); EPI=re.compile(r'^[a-z]{3,}$'); ABB=re.compile(r'^[A-Z]\.$')
sig={r['page']:r for r in csv.DictReader(open(os.path.join(outdir,'page_signals.csv')))}
occ=[]
for d in sorted(os.listdir(ddir)):
    p=os.path.join(ddir,d)
    if not os.path.isdir(p): continue
    for f in sorted(os.listdir(p)):
        if not f.endswith('.xml'): continue
        stem=f[:-4]; r=ET.parse(os.path.join(p,f)).getroot()
        # word tokens in reading order; rejoin "Litto" "-" <line end> "rina"; drop trailing punctuation
        toks=[]
        for tl in r.iter(NS+'TextLine'):
            ss=[s for s in tl if s.tag==NS+'String']
            for s in ss: toks.append([s.get('CONTENT',''), float(s.get('WC') or 0), tl is not None])
            toks.append(['\n',1.0,False])
        words=[]; i=0
        while i<len(toks):
            w,c,_=toks[i]
            if w=='\n': i+=1; continue
            # line-end hyphen join: word, '-', '\n', word
            if i+3<len(toks) and toks[i+1][0]=='-' and toks[i+2][0]=='\n' and re.match(r'^[a-z]+',toks[i+3][0]):
                w=w+toks[i+3][0]; c=min(c,toks[i+3][1]); i+=4
            else: i+=1
            words.append((w,c))
        for j in range(len(words)-1):
            a,ca=words[j]; b,cb=words[j+1]
            b2=re.sub(r'[.,;:)\]]+$','',b); a2=re.sub(r'^[(\[]+','',a)
            if GEN.match(a2) and EPI.match(b2):
                if english(a2) and english(b2): continue   # both ordinary words, e.g. "The present"
                occ.append(dict(druid=d,page=stem,form='binomial',genus=a2,epithet=b2,name=f'{a2} {b2}',wc=round(min(ca,cb),4)))
            elif ABB.match(a2) and EPI.match(b2) and b2 not in eng:
                occ.append(dict(druid=d,page=stem,form='abbrev',genus=a2,epithet=b2,name=f'{a2} {b2}',wc=round(min(ca,cb),4)))
for o in occ:
    s=sig.get(o['page'],{}); o['page_words']=s.get('words',''); o['page_mean_wc']=s.get('mean_wc','')
with open(os.path.join(outdir,'name_occurrences.csv'),'w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(occ[0].keys())); w.writeheader(); w.writerows(occ)
u=Counter(o['name'] for o in occ if o['form']=='binomial')
print('occurrences',len(occ),'binomial',sum(o['form']=='binomial' for o in occ),'abbrev',sum(o['form']=='abbrev' for o in occ))
print('unique binomial strings',len(u)); print(u.most_common(25))
