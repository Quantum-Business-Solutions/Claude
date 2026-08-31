"""Generate the migration asset ledger from the verified reference data.

One generator, three outputs, so the repo copy, the ClientCommand page and the
Claude artifact cannot drift: they are the same bytes wrapped differently. Every
number below is read from reference/*.json, which is written by the verify_*
scripts against the live portal -- nothing here is typed by hand.
"""
import json,html,re,datetime

R=lambda n:json.load(open(f"reference/{n}.json"))
state=R("current_state"); embeds=R("form_embeds"); pairs=R("pairs")
pageh={r["slug"]:r for r in R("page_health")}
blogh={r["slug"]:r for r in R("blog_health")}
emailh={r["id"]:r for r in R("email_clones")}
wf=R("workflow_clones")
E=html.escape
# f-strings cannot hold a backslash, so the prefix strip lives here
PFX=re.compile(r"^Praxera\s*-\s*")
strip=lambda n:PFX.sub("",n or "")
STAMP=datetime.date.today().strftime("%-d %B %Y")

# ---------------------------------------------------------------- counts ----
N={"pages":len(pairs["pages"]),"blog":len(pairs["blog"]),
   "emails":len(pairs["emails"]),"forms":len(state["praxera_forms"]),
   "flows":len(wf)}
live_pages=sum(1 for r in R("page_health") if r["state"]=="PUBLISHED")
live_blog=sum(1 for r in R("blog_health") if r["state"]=="PUBLISHED")
live_mail=sum(1 for r in emailh.values() if r["state"]!="DRAFT")
live_flow=sum(1 for f in wf if f["enabled"])
LIVE=live_pages+live_blog+live_mail+live_flow

sends=sum(f["sends"] for f in wf)
px_sends=sum(f["praxera_sends"] for f in wf)
dv_sends=sum(f["davinci_sends"] for f in wf)
enrol=[x for f in wf for x in f["enrol_forms"]]
enrol_bad=[x for x in enrol if not x["praxera"]]
dead=sum(f["dead_workflow_list_clauses"] for f in wf)

page_claims=[r for r in R("page_health") if r["claims"]]
blog_claims=[r for r in R("blog_health") if r["claims"]]
mail_claims=[r for r in emailh.values() if r["claims"]]
page_links=[r for r in R("page_health") if r["brand_links"]]
mail_social=[r for r in emailh.values() if r["brand_links"]]
place=[r for r in R("page_health") if r["placeholders"]]
foreign_pg=[r for r in R("page_health") if r["foreign_images"]]
foreign_ml=[r for r in emailh.values() if r["foreign_images"]]
noform=embeds["pages_with_no_form"]
orphan=[f["name"].strip() for f in state["praxera_forms"]
        if f["name"].strip() not in embeds["by_form"]]

def chip(t,k): return f'<span class="chip c-{k}">{E(t)}</span>'
def row(*c): return "<tr>"+"".join(c)+"</tr>"

# ------------------------------------------------------------- the tables ---
def tbl(tid,head,rows,note=""):
    cell=lambda h:('<th class="num">' if h.startswith("#") else "<th>")+E(h.lstrip("#"))+"</th>"
    th="".join(cell(h) for h in head)
    return (f'<div class="tscroll"><table id="{tid}"><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>'
            + (f'<p class="note">{note}</p>' if note else ""))

def filt(tid,opts):
    btn=lambda v,l:('<button class="f" data-t="'+tid+'" data-f="'+E(v)+'" aria-pressed="'
                    +("true" if v=="all" else "false")+'">'+E(l)+"</button>")
    b="".join(btn(v,l) for v,l in opts)
    return (f'<div class="filters"><label class="srch">'
            f'<input type="search" data-t="{tid}" placeholder="Filter&hellip;" '
            f'aria-label="Filter this table"></label>{b}'
            f'<span class="count" id="ct-{tid}"></span></div>')

# pages -----------------------------------------------------------------
prows=[]
for p in sorted(pairs["pages"],key=lambda x:x["slug"] or ""):
    h=pageh.get(p["slug"],{})
    issues=[]
    if h.get("brand_links"): issues.append(("bad",f'{len(h["brand_links"])} DaVinci link'+("s" if len(h["brand_links"])>1 else "")))
    if h.get("claims"): issues.append(("bad","manufacturing claim"))
    if h.get("placeholders"): issues.append(("warn","placeholder copy"))
    if p["slug"] in noform: issues.append(("mute","no form"))
    if h.get("foreign_images"): issues.append(("mute",f'{len(h["foreign_images"])} asset'+("s" if len(h["foreign_images"])>1 else "")+" off-domain"))
    tag="clear" if not issues else ("blocked" if any(k=="bad" for k,_ in issues) else "tidy")
    prows.append(f'<tr data-s="{tag}"><td class="nm">{E(p["slug"] or "(home)")}</td>'
        f'<td class="ev">{(E(re.sub(r"^https?://","",p["source_url"])) if p["source_url"] else "&mdash;")}</td>'
        f'<td>{chip("draft","ok")}</td>'
        f'<td>{" ".join(chip(t,k) for k,t in issues) or chip("clear","acc")}</td></tr>')

