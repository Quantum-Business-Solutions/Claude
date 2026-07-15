"""
push_email.py

Reusable function for pushing a single branded email draft into HubSpot.

Usage:
    from push_email import push_email_draft

    result = push_email_draft(
        token='pat-na1-...',
        winner_template_path='/tmp/winner_email.json',  # cached winner JSON
        config={
            'name': 'Internal Name',
            'subject': 'Subject Line',
            'preview': 'Preview text',
            'eyebrow': 'A POV from Shawn Peterson',
            'headline': 'The headline in serif',
            'body_html': '<p>...</p><p>...</p>',  # body paragraphs only
            'cta_text': 'Book a Call',
            'cta_url': 'https://meetings.hubspot.com/...',
            'send_date_iso': '2026-04-22T14:00:00Z',  # optional
            'recipient_lists': {  # optional; defaults to winner's lists
                'contactLists': ['249', '310'],
                'contactIlsLists': ['323', '388'],
            },
            'design_tokens': {  # optional; defaults to QBS brand
                'gold': '#c4a44a',
                'navy_header': '#181844',
                'navy_footer': '#101725',
                'bg': '#fafaf7',
                'text': '#101725',
                'muted': '#6b7280',
                'border': '#e6e4dc',
                'body_font': 'DM Sans, Arial, sans-serif',
                'heading_font': 'Instrument Serif, Georgia, serif',
                'logo_url': 'https://...',
            }
        }
    )
    # result = {'success': True, 'email_id': '...', 'edit_url': '...'}
"""
import json
import subprocess
import copy
import re
import time


# QBS default design tokens
DEFAULT_TOKENS = {
    'gold': '#c4a44a',
    'navy_header': '#181844',
    'navy_footer': '#101725',
    'bg': '#fafaf7',
    'white': '#ffffff',
    'text': '#101725',
    'muted': '#6b7280',
    'border': '#e6e4dc',
    'body_font': 'DM Sans, Arial, sans-serif',
    'heading_font': 'Instrument Serif, Georgia, serif',
    'logo_url': 'https://20682069.fs1.hubspotusercontent-na1.net/hubfs/20682069/QUANTUM/IMAGES/Quantum%20Graphics%20and%20Logos/Quantum_Logo_Navy_Header_Cropped.jpg',
    'logo_width': 2084,
    'logo_height': 753,
}


