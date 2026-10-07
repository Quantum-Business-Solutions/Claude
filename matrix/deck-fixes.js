/* ICDA 2026 deck: QA pass fixes (loaded last, from deck-proof.js).
   720p projector layout, readable minimum type, American spelling, no repeated heading in the honest part. */
(function(){if(!window.DECK)return;
 var all=DECK.slides;
 /* media that moved: Bob's cutout and the opener poster were re-uploaded on 7 Oct 2026 after the originals were deleted from the CDN;
    four mirrored background loops are gone for good, so those slides fall back to the gradient mesh instead of requesting dead files */
 [].forEach.call(document.querySelectorAll('img[src*="cf926fd6-d099-4cd9-86f8-d4e6ade270ac"]'),function(i){i.src='https://d3snorpfx4xhv8.cloudfront.net/e4d416f7-7355-4276-8c8e-26821a906ac8/6271dfc8-d3ca-4d3b-9255-505f935f82d3.webp'});
 var tvx=document.getElementById('tv');if(tvx)tvx.poster='https://d3snorpfx4xhv8.cloudfront.net/e4d416f7-7355-4276-8c8e-26821a906ac8/8bcbc7a0-57ae-45fa-a4f2-9c908f055629.jpeg';
 [].forEach.call(document.querySelectorAll('video.bgv'),function(v){var u=v.getAttribute('data-src')||v.getAttribute('src')||'';if(/d3u0tzju9qaucj\.cloudfront\.net/.test(u)&&v.parentNode)v.parentNode.removeChild(v)});
 /* tag the slides that need room on a short (720p) screen */
 all.forEach(function(s){if(s.querySelector('.plw'))s.classList.add('plsec');if(s.querySelector('.rem'))s.classList.add('remsec')});
 var st=document.createElement('style');st.textContent=
  /* plays: the four facts sit on one row instead of wrapping into the slide counter */
  '.plw .kv{max-width:none;flex-wrap:nowrap}.plw .kv>div{flex:1 1 0;min-width:0;padding-right:1.2vw}'+
  /* donut and matrix labels: nothing on a task slide smaller than 11px */
  '.donut span{font-size:clamp(11px,.75vw,13px)!important;letter-spacing:.14em!important}.mxh span{font-size:max(11px,.7vw)!important}.nt-top .bd{font-size:max(11px,.66vw)!important}.mock .bar span{font-size:max(11px,.7vw)!important}'+
  /* the name under each dealer logo is readable from the room */
  '.lg .lgn{font-size:clamp(10px,.72vw,12px)!important;color:#2B3140!important}'+
  /* Bob\'s bubble stays narrow on smaller screens so it never covers a caption */
  '@media (max-width:1500px){.bobcam.sm .bub{max-width:15vw;font-size:clamp(12px,1.1vw,17px)}}'+
  '@media (max-height:820px){'+
   '.plsec,.remsec,.px{padding-top:7.5vh!important;padding-bottom:10.5vh!important}'+
   '.plw .pll h3{font-size:clamp(1.6rem,2.9vw,2.6rem)!important;margin:1.2vh 0 0!important}'+
   '.plw .pll .pts{margin-top:1.6vh!important}.plw .pll .pts li{font-size:clamp(.9rem,1.45vw,1.15rem)!important;line-height:1.34!important;margin-bottom:1.1vh!important}'+
   '.plw .kv{margin-top:1.8vh!important;padding-top:1.5vh!important}.plw .kv dd{font-size:clamp(.82rem,1.2vw,1rem)!important}'+
   '.remsec .rem{margin-top:2vh!important;gap:.9vh!important}.remsec h2,.remsec h1{font-size:clamp(1.7rem,3.6vw,3rem)!important}'+
   '.px .pxg{margin-top:1.8vh!important}.px .pc{padding:1.3vh .85vw 1.2vh!important}'+
  '}';
 document.head.appendChild(st);

 /* American spelling throughout (slides and notes) */
 var SP=[['industrialises','industrializes'],['industrialise','industrialize'],['Personalised','Personalized'],['personalised','personalized'],['analysed','analyzed'],['judgement','judgment'],['anonymise','anonymize'],['optimisation','optimization'],['prioritise','prioritize']];
 function fixText(t){SP.forEach(function(p){if(t.indexOf(p[0])>-1)t=t.split(p[0]).join(p[1])});return t}
 all.forEach(function(s){var w=document.createTreeWalker(s,NodeFilter.SHOW_TEXT,null),n;while((n=w.nextNode())){var v=fixText(n.nodeValue);if(v!==n.nodeValue)n.nodeValue=v}
  var no=s.getAttribute('data-notes');if(no){var f=fixText(no);if(f!==no)s.setAttribute('data-notes',f)}});

 /* the honest part: slide 47 already says "Three ways dealers waste money", so the list slide gets its own heading */
 all.forEach(function(s){var h=s.querySelector('h2');if(h&&/^Three ways to waste the money\.?$/i.test(h.textContent.trim()))h.innerHTML='Where it <span class="grad">goes wrong.</span>'});

 /* menu labels follow any heading that changed */
 var ml=document.getElementById('mlist');if(ml){var html='',last=null;all.forEach(function(s,n){var sec=s.getAttribute('data-sec')||'';if(sec!==last){html+='<h4>'+sec+'</h4>';last=sec}
  var h=s.querySelector('h1,h2,h3');var lab=h?h.textContent.replace(/\s+/g,' ').trim():(s.classList.contains('trailer')?'The video: The Old Way vs. The Quantum Way':'Slide '+(n+1));if(lab.length>72)lab=lab.slice(0,72)+'…';
  html+='<a href="#" data-n="'+n+'"><i>'+(n+1)+'</i><span>'+lab+'</span></a>'});ml.innerHTML=html}
 var s0=DECK.state();DECK.go(s0.idx);
 /* content polish loads last */
 var px=document.createElement('script');px.src='deck-polish.js';document.body.appendChild(px);
 /* the booking QR sits on every content slide */
 var qx=document.createElement('script');qx.src='deck-qr.js';document.body.appendChild(qx);
})();
