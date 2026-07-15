# HubSpot Push Mechanics

This file documents the HubSpot Marketing Email API usage for pushing branded emails as drafts. All endpoints work with either the HubSpot MCP connector OR a Private App Token (PAT) with marketing-email scopes.

## Authentication

Two paths:

**Path A — HubSpot MCP** (preferred when available):
The MCP connector authenticates via OAuth tied to the user's account. No token needed. Use the connector's tools where they exist; fall back to direct API calls for endpoints the MCP doesn't expose (like the Marketing Email API).

**Path B — Private App Token (PAT)**:
The user generates a PAT in HubSpot Settings → Integrations → Private Apps. Required scopes:
- `content` (read/write marketing content)
- `crm.objects.marketing_events.read`
- `crm.lists.read` (to use existing recipient lists)
- `marketing.campaigns.read` and `marketing.campaigns.write` (to create + associate campaigns)
- `files` (to upload logo/asset images)

Pass it in the Authorization header: `Bearer pat-na1-...`

**Important security notes**:
- Don't paste the PAT into chat history — request it inline only when needed
- Remind the user to rotate the PAT after the work is done
- If pasted, treat it as expended after the session

## Step-by-step push process

### Step 1: Find the structural template email

You need a "winner" email to clone — its widget IDs and base structure become the template for new emails.

```
GET /marketing/v3/emails/{email_id}
```

Pick the email by ID (from the historical research step). Save its full JSON locally. You'll deep-copy this for each new email.

### Step 2: Build the email payload

Deep-copy the winner. Strip these fields (they would conflict with creation):

```python
import copy
payload = copy.deepcopy(winner_email)
for k in ['id', 'createdAt', 'updatedAt', 'publishDate', 'publishedAt',
          'publishedByEmail', 'publishedById', 'publishedByName',
          'isPublished', 'state', 'previewKey',
          'campaign', 'campaignName', 'campaignUtm',
          'primaryEmailCampaignId', 'allEmailCampaignIds',
          'clonedFrom', 'createdById', 'updatedById']:
    payload.pop(k, None)
```

Set the new email's identity:

```python
payload['name'] = 'Internal Name (visible in email list)'
payload['subject'] = 'Subject line that recipients see'
payload['state'] = 'DRAFT'
```

### Step 3: Update widgets

Each widget in `payload['content']['widgets']` is a dict you can modify in place. Key widgets:

```python
widgets = payload['content']['widgets']

# Preview text
widgets['preview_text']['body']['value'] = 'Preview text here'

# Header logo (image_email widget — DO NOT put HTML here)
widgets['module-0-0-0']['body']['img']['src'] = LOGO_URL
widgets['module-0-0-0']['body']['img']['width'] = LOGO_WIDTH
widgets['module-0-0-0']['body']['img']['height'] = LOGO_HEIGHT
widgets['module-0-0-0']['body']['hs_enable_module_padding'] = False

# Body (rich_text widget — full inline-styled HTML goes here)
widgets['module-1-0-0']['body']['html'] = body_html

# CTA button
btn = widgets['module_17472322758541']['body']
btn['text'] = 'Button Text →'
btn['link_to'] = 'url'
btn['destination'] = MEETING_URL_OR_OTHER
btn['file'] = None
btn['meeting_field'] = MEETING_URL  # if it's a meeting link
btn['page_field'] = None
btn['background_color'] = '#c4a44a'
btn['font_style'] = {
    "color": "#ffffff", "font": "DM Sans, Arial, sans-serif",
    "size": {"units": "px", "value": 16},
    "styles": {"bold": True, "font-weight": "bold"}
}

# Signature/footer block
widgets['module_17540506686871']['body']['html'] = signature_html
```

### Step 4: Set the section background (header bar)

```python
for s in payload['content']['flexAreas']['main']['sections']:
    if s['id'] == 'section-0':
        s['style'] = {
            'backgroundColor': '#181844',  # match the logo's navy
            'backgroundType': 'CONTENT',
            'paddingBottom': '0px',
            'paddingTop': '0px'
        }
```

### Step 5: Set recipient lists

Use the lists from the winner email by default:

```python
payload['to'] = {
    'contactIds': {'exclude': [], 'include': []},
    'contactIlsLists': {
        'exclude': [],
        'include': ['323', '388', '442']  # winner's ILS list IDs
    },
    'contactLists': {
        'exclude': [],
        'include': ['249', '310', '361']  # winner's legacy list IDs
    },
    'suppressGraymail': True
}
```

To leave recipients unset (user picks in UI), use empty include arrays.

### Step 6: Set the send date (optional)

