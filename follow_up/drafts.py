"""Create Outlook DRAFTS (never sends) via ClientCommand's personal Microsoft connection.

    python3 -m follow_up.drafts emails.json [--cap 15]

emails.json = [{"to": ["a@b.com"], "subject": "...", "body": "..."}]. Every draft is plain text,
BCCs the HubSpot logging address so the send is recorded on the contact, and ends with the signature.
Stops at --cap drafts per run. Env: CLIENTCOMMAND_URL (contains a token; never print it).
"""
import os, sys, json, ssl, urllib.request

BCC = os.environ.get('CI_HUBSPOT_BCC', '20682069@bcc.hubspot.com')
SIG = '\n\nThanks,\nShawn\nQuantum Business Solutions'
_CA = os.environ.get('SSL_CERT_FILE') or '/root/.ccr/ca-bundle.crt'
_CTX = ssl.create_default_context(cafile=_CA) if os.path.exists(_CA) else ssl.create_default_context()


def rpc(name, args):
    req = urllib.request.Request(os.environ['CLIENTCOMMAND_URL'],
                                 json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}).encode(),
                                 {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}, method='POST')
    raw = urllib.request.urlopen(req, context=_CTX, timeout=120).read().decode()
    if 'data:' in raw[:20]:
        raw = [l[5:].strip() for l in raw.splitlines() if l.startswith('data:')][-1]
    return json.loads(raw)['result']['content'][0]['text']


def make(emails, cap=15):
    out = []
    for e in emails[:cap]:
        body = e['body'].rstrip()
        if not body.endswith('Quantum Business Solutions'):
            body += SIG
        out.append((e['subject'], rpc('draft_my_email', {'to': e['to'], 'bcc': [BCC], 'subject': e['subject'], 'body': body, 'body_type': 'Text'})))
    return out


if __name__ == '__main__':
    cap = int(sys.argv[sys.argv.index('--cap') + 1]) if '--cap' in sys.argv else 15
    for s, r in make(json.load(open(sys.argv[1])), cap):
        print(s, 'OK' if '"id"' in r else r[:120])
