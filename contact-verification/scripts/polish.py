p='verification-process.html'
s=open(p).read()
before=len(s)
def sub(old,new,label):
    global s
    if old not in s: print("  ANCHOR MISSING: "+label); return False
    s=s.replace(old,new,1); print("  ok: "+label); return True

# ── STAGE 2: the profile read was missing account_id, the provider, and the allowlist ──
sub("""<pre>POST /api/v1/linkedin/search?account_id={acct}&amp;limit=5
  {"api":"classic","category":"people","keywords":"Firstname Lastname Company"}
GET  /api/v1/users/{public_identifier}?linkedin_sections=experience_preview</pre>""",
"""<pre>POST /api/v1/linkedin/search?account_id={acct}&amp;limit=5
  {"api":"classic","category":"people","keywords":"Firstname Lastname Company"}
GET  /api/v1/users/{identifier}?account_id={acct}&amp;linkedin_sections=experience_preview</pre>
  <div class="callout bad">
    <strong>Whose LinkedIn account reads the profile is not a detail.</strong> Both calls require
    <code>account_id</code>, and only the accounts belonging to your own team are authorised. A
    connected-accounts list will also contain <em>client</em> identities; reading prospect profiles
    through a client's LinkedIn account is not a recoverable mistake. Keep an explicit allowlist in
    the run config and fail closed on anything outside it.
  </div>
  <p class="meta">Identifier hygiene, each learned by a 400 or a wrong answer: strip
  <code>?trk=…</code> tracking parameters; URL-encode non-ASCII (<code>ñ</code> →
  <code>%C3%B1</code>); never send <code>*experience</code> as the section name. And read every
  property that might hold a profile URL, not just one — a portal typically carries several
  (<code>hs_linkedin_url</code>, a Hublead public identifier, a vendor's LinkedIn URL field). Reading
  one field is how 30 contacts got silently skipped on the first pass of this process.</p>""",
"Stage 2 account_id + allowlist + identifier hygiene")

# ── STAGE 5: independent / fractional / retired must NOT be re-associated ──
sub("""    <li><strong>Find or create the company record.</strong> Search by <code>domain EQ</code> first.</li>""",
"""    <li><strong>Decide whether there is a destination at all.</strong> Not every mover goes to a
      company you should create. Someone who went independent, took a fractional or advisory seat,
      is between roles, or retired has no employer to re-associate to — record the destination in
      the evidence field, leave the verdict <code>no</code>, and set the lead status to reflect it.
      Creating a company record for a one-person practice fills the CRM with junk and, worse,
      promotes a non-buyer onto the calling list.</li>
    <li><strong>Disambiguate before you move anyone.</strong> A changed email domain looks like a
      job change and usually isn't — on one list, 37 of 49 domain mismatches were aliases or former
      names, not moves. And never choose between same-named company records: where several exist,
      suppress and queue rather than guess.</li>
    <li><strong>Find or create the company record.</strong> Search by <code>domain EQ</code> first.
      Take the domain from the LinkedIn company page so the record is matchable later — never
      create a name-only stub.</li>""",
"Stage 5 no-destination + disambiguation")

# ── EMAIL LADDER: bounce history outranks the verifier; first-party address wins ──
sub("""    <h3>Rung 1 · Look in the record you already have</h3>""",
"""    <h3>Rung 0 · Bounce history outranks the verifier</h3>
    <p>Before spending a credit, read what the CRM already knows about deliverability — the hard
    bounce reason, any sending tool's bounce flag, a stored verification result. A bounce is ground
    truth and no verifier overrides it: tested against three addresses that had genuinely
    hard-bounced, the verifier returned <em>valid</em> for two of them. Never re-check an address you
    already hold bounce data for, and never let a <code>valid</code> overturn a recorded bounce.</p>

    <h3>Rung 1 · Look in the record you already have</h3>""",
"Email rung 0 bounce history")

