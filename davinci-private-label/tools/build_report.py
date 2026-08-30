"""Emit the merged-audit page. Rows are generated because there are 300+ of them."""
import json,html,collections,sys
S="/tmp/claude-0/-home-user-Claude/0f427e52-eb7f-5b23-8772-a7e122ea7371/scratchpad"
D=json.load(open(S+"/data.json"))
e=lambda s: html.escape(str(s))

CSS = """
:root{
  --paper:#F6F7F4; --surface:#FFFFFF; --sunk:#EEF0EA;
  --ink:#191B17; --body:#3A3F36; --muted:#6E7369; --rule:#DDE0D8;
  --accent:#65A11B; --accent-soft:#EAF2DC;
  --ok:#3D5A80; --ok-soft:#E4EAF2;
  --warn:#8A6300; --warn-soft:#F6EDD8;
  --bad:#9B3B31; --bad-soft:#F5E3E0;
  --shadow:0 1px 2px rgba(25,27,23,.05), 0 8px 24px -16px rgba(25,27,23,.28);
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --paper:#141613; --surface:#1C1F1B; --sunk:#22261F;
  --ink:#E9EBE4; --body:#C3C8BB; --muted:#8B9184; --rule:#2F342B;
  --accent:#8CC63F; --accent-soft:#25301A;
  --ok:#8FB4DC; --ok-soft:#1B2632;
  --warn:#D9A93F; --warn-soft:#2E2716;
  --bad:#DE8378; --bad-soft:#331F1C;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -16px rgba(0,0,0,.8);
}}
:root[data-theme="dark"]{
  --paper:#141613; --surface:#1C1F1B; --sunk:#22261F;
  --ink:#E9EBE4; --body:#C3C8BB; --muted:#8B9184; --rule:#2F342B;
  --accent:#8CC63F; --accent-soft:#25301A;
  --ok:#8FB4DC; --ok-soft:#1B2632;
  --warn:#D9A93F; --warn-soft:#2E2716;
  --bad:#DE8378; --bad-soft:#331F1C;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -16px rgba(0,0,0,.8);
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--body);
  font-family:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:16px;line-height:1.6;margin:0;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding:0 28px 96px}
.measure{max-width:68ch}
h1,h2,h3{font-family:Newsreader,Georgia,"Times New Roman",serif;color:var(--ink);
  text-wrap:balance;font-weight:500;margin:0}
h1{font-size:clamp(2.1rem,5vw,3.1rem);line-height:1.08;letter-spacing:-.015em}
h2{font-size:clamp(1.45rem,3vw,1.9rem);line-height:1.18;margin:0 0 .3rem}
h3{font-size:1.08rem;line-height:1.3;font-weight:600}
p{margin:0 0 1rem}
a{color:var(--accent);text-underline-offset:3px}
code,.mono{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace}
.eyebrow{font-family:"IBM Plex Mono",monospace;font-size:.68rem;letter-spacing:.16em;
  text-transform:uppercase;color:var(--muted);margin:0 0 .55rem}

/* ---- masthead ---- */
header.top{border-bottom:1px solid var(--rule);background:var(--surface);margin-bottom:44px}
header.top .wrap{padding-top:40px;padding-bottom:34px}
.brandline{display:flex;align-items:center;gap:10px;margin-bottom:22px}
.brandline .dot{width:9px;height:9px;border-radius:50%;background:var(--accent);flex:none}
.brandline span{font-family:"IBM Plex Mono",monospace;font-size:.7rem;letter-spacing:.15em;
  text-transform:uppercase;color:var(--muted)}
.sub{font-size:1.05rem;color:var(--body);margin-top:16px;max-width:62ch}

/* ---- metric strip ---- */
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:1px;background:var(--rule);border:1px solid var(--rule);border-radius:3px;
  overflow:hidden;margin:30px 0 0}
.metric{background:var(--surface);padding:16px 18px}
.metric b{display:block;font-family:Newsreader,serif;font-size:2rem;line-height:1;
  color:var(--ink);font-variant-numeric:tabular-nums;font-weight:500}
.metric small{display:block;margin-top:7px;font-size:.72rem;letter-spacing:.05em;
  color:var(--muted);text-transform:uppercase;font-family:"IBM Plex Mono",monospace}

/* ---- sections ---- */
section{margin-top:66px;scroll-margin-top:20px}
.shead{border-top:2px solid var(--ink);padding-top:14px;margin-bottom:22px}

/* ---- callout ---- */
.call{background:var(--surface);border:1px solid var(--rule);
  border-left:3px solid var(--accent);border-radius:0 3px 3px 0;
  padding:20px 22px;margin:24px 0;box-shadow:var(--shadow)}
.call.bad{border-left-color:var(--bad)}
.call.warn{border-left-color:var(--warn)}
.call h3{margin-bottom:.4rem}
.call p:last-child{margin-bottom:0}

/* ---- evidence chip ---- */
.chip{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:.63rem;
  letter-spacing:.09em;text-transform:uppercase;padding:2px 7px;border-radius:2px;
  white-space:nowrap;font-weight:500}
.c-ok{background:var(--ok-soft);color:var(--ok)}
.c-warn{background:var(--warn-soft);color:var(--warn)}
.c-bad{background:var(--bad-soft);color:var(--bad)}
.c-acc{background:var(--accent-soft);color:var(--accent)}
.c-mute{background:var(--sunk);color:var(--muted)}

/* ---- tables ---- */
.tscroll{overflow-x:auto;border:1px solid var(--rule);border-radius:3px;
  background:var(--surface);box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;font-size:.855rem}
th{font-family:"IBM Plex Mono",monospace;font-size:.65rem;letter-spacing:.11em;
  text-transform:uppercase;color:var(--muted);text-align:left;font-weight:500;
  padding:11px 14px;border-bottom:1px solid var(--rule);background:var(--sunk);
  position:sticky;top:0;white-space:nowrap}
td{padding:10px 14px;border-bottom:1px solid var(--rule);vertical-align:top}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--sunk)}
td.num{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}
td.ev{font-family:"IBM Plex Mono",monospace;font-size:.74rem;color:var(--muted);
  line-height:1.45;word-break:break-word;min-width:240px}
td.nm{color:var(--ink);font-weight:500;min-width:210px}
.u{font-family:"IBM Plex Mono",monospace;font-size:.73rem;word-break:break-all;color:var(--muted)}

/* ---- filters ---- */
.filters{display:flex;flex-wrap:wrap;gap:7px;margin:0 0 14px;align-items:center}
.filters .lab{font-family:"IBM Plex Mono",monospace;font-size:.65rem;letter-spacing:.11em;
  text-transform:uppercase;color:var(--muted);margin-right:4px}
button.f{font-family:"IBM Plex Mono",monospace;font-size:.7rem;letter-spacing:.05em;
  padding:5px 11px;border:1px solid var(--rule);background:var(--surface);
  color:var(--body);border-radius:2px;cursor:pointer;transition:all .12s}
button.f:hover{border-color:var(--accent);color:var(--ink)}
button.f[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:var(--paper)}
button.f:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.count{font-family:"IBM Plex Mono",monospace;font-size:.7rem;color:var(--muted);margin-left:auto}

/* ---- disclosure ---- */
details{border:1px solid var(--rule);border-radius:3px;background:var(--surface);
  margin:14px 0;box-shadow:var(--shadow)}
summary{cursor:pointer;padding:13px 18px;font-weight:600;color:var(--ink);
  font-size:.92rem;list-style:none;display:flex;align-items:center;gap:9px}
summary::-webkit-details-marker{display:none}
summary::before{content:"+";font-family:"IBM Plex Mono",monospace;color:var(--accent);
  font-size:1rem;line-height:1}
details[open] summary::before{content:"–"}
summary:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.dbody{padding:0 18px 18px}
.dbody .tscroll{box-shadow:none}

/* ---- chain ---- */
.chain{display:grid;gap:1px;background:var(--rule);border:1px solid var(--rule);
  border-radius:3px;overflow:hidden;margin:16px 0}
.chain .row{background:var(--surface);display:grid;
  grid-template-columns:150px 1fr auto;gap:14px;padding:12px 16px;align-items:center}
.chain .row .k{font-family:"IBM Plex Mono",monospace;font-size:.7rem;
  letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.chain .row .v{color:var(--ink);font-size:.88rem;word-break:break-word}
.chain .hd{background:var(--sunk);grid-template-columns:1fr;padding:11px 16px}
.chain .hd .t{font-weight:600;color:var(--ink)}

ul.tight{margin:0 0 1rem;padding-left:1.15rem}
ul.tight li{margin-bottom:.4rem}
.note{font-size:.83rem;color:var(--muted);font-style:italic;margin-top:10px}
hr.soft{border:0;border-top:1px solid var(--rule);margin:36px 0}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
@media (max-width:640px){
  .chain .row{grid-template-columns:1fr;gap:4px}
  .wrap{padding:0 18px 64px}
}
"""

