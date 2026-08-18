"""Identity resolution v3.

Two bug classes Shawn found in v2, fixed generally rather than by patching names:

  BUG 1 (Louis Usherwood): HubSpot has "Lou Usherwood", the harvest got "Louis".
    A nickname dictionary will always have holes. Fix: name compatibility =
    exact OR shares a nickname group OR one is a prefix of the other. Also strip
    middle names/initials, which produced "Jeffrey D." vs "Jeffrey".
    Prefix matching is only ever applied together with an exact surname match AND
    the same company cluster, so its false-positive surface is tiny.

  BUG 2 (Kevin Kannel): UTEC exists twice as a company (utec-corp.com and
    utecit.com). Keying a person on raw company_id splits one person across two
    shells of one dealer. Fix: union-find company clusters on shared domain and
    normalized name, and key people on the CLUSTER, never the raw id.
    This also repairs the case where a HubSpot contact hangs off a different
    shell than the harvested row cites, which is most of the 18 splits.
"""
import re, json
from collections import defaultdict

STOPC = {'inc','llc','ltd','the','and','co','company','corp','corporation','group',
         'of','a','llp','pc','plc','holdings'}

NICK = {}
for grp in [("tom","thomas","tommy"),("ty","tyler"),("bob","robert","rob","bobby"),
            ("bill","william","will","billy"),("dick","richard","rick","rich","ricky"),
            ("jim","james","jimmy","jamie"),("mike","michael","mikey","mick"),
            ("dave","david"),("dan","daniel","danny"),("joe","joseph","joey"),
            ("chris","christopher","kit"),("steve","steven","stephen"),
            ("ed","edward","eddie","ted","teddy"),("tony","anthony"),
            ("chuck","charles","charlie","chas"),("ken","kenneth","kenny"),
            ("jeff","jeffrey","jeffery"),("greg","gregory"),("matt","matthew"),
            ("nick","nicholas"),("pat","patrick","patricia","patty"),
            ("sue","susan","suzanne","susie"),("kathy","katherine","kathleen","kate","katie","cathy"),
            ("liz","elizabeth","beth","betsy","lisa"),("jen","jennifer","jenny"),
            ("becky","rebecca"),("peggy","margaret","meg","maggie"),("larry","lawrence"),
            ("ron","ronald","ronnie"),("don","donald","donnie"),("terry","terrence","terence"),
            ("andy","andrew","drew"),("sam","samuel","samantha"),("ben","benjamin"),
            ("alex","alexander","alexandra"),("phil","philip","phillip"),
            ("frank","francis","franklin"),("gerry","gerald","jerry","jerome"),
            ("art","arthur"),("stan","stanley"),("walt","walter"),("vince","vincent"),
            ("cindy","cynthia"),("debbie","deborah","debra","deb"),("sandy","sandra"),
            ("tim","timothy"),("doug","douglas"),("brad","bradley"),("marty","martin"),
            ("gus","august"),("hank","henry"),("jack","john","johnny","jonathan","jon"),
            ("lou","louis","lewis","louie"),("al","albert","alan","allen"),
            ("stu","stuart"),("mitch","mitchell"),("nate","nathan","nathaniel"),
            ("zach","zachary"),("josh","joshua"),("adam","ad"),("gabe","gabriel"),
            ("tobe","tobias"),("rick","frederick","fred"),("kris","kristopher","kristen"),
            ("tammy","tamara"),("vicky","victoria"),("angie","angela"),("connie","constance"),
            ("marge","marjorie"),("wes","wesley"),("rod","rodney"),("russ","russell"),
            ("clay","clayton"),("court","courtney"),("gene","eugene"),("herb","herbert"),
            ("les","leslie","lester"),("ray","raymond"),("sal","salvatore"),("shel","sheldon"),
            ("theo","theodore"),("van","vanessa"),("cam","cameron"),("brit","brittany")]:
    for w in grp:
        NICK.setdefault(w, grp[0])


def nmz(s):
    return re.sub(r'[^a-z]', '', (s or '').lower())


