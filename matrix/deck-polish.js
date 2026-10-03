/* ICDA 2026 deck: content polish (loaded last, from deck-fixes.js).
   The Triple A of AI, softer channel claim, charts on the text-only slides, one take-home code on the close. */
(function(){if(!window.DECK)return;
 var SL=DECK.slides,HUB='https://clientcommand.thequantumleap.business/s/9fe6890271ce7f36864d298528a4ce09/index.html';
 function S(p){for(var i=0;i<SL.length;i++)if((SL[i].getAttribute('data-sk')||'').indexOf(p)===0)return SL[i];return null}
 function note(s,a,b){if(s)s.setAttribute('data-notes',(s.getAttribute('data-notes')||'').split(a).join(b))}
 function qr(u){return 'https://api.qrserver.com/v1/create-qr-code/?size=440x440&margin=0&data='+encodeURIComponent(u)}

 var st=document.createElement('style');st.textContent=
  /* share bars under the branded-traffic numbers */
  '.brb{margin-top:1.8vh;height:12px;border-radius:7px;background:rgba(182,255,60,.85);overflow:hidden}.brb i{display:block;height:100%;background:linear-gradient(90deg,#FF5A1F,#FFB020)}'+
  '.brl{display:flex;justify-content:space-between;margin-top:.8vh;font:700 clamp(11px,.72vw,13px)/1.2 var(--sans);letter-spacing:.08em;text-transform:uppercase}.brl span:first-child{color:#FFB020}.brl span:last-child{color:#B6FF3C}'+
  /* the Triple A staircase on the chapter card */
  '.aaa{display:flex;align-items:flex-end;gap:1.2vw;margin-top:4.5vh;max-width:min(980px,82vw)}'+
  '.aaa>div{flex:1 1 0;min-width:0;display:flex;flex-direction:column;justify-content:flex-end;border-radius:16px 16px 6px 6px;padding:2.2vh 1.3vw;border:1px solid rgba(255,255,255,.14);background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(255,255,255,.02));position:relative}'+
  '.aaa>div:nth-child(1){min-height:17vh}.aaa>div:nth-child(2){min-height:24vh;border-color:rgba(255,176,32,.55)}.aaa>div:nth-child(3){min-height:31vh;border-color:rgba(182,255,60,.6)}'+
  '.aaa .l{font:400 clamp(2rem,4.2vw,4rem)/.9 var(--disp);background:var(--hot);-webkit-background-clip:text;background-clip:text;color:transparent}.aaa>div:nth-child(3) .l{background:none;color:#B6FF3C}'+
  '.aaa .t{font:400 clamp(1rem,1.7vw,1.6rem)/1 var(--disp);text-transform:uppercase;color:#fff;margin-top:1vh}.aaa .d{font:500 clamp(12px,.95vw,16px)/1.35 var(--sans);color:#A9B2C6;margin-top:.7vh}'+
  /* ninety-day track */
  '.tl{margin-top:3.6vh}.tl .bar{display:flex;height:12px;border-radius:7px;overflow:hidden}.tl .bar i{flex:1}.tl .bar i:nth-child(1){background:#FFB020}.tl .bar i:nth-child(2){background:#FF5A1F}.tl .bar i:nth-child(3){background:#B6FF3C}'+
  '.tl .mk{display:flex;justify-content:space-between;margin-top:1vh;font:700 clamp(11px,.8vw,14px)/1 var(--sans);letter-spacing:.14em;text-transform:uppercase;color:#A9B2C6}.tl .mk span:last-child{color:#B6FF3C}.tl+.days{margin-top:2.4vh}'+
  /* twenty ways as chips, service column lit */
  '.tw .cols ol{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:1vh}.tw .cols>div:nth-child(2) ol{counter-reset:n 6}.tw .cols>div:nth-child(3) ol{counter-reset:n 12}'+
  '.tw .cols li{display:flex;align-items:center;gap:.8vw;padding:1.1vh .9vw!important;margin-bottom:0!important;border-radius:12px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.04)}'+
  '.tw .cols li::before{content:counter(n,decimal-leading-zero)!important;position:static!important;flex:0 0 auto;font-weight:400!important;min-width:2em;text-align:center;font:400 clamp(1rem,1.4vw,1.4rem)/1 var(--disp);color:#FFB020}'+
  '.tw .cols>div:nth-child(2) li{border-color:rgba(182,255,60,.45);background:rgba(182,255,60,.07)}.tw .cols>div:nth-child(2) li::before,.tw .cols>div:nth-child(2) h4{color:#B6FF3C}'+
  '@media (max-height:820px){.aaa{margin-top:3vh}.aaa>div:nth-child(1){min-height:16vh}.aaa>div:nth-child(2){min-height:22vh}.aaa>div:nth-child(3){min-height:28vh}.tw .cols li{padding:.7vh .8vw}.tw .cols ol{gap:.7vh}}'+
  /* close: two equal codes */
  '.qrb .s2{font:500 clamp(11px,.8vw,13px)/1.3 var(--sans)!important;letter-spacing:0!important;text-transform:none!important;color:#A9B2C6;text-align:center;max-width:17vw}'+
  /* Bob sits bottom right on the close, so the contact line stays clear of him */
  '@media (max-width:1700px){.cl-meta{max-width:60vw;margin-left:auto!important;margin-right:auto!important;line-height:1.7}}';
 document.head.appendChild(st);

 /* 01: the measuring happened two weeks before the talk, not last week */
 var s10=S('01 Scoreboard|Last week I measured');if(s10){var h=s10.querySelector('h1');if(h)h.innerHTML='Before I flew here, I measured <span class="grad">all eleven</span> of your websites.'}

 /* 01: each branded-traffic figure gets its own bar */
 var s12=S('01 Scoreboard|You’re not being discovered');if(s12)[].forEach.call(s12.querySelectorAll('.tiles>div'),function(t){var v=parseInt(t.querySelector('.v').textContent,10);if(!v||t.querySelector('.brb'))return;
  t.insertAdjacentHTML('beforeend','<div class="brb" role="img" aria-label="'+v+' percent typed your name, '+(100-v)+' percent found you"><i style="width:'+v+'%"></i></div><div class="brl"><span>Typed your name</span><span>Found you · '+(100-v)+'%</span></div>')});

 /* 02: the slide has no left and right, so the note should not either */
 note(S('02 Mirror|You’re not losing'),'On the left of your mind is you:','Picture your own team:');

 /* 03: the Triple A of AI */
 SL.forEach(function(s){if(s.getAttribute('data-sec')==='03 Three rungs')s.setAttribute('data-sec','03 Triple A')});
 var s19=S('03 Three rungs|ThreeRungs');if(s19){var h2=s19.querySelector('h2');if(h2)h2.innerHTML='The Triple A<br>of AI';
  var w=s19.querySelector('.in-wrap');if(w&&!w.querySelector('.aaa'))w.insertAdjacentHTML('beforeend','<div class="aaa"><div><div class="l">A1</div><div class="t">Assistant</div><div class="d">You ask, it answers.</div></div><div><div class="l">A2</div><div class="t">Automation</div><div class="d">A trigger runs it. Nobody has to remember.</div></div><div><div class="l">A3</div><div class="t">Agent</div><div class="d">It decides what matters. You approve.</div></div></div>');
  s19.setAttribute('data-notes',"Chapter card. Name it and let it stick: 'The Triple A of AI. Assistant, Automation, Agent. Three rungs, and which one you stand on decides what AI is worth to you.' Every task in the take-home list is rated on these three.")}
 var s20=S('03 Three rungs|#19');if(s20){var k=s20.querySelector('.kick');if(k)k.textContent='Rung one: where the vast majority of this channel is standing'}

 /* 04: the full library is the Triple A list they take home */
 var s35=null;SL.forEach(function(s){if(/137 tasks/i.test(s.textContent))s35=s});
 if(s35){var w2=document.createTreeWalker(s35,NodeFilter.SHOW_TEXT,null),n;while((n=w2.nextNode()))if(n.nodeValue.indexOf('every task, every rung')>-1)n.nodeValue=n.nodeValue.replace('every task, every rung','every task, rated on the Triple A');
  note(s35,'The QR on the take-home slide gives them all of it.','The take-home code on the last slide gives them all of it, rated Assistant, Automation, Agent.')}

 /* 06: twenty ways as chips instead of a plain list */
 var s44=S('06 Twenty|#43');if(s44)s44.classList.add('tw');

 /* 90 days: a track above the three phases */
 var s50=S('90 days|');if(s50){var d=s50.querySelector('.days');if(d&&!s50.querySelector('.tl'))d.insertAdjacentHTML('beforebegin','<div class="tl" aria-hidden="true"><div class="bar"><i></i><i></i><i></i></div><div class="mk"><span>Day 1</span><span>Day 30</span><span>Day 60</span><span>Day 90 · prove it</span></div></div>')}

 /* close: the take-home slide folds into it, one code for everything */
 var take=S('Take it home|');if(take){var ti=SL.indexOf(take);if(ti>-1)SL.splice(ti,1);take.parentNode.removeChild(take)}
 var close=S('Close|');if(close){var sm=close.querySelector('.qrb.sm');if(sm){sm.classList.remove('sm');
   var mt=close.querySelector('.meta');if(mt)mt.classList.add('cl-meta');
   sm.innerHTML='<img alt="QR code: take it all home" src="'+qr(HUB)+'"><span>Take it all home</span><span class="s2">Your report, this playbook, the Triple A task list and the film</span>'}
  note(close,'The small code is the full film on YouTube, for anyone who wants to send it to their team.','The second code is take-it-all-home: their own report, this whole playbook, the full Triple A task list and the film to send their team. Leave this slide up through Q&A.')}
 SL.forEach(function(s){note(s,'its QR is on the close slide.','it is on the take-home page, the second code on the close slide.')});

 /* menu follows */
 var ml=document.getElementById('mlist');if(ml){var html='',last=null;SL.forEach(function(s,n){var sec=s.getAttribute('data-sec')||'';if(sec!==last){html+='<h4>'+sec+'</h4>';last=sec}
  var hh=s.querySelector('h1,h2,h3');var lab=hh?hh.textContent.replace(/\s+/g,' ').trim():(s.classList.contains('trailer')?'The video: The Old Way vs. The Quantum Way':'Slide '+(n+1));if(lab.length>72)lab=lab.slice(0,72)+'…';
  html+='<a href="#" data-n="'+n+'"><i>'+(n+1)+'</i><span>'+lab+'</span></a>'});ml.innerHTML=html}
 var s0=DECK.state();DECK.go(Math.min(s0.idx,SL.length-1));
})();
