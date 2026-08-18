p='verification-process.html'
s=open(p).read(); before=len(s)
fails=[]

# --- 1. section ids so anchors + :target highlight work ---
for span,sid in [("STAGE 1","stage1"),("STAGE 2","stage2"),("STAGE 3–4","stage34"),
                 ("STAGE 5</span>","stage5"),("STAGE 5b","stage5b"),("STAGE 6","stage6"),
                 ("STAGE 7","stage7"),("VOCABULARY","vocab"),("OUTPUT","output"),("PERSONA","persona")]:
    anchor='<section>\n  <span class="num">'+span
    if anchor in s: s=s.replace(anchor,'<section id="'+sid+'">\n  <span class="num">'+span,1)
    else: fails.append("sectionid:"+sid)

# --- 2. wrap each flow node in a clickable <a> ---
# (open-anchor, close-anchor, target-section)
NODES=[
 ('<rect x="360" y="14"','the only input</text>','stage1'),
 ('<rect x="330" y="86"','never from a local queue file</text>','stage1'),
 ('<path d="M500,162','>on file?</text>','stage2'),
 ('<rect x="712" y="176"','>solved about half</text>','stage2'),
 ('<rect x="712" y="252"','>name + company keywords</text>','stage2'),
 ('<rect x="736" y="330"','>UNREADABLE</text>','stage2'),
 ('<rect x="316" y="268"','not the headline</text>','stage34'),
 ('<path d="M500,352','null</tspan>?</text>','stage34'),
 ('<rect x="36" y="376"','dial them</text>','stage34'),
 ('<rect x="770" y="374"','re-pull FULL experience</text>','stage34'),
 ('<rect x="330" y="474"','do not dial at the company on file</text>','stage5'),
 ('<rect x="256" y="550"','they DO work at the new company</text>','stage5'),
 ('<rect x="256" y="702"','never stays, never deleted</text>','stage6'),
 ('<rect x="300" y="778"','does not exist</text>','stage7'),
 ('<rect x="286" y="854"','back to prospect at the new company</text>','stage7'),
 ('<path d="M500,932','tech-signal lists?</text>','output'),
 ('<rect x="36" y="956"','a rep can dial it</text>','output'),
 ('<rect x="788" y="946"',"check it isn't just unenriched</text>",'output'),
]
for op,cl,tgt in NODES:
    if s.count(op)!=1: fails.append("open x1 fail: "+op+" ("+str(s.count(op))+")"); continue
    if s.count(cl)!=1: fails.append("close x1 fail: "+cl+" ("+str(s.count(cl))+")"); continue
    s=s.replace(op,'<a class="node" href="#'+tgt+'">'+op,1)
    s=s.replace(cl,cl+'</a>',1)

# --- 3. CSS: cursor, hover emphasis, focus ring, land-highlight ---
css="""  svg a.node{cursor:pointer}
  svg a.node text{text-decoration:none}
  svg a.node rect,svg a.node path{transition:stroke-width .12s ease, filter .12s ease}
  svg a.node:hover rect,svg a.node:hover path{stroke-width:2.6px; filter:brightness(1.05)}
  svg a.node:focus-visible rect,svg a.node:focus-visible path{stroke:var(--accent); stroke-width:3px}
  section{scroll-margin-top:14px}
  section:target{animation:flash 1.5s ease}
  @keyframes flash{0%{box-shadow:0 0 0 3px var(--accent)}100%{box-shadow:var(--shadow)}}
"""
if "</style>" in s: s=s.replace("</style>",css+"</style>",1)
else: fails.append("no </style>")

# --- 4. one-line affordance under the FLOW heading ---
hint='  <h2>The whole process, end to end</h2>'
if hint in s:
    s=s.replace(hint,hint+'\n  <p class="meta">Every box is a link — click any step to jump to its full spec below.</p>',1)
else: fails.append("no flow h2")

open(p,'w').write(s)
print("bytes",before,"->",len(s))
print("clickable nodes wrapped:",s.count('class="node"'))
print("FAILURES:",fails if fails else "none")
