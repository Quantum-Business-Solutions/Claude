import re, markdown, html
src = open('/home/user/Claude/campaign/bog-down-bob-campaign.md').read()
# drop the title block (we render our own hero) and section 0 (rendered as the hero strip)
body = src.split('## 1. Big idea', 1)[1]
body = '## 1. Big idea' + body
body = body.replace('*Same job. Same hours. Different system. Leave Bob behind.*', '')
md = markdown.Markdown(extensions=['tables', 'sane_lists'])
h = md.convert(body)
# sections
parts = re.split(r'(<h2>.*?</h2>)', h)
toc, out = [], []
for p in parts:
    m = re.match(r'<h2>(\d+)\. (.*?)</h2>', p)
    if m:
        sid = 's' + m.group(1)
        toc.append((sid, m.group(1), re.sub('<.*?>', '', m.group(2))))
        if out: out.append('</section>')
        out.append('<section id="%s" class="sec"><div class="sh"><span class="sn">%s</span><h2>%s</h2></div>' % (sid, m.group(1).zfill(2), m.group(2)))
    else:
        out.append(p)
out.append('</section>')
h = ''.join(out)
h = re.sub(r'<table>', '<div class="tw"><table>', h); h = h.replace('</table>', '</table></div>')
# copyable posts: <p><strong>Post N: ...</strong></p> (+ optional <p><em>..</em></p>) + <blockquote>
def post(m):
    title, note, q = m.group(1), m.group(2) or '', m.group(3)
    return ('<div class="copy"><div class="ch"><b>%s</b><button type="button" class="cb">Copy post</button></div>%s<blockquote>%s</blockquote></div>' % (title, note, q))
h = re.sub(r'<p><strong>(Post \d+:[^<]*)</strong>\s*(<em>[^<]*</em>)?\s*</p>\s*<blockquote>(.*?)</blockquote>', lambda m: post(type('M',(),{'group':lambda self,i:[None,m.group(1),('<p>'+m.group(2)+'</p>') if m.group(2) else '',m.group(3)][i]})()), h, flags=re.S)
def email(m):
    title, lst, q = m.group(1), m.group(2), m.group(3)
    return ('<div class="copy email"><div class="ch"><b>%s</b><button type="button" class="cb">Copy email</button></div><ul>%s</ul><blockquote>%s</blockquote></div>' % (title, lst, q))
h = re.sub(r'<p><strong>(Email \d+:[^<]*)</strong></p>\s*<ul>(.*?)<li><strong>Body:</strong></li>\s*</ul>\s*<blockquote>(.*?)</blockquote>', email, h, flags=re.S)
h = h.replace('<hr />', '')
tpl = open('shell.html').read()
tochtml = ''.join('<a href="#%s"><i>%s</i>%s</a>' % (a, n.zfill(2), t) for a, n, t in toc)
open('leave-bob-behind.html', 'w').write(tpl.replace('{{TOC}}', tochtml).replace('{{BODY}}', h))
print(len(h), [t for _, _, t in toc], h.count('class="copy'))