sub("""    <h3>Rung 2 · Learn the company's format from a colleague you already trust</h3>""",
"""    <p>Two more fields worth reading at this rung, because they answer part of the question for
    free: a vendor's own stored verification status, and its "email matches company name" flag. And
    if the person's LinkedIn contact info block carries a published address on the confirmed domain,
    <strong>prefer it over anything derived</strong> — it is first-party. On this pass a
    self-published <code>gwen.lamar@</code> beat a vendor's <code>gwendolyn.lamar@</code> when both
    verified.</p>

    <h3>Rung 2 · Learn the company's format from a colleague you already trust</h3>""",
"Email first-party preference")

sub("""    <p>Verification returns four answers, and they are not shades of one thing:</p>""",
"""    <div class="callout">
      <strong>Normalise the name before building a candidate.</strong> Decompose to ASCII, strip
      everything that is not a letter, lowercase. Without that step an apostrophe or an accent
      produces a malformed address — a derivation routine on an earlier run crashed on
      <em>O'Dell</em>, and in a bulk run it would have silently skipped every O'Brien, O'Neill and
      D'Angelo on the list. Skip contacts whose name does not yield two usable tokens rather than
      guessing at a single-token name.
    </div>
    <p>Verification returns four answers, and they are not shades of one thing:</p>""",
"Email name normalisation")

