#!/usr/bin/env python3
"""Build the official Praxera coded HubSpot email templates.

Emits four `.html` coded email templates into
assets/praxera-email-templates/ and a matching `*_preview.html` (HubL replaced
with sample content) into reports/praxera-email-templates/previews/ so the
layout can be screenshotted with a real browser.

Brand rules enforced here:
  * "Praxera" only (never "Praxera Laboratories" / "Praxera Labs")
  * parent company is FoodScience LLC
  * Praxera is a private-label partner, never a manufacturer
  * no DaVinci / VetriScience / Pet Tech links, no ecommerce / purchase path
  * every product CTA points at /get-started
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'praxera-email-templates')
PREV = os.path.join(ROOT, 'reports', 'praxera-email-templates', 'previews')

# ---------------------------------------------------------------- brand ----
INK        = '#092637'   # dark ink, sampled from logo
GREEN      = '#6CA843'   # brand green, sampled from logo
GREEN_LT   = '#A3D06F'   # lighter tint used in brand artwork
GREEN_TINT = '#EFF6E8'   # pale green band background
BODY       = '#33434C'   # body copy grey
MUTED      = '#6B7A82'
PAGE_BG    = '#EEF1F0'
WHITE      = '#FFFFFF'
RULE       = '#DCE3E0'

FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"

LOGO_WHITE = 'https://www.praxerasupplements.com/hubfs/Praxera/Praxera%20Logo%20White.png'
LOGO_DARK  = 'https://www.praxerasupplements.com/hubfs/Praxera/Praxera%20Logo.png'
# Logo PNG is 612x208 with transparent padding; the visible wordmark is only
# x=88..523 (436px) / y=74..140 (67px). Width/height below keep the true 612:208
# ratio so the wordmark is never stretched (the bug inherited from the DaVinci
# clones, which carried DaVinci's 245x107 attributes onto a 612x208 file).
LOGO_W, LOGO_H = 294, 100          # masthead  -> wordmark renders ~209x32
LOGO_FW, LOGO_FH = 197, 67         # footer    -> wordmark renders ~140x22

SITE = 'https://www.praxerasupplements.com'
CTA_URL = SITE + '/get-started'
CTA_LABEL = 'Schedule a Consultation'

FDA = ("These statements have not been evaluated by the Food and Drug Administration. "
       "These products are not intended to diagnose, treat, cure, or prevent any disease. "
       "Information in this email is provided for informational purposes only and is not "
       "intended as a substitute for advice from your physician or other health care professional.")

# ------------------------------------------------------------- fragments ---

def annotation(label):
    return ('<!--\n'
            '  templateType: "email"\n'
            '  isAvailableForNewContent: true\n'
            '  label: "%s"\n'
            '-->\n' % label)


HEAD_TITLE = ("{% if content.html_title and content.html_title != '' %}{{ content.html_title }}"
              "{% elif content.name %}{{ content.name }}{% else %}{{ content.body.subject }}{% endif %}")


def head(extra_inline=''):
    """<head> block. Rules in #hs-inline-css are inlined by HubSpot onto the
    rendered markup (that is how rich-text content picks up brand typography).
    Media queries must stay OUT of that node, so they live in a second style."""
    return """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="x-apple-disable-message-reformatting" />
    <meta name="color-scheme" content="light dark" />
    <meta name="supported-color-schemes" content="light dark" />
    <title>__TITLE__</title>
    <meta property="og:title" content="__TITLE__" />
    <meta name="twitter:title" content="__TITLE__" />
    {% if content.meta_description %}<meta name="description" content="{{ content.meta_description }}" />{% endif %}

    <style type="text/css" id="hs-inline-css">
      /*<![CDATA[*/
      /* Everything in this node is inlined by HubSpot before sending, which is
         what gives marketer-entered rich text the Praxera type styles. */
      body { margin:0; padding:0; }
      .px p, .px li { font-family:__FONT__; font-size:16px; line-height:26px; color:__BODY__; margin:0 0 16px 0; }
      .px li { margin:0 0 8px 0; }
      .px ul, .px ol { margin:0 0 16px 0; padding-left:22px; }
      .px a { color:__GREEN__; text-decoration:underline; }
      .px h1 { font-family:__FONT__; font-size:28px; line-height:36px; color:__INK__; font-weight:bold; margin:0 0 14px 0; }
      .px h2 { font-family:__FONT__; font-size:21px; line-height:29px; color:__INK__; font-weight:bold; margin:0 0 12px 0; }
      .px h3 { font-family:__FONT__; font-size:17px; line-height:25px; color:__INK__; font-weight:bold; margin:0 0 10px 0; }
      .teaser p { font-family:__FONT__; font-size:15px; line-height:24px; color:__BODY__; margin:0 0 10px 0; }
      .ink-copy p, .ink-copy li { color:#DDE5E8; }
      .ink-copy a { color:__GREEN_LT__; }
      __EXTRA_INLINE__
      /*]]>*/
    </style>

    <style type="text/css">
      /* Not inlined: media queries + dark-mode hardening. */
      img { -ms-interpolation-mode:bicubic; border:0; outline:none; text-decoration:none; }
      table { border-collapse:collapse; mso-table-lspace:0pt; mso-table-rspace:0pt; }
      a[x-apple-data-detectors] { color:inherit !important; text-decoration:none !important; font-size:inherit !important; font-family:inherit !important; font-weight:inherit !important; line-height:inherit !important; }

      /* Outlook.com / Apple Mail dark mode: hold the masthead and footer on a
         real dark plate so the white logo never lands on an inverted white box. */
      @media (prefers-color-scheme: dark) {
        .plate, .plate td { background-color:__INK__ !important; }
        .plate-text { color:#FFFFFF !important; }
      }
      [data-ogsc] .plate, [data-ogsc] .plate td { background-color:__INK__ !important; }
      [data-ogsc] .plate-text { color:#FFFFFF !important; }
      [data-ogsc] .paper, [data-ogsc] .paper td { background-color:#FFFFFF !important; }

      @media only screen and (max-width:620px) {
        .wrap { width:100% !important; max-width:100% !important; }
        .px { padding-left:20px !important; padding-right:20px !important; }
        .py { padding-top:26px !important; padding-bottom:26px !important; }
        .logo { width:210px !important; height:auto !important; }
        .logo-sm { width:150px !important; height:auto !important; }
        .col { display:block !important; width:100% !important; max-width:100% !important; }
        .col-gap { display:block !important; width:100% !important; max-width:100% !important; height:14px !important; line-height:14px !important; font-size:14px !important; }
        .thumb { width:100% !important; max-width:100% !important; height:auto !important; }
        .h1, .px h1 { font-size:24px !important; line-height:32px !important; }
        .h2, .px h2 { font-size:19px !important; line-height:27px !important; }
        .btn-td { padding-left:20px !important; padding-right:20px !important; }
        .center-sm { text-align:center !important; }
      }
    </style>

    <!--[if gte mso 9]>
      <xml><o:OfficeDocumentSettings><o:AllowPNG/><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml>
    <![endif]-->
    <!--[if mso]>
      <style type="text/css">
        body, table, td, p, a, h1, h2, h3, li { font-family: Arial, Helvetica, sans-serif !important; }
      </style>
    <![endif]-->
  </head>
""".replace('__TITLE__', HEAD_TITLE).replace('__FONT__', FONT).replace('__BODY__', BODY) \
   .replace('__GREEN_LT__', GREEN_LT).replace('__GREEN__', GREEN).replace('__INK__', INK) \
   .replace('__EXTRA_INLINE__', extra_inline)


PREHEADER = """  <body style="margin:0; padding:0; background-color:__PAGE_BG__;" bgcolor="__PAGE_BG__">
    <div style="display:none; font-size:1px; color:__PAGE_BG__; line-height:1px; max-height:0; max-width:0; opacity:0; overflow:hidden;">
      {% text 'preview_text' label='Preview text <span class="help-text">Shown after the subject line in most inboxes</span>', value='', no_wrapper=True %}
      &#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;
    </div>

    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:__PAGE_BG__;" bgcolor="__PAGE_BG__">
      <tr>
        <td align="center" valign="top" style="padding:24px 12px;">
          <!--[if mso]><table role="presentation" align="center" border="0" cellpadding="0" cellspacing="0" width="600"><tr><td><![endif]-->
          <table role="presentation" class="wrap" align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:600px; margin:0 auto;">
""".replace('__PAGE_BG__', PAGE_BG)


def masthead(kicker_field=True):
    """Dark ink plate + white logo + green rule. Explicitly painted so a dark
    email theme cannot invert it into a white box behind a white PNG."""
    k = ''
    if kicker_field:
        k = ("""              <tr>
                <td class="plate plate-text" align="center" bgcolor="__INK__" style="background-color:__INK__; padding:0 24px 24px 24px; font-family:__FONT__; font-size:11px; line-height:16px; letter-spacing:1.6px; text-transform:uppercase; color:__GREEN_LT__;">
                  {% text 'masthead_kicker' label='Masthead kicker', value='Practitioner Brief', no_wrapper=True %}
                </td>
              </tr>
""")
    return ("""            <!-- masthead -->
            <tr>
              <td class="plate" bgcolor="__INK__" style="background-color:__INK__;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="plate" bgcolor="__INK__" style="background-color:__INK__;">
                  <tr>
                    <td align="center" bgcolor="__INK__" style="background-color:__INK__; padding:__PADT__ 24px __PADB__ 24px;">
                      <a href="__SITE__" style="text-decoration:none;">
                        <img class="logo" src="__LOGO_WHITE__" alt="Praxera" width="__LW__" height="__LH__" style="display:block; width:__LW__px; max-width:100%; height:auto; border:0;" />
                      </a>
                    </td>
                  </tr>
__KICKER__                </table>
              </td>
            </tr>
            <tr><td height="4" bgcolor="__GREEN__" style="background-color:__GREEN__; height:4px; line-height:4px; font-size:4px;">&nbsp;</td></tr>
""").replace('__KICKER__', k) \
    .replace('__PADT__', '10px') \
    .replace('__PADB__', '6px' if not kicker_field else '0') \
    .replace('__LOGO_WHITE__', LOGO_WHITE).replace('__LW__', str(LOGO_W)).replace('__LH__', str(LOGO_H)) \
    .replace('__SITE__', SITE).replace('__INK__', INK).replace('__GREEN__', GREEN).replace('__FONT__', FONT) \
    .replace('__GREEN_LT__', GREEN_LT)


def cta_band(dark=True, show_button=True, heading='Ready to build your own line?',
             body='Talk to a Praxera private-label specialist about catalog selection, label design and turnkey production.',
             name='cta'):
    bg = INK if dark else GREEN_TINT
    hcol = WHITE if dark else INK
    bcol = '#C9D6DB' if dark else BODY
    plate = ' class="plate"' if dark else ''
    btn = """                      {% text '__NAME___label' label='CTA button label', value='__CTA_LABEL__', no_wrapper=True, export_to_template_context=True %}
                      {% text '__NAME___url' label='CTA button link', value='__CTA_URL__', no_wrapper=True, export_to_template_context=True %}
                      <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="center" style="margin:0 auto;">
                        <tr>
                          <td class="btn-td" align="center" bgcolor="__GREEN__" style="background-color:__GREEN__; border-radius:4px; padding:15px 32px; mso-padding-alt:15px 32px;">
                            <a href="{{ widget_data.__NAME___url.value }}" style="display:block; font-family:__FONT__; font-size:16px; line-height:20px; font-weight:bold; color:#FFFFFF; text-decoration:none;">{{ widget_data.__NAME___label.value }}</a>
                          </td>
                        </tr>
                      </table>
""" if show_button else ''
    return ("""            <!-- CTA band -->
            <tr>
              <td__PLATE__ bgcolor="__BG__" style="background-color:__BG__;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%"__PLATE__ bgcolor="__BG__" style="background-color:__BG__;">
                  <tr>
                    <td class="px py" align="center" bgcolor="__BG__" style="background-color:__BG__; padding:34px 40px 36px 40px;">
                      <div style="font-family:__FONT__; font-size:21px; line-height:29px; font-weight:bold; color:__HCOL__; margin:0 0 10px 0;">
                        {% text '__NAME___heading' label='CTA heading', value='__HEADING__', no_wrapper=True %}
                      </div>
                      <div style="font-family:__FONT__; font-size:15px; line-height:24px; color:__BCOL__; margin:0 0 __BODYMB__ 0;">
                        {% text '__NAME___body' label='CTA supporting line', value='__BODY__', no_wrapper=True %}
                      </div>
__BTN__                    </td>
                  </tr>
                </table>
              </td>
            </tr>
""").replace('__BTN__', btn).replace('__BODYMB__', '22px' if show_button else '0') \
    .replace('__PLATE__', plate).replace('__BG__', bg).replace('__HCOL__', hcol).replace('__BCOL__', bcol) \
    .replace('__NAME__', name).replace('__HEADING__', heading).replace('__BODY__', body) \
    .replace('__CTA_LABEL__', CTA_LABEL).replace('__CTA_URL__', CTA_URL) \
    .replace('__FONT__', FONT).replace('__GREEN__', GREEN)


def button(name, label=CTA_LABEL, url=CTA_URL, align='center'):
    return ("""                      {% text '__NAME___label' label='Button label', value='__LABEL__', no_wrapper=True, export_to_template_context=True %}
                      {% text '__NAME___url' label='Button link', value='__URL__', no_wrapper=True, export_to_template_context=True %}
                      <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="__ALIGN__" style="__MARGIN__">
                        <tr>
                          <td class="btn-td" align="center" bgcolor="__GREEN__" style="background-color:__GREEN__; border-radius:4px; padding:15px 32px; mso-padding-alt:15px 32px;">
                            <a href="{{ widget_data.__NAME___url.value }}" style="display:block; font-family:__FONT__; font-size:16px; line-height:20px; font-weight:bold; color:#FFFFFF; text-decoration:none;">{{ widget_data.__NAME___label.value }}</a>
                          </td>
                        </tr>
                      </table>
""").replace('__NAME__', name).replace('__LABEL__', label).replace('__URL__', url) \
    .replace('__ALIGN__', align).replace('__MARGIN__', 'margin:0 auto;' if align == 'center' else 'margin:0;') \
    .replace('__GREEN__', GREEN).replace('__FONT__', FONT)


FOOTER = """            <!-- footer -->
            <tr>
              <td class="plate" bgcolor="__INK__" style="background-color:__INK__;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="plate" bgcolor="__INK__" style="background-color:__INK__;">
                  <tr><td height="4" bgcolor="__GREEN__" style="background-color:__GREEN__; height:4px; line-height:4px; font-size:4px;">&nbsp;</td></tr>
                  <tr>
                    <td class="px" align="center" bgcolor="__INK__" style="background-color:__INK__; padding:16px 40px 0 40px;">
                      <img class="logo-sm" src="__LOGO_WHITE__" alt="Praxera" width="__LFW__" height="__LFH__" style="display:block; width:__LFW__px; max-width:100%; height:auto; border:0; margin:0 auto;" />
                    </td>
                  </tr>
                  <tr>
                    <td class="px plate-text" align="center" bgcolor="__INK__" style="background-color:__INK__; padding:6px 40px 0 40px; font-family:__FONT__; font-size:13px; line-height:21px; color:#B8C6CC;">
                      Private label supplements for practitioners &middot; a FoodScience LLC brand
                    </td>
                  </tr>
                  <tr>
                    <td class="px" align="center" bgcolor="__INK__" style="background-color:__INK__; padding:14px 40px 0 40px; font-family:__FONT__; font-size:13px; line-height:22px; color:#B8C6CC;">
                      <a href="__SITE__/get-started" style="color:__GREEN_LT__; text-decoration:none; font-weight:bold;">Schedule a consultation</a>
                      &nbsp;&middot;&nbsp;
                      <a href="__SITE__" style="color:__GREEN_LT__; text-decoration:none; font-weight:bold;">praxerasupplements.com</a>
                      &nbsp;&middot;&nbsp;
                      <a href="mailto:info@praxerasupplements.com" style="color:__GREEN_LT__; text-decoration:none; font-weight:bold;">info@praxerasupplements.com</a>
                    </td>
                  </tr>
                  <tr>
                    <td class="px" align="center" bgcolor="__INK__" style="background-color:__INK__; padding:18px 40px 0 40px; font-family:__FONT__; font-size:12px; line-height:20px; color:#8FA3AB;">
                      {{ site_settings.company_name }}<br />
                      {{ site_settings.company_street_address_1 }}{% if site_settings.company_street_address_2 %}, {{ site_settings.company_street_address_2 }}{% endif %}<br />
                      {{ site_settings.company_city }}, {{ site_settings.company_state }} {{ site_settings.company_zip }} {{ site_settings.company_country }}
                    </td>
                  </tr>
                  <tr>
                    <td class="px" align="center" bgcolor="__INK__" style="background-color:__INK__; padding:16px 40px 0 40px; font-family:__FONT__; font-size:12px; line-height:20px; color:#8FA3AB;">
                      You are receiving this email because you subscribed to {{ subscription_name }} from {{ site_settings.company_name }}.<br />
                      <a class="hubspot-mergetag" data-unsubscribe="true" href="{{ unsubscribe_link }}" style="color:#B8C6CC; text-decoration:underline; white-space:nowrap;">Manage email preferences</a>
                      &nbsp;&middot;&nbsp;
                      <a class="hubspot-mergetag" data-unsubscribe="true" href="{{ unsubscribe_link_all }}" style="color:#B8C6CC; text-decoration:underline; white-space:nowrap;">Unsubscribe from all emails</a>
                    </td>
                  </tr>
                  <tr>
                    <td class="px" align="center" bgcolor="__INK__" style="background-color:__INK__; padding:18px 40px 30px 40px;">
                      <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                        <tr><td height="1" bgcolor="#1D3B4B" style="background-color:#1D3B4B; height:1px; line-height:1px; font-size:1px;">&nbsp;</td></tr>
                      </table>
                      <div style="font-family:__FONT__; font-size:11px; line-height:17px; color:#6F868F; padding-top:14px;">
                        __FDA__
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
""".replace('__LOGO_WHITE__', LOGO_WHITE).replace('__LFW__', str(LOGO_FW)).replace('__LFH__', str(LOGO_FH)) \
   .replace('__SITE__', SITE).replace('__INK__', INK).replace('__GREEN_LT__', GREEN_LT) \
   .replace('__GREEN__', GREEN).replace('__FONT__', FONT).replace('__FDA__', FDA)


CLOSE = """          </table>
          <!--[if mso]></td></tr></table><![endif]-->
        </td>
      </tr>
    </table>
  </body>
</html>
"""


def paper_open(pad='36px 40px 8px 40px'):
    return ("""            <tr>
              <td class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                  <tr>
                    <td class="px py" bgcolor="__WHITE__" style="background-color:__WHITE__; padding:__PAD__;">
""").replace('__WHITE__', WHITE).replace('__PAD__', pad)


PAPER_CLOSE = """                    </td>
                  </tr>
                </table>
              </td>
            </tr>
"""


def article_block(n, default_head, default_teaser, last=False):
    """Thumbnail-left / copy-right article row that collapses to one column
    under 620px. mso ghost cells keep Outlook in two columns.

    The exported widgets are declared BEFORE the {% if %} that reads them --
    export_to_template_context only populates widget_data at the point the tag
    renders, so a guard placed above the declaration is always false. The copy
    column appears exactly once so no HubSpot module name is declared twice."""
    div = '' if last else ("""                        <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                          <tr><td height="28" style="height:28px; line-height:28px; font-size:28px;">&nbsp;</td></tr>
                          <tr><td height="1" bgcolor="__RULE__" style="background-color:__RULE__; height:1px; line-height:1px; font-size:1px;">&nbsp;</td></tr>
                          <tr><td height="28" style="height:28px; line-height:28px; font-size:28px;">&nbsp;</td></tr>
                        </table>
""").replace('__RULE__', RULE)
    return ("""                      {% image 'article___N___image' label='Article __N__ image', src='__THUMB__', alt='', no_wrapper=True, export_to_template_context=True %}
                      {% text 'article___N___headline' label='Article __N__ headline <span class="help-text">Leave blank to hide this article</span>', value='__DHEAD__', no_wrapper=True, export_to_template_context=True %}
                      {% text 'article___N___url' label='Article __N__ link', value='__SITE__/blog', no_wrapper=True, export_to_template_context=True %}
                      {% text 'article___N___link_label' label='Article __N__ link text', value='Read more', no_wrapper=True, export_to_template_context=True %}
                      {% if widget_data.article___N___headline.value %}
                      {% set a__N___img = widget_data.article___N___image.src %}
                      {% set a__N___copy_w = 318 if a__N___img else 520 %}
                      <div style="font-size:0; line-height:0;">
                        {% if a__N___img %}
                        <!--[if mso]><table role="presentation" border="0" cellpadding="0" cellspacing="0" width="520"><tr><td width="180" valign="top"><![endif]-->
                        <div class="col" style="display:inline-block; width:100%; max-width:180px; vertical-align:top;">
                          <a href="{{ widget_data.article___N___url.value }}" style="text-decoration:none;">
                            <img class="thumb" src="{{ a__N___img }}" alt="{{ widget_data.article___N___image.alt }}" width="180" style="display:block; width:100%; max-width:180px; height:auto; border:0; border-radius:4px;" />
                          </a>
                        </div>
                        <!--[if mso]></td><td width="20" valign="top">&nbsp;</td><td width="320" valign="top"><![endif]-->
                        <div class="col-gap" style="display:inline-block; width:20px; height:1px; line-height:1px; font-size:1px;">&nbsp;</div>
                        {% endif %}
                        <div class="col" style="display:inline-block; width:100%; max-width:{{ a__N___copy_w }}px; vertical-align:top;">
                          <div class="h2" style="font-family:__FONT__; font-size:19px; line-height:27px; font-weight:bold; color:__INK__; margin:0 0 8px 0;">
                            <a href="{{ widget_data.article___N___url.value }}" style="color:__INK__; text-decoration:none;">{{ widget_data.article___N___headline.value }}</a>
                          </div>
                          <div class="teaser">
                            {% rich_text 'article___N___teaser' label='Article __N__ teaser', html='<p>__DTEASER__</p>' %}
                          </div>
                          <div style="font-family:__FONT__; font-size:14px; line-height:22px; font-weight:bold;">
                            <a href="{{ widget_data.article___N___url.value }}" style="color:__GREEN__; text-decoration:none;">{{ widget_data.article___N___link_label.value }} &rarr;</a>
                          </div>
                        </div>
                        {% if a__N___img %}<!--[if mso]></td></tr></table><![endif]-->{% endif %}
                      </div>
__DIV__                      {% endif %}
""").replace('__N__', str(n)).replace('__DHEAD__', default_head).replace('__DTEASER__', default_teaser) \
    .replace('__DIV__', div).replace('__FONT__', FONT).replace('__INK__', INK).replace('__GREEN__', GREEN) \
    .replace('__SITE__', SITE).replace('__THUMB__', '')


# ------------------------------------------------------------- templates ---

def tpl_newsletter():
    s = annotation('Praxera - Newsletter') + head() + PREHEADER + masthead(kicker_field=True)
    s += paper_open('36px 40px 30px 40px')
    s += ("""                      <div class="h1" style="font-family:__FONT__; font-size:28px; line-height:36px; font-weight:bold; color:__INK__; margin:0 0 14px 0;">
                        {% text 'intro_heading' label='Intro heading', value='What practitioners are asking us this month', no_wrapper=True %}
                      </div>
                      {% rich_text 'intro_body' label='Intro copy', html='<p>A short note from the Praxera team &mdash; what we are seeing across practitioner brands, and what is worth your attention this month.</p>' %}
""").replace('__FONT__', FONT).replace('__INK__', INK)
    s += PAPER_CLOSE
    s += ("""            <tr>
              <td class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                  <tr>
                    <td class="px" bgcolor="__WHITE__" style="background-color:__WHITE__; padding:0 40px 0 40px;">
                      <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                        <tr><td height="1" bgcolor="__RULE__" style="background-color:__RULE__; height:1px; line-height:1px; font-size:1px;">&nbsp;</td></tr>
                        <tr><td height="28" style="height:28px; line-height:28px; font-size:28px;">&nbsp;</td></tr>
                      </table>
""").replace('__WHITE__', WHITE).replace('__RULE__', RULE)
    s += article_block(1, 'Choosing a delivery form your patients will actually take', 'Capsules, powders, chewables or liquids &mdash; a short guide to matching format to compliance.')
    s += article_block(2, 'What a practitioner-brand label has to say (and what it cannot)', 'Claims, panels and the small print that keeps your line compliant.')
    s += article_block(3, 'Five questions to ask before you launch a private label line', 'Minimums, lead times, label design and the decisions that are hard to reverse.', last=True)
    s += ("""                      <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%">
                        <tr><td height="34" style="height:34px; line-height:34px; font-size:34px;">&nbsp;</td></tr>
                      </table>
""")
    s += PAPER_CLOSE
    s += cta_band(dark=True)
    s += FOOTER + CLOSE
    return s


def tpl_marketing():
    s = annotation('Praxera - Marketing Email') + head() + PREHEADER + masthead(kicker_field=False)
    s += paper_open('38px 40px 30px 40px')
    s += ("""                      <div style="font-family:__FONT__; font-size:11px; line-height:16px; letter-spacing:1.6px; text-transform:uppercase; color:__GREEN__; font-weight:bold; margin:0 0 12px 0;">
                        {% text 'eyebrow' label='Eyebrow', value='Private label supplements', no_wrapper=True %}
                      </div>
                      <div class="h1" style="font-family:__FONT__; font-size:28px; line-height:36px; font-weight:bold; color:__INK__; margin:0 0 18px 0;">
                        {% text 'headline' label='Headline', value='Your formula on your label, without the overhead', no_wrapper=True %}
                      </div>
                      <div class="px">
                        {{ content.email_body }}
                      </div>
""").replace('__FONT__', FONT).replace('__INK__', INK).replace('__GREEN__', GREEN)
    s += PAPER_CLOSE
    # optional supporting image
    s += ("""            {% image 'support_image' label='Supporting image (optional)', src='', alt='', no_wrapper=True, export_to_template_context=True %}
            {% if widget_data.support_image.src %}
            <tr>
              <td class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                  <tr>
                    <td class="px" align="center" bgcolor="__WHITE__" style="background-color:__WHITE__; padding:6px 40px 10px 40px;">
                      <img src="{{ widget_data.support_image.src }}" alt="{{ widget_data.support_image.alt }}" width="520" style="display:block; width:100%; max-width:520px; height:auto; border:0; border-radius:4px; margin:0 auto;" />
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            {% endif %}
""").replace('__WHITE__', WHITE)
    # primary CTA on paper
    s += ("""            <tr>
              <td class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                  <tr>
                    <td class="px" align="center" bgcolor="__WHITE__" style="background-color:__WHITE__; padding:14px 40px 38px 40px;">
""").replace('__WHITE__', WHITE)
    s += button('primary_cta')
    s += ("""                      <div style="font-family:__FONT__; font-size:13px; line-height:21px; color:__MUTED__; padding-top:16px;">
                        {% text 'cta_footnote' label='Note under the button (optional)', value='No obligation &mdash; a 20 minute call to see whether private label is the right fit.', no_wrapper=True %}
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
""").replace('__FONT__', FONT).replace('__MUTED__', MUTED)
    s += cta_band(dark=False, show_button=False, heading='Built in the U.S., backed by FoodScience LLC',
                  body='Over 190 finished formulas, manufactured in the U.S. in a cGMP facility, ready for your label.',
                  name='band')
    s += FOOTER + CLOSE
    return s


def tpl_blog():
    """Blog subscription notification. Uses the blog-post context tokens that
    HubSpot populates on a blog notification send, each guarded so the template
    is still usable as a hand-written post announcement."""
    s = annotation('Praxera - Blog Notification') + head() + PREHEADER + masthead(kicker_field=False)
    s += ("""            <tr>
              <td class="px" align="center" bgcolor="__WHITE__" style="background-color:__WHITE__; padding:26px 40px 0 40px; font-family:__FONT__; font-size:11px; line-height:16px; letter-spacing:1.6px; text-transform:uppercase; color:__GREEN__; font-weight:bold;">
                {% text 'blog_kicker' label='Kicker', value='New on the Praxera blog', no_wrapper=True %}
              </td>
            </tr>
""").replace('__WHITE__', WHITE).replace('__FONT__', FONT).replace('__GREEN__', GREEN)
    s += ("""            {% image 'fallback_image' label='Featured image (used only if the post has none)', src='', alt='', no_wrapper=True, export_to_template_context=True %}
            {% text 'fallback_title' label='Post title (used only if the post title is unavailable)', value='', no_wrapper=True, export_to_template_context=True %}
            {% text 'fallback_url' label='Post link (used only if the post link is unavailable)', value='__SITE__/blog', no_wrapper=True, export_to_template_context=True %}
            {% set post_title = content.name or widget_data.fallback_title.value %}
            {% set post_url = content.absolute_url or widget_data.fallback_url.value %}
            {% set post_image = content.featured_image or widget_data.fallback_image.src %}
            {% set post_excerpt = content.post_summary or content.meta_description %}
            {% if post_image %}
            <tr>
              <td class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                  <tr>
                    <td class="px" align="center" bgcolor="__WHITE__" style="background-color:__WHITE__; padding:22px 40px 0 40px;">
                      <a href="{{ post_url }}" style="text-decoration:none;">
                        <img src="{{ post_image }}" alt="{{ post_title }}" width="520" style="display:block; width:100%; max-width:520px; height:auto; border:0; border-radius:4px; margin:0 auto;" />
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            {% endif %}
""").replace('__WHITE__', WHITE).replace('__SITE__', SITE)
    s += paper_open('24px 40px 6px 40px')
    s += ("""                      <div class="h1" style="font-family:__FONT__; font-size:27px; line-height:35px; font-weight:bold; color:__INK__; margin:0 0 12px 0;">
                        <a href="{{ post_url }}" style="color:__INK__; text-decoration:none;">{{ post_title }}</a>
                      </div>
                      {% if content.publish_date_localized %}
                      <div style="font-family:__FONT__; font-size:13px; line-height:20px; color:__MUTED__; margin:0 0 16px 0;">
                        {{ content.publish_date_localized }}{% if content.blog_post_author.display_name %} &middot; {{ content.blog_post_author.display_name }}{% endif %}
                      </div>
                      {% endif %}
                      {% if post_excerpt %}
                      <div style="font-family:__FONT__; font-size:16px; line-height:26px; color:__BODY__; margin:0 0 24px 0;">
                        {{ post_excerpt|striptags|truncate(260, true, '&hellip;') }}
                      </div>
                      {% endif %}
                      <div class="px">
                        {% rich_text 'editor_note' label='Note from the team (optional)', html='' %}
                      </div>
""").replace('__FONT__', FONT).replace('__INK__', INK).replace('__MUTED__', MUTED).replace('__BODY__', BODY)
    s += PAPER_CLOSE
    s += ("""            <tr>
              <td class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                  <tr>
                    <td class="px" align="left" bgcolor="__WHITE__" style="background-color:__WHITE__; padding:4px 40px 38px 40px;">
                      {% text 'read_label' label='Read button label', value='Read the post', no_wrapper=True, export_to_template_context=True %}
                      <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="left" style="margin:0;">
                        <tr>
                          <td class="btn-td" align="center" bgcolor="__GREEN__" style="background-color:__GREEN__; border-radius:4px; padding:15px 32px; mso-padding-alt:15px 32px;">
                            <a href="{{ post_url }}" style="display:block; font-family:__FONT__; font-size:16px; line-height:20px; font-weight:bold; color:#FFFFFF; text-decoration:none;">{{ widget_data.read_label.value }}</a>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
""").replace('__WHITE__', WHITE).replace('__GREEN__', GREEN).replace('__FONT__', FONT)
    s += cta_band(dark=True, heading='Thinking about your own supplement line?',
                  body='Praxera pairs practitioner brands with finished formulas, label design and turnkey production.')
    s += FOOTER + CLOSE
    return s


def tpl_simple():
    """Minimal chrome for onboarding, guide delivery and other 1:1 style sends."""
    s = annotation('Praxera - Simple Email') + head() + PREHEADER
    s += ("""            <!-- compact masthead -->
            <tr>
              <td class="plate" align="left" bgcolor="__INK__" style="background-color:__INK__; padding:14px 40px 14px 40px;">
                <a href="__SITE__" style="text-decoration:none;">
                  <img class="logo-sm" src="__LOGO_WHITE__" alt="Praxera" width="__LFW__" height="__LFH__" style="display:block; width:__LFW__px; max-width:100%; height:auto; border:0;" />
                </a>
              </td>
            </tr>
            <tr><td height="3" bgcolor="__GREEN__" style="background-color:__GREEN__; height:3px; line-height:3px; font-size:3px;">&nbsp;</td></tr>
""").replace('__LOGO_WHITE__', LOGO_WHITE).replace('__LFW__', str(LOGO_FW)).replace('__LFH__', str(LOGO_FH)) \
    .replace('__SITE__', SITE).replace('__INK__', INK).replace('__GREEN__', GREEN)
    s += paper_open('34px 40px 10px 40px')
    s += ("""                      <div class="px">
                        {{ content.email_body }}
                      </div>
""")
    s += PAPER_CLOSE
    s += ("""            {% text 'simple_cta_label' label='Button label (leave blank to hide)', value='', no_wrapper=True, export_to_template_context=True %}
            {% text 'simple_cta_url' label='Button link', value='__CTA_URL__', no_wrapper=True, export_to_template_context=True %}
            {% if widget_data.simple_cta_label.value %}
            <tr>
              <td class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                  <tr>
                    <td class="px" align="left" bgcolor="__WHITE__" style="background-color:__WHITE__; padding:6px 40px 10px 40px;">
                      <table role="presentation" border="0" cellpadding="0" cellspacing="0" align="left" style="margin:0;">
                        <tr>
                          <td class="btn-td" align="center" bgcolor="__GREEN__" style="background-color:__GREEN__; border-radius:4px; padding:14px 30px; mso-padding-alt:14px 30px;">
                            <a href="{{ widget_data.simple_cta_url.value }}" style="display:block; font-family:__FONT__; font-size:16px; line-height:20px; font-weight:bold; color:#FFFFFF; text-decoration:none;">{{ widget_data.simple_cta_label.value }}</a>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            {% endif %}
            <tr>
              <td class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" class="paper" bgcolor="__WHITE__" style="background-color:__WHITE__;">
                  <tr>
                    <td class="px" bgcolor="__WHITE__" style="background-color:__WHITE__; padding:18px 40px 32px 40px; font-family:__FONT__; font-size:15px; line-height:25px; color:__BODY__;">
                      {% text 'signoff' label='Sign-off', value='&mdash; The Praxera team', no_wrapper=True %}
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
""").replace('__WHITE__', WHITE).replace('__GREEN__', GREEN).replace('__FONT__', FONT) \
    .replace('__BODY__', BODY).replace('__CTA_URL__', CTA_URL)
    s += FOOTER + CLOSE
    return s


TEMPLATES = {
    'Praxera - Newsletter.html': tpl_newsletter,
    'Praxera - Marketing Email.html': tpl_marketing,
    'Praxera - Blog Notification.html': tpl_blog,
    'Praxera - Simple Email.html': tpl_simple,
}

# --------------------------------------------------------------- preview ---
SAMPLE_IMG = 'https://www.praxerasupplements.com/hubfs/Praxera/Praxera%20Logo.png'
SAMPLE = {
    'site_settings.company_name': 'FoodScience LLC',
    'site_settings.company_street_address_1': '929 Harvest Lane',
    'site_settings.company_street_address_2': '',
    'site_settings.company_city': 'Williston',
    'site_settings.company_state': 'VT',
    'site_settings.company_zip': '05495',
    'site_settings.company_country': 'United States',
    'subscription_name': 'Praxera Supplements Blog Subscription',
    'unsubscribe_link': '#',
    'unsubscribe_link_all': '#',
    'post_title': 'Six questions to ask before you launch a private label supplement line',
    'post_url': '#',
    'post_image': SAMPLE_IMG,
    'post_excerpt': ('Minimums, lead times, label design and regulatory review all shape what your '
                     'first run looks like. Here is the short list we walk every practitioner brand '
                     'through before anything goes to print.'),
    'content.publish_date_localized': 'September 13, 2026',
    'content.blog_post_author.display_name': 'The Praxera Team',
    'content.email_body': (
        '<p>Practitioner brands come to Praxera with the same problem: patients trust the '
        'protocol, but there is nothing on the shelf with your name on it.</p>'
        '<p>Praxera is a private label partner. You choose from more than 190 finished formulas, '
        'we handle label design and turnkey production, and the product ships ready to sell under '
        'your brand. Everything is manufactured in the U.S. in a cGMP facility.</p>'
        '<ul><li>Low minimums on most formulas</li><li>Label design support included</li>'
        '<li>Backed by FoodScience LLC</li></ul>'),
}
ARTICLE_SAMPLE = {
    1: ('Choosing a delivery form your patients will actually take',
        'Capsules, powders, chewables or liquids &mdash; a short guide to matching format to compliance.'),
    2: ('What a practitioner-brand label has to say (and what it cannot)',
        'Claims, panels and the small print that keeps your line compliant.'),
    3: ('Five questions to ask before you launch a private label line',
        'Minimums, lead times, label design and the decisions that are hard to reverse.'),
}


def to_preview(src):
    """Crude HubL substitution so the layout can be rendered in a browser."""
    out = src

    # {% set %} lines -> drop (values injected via SAMPLE)
    out = re.sub(r'\{%\s*set\s+[^%]*%\}', '', out)

    # rich_text -> its default html, wrapped like HubSpot wraps it
    def _rt(m):
        html = re.search(r"html='(.*?)'\s*%\}", m.group(0), re.S)
        return '<div class="hs_cos_wrapper">%s</div>' % (html.group(1) if html else '')
    out = re.sub(r"\{%\s*rich_text\s+'[^']+'[^%]*%\}", _rt, out, flags=re.S)

    # exported widgets -> emit nothing, remember their defaults
    exported = {}

    def _exp(m):
        blk = m.group(0)
        name = re.search(r"\{%\s*(?:text|image)\s+'([^']+)'", blk).group(1)
        val = re.search(r"value='(.*?)'", blk, re.S)
        srcv = re.search(r"src='(.*?)'", blk, re.S)
        altv = re.search(r"alt='(.*?)'", blk, re.S)
        exported[name] = {'value': val.group(1) if val else '',
                          'src': srcv.group(1) if srcv else '',
                          'alt': altv.group(1) if altv else ''}
        return ''
    out = re.sub(r"\{%\s*(?:text|image)\s+'[^']+'[^%]*export_to_template_context=True\s*%\}",
                 _exp, out, flags=re.S)

    # sample article content
    for n, (h, t) in ARTICLE_SAMPLE.items():
        exported.setdefault('article_%d_headline' % n, {})['value'] = h
        exported.setdefault('article_%d_image' % n, {})['src'] = SAMPLE_IMG
        exported['article_%d_image' % n]['alt'] = h
        exported.setdefault('article_%d_url' % n, {})['value'] = '#'
        exported.setdefault('article_%d_link_label' % n, {})['value'] = 'Read more'
    if 'primary_cta_label' in exported:
        exported['primary_cta_label']['value'] = CTA_LABEL
    if 'simple_cta_label' in exported:
        exported['simple_cta_label']['value'] = 'Download the guide'
    if 'read_label' in exported:
        exported['read_label']['value'] = 'Read the post'

    # remaining inline text widgets -> their default value
    out = re.sub(r"\{%\s*text\s+'[^']+'[^%]*?value='(.*?)'[^%]*%\}", lambda m: m.group(1), out, flags=re.S)
    out = re.sub(r"\{%\s*text\s+'[^']+'[^%]*%\}", '', out, flags=re.S)

    # conditionals: keep the first branch, drop else branches for image-less variants
    out = re.sub(r"\{%\s*if\s+widget_data\.support_image\.src\s*%\}.*?\{%\s*endif\s*%\}", '', out, flags=re.S)
    out = re.sub(r"\{%\s*if\s+widget_data\.simple_cta_label\.value\s*%\}", '', out)
    out = re.sub(r"\{%\s*else\s*%\}.*?\{%\s*endif\s*%\}", '', out, flags=re.S)
    out = re.sub(r"\{%\s*if[^%]*%\}", '', out)
    out = re.sub(r"\{%\s*endif\s*%\}", '', out)

    # variables
    for n in ARTICLE_SAMPLE:
        SAMPLE['a%d_img' % n] = SAMPLE_IMG
        SAMPLE['a%d_copy_w' % n] = '318'

    def _var(m):
        expr = m.group(1).strip()
        base = expr.split('|')[0].strip()
        wd = re.match(r'widget_data\.([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)', base)
        if wd:
            return exported.get(wd.group(1), {}).get(wd.group(2), '')
        return SAMPLE.get(base, '')
    out = re.sub(r'\{\{(.*?)\}\}', _var, out, flags=re.S)

    out = re.sub(r'\{%.*?%\}', '', out, flags=re.S)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PREV, exist_ok=True)
    for fn, fn_build in TEMPLATES.items():
        src = fn_build()
        with open(os.path.join(OUT, fn), 'w') as f:
            f.write(src)
        pv = to_preview(src)
        with open(os.path.join(PREV, fn.replace('.html', '_preview.html')), 'w') as f:
            f.write(pv)
        print('wrote', fn, len(src), 'bytes')


if __name__ == '__main__':
    main()
