/* ICDA 2026 deck: phone remote. The REMOTE button (presenter view) shows a QR code; scan it with your phone to get Next, Back,
   a jump list and your speaker notes. Commands travel over a Supabase Realtime broadcast channel named after a private code. Nothing is stored. */
(function(){
 if(!window.DECK||!/[?&]presenter/.test(location.search))return;
 var SB='https://ladhdgwedwynmdmeeena.supabase.co',KEY='sb_publishable_YP3m7RX-lI7ycGk-36G-QQ_QoifyVHE',LS='icda26-remote-code';
 var base=location.href.replace(/[?#].*$/,'').replace(/[^\/]*$/,'')+'remote.html';
 function code(){var c='';try{c=localStorage.getItem(LS)||''}catch(e){}if(!c){c=Array.apply(0,Array(6)).map(function(){return 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'.charAt(Math.floor(Math.random()*32))}).join('');try{localStorage.setItem(LS,c)}catch(e){}}return c}
 var st=document.createElement('style');st.textContent='#brem{display:none}body.pres #brem{display:inline-block}#rem-pop{position:fixed;inset:0;z-index:99;background:rgba(7,9,15,.92);display:none;align-items:center;justify-content:center}#rem-pop.on{display:flex}#rem-card{background:#151826;border:1px solid rgba(255,255,255,.18);border-radius:20px;padding:26px 30px;max-width:min(92vw,460px);text-align:center;color:#E4E9F5;font:500 15px/1.45 var(--sans)}#rem-card h3{margin:0 0 6px;font:400 1.9rem/1 var(--disp);text-transform:uppercase}#rem-q{background:#fff;border-radius:12px;padding:12px;display:inline-block;margin:14px 0 8px}#rem-q svg{display:block;width:min(56vw,230px);height:auto}#rem-card a{color:#B6FF3C;word-break:break-all;font-size:12.5px}#rem-card button{margin-top:14px;font:700 12px var(--sans);letter-spacing:.1em;text-transform:uppercase;color:#0B0D15;background:#B6FF3C;border:0;border-radius:8px;padding:10px 16px;cursor:pointer}#rem-s{margin-top:8px;font-size:13px;color:#8893AA}';document.head.appendChild(st);
 var pop=document.createElement('div');pop.id='rem-pop';pop.innerHTML='<div id="rem-card"><h3>Phone remote</h3><div>Scan with your phone. Next, back, jump and your notes.</div><div id="rem-q"></div><div><a id="rem-a" target="_blank" rel="noopener"></a></div><div id="rem-s">Not connected yet</div><button id="rem-x">Done</button></div>';document.body.appendChild(pop);
 var ch=null,sbc=null,C=code(),connected=false,lastSent='';
 function libs(cb){var n=0,need=2;function d(){if(++n===need)cb()}
  function ld(src,ok){if(ok()){d();return}var s=document.createElement('script');s.src=src;s.onload=d;s.onerror=function(){d()};document.head.appendChild(s)}
  ld('https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js',function(){return !!window.supabase});
  ld('https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js',function(){return !!window.qrcode})}
 function state(){var i=DECK.state().idx,S=DECK.slides,s=S[i];if(!s)return null;var h=function(el){var x=el&&el.querySelector('h1,h2,h3');return x?x.textContent:(el&&el.classList.contains('trailer')?'The video':(el?el.textContent:''))};var cl=function(t){return (t||'').replace(/\s+/g,' ').trim().slice(0,70)};
  return {idx:i,total:S.length,chap:s.getAttribute('data-chap')||'',title:cl(h(s)),next:S[i+1]?cl(h(S[i+1])):'',notes:(s.getAttribute('data-notes')||'').slice(0,2500),toc:S.map(function(x,n){return {i:n,t:cl(h(x))}})}}
 function push(){if(!ch||!connected)return;var s=state();if(!s)return;ch.send({type:'broadcast',event:'state',payload:s})}
 function connect(){if(ch)return;libs(function(){if(!window.supabase){document.getElementById('rem-s').textContent='Could not load the remote service. Check the internet.';return}
  sbc=window.supabase.createClient(SB,KEY);ch=sbc.channel('icda26-'+C,{config:{broadcast:{self:false}}});
  ch.on('broadcast',{event:'cmd'},function(m){var p=m.payload||{},i=DECK.state().idx,n=DECK.slides.length;
   if(p.a==='next')DECK.go(Math.min(n-1,i+1));else if(p.a==='prev')DECK.go(Math.max(0,i-1));else if(p.a==='go'&&p.n>=0&&p.n<n)DECK.go(p.n);
   document.getElementById('rem-s').textContent='Phone connected';setTimeout(push,120)});
  ch.subscribe(function(s){connected=(s==='SUBSCRIBED');document.getElementById('rem-s').textContent=connected?'Ready. Scan the code.':'Connecting…';if(connected)push()})})}
 function show(){var url=base+'?c='+C;document.getElementById('rem-a').href=url;document.getElementById('rem-a').textContent=url;
  libs(function(){try{var q=window.qrcode(0,'M');q.addData(url);q.make();document.getElementById('rem-q').innerHTML=q.createSvgTag({cellSize:4,margin:0,scalable:true})}catch(e){document.getElementById('rem-q').textContent='Open the link below on your phone'}});
  pop.classList.add('on');connect();try{localStorage.setItem('icda26-remote-on','1')}catch(e){}}
 var hud=document.getElementById('hud');if(hud){var b=document.createElement('button');b.id='brem';b.textContent='PHONE REMOTE';b.onclick=show;hud.insertBefore(b,document.getElementById('bmenu')||null)}
 document.getElementById('rem-x').onclick=function(){pop.classList.remove('on')};
 document.addEventListener('keydown',function(e){var t=e.target;if(t&&(t.isContentEditable||t.tagName==='TEXTAREA'||t.tagName==='INPUT'))return;if(e.key==='Escape')pop.classList.remove('on')});
 setInterval(function(){var s=state();if(!s)return;var sig=s.idx+'|'+s.total;if(sig!==lastSent){lastSent=sig;push()}},350);setInterval(push,3000);
 try{if(localStorage.getItem('icda26-remote-on')==='1')connect()}catch(e){}
})();