```python
payload['publishDate'] = '2026-04-22T14:00:00Z'  # ISO format, UTC
payload['sendOnPublish'] = True  # when user hits publish, it sends at publishDate
```

For the QBS default cadence (Wednesdays 9am CT = 14:00 UTC during CDT), use:

```python
from datetime import datetime, timedelta, timezone

def next_wednesday_9am_ct(start_date):
    d = start_date
    while d.weekday() != 2:  # 2 = Wednesday
        d += timedelta(days=1)
    return d.replace(hour=14, minute=0, second=0, microsecond=0)

first_send = next_wednesday_9am_ct(datetime.now(timezone.utc))
send_dates = [first_send + timedelta(weeks=i) for i in range(num_emails)]
```

### Step 7: POST to create

```python
import subprocess, json
cmd = ['curl', '-s', '-X', 'POST', 'https://api.hubapi.com/marketing/v3/emails/',
       '-H', f'Authorization: Bearer {TOKEN}',
       '-H', 'Content-Type: application/json',
       '-d', json.dumps(payload)]
r = subprocess.run(cmd, capture_output=True, text=True)
result = json.loads(r.stdout)
email_id = result['id']
```

If creation succeeds, the response contains the new email's full object including its `id`. Save the ID for verification + campaign association.

### Step 8: Create or attach to a campaign

Create a new campaign:

```python
campaign_payload = {
    "properties": {
        "hs_name": "Campaign Name",
        "hs_start_date": "2026-04-22",
        "hs_end_date": "2026-09-23",
        "hs_goal": "Drive consultations from B2B audience.",
        "hs_audience": "Marketing Contacts (~5,500)"
    }
}
# POST /marketing/v3/campaigns → returns {id: '...'}
```

Associate each email to the campaign:

```python
# PUT /marketing/v3/campaigns/{campaign_id}/assets/MARKETING_EMAIL/{email_id}
# Returns 204 on success
```

### Step 9: Verify everything

After creating all emails, fetch each by ID to confirm it persisted correctly:

```python
for email_id in created_ids:
    r = subprocess.run(['curl', '-s',
        f'https://api.hubapi.com/marketing/v3/emails/{email_id}',
        '-H', f'Authorization: Bearer {TOKEN}'], capture_output=True, text=True)
    j = json.loads(r.stdout)
    assert j.get('id') == email_id
    assert j.get('state') == 'DRAFT'
```

Don't skip this — the API can occasionally fail silently with DNS issues during heavy bursts. Verifying catches the false successes.

## Common pitfalls

**1. DNS cache overflow during burst creation.**
If you're creating 20+ emails in rapid succession, expect occasional `DNS cache overflow` errors. Solution: add `time.sleep(0.5)` between requests, retry failures after a 10-second wait, and always verify by fetch after the batch completes.

**2. Widget content getting silently sanitized.**
If you put HTML inside an `image_email` widget, HubSpot strips it. Always use the right widget type for the content (image widget for images, rich_text for HTML).

**3. Style settings reverting to defaults.**
HubSpot's editor sometimes overrides custom style settings on save. Apply the styles inline (in the HTML itself) as well as in the `styleSettings` object — belt and suspenders.

**4. Send dates not appearing in the UI.**
Setting `publishDate` doesn't auto-schedule. The user must still click Schedule in the UI. The date is just a placeholder showing your suggested time. Mention this in the final summary.

**5. Recipient lists not transferring.**
Both legacy `contactLists` and v3 `contactIlsLists` arrays need to be populated for full coverage. Some HubSpot accounts only show one or the other in the UI, but it's safest to populate both with the same list IDs.

**6. Image URLs returning 404 in production.**
Test every image URL before pushing emails. HubSpot file manager URLs can be temporarily inaccessible during file processing. Use this check:

```python
import subprocess
r = subprocess.run(['curl', '-s', '-o', '/dev/null',
    '-w', '%{http_code}', image_url], capture_output=True, text=True)
assert r.stdout.strip() == '200', f'Image not accessible: {image_url}'
```

## What the user sees after success

After the push completes, the user should be able to:

1. Open HubSpot → Marketing → Email → Drafts
2. Filter by the campaign name OR by name prefix
3. See all created emails grouped together
4. Click any email to review and edit
5. Click Schedule when ready (the suggested send date is pre-set)

Provide direct edit links in the final summary:
```
https://app.hubspot.com/email/{HUB_ID}/edit/{email_id}
```

The `HUB_ID` for QBS is `20682069`. For client work, get the Hub ID from the HubSpot account or from the API response:
```
GET /account-info/v3/details
```
