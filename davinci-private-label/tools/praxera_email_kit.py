"""Both Praxera email templates, built from one set of design tokens.

The first attempt was default Helvetica on a flat green slab, and it looked it.
Email restricts the toolkit hard -- no webfonts you can rely on, no flexbox, no
grid -- so the character has to come from the few things that do survive: a
serif/sans pairing, letterspaced eyebrows, hairline rules, and asymmetry instead
of centring everything.

Georgia carries the headlines because it ships everywhere and gives the brand
some weight; Helvetica carries the body. Colour is applied to SECTION backgrounds
rather than nested tables, and the hero photograph is a real HubSpot image module
rather than an <img> inside rich text, so both stay editable in drag-and-drop.
"""
import json,os,sys,urllib.request,urllib.error

T=os.environ["TOKEN"]
LOGO="https://info.davincilabs.com/hs-fs/hubfs/Praxera/Praxera%20Logo.png"
LOGO_W="https://info.davincilabs.com/hs-fs/hubfs/Praxera/Praxera%20Logo%20White.png"
HERO_IMG="https://www.pettechlabs.com/hubfs/Praxera/email/praxera-product-lineup-hero.png"

INK="#231F20"; BODY="#44483F"; MUTE="#7B8177"
DEEP="#24501A"; BRIGHT="#76BC43"; PALE="#BFDF97"; RULE="#E4E7E0"
SERIF="Georgia,'Times New Roman',serif"
SANS="Helvetica,Arial,sans-serif"

def call(m,u,body=None):
    if u.startswith("/"): u="https://api.hubapi.com"+u
    d=json.dumps(body).encode() if body is not None else None
    r=urllib.request.Request(u,data=d,method=m,
        headers={"Authorization":"Bearer "+T,"Content-Type":"application/json"})
    try: return json.load(urllib.request.urlopen(r,timeout=60))
    except urllib.error.HTTPError as e:
        print("HTTP",e.code,e.read().decode()[:600]); return None


PAD_X="32px"
def pad(inner,px=PAD_X,pt="0px",pb="0px"):
    """Own the padding. hs_enable_module_padding is false on every widget, so a
    block that relies on HubSpot for gutters renders flush to the 600px edge."""
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="border-collapse:collapse;"><tr><td style="padding:{pt} {px} {pb};">'
            f'{inner}</td></tr></table>')

def rich(html):
    return {"type":"module","body":{"module_id":1155639,"html":html,
                                    "hs_enable_module_padding":False}}
def image(src,alt,w,link=None):
    """A real image module -- survives the editor and stays swappable."""
    return {"type":"module","body":{"module_id":1367093,"alignment":{"horizontal_align":"CENTER"},
            "img":{"src":src,"alt":alt,"width":w},"link":link or "",
            "hs_enable_module_padding":False}}

def sect(sid,widgets,bg=None,pt="0px",pb="0px"):
    st={"backgroundColor":bg,"backgroundImage":None,"backgroundImageType":None,
        "backgroundType":"CONTENT","paddingBottom":pb,"paddingTop":pt,"stack":"LEFT_TO_RIGHT",
        "breakpointStyles":{"default":{"backgroundColor":bg,"backgroundImage":None,
          "backgroundImageType":None,"backgroundType":"CONTENT","hidden":None,
          "paddingBottom":pb,"paddingTop":pt,"verticalAlign":None}}}
    return {"id":sid,"path":None,"style":st,
            "columns":[{"id":sid+"_c0","widgets":widgets,"width":12}]}

def eyebrow(text,color):
    return (f'<p style="margin:0 0 12px;font-family:{SANS};font-size:11px;'
            f'letter-spacing:.2em;text-transform:uppercase;color:{color};">{text}</p>')

def masthead(label):
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr><td align="left" style="padding:0 0 16px;">'
            f'<img src="{LOGO}" alt="Praxera" width="128" style="display:block;max-width:128px;height:auto;">'
            f'</td><td align="right" style="padding:0 0 16px;font-family:{SANS};font-size:10px;'
            f'letter-spacing:.22em;text-transform:uppercase;color:{MUTE};">{label}</td></tr>'
            f'<tr><td colspan="2" style="border-top:2px solid {INK};font-size:0;line-height:0;">&nbsp;</td></tr>'
            f'</table>')

def button(text,href,align="left"):
    return (f'<div style="text-align:{align};font-family:{SANS};">'
            f'<a href="{href}" style="background:{BRIGHT};color:#ffffff;text-decoration:none;'
            f'padding:15px 34px;font-size:14px;font-weight:bold;letter-spacing:.04em;'
            f'display:inline-block;border-radius:2px;">{text}</a></div>')

