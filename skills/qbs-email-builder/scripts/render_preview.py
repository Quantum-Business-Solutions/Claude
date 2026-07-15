"""
render_preview.py

Render an email design as a standalone HTML file you can open in a browser
or screenshot before pushing to HubSpot.

Usage:
    from render_preview import render_email_preview

    html_path = render_email_preview(
        config={
            'name': 'Test Email',
            'subject': 'Test subject',
            'preview': 'Preview text',
            'eyebrow': 'A POV from Shawn',
            'headline': 'The headline',
            'body_html': '<p>Body content...</p>',
            'cta_text': 'Book a Call',
            'cta_url': 'https://example.com',
        },
        output_path='/tmp/preview.html'
    )
    # Returns the path to the saved HTML file

CLI usage:
    python render_preview.py path/to/config.json /tmp/preview.html
"""
import json
import re
import sys


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
}


def render_email_preview(config, output_path='/tmp/preview.html', tokens=None):
    """Render an email config as a standalone HTML file."""
    t = {**DEFAULT_TOKENS, **(tokens or {})}

    # Style the body HTML the same way push_email.py does
    body = config['body_html'].replace(
        '<p>',
        f'<p style="margin:0 0 20px 0; font-family:{t["body_font"]}; '
        f'font-size:17px; line-height:1.75; color:{t["text"]};">'
    )
    body = re.sub(r'<strong>',
                  f'<strong style="color:{t["text"]}; font-weight:700;">',
                  body)

    # Default sender info (QBS) — config can override
    sender_name = config.get('sender_name', 'Shawn Peterson')
    sender_title = config.get('sender_title', 'Founder & CEO, Quantum Business Solutions')
    sender_email = config.get('sender_email', 'shawn@thequantumleap.business')
    credentials = config.get('credentials',
        'HubSpot Diamond Partner &nbsp;&middot;&nbsp; #1 ZoomInfo Partner &nbsp;&middot;&nbsp; Top-Tier ConnectAndSell Partner')
    company_name = config.get('company_name', 'Quantum Business Solutions')
    location = config.get('location', 'Sioux Falls, SD')
    website = config.get('website', 'thequantumleap.business')

    cta_text = config['cta_text']
    if not cta_text.endswith('→'):
        cta_text += ' →'

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Email Preview: {config.get('name', 'Email')}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Instrument+Serif&display=swap" rel="stylesheet">
<style>
  body {{
    margin: 0;
    padding: 40px 20px;
    background: {t['bg']};
    font-family: {t['body_font']};
  }}
  .email {{
    max-width: 640px;
    margin: 0 auto;
    background: {t['white']};
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  }}
  .preview-meta {{
    max-width: 640px;
    margin: 0 auto 24px auto;
    background: #fff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 14px 18px;
    font-family: {t['body_font']};
    font-size: 13px;
    color: {t['muted']};
  }}
  .preview-meta strong {{ color: {t['text']}; }}
</style>
</head>
<body>

<div class="preview-meta">
  <p style="margin:0 0 4px 0;"><strong>Subject:</strong> {config.get('subject', '')}</p>
  <p style="margin:0;"><strong>Preview:</strong> {config.get('preview', '')}</p>
</div>

<div class="email">

<!-- Navy Header -->
<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background-color:{t['navy_header']};">
<tr>
<td align="center" style="padding:0; background-color:{t['navy_header']};">
<img src="{t['logo_url']}" alt="{company_name}" style="display:block; width:100%; max-width:640px; height:auto; border:0;" />
</td>
</tr>
<tr>
<td style="background-color:{t['gold']}; height:3px; line-height:3px; font-size:3px;">&nbsp;</td>
</tr>
</table>

<!-- Body -->
<div style="padding:44px 32px 8px 32px;">
<p style="font-family:{t['body_font']}; font-size:13px; color:{t['muted']}; letter-spacing:0.16em; text-transform:uppercase; margin:0 0 20px 0; font-weight:600;">{config['eyebrow']}</p>
<h1 style="font-family:{t['heading_font']}; font-size:38px; line-height:1.15; color:{t['text']}; margin:0 0 26px 0; font-weight:400;">{config['headline']}</h1>
<div style="font-family:{t['body_font']}; font-size:17px; line-height:1.75; color:{t['text']};">
{body}
</div>
</div>

<!-- CTA -->
<div style="padding:28px 32px 40px 32px; text-align:center;">
<table cellpadding="0" cellspacing="0" role="presentation" style="margin:0 auto;">
<tr>
<td style="background-color:{t['gold']}; border-radius:6px;">
<a href="{config['cta_url']}" style="display:inline-block; padding:16px 36px; font-family:{t['body_font']}; font-size:16px; font-weight:700; color:#ffffff; text-decoration:none; letter-spacing:0.02em;">{cta_text}</a>
</td>
</tr>
</table>
</div>

<!-- Divider -->
<div style="padding:0 32px 10px 32px;">
<table width="100%" cellpadding="0" cellspacing="0" role="presentation">
<tr><td style="border-top:1px solid {t['border']}; height:1px; line-height:1px; font-size:1px;">&nbsp;</td></tr>
</table>
</div>

<!-- Signature -->
<div style="padding:28px 32px 16px 32px;">
<p style="font-family:{t['body_font']}; font-size:16px; line-height:1.5; color:{t['text']}; margin:0 0 4px 0;">Talk soon,</p>
<p style="font-family:{t['heading_font']}; font-size:28px; line-height:1.2; color:{t['text']}; margin:0 0 6px 0; font-weight:400;">{sender_name}</p>
<p style="font-family:{t['body_font']}; font-size:14px; line-height:1.5; color:{t['muted']}; margin:0 0 2px 0;">{sender_title}</p>
<p style="font-family:{t['body_font']}; font-size:14px; line-height:1.5; color:{t['muted']}; margin:0 0 18px 0;"><a href="mailto:{sender_email}" style="color:{t['gold']}; text-decoration:none;">{sender_email}</a></p>
</div>

<!-- Credentials card -->
<div style="padding:0 32px 40px 32px;">
<table width="100%" cellpadding="0" cellspacing="0" role="presentation" style="background-color:#f5f3ec; border-radius:4px;">
<tr><td style="padding:18px 22px;">
<p style="font-family:{t['body_font']}; font-size:12px; letter-spacing:0.14em; text-transform:uppercase; color:{t['muted']}; margin:0 0 8px 0; font-weight:600;">{company_name}</p>
<p style="font-family:{t['body_font']}; font-size:13px; line-height:1.55; color:{t['text']}; margin:0;">{credentials}</p>
</td></tr>
</table>
</div>

<!-- Navy Footer -->
<table width="100%" cellpadding="0" cellspacing="0" role="presentation">
<tr><td style="background-color:{t['gold']}; height:3px; line-height:3px; font-size:3px;">&nbsp;</td></tr>
<tr>
<td style="background-color:{t['navy_footer']}; padding:22px 20px; text-align:center;">
<p style="font-family:{t['body_font']}; font-size:12px; color:#8a8f9b; margin:0 0 6px 0; letter-spacing:0.06em;">{company_name} &nbsp;|&nbsp; {location}</p>
<p style="font-family:{t['body_font']}; font-size:12px; color:#6b7280; margin:0;"><a href="https://{website}" style="color:#8a8f9b; text-decoration:none;">{website}</a></p>
</td>
</tr>
</table>

</div>
</body>
</html>"""

    with open(output_path, 'w') as f:
        f.write(html)

    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python render_preview.py <config.json> <output.html>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        config = json.load(f)
    out = render_email_preview(config, sys.argv[2])
    print(f"Rendered: {out}")