def chip(text,kind): return f'<span class="chip c-{kind}">{e(text)}</span>'

# ---------------- workflows table
def wf_rows():
    order={"CORE":0,"TOUCHES":1}
    ws=sorted(D["workflows"],key=lambda w:(order[w["tier"]],not w["live"],w["n"].lower()))
    out=[]
    for w in ws:
        live = chip("live","acc") if w["live"] else chip("off","mute")
        tier = chip(w["tier"],"ok" if w["tier"]=="CORE" else "mute")
        eg = "<br>".join("· "+e(x[:58]) for x in w["eg"]) if w["eg"] else "&mdash;"
        out.append(
          f'<tr data-tier="{w["tier"]}" data-live="{"1" if w["live"] else "0"}">'
          f'<td class="nm">{e(w["n"])}</td>'
          f'<td>{live}</td><td>{tier}</td>'
          f'<td class="num">{w["em"]}</td>'
          f'<td class="ev">{e(w["ev"])}</td>'
          f'<td class="ev">{eg}</td></tr>')
    return "\n".join(out)

# ---------------- destinations
def dest_rows():
    out=[]
    for u,n in D["dest"]:
        host = ("main site (Magento)" if "www.davincilabs.com" in u else
                "PL blog" if "blog.davincilabs.com" in u else
                "landing pages" if "info.davincilabs.com" in u else "other")
        k = "bad" if "www.davincilabs.com" in u else "mute"
        out.append(f'<tr><td class="num">{n}</td><td>{chip(host,k)}</td>'
                   f'<td class="u">{e(u)}</td></tr>')
    return "\n".join(out)

