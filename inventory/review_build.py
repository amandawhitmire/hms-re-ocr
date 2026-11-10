"""Pick names for visual review, locate them in the ALTO, and download IIIF crops."""
import os, sys, re, csv, json, time, random, difflib, urllib.request, xml.etree.ElementTree as ET
from collections import defaultdict
root, outdir = sys.argv[1], sys.argv[2]
NS='{http://www.loc.gov/standards/alto/ns-v4#}'
crops=os.path.join(outdir,'review','crops'); os.makedirs(crops,exist_ok=True)
rows=list(csv.DictReader(open(os.path.join(root,'inventory','name_findings.csv'))))
for i,r in enumerate(rows): r['row']=i
sm=[r for r in rows if r['status']=='suspected_misread']
low=[r for r in sm if float(r['wc'])<0.90]; mid=[r for r in sm if 0.90<=float(r['wc'])<0.95]
high=[r for r in sm if float(r['wc'])>=0.95]; random.Random(7).shuffle(high)
# heavily garbled: unresolved, low confidence, loosely close to a verified name in the same paper
ver=defaultdict(set)
for r in rows:
    if r['status']=='verified' and r['form']=='binomial': ver[r['druid']].add(r['name'])
garb=[]
for r in rows:
    if r['status']=='unresolved' and r['form']=='binomial' and float(r['wc'])<0.85:
        m=difflib.get_close_matches(r['name'],list(ver[r['druid']]),n=1,cutoff=0.65)
        if m: r['suggestion']=m[0]; r['basis']='loose match to verified name in same paper'; garb.append(r)
sel=[('low','Low confidence (below 0.90)',low),('mid','Uncertain (0.90 to 0.95)',mid),('high','High confidence sample (0.95 and up)',high[:100]),('garbled','Heavily garbled',garb)]
# occurrence number of each row among same page+name, to find the right spot on the page
nth={}; seen=defaultdict(int)
for r in rows:
    k=(r['page'],r['name']); nth[r['row']]=seen[k]; seen[k]+=1
norm=lambda s: re.sub(r'^[(\[]+|[.,;:)\]]+$','',s)
def locate(page, druid, genus, epithet, n):
    ss=[s for s in ET.parse(os.path.join(root,'druids',druid,page+'.xml')).getroot().iter(NS+'String')]
    C=[s.get('CONTENT','') for s in ss]
    def word_at(i, target):   # returns end index if target matches at i (allowing a line-end hyphen join)
        if i<len(C) and norm(C[i])==norm(target): return i
        if i+2<len(C) and C[i+1]=='-' and norm(C[i]+C[i+2])==norm(target): return i+2
        return None
    hits=[]
    for i in range(len(C)):
        e=word_at(i,genus)
        if e is None: continue
        e2=word_at(e+1,epithet)
        if e2 is not None: hits.append(ss[i:e2+1])
    if len(hits)<=n: return None
    sel=hits[n]
    x0=min(int(s.get('HPOS')) for s in sel); y0=min(int(s.get('VPOS')) for s in sel)
    x1=max(int(s.get('HPOS'))+int(s.get('WIDTH')) for s in sel); y1=max(int(s.get('VPOS'))+int(s.get('HEIGHT')) for s in sel)
    return x0,y0,x1,y1
items=[]; fails=[]
for gid,glabel,group in sel:
    for r in group:
        bb=locate(r['page'],r['druid'],r['genus'],r['epithet'],nth[r['row']])
        if not bb: fails.append((r['page'],r['name'])); continue
        x0,y0,x1,y1=bb; px,py=160,70
        X,Y=max(x0-px,0),max(y0-py,0); W,H=x1-x0+2*px,y1-y0+2*py
        size='1100,' if W>1100 else 'full'
        iid=f"{r['page']}-{nth[r['row']]}-{re.sub(r'[^A-Za-z0-9]','',r['name'])[:30]}"
        fp=os.path.join(crops,iid+'.jpg')
        url=f"https://stacks.stanford.edu/image/iiif/{r['druid']}%2F{r['page']}/{X},{Y},{W},{H}/{size}/0/default.jpg"
        if not os.path.exists(fp):
            req=urllib.request.Request(url,headers={'User-Agent':'hms-ocr-quality-check'})
            for a in range(3):
                try: open(fp,'wb').write(urllib.request.urlopen(req,timeout=60).read()); break
                except Exception as e: time.sleep(3)
            else: fails.append((r['page'],r['name'],'download')); continue
            time.sleep(0.15)
        items.append(dict(id=iid,group=gid,groupLabel=glabel,druid=r['druid'],page=r['page'],year=r['druid'] and '',
            ocr=r['name'],suggestion=r['suggestion'],wc=float(r['wc']),pageType=r['page_type'],basis=r['basis'],
            box=[x0,y0,x1,y1],crop=f"crops/{iid}.jpg",
            fullPage=f"https://stacks.stanford.edu/image/iiif/{r['druid']}%2F{r['page']}/full/pct:40/0/default.jpg"))
meta={r['id']:r for r in csv.DictReader(open(os.path.join(root,'metadata-hms-student-corpus.csv'),encoding='utf-8-sig'))}
for it in items:
    m=meta.get(it['druid'],{}); it['year']=m.get('date','')[:4]; it['title']=m.get('title','')
json.dump(items,open(os.path.join(outdir,'review','items.json'),'w'),ensure_ascii=False)
from collections import Counter
print('items',len(items),Counter(i['group'] for i in items)); print('fails',len(fails),fails[:15])
print('crop bytes total',sum(os.path.getsize(os.path.join(crops,f)) for f in os.listdir(crops)))
