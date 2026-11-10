"""Per-page text quality signals from the ALTO + txt files. Read-only on druids/."""
import os, sys, re, csv, xml.etree.ElementTree as ET
from collections import Counter, defaultdict
root=sys.argv[1]; outdir=sys.argv[2]
NS='{http://www.loc.gov/standards/alto/ns-v4#}'
ddir=os.path.join(root,'druids')
meta={r['id']:r for r in csv.DictReader(open(os.path.join(root,'metadata-hms-student-corpus.csv'),encoding='utf-8-sig'))}
pages=[]  # (druid, stem, [(word,wc)], txt)
for d in sorted(os.listdir(ddir)):
    p=os.path.join(ddir,d)
    if not os.path.isdir(p): continue
    for f in sorted(os.listdir(p)):
        if f.endswith('.xml'):
            stem=f[:-4]
            r=ET.parse(os.path.join(p,f)).getroot()
            ws=[(s.get('CONTENT',''),float(s.get('WC') or 0)) for s in r.iter(NS+'String')]
            pages.append((d,stem,ws,open(os.path.join(p,stem+'.txt'),encoding='utf-8').read()))
# lexicon: system dictionary + corpus words seen often, in several druids, read with high confidence
dic=set(w.strip().lower() for w in open('/usr/share/dict/words'))
dic|=set(w.strip().lower() for w in open('/usr/share/dict/web2a') for w in w.split())
freq=Counter(); druids_of=defaultdict(set); wcsum=Counter()
ALPHA=re.compile(r"^[A-Za-z][a-z]+$|^[A-Z]+$")
for d,stem,ws,_ in pages:
    for w,c in ws:
        if ALPHA.match(w):
            lw=w.lower(); freq[lw]+=1; druids_of[lw].add(d); wcsum[lw]+=c
corpus_lex={w for w in freq if freq[w]>=5 and len(druids_of[w])>=3 and wcsum[w]/freq[w]>=0.90}
def known(w):
    if w in dic or w in corpus_lex: return True
    for suf,rep in (('ies','y'),('es',''),('s',''),('ed',''),('ed','e'),('ing',''),('ing','e'),('ly',''),('ally','al'),('er',''),('est','')):
        if w.endswith(suf) and (w[:-len(suf)]+rep) in dic: return True
    return False
rows=[]; oov_all=Counter()
for d,stem,ws,txt in pages:
    alpha=[(w,c) for w,c in ws if ALPHA.match(w) and len(w)>=3]
    oov=[w for w,c in alpha if not known(w.lower())]
    oov_all.update(w.lower() for w in oov)
    weird=[w for w,c in ws if re.search(r'[^\x00-\x7F°±µ×÷§¶—–‘’“”…·αβγδεθλμπσΩ]',w)]
    lines=txt.split('\n')
    hyph=sum(1 for i,l in enumerate(lines[:-1]) if re.search(r'[A-Za-z]-$',l.rstrip()) and re.match(r'\s*[a-z]',lines[i+1] or ''))
    wcs=[c for w,c in ws]
    m=meta.get(d,{})
    rows.append(dict(druid=d,page=stem,date=m.get('date','')[:4],words=len(ws),alpha_words=len(alpha),
        mean_wc=round(sum(wcs)/len(wcs),4) if wcs else '',
        low_wc_frac=round(sum(c<0.8 for c in wcs)/len(wcs),4) if wcs else '',
        oov_frac=round(len(oov)/len(alpha),4) if alpha else '',
        nonstandard_chars=len(weird), line_end_hyphens=hyph,
        sample_oov=' '.join(oov[:15])))
os.makedirs(outdir,exist_ok=True)
with open(os.path.join(outdir,'page_signals.csv'),'w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
with open(os.path.join(outdir,'oov_words.csv'),'w',newline='') as fh:
    w=csv.writer(fh); w.writerow(['word','count'])
    for k,v in oov_all.most_common(): w.writerow([k,v])
print('pages',len(rows),'corpus lexicon',len(corpus_lex))
