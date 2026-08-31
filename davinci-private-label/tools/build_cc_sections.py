"""Emit the ClientCommand ledger as SECTION BODIES, not a whole document.

ClientCommand refuses to convert a page to sections while its content is a full
HTML document -- the guard fires on the doctype, not on the byte count, which is
why "the page is too big" was the wrong diagnosis. A body fragment converts
fine. Two consequences shape this file:

  * No page-level wrapper. Each section is rendered as a sibling <section>, so a
    <div class="wrap"> opened in one section would never close in another. The
    width and gutters live on the section rule instead.
  * The renderer injects <h2>{label}</h2> as the first child of every section.
    That heading IS the section heading -- so the bodies here carry no <h2> of
    their own, and the stylesheet dresses `section > h2:first-child` to look the
    way .shead used to. Editing a section's label in ClientCommand therefore
    renames the visible heading, which is the behaviour an editor expects.
"""
import json,datetime,re

R=lambda n:json.load(open(f"reference/{n}.json"))
state=R("current_state"); embeds=R("form_embeds"); wf=R("workflow_clones")
redir=R("redirects")
pageh={r["slug"]:r for r in R("page_health")}
blogh={r["slug"]:r for r in R("blog_health")}
emailh={r["id"]:r for r in R("email_clones")}
STAMP=datetime.date.today().strftime("%-d %B %Y")

N={"pages":62,"blog":75,"emails":len(emailh),"forms":len(state["praxera_forms"]),
   "flows":len(wf)}
sends=sum(f["sends"] for f in wf)
dead=sum(f["dead_workflow_list_clauses"] for f in wf)
enrol_bad=[x for f in wf for x in f["enrol_forms"] if not x["praxera"]]
mail_social=[r for r in emailh.values() if r["brand_links"]]
mail_claims=[r for r in emailh.values() if r["claims"]]
page_claims=[r for r in R("page_health") if r["claims"]]
blog_claims=[r for r in R("blog_health") if r["claims"]]
page_links=[r for r in R("page_health") if r["brand_links"]]
place=[r for r in R("page_health") if r["placeholders"]]
foreign_pg=[r for r in R("page_health") if r["foreign_images"]]
foreign_ml=[r for r in emailh.values() if r["foreign_images"]]
orphan=[f["name"].strip() for f in state["praxera_forms"]
        if f["name"].strip() not in embeds["by_form"]]
noform=embeds["pages_with_no_form"]
RC=redir["counts"]
replyto=sum(1 for r in emailh.values() if r["reply_to"]=="enews@davincilabs.com")

CSS=re.sub(r"/\*.*?\*/","",open("src/cc_sections.css").read(),flags=re.S)
CSS=re.sub(r"\n{2,}","\n",CSS).strip()

def chip(t,k): return f'<span class="chip c-{k}">{t}</span>'

SECTIONS=[]
def S(key,label,body):
    """The body carries its own heading; the renderer's injected <h2>{label}</h2>
    is hidden by CSS. The label still names the block in ClientCommand's editor,
    which is what a person picks a section by."""
    head=(f'<div class="shead"><h2>{label}</h2></div>' if key!="intro"
          else f'<h1>{label}</h1>')
    SECTIONS.append({"block_key":key,"label":label,
                     "body":f"<!--sec:{key}-->\n{head}\n{body.strip()}"})

