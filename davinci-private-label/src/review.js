/* Reviewable asset ledger.
 *
 * The page renders itself from two JSON islands -- the asset rows, which never
 * change, and the review state, which does -- and saves by publishing a new
 * version of itself with the review island rewritten.
 */
(function(){
"use strict";
var DATA   = JSON.parse(document.getElementById("data").textContent);
var review = JSON.parse(document.getElementById("review").textContent);
if(!review.items) review.items={};

var GROUPS=DATA.groups, ROWS=DATA.rows;
var key=function(r){return r.k+":"+r.id;};
var E=function(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});};

/* ---- per-viewer preferences, never part of the shared document ---------- */
var LS={
  get:function(k,d){try{var v=localStorage.getItem(k);return v==null?d:v;}catch(e){return d;}},
  set:function(k,v){try{localStorage.setItem(k,v);}catch(e){}}
};
var SS={
  get:function(k,d){try{var v=sessionStorage.getItem(k);return v==null?d:v;}catch(e){return d;}},
  set:function(k,v){try{sessionStorage.setItem(k,v);}catch(e){}},
  del:function(k){try{sessionStorage.removeItem(k);}catch(e){}}
};
var who=LS.get("praxera.reviewer","");

/* ---- publishing ---------------------------------------------------------- */
var api=null, readOnly=false, mode="files", timer=null, saving=false, dirty=false;
var saveMsg="ready", saveCls="";

function buildDoc(){
  /* Reconstructed from the parts the document already carries, so the source
     stays single-copy and the live DOM is never serialized. */
  var css  = document.getElementById("sheet").textContent;
  var app  = document.getElementById("app").textContent;
  var data = document.getElementById("data").textContent;
  var end  = "<"+"/script>";
  return '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n'
    +'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
    +"<title>Praxera Migration Asset Ledger</title>\n"
    +'<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    +'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    +'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:'
    +'opsz,wght@6..72,400;6..72,500&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:'
    +'wght@400;500;600&display=swap">\n'
    +'<style id="sheet">'+css+"</style>\n</head><body>\n"
    +'<div id="root"></div>\n'
    +'<script type="application/json" id="data">'+data+end+"\n"
    +'<script type="application/json" id="review">'
      +JSON.stringify(review).replace(/</g,"\\u003c")+end+"\n"
    +'<script id="app">'+app+end+"\n</body></html>\n";
}

function flag(txt,cls){
  saveMsg=txt; saveCls=cls||"";
  var el=document.getElementById("save");
  if(el){el.textContent=txt;el.className="save"+(cls?" "+cls:"");}
}

function goReadOnly(msg){
  readOnly=true;
  flag(msg||"read-only view","err");
  render();
}

function save(){
  dirty=true;
  if(readOnly||!api){flag("not saved — no write access","err");return;}
  clearTimeout(timer);
  flag("saving\u2026");
  timer=setTimeout(commit,1600);   /* batch a run of clicks into one publish */
}

function commit(){
  if(saving||readOnly||!api) return;
  saving=true;
  var doc;
  try{ doc=buildDoc(); }
  catch(e){ saving=false; flag("could not build the page","err"); return; }
  /* Anything unsent has to outlive an html-form publish, which reloads. */
  SS.set("praxera.review",JSON.stringify(review));
  var p = mode==="files" ? api.publish({"index.html":doc}) : api.publish(doc);
  p.then(function(){
    saving=false;dirty=false;SS.del("praxera.review");
    flag("saved","on");
  }).catch(function(err){
    saving=false;
    var c=(err&&err.code)||"upstream_error";
    if(mode==="files"&&(c==="capability_disabled"||c==="read_only_path"
                        ||c==="invalid_content"||c==="transform_error")){
      /* The files form is not available here; the html form reloads the view
         but writes the same bytes. */
      mode="html";saving=false;commit();return;
    }
    if(c==="not_writer"||c==="not_granted"||c==="not_declared"
       ||c==="consent_required"||c==="capability_disabled"){
      goReadOnly("read-only view");return;
    }
    if(c==="conflict"){flag("someone else saved first \u2014 reloading");return;}
    if(c==="rate_limited"){flag("saving too fast \u2014 retrying shortly","err");
      clearTimeout(timer);timer=setTimeout(commit,6000);return;}
    if(c==="too_large"){flag("page too large to save","err");return;}
    flag("save failed \u2014 will retry","err");
    clearTimeout(timer);timer=setTimeout(commit,4000);
  });
}