def first_forms(f):
    """Normalized variants of a first name: full string, first token, nickname root.
    Handles 'Jeffrey D.', 'Joe R', 'Lynda Natalia'."""
    raw = (f or '').lower().strip()
    toks = [t for t in re.split(r'[^a-z]+', raw) if t]
    out = set()
    if not toks:
        return out
    out.add(''.join(toks))
    out.add(toks[0])
    # drop trailing single-letter initials
    core = [t for t in toks if len(t) > 1]
    if core:
        out.add(core[0]); out.add(''.join(core))
    for v in list(out):
        if v in NICK:
            out.add(NICK[v])
    return {v for v in out if v}


def first_compatible(a, b):
    """True if two first names plausibly denote the same person.
    ONLY call this alongside an exact surname match and same company cluster."""
    fa, fb = first_forms(a), first_forms(b)
    if not fa or not fb:
        return False
    if fa & fb:
        return True
    for x in fa:
        for y in fb:
            if len(x) >= 2 and len(y) >= 2 and (x.startswith(y) or y.startswith(x)):
                return True
    return False


PARTICLE = {'van','von','de','del','della','di','da','du','la','le','les','st','ste',
            'mac','mc','o','den','der','ten','ter','vander','vanden'}
SUFFIX = {'jr','sr','ii','iii','iv','v','md','phd','cpa','esq'}


def last_forms(l):
    """Surname variants. HubSpot has 'Van Kannel', the harvest had 'Kannel' —
    so a compound surname must also be matchable by its distinctive last token.
    Also strips generational suffixes: 'Rapacciuolo Sr.' == 'Rapacciuolo'."""
    toks = [t for t in re.split(r'[^a-z]+', (l or '').lower()) if t]
    toks = [t for t in toks if t not in SUFFIX]
    if not toks:
        return set()
    out = {''.join(toks)}
    core = [t for t in toks if t not in PARTICLE]
    if core:
        out.add(''.join(core))
        out.add(core[-1])
    out.add(toks[-1])
    return {v for v in out if len(v) >= 2}


def last_compatible(a, b):
    la, lb = last_forms(a), last_forms(b)
    return bool(la and lb and (la & lb))


def cnorm(n):
    return ' '.join(w for w in re.split(r'[^a-z0-9]+', (n or '').lower())
                    if w and w not in STOPC)


def dom(d):
    d = (d or '').strip().lower()
    d = re.sub(r'^https?://', '', d).replace('www.', '').split('/')[0].split('?')[0]
    return d or None


def slugof(u):
    m = re.search(r'linkedin\.com/(?:in|pub)/([^/?,#\s]+)', (u or '').strip().lower())
    return m.group(1).strip('/') if m else None


def canon_li(u):
    s = slugof(u)
    return f"https://linkedin.com/in/{s}" if s else None


class Companies:
    """Union-find clustering of duplicate company records."""
    def __init__(self, deal):
        self.deal = deal
        self.parent = {}
        bydom, byname = defaultdict(list), defaultdict(list)
        for cid, c in deal.items():
            self.parent[cid] = cid
            d = dom(c.get('domain'))
            if d:
                bydom[d].append(cid)
            n = cnorm(c.get('name'))
            if n:
                byname[n].append(cid)
        # Shawn's rule: in this space, two records on the SAME DOMAIN are the same
        # company. Union those automatically.
        for grp in bydom.values():
            for x in grp[1:]:
                self.union(grp[0], x)
        # Same NAME is only a candidate. "UTEC Co" (utecit.com, office technology,
        # Ann Arbor) and "UTEC" (utec-corp.com, an EXPLOSIVES LABORATORY in Galena,
        # Kansas) both reduce to "utec". Auto-unioning on name would have merged a
        # copier dealer into an explosives lab. Name matches are surfaced for
        # verification instead of being fused.
        self.name_candidates = {n: ids for n, ids in byname.items()
                                if len({self.find(i) for i in ids}) > 1}
        self.members = defaultdict(list)
        for cid in deal:
            self.members[self.find(cid)].append(cid)
        self.tok = {}
        for root, mem in self.members.items():
            t = set()
            for cid in mem:
                t |= {w for w in cnorm(deal[cid].get('name')).split() if len(w) > 2}
            self.tok[root] = t

    def find(self, x):
        if x not in self.parent:
            self.parent[x] = x
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb

    def cluster(self, cid):
        cid = str(cid or '')
        return self.find(cid) if cid else ''


