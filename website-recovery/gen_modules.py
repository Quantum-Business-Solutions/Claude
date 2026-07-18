#!/usr/bin/env python3
"""Generate 7 conversion modules (two-futures, cost-of-inaction, before-after,
roi-estimator, is-this-you, myth-reality, why-now) for all 9 Quantum themes."""
import json, os

S = '/tmp/claude-0/-home-user-Claude/afaaa5d3-2de0-5da2-9bf3-affd4e8c30f7/scratchpad/new-modules/'
os.makedirs(S, exist_ok=True)

def text(id, label, default=""):
    return {"id": id, "name": id, "label": label, "required": False, "locked": False,
            "allow_new_line": False, "type": "text", "display_width": None, "default": default}

def group(id, label, children, defaults, mn=1, mx=8, dflt=3):
    return {"id": id, "name": id, "label": label, "required": False, "locked": False,
            "occurrence": {"min": mn, "max": mx, "sorting_label_field": None, "default": dflt},
            "tab": "CONTENT", "expanded": False, "group_occurrence_meta": None, "type": "group",
            "display_width": None, "children": children, "default": defaults}

META = lambda label: {"global": False,
    "content_types": ["LANDING_PAGE", "SITE_PAGE", "BLOG_LISTING", "BLOG_POST"],
    "host_template_types": ["PAGE", "BLOG_POST", "BLOG_LISTING"],
    "label": label, "is_available_for_new_content": True}

HEADER = ('<section class="q-section"><div class="q-container">'
 '<div style="text-align:center;max-width:760px;margin:0 auto 30px">'
 '{% if module.eyebrow %}<div class="q-eyebrow" style="justify-content:center"><span class="q-eyebrow-rule"></span>{{ module.eyebrow }}</div>{% endif %}'
 '<h2 style="margin:14px 0 12px">{{ module.heading }}</h2>'
 '{% if module.intro %}<p style="color:var(--fg-muted)">{{ module.intro }}</p>{% endif %}</div>')
FOOTER = '</div></section>'
CHIP = 'display:inline-block;border:1px solid rgba(196,164,74,.5);border-radius:999px;padding:4px 14px;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--q-gold,#c4a44a);margin-bottom:14px'

MODULES = {}

# 1 ---- two futures ----
MODULES['quantum-two-futures'] = {
 "meta": META("Quantum Two Futures (status quo vs with Quantum)"),
 "fields": [
   text("eyebrow","Eyebrow","Two Futures"),
   text("heading","Heading (em allowed)","Same starting point. <em>Very different endings.</em>"),
   text("intro","Intro","The decision you make this quarter compounds for years. Here's where each path leads."),
   text("left_label","Left chip","The Status Quo"),
   group("left_items","Status-quo bullets",[text("a","Bullet")],
     [{"a":"Flat pipeline, quarter after quarter"},{"a":"Spend that can't be tied to revenue"},
      {"a":"Reps buried in manual work, not selling"},{"a":"A system that gets heavier every year"}],1,8,4),
   text("right_label","Right chip","With Quantum"),
   group("right_items","With-Quantum bullets",[text("b","Bullet")],
     [{"b":"Compounding, predictable pipeline growth"},{"b":"Every dollar traced from spend to closed revenue"},
      {"b":"Reps focused on live conversations, not admin"},{"b":"A system that gets smarter and faster over time"}],1,8,4),
   text("footnote","Footnote",""),
 ],
 "html": HEADER + '''<style>
.q-tf{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.q-tf-p{border-radius:14px;padding:28px 26px;border:1px solid rgba(138,143,155,.25);background:var(--bg-alt,#101725)}
.q-tf-p.gold{border-color:var(--q-gold,#c4a44a);background:linear-gradient(180deg,rgba(196,164,74,.08),rgba(196,164,74,.02))}
.q-tf-p ul{margin:14px 0 0;padding:0;list-style:none}
.q-tf-p li{padding:7px 0 7px 26px;position:relative;font-size:14.5px;line-height:1.5;color:var(--fg-muted,#8a8f9b)}
.q-tf-p.gold li{color:var(--fg,#e2e5eb)}
.q-tf-p li:before{content:"\\2715";position:absolute;left:0;top:8px;font-size:11px;opacity:.7}
.q-tf-p.gold li:before{content:"\\2713";color:var(--q-gold,#c4a44a);font-size:13px;opacity:1}
@media(max-width:820px){.q-tf{grid-template-columns:1fr}}
</style>
<div class="q-tf">
 <div class="q-tf-p"><span style="''' + CHIP + '''">{{ module.left_label }}</span>
  <svg viewBox="0 0 300 90" style="width:100%;display:block"><path d="M6,38 C80,40 160,52 294,68" fill="none" stroke="rgba(138,143,155,.65)" stroke-width="2.5"/><line x1="6" y1="84" x2="294" y2="84" stroke="rgba(138,143,155,.2)"/></svg>
  <ul>{% for i in module.left_items %}<li>{{ i.a }}</li>{% endfor %}</ul></div>
 <div class="q-tf-p gold"><span style="''' + CHIP + '''">{{ module.right_label }}</span>
  <svg viewBox="0 0 300 90" style="width:100%;display:block"><defs><linearGradient id="qtfg" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#c4a44a" stop-opacity=".3"/><stop offset="1" stop-color="#c4a44a"/></linearGradient></defs><path d="M6,74 C110,70 200,44 294,10" fill="none" stroke="url(#qtfg)" stroke-width="2.5"/><line x1="6" y1="84" x2="294" y2="84" stroke="rgba(196,164,74,.25)"/></svg>
  <ul>{% for i in module.right_items %}<li>{{ i.b }}</li>{% endfor %}</ul></div>
</div>
{% if module.footnote %}<p style="text-align:center;color:var(--fg-muted);font-size:13px;margin-top:20px">{{ module.footnote }}</p>{% endif %}''' + FOOTER,
}

