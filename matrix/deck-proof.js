/* ICDA 2026 deck: "We run on it" -- twenty real ways Quantum uses AI, two slides after Twenty Ways.
   Edit the list below; nothing else in the deck needs republishing. Each item: [area, title, what happens, runs on, story prompt for the notes]. */
(function(){if(!window.DECK)return;
 var EX=[
  ['SEO / AEO','Search & AI answer readiness','Sixteen checks on every page, and real buyer questions asked to the AI assistants from the client&rsquo;s own city.','Client Command','The scoreboard you just saw was this.'],
  ['Research','Account research in one click','A one-page brief on any company before the first call: who they are, what changed, who signs.','Client Command &middot; Perplexity &middot; Firecrawl','The last call you walked into cold.'],
  ['Call analysis','Every call, mined','Transcripts become client questions, commitments and buying signals, logged against the account.','Zoom &middot; Client Command','The promise someone made on a call and nobody wrote down.'],
  ['Meeting prep','Briefed before every meeting','Carry-forward agenda, open commitments and attention items, ready before the meeting starts.','Client Command','Walking into a QBR already knowing the three open items.'],
  ['Plans &amp; SOWs','Scope to signed SOW','A statement of work and delivery plan drafted from the discovery notes, in our format.','Claude &middot; Client Command','How long an SOW used to take versus now.'],
  ['Proposals','Proposals that build themselves','Branded web proposals assembled from the scope, then sent for signature.','Client Command','A proposal out the same afternoon as the meeting.'],
  ['Client success','Churn signals before the churn','Health checks across delivery, scope drift and sentiment flag the account that is going quiet.','Client Command','The client we saved because the system noticed first.'],
  ['Client reviews','Value reviews, written for us','The quarterly review drafted from the work actually delivered, not from memory.','Client Command &middot; HubSpot','A review the client forwarded to their boss.'],
  ['Delivery QA','Tickets checked against reality','Open tickets compared with what is actually built in the client&rsquo;s HubSpot; done work gets flagged to close.','Claude &middot; HubSpot','Hours banked that would have sat open for months.'],
  ['Portal audits','HubSpot audit in an afternoon','Data health, architecture, adoption, automation and reporting scored from live data.','Claude &middot; HubSpot','The new client whose portal told us the real problem.'],
  ['Social media','Posts and carousels in our voice','LinkedIn posts and carousels drafted on brand, queued for approval.','BrandCommand','The post that came from a five-minute voice note.'],
  ['Outreach','LinkedIn outreach that checks first','Every contact&rsquo;s current employer verified before a message goes out, and every send logged to HubSpot.','Unipile &middot; HubSpot','Not pitching someone who left the company a year ago.'],
  ['Data enrichment','Enrichment as a standard','The same 81 ZoomInfo fields deployed into every client portal, so data lands in the same place every time.','ZoomInfo &middot; HubSpot','The setup that used to take a day.'],
  ['List hygiene','Calling lists verified','Lists checked against LinkedIn so reps stop dialing people at their old company.','Client Command &middot; LinkedIn','The rep who used to burn an hour on dead numbers.'],
  ['Software','We build our own software with AI','Client Command, our operating system, built and shipped with Claude Code, change by change.','Claude Code &middot; GitHub','This week: a YouTube publisher, built and live in an afternoon.'],
  ['Video','This film','The cast, the shots and the edit, made with AI and checked by AI for lip sync and timing.','Higgsfield &middot; Claude','Bob does not exist. You still recognized him.'],
  ['Publishing','One sentence to YouTube','&ldquo;Upload this to YouTube&rdquo; publishes the video with title, tags and thumbnail.','Client Command &middot; YouTube','Our Academy course went up as a series in one go.'],
  ['Content','Blogs and email in house style','Blog posts and nurture email campaigns drafted in our format and pushed into HubSpot as drafts.','Claude &middot; HubSpot','A month of content from one conversation.'],
  ['Websites','Website directions, not mockups','Three complete website directions for a client, built as real pages they can click through.','Client Command','The dealer who picked a direction in the first meeting.'],
  ['Operations','The business runs its own meetings','Inbox triage, L10 recaps, KPI scorecards and a shared team memory that remembers what we decided.','Client Command &middot; Hindsight','What Monday looks like now.']];
 var st=document.createElement('style');st.textContent=
  '.px .pxg{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:1vw;margin-top:2.6vh;text-align:left}'+
  '.px .pc{position:relative;border:1px solid rgba(255,255,255,.12);border-radius:16px;background:linear-gradient(160deg,rgba(255,255,255,.06),rgba(255,255,255,.015));padding:1.7vh .95vw 1.5vh;opacity:0;transform:translateY(16px);transition:opacity .5s,transform .5s}'+
  '.s.in.px .pc{opacity:1;transform:none}'+
  '.px .pc .n{position:absolute;right:.8vw;top:1.3vh;font:400 clamp(18px,1.6vw,28px)/1 var(--disp);color:rgba(255,255,255,.14)}'+
  '.px .pc .a{font:700 clamp(9px,.7vw,11px)/1 var(--sans);letter-spacing:.16em;text-transform:uppercase;color:#B6FF3C}'+
  '.px .pc .t{font:400 clamp(16px,1.45vw,25px)/1.02 var(--disp);text-transform:uppercase;color:#fff;margin:.9vh 0 .7vh;padding-right:1.6vw}'+
  '.px .pc .d{font:500 clamp(11px,.86vw,14px)/1.4 var(--sans);color:#A9B2C6}'+
  '.px .pc .r{margin-top:1vh;font:600 clamp(9px,.68vw,11px)/1.3 var(--sans);letter-spacing:.06em;color:#4DE8FF}'+
  '.px h2 .grad{white-space:nowrap}'+
  '@media (max-width:900px){.px .pxg{grid-template-columns:1fr 1fr}}';
 document.head.appendChild(st);
 var after=[].filter.call(document.querySelectorAll('section.s'),function(s){return (s.getAttribute('data-sec')||'')==='06 Twenty'&&/Trigger-event monitoring/.test(s.textContent)})[0];
 if(!after||document.getElementById('proof1'))return;
 function card(e,i){return '<div class="pc" style="transition-delay:'+(0.15+0.05*(i%10))+'s"><div class="n">'+String(i+1).padStart(2,'0')+'</div><div class="a">'+e[0]+'</div><div class="t">'+e[1]+'</div><div class="d">'+e[2]+'</div><div class="r">Runs on: '+e[3]+'</div></div>'}
 function notes(lo,hi){var t='TELL STORIES, NOT FEATURES. Pick two or three from this slide and tell the real story behind each; do not read the cards. Story prompts: ';for(var i=lo;i<hi;i++)t+=(i+1)+' '+EX[i][1].replace(/&[a-z]+;/g,"'")+': '+EX[i][4]+' ';return t+' Every card is something Quantum runs today; check each one before October 8 and change the list in deck-proof.js if anything is not live.'}
 var s1=document.createElement('section');s1.className='s px';s1.id='proof1';s1.setAttribute('data-sec','We run on it');
 s1.setAttribute('data-notes',"'Everything I have shown you, we run on ourselves. Twenty real examples, from my own company.' "+notes(0,10));
 s1.innerHTML='<div class="mesh"></div><div class="in-wrap"><div class="kick">Proof &middot; how Quantum runs today</div><h2>We don&rsquo;t just sell it. <span class="grad">We run on it.</span></h2><div class="pxg">'+EX.slice(0,10).map(function(e,i){return card(e,i)}).join('')+'</div></div>';
 var s2=document.createElement('section');s2.className='s px';s2.id='proof2';s2.setAttribute('data-sec','We run on it');
 s2.setAttribute('data-notes',"'And ten more.' "+notes(10,20)+" End on the film: 'Even the guy in the cardigan was made this way.'");
 s2.innerHTML='<div class="mesh"></div><div class="in-wrap"><div class="kick">Proof &middot; examples 11&ndash;20</div><h2>Twenty real examples. <span class="grad">Ten more.</span></h2><div class="pxg">'+EX.slice(10,20).map(function(e,i){return card(e,i+10)}).join('')+'</div></div>';
 after.parentNode.insertBefore(s2,after.nextSibling);after.parentNode.insertBefore(s1,s2);
 var SL=DECK.slides,ai=SL.indexOf(after);if(ai>-1){SL.splice(ai+1,0,s1,s2)}
 if('IntersectionObserver' in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)e.target.classList.add('in')})},{threshold:[0.25]});io.observe(s1);io.observe(s2)}else{s1.classList.add('in');s2.classList.add('in')}
 var ml=document.getElementById('mlist');if(ml){var html='',last=null;SL.forEach(function(s,n){var sec=s.getAttribute('data-sec')||'';if(sec!==last){html+='<h4>'+sec+'</h4>';last=sec}
  var h=s.querySelector('h1,h2,h3');var lab=h?h.textContent.replace(/\s+/g,' ').trim():(s.classList.contains('trailer')?'The video: The Old Way vs. The Quantum Way':'Slide '+(n+1));if(lab.length>72)lab=lab.slice(0,72)+'…';
  html+='<a href="#" data-n="'+n+'"><i>'+(n+1)+'</i><span>'+lab+'</span></a>'});ml.innerHTML=html}
 var s0=DECK.state();DECK.go(s0.idx);
})();
