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
  '.nw .in-wrap{max-width:min(1500px,92vw)}.nw h2{font-size:clamp(1.8rem,3.9vw,3.4rem)!important;margin-bottom:0}.nw .sub{margin-top:1vh}'+
  '.lad{display:flex;flex-wrap:wrap;gap:.5vw;margin:1.8vh 0 2.2vh}.lad span{font:700 clamp(11px,.78vw,13px)/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#8893AA;border:1px solid rgba(255,255,255,.16);border-radius:999px;padding:.8vh .9vw}.lad span.on{background:#B6FF3C;color:#0B0D15;border-color:#B6FF3C}'+
  '.cds{display:grid;grid-template-columns:repeat(3,1fr);gap:1.2vw}.cds.c2{grid-template-columns:repeat(2,1fr)}.cds.c4{grid-template-columns:repeat(4,1fr)}.cds.c6{grid-template-columns:repeat(3,1fr)}'+
  '.ncd{position:relative;border:1px solid rgba(255,255,255,.14);border-radius:18px;padding:2.4vh 1.3vw 2.2vh;background:linear-gradient(165deg,rgba(255,255,255,.07),rgba(255,255,255,.015))}'+
  '.ncd .no{font:400 clamp(1.4rem,2.2vw,2.2rem)/1 var(--disp);color:#FFB020}.ncd h3{font:400 clamp(1.1rem,1.65vw,1.6rem)/1.1 var(--disp);text-transform:uppercase;color:#fff;margin:.9vh 0 1vh}'+
  '.ncd p{font:500 clamp(13px,1.05vw,17px)/1.45 var(--sans);color:#BAC3D6;margin:0}.ncd p b{color:#fff}.ncd .tg{display:inline-block;margin-top:1.2vh;font:700 clamp(11px,.72vw,12px)/1 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#B6FF3C}'+
  '.ncd.hi{border-color:rgba(182,255,60,.6);background:linear-gradient(165deg,rgba(182,255,60,.13),rgba(182,255,60,.02))}'+
  '.ask{display:flex;flex-wrap:wrap;gap:.7vw;align-items:center;margin-top:2.4vh}.ask b{font:700 clamp(11px,.8vw,13px)/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#4DE8FF;margin-right:.4vw}'+
  '.ask span{font:600 clamp(12px,.95vw,15px)/1.2 var(--sans);color:#E4E9F5;border:1px solid rgba(77,232,255,.45);background:rgba(77,232,255,.07);border-radius:999px;padding:.9vh 1vw}'+
  '.big3{display:grid;grid-template-columns:1.1fr 1fr;gap:2.4vw;align-items:center;margin-top:3vh}.stat{border:1px solid rgba(255,255,255,.14);border-radius:18px;padding:2.6vh 1.6vw;background:rgba(255,255,255,.04);margin-bottom:1.2vw}.stat:last-child{margin-bottom:0}'+
  '.stat .v{font:400 clamp(2.4rem,5vw,5rem)/1 var(--disp);background:var(--hot);-webkit-background-clip:text;background-clip:text;color:transparent}.stat .k{margin-top:1vh;font:700 clamp(11px,.85vw,14px)/1.35 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#A9B2C6}'+
  '.who .nm{font:400 clamp(2.6rem,6vw,6rem)/.95 var(--disp);text-transform:uppercase;color:#fff}.who .rl2{margin-top:1.4vh;font:600 clamp(14px,1.3vw,22px)/1.4 var(--sans);color:#C3CBDC}'+
  '.stp{display:grid;grid-template-columns:1fr auto 1fr auto 1fr;gap:1vw;align-items:stretch;margin-top:3vh}.stp .ar2{align-self:center;font:400 clamp(1.6rem,2.6vw,2.6rem)/1 var(--disp);color:#FFB020}'+
  '.tagp{display:inline-block;font:700 clamp(11px,.8vw,13px)/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#0B0D15;background:#FFB020;border-radius:6px;padding:.8vh .8vw;margin-bottom:1.2vh}'+
  '.chat{display:flex;flex-direction:column;gap:1.2vh;margin-top:2.6vh}.chat .q,.chat .a{max-width:78%;font:500 clamp(13px,1.1vw,18px)/1.4 var(--sans);border-radius:18px;padding:1.5vh 1.2vw}'+
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
  "These are the three patterns I see in dealerships of every size. EDIT THESE to your own three in Edit mode (press E, click the text). Suggested talk track: 'One: everybody has tried AI, almost nobody has deployed it; Frank Cannata says he hears very little about it from dealers. Two: the data you need is already in your CRM, your ERP and your service system, and nothing reads it. Three: the week gets eaten by retyping and chasing, the same deal keyed into five systems. None of this is about the technology. It is about the plumbing and the process.' Then the quote slide, then the shows of hands.",
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

 /* ---- the five steps ---- */
 mk('n-keep','01 Keep',
  "KEEP. 'First things first: before we chase anything new, keep the customers we have. This is the cheapest revenue in your business.' Three things. One: an assistant so nobody waits, on the phone, by text, at 2am; toner, meter reads, invoice copies, where is my tech. Two, and this is the big one: connect AI to your ERP and your CRM through an MCP and talk to your data. Read the four questions: where have there been anomalies, where are we missing opportunities, where have we had the most service problems, where have trends changed with customers. Three: reports and automations that flag the account before it leaves. Then walk the 2am call flow chart, the service process and the service-to-sales bridge that follow.",
  '<div class="kick">Revenue Efficiency Model · Retain your current customers</div><h2>Keep: <span class="grad">nobody waits.</span></h2>'+ladder(0)+
  cards([{h:'An assistant that never makes them wait',p:'Answers on the first ring, any hour: toner, meter reads, invoice copies, where is my tech.'},
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
  cards([{h:'AI Lead Finder',p:'Leverage your own data to find competitive leases and the decision maker on prospective accounts, and bring more leads to the surface.',hi:1},
         {h:'Know who is in the market',p:'Intent signals show who is researching right now, before they call a competitor.'},
         {h:'Research before the first touch',p:'A one-page brief on any account: who they are, what changed, who signs.'}]));

 /* ---- in the field ---- */
 mk('n-field','In the field',
  "IN THE FIELD. Frame it as imagination plus today. 'Imagine a rep walking a prospect's building wearing smart glasses. Like on a Zoom or Teams call, it picks up the conversation so all of that context lands in the CRM. You ask permission, at least for the important parts. Then they snap a quick picture of each machine and its meter page. When all the pictures are in, they push them to the AI and say: create me a proposal from every configuration you see here, with the meters and pages printed on each.' Be straight: 'The glasses are where this is going. A phone does most of it today.' Then the end-to-end flow chart and the proposal machine.",
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
  "ADMIN AND OPERATIONS. 'The back side of the house. Same idea as Keep: connect the AI to your ERP and your CRM and just ask.' Read the three questions. 'Which orders are past due? It gives me the answer, with the customer, the rep and what is holding each one. Which contracts renew next quarter with no call booked? Where do our invoices disagree with the contract?' The answers are illustrations; the point is that a question you could not ask yesterday now takes ten seconds. Then the same-deal-typed-five-times chart and the Sales Admin map.",
  '<div class="kick">Admin and operations · ask your data</div><h2>Which orders are <span class="grad">past due?</span></h2>'+
  '<div class="chat"><div class="q">Which orders are past due?</div><div class="a">The open orders past their delivery date, oldest first, with the customer, the rep and what is holding each one.</div>'+
  '<div class="q">Which contracts renew next quarter with no call booked?</div><div class="a">The renewals in the next 90 days with nothing on the calendar, grouped by rep, with the last conversation for each.</div>'+
  '<div class="q">Where do our invoices disagree with the contract?</div><div class="a">The invoices that charge something the contract does not say, with both numbers side by side.</div></div>'+
  '<p class="src" style="margin-top:1.6vh">Illustration. The answers come from your own ERP and CRM, connected through an MCP.</p>');
 }
})();