# 2 ---- cost of inaction ----
MODULES['quantum-cost-of-inaction'] = {
 "meta": META("Quantum Cost of Inaction (waiting timeline + total)"),
 "fields": [
   text("eyebrow","Eyebrow","The Cost of Waiting"),
   text("heading","Heading (em allowed)","Doing nothing <em>isn't free</em>"),
   text("intro","Intro","Every quarter without a connected system, the gap widens — wasted spend, decaying pipeline, and competitors compounding ahead of you."),
   group("milestones","Timeline milestones",[text("chip","Month chip (e.g. Month 3)"),text("delta","Big delta (e.g. -22%)"),text("mdesc","Description")],
     [{"chip":"Month 3","delta":"","mdesc":"Small cracks, ignored: leads sit un-worked in inboxes, reps grow numb to the CRM, no baseline to improve against."},
      {"chip":"Month 6","delta":"","mdesc":"Momentum stalls: pipeline coverage slips below target, cost per opportunity climbs, best rep frustrated by manual work."},
      {"chip":"Month 12","delta":"","mdesc":"Competitors pull ahead: deals lost to faster-moving rivals, forecasts unreliable, board loses trust in the numbers."}],1,6,3),
   text("total_value","Total banner value (set per page — leave blank to hide)",""),
   text("total_label","Total banner label","estimated 12-month cost of inaction"),
   text("cta_label","CTA label","Stop the bleed"),
   text("cta_url","CTA URL","https://meetings.hubspot.com/shawn-peterson"),
   text("footnote","Footnote / assumptions",""),
 ],
 "html": HEADER + '''<style>
.q-coi{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.q-coi-c{border:1px solid rgba(138,143,155,.25);border-radius:14px;padding:24px 22px;background:var(--bg-alt,#101725)}
.q-coi-c .d{font-family:var(--q-serif,Georgia),serif;font-size:30px;color:var(--q-gold,#c4a44a)}
.q-coi-band{margin-top:26px;border:1px solid rgba(196,164,74,.45);border-radius:14px;padding:26px 30px;display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;background:linear-gradient(90deg,rgba(196,164,74,.1),rgba(196,164,74,.03))}
.q-coi-band .v{font-family:var(--q-serif,Georgia),serif;font-size:42px;color:var(--q-gold,#c4a44a);line-height:1.1}
.q-coi-btn{border:1px solid var(--q-gold,#c4a44a);color:var(--q-gold,#c4a44a);padding:12px 28px;border-radius:999px;font-weight:600;text-decoration:none;white-space:nowrap}
.q-coi-btn:hover{background:var(--q-gold,#c4a44a);color:#080b12}
@media(max-width:820px){.q-coi{grid-template-columns:1fr}}
</style>
<div class="q-coi">{% for m in module.milestones %}
 <div class="q-coi-c"><span style="''' + CHIP + '''">{{ m.chip }}</span>
 {% if m.delta %}<div class="d">{{ m.delta }}</div>{% endif %}
 <p style="color:var(--fg-muted);font-size:14.5px;margin:10px 0 0">{{ m.mdesc }}</p></div>
{% endfor %}</div>
{% if module.total_value %}<div class="q-coi-band"><div><div class="v">{{ module.total_value }}</div><div style="color:var(--fg-muted);letter-spacing:.06em;text-transform:uppercase;font-size:12.5px;margin-top:4px">{{ module.total_label }}</div></div><a class="q-coi-btn" href="{{ module.cta_url }}">{{ module.cta_label }}</a></div>{% endif %}
{% if module.footnote %}<p style="text-align:center;color:var(--fg-muted);font-size:12.5px;margin-top:16px">{{ module.footnote }}</p>{% endif %}''' + FOOTER,
}

