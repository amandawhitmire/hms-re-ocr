import os, sys, json, re, csv
import xml.etree.ElementTree as ET
from collections import Counter
ddir=sys.argv[1]; out=sys.argv[2]
NS='{http://www.loc.gov/standards/alto/ns-v4#}'
rows=[]; probs=Counter(); examples={}
for d in sorted(os.listdir(ddir)):
    p=os.path.join(ddir,d)
    if not os.path.isdir(p): continue
    for f in sorted(os.listdir(p)):
        if not f.endswith('.xml'): continue
        stem=f[:-4]; base=os.path.join(p,stem)
        r=dict(druid=d,page=stem)
        try:
            root=ET.parse(base+'.xml').getroot()
        except Exception as e:
            probs['xml_not_wellformed']+=1; examples.setdefault('xml_not_wellformed',stem); continue
        if root.tag!=NS+'alto': probs['xml_wrong_ns']+=1
        strs=root.iter(NS+'String'); words=[s.get('CONTENT','') for s in strs]
        wcs=[float(s.get('WC')) for s in root.iter(NS+'String') if s.get('WC')]
        pg=root.find(f'.//{NS}Page')
        fn=root.find(f'.//{NS}fileName')
        if fn is None or fn.text!=stem: probs['xml_filename_mismatch']+=1; examples.setdefault('xml_filename_mismatch',(stem, fn.text if fn is not None else None))
        try: j=json.load(open(base+'.json'))
        except Exception: probs['json_unreadable']+=1; examples.setdefault('json_unreadable',stem); continue
        resp=j.get('responses',[j])[0] if isinstance(j,dict) else {}
        if 'error' in resp: probs['json_has_error']+=1; examples.setdefault('json_has_error',stem)
        fta=resp.get('fullTextAnnotation',{})
        jtext=fta.get('text','')
        jwords=sum(len(pa['words']) for pg_ in fta.get('pages',[]) for b in pg_.get('blocks',[]) for pa in b.get('paragraphs',[]))
        txt=open(base+'.txt',encoding='utf-8').read()
        nows=lambda s: re.sub(r'\s+','',s)
        r.update(xml_words=len(words), json_words=jwords, txt_chars=len(nows(txt)), xml_chars=len(nows(''.join(words))), json_chars=len(nows(jtext)),
                 mean_wc=round(sum(wcs)/len(wcs),4) if wcs else '', pc=pg.get('PC') if pg is not None else '',
                 w=pg.get('WIDTH') if pg is not None else '', h=pg.get('HEIGHT') if pg is not None else '',
                 lang=';'.join(l.get('languageCode','') for l in fta.get('pages',[{}])[0].get('property',{}).get('detectedLanguages',[])) if fta.get('pages') else '')
        if jwords!=len(words): probs['xml_vs_json_wordcount']+=1; examples.setdefault('xml_vs_json_wordcount',(stem,len(words),jwords))
        if r['txt_chars']!=r['xml_chars']: probs['txt_vs_xml_chars']+=1; examples.setdefault('txt_vs_xml_chars',(stem,r['txt_chars'],r['xml_chars']))
        if r['txt_chars']!=r['json_chars']: probs['txt_vs_json_chars']+=1; examples.setdefault('txt_vs_json_chars',(stem,r['txt_chars'],r['json_chars']))
        if not words: probs['no_words']+=1
        rows.append(r)
with open(out,'w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('pages checked',len(rows)); print(dict(probs)); print(examples)
wc=[r['mean_wc'] for r in rows if r['mean_wc']!='']
wc.sort(); n=len(wc)
print('mean word conf per page: min',wc[0],'p5',wc[n//20],'p25',wc[n//4],'median',wc[n//2],'p75',wc[3*n//4])
print('pages <0.80:',sum(x<0.8 for x in wc),'<0.90:',sum(x<0.9 for x in wc))
print('langs',Counter(r['lang'] for r in rows).most_common(12))
print('words total',sum(r['xml_words'] for r in rows))