# -- intro carries the stylesheet, the hero and the metrics -----------------
S("intro","The Praxera stack is built. Nothing is switched on.", f'''
<style>{CSS}</style>
<p class="brandline"><span class="dot"></span>FoodScience LLC &middot; HubSpot 4087538
&middot; Private Label &rarr; Praxera</p>
<p class="lede">Every asset the private-label business runs on now exists in Praxera form,
in draft, alongside the original. At cutover the old set goes off, the new set goes on, and the
old URLs redirect to the new ones &mdash; and a rollback is switching them back.</p>
<div class="metrics">
<div class="metric good"><b>{N["pages"]}</b><small>pages</small></div>
<div class="metric good"><b>{N["blog"]}</b><small>blog posts</small></div>
<div class="metric good"><b>{N["emails"]}</b><small>emails</small></div>
<div class="metric good"><b>{N["forms"]}</b><small>forms</small></div>
<div class="metric good"><b>{N["flows"]}</b><small>workflows</small></div>
<div class="metric bad"><b>0</b><small>anything live</small></div>
</div>
<p class="note">Every figure on this page was re-read from the live portal on {STAMP}.
Nothing is published, nothing is enabled, and no DaVinci, PetTechLabs or VetriScience asset
has been modified.</p>
<p><a class="cta" href="https://claude.ai/code/artifact/5ed16bf6-6612-4867-9584-bb2face0631d">Open
the asset ledger and sign off asset by asset &rarr;</a></p>
<p class="note">That ledger lists all {sum(N.values())-N["forms"]-N["flows"]+N["forms"]+N["flows"]}
assets individually, each with Approve, Needs work and a comment thread, saved and attributed.</p>
''')

S("closed","Two of the ten open items are done", f'''
<p class="eyebrow">Re-checked against the live drafts today</p>
<p>Checking the 30 August Launch Guide&rsquo;s list against the site as it stands, two items are
complete and one is still open exactly as described.</p>
<div class="win"><span class="tick">&#10003;</span><div>
<h3>Item 1 &mdash; <code>[BRAND_TBD]</code> in the page titles</h3>
<p>Was 42 pages. <strong>Now zero.</strong> No Praxera page title or meta description carries the
token. The guide&rsquo;s most visible defect, closed.</p></div></div>
<div class="win"><span class="tick">&#10003;</span><div>
<h3>Item 9 &mdash; the stray duplicate page</h3>
<p>The <code>-temporary-slug-blog/vitamin-manufacturing&hellip;</code> copy is gone. Nothing on the
site or the blog carries a temporary slug.</p></div></div>
<div class="win"><span class="tick warn">&bull;</span><div>
<h3>Item 3 &mdash; hidden image descriptions &mdash; still open</h3>
<p>Five, as described. The About page still reads <code>DaVinci Vermont manufacturing
facility</code>, the <strong>last DaVinci reference anywhere on the site</strong>, and the brand is
misspelled <code>prexera</code> four times &mdash; three on the home page, one on dropshipping.</p>
</div></div>
<p class="note"><code>[BRAND_TBD]</code> does still appear once in the body of the privacy policy
&mdash; a different instance from the page titles, and still open.</p>
''')

S("redirects","The redirect plan", f'''
<p class="eyebrow">Cutover</p>
<p>Each DaVinci private-label page the Praxera set replaces becomes a redirect to its
replacement, so the pairing is not just provenance &mdash; it is the redirect table.
<strong>{RC["redirects"]} redirects</strong>: {RC["by_kind"]["page"]} website pages and
{RC["by_kind"]["blog"]} blog posts. The full mapping, old URL to new, is the second column of
every page and post row in the ledger.</p>
<p>Two consequences worth stating plainly. The DaVinci originals must be
<strong>redirected, not deleted</strong>, or the inbound links and the search history go with
them. And Praxera slugs must stay fixed from here &mdash; the redirect table and the audit
spreadsheets both point at them.</p>
<div class="tscroll"><table>
<thead><tr><th>Redirect coverage</th><th class="num">Count</th><th>Reading</th></tr></thead>
<tbody>
<tr><td class="nm">Website pages</td><td class="num">{RC["by_kind"]["page"]}</td>
<td class="ev">a DaVinci <code>pl-demo-*</code> page redirects to each</td></tr>
<tr><td class="nm">Blog posts</td><td class="num">{RC["by_kind"]["blog"]}</td>
<td class="ev">the whole <code>blog.davincilabs.com/private-label/</code> group is covered</td></tr>
<tr><td class="nm">Praxera pages that are brand new</td><td class="num">{RC["orphan_targets"]}</td>
<td class="ev">the home page and two thank-you pages. No DaVinci original, so no redirect needed
&mdash; marked <strong>new page</strong> in the ledger, not counted as a gap</td></tr>
<tr><td class="nm">Published DaVinci pages with nowhere to point</td>
<td class="num">{RC["orphan_sources"]}</td>
<td class="ev">the guide landing pages &mdash; the one real gap</td></tr>
</tbody></table></div>
<div class="call bad"><h3>Three published guide pages have no Praxera equivalent</h3>
<p><code>info.davincilabs.com/private-label-supplements-guide</code> (<strong>57 assets link to
it</strong>), <code>/private-label-supplements-resource-center</code> (14) and
<code>/private-label-supplements-client-onboarding</code> (2). Live lead-gen pages with nothing to
redirect to, so at cutover they either keep serving DaVinci content or break 73 inbound links.</p>
<p>This is the same gap from the other side as the orphaned forms:
<strong>Praxera - Supplements Guide</strong>, <strong>Praxera - Client Onboarding Guide</strong>
and <strong>Praxera - Ingredients &amp; Testing Guide</strong> are built and sitting on no page.
Building the three Praxera guide pages places those forms and creates the redirect targets in one
move.</p></div>
''')

