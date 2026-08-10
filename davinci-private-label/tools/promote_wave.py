#!/usr/bin/env python3
"""Promote a page only if it measures clean, right now.

Waves, not batches: a page that reads zero goes live on its own record
immediately, a page that does not stays a draft. Nothing is promoted on the
strength of a sibling passing, and nothing is promoted on a gate result taken
before the last rebuild -- the gate is re-run here, in this process, so the
measurement and the promotion cannot drift apart.

Order matters and is the whole point. Verify, snapshot, promote, verify again.
Promoting first is what cost this project three days: a promoted page no longer
holds its original markup, so the evidence needed to judge it is gone.

usage: promote_wave.py <name> <V1_ID> <V3_ID> [--dry]
       promote_wave.py --list <file>      one "<name> <V1_ID> <V3_ID>" per line
"""
import os, sys, json, time, subprocess, datetime

S    = os.path.dirname(os.path.abspath(__file__)) + '/'
REPO = '/home/user/Claude/davinci-private-label/snapshots/v1-pre-promotion/'


def sh(cmd):
    p = subprocess.run(cmd, shell=True, cwd=S, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def snapshot(v1id):
    """The page exactly as it is before anything is written to it."""
    os.makedirs(REPO, exist_ok=True)
    path = REPO + f"{v1id}.json"
    # One unparseable response used to abort the page silently. A transient API
    # hiccup is not a reason to skip a snapshot -- it is a reason to ask again.
    page = None
    for attempt in range(4):
        rc, out = sh(f'curl -s --fail --retry 2 -H "Authorization: Bearer $TOKEN" '
                     f'"https://api.hubapi.com/cms/v3/pages/site-pages/{v1id}"')
        try:
            page = json.loads(out); break
        except Exception:
            if attempt == 3:
                print(f"    could not read {v1id} after 4 attempts: {out[:120]}")
                return None
            time.sleep(2 ** attempt)
    widgets = (page.get('widgetContainers') or {}).get('main_content', {}).get('widgets', [])
    if not widgets:
        # already promoted, or empty: never overwrite a good snapshot with an empty one
        return path if os.path.exists(path) else None
    json.dump(page, open(path, 'w'), indent=1)
    return path


def one(name, v1id, v3id, dry=False):
    stamp = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"[{stamp}] {name}")

    rc, out = sh(f"python3 vis/gate.py {v1id} {v3id} {name} 2>&1 | grep -v '^127.0.0.1'")
    verdict = [l for l in out.splitlines() if ' PASS ' in l or ' FAIL ' in l]
    for l in verdict: print("   ", l.strip())
    if rc != 0:
        for l in out.splitlines():
            if l.strip().startswith('-'): print("       ", l.strip())
        print(f"    HELD as a draft -- the gate is not clean")
        return False

    if dry:
        print("    would promote (dry run)"); return True

    snap = snapshot(v1id)
    if not snap:
        print("    ABORT: no pre-promotion snapshot could be written"); return False
    print(f"    snapshot -> {os.path.basename(snap)}")

    rc, out = sh(f"python3 promote/promote.py {v3id} {v1id}")
    print("   ", out.strip().splitlines()[-1] if out.strip() else "(no output)")
    if rc != 0:
        print("    promotion refused or rolled back -- page left as it was")
        return False

    # The draft measured clean; now prove the promoted record does too. The
    # reference is the mirror captured before promotion -- passing the V1 id
    # again would re-mirror the page we just converted and compare it with
    # itself, which passes no matter what went wrong.
    rc, out = sh(
        'python3 -c "'
        "import sys; sys.path.insert(0,'vis'); import gate; "
        f"ok,_ = gate.run(None, '{v1id}', '{name}'); sys.exit(0 if ok else 1)\" "
        "2>&1 | grep -v '^127.0.0.1' | grep -E 'PASS|FAIL|  - '")
    for l in out.strip().splitlines(): print("   ", l.strip())
    if rc != 0:
        print("    PROMOTED BUT THE RECORD DOES NOT MEASURE CLEAN -- inspect before showing it")
        return False
    print("    promoted, slug unchanged, promoted record re-verified")
    return True


if __name__ == '__main__':
    if '--list' in sys.argv:
        rows = [l.split() for l in open(sys.argv[sys.argv.index('--list') + 1])
                if l.strip() and not l.startswith('#')]
    else:
        rows = [sys.argv[1:4]]
    dry = '--dry' in sys.argv
    done = [one(n, a, b, dry) for n, a, b in rows]
    print(f"\npromoted {sum(done)} of {len(done)}; "
          f"{len(done) - sum(done)} held as drafts")
