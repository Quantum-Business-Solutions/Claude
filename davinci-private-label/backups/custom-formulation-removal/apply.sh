#!/usr/bin/env bash
# Custom Formulation removal — the ONE remaining write.
#
# Change 2 (delete the Praxera custom-formulation page) was done by Shawn on
# 2 Sep 2026, along with alp/ads-custom. Verified gone, and nothing links to
# either from any page, blog post or form. Only the footer entry is left.
#
# Change 1: drop "Custom Formulation" from the footer Capabilities column.
# Blast radius: 60 Praxera pages + 75 Praxera blog posts + 10 DaVinci drafts.
# All DRAFT. Nothing published on any brand renders this module.
set -euo pipefail

PAT="${HUBSPOT_PAT:?export HUBSPOT_PAT=pat-na1-... first}"
DIR="$(cd "$(dirname "$0")" && pwd)"
API="https://api.hubapi.com"
MOD="Private%20Label/Modules/Global%20Footer.module/fields.json"

show() { python3 -c 'import sys,json
j=json.load(sys.stdin)
def f(n):
 if isinstance(n,dict):
  if n.get("headline")=="Capabilities":
   print("   ","'"$1"'",[i.get("linkLabel") for i in n.get("simplemenu_field",[])])
  [f(v) for v in n.values()]
 elif isinstance(n,list): [f(v) for v in n]
f(j)'; }

echo "== before =="
curl -sS -H "Authorization: Bearer $PAT" \
  "$API/cms/v3/source-code/published/content/$MOD" | show "BEFORE:"

echo "== writing =="
curl -sS -w '   HTTP %{http_code}\n' -X PUT \
  -H "Authorization: Bearer $PAT" \
  -F "file=@$DIR/fields.json.after;filename=fields.json;type=application/json" \
  "$API/cms/v3/source-code/published/content/$MOD" -o /dev/null

echo "== after =="
curl -sS -H "Authorization: Bearer $PAT" \
  "$API/cms/v3/source-code/published/content/$MOD" \
  | tee /tmp/_ff.json | show "AFTER :"
python3 - <<'PY'
import json,re
j=json.load(open("/tmp/_ff.json"))
s=json.dumps(j)
assert not re.search(r"custom[\s\-_]{0,3}formulation",s,re.I), "STILL PRESENT - write did not take"
print("   OK - Custom Formulation gone from the module")
PY
echo
echo "Done. The footer entry only. Nothing else touched."