# ---------------- emails
def email_rows():
    out=[]
    for m in sorted(D["emails"],key=lambda x:x["n"].lower()):
        st=m["s"]
        k = "acc" if st.startswith("AUTOMATED") else ("ok" if st.startswith("PUBLISHED") else "warn")
        out.append(f'<tr data-state="{e(st)}"><td class="nm">{e(m["n"])}</td>'
                   f'<td>{chip(st.replace("_"," ").lower(),k)}</td>'
                   f'<td class="u">{e(m["u"][:110])}</td></tr>')
    return "\n".join(out)

# ---------------- assets
def asset_rows():
    out=[]
    for a in sorted(D["assets"],key=lambda x:(x["t"],x["ti"].lower())):
        st=a["st"]
        k = "bad" if "GONE" in st else ("mute" if "n/a" in st else
            ("ok" if st.startswith("PUBLISHED") else "warn"))
        sk = {"STRONG":"ok","MEDIUM":"warn","WEAK":"bad"}[a["str"]]
        out.append(
          f'<tr data-type="{e(a["t"])}" data-str="{a["str"]}" data-gone="{"1" if "GONE" in st else "0"}">'
          f'<td class="nm">{e(a["ti"][:66])}</td>'
          f'<td>{chip(a["t"],"mute")}</td>'
          f'<td>{chip(st.replace("_"," ").lower(),k)}</td>'
          f'<td class="num">{a["inb"]}</td><td class="num">{a["eml"]}</td><td class="num">{a["wf"]}</td>'
          f'<td>{chip(a["str"],sk)}</td>'
          f'<td class="ev">{e(a["ev"][:120])}</td></tr>')
    return "\n".join(out)