# ── NEW SECTION: write vocabulary + the output list definition ──
NEWSEC = """
<section>
  <span class="num">VOCABULARY</span>
  <h2>What gets written, in exactly which words</h2>
  <div class="col">
    <p>A verdict is only as useful as the field it lands in, and this is where a re-runner can do
    real damage by inventing a value. Every string below is literal.</p>
  </div>

  <h3>The verification properties</h3>
  <dl class="kv">
    <dt>ai__li_still_at_company</dt><dd><code>yes</code> · <code>no</code> · <code>unreadable</code> — the routing decision</dd>
    <dt>ai__contact_evidence</dt><dd>What was read, where, and the caveat a rep needs. Also carries the persona-exclusion marker. <strong>Append-only</strong> — see the warning below.</dd>
    <dt>ai__contact_verified_date</dt><dd>Date type, <code>YYYY-MM-DD</code>. The <em>actual</em> write date, never a constant.</dd>
    <dt>ai__sources_confirming</dt><dd>How many independent sources actually agreed. Not a constant.</dd>
    <dt>ai__li_recent_role_change</dt><dd><code>yes</code> · <code>no</code></dd>
    <dt>ai__li_tenure_years</dt><dd>Number, from the current row's start date</dd>
    <dt>ai__email_information</dt><dd>The email narrative: what was replaced, what verification said, how much to trust it</dd>
    <dt>previous__email</dt><dd>A prior employer's address. Never clobber an existing value.</dd>
    <dt>previous__company_domain_name</dt><dd><strong>URL type</strong> — prefix <code>https://</code> or it rejects with <code>INVALID_URL</code></dd>
  </dl>

  <h3>Lead status — the exact enum, and the one you must not touch</h3>
  <div class="tblwrap">
    <table>
      <thead><tr><th>Finding</th><th>Write this literal value</th><th class="n">Used</th></tr></thead>
      <tbody>
        <tr><td>Confirmed at a different employer</td><td class="m">No Longer with Company</td><td class="n">153</td></tr>
        <tr><td>Moved, destination ambiguous or fractional</td><td class="m">Need Updated Info</td><td class="n">36</td></tr>
        <tr><td>Retired</td><td class="m">Retired - Remove from All Lists</td><td class="n">5</td></tr>
        <tr><td>Employed, but cannot buy</td><td class="m">Not Decision Maker</td><td class="n">4</td></tr>
        <tr><td><strong>Confirmed still there</strong></td><td><strong>write nothing — leave it alone</strong></td><td class="n">—</td></tr>
      </tbody>
    </table>
  </div>
  <div class="callout bad">
    <strong>Never normalise the lead status of a contact you just confirmed.</strong> The calling
    list requires <code>ConnectandSell Prospect</code>. Rewriting a confirmed contact's status —
    even to something that reads better — ejects the person you just verified from the list you are
    building. The portal enum offers two dozen values; only the four above are outputs of this
    process.
  </div>

  <h3>The evidence field has one writer's worth of room and several writers</h3>
  <div class="callout warn">
    Roughly 1,000 characters, hard truncated. On this pass the verdict writer <em>overwrote</em> the
    field while every later phase <em>appended</em> to it — which is why 22 of 70 movers lost the
    marker two production lists filter on, and why a repair script had to exist. Make every write
    append, give each phase a size budget, put markers in <strong>dedicated typed properties</strong>
    rather than prose, and run any marker re-stamp <em>after</em> the last verdict write.
  </div>

  <h3>Properties this process must not write</h3>
  <ul>
    <li><code>jobtitle</code> — three systems already fight over it at roughly 38% oscillation; a
      write was observed reverting within seconds. The real title belongs in the evidence field.</li>
    <li><code>hs_persona</code> — see the next section. Proposals only.</li>
    <li><code>mobilephone</code> — a mobile follows the person, not the employer.</li>
    <li>Anything on a contact outside the intake snapshot.</li>
  </ul>
</section>

<section>
  <span class="num">OUTPUT</span>
  <h2>The calling list, defined</h2>
  <div class="col">
    <p>The process produces a second, derived dynamic list — the one reps actually work. It is worth
    stating its clauses exactly, because three of the four are properties this process writes, which
    means the process can remove people from its own output.</p>
  </div>
  <div class="tblwrap">
    <table>
      <thead><tr><th>Clause</th><th>Filter</th><th>Note</th></tr></thead>
      <tbody>
        <tr><td class="n">1</td><td class="m">ai__li_still_at_company IS_ANY_OF [yes]</td><td>confirmed current</td></tr>
        <tr><td class="n">2</td><td class="m">hs_lead_status IS_ANY_OF [ConnectandSell Prospect]</td><td>this is why clause 2 of the vocabulary table matters</td></tr>
        <tr><td class="n">3</td><td class="m">ai__contact_evidence DOES_NOT_CONTAIN &lt;exclusion token&gt;</td><td><strong>must set includeObjectsWithNoValueSet: true</strong>, or every contact with an empty evidence field drops out</td></tr>
        <tr><td class="n">4</td><td class="m">IN_LIST &lt;source list id&gt;</td><td>inherits the whole source ICP — the coupling that hides verified people</td></tr>
      </tbody>
    </table>
  </div>
  <p class="meta">Clause 4 is the one to think hardest about. It keeps the calling list honest to the
  campaign's ICP, and it is also why re-associating a mover can make them vanish: they leave the
  source list, so they leave this one. Decide deliberately whether your output should inherit the
  source ICP or stand on the verification evidence alone.</p>
</section>

<section>
  <span class="num">PERSONA</span>
  <h2>Persona: the largest destructive write, and the one to default off</h2>
  <div class="col">
    <p>On this pass, correcting <code>hs_persona</code> removed <strong>105 of the 324</strong>
    contacts that left the source list — more than any cause except the verdicts themselves. Those
    removals were right: the records were analysts, sales directors, a COO, a marketing specialist,
    people who were never marketing buyers and had been mis-personad into the campaign. But it is a
    write to a targeting property, it is the second-largest thing this process does, and it deserves
    to be named as a stage rather than appear as a number in a table.</p>
  </div>
  <div class="callout bad">
    <strong>In an unattended run this defaults to off, and produces proposals.</strong> A persona
    re-map changes who is in the campaign. Emit the proposed change with the title that justifies it
    and let a human approve the set.
  </div>
  <h3>What makes it treacherous</h3>
  <ul>
    <li><strong>Multiple persona workflows race each other.</strong> Expect a value you write to be
      re-decided. Verify by reading back.</li>
    <li><strong>The workflow that assigns "does not match persona" only fires on a BLANK persona.</strong>
      A wrong persona is therefore stable — nothing will correct it for you, and nothing will
      correct yours either.</li>
    <li><strong>Persona is title-driven, so it survives a job change at the same title.</strong> If
      movers are dropping out of a persona-gated list, persona is probably not the reason — check
      which criterion actually failed before concluding anything.</li>
  </ul>
</section>
"""
sub('<section>\n  <span class="num">FAILURE MODES</span>', NEWSEC + '\n<section>\n  <span class="num">FAILURE MODES</span>',
    "new VOCABULARY / OUTPUT / PERSONA sections")