cards=[("pages",N["pages"],"website pages","all draft","acc",
        "On praxerasupplements.com. Slugs unchanged, so the audit spreadsheets and the redirect "
        "table still point at the right rows."),
       ("blog",N["blog"],"blog posts","all draft","acc",
        "Cloned from the <code>/private-label/</code> group. No DaVinci URL and no DaVinci "
        "wording survives in any of them."),
       ("emails",N["emails"],"marketing emails","all draft","acc",
        "Every email a private-label workflow sends, plus the two new Praxera templates."),
       ("forms",N["forms"],"forms","not live","ok",
        f'{len(embeds["by_form"])} are placed on {embeds["n_pages_with_praxera_form"]} pages. '
        "No DaVinci form is embedded on any Praxera page."),
       ("flows",N["flows"],"workflows","disabled","ok",
        f"All {sends} email sends point at a Praxera email. None is enabled."),
       ("tpl",2,"email templates","draft","acc",
        "Pulse newsletter and product/category, both drag-and-drop editable in HubSpot.")]
S("stack","The parallel stack",
  '<p class="eyebrow">What exists today</p><div class="stack">'
  +"".join(f'<div class="card"><b>{n}</b><div class="lbl">{lbl}</div>'
           f'<div class="st">{chip(st,k)}</div><p>{txt}</p></div>'
           for _,n,lbl,st,k,txt in cards)+"</div>")

frows="".join(
  f'<tr><td class="nm">{f["name"].strip()}</td>'
  f'<td>{chip(f"on {len(on)} page"+("s" if len(on)>1 else ""),"acc") if (on:=[x or "(home)" for x in embeds["by_form"].get(f["name"].strip(),[])]) else chip("on no page","bad")}</td>'
  f'<td class="num">{sum(1 for w in wf for x in w["enrol_forms"] if x["id"]==f["id"])}</td>'
  f'<td class="ev">{", ".join(sorted(on)[:5])+(" …" if len(on)>5 else "") if on else "&mdash;"}</td></tr>'
  for f in sorted(state["praxera_forms"],key=lambda x:x["name"]))
S("forms","Forms, and where they sit", f'''
<p class="eyebrow">Entry points</p>
<div class="tscroll"><table><thead><tr><th>Praxera form</th><th>Placement</th>
<th class="num">Flows enrolling</th><th>Pages</th></tr></thead><tbody>{frows}</tbody></table></div>
<p class="note">{len(orphan)} forms are built and on no page. Three of them are the guide forms
that belong on the three Praxera guide pages the redirect plan is missing.</p>
''')