def _api(method, path, token, payload=None):
    cmd = ['curl', '-s', '-X', method,
           f'https://api.hubapi.com{path}',
           '-H', f'Authorization: Bearer {token}',
           '-H', 'Content-Type: application/json']
    if payload:
        cmd += ['-d', json.dumps(payload)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(r.stdout) if r.stdout else {}
    except Exception:
        return {'_raw': r.stdout[:500]}


def _build_body_html(eyebrow, headline, body_html, tokens):
    """Wrap raw body HTML with the QBS-style eyebrow + headline header."""
    t = tokens
    # Apply paragraph styling to <p> tags
    body = body_html.replace(
        '<p>',
        f'<p style="margin:0 0 20px 0; font-family:{t["body_font"]}; '
        f'font-size:17px; line-height:1.75; color:{t["text"]};">'
    )
    # Style strong tags
    body = re.sub(r'<strong>',
                  f'<strong style="color:{t["text"]}; font-weight:700;">',
                  body)
    return f"""<div style="padding:44px 32px 8px 32px;">
<p style="font-family:{t['body_font']}; font-size:13px; color:{t['muted']}; letter-spacing:0.16em; text-transform:uppercase; margin:0 0 20px 0; font-weight:600;">{eyebrow}</p>
<h1 style="font-family:{t['heading_font']}; font-size:38px; line-height:1.15; color:{t['text']}; margin:0 0 26px 0; font-weight:400;">{headline}</h1>
<div style="font-family:{t['body_font']}; font-size:17px; line-height:1.75; color:{t['text']};">
{body}
</div>
</div>"""


def _build_signature_html(tokens, sender_name='Shawn Peterson',
                          sender_title='Founder & CEO, Quantum Business Solutions',
                          sender_email='shawn@thequantumleap.business',
                          credentials='HubSpot Diamond Partner &nbsp;&middot;&nbsp; #1 ZoomInfo Partner &nbsp;&middot;&nbsp; Top-Tier ConnectAndSell Partner',
                          company_name='Quantum Business Solutions',
                          location='Sioux Falls, SD',
                          website='thequantumleap.business'):
    """Build the branded signature + credentials + footer HTML block."""
    t = tokens
    return f"""<div>
<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="margin:16px 0 0 0;">
<tr><td style="border-top:1px solid {t['border']}; height:1px; line-height:1px; font-size:1px;">&nbsp;</td></tr>
</table>

<div style="padding:28px 0 16px 0;">
<p style="font-family:{t['body_font']}; font-size:16px; line-height:1.5; color:{t['text']}; margin:0 0 4px 0;">Talk soon,</p>
<p style="font-family:{t['heading_font']}; font-size:28px; line-height:1.2; color:{t['text']}; margin:0 0 6px 0; font-weight:400;">{sender_name}</p>
<p style="font-family:{t['body_font']}; font-size:14px; line-height:1.5; color:{t['muted']}; margin:0 0 2px 0;">{sender_title}</p>
<p style="font-family:{t['body_font']}; font-size:14px; line-height:1.5; color:{t['muted']}; margin:0 0 22px 0;"><a href="mailto:{sender_email}" style="color:{t['gold']}; text-decoration:none;">{sender_email}</a></p>
</div>

<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#f5f3ec; border-radius:4px; margin:0 0 28px 0;">
<tr><td style="padding:18px 22px;">
<p style="font-family:{t['body_font']}; font-size:12px; letter-spacing:0.14em; text-transform:uppercase; color:{t['muted']}; margin:0 0 8px 0; font-weight:600;">{company_name}</p>
<p style="font-family:{t['body_font']}; font-size:13px; line-height:1.55; color:{t['text']}; margin:0;">{credentials}</p>
</td></tr>
</table>

<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="margin:0;">
<tr><td style="background-color:{t['gold']}; height:3px; line-height:3px; font-size:3px;">&nbsp;</td></tr>
<tr><td style="background-color:{t['navy_footer']}; padding:22px 20px; text-align:center;">
<p style="font-family:{t['body_font']}; font-size:12px; color:#8a8f9b; margin:0 0 6px 0; letter-spacing:0.06em;">{company_name} &nbsp;|&nbsp; {location}</p>
<p style="font-family:{t['body_font']}; font-size:12px; color:#6b7280; margin:0;"><a href="https://{website}" style="color:#8a8f9b; text-decoration:none;">{website}</a></p>
</td></tr>
</table>
</div>"""


def push_email_draft(token, winner_template_path, config, hub_id='20682069'):
    """
    Create a single branded email draft in HubSpot.

    Args:
        token: HubSpot Private App Token
        winner_template_path: path to a JSON file containing a fetched 'winner' email
                             (used for structural cloning)
        config: dict with email content + optional overrides (see module docstring)
        hub_id: HubSpot Hub ID (defaults to QBS)

    Returns:
        dict with 'success' (bool), 'email_id' (str), 'edit_url' (str), 'error' (str if failed)
    """
    # Merge tokens: config can override defaults
    tokens = {**DEFAULT_TOKENS, **(config.get('design_tokens') or {})}

    # Load winner template
    with open(winner_template_path) as f:
        winner = json.load(f)

    # Deep copy and strip
    payload = copy.deepcopy(winner)
    for k in ['id', 'createdAt', 'updatedAt', 'publishDate', 'publishedAt',
              'publishedByEmail', 'publishedById', 'publishedByName',
              'isPublished', 'state', 'previewKey',
              'campaign', 'campaignName', 'campaignUtm',
              'primaryEmailCampaignId', 'allEmailCampaignIds',
              'clonedFrom', 'createdById', 'updatedById']:
        payload.pop(k, None)

    # Set identity
    payload['name'] = config['name']
    payload['subject'] = config['subject']
    payload['state'] = 'DRAFT'

    # Recipient lists
    if 'recipient_lists' in config:
        rl = config['recipient_lists']
        payload['to'] = {
            'contactIds': {'exclude': [], 'include': []},
            'contactIlsLists': {'exclude': [], 'include': rl.get('contactIlsLists', [])},
            'contactLists': {'exclude': [], 'include': rl.get('contactLists', [])},
            'suppressGraymail': True,
        }
    # else: keep winner's lists (already in payload)

    # Apply style settings
    payload['content']['styleSettings'] = {
        'backgroundColor': tokens['bg'],
        'backgroundImageType': 'REPEAT',
        'bodyBorderColor': tokens['bg'],
        'bodyBorderColorChoice': 'BORDER_MANUAL',
        'bodyBorderWidth': 0.0,
        'bodyColor': tokens['white'],
        'buttonStyleSettings': {
            'backgroundColor': tokens['gold'],
            'cornerRadius': 6,
            'fontStyle': {'bold': True, 'color': '#ffffff', 'font': tokens['body_font'],
                          'italic': False, 'size': 16, 'underline': False}
        },
        'dividerStyleSettings': {'color': {'color': tokens['gold'], 'opacity': 100}, 'height': 1, 'lineType': 'solid'},
        'headingOneFont': {'size': 38, 'font': tokens['heading_font'], 'color': tokens['text']},
        'headingTwoFont': {'size': 24, 'font': tokens['heading_font'], 'color': tokens['text']},
        'linksFont': {'bold': False, 'color': tokens['gold'], 'italic': False, 'underline': True, 'font': tokens['body_font']},
        'primaryFont': tokens['body_font'],
        'primaryFontColor': tokens['text'],
        'primaryFontSize': 17.0,
        'secondaryFont': tokens['body_font'],
        'secondaryFontColor': tokens['muted'],
        'secondaryFontSize': 13.0
    }

    # Section-0 navy bar style
    for s in payload['content'].get('flexAreas', {}).get('main', {}).get('sections', []):
        if s.get('id') == 'section-0':
            s['style'] = {
                'backgroundColor': tokens['navy_header'],
                'backgroundType': 'CONTENT',
                'paddingBottom': '0px',
                'paddingTop': '0px',
            }

    widgets = payload['content']['widgets']

    # 1. Header logo
    widgets['module-0-0-0'] = {
        'body': {
            'alignment': 'center',
            'css_class': 'dnd-module',
            'hs_enable_module_padding': False,
            'img': {
                'alt': config.get('logo_alt', 'Company Logo'),
                'height': tokens['logo_height'],
                'src': tokens['logo_url'],
                'width': tokens['logo_width'],
            },
            'link': '',
            'module_id': 1367093,
            'path': '@hubspot/image_email',
            'schema_version': 2,
            'style': {'alignment': 'center', 'corner_radius': 0, 'corner_radius_unit': '%'}
        },
        'id': 'module-0-0-0',
        'module_id': 1367093,
        'name': 'module-0-0-0',
        'order': 1,
        'type': 'module',
        'styles': {'breakpointStyles': {'default': {}, 'mobile': {}}}
    }

    # 2. Preview text
    if 'preview_text' in widgets:
        widgets['preview_text']['body']['value'] = config['preview']

    # 3. Body
    widgets['module-1-0-0']['body']['html'] = _build_body_html(
        config['eyebrow'], config['headline'], config['body_html'], tokens
    )

    # 4. CTA button
    btn = widgets['module_17472322758541']['body']
    cta_text = config['cta_text']
    if not cta_text.endswith('→'):
        cta_text += ' →'
    btn['text'] = cta_text
    btn['link_to'] = 'url'
    btn['destination'] = config['cta_url']
    btn['file'] = None
    btn['meeting_field'] = config['cta_url']
    btn['page_field'] = None
    btn['background_color'] = tokens['gold']
    btn['corner_radius'] = 6
    btn['font'] = tokens['body_font']
    btn['font_color'] = '#ffffff'
    btn['font_size'] = 16
    btn['font_style'] = {
        "color": "#ffffff", "font": tokens['body_font'],
        "size": {"units": "px", "value": 16},
        "styles": {"bold": True, "font-weight": "bold", "italic": False, "underline": False}
    }

    # 5. Signature block
    sig_kwargs = {k: v for k, v in config.items()
                  if k in ('sender_name', 'sender_title', 'sender_email',
                           'credentials', 'company_name', 'location', 'website')}
    widgets['module_17540506686871']['body']['html'] = _build_signature_html(tokens, **sig_kwargs)

    # 6. Send date (optional)
    if 'send_date_iso' in config:
        payload['publishDate'] = config['send_date_iso']
        payload['sendOnPublish'] = True

    # POST to create
    resp = _api('POST', '/marketing/v3/emails/', token, payload)
    if not resp.get('id'):
        return {
            'success': False,
            'email_id': None,
            'edit_url': None,
            'error': resp.get('message', str(resp)[:300]),
        }

    email_id = resp['id']
    return {
        'success': True,
        'email_id': email_id,
        'edit_url': f'https://app.hubspot.com/email/{hub_id}/edit/{email_id}',
        'error': None,
    }


def verify_email_exists(email_id, token):
    """Fetch an email by ID and return True if it exists in DRAFT state."""
    r = _api('GET', f'/marketing/v3/emails/{email_id}', token)
    return r.get('id') == email_id and r.get('state') == 'DRAFT'


def associate_with_campaign(email_id, campaign_id, token):
    """Associate an email with a campaign. Returns True on success."""
    cmd = ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
           '-X', 'PUT',
           f'https://api.hubapi.com/marketing/v3/campaigns/{campaign_id}/assets/MARKETING_EMAIL/{email_id}',
           '-H', f'Authorization: Bearer {token}']
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip() in ('200', '204')


def fetch_winner_email(email_id, token, save_path='/tmp/winner_email.json'):
    """Fetch a winner email by ID and save it locally as a template."""
    r = _api('GET', f'/marketing/v3/emails/{email_id}', token)
    if r.get('id'):
        with open(save_path, 'w') as f:
            json.dump(r, f, indent=2)
        return save_path
    return None
