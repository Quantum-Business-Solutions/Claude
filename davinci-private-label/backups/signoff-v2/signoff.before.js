/* Per-asset sign-off, hosted in the ClientCommand portal.
 *
 * State lives in portal_document_state through window.ClientCommand, not in
 * localStorage: the portal renders this page in a sandboxed iframe without
 * allow-same-origin, so localStorage THROWS and the usual try/catch swallows it
 * -- a page that looks like it saved and did not.
 *
 * Three things about that store shape this file:
 *   shared   one row per (document, state_key), no user in the key, so every
 *            viewer reads and writes the same decisions.
 *   last-write-wins  no merge, no conflict detection. State is partitioned one
 *            key per asset group so two reviewers working different groups
 *            cannot overwrite each other; inside a group they still can.
 *   attributed per ROW, not per item. 272 assets under one key would record a
 *            single writer, so each decision carries its own reviewer name.
 */
(function(){
"use strict";
/* Rows arrive in several islands so the payload can cross into the portal in
   verifiable pieces; metadata is separate and small. */
var DATA=JSON.parse(document.getElementById("meta").textContent);
DATA.rows=[];
[].forEach.call(document.querySelectorAll("script.rowdata"),function(el){
  DATA.rows=DATA.rows.concat(JSON.parse(el.textContent));
});
var GROUPS=DATA.groups, ROWS=DATA.rows, R=DATA.redirects||{by_kind:{}};
/* Issue labels are interned: a row carries indices into DATA.labels. */
var LABELS=DATA.labels||[];
ROWS.forEach(function(r){
  r.i=(r.i||[]).map(function(x){return typeof x==="number"?LABELS[x]:x;});
});
var KEYPREFIX="assets:";                 /* assets:website-pages, … */
var CAP=256*1024;                        /* per-row limit, enforced server-side */

var state={};                            /* groupKey -> {itemId:{s,by,at,c[]}} */
GROUPS.forEach(function(g){ state[g[0]]={}; });

var bridge=(typeof window.ClientCommand!=="undefined");
var who="", dirty={}, timer={}, msg="ready", cls="";

function E(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
function keyOf(g){return KEYPREFIX+g;}
function slug(g){var m={p:"website-pages",b:"blog-posts",e:"emails",
  f:"forms",w:"workflows"};return KEYPREFIX+(m[g]||g);}

/* ---- saving ------------------------------------------------------------- */
function flag(t,k){msg=t;cls=k||"";var el=document.getElementById("save");
  if(el){el.textContent=t;el.className="save "+(k||"");}}

function save(g){
  if(!bridge){flag("not saved — open this page inside the portal","err");return;}
  dirty[g]=true;
  clearTimeout(timer[g]);
  flag("saving…");
  /* The host already coalesces at 600ms; this batches a run of clicks on one
     group into a single write rather than one per click. */
  timer[g]=setTimeout(function(){commit(g);},700);
}

function commit(g){
  var payload=JSON.stringify(state[g]);
  if(payload.length>CAP){
    flag("this group is too large to save — tell QBS","err");return;
  }
  try{ window.ClientCommand.save(state[g],slug(g)); dirty[g]=false; }
  catch(e){ flag("save failed — "+(e&&e.message||"unknown"),"err"); }
}

/* ---- review mutations ---------------------------------------------------- */
function item(g,id){var s=state[g];if(!s[id])s[id]={};return s[id];}
function setStatus(g,id,v){
  var it=item(g,id);
  if(it.s===v){delete it.s;delete it.by;delete it.at;}
  else{it.s=v;it.by=who||"unnamed";it.at=new Date().toISOString();}
  if(!it.s&&!(it.c&&it.c.length))delete state[g][id];
  save(g);render();
}
function addComment(g,id,text){
  text=(text||"").trim();if(!text)return;
  var it=item(g,id);if(!it.c)it.c=[];
  it.c.push({n:who||"unnamed",t:text,at:new Date().toISOString()});
  save(g);render();
}

/* ---- per-viewer view state (never written to the shared row) ------------- */
var view={},open={};
GROUPS.forEach(function(g){view[g[0]]={f:"all",q:""};});

function statusOf(r){var it=state[r.k][r.id];return it&&it.s?it.s:"";}
function severity(r){
  for(var i=0;i<r.i.length;i++)if(r.i[i][0]==="bad")return "blocked";
  return r.i.length?"tidy":"clear";
}
function matches(r,f,q){
  if(q){var hay=(r.n+" "+r.r+" "+(r.t||"")+" "+
    r.i.map(function(x){return x[1];}).join(" ")).toLowerCase();
    if(hay.indexOf(q)<0)return false;}
  if(f==="all")return true;
  if(f==="ok"||f==="fix")return statusOf(r)===f;
  if(f==="todo")return !statusOf(r);
  return severity(r)===f;
}
function when(iso){try{return new Date(iso).toLocaleDateString(undefined,
  {month:"short",day:"numeric"});}catch(e){return "";}}

/* ---- rendering ----------------------------------------------------------- */
function rowHtml(r){
  var it=state[r.k][r.id]||{},st=it.s||"",cn=(it.c||[]).length;
  var cls2="r"+(st==="ok"?" done":"")+(st==="fix"?" flag":"");
  var chips=r.i.length?r.i.map(function(x){
      return '<span class="chip c-'+x[0]+'">'+E(x[1])+"</span>";}).join("")
    :'<span class="chip c-acc">clear</span>';
  var by=st?'<span class="by">'+(st==="ok"?"approved":"flagged")+" by "
    +E(it.by||"unnamed")+" · "+when(it.at)+"</span>":"";
  var h='<tr class="'+cls2+'" data-g="'+r.k+'" data-i="'+E(r.id)+'">'
    +'<td class="nm">'+E(r.n)+by+"</td>"
    +'<td class="ev"'+(r.t?' title="'+E(r.t)+'"':"")+">"
      +(r.new?'<span class="chip c-ok">new page</span>':(r.r?E(r.r):"&mdash;"))+"</td>"
    +"<td>"+chips+"</td>"
    +'<td class="act"><span class="rv">'
      +'<button class="ok" data-a="ok" aria-pressed="'+(st==="ok")+'">✓ Approve</button>'
      +'<button class="fix" data-a="fix" aria-pressed="'+(st==="fix")+'">Needs work</button>'
      +"</span>"
    +'<button class="cm'+(cn?" has":"")+'" data-a="cm">'
      +(cn?cn+" comment"+(cn>1?"s":""):"Comment")+"</button></td></tr>";
  if(open[r.k+":"+r.id])h+=threadHtml(r,it);
  return h;
}
function threadHtml(r,it){
  var list=(it.c||[]).map(function(c){
    return '<div class="cmt"><div class="who">'+E(c.n)+" · "+when(c.at)
      +'</div><div class="txt">'+E(c.t)+"</div></div>";}).join("");
  if(!list)list='<p class="empty">No comments on this asset yet.</p>';
  return '<tr class="th" data-g="'+r.k+'" data-i="'+E(r.id)+'"><td colspan="4">'
    +'<div class="thread">'+list
    +'<textarea data-a="txt" aria-label="Comment" placeholder="Add a comment about '
    +E(r.n)+'…"></textarea>'
    +'<div class="row"><button data-a="post">Post comment</button>'
    +'<button class="gh" data-a="close">Close</button></div></div></td></tr>';
}
function tally(rows){var t={ok:0,fix:0,todo:0};
  rows.forEach(function(r){var s=statusOf(r);
    t[s==="ok"?"ok":s==="fix"?"fix":"todo"]++;});return t;}

var FILTERS=[["all","All"],["todo","Not reviewed"],["ok","Approved"],
             ["fix","Needs work"],["blocked","Has a defect"]];

function groupHtml(g){
  var gk=g[0],rows=ROWS.filter(function(r){return r.k===gk;});
  var v=view[gk],shown=rows.filter(function(r){return matches(r,v.f,v.q);});
  var t=tally(rows);
  var btns=FILTERS.map(function(f){
    return '<button class="f" data-g="'+gk+'" data-f="'+f[0]+'" aria-pressed="'
      +(v.f===f[0])+'">'+E(f[1])+"</button>";}).join("");
  return '<section id="g-'+gk+'"><div class="shead"><p class="eyebrow">'
    +t.ok+" approved · "+t.fix+" need work · "+t.todo+" not yet reviewed"
    +' · saved under <code>'+slug(gk)+"</code></p><h2>"+E(g[1])+"</h2></div>"
    +'<div class="filters"><label class="srch"><input type="search" data-g="'+gk
      +'" value="'+E(v.q)+'" placeholder="Filter…" aria-label="Filter '+E(g[1])
      +'"></label>'+btns+'<span class="count">'+shown.length+" of "+rows.length
      +"</span></div>"
    +'<div class="tscroll"><table><thead><tr><th>Praxera asset</th><th>'
      +E(g[2]||"Replaces")+"</th><th>Outstanding</th><th>Your review</th>"
      +"</tr></thead><tbody>"
      +(shown.length?shown.map(rowHtml).join("")
        :'<tr class="r"><td colspan="4" class="ev">Nothing matches this filter.</td></tr>')
      +"</tbody></table></div></section>";
}

function headerHtml(){
  var t=tally(ROWS),n=ROWS.length;
  var pa=(t.ok/n*100).toFixed(2),pf=(t.fix/n*100).toFixed(2);
  var nav=GROUPS.map(function(g){
    var rs=ROWS.filter(function(r){return r.k===g[0];}),tt=tally(rs);
    return '<a href="#g-'+g[0]+'">'+E(g[1])+" <b>"+tt.ok+"/"+rs.length+"</b></a>";
  }).join("");
  return '<header class="top"><div class="wrap">'
    +'<p class="brandline"><span class="dot"></span>FoodScience LLC · HubSpot 4087538'
    +' · Private Label → Praxera</p>'
    +"<h1>Sign off the Praxera stack,<br>one asset at a time.</h1>"
    +'<p class="lede">All '+n+" assets exist in Praxera form, in draft, alongside the "
    +"original. Approve the ones that are right, flag the ones that are not, and leave a "
    +"comment where the reason matters. Everything is saved to this portal against this "
    +"page, so the next person to open it sees it — no login beyond the portal link.</p>"
    +'<p class="lede">For pages and posts the second column is the DaVinci URL that will '
    +"<strong>redirect here</strong> at cutover — "+R.pairs+" redirects in all ("
    +R.by_kind.page+" pages, "+R.by_kind.blog+" posts). A row marked <strong>new page</strong> "
    +"has no DaVinci original and needs no redirect.</p>"
    +'<div class="prog"><div class="bar"><i class="a" style="width:'+pa+'%"></i>'
      +'<i class="f" style="width:'+pf+'%"></i></div><div class="lg">'
      +'<span><i class="k a"></i>Approved <b>'+t.ok+"</b></span>"
      +'<span><i class="k f"></i>Needs work <b>'+t.fix+"</b></span>"
      +'<span><i class="k u"></i>Not reviewed <b>'+t.todo+"</b></span>"
      +"<span>Total <b>"+n+"</b></span></div></div>"
    +'<div class="idbar'+(bridge?"":" ro")+'" id="idbar">'
      +'<label for="who">Reviewing as</label>'
      +'<input id="who" value="'+E(who)+'" placeholder="Your name" autocomplete="name">'
      +'<span class="save '+cls+'" id="save">'+E(msg)+"</span>"
      +(bridge?"":'<span class="save err">This page is not running inside the portal, '
        +"so nothing is saved.</span>")+"</div>"
    +'<p class="note">Two people can review at once, but a group is saved as one record '
    +"and the last save wins — so take a group each rather than the same one. "
    +"Asset state re-read from the live portal on "+E(DATA.stamp)+"; nothing is published, "
    +"nothing is enabled.</p>"
    +'</div></header><div class="wrap"><nav class="jump">'+nav+"</nav>"
    +GROUPS.map(groupHtml).join("")+"</div>";
}
function render(){var y=window.scrollY;
  document.getElementById("root").innerHTML=headerHtml();window.scrollTo(0,y);}

/* ---- events -------------------------------------------------------------- */
var root=document.getElementById("root");
root.addEventListener("click",function(ev){
  var b=ev.target.closest("button");if(!b)return;
  if(b.classList.contains("f")){view[b.dataset.g].f=b.dataset.f;render();return;}
  var tr=b.closest("tr");if(!tr)return;
  var g=tr.dataset.g,id=tr.dataset.i,a=b.dataset.a,k=g+":"+id;
  if(a==="ok"||a==="fix"){setStatus(g,id,a);return;}
  if(a==="cm"){open[k]=!open[k];render();
    if(open[k]){var ta=root.querySelector('tr.th[data-g="'+g+'"] textarea');
      if(ta)ta.focus();}
    return;}
  if(a==="close"){open[k]=false;render();return;}
  if(a==="post"){var box=tr.querySelector("textarea");
    if(box&&box.value.trim()){addComment(g,id,box.value);open[k]=true;render();}
    return;}
});
root.addEventListener("input",function(ev){
  var t=ev.target;
  if(t.id==="who"){who=t.value.trim();return;}
  if(t.type==="search"){var g=t.dataset.g,pos=t.selectionStart;
    view[g].q=t.value.trim().toLowerCase();render();
    var again=root.querySelector('input[type=search][data-g="'+g+'"]');
    if(again){again.focus();try{again.setSelectionRange(pos,pos);}catch(e){}}}
});
root.addEventListener("keydown",function(ev){
  if(ev.key==="Enter"&&(ev.metaKey||ev.ctrlKey)&&ev.target.tagName==="TEXTAREA"){
    var tr=ev.target.closest("tr");
    if(tr)addComment(tr.dataset.g,tr.dataset.i,ev.target.value);}
});

/* ---- boot ---------------------------------------------------------------- */
render();
if(bridge){
  window.ClientCommand.onSaved=function(ok,err){
    var pending=GROUPS.some(function(g){return dirty[g[0]];});
    flag(ok?(pending?"saving…":"saved to the portal"):
      ("not saved"+(err?" — "+err:"")),ok?"on":"err");
  };
  /* One load per group: the store is partitioned so two reviewers working
     different groups never overwrite one another. */
  GROUPS.forEach(function(g){
    window.ClientCommand.load(slug(g[0]),function(v){
      if(v&&typeof v==="object"){state[g[0]]=v;render();}
    });
  });
}else{
  flag("not saved — open this page inside the portal","err");
}
})();
