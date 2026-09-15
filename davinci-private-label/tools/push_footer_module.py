#!/usr/bin/env python3
"""Upload the corrected Global Footer module to the Private Label theme.

Fixes two things at once:

  1. All eleven footer links rendered href="#" on all 68 pages. They came from
     module.footer_menu, whose simple-menu fields have labels but no
     destinations - the same fault as the header menu on 3 Sep. That one was
     repairable because an advanced menu is an API object; these simple-menu
     values live in the module's GLOBAL CONTENT, which HubSpot exposes on no
     API path (seventeen tried). So the columns are written into module.html
     instead, with destinations verified 200.

  2. Phone and email under the physical address, per Shawn:
     1-800-325-1776 and info@praxerasupplements.com, as tel: and mailto: links.

The address text itself still comes from {{ module.address }} - global content -
so the FoodScience sentence and the open (R) question are untouched.

Before-state: backups/footer-contact/*.published.2026-09-15

usage: python3 tools/push_footer_module.py          # dry run, shows the diff
       python3 tools/push_footer_module.py --apply
"""
import difflib
import re
import sys
import urllib.parse
import urllib.request

PATH = 'Private Label/Modules/Global Footer.module/module.html'
LOCAL = 'modules/Global Footer.module.html'
BEFORE = 'backups/footer-contact/module.html.published.2026-09-15b'
API = 'https://api.hubapi.com/cms/v3/source-code/published/content/'

TOKEN = re.search(r'pat-na1-[0-9a-f-]+', open('/tmp/hs.py').read()).group(0)


def fetch():
    u = API + urllib.parse.quote(PATH)
    req = urllib.request.Request(u, headers={'Authorization': 'Bearer ' + TOKEN})
    return urllib.request.urlopen(req).read().decode('utf8', 'replace')


def push(body):
    boundary = '----hsfooterboundary'
    data = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="module.html"\r\nContent-Type: text/html\r\n\r\n').encode()
    data += body.encode() + f'\r\n--{boundary}--\r\n'.encode()
    req = urllib.request.Request(
        API + urllib.parse.quote(PATH), data=data, method='PUT',
        headers={'Authorization': 'Bearer ' + TOKEN,
                 'Content-Type': f'multipart/form-data; boundary={boundary}'})
    return urllib.request.urlopen(req).read().decode()


def main():
    new = open(LOCAL, encoding='utf-8').read()
    live = fetch()

    if live == new:
        print('already up to date - nothing to push')
        return

    print('\n'.join(difflib.unified_diff(
        live.splitlines(), new.splitlines(),
        fromfile='live module.html', tofile='new module.html', lineterm='')))

    # the live copy must still be the one we backed up, or someone edited it since
    expected = open(BEFORE, encoding='utf-8').read()
    if live != expected:
        raise SystemExit('\nREFUSED: the live module.html is not the version backed up '
                         'on 15 Sep - someone has edited it since. Re-read it before pushing.')

    if '--apply' not in sys.argv:
        print('\nDRY RUN - pass --apply to upload.')
        return

    print(push(new))
    after = fetch()
    print('verified live == new:', after == new)


if __name__ == '__main__':
    main()
