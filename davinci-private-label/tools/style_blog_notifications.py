"""Give the four Praxera blog-notification emails a real Praxera identity.

HubSpot scaffolds them from Start_from_scratch with its own demo palette - orange
placeholder logo, teal buttons, blue-grey type on #EAF0F6. This sets the Praxera
palette, puts the WHITE logo on a dark masthead so it survives dark mode, sizes the
logo from its real ink extent rather than its bounding box, and writes per-frequency
preview text.

The logo file is 612x208 but the visible wordmark is only x=88..524, y=74..141. A
naive "make it 200 wide" leaves the wordmark at ~142px and the rest transparent
padding - the same class of bug that stretched the logo in the 111 cloned emails.
For a 200px visible wordmark the declared box is 281x95, which keeps 612:208.

Safe to re-run. Dry run by default, --apply to write.
"""
import json, sys, copy
exec(open('/tmp/hs.py').read())

SUB_ID = '3608525332'
GREEN, INK, PAPER = '#6CA843', '#092637', '#F4F6F5'
LOGO_WHITE = 'https://www.praxerasupplements.com/hubfs/Praxera/Praxera%20Logo%20White.png'

PREVIEW = {
    'instant': 'A new post just went live on the Praxera blog.',
    'daily':   "Today's new thinking on building a private label supplement brand.",
    'weekly':  'Your weekly read on building a private label supplement brand.',
    'monthly': 'This month on the Praxera blog.',
}

STYLE = {
    'backgroundColor': PAPER,
    'bodyColor': '#FFFFFF',
    'bodyBorderColor': '#E2E7E5',
    'bodyBorderColorChoice': 'BORDER_MANUAL',
    'bodyBorderWidth': 1.0,
    'primaryFont': 'Helvetica, Arial, sans-serif',
    'primaryFontColor': '#33434C',
    'primaryFontSize': 16.0,
    'secondaryFont': 'Helvetica, Arial, sans-serif',
    'secondaryFontColor': INK,
    'headingOneFont': {'size': 30, 'color': INK, 'bold': True,
                       'font': 'Helvetica, Arial, sans-serif'},
    'headingTwoFont': {'size': 22, 'color': INK, 'bold': True,
                       'font': 'Helvetica, Arial, sans-serif'},
    'linksFont': {'color': GREEN, 'bold': False, 'italic': False, 'underline': True},
    'buttonStyleSettings': {
        'backgroundColor': GREEN,
        'cornerRadius': 4,
        'fontStyle': {'bold': True, 'color': '#FFFFFF', 'italic': False,
                      'font': 'Helvetica, Arial, sans-serif', 'size': 16,
                      'underline': False},
    },
    'dividerStyleSettings': {'color': {'color': '#E2E7E5', 'opacity': 100},
                             'height': 1, 'lineType': 'solid'},
}


def frequency(email):
    n = (email.get('name') or '').lower()
    for f in PREVIEW:
        if f in n:
            return f
    return None


def main(apply=False):
    emails, after = [], None
    while True:
        q = {'limit': 100, 'archived': 'false'}
        if after:
            q['after'] = after
        r = call('GET', '/marketing/v3/emails', q=q)
        emails += r.get('results', [])
        after = r.get('paging', {}).get('next', {}).get('after')
        if not after:
            break
    mine = [e for e in emails
            if (e.get('type') or '') == 'BLOG_EMAIL'
            and str((e.get('subscriptionDetails') or {}).get('subscriptionId')) == SUB_ID]
    print('Praxera blog-notification emails: %d' % len(mine))

    for e in mine:
        eid = e['id']
        live = call('GET', '/marketing/v3/emails/' + eid)      # re-read before writing
        freq = frequency(live)
        content = copy.deepcopy(live['content'])

        content['styleSettings'] = {**(content.get('styleSettings') or {}), **STYLE}

        w = content.get('widgets') or {}
        if 'builtin_image_module' in w:
            w['builtin_image_module']['body']['img'] = {
                'src': LOGO_WHITE, 'width': 281, 'height': 95,
                'alt': 'Praxera', 'align': 'center',
            }
        if freq and 'preview_text' in w:
            w['preview_text']['body']['value'] = PREVIEW[freq]

        # dark masthead so the white logo never sits on a light-mode white card
        for s in content.get('flexAreas', {}).get('main', {}).get('sections', []):
            ids = [x for c in s.get('columns', []) for x in (c.get('widgets') or [])]
            if 'builtin_image_module' in ids:
                s.setdefault('style', {})
                s['style']['backgroundColor'] = INK
                s['style']['paddingTop'] = '28px'
                s['style']['paddingBottom'] = '28px'

        if not apply:
            print('  %s  %-42s would restyle (freq=%s)' % (eid, (live.get('name') or '')[:42], freq))
            continue
        r = call('PATCH', '/marketing/v3/emails/' + eid, b={'content': content})
        ss = (r['content'].get('styleSettings') or {})
        img = ((r['content'].get('widgets') or {}).get('builtin_image_module') or {}).get('body', {}).get('img', {})
        print('  %s  %-42s bg=%s button=%s logo=%sx%s'
              % (eid, (r.get('name') or '')[:42], ss.get('backgroundColor'),
                 (ss.get('buttonStyleSettings') or {}).get('backgroundColor'),
                 img.get('width'), img.get('height')))
    if not apply:
        print('\nDry run. Re-run with --apply to write.')


if __name__ == '__main__':
    main(apply='--apply' in sys.argv)