# ---------------- forms
def form_rows():
    out=[]
    for f in D["forms"]:
        gap = chip("no live workflow","bad") if f["lw"]==0 else chip(f'{f["lw"]} live','ok')
        out.append(f'<tr><td class="nm">{e(f["n"].strip())}</td>'
                   f'<td class="num">{len(f["pages"])}</td>'
                   f'<td>{gap}</td>'
                   f'<td class="ev">{e(", ".join(f["pages"][:4]))}'
                   f'{" …" if len(f["pages"])>4 else ""}</td></tr>')
    return "\n".join(out)

R=D["recon"]
nwf=len(D["workflows"]); ncore=sum(1 for w in D["workflows"] if w["tier"]=="CORE")
ncorelive=sum(1 for w in D["workflows"] if w["tier"]=="CORE" and w["live"])
gone=sum(1 for a in D["assets"] if "GONE" in a["st"])
nlivecoreemails=49  # distinct verified emails sent by the 12 live core workflows

HTML=f"""<title>Praxera Migration Asset Ledger</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>{CSS}</style>

<header class="top"><div class="wrap">
  <div class="brandline"><span class="dot"></span>
    <span>FoodScience LLC &middot; HubSpot 4087538 &middot; Private Label &rarr; Praxera</span></div>
  <h1>What the Praxera migration<br>has to carry across</h1>
  <p class="sub">Two audits of the same portal, taken eight weeks apart by different methods,
  reconciled into one list. Every row names the specific thing that made it private label &mdash;
  a slug, an <code>href</code>, a form on a page &mdash; because a name is not evidence.</p>
  <div class="metrics">
    <div class="metric"><b>{R['live_verified']}</b><small>emails link to a PL page</small></div>
    <div class="metric"><b>{ncorelive}</b><small>live core workflows</small></div>
    <div class="metric"><b>6</b><small>forms on the new site</small></div>
    <div class="metric"><b>0</b><small>have a live workflow</small></div>
    <div class="metric"><b>105</b><small>assets in the June audit</small></div>
    <div class="metric"><b>62</b><small>pages that audit never saw</small></div>
  </div>
  <p class="note">Generated {e(D['generated'])} from HubSpot draft state. Patrick&rsquo;s audit:
  <code>DaVinci_PrivateLabel_Migration_Audit_1.xlsx</code>, 25 June 2026.</p>
</div></header>

<div class="wrap">

<section id="verdict">
  <div class="shead"><p class="eyebrow">Start here</p><h2>The three things that decide the launch</h2></div>
  <div class="measure">

  <div class="call bad">
    <h3>1 &nbsp;Nothing on the new site is wired to anything</h3>
    <p>All six forms embedded across the 65 Praxera pages have <strong>zero live workflows</strong>
    listening to them. The nine live private-label workflows enrol on four <em>different</em>
    forms &mdash; <code>PRIVATE LABEL NEW</code>, <code>PRIVATE LABEL NEW (New DV Site)</code>,
    <code>Contact Us NEW</code>, <code>LP: Private Labeling Supplements Guide</code>.
    A lead who fills in the new consultation form today receives nothing and reaches no queue.</p>
    <p class="note">Detected by matching form GUIDs found on the pages against enrolment criteria in
    every flow. A workflow enrolling by list membership or property change would not appear this
    way, so read this as &ldquo;no form-triggered follow-up&rdquo;, not a mathematical zero.</p>
  </div>

  <div class="call bad">
    <h3>2 &nbsp;The two most-linked destinations aren&rsquo;t in HubSpot</h3>
    <p><code>www.davincilabs.com/private-label-get-started</code> is the target of
    <strong>83 email links</strong> and 70 workflow references;
    <code>/private-labeling/</code> takes another 27. Both live on the Magento main site,
    outside HubSpot, so no CMS-side redirect reaches them. They are the largest single
    breakage risk in the migration and they need a redirect owner outside this portal.</p>
  </div>

  <div class="call warn">
    <h3>3 &nbsp;The guide funnel has no capture on the new site</h3>
    <p>Of the pages that offer a download, only <code>pl-demo-onboarding-guide</code> carries a form.
    <code>pl-demo-guides</code>, <code>pl-demo-sell-sheets</code>,
    <code>pl-demo-ingredients-testing</code>, <code>pl-demo-definitive-guide</code> and
    <code>pl-demo-resources</code> have none. A Praxera-branded Ingredients &amp; Testing form
    <em>was</em> built on 26 July &mdash; it was never placed on a page.</p>
  </div>
  </div>
</section>

<section id="method">
  <div class="shead"><p class="eyebrow">How the two audits check each other</p>
    <h2>Where they agree, believe the number</h2></div>
  <div class="measure">
  <p>Patrick&rsquo;s June audit scanned URLs and links. This scan read form GUIDs, flow definitions
  and email bodies across all 511 workflows and 2,962 emails in the portal. Different instruments,
  same portal, eight weeks apart.</p>
  <p>The first pass matched the string <code>private-label</code> anywhere in an email payload and
  returned <strong>394</strong> hits &mdash; more than double Patrick&rsquo;s count. That gap was
  the tell. Requiring an actual <code>&lt;a href&gt;</code> pointing at a private-label URL, rather
  than the token appearing in an image filename or a CSS class, drops it to <strong>184</strong>.
  Patrick found 183.</p>
  </div>
  <div class="tscroll" style="margin-top:20px"><table>
    <thead><tr><th>Reconciliation</th><th class="num">Count</th><th>Reading</th></tr></thead>
    <tbody>
      <tr><td class="nm">Both audits agree</td><td class="num">{R['agree_both']}</td>
        <td class="ev">the trustworthy core of the email list</td></tr>
      <tr><td class="nm">Patrick only</td><td class="num">{R['patrick_distinct_emails']-R['agree_both']}</td>
        <td class="ev">unpublished, deleted, or the link was removed since June</td></tr>
      <tr><td class="nm">Live scan only</td><td class="num">{R['live_verified']-R['agree_both']}</td>
        <td class="ev">created since June, or Praxera-era</td></tr>
      <tr><td class="nm">Rejected as token-only</td><td class="num">210</td>
        <td class="ev">the string appears, no link does &mdash; incl. PetTechLabs&rsquo; own
        private-label pages, a different brand in the same portal</td></tr>
    </tbody></table></div>
  <p class="note">Rejecting 210 rows matters more than finding 184. A PetTechLabs nurture on a
  DaVinci migration list is how the wrong emails get rewritten.</p>
</section>

<section id="workflows">
  <div class="shead"><p class="eyebrow">Automation &middot; {nwf} workflows</p>
    <h2>What to clone, and what only needs a link fixed</h2></div>
  <div class="measure">
  <p><strong>Core</strong> means the workflow is the private-label funnel: it is named for the brand,
  or it sends three or more verified private-label emails. Those get Praxera clones.
  <strong>Touches</strong> means it links to a private-label page once, incidentally &mdash;
  a footer, a single CTA. Those need the URL updated and nothing else.</p>
  </div>
  <div class="filters" id="wf-filters">
    <span class="lab">Show</span>
    <button class="f" data-f="all" aria-pressed="true">All</button>
    <button class="f" data-f="CORE" aria-pressed="false">Core only</button>
    <button class="f" data-f="TOUCHES" aria-pressed="false">Touches only</button>
    <button class="f" data-f="live" aria-pressed="false">Live only</button>
    <span class="count" id="wf-count"></span>
  </div>
  <div class="tscroll"><table id="wf-table">
    <thead><tr><th>Workflow</th><th>State</th><th>Tier</th><th class="num">PL emails</th>
      <th>Evidence</th><th>Example email sent</th></tr></thead>
    <tbody>{wf_rows()}</tbody></table></div>
  <p class="note">{ncore} core &middot; {nwf-ncore} incidental. Two rows are marked
  name-only &mdash; <code>New to Supplements-Private Label</code> and
  <code>Experienced with Supplements-Private Label</code> carry the words and nothing else;
  both are off and neither is worth cloning.</p>
</section>

<section id="destinations">
  <div class="shead"><p class="eyebrow">Redirect priority</p>
    <h2>Where those emails actually point</h2></div>
  <div class="measure"><p>Ranked by how many emails link there. Query strings collapsed.
  Anything on the main site is outside HubSpot&rsquo;s redirect tooling.</p></div>
  <div class="tscroll"><table>
    <thead><tr><th class="num">Emails</th><th>Where it lives</th><th>Destination</th></tr></thead>
    <tbody>{dest_rows()}</tbody></table></div>
</section>

<section id="forms">
  <div class="shead"><p class="eyebrow">Entry points</p>
    <h2>The six forms on the new site</h2></div>
  <div class="tscroll"><table>
    <thead><tr><th>Form</th><th class="num">Pages</th><th>Listening</th><th>Where it appears</th></tr></thead>
    <tbody>{form_rows()}</tbody></table></div>
  <p class="note">One is already Praxera-named. The rest still carry
  &ldquo;Private Label&rdquo; or <code>[Brand TBD]</code> in the form name, which is visible in
  HubSpot reporting and in notification emails.</p>
</section>

<section id="assets">
  <div class="shead"><p class="eyebrow">Patrick&rsquo;s inventory, re-checked live</p>
    <h2>105 assets &mdash; and the 62 it never saw</h2></div>
  <div class="measure">
  <p>Every asset from the June workbook, re-queried against HubSpot today. Slug drift:
  <strong>none</strong> &mdash; the audit spreadsheets still point where they did.</p>
  <p>{gone} rows return 404. Three of them are not deletions: <code>pl-demo-custom-formulation</code>,
  <code>pl-demo-definitive-guide</code> and <code>pl-demo-get-started</code> were
  <em>rebuilt</em> in the new site with fresh HubSpot IDs, so the June IDs are stale rather than
  dead. <code>pl-demo-pillarpage</code> became <code>en/pl-demo-pillar</code>.
  Only <code>private-label-home</code> is genuinely gone.</p>
  </div>
  <div class="filters" id="as-filters">
    <span class="lab">Show</span>
    <button class="f" data-f="all" aria-pressed="true">All</button>
    <button class="f" data-f="Blog post" aria-pressed="false">Blog</button>
    <button class="f" data-f="Landing page" aria-pressed="false">Landing</button>
    <button class="f" data-f="Main-site page" aria-pressed="false">Main site</button>
    <button class="f" data-f="gone" aria-pressed="false">404 only</button>
    <button class="f" data-f="weak" aria-pressed="false">Weak evidence</button>
    <span class="count" id="as-count"></span>
  </div>
  <div class="tscroll" style="max-height:620px;overflow-y:auto"><table id="as-table">
    <thead><tr><th>Asset</th><th>Type</th><th>Live status</th>
      <th class="num">In</th><th class="num">Em</th><th class="num">Wf</th>
      <th>Evidence</th><th>Why it is PL</th></tr></thead>
    <tbody>{asset_rows()}</tbody></table></div>

  <div class="call warn">
    <h3>The coverage gap</h3>
    <p>The June audit lists <strong>6</strong> private-label site pages. There are now
    <strong>65</strong>, and only three of the old slugs survive into the new build. So
    <strong>62 of the pages you are about to launch appear in no migration audit at all</strong> &mdash;
    they have never been checked for inbound links, email references or workflow references, because
    they did not exist when the check was run.</p>
  </div>
</section>

<section id="guides">
  <div class="shead"><p class="eyebrow">Lead magnets</p>
    <h2>Each guide is a chain, not a file</h2></div>
  <div class="measure"><p>A guide breaks at whichever link still points at DaVinci. Four chains
  matter, ordered by how much traffic depends on them.</p></div>

  <div class="chain">
    <div class="row hd"><span class="t">Private Label Supplements Guide &nbsp;&middot;&nbsp;
      31 inbound links, the most-referenced asset in the audit</span></div>
    <div class="row"><span class="k">Landing page</span>
      <span class="v u">info.davincilabs.com/private-label-supplements-guide</span>
      <span>{chip("published","ok")}</span></div>
    <div class="row"><span class="k">Form</span>
      <span class="v">LP: Private Labeling Supplements Guide</span><span>{chip("live","acc")}</span></div>
    <div class="row"><span class="k">Thank-you</span>
      <span class="v u">/thank-you-guide-private-labeling-supplements</span><span>{chip("published","ok")}</span></div>
    <div class="row"><span class="k">Feeds</span>
      <span class="v">ToF_Danielle_Nurture (9 emails) &middot; ToF_Paul_Nurture (8 emails)</span>
      <span>{chip("live","acc")}</span></div>
    <div class="row"><span class="k">Praxera side</span>
      <span class="v">pl-demo-guides &mdash; no form embedded</span><span>{chip("gap","bad")}</span></div>
  </div>

  <div class="chain">
    <div class="row hd"><span class="t">Ingredients, Testing &amp; Certification Guide</span></div>
    <div class="row"><span class="k">Landing page</span>
      <span class="v u">info.davincilabs.com/ingredients-testing-certification-guide</span>
      <span>{chip("published","ok")}</span></div>
    <div class="row"><span class="k">Form</span>
      <span class="v">DV LP: Private Labeling Supplement: Ingredients, Testing &amp; Certification</span>
      <span>{chip("live","acc")}</span></div>
    <div class="row"><span class="k">Nurture</span>
      <span class="v">Ingredients, Testing And Certifications Guide Nurture_MoF (6 emails)</span>
      <span>{chip("off","mute")}</span></div>
    <div class="row"><span class="k">Praxera side</span>
      <span class="v">Form built 26 July as &ldquo;Private Label [New Brand]&rdquo; &mdash;
      never placed on a page</span><span>{chip("orphan","bad")}</span></div>
  </div>

  <div class="chain">
    <div class="row hd"><span class="t">Client Onboarding Guide &nbsp;&middot;&nbsp; the one chain that is partly staged</span></div>
    <div class="row"><span class="k">Landing page</span>
      <span class="v u">info.davincilabs.com/private-label-supplements-client-onboarding</span>
      <span>{chip("published","ok")}</span></div>
    <div class="row"><span class="k">Praxera page</span>
      <span class="v">en/pl-demo-onboarding-guide</span><span>{chip("form present","ok")}</span></div>
    <div class="row"><span class="k">Form</span>
      <span class="v">Private Label [Brand TBD] - Page - Onboarding Guide</span>
      <span>{chip("rename needed","warn")}</span></div>
    <div class="row"><span class="k">Thank-you</span>
      <span class="v">en/pl-demo-ty-onboarding &mdash; carries the consultation form, not onboarding</span>
      <span>{chip("check","warn")}</span></div>
  </div>

  <div class="chain">
    <div class="row hd"><span class="t">Resource Center &nbsp;&middot;&nbsp; 11 email links, 9 workflow references</span></div>
    <div class="row"><span class="k">Landing page</span>
      <span class="v u">info.davincilabs.com/private-label-supplements-resource-center</span>
      <span>{chip("published","ok")}</span></div>
    <div class="row"><span class="k">Praxera page</span>
      <span class="v">en/pl-demo-resources &mdash; no form embedded</span><span>{chip("gap","bad")}</span></div>
  </div>

  <p class="note">One more loose thread: a page still links to
  <code>fsc-live.com/dvcdn/docs/PrivateLabels.pdf</code> and two link to
  <code>www.davincilabs.com/product-guide</code> &mdash; assets hosted outside both HubSpot and
  the new domain.</p>
</section>

<section id="emails">
  <div class="shead"><p class="eyebrow">The full list</p>
    <h2>{R['live_verified']} emails linking to a private-label page</h2></div>
  <details><summary>Open the verified email list</summary><div class="dbody">
    <div class="filters" id="em-filters">
      <span class="lab">Show</span>
      <button class="f" data-f="all" aria-pressed="true">All</button>
      <button class="f" data-f="AUTOMATED" aria-pressed="false">Automated</button>
      <button class="f" data-f="PUBLISHED" aria-pressed="false">Published</button>
      <button class="f" data-f="DRAFT" aria-pressed="false">Draft</button>
      <span class="count" id="em-count"></span>
    </div>
    <div class="tscroll" style="max-height:560px;overflow-y:auto"><table id="em-table">
      <thead><tr><th>Email</th><th>State</th><th>Links to</th></tr></thead>
      <tbody>{email_rows()}</tbody></table></div>
    <p class="note">Each row qualified because an anchor in its body resolves to a
    private-label URL. That string is the evidence; it is shown.</p>
  </div></details>
</section>

<section id="next">
  <div class="shead"><p class="eyebrow">Sequence</p><h2>What to do with this</h2></div>
  <div class="measure">
  <ul class="tight">
    <li><strong>Before launch, not after:</strong> point a live workflow at the Praxera
      consultation form, or the new site collects leads into silence.</li>
    <li><strong>Get a redirect owner for the Magento pages.</strong> 110 email links depend on two
      URLs that HubSpot cannot redirect.</li>
    <li><strong>Clone the {ncorelive} live core workflows</strong> and the
      {nlivecoreemails} verified emails they send, repointing enrolment at the Praxera forms.</li>
    <li><strong>Place the orphaned Ingredients &amp; Testing form</strong> and add capture to the
      four guide pages that have none.</li>
    <li><strong>Extend the audit over the 62 uncovered pages</strong> before anything publishes.</li>
    <li><strong>Fill the Redirect Plan tab</strong> in Patrick&rsquo;s workbook &mdash; its
      &ldquo;New URL&rdquo; column is still blank, and the canonical domain now exists to fill it with.</li>
  </ul>
  <p class="note">Scope note: this covers assets, not copy. The manufacturing-claim sweep,
  placeholder text and alt-text items are tracked separately.</p>
  </div>
</section>

</div>

<script>
function wire(barId, tableId, countId, match){{
  var bar=document.getElementById(barId), tbl=document.getElementById(tableId),
      cnt=document.getElementById(countId);
  if(!bar||!tbl) return;
  var rows=Array.prototype.slice.call(tbl.tBodies[0].rows);
  function apply(f){{
    var n=0;
    rows.forEach(function(r){{
      var ok = (f==='all') || match(r,f);
      r.hidden = !ok; if(ok) n++;
    }});
    cnt.textContent = n + ' of ' + rows.length;
  }}
  bar.addEventListener('click', function(ev){{
    var b=ev.target.closest('button.f'); if(!b) return;
    bar.querySelectorAll('button.f').forEach(function(x){{
      x.setAttribute('aria-pressed', String(x===b)); }});
    apply(b.dataset.f);
  }});
  apply('all');
}}
wire('wf-filters','wf-table','wf-count',function(r,f){{
  if(f==='live') return r.dataset.live==='1';
  return r.dataset.tier===f;
}});
wire('as-filters','as-table','as-count',function(r,f){{
  if(f==='gone') return r.dataset.gone==='1';
  if(f==='weak') return r.dataset.str==='WEAK'||r.dataset.str==='MEDIUM';
  return r.dataset.type===f;
}});
wire('em-filters','em-table','em-count',function(r,f){{
  return (r.dataset.state||'').indexOf(f)===0;
}});
</script>
"""
open(S+"/praxera_ledger.html","w").write(HTML)
print("wrote", S+"/praxera_ledger.html", len(HTML), "bytes")