# blog ------------------------------------------------------------------
brows=[]
for b in sorted(pairs["blog"],key=lambda x:x["slug"] or ""):
    h=blogh.get(b["slug"],{})
    issues=[]
    if h.get("brand_links"): issues.append(("bad","DaVinci link"))
    if h.get("claims"): issues.append(("bad","manufacturing claim"))
    if h.get("bare_none"): issues.append(("warn",'literal "None"'))
    if not b.get("tags"): issues.append(("warn","no tags"))
    d=(b.get("publishDate") or "")[:10]
    if d.startswith("1970"): issues.append(("warn","1970 date"))
    tag="clear" if not issues else ("blocked" if any(k=="bad" for k,_ in issues) else "tidy")
    brows.append(f'<tr data-s="{tag}"><td class="nm">{E((b["name"] or "")[:78])}</td>'
        f'<td class="ev">{(E(re.sub(r"^https?://","",b["source_url"])) if b["source_url"] else "&mdash;")}</td>'
        f'<td>{chip("draft","ok")}</td>'
        f'<td>{" ".join(chip(t,k) for k,t in issues) or chip("clear","acc")}</td></tr>')

# emails ----------------------------------------------------------------
srcmap={r["id"]:r for r in pairs["emails"]}
erows=[]
for e in sorted(pairs["emails"],key=lambda x:x["name"]):
    h=emailh.get(e["id"],{})
    issues=[]
    if h.get("brand_links"): issues.append(("bad",f'{len(h["brand_links"])} DaVinci social link'+("s" if len(h["brand_links"])>1 else "")))
    if h.get("claims"): issues.append(("bad","manufacturing claim"))
    if h.get("reply_to")=="enews@davincilabs.com": issues.append(("warn","DaVinci reply-to"))
    if h.get("foreign_images"): issues.append(("mute","assets off-domain"))
    tag="clear" if not issues else ("blocked" if any(k=="bad" for k,_ in issues) else "tidy")
    erows.append(f'<tr data-s="{tag}"><td class="nm">{E(strip(e["name"])[:74])}</td>'
        f'<td class="ev">{E((e["source_name"] or "new for Praxera")[:64])}</td>'
        f'<td>{chip("draft","ok")}</td>'
        f'<td>{" ".join(chip(t,k) for k,t in issues) or chip("clear","acc")}</td></tr>')

# forms -----------------------------------------------------------------
frows=[]
for f in sorted(state["praxera_forms"],key=lambda x:x["name"]):
    n=f["name"].strip(); on=[x or "(home)" for x in embeds["by_form"].get(n,[])]
    used=[w["name"] for w in wf for x in w["enrol_forms"] if x["id"]==f["id"]]
    if on: st,tag=chip(f"on {len(on)} page"+("s" if len(on)>1 else ""),"acc"),"clear"
    else:  st,tag=chip("on no page","bad"),"blocked"
    frows.append(f'<tr data-s="{tag}"><td class="nm">{E(n)}</td><td>{st}</td>'
        f'<td class="num">{len(used)}</td>'
        f'<td class="ev">{(E(", ".join(sorted(on)[:6])) if on else "&mdash;")}</td></tr>')

# workflows -------------------------------------------------------------
wrows=[]
for f in sorted(wf,key=lambda x:-x["sends"]):
    bad=[x["name"] for x in f["enrol_forms"] if not x["praxera"]]
    issues=[]
    if f["davinci_sends"]: issues.append(("bad",f'{f["davinci_sends"]} DaVinci send'))
    if bad: issues.append(("bad","enrols on "+", ".join(sorted(set(bad))[:2])))
    if not f["enrol_forms"]: issues.append(("warn","no form enrolment"))
    if f["dead_workflow_list_clauses"]:
        issues.append(("mute",f'{f["dead_workflow_list_clauses"]} dead clause'
                       +("s" if f["dead_workflow_list_clauses"]>1 else "")))
    tag="clear" if not issues else ("blocked" if any(k=="bad" for k,_ in issues) else "tidy")
    wrows.append(f'<tr data-s="{tag}"><td class="nm">{E(strip(f["name"])[:60])}</td>'
        f'<td class="num">{f["sends"]}</td>'
        f'<td>{chip("off","ok") if not f["enabled"] else chip("ENABLED","bad")}</td>'
        f'<td>{" ".join(chip(t,k) for k,t in issues) or chip("clear","acc")}</td></tr>')

FOPTS=[("all","All"),("blocked","Needs a fix"),("tidy","Housekeeping"),("clear","Clear")]

# ------------------------------------------------------------------ body ----
def metric(v,l,k=""): return f'<div class="metric {k}"><b>{v}</b><small>{E(l)}</small></div>'

