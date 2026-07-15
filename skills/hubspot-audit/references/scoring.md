# Scoring Rubric (Computed, Defensible)

Every dimension score is **computed**, not asserted. This file defines the exact deduction table per dimension. The score appears in the deliverable alongside a "Score Calculation Detail" appendix that shows every deduction applied.

## Principles

1. **Start at 100.** A portal with no findings scores 100.
2. **Deduct per finding severity** — see values below.
3. **High-signal feature utilization contributes.** From the feature matrix, each Scored feature that is in-tier but not used well deducts from the relevant dimension.
4. **Floor at 0, cap deductions at −100.**
5. **Overall score = minimum of the six dimension scores.** Not an average. Strategic health cannot exceed the weakest link.
6. **Every deduction is logged** — the deliverable's Appendix D lists every deduction with its source finding/feature.

## Deduction values

| Severity | Finding deduction | Feature non-use deduction (if Scored) |
|---|---|---|
| Critical | −15 | −12 |
| High | −8 | −5 |
| Medium | −3 | −2 |
| Low | −1 | −1 |

Cap total deductions at −100. Floor at 0.

## Double-counting prevention

When a feature matrix entry and an explicit finding describe the same underlying issue, **apply the finding deduction and skip the matrix deduction** for that feature. The matrix deduction exists for features that are unused but haven't produced an explicit finding (often because the feature's non-use is a passive cost rather than an active problem worth calling out).

Example: "0 buying roles on open deals" surfaces as Critical finding 1.2 (−15 in Data Health) AND as feature SH-04 used_well=no (−12 in Data Health). Apply only the finding, not both.

When in doubt: if you wrote an explicit finding for it, the finding wins and the matrix entry is marked as "covered by finding X.Y" in the calculation detail appendix.

## Bands

| Score | Band | Meaning |
|---|---|---|
| 85–100 | Healthy | Well-maintained |
| 70–84 | Good | Cleanup warranted, no urgent risk |
| 50–69 | Degraded | Meaningful work needed |
| 30–49 | Poor | Significant issues |
| 0–29 | Critical | Active drag on business |

---

## Data Health dimension — deduction rubric

Starting score: 100.

### Automatic-critical triggers (−15 each)

- Marketing Contact count ≥90% of tier ceiling (billing risk)
- Contact dupe rate >5%
- `hs_analytics_source` null on >30% of contacts created in last 365d
- <40% of open deals have a Decision Maker identified via buying role
- No ICP property exists OR <40% fill on active customers
- Close reason fill rate <50% OR reasons are unstructured free-text
- Commission data integrity gaps (owner instability >15% on deals, close-date drift common) — only if commission is run off HubSpot data

### High-severity deductions (−8 each)

- Contact dupe rate 3–5%
- Company dupe rate (by domain) >5%
- Contact phone fill <30%
- Contact job title fill <30% (weighted higher if persona framework exists)
- Orphan deals (no associated contact) >15%
- Stale marketing contacts >35%
- Lifecycle stage regression events >50/month
- Recent contacts missing required fields (>40% missing)
- Lead leakage at 7 days >25% of MQLs
- Deal `amount` null on >50% of open deals

### Medium deductions (−3 each)

- Lists graveyard — >100 static lists with no activity
- Lifecycle stage null on 10–25% of contacts
- Duplicate lists with same semantic meaning
- Company source attribution (null) >50%
- `hs_analytics_source` null on 15–30% of contacts
- Deal type property <10% fill
- Invalid email formats >2% of sampled contacts

### Low deductions (−1 each)

- 2017-era CSV import lists still present
- Small duplicate property count
- Properties with 0 fills and no references (per property, capped at −5 total)

### Feature contributions from matrix

If the portal has the relevant tier but doesn't use well:
- Data quality workflows (OH-02) not configured: −5
- Forms (MH-02) exist but source preservation not configured: −5
- Attribution setup (MH-07) incomplete: −5 (in-tier) / −12 (if model entirely absent)

---

## Architecture dimension — deduction rubric

Starting score: 100.

### Automatic-critical triggers (−15 each)

- Pipeline-per-rep anti-pattern (5+ deal pipelines with <50 deals each)
- Sales methodology claimed by leadership but zero structural embedding
- Zero structural evidence of sales-marketing alignment
- Target Accounts enabled but >1000 companies flagged (no discipline)

### High-severity deductions (−8 each)

