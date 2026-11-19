"""API clients (HubSpot, Gemini, TypeSafe Jev, ConnectAndSell). Keys come from the environment only."""
import os, json, ssl, time, urllib.request, urllib.parse, urllib.error

_CA = os.environ.get('SSL_CERT_FILE') or '/root/.ccr/ca-bundle.crt'
CTX = ssl.create_default_context(cafile=_CA) if os.path.exists(_CA) else ssl.create_default_context()


def _env(*names):
    for n in names:
        if os.environ.get(n):
            return os.environ[n]
    raise KeyError('missing env var: ' + ' or '.join(names))


# ---------------- HubSpot ----------------
def hs(method, path, body=None):
    tok = _env('HUBSPOT_TOKEN', 'QBS_HUBSPOT_TOKEN')
    for a in range(8):
        req = urllib.request.Request('https://api.hubapi.com' + path,
                                     json.dumps(body).encode() if body is not None else None,
                                     {'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'}, method=method)
        try:
            return json.load(urllib.request.urlopen(req, context=CTX, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 + a * 2); continue
            raise RuntimeError('HubSpot %s %s -> %s %s' % (method, path, e.code, e.read()[:300]))
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            time.sleep(2 + a * 2)
    raise RuntimeError('HubSpot retries exhausted: ' + path)


# ---------------- Gemini (primary text model), fallback chain ----------------
GEMINI_MODELS = ['gemini-3.5-flash', 'gemini-3.1-flash-lite']


def gemini(prompt):
    key = _env('GOOGLE_GEMINI_KEY')
    last = None
    for m in GEMINI_MODELS:
        for i in range(3):
            try:
                req = urllib.request.Request(
                    'https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent' % m,
                    json.dumps({'contents': [{'parts': [{'text': prompt}]}],
                                'generationConfig': {'responseMimeType': 'application/json', 'temperature': 0,
                                                     'thinkingConfig': {'thinkingBudget': 0}}}).encode(),
                    {'Content-Type': 'application/json', 'x-goog-api-key': key})
                d = json.load(urllib.request.urlopen(req, context=CTX, timeout=120))
                return json.loads(d['candidates'][0]['content']['parts'][0]['text']), m
            except Exception as e:
                last = str(e); time.sleep(2 * (i + 1))
    return {'error': last}, None

# ---------------- Claude (Anthropic API). Used first when ANTHROPIC_API_KEY is set, Gemini is the fallback ----------------
CLAUDE_MODELS = (os.environ.get('CI_CLAUDE_MODELS') or 'claude-sonnet-5-5,claude-haiku-5-5').split(',')


def _cc_messages(body):
    """Call the Anthropic API through ClientCommand's stored team key (env CLIENTCOMMAND_URL). The key never leaves ClientCommand."""
    req = urllib.request.Request(os.environ['CLIENTCOMMAND_URL'], json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {
        'name': 'call_internal_api', 'arguments': {'service': 'anthropic', 'method': 'POST', 'path': '/v1/messages',
                                                   'reason': 'Call Intel weekly scoring (transcript -> structured fields)', 'body': body}}}).encode(),
        {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}, method='POST')
    raw = urllib.request.urlopen(req, context=CTX, timeout=300).read().decode()
    if raw.lstrip().startswith('event') or 'data:' in raw[:20]:
        raw = [l[5:].strip() for l in raw.splitlines() if l.startswith('data:')][-1]
    r = json.loads(raw)
    if r.get('error'): raise RuntimeError(str(r['error'])[:200])
    out = json.loads(r['result']['content'][0]['text'])
    if not out.get('ok', out.get('status') == 200): raise RuntimeError('anthropic via ClientCommand: %s' % str(out)[:200])
    return out['data']


def claude_available():
    return bool(os.environ.get('ANTHROPIC_API_KEY') or os.environ.get('CLIENTCOMMAND_URL'))