# 3 ---- before / after ----
MODULES['quantum-before-after'] = {
 "meta": META("Quantum Before/After (metrics table)"),
 "fields": [
   text("eyebrow","Eyebrow","By the Numbers"),
   text("heading","Heading (em allowed)","Before Quantum, and <em>after</em>"),
   text("intro","Intro","The metrics that move when your revenue engine finally connects."),
   group("rows","Metric rows (use real, verifiable numbers only)",[text("metric","Metric"),text("bv","Before"),text("av","After"),text("delta","Change")],
     [{"metric":"Your metric","bv":"—","av":"—","delta":""},
      {"metric":"Your metric","bv":"—","av":"—","delta":""},
      {"metric":"Your metric","bv":"—","av":"—","delta":""}],1,8,3),
   text("footnote","Footnote / source line","Results from client engagements; individual outcomes vary."),
 ],
 "html": HEADER + '''<style>
.q-ba{width:100%;max-width:880px;margin:0 auto;border-collapse:collapse;font-size:15px}
.q-ba th{text-align:left;padding:13px 16px;border-bottom:1px solid rgba(196,164,74,.35);color:var(--fg-muted);font-weight:600;font-size:12.5px;letter-spacing:.08em;text-transform:uppercase}
.q-ba td{padding:14px 16px;border-bottom:1px solid rgba(196,164,74,.14)}
.q-ba .m{color:var(--fg);font-weight:600}
.q-ba .b{color:var(--fg-muted)}
.q-ba .a{color:var(--fg);font-family:var(--q-serif,Georgia),serif;font-size:18px}
.q-ba .dl{color:var(--q-gold,#c4a44a);font-weight:600;white-space:nowrap}
</style>
<div style="overflow-x:auto"><table class="q-ba"><tr><th>Metric</th><th>Before</th><th>After</th><th>Change</th></tr>
{% for r in module.rows %}<tr><td class="m">{{ r.metric }}</td><td class="b">{{ r.bv }}</td><td class="a">{{ r.av }}</td><td class="dl">{{ r.delta }}</td></tr>{% endfor %}
</table></div>
{% if module.footnote %}<p style="text-align:center;color:var(--fg-muted);font-size:12.5px;margin-top:16px">{{ module.footnote }}</p>{% endif %}''' + FOOTER,
}

