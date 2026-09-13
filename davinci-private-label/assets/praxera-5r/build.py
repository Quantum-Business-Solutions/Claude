import base64, math
def b64(p): return 'data:image/png;base64,'+base64.b64encode(open(p,'rb').read()).decode()
GREEN='#6CA843'; DARK='#092637'
IMG={'caps':b64('src_0.png'),'leaf':b64('src_2.png'),'micro':b64('src_3.png'),
     'prod':b64('product.png'),'logo':b64('praxera_logo.png')}

STEPS=[("01","REMOVE","Promote a healthy microbiome and normal inflammatory response by “weeding out” gut offenders, such as overgrown bacteria, yeast, or parasites. Many clinicians also remove inflammatory foods, such as gluten, dairy, and processed sugar products.",["VIRA-SHIELD","CANDID-AWAY™","GRAPEFRUIT SEED EXTRACT","OLIVIR™ 15"]),
("02","REPLACE","Give the digestive system what it needs to properly break down foods, foreign organisms, and allergens. Provide digestive factors such as enzymes, betaine hydrochloride, and bile acids.",["DIGESTIVE ENZYMES","DIGESTIVE ENZYMES PRO","ENZYME BENEFITS™"]),
("03","REINOCULATE","Support the gut microbiome with prebiotics, probiotics, and fiber. Proper microbial balance means fewer digestive symptoms and a strong immune system.",["MEGA PROBIOTIC™ ND 50","DAILY BEST™ PROBIOTIC","DIGESTIVE ENZYMES CHEWABLE WITH PREBIOTICS &amp; PROBIOTICS","PREBIOTIC FIBER","ARABINOGALACTAN POWDER"]),
("04","REPAIR","A cornerstone for improved gut health includes strengthening intestinal barrier integrity and restoring its function. This step is critical for addressing gastrointestinal concerns while supporting digestion, bowel regularity, a calm immune response, and a healthy microbial environment.",["G.I. BENEFITS®","L-GLUTAMINE POWDER","IMMUNO BENEFITS™"]),
("05","REBALANCE","Engineer a healthy lifestyle to promote proper gut function for once and for all. Improve lifestyle factors such as sleep, exercise, and nutrition habits, which can all affect the gut. Persistent stress can cause damage to the gut lining, making stress management a key requirement for long-term gut health.",["CLEAR G.I."])]

# ---- ring: rounded "petal" wedges, matching the original composition ----
VB=620; CX=CY=310
RO=292; RI=138          # outer / inner radius of the annulus band
CR=34                   # corner radius of each petal
GAP=4.2                 # degrees of white gap between petals
G_DARK='#76BD43'; G_LIGHT='#A3D06F'

def petal(a_mid, span=72.0-GAP):
    """annular sector inset by CR, later stroked with width 2*CR and round joins"""
    ro=RO-CR; ri=RI+CR
    do=math.degrees(CR/ro); di=math.degrees(CR/ri)
    a0o=math.radians(a_mid-span/2+do); a1o=math.radians(a_mid+span/2-do)
    a0i=math.radians(a_mid-span/2+di); a1i=math.radians(a_mid+span/2-di)
    P=lambda r,a:(CX+r*math.cos(a), CY-r*math.sin(a))
    x0,y0=P(ro,a0o); x1,y1=P(ro,a1o); x2,y2=P(ri,a1i); x3,y3=P(ri,a0i)
    return (f"M{x0:.2f},{y0:.2f} A{ro:.1f},{ro:.1f} 0 0 0 {x1:.2f},{y1:.2f} "
            f"L{x2:.2f},{y2:.2f} A{ri:.1f},{ri:.1f} 0 0 1 {x3:.2f},{y3:.2f} Z")

def lbl(a_mid, r=None):
    if r is None: r=RI+(RO-RI)*0.72
    a=math.radians(a_mid); return (CX+r*math.cos(a), CY-r*math.sin(a))

# counter-clockwise: 01 top-left, 02 left, 03 bottom, 04 right, 05 top-right
SEG=[("01",104,G_DARK,None),("02",176,None,'caps'),("03",248,None,'micro'),
     ("04",320,G_LIGHT,None),("05",32,None,'leaf')]
paths=[]
for num,ang,col,img in SEG:
    fill = col if col else f"url(#pat_{img})"
    d=petal(ang)
    paths.append(f'<path d="{d}" fill="{fill}" stroke="{fill}" stroke-width="{2*CR}" '
                 f'stroke-linejoin="round" stroke-linecap="round"/>')

# centre product disc - large, overlapping the band, nudged left of ring centre
PX,PY,PR = CX-30, CY+6, 176
paths.append(f'<circle cx="{PX}" cy="{PY}" r="{PR+9}" fill="#fff"/>')
paths.append(f'<clipPath id="pc"><circle cx="{PX}" cy="{PY}" r="{PR}"/></clipPath>')
paths.append(f'<image href="{IMG["prod"]}" x="{PX-PR}" y="{PY-PR}" width="{2*PR}" height="{2*PR}" '
             f'preserveAspectRatio="xMidYMid slice" clip-path="url(#pc)"/>')