def claude(prompt):
    key = os.environ.get('ANTHROPIC_API_KEY')
    if not key and not os.environ.get('CLIENTCOMMAND_URL'):
        return {'error': 'no Anthropic key or ClientCommand endpoint configured'}, None
    last = None
    for m in CLAUDE_MODELS:
        for i in range(3):
            body = {'model': m, 'max_tokens': 4096,
                    'system': 'Reply with a single JSON object only, no prose, no code fences.',
                    'messages': [{'role': 'user', 'content': prompt}]}
            try:
                if key:
                    req = urllib.request.Request('https://api.anthropic.com/v1/messages', json.dumps(body).encode(),
                                                 {'Content-Type': 'application/json', 'x-api-key': key, 'anthropic-version': '2023-06-01'})
                    d = json.load(urllib.request.urlopen(req, context=CTX, timeout=120))
                else:
                    d = _cc_messages(body)
                t = ''.join(b.get('text', '') for b in d['content'] if b.get('type') == 'text').strip()
                t = t[t.index('{'):t.rindex('}') + 1]
                return json.loads(t), m
            except urllib.error.HTTPError as e:
                last = 'HTTP %s %s' % (e.code, e.read()[:200])
                if e.code in (401, 402, 403): break   # key/billing problem: try the next provider
                time.sleep(2 * (i + 1))
            except Exception as e:
                last = str(e); time.sleep(2 * (i + 1))
    return {'error': last}, None


def llm(prompt):
    """Claude first (if a key is configured), then Gemini. Returns (json, model)."""
    if claude_available() and os.environ.get('CI_SCORER', 'claude') != 'gemini':
        o, m = claude(prompt)
        if 'error' not in o:
            return o, m
    return gemini(prompt)


# ---------------- TypeSafe Jev (typed decisions with calibrated probabilities) ----------------
def jev(state, questions):
    key = _env('JEV_API_KEY')
    req = urllib.request.Request('https://api.typesafe.ai/v1/systemone',
                                 json.dumps({'model': 'jev-latest', 'state': state[:30000], 'questions': questions}).encode(),
                                 {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key})
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(req, context=CTX, timeout=60))['answers']
        except Exception:
            time.sleep(1 + i)
    return None


# ---------------- ConnectAndSell Reporting API (read-only) ----------------
_tok = {'t': None, 'exp': 0}
_last = [0]
CAS = (os.environ.get('CAS_BASE_URL') or 'https://api.connectandsell.com').rstrip('/')  # set CAS_BASE_URL if CAS moves the API to a new host


def _cas_auth():
    body = urllib.parse.urlencode({'grant_type': 'password', 'username': _env('CAS_USER_ID'), 'password': _env('CAS_PASSWORD'),
                                   'ApiKey': _env('CAS_API_KEY'), 'SecretKey': os.environ.get('CAS_SECRET_KEY', '')}).encode()
    j = json.load(urllib.request.urlopen(urllib.request.Request(CAS + '/Authenticate', body,
                  {'Content-Type': 'application/x-www-form-urlencoded'}, method='POST'), context=CTX, timeout=60))
    _tok['t'] = j['access_token']; _tok['exp'] = time.time() + int(j.get('expires_in', 7000)) - 120


def cas(method, path, body=None):
    if not _tok['t'] or time.time() > _tok['exp']:
        _cas_auth()
    for a in range(5):
        w = 0.4 - (time.time() - _last[0])           # CAS allows <= 3 requests/second
        if w > 0: time.sleep(w)
        _last[0] = time.time()
        req = urllib.request.Request(CAS + path, json.dumps(body).encode() if body is not None else None,
                                     {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + _tok['t']}, method=method)
        try:
            return json.load(urllib.request.urlopen(req, context=CTX, timeout=120))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504): time.sleep(2 + a * 3); continue
            if e.code == 401: _tok['t'] = None; _cas_auth(); continue
            raise RuntimeError('CAS %s %s' % (e.code, e.read()[:300]))
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            time.sleep(3 + a * 5)
    raise RuntimeError('CAS retries exhausted')
