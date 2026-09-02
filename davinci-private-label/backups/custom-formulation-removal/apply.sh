#!/usr/bin/env bash
# Custom Formulation removal — the two writes, and nothing else.
# Authorised by Shawn, 2 Sep 2026. Run from davinci-private-label/.
#
# Change 1: drop the "Custom Formulation" entry from the footer Capabilities column.
# Change 2: delete the Praxera custom-formulation page.
# Both targets are DRAFT. Nothing published is touched.
set -euo pipefail

PAT="${HUBSPOT_PAT:?export HUBSPOT_PAT=pat-na1-... first}"
DIR="$(cd "$(dirname "$0")" && pwd)"
API="https://api.hubapi.com"
MOD="Private%20Label/Modules/Global%20Footer.module/fields.json"
PAGE_ID="216189433487"

echo "== pre-flight: the file we are about to replace =="
curl -sS -H "Authorization: Bearer $PAT" \
  "$API/cms/v3/source-code/published/content/$MOD" \
  | python3 -c 'import sys,json;j=json.load(sys.stdin)
def f(n):
 if isinstance(n,dict):
  if n.get("headline")=="Capabilities":
   print("   BEFORE:",[i.get("linkLabel") for i in n.get("simplemenu_field",[])])
  [f(v) for v in n.values()]
 elif isinstance(n,list): [f(v) for v in n]
f(j)'

echo "== change 1: footer =="
curl -sS -w '   HTTP %{http_code}\n' -X PUT \
  -H "Authorization: Bearer $PAT" \
  -F "file=@$DIR/fields.json.after;filename=fields.json;type=application/json" \
  "$API/cms/v3/source-code/published/content/$MOD" -o /dev/null

echo "== verify footer =="
curl -sS -H "Authorization: Bearer $PAT" \
  "$API/cms/v3/source-code/published/content/$MOD" \
  | python3 -c 'import sys,json;j=json.load(sys.stdin)
def f(n):
 if isinstance(n,dict):
  if n.get("headline")=="Capabilities":
   l=[i.get("linkLabel") for i in n.get("simplemenu_field",[])]
   print("   AFTER :",l)
   assert not any("ustom" in (x or "") and "ormulation" in (x or "") for x in l), "STILL PRESENT"
   print("   OK - Custom Formulation gone")
  [f(v) for v in n.values()]
 elif isinstance(n,list): [f(v) for v in n]
f(j)'

echo "== change 2: delete the page =="
curl -sS -w '   HTTP %{http_code}\n' -X DELETE \
  -H "Authorization: Bearer $PAT" \
  "$API/cms/v3/pages/site-pages/$PAGE_ID" -o /dev/null

echo "== verify page =="
code=$(curl -sS -o /dev/null -w '%{http_code}' \
  -H "Authorization: Bearer $PAT" "$API/cms/v3/pages/site-pages/$PAGE_ID")
echo "   GET page -> HTTP $code   (404 = gone, 200 = still there)"

echo
echo "Done. Nothing else was touched."