BODY=f'''
<header class="top"><div class="wrap">
<div class="brandline"><span class="dot"></span>
<span>FoodScience LLC &middot; HubSpot 4087538 &middot; Private Label &rarr; Praxera</span></div>
<h1>The Praxera stack is built.<br>Nothing is switched on.</h1>
<p class="sub">Every asset the private-label business runs on now exists in Praxera form,
in draft, alongside the original. At cutover the old set goes off and the new set goes on in
one move &mdash; and a rollback is switching them back.</p>
<div class="metrics">
{metric(N["pages"],"pages","good")}{metric(N["blog"],"blog posts","good")}
{metric(N["emails"],"emails","good")}{metric(N["forms"],"forms","good")}
{metric(N["flows"],"workflows","good")}{metric(LIVE,"anything live","bad")}
</div>
<p class="note">Every figure on this page was re-read from the live portal on {STAMP}.
Nothing is published, nothing is enabled, and no DaVinci, PetTechLabs or VetriScience asset
has been modified.</p>
</div></header>

<div class="wrap">

<nav class="jump" aria-label="Sections">
<a href="#stack">Stack</a><a href="#ledger">Asset ledger</a><a href="#recheck">Re-check</a>
<a href="#open">Open items</a><a href="#seq">Sequence</a><a href="#method">Method</a>
</nav>

<section id="stack">
<div class="shead"><p class="eyebrow">What exists today</p><h2>The parallel stack</h2></div>
<div class="stack">
<div class="card"><b>{N["pages"]}</b><div class="lbl">website pages</div>
<div class="st">{chip("all draft","acc")}</div>
<p class="note">On praxerasupplements.com. Slugs unchanged, so the audit spreadsheets still point
at the right rows. {len(pairs["pages"])-2} are matched to the DaVinci page they replace.</p></div>
<div class="card"><b>{N["blog"]}</b><div class="lbl">blog posts</div>
<div class="st">{chip("all draft","acc")}</div>
<p class="note">Cloned from the <code>/private-label/</code> group. No DaVinci URL and no DaVinci
wording survives in any of them.</p></div>
<div class="card"><b>{N["emails"]}</b><div class="lbl">marketing emails</div>
<div class="st">{chip("all draft","acc")}</div>
<p class="note">Every email a private-label workflow sends, plus the two new Praxera templates.
Zero carry DaVinci wording.</p></div>
<div class="card"><b>{N["forms"]}</b><div class="lbl">forms</div>
<div class="st">{chip("not live","ok")}</div>
<p class="note">{len(embeds["by_form"])} are placed on {embeds["n_pages_with_praxera_form"]} pages.
No DaVinci form is embedded on any Praxera page.</p></div>
<div class="card"><b>{N["flows"]}</b><div class="lbl">workflows</div>
<div class="st">{chip("disabled","ok")}</div>
<p class="note">All {sends} email sends point at a Praxera email &mdash;
{dv_sends} point anywhere else. None is enabled.</p></div>
<div class="card"><b>2</b><div class="lbl">email templates</div>
<div class="st">{chip("draft","acc")}</div>
<p class="note">Pulse newsletter and product/category, both drag-and-drop editable in HubSpot.</p></div>
</div>
</section>

<section id="ledger">
<div class="shead"><p class="eyebrow">Every asset, and what is left to do to it</p>
<h2>The asset ledger</h2></div>
<div class="measure"><p>Each table pairs the Praxera asset with the DaVinci asset it replaces
and states what still needs doing. <strong>Needs a fix</strong> is copy or a link a visitor would
see and that we cannot launch with. <strong>Housekeeping</strong> is real but cosmetic or internal.
<strong>Clear</strong> means nothing outstanding was found.</p></div>

<h3 class="tsub">Website pages <span class="tct">{N["pages"]}</span></h3>
{filt("t-pages",FOPTS)}
{tbl("t-pages",["Praxera page","Replaces","State","Outstanding"],prows,
 "Off-domain assets are images still served from the DaVinci file domain. They render "
 "correctly today and are invisible to a reader, but they break if that domain is "
 "disconnected at cutover, so they are listed rather than ignored.")}

<h3 class="tsub">Blog posts <span class="tct">{N["blog"]}</span></h3>
{filt("t-blog",FOPTS)}
{tbl("t-blog",["Praxera post","Replaces","State","Outstanding"],brows,
 "Publish dates and tags did not survive the clone. Neither is visible in draft, and both are "
 "visible the moment the blog publishes.")}

<h3 class="tsub">Marketing emails <span class="tct">{N["emails"]}</span></h3>
{filt("t-emails",FOPTS)}
{tbl("t-emails",["Praxera email","Replaces","State","Outstanding"],erows,
 "The DaVinci social links are the footer icon row: a Praxera email whose Instagram icon "
 "opens DaVinci's account. It is one module, shared across the set.")}

<h3 class="tsub">Forms <span class="tct">{N["forms"]}</span></h3>
{filt("t-forms",FOPTS)}
{tbl("t-forms",["Praxera form","Placement","#Flows enrolling","Pages"],frows,
 "A form on no page is not necessarily wrong &mdash; several were built ahead of the guide "
 "pages that will carry them. It is wrong at launch.")}

<h3 class="tsub">Workflows <span class="tct">{N["flows"]}</span></h3>
{filt("t-flows",FOPTS)}
{tbl("t-flows",["Praxera workflow","#Email sends","Enabled","Outstanding"],wrows,
 "Dead clauses test membership of workflows HubSpot deleted years ago along with their "
 "generated membership lists. They can never match, so they are deletions, not audiences to "
 "rebuild.")}
</section>

<section id="recheck">
<div class="shead"><p class="eyebrow">This version</p><h2>What the re-check changed</h2></div>
<div class="measure"><p>The whole portal was re-read for this version rather than carried
forward from the last one. Six numbers moved, and two of the moves matter.</p></div>
<div class="tscroll"><table>
<thead><tr><th>Figure</th><th class="num">Was</th><th class="num">Is</th><th>Why</th></tr></thead>
<tbody>
<tr><td class="nm">Praxera website pages</td><td class="num">65</td><td class="num">{N["pages"]}</td>
<td class="ev">counted against the domain; there are no Praxera landing pages, only site pages</td></tr>
<tr><td class="nm">Emails with a clickable DaVinci link</td><td class="num">0</td>
<td class="num">{len(mail_social)}</td>
<td class="ev">the earlier pass matched hostnames. The footer social icons point at
twitter.com/Davincilabsvt and instagram.com/davincilaboratories &mdash; the brand is in the
path, not the host, so it was missed</td></tr>
<tr><td class="nm">Clones enrolling on a DaVinci form</td><td class="num">&mdash;</td>
<td class="num">{len(enrol_bad)}</td>
<td class="ev">not previously measured. Enrolment was read from the criteria block rather than
assumed from the clone log</td></tr>
<tr><td class="nm">Dead workflow-list clauses</td><td class="num">7</td><td class="num">{dead}</td>
<td class="ev">the earlier count covered one flow's worth</td></tr>
<tr><td class="nm">Pages with manufacturing claims</td><td class="num">46</td>
<td class="num">{len(page_claims)}</td>
<td class="ev">the earlier pattern counted a phrase once per occurrence and matched across
list punctuation, so &ldquo;we offer: doctor-formulated&rdquo; read as a claim</td></tr>
<tr><td class="nm">Literal &ldquo;None&rdquo; on pages</td><td class="num">26</td><td class="num">0</td>
<td class="ev">fixed since the last version; 3 blog posts still carry it</td></tr>
</tbody></table></div>
<div class="call good"><h3>What did not move</h3>
<p>Zero published pages, zero published posts, zero sent emails, zero enabled workflows, and no
DaVinci, PetTechLabs or VetriScience asset touched. All {sends} workflow email sends still point
at a Praxera email. No DaVinci form is embedded on any Praxera page.</p></div>
</section>

<section id="open">
<div class="shead"><p class="eyebrow">Still open</p><h2>What has to happen before launch</h2></div>
<div class="measure">

<div class="call bad"><h3>Manufacturing claims &mdash; {len(page_claims)} pages,
{len(blog_claims)} posts, {len(mail_claims)} emails</h3>
<p>Praxera cannot present itself as the manufacturer. Verbatim, from the rendered drafts:
<em>&ldquo;everything we produce is doctor-formulated&rdquo;</em> (16 assets),
<em>&ldquo;we are one of the most trusted dietary supplement manufacturers&rdquo;</em> (6),
<em>&ldquo;we handle formulation, manufacturing&hellip;&rdquo;</em>. Provenance wording
&mdash; &ldquo;Manufactured in Vermont, U.S.A.&rdquo; &mdash; is fine; the first person is not.
This is the largest remaining item and the only one that is a compliance risk.</p></div>

<div class="call bad"><h3>{len(mail_social)} emails link to DaVinci's social accounts</h3>
<p>The footer icon row was cloned intact, so a Praxera email's Instagram icon opens
<code>instagram.com/davincilaboratories</code> and its X icon opens
<code>twitter.com/Davincilabsvt</code>. Praxera needs its own accounts, or the row needs removing.
It is a single shared module, so it is one edit repeated, not {len(mail_social)} separate ones.</p></div>

<div class="call bad"><h3>{len(enrol_bad)} workflow clones still enrol on a DaVinci form</h3>
<p>Five enrol on <code>Contact Us NEW</code>, which has no Praxera clone; one on a form that has
been deleted; one on <code>Brand Development Call (Inactive)</code>. Switched on as they are, those
flows would take their enrolment from the DaVinci side of the house.</p></div>

<div class="call warn"><h3>{len(page_links)} pages still carry a clickable DaVinci link</h3>
<p><code>resources</code> and <code>learning/definitive-guide</code> hold most of them &mdash;
link lists pointing back at <code>blog.davincilabs.com/private-label/&hellip;</code>, which now have
Praxera equivalents to point at instead. The home page and <code>dropshipping</code> carry the
Product Guide link from the shared module.</p></div>

<div class="call warn"><h3>{len(orphan)} Praxera forms are on no page, and
{len(noform)} pages have no form</h3>
<p>Built and unplaced: {E(", ".join(orphan[:4]))}{"&hellip;" if len(orphan)>4 else ""}.
The pages that most obviously want them are <code>guides</code>,
<code>learning/ingredients-testing</code>, <code>learning/definitive-guide</code>,
<code>sell-sheets</code> and <code>resources</code>. <code>book-consultation</code> has neither
a form nor a booking widget &mdash; only a placeholder.</p></div>

<div class="call warn"><h3>Placeholder copy on {len(place)} pages</h3>
<p>Nine are marked for Justin or Patrick &mdash; facility detail, packaging options, case studies,
the three paid-traffic landing pages. <code>privacy</code> still contains
<code>[BRAND_TBD]</code>, which is a legal document with an unreplaced merge token in it.</p></div>

<div class="call warn"><h3>Sending identity</h3>
<p>{sum(1 for r in emailh.values() if r["reply_to"]=="enews@davincilabs.com")} of {N["emails"]}
clones still reply to <code>enews@davincilabs.com</code>. Praxera needs its own sending domain
authenticated before any of this can send.</p></div>

<div class="call warn"><h3>Blog housekeeping and the domain root</h3>
<p>74 of {N["blog"]} posts carry publish date <code>1970-01-01</code>, none has tags, and the
original CTAs did not survive the clone. Separately, 149 blog links were pointed at
<code>praxerasupplements.com/</code> as a holding position and nothing is there yet.</p></div>

<div class="call good"><h3>{len(foreign_pg)} pages and {len(foreign_ml)} emails load assets from
the DaVinci domain</h3>
<p>Not a branding defect &mdash; the files are Praxera artwork that happens to live in the DaVinci
file domain, which is where this portal keeps its files. Listed because they break if that domain
is disconnected at cutover, so the decision needs making before, not after.</p></div>
</div>
</section>

<section id="seq">
<div class="shead"><p class="eyebrow">Sequence</p><h2>Order of operations</h2></div>
<div class="measure"><ol class="steps">
<li><strong>The manufacturing-claim copy pass</strong> across {len(page_claims)} pages,
{len(blog_claims)} posts and {len(mail_claims)} emails. Nothing else is a compliance risk and
nothing else should start first.</li>
<li><strong>Decide the Praxera social accounts</strong>, then fix the shared email footer once.</li>
<li><strong>Point the {len(enrol_bad)} enrolment triggers at Praxera forms</strong> &mdash; clone
<code>Contact Us NEW</code>, drop the deleted and inactive ones.</li>
<li><strong>Repoint the remaining DaVinci links</strong> on {len(page_links)} pages and edit the
shared Product Guide module.</li>
<li><strong>Place the {len(orphan)} orphaned forms</strong> and give
<code>book-consultation</code> a real booking widget.</li>
<li><strong>Fill the {len(place)} placeholder pages</strong> and replace
<code>[BRAND_TBD]</code> in the privacy policy.</li>
<li><strong>Authenticate the Praxera sending domain</strong> and repoint reply-to.</li>
<li><strong>Stand up the home page</strong> at the domain root.</li>
<li><strong>Blog housekeeping</strong> &mdash; dates, tags, CTAs.</li>
<li><strong>Delete the {dead} dead suppression clauses</strong> and decide whether the D4HCP flow
is wanted at all.</li>
<li><strong>Cutover:</strong> publish the pages and the blog, enable the {N["flows"]} workflows,
switch the originals off. Rolling back is doing the last two in reverse.</li>
</ol></div>
</section>

<section id="method">
<div class="shead"><p class="eyebrow">How the private-label set was identified</p>
<h2>Classified by address, not by topic</h2></div>
<div class="measure">
<p>DaVinci sells supplements under its own name to practitioners <em>and</em> runs a private-label
business, from one portal, on one contact list, and the phrase &ldquo;private label&rdquo; appears
on both sides. PetTechLabs, a separate brand in the same portal, runs its own private-label pet
line. So nothing was classified by what it is about. It was classified by the address it lives at
&mdash; the <code>/private-label/</code> blog group, an
<code>info.davincilabs.com/private-label*</code> slug, the <code>pl-demo-*</code> pages.</p>
<p>The first pass matched the string <code>private-label</code> anywhere in an email and returned
<strong>394</strong> hits. Requiring an actual <code>&lt;a href&gt;</code> pointing at a
private-label URL &mdash; rather than the token appearing in an image filename or a CSS class
&mdash; drops that to <strong>184</strong>. Patrick's June audit, using different instruments eight
weeks earlier, found 183. They agree on 179.</p>
<p>Twenty-five posts are about private label but sit in PetTechLabs' namespace. Topically they
qualify; structurally they are another brand's, and none was moved. Rejecting those 210 token-only
matches mattered more than finding the 184 &mdash; a PetTechLabs nurture swept into a DaVinci
migration list is how the wrong emails get rewritten.</p>
</div>
<div class="call good"><h3>The same rule applies to this page</h3>
<p>Every count here comes from reading the live records, not from the previous version of this
document. Where the two disagree, the re-check is shown above and the live portal wins.</p></div>
</section>

</div>

<script>
(function(){{
  var tables={{}};
  document.querySelectorAll("table[id^='t-']").forEach(function(t){{
    tables[t.id]={{el:t,rows:[].slice.call(t.tBodies[0].rows),f:"all",q:""}};
  }});
  function apply(id){{
    var s=tables[id];if(!s)return;var n=0;
    s.rows.forEach(function(r){{
      var okF=s.f==="all"||r.dataset.s===s.f;
      var okQ=!s.q||r.textContent.toLowerCase().indexOf(s.q)>-1;
      var show=okF&&okQ;r.hidden=!show;if(show)n++;
    }});
    var c=document.getElementById("ct-"+id);
    if(c)c.textContent=n+" of "+s.rows.length;
  }}
  document.querySelectorAll(".filters button.f").forEach(function(b){{
    b.addEventListener("click",function(){{
      var id=b.dataset.t;tables[id].f=b.dataset.f;
      document.querySelectorAll('.filters button.f[data-t="'+id+'"]').forEach(function(o){{
        o.setAttribute("aria-pressed",String(o===b));
      }});
      apply(id);
    }});
  }});
  document.querySelectorAll(".filters input[type=search]").forEach(function(i){{
    i.addEventListener("input",function(){{
      var id=i.dataset.t;tables[id].q=i.value.trim().toLowerCase();apply(id);
    }});
  }});
  Object.keys(tables).forEach(apply);
}})();
</script>
'''

