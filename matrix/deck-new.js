/* ICDA 2026 deck: the new slides for the Revenue Efficiency Model order (loaded from deck-qr.js).
   Adds: who I am, the trends, key terms, the five steps of the model, in the field, marketing, ask-your-data.
   deck-order.js then puts every slide in sequence. To change wording here, press E in presenter mode, or edit the text below.
   Skipped when the link ends in ?order=classic. */
(function(){
 if(/[?&]order=classic/.test(location.search))return;
 var tries=0;(function wait(){if(window.DECK&&document.getElementById('flow-call')&&document.getElementById('real-enrich')){run();return}if(++tries>300)return;setTimeout(wait,150)})();
 function run(){
 if(document.getElementById('n-keep'))return;
 var SL=DECK.slides,host=SL[0].parentNode;
 function mk(id,data,notes,html,cls){var s=document.createElement('section');s.className='s rl nw'+(cls?' '+cls:'');s.id=id;s.setAttribute('data-sec',data);s.setAttribute('data-notes',notes);s.setAttribute('data-sk',data+'|'+id);s.innerHTML='<div class="mesh"></div><div class="in-wrap">'+html+'</div>';host.appendChild(s);SL.push(s);
  if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)e.target.classList.add('in')})},{threshold:[0.25]});io.observe(s)}else s.classList.add('in');return s}

 var st=document.createElement('style');st.textContent=
  '.nw h2+.cds,.nw .kick+h2+.cds{margin-top:2.6vh}.nw .in-wrap{max-width:min(1500px,92vw)}.nw h2{font-size:clamp(1.8rem,3.9vw,3.4rem)!important;margin-bottom:0}.nw .sub{margin-top:1vh}'+
  '.lad{display:flex;flex-wrap:wrap;gap:.5vw;margin:1.8vh 0 2.2vh}.lad span{font:700 clamp(11px,.9vw,15px)/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#8893AA;border:1px solid rgba(255,255,255,.16);border-radius:999px;padding:.8vh .9vw}.lad span.on{background:#B6FF3C;color:#0B0D15;border-color:#B6FF3C}'+
  '.cds{display:grid;grid-template-columns:repeat(3,1fr);gap:1.2vw}.cds.c2{grid-template-columns:repeat(2,1fr)}.cds.c4{grid-template-columns:repeat(4,1fr)}.cds.c6{grid-template-columns:repeat(3,1fr)}'+
  '.ncd{position:relative;border:1px solid rgba(255,255,255,.14);border-radius:18px;padding:3vh 1.5vw 3vh;background:linear-gradient(165deg,rgba(255,255,255,.07),rgba(255,255,255,.015))}'+
  '.ncd .no{font:400 clamp(1.6rem,2.7vw,3rem)/1 var(--disp);color:#FFB020}.ncd h3{font:400 clamp(1.2rem,2vw,2.4rem)/1.1 var(--disp);text-transform:uppercase;color:#fff;margin:.9vh 0 1vh}'+
  '.ncd p{font:500 clamp(14px,1.3vw,25px)/1.45 var(--sans);color:#BAC3D6;margin:0}.ncd p b{color:#fff}.ncd .tg{display:inline-block;margin-top:1.2vh;font:700 clamp(11px,.72vw,12px)/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#B6FF3C}'+
  '.ncd.hi{border-color:rgba(182,255,60,.6);background:linear-gradient(165deg,rgba(182,255,60,.13),rgba(182,255,60,.02))}'+
  '.ask{display:flex;flex-wrap:wrap;gap:.7vw;align-items:center;margin-top:2.4vh}.ask b{font:700 clamp(12px,.95vw,16px)/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#4DE8FF;margin-right:.4vw}'+
  '.ask span{font:600 clamp(13px,1.1vw,20px)/1.2 var(--sans);color:#E4E9F5;border:1px solid rgba(77,232,255,.45);background:rgba(77,232,255,.07);border-radius:999px;padding:.9vh 1vw}'+
  '.big3{display:grid;grid-template-columns:1.1fr 1fr;gap:2.4vw;align-items:center;margin-top:3vh}.stat{border:1px solid rgba(255,255,255,.14);border-radius:18px;padding:2.6vh 1.6vw;background:rgba(255,255,255,.04);margin-bottom:1.2vw}.stat:last-child{margin-bottom:0}'+
  '.stat .v{font:400 clamp(2.4rem,5vw,5rem)/1 var(--disp);background:var(--hot);-webkit-background-clip:text;background-clip:text;color:transparent}.stat .k{margin-top:1vh;font:700 clamp(12px,1vw,18px)/1.35 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#A9B2C6}'+
  '.who .nm{font:400 clamp(2.6rem,6vw,6rem)/.95 var(--disp);text-transform:uppercase;color:#fff}.who .rl2{margin-top:1.4vh;font:600 clamp(15px,1.5vw,28px)/1.4 var(--sans);color:#C3CBDC}'+
  '.stp{display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:1vw;align-items:stretch;margin-top:3vh}.stp .ar2{align-self:center;font:400 clamp(1.6rem,2.6vw,2.6rem)/1 var(--disp);color:#FFB020}'+
  '.tagp{display:inline-block;font:700 clamp(12px,.95vw,16px)/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#0B0D15;background:#FFB020;border-radius:6px;padding:.8vh .8vw;margin-bottom:1.2vh}'+
  '.chat{display:flex;flex-direction:column;gap:1.2vh;margin-top:2.6vh}.chat .q,.chat .a{max-width:78%;font:500 clamp(14px,1.35vw,26px)/1.4 var(--sans);border-radius:18px;padding:1.5vh 1.2vw}'+
  '.chat .q{align-self:flex-end;background:#FFB020;color:#0B0D15;font-weight:700;border-bottom-right-radius:4px}.chat .a{align-self:flex-start;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);color:#D2D9E8;border-bottom-left-radius:4px}'+
  '@media (max-height:820px){.lad{margin:1.2vh 0 1.4vh}.ask{margin-top:1.6vh}.big3{margin-top:2vh}.stp{margin-top:2vh}.chat{margin-top:1.6vh;gap:.9vh}.ncd{padding:1.6vh 1.1vw}}'+
  '@media (max-width:900px){.cds,.cds.c4,.cds.c6,.cds.c2,.big3{grid-template-columns:1fr}.stp{grid-template-columns:1fr}.stp .ar2{display:none}.chat .q,.chat .a{max-width:96%}}';
 document.head.appendChild(st);

 function ladder(i){return '<div class="lad">'+['Keep','Grow','Multiply','Convert','Expand'].map(function(n,k){return '<span'+(k===i?' class="on"':'')+'>0'+(k+1)+' '+n+'</span>'}).join('')+'</div>'}
 function cards(a,cls){return '<div class="cds '+(cls||'')+'">'+a.map(function(c,i){return '<div class="ncd'+(c.hi?' hi':'')+'"><div class="no">'+(c.no||(i+1))+'</div><h3>'+c.h+'</h3><p>'+c.p+'</p>'+(c.tg?'<span class="tg">'+c.tg+'</span>':'')+'</div>'}).join('')+'</div>'}
 function ask(a){return a&&a.length?'<div class="ask"><b>Ask it</b>'+a.map(function(x){return '<span>'+x+'</span>'}).join('')+'</div>':''}

 /* ---- who I am ---- */
 mk('n-who','Welcome',
  "Walk on, smile, keep it short. 'Hey guys, how is it going. Shawn Peterson. A little about where I come from and why I am qualified to talk about this.' I have worked with dealers from one million dollars a year to five hundred million. 'So what I am about to show you is not theory. It is what I see in dealerships of every size, and it is how we run our own company.' Then move to the room slide.",
  '<div class="kick">A little about me</div><div class="who"><div class="nm">Shawn Peterson</div><div class="rl2">Quantum Business Solutions</div></div>'+
  '<div class="big3"><div><div class="stat"><div class="v">$1M to $500M</div><div class="k">Annual revenue of the dealers I have worked with</div></div></div>'+
  '<div><div class="stat"><div class="v">We run on it</div><div class="k">The software, the audits and the analysis you will see are ones we built and use</div></div></div></div>');

 /* ---- the trends ---- */
 mk('n-trends','Welcome',
  "These are the three patterns I see in dealerships of every size. EDIT THESE to your own three in Edit mode (press E, click the text). Suggested talk track: 'One: everybody has tried AI, almost nobody has deployed it. Two: the data you need is already in your CRM, your ERP and your service system, and nothing reads it. Three: the week gets eaten by retyping and chasing, the same deal keyed into five systems. None of this is about the technology. It is about the plumbing and the process.' Then the shows of hands.",
  '<div class="kick">What I keep seeing</div><h2>Three things, <span class="grad">every size of dealer.</span></h2>'+
  cards([{h:'Everyone has used AI. Almost no one has deployed it.',p:'A chat window is not a system. The gap between the two is the whole opportunity.'},
         {h:'The answers are already in your data.',p:'Your CRM, your ERP and your service system hold what you need. Nothing is reading it for you.'},
         {h:'The week gets eaten by retyping.',p:'The same deal keyed into five systems, and the same questions asked on every call.'}]));

 /* ---- key terms ---- */
 mk('n-terms','The language of AI',
  "KEY TERMS, in plain English, two minutes. Do not get technical; give them the vocabulary so the rest makes sense. 'API: a door that lets one piece of software talk to another. MCP: a standard plug so AI can use your tools and read your data, like USB for AI. SDK: a toolkit for building on top of a platform. CLI and the terminal: typing commands instead of clicking; that is how the AI coding tools work. Connectors: ready-made plugs between the AI and an app you already own. And memory: what the AI remembers about your business between conversations, your second brain.' Then: 'In a perfect world your AI has memory, it is plugged into your systems, and it can act. That is the whole talk.'",
  '<div class="kick">The words, in plain English</div><h2>What all of these <span class="grad">actually mean.</span></h2>'+
  cards([{no:'API',h:'The door',p:'How one piece of software talks to another, without a person in between.'},
         {no:'MCP',h:'The plug for AI',p:'A standard way to let AI use your tools and read your data. Think USB for AI.'},
         {no:'SDK',h:'The toolkit',p:'What developers use to build on top of a platform you already own.'},
         {no:'CLI',h:'The command line',p:'Typing instructions instead of clicking. How the AI coding tools work, in a terminal window.'},
         {no:'Connector',h:'The ready-made plug',p:'A prebuilt link between the AI and an app you already use, so nobody has to wire it up.'},
         {no:'Memory',h:'Your second brain',p:'What the AI remembers about your business between conversations, so you stop starting from zero.'}],'c6'));


 /* ---- where do I begin ---- */
 mk('n-begin','Where to begin',
  "PAUSE HERE. This is the turn of the whole talk. 'So where do I begin? Not with a tool. Start with the question: what is the most efficient, most effective way to grow my business? Here is the model we use.' Then click to the Revenue Efficiency Model picture. 'You start with Keep: the customers you already have. Then Grow, Multiply, Convert, Expand. For each one I will show you where AI fits, in the Triple A terms we just covered.'",
  '<div class=\"kick\">Where do I begin?</div><h2>Begin with how a dealership <span class=\"grad\">actually grows.</span></h2>'+
  '<p class=\"sub\" style=\"font-size:clamp(15px,1.5vw,24px);max-width:62ch\">Five ways revenue walks in the door, ordered by effort. Start with Keep, work to the right, and put AI to work at every step.</p>'+
  '<div class=\"cds\" style=\"grid-template-columns:repeat(5,1fr);margin-top:3.4vh\">'+[['01','Keep','Retain your current customers'],['02','Grow','Grow your existing customer base'],['03','Multiply','Referral and affiliate programs'],['04','Convert','Win business from your current base'],['05','Expand','Focus on net new business']].map(function(c,i){return '<div class=\"ncd'+(i===0?' hi':'')+'\"><div class=\"no\">'+c[0]+'</div><h3>'+c[1]+'</h3><p>'+c[2]+'</p></div>'}).join('')+'</div>');


 /* ---- processes from the Quantum RevGen chart, marked with where an assistant, automation or agent helps ---- */
 var st2=document.createElement('style');st2.textContent=
  '.jg{display:grid;grid-template-columns:clamp(110px,11vw,190px) repeat(3,1fr);gap:.9vh .8vw;margin-top:2.2vh;align-items:stretch}'+
  '.jh{font:400 clamp(1.2rem,2.2vw,2.4rem)/1 var(--disp);text-transform:uppercase;color:#fff;background:linear-gradient(90deg,rgba(255,255,255,.12),rgba(255,255,255,.04));border-radius:10px 24px 24px 10px;padding:1.2vh 1vw}'+
  '.jt{font:italic 500 clamp(13px,1.15vw,20px)/1.35 var(--sans);color:#C3CBDC;padding:.4vh .5vw}.jl{font:700 clamp(11px,.9vw,15px)/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:#8893AA;align-self:center}'+
  '.jr{display:flex;flex-direction:column;justify-content:center;border-radius:12px;padding:1vh .8vw;border:1px solid rgba(255,255,255,.14)}.jr b{font:400 clamp(1.4rem,2.2vw,2.2rem)/1 var(--disp)}.jr span{font:700 clamp(12px,1vw,17px)/1.1 var(--sans);letter-spacing:.08em;text-transform:uppercase;color:#fff;margin-top:.3vh}.jr small{font:500 clamp(11px,.85vw,14px)/1.2 var(--sans);color:#A9B2C6}'+
  '.jr.a1 b{color:#4DE8FF}.jr.a2 b{color:#FFB020}.jr.a3 b{color:#B6FF3C}.jr.a1{border-color:rgba(77,232,255,.4)}.jr.a2{border-color:rgba(255,176,32,.45)}.jr.a3{border-color:rgba(182,255,60,.5)}'+
  '.jc{font:500 clamp(13px,1.2vw,22px)/1.35 var(--sans);color:#D2D9E8;border-radius:12px;padding:1vh .8vw;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1)}'+
  '.fcy{width:100%;height:auto;max-height:66vh;display:block;margin-top:1.4vh}.fcy text{font-family:var(--sans)}'+
  '@media (max-width:900px){.jg{grid-template-columns:1fr}.jl,.jt{display:none}}';
 document.head.appendChild(st2);
 function jrow(cls,a,name,sub,cells){return '<div class="jr '+cls+'"><b>'+a+'</b><span>'+name+'</span><small>'+sub+'</small></div>'+cells.map(function(c){return '<div class="jc">'+c+'</div>'}).join('')}
 mk('flow-journey','Where to begin',
  "THE BUYER JOURNEY, from our RevGen chart. 'This is the chart we build with every client: the customer moves from target identified, to aware of you, to considering you. Across the top is what they are thinking. Down the side is where AI helps at each stage, on the three rungs. The assistant is you asking. The automation is a trigger doing it without anybody remembering. The agent decides what matters and you approve.' Do not read the grid. Pick one column: 'For a copier dealer, the Target column is your list of every business with a lease coming due.' Then the flow chart on the next slide.",
  '<div class=\"kick\">The RevGen journey · where AI helps</div><h2>Three stages. <span class=\"grad\">Three kinds of help.</span></h2>'+
  '<div class=\"jg\"><div></div><div class=\"jh\">Target identified</div><div class=\"jh\">Awareness</div><div class=\"jh\">Consideration</div>'+
  '<div class=\"jl\">What your customer is thinking</div><div class=\"jt\">“How do I grow my sales?”</div><div class=\"jt\">“Does this solve it? Who is this company?”</div><div class=\"jt\">“Who will implement it? How long will it take?”</div>'+
  jrow('a1','A1','Assistant','you ask',['Draft your ideal customer profile and buyer personas.','Write messages for each vertical and decision maker.','Prepare a one-page brief before every meeting.'])+
  jrow('a2','A2','Automation','a trigger runs it',['Enrich companies and contacts. Refresh lists as leases and data change.','Run the sequences by vertical, lease expiry and existing customer.','Book, confirm and remind. Send the pre-meeting form into your CRM.'])+
  jrow('a3','A3','Agent','decides, you approve',['Find competitive leases and who signs. Bring a short list to the rep.','Read replies, spot who is interested and flag them, so nobody triages by hand.','Re-book no-shows, move the quiet ones to nurture, and hand hot ones to a rep.'])+
  '</div>');

 function fcy(){
  var A={a1:'#4DE8FF',a2:'#FFB020',a3:'#B6FF3C'};
  function bad(x,y,list){return list.map(function(k,i){var bx=x-i*36;return '<rect x=\"'+(bx-32)+'\" y=\"'+(y-14)+'\" width=\"32\" height=\"17\" rx=\"8\" fill=\"#0B0D15\" stroke=\"'+A[k]+'\" stroke-width=\"1.5\"/><text x=\"'+(bx-16)+'\" y=\"'+(y-1)+'\" text-anchor=\"middle\" font-size=\"11\" font-weight=\"700\" fill=\"'+A[k]+'\">A'+k.charAt(1)+'</text>'}).join('')}
  function nd(x,y,w,h,t,sub,b,hi){return '<rect x=\"'+x+'\" y=\"'+y+'\" width=\"'+w+'\" height=\"'+h+'\" rx=\"9\" fill=\"'+(hi?'rgba(182,255,60,.12)':'rgba(255,255,255,.06)')+'\" stroke=\"'+(hi?'#B6FF3C':'rgba(255,255,255,.3)')+'\" stroke-width=\"1.4\"/><text x=\"'+(x+w/2)+'\" y=\"'+(y+(sub?19:h/2+5))+'\" text-anchor=\"middle\" font-size=\"'+(t.length*8.6>w-14?12.5:14.5)+'\" font-weight=\"700\" fill=\"#fff\">'+t+'</text>'+(sub?'<text x=\"'+(x+w/2)+'\" y=\"'+(y+35)+'\" text-anchor=\"middle\" font-size=\"11.5\" fill=\"#A9B2C6\">'+sub+'</text>':'')+bad(x+w-6,y,b||[])}
  function dia(cx,cy,w,h,t,b){return '<polygon points=\"'+cx+','+(cy-h/2)+' '+(cx+w/2)+','+cy+' '+cx+','+(cy+h/2)+' '+(cx-w/2)+','+cy+'\" fill=\"rgba(77,232,255,.08)\" stroke=\"#4DE8FF\" stroke-width=\"1.4\"/><text x=\"'+cx+'\" y=\"'+(cy+5)+'\" text-anchor=\"middle\" font-size=\"14\" font-weight=\"700\" fill=\"#fff\">'+t+'</text>'+bad(cx+22,cy-h/2+2,b||[])}
  function ln(d){return '<path d=\"'+d+'\" fill=\"none\" stroke=\"#8893AA\" stroke-width=\"1.6\" marker-end=\"url(#fcyh)\"/>'}
  function tx(x,y,t,c,a){return '<text x=\"'+x+'\" y=\"'+y+'\" text-anchor=\"'+(a||'middle')+'\" font-size=\"11.5\" fill=\"'+(c||'#A9B2C6')+'\">'+t+'</text>'}
  var o='<svg class=\"fcy\" viewBox=\"0 0 1000 420\" role=\"img\" aria-label=\"Flow chart: from ideal customer profile to a booked meeting, with sales and marketing tracks, marked where an assistant, automation or agent helps\"><defs><marker id=\"fcyh\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"7\" markerHeight=\"7\" orient=\"auto-start-reverse\"><path d=\"M0 0L10 5L0 10z\" fill=\"#8893AA\"/></marker></defs>';
  o+='<rect x=\"22\" y=\"98\" width=\"976\" height=\"112\" rx=\"12\" fill=\"rgba(255,176,32,.05)\"/><rect x=\"22\" y=\"216\" width=\"976\" height=\"112\" rx=\"12\" fill=\"rgba(77,232,255,.05)\"/>'+tx(30,114,'SALES TRACK','#FFB020','start')+tx(30,232,'MARKETING TRACK','#4DE8FF','start');
  o+=nd(30,16,200,44,'1 Ideal customer profile','',['a1'])+nd(280,16,200,44,'2 Buyer personas','up to three',['a1'])+nd(530,16,200,44,'3 Build the lists','',['a1','a3'])+nd(780,16,200,44,'4 Enrich the data','contacts and companies',['a2']);
  o+=ln('M230 38H280')+ln('M480 38H530')+ln('M730 38H780');
  o+=ln('M880 60V82H12V150H30')+ln('M12 150V268H30');
  o+=nd(30,128,200,44,'5a Build a call queue','',['a2'])+nd(280,128,200,44,'6a Call with scripts','',['a1'])+dia(630,150,150,70,'Connected?',[])+nd(780,128,200,44,'Appointment booked','calendar, confirmation',['a2']);
  o+=ln('M230 150H280')+ln('M480 150H555')+ln('M705 150H780')+tx(742,142,'yes')+tx(630,200,'no: voicemail, email and text, then follow up','#A9B2C6');
  o+=nd(30,246,200,44,'5b Create the sequence','',['a2'])+nd(280,246,200,44,'6b Segmented messages','vertical, lease, upsell',['a1','a2'])+dia(630,268,150,70,'Interested?',['a3'])+nd(780,246,200,44,'Meeting or hot lead','booked, or high-urgency queue',['a2']);
  o+=ln('M230 268H280')+ln('M480 268H555')+ln('M705 268H780')+tx(742,260,'yes')+tx(630,318,'no: stay top of mind in the awareness queue','#A9B2C6');
  o+=ln('M980 150H992V372H982')+ln('M980 268H992');
  o+=nd(780,350,200,44,'8 Form into your CRM','before the meeting',['a2'])+nd(530,350,200,44,'9 Two reminders','plus a short prep video',['a2'])+nd(280,350,200,44,'The meeting','rep walks in prepared','',1);
  o+=ln('M780 372H730')+ln('M530 372H480');
  o+='</svg>';return o}
 mk('flow-cycle','Where to begin',
  "THE FLOW, from the copier-dealer version of our revenue cycle. 'Left to right. You define your ideal customer, build personas, build the list, and enrich it. Then it splits: sales makes the calls, marketing sends the sequence. Both end at a booked meeting, with a form into the CRM and two reminders.' Then point at the badges: 'A1 is the assistant: you ask and it drafts, the persona, the scripts, the messages. A2 is automation: enrichment, the call queue, confirmations, reminders, nobody has to remember. A3 is the agent: it reads the replies, decides who is interested and hands you a short list. Today most dealers are doing this by hand, or not at all.'",
  '<div class=\"kick\">The flow · new business, start to meeting</div><h2>From ideal customer to <span class=\"grad\">booked meeting.</span></h2>'+fcy()+
  '<div class=\"ask\" style=\"margin-top:1.2vh\"><b style=\"color:#4DE8FF\">A1</b><span style=\"border-color:rgba(77,232,255,.45)\">Assistant: you ask</span><b style=\"color:#FFB020\">A2</b><span style=\"border-color:rgba(255,176,32,.5);background:rgba(255,176,32,.07)\">Automation: a trigger runs it</span><b style=\"color:#B6FF3C\">A3</b><span style=\"border-color:rgba(182,255,60,.5);background:rgba(182,255,60,.07)\">Agent: it decides, you approve</span></div>');


 function frev(){
  var A={a1:'#4DE8FF',a2:'#FFB020',a3:'#B6FF3C'};
  function bad(x,y,list){return list.map(function(k,i){var bx=x-i*36;return '<rect x=\"'+(bx-32)+'\" y=\"'+(y-14)+'\" width=\"32\" height=\"17\" rx=\"8\" fill=\"#0B0D15\" stroke=\"'+A[k]+'\" stroke-width=\"1.5\"/><text x=\"'+(bx-16)+'\" y=\"'+(y-1)+'\" text-anchor=\"middle\" font-size=\"11\" font-weight=\"700\" fill=\"'+A[k]+'\">A'+k.charAt(1)+'</text>'}).join('')}
  function nd(x,y,w,h,t,sub,b,hi){return '<rect x=\"'+x+'\" y=\"'+y+'\" width=\"'+w+'\" height=\"'+h+'\" rx=\"9\" fill=\"'+(hi?'rgba(182,255,60,.12)':'rgba(255,255,255,.06)')+'\" stroke=\"'+(hi?'#B6FF3C':'rgba(255,255,255,.3)')+'\" stroke-width=\"1.4\"/><text x=\"'+(x+w/2)+'\" y=\"'+(y+(sub?19:h/2+5))+'\" text-anchor=\"middle\" font-size=\"'+(t.length*8.6>w-14?12.5:14.5)+'\" font-weight=\"700\" fill=\"#fff\">'+t+'</text>'+(sub?'<text x=\"'+(x+w/2)+'\" y=\"'+(y+35)+'\" text-anchor=\"middle\" font-size=\"11.5\" fill=\"#A9B2C6\">'+sub+'</text>':'')+bad(x+w-6,y,b||[])}
  function dia(cx,cy,w,h,t,b){return '<polygon points=\"'+cx+','+(cy-h/2)+' '+(cx+w/2)+','+cy+' '+cx+','+(cy+h/2)+' '+(cx-w/2)+','+cy+'\" fill=\"rgba(77,232,255,.08)\" stroke=\"#4DE8FF\" stroke-width=\"1.4\"/><text x=\"'+cx+'\" y=\"'+(cy+5)+'\" text-anchor=\"middle\" font-size=\"14\" font-weight=\"700\" fill=\"#fff\">'+t+'</text>'+bad(cx+22,cy-h/2+2,b||[])}
  function ln(d){return '<path d=\"'+d+'\" fill=\"none\" stroke=\"#8893AA\" stroke-width=\"1.6\" marker-end=\"url(#fcyh)\"/>'}
  function tx(x,y,t,c,a){return '<text x=\"'+x+'\" y=\"'+y+'\" text-anchor=\"'+(a||'middle')+'\" font-size=\"11.5\" fill=\"'+(c||'#A9B2C6')+'\">'+t+'</text>'}

  var o='<svg class=\"fcy\" viewBox=\"0 0 1000 430\" role=\"img\" aria-label=\"Flow chart: the Quantum RevGen end to end process, from lead sources to solution determination, marked where an assistant, automation or agent helps\"><defs><marker id=\"fcyh\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"7\" markerHeight=\"7\" orient=\"auto-start-reverse\"><path d=\"M0 0L10 5L0 10z\" fill=\"#8893AA\"/></marker></defs>';
  /* stage chevrons */
  [['Target identified',150,150],['Awareness',300,150],['Consideration',450,150]].forEach(function(c,i){o+='<polygon points=\"'+c[1]+',8 '+(c[1]+c[2]-14)+',8 '+(c[1]+c[2])+',26 '+(c[1]+c[2]-14)+',44 '+c[1]+',44 '+(c[1]+14)+',26\" fill=\"rgba(255,255,255,'+(i===0?.16:.08)+')\" stroke=\"rgba(255,255,255,.25)\"/><text x=\"'+(c[1]+c[2]/2)+'\" y=\"31\" text-anchor=\"middle\" font-size=\"13.5\" font-weight=\"700\" fill=\"#fff\">'+c[0]+'</text>'});
  /* lead sources */
  o+='<rect x=\"10\" y=\"60\" width=\"120\" height=\"170\" rx=\"10\" fill=\"rgba(255,255,255,.06)\" stroke=\"rgba(255,255,255,.3)\" stroke-width=\"1.4\"/><text x=\"70\" y=\"82\" text-anchor=\"middle\" font-size=\"13.5\" font-weight=\"700\" fill=\"#fff\">Lead sources</text>';
  ['Third party data','Paid ads','Trigger events','Organic social','Referrals','Webinar','Earned'].forEach(function(t,i){o+=tx(70,102+i*18,t,'#C3CBDC')});
  o+=bad(124,60,['a2']);
  o+=ln('M130 145H160');
  /* call target, contact made */
  o+=dia(200,145,84,66,'',[])+tx(200,141,'Call','#fff')+tx(200,157,'target?','#fff')+bad(222,115,['a3']);
  o+=dia(330,145,92,70,'',[])+tx(330,141,'Contact','#fff')+tx(330,157,'made?','#fff');
  o+=ln('M240 145H285')+tx(262,139,'yes')+ln('M200 177V250')+tx(212,215,'no','#A9B2C6','start')+nd(140,250,120,40,'Enter nurture','prove you are alive',['a2']);
  /* outcomes */
  var oc=[['Booked meeting','confirm and remind',['a2']],['Interested','send more information',['a2']],['Busy, call back','follow up in X days',['a2']],['Not decision maker','capture the right contact',['a3']],['Disqualified','remove from campaigns',[]]];
  oc.forEach(function(c,i){var y=62+i*56;o+=nd(420,y,160,40,c[0],c[1],c[2],i===0);o+=ln('M375 145H400V'+(y+20)+'H420')});
  o+=tx(398,138,'yes','#A9B2C6','end');
  /* meeting to solution */
  o+=ln('M580 82H610V145H625')+dia(660,145,70,62,'Attends?',['a2'])+ln('M695 145H725')+tx(710,139,'yes');
  o+=nd(725,125,90,40,'Intro call','',['a1']);
  o+=ln('M815 145H838')+dia(878,145,80,66,'A fit?',['a3']);
  o+=ln('M878 178V212')+tx(892,200,'yes','#A9B2C6','start');
  o+=nd(780,212,200,44,'Solution determination','the proposal',['a1'],1);
  o+=ln('M880 256V300H630V345')+ln('M880 300H780V345')+ln('M880 300H930V345');
  o+=nd(560,345,140,44,'GTM program','assess, playbook',['a2'])+nd(710,345,140,44,'Sales as a service','onboard, execute',['a2'])+nd(860,345,140,44,'Technology','set up, demos',['a2']);
  o+=tx(672,196,'no','#A9B2C6','start')+nd(610,215,100,34,'Re-book','');
  o+=ln('M660 176V215');
  o+='</svg>';return o}
 mk('flow-revgen','Where to begin',
  "THE ONE YOU HAVE ALWAYS USED: our RevGen End to End. 'This is the process we put in front of every client. Leads come from seven places, they move from target identified, to aware of us, to considering us. Along the way it is a set of yes-or-no decisions: call the target, did we reach the person, did they attend, is it a fit.' Then the badges: 'A1 is the assistant, you ask. A2 is automation, nobody has to remember. A3 is the agent, it decides and you approve. Look at where the A3s are. They are the decisions: who to call, are they the decision maker, is it a fit.' 'None of this is new. What is new is that the reading and the remembering no longer have to be done by a person.' [Dealers can map their own sales process onto it; offer the Lucid file as a take-home.]",
  '<div class=\"kick\">Our RevGen end to end · where AI helps</div><h2>The process, with <span class=\"grad\">the help marked on it.</span></h2>'+frev()+
  '<div class=\"ask\" style=\"margin-top:1.2vh\"><b style=\"color:#4DE8FF\">A1</b><span style=\"border-color:rgba(77,232,255,.45)\">Assistant: you ask</span><b style=\"color:#FFB020\">A2</b><span style=\"border-color:rgba(255,176,32,.5);background:rgba(255,176,32,.07)\">Automation: a trigger runs it</span><b style=\"color:#B6FF3C\">A3</b><span style=\"border-color:rgba(182,255,60,.5);background:rgba(182,255,60,.07)\">Agent: it decides, you approve</span></div>');


 /* ---- the full RevGen End to End chart, exactly as it is used with clients (click to zoom) ---- */
 var RG='https://20682069.fs1.hubspotusercontent-na1.net/hubfs/20682069/icda-2026/revgen-end-to-end.png';
 var st5=document.createElement('style');st5.textContent='.rgf{margin:1.6vh auto 0;background:#fff;border-radius:16px;padding:1vh 1vw;width:fit-content;max-width:100%;cursor:zoom-in;box-shadow:0 20px 60px rgba(0,0,0,.45)}.rgf img{display:block;height:min(66vh,calc((100vw - 260px)/1.768));width:auto;max-width:100%}.rgf+.src{text-align:center}#rg-zoom{position:fixed;inset:0;z-index:85;background:#fff;overflow:auto;display:none;cursor:zoom-out}#rg-zoom.on{display:block}#rg-zoom img{display:block;width:max(100vw,1900px);height:auto}#rg-hint{position:fixed;right:18px;bottom:18px;z-index:86;background:#0B0D15;color:#fff;font:700 12px var(--sans);letter-spacing:.1em;text-transform:uppercase;padding:9px 14px;border-radius:999px;display:none}#rg-zoom.on+#rg-hint{display:block}';document.head.appendChild(st5);
 var rz=document.createElement('div');rz.id='rg-zoom';rz.innerHTML='<img alt=\"Quantum Business Solutions RevGen End to End process map\" src=\"'+RG+'\">';document.body.appendChild(rz);var rh=document.createElement('div');rh.id='rg-hint';rh.textContent='Click or press Esc to close';document.body.appendChild(rh);
 rz.onclick=function(){rz.classList.remove('on')};document.addEventListener('keydown',function(e){if(e.key==='Escape')rz.classList.remove('on')});
 mk('flow-revfull','Where to begin',
  "THE FULL CHART. 'This is the one I have used with clients for years: our RevGen End to End. Everything on the last slide, with the whole thing underneath it.' Read the structure left to right: seven lead sources, three stages across the top (Target identified, Awareness, Consideration), and under each stage what the customer is thinking, feeling and needs, and what marketing, the SDR and sales do. Then the yes-or-no decisions, and Solution determination on the right. 'You do not need to read it from here. Click the chart and it fills the screen, and the PDF and the take-home page have it too.' Click the image to zoom. Press Escape or click again to close.",
  '<div class=\"kick\">Our RevGen End to End · the full chart</div><h2>The whole process, <span class=\"grad\">on one page.</span></h2><div class=\"rgf\" id=\"rgf\" title=\"Click to zoom\"><img alt=\"Quantum Business Solutions RevGen End to End process map\" src=\"'+RG+'\"></div><p class=\"src\" style=\"margin-top:1.2vh\">Click the chart to zoom in. Press Esc to close.</p>');
 document.getElementById('rgf').onclick=function(){rz.classList.add('on')};


 /* ---- more shows of hands: the homework questions, placed where the topic comes up ---- */
 var sohSrc=null;SL.forEach(function(x){if(/Show of hands\s*·\s*03/.test(x.textContent))sohSrc=x});
 function hands(id,n,h,notes){if(!sohSrc)return;var c=sohSrc.cloneNode(true);c.id=id;c.classList.remove('in');
  [].forEach.call(c.querySelectorAll('[data-ek]'),function(e){e.removeAttribute('data-ek')});[].forEach.call(c.querySelectorAll('video,.scrim'),function(e){e.parentNode.removeChild(e)});
  var tg=c.querySelector('.tag');if(tg)tg.textContent='Show of hands · 0'+n;var hh=c.querySelector('h1');if(hh)hh.innerHTML=h;
  c.setAttribute('data-sk','Show of hands|'+id);c.setAttribute('data-notes',notes);host.appendChild(c);SL.push(c);
  if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)e.target.classList.add('in')})},{threshold:[0.25]});io.observe(c)}else c.classList.add('in')}
 hands('h-data',5,'Keep them up if you’ve <span class=\"grad\">listed every data source</span> your company has.',"SHOW OF HANDS, right after the data slide. Expect almost no hands. 'Every data source. The ERP, the CRM, the service system, the leasing portal, the spreadsheets on someone's desktop, the shared drives, the call recordings, the email. Written down, all of them, in one list.' Hold the pause. 'That list is step one of everything else in this talk. You cannot connect what you have not named.' Then the next slide.");
 hands('h-conn',6,'Keep them up if you’ve checked <span class=\"grad\">which of them are connected.</span>',"Hands should be down by now. 'For each item on that list: can the AI reach it? Is it connected, through an API, a connector or an MCP, or does a person have to export it and paste it?' 'Most dealers find two or three connected and the rest locked in a screen or a spreadsheet. That gap is your first project.' Homework: write the list this week, mark each line connected or not connected.");
 hands('h-process',7,'Keep them up if you’ve <span class=\"grad\">mapped your entire process,</span> start to finish.',"SHOW OF HANDS, right after the full RevGen chart. 'Lead source to cash. Every step, every decision, every handoff, drawn out like this.' Expect very few hands. 'You cannot automate a process you have not drawn. The chart you just saw took us years of refinement. Draw yours, even rough, on a whiteboard, and mark where a person waits, retypes or chases.' Offer: the Lucid file is a starting point.");
 hands('h-tasks',8,'Keep them up if you’ve <span class=\"grad\">listed every single task</span> your team does.',"SHOW OF HANDS, right after the task library. 'One hundred and thirty-seven tasks just for sales and marketing. Has anyone listed every task their own people do, by role?' Expect almost none. 'That list is the raw material. Each task gets a rating: assistant, automation or agent. You will be surprised how many are the same task done five different ways by five different people.' Homework: each manager lists their team's tasks in a week.");
 hands('h-ailist',9,'Keep them up if you’ve listed <span class=\"grad\">everything you’d like to do with AI.</span>',"SHOW OF HANDS, near the end. 'Everything you would like AI to do for your company. Every idea. On one list.' Pause. 'And have you ranked it? Effort against payoff?' Then click: the next slide is the grid. 'Most people pick the exciting idea. The right one is high payoff for low effort, and it is usually less exciting than you think.'");
 var st6=document.createElement('style');st6.textContent='.mtx{position:relative;display:grid;grid-template-columns:2.2vw 1fr 1fr;grid-template-rows:1fr 1fr auto;gap:1.2vw;margin-top:2.4vh;padding-left:.5vw}.mtx .yl{grid-column:1;grid-row:1/3;writing-mode:vertical-rl;transform:rotate(180deg);text-align:center;font:700 clamp(12px,.95vw,16px)/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#8893AA}.mtx .xl{grid-column:2/4;text-align:center;font:700 clamp(12px,.95vw,16px)/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#8893AA}'+'.qd{border:1px solid rgba(255,255,255,.14);border-radius:18px;padding:2.2vh 1.4vw;background:rgba(255,255,255,.04)}.qd b{display:block;font:400 clamp(1.3rem,2.2vw,2.6rem)/1 var(--disp);text-transform:uppercase;color:#fff}.qd i{display:block;font:700 clamp(11px,.85vw,14px)/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#8893AA;font-style:normal;margin:.6vh 0 1vh}.qd p{margin:0;font:500 clamp(13px,1.15vw,21px)/1.4 var(--sans);color:#C3CBDC}'+'.qd.q2{grid-column:2;grid-row:1;border-color:rgba(182,255,60,.6);background:rgba(182,255,60,.1)}.qd.q1{grid-column:3;grid-row:1;border-color:rgba(255,176,32,.5)}.qd.q4{grid-column:2;grid-row:2}.qd.q3{grid-column:3;grid-row:2;opacity:.8}@media (max-width:900px){.mtx{grid-template-columns:1fr}.mtx .yl,.mtx .xl{display:none}.qd.q1,.qd.q2,.qd.q3,.qd.q4{grid-column:1;grid-row:auto}}';document.head.appendChild(st6);
 mk('n-matrix','Your next step',
  "THE LIST, RANKED. Draw it on a whiteboard if the room is small. 'Two questions for every idea on your list. How hard is it? How much is it worth? Score each one to five. Top left, high payoff and low effort: do those first, this quarter. Top right, high payoff and high effort: plan them, because they are the ones that change the company. Bottom left, low effort and low payoff: fill-ins, do them when someone has an hour. Bottom right, high effort for low payoff: skip, no matter how clever they sound.' The examples are only a starting point, they are not a recommendation for any one dealer. Close it: 'Your first project is the top-left corner. Not the most exciting one.'",
  '<div class=\"kick\">Your list, ranked</div><h2>Effort against payoff. <span class=\"grad\">Start top left.</span></h2>'+
  '<div class=\"mtx\"><div class=\"yl\">Payoff &rarr;</div><div class=\"qd q1\"><b>Plan it</b><i>High payoff · high effort</i><p>Connect your ERP and CRM. The AI Lead Finder across your history. The proposal machine.</p></div><div class=\"qd q2\"><b>Do first</b><i>High payoff · low effort</i><p>Ask your CRM a question. Find lease dates in old notes. A past-due orders answer.</p></div><div class=\"qd q3\"><b>Skip for now</b><i>Low payoff · high effort</i><p>A custom-built app for one rare task.</p></div><div class=\"qd q4\"><b>Fill-ins</b><i>Low payoff · low effort</i><p>Meeting summaries. A draft case study. Tidy-up automations.</p></div><div class=\"xl\">Effort &rarr;</div></div>'+
  '<p class=\"src\" style=\"margin-top:1.2vh\">Examples to start your list. Score every idea 1 to 5 on effort and on payoff.</p>');


 /* ---- one flow per rung: Assistant, Automation (the retyping chart), Agent ---- */
 function frm(vb,build,label){
  var A={a1:'#4DE8FF',a2:'#FFB020',a3:'#B6FF3C'};
  function bad(x,y,list){return list.map(function(k,i){var bx=x-i*36;return '<rect x=\"'+(bx-32)+'\" y=\"'+(y-14)+'\" width=\"32\" height=\"17\" rx=\"8\" fill=\"#0B0D15\" stroke=\"'+A[k]+'\" stroke-width=\"1.5\"/><text x=\"'+(bx-16)+'\" y=\"'+(y-1)+'\" text-anchor=\"middle\" font-size=\"11\" font-weight=\"700\" fill=\"'+A[k]+'\">A'+k.charAt(1)+'</text>'}).join('')}
  function nd(x,y,w,h,t,sub,b,hi){return '<rect x=\"'+x+'\" y=\"'+y+'\" width=\"'+w+'\" height=\"'+h+'\" rx=\"9\" fill=\"'+(hi?'rgba(182,255,60,.12)':'rgba(255,255,255,.06)')+'\" stroke=\"'+(hi?'#B6FF3C':'rgba(255,255,255,.3)')+'\" stroke-width=\"1.4\"/><text x=\"'+(x+w/2)+'\" y=\"'+(y+(sub?19:h/2+5))+'\" text-anchor=\"middle\" font-size=\"'+(t.length*8.6>w-14?12.5:14.5)+'\" font-weight=\"700\" fill=\"#fff\">'+t+'</text>'+(sub?'<text x=\"'+(x+w/2)+'\" y=\"'+(y+35)+'\" text-anchor=\"middle\" font-size=\"11.5\" fill=\"#A9B2C6\">'+sub+'</text>':'')+bad(x+w-6,y,b||[])}
  function dia(cx,cy,w,h,t,b){return '<polygon points=\"'+cx+','+(cy-h/2)+' '+(cx+w/2)+','+cy+' '+cx+','+(cy+h/2)+' '+(cx-w/2)+','+cy+'\" fill=\"rgba(77,232,255,.08)\" stroke=\"#4DE8FF\" stroke-width=\"1.4\"/><text x=\"'+cx+'\" y=\"'+(cy+5)+'\" text-anchor=\"middle\" font-size=\"14\" font-weight=\"700\" fill=\"#fff\">'+t+'</text>'+bad(cx+22,cy-h/2+2,b||[])}
  function ln(d){return '<path d=\"'+d+'\" fill=\"none\" stroke=\"#8893AA\" stroke-width=\"1.6\" marker-end=\"url(#fcyh)\"/>'}
  function tx(x,y,t,c,a){return '<text x=\"'+x+'\" y=\"'+y+'\" text-anchor=\"'+(a||'middle')+'\" font-size=\"11.5\" fill=\"'+(c||'#A9B2C6')+'\">'+t+'</text>'}


  var o='<svg class=\"fcy\" viewBox=\"'+vb+'\" role=\"img\" aria-label=\"'+label+'\"><defs><marker id=\"fcyh\" viewBox=\"0 0 10 10\" refX=\"9\" refY=\"5\" markerWidth=\"7\" markerHeight=\"7\" orient=\"auto-start-reverse\"><path d=\"M0 0L10 5L0 10z\" fill=\"#8893AA\"/></marker></defs>';
  o+=build({nd:nd,dia:dia,ln:ln,tx:tx,bad:bad});o+='</svg>';return o}
 function trio(a){return '<div class=\"cds\" style=\"margin-top:1.6vh\">'+a.map(function(c,i){return '<div class=\"ncd\" style=\"padding:1.6vh 1.1vw\"><div class=\"no\" style=\"font-size:clamp(1.2rem,1.8vw,2.1rem)\">'+(i+1)+'</div><h3 style=\"font-size:clamp(1rem,1.5vw,1.8rem);margin:.4vh 0 .5vh\">'+c[0]+'</h3><p style=\"font-size:clamp(12.5px,1vw,18px)\">'+c[1]+'</p></div>'}).join('')+'</div>'}
 var fa1=frm('0 0 1000 270',function(k){var o='';
  o+=k.tx(95,108,'YOU','#FFB020')+k.tx(300,108,'YOU','#FFB020')+k.tx(515,108,'AI','#B6FF3C')+k.tx(890,108,'YOU','#FFB020');
  o+=k.nd(20,120,150,56,'You think of it','a question or task',[])+k.nd(215,120,170,56,'You open a chat','and type or paste',['a1'])+k.nd(430,120,170,56,'AI answers','from what you gave it',['a1'],1);
  o+=k.dia(700,148,120,80,'',[])+k.tx(700,144,'Is it','#fff')+k.tx(700,160,'right?','#fff');
  o+=k.nd(800,120,180,56,'You copy it over','into your system, by hand',[]);
  o+=k.ln('M170 148H215')+k.ln('M385 148H430')+k.ln('M600 148H640')+k.ln('M760 148H800')+k.tx(780,140,'yes')+k.ln('M700 188V240H300V178')+k.tx(500,232,'no: ask again, again','#A9B2C6');
  o+=k.tx(890,205,'Tomorrow, you start over.','#A9B2C6');return o},'Flow chart: with an assistant you think of a task, open a chat, ask, and copy the answer over by hand, every time');
 mk('flow-a1','The Triple A of AI',
  "ASSISTANT, as a flow. 'Look at who does the work. You think of it. You open the chat. You type or paste. The AI answers. You decide if it is right, you copy it into your system by hand, and tomorrow you start over.' The three points under the chart: you are the trigger, so nothing happens unless somebody asks; it only knows what you give it; and it does not remember tomorrow. 'This is still enormously useful. It is just not a system.' Then Rung two.",
  '<div class=\"kick\">Rung 01 · Assistant · how it works</div><h2>You are <span class=\"grad\">the trigger, every time.</span></h2>'+fa1+trio([['You are the trigger','Nothing happens unless somebody asks. Every time.'],['It knows what you give it','Paste in a note and it can help. It cannot see your CRM or your ERP.'],['It forgets tomorrow','No memory. The same question gets asked again next week.']]));
 var fa3=frm('0 0 1000 330',function(k){var o='';
  o+=k.nd(20,120,150,56,'A signal or a goal','lease at 11 months',['a2'])+k.nd(205,120,175,56,'It reads everything','CRM, ERP, service, email',['a3'],1);
  o+=k.dia(500,148,120,80,'',['a3'])+k.tx(500,144,'Worth','#fff')+k.tx(500,160,'acting?','#fff');
  o+=k.nd(590,120,170,56,'It drafts the action','email, quote or task',['a3'])+k.nd(795,120,185,56,'You approve','one tap, or edit it',[],1);
  o+=k.nd(795,235,185,56,'It acts','sends, books, updates',['a2'])+k.nd(540,235,200,56,'It learns what worked','so next time is better',['a3'])+k.nd(250,235,200,56,'It logs it and waits','watches for a change',['a2']);
  o+=k.ln('M170 148H205')+k.ln('M380 148H440')+k.ln('M560 148H590')+k.tx(575,140,'yes')+k.ln('M760 148H795')+k.ln('M887 176V235')+k.ln('M795 263H740')+k.ln('M500 188V212H350V235')+k.tx(425,206,'no','#A9B2C6');
  o+=k.tx(887,112,'THE HUMAN STAYS IN CHARGE','#B6FF3C');return o},'Flow chart: an agent reads your systems, decides whether to act, drafts the action, a person approves, then it acts and learns');
 mk('flow-a3','The Triple A of AI',
  "AGENT, as a flow. 'Now look at who does the work. A signal arrives, a lease at eleven months, a ticket that closed with a fault code. The agent reads everything it needs: the CRM, the ERP, the service history, the email. It decides whether this is worth acting on. If not, it logs it and keeps watching. If it is, it drafts the action: the email, the quote, the task. Then a person approves, one tap or an edit, and only then does it act, and it learns what worked.' The point is the green box: the human stays in charge. 'This is not a robot replacing your people. It is a very fast assistant that does the reading and the drafting and asks you to decide.' [Be honest: this is where the tools are going, and where the early adopters are now.] Then 'judging AI by ChatGPT'.",
  '<div class=\"kick\">Rung 03 · Agent · how it works</div><h2>It decides what matters. <span class=\"grad\">You approve.</span></h2>'+fa3+trio([['It does the reading','Every account, every ticket, every email, in the time it takes you to open one.'],['It decides what is worth acting on','Most signals are noise. It logs them and keeps watching.'],['A person approves','One tap, or an edit. Nothing goes out without you.']]));

 /* ---- tasks by department ---- */
 mk('n-dept','Tasks by department',
  "TASKS BY DEPARTMENT. 'That was the model. Now let us come down a level: what can AI take off each department's plate?' Four places: sales, marketing, sales admin and operations, and customer service. Customer service you already saw under Keep. Every task in the library is rated Assistant, Automation or Agent, so you can see which rung each one sits on. Then the chart of where the hours come back, and the full library. After that we walk sales in the field, then marketing, where the website and SEO and AEO analysis lives, then admin and operations.",
  '<div class=\"kick\">Now, by department</div><h2>What AI can take off <span class=\"grad\">each team’s plate.</span></h2>'+
  '<div class=\"cds c4\" style=\"margin-top:3vh\">'+
  [['01','Sales','Prospect, prepare, propose. The rep’s week with less typing.','In the field',1],['02','Marketing','Be found, publish, listen, show. Including your website, SEO and AEO.','Marketing',0],['03','Sales admin and operations','Order to install to invoice, without retyping the same deal.','Admin',0],['04','Customer service','Calls, tickets, meter reads and dispatch.','Started in Keep',0]].map(function(c){return '<div class=\"ncd'+(c[4]?' hi':'')+'\"><div class=\"no\">'+c[0]+'</div><h3>'+c[1]+'</h3><p>'+c[2]+'</p><span class=\"tg\">'+c[3]+'</span></div>'}).join('')+'</div>'+
  '<p class=\"src\" style=\"margin-top:2vh\">Every task is rated on the Triple A: assistant, automation or agent.</p>');

 /* ---- the five steps ---- */
 mk('n-keep','01 Keep',
  "KEEP. 'First things first: before we chase anything new, keep the customers we have. This is the cheapest revenue in your business.' Three things. One: an assistant so nobody waits, on the phone or by text, even after the office closes; toner, meter reads, invoice copies, where is my tech. Two, and this is the big one: connect AI to your ERP and your CRM through an MCP and talk to your data. Read the four questions: where have there been anomalies, where are we missing opportunities, where have we had the most service problems, where have trends changed with customers. Three: reports and automations that flag the account before it leaves. Then walk the service-call flow chart, the service process and the service-to-sales bridge that follow.",
  '<div class="kick">Revenue Efficiency Model · Retain your current customers</div><h2>Keep: <span class="grad">nobody waits.</span></h2>'+ladder(0)+
  cards([{h:'An assistant that never makes them wait',p:'Answers on the first ring, even after hours: toner, meter reads, invoice copies, where is my tech.'},
         {h:'Talk to your data',p:'Connect AI to your ERP and CRM through an <b>MCP</b>, then ask it questions in plain English.',hi:1},
         {h:'See it before they leave',p:'Reports and automations that flag a repeat fault, a missed meter read or a quiet account, months before renewal.'}])+
  ask(['Where have there been anomalies?','Where are we missing opportunities?','Where have the most service problems been?','Where have trends changed with customers?']));

 mk('n-grow','02 Grow',
  "GROW. 'The next cheapest revenue is the customer you already have: sell them the next thing.' Look at your database. Out of your customers, who is a good fit for another product or service based on your ideal customer profile? Then the question nobody can answer today: of the ones who fit, how many has anyone actually talked to about it, ever? That lives in your CRM history, your calls and your emails; AI can read all of it in one pass. Third, the signal you already own: meter volume outrunning the contract, a managed IT gap in an account you already serve.",
  '<div class="kick">Revenue Efficiency Model · Grow your existing customer base</div><h2>Grow: <span class="grad">the next product, the same customer.</span></h2>'+ladder(1)+
  cards([{h:'Who is a fit for another product?',p:'Match your customer database to your ideal customer profile: who should be buying managed IT, security or another line from you?'},
         {h:'Have we ever had that conversation?',p:'Of the customers who fit, how many has anyone actually talked to about it? The answer is in your CRM history, calls and emails.',hi:1},
         {h:'Volume outrunning the contract',p:'Spot meter volume past what the contract covers, and hand the rep the talking points.'}])+
  ask(['Which customers fit our profile but buy only one thing from us?','How many of them have we ever talked to about it?']));

 mk('n-multiply','03 Multiply',
  "MULTIPLY. 'Referrals are the most efficient new customers you will ever get, and almost nobody has a system for them.' Here is one we run ourselves. Every decision maker and champion at a customer is watched in the background. The moment one leaves or bounces to another company, they drop onto a list automatically and we track where they land, so we can reach out; they already know who we are. That is the 'Keeping a list honest' chart you saw earlier. Second: AI that notices happy moments, a clean install, a great survey, a fast fix, and prompts the referral ask at exactly the right time.",
  '<div class="kick">Revenue Efficiency Model · Multiply through referral and affiliate programs</div><h2>Multiply: <span class="grad">referrals that run themselves.</span></h2>'+ladder(2)+
  cards([{h:'Never lose a champion',p:'Every decision maker and champion is watched in the background. If they leave or bounce, they drop onto a list automatically.',hi:1},
         {h:'Follow them to the next company',p:'We track where they land and reach out. They already know who you are.',tg:'We run this ourselves'},
         {h:'Ask at the happy moment',p:'AI notices when things go well, a clean install, a great survey, a fast fix, and prompts the referral ask at the right time.'}]));

 mk('n-convert','04 Convert',
  "CONVERT. 'Now the lists you already own: target accounts, stalled deals, quiet leads.' Once you have the data, ask it the questions. What share of my target accounts have we actually met with in the last thirty days, ninety days, a hundred and eighty? Of those, which still have their decision maker, are those people still working there? That second question is the one that saves a rep from dialing someone who left a year ago. And re-engage quiet deals automatically when something changes on the account.",
  '<div class="kick">Revenue Efficiency Model · Win business from your current customer base</div><h2>Convert: <span class="grad">the lists you already own.</span></h2>'+ladder(3)+
  cards([{h:'Know your target accounts',p:'What share have we met with in the last 30, 90 and 180 days? Who has gone quiet?',hi:1},
         {h:'Are the decision makers still there?',p:'Check every contact on a target list against where they work now, before anyone picks up the phone.'},
         {h:'Wake up stalled deals',p:'Re-engage quiet deals automatically when something changes on the account.'}])+
  ask(['What percent of target accounts did we meet in 30 days? 90? 180?','Which still have their decision maker?']));

 mk('n-expand','05 Expand',
  "EXPAND. 'Net-new business is the most expensive thing you do, so you do it last and with a head start.' The AI Lead Finder: it leverages your own data to go out and find competitive leases and who the decision maker is on prospective accounts, so additional leads come to the surface. Second, intent: who is in the market right now. Third, AI research: a one-page brief on any account before the first touch. Then the territory intelligence engine, the first play, is exactly this. [Describe the AI Lead Finder only as far as you are comfortable; confirm details before you speak to them.]",
  '<div class="kick">Revenue Efficiency Model · Focus on net new business</div><h2>Expand: <span class="grad">a head start on every new account.</span></h2>'+ladder(4)+
  cards([{h:'AI Lead Finder',p:'Read the notes, emails and calls you already have to find competitive lease end dates, who signs, and who outsources IT. You saw it near the start.',hi:1},
         {h:'Know who is in the market',p:'Intent signals show who is researching right now, before they call a competitor.'},
         {h:'Research before the first touch',p:'A one-page brief on any account: who they are, what changed, who signs.'}]));


 /* ---- the AI Lead Finder: the process we have run for dealers (no client names) ---- */
 var st3=document.createElement('style');st3.textContent=
  '.lf{display:grid;grid-template-columns:1fr auto 1fr;gap:1.6vw;align-items:center;margin-top:2.6vh}.lf .ar2{font:400 clamp(2rem,3.4vw,3.6rem)/1 var(--disp);color:#FFB020}'+
  '.lfc{border:1px solid rgba(255,255,255,.16);border-radius:18px;padding:2.4vh 1.5vw;background:linear-gradient(165deg,rgba(255,255,255,.07),rgba(255,255,255,.015))}'+
  '.lfc .cap{font:700 clamp(11px,.85vw,14px)/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:#8893AA;margin-bottom:1.4vh}'+
  '.lfc.note{font:italic 500 clamp(15px,1.45vw,27px)/1.5 var(--sans);color:#D2D9E8}.lfc.note mark{background:rgba(255,176,32,.22);color:#fff;border-radius:5px;padding:0 .25em}'+
  '.lfc.out{border-color:rgba(182,255,60,.55);background:linear-gradient(165deg,rgba(182,255,60,.12),rgba(182,255,60,.02))}'+
  '.lfr{display:flex;justify-content:space-between;gap:1vw;padding:1vh 0;border-bottom:1px solid rgba(255,255,255,.1);font:600 clamp(14px,1.3vw,24px)/1.25 var(--sans)}.lfr:last-child{border-bottom:0}.lfr span:first-child{color:#A9B2C6;font-weight:700;font-size:.8em;letter-spacing:.1em;text-transform:uppercase;align-self:center}.lfr b{color:#fff;text-align:right}'+
  '.lfx .ncd{padding:1.8vh 1.1vw}.lfx .ncd .no{font-size:clamp(1.2rem,1.8vw,2.1rem)}.lfx .ncd h3{font-size:clamp(1rem,1.5vw,1.8rem);margin:.5vh 0 .6vh}.lfx .ncd p{font-size:clamp(12.5px,1vw,18px)}.lfc.note{font-size:clamp(14px,1.3vw,24px)}.lfr{font-size:clamp(13px,1.15vw,21px);padding:.7vh 0}'+
  '.srcs{display:flex;flex-wrap:wrap;gap:.7vw;align-items:center;margin-top:2.6vh}.srcs b{font:700 clamp(12px,.95vw,16px)/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#4DE8FF;margin-right:.4vw}.srcs span{font:600 clamp(13px,1.1vw,20px)/1.2 var(--sans);color:#E4E9F5;border:1px solid rgba(77,232,255,.45);background:rgba(77,232,255,.07);border-radius:999px;padding:.9vh 1vw}'+
  '.lf2{display:grid;grid-template-columns:1.25fr 1fr;gap:2.2vw;margin-top:2.4vh;align-items:start}.stl{display:flex;flex-direction:column;gap:1.1vh}.stl div{display:flex;gap:1vw;align-items:flex-start;border:1px solid rgba(255,255,255,.13);border-radius:14px;padding:1.3vh 1vw;background:rgba(255,255,255,.04)}'+
  '.stl i{font:400 clamp(1.3rem,2vw,2.2rem)/1 var(--disp);color:#FFB020;font-style:normal;flex:0 0 auto;min-width:1.4em}.stl b{display:block;font:400 clamp(1.05rem,1.55vw,1.9rem)/1.1 var(--disp);text-transform:uppercase;color:#fff}.stl p{margin:.3vh 0 0;font:500 clamp(12.5px,1.05vw,19px)/1.35 var(--sans);color:#BAC3D6}'+
  '.stl div.hi{border-color:rgba(182,255,60,.55);background:rgba(182,255,60,.07)}'+
  '@media (max-width:900px){.lf,.lf2{grid-template-columns:1fr}.lf .ar2{display:none}}'+
  '@media (max-height:820px){.lf{margin-top:1.6vh}.lf2{margin-top:1.4vh}.stl{gap:.7vh}.stl div{padding:.9vh .9vw}.lfc{padding:1.6vh 1.2vw}.srcs{margin-top:1.6vh}}';
 document.head.appendChild(st3);
 mk('n-lf','05 Expand',
  "THE AI LEAD FINDER, part one: the idea. THIS IS YOUR FAST-ROI EXAMPLE, near the start, before the Triple A. Frame it: 'Before I give you any framework, here is one place AI pays back immediately, with data you already own.'  'Your CRM is full of leads, and they are hiding in sentences. Years of notes, tasks, emails, call transcripts and meeting notes. Somebody wrote down the competitor's lease end date, who the decision maker is, that the IT is outsourced. It is in free text, so no report can see it, and only a small share of reps ever filled in a structured lease field.' Read the example: a messy note on the left, structured fields on the right. 'AI reads the note the way a person would, and writes the answer into real fields: lease end, the competitor and the equipment, the decision maker, whether IT is outsourced, and how sure we are.' [The note is an illustration with a made-up account. Do not name any client.] Then: 'Now the process.'",
  '<div class=\"kick\">A fast win · the AI Lead Finder</div><h2>Your CRM already knows <span class=\"grad\">who is up for renewal.</span></h2>'+
  '<div class=\"lf\"><div class=\"lfc note\"><div class=\"cap\">What a rep typed, three years ago</div>“Spoke with Linda, she signs. <mark>Ricoh lease runs through Dec 2027.</mark> <mark>IT is outsourced to an outside vendor.</mark> Not thrilled with service. Call back next year.”</div><div class=\"ar2\">&rarr;</div>'+
  '<div class=\"lfc out\"><div class=\"cap\">What the AI writes into your CRM</div>'+
  '<div class=\"lfr\"><span>Competitive lease ends</span><b>Dec 2027</b></div><div class=\"lfr\"><span>Competitor</span><b>Ricoh</b></div><div class=\"lfr\"><span>Decision maker</span><b>Linda, signs</b></div><div class=\"lfr\"><span>IT outsourced?</span><b>Yes, outside vendor</b></div><div class=\"lfr\"><span>Confidence</span><b>Stated by the prospect</b></div></div></div>'+
  '<div class=\"srcs\"><b>The AI reads</b><span>Notes</span><span>Tasks</span><span>Emails</span><span>Call transcripts</span><span>Meeting notes</span></div>'+
  '<div class=\"lfx\">'+cards([{no:'01',h:'Competitive lease end dates',p:'Who is up for renewal in the next 12 months, and who is already past it.',hi:1},{no:'02',h:'Competitor and equipment',p:'Which brand is in the building, and what the customer said about it.'},{no:'03',h:'Decision makers',p:'Who signs, and who changed since you last called.'},{no:'04',h:'Who outsources IT',p:'Your managed-IT cross-sell list, found in the same pass.'}],'c4').replace('class=\"cds c4\"','class=\"cds c4\" style=\"margin-top:2vh\"')+'</div>'+
  '<p class=\"src\" style=\"margin-top:1.4vh\">Illustration. Made-up account and note.</p>');

 mk('n-lf2','05 Expand',
  "THE AI LEAD FINDER, part two: the process. Walk the six steps. ONE: connect to the history you already own; this is read-only, nothing is changed in your CRM. TWO: mine it. Keyword and meaning search across notes, tasks, emails, calls and meetings, looking for lease dates, competitor names, who signs, whether IT is outsourced. THREE: write the answers into a handful of structured fields, so a list can finally be built. FOUR: score how sure we are. A date the prospect stated in their own email beats a date a rep reconstructed; a date calculated from an old activity plus a typical term, say a 2022 install and a five-year lease, gives a 2027 estimate, and we label it as an estimate. Never let a guess override a fact. FIVE: a view and tasks, so reps get a short list of accounts expiring in the next twelve months, with the evidence quoted. SIX: stop the leak. Add the lease date and IT-outsourcing discovery questions to every future call so the data is structured from here on. Then the proof, all from our own work: on one large dealer's history it found about 2,600 competitive lease end dates; doing this by hand took about twenty hours, with the AI it took about one; and in the first marketing test, twenty to thirty touches booked three to four meetings. Then bridge to the shows of hands: 'That is what is possible when the data is readable. Now let me find out where this room is.' [Be accurate: those are results from real engagements, shared without names. If asked, we run this as a pilot on a slice of a dealer's CRM history.]",
  '<div class=\"kick\">A fast win · the AI Lead Finder · the process</div><h2>Six steps from <span class=\"grad\">buried notes to a booked meeting.</span></h2>'+
  '<div class=\"lf2\"><div class=\"stl\">'+
  [['1','Connect to the history','Read-only access to years of notes, tasks, emails, calls and meetings. Nothing in your CRM changes.',0],['2','Mine it for signals','Search by words and by meaning for lease dates, competitors, who signs, and who outsources IT.',0],['3','Write it into real fields','A few structured fields, so a list can finally be built from it.',1],['4','Score how sure we are','A date the prospect stated beats a rep’s memory. A calculated date is labeled an estimate.',0],['5','Hand reps a short list','A view and tasks: accounts expiring in 12 months, with the evidence quoted.',0],['6','Stop the leak','Two discovery questions on every call from now on, so the data arrives structured.',0]].map(function(r){return '<div'+(r[3]?' class=\"hi\"':'')+'><i>'+r[0]+'</i><span><b>'+r[1]+'</b><p>'+r[2]+'</p></span></div>'}).join('')+'</div>'+
  '<div><div class=\"stat\"><div class=\"v\">~2,600</div><div class=\"k\">Competitive lease end dates found in one large dealer’s history</div></div><div class=\"stat\"><div class=\"v\">20 hrs &rarr; 1</div><div class=\"k\">To find the lease leads: by hand, then with the AI</div></div><div class=\"stat\"><div class=\"v\">3 to 4</div><div class=\"k\">Meetings booked from the first 20 to 30 outreach touches</div></div></div></div>');

 /* ---- in the field ---- */
 mk('n-field','In the field',
  "IN THE FIELD. Frame it as imagination plus today. 'Imagine a rep walking a prospect's building wearing smart glasses. Like on a Zoom or Teams call, it picks up the conversation so all of that context lands in the CRM. You ask permission, at least for the important parts. Then they snap a quick picture of each machine and its meter page. When all the pictures are in, they push them to the AI and say: create me a proposal from every configuration you see here, with the meters and pages printed on each.' Be straight: 'The glasses are where this is going. A phone does most of it today.' Then the sales process and the proposal machine.",
  '<div class="kick">In the field · where this is going</div><h2>Walk the building. <span class="grad">AI does the paperwork.</span></h2>'+
  '<div class="stp"><div class="ncd"><span class="tagp">Talk</span><h3>The conversation is captured</h3><p>Smart glasses or a phone pick up the call, with permission, so the context lands in your CRM like a Zoom or Teams meeting.</p></div><div class="ar2">&rarr;</div>'+
  '<div class="ncd"><span class="tagp">Snap</span><h3>A photo of each machine</h3><p>A quick picture of every device and its meter page. No clipboard.</p></div><div class="ar2">&rarr;</div>'+
  '<div class="ncd hi"><span class="tagp">Propose</span><h3>Build me a proposal</h3><p>Push the pictures to AI: create a proposal from every configuration you see here. A branded draft comes back for the rep to approve.</p></div></div>'+
  '<p class="src" style="margin-top:2vh">Ask permission first. The glasses are where this is going; a phone does most of it today.</p>');

 /* ---- marketing ---- */
 mk('n-mkt','Marketing and attracting',
  "MARKETING AND ATTRACTING. 'Now the other side of the house: getting found and getting heard.' Four jobs. Be found: your website, SEO and AEO, the answers AI gives about you; that is the analysis I ran on all eleven of your sites, next. Publish: blogs, email and case studies drafted from real installs. Listen: AI listening to social and the market and telling you what to answer. Show: video; the film you watched was made this way. 'Let me show you what we found when we measured you.'",
  '<div class="kick">Marketing and attracting</div><h2>Be found. Be heard. <span class="grad">Be seen.</span></h2>'+
  '<div class="cds c4" style="margin-top:3vh">'+
  [['01','Be found','Your website, SEO and AEO, and the answers AI gives about you.','Measured next',1],['02','Publish','Blogs, email and case studies drafted from real installs, in your voice.','',0],['03','Listen','AI listens to social and the market and tells you what to answer.','',0],['04','Show','Video content. The film you watched was made this way.','',0]].map(function(c){return '<div class="ncd'+(c[4]?' hi':'')+'"><div class="no">'+c[0]+'</div><h3>'+c[1]+'</h3><p>'+c[2]+'</p>'+(c[3]?'<span class="tg">'+c[3]+'</span>':'')+'</div>'}).join('')+'</div>');

 /* ---- admin and operations ---- */
 mk('n-ops','Admin and operations',
  "ADMIN AND OPERATIONS. 'The back side of the house. Same idea as Keep: connect the AI to your ERP and your CRM and just ask.' Read the three questions. 'Which orders are past due? It gives me the answer, with the customer, the rep and what is holding each one. Which contracts renew next quarter with no call booked? Where do our invoices disagree with the contract?' The answers are illustrations; the point is that a question you could not ask yesterday now takes ten seconds. Then the Sales Admin map. The same-deal-typed-five-times chart you saw earlier is the problem it fixes.",
  '<div class="kick">Admin and operations · ask your data</div><h2>Which orders are <span class="grad">past due?</span></h2>'+
  '<div class="chat"><div class="q">Which orders are past due?</div><div class="a">The open orders past their delivery date, oldest first, with the customer, the rep and what is holding each one.</div>'+
  '<div class="q">Which contracts renew next quarter with no call booked?</div><div class="a">The renewals in the next 90 days with nothing on the calendar, grouped by rep, with the last conversation for each.</div>'+
  '<div class="q">Where do our invoices disagree with the contract?</div><div class="a">The invoices that charge something the contract does not say, with both numbers side by side.</div></div>'+
  '<p class="src" style="margin-top:1.6vh">Illustration. The answers come from your own ERP and CRM, connected through an MCP.</p>');

 /* the chapter numeral on the Triple A card is a leftover from the old order */
 var tA=document.querySelector('#deck > section[data-sk^="03 Three rungs|ThreeRungs"]');if(tA)[].forEach.call(tA.querySelectorAll('*'),function(e){if(!e.children.length&&/^\s*0?3\s*$/.test(e.textContent))e.style.display='none'});


 /* ---- the real challenge: no shared place for the data, so everyone repeats the same work ---- */
 mk('n-lake','The Triple A of AI',
  "THE REAL CHALLENGE. 'Here is what holds most dealers back, and it is not the AI. It is that the data has no home. The ERP has some, the CRM has some, email has some, the service system, the leasing portal, shared drives, the call recordings, and a lot of it lives in spreadsheets on one person's desktop. So everybody builds their own copy. The rep makes a prospect list. Marketing exports a different one. Service keeps its own notes. Admin retypes the same signed deal into five systems. And everybody has their own AI chat that starts from zero. A lot of people doing a lot of the same things.' Then the fix: 'A data lake sounds technical, and it is only one way to do this. The real requirement is that the data is connected, so the AI can read all of it. It can stay where it lives, in the ERP, the CRM, the service system, as long as it is connected through the connectors and the APIs we just covered. Or you land a copy in one place. Either works. Start with the three systems that matter most and connect those.' Land it: 'Because all of it can be reached, the AI can finally give you a real answer, not a guess, and you can build things on top of it: the list, the report, the automation, the app. Build it once. Everyone uses the same one.' Then the second brain slide.",
  '<div class=\"kick\">The real challenge</div><h2>The data isn\u2019t connected, <span class=\"grad\">so everyone repeats the same work.</span></h2>'+
  '<div class=\"lf\"><div class=\"lfc\"><div class=\"cap\">Today · the same work, five times</div>'+
  [['Sales rep','Builds a prospect list in a spreadsheet.'],['Marketing','Exports a different list from the CRM.'],['Service','Keeps customer notes in the service system.'],['Admin','Retypes the signed deal into five systems.'],['Everyone','Has an AI chat that starts from zero.']].map(function(r){return '<div class=\"lfr\"><span>'+r[0]+'</span><b style=\"font-weight:600;text-align:right\">'+r[1]+'</b></div>'}).join('')+'</div>'+
  '<div class=\"ar2\">&rarr;</div>'+
  '<div class=\"lfc out\"><div class=\"cap\">Connected · one place the AI can reach</div>'+
  '<div class=\"srcs\" style=\"margin-top:0\"><span>ERP</span><span>CRM</span><span>Email</span><span>Calls</span><span>Documents</span><span>Service tickets</span></div>'+
  '<div style=\"text-align:center;font:400 clamp(1.3rem,2vw,2.3rem)/1.1 var(--disp);color:#B6FF3C;margin:1.6vh 0;white-space:nowrap\">&darr; connected once, read together &darr;</div>'+
  '<div class=\"lfr\"><span>Ask</span><b>Real answers, from all of it</b></div><div class=\"lfr\"><span>Build</span><b>Lists, reports, automations, apps</b></div><div class=\"lfr\"><span>Result</span><b>Built once. Used by every team.</b></div></div></div>'+
  '<div class=\"mon\"><b>Start small</b><span>It does not all have to sit in one lake. It has to be connected. Pick the three systems that matter most and connect them, or land a copy in one place. Then connect the AI to it.</span></div>');

 /* ---- second brain, used across the organization ---- */
 var st4=document.createElement('style');st4.textContent=
  '.brn{display:grid;grid-template-columns:1fr auto 1.25fr;gap:1.5vw;align-items:center;margin-top:2.4vh}.brn .col{display:flex;flex-direction:column;gap:1vh}'+
  '.brn .in,.brn .dp{border:1px solid rgba(255,255,255,.14);border-radius:14px;padding:1.2vh 1vw;background:rgba(255,255,255,.05)}.brn .in b,.brn .dp b{display:block;font:400 clamp(1rem,1.5vw,1.8rem)/1.1 var(--disp);text-transform:uppercase;color:#fff}.brn .in p,.brn .dp p{margin:.3vh 0 0;font:500 clamp(12.5px,1.05vw,19px)/1.35 var(--sans);color:#BAC3D6}'+
  '.brn .dp{border-color:rgba(255,176,32,.35)}.brn .dp b{color:#FFB020}.brn .hub{width:clamp(110px,13vw,230px);aspect-ratio:1;border-radius:50%;display:flex;align-items:center;justify-content:center;text-align:center;font:400 clamp(1.1rem,1.9vw,2.2rem)/1.05 var(--disp);text-transform:uppercase;color:#0B0D15;background:radial-gradient(circle at 35% 30%,#D8FF7A,#B6FF3C 55%,#7FD41E);box-shadow:0 0 0 .8vw rgba(182,255,60,.14),0 0 0 1.6vw rgba(182,255,60,.07)}'+
  '.brn .cap2{font:700 clamp(11px,.85vw,14px)/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:#8893AA;margin-bottom:.4vh}'+
  '.mon{display:flex;gap:1vw;align-items:center;margin-top:2.4vh;border-left:4px solid #B6FF3C;padding:1.2vh 1.2vw;background:rgba(182,255,60,.08);border-radius:0 12px 12px 0}.mon b{flex:0 0 auto;font:700 clamp(12px,.95vw,16px)/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#B6FF3C}.mon span{font:600 clamp(14px,1.25vw,23px)/1.35 var(--sans);color:#fff}'+
  '@media (max-width:900px){.brn{grid-template-columns:1fr}.brn .hub{margin:0 auto}}@media (max-height:820px){.brn{margin-top:1.4vh}.brn .col{gap:.7vh}.mon{margin-top:1.4vh}}';
 document.head.appendChild(st4);
 mk('n-brain','The Triple A of AI',
  "YOUR SECOND BRAIN, and how it gets used across the whole company. 'Memory is the word that matters most here. Without it, every conversation with an AI starts from zero. With it, the AI knows your business: your documents, your CRM and ERP through those connectors and MCPs, your past conversations, and how you do things.' Walk left to right. 'Four things go in: your documents, your systems, your conversations, your decisions. One brain. Then every team gets something different out of it.' Sales walks in knowing the account and what was promised. Service finds the fix in years of tickets and manuals. Marketing writes in your voice from your own case studies. Admin and operations: the pricing rules and the contract terms. Leadership asks the business a question and gets an answer with the source. Caution, and say it: not everything goes to everyone. Start with one team and one folder, then connect one system, then let it keep notes. [Do not over-promise: this is where the tools are going and where the early adopters are today.]",
  '<div class=\"kick\">Memory, connectors and MCP, put to work</div><h2>Your second brain, <span class=\"grad\">used across the whole company.</span></h2>'+
  '<div class=\"brn\"><div class=\"col\"><div class=\"cap2\">What goes in</div>'+
  [['Your documents','Price lists, proposals, contracts, manuals, case studies.'],['Your systems','CRM and ERP, through connectors and MCP.'],['Your conversations','Calls, emails and meeting notes.'],['Your decisions','Your rules, your voice, what has worked.']].map(function(c){return '<div class=\"in\"><b>'+c[0]+'</b><p>'+c[1]+'</p></div>'}).join('')+'</div>'+
  '<div class=\"hub\">One shared<br>brain</div>'+
  '<div class=\"col\"><div class=\"cap2\">What each team gets out</div>'+
  [['Sales','Walks in knowing the account, the history and what was promised.'],['Service','Finds the fix in years of tickets and manuals.'],['Marketing','Writes in your voice, from your own case studies.'],['Admin and operations','Knows your pricing rules and contract terms.'],['Leadership','Ask the business a question. Get the answer and the source.']].map(function(c){return '<div class=\"dp\"><b>'+c[0]+'</b><p>'+c[1]+'</p></div>'}).join('')+'</div></div>'+
  '<div class=\"mon\"><b>Start small</b><span>One team, one folder, one connected system. Then let it keep notes. Not everything goes to everyone.</span></div>');

 /* ---- one concrete Monday action on each step of the model ---- */
 [['n-keep','Pull the last 90 days of service tickets and ask the AI which customers had three or more problems.'],['n-grow','Export your customer list and ask which fit your best-customer profile but buy only one thing from you.'],['n-multiply','List your champions and decision makers, and set an alert for anyone who changes companies.'],['n-convert','Take your target account list and ask which have had no meeting in 180 days.'],['n-expand','Pick one account list and ask the AI to find lease end dates in your old notes.']].forEach(function(m){var w=document.querySelector('#'+m[0]+' .in-wrap');if(w)w.insertAdjacentHTML('beforeend','<div class=\"mon\"><b>Monday</b><span>'+m[1]+'</span></div>')});

 /* ---- copier dealers do not take calls at 2 a.m.: after-hours wording across every slide ---- */
 var FIX=[['The call at 2am, decided.','The service call, decided.'],['The call at 2am.','The call nobody picks up.'],['2am, a Saturday, or your busiest Monday','After five, at lunch, or your busiest Monday'],['2am or Monday','After hours'],['Calls at 2am, and every','After-hours calls, and every'],['the 2am calls','the after-hours calls'],['This is the call at 2am','This is the service call'],['Two in the morning, Saturday, or your busiest Monday.','After five, over lunch, or your busiest Monday.'],['the 2am call flow chart','the service-call flow chart'],['the service call at 2am,','the service call,']];
 function fixCopy(str){FIX.forEach(function(f){str=str.split(f[0]).join(f[1])});return str}
 [].forEach.call(host.querySelectorAll('section'),function(sec){
  ['data-notes','aria-label'].forEach(function(a){var v=sec.getAttribute(a);if(v){var n2=fixCopy(v);if(n2!==v)sec.setAttribute(a,n2)}});
  [].forEach.call(sec.querySelectorAll('[aria-label]'),function(e){var v=e.getAttribute('aria-label'),n2=fixCopy(v);if(n2!==v)e.setAttribute('aria-label',n2)});
  [].forEach.call(sec.querySelectorAll('h1,h2,h3'),function(h){var v=h.innerHTML,n2=v.split('The call at 2am, <span class="grad">decided.').join('The service call, <span class="grad">decided.').split('The call at <span class="grad">2am.</span>').join('The call <span class="grad">nobody picks up.</span>');if(n2!==v)h.innerHTML=n2});
  var tw=document.createTreeWalker(sec,NodeFilter.SHOW_TEXT,null),nd;while((nd=tw.nextNode())){var v2=fixCopy(nd.nodeValue);if(v2!==nd.nodeValue)nd.nodeValue=v2}});
 }
})();
