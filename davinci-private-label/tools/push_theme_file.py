#!/usr/bin/env python3
"""Upload one theme file, but only onto the version it was backed up from.

The footer work needed this and so does the blog CSS, so it is a tool rather
than another copy of the same twenty lines. It diffs local against live, refuses
if live has drifted from the recorded before-state (someone edited by hand since
the backup), uploads as multipart, then re-reads and proves the bytes match.

usage: python3 tools/push_theme_file.py <local> <theme path> <before file>
       python3 tools/push_theme_file.py ... --apply
"""
import difflib
import re
import sys
import urllib.parse
import urllib.request

API = 'https://api.hubapi.com/cms/v3/source-code/published/content/'
TOKEN = re.search(r'pat-na1-[0-9a-f-]+', open('/tmp/hs.py').read()).group(0)


def fetch(path):
    req = urllib.request.Request(API + urllib.parse.quote(path),
                                 headers={'Authorization': 'Bearer ' + TOKEN})
    return urllib.request.urlopen(req).read().decode('utf8', 'replace')


def push(path, body):
    boundary = '----hsthemeboundary'
    name = path.rsplit('/', 1)[-1]
    data = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
            f'filename="{name}"\r\nContent-Type: text/plain\r\n\r\n').encode()
    data += body.encode() + f'\r\n--{boundary}--\r\n'.encode()
    req = urllib.request.Request(
        API + urllib.parse.quote(path), data=data, method='PUT',
        headers={'Authorization': 'Bearer ' + TOKEN,
                 'Content-Type': f'multipart/form-data; boundary={boundary}'})
    return urllib.request.urlopen(req).read().decode()


def main():
    args = [a for a in sys.argv[1:] if a != '--apply']
    if len(args) != 3:
        raise SystemExit(__doc__)
    local, path, before_file = args

    new = open(local, encoding='utf-8').read()
    live = fetch(path)
    if live == new:
        print('already up to date - nothing to push')
        return

    print('\n'.join(difflib.unified_diff(
        live.splitlines(), new.splitlines(),
        fromfile=f'live {path}', tofile=f'new {local}', lineterm='')))

    expected = open(before_file, encoding='utf-8').read()
    if live != expected:
        raise SystemExit(f'\nREFUSED: live {path} is not the version in {before_file} - '
                         f'someone has edited it since. Re-read it before pushing.')

    if '--apply' not in sys.argv:
        print('\nDRY RUN - pass --apply to upload.')
        return

    print(push(path, new))
    print('verified live == new:', fetch(path) == new)


if __name__ == '__main__':
    main()
