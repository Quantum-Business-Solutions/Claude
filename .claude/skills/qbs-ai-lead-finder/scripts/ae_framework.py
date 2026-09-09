"""Active Engagement framework - properties only.

Workflows are deliberately NOT created: their enrollment criteria (which call
dispositions count as a conversation) is an open client decision. Everything
here is inert until that is settled and the workflows are built, which is the
point - the schema can land now without asserting anything false.

Native HubSpot properties are used wherever they already carry the fact:
  meetings          -> hs_latest_meeting_activity  (companies AND contacts)
  sales email reply -> hs_sales_email_last_replied (contacts only; companies
                       have no native equivalent, so that one is ours)

  PAT=<token> python3 ae_framework.py         # dry run
  PAT=<token> python3 ae_framework.py --go
"""
import json, os, sys, time, urllib.request, urllib.error

GO = "--go" in sys.argv
H = {"Authorization": "Bearer " + os.environ["PAT"], "Content-Type": "application/json"}

def req(url, body=None, method="POST"):
    for i in range(6):
        try:
            r = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                       headers=H, method=method)
            raw = urllib.request.urlopen(r).read()
            return (json.loads(raw) if raw else {}), None
        except urllib.error.HTTPError as e:
            b = e.read().decode()[:260]
            if e.code in (429, 502, 503, 504): time.sleep(2 * (i + 1)); continue
            return None, "%s %s" % (e.code, b)
        except Exception:
            time.sleep(2 * (i + 1))
    return None, "retries exhausted"

def dt(obj, name, label, group, desc):
    return dict(objectType=obj, name=name, label=label, type="datetime", fieldType="date",
                groupName=group, description=desc)

def calc(obj, name, label, group, desc, formula, typ="date", ft="calculation_equation"):
    return dict(objectType=obj, name=name, label=label, type=typ, fieldType=ft,
                groupName=group, description=desc, calculationFormula=formula)

CO_G, CT_G, CL_G = "company_activity", "contactinformation", "callinformation"

# --- tier 1: raw signal + high-water helpers (must exist before the formulas)
BASE = [
 dt("calls", "conversation_date", "Conversation Date", CL_G,
    "Timestamp of a call that was a real conversation. Set by workflow from the call's own timestamp."),
 dt("calls", "company_recent_conversation_date", "Company - Recent Conversation Date", CL_G,
    "The associated company's current Most Recent Conversation Date, fetched so the workflow can compare "
    "against it. Prevents a late-logged old call from overwriting a newer conversation."),
 dt("calls", "contact_recent_conversation_date", "Contact - Recent Conversation Date", CL_G,
    "The associated contact's current Most Recent Conversation Date, fetched for the same high-water comparison."),

 dt("companies", "most_recent_conversation_date", "Most Recent Conversation Date", CO_G,
    "Most recent call that was a real conversation, rolled up from the call record. "
    "Dials, voicemails and no-answers never reach this field."),
 dt("companies", "most_recent_sales_email_reply_date", "Most Recent Sales Email Reply Date", CO_G,
    "Most recent sales email REPLY from any associated contact. Rolled up by workflow - HubSpot has no "
    "native company-level equivalent. Opens and clicks are not replies and do not count."),

 dt("contacts", "most_recent_conversation_date", "Most Recent Conversation Date", CT_G,
    "Most recent call with this contact that was a real conversation, rolled up from the call record."),
]

# --- tier 2: the roll-ups (reference tier 1 + native HubSpot fields)
CO_FORMULA = "max(most_recent_conversation_date, max(hs_latest_meeting_activity, most_recent_sales_email_reply_date))"
CT_FORMULA = "max(most_recent_conversation_date, max(hs_latest_meeting_activity, hs_sales_email_last_replied))"

ROLLUP = [
 calc("companies", "most_recent_active_engagement_date", "Most Recent Active Engagement Date", CO_G,
      "The latest of: a real conversation, a meeting, or a sales email reply. This is the single "
      "'are we actually engaged' date. A dial, a voicemail or an email open never moves it.", CO_FORMULA),
 calc("contacts", "most_recent_active_engagement_date", "Most Recent Active Engagement Date", CT_G,
      "The latest of: a real conversation, a meeting, or a sales email reply. Same definition as the "
      "company-level property of the same name.", CT_FORMULA),
]

def show(d):
    return "%-10s %-38s %-9s %s" % (d["objectType"], d["name"], d["type"],
                                    ("= " + d["calculationFormula"][:60]) if d.get("calculationFormula") else d["label"])

def exists(obj, name):
    got, _ = req("https://api.hubapi.com/crm/v3/properties/%s/%s" % (obj, name), method="GET")
    return bool(got)

allp = BASE + ROLLUP
print("ACTIVE ENGAGEMENT FRAMEWORK - portal 516382")
print("Properties to create (workflows deliberately excluded):\n")
todo = []
for d in allp:
    if exists(d["objectType"], d["name"]):
        print("   SKIP (exists)  %s" % show(d))
    else:
        todo.append(d); print("   create         %s" % show(d))
print("\n   %d to create, %d already present" % (len(todo), len(allp) - len(todo)))
print("\n   conversation (calls) already exists in this portal - enum Yes/No, 0 of 1.53M populated")

if not GO:
    print("\ndry run - re-run with --go")
    sys.exit(0)

print()
made, failed = [], []
for d in todo:
    obj = d.pop("objectType")
    r, e = req("https://api.hubapi.com/crm/v3/properties/%s" % obj, d)
    d["objectType"] = obj
    if e:
        failed.append((obj, d["name"], e)); print("   FAILED  %-10s %-38s %s" % (obj, d["name"], e))
    else:
        made.append((obj, d["name"])); print("   created %-10s %s" % (obj, d["name"]))
print("\ncreated %d, failed %d" % (len(made), len(failed)))
json.dump({"made": made, "failed": [list(f) for f in failed]}, open("ae_framework_result.json", "w"))