def footer():
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
            f'<tr><td style="border-top:1px solid {RULE};padding-top:18px;font-family:{SANS};'
            f'font-size:11px;line-height:1.7;color:{MUTE};">'
            f'<strong style="color:{BODY};letter-spacing:.08em;">PRAXERA</strong><br>'
            f'Vermont, U.S.A.<br>'
            f'<span style="color:#9AA093;">Draft placeholder built by Quantum Business Solutions '
            f'&mdash; do not send.</span></td></tr></table>')


def article(title,blurb,href,kicker):
    """One newsletter item. A Pulse implies several -- one block under a masthead
    that says 'issue' is a cheque the body does not cash."""
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'style="border-collapse:collapse;border-top:1px solid {RULE};">'
            f'<tr><td style="padding:18px 0 0;">'
            f'<p style="margin:0 0 7px;font-family:{SANS};font-size:10px;letter-spacing:.2em;'
            f'text-transform:uppercase;color:{BRIGHT};">{kicker}</p>'
            f'<a href="{href}" style="text-decoration:none;">'
            f'<h3 style="margin:0 0 8px;font-family:{SERIF};font-size:19px;line-height:1.3;'
            f'color:{INK};font-weight:normal;">{title}</h3></a>'
            f'<p style="margin:0 0 10px;font-family:{SANS};font-size:14px;line-height:1.65;'
            f'color:{BODY};">{blurb}</p>'
            f'<a href="{href}" style="font-family:{SANS};font-size:13px;font-weight:bold;'
            f'color:{DEEP};text-decoration:none;letter-spacing:.03em;">Read it &rarr;</a>'
            f'</td></tr></table>')

# ---------------------------------------------------------------- newsletter
def newsletter_widgets():
    hero=(eyebrow("Issue 01 &nbsp;&middot;&nbsp; Your brand. Our standards.",PALE) +
          f'<h1 style="margin:0 0 14px;font-family:{SERIF};font-size:31px;line-height:1.16;'
          f'color:#ffffff;font-weight:normal;max-width:430px;">Introducing Praxera</h1>'
          f'<p style="margin:0;font-family:{SANS};font-size:15px;line-height:1.65;'
          f'color:{PALE};max-width:430px;">Private label supplements for the brands '
          f'you&rsquo;re building &mdash; formulated in Vermont, made to your label, '
          f'backed by fifty years of manufacturing standards.</p>')

    lead=(eyebrow("The short version",BRIGHT) +
          f'<h2 style="margin:0 0 18px;font-family:{SERIF};font-size:26px;line-height:1.22;'
          f'color:{INK};font-weight:normal;">A new name for a programme you already know</h2>'
          f'<p style="margin:0 0 15px;font-family:{SANS};font-size:15px;line-height:1.75;'
          f'color:{BODY};">Same formulations. Same facility. Same team on the phone. '
          f'What changes is the name on the programme and the standard of the experience '
          f'around it &mdash; a clearer catalogue, faster quoting, and a design service that '
          f'takes your label from sketch to shelf.</p>'
          f'<p style="margin:0;font-family:{SANS};font-size:15px;line-height:1.75;color:{BODY};">'
          f'Below: three questions we are asked in almost every first call.</p>')

    items=(article("How much does it cost to start a private label supplement line?",
             "The honest ranges for minimums, tooling, label design and first production run "
             "&mdash; and where new brands usually underestimate.",
             "https://www.praxerasupplements.com/blog/how-much-to-start-a-private-label-supplement-business",
             "Costs") +
           article("USP, NSF, GMP and FDA: which certifications actually matter",
             "A buyer&rsquo;s guide to what each mark covers, what it does not, and which ones "
             "your retail partners will ask about.",
             "https://www.praxerasupplements.com/blog/supplement-certifications-usp-nsf-gmp-fda",
             "Compliance") +
           article("Contract manufacturing or private label &mdash; which do you need?",
             "They are not the same service and the wrong choice costs months. A short guide "
             "to telling them apart before you request a quote.",
             "https://www.praxerasupplements.com/blog/contract-manufacturing-vs-private-labeling-supplements",
             "Getting started"))

    return {"px_masthead":rich(pad(masthead("The Praxera Pulse &nbsp;&middot;&nbsp; Issue 01"))),
            "px_hero":rich(pad(hero)),
            "px_heroimg":image(HERO_IMG,"Praxera private label supplement range",600),
            "px_body":rich(pad(lead)),
            "px_items":rich(pad(items)),
            "px_cta":rich(pad(button("Book a consultation",
                     "https://www.praxerasupplements.com/en/pl-demo-book-consultation"))),
            "px_footer":rich(pad(footer()))}

