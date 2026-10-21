import json, re, sys, time, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
def get(u):
    for i in range(3):
        try: return urllib.request.urlopen(u,timeout=60).read()
        except Exception as e: err=e; time.sleep(2)
    raise err
def epmc_doi(doi,pmid=None):
    q=f'DOI:"{doi}"' if doi else f'EXT_ID:{pmid} AND SRC:MED'
    u="https://www.ebi.ac.uk/europepmc/webservices/rest/search?"+urllib.parse.urlencode({"query":q,"format":"json","resultType":"core","pageSize":1})
    r=json.loads(get(u)); res=r["resultList"]["result"]
    if not res: return {}
    x=res[0]; pts=[p for p in (x.get("pubTypeList",{}) or {}).get("pubType",[])]
    return {"doi":x.get("doi"),"pmid":x.get("pmid"),"title":x.get("title"),"oa":x.get("isOpenAccess"),"pmcid":x.get("pmcid"),"inEPMC":x.get("inEPMC"),"pubtypes":pts,"year":x.get("pubYear"),"has_abstract":bool(x.get("abstractText"))}
def text(el):
    return "".join(el.itertext())
pmcid=sys.argv[1]; maxn=int(sys.argv[2]) if len(sys.argv)>2 else 10
xml=get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML")
root=ET.fromstring(xml)
doi=(root.find(".//article-meta/article-id[@pub-id-type='doi']").text if root.find(".//article-meta/article-id[@pub-id-type='doi']") is not None else None)
title=text(root.find(".//article-meta/title-group/article-title"))
refs={}
for ref in root.iter("ref"):
    d=ref.find(".//pub-id[@pub-id-type='doi']")
    if d is None:
        m=re.search(r"10\.\d{4,9}/[^\s<>\"]+",text(ref)); dd=m.group(0).rstrip(".,;") if m else None
    else: dd=d.text.strip()
    pm=ref.find(".//pub-id[@pub-id-type='pmid']")
    t=ref.find(".//article-title")
    refs[ref.get("id")]={"doi":dd,"pmid":(pm.text.strip() if pm is not None else None),"title":(text(t).strip() if t is not None else text(ref).strip()[:150])}
# crossref fallback by order
try:
    cr=json.loads(get("https://api.crossref.org/works/"+urllib.parse.quote(doi)+"?mailto=none@example.org"))["message"].get("reference",[])
except Exception: cr=[]
ids=[r.get("id") for r in root.iter("ref")]
if cr and len(cr)==len(ids):
    for rid,c in zip(ids,cr):
        if not refs[rid].get("doi") and c.get("DOI"): refs[rid]["doi"]=c["DOI"]
print("crossref refs",len(cr),"xml refs",len(ids),file=sys.stderr)
out=[]
for sec in root.iter("sec"):
    st=sec.find("title"); stitle=text(st).strip() if st is not None else ""
    if re.search(r"method|material|statistic|data avail|fund|author|conflict|supplement",stitle,re.I): continue
    for p in sec.findall("p"):
        # build text with markers
        parts=[]
        def walk(e):
            if e.tag=="xref" and e.get("ref-type")=="bibr":
                parts.append("\u00ab"+e.get("rid")+"\u00bb")
            elif e.tag in ("table-wrap","fig"): pass
            else:
                if e.text: parts.append(e.text)
                for c in e: walk(c); 
            if e.tail and e is not p: parts.append(e.tail)
        if p.text: parts.append(p.text)
        for c in p: walk(c)
        s="".join(parts)
        sents=re.split(r"(?<=[.!?])\s+(?=[A-Z])",s)
        for se in sents:
            rids=re.findall(r"\u00ab([^\u00bb]+)\u00bb",se)
            rid_set=set(r for x in rids for r in x.split())
            if len(rid_set)!=1: continue
            rid=rid_set.pop()
            clean=re.sub(r"\s*\u00ab[^\u00bb]+\u00bb","",se); clean=re.sub(r"\s*[\[\(][\s,–\-]*[\]\)]","",clean); clean=re.sub(r"\s+"," ",clean).strip()
            if len(clean)<70 or len(clean)>400 or not re.search(r"\d|found|show|report|increas|decreas|associat",clean): continue
            r=refs.get(rid,{})
            if not (r.get("doi") or r.get("pmid")): continue
            out.append({"section":stitle,"claim_text":clean,"cited_doi":r.get("doi"),"cited_pmid":r.get("pmid"),"cited_title":r["title"]})
seen=set(); cand=[]
for c in out:
    key=(c["cited_doi"] or c["cited_pmid"]).lower()
    if key in seen: continue
    seen.add(key); cand.append(c)
res=[]
for c in cand:
    if len(res)>=maxn: break
    m=epmc_doi(c["cited_doi"],c["cited_pmid"]); c.update({"cited_meta":m})
    if not c["cited_doi"]: c["cited_doi"]=m.get("doi")
    res.append(c)
print(json.dumps({"pmcid":pmcid,"doi":doi,"title":title,"n_sent":len(out),"candidates":res},ensure_ascii=False))
