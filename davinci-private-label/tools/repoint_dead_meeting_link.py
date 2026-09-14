#!/usr/bin/env python3
"""Repoint the dead round-robin meeting link in six Praxera emails to /get-started.

https://meetings.hubspot.com/samantha-fuller/private-label-round-robin does not
resolve to a real scheduler. meetings.hubspot.com answers HTTP 200 with an 82KB
JavaScript shell for EVERY slug, real or invented, so the 200 proves nothing -
the portal's own scheduler API is the authority, and this slug is not in it.

The copy around every one of these links is "book a call" / "schedule a quick
call" / "grab a few minutes from our calendar", so /get-started - the Schedule a
Consultation page - is the right landing place, per Shawn on 14 Sep.

All six emails are DRAFT, so nothing is sent or published by this.

usage: repoint_dead_meeting_link.py [--apply]
"""
import json
import sys

exec(open('/tmp/hs.py').read())

DEAD = 'https://meetings.hubspot.com/samantha-fuller/private-label-round-robin'
NEW = 'https://www.praxerasupplements.com/get-started'

EMAILS = {
    '220685976456': 'Private_Label_Guide_ToF_Paul_Get Started_Private_Label_With_Praxera',
    '220685976586': '1: Private Label Guide: High-Priority',
    '220688283275': 'Private Label: High Priority - 6 Benefits',
    '220692678021': 'Private Label: High Priority - how to make money',
    '220692678023': '3: Private_Label_Guide_ToF_Paul_ Step-by-step Guide to managing shipping and Inventory',
    '220692678044': 'Private_Label_Guide_ToF_Paul_6_Benefits of Selling PL',
}


def main():
    dry = '--apply' not in sys.argv
    log = {}
    for eid, label in EMAILS.items():
        email = call('GET', f'/marketing/v3/emails/{eid}')
        assert email['state'] == 'DRAFT', f'{eid} is {email["state"]}, not DRAFT'
        blob = json.dumps(email['content'])
        n = blob.count(DEAD)
        if not n:
            print(f'{eid}  {label[:48]:50} already clean')
            continue
        log[eid] = {'name': label, 'replaced': n}
        print(f'{eid}  {label[:48]:50} {n} link(s)')
        if not dry:
            call('PATCH', f'/marketing/v3/emails/{eid}',
                 b={'content': json.loads(blob.replace(DEAD, NEW))})

    json.dump(log, open('reference/meeting_link_repoint.json', 'w'), indent=1)
    total = sum(v['replaced'] for v in log.values())
    print(f'\n{total} link(s) across {len(log)} email(s)')
    if dry:
        print('DRY RUN - pass --apply to write.')


if __name__ == '__main__':
    main()
