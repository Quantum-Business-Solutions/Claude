"""Rebuild the Praxera test email as real drag-and-drop sections.

The first attempt put the whole newsletter inside one rich-text widget. HubSpot
sanitises rich text, so the nested tables collapsed, and -- more to the point --
a single block is not editable in the drag-and-drop editor, which is the whole
requirement. Marketers need to move the hero, retype the headline and swap the
button without opening HTML.

So each part of the newsletter is its own widget in its own section, and the
green hero band is a SECTION background colour rather than a table, which is how
the DnD editor expects colour to be applied.
"""
import json,os,sys,urllib.request,urllib.error

T=os.environ["TOKEN"]
EMAIL="220684191815"
LOGO="https://info.davincilabs.com/hs-fs/hubfs/Praxera/Praxera%20Logo.png"
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

MAST = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
        f'<tr><td align="left" style="padding:0;">'
        f'<img src="{LOGO}" alt="Praxera" width="140" style="display:block;max-width:140px;height:auto;">'
        f'</td><td align="right" style="padding:0;font-family:Helvetica,Arial,sans-serif;'
        f'font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:#65A11B;'
        f'font-weight:bold;">The Praxera Pulse</td></tr></table>')

HERO = (f'<div style="text-align:center;font-family:Helvetica,Arial,sans-serif;">'
        f'<p style="margin:0 0 16px;font-size:13px;letter-spacing:.12em;'
        f'text-transform:uppercase;color:{PALE};">Your brand. Our standards.</p>'
        f'<img src="{LOGO}" alt="Praxera" width="190" '
        f'style="display:inline-block;max-width:190px;height:auto;background:#ffffff;'
        f'padding:16px 30px;border-radius:4px;">'
        f'<p style="margin:20px 0 0;font-size:15px;line-height:1.55;color:#DDEEC6;">'
        f'Private label supplements for the brands you&rsquo;re building.</p></div>')

BODY = (f'<div style="font-family:Helvetica,Arial,sans-serif;">'
        f'<h1 style="margin:0 0 16px;font-size:22px;line-height:1.25;color:{INK};">'
        f'BUILD YOUR LINE WITH PRAXERA</h1>'
        f'<p style="margin:0 0 14px;font-size:15px;line-height:1.65;color:#3c4038;">Hi there,</p>'
        f'<p style="margin:0 0 14px;font-size:15px;line-height:1.65;color:#3c4038;">'
        f'This is a layout and branding test draft. Every block below is a separate '
        f'drag-and-drop module, so the hero, the headline, the copy and the button can '
        f'each be edited in HubSpot without touching HTML.</p>'
        f'<p style="margin:0 0 14px;font-size:15px;line-height:1.65;color:#3c4038;">'
        f'It is not attached to a list, a workflow or a send.</p>'
        f'<h2 style="margin:26px 0 10px;font-size:17px;line-height:1.3;color:{INK};">'
        f'What Sets Your Brand Apart?</h2>'
        f'<p style="margin:0;font-size:15px;line-height:1.65;color:#3c4038;">'
        f'Placeholder copy. Real messaging will come from the approved Praxera '
        f'positioning, not from this draft.</p></div>')

CTA  = (f'<div style="text-align:left;font-family:Helvetica,Arial,sans-serif;">'
        f'<a href="https://www.praxerasupplements.com/en/pl-demo-book-consultation" '
        f'style="background:{BRIGHT};color:#ffffff;text-decoration:none;padding:14px 30px;'
        f'border-radius:3px;font-size:15px;font-weight:bold;display:inline-block;">'
        f'Book a consultation</a></div>')

FOOT = ('<p style="margin:0;font-family:Helvetica,Arial,sans-serif;font-size:12px;'
        'line-height:1.6;color:#7b8177;">Praxera &middot; Vermont, U.S.A.<br>'
        'Draft placeholder built by Quantum Business Solutions &mdash; do not send.</p>')

def main():
    cur=call("GET",f"/marketing/v3/emails/{EMAIL}")
    if not cur: sys.exit(1)
    c=json.loads(json.dumps(cur["content"]))
    keep_spam=c["widgets"].get("email_can_spam")
    keep_prev=c["widgets"].get("preview_text")

    widgets={}
    if keep_spam: widgets["email_can_spam"]=keep_spam
    if keep_prev:
        keep_prev["value"]="Praxera brand test draft - not for sending"
        widgets["preview_text"]=keep_prev
    widgets["px_masthead"]=richtext(MAST)
    widgets["px_hero"]=richtext(HERO)
    widgets["px_body"]=richtext(BODY)
    widgets["px_cta"]=richtext(CTA)
    widgets["px_footer"]=richtext(FOOT)

    sections=[
      section("section_mast",["px_masthead"],None,"24px","20px"),
      section("section_hero",["px_hero"],GREEN,"38px","38px"),
      section("section_body",["px_body"],None,"30px","8px"),
      section("section_cta", ["px_cta"], None,"14px","26px"),
      section("section_foot",["px_footer"],None,"18px","10px"),
    ]
    if keep_spam:
        sections.append(section("section_spam",["email_can_spam"],None,"6px","20px"))

    c["widgets"]=widgets
    c["flexAreas"]={"main":{"boxFirstElementIndex":0,
                            "boxLastElementIndex":len(sections)-1,
                            "boxed":True,"isSingleColumnFullWidth":False,
                            "sections":sections}}
    c["styleSettings"]["backgroundColor"]="#f4f5f2"
    c["styleSettings"]["bodyColor"]="#ffffff"

    r=call("PATCH",f"/marketing/v3/emails/{EMAIL}",
           {"content":c,"emailTemplateMode":"DRAG_AND_DROP"})
    if r:
        got=r["content"]
        print("state:",r["state"],"| mode:",r.get("emailTemplateMode"))
        print("sections:",[s["id"] for s in got["flexAreas"]["main"]["sections"]])
        print("widgets :",list(got["widgets"]))

if __name__=="__main__": main()
