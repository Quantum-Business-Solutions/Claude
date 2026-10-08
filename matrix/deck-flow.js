/* ICDA 2026 deck: flow charts, the API show of hands, and an open task library (loaded last, from deck-qr.js).
   Waits until deck-real.js has finished building the deck, then adds to it.
   The steps and who does them (AI does it / AI assists / you) come from the four role process maps already in the deck. */
(function(){
 var tries=0;(function wait(){if(window.DECK&&document.getElementById('real-enrich')){run();return}if(++tries>240)return;setTimeout(wait,150)})();
 function run(){
 var SL=DECK.slides;
 function put(s,after){after.parentNode.insertBefore(s,after.nextSibling);SL.splice(SL.indexOf(after)+1,0,s);
  if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)e.target.classList.add('in')})},{threshold:[0.25]});io.observe(s)}else s.classList.add('in')}
 function sec(id,data,notes,html){var s=document.createElement('section');s.className='s rl fc';s.id=id;s.setAttribute('data-sec',data);s.setAttribute('data-notes',notes);s.setAttribute('data-sk',data+'|'+id);s.innerHTML='<div class="mesh"></div><div class="in-wrap">'+html+'</div>';return s}

 var st=document.createElement('style');st.textContent=
  '.fc .in-wrap{max-width:min(1500px,94vw)}.fc h2{font-size:clamp(1.7rem,3.4vw,3rem)!important;margin-bottom:0}'+
  '.fc svg.fl{width:100%;height:auto;max-height:55vh;display:block;margin-top:1.6vh;overflow:visible}'+
  '.fl .band{fill:rgba(255,255,255,.028);stroke:rgba(255,255,255,.09)}.fl .bl{fill:#8893AA;font:700 12.5px var(--sans);letter-spacing:.18em}'+
  '.fl .fn .bx{fill:rgba(18,21,32,.96);stroke:rgba(255,255,255,.2);stroke-width:1.4}'+
  '.fl .k-ai .bx{stroke:rgba(182,255,60,.6)}.fl .k-ai .cb{fill:#B6FF3C}.fl .k-as .bx{stroke:rgba(255,176,32,.7)}.fl .k-as .cb{fill:#FFB020}.fl .k-you .bx{stroke:rgba(136,147,170,.7)}.fl .k-you .cb{fill:#8893AA}.fl .k-bad .bx{stroke:rgba(255,90,31,.7)}.fl .k-bad .cb{fill:#FF5A1F}'+
  '.fl .fn .t{fill:#fff;font:700 15px var(--sans)}.fl .fn .s{fill:#A9B2C6;font:500 12.5px var(--sans)}'+
  '.fl .dia{fill:rgba(77,232,255,.1);stroke:rgba(77,232,255,.7);stroke-width:1.5}.fl .dt{fill:#fff;font:700 13.5px var(--sans);text-anchor:middle}'+
  '.fl .ar{fill:none;stroke:#7E889F;stroke-width:2}.fl .ar.g{stroke:#B6FF3C}.fl .ar.o{stroke:#FFB020;stroke-dasharray:7 6}.fl .ar.r{stroke:#FF5A1F;stroke-dasharray:6 5}'+
  '.fl .lb{fill:#B9C2D6;font:600 12.5px var(--sans)}.fl .lbo{fill:#FFB020;font:700 12.5px var(--sans)}.fl .big{fill:#FF5A1F;font:400 34px var(--disp)}.fl .big.g{fill:#B6FF3C}.fl .bigs{fill:#A9B2C6;font:700 12.5px var(--sans);letter-spacing:.12em}'+
  '.fl .pill rect{fill:#FF5A1F}.fl .pill text{fill:#fff;font:700 12.5px var(--sans);text-anchor:middle}'+
  '.fl .hot .hn{fill:#fff;font:700 15px var(--sans);text-anchor:middle}.fl .hot .dot{fill:#FF5A1F;stroke:#0B0D15;stroke-width:2}.fl .hot .pl{fill:rgba(255,90,31,.4);transform-box:fill-box;transform-origin:center;animation:flp 2.2s ease-out infinite}'+
  '@keyframes flp{0%{transform:scale(1);opacity:.9}100%{transform:scale(2.2);opacity:0}}@media (prefers-reduced-motion:reduce){.fl .hot .pl{animation:none}}'+
  '.fl .fcap{fill:#E4E9F5;font:600 14.5px var(--sans)}'+
  '.hcap{display:grid;grid-template-columns:repeat(5,1fr);gap:1vw;margin-top:1.6vh}.hcap.c3{grid-template-columns:repeat(3,1fr)}.hcap>div{display:flex;gap:.6vw;align-items:flex-start;font:500 clamp(12px,.92vw,15px)/1.35 var(--sans);color:#C3CBDC}'+
  '.hcap b{flex:0 0 auto;width:clamp(22px,1.7vw,30px);height:clamp(22px,1.7vw,30px);border-radius:50%;background:#FF5A1F;color:#fff;display:flex;align-items:center;justify-content:center;font:700 clamp(12px,.9vw,15px) var(--sans)}'+
  '.fc .legend{margin-top:1.4vh}.fc .legend .hl{color:#FF8A3D}'+
  '@media (max-height:820px){.fc svg.fl{max-height:51vh;margin-top:1vh}.hcap{margin-top:1vh}.fc .legend{margin-top:.8vh}}'+
  '@media (max-width:900px){.hcap,.hcap.c3{grid-template-columns:1fr 1fr}}';
 document.head.appendChild(st);

 /* drawing helpers */
 function node(x,y,w,h,k,t,s){return '<g class="fn k-'+k+'" transform="translate('+x+' '+y+')"><rect class="bx" width="'+w+'" height="'+h+'" rx="12"/><rect class="cb" width="6" height="'+h+'" rx="3"/><text class="t" x="18" y="'+(s?h/2-3:h/2+5)+'">'+t+'</text>'+(s?'<text class="s" x="18" y="'+(h/2+15)+'">'+s+'</text>':'')+'</g>'}
 function dia(cx,cy,w,h,a,b){return '<g><polygon class="dia" points="'+cx+','+(cy-h/2)+' '+(cx+w/2)+','+cy+' '+cx+','+(cy+h/2)+' '+(cx-w/2)+','+cy+'"/><text class="dt" x="'+cx+'" y="'+(b?cy-3:cy+5)+'">'+a+'</text>'+(b?'<text class="dt" x="'+cx+'" y="'+(cy+13)+'">'+b+'</text>':'')+'</g>'}
 function ar(d,c){return '<path class="ar '+(c||'')+'" d="'+d+'" marker-end="url(#ah'+(c||'')+')"/>'}
 function lb(x,y,t,a,c){return '<text class="'+(c||'lb')+'" x="'+x+'" y="'+y+'"'+(a?' text-anchor="'+a+'"':'')+'>'+t+'</text>'}
 function hot(x,y,n){return '<g class="hot" transform="translate('+x+' '+y+')"><circle class="pl" r="14"/><circle class="dot" r="14"/><text class="hn" y="5">'+n+'</text></g>'}
 function band(y,h,t){return '<rect class="band" x="0" y="'+y+'" width="1200" height="'+h+'" rx="14"/>'+lb(16,y+22,t,null,'bl')}
 var DEFS='<defs><marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#7E889F"/></marker><marker id="ahg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#B6FF3C"/></marker><marker id="aho" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#FFB020"/></marker><marker id="ahr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#FF5A1F"/></marker></defs>';
 function svg(h,label,body){return '<svg class="fl" viewBox="0 0 1200 '+h+'" role="img" aria-label="'+label+'">'+DEFS+body+'</svg>'}
 var LEG='<div class="legend"><span><b style="background:var(--lime)"></b>AI does it</span><span><b style="background:var(--amber)"></b>AI assists</span><span><b style="background:#3A4152"></b>Stays yours</span><span class="hl"><b style="background:#FF5A1F;border-radius:50%"></b>Where the time leaks</span></div>';

 /* ---- 1. one deal, start to renewal ---- */
 var f1=svg(430,'Flow chart: one deal from trigger to renewal, with five places the time leaks',
  band(0,132,'SELL')+band(142,132,'ORDER & INSTALL')+band(284,132,'SERVICE & KEEP')+
  node(22,40,170,60,'ai','Trigger spotted','caught overnight')+node(214,40,170,60,'ai','Account researched','one-page brief')+node(406,40,170,60,'ai','First touch written','rep approves')+
  dia(650,70,112,86,'Reply?')+node(752,40,228,60,'as','Discovery to close','AI preps, notes, drafts')+
  ar('M192 70H212')+ar('M384 70H404')+ar('M576 70H594')+ar('M706 70H750','g')+lb(728,61,'yes','middle')+
  ar('M650 113V124H491V102','o')+lb(572,118,'no: AI follows up','middle','lbo')+
  node(1012,182,168,60,'ai','Contract signed','starts everything')+node(816,182,176,60,'ai','Credit app & lease','pre-filled')+node(640,182,156,60,'ai','Order entered','no retyping')+node(456,182,164,60,'ai','Install & meters','booked, enrolled')+node(272,182,164,60,'ai','Commission paid','from the deal')+node(70,182,182,60,'you','Exceptions','only what needs you')+
  ar('M980 70H1096V180')+ar('M1012 212H994')+ar('M816 212H798')+ar('M640 212H622')+ar('M456 212H438')+ar('M272 212H254')+
  node(22,324,190,60,'ai','Service call answered','AI agent, first ring')+node(234,324,172,60,'ai','Ticket & dispatch','right tech, right part')+node(428,324,160,60,'you','Tech on site','note captured')+
  dia(676,354,124,88,'Upgrade or','risk signal?')+node(784,324,200,60,'ai','Flagged to sales','talking points attached')+node(1006,324,174,60,'ai','Renewal clock set','next call booked')+
  ar('M195 242V322')+ar('M212 354H232')+ar('M406 354H426')+ar('M588 354H612')+ar('M738 354H782','g')+lb(760,345,'yes','middle')+ar('M984 354H1004')+ar('M676 398V408')+lb(690,408,'no: logged')+
  '<path class="ar o" d="M1093 384V422H8V70H20" marker-end="url(#aho)"/>'+lb(330,416,'What the tech saw feeds the next sale','middle','lbo')+
  hot(380,34,1)+hot(976,34,2)+hot(988,176,3)+hot(206,318,4)+hot(978,318,5));
 var s1=sec('flow-deal','04 Time back',
  "THE FLOW CHART. Point, do not read. 'This is one deal, from the trigger to the renewal, in the three jobs you already have: the rep, sales admin, and service. Green is AI doing it, amber is AI helping, grey is you.' Then walk the five red dots. ONE: before the first call, someone looks the account up and writes the email. TWO: a walkthrough takes three to five days to become a proposal. THREE: the signed deal gets retyped into the leasing portal, the ERP, scheduling, the meter tool and payroll. FOUR: the 2am calls and every toner request. FIVE: the tech sees everything inside the account and almost none of it reaches sales; follow the dashed arrow back to the start. 'That loop is the whole business: service knowledge becomes the next sale.' Ask: 'Where is the red dot in YOUR dealership?'",
  '<div class="kick">The whole flow · one deal, start to renewal</div><h2>Five places the time <span class="grad">leaks.</span></h2>'+f1+
  '<div class="hcap"><div><b>1</b><span>Looking up the account and writing the first email</span></div><div><b>2</b><span>Three to five days from walkthrough to proposal</span></div><div><b>3</b><span>One signed deal retyped into five systems</span></div><div><b>4</b><span>Calls at 2am, and every toner and meter request</span></div><div><b>5</b><span>What the tech saw never reaches sales</span></div></div>'+LEG);

 /* ---- 2. the same deal, typed five times ---- */
 var X=[240,420,600,780,960],NM=[['Leasing portal','credit app'],['ERP','order entry'],['Scheduling','delivery and install'],['Meter tool','DCA, FMAudit'],['Payroll','commission']],r1='',r2='',i;
 for(i=0;i<5;i++){r1+=node(X[i],74,150,60,'bad',NM[i][0],NM[i][1]);r2+=node(X[i],300,150,60,'ai',NM[i][0],NM[i][1]);
  var gx=i===0?172:X[i-1]+150;r1+=ar('M'+gx+' 104H'+(X[i]-2),'r');
  var pc=(gx+X[i])/2;r1+='<g class="pill" transform="translate('+(pc-30)+' 42)"><rect width="60" height="22" rx="11"/><text x="30" y="16">retype</text></g>';
  r2+=ar('M'+(X[i]+75)+' 270V298','g')}
 var f2=svg(420,'Flow chart: one signed deal retyped by hand into five systems today, versus entered once with AI',
  '<rect class="band" x="0" y="0" width="1200" height="196" rx="14"/>'+lb(16,22,'TODAY · RETYPED BY HAND','start','bl')+
  node(22,74,150,60,'you','Signed deal','the source')+r1+
  '<text class="big" x="1182" y="176" text-anchor="end">5 re-keys</text>'+
  '<rect class="band" x="0" y="214" width="1200" height="196" rx="14"/>'+lb(16,236,'WITH AI · ENTERED ONCE','start','bl')+
  node(22,300,150,60,'ai','Signed deal','entered once')+'<path class="ar g" d="M97 300V270H1035" />'+r2+
  lb(640,262,'one entry, every system follows','middle','lbo')+'<text class="big g" x="1182" y="392" text-anchor="end">1 entry</text>');
 var s2=sec('flow-retype','04 Time back',
  "THE RETYPING CHART. 'Same signed deal, two ways. On top is what happens in most dealerships: somebody retypes it into the leasing portal, then the ERP, then scheduling, then the meter tool, then payroll for the commission. Five re-keys. Every one is a delay and a chance for an error.' Point at the red 'retype' pills. 'Below: the same five systems, the same deal, entered once. You do not rip out a single system. The retyping goes.' Then: 'The grey is the human part: credit decisions and exceptions. That stays yours.' Ask: 'How many of those five does your admin retype today?' The five systems are the ones on the Sales Admin map.",
  '<div class="kick">The flow · signed to installed</div><h2>The same deal, typed <span class="grad">five times.</span></h2>'+f2+
  '<div class="hcap c3"><div><b>!</b><span>Each retype is a delay and a chance for an error</span></div><div><b>=</b><span>The five systems stay. The rekeying goes</span></div><div><b>+</b><span>Credit decisions and exceptions stay with a person</span></div></div>'+LEG);

 /* ---- 3. the call at 2am, as a decision flow ---- */
 var f3=svg(452,'Decision flow chart: the service call at 2am, from the call to a flag for sales',
  node(14,185,140,60,'you','Customer calls','2am or Monday')+node(176,185,162,60,'ai','AI agent answers','first ring')+node(360,185,150,60,'ai','Account found','caller ID or serial')+
  dia(592,215,124,94,'What do they','need?')+ar('M154 215H174')+ar('M338 215H358')+ar('M510 215H530')+
  node(716,30,214,60,'ai','Handled on the spot','toner, meters, invoices, ETAs')+node(950,30,230,60,'ai','Logged to dispatch','no person touched it')+
  ar('M592 168V60H714','g')+lb(602,120,'routine')+ar('M930 60H948','g')+
  node(716,185,176,60,'as','Talk through the fix','saves the truck roll')+ar('M654 215H714')+lb(684,205,'broken','middle')+
  dia(964,215,104,86,'Fixed?')+ar('M892 215H910')+node(1048,185,132,60,'ai','Closed','logged')+ar('M1016 215H1046','g')+lb(1031,205,'yes','middle')+
  node(1010,310,170,60,'ai','Ticket & tech','right tech, right part')+ar('M964 258V340H1008')+lb(976,300,'no')+
  node(812,310,170,60,'you','Tech on site','ETA texted first')+ar('M1010 340H984')+
  node(620,310,170,60,'ai','Flagged to sales','mined from the note')+ar('M812 340H792','g')+
  node(692,386,234,56,'you','Escalate to a person','upset or complex: human takes it')+ar('M592 262V414H690')+lb(584,330,'upset or complex','end')+
  hot(332,179,1)+hot(922,24,2)+hot(886,179,3)+hot(782,304,4)+
  '<g><circle cx="30" cy="318" r="12" fill="#FF5A1F"/><text x="30" y="323" text-anchor="middle" style="fill:#fff;font:700 13px var(--sans)">1</text><text class="fcap" x="52" y="323">Answered on the first ring</text></g>'+
  '<g><circle cx="30" cy="354" r="12" fill="#FF5A1F"/><text x="30" y="359" text-anchor="middle" style="fill:#fff;font:700 13px var(--sans)">2</text><text class="fcap" x="52" y="359">Routine requests need no person</text></g>'+
  '<g><circle cx="30" cy="390" r="12" fill="#FF5A1F"/><text x="30" y="395" text-anchor="middle" style="fill:#fff;font:700 13px var(--sans)">3</text><text class="fcap" x="52" y="395">A talked-through fix saves a truck roll</text></g>'+
  '<g><circle cx="30" cy="426" r="12" fill="#FF5A1F"/><text x="30" y="431" text-anchor="middle" style="fill:#fff;font:700 13px var(--sans)">4</text><text class="fcap" x="52" y="431">What the tech saw reaches sales</text></g>');
 var s3=sec('flow-call','04 Time back',
  "THE DECISION FLOW. 'This is the call at 2am, and it is a real flow chart: the diamonds are the decisions. The call comes in. An AI agent answers on the first ring, in your company name, and finds the account by caller ID or serial number. Then it decides what they need.' Go up: 'Toner, a meter read, an invoice copy, where is my tech. Handled on the spot, logged, no person touched it.' Go through the middle: 'Something is broken. It walks them through a fix. Fixed? Closed. Not fixed? It opens the ticket, picks the right tech and part, texts the ETA.' Then the bottom right: 'And here is the one nobody has: the tech note gets mined and flagged to sales.' Go down: 'Upset or complex goes to a person. Always.' Four red dots are where the time comes back. Ask: 'What share of your service calls today were toner or an ETA?'",
  '<div class="kick">The flow · the service call</div><h2>The call at 2am, <span class="grad">decided.</span></h2>'+f3+LEG);

 var bars=null;SL.forEach(function(s){if(!bars&&/WHERE THE HOURS COME BACK/i.test(s.textContent))bars=s});
 if(bars){put(s1,bars);put(s2,s1);put(s3,s2)}

 /* ---- 4. show of hands 04: connected by API ---- */
 var soh=null;SL.forEach(function(s){if(/Show of hands\s*·\s*03/.test(s.textContent))soh=s});
 if(soh){var c=soh.cloneNode(true);c.removeAttribute('id');c.classList.remove('in');
  [].forEach.call(c.querySelectorAll('[data-ek]'),function(e){e.removeAttribute('data-ek')});
  [].forEach.call(c.querySelectorAll('video,.scrim'),function(e){e.parentNode.removeChild(e)});
  var tg=c.querySelector('.tag');if(tg)tg.textContent='Show of hands · 04';
  var h=c.querySelector('h1');if(h)h.innerHTML='Keep them up if your AI is connected to <span class="grad">all your tools</span> through an API.';
  c.setAttribute('data-sk','Show of hands|api');
  c.setAttribute('data-notes',"Expect almost no hands. Hold the pause, then: 'An assistant in a browser tab cannot see your fleet, your service tickets or your contracts. It only knows what you paste into it. For the automation and the agent you need the plumbing: your CRM, your ERP, your ticketing, your email and your phones, connected to the AI through an API.' Then: 'That plumbing is the unglamorous work, and it is the whole difference between using AI and deploying it.' Optional: 'Who here has an API key for even one of these systems?'");
  put(c,soh)}

 /* ---- 5. the task library opens with every category expanded ---- */
 var acc=document.getElementById('acc');
 if(acc){var openAll=function(){[].forEach.call(acc.querySelectorAll('details'),function(d){d.open=true})};openAll();
  new MutationObserver(function(){openAll()}).observe(acc,{childList:true})}
 var lib=null;SL.forEach(function(s){if(!lib&&s.querySelector('#acc'))lib=s});
 if(lib)lib.setAttribute('data-notes',(lib.getAttribute('data-notes')||'').replace('Open one category live: Discovery for sales, or SEO for marketing. Click a heading to open or close it; scroll inside the panel.','Every category opens expanded. Scroll inside the panel; the headings still open and close, and Close all folds them.'));

 /* menu and position follow */
 var ml=document.getElementById('mlist');if(ml){var html='',last=null;SL.forEach(function(s,n){var sc=s.getAttribute('data-sec')||'';if(sc!==last){html+='<h4>'+sc+'</h4>';last=sc}
  var hh=s.querySelector('h1,h2,h3');var lab=hh?hh.textContent.replace(/\s+/g,' ').trim():(s.classList.contains('trailer')?'The video: The Old Way vs. The Quantum Way':'Slide '+(n+1));if(lab.length>72)lab=lab.slice(0,72)+'…';
  html+='<a href="#" data-n="'+n+'"><i>'+(n+1)+'</i><span>'+lab+'</span></a>'});ml.innerHTML=html}
 var s0=DECK.state();DECK.go(Math.min(s0.idx,SL.length-1));
 }
})();
