"""Crop the image region of a word sequence from its page via the IIIF Image API.
usage: iiif_crop.py ROOT PAGE_STEM "words to find" OUT.jpg [pad]"""
import sys, re, urllib.request, csv, os, xml.etree.ElementTree as ET
root, stem, phrase, out = sys.argv[1:5]; pad=int(sys.argv[5]) if len(sys.argv)>5 else 40
NS='{http://www.loc.gov/standards/alto/ns-v4#}'
druid=stem.split('_')[0][:11]
x=os.path.join(root,'druids',druid,stem+'.xml')
ss=[s for s in ET.parse(x).getroot().iter(NS+'String')]
target=phrase.split()
for i in range(len(ss)):
    if [s.get('CONTENT') for s in ss[i:i+len(target)]]==target:
        sel=ss[i:i+len(target)]; break
else: sys.exit('phrase not found')
x0=min(int(s.get('HPOS')) for s in sel)-pad; y0=min(int(s.get('VPOS')) for s in sel)-pad
x1=max(int(s.get('HPOS'))+int(s.get('WIDTH')) for s in sel)+pad; y1=max(int(s.get('VPOS'))+int(s.get('HEIGHT')) for s in sel)+pad
x0,y0=max(x0,0),max(y0,0)
url=f'https://stacks.stanford.edu/image/iiif/{druid}%2F{stem}/{x0},{y0},{x1-x0},{y1-y0}/full/0/default.jpg'
req=urllib.request.Request(url,headers={'User-Agent':'hms-ocr-quality-check'})
open(out,'wb').write(urllib.request.urlopen(req,timeout=60).read())
print(url)