# 4 ---- roi estimator ----
MODULES['quantum-roi-estimator'] = {
 "meta": META("Quantum ROI Estimator (interactive sliders)"),
 "fields": [
   text("eyebrow","Eyebrow","ROI Estimator"),
   text("heading","Heading (em allowed)","See what a <em>connected system</em> is worth to you"),
   text("intro","Intro","Adjust the sliders to your business. The model estimates what a modest lift on your current engine is worth — assumptions below."),
   text("uplift_pct","Modeled lift % (e.g. 25)","25"),
   text("investment","Reference investment $ (e.g. 14950)","14950"),
   text("cta_label","CTA label","Get my custom plan"),
   text("cta_url","CTA URL","https://meetings.hubspot.com/shawn-peterson"),
   text("footnote","Assumptions footnote","Illustrative model: applies the lift % to your current annual closed revenue (leads × 12 × close rate × deal size). Your actual plan gets real numbers from your data."),
 ],
 "html": HEADER + '''<style>
.q-roi{display:grid;grid-template-columns:1.1fr 1fr;gap:20px;max-width:920px;margin:0 auto}
.q-roi-p{border:1px solid rgba(138,143,155,.25);border-radius:14px;padding:26px;background:var(--bg-alt,#101725)}
.q-roi-p.gold{border-color:var(--q-gold,#c4a44a)}
.q-roi label{display:flex;justify-content:space-between;color:var(--fg-muted);font-size:13.5px;margin:18px 0 6px}
.q-roi label b{color:var(--fg)}
.q-roi input[type=range]{width:100%;accent-color:var(--q-gold,#c4a44a)}
.q-roi .big{font-family:var(--q-serif,Georgia),serif;font-size:46px;color:var(--q-gold,#c4a44a);line-height:1.05}
.q-roi .sub{display:flex;gap:14px;margin-top:18px}
.q-roi .sub>div{flex:1;border:1px solid rgba(196,164,74,.2);border-radius:10px;padding:12px}
.q-roi .sub .n{font-family:var(--q-serif,Georgia),serif;font-size:22px;color:var(--q-gold,#c4a44a)}
.q-roi-btn{display:inline-block;margin-top:20px;border:1px solid var(--q-gold,#c4a44a);color:var(--q-gold,#c4a44a);padding:11px 26px;border-radius:999px;font-weight:600;text-decoration:none}
.q-roi-btn:hover{background:var(--q-gold,#c4a44a);color:#080b12}
@media(max-width:820px){.q-roi{grid-template-columns:1fr}}
</style>
<div class="q-roi" data-uplift="{{ module.uplift_pct }}" data-invest="{{ module.investment }}">
 <div class="q-roi-p">
  <label>New leads / month <b class="q-roi-lv">200</b></label><input class="q-roi-l" type="range" min="10" max="1000" step="10" value="200">
  <label>Average deal size <b class="q-roi-dv">$10,000</b></label><input class="q-roi-d" type="range" min="1000" max="100000" step="1000" value="10000">
  <label>Close rate <b class="q-roi-cv">20%</b></label><input class="q-roi-c" type="range" min="5" max="60" step="1" value="20">
 </div>
 <div class="q-roi-p gold">
  <div style="color:var(--fg-muted);font-size:12.5px;letter-spacing:.08em;text-transform:uppercase">Projected added revenue / year</div>
  <div class="big q-roi-out">$—</div>
  <div class="sub"><div><div class="n q-roi-roi">—</div><div style="color:var(--fg-muted);font-size:12.5px">estimated ROI multiple</div></div>
  <div><div class="n q-roi-pb">—</div><div style="color:var(--fg-muted);font-size:12.5px">estimated payback</div></div></div>
  <a class="q-roi-btn" href="{{ module.cta_url }}">{{ module.cta_label }}</a>
 </div>
</div>
{% if module.footnote %}<p style="text-align:center;color:var(--fg-muted);font-size:12.5px;margin-top:16px;max-width:760px;margin-left:auto;margin-right:auto">{{ module.footnote }}</p>{% endif %}
<script>
(function(){document.querySelectorAll('.q-roi').forEach(function(w){
 var l=w.querySelector('.q-roi-l'),d=w.querySelector('.q-roi-d'),c=w.querySelector('.q-roi-c');
 var up=(parseFloat(w.dataset.uplift)||25)/100, inv=parseFloat(w.dataset.invest)||14950;
 function fm(n){return n>=1e6?'$'+(n/1e6).toFixed(1)+'M':'$'+Math.round(n/1e3)+'K'}
 function go(){var L=+l.value,D=+d.value,C=+c.value/100;
  w.querySelector('.q-roi-lv').textContent=L;
  w.querySelector('.q-roi-dv').textContent='$'+D.toLocaleString();
  w.querySelector('.q-roi-cv').textContent=Math.round(C*100)+'%';
  var add=L*12*C*D*up;
  w.querySelector('.q-roi-out').textContent=fm(add);
  w.querySelector('.q-roi-roi').textContent=(add/inv).toFixed(1)+'x';
  var pb=inv/(add/12);
  w.querySelector('.q-roi-pb').textContent=pb<1?'<1 mo':Math.ceil(pb)+' mo';}
 [l,d,c].forEach(function(i){i.addEventListener('input',go)}); go();
});})();
</script>''' + FOOTER,
}