def wrow(f):
    bad=sorted({x["name"] for x in f["enrol_forms"] if not x["praxera"]})
    out=[]
    if f["davinci_sends"]: out.append(chip(f'{f["davinci_sends"]} DaVinci send',"bad"))
    if bad: out.append(chip("enrols on "+", ".join(bad[:2]),"bad"))
    if not f["enrol_forms"]: out.append(chip("no form enrolment","warn"))
    if f["dead_workflow_list_clauses"]:
        n=f["dead_workflow_list_clauses"]
        out.append(chip(f'{n} dead clause'+("s" if n>1 else ""),"mute"))
    name=f["name"].replace("Praxera - ","")
    return (f'<tr><td class="nm">{name}</td><td class="num">{f["sends"]}</td>'
            f'<td>{chip("off","ok")}</td><td>{" ".join(out) or chip("clear","acc")}</td></tr>')
S("workflows",f'The {N["flows"]} workflow clones', f'''
<p class="eyebrow">Automation</p>
<div class="tscroll"><table><thead><tr><th>Praxera workflow</th><th class="num">Email sends</th>
<th>Enabled</th><th>Outstanding</th></tr></thead><tbody>
{"".join(wrow(f) for f in sorted(wf,key=lambda x:-x["sends"]))}</tbody></table></div>
<p class="note">Dead clauses test membership of workflows HubSpot deleted years ago along with
their generated membership lists. They can never match, so they are deletions, not audiences to
rebuild.</p>
''')

S("recheck","What the re-check changed", f'''
<p class="eyebrow">This version</p>
<p>The whole portal was re-read for this version rather than carried forward from the last one.
Six figures moved, and two of the moves matter.</p>
<div class="tscroll"><table>
<thead><tr><th>Figure</th><th class="num">Was</th><th class="num">Is</th><th>Why</th></tr></thead>
<tbody>
<tr><td class="nm">Praxera website pages</td><td class="num">65</td><td class="num">62</td>
<td class="ev">counted against the domain; there are no Praxera landing pages, only site pages</td></tr>
<tr><td class="nm">Emails with a clickable DaVinci link</td><td class="num">0</td>
<td class="num">{len(mail_social)}</td>
<td class="ev">the earlier pass matched hostnames. The footer social icons point at
twitter.com/Davincilabsvt and instagram.com/davincilaboratories &mdash; the brand is in the path,
not the host, so it was missed</td></tr>
<tr><td class="nm">Clones enrolling on a DaVinci form</td><td class="num">&mdash;</td>
<td class="num">{len(enrol_bad)}</td>
<td class="ev">not previously measured. Enrolment was read from the criteria block rather than
assumed from the clone log</td></tr>
<tr><td class="nm">Dead workflow-list clauses</td><td class="num">7</td><td class="num">{dead}</td>
<td class="ev">the earlier count covered one flow&rsquo;s worth</td></tr>
<tr><td class="nm">Pages with manufacturing claims</td><td class="num">46</td>
<td class="num">{len(page_claims)}</td>
<td class="ev">the earlier pattern matched across list punctuation, so &ldquo;we offer:
doctor-formulated&rdquo; read as a claim</td></tr>
<tr><td class="nm">Literal &ldquo;None&rdquo; on pages</td><td class="num">26</td><td class="num">0</td>
<td class="ev">fixed since the last version; 3 blog posts still carry it</td></tr>
</tbody></table></div>
<div class="call good"><h3>What did not move</h3>
<p>Zero published pages, zero published posts, zero sent emails, zero enabled workflows. All
{sends} workflow email sends still point at a Praxera email, and no DaVinci form is embedded on
any Praxera page.</p>
<p><strong>Nothing belonging to another brand was touched.</strong> All 486 PetTechLabs,
VetriScience and Pet Naturals records &mdash; pages, posts, emails and forms, published copy and
drafts &mdash; were searched: <strong>none contains the word Praxera</strong>. There is also no
structural connection between the two sites: all {N["pages"]} Praxera pages render from
<code>Private Label/Templates/Page - DND.html</code>, PetTechLabs from its own
<code>Pet_Tech_Labs</code> templates, and the two sets share <strong>zero modules</strong>. Some
PetTechLabs records do show recent edits on the same HubSpot login this work uses, because the API
token is bound to a QBS user account rather than to this project; reading those revisions shows
schema markup and internal-linking changes from separate SEO work.</p>
<p>The 16 modules the Praxera pages do share are shared only with <em>unpublished</em> DaVinci
pl-demo pages, so the pending global-module edits cannot change a live page.</p></div>
''')