/* ---- review mutations ---------------------------------------------------- */
function item(k){
  if(!review.items[k]) review.items[k]={};
  return review.items[k];
}
function setStatus(k,s){
  var it=item(k);
  if(it.s===s){ delete it.s; delete it.by; delete it.at; }
  else { it.s=s; it.by=who||"unnamed"; it.at=new Date().toISOString(); }
  if(!it.s&&!(it.c&&it.c.length)) delete review.items[k];
  save(); render();
}
function addComment(k,text){
  text=(text||"").trim(); if(!text) return;
  var it=item(k);
  if(!it.c) it.c=[];
  it.c.push({n:who||"unnamed",t:text,at:new Date().toISOString()});
  save(); render();
}

/* ---- view state (per viewer, not shared) --------------------------------- */
var view={};
GROUPS.forEach(function(g){
  view[g[0]]={f:SS.get("f."+g[0],"all"),q:SS.get("q."+g[0],"")};
});
var open={};   /* which comment threads are expanded */

function statusOf(r){
  var it=review.items[key(r)];
  return it&&it.s ? it.s : "";
}
function severity(r){
  for(var i=0;i<r.i.length;i++) if(r.i[i][0]==="bad") return "blocked";
  return r.i.length ? "tidy" : "clear";
}
function matches(r,f,q){
  if(q){
    var hay=(r.n+" "+r.r+" "+(r.t||"")+" "
      +r.i.map(function(x){return x[1];}).join(" ")).toLowerCase();
    if(hay.indexOf(q)<0) return false;
  }
  if(f==="all") return true;
  if(f==="ok"||f==="fix") return statusOf(r)===f;
  if(f==="todo") return !statusOf(r);
  return severity(r)===f;
}

function when(iso){
  try{ return new Date(iso).toLocaleDateString(undefined,
    {month:"short",day:"numeric"}); }catch(e){ return ""; }
}

function rowHtml(r){
  var k=key(r), it=review.items[k]||{}, st=it.s||"", cn=(it.c||[]).length;
  var cls="r"+(st==="ok"?" done":"")+(st==="fix"?" flag":"");
  var chips=r.i.length
    ? r.i.map(function(x){return '<span class="chip c-'+x[0]+'">'+E(x[1])+"</span>";}).join("")
    : '<span class="chip c-acc">clear</span>';
  var by=st?'<span class="by">'+(st==="ok"?"approved":"flagged")+" by "
        +E(it.by||"unnamed")+" \u00b7 "+when(it.at)+"</span>":"";
  var h='<tr class="'+cls+'" data-k="'+E(k)+'">'
    +'<td class="nm">'+E(r.n)+by+"</td>"
    +'<td class="ev"'+(r.t?' title="'+E(r.t)+'"':"")+">"
      +(r.r?E(r.r):"&mdash;")+"</td>"
    +"<td>"+chips+"</td>"
    +'<td class="act"><span class="rv">'
      +'<button class="ok" data-a="ok" aria-pressed="'+(st==="ok")+'"'
      +' title="Approve this asset">\u2713 Approve</button>'
      +'<button class="fix" data-a="fix" aria-pressed="'+(st==="fix")+'"'
      +' title="Flag this asset as needing work">Needs work</button></span>'
    +'<button class="cm'+(cn?" has":"")+'" data-a="cm">'
      +(cn?cn+" comment"+(cn>1?"s":""):"Comment")+"</button></td></tr>";
  if(open[k]) h+=threadHtml(r,it);
  return h;
}

