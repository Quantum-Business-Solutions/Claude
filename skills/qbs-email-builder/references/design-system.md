# Design System

The visual design of an email signals trust before the reader has read a word. A templated email looks templated; a designed email looks like the company put thought into it.

This file documents the QBS default design and how to adapt it for client work.

## QBS default design tokens

```python
# Colors
GOLD       = '#c4a44a'   # primary accent
NAVY_HEADER = '#181844'  # header bar (matches Quantum logo navy)
NAVY_FOOTER = '#101725'  # footer bar (slightly deeper for contrast)
BG          = '#fafaf7'  # page background (warm off-white)
WHITE       = '#ffffff'  # email body background
TEXT        = '#101725'  # body text
MUTED       = '#6b7280'  # secondary text (eyebrow, footer)
BORDER      = '#e6e4dc'  # subtle dividers

# Callouts (used sparingly)
CALLOUT_POS_BG     = '#faf7ec'  # warm gold-tinted bg for positive callouts
CALLOUT_NEG_BG     = '#faf0f0'  # warm red-tinted bg for limitation callouts
CALLOUT_NEG_ACCENT = '#c44a4a'  # red accent for warning callouts

# Fonts
BODY_FONT     = 'DM Sans, Arial, sans-serif'
HEADING_FONT  = 'Instrument Serif, Georgia, serif'

# Logo asset (already in HubSpot file manager)
LOGO_URL = 'https://20682069.fs1.hubspotusercontent-na1.net/hubfs/20682069/QUANTUM/IMAGES/Quantum%20Graphics%20and%20Logos/Quantum_Logo_Navy_Header_Cropped.jpg'
```

## Layout structure

Every QBS email follows this top-to-bottom structure:

```
┌──────────────────────────────────────┐
│   NAVY HEADER (logo, full-bleed)     │  ← navy bar with cropped Quantum logo
├──────────────────────────────────────┤
│ ━━━━━━━━━━━ gold accent ━━━━━━━━━━━ │  ← 3px gold stripe
├──────────────────────────────────────┤
│ EYEBROW LABEL                        │  ← small caps, 13px, muted
│                                       │
│ Headline in serif, 38px              │  ← Instrument Serif
│                                       │
│ [firstname],                          │
│                                       │
│ Body paragraphs in DM Sans, 17px,    │
│ 1.75 line-height, 140-180 words.     │
│                                       │
│ [Optional callout box]                │
│                                       │
│ Closing line / soft CTA question?    │
│                                       │
│       [ GOLD CTA BUTTON → ]           │  ← centered, 6px radius
│                                       │
│ ────────────── divider ──────────────│
│                                       │
│ Talk soon,                            │
│ Shawn Peterson (serif, 28px)          │  ← branded signature
│ Founder & CEO, Quantum Business Sol.  │
│ shawn@thequantumleap.business         │
│                                       │
│ ┌─ QUANTUM BUSINESS SOLUTIONS ─────┐ │
│ │ HubSpot Diamond · #1 ZoomInfo …  │ │  ← partner credentials card
│ └────────────────────────────────────┘ │
├──────────────────────────────────────┤
│ ━━━━━━━━━━━ gold accent ━━━━━━━━━━━ │
├──────────────────────────────────────┤
│   NAVY FOOTER (location + URL)       │  ← mirror of header
└──────────────────────────────────────┘
```

## HubSpot widget structure

QBS emails use the `@hubspot/email/dnd/Start_from_scratch.html` template with these widgets:

- `module-0-0-0` — header logo (image_email widget, navy logo full-bleed)
- `module-1-0-0` — body content (rich_text widget with eyebrow + headline + body all inline-styled)
- `module_17472322758541` — CTA button (button widget)
- `module_17540506686871` — signature + credentials + footer (rich_text widget with all inline-styled HTML)
- `preview_text` — preview text widget

The widget IDs above are stable references in HubSpot's email object model. Use them by name when patching.

## Critical rules to avoid breakage

1. **Never put custom HTML inside `module-0-0-0`.** It's an `image_email` widget — HubSpot will sanitize and strip your HTML, leaving `&nbsp;`. Use a proper image widget pointing at the logo URL instead.

2. **Apply ALL typography styling inline.** HubSpot's email editor strips most `<style>` blocks. Every `<p>`, `<h1>`, etc., needs full inline styles. Define a token dict at the top of your script and template the styles into the HTML.

3. **Always set `state: 'DRAFT'` and `isPublished: false` on creation.** You don't want the API to accidentally publish-and-send. Use `sendOnPublish: true` so the user can later schedule with one click.

4. **Strip these fields when cloning a template email:**
   ```python
   for k in ['id', 'createdAt', 'updatedAt', 'publishDate', 'publishedAt',
             'publishedByEmail', 'publishedById', 'publishedByName',
             'isPublished', 'state', 'previewKey',
             'campaign', 'campaignName', 'campaignUtm',
             'primaryEmailCampaignId', 'allEmailCampaignIds',
             'clonedFrom', 'createdById', 'updatedById']:
       payload.pop(k, None)
   ```

5. **Set the section-0 background color to match the header logo's navy** so the header looks edge-to-edge with no seam:
   ```python
   for s in content['flexAreas']['main']['sections']:
       if s['id'] == 'section-0':
           s['style'] = {
               'backgroundColor': '#181844',  # match logo navy
               'backgroundType': 'CONTENT',
               'paddingBottom': '0px',
               'paddingTop': '0px'
           }
   ```

## Adapting the design for client work

For client emails, keep the **structural design** (navy header pattern, eyebrow → serif headline → body → CTA → branded footer) but swap the **visual tokens**:

### Step 1: Identify the client's brand

From the client's website, identify:
- Primary brand color (often the dominant color on their homepage hero)
- Accent color (often the CTA button color)
- Heading font (inspect their `<h1>` font-family in DevTools)
- Body font (inspect their `<p>` font-family)
- Logo (download a high-res version for email use)

If the client has a brand guide, use that instead of inferring from the website.

### Step 2: Replace the tokens

```python
# Client tokens (example)
CLIENT_PRIMARY = '#1a3a8a'    # their navy
CLIENT_ACCENT  = '#ff6b35'    # their CTA orange
CLIENT_HEADING = 'Playfair Display, Georgia, serif'
CLIENT_BODY    = 'Inter, Arial, sans-serif'
CLIENT_LOGO    = 'https://files.example.com/logo-on-navy.png'
```

### Step 3: Upload the client's logo to their HubSpot file manager

Use the same approach as we did for the QBS logo — upload via the Files v3 API to a folder named after the client. Set `access: PUBLIC_INDEXABLE` so the image is accessible from email clients.

### Step 4: Use the client's existing best email as the structural reference

If the client has historical emails, fetch their top performer and use it as the cloning template (just like the QBS workflow). The voice match plus structural consistency makes the new emails feel native to their existing program.

## What NOT to change when adapting

These elements should stay constant regardless of client:

- The **navy-bar-with-logo** header pattern (any solid color header bar with the client's logo, gold-stripe equivalent in their accent color)
- The **eyebrow → serif headline → body** content hierarchy
- The **140–180 word body length** (this is a performance constraint, not a brand thing)
- The **single CTA pattern** (one button, centered, brand color)
- The **navy footer mirror of the header** (any solid footer bar matching the header style)

These structural choices are what make the design "designed" rather than templated — they don't depend on QBS's specific brand.