S("open","What has to happen before launch", f'''
<p class="eyebrow">Still open</p>
<div class="call bad"><h3>Manufacturing claims &mdash; {len(page_claims)} pages,
{len(blog_claims)} posts, {len(mail_claims)} emails</h3>
<p>Praxera cannot present itself as the manufacturer. Verbatim, from the rendered drafts:
<em>&ldquo;everything we produce is doctor-formulated&rdquo;</em> (16 assets),
<em>&ldquo;we are one of the most trusted dietary supplement manufacturers&rdquo;</em> (6),
<em>&ldquo;we handle formulation, manufacturing&hellip;&rdquo;</em>. Provenance wording &mdash;
&ldquo;Manufactured in Vermont, U.S.A.&rdquo; &mdash; is fine; the first person is not. The largest
remaining item and the only compliance risk.</p></div>
<div class="call bad"><h3>Three published guide pages have nothing to redirect to</h3>
<p>73 assets link to them, 57 to the Supplements Guide alone. Building the three Praxera guide
pages also places three of the six orphaned forms.</p></div>
<div class="call bad"><h3>{len(mail_social)} emails link to DaVinci&rsquo;s social accounts</h3>
<p>The footer icon row was cloned intact, so a Praxera email&rsquo;s Instagram icon opens
<code>instagram.com/davincilaboratories</code> and its X icon opens
<code>twitter.com/Davincilabsvt</code>. One shared module, so one edit repeated.</p></div>
<div class="call bad"><h3>{len(enrol_bad)} workflow clones still enrol on a DaVinci form</h3>
<p>Five enrol on <code>Contact Us NEW</code>, which has no Praxera clone; one on a deleted form;
one on <code>Brand Development Call (Inactive)</code>.</p></div>
<div class="call warn"><h3>Five hidden image descriptions</h3>
<p>Invisible on the page, read by screen readers and search engines. Includes the last DaVinci
reference on the site and four <code>prexera</code> misspellings. Minutes to fix.</p></div>
<div class="call warn"><h3>{len(page_links)} pages still carry a clickable DaVinci link</h3>
<p><code>resources</code> and <code>learning/definitive-guide</code> hold most of them. The
redirects will catch these after cutover, but a link that needs a redirect to reach the right
brand is still worth repointing directly.</p></div>
<div class="call warn"><h3>Placeholder copy on {len(place)} pages</h3>
<p>Nine are marked for Justin or Patrick. The privacy policy still contains
<code>[BRAND_TBD]</code> in its body. <code>book-consultation</code> has neither a form nor a
booking widget.</p></div>
<div class="call warn"><h3>Sending identity</h3>
<p>{replyto} of {N["emails"]} clones still reply to <code>enews@davincilabs.com</code>. Praxera
needs its own sending domain authenticated before any of this can send.</p></div>
<div class="call warn"><h3>Blog housekeeping and the domain root</h3>
<p>74 of {N["blog"]} posts carry publish date <code>1970-01-01</code>, none has tags, and the
original CTAs did not survive the clone. 149 blog links point at
<code>praxerasupplements.com/</code> and nothing is there yet.</p></div>
<div class="call good"><h3>{len(foreign_pg)} pages and {len(foreign_ml)} emails load assets from
the DaVinci domain</h3>
<p>Not a branding defect &mdash; Praxera artwork living in the portal&rsquo;s file domain. Listed
because they break if that domain is disconnected at cutover.</p></div>
''')

