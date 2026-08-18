import json,subprocess,os,re

# ---------- 1. correct the published process doc ----------
p='verification-process.html'
s=open(p).read()

s=s.replace(
 "Written from the full pass on list 5243 — 662 contacts in, every one read on LinkedIn, 340 surviving.",
 "Written from the full pass on list 5243: 662 contacts at intake, 491 read against dated LinkedIn history, 340 surviving. The other 171 left the list — on lead-status and persona writes this process itself made — before they were ever read.")

s=s.replace(
 "<tr><td>Contacts at intake</td><td class=\"n\">662</td><td>every one read against dated LinkedIn history</td></tr>",
 "<tr><td>Contacts at intake</td><td class=\"n\">662</td><td>snapshot taken before the first write</td></tr>\n        <tr><td>Actually read against dated LinkedIn history</td><td class=\"n\">491</td><td>the remaining 171 left the list before being reached — see the caution below</td></tr>")

s=s.replace(
 "<tr><td>Unverifiable by any source</td><td class=\"n\">15</td><td><span class=\"pill p-warn\">unreadable</span>, each naming what was tried</td></tr>",
 "<tr><td>Unverifiable by any source</td><td class=\"n\">41</td><td><span class=\"pill p-warn\">unreadable</span> across the whole pass — 8.3%, not the 15 still on the list at the end</td></tr>")

s=s.replace(
 "<tr><td class=\"n\">4</td><td>Nothing worked → <span class=\"pill p-warn\">unreadable</span>, naming every source tried</td><td>—</td><td>15 of 662</td></tr>",
 "<tr><td class=\"n\">4</td><td>Nothing worked → <span class=\"pill p-warn\">unreadable</span>, naming every source tried</td><td>—</td><td>41 of 493, ~8%</td></tr>")

# the false "stop worrying about it" conclusion on the 32 phones
s=s.replace(
 "<h3>Check the rest of the list too, then stop worrying about it</h3>",
 "<h3>Check the rest of the list too — and self-test the check before believing it</h3>")
s=s.replace(
 "<p>The same audit across all 312 contacts on the calling list found 276 matching their employer and 32 not — and <em>none</em> of the 32 belonged to a different company. They were alternate or direct lines at the correct employer: three contacts at one company all shared that company's office line while the company record held its toll-free number. The wrong-company phone problem is created by re-association, so it lives where re-association happens.</p>",
 "<p>The same audit across all 312 contacts on the calling list found 276 matching their employer and 32 not. The first attempt to identify those 32 reported that none belonged to another company — <strong>and that conclusion was wrong.</strong> It used a digits-only token search that cannot match a number stored in parenthesised form, so it returned nothing for all 32 and the nothing was read as an answer. Re-run with a query that tries every stored format, and after a self-test against a number already known to be present, <strong>9 of the 32 sit on a differently-named company's number.</strong></p>\n    <p>Those 9 split two ways and neither the CRM nor a vendor can separate them automatically. Roughly half are the employer's own predecessor or an acquired subsidiary — a contact at Workiva holding the number registered to WebFilings, Workiva's original name. The rest look like a former employer's line on a contact who never moved, the same defect as the movers but pre-existing. The vendor alias test does <em>not</em> resolve this: it keeps predecessor names as separate company records with separate ids, so \"different id\" and \"different company\" are not the same statement once an acquisition is involved.</p>\n    <p><strong>So non-mover phone conflicts get flagged for a human, never auto-corrected.</strong> Overwriting a contact's working office line with their employer's toll-free menu is a worse outcome than the ambiguity.</p>")

s=s.replace(
 "<p class=\"meta\">One caution on method: a search for how many contacts share a given number returned all zeros, because a digits-only token search does not match numbers stored in parenthesised format. A check that returns nothing is not a check that found nothing — confirm the query works on a case you already know before trusting its silence.</p>",
 "<div class=\"callout bad\"><strong>Self-test every query before you trust its silence.</strong> A digits-only token search against a parenthesised stored number returns nothing, for every input, forever. That silence was twice read as a finding in this pass — once as \"no contact shares this number\" and once as \"no company owns this number\" — and the second one reached a written conclusion before it was caught. Run the query against a case whose answer you already know. If it cannot find that, it has told you nothing about anything else.</div>")

# Stage 1 caution about list-based completeness
s=s.replace(
 "<div class=\"callout warn\">\n    <strong>Completion is a property of the list, not of your loop.</strong>",
 "<div class=\"callout warn\">\n    <strong>Snapshot the intake membership before the first write, and keep it immutable.</strong> This process changes lead status and persona, and both are entry criteria — so its own writes eject records from the list it is working. On 5243 that removed 171 of 662 contacts before they were ever read, and only the intake snapshot makes them recoverable or even countable. Measure progress against live membership; measure <em>coverage</em> against the snapshot.\n  </div>\n  <div class=\"callout warn\">\n    <strong>Completion is a property of the list, not of your loop.</strong>")

open(p,'w').write(s)
print("doc corrected")
for probe in ("every one read on LinkedIn","none</em> of the 32","15 of 662"):
    print("  stale phrase still present? "+probe+" -> "+str(probe in s))