function threadHtml(r,it){
  var k=key(r), list=(it.c||[]).map(function(c){
    return '<div class="cmt"><div class="who">'+E(c.n)+" \u00b7 "+when(c.at)
      +'</div><div class="txt">'+E(c.t)+"</div></div>";
  }).join("");
  if(!list) list='<p class="empty">No comments on this asset yet.</p>';
  return '<tr class="th" data-k="'+E(k)+'"><td colspan="4"><div class="thread">'+list
    +'<textarea data-a="txt" placeholder="Add a comment about '+E(r.n)+'\u2026"'
    +' aria-label="Comment"></textarea>'
    +'<div class="row"><button data-a="post">Post comment</button>'
    +'<button class="gh" data-a="close">Close</button></div></div></td></tr>';
}

function tally(rows){
  var t={ok:0,fix:0,todo:0};
  rows.forEach(function(r){var s=statusOf(r);t[s==="ok"?"ok":s==="fix"?"fix":"todo"]++;});
  return t;
}

var FILTERS=[["all","All"],["todo","Not reviewed"],["ok","Approved"],
             ["fix","Needs work"],["blocked","Has a defect"]];

function groupHtml(g){
  var gk=g[0], rows=ROWS.filter(function(r){return r.k===gk;});
  var v=view[gk], shown=rows.filter(function(r){return matches(r,v.f,v.q);});
  var t=tally(rows);
  var btns=FILTERS.map(function(f){
    return '<button class="f" data-g="'+gk+'" data-f="'+f[0]+'" aria-pressed="'
      +(v.f===f[0])+'">'+E(f[1])+"</button>";}).join("");
  return '<section id="g-'+gk+'"><div class="shead"><p class="eyebrow">'
    +t.ok+" approved \u00b7 "+t.fix+" need work \u00b7 "+t.todo+" not yet reviewed</p>"
    +'<h2>'+E(g[1])+"</h2></div>"
    +'<div class="filters"><label class="srch">'
      +'<input type="search" data-g="'+gk+'" value="'+E(v.q)+'" placeholder="Filter\u2026"'
      +' aria-label="Filter '+E(g[1])+'"></label>'+btns
      +'<span class="count">'+shown.length+" of "+rows.length+"</span></div>"
    +'<div class="tscroll"><table><thead><tr><th>Praxera asset</th><th>Replaces</th>'
      +"<th>Outstanding</th><th>Your review</th></tr></thead><tbody>"
      +(shown.length?shown.map(rowHtml).join("")
        :'<tr class="r"><td colspan="4" class="ev">Nothing matches this filter.</td></tr>')
      +"</tbody></table></div></section>";
}

function headerHtml(){
  var t=tally(ROWS), n=ROWS.length;
  var pa=(t.ok/n*100).toFixed(2), pf=(t.fix/n*100).toFixed(2);
  var nav=GROUPS.map(function(g){
    var rs=ROWS.filter(function(r){return r.k===g[0];}), tt=tally(rs);
    return '<a href="#g-'+g[0]+'">'+E(g[1])+" <b>"+tt.ok+"/"+rs.length+"</b></a>";
  }).join("");
  return '<header class="top"><div class="wrap">'
    +'<div class="brandline"><span class="dot"></span><span>FoodScience LLC \u00b7 '
    +'HubSpot 4087538 \u00b7 Private Label \u2192 Praxera</span></div>'
    +"<h1>Sign off the Praxera stack,<br>one asset at a time.</h1>"
    +'<p class="sub">All '+n+" assets exist in Praxera form, in draft, alongside the "
    +"original. Approve the ones that are right, flag the ones that are not, and leave a "
    +"comment where the reason matters. Everything you do here is saved into the page "
    +"itself, so the next person to open it sees it.</p>"
    +'<div class="prog"><div class="bar"><i class="a" style="width:'+pa+'%"></i>'
      +'<i class="f" style="width:'+pf+'%"></i></div>'
      +'<div class="lg"><span><i class="k a"></i>Approved <b>'+t.ok+"</b></span>"
      +'<span><i class="k f"></i>Needs work <b>'+t.fix+"</b></span>"
      +'<span><i class="k u"></i>Not reviewed <b>'+t.todo+"</b></span>"
      +"<span>Total <b>"+n+"</b></span></div></div>"
    +'<div class="idbar'+(readOnly?" ro":"")+'" id="idbar">'
      +'<label for="who">Reviewing as</label>'
      +'<input id="who" value="'+E(who)+'" placeholder="Your name" autocomplete="name"'
      +(readOnly?" disabled":"")+">"
      +'<span class="save '+saveCls+'" id="save">'+E(saveMsg)+"</span>"
      +(readOnly?'<span class="save err">This view cannot write to the page, so '
        +'approvals and comments are not saved.</span>':"")+"</div>"
    +'<p class="note">Asset state re-read from the live portal on '+E(DATA.stamp)
    +". Nothing is published, nothing is enabled, and no DaVinci, PetTechLabs or "
    +"VetriScience asset has been modified.</p>"
    +'</div></header><div class="wrap"><nav class="jump" aria-label="Asset groups">'
    +nav+"</nav>"+GROUPS.map(groupHtml).join("")+"</div>";
}

