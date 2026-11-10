"""Fetch the IIIF manifest for each druid folder (cached) and save a canvas table."""
import os, sys, json, time, csv, urllib.request
root, outdir = sys.argv[1], sys.argv[2]
cache=os.path.join(outdir,'manifests'); os.makedirs(cache,exist_ok=True)
druids=sorted(d for d in os.listdir(os.path.join(root,'druids')) if os.path.isdir(os.path.join(root,'druids',d)))
rows=[]; errs=[]
for d in druids:
    fp=os.path.join(cache,d+'.json')
    if not os.path.exists(fp):
        try:
            req=urllib.request.Request(f'https://purl.stanford.edu/{d}/iiif/manifest',headers={'User-Agent':'hms-ocr-quality-check'})
            open(fp,'wb').write(urllib.request.urlopen(req,timeout=60).read()); time.sleep(0.2)
        except Exception as e: errs.append((d,str(e))); continue
    m=json.load(open(fp))
    for i,c in enumerate(m['sequences'][0]['canvases'],1):
        res=c['images'][0]['resource'] if c.get('images') else {}
        svc=res.get('service',{}).get('@id','')
        stem=svc.split('%2F')[-1] if svc else ''
        alto=[s for s in c.get('seeAlso',[]) if 'alto' in s.get('profile','') or s.get('format')=='application/xml']
        rows.append(dict(druid=d,seq=i,label=c.get('label',''),image_stem=stem,width=c.get('width'),height=c.get('height'),
            service=svc,old_ocr=alto[0]['@id'] if alto else '',old_ocr_profile=alto[0].get('profile','') if alto else ''))
with open(os.path.join(outdir,'iiif_canvases.csv'),'w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('manifests ok',len(druids)-len(errs),'errors',errs[:10]); print('canvases',len(rows))
