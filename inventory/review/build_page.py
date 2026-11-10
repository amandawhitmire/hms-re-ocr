import json, base64, os, sys
d=os.path.dirname(os.path.abspath(__file__))
items=json.load(open(os.path.join(d,'items.json')))
crops={it['id']:base64.b64encode(open(os.path.join(d,it['crop']),'rb').read()).decode() for it in items}
t=open(os.path.join(d,'template.html')).read()
safe=lambda s: s.replace('</','<\\/')
app=open(os.path.join(d,'app.js')).read()
out=t.replace('__APP__',app).replace('__ITEMS__',safe(json.dumps(items,ensure_ascii=False))).replace('__CROPS__',json.dumps(crops))
open(os.path.join(d,'index.html'),'w').write(out); print(len(out.encode()))
