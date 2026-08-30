"""What still stops the 83 Praxera clones from being sendable.

Brand marks are the visible half. The half that fails quietly is deliverability
and compliance plumbing: who the mail claims to be from, whether CAN-SPAM's
physical address survived the clone, whether the plain-text alternative still
names the old company, and whether the links go anywhere real.
"""
import json,os,re,html,collections,urllib.request,time
import concurrent.futures as cf

T=os.environ["TOKEN"]
def get(u,tr=4):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    for i in range(tr):
        try: return json.load(urllib.request.urlopen(
            urllib.request.Request(u,headers={"Authorization":"Bearer "+T}),timeout=60))
        except Exception:
            if i==tr-1: raise
            time.sleep(2*(i+1))

DV_WORD=re.compile(r"da\s?vinci",re.I)
DV_LINK=re.compile(r'href\s*=\s*"(https?://(?:www\.|blog\.|info\.)?davincilabs\.com[^"]*)"',re.I)
TAG=re.compile(r"<[^>]+>")
ADDR=re.compile(r"\d{2,5}\s+[A-Z][a-z]+\s+(Lane|Street|St|Road|Rd|Ave|Avenue|Drive|Dr)",re.I)
UNSUB=re.compile(r"(unsubscribe|hs_email_unsub|\{\{\s*unsubscribe)",re.I)
CANSPAM=re.compile(r"can_spam|email_can_spam",re.I)

def bodies(c):
    o=[]
    for k,v in (c.get("widgets") or {}).items():
        b=v.get("body") or {}
        for f in ("html","value"):
            if isinstance(b.get(f),str) and b[f]: o.append(b[f])
    return o

def main():
    clones=json.load(open("reference/praxera_email_clones.json"))
    def one(c):
        d=get(f"/marketing/v3/emails/{c['clone_id']}?includeStats=false")
        cc=d.get("content") or {}
        hs=bodies(cc); joined="".join(hs)
        text=html.unescape(TAG.sub(" ",joined))
        frm=d.get("from") or {}
        plain=(cc.get("plainTextVersion") or "")
        return {
          "id":c["clone_id"],"name":c["clone_name"],"live_source":c.get("live_source"),
          "subject":d.get("subject") or "",
          "subject_dv":bool(DV_WORD.search(d.get("subject") or "")),
          "fromName":frm.get("fromName") or "",
          "replyTo":frm.get("replyTo") or "",
          "reply_dv":"davincilabs.com" in (frm.get("replyTo") or "").lower(),
          "preview":bool(((cc.get("widgets") or {}).get("preview_text") or {}).get("body",{}).get("value")),
          "dv_links":sorted(set(DV_LINK.findall(joined))),
          "dv_text":len(DV_WORD.findall(text)),
          "plain_dv":len(DV_WORD.findall(plain)),
          "plain_len":len(plain),
          "address":bool(ADDR.search(text)),
          "unsub":bool(UNSUB.search(joined)) or bool(CANSPAM.search(json.dumps(cc))),
          "placeholder":text.count("[PLACEHOLDER"),
        }
    with cf.ThreadPoolExecutor(6) as ex: rows=list(ex.map(one,clones))
    json.dump(rows,open("reference/email_code_audit.json","w"),indent=1)
    live=[r for r in rows if r["live_source"]]
    def c(k,pred=lambda v:v,rs=None): return sum(1 for r in (rs or rows) if pred(r[k]))
    print(f"clones audited: {len(rows)}   (from a live workflow: {len(live)})\n")
    print(f"{'issue':46} {'all':>5} {'live':>5}")
    def line(lbl,k,pred=lambda v:v):
        print(f"  {lbl:44} {c(k,pred):>5} {c(k,pred,live):>5}")
    line("subject line still says DaVinci","subject_dv")
    line("reply-to is still @davincilabs.com","reply_dv")
    line("links still pointing at davincilabs.com","dv_links",lambda v:len(v)>0)
    line("DaVinci still in rendered text","dv_text")
    line("plain-text version says DaVinci","plain_dv")
    line("plain-text version missing entirely","plain_len",lambda v:v==0)
    line("no physical address in the body","address",lambda v:not v)
    line("no unsubscribe / CAN-SPAM module","unsub",lambda v:not v)
    line("no preview text set","preview",lambda v:not v)
    line("carries an address placeholder","placeholder")
    print(f"\nfromName values: {dict(collections.Counter(r['fromName'] for r in rows))}")
    print(f"replyTo values : {dict(collections.Counter(r['replyTo'] for r in rows))}")
    lk=collections.Counter(u for r in rows for u in r["dv_links"])
    print(f"\nDAVINCI LINK TARGETS ({len(lk)} distinct, {sum(lk.values())} links):")
    for u,n in lk.most_common(10): print(f"   {n:>3}x  {u[:92]}")

if __name__=="__main__": main()
