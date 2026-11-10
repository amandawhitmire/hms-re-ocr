"""Stratified sample: decade x confidence band, at most one page per druid, fixed seed."""
import pandas as pd
p=pd.read_csv('inventory/page_signals.csv'); p=p[p.words>=20].copy()
p['decade']=(p.date//10*10).clip(upper=2000)  # fold 2010s (6 druids) into 2000s
p['band']=pd.cut(p.mean_wc,[0,0.85,0.93,0.97,1.0],labels=['<0.85','0.85-0.93','0.93-0.97','>=0.97'])
p=p.sample(frac=1,random_state=42)
picked=[]; used=set()
for (dec,band),g in p.groupby(['decade','band'],observed=True):
    n=0
    for _,r in g.iterrows():
        if r.druid in used: continue
        picked.append(r); used.add(r.druid); n+=1
        if n==2: break
s=pd.DataFrame(picked).sort_values(['decade','band'])
s.to_csv('inventory/sample_pages.csv',index=False)
print(len(s)); print(s.groupby(['decade','band'],observed=True).size().unstack())
