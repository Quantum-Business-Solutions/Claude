#!/usr/bin/env python3
"""Build the "who is reviewing?" box for a ClientCommand sign-off sheet.

One source, one per client. The sheets are opened on a no-login share link, so
the portal sends the page no user: it has no name and no side, refuses marks,
and only scrolls the identity bar when you press one, which reads as a dead
button. This box asks who is looking, once, on arrival — one click sets the
name and the client side and every button works from then on.

It is a no-op for QBS: a signed-in team member gets "Signed in as …" and no
#who box, so it never builds.

The only things that differ per client are the names and one line of copy. It
hooks on #who and button.sd[data-s="client"], which every build of the app has —
check with `grep -c 'data-s="client"'` against a client's boot before deploying.

Stopgap. The durable fix is in src/signoff.js and belongs in ClientCommand's
asset-signoff template; drop these sections once that ships.

usage: build_clientlink_box.py <client>      # praxera | revolution
       build_clientlink_box.py --all
"""
import sys

CLIENTS = {
    'praxera': {
        'people': ['Tammy Johnson', 'Melinda Elmadjian', 'Sarah Miller'],
        'subline': 'So your approvals are recorded against your name. '
                   'You only need to do this once.',
        'fallback': 'Praxera (client link)',
        'portal': '6d797a44-e010-410f-b532-64ac42627d64',
        'slug': 'praxera-asset-signoff',
    },
    'revolution': {
        # Revolution Office has one client account on the portal, Tom Menton.
        # Anyone else arrives through the share link and types their own name.
        'people': ['Tom Menton'],
        # Their sheet says "Verified ✓" rather than "Approved", so the copy
        # stays neutral about what the marks are called.
        'subline': 'So your marks are recorded against your name. '
                   'You only need to do this once.',
        'fallback': 'Revolution Office (client link)',
        'portal': 'b483aef1-a9ee-4c0c-b83b-056c64a01e21',
        'slug': 'revolution-website-signoff',
    },
}

TEMPLATE = '''<script>
/* Client share link — ask who is reviewing, once, on arrival.
   Built by tools/build_clientlink_box.py for %(client)s. */
(function () {
  var PEOPLE = %(people)s;
  var FALLBACK = %(fallback)s;
  var tries = 0, done = false;
  function apply(name) {
    if (done) return;
    done = true;
    var who = document.getElementById("who");
    if (who) { who.value = name; who.dispatchEvent(new Event("input", { bubbles: true })); }
    var btn = document.querySelector('button.sd[data-s="client"]');
    if (btn && btn.getAttribute("aria-pressed") !== "true") btn.click();
  }
  function close(el, name) {
    if (el && el.parentNode) el.parentNode.removeChild(el);
    apply(name);
  }
  function ask() {
    var wrap = document.createElement("div");
    wrap.setAttribute("role", "dialog");
    wrap.setAttribute("aria-modal", "true");
    wrap.setAttribute("aria-label", "Who is reviewing");
    wrap.style.cssText = "position:fixed;inset:0;z-index:9999;background:rgba(9,38,55,.55);display:flex;align-items:center;justify-content:center;padding:20px;font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif";
    var card = document.createElement("div");
    card.style.cssText = "background:#fff;border-radius:12px;max-width:420px;width:100%%;padding:26px 26px 20px;box-shadow:0 18px 50px rgba(9,38,55,.3)";
    wrap.appendChild(card);
    var h = document.createElement("h2");
    h.textContent = "Who is reviewing today?";
    h.style.cssText = "margin:0 0 6px;font-size:20px;line-height:1.25;color:#092637";
    card.appendChild(h);
    var p = document.createElement("p");
    p.textContent = %(subline)s;
    p.style.cssText = "margin:0 0 18px;color:#5b6472;font-size:14px";
    card.appendChild(p);
    PEOPLE.forEach(function (n) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = n;
      b.style.cssText = "display:block;width:100%%;margin:0 0 8px;padding:12px 14px;text-align:left;border:1px solid #d9dee6;border-radius:8px;background:#fff;cursor:pointer;font:inherit;color:#092637";
      b.onmouseover = function () { b.style.borderColor = "#6CA843"; b.style.background = "#f4faf0"; };
      b.onmouseout = function () { b.style.borderColor = "#d9dee6"; b.style.background = "#fff"; };
      b.onclick = function () { close(wrap, n); };
      card.appendChild(b);
    });
    var row = document.createElement("div");
    row.style.cssText = "display:flex;gap:8px;margin-top:14px";
    card.appendChild(row);
    var input = document.createElement("input");
    input.type = "text";
    input.placeholder = "Someone else — your name";
    input.setAttribute("aria-label", "Your name");
    input.style.cssText = "flex:1;padding:11px 12px;border:1px solid #d9dee6;border-radius:8px;font:inherit";
    row.appendChild(input);
    var go = document.createElement("button");
    go.type = "button";
    go.textContent = "Start";
    go.style.cssText = "padding:11px 18px;border:0;border-radius:8px;background:#6CA843;color:#fff;cursor:pointer;font:inherit;font-weight:600";
    go.onclick = function () { close(wrap, input.value.trim() || FALLBACK); };
    row.appendChild(go);
    input.addEventListener("keydown", function (e) { if (e.key === "Enter") go.click(); });
    var skip = document.createElement("button");
    skip.type = "button";
    skip.textContent = "Skip";
    skip.style.cssText = "margin-top:14px;border:0;background:none;color:#5b6472;cursor:pointer;font:inherit;font-size:13px;text-decoration:underline;padding:0";
    skip.onclick = function () { close(wrap, FALLBACK); };
    card.appendChild(skip);
    document.body.appendChild(wrap);
    card.querySelector("button").focus();
  }
  function start() {
    var who = document.getElementById("who");
    var btn = document.querySelector('button.sd[data-s="client"]');
    if ((!who || !btn) && tries++ < 40) return setTimeout(start, 300);
    if (!who || !btn) return;      /* signed in through the portal — leave alone */
    if (who.value) return;         /* already identified */
    ask();
  }
  setTimeout(start, 600);
})();
</script>
'''


def build(client):
    import json
    c = CLIENTS[client]
    return TEMPLATE % {
        'client': client,
        'people': json.dumps(c['people']),
        'fallback': json.dumps(c['fallback']),
        'subline': json.dumps(c['subline']),
    }


def main():
    args = sys.argv[1:]
    targets = list(CLIENTS) if (not args or args[0] == '--all') else args
    for t in targets:
        if t not in CLIENTS:
            raise SystemExit(f'unknown client {t!r}; known: {", ".join(CLIENTS)}')
        out = f'tools/clientlink_{t}.html'
        body = build(t)
        open(out, 'w').write(body)
        c = CLIENTS[t]
        print(f'{t:11} {len(body):>6} chars -> {out}')
        print(f'            portal {c["portal"]}  slug {c["slug"]}')
        print(f'            names: {", ".join(c["people"])}')


if __name__ == '__main__':
    main()