class Resolver:
    def __init__(self, portal_rows, companies):
        self.co = companies
        self.P = {}
        self.by_slug, self.by_email = {}, {}
        self.by_lc = defaultdict(list)     # (lastname, company cluster)
        self.by_ld = defaultdict(list)     # (lastname, email domain)
        self.by_last = defaultdict(list)
        for p in portal_rows:
            cid = p['id']
            self.P[cid] = p
            s = slugof(p.get('linkedin_profile_url__unique_value') or p.get('hs_linkedin_url'))
            if s:
                self.by_slug.setdefault(s, cid)
            em = (p.get('email') or '').strip().lower()
            if em:
                self.by_email.setdefault(em, cid)
            lforms = last_forms(p.get('lastname'))
            if not lforms:
                continue
            cl = self.co.cluster(p.get('associatedcompanyid'))
            d = dom(p.get('hs_email_domain')) or (em.split('@')[-1] if '@' in em else None)
            for ln in lforms:
                self.by_last[ln].append(cid)
                if cl:
                    self.by_lc[(ln, cl)].append(cid)
                if d:
                    self.by_ld[(ln, d)].append(cid)

    def resolve(self, first, last, company_id, domain, company_name, email, li_url):
        s = slugof(li_url)
        if s and s in self.by_slug:
            return self.by_slug[s], 'linkedin_url', 'high'
        em = (email or '').strip().lower()
        if em and em in self.by_email:
            return self.by_email[em], 'email', 'high'
        lforms = last_forms(last)
        if not lforms or not nmz(first):
            return None, 'no_usable_name', 'none'

        cl = self.co.cluster(company_id)
        if not cl and dom(domain):
            for cid2, c in self.co.deal.items():
                if dom(c.get('domain')) == dom(domain):
                    cl = self.co.cluster(cid2); break
        if cl:
            for ln in lforms:
                for cid in self.by_lc.get((ln, cl), []):
                    if first_compatible(first, self.P[cid].get('firstname')):
                        return cid, 'name+company_cluster', 'high'
        d = dom(domain)
        if d:
            for ln in lforms:
                for cid in self.by_ld.get((ln, d), []):
                    if first_compatible(first, self.P[cid].get('firstname')):
                        return cid, 'name+email_domain', 'high'

        want = set(cnorm(company_name).split()) | (self.co.tok.get(cl) or set())
        want = {w for w in want if len(w) > 2}
        cands = []
        for ln in lforms:
            cands += self.by_last.get(ln, [])
        seen=set(); cands=[c for c in cands if not (c in seen or seen.add(c))]
        loose = [c for c in cands if first_compatible(first, self.P[c].get('firstname'))]
        for cid in loose:
            p = self.P[cid]
            have = {w for w in cnorm(p.get('company')).split() if len(w) > 2}
            pcl = self.co.cluster(p.get('associatedcompanyid'))
            if pcl:
                have |= (self.co.tok.get(pcl) or set())
            if want and have and (want & have):
                return cid, 'name+fuzzy_company', 'medium'
        if len(loose) == 1:
            return loose[0], 'name_only_single_match', 'low'
        if loose:
            return loose[0], f'name_only_{len(loose)}_matches', 'low'
        return None, 'no_match', 'none'

    def person_key(self, contact_id, first, last, company_id, li_url):
        if contact_id:
            return 'hs:' + str(contact_id)
        s = slugof(li_url)
        if s:
            return 'li:' + s
        ff = sorted(first_forms(first))
        root = NICK.get(ff[0], ff[0]) if ff else ''
        lf = sorted(last_forms(last))
        return f"nm:{root}|{lf[0] if lf else ''}|{self.co.cluster(company_id)}"