- Contact property sprawl: >300 total OR >180 custom
- Company property sprawl: >200 total OR >130 custom
- Deal property sprawl: >150 total OR >90 custom
- 5+ deal pipelines with reasonable counts (still too many)
- Stage design issues (stages with 0 deals in 180d, probabilities not monotonic)
- No custom lifecycle stage on a portal with evident complexity (Pro+)
- Team structure flat on 30+ seat portal
- Super admin count >5
- Deactivated users still owning >10% of active records
- Methodology partially embedded (fields exist but not consistently)
- Target Accounts enabled but <10 flagged (dormant)

### Medium deductions (−3 each)

- Contact property sprawl: 150–300 total
- Company property sprawl: 100–200 total
- Deal property sprawl: 80–150 total
- Lists 150–500 with orphans 15–35%
- Orphan properties (per 20 orphans, capped at −9)
- No association labels on Contact↔Company (Pro+ available)
- Custom properties with 0 fills (per 20 dead fields, capped at −6)

### Low deductions (−1 each)

- Property naming inconsistency (mixed conventions)
- Internal names exposed in UI

### Feature contributions from matrix

- Custom objects architecture not used where industry-appropriate (e.g., dealer-channel without equipment/contracts objects): −5
- Lifecycle stage custom additions not used (Pro+): −2

---

## Adoption dimension — deduction rubric

Starting score: 100.

### Automatic-critical triggers (−15 each)

- <60% active user rate (login last 30d)
- <40% of sales reps with any call logged in last 30d (Call Black Hole)
- Managers not using dashboards (<1 view in 30d by managerial users)
- Target Accounts enabled but <30% of flagged accounts have activity in 30d (ABM Theater)
- Methodology fields <40% fill rate on post-qualification deals
- Pipeline concentrated on a single user (>90% of open deals one-owned)
- For field-heavy teams: <40% mobile usage among field reps

### High-severity deductions (−8 each)

- Active user rate 60–75%
- Activity volume <15 engagements/week/rep for sales reps
- >30% of seats inactive
- <50% of sales reps have active meeting link
- Sequence adoption <40% of reps enrolling in 30d
- >40% of workflows have 0 enrollments in 90d (ghost workflows)
- Task completion rate <60% OR overdue >30%
- Zero AI features adopted on Pro+ portal
- Deactivated users still owning records

### Medium deductions (−3 each)

- Active user rate 75–85%
- Activity volume 15–40/week
- Ghost sequences 20–40%
- Knowledge base articles stale (not updated in 180d)

### Low deductions (−1 each)

- Low template/snippet sharing
- Mobile app unused among non-field roles (less critical)

### Feature contributions from matrix

Key scored features that deduct when in-tier but unused:
- HubSpot Calling or dialer (SH-01/02) not used well: −12
- Sequences (SH-05) ghost: −5
- Playbooks (SH-06) not used: −3
- Meeting scheduler (SH-07) not used: −5
- Coaching playlists (SH-09) not used despite Enterprise: −5
- Forecast tool (SH-08) not used: −5
- Marketing emails (MH-01) sent but irregular: −3
- Tickets (SVH-01) unused despite Service Hub: −3

---

## Automation dimension — deduction rubric

Starting score: 100.

### Automatic-critical triggers (−15 each)

- Any workflow erroring for >30 days with side effects
- Re-enrollment + goal property collision workflow (active harm)
- Lead routing to deactivated users
- No deal progression safety nets on a portal with clear stall problem

### High-severity deductions (−8 each)

- Workflows in error 1–3 for >7 days
- Orphan workflows >30% of active
- Workflows without exit criteria (contacts accumulating)
- No data hygiene workflows
- Notification spam risk (>50/day per user)
- Workflow emails without frequency capping
- Multiple workflows setting the same lifecycle stage with different logic
- No lead follow-up automation (no MQL cadence, no reassignment on no-response)

### Medium deductions (−3 each)

- Workflows with duplicate semantic meaning
- Unnamed / poorly named workflows (per 5 workflows, capped at −9)
- Custom code actions without error handling (Ops Pro+)
- Data sync errors in last 30d (Ops Hub)

### Low deductions (−1 each)

- Workflow count >200 without governance

### Feature contributions from matrix

- SLAs (SVH-02) not configured despite Service Pro+: −5
- Programmable automation (OH-03) not used despite Ops Pro+: −3
- Data sync (OH-01) errors: −5 per problematic sync

---

## Integrations dimension — deduction rubric

Starting score: 100.

### Automatic-critical triggers (−15 each)

