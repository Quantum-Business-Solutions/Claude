"""Keep the three copies of the ledger in step.

The ledger lives in three places on purpose -- the repo (source of truth), the
ClientCommand portal (what the client opens), and a Claude artifact (what we
screen-share). They drift the moment one is edited alone, so this reads the
portal copy, stores it in the repo, and emits the artifact body with the
document wrapper stripped, since the artifact host supplies its own skeleton.
"""
import json,os,re,sys

SRC="deliverables/praxera_migration_asset_ledger.html"
ART=("/tmp/claude-0/-home-user-Claude/0f427e52-eb7f-5b23-8772-a7e122ea7371/"
     "scratchpad/praxera_ledger.html")

def to_artifact(doc):
    """Artifacts get <title>/<link>/<style> plus the body, never the skeleton."""
    head=re.search(r"<head>(.*?)</head>",doc,re.S)
    body=re.search(r"<body[^>]*>(.*?)</body>",doc,re.S)
    keep=""
    if head:
        for m in re.finditer(r"<(title|link|style)\b.*?</\1>",head.group(1),re.S):
            keep+=m.group(0)+"\n"
    return keep+(body.group(1) if body else doc)

if __name__=="__main__":
    if not os.path.exists(SRC):
        print(f"missing {SRC} -- write the portal copy there first"); sys.exit(1)
    doc=open(SRC).read()
    art=to_artifact(doc)
    os.makedirs(os.path.dirname(ART),exist_ok=True)
    open(ART,"w").write(art)
    print(f"repo copy    : {len(doc):,} bytes  {SRC}")
    print(f"artifact body: {len(art):,} bytes  {ART}")
    print("wrapper stripped:", "<!doctype" not in art.lower() and "<body" not in art.lower())