# 5 ---- is this you ----
MODULES['quantum-is-this-you'] = {
 "meta": META("Quantum Is This You (interactive checklist qualifier)"),
 "fields": [
   text("eyebrow","Eyebrow","Is This You?"),
   text("heading","Heading (em allowed)","Check every one that <em>sounds familiar</em>"),
   text("intro","Intro","The more that land, the more we can help. Be honest — this is just for you."),
   group("items","Checklist items",[text("q","Statement")],
     [{"q":"Leads slip through the cracks between marketing and sales"},
      {"q":"We can't trace marketing spend to actual revenue"},
      {"q":"Our reps spend more time on admin than selling"},
      {"q":"Our tools don't talk to each other"},
      {"q":"Outbound is inconsistent — feast or famine"},
      {"q":"We're not showing up in AI search or answer engines"}],1,10,6),
   text("banner_text","Banner text (use {n} and {t})","{n} of {t} sound familiar. Start checking the ones that hit home."),
   text("cta_label","CTA label","Book a call"),
   text("cta_url","CTA URL","https://meetings.hubspot.com/shawn-peterson"),
 ],
 "html": HEADER + '''<style>
.q-ity{max-width:760px;margin:0 auto}
.q-ity-i{display:flex;gap:14px;align-items:flex-start;border:1px solid rgba(138,143,155,.25);border-radius:12px;padding:16px 18px;margin-bottom:12px;cursor:pointer;background:var(--bg-alt,#101725);transition:border-color .15s}
.q-ity-i:hover{border-color:rgba(196,164,74,.5)}
.q-ity-i.on{border-color:var(--q-gold,#c4a44a);background:linear-gradient(90deg,rgba(196,164,74,.08),rgba(196,164,74,.02))}
.q-ity-b{width:20px;height:20px;flex:0 0 20px;border:1.5px solid rgba(138,143,155,.6);border-radius:5px;margin-top:1px;position:relative}
.q-ity-i.on .q-ity-b{border-color:var(--q-gold,#c4a44a);background:var(--q-gold,#c4a44a)}
.q-ity-i.on .q-ity-b:after{content:"\\2713";position:absolute;inset:0;color:#080b12;font-size:14px;text-align:center;line-height:20px}
.q-ity-band{margin-top:22px;border:1px solid rgba(196,164,74,.45);border-radius:12px;padding:20px 24px;display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap;background:linear-gradient(90deg,rgba(196,164,74,.1),rgba(196,164,74,.03))}
.q-ity-btn{border:1px solid var(--q-gold,#c4a44a);color:var(--q-gold,#c4a44a);padding:11px 26px;border-radius:999px;font-weight:600;text-decoration:none;white-space:nowrap}
.q-ity-btn:hover{background:var(--q-gold,#c4a44a);color:#080b12}
</style>
<div class="q-ity" data-banner="{{ module.banner_text }}">
{% for i in module.items %}<div class="q-ity-i"><span class="q-ity-b"></span><span style="color:var(--fg);font-size:15px">{{ i.q }}</span></div>{% endfor %}
<div class="q-ity-band"><span class="q-ity-msg" style="font-family:var(--q-serif,Georgia),serif;font-size:19px;color:var(--fg)"></span><a class="q-ity-btn" href="{{ module.cta_url }}">{{ module.cta_label }}</a></div>
</div>
<script>
(function(){document.querySelectorAll('.q-ity').forEach(function(w){
 var items=w.querySelectorAll('.q-ity-i'),msg=w.querySelector('.q-ity-msg'),tpl=w.dataset.banner;
 function go(){var n=w.querySelectorAll('.q-ity-i.on').length;
  msg.textContent=tpl.replace('{n}',n).replace('{t}',items.length);}
 items.forEach(function(i){i.addEventListener('click',function(){i.classList.toggle('on');go()})}); go();
});})();
</script>''' + FOOTER,
}