# numbers last so they sit above everything
for num,ang,col,img in SEG:
    lx,ly=lbl(ang)
    paths.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="central" '
                 f'font-family="Arial Black, Arial, sans-serif" font-size="54" font-weight="900" fill="#fff">{num}</text>')

defs="".join(
 f'<pattern id="pat_{k}" patternUnits="userSpaceOnUse" width="{VB}" height="{VB}">'
 f'<image href="{IMG[k]}" x="0" y="0" width="{VB}" height="{VB}" preserveAspectRatio="xMidYMid slice"/></pattern>'
 for k in ('caps','leaf','micro'))

cols=""
for num,title,body,items in STEPS:
    lis="".join(f'<li>{i}</li>' for i in items)
    cols+=(f'<div class="col"><div class="ch"><span class="cn">{num}</span>'
           f'<span class="ct">{title}</span></div><p>{body}</p><ul>{lis}</ul></div>')

html=f"""<meta charset="utf-8">
<style>
@page {{ size: 11in 8.5in; margin: 0; }}
*{{box-sizing:border-box}} html,body{{margin:0;padding:0}}
body{{width:1056px;height:816px;position:relative;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;color:{DARK};background:#fff;overflow:hidden}}
.left{{position:absolute;left:52px;top:62px;width:392px}}
.logo{{width:205px;display:block;margin:0 0 12px -4px}}
.rule{{width:280px;height:1px;background:#cdd5d9;margin:0 0 24px 0}}
h1{{font-family:'Arial Black','Helvetica Neue',Arial,sans-serif;font-weight:900;font-size:52px;line-height:.97;letter-spacing:-1.2px;margin:0 0 20px 0;text-transform:uppercase}}
h1 .g{{color:{GREEN}}}
.intro{{font-size:15.5px;line-height:1.52;color:#33434c;margin:0;width:372px}}
.ring{{position:absolute;right:18px;top:14px;width:492px;height:492px}}
.cols{{position:absolute;left:52px;right:44px;top:540px;display:flex}}
.col{{flex:1;padding:0 13px;border-right:1px dotted #bcc6cc}}
.col:first-child{{padding-left:0}} .col:last-child{{border-right:none;padding-right:0}}
.ch{{display:flex;align-items:baseline;gap:6px;margin-bottom:5px}}
.cn{{font-family:'Arial Black',Arial,sans-serif;font-weight:900;font-size:23px;color:{GREEN};line-height:1}}
.ct{{font-weight:800;font-size:14.5px;letter-spacing:.3px}}
.col p{{font-size:10.4px;line-height:1.34;margin:0 0 6px 0;color:#37474f}}
.col ul{{list-style:none;margin:0;padding:0}}
.col li{{font-size:9.6px;font-weight:700;line-height:1.28;margin-bottom:1.5px;padding-left:10px;position:relative;letter-spacing:.15px}}
.col li:before{{content:"\\00BB";position:absolute;left:0;color:{GREEN}}}
.foot{{position:absolute;left:52px;right:44px;bottom:24px;display:flex;height:28px}}
.fda{{flex:1;border:1px solid #9fabb2;display:flex;align-items:center;justify-content:center;font-size:9px;color:#3d4d56;padding:0 10px;text-align:center}}
.visit{{background:{DARK};color:#fff;display:flex;align-items:center;padding:0 20px;font-size:11px;letter-spacing:2.2px;font-weight:700;white-space:nowrap}}
.visit i{{font-style:italic;letter-spacing:0;font-weight:400;margin-right:9px;text-transform:none;font-size:11.5px}}
</style>
<div class="left">
  <img class="logo" src="{IMG['logo']}" alt="Praxera">
  <div class="rule"></div>
  <h1>The <span class="g">5R Gut<br>Health</span><br>Protocol</h1>
  <p class="intro">The 5R Framework offers a simple, step-by-step method for addressing even the most challenging gastrointestinal cases. Use this guide to match Praxera&rsquo;s digestive health products with each phase of gut support.</p>
</div>
<svg class="ring" viewBox="0 0 {VB} {VB}"><defs>{defs}</defs>{''.join(paths)}</svg>
<div class="cols">{cols}</div>
<div class="foot">
  <div class="fda">This statement has not been evaluated by the Food and Drug Administration. This product is not intended to diagnose, treat, cure, or prevent any disease.</div>
  <div class="visit"><i>to learn more visit</i> PRAXERASUPPLEMENTS.COM</div>
</div>"""
open('praxera_5r.html','w',encoding='utf-8').write(html)
print('built')
