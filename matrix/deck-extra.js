/* ICDA 2026 deck: later additions. deck.js exposes window.DECK = {tv, go, slides, setCC, startTrailer, state()}. */
(function(){if(!window.DECK)return;var tv=DECK.tv,b=document.body;
 /* While the ad plays, hide the deck's bottom bar so it does not sit on top of the video's scrub bar. It comes back on pause, or when the mouse reaches the very bottom edge. */
 var st=document.createElement('style');st.textContent='body.vplay #hud{opacity:0;pointer-events:none;transition:opacity .3s}body.vplay.hudpeek #hud{opacity:1;pointer-events:auto}#hud{transition:opacity .3s}';document.head.appendChild(st);
 function sync(){var s=DECK.state();b.classList.toggle('vplay',!!(s.started&&!tv.paused&&DECK.slides[s.idx]&&DECK.slides[s.idx].classList.contains('trailer')))}
 ['play','playing','pause','ended','seeked'].forEach(function(ev){tv.addEventListener(ev,sync)});setInterval(sync,700);
 document.addEventListener('mousemove',function(e){b.classList.toggle('hudpeek',e.clientY>innerHeight-8)});
 /* runtime label on the play overlay, and the presenter note */
 var RUN='7:19';var sp=document.querySelector('.pmeta span');if(sp)sp.innerHTML=RUN+' &middot; sound on &middot; press space';
 var tr=document.querySelector('.s.trailer');if(tr)tr.setAttribute('data-notes',(tr.getAttribute('data-notes')||'').replace(/\d:\d\d ad/,RUN+' ad'));
})();
