#!/usr/bin/env python3
"""Un-delete the hero (and faq / disclaimer) modules on the Praxera blog posts.

What happened
-------------
In two bursts today - 19:22-19:35 and 20:02 UTC - the `hero`, `faq` and
`disclaimer` widgets on 25 published posts were flagged `deleted_at`. The saved
content is untouched: `widgets.hero.body` still holds the right eyebrow,
headline, subhead and background image, all the way back through every revision
to 29 Aug. Only the delete flag is set.

With the instance deleted, the template renders `PL - Hero`'s *default* field
values instead, which is why 25 posts all show the same header:

    eyebrow  PRIVATE LABEL SUPPLEMENTS          (saved: PRIVATE LABEL SUPPLEMENTS BLOG)
    headline Your brand. Our formulations.      (saved: the post's own title, as an h1)
    subhead  250+ doctor-formulated products... (saved: the byline and date)
    button   Schedule a Consultation            (saved: none)
    theme    light                              (saved: dark)

So the repair is to drop `deleted_at` and put the saved body back. Nothing is
rewritten - whatever `.before.json` holds is what goes back.

Before-state: backups/blog-hero-restore/{id}.before.json (all 72 posts)

usage: python3 tools/restore_blog_hero.py                    # dry run, lists what it would do
       python3 tools/restore_blog_hero.py --one <post_id>    # repair a single post
       python3 tools/restore_blog_hero.py --apply            # repair all of them
       python3 tools/restore_blog_hero.py --apply --widgets hero
                                                             # only the hero, leave faq/disclaimer
"""
import argparse
import json
import os
import sys
import time

BACKUP = 'backups/blog-hero-restore'
WIDGETS = ('hero', 'faq', 'disclaimer', 'article_body')

exec(open('/tmp/hs.py').read())  # noqa: provides call()


def deleted_widgets(post, wanted):
    """The widgets on this post that carry a deleted_at flag."""
    out = {}
    for name, w in (post.get('widgets') or {}).items():
        if name in wanted and isinstance(w, dict) and w.get('deleted_at'):
            out[name] = w
    return out


def repair(post_id, wanted, apply_it, from_backup=False):
    live = call('GET', f'/cms/v3/blogs/posts/{post_id}')
    bad = deleted_widgets(live, wanted)
    if not bad:
        return 'clean', {}

    # Re-read the backup and make sure the body we are restoring is the body that
    # was there before - the flag is the only thing this script is allowed to change.
    before = json.load(open(os.path.join(BACKUP, f'{post_id}.before.json')))
    for name, w in bad.items():
        was = ((before.get('widgets') or {}).get(name) or {})
        if json.dumps(was.get('body'), sort_keys=True) != json.dumps(w.get('body'), sort_keys=True):
            if not from_backup:
                raise SystemExit(
                    f'REFUSED {post_id}/{name}: the live body differs from the backup. Look at '
                    f'the diff first, then re-run with --from-backup to put the backup body back.')

    # PATCH replaces the whole `widgets` map: anything left out of the payload comes
    # back flagged deleted_at. Learned the hard way - a first pass sent only the
    # widgets it meant to repair and knocked out the ones it had not mentioned. So
    # send every widget the post has, every time, and only strip the flag.
    payload = {}
    for name, w in (live.get('widgets') or {}).items():
        out = {k: v for k, v in w.items() if not (k == 'deleted_at' and name in wanted)}
        if from_backup and name in wanted:
            was = ((before.get('widgets') or {}).get(name) or {})
            if was.get('body') is not None:
                out['body'] = was['body']
        payload[name] = out

    if not apply_it:
        return 'would restore', payload

    call('PATCH', f'/cms/v3/blogs/posts/{post_id}', b={'widgets': payload})
    call('POST', f'/cms/v3/blogs/posts/{post_id}/draft/push-live', b={})

    after = call('GET', f'/cms/v3/blogs/posts/{post_id}')
    still = deleted_widgets(after, wanted)
    if still:
        return 'FAILED - still deleted: ' + ','.join(still), payload
    return 'restored', payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--one')
    ap.add_argument('--from-backup', action='store_true',
                    help='put the backup body back where the live body has drifted')
    ap.add_argument('--widgets', default=','.join(WIDGETS),
                    help='comma-separated subset of hero,faq,disclaimer,article_body')
    a = ap.parse_args()
    wanted = tuple(x.strip() for x in a.widgets.split(',') if x.strip())

    ids = [a.one] if a.one else [f[:-len('.before.json')] for f in sorted(os.listdir(BACKUP))
                                 if f.endswith('.before.json')]

    counts = {}
    for pid in ids:
        status, payload = repair(pid, wanted, a.apply, a.from_backup)
        counts[status.split(' -')[0]] = counts.get(status.split(' -')[0], 0) + 1
        if status != 'clean':
            name = call('GET', f'/cms/v3/blogs/posts/{pid}', q={'property': 'id,name'}).get('name', '')
            print(f'  {status:<14} {pid}  {name[:58]}  [{", ".join(payload)}]')
        if a.apply:
            time.sleep(0.3)

    print('\n' + '  '.join(f'{k}: {v}' for k, v in sorted(counts.items())))
    if not a.apply:
        print('\nDRY RUN - pass --apply to write.')


if __name__ == '__main__':
    main()