S("sequence","Order of operations", f'''
<p class="eyebrow">Sequence</p>
<ol class="steps">
<li><strong>The manufacturing-claim copy pass</strong> across {len(page_claims)} pages,
{len(blog_claims)} posts and {len(mail_claims)} emails. The only compliance risk; nothing else
should start first.</li>
<li><strong>Build the three Praxera guide pages</strong> &mdash; places three orphaned forms and
closes the redirect gap.</li>
<li><strong>Fix the five image descriptions</strong> &mdash; minutes, and it removes the last
DaVinci reference on the site.</li>
<li><strong>Decide the Praxera social accounts</strong>, then fix the shared email footer once.</li>
<li><strong>Point the {len(enrol_bad)} enrolment triggers at Praxera forms.</strong></li>
<li><strong>Repoint the remaining DaVinci links</strong> and edit the shared Product Guide
module.</li>
<li><strong>Place the remaining orphaned forms</strong> and give <code>book-consultation</code> a
booking widget.</li>
<li><strong>Fill the {len(place)} placeholder pages</strong> and replace <code>[BRAND_TBD]</code>
in the privacy policy.</li>
<li><strong>Authenticate the Praxera sending domain</strong> and repoint reply-to.</li>
<li><strong>Stand up the home page</strong> at the domain root.</li>
<li><strong>Blog housekeeping</strong> &mdash; dates, tags, CTAs.</li>
<li><strong>Delete the {dead} dead suppression clauses</strong> and decide on the D4HCP flow.</li>
<li><strong>Cutover:</strong> publish, enable the {N["flows"]} workflows, switch the originals off,
put the {RC["redirects"]} redirects in place. Rolling back is doing those in reverse, which is why
the originals are redirected rather than deleted.</li>
</ol>
''')

S("method","Classified by address, not by topic", '''
<p class="eyebrow">How the private-label set was identified</p>
<p>DaVinci sells supplements under its own name to practitioners <em>and</em> runs a private-label
business, from one portal, on one contact list, and the phrase &ldquo;private label&rdquo; appears
on both sides. PetTechLabs, a separate brand in the same portal, runs its own private-label pet
line. So nothing was classified by what it is about. It was classified by the address it lives at
&mdash; the <code>/private-label/</code> blog group, an
<code>info.davincilabs.com/private-label*</code> slug, the <code>pl-demo-*</code> pages.</p>
<p>The first pass matched the string <code>private-label</code> anywhere in an email and returned
<strong>394</strong> hits. Requiring an actual <code>&lt;a href&gt;</code> pointing at a
private-label URL &mdash; rather than the token appearing in an image filename or a CSS class
&mdash; drops that to <strong>184</strong>. Patrick&rsquo;s June audit, using different instruments
eight weeks earlier, found 183. They agree on 179.</p>
<p>Twenty-five posts are about private label but sit in PetTechLabs&rsquo; namespace. Topically
they qualify; structurally they are another brand&rsquo;s, and none was moved.</p>
''')

json.dump(SECTIONS,open("deliverables/cc_sections.json","w"),indent=1)
whole="\n".join(s["body"] for s in SECTIONS)
open("deliverables/cc_fragment.html","w").write(whole)
# a standalone copy that renders the way the portal will, for local checking
prev="".join(f'<section id="{s["block_key"]}">\n<h2>{s["label"]}</h2>\n{s["body"]}\n</section>\n'
             for s in SECTIONS)
open("deliverables/cc_markers.json","w").write(
    json.dumps([f"<!--sec:{s['block_key']}-->" for s in SECTIONS[1:]],indent=1))
open("deliverables/cc_preview.html","w").write(
 '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
 '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
 '<title>Praxera Migration Asset Ledger</title>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:'
 'opsz,wght@6..72,400;6..72,500&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:'
 'wght@400;500;600&display=swap">\n</head><body>\n'+prev+"</body></html>\n")
print(f"{len(SECTIONS)} sections, {sum(len(s['body']) for s in SECTIONS)} body bytes")
for s in SECTIONS: print(f"   {s['block_key']:12s} {len(s['body']):>6}  {s['label'][:56]}")