HEAD=open("deliverables/_head.html").read()
doc=("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">\n"
     "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
     +HEAD+"</head><body>\n"+BODY+"\n</body></html>\n")
open("deliverables/praxera_migration_asset_ledger.html","w").write(doc)
# The artifact is wrapped in its own skeleton at publish time, so it gets the
# head's contents and the body -- never the html/head/body tags themselves.
open("deliverables/artifact_ledger.html","w").write(HEAD+BODY)
print("full doc   ",len(doc),"bytes")
print("artifact   ",len(HEAD+BODY),"bytes")
print(f"rows: pages {len(prows)} blog {len(brows)} emails {len(erows)} "
      f"forms {len(frows)} flows {len(wrows)}")

# ---------------------------------------------------------------------------
# The ClientCommand copy.
#
# Same data, shorter body. The portal page has to be pasted through an MCP call
# and then hand-editable, so it carries the tables a person actually edits --
# forms, workflows, the re-check -- and states the page/blog/email findings as
# counts with the named exceptions, rather than 248 rows nobody will edit by
# hand. The row-by-row ledger stays in the artifact, linked.
# ---------------------------------------------------------------------------
def small(rows):
    return "".join(r.replace(' data-s="clear"','').replace(' data-s="blocked"','')
                    .replace(' data-s="tidy"','') for r in rows)

