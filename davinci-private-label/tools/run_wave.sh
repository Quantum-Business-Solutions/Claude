#!/usr/bin/env bash
# Swap icons on one or more pages, with the checks that make it reversible.
#
# Every step here exists because something went wrong without it:
#   snapshot  a PATCH to /draft creates no HubSpot revision, so the revision
#             history will not show the change and cannot roll it back. The
#             snapshot is the only undo that exists.
#   dry run   the swap keys on the card's own label, so read what it intends
#             to do before it does it. A "~" marks a stretch match, not a match.
#   apply     re-reads each page immediately before writing and skips it if
#             someone saved in between.
#   qa        full field diff on the page you touched, plus a draft-timestamp
#             check on the other 136. The swap tool's own readback cannot see a
#             page it never opened, and the sweep costs about six seconds.
#   shot      renders the real draft through HubSpot's preview and reports
#             any broken or mis-sized icon, which no JSON diff can catch.
#
# usage: TOKEN=... tools/run_wave.sh <slug> [slug ...]
set -euo pipefail
cd "$(dirname "$0")/.."
[ $# -ge 1 ] || { echo "usage: TOKEN=... tools/run_wave.sh <slug> [slug ...]"; exit 2; }
: "${TOKEN:?set TOKEN to the HubSpot private-app token}"

echo "=== 1/5  snapshot (the only undo) ============================="
SNAP=$(python3 tools/snapshot.py | tee /dev/stderr | sed -n 's#.*-> .*/snapshots/pages/\(.*\)/#\1#p')
[ -n "$SNAP" ] || { echo "snapshot failed"; exit 1; }

echo; echo "=== 2/5  dry run ============================================="
python3 tools/icon_swap.py "$@"
echo
read -r -p "apply these changes? [y/N] " ok
[ "$ok" = y ] || { echo "stopped. snapshot kept at snapshots/pages/$SNAP"; exit 0; }

echo; echo "=== 3/5  apply ==============================================="
python3 tools/icon_swap.py "$@" --apply

echo; echo "=== 4/5  QA: the pages touched, in full; the rest by timestamp ="
python3 tools/qa_write.py "snapshots/pages/$SNAP" --expect "$@"

echo; echo "=== 5/5  render each page and check the icons ================="
for s in "$@"; do
  python3 tools/preview_shot.py "$s" --out "/tmp/shot_${s//\//_}"
done

echo
echo "done. to undo:  TOKEN=... python3 tools/snapshot.py --restore $SNAP $*"
