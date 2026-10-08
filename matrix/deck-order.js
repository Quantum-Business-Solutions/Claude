/* ICDA 2026 deck: the running order, the Arrange panel and the table of contents (loaded from deck-qr.js, after deck-new.js).

   THE ORDER LIVES IN THE LIST BELOW. Each line is a slide; a line that starts with # starts a new chapter.
   To move a slide, move its line. To hide a slide by default, put its name in HIDDEN.
   You can also do all of this by dragging in the browser: open the deck with ?presenter and press A (or click ARRANGE).
   Browser changes are saved on that computer only. Use "Copy order" in the panel to send me an order to make permanent.
   Open any link with ?order=classic to see the deck in its earlier order. */
(function(){
 if(/[?&]order=classic/.test(location.search))return;
 var PRES=/[?&]presenter/.test(location.search);
 var ORDER=[
  '#Welcome','title','film','n-who','room','n-trends','cannata','soh1','soh2','soh3','soh4','gap',
  '#The Triple A of AI','tripleA','rung1','flow-retype','rung2','rung3','judging','n-terms','n-lake','n-brain',
  '#How we use AI','real-built','real-calls','real-audit','real-enrich','flow-deal','proof1','proof2',
  '#Where to begin','n-begin','model','flow-journey','flow-revgen','flow-revfull',
  '#01 Keep','n-keep','flow-call','csproc','play3',
  '#02 Grow','n-grow',
  '#03 Multiply','n-multiply',
  '#04 Convert','n-convert',
  '#05 Expand','n-expand','n-lf','n-lf2','play1',
  '#Tasks by department','n-dept','bars26','library','twenty',
  '#Sales: in the field','n-field','salesproc','salesroom','play2',
  '#Marketing','n-mkt','unc','bars13','looked','beat','report','play5','mktproc','play4',
  '#Admin and operations','n-ops','adminproc',
  '#Live build','live',
  '#The honest part','honest1','honest2',
  '#Your next step','bobbill','days90','close'];
 /* slides that exist but start hidden (show them with the eye in the Arrange panel) */
 var HIDDEN=['show','sbcard','revold','mirror','timeback','playscard','twentycard','twenty','flow-cycle','cannata','live'];

 /* how each slide is found. id, or the start of its key (data-sk), or text it contains */
 var RULES={title:['pre','Open|Go-to-Market'],film:['cls','trailer'],'n-who':['id'],room:['pre','The room|'],'n-trends':['id'],cannata:['has','hearing, from dealers'],
  soh1:['pre','Show of hands|Used AI'],soh2:['pre','Show of hands|Keep them up if your company'],soh3:['pre','Show of hands|Keep them up if AI is working'],soh4:['pre','Show of hands|api'],gap:['pre','Show of hands|That gap'],
  show:['pre','Open|Let me just'],model:['id'],sbcard:['pre','01 Scoreboard|TheScoreboard'],unc:['pre','01 Scoreboard|Last week'],bars13:['pre','01 Scoreboard|#10'],looked:['pre','01 Scoreboard|You’re'],beat:['pre','01 Scoreboard|One company'],report:['pre','01 Scoreboard|Your own report'],
  revold:['pre','Revenue Efficiency|'],mirror:['pre','02 Mirror|TheMirror'],tripleA:['pre','03 Three rungs|ThreeRungs'],rung1:['pre','03 Three rungs|#19'],rung2:['pre','03 Three rungs|#20'],rung3:['pre','03 Three rungs|#21'],judging:['pre','03 Three rungs|Judging'],
  'n-terms':['id'],timeback:['pre','04 Time back|Who gets'],bars26:['pre','04 Time back|Where the hours'],'flow-deal':['id'],'flow-retype':['id'],'flow-call':['id'],
  salesproc:['pre','04 Time back|A deal, start'],salesroom:['pre','04 Time back|It won'],mktproc:['pre','04 Time back|One install'],adminproc:['pre','04 Time back|Signed to installed'],csproc:['pre','04 Time back|The call at 2am.'],library:['has','137 tasks'],
  playscard:['pre','05 Five plays|FivePlays'],play1:['pre','05 Five plays|The territory'],play2:['pre','05 Five plays|The proposal'],play3:['pre','05 Five plays|The service-to-sales'],play4:['pre','05 Five plays|The one-person'],play5:['pre','05 Five plays|Being the answer'],
  live:['pre','Live build|'],twentycard:['pre','06 Twenty|TwentyWays'],twenty:['pre','06 Twenty|#43'],'real-built':['id'],'real-calls':['id'],'real-audit':['id'],'real-enrich':['id'],proof1:['id'],proof2:['id'],
  honest1:['pre','Honest part|Three ways'],honest2:['pre','Honest part|#45'],bobbill:['id'],days90:['pre','90 days|'],close:['pre','Close|'],
  'n-keep':['id'],'n-grow':['id'],'n-multiply':['id'],'n-convert':['id'],'n-expand':['id'],'n-field':['id'],'n-mkt':['id'],'n-ops':['id'],'n-begin':['id'],'n-brain':['id'],'n-lake':['id'],'n-lf':['id'],'n-lf2':['id'],'flow-journey':['id'],'flow-cycle':['id'],'flow-revgen':['id'],'flow-revfull':['id'],'n-dept':['id']};

 var tries=0;(function wait(){if(window.DECK&&document.getElementById('n-ops')&&document.getElementById('n-dept')&&document.getElementById('n-brain')&&document.getElementById('n-lake')&&document.getElementById('flow-revfull')&&document.getElementById('n-lf2')&&document.getElementById('flow-call')&&document.getElementById('real-enrich')){run();return}if(++tries>360)return;setTimeout(wait,150)})();

 function run(){
 if(document.getElementById('arr-panel'))return;
 var SL=DECK.slides,host=SL[0].parentNode,EL={},LS='icda26-order-v2',i;
 function sk(s){return s.getAttribute('data-sk')||''}
 /* 1. give every slide a key */
 var pool=SL.slice();
 Object.keys(RULES).forEach(function(k){var r=RULES[k],f=null;
  for(var n=0;n<pool.length;n++){var s=pool[n],ok=false;
   if(r[0]==='id')ok=s.id===k;else if(r[0]==='cls')ok=s.classList.contains(r[1]);else if(r[0]==='pre')ok=sk(s).indexOf(r[1])===0;else ok=(s.textContent||'').replace(/\s+/g,' ').indexOf(r[1])>-1;
   if(ok){f=s;pool.splice(n,1);break}}
  if(f){EL[k]=f;f.setAttribute('data-key',k)}});
 /* anything not matched keeps its place after the slide that came before it */
 var known=SL.map(function(s){return s.getAttribute('data-key')||''});
 SL.forEach(function(s,n){if(!s.getAttribute('data-key')){var kk='x'+n;s.setAttribute('data-key',kk);EL[kk]=s}});
 /* 2. the base order, with strays inserted after their predecessor */
 var base=ORDER.filter(function(k){return k.charAt(0)==='#'||EL[k]}),inBase={};base.forEach(function(k){inBase[k]=1});
 for(i=0;i<SL.length;i++){var kk2=SL[i].getAttribute('data-key');if(!inBase[kk2]){var prev=null;for(var q=i-1;q>=0;q--){var pk=SL[q].getAttribute('data-key');if(inBase[pk]){prev=pk;break}}
   var at=prev?base.indexOf(prev)+1:base.length;base.splice(at,0,kk2);inBase[kk2]=1}}
 var sig=base.join('|').length+':'+base.length+':'+HIDDEN.join(',').length;
 var order=base.slice(),hid={};HIDDEN.forEach(function(k){hid[k]=1});
 /* 3. this computer's saved arrangement, if it was made against this same base */
 try{var sv=JSON.parse(localStorage.getItem(LS)||'null');if(sv&&sv.sig===sig&&Array.isArray(sv.order)){var seen={};order=sv.order.filter(function(k){return (k.charAt(0)==='#'||EL[k])&&!seen[k]&&(seen[k]=1)});base.forEach(function(k){if(!seen[k]){order.push(k)}});hid={};(sv.hidden||[]).forEach(function(k){hid[k]=1})}}catch(e){}
 function save(){try{localStorage.setItem(LS,JSON.stringify({sig:sig,order:order,hidden:Object.keys(hid)}))}catch(e){}}

 /* 4. apply the order to the page */
 function title(el){var h=el.querySelector('h1,h2,h3');var t=h?h.textContent:(el.classList.contains('trailer')?'The video: The Old Way vs. The Quantum Way':el.textContent);return t.replace(/\s+/g,' ').trim().slice(0,70)}
 function apply(keepKey){
  var cur=keepKey||(SL[DECK.state().idx]&&SL[DECK.state().idx].getAttribute('data-key'));
  var chap='',all=[],vis=[];
  order.forEach(function(k){if(k.charAt(0)==='#'){chap=k.slice(1);return}var el=EL[k];if(!el)return;el.setAttribute('data-sec',chap);el.setAttribute('data-chap',chap);el.classList.toggle('hidslide',!!hid[k]);all.push(el);if(!hid[k])vis.push(el)});
  var ref=null;for(var n=all.length-1;n>=0;n--){var e=all[n];if(e.nextElementSibling!==ref||e.parentNode!==host)host.insertBefore(e,ref);ref=e}
  SL.length=0;vis.forEach(function(v){SL.push(v)});
  rebuildMenu();rebuildToc();
  var ni=0;SL.forEach(function(s,x){if(s.getAttribute('data-key')===cur)ni=x});DECK.go(ni);
  if(panelOpen)renderPanel()}
 function rebuildMenu(){var ml=document.getElementById('mlist');if(!ml)return;var html='',last=null;SL.forEach(function(s,n){var sc=s.getAttribute('data-sec')||'';if(sc!==last){html+='<h4>'+sc+'</h4>';last=sc}html+='<a href="#" data-n="'+n+'"><i>'+(n+1)+'</i><span>'+title(s)+'</span></a>'});ml.innerHTML=html}

 /* 5. styles */
 var st=document.createElement('style');st.textContent=
  '.hidslide{display:none!important}'+
  '#toc{position:fixed;right:6px;top:50%;transform:translateY(-50%);z-index:35;display:flex;flex-direction:column;gap:2px;align-items:flex-end;padding:6px 4px;border-radius:14px;max-height:62vh}'+
  '#toc:hover,#toc.pin{background:rgba(11,13,21,.9);border:1px solid rgba(255,255,255,.14);padding:8px 10px;right:10px;overflow-y:auto}'+
  '#toc a{display:flex;align-items:center;gap:9px;text-decoration:none;color:#9AA4BC;font:600 clamp(11px,.82vw,13px)/1 var(--sans);padding:.55vh 0;cursor:pointer;white-space:nowrap}'+
  '#toc a .lb{max-width:0;overflow:hidden;opacity:0;transition:max-width .25s,opacity .2s}#toc:hover a .lb,#toc.pin a .lb{max-width:230px;opacity:1}'+
  '#toc a i{flex:0 0 auto;width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,.28);transition:all .2s}#toc a.on i{background:#B6FF3C;width:11px;height:11px;box-shadow:0 0 0 3px rgba(182,255,60,.25)}#toc a.on{color:#fff}#toc a:hover{color:#fff}'+
  '@media (max-width:900px),(max-height:520px){#toc{display:none}}'+
  '#barr{display:none}body.pres #barr{display:inline-block}'+
  '#arr-panel{position:fixed;inset:0;z-index:90;background:rgba(7,9,15,.985);display:none;flex-direction:column;font-family:var(--sans);color:#E4E9F5}#arr-panel.on{display:flex}'+
  '#arr-panel header{padding:14px 22px 6px;display:flex;align-items:baseline;gap:18px;flex-wrap:wrap}#arr-panel header b{font:400 1.7rem/1 var(--disp);letter-spacing:.02em;text-transform:uppercase}#arr-panel header p{margin:0;font:500 13px/1.45 var(--sans);color:#A9B2C6;flex:1 1 380px}'+
  '#arr-panel .tb{display:flex;flex-wrap:wrap;gap:8px;padding:8px 22px 12px;border-bottom:1px solid rgba(255,255,255,.12)}#arr-panel .tb button,#arr-panel .tb a{font:700 11.5px/1 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:#E4E9F5;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.16);border-radius:8px;padding:9px 12px;cursor:pointer;text-decoration:none}#arr-panel .tb .go{background:#B6FF3C;color:#0B0D15;border-color:#B6FF3C}'+
  '#arr-list{flex:1;overflow-y:auto;padding:6px 22px 60px;display:grid;grid-template-columns:repeat(auto-fill,minmax(clamp(190px,17vw,300px),1fr));gap:14px 14px;align-content:start}'+
  '#arr-list .sch{grid-column:1/-1;margin:14px 0 0;padding-bottom:6px;border-bottom:1px solid rgba(255,176,32,.35);font:700 12px/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#FFB020;cursor:grab;display:flex;justify-content:space-between;align-items:center;gap:10px}#arr-list .sch em{font-style:normal;color:#8893AA;letter-spacing:.08em}'+
  '#arr-list .sc{position:relative;cursor:grab;border-radius:10px;border:2px solid rgba(255,255,255,.12);background:#0B0D15;transition:transform .12s,border-color .12s}#arr-list .sc:hover{border-color:rgba(255,255,255,.4);transform:translateY(-2px)}#arr-list .sc.cur{border-color:#B6FF3C}#arr-list .sc.off{opacity:.38}#arr-list .sc.drag,#arr-list .sch.drag{opacity:.3}#arr-list .sc.ov{border-color:#4DE8FF;box-shadow:-6px 0 0 #4DE8FF}#arr-list .sch.ov{box-shadow:0 -3px 0 #4DE8FF}'+
  '#arr-list .sth{border-radius:8px 8px 0 0;position:relative;contain:paint;width:100%;height:0;padding-top:56.25%;overflow:hidden;background:#090B12;pointer-events:none}#arr-list .sth>div{position:absolute;left:0;top:0;transform-origin:0 0;overflow:hidden}#arr-list .sth section{position:absolute!important;left:0;top:0;width:100%!important;height:100%!important;min-height:0!important;transform:none!important;opacity:1!important;display:flex!important;margin:0!important}#arr-list .sth *{animation:none!important;transition:none!important}#arr-list .sth .qr-persist,#arr-list .sth video,#arr-list .sth iframe{display:none!important}'+
  '#arr-list .scap{display:flex;align-items:center;gap:6px;padding:6px 8px;font:600 12px/1.25 var(--sans);background:rgba(255,255,255,.05)}#arr-list .n{flex:0 0 auto;min-width:22px;color:#B6FF3C;font-weight:800}#arr-list .t{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}#arr-list button{flex:0 0 auto;background:rgba(255,255,255,.06);border:0;color:#C5CCDD;font:700 13px/1 var(--sans);cursor:pointer;padding:5px 7px;border-radius:6px}#arr-list button:hover{background:rgba(255,255,255,.2);color:#fff}'+
  '#arr-end{grid-column:1/-1;height:46px;border:2px dashed rgba(255,255,255,.14);border-radius:10px;display:flex;align-items:center;justify-content:center;font:600 12px var(--sans);color:#6F7A92}#arr-end.ov{border-color:#4DE8FF;color:#4DE8FF}'+
  '#arr-toast{position:fixed;left:50%;bottom:90px;transform:translateX(-50%);z-index:95;background:#B6FF3C;color:#0B0D15;font:700 13px var(--sans);padding:10px 16px;border-radius:10px;display:none}'+
  '#bedit{display:none}body.pres #bedit{display:inline-block}';
 document.head.appendChild(st);
 if(PRES)document.body.classList.add('pres');

 /* 6. table of contents */
 var toc=document.createElement('div');toc.id='toc';toc.setAttribute('aria-label','Table of contents');document.body.appendChild(toc);
 function chapters(){var cs=[],last=null;SL.forEach(function(s,n){var c=s.getAttribute('data-chap')||'';if(c!==last){cs.push({t:c,at:n,n:0});last=c}cs[cs.length-1].n++});return cs}
 function rebuildToc(){var cs=chapters();toc.innerHTML=cs.map(function(c,x){return '<a data-at="'+c.at+'" title="'+c.t+'"><span class="lb">'+c.t+' · '+c.n+'</span><i></i></a>'}).join('');
  [].forEach.call(toc.querySelectorAll('a'),function(a){a.onclick=function(e){e.preventDefault();DECK.go(+a.getAttribute('data-at'))}});markToc()}
 function markToc(){var cur=SL[DECK.state().idx],c=cur?cur.getAttribute('data-chap'):'';[].forEach.call(toc.querySelectorAll('a'),function(a){a.classList.toggle('on',a.getAttribute('title')===c)})}
 setInterval(markToc,300);

 /* 7. the Arrange panel */
 var panelOpen=false,panel=document.createElement('div');panel.id='arr-panel';
 panel.innerHTML='<header><b>Arrange slides</b><p>Drag any slide to move it, like a slide sorter. Click a slide to jump to it. The eye hides it from the talk without deleting it. Drag an orange chapter bar to move where a chapter starts. Saved on this computer. Press E on any slide to retype its text.</p></header><div class="tb"><button class="go" data-a="done">Done</button><button data-a="copy">Copy order</button><button data-a="reset">Reset to Shawn&rsquo;s order</button><a href="?presenter&order=classic" data-a="classic">Classic order</a></div><div id="arr-list"></div>';
 document.body.appendChild(panel);
 var toast=document.createElement('div');toast.id='arr-toast';document.body.appendChild(toast);
 function say(t){toast.textContent=t;toast.style.display='block';clearTimeout(say.t);say.t=setTimeout(function(){toast.style.display='none'},2600)}
 var dragK=null;
 var thCache={};
 function thumb(el){var c=el.cloneNode(true);c.removeAttribute('id');c.classList.add('in');c.classList.remove('hidslide');
  [].forEach.call(c.querySelectorAll('[id]'),function(n){n.removeAttribute('id')});
  [].forEach.call(c.querySelectorAll('video,iframe,script,audio,canvas'),function(n){n.parentNode.removeChild(n)});
  [].forEach.call(c.querySelectorAll('[data-to]'),function(n){n.textContent=n.getAttribute('data-to')});
  return c}
 function fitThumbs(){var list=document.getElementById('arr-list'),W=window.innerWidth,H=window.innerHeight;[].forEach.call(list.querySelectorAll('.sth'),function(t){var w=t.getBoundingClientRect().width;if(!w)return;var sc=w/W,d=t.firstChild;d.style.width=W+'px';d.style.height=H+'px';d.style.transform='scale('+sc+')'})}
 function renderPanel(){var list=document.getElementById('arr-list'),curEl=SL[DECK.state().idx],curK=curEl&&curEl.getAttribute('data-key'),vn=0,h='',cnt={},c0=null;
  order.forEach(function(k){if(k.charAt(0)==='#'){c0=k;cnt[k]=0}else if(c0&&EL[k]&&!hid[k])cnt[c0]++});
  order.forEach(function(k,ix){
   if(k.charAt(0)==='#'){h+='<div class="sch" draggable="true" data-ix="'+ix+'"><span>'+k.slice(1)+'</span><em>'+cnt[k]+' slides</em></div>';return}
   var el=EL[k];if(!el)return;var off=!!hid[k];if(!off)vn++;
   h+='<div class="sc'+(off?' off':'')+(k===curK?' cur':'')+'" draggable="true" data-ix="'+ix+'" data-k="'+k+'"><div class="sth"><div></div></div><div class="scap"><span class="n">'+(off?'hidden':vn)+'</span><span class="t">'+title(el).replace(/</g,'&lt;')+'</span><button data-a="up" title="Move earlier">&larr;</button><button data-a="dn" title="Move later">&rarr;</button><button data-a="eye" title="'+(off?'Show':'Hide')+' this slide">'+(off?'&#9675;':'&#9679;')+'</button></div></div>'});
  h+='<div id="arr-end" data-ix="'+order.length+'">Drop here to put a slide at the very end</div>';
  var sTop=list.scrollTop;list.innerHTML=h;
  [].forEach.call(list.querySelectorAll('.sc'),function(r){var k=r.getAttribute('data-k');r.querySelector('.sth>div').appendChild(thumb(EL[k]))});
  fitThumbs();list.scrollTop=sTop;
  [].forEach.call(list.children,function(r){var ix=+r.getAttribute('data-ix');
   if(r.id!=='arr-end'){
   r.addEventListener('dragstart',function(e){dragK=ix;r.classList.add('drag');e.dataTransfer.effectAllowed='move';try{e.dataTransfer.setData('text/plain',String(ix))}catch(x){}});
   r.addEventListener('dragend',function(){dragK=null;[].forEach.call(list.children,function(c){c.classList.remove('drag','ov')})})}
   r.addEventListener('dragover',function(e){e.preventDefault();[].forEach.call(list.children,function(c){c.classList.remove('ov')});r.classList.add('ov')});
   r.addEventListener('drop',function(e){e.preventDefault();if(dragK==null||dragK===ix)return;var m=order.splice(dragK,1)[0];var to=ix>dragK?ix-1:ix;order.splice(to,0,m);dragK=null;save();apply(m.charAt(0)==='#'?null:m)});
   r.addEventListener('click',function(e){var b=e.target.closest('button');var k=order[ix];if(!k)return;
    if(b){var a=b.getAttribute('data-a');
     if(a==='eye'){if(hid[k])delete hid[k];else hid[k]=1;save();apply()}
     else if(a==='up'&&ix>0){order.splice(ix-1,0,order.splice(ix,1)[0]);save();apply(k.charAt(0)==='#'?null:k)}
     else if(a==='dn'&&ix<order.length-1){order.splice(ix+1,0,order.splice(ix,1)[0]);save();apply(k.charAt(0)==='#'?null:k)}
     return}
    if(k.charAt(0)!=='#'&&!hid[k]){var at=SL.indexOf(EL[k]);if(at>-1){openPanel(false);DECK.go(at)}}})});
  var cur=list.querySelector('.cur');if(cur&&!renderPanel.s){renderPanel.s=1;cur.scrollIntoView({block:'center'})}}
 window.addEventListener('resize',function(){if(panelOpen)fitThumbs()});
 function openPanel(on){panelOpen=on;panel.classList.toggle('on',on);document.body.classList.toggle('arring',on);if(on){renderPanel.s=0;renderPanel()}}
 panel.addEventListener('click',function(e){var b=e.target.closest('[data-a]');if(!b||b.closest('#arr-list'))return;var a=b.getAttribute('data-a');
  if(a==='done')openPanel(false);
  else if(a==='reset'){try{localStorage.removeItem(LS)}catch(x){}order=base.slice();hid={};HIDDEN.forEach(function(k){hid[k]=1});apply();say('Back to Shawn’s order')}
  else if(a==='copy'){var txt=JSON.stringify({order:order,hidden:Object.keys(hid)});if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(function(){say('Order copied. Paste it to Claude to make it permanent.')},function(){window.prompt('Copy this order:',txt)})}else window.prompt('Copy this order:',txt)}});
 /* toolbar button and keys */
 var hud=document.getElementById('hud');
 if(hud){var ba=document.createElement('button');ba.id='barr';ba.textContent='ARRANGE';ba.onclick=function(){openPanel(!panelOpen)};var bm=document.getElementById('bmenu');hud.insertBefore(ba,bm||null);var be=document.createElement('button');be.id='bedit';be.textContent='EDIT TEXT';be.onclick=function(){document.dispatchEvent(new KeyboardEvent('keydown',{key:'e',bubbles:true}))};hud.insertBefore(be,bm||null)}
 document.addEventListener('keydown',function(e){var t=e.target;if(t&&(t.isContentEditable||t.tagName==='TEXTAREA'||t.tagName==='INPUT'))return;
  if((e.key==='a'||e.key==='A')&&PRES&&!e.metaKey&&!e.ctrlKey){openPanel(!panelOpen);e.preventDefault()}
  else if((e.key==='t'||e.key==='T')&&!e.metaKey&&!e.ctrlKey){toc.classList.toggle('pin');e.preventDefault()}
  else if(e.key==='Escape'&&panelOpen){openPanel(false)}});

 /* 8. text editing works on every slide: give the newer slides the same edit hooks the original ones have */
 var EDSEL='h1,h2,h3,h4,p,li,.kick,.k,.lede,.sub,blockquote,figcaption,td,th,.pmeta b,.pmeta span,.big:not([data-to]),.v:not([data-to])',EDS={};
 try{EDS=JSON.parse(localStorage.getItem('icda26-edits-v1')||'{}')||{}}catch(e){}
 Object.keys(EL).forEach(function(k){var s=EL[k];if(s.querySelector('[data-ek]'))return;var base=sk(s)||k,n=0;
  [].forEach.call(s.querySelectorAll(EDSEL),function(el){if(el.closest('.acc,#stk,#notes,svg')||el.querySelector(EDSEL))return;el.setAttribute('data-ek',base+'#'+(n++));var v=EDS[el.getAttribute('data-ek')];if(v!=null)el.innerHTML=v})});

 apply(null);DECK.go(0);
 }
})();