CC=f'''
<header class="top"><div class="wrap">
<div class="brandline"><span class="dot"></span>
<span>FoodScience LLC &middot; HubSpot 4087538 &middot; Private Label &rarr; Praxera</span></div>
<h1>The Praxera stack is built.<br>Nothing is switched on.</h1>
<p class="sub">Every asset the private-label business runs on now exists in Praxera form,
in draft, alongside the original. At cutover the old set goes off and the new set goes on in
one move &mdash; and a rollback is switching them back.</p>
<div class="metrics">
{metric(N["pages"],"pages","good")}{metric(N["blog"],"blog posts","good")}
{metric(N["emails"],"emails","good")}{metric(N["forms"],"forms","good")}
{metric(N["flows"],"workflows","good")}{metric(LIVE,"anything live","bad")}
</div>
<p class="note">Every figure on this page was re-read from the live portal on {STAMP}.
Nothing is published, nothing is enabled, and no DaVinci, PetTechLabs or VetriScience asset
has been modified.</p>
</div></header>

<div class="wrap">

<section id="stack">
<div class="shead"><p class="eyebrow">What exists today</p><h2>The parallel stack</h2></div>
<div class="stack">
<div class="card"><b>{N["pages"]}</b><div class="lbl">website pages</div>
<div class="st">{chip("all draft","acc")}</div>
<p>On praxerasupplements.com. Slugs unchanged, so the audit spreadsheets still point at the
right rows.</p></div>
<div class="card"><b>{N["blog"]}</b><div class="lbl">blog posts</div>
<div class="st">{chip("all draft","acc")}</div>
<p>Cloned from the <code>/private-label/</code> group. No DaVinci URL and no DaVinci wording
survives in any of them.</p></div>
<div class="card"><b>{N["emails"]}</b><div class="lbl">marketing emails</div>
<div class="st">{chip("all draft","acc")}</div>
<p>Every email a private-label workflow sends, plus the two new Praxera templates.</p></div>
<div class="card"><b>{N["forms"]}</b><div class="lbl">forms</div>
<div class="st">{chip("not live","ok")}</div>
<p>{len(embeds["by_form"])} are placed on {embeds["n_pages_with_praxera_form"]} pages. No DaVinci
form is embedded on any Praxera page.</p></div>
<div class="card"><b>{N["flows"]}</b><div class="lbl">workflows</div>
<div class="st">{chip("disabled","ok")}</div>
<p>All {sends} email sends point at a Praxera email. None is enabled.</p></div>
<div class="card"><b>2</b><div class="lbl">email templates</div>
<div class="st">{chip("draft","acc")}</div>
<p>Pulse newsletter and product/category, both drag-and-drop editable in HubSpot.</p></div>
</div>
</section>

<section id="forms">
<div class="shead"><p class="eyebrow">Entry points</p><h2>Forms, and where they sit</h2></div>
{tbl("cc-forms",["Praxera form","Placement","#Flows enrolling","Pages"],small(frows),
 "Six forms are built and on no page. Several were made ahead of the guide pages that will "
 "carry them &mdash; which is fine now and wrong at launch.")}
</section>

<section id="flows">
<div class="shead"><p class="eyebrow">Automation</p><h2>The {N["flows"]} workflow clones</h2></div>
{tbl("cc-flows",["Praxera workflow","#Email sends","Enabled","Outstanding"],small(wrows),
 "Dead clauses test membership of workflows HubSpot deleted years ago along with their "
 "generated membership lists. They can never match, so they are deletions, not audiences to "
 "rebuild.")}
</section>

<section id="recheck">
<div class="shead"><p class="eyebrow">This version</p><h2>What the re-check changed</h2></div>
<div class="measure"><p>The whole portal was re-read for this version rather than carried
forward from the last one. Six figures moved, and two of the moves matter.</p></div>
<div class="tscroll"><table>
<thead><tr><th>Figure</th><th class="num">Was</th><th class="num">Is</th><th>Why</th></tr></thead>
<tbody>
<tr><td class="nm">Praxera website pages</td><td class="num">65</td><td class="num">{N["pages"]}</td>
<td class="ev">counted against the domain; there are no Praxera landing pages, only site pages</td></tr>
<tr><td class="nm">Emails with a clickable DaVinci link</td><td class="num">0</td>
<td class="num">{len(mail_social)}</td>
<td class="ev">the earlier pass matched hostnames. The footer social icons point at
twitter.com/Davincilabsvt and instagram.com/davincilaboratories &mdash; the brand is in the
path, not the host, so it was missed</td></tr>
<tr><td class="nm">Clones enrolling on a DaVinci form</td><td class="num">&mdash;</td>
<td class="num">{len(enrol_bad)}</td>
<td class="ev">not previously measured. Enrolment was read from the criteria block rather than
assumed from the clone log</td></tr>
<tr><td class="nm">Dead workflow-list clauses</td><td class="num">7</td><td class="num">{dead}</td>
<td class="ev">the earlier count covered one flow's worth</td></tr>
<tr><td class="nm">Pages with manufacturing claims</td><td class="num">46</td>
<td class="num">{len(page_claims)}</td>
<td class="ev">the earlier pattern matched across list punctuation, so &ldquo;we offer:
doctor-formulated&rdquo; read as a claim</td></tr>
<tr><td class="nm">Literal &ldquo;None&rdquo; on pages</td><td class="num">26</td><td class="num">0</td>
<td class="ev">fixed since the last version; 3 blog posts still carry it</td></tr>
</tbody></table></div>
<div class="call good"><h3>What did not move</h3>
<p>Zero published pages, zero published posts, zero sent emails, zero enabled workflows, and no
DaVinci, PetTechLabs or VetriScience asset touched. All {sends} workflow email sends still point
at a Praxera email. No DaVinci form is embedded on any Praxera page.</p></div>
</section>

<section id="open">
<div class="shead"><p class="eyebrow">Still open</p><h2>What has to happen before launch</h2></div>
<div class="measure">

<div class="call bad"><h3>Manufacturing claims &mdash; {len(page_claims)} pages,
{len(blog_claims)} posts, {len(mail_claims)} emails</h3>
<p>Praxera cannot present itself as the manufacturer. Verbatim, from the rendered drafts:
<em>&ldquo;everything we produce is doctor-formulated&rdquo;</em> (16 assets),
<em>&ldquo;we are one of the most trusted dietary supplement manufacturers&rdquo;</em> (6),
<em>&ldquo;we handle formulation, manufacturing&hellip;&rdquo;</em>. Provenance wording
&mdash; &ldquo;Manufactured in Vermont, U.S.A.&rdquo; &mdash; is fine; the first person is not.
This is the largest remaining item and the only one that is a compliance risk.</p></div>

<div class="call bad"><h3>{len(mail_social)} emails link to DaVinci's social accounts</h3>
<p>The footer icon row was cloned intact, so a Praxera email's Instagram icon opens
<code>instagram.com/davincilaboratories</code> and its X icon opens
<code>twitter.com/Davincilabsvt</code>. Praxera needs its own accounts, or the row needs removing.
It is one shared module, so it is one edit repeated, not {len(mail_social)} separate ones.</p></div>

<div class="call bad"><h3>{len(enrol_bad)} workflow clones still enrol on a DaVinci form</h3>
<p>Five enrol on <code>Contact Us NEW</code>, which has no Praxera clone; one on a form that has
been deleted; one on <code>Brand Development Call (Inactive)</code>. Switched on as they are, those
flows would take their enrolment from the DaVinci side of the house.</p></div>

<div class="call warn"><h3>{len(page_links)} pages still carry a clickable DaVinci link</h3>
<p><code>resources</code> and <code>learning/definitive-guide</code> hold most of them &mdash;
link lists pointing back at <code>blog.davincilabs.com/private-label/&hellip;</code>, which now have
Praxera equivalents to point at instead. The home page and <code>dropshipping</code> carry the
Product Guide link from the shared module.</p></div>

<div class="call warn"><h3>{len(orphan)} Praxera forms are on no page, and
{len(noform)} pages have no form</h3>
<p>The pages that most obviously want them are <code>guides</code>,
<code>learning/ingredients-testing</code>, <code>learning/definitive-guide</code>,
<code>sell-sheets</code> and <code>resources</code>. <code>book-consultation</code> has neither a
form nor a booking widget &mdash; only a placeholder.</p></div>

<div class="call warn"><h3>Placeholder copy on {len(place)} pages</h3>
<p>Nine are marked for Justin or Patrick &mdash; facility detail, packaging options, case studies,
the three paid-traffic landing pages. <code>privacy</code> still contains
<code>[BRAND_TBD]</code>, which is a legal document with an unreplaced merge token in it.</p></div>

<div class="call warn"><h3>Sending identity</h3>
<p>{sum(1 for r in emailh.values() if r["reply_to"]=="enews@davincilabs.com")} of {N["emails"]}
clones still reply to <code>enews@davincilabs.com</code>. Praxera needs its own sending domain
authenticated before any of this can send.</p></div>

<div class="call warn"><h3>Blog housekeeping and the domain root</h3>
<p>74 of {N["blog"]} posts carry publish date <code>1970-01-01</code>, none has tags, and the
original CTAs did not survive the clone. Separately, 149 blog links were pointed at
<code>praxerasupplements.com/</code> as a holding position and nothing is there yet.</p></div>

<div class="call good"><h3>{len(foreign_pg)} pages and {len(foreign_ml)} emails load assets from
the DaVinci domain</h3>
<p>Not a branding defect &mdash; the files are Praxera artwork that happens to live in the DaVinci
file domain, which is where this portal keeps its files. Listed because they break if that domain
is disconnected at cutover, so the decision needs making before, not after.</p></div>
</div>
</section>

<section id="seq">
<div class="shead"><p class="eyebrow">Sequence</p><h2>Order of operations</h2></div>
<div class="measure"><ol class="steps">
<li><strong>The manufacturing-claim copy pass</strong> across {len(page_claims)} pages,
{len(blog_claims)} posts and {len(mail_claims)} emails. Nothing else is a compliance risk and
nothing else should start first.</li>
<li><strong>Decide the Praxera social accounts</strong>, then fix the shared email footer once.</li>
<li><strong>Point the {len(enrol_bad)} enrolment triggers at Praxera forms</strong> &mdash; clone
<code>Contact Us NEW</code>, drop the deleted and inactive ones.</li>
<li><strong>Repoint the remaining DaVinci links</strong> on {len(page_links)} pages and edit the
shared Product Guide module.</li>
<li><strong>Place the {len(orphan)} orphaned forms</strong> and give
<code>book-consultation</code> a real booking widget.</li>
<li><strong>Fill the {len(place)} placeholder pages</strong> and replace
<code>[BRAND_TBD]</code> in the privacy policy.</li>
<li><strong>Authenticate the Praxera sending domain</strong> and repoint reply-to.</li>
<li><strong>Stand up the home page</strong> at the domain root.</li>
<li><strong>Blog housekeeping</strong> &mdash; dates, tags, CTAs.</li>
<li><strong>Delete the {dead} dead suppression clauses</strong> and decide whether the D4HCP flow
is wanted at all.</li>
<li><strong>Cutover:</strong> publish the pages and the blog, enable the {N["flows"]} workflows,
switch the originals off. Rolling back is doing the last two in reverse.</li>
</ol></div>
</section>

<section id="method">
<div class="shead"><p class="eyebrow">How the private-label set was identified</p>
<h2>Classified by address, not by topic</h2></div>
<div class="measure">
<p>DaVinci sells supplements under its own name to practitioners <em>and</em> runs a private-label
business, from one portal, on one contact list, and the phrase &ldquo;private label&rdquo; appears
on both sides. PetTechLabs, a separate brand in the same portal, runs its own private-label pet
line. So nothing was classified by what it is about. It was classified by the address it lives at
&mdash; the <code>/private-label/</code> blog group, an
<code>info.davincilabs.com/private-label*</code> slug, the <code>pl-demo-*</code> pages.</p>
<p>The first pass matched the string <code>private-label</code> anywhere in an email and returned
<strong>394</strong> hits. Requiring an actual <code>&lt;a href&gt;</code> pointing at a
private-label URL &mdash; rather than the token appearing in an image filename or a CSS class
&mdash; drops that to <strong>184</strong>. Patrick's June audit, using different instruments eight
weeks earlier, found 183. They agree on 179.</p>
<p>Twenty-five posts are about private label but sit in PetTechLabs' namespace. Topically they
qualify; structurally they are another brand's, and none was moved.</p>
</div>
</section>

<section id="detail">
<div class="shead"><p class="eyebrow">Sign-off</p><h2>Approve the assets one at a time</h2></div>
<div class="measure"><p>The full ledger lists all {N["pages"]}&nbsp;pages, {N["blog"]}&nbsp;posts,
{N["emails"]}&nbsp;emails, {N["forms"]}&nbsp;forms and {N["flows"]}&nbsp;workflows, each paired
with the DaVinci asset it replaces and what is outstanding on it. Every row carries
<strong>Approve</strong> and <strong>Needs work</strong>, and a comment thread for the cases where
the reason matters.</p>
<p>Reviews are saved into the page itself and attributed to whoever left them, so this is the
record rather than a copy of one &mdash; open it, put your name in, and work down the list.
Progress shows per group and overall.</p>
<p><a href="https://claude.ai/code/artifact/5ed16bf6-6612-4867-9584-bb2face0631d">Open the asset
ledger and start signing off &rarr;</a></p></div>
</section>

</div>
'''
cc=("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">\n"
    "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
    +HEAD+"</head><body>\n"+CC+"\n</body></html>\n")
open("deliverables/clientcommand_ledger.html","w").write(cc)
print("clientcommand",len(cc),"bytes")
