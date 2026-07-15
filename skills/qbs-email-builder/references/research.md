# Research Playbook

The single biggest predictor of email performance is whether the writing matches the company's voice. Generic AI emails fail because they sound like AI. Voice-matched emails feel like the company wrote them.

This file describes how to research a target company before writing a single line of copy.

## When the user gave a URL

Use `web_fetch` to pull these pages (in order):

1. **Homepage** — captures the headline, hero copy, primary value prop, and what they want visitors to do
2. **About / Company page** — captures their story, founders' voice, positioning vs. competitors
3. **Services / Products page** — captures the actual offerings and how they're framed
4. **Blog (most recent 2–3 posts)** — captures actual writing voice in long-form

Don't fetch more than 4–5 pages. The signal saturates quickly.

After fetching, identify and write down:

- **Primary value proposition** (what problem do they claim to solve)
- **Target audience language** (how do they describe their customers — by industry? size? job title?)
- **Voice characteristics** (formal vs. conversational; we/our vs. I; long sentences vs. short)
- **Active campaigns** (what are they promoting in their hero, banners, recent blog posts — those are top of mind for them)
- **CTA patterns** (do they push for demos, calls, downloads, free trials)

## When the user gave only a brief

Use `web_search` to find the company's website, then fall back to the URL workflow above.

If the company is too small or new to have searchable web presence, work directly from the brief and write more general POV-style emails.

## When HubSpot is connected (CRITICAL STEP)

This is the highest-leverage research step. Pull the company's existing email performance data and use the top performer as the **voice template**.

### How to pull historical emails

```python
import subprocess, json
TOKEN = '<the user's PAT or use HubSpot MCP>'

# Get aggregate stats and per-email performance for the last 24 months
import datetime
start = '2024-01-01T00:00:00Z'
end = datetime.datetime.now().strftime('%Y-%m-%dT00:00:00Z')

cmd = ['curl', '-s',
    f'https://api.hubapi.com/marketing/v3/emails/statistics/list?startTimestamp={start}&endTimestamp={end}&limit=100',
    '-H', f'Authorization: Bearer {TOKEN}']
r = subprocess.run(cmd, capture_output=True, text=True)
stats = json.loads(r.stdout)

# campaignAggregations contains per-campaign stats
# Sort by openratio + clickratio*5 to find the genuine top performers
ca = stats.get('campaignAggregations', {})
rows = []
for cid, data in ca.items():
    c = data.get('counters', {})
    delivered = c.get('delivered', 0)
    if delivered < 50:  # skip tests
        continue
    rows.append({
        'campaign_id': cid,
        'delivered': delivered,
        'open_rate': (c.get('open', 0) / delivered * 100),
        'click_rate': (c.get('click', 0) / delivered * 100),
    })

# Top performers
top = sorted(rows, key=lambda x: x['open_rate'] + x['click_rate']*5, reverse=True)[:5]
```

For each top campaign, fetch the campaign details to get the email IDs, then fetch each email's body content. The campaign endpoint:

```
GET /marketing/v3/campaigns/{campaign_id}
```

Returns `assets.MARKETING_EMAIL.results` — a list of `{id, name}` dicts. Fetch each email:

```
GET /marketing/v3/emails/{email_id}
```

The body content lives in `content.widgets['module-1-0-0'].body.html` (or similarly-named widget — inspect to find the largest text block).

### What to extract from the winner

Read the full body of the top 1–2 performers and identify:

- **Sentence length pattern** (short and punchy? long and explanatory?)
- **Use of "I" vs. "we"** (personal voice vs. corporate)
- **Framework patterns** (numbered lists, contrast pairs, quotes, statistics)
- **CTA style** (button + question? plain text? "Reply with..."?)
- **Signature treatment** (formal title block? casual one-liner?)
- **Subject line patterns** (questions? statements? lowercase? capitalized?)

This becomes the voice template that every new email matches.

### Critical: also pull the recipient list IDs

The winner email's `to.contactLists.include` and `to.contactIlsLists.include` arrays show which lists were used. New emails should use the same lists by default — these are the audiences that have already proven they engage with this company's content.

## When researching for client work

Same workflow as above, but additionally:

- **Don't apply QBS branding** to client emails. Adapt the design system to the client's brand colors and fonts (see `design-system.md`)
- **Watch for industry compliance constraints** (healthcare, financial services, legal — these have content restrictions)
- **Identify the client's competitors** — useful for positioning POVs without being directly comparative
- **Confirm the client owns the sender domain** before designing email sender addresses

## What "good research" output looks like

After research, you should be able to write a one-paragraph "company brief" that includes:

> [Company] sells [what] to [who]. Their voice is [tone characterization]. They emphasize [core value props]. Their best-performing email achieved [N]% open / [N]% CTR with the subject "[X]" — it used [framework type] with [voice characteristics]. New emails should match this voice and use lists [IDs] for recipients.

Drop this paragraph into context before writing emails. Reference it for every email you write.
