import re,json,copy,sys
TOK=re.compile(r"(\{\{.*?\}\}|<[^>]*>)",re.S)
EL=re.compile(r"(<(p|h1)\b[^>]*>)(.*?)(</\2>)",re.S)
def words_outside(inner):
    return len(re.findall(r"\S+",re.sub(r"<[^>]*>|\{\{.*?\}\}","X",inner)))
def bind_inner(inner,k):
    parts=TOK.split(inner)  # alternating text, markup
    # positions of bindable spaces: single ' ' inside text parts, with a non-space char on both sides within the text, or touching a token/tag boundary
    idx=[]  # (part_index, char_index)
    for pi,p in enumerate(parts):
        if pi%2==1: continue
        for m in re.finditer(r"(?<=\S) (?=\S)",p): idx.append((pi,m.start()))
    # also spaces that sit at a text/token boundary, e.g. 'word {{token}}' : handled because the space is inside the text part next to token
    for pi,p in enumerate(parts):
        if pi%2==1: continue
        for m in re.finditer(r"(?<=\S) $|^ (?=\S)",p):
            idx.append((pi,m.start()))
    idx=sorted(set(idx))
    if not idx: return inner
    chosen=idx[-k:]
    for pi,ci in sorted(chosen,key=lambda x:(x[0],-x[1]),reverse=False):
        pass
    # replace from the end so indexes stay valid
    for pi,ci in sorted(chosen,key=lambda x:(x[0],x[1]),reverse=True):
        p=parts[pi]; parts[pi]=p[:ci]+'&nbsp;'+p[ci+1:]
    return ''.join(parts)
def skip(open_tag,inner):
    if 'letter-spacing:1.6px' in open_tag or 'letter-spacing:1.5px' in open_tag: return True   # small caps labels
    if inner.lstrip().startswith('<span') and 'border-radius:100px' in inner and words_outside(inner)<=4 and 'font-size:11px' in inner: return True      # pill label
    if inner.startswith('Hi '): return True
    if words_outside(inner)<=3: return True
    return False
def kind(open_tag):
    if 'font-size:56px' in open_tag or 'font-size:38px' in open_tag or re.search(r'font-size:(4\d|5\d)px',open_tag): return 'big'
    return 'txt'
def bind_html(html,ks=None,eid=''):
    out=[];n=[0]
    def rep(m):
        o,tag,inner,c=m.groups()
        key=(eid,n[0]); n[0]+=1
        if skip(o,inner): return m.group(0)
        k=(ks or {}).get(key) or (1 if kind(o)=='big' else 2)
        return o+bind_inner(inner,k)+c
    return EL.sub(rep,html)
def apply(email,ks=None):
    e=copy.deepcopy(email)
    w=e['content']['widgets']
    for name,m in w.items():
        if m.get('type')!='module': continue
        b=m['body']
        if 'html' in b: b['html']=bind_html(b['html'],ks,e['id']+':'+name)
    return e
if __name__=='__main__':
    emails=json.load(open('emails_before.json'))
    new=[apply(e) for e in emails]
    json.dump(new,open('emails_after.json','w'))
    ch=0
    for a,b in zip(emails,new):
        if json.dumps(a['content'])!=json.dumps(b['content']): ch+=1
    print('changed',ch,'of',len(emails))