def newsletter_sections(extra):
    s=[sect("section_mast",["px_masthead"],None,"28px","20px"),
       sect("section_hero",["px_hero"],DEEP,"40px","36px"),
       sect("section_img",["px_heroimg"],DEEP,"0px","0px"),
       sect("section_body",["px_body"],None,"34px","6px"),
       sect("section_items",["px_items"],None,"10px","10px"),
       sect("section_cta", ["px_cta"], None,"22px","34px"),
       sect("section_foot",["px_footer"],None,"6px","14px")]
    if extra: s.append(sect("section_spam",["email_can_spam"],None,"4px","22px"))
    return s

# ------------------------------------------------------------------ product
def product_widgets():
    band=(eyebrow("Add to your line",PALE) +
          f'<h1 style="margin:0 0 10px;font-family:{SERIF};font-size:32px;line-height:1.14;'
          f'color:#ffffff;font-weight:normal;">Immune Support</h1>'
          f'<p style="margin:0;font-family:{SANS};font-size:14px;line-height:1.6;color:{PALE};">'
          f'Capsules, powders and liquids &mdash; ready for your label.</p>')
    # a real spec table is what a private-label buyer actually needs to see
    spec=("".join(
        f'<tr><td style="padding:11px 0;border-bottom:1px solid {RULE};font-family:{SANS};'
        f'font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:{MUTE};'
        f'width:38%;">{k}</td>'
        f'<td style="padding:11px 0;border-bottom:1px solid {RULE};font-family:{SANS};'
        f'font-size:14px;color:{BODY};">{v}</td></tr>'
        for k,v in (("Formats","Capsule, powder, liquid"),
                    ("Minimum order","Placeholder"),
                    ("Lead time","Placeholder"),
                    ("Label &amp; artwork","In-house design available"))))
    body=(f'<p style="margin:0 0 18px;font-family:{SANS};font-size:15px;line-height:1.7;'
          f'color:{BODY};">Placeholder for the category pitch &mdash; what the format is, '
          f'who it is for, and why it belongs in your customer&rsquo;s line.</p>'
          f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
          f'style="border-top:1px solid {RULE};">{spec}</table>')
    return {"px_masthead":rich(pad(masthead("Immune Support"))),
            "px_heroimg":image(HERO_IMG,"",600),
            "px_band":rich(pad(band)),
            "px_body":rich(pad(body)),
            "px_cta":rich(pad(button("Request a quote",
                     "https://www.praxerasupplements.com/en/pl-demo-book-consultation"))),
            "px_footer":rich(pad(footer()))}

def product_sections(extra):
    s=[sect("section_mast",["px_masthead"],None,"28px","20px"),
       sect("section_img",["px_heroimg"],None,"0px","0px"),
       sect("section_band",["px_band"],DEEP,"32px","34px"),
       sect("section_body",["px_body"],None,"32px","10px"),
       sect("section_cta",["px_cta"],None,"22px","34px"),
       sect("section_foot",["px_footer"],None,"6px","14px")]
    if extra: s.append(sect("section_spam",["email_can_spam"],None,"4px","22px"))
    return s

def apply(eid,widgets,sections_fn):
    src=call("GET","/marketing/v3/emails/208438457715")
    c=json.loads(json.dumps(src["content"]))
    spam=c["widgets"].get("email_can_spam")
    prev=c["widgets"].get("preview_text")
    w=dict(widgets)
    if spam: w["email_can_spam"]=spam
    if prev:
        prev["value"]="Praxera template - draft, not for sending"
        w["preview_text"]=prev
    secs=sections_fn(bool(spam))
    c["widgets"]=w
    c["flexAreas"]={"main":{"boxFirstElementIndex":0,"boxLastElementIndex":len(secs)-1,
                            "boxed":True,"isSingleColumnFullWidth":False,"sections":secs}}
    c["styleSettings"]["backgroundColor"]="#F4F5F2"
    c["styleSettings"]["bodyColor"]="#FFFFFF"
    r=call("PATCH",f"/marketing/v3/emails/{eid}",
           {"content":c,"emailTemplateMode":"DRAG_AND_DROP"})
    back=call("GET",f"/marketing/v3/emails/{eid}")
    print(f"  {eid} {back['state']:8} sections="
          f"{len(back['content']['flexAreas']['main']['sections'])}")

if __name__=="__main__":
    ids=json.load(open("reference/praxera_email_templates.json"))
    print("newsletter:"); apply(ids["newsletter"],newsletter_widgets(),newsletter_sections)
    print("product:");    apply(ids["product"],   product_widgets(),   product_sections)