- Dual-engagement logging (Zoom + Read AI, Gong + Chorus, etc.)
- Disconnected apps with active references still in workflows/lists
- API quota near daily limit (>90%)
- <70% of reps at full role-appropriate engagement coverage
- Any calling rep without a dialer integration (ties to Call Black Hole)

### High-severity deductions (−8 each)

- Integration errors on recent syncs
- Private apps with overbroad scopes (admin where read-only sufficient)
- Webhooks with high failure rates
- Users with no inbox OR no calendar connected
- Contact creation source attribution dominated by one integration with data quality issues

### Medium deductions (−3 each)

- Apps installed but showing no recent data flow
- Calendar sync on <70% of reps
- Ad accounts (MH-08) not connected when marketing runs ads
- Social accounts (MH-09) partially connected

### Low deductions (−1 each)

- Marketplace apps installed but dormant (per 3 dormant apps, capped at −3)

### Feature contributions from matrix

- Ad accounts (MH-08) in-tier but not connected: −5
- Social accounts (MH-09) in-tier but not connected: −5
- Data sync two-way (OH-01) in-tier but absent: −3

---

## Reporting dimension — deduction rubric

Starting score: 100.

### Automatic-critical triggers (−15 each)

- Missing >3 of the "Revenue Core 8" metrics (pipeline snapshot, pipeline trend, closed won MTD/QTD/YTD, win rate by rep, win rate by source, avg cycle length, avg deal size, forecast accuracy)
- No exec dashboard
- Fewer than 3 of the "Efficiency Core 10" metrics present
- Attribution model entirely absent
- Target Accounts enabled with no ABM dashboard
- ICP property exists but zero reports segment by it

### High-severity deductions (−8 each)

- No win/loss dashboard or loss reasons never aggregated (Win/Loss Amnesia)
- No forecast accuracy tracking
- Dashboard sprawl >40 dashboards with >60% unviewed in 30d
- Missing 1–3 of Revenue Core 8
- Attribution model selected but inappropriate for sales cycle
- No scheduled report emails to leadership

### Medium deductions (−3 each)

- Dashboard sprawl 15–40 OR 30–60% unviewed
- Orphan reports >30% of report library
- Forecast tool unused (Pro+)
- Goals tool unused (free)
- Reports relying on stale/broken data fields

### Low deductions (−1 each)

- Unused custom report capacity
- No cross-object reporting (Pro+ capability)

### Feature contributions from matrix

- Datasets (OH-04) unused despite Ops Enterprise: −3
- Feedback surveys (SVH-05) unused despite Service Pro+: −3

---

## Calculation output format

Every audit produces a per-dimension calculation record that appears in Appendix D of the deliverable:

```yaml
dimension: adoption
starting_score: 100
deductions:
  - source: finding
    id: 3.1
    severity: critical
    reason: "Pipeline ownership concentrated on a single user"
    amount: -15
  - source: finding
    id: 3.2
    severity: critical
    reason: "Call logging gap — <40% of reps logged a call in 30d"
    amount: -15
  - source: finding
    id: 3.3
    severity: high
    reason: "5 of 11 owner seats inactive"
    amount: -8
  - source: feature_matrix
    id: SH-01
    reason: "HubSpot Calling in-tier but not used well"
    amount: -12
  - source: feature_matrix
    id: SH-05
    reason: "Sequences in-tier but no enrollments in 90d"
    amount: -5
  - source: feature_matrix
    id: SH-07
    reason: "Meeting scheduler in-tier but <50% rep adoption"
    amount: -5
total_deductions: -60
final_score: 40
band: Poor
```

This gets rendered in the Word doc as a two-column table (Reason | Deduction) with the total at the bottom. Every number in the doc is traceable.

## Overall portal health

Overall = minimum of six dimension scores. Narrative sentence alongside:

- 85–100: "A well-maintained portal with only minor optimization opportunities."
- 70–84: "Fundamentally sound with cleanup opportunities in [limiting dimension]."
- 50–69: "Operational but leaking value; concentrated problems in [dimensions]."
- 30–49: "Significant drag on revenue operations; critical issues require immediate attention."
- 0–29: "Portal is actively counterproductive; without remediation, additional HubSpot investment compounds the problems."

Limiting dimension is explicitly named.

## Maturity capability scoring — separate

RevOps Maturity staging (5 capabilities × 5 stages) is NOT computed numerically. It's assigned by evaluating against the stage criteria in `revops_maturity.md`. Each capability's stage is the highest stage where ALL Stage N criteria are met. See that file for rubric.

Overall maturity = minimum of the five capability stages.