function render(){
  var y=window.scrollY;
  document.getElementById("root").innerHTML=headerHtml();
  window.scrollTo(0,y);
}

/* ---- events (delegated, so re-rendering never orphans a handler) --------- */
var root=document.getElementById("root");

root.addEventListener("click",function(ev){
  var b=ev.target.closest("button"); if(!b) return;
  if(b.classList.contains("f")){
    view[b.dataset.g].f=b.dataset.f; SS.set("f."+b.dataset.g,b.dataset.f);
    render(); return;
  }
  var tr=b.closest("tr"); if(!tr) return;
  var k=tr.dataset.k, a=b.dataset.a;
  if(a==="ok"||a==="fix"){
    if(readOnly) return;
    setStatus(k,a); return;
  }
  if(a==="cm"){ open[k]=!open[k]; render();
    if(open[k]){ var ta=root.querySelector('tr.th[data-k="'+CSS.escape(k)+'"] textarea');
      if(ta) ta.focus(); }
    return; }
  if(a==="close"){ open[k]=false; render(); return; }
  if(a==="post"){
    if(readOnly) return;
    var box=tr.querySelector("textarea");
    if(box&&box.value.trim()){ addComment(k,box.value); open[k]=true; render(); }
    return;
  }
});

root.addEventListener("input",function(ev){
  var t=ev.target;
  if(t.id==="who"){ who=t.value.trim(); LS.set("praxera.reviewer",who); return; }
  if(t.type==="search"){
    var g=t.dataset.g, pos=t.selectionStart;
    view[g].q=t.value.trim().toLowerCase(); SS.set("q."+g,view[g].q);
    render();
    var again=root.querySelector('input[type=search][data-g="'+g+'"]');
    if(again){ again.focus(); try{again.setSelectionRange(pos,pos);}catch(e){} }
  }
});

root.addEventListener("keydown",function(ev){
  if(ev.key==="Enter"&&(ev.metaKey||ev.ctrlKey)&&ev.target.tagName==="TEXTAREA"){
    var tr=ev.target.closest("tr");
    if(tr) addComment(tr.dataset.k,ev.target.value);
  }
});

/* ---- boot ---------------------------------------------------------------- */
/* An html-form publish reloads the view, so anything unsent at that moment is
   picked back up here rather than lost. */
var pending=SS.get("praxera.review",null);
if(pending){
  try{
    var p=JSON.parse(pending), n=Object.keys(p.items||{}).length;
    if(n>=Object.keys(review.items).length) review=p;
  }catch(e){}
  SS.del("praxera.review");
}
render();

if(window.claude&&typeof window.claude.use==="function"){
  window.claude.use("artifact").then(function(a){
    if(!a){ goReadOnly("read-only view"); return; }
    api=a; flag(dirty?"saving\u2026":"ready");
    if(dirty) commit();
  }).catch(function(){ goReadOnly("read-only view"); });
}else{
  goReadOnly("preview \u2014 not saved");
}
})();