# 6 ---- myth vs reality ----
MODULES['quantum-myth-reality'] = {
 "meta": META("Quantum Myth vs Reality"),
 "fields": [
   text("eyebrow","Eyebrow","Myth vs. Reality"),
   text("heading","Heading (em allowed)","What most people think — <em>and what's actually true</em>"),
   text("intro","Intro","The assumptions that keep teams stuck, and the reality that changes the math."),
   group("pairs","Myth/Reality pairs",[text("myth","Myth"),text("reality","Reality")],
     [{"myth":"Agencies just sell you more tools you won't use.","reality":"We start with outcomes and use the stack you already own — new tools only when they pay for themselves."},
      {"myth":"We need more leads to grow.","reality":"Most teams don't have a lead problem — they have a system problem. Connecting what you have unlocks pipeline you're already paying for."},
      {"myth":"AI and automation are too complex for our team.","reality":"We build the workflows and hand you a system your team actually runs — with humans in the loop where it matters."},
      {"myth":"This will take a year to show results.","reality":"We build in weeks, not quarters — typically with qualified pipeline lift inside 90 days and quick wins in the first few weeks."}],1,8,4),
 ],
 "html": HEADER + '''<style>
.q-mr{max-width:880px;margin:0 auto}
.q-mr-r{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
.q-mr-c{border-radius:12px;padding:20px 22px;border:1px solid rgba(138,143,155,.25);background:var(--bg-alt,#101725)}
.q-mr-c.re{border-color:rgba(196,164,74,.5);background:linear-gradient(180deg,rgba(196,164,74,.07),rgba(196,164,74,.02))}
.q-mr-t{font-size:10.5px;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px}
@media(max-width:820px){.q-mr-r{grid-template-columns:1fr}}
</style>
<div class="q-mr">{% for p in module.pairs %}
<div class="q-mr-r">
 <div class="q-mr-c"><div class="q-mr-t" style="color:var(--fg-muted)">&#10005; Myth</div><p style="margin:0;color:var(--fg-muted);font-size:14.5px">{{ p.myth }}</p></div>
 <div class="q-mr-c re"><div class="q-mr-t" style="color:var(--q-gold,#c4a44a)">&#10003; Reality</div><p style="margin:0;color:var(--fg);font-size:14.5px">{{ p.reality }}</p></div>
</div>{% endfor %}</div>''' + FOOTER,
}

# 7 ---- why now ----
MODULES['quantum-why-now'] = {
 "meta": META("Quantum Why Now (urgency + compounding banner)"),
 "fields": [
   text("eyebrow","Eyebrow","Why Now"),
   text("heading","Heading (em allowed)","The window is open — <em>but not for long</em>"),
   text("intro","Intro","Three shifts are happening at once. The teams that move now compound the advantage; the ones that wait spend years catching up."),
   group("cards","Reason cards",[text("ct","Title"),text("cd","Description")],
     [{"ct":"Buyers now ask AI first","cd":"Prospects research through ChatGPT, Perplexity, and AI overviews before they ever hit your site. If you're not the cited answer, you're not in the deal."},
      {"ct":"The tooling finally works","cd":"What used to take a data team and six months now ships in weeks — the stack matured, and connected systems are a build decision, not a science project."},
      {"ct":"Early movers compound","cd":"Systems get smarter with data and time. The team that starts this quarter is a year of learning ahead of the one that starts next year."}],1,6,3),
   text("banner_text","Banner text","Every quarter you wait, competitors who moved first are training their system on data you don't have yet."),
   text("cta_label","CTA label","Start now"),
   text("cta_url","CTA URL","https://meetings.hubspot.com/shawn-peterson"),
 ],
 "html": HEADER + '''<style>
.q-wn{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.q-wn-c{border:1px solid rgba(138,143,155,.25);border-radius:14px;padding:24px 22px;background:var(--bg-alt,#101725)}
.q-wn-band{margin-top:26px;border:1px solid rgba(196,164,74,.45);border-radius:14px;padding:22px 28px;display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;background:linear-gradient(90deg,rgba(196,164,74,.1),rgba(196,164,74,.03))}
.q-wn-btn{border:1px solid var(--q-gold,#c4a44a);color:var(--q-gold,#c4a44a);padding:11px 26px;border-radius:999px;font-weight:600;text-decoration:none;white-space:nowrap}
.q-wn-btn:hover{background:var(--q-gold,#c4a44a);color:#080b12}
@media(max-width:820px){.q-wn{grid-template-columns:1fr}}
</style>
<div class="q-wn">{% for c in module.cards %}
 <div class="q-wn-c"><h4 style="margin:0 0 10px">{{ c.ct }}</h4><p style="margin:0;color:var(--fg-muted);font-size:14.5px">{{ c.cd }}</p></div>
{% endfor %}</div>
<div class="q-wn-band"><span style="font-family:var(--q-serif,Georgia),serif;font-size:19px;color:var(--fg);max-width:640px">{{ module.banner_text }}</span><a class="q-wn-btn" href="{{ module.cta_url }}">{{ module.cta_label }}</a></div>''' + FOOTER,
}

for name, m in MODULES.items():
    d = S + name + '.module'
    os.makedirs(d, exist_ok=True)
    open(d + '/module.html', 'w').write(m['html'])
    json.dump(m['fields'], open(d + '/fields.json', 'w'), indent=1)
    json.dump(m['meta'], open(d + '/meta.json', 'w'), indent=1)
    print('generated', name)
