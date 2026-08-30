"""Second Praxera template: the per-product / category layout.

The Pulse template is a newsletter -- masthead, one hero, a run of copy. The
product emails in this portal work differently: a category label in the masthead,
a picture-led hero with the offer on it, short body, one button. Two different
jobs, so two templates rather than one compromise.

Built with the same rule as the first: every block is its own drag-and-drop
widget, and colour comes from section backgrounds, so a marketer can swap the
category, the image and the button without opening HTML.
"""
import json,os,sys,urllib.request,urllib.error

T=os.environ["TOKEN"]
LOGO="https://info.davincilabs.com/hs-fs/hubfs/Praxera/Praxera%20Logo.png"
HERO_IMG="https://info.davincilabs.com/hubfs/private-label/shutterstock_1565452774.jpg"
INK="#231F20"; GREEN="#2C5F1B"; BRIGHT="#76BC43"; PALE="#C7E5A3"

def call(m,u,body=None):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    d=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(u,data=d,method=m,
        headers={"Authorization":"Bearer "+T,"Content-Type":"application/json"})
    try: return json.load(urllib.request.urlopen(r,timeout=60))
    except urllib.error.HTTPError as e:
        print("HTTP",e.code,e.read().decode()[:600]); return None

def richtext(html):
    return {"type":"module","body":{"module_id":1155639,"html":html,
                                    "hs_enable_module_padding":False}}

def section(sid,widgets,bg=None,pt="0px",pb="0px"):
    st={"backgroundColor":bg,"backgroundImage":None,"backgroundImageType":None,
        "backgroundType":"CONTENT","paddingBottom":pb,"paddingTop":pt,
        "stack":"LEFT_TO_RIGHT",
        "breakpointStyles":{"default":{"backgroundColor":bg,"backgroundImage":None,
            "backgroundImageType":None,"backgroundType":"CONTENT","hidden":None,
            "paddingBottom":pb,"paddingTop":pt,"verticalAlign":None}}}
    return {"id":sid,"path":None,"style":st,
            "columns":[{"id":sid+"_c0","widgets":widgets,"width":12}]}

MAST=(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
      f'<tr><td align="left" style="padding:0;">'
      f'<img src="{LOGO}" alt="Praxera" width="132" style="display:block;max-width:132px;height:auto;">'
      f'</td><td align="right" style="padding:0;font-family:Helvetica,Arial,sans-serif;'
      f'font-size:12px;letter-spacing:.1em;color:#6E7369;">Immune Support</td></tr></table>')

# picture-led hero: image on top, offer panel beneath, the shape the product emails use
HERO=(f'<img src="{HERO_IMG}" alt="" width="540" '
      f'style="display:block;width:100%;max-width:540px;height:auto;border-radius:4px 4px 0 0;">'
      f'<div style="background:{GREEN};padding:26px 28px;border-radius:0 0 4px 4px;'
      f'text-align:center;font-family:Helvetica,Arial,sans-serif;">'
      f'<p style="margin:0 0 8px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;'
      f'color:{PALE};">Add to your line</p>'
      f'<p style="margin:0 0 4px;font-size:25px;line-height:1.15;color:#ffffff;font-weight:bold;">'
      f'Immune Support</p>'
      f'<p style="margin:8px 0 0;font-size:14px;line-height:1.5;color:#DDEEC6;">'
      f'Capsules, powders and liquids &mdash; ready for your label.</p></div>')

BODY=(f'<div style="font-family:Helvetica,Arial,sans-serif;">'
      f'<p style="margin:0 0 14px;font-size:15px;line-height:1.65;color:#3c4038;">Hi there,</p>'
      f'<p style="margin:0 0 14px;font-size:15px;line-height:1.65;color:#3c4038;">'
      f'Placeholder copy for the per-product template. This is where the category pitch goes '
      f'&mdash; what the format is, who it is for, and why it belongs in the customer&rsquo;s line.</p>'
      f'<p style="margin:0 0 6px;font-size:15px;line-height:1.65;color:#3c4038;">'
      f'<strong>Minimums, formats and lead times</strong> sit here as a short list, so the '
      f'reader can qualify themselves before they click.</p></div>')

CTA=(f'<div style="text-align:center;font-family:Helvetica,Arial,sans-serif;">'
     f'<a href="https://www.praxerasupplements.com/en/pl-demo-book-consultation" '
     f'style="background:{BRIGHT};color:#ffffff;text-decoration:none;padding:15px 36px;'
     f'border-radius:3px;font-size:15px;font-weight:bold;display:inline-block;">'
     f'Request a quote</a></div>')

FOOT=('<p style="margin:0;font-family:Helvetica,Arial,sans-serif;font-size:12px;'
      'line-height:1.6;color:#7b8177;text-align:center;">Praxera &middot; Vermont, U.S.A.<br>'
      'Draft placeholder built by Quantum Business Solutions &mdash; do not send.</p>')

def main():
    created=call("POST","/marketing/v3/emails",{
      "name":"Praxera - TEMPLATE - Product / Category (QBS, do not send)",
      "subject":"Praxera product template - draft only, do not send",
      "state":"DRAFT","type":"BATCH_EMAIL",
      "from":{"fromName":"Praxera","replyTo":"enews@davincilabs.com"},
      "subscriptionDetails":{"officeLocationId":"5451098384"},
      "businessUnitId":"0"})
    if not created: sys.exit(1)
    eid=created["id"]; print("created",eid)

    src=call("GET","/marketing/v3/emails/208438457715")
    c=json.loads(json.dumps(src["content"]))
    spam=c["widgets"].get("email_can_spam")
    prev=c["widgets"].get("preview_text")
    if prev: prev["value"]="Praxera product template - not for sending"

    widgets={}
    if spam: widgets["email_can_spam"]=spam
    if prev: widgets["preview_text"]=prev
    widgets["px_masthead"]=richtext(MAST)
    widgets["px_hero"]=richtext(HERO)
    widgets["px_body"]=richtext(BODY)
    widgets["px_cta"]=richtext(CTA)
    widgets["px_footer"]=richtext(FOOT)

    sections=[section("section_mast",["px_masthead"],None,"24px","18px"),
              section("section_hero",["px_hero"],None,"0px","26px"),
              section("section_body",["px_body"],None,"6px","10px"),
              section("section_cta",["px_cta"],None,"10px","26px"),
              section("section_foot",["px_footer"],None,"16px","10px")]
    if spam: sections.append(section("section_spam",["email_can_spam"],None,"6px","20px"))

    c["widgets"]=widgets
    c["flexAreas"]={"main":{"boxFirstElementIndex":0,"boxLastElementIndex":len(sections)-1,
                            "boxed":True,"isSingleColumnFullWidth":False,"sections":sections}}
    c["styleSettings"]["backgroundColor"]="#f4f5f2"
    c["styleSettings"]["bodyColor"]="#ffffff"
    r=call("PATCH",f"/marketing/v3/emails/{eid}",
           {"content":c,"emailTemplateMode":"DRAG_AND_DROP"})
    if r:
        back=call("GET",f"/marketing/v3/emails/{eid}")
        print("state:",back["state"],"| sections:",
              [s["id"] for s in back["content"]["flexAreas"]["main"]["sections"]])
        json.dump({"newsletter":"220684191815","product":eid},
                  open("reference/praxera_email_templates.json","w"),indent=1)

if __name__=="__main__": main()
