/* ICDA 2026 deck: real examples (loaded last, from deck-polish.js).
   Cuts the MSP slide and the four repeated task lists, opens with the real Revenue Efficiency Model, and adds five stories from Quantum's own work.
   Every number below comes from the ClientCommand repo, the contact-verification repo, a HubSpot audit run on 29 Sept 2026,
   or Call Analysis on a client portal (anonymized). Edit the numbers here; nothing else needs republishing. */
(function(){if(!window.DECK)return;
 var SL=DECK.slides;
 function S(p){for(var i=0;i<SL.length;i++)if((SL[i].getAttribute('data-sk')||'').indexOf(p)===0)return SL[i];return null}
 function drop(s){if(!s)return;var i=SL.indexOf(s);if(i>-1)SL.splice(i,1);if(s.parentNode)s.parentNode.removeChild(s)}
 function note(s,a,b){if(s)s.setAttribute('data-notes',(s.getAttribute('data-notes')||'').split(a).join(b))}
 function sec(id,data,notes,html){var s=document.createElement('section');s.className='s rl';s.id=id;s.setAttribute('data-sec',data);s.setAttribute('data-notes',notes);s.innerHTML='<div class="mesh"></div><div class="in-wrap">'+html+'</div>';return s}
 function put(s,before){before.parentNode.insertBefore(s,before);var i=SL.indexOf(before);SL.splice(i,0,s);
  if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)e.target.classList.add('in')})},{threshold:[0.25]});io.observe(s)}else s.classList.add('in')}

 var st=document.createElement('style');st.textContent=
  '.rl .big{font:400 clamp(3rem,8.4vw,8rem)/.9 var(--disp);background:var(--hot);-webkit-background-clip:text;background-clip:text;color:transparent;white-space:nowrap}'+
  '.rl .cap{font:700 clamp(11px,.8vw,14px)/1.3 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#A9B2C6;margin-top:1vh}'+
  '.rl .src{margin-top:2.2vh;font:500 clamp(11px,.8vw,13px)/1.4 var(--sans);color:#8893AA}'+
  /* the real Revenue Efficiency Model image, cropped to its content on a white card */
  '.rem-card{margin:2vh auto 0;background:#fff;border-radius:18px;padding:1.4vh 1.4vw;display:block;width:fit-content;box-shadow:0 18px 60px rgba(0,0,0,.45)}'+
  '.rem-img{position:relative;overflow:hidden;height:min(66vh,calc((100vw - 320px)/1.7727));aspect-ratio:1.7727}.rem-img img{display:block;width:105.77%;max-width:none;margin-left:-3.846%;margin-top:-13.46%}'+
  /* built, not bought */
  '.bt{display:grid;grid-template-columns:1.05fr 1fr;gap:3vw;align-items:center;margin-top:3vh}'+
  '.bt .stats{display:grid;grid-template-columns:1fr 1fr;gap:1vw}.bt .stats>div{border:1px solid rgba(255,255,255,.14);border-radius:16px;padding:2vh 1.2vw;background:rgba(255,255,255,.04)}'+
  '.bt .stats .v{font:400 clamp(2rem,3.9vw,3.8rem)/1 var(--disp);color:#fff}.bt .stats .v em{font-style:normal;color:#B6FF3C}.bt .stats .k{margin-top:.8vh;font:700 clamp(11px,.78vw,13px)/1.3 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#A9B2C6}'+
  '.bt .stats .wide{grid-column:1/-1;border-color:rgba(182,255,60,.55);background:linear-gradient(160deg,rgba(182,255,60,.12),rgba(182,255,60,.02))}'+
  '.apps{display:grid;grid-template-columns:1fr 1fr;gap:.8vw}.apps>div{border:1px solid rgba(255,255,255,.12);border-radius:14px;padding:1.6vh 1vw;background:rgba(255,255,255,.035)}'+
  '.apps b{display:block;font:400 clamp(1rem,1.5vw,1.5rem)/1 var(--disp);text-transform:uppercase;color:#fff}.apps span{display:block;margin-top:.6vh;font:500 clamp(12px,.9vw,15px)/1.35 var(--sans);color:#A9B2C6}'+
  '.apps>div:first-child{grid-column:1/-1;border-color:rgba(255,176,32,.55)}'+
  /* funnel */
  '.fnl{margin-top:3.4vh;display:flex;flex-direction:column;gap:2.2vh}.fnl .r .lab{display:flex;align-items:baseline;gap:1vw}.fnl .r .num{font:400 clamp(2rem,4.6vw,4.4rem)/1 var(--disp);color:#fff}'+
  '.fnl .r .what{font:700 clamp(12px,.9vw,15px)/1.3 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#A9B2C6}.fnl .r .pct{margin-left:auto;font:400 clamp(1.2rem,2vw,2rem)/1 var(--disp);color:#FFB020}'+
  '.fnl .bar{height:clamp(14px,2.4vh,26px);border-radius:8px;margin-top:.8vh;min-width:6px}.fnl .r:nth-child(1) .bar{background:linear-gradient(90deg,#3A4152,#5A6479)}.fnl .r:nth-child(2) .bar{background:linear-gradient(90deg,#FFB020,#FF8A3D)}.fnl .r:nth-child(3) .bar{background:#B6FF3C}'+
  '.fnl .r:nth-child(3) .num{color:#B6FF3C}'+
  '.mini{display:flex;flex-wrap:wrap;gap:1.4vw;margin-top:3vh}.mini>div{flex:1 1 130px}.mini .v{font:400 clamp(1.4rem,2.4vw,2.4rem)/1 var(--disp);color:#fff}.mini .k{margin-top:.5vh;font:700 clamp(11px,.72vw,12px)/1.3 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#8893AA}'+
  /* audit */
  '.au{display:grid;grid-template-columns:1fr 1.15fr;gap:2.6vw;margin-top:3vh;align-items:start}'+
  '.au .dim{display:grid;grid-template-columns:clamp(110px,10vw,170px) 1fr 3ch;gap:.9vw;align-items:center;margin-bottom:1.7vh}.au .dim .l{font:700 clamp(11px,.85vw,14px)/1.2 var(--sans);letter-spacing:.1em;text-transform:uppercase;color:#C3CBDC}'+
  '.au .dim .tr{height:clamp(12px,2vh,20px);border-radius:8px;background:rgba(255,255,255,.08);overflow:hidden}.au .dim .tr i{display:block;height:100%;border-radius:8px}.au .dim .sc{font:400 clamp(1.1rem,1.8vw,1.8rem)/1 var(--disp);color:#fff;text-align:right}'+
  '.au .dim.na .tr{background:repeating-linear-gradient(45deg,rgba(255,255,255,.05),rgba(255,255,255,.05) 6px,transparent 6px,transparent 12px)}.au .dim.na .sc{color:#6C768C;font-size:clamp(.8rem,1vw,1rem)}'+
  '.au .scale{display:flex;flex-wrap:wrap;gap:1.2vw;margin-top:2.4vh}.au .scale>div{flex:1 1 90px}.au .scale .v{font:400 clamp(1.1rem,1.9vw,1.9rem)/1 var(--disp);color:#fff}.au .scale .k{font:700 clamp(11px,.7vw,12px)/1.3 var(--sans);letter-spacing:.12em;text-transform:uppercase;color:#8893AA;margin-top:.4vh}'+
  '.find{border:1px solid rgba(255,255,255,.14);border-left:4px solid #FF5A1F;border-radius:12px;padding:1.5vh 1.1vw;background:rgba(255,255,255,.04);margin-bottom:1.3vh}.find.hi{border-left-color:#FFB020}'+
  '.find .sv{font:700 clamp(11px,.7vw,12px)/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#FF8A3D}.find.hi .sv{color:#FFB020}.find .ti{font:600 clamp(13px,1.05vw,17px)/1.3 var(--sans);color:#fff;margin:.6vh 0}.find .ev{font:500 clamp(11.5px,.85vw,14px)/1.4 var(--sans);color:#A9B2C6}'+
  '.find .ev b{color:#fff}'+
  '@media (max-height:820px){.rem-card{margin-top:1.4vh}.rl .big{font-size:clamp(2.6rem,7vw,6.4rem)}.fnl{gap:1.4vh;margin-top:2.4vh}.mini{margin-top:2vh}.au{margin-top:2vh}.au .dim{margin-bottom:1.1vh}.find{padding:1vh .9vw;margin-bottom:.9vh}.bt{margin-top:2vh}.rl .src{margin-top:1.4vh}}'+
  '@media (max-width:1100px){.bt,.au{grid-template-columns:1fr}.rem-card{display:block}.rem-img{height:auto;width:100%}}';
 document.head.appendChild(st);

 /* 1. the MSP slide goes; the scoreboard chapter stops sounding like the whole talk */
 drop(S('02 Mirror|You’re not losing'));
 var ch=S('01 Scoreboard|Your websites');if(!ch)SL.forEach(function(s){if(s.getAttribute('data-sec')==='01 Scoreboard'&&s.querySelector('.chap'))ch=s});
 if(ch){var p=ch.querySelector('.sub');if(p)p.textContent='Start with what can be measured today.'}

 /* 2. the four repeated task lists go; the process maps, the bars and the full library stay */
 var removed=0;SL.slice().forEach(function(s){if((s.getAttribute('data-gen')||'').indexOf('list:')===0){drop(s);removed++}});
 SL.forEach(function(s){
  note(s,'Everything you just saw was the core tasks of four roles. This is the full library behind them:','You just saw the process for four roles. This is the full library behind them:');
  note(s,'Everything you just saw was four roles. Here is every task: 89 sales, 48 marketing.','You just saw the process for four roles. This is the full library behind them: 89 sales tasks, 48 marketing tasks.')});
 SL.forEach(function(s){if(/67 core tasks across four roles/.test(s.textContent))note(s,'This is QBS\'s own classification, not a survey','The four task lists for each role are in the take-home library. This is QBS\'s own classification, not a survey')});

 /* 3. the real Revenue Efficiency Model opens the session, so the website reads as one input and not the point */
 var first01=null;SL.forEach(function(s){if(!first01&&s.getAttribute('data-sec')==='01 Scoreboard')first01=s});
 if(first01){put(sec('model','The model',
  "THE FRAMEWORK, our real one. 'This is how every dealer makes revenue, ordered by effort. Keep what you have. Grow it with cross-sell and upsell. Multiply it through referrals. Convert the customers you already have. Only then expand into net-new business, the most expensive thing you do.' Then: 'Most dealers aim nearly all their effort at the top of this staircase, the new-business arrow. Your website mostly serves the first four steps, and AI works all five. We start with the website because it is the one thing I could measure for each of you before I flew here. Then the rest of the session works every step.' The next slides measure the website; the Revenue Efficiency slide later shows the AI play for each step.",
  '<div class="kick">The Revenue Efficiency Model</div>'+
  '<div class="rem-card"><div class="rem-img"><img alt="The Quantum Revenue Efficiency Model: 01 Keep, 02 Grow, 03 Multiply, 04 Convert, 05 Expand" src="https://20682069.fs1.hubspotusercontent-na1.net/hubfs/20682069/sales-blitz-playbook/rev-efficiency-model.png"></div></div>'+
  '<p class="src" style="margin-top:1.6vh;text-align:center">Five ways revenue walks in the door, ordered by effort. The website is one input. AI works all five.</p>'),first01)}
 var revm=null;SL.forEach(function(s){if(!revm&&s.getAttribute('data-sec')==='Revenue Efficiency')revm=s});
 if(revm){var rk=revm.querySelector('.kick');if(rk)rk.textContent='The Revenue Efficiency Model · the AI play for each step'}

 /* 4. five stories from Quantum's own work, in front of the twenty cards */
 var p1=document.getElementById('proof1');
 if(p1){
  put(sec('real-built','We run on it',
   "STORY ONE: we build our own software. 'I did not just learn this and sell it. I run my company on software we built with AI.' ClientCommand is the operating system: client portals, delivery plans, proposals, the SEO and AEO analysis you got, call analysis, HubSpot audits. Then the number: 'Over seven thousand dollars a month of software spend, gone. Not reduced. Gone.' Name two or three of the actual tools from the stage (fill in before October 8). Say the build facts as they are: counts come from the code today. Do not claim the savings for clients.",
   '<div class="kick">Proof · what we built</div><h2>Built, <span class="grad">not bought.</span></h2>'+
   '<div class="bt"><div class="stats">'+
    '<div class="wide"><div class="v"><em>$7,000+</em> a month</div><div class="k">Software spend eliminated at QBS · $84,000+ a year</div></div>'+
    '<div><div class="v">155</div><div class="k">Backend functions</div></div>'+
    '<div><div class="v">468</div><div class="k">Tools an AI can call</div></div>'+
    '<div><div class="v">590</div><div class="k">Database migrations</div></div>'+
    '<div><div class="v">67</div><div class="k">App screens</div></div>'+
   '</div><div class="apps">'+
    '<div><b>ClientCommand</b><span>Our operating system: client portals, delivery plans, proposals, SEO and AEO analysis, call analysis, HubSpot audits.</span></div>'+
    '<div><b>BrandCommand</b><span>Brand and social content in our voice.</span></div>'+
    '<div><b>QuoteCommand</b><span>Quotes.</span></div>'+
    '<div><b>DocCommand</b><span>Documents and agreements.</span></div>'+
    '<div><b>CommissionCommand</b><span>Commissions.</span></div>'+
   '</div></div><p class="src">Counts from the ClientCommand code as of 7 October 2026. Savings figure: QBS, monthly.</p>'),p1);

  put(sec('real-calls','We run on it',
   "STORY TWO: call analysis. 'We pointed Claude at every call a client's team had ever made in HubSpot.' Client is anonymous on purpose. The page it produced breaks calls down by source, hour of day, how many attempts it takes to reach someone, how long to the first conversation and the first meeting, and by rep. Land the scale: the bars are to scale, and the meetings bar is a sliver. 'About four hundred and eighty calls for every meeting. Nobody had ever added it up, and they had been dialing for more than four years.' Then: 'Which hour, which tool, which attempt: that is where you find out what to change.' Do not name the client. Get their OK before using the real name.",
   '<div class="kick">Proof · call analysis</div><h2>514,000 calls. <span class="grad">Nobody had added them up.</span></h2>'+
   '<div class="fnl">'+
    '<div class="r"><div class="lab"><span class="num">513,889</span><span class="what">Calls logged in HubSpot since May 2022</span></div><div class="bar" style="width:100%"></div></div>'+
    '<div class="r"><div class="lab"><span class="num">35,387</span><span class="what">Conversations</span><span class="pct">6.9%</span></div><div class="bar" style="width:6.886%"></div></div>'+
    '<div class="r"><div class="lab"><span class="num">1,068</span><span class="what">Meetings</span><span class="pct">1 per 481 calls</span></div><div class="bar" style="width:.208%"></div></div>'+
   '</div><div class="mini"><div><div class="v">22</div><div class="k">Reps</div></div><div><div class="v">47,732</div><div class="k">People dialed</div></div><div><div class="v">569 hrs</div><div class="k">Talk time</div></div></div>'+
   '<p class="src">A real client portal in ClientCommand, anonymized. Bars drawn to scale.</p>'),p1);

  put(sec('real-audit','We run on it',
   "STORY THREE: the HubSpot audit, run on our own portal first. 'Before we audit a client, we audit ourselves.' Real run, 29 September 2026: 153,000 contacts, 100,000 companies, 28,887 tickets. It scores six dimensions from live data. Be honest about the weak one: 'Our adoption score is 28. The audit found owner attribution was broken, so our own activity did not show up under real people. That is what it is for: it tells you the truth about your own house, with a list of what to do about it.' Then the finding on the right: fourteen thousand replies and nobody at sales qualified. Point out two dimensions say not assessed, because the tool refuses to guess what it cannot read. Confirm you are comfortable showing the 28 before October 8.",
   '<div class="kick">Proof · HubSpot audit</div><h2>We audit ourselves <span class="grad">first.</span></h2>'+
   '<div class="au"><div>'+
    '<div class="dim"><span class="l">Data health</span><span class="tr"><i style="width:93%;background:#B6FF3C"></i></span><span class="sc">93</span></div>'+
    '<div class="dim"><span class="l">Architecture</span><span class="tr"><i style="width:84%;background:#B6FF3C"></i></span><span class="sc">84</span></div>'+
    '<div class="dim"><span class="l">Automation</span><span class="tr"><i style="width:80%;background:#B6FF3C"></i></span><span class="sc">80</span></div>'+
    '<div class="dim"><span class="l">Adoption</span><span class="tr"><i style="width:28%;background:linear-gradient(90deg,#FF5A1F,#FFB020)"></i></span><span class="sc">28</span></div>'+
    '<div class="dim na"><span class="l">Integrations</span><span class="tr"></span><span class="sc">n/a</span></div>'+
    '<div class="dim na"><span class="l">Reporting</span><span class="tr"></span><span class="sc">n/a</span></div>'+
    '<div class="scale"><div><div class="v">153,483</div><div class="k">Contacts</div></div><div><div class="v">100,179</div><div class="k">Companies</div></div><div><div class="v">1,561</div><div class="k">Deals</div></div><div><div class="v">28,887</div><div class="k">Tickets</div></div></div>'+
   '</div><div>'+
    '<div class="find"><div class="sv">Finding · High</div><div class="ti">14,254 replies in 90 days, and zero sales qualified contacts</div><div class="ev">A reply is demand. <b>Nobody was assigned to act on it</b>, so the best inbound signal in the portal died in an inbox.</div></div>'+
    '<div class="find hi"><div class="sv">Finding · High</div><div class="ti">187 open deals carry no amount</div><div class="ev">About <b>$744,260</b> of pipeline missing from the forecast, if they look like the other open deals.</div></div>'+
    '<div class="find hi"><div class="sv">Finding · Medium</div><div class="ti">34 of 100 workflows are switched off</div><div class="ev">A third of the automation we built sits dormant, and nobody could see which.</div></div>'+
   '</div></div><p class="src">QBS portal audit, 29 September 2026. Integrations and reporting are not assessed: the audit says so instead of guessing.</p>'),p1);

  var flow=function(n,k,t,d,w){return '<div class="node k-'+k+'" style="--i:'+(n-1)+'"><div class="nt-top"><span class="nn">'+(n<10?'0'+n:n)+'</span><span class="bd">'+(k==='ai'?'AI does it':k==='assist'?'AI assists':'You')+'</span></div><div class="nt">'+t+'</div><div class="nd">'+d+'</div><div class="wh"><i>in</i>'+w+'</div></div>'};
  put(sec('real-enrich','We run on it',
   "STORY FOUR: one task, step by step, and how it got automated. 'This is how we keep a calling list honest. A rep used to look up each name on LinkedIn, retype the CRM, guess the email.' Walk left to right. Lime is AI, amber is AI helping, grey is a person. Point at step 07: 'When it cannot prove something, it does not guess. It queues it for a person. A founder who looks like they left, but is still in the chair, is exactly that case.' Real pass: 662 contacts in, 491 read against dated LinkedIn history. It runs daily, unattended, against our own HubSpot. And the rule that matters: a halted run is a success; a silent one is not. Same process, different task, is how the matrix on the take-home page works.",
   '<div class="kick">Proof · a task, automated</div><h2>Keeping a list <span class="grad">honest.</span></h2>'+
   '<div class="flow">'+
    flow(1,'ai','List pulled','Membership read from HubSpot itself, never a stale file','HubSpot')+
    flow(2,'ai','History read','Dated job history on LinkedIn, not the headline','LinkedIn')+
    flow(3,'ai','Verdict written','Still there, moved, or cannot tell, with the evidence stamped on the record','HubSpot')+
    flow(4,'ai','Mover followed','New employer found or created, associations swapped','HubSpot')+
    flow(5,'ai','Email repaired','Fourteen formats tried, each one verified before use','Email check')+
    flow(6,'ai','Phone fixed','Numbers that belong to the old employer cleared or corrected','HubSpot')+
    flow(7,'you','Judgment calls','Edge cases are queued for a person, never guessed','You')+
    flow(8,'ai','Calling list refreshed','A rep dials someone who still works there','HubSpot')+
   '</div><div class="legend"><span><b style="background:var(--lime)"></b>AI does it</span><span><b style="background:var(--amber)"></b>AI assists</span><span><b style="background:#3A4152"></b>Stays yours</span><span style="color:var(--cyan)">Cyan = where it happens</span></div>'+
   '<p class="src">One real pass: 662 contacts in, 491 read against dated LinkedIn history. Runs daily, unattended, and halts when it cannot prove something.</p>'),p1);
 }

 /* deck.js only tracks the slides it built itself, so on an inserted slide the counter, section label and presenter notes
    stay on the previous one. Track the inserted slides here, and give each its own key for My notes. */
 SL.forEach(function(s){if(!s.getAttribute('data-sk')){var h=s.querySelector('h1,h2,h3');s.setAttribute('data-sk',(s.getAttribute('data-sec')||'')+'|'+(s.id||(h?h.textContent.replace(/\s+/g,' ').trim():'slide')))}});
 /* once scrolling stops, sync the counter, section label and notes to the slide that is actually on screen */
 var settle=null;function sync(){var best=-1,bv=1e9;SL.forEach(function(s,k){var d=Math.abs(s.getBoundingClientRect().top);if(d<bv){bv=d;best=k}});
  if(best>-1&&bv<window.innerHeight*0.2&&DECK.state().idx!==best)DECK.go(best)}
 document.addEventListener('scroll',function(){clearTimeout(settle);settle=setTimeout(sync,220)},true);

 /* menu follows */
 var ml=document.getElementById('mlist');if(ml){var html='',last=null;SL.forEach(function(s,n){var sec=s.getAttribute('data-sec')||'';if(sec!==last){html+='<h4>'+sec+'</h4>';last=sec}
  var hh=s.querySelector('h1,h2,h3');var lab=hh?hh.textContent.replace(/\s+/g,' ').trim():(s.classList.contains('trailer')?'The video: The Old Way vs. The Quantum Way':'Slide '+(n+1));if(lab.length>72)lab=lab.slice(0,72)+'…';
  html+='<a href="#" data-n="'+n+'"><i>'+(n+1)+'</i><span>'+lab+'</span></a>'});ml.innerHTML=html}
 var s0=DECK.state();DECK.go(Math.min(s0.idx,SL.length-1));
})();
