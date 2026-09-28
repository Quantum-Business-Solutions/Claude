/* ICDA 2026 deck: later additions. deck.js exposes window.DECK = {tv, go, slides, setCC, startTrailer, state()}. */
(function(){if(!window.DECK)return;var tv=DECK.tv,b=document.body;
 /* While the ad plays, hide the deck's bottom bar so it does not sit on top of the video's scrub bar. It comes back on pause, or when the mouse reaches the very bottom edge. */
 var st=document.createElement('style');st.textContent='body.vplay #hud{opacity:0;pointer-events:none;transition:opacity .3s}body.vplay.hudpeek #hud{opacity:1;pointer-events:auto}#hud{transition:opacity .3s}';document.head.appendChild(st);
 function sync(){var s=DECK.state();b.classList.toggle('vplay',!!(s.started&&!tv.paused&&DECK.slides[s.idx]&&DECK.slides[s.idx].classList.contains('trailer')))}
 ['play','playing','pause','ended','seeked'].forEach(function(ev){tv.addEventListener(ev,sync)});setInterval(sync,700);
 document.addEventListener('mousemove',function(e){b.classList.toggle('hudpeek',e.clientY>innerHeight-8)});
 /* runtime label on the play overlay, and the presenter note */
 var RUN='1:33';var sp=document.querySelector('.pmeta span');if(sp)sp.innerHTML=RUN+' &middot; sound on &middot; press space';
 var tr=document.querySelector('.s.trailer');if(tr)tr.setAttribute('data-notes',"LIGHTS DOWN, SOUND UP. The silent preview loops while people sit down. Press space (or click) to play the 93-second opener: meet Bob. Do not talk over it. When it ends it goes back to the preview; advance. The full 6:55 film is on YouTube (https://youtu.be/GxU0919SdTA); its QR is on the close slide.");
})();
/* v9 (runs after deck.js via deck-extra.js, so neither index.html nor deck.js is republished): Bob comes back through the talk, "What Bob costs you" calculator slide, and a close that asks for the meeting. */
(function(){
 var BOB='https://d3snorpfx4xhv8.cloudfront.net/e4d416f7-7355-4276-8c8e-26821a906ac8/cf926fd6-d099-4cd9-86f8-d4e6ade270ac.webp';
 var BOOK='https://meetings.hubspot.com/shawn-peterson?utm_source=icda2026&utm_medium=keynote&utm_campaign=bob-audit';
 var FILM='https://youtu.be/GxU0919SdTA';
 var COST='https://clientcommand.thequantumleap.business/s/85afc04ff3f5e8720a00601c998ef62d/cost.html';
 var QR=function(u){return 'https://api.qrserver.com/v1/create-qr-code/?size=440x440&margin=0&data='+encodeURIComponent(u)};
 var st=document.createElement('style');st.textContent=
  '.bobcam{position:absolute;right:3.5vw;bottom:0;width:min(21vw,300px);z-index:4;pointer-events:none;transform:translateY(105%);transition:transform .9s cubic-bezier(.2,.9,.25,1.15) .7s}'+
  '.s.in .bobcam{transform:translateY(0)}'+
  '.bobcam img{display:block;width:100%;filter:drop-shadow(0 18px 40px rgba(0,0,0,.55))}'+
  '.bobcam .bub{position:absolute;right:62%;top:-4%;width:max-content;max-width:min(24vw,340px);background:#FFB43C;color:#06070C;font:700 clamp(14px,1.35vw,21px)/1.25 var(--sans);padding:.7em .95em;border-radius:18px 18px 4px 18px;box-shadow:0 10px 30px rgba(0,0,0,.4);opacity:0;transform:scale(.85);transform-origin:100% 100%;transition:opacity .4s 1.5s,transform .4s 1.5s}'+
  '.s.in .bobcam .bub{opacity:1;transform:scale(1)}'+
  '.bobcam.sm{width:min(13.5vw,210px)}.bobcam.sm .bub{top:16%;max-width:min(22vw,330px)}'+
  '.bobcam.left{right:auto;left:3.5vw}.bobcam.left .bub{right:auto;left:62%;border-radius:18px 18px 18px 4px;transform-origin:0 100%}'+
  '.bill{display:grid;grid-template-columns:1.05fr 1fr;gap:3vw;align-items:center;margin-top:2.2vh}'+
  '.bill .ins{display:flex;flex-direction:column;gap:1.4vh}'+
  '.bill .in1{display:grid;grid-template-columns:1fr auto;align-items:center;gap:1vw;border:1px solid var(--line);border-radius:14px;padding:1.1vh 1.2vw;background:rgba(255,255,255,.03)}'+
  '.bill .in1 label{font:500 clamp(14px,1.3vw,20px)/1.3 var(--sans);color:var(--dim)}'+
  '.bill .ctl{display:flex;align-items:center;gap:.7vw}'+
  '.bill .ctl button{width:clamp(34px,2.6vw,46px);height:clamp(34px,2.6vw,46px);border-radius:50%;border:1px solid var(--line);background:transparent;color:#fff;font:700 clamp(18px,1.6vw,26px)/1 var(--sans);cursor:pointer}'+
  '.bill .ctl button:hover{border-color:#B6FF3C;color:#B6FF3C}'+
  '.bill .ctl b{min-width:4.2em;text-align:center;font:400 clamp(26px,2.6vw,44px)/1 var(--disp);letter-spacing:.02em}'+
  '.bill .out{text-align:left}'+
  '.bill .out .v{font:400 clamp(56px,7.6vw,132px)/.95 var(--disp);background:linear-gradient(100deg,#FFC94B,#FF6B4A);-webkit-background-clip:text;background-clip:text;color:transparent}'+
  '.bill .out .k{font:500 clamp(15px,1.4vw,22px)/1.4 var(--sans);color:var(--dim);margin-top:1vh;max-width:30em}'+
  '.bill .out .k b{color:#fff}'+
  '.bill .foot{font:500 clamp(12px,1vw,15px)/1.4 var(--sans);color:var(--dim);margin-top:1.6vh;display:flex;gap:1.2vw;align-items:center}'+
  '.bill .foot img{width:clamp(70px,6.5vw,110px);height:auto;border-radius:8px;background:#fff;padding:6px}'+
  '.ask3{display:grid;grid-template-columns:repeat(3,1fr);gap:1.4vw;margin:2.6vh 0 2.4vh}'+
  '.ask3>div{border:1px solid var(--line);border-radius:14px;padding:1.4vh 1.2vw;background:rgba(6,7,12,.55);backdrop-filter:blur(6px)}'+
  '.ask3 .n{font:700 clamp(11px,.9vw,14px)/1 var(--sans);letter-spacing:.18em;text-transform:uppercase;color:#B6FF3C}'+
  '.ask3 .t{font:400 clamp(22px,2.2vw,38px)/1.05 var(--disp);margin-top:.6vh}'+
  '.ask3 .d{font:500 clamp(13px,1.05vw,17px)/1.35 var(--sans);color:var(--dim);margin-top:.5vh}'+
  '.bookrow{display:flex;gap:2vw;align-items:center;justify-content:center;flex-wrap:wrap}'+
  '.bookrow .qrb{display:flex;flex-direction:column;align-items:center;gap:.8vh}'+
  '.bookrow .qrb img{width:clamp(120px,11vw,190px);height:auto;background:#fff;padding:8px;border-radius:12px}'+
  '.bookrow .qrb.sm img{width:clamp(80px,7vw,120px)}'+
  '.bookrow .qrb span{font:700 clamp(12px,1vw,16px)/1.2 var(--sans);letter-spacing:.06em;text-transform:uppercase}'+
  '.bookrow .cta{max-width:34em;text-align:left}'+
  '.bookrow .cta .h{font:400 clamp(26px,2.8vw,48px)/1 var(--disp)}'+
  '.bookrow .cta .d{font:500 clamp(14px,1.2vw,19px)/1.4 var(--sans);color:#dfe3ee;margin-top:.8vh}'+
  '.bookrow .cta .d b{color:#FFB43C}'+
  '@media (max-width:900px){.bill{grid-template-columns:1fr}.ask3{grid-template-columns:1fr}.bobcam{width:34vw}.bobcam .bub{max-width:52vw}}';
 document.head.appendChild(st);

 function secBy(test){var all=document.querySelectorAll('section.s');for(var i=0;i<all.length;i++){if(test(all[i]))return all[i]}return null}
 function txt(s){return (s.textContent||'').replace(/\s+/g,' ')}
 function cameo(sec,line,cls){if(!sec||sec.querySelector('.bobcam'))return;var d=document.createElement('div');d.className='bobcam'+(cls?' '+cls:'');
  d.innerHTML='<div class="bub">'+line+'</div><img src="'+BOB+'" alt="Bog Down Bob">';sec.appendChild(d)}
 function note(sec,add){if(sec)sec.setAttribute('data-notes',(sec.getAttribute('data-notes')||'')+' '+add)}

 /* 6 — Bob callbacks */
 var looked=secBy(function(s){return /being looked up/i.test(txt(s))});
 cameo(looked,'A website nobody finds? Love it. That&rsquo;s my work.','sm');
 note(looked,'BOB CAMEO: let him land, then: &lsquo;Remember Bob? He built your website strategy.&rsquo;');
 var rung1=secBy(function(s){return /Rung one/i.test(txt(s))&&s.querySelector('.rungs')});
 cameo(rung1,'Rung one? Stay right here. It&rsquo;s cozy.');
 note(rung1,'BOB CAMEO: &lsquo;Bob loves rung one. You are still the trigger, which means you are still doing the work.&rsquo;');
 var honest=secBy(function(s){return /buy the platform before naming the workflow/i.test(txt(s))});
 cameo(honest,'Honestly? All three are my idea.');
 note(honest,'BOB CAMEO: &lsquo;Every one of these is Bob in a nicer suit.&rsquo;');

 /* 9 — What Bob costs you (inserted right before the 90-day plan) */
 var days=secBy(function(s){return (s.getAttribute('data-sec')||'')==='90 days'});
 if(days&&!document.getElementById('bobbill')){
  var c=document.createElement('section');c.className='s';c.id='bobbill';c.setAttribute('data-sec','What Bob costs');
  c.setAttribute('data-notes',"THE NUMBER THAT GETS A BUDGET APPROVED. Do not claim the default inputs are industry data; they are an example. Ask the room: &lsquo;How many reps? How many hours a week do they spend on the stuff you just watched Rick do?&rsquo; Click + and &minus; to their answers live. Then: &lsquo;That is what Bob costs you a year. Before one missed renewal.&rsquo; The QR is the same calculator on their phone. Then advance to the 90-day plan: here is how you get it back.");
  c.innerHTML='<div class="mesh"></div><div class="in-wrap"><div class="kick">The bill nobody sends you</div><h2>What <span class="grad">Bob</span> costs you.</h2>'+
   '<div class="bill"><div class="ins">'+
    '<div class="in1"><label>Salespeople</label><div class="ctl"><button data-k="reps" data-d="-1" aria-label="Fewer salespeople">&minus;</button><b id="bb-reps"></b><button data-k="reps" data-d="1" aria-label="More salespeople">+</button></div></div>'+
    '<div class="in1"><label>Hours a week each on busywork<br><small>data entry, chasing, retyping, follow-ups</small></label><div class="ctl"><button data-k="hrs" data-d="-1" aria-label="Fewer hours">&minus;</button><b id="bb-hrs"></b><button data-k="hrs" data-d="1" aria-label="More hours">+</button></div></div>'+
    '<div class="in1"><label>Loaded cost per hour</label><div class="ctl"><button data-k="rate" data-d="-5" aria-label="Lower cost">&minus;</button><b id="bb-rate"></b><button data-k="rate" data-d="5" aria-label="Higher cost">+</button></div></div>'+
   '</div><div class="out"><div class="v" id="bb-total"></div><div class="k" id="bb-sub"></div>'+
   '<div class="foot"><img alt="QR code: run your own numbers" src="'+QR(COST)+'"><span>Example inputs &mdash; change them to yours.<br>Scan to run your own numbers.</span></div></div></div></div>';
  days.parentNode.insertBefore(c,days);
  var SL=window.DECK&&DECK.slides;if(SL){var di=SL.indexOf(days);if(di>-1)SL.splice(di,0,c)}
  if('IntersectionObserver' in window){new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)e.target.classList.add('in')})},{threshold:[0.25]}).observe(c)}else{c.classList.add('in')}
  cameo(c,'I don&rsquo;t send an invoice. I don&rsquo;t have to.','sm left');
  var V={reps:8,hrs:10,rate:55},LIM={reps:[1,200],hrs:[1,40],rate:[20,200]};
  var money=function(n){return '$'+Math.round(n).toLocaleString('en-US')};
  window.BOBBILL=function(){return V.reps*V.hrs*V.rate*48};
  var draw=function(){document.getElementById('bb-reps').textContent=V.reps;document.getElementById('bb-hrs').textContent=V.hrs;document.getElementById('bb-rate').textContent='$'+V.rate;
   var y=window.BOBBILL(),wk=Math.round(V.reps*V.hrs*48/40);
   document.getElementById('bb-total').textContent=money(y)+'/yr';
   document.getElementById('bb-sub').innerHTML='That is <b>'+wk.toLocaleString('en-US')+' forty-hour weeks</b> a year of your team&rsquo;s time going to Bob &mdash; before a single missed renewal or a deal that went cold.';
   var cb=document.getElementById('ask-bill');if(cb)cb.textContent=money(y)+' a year'};
  c.addEventListener('click',function(e){var b=e.target.closest('button[data-k]');if(!b)return;e.stopPropagation();var k=b.getAttribute('data-k');
   V[k]=Math.max(LIM[k][0],Math.min(LIM[k][1],V[k]+parseInt(b.getAttribute('data-d'),10)));draw()});
  setTimeout(draw,0);
 }

 /* 10 — the close asks for the meeting */
 var close=secBy(function(s){return (s.getAttribute('data-sec')||'')==='Close'});
 if(close&&!close.querySelector('.ask3')){
  var w=close.querySelector('.in-wrap');
  w.innerHTML='<div class="kick">One ask</div><h2>Leave Bob <span class="grad">behind.</span></h2>'+
   '<div class="ask3"><div><div class="n">Where you are</div><div class="t">Your score</div><div class="d">On your report, waiting for you. Built before I got on the plane.</div></div>'+
   '<div><div class="n">How you work</div><div class="t">Your rung</div><div class="d">You shouted it. Most of this room is on rung one.</div></div>'+
   '<div><div class="n">What it costs</div><div class="t" id="ask-bill">&nbsp;</div><div class="d">What Bob takes from a team like yours, every year.</div></div></div>'+
   '<div class="bookrow"><div class="qrb"><img alt="QR code: book your Bob Audit" src="'+QR(BOOK)+'"><span>Book it now</span></div>'+
   '<div class="cta"><div class="h">A free 30-minute Bob Audit.</div><div class="d">We pick the one workflow Bob is costing you the most, and map how to take it back. <b>Book this week: the first three dealers get theirs done before October 31.</b></div></div>'+
   '<div class="qrb sm"><img alt="QR code: watch the full film" src="'+QR(FILM)+'"><span>The full film</span></div></div>'+
   '<div class="meta"><b>Shawn Peterson</b> &middot; Quantum Business Solutions &middot; 712-389-4639 &middot; meetings.hubspot.com/shawn-peterson</div>';
  cameo(close,'Wait. Don&rsquo;t go. We had something.','sm');
  close.setAttribute('data-notes',"THE CLOSE. Point at the three boxes: &lsquo;Your score is on your report. Your rung, you told me. And that number is what Bob costs a team like yours every year.&rsquo; Then the ask, plainly: &lsquo;Scan the big code. Thirty minutes, free, this week. We pick the one workflow Bob is costing you the most and map how you take it back. First three of you get it done before the end of October.&rsquo; Pause. Bob says his line. Then keep it light: &lsquo;And either way: pick one thing before you fly home.&rsquo; The small code is the full film on YouTube, for anyone who wants to send it to their team.");
  var ab=document.getElementById('ask-bill');if(ab&&window.BOBBILL)ab.textContent='$'+Math.round(window.BOBBILL()).toLocaleString('en-US')+' a year';
 }
 /* the Sections menu was built before the new slide existed: rebuild it from the live slide list */
 var ml=document.getElementById('mlist');if(ml&&window.DECK){var html='',last=null;DECK.slides.forEach(function(s,n){var sec=s.getAttribute('data-sec')||'';if(sec!==last){html+='<h4>'+sec+'</h4>';last=sec}
  var h=s.querySelector('h1,h2,h3');var lab=h?h.textContent.replace(/\s+/g,' ').trim():(s.classList.contains('trailer')?'The video: The Old Way vs. The Quantum Way':'Slide '+(n+1));if(lab.length>72)lab=lab.slice(0,72)+'…';
  html+='<a href="#" data-n="'+n+'"><i>'+(n+1)+'</i><span>'+lab+'</span></a>'});ml.innerHTML=html}
 if(window.DECK){var s0=DECK.state();DECK.go(s0.idx)}
})();