# ── STAGE 7: read-back verification and calculated-field lag ──
sub("""  <div class="callout">
    <strong>The lead-status workflow is not fighting you.</strong>""",
"""  <div class="callout bad">
    <strong>Verify every write by reading it back.</strong> A batch update returns
    <code>COMPLETE</code> with zero errors and can still not apply. Diff the ids you requested
    against the ids returned, then re-read the records. Every self-check in this process exists
    because a write that reported success had not landed.
  </div>
  <div class="callout warn">
    <strong>Calculated fields lag — do not mistake that for failure.</strong>
    <code>associatedcompanyid</code> can take 20 seconds or more to reflect a new association. Read
    it too early, see it empty, and you will "repair" a write that worked. Re-read before concluding
    anything failed. Related limit: a batch read will not accept
    <code>propertiesWithHistory</code> at 100 records — drop to 25 per call or the whole response
    comes back null. Property history is the only way to catch two systems fighting over one field,
    so this matters more than it looks.
  </div>
  <div class="callout">
    <strong>The lead-status workflow is not fighting you.</strong>""",
    "Stage 7 read-back + calculated field lag")

# ── the write endpoints, absent entirely ──
sub("""<section>
  <span class="num">NEXT LIST</span>""",
"""<section>
  <span class="num">ENDPOINTS</span>
  <h2>Every call this process makes</h2>
  <div class="col">
    <p>The reads are scattered through the stages above; the writes were missing entirely. Limits
    shown are the ones that actually bite.</p>
  </div>
  <pre># READ
GET  /crm/v3/lists/{listId}                      ?includeFilters=true   → the list's real criteria
GET  /crm/v3/lists/{listId}/memberships          limit=250, page on paging.next.after
POST /crm/v3/objects/contacts/batch/read         100 ids max; 25 if asking for propertiesWithHistory
POST /crm/v3/objects/contacts/search             CONTAINS_TOKEN needs the stored format, not raw digits
POST /crm/v3/objects/companies/batch/read        100 ids max
POST /crm/v3/objects/companies/search            filter domain EQ

# WRITE
POST   /crm/v3/objects/contacts/batch/update     100 inputs max — chunk, then diff requested vs returned
PATCH  /crm/v3/objects/contacts/{id}             single-record writes
POST   /crm/v3/objects/companies                 create; find-or-create by domain or it mints duplicates
DELETE /crm/v4/objects/contacts/{cid}/associations/companies/{coid}
PUT    /crm/v4/objects/contacts/{cid}/associations/companies/{coid}
       body: [{"associationCategory":"HUBSPOT_DEFINED","associationTypeId":1},
              {"associationCategory":"HUBSPOT_DEFINED","associationTypeId":279}]
POST   /crm/v3/lists                             objectTypeId "0-1", processingType "DYNAMIC",
                                                 top-level OR branch wrapping AND sub-branches
POST   /crm/v3/properties/contacts               only when a genuinely new field is needed</pre>
  <p class="meta">Ordering constraints that are not optional, all learned by failure: both
  association typeIds in a single PUT; <code>hs_additional_emails</code> cleared before
  <code>email</code>; <code>https://</code> on the URL-typed previous-domain field; marker
  re-stamping after the last verdict write; and the phone carried inside the re-association
  transaction rather than swept up later.</p>
</section>

<section>
  <span class="num">NEXT LIST</span>""",
    "ENDPOINTS section")

open(p,'w').write(s)
print("\n"+str(before)+" -> "+str(len(s))+" chars")
