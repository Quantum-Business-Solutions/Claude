/* ClientCommand Asset Sign-off — shared, two-stage, editable.
 *
 * Generic: everything client-specific comes from the #meta island and the
 * script.rowdata islands, so the same script serves any client's sign-off.
 *
 * Storage is portal_document_state through the host bridge (postMessage). The
 * host writes as the signed-in user under RLS; the page never touches a DB.
 * localStorage is NOT available (sandbox has no allow-same-origin).
 *
 * Keys (one row each in portal_document_state):
 *   assets:<group>   review state per item  {q,c,f,cm,sr}
 *   assets:edits     rows added / changed / removed by people
 *   assets:log       the change log — who did what, when
 *
 * Concurrency: several people work the sheet at once. Every fact carries its
 * own timestamp and merges item-by-item (newest wins, comments union), the
 * page re-reads the portal every 25s, and it writes only the keys it changed.
 * Last-write-wins still exists inside one item in the same second; accepted.
 */
(function(){
"use strict";
var META=JSON.parse(document.getElementById("meta").textContent);
var ROWS=[];
[].forEach.call(document.querySelectorAll("script.rowdata"),function(el){
  ROWS=ROWS.concat(JSON.parse(el.textContent));});
var LABELS=META.labels||[];
var TYPES=META.types||[],HS=META.hs||{},LIVE=META.live||{};
ROWS.forEach(function(r){r.i=(r.i||[]).map(function(x){return typeof x==="number"?LABELS[x]:x;});
  r.sc=r.sc||[];r.gen=1;if(typeof r.y==="number")r.y=TYPES[r.y];
  if(!r.h&&r.hid&&HS[r.k])r.h=HS[r.k].replace("{id}",r.hid);
  if(!r.u&&LIVE[r.k]&&r.slug!==undefined)r.u=LIVE[r.k].replace("{slug}",r.slug);});
var GROUPS=META.groups, GK=GROUPS.map(function(g){return g[0];});
var PFX="assets:", CAP=250*1024;
var KEY={edits:PFX+"edits",log:PFX+"log",gen:PFX+"general"};
var GEN={k:"_",id:"general",n:"Global notes",sc:META.gc||[],i:[]};
function gkey(g){return g==="_"?KEY.gen:PFX+(META.keys&&META.keys[g]||g);}

/* ---- host bridge (own listener: the shim's single callback cannot tell
        several keys apart) ---------------------------------------------- */
var hosted=(window.parent&&window.parent!==window);
var HOST="clientcommand-host",PAGE="clientcommand-page";
function post(m){m.source=PAGE;try{window.parent.postMessage(m,"*");}catch(e){}}
var user=null;               /* {name,email,kind:'team'|'client'} from host */
var saveCb={};
window.addEventListener("message",function(e){
  var d=e.data;if(!d||d.source!==HOST)return;
  if(d.type==="state")onRemote(d.key,d.value);
  else if(d.type==="saved"){var f=saveCb[d.key];if(f){delete saveCb[d.key];f(d.ok,d.error);}
    else flag(d.ok?"saved to the portal":("not saved"+(d.error?" — "+d.error:"")),d.ok?"on":"err");}
  else if(d.type==="downloaded"){clearTimeout(csvTimer);flag("downloaded "+(d.name||""),"on");}
  else if(d.type==="whoami"&&!(d.user&&typeof d.user==="object")){hostv2=true;render();}
  else if(d.type==="whoami"&&d.user&&typeof d.user==="object"){
    hostv2=true;
    user={name:String(d.user.name||""),email:String(d.user.email||""),kind:String(d.user.kind||"")};
    if(user.name)who=user.name; if(user.kind==="team")side="qbs"; if(user.kind==="client")side="client";
    render();}
});
function requestState(k){post({type:"ready",key:k});}
function writeState(k,v,cb){
  var s=JSON.stringify(v);
  if(s.length>CAP){flag("too much saved under "+k+" — tell QBS","err");return;}
  if(cb)saveCb[k]=cb;
  post({type:"state:set",key:k,value:v});
}

/* ---- state ------------------------------------------------------------ */
var state={},edits={mod:{},add:{},del:{},chips:{}},log={e:[]};
GK.forEach(function(g){state[g]={};edits.mod[g]={};edits.add[g]=[];edits.del[g]={};edits.chips[g]={};});state._={};
var who="",side="",msg=hosted?"loading…":"not saved — open inside the portal",cls=hosted?"":"err";
var loaded={},dirty={},timer=null;

function now(){return new Date().toISOString();}
function uid(){return Date.now().toString(36)+Math.random().toString(36).slice(2,7);}
function me(){return who||"unnamed";}
function later(a,b){return (a&&a.at||"")>(b&&b.at||"");}

/* merge helpers — newest fact wins, lists union by id */
function mergeStamp(l,r){if(!l)return r;if(!r)return l;return later(r,l)?r:l;}
function mergeList(l,r,merge){var out={},o=[];
  (l||[]).concat(r||[]).forEach(function(c){if(!c||!c.id)return;
    if(out[c.id]){out[c.id]=merge?merge(out[c.id],c):(later(c,out[c.id])?c:out[c.id]);}
    else out[c.id]=c;});
  for(var k in out)o.push(out[k]);
  o.sort(function(a,b){return (a.at||"")<(b.at||"")?-1:1;});return o;}
function mergeComment(a,b){var c=later(b,a)?b:a; var o={};for(var k in c)o[k]=c[k];
  o.st=later(b.rs,a.rs)?b.st:a.st; o.rs=mergeStamp(a.rs,b.rs);
  o.re=mergeList(a.re,b.re); return o;}
function mergeItem(l,r){if(!l)return r;if(!r)return l;var o={};
  o.q=mergeStamp(l.q,r.q);o.c=mergeStamp(l.c,r.c);o.f=mergeStamp(l.f,r.f);
  o.r1=mergeStamp(l.r1,r.r1);o.r2=mergeStamp(l.r2,r.r2);o.r3=mergeStamp(l.r3,r.r3);
  o.cm=mergeList(l.cm,r.cm,mergeComment);
  o.sr={};var ks={};[l.sr,r.sr].forEach(function(s){for(var k in (s||{}))ks[k]=1;});
  for(var k in ks)o.sr[k]=mergeComment(l.sr&&l.sr[k]||{id:k,re:[]},r.sr&&r.sr[k]||{id:k,re:[]});
  return o;}
function mergeGroup(l,r){var o={},ks={};[l,r].forEach(function(s){for(var k in (s||{}))ks[k]=1;});
  for(var k in ks)o[k]=mergeItem(l&&l[k],r&&r[k]);return o;}
function mergeEdits(l,r){var o={mod:{},add:{},del:{},chips:{}};
  GK.forEach(function(g){
    o.mod[g]={};var ks={};[l,r].forEach(function(s){for(var k in (s.mod&&s.mod[g]||{}))ks[k]=1;});
    for(var k in ks){var a=l.mod[g]&&l.mod[g][k],b=r.mod&&r.mod[g]&&r.mod[g][k];
      if(!a||!b){o.mod[g][k]=a||b;continue;}
      var m={};for(var f in a)m[f]=a[f];for(var f2 in b)if(!a[f2]||later(b[f2],a[f2]))m[f2]=b[f2];o.mod[g][k]=m;}
    o.add[g]=mergeList(l.add[g],r.add&&r.add[g]);
    o.del[g]={};ks={};[l,r].forEach(function(s){for(var k in (s.del&&s.del[g]||{}))ks[k]=1;});
    for(var k2 in ks)o.del[g][k2]=mergeStamp(l.del[g]&&l.del[g][k2],r.del&&r.del[g]&&r.del[g][k2]);
    o.chips[g]={};[l,r].forEach(function(s){var cg=s.chips&&s.chips[g]||{};
      for(var k3 in cg){o.chips[g][k3]=o.chips[g][k3]||{};
        for(var lb in cg[k3])o.chips[g][k3][lb]=mergeStamp(o.chips[g][k3][lb],cg[k3][lb]);}});
  });return o;}
function onRemote(key,value){
  if(key===KEY.edits){if(value&&typeof value==="object")edits=mergeEdits(edits,value);loaded[key]=1;}
  else if(key===KEY.log){if(value&&value.e)log.e=mergeList(log.e,value.e).slice(-800);loaded[key]=1;}
  else{var g=GK.concat(["_"]).filter(function(x){return gkey(x)===key;})[0];
    if(g){if(value&&typeof value==="object")state[g]=mergeGroup(state[g],value);loaded[key]=1;}}
  if(pendingWrite[key]){doWrite(key);}
  var all=GK.every(function(g){return loaded[gkey(g)];})&&loaded[KEY.edits]&&loaded[KEY.log]&&loaded[KEY.gen];
  if(all&&(msg==="loading…"||msg==="refreshing…"))flag("up to date","on");
  render();
}
function refresh(){if(!hosted)return;GK.forEach(function(g){requestState(gkey(g));});
  requestState(KEY.edits);requestState(KEY.log);requestState(KEY.gen);}

/* ---- saving --------------------------------------------------------------- */
function flag(t,k){msg=t;cls=k||"";var el=document.getElementById("save");
  if(el){el.textContent=t;el.className="save "+(k||"");}}
function touch(k){if(!hosted){flag("not saved — open inside the portal","err");return;}
  dirty[k]=1;clearTimeout(timer);flag("saving…");timer=setTimeout(commit,700);}
/* Read-before-write: ask the host for the current row, merge it in, then write
   the merged value. Two people saving the same group seconds apart both keep
   their changes. If the host does not answer in 2s, write anyway. */
var pendingWrite={},writeTimer={};
function commit(){var ks=Object.keys(dirty);dirty={};if(!ks.length)return;
  ks.forEach(function(k){pendingWrite[k]=1;requestState(k);
    clearTimeout(writeTimer[k]);writeTimer[k]=setTimeout(function(){if(pendingWrite[k])doWrite(k);},2000);});}
function doWrite(k){delete pendingWrite[k];clearTimeout(writeTimer[k]);
  var v=k===KEY.edits?edits:k===KEY.log?log:k===KEY.gen?state._:state[GK.filter(function(g){return gkey(g)===k;})[0]];
  writeState(k,v,function(ok,err){
    if(!ok)flag("not saved — "+(err||"unknown"),"err");
    else if(!Object.keys(dirty).length&&!Object.keys(pendingWrite).length)flag("saved to the portal","on");});}
function logIt(a,g,id,name,extra){
  log.e.push({id:uid(),at:now(),by:me(),sd:side,a:a,g:g,i:id,n:name,x:extra||""});
  if(log.e.length>800)log.e=log.e.slice(-800);touch(KEY.log);}

/* ---- rows (generated + edits) ---------------------------------------------- */
function rowsOf(g){
  var out=ROWS.filter(function(r){return r.k===g;}).map(function(r){var o={};for(var k in r)o[k]=r[k];return o;});
  (edits.add[g]||[]).forEach(function(a){var o={};for(var k in a)o[k]=a[k];o.k=g;o.i=o.i||[];o.sc=[];o.added=1;out.push(o);});
  out.forEach(function(r){var m=edits.mod[g][r.id];if(m){["n","u","h","r","y","note"].forEach(function(f){if(m[f])r[f]=m[f].v;});r.edited=m;}
    var d=edits.del[g][r.id];r.deleted=!!(d&&!d.x);
    var ch=edits.chips[g][r.id]||{};r.i=r.i.filter(function(x){return !(ch[x[1]]&&!ch[x[1]].x);});});
  return out;}
function findRow(g,id){if(g==="_")return GEN;return rowsOf(g).filter(function(x){return x.id===id;})[0];}
function rowName(g,id){var r=findRow(g,id);return r?r.n:id;}
function item(g,id){var s=state[g];if(!s[id])s[id]={};return s[id];}
function stat(it,k){return it&&it[k]&&!it[k].x?it[k]:null;}
function statusOf(g,id){var it=state[g][id]||{};return {q:stat(it,"q"),c:stat(it,"c"),f:stat(it,"f")};}
var REVS=["r1","r2","r3"];
function revOf(r,k){var it=state[r.k][r.id]||{};if(it[k])return it[k].x?null:it[k];
  return (r.rv||[]).indexOf(+k.slice(1))>=0?{by:"Design Approval Sheet v6",at:"2026-09-07T12:00:00-04:00",sheet:1}:null;}
function setRev(g,id,k){var r=findRow(g,id);if(!r)return;if(!side){askSide();return;}
  var it=item(g,id),on=revOf(r,k);
  it[k]=on?{at:now(),by:me(),x:1}:{at:now(),by:me()};
  logIt(on?"rev-clear":"rev-tick",g,id,r.n,"Rev "+k.slice(1));touch(gkey(g));}
function comments(r){var it=state[r.k][r.id]||{},sr=it.sr||{};
  var seeds=(r.sc||[]).map(function(s){var o={id:s.id,n:s.n,at:s.at,t:s.t,src:s.src,seed:1};
    var x=sr[s.id]||{};o.st=x.st||"open";o.rs=x.rs;o.re=(s.re||[]).map(function(r,i){return {id:s.id+":r"+i,n:r.n,t:r.t,at:r.at,seed:1};}).concat(x.re||[]);return o;});
  var mine=(it.cm||[]).map(function(c){var o={};for(var k in c)o[k]=c[k];o.st=o.st||"open";o.re=o.re||[];return o;});
  return seeds.concat(mine).sort(function(a,b){return (a.at||"")<(b.at||"")?-1:1;});}
function openCount(r){return comments(r).filter(function(c){return c.st!=="done";}).length;}

/* ---- mutations ------------------------------------------------------------- */
function can(k){if(!side)return false;if(k==="q")return side==="qbs";if(k==="c")return side==="client";return true;}
function locked(k){return !!side&&!can(k);}   /* the other side's button */
var needSide=false;
function askSide(){needSide=true;render();var el=document.getElementById("idbar");
  if(el){el.scrollIntoView({behavior:"smooth",block:"center"});var w=document.getElementById("who");if(w)w.focus();}}
function setStatus(g,id,k){
  var r=findRow(g,id);if(!r)return;
  if(!side){askSide();return;}
  if(!can(k)){flag(k==="q"?"only QBS can give the QBS approval":k==="c"?"only the client can give the client approval":"","err");return;}
  var it=item(g,id),on=stat(it,k);
  if(on){it[k]={at:now(),by:me(),x:1};logIt(k==="q"?"qbs-unapprove":k==="c"?"client-unapprove":"clear-flag",g,id,r.n);}
  else{it[k]={at:now(),by:me()};
    if(k==="f"){["q","c"].forEach(function(o){if(stat(it,o))it[o]={at:now(),by:me(),x:1};});}
    else if(stat(it,"f"))it.f={at:now(),by:me(),x:1};
    logIt(k==="q"?"qbs-approve":k==="c"?"client-approve":"needs-work",g,id,r.n);}
  touch(gkey(g));}
function addComment(g,id,text){text=(text||"").trim();if(!text)return;
  var it=item(g,id);if(!it.cm)it.cm=[];
  it.cm.push({id:uid(),n:me(),sd:side,t:text,at:now(),st:"open",re:[]});
  logIt("comment",g,id,rowName(g,id),text.slice(0,140));touch(gkey(g));}
function findComment(it,cid){var c=(it.cm||[]).filter(function(x){return x.id===cid;})[0];
  if(c)return c;if(!it.sr)it.sr={};if(!it.sr[cid])it.sr[cid]={id:cid,re:[]};return it.sr[cid];}
function replyTo(g,id,cid,text){text=(text||"").trim();if(!text)return;
  var c=findComment(item(g,id),cid);c.re=c.re||[];c.re.push({id:uid(),n:me(),sd:side,t:text,at:now()});
  logIt("reply",g,id,rowName(g,id),text.slice(0,140));touch(gkey(g));}
function resolveComment(g,id,cid,done){var c=findComment(item(g,id),cid);
  c.st=done?"done":"open";c.rs={at:now(),by:me()};
  logIt(done?"resolve-comment":"reopen-comment",g,id,rowName(g,id));touch(gkey(g));}
function editRow(g,id,f){var m=edits.mod[g][id]||(edits.mod[g][id]={}),ch=[],cur=findRow(g,id)||{};
  for(var k in f){var v=(f[k]||"").trim();if(v!==(cur[k]||"")){m[k]={v:v,at:now(),by:me()};ch.push(k+": "+(v||"(blank)").slice(0,60));}}
  if(ch.length){logIt("edit",g,id,rowName(g,id),ch.join(" · "));touch(KEY.edits);}}
function addRow(g,f){var o={id:"x"+uid(),at:now(),by:me()};
  for(var k in f)if((f[k]||"").trim())o[k]=f[k].trim();
  if(!o.n)return;edits.add[g].push(o);logIt("add",g,o.id,o.n);touch(KEY.edits);}
function delRow(g,id,undo){edits.del[g][id]=undo?{at:now(),by:me(),x:1}:{at:now(),by:me()};
  logIt(undo?"restore":"delete",g,id,rowName(g,id));touch(KEY.edits);}
function dismissChip(g,id,label){var c=edits.chips[g][id]||(edits.chips[g][id]={});c[label]={at:now(),by:me()};
  logIt("clear-chip",g,id,rowName(g,id),label);touch(KEY.edits);}


/* ---- CSV export: the host saves the file (a sandboxed frame cannot start a
        download itself); if the host does not answer, show the text to copy. */
var csvShown=false,csvTimer=null;
function csvText(){var q=function(v){v=String(v==null?"":v);return /[",\n]/.test(v)?'"'+v.replace(/"/g,'""')+'"':v;};
  var out=[["Group","Asset","Type","Live link","HubSpot link","Detail","Findings","QBS approved by","QBS approved at","Client approved by","Client approved at","Needs work by","Needs work at","Rev 1","Rev 2","Rev 3","Open comments","Comments","Note","Removed"].join(",")];
  GROUPS.forEach(function(g){rowsOf(g[0]).forEach(function(r){var s=statusOf(r.k,r.id);
    var cs=comments(r).map(function(c){return c.n+" ("+when(c.at)+(c.st==="done"?", resolved":"")+"): "+c.t+(c.re||[]).map(function(x){return " | reply "+x.n+": "+x.t;}).join("");}).join("\n");
    out.push([g[1],r.n,r.y||"",r.u||"",r.h||"",r.r||"",r.i.map(function(x){return x[1]+(x[2]?" — "+x[2]:"");}).join("; "),
      s.q?s.q.by:"",s.q?s.q.at:"",s.c?s.c.by:"",s.c?s.c.at:"",s.f?s.f.by:"",s.f?s.f.at:""].concat(REVS.map(function(k){var x=revOf(r,k);return x?"✓ "+x.by:"";})).concat([openCount(r),cs,r.note||"",r.deleted?"yes":""]).map(q).join(","));});});
  return out.join("\n");}
function exportCsv(){var name=(META.file||"asset-signoff")+"-"+new Date().toISOString().slice(0,10)+".csv";
  if(hosted){post({type:"download",name:name,mime:"text/csv",text:csvText()});
    clearTimeout(csvTimer);csvTimer=setTimeout(function(){csvShown=true;render();},1500);}
  else{csvShown=true;render();}}
/* Excel: xlsx-js-style is fetched on first use (CDN); the host saves the bytes.
   If the library or the host cannot, fall back to CSV. */
var XL=null;
function loadXlsx(cb){if(window.XLSX){cb(window.XLSX);return;}if(XL){XL.push(cb);return;}XL=[cb];
  var sc=document.createElement("script");sc.src="https://cdn.jsdelivr.net/npm/xlsx-js-style@1.2.0/dist/xlsx.bundle.js";
  var tm=setTimeout(function(){if(XL){XL=null;flag("Excel library did not load — sending CSV instead","err");exportCsv();}},9000);
  sc.onload=function(){clearTimeout(tm);var q=XL;XL=null;q.forEach(function(f){f(window.XLSX);});};
  sc.onerror=function(){clearTimeout(tm);XL=null;flag("Excel library did not load — sending CSV instead","err");exportCsv();};
  document.head.appendChild(sc);}
function xlsxBook(X){
  var H={font:{name:"Aptos",bold:true,color:{rgb:"FFFFFF"},sz:10},fill:{fgColor:{rgb:"1F2A44"}},alignment:{vertical:"center",wrapText:true},border:{bottom:{style:"thin",color:{rgb:"7A879E"}}}};
  var T={font:{name:"Aptos",bold:true,sz:16,color:{rgb:"1F2A44"}}};
  var S={font:{name:"Aptos",sz:10,color:{rgb:"5B6472"}}};
  var G={font:{name:"Aptos",bold:true,sz:10,color:{rgb:"1F2A44"}},fill:{fgColor:{rgb:"E7ECF3"}}};
  var B={font:{name:"Aptos",sz:10},alignment:{vertical:"top",wrapText:true},border:{bottom:{style:"hair",color:{rgb:"D9DEE6"}}}};
  var OK={font:{name:"Aptos",sz:10,bold:true,color:{rgb:"1E6B2E"}},fill:{fgColor:{rgb:"E3F3E6"}},alignment:{horizontal:"center",vertical:"top"},border:B.border};
  var NO={font:{name:"Aptos",sz:10,color:{rgb:"9A6100"}},fill:{fgColor:{rgb:"FBF1DA"}},alignment:{horizontal:"center",vertical:"top"},border:B.border};
  var BAD={font:{name:"Aptos",sz:10,bold:true,color:{rgb:"9B2C2C"}},fill:{fgColor:{rgb:"FBE5E2"}},alignment:{vertical:"top",wrapText:true},border:B.border};
  var LINK={font:{name:"Aptos",sz:10,color:{rgb:"1D4ED8"},underline:true},alignment:{vertical:"top"},border:B.border};
  function cell(v,st){return {v:v==null?"":v,t:typeof v==="number"?"n":"s",s:st};}
  function link(u,label){if(!u)return cell("",B);return {v:label||u,t:"s",l:{Target:u},s:LINK};}
  function stampTxt(x){return x?x.by+" · "+when(x.at):"";}
  var wb=X.utils.book_new();
  GROUPS.forEach(function(g){
    var rows=rowsOf(g[0]).filter(function(r){return !r.deleted;});
    var aoa=[[cell(META.title.toUpperCase()+" — "+g[1].toUpperCase(),T)],[cell((META.brandline||"")+"  |  exported "+new Date().toLocaleString()+"  |  Rev ticks and approvals as recorded in ClientCommand",S)],[],
      ["Asset","Type","Live","HubSpot editor",g[2]||"Detail","Rev 1","Rev 2","Rev 3","QBS approved","Client approved","Needs work","Findings","Open comments","Comments","Note"].map(function(h){return cell(h,H);})];
    var byType={};rows.forEach(function(r){(byType[r.y||"Other"]=byType[r.y||"Other"]||[]).push(r);});
    var types=Object.keys(byType).sort();var merges=[{s:{r:0,c:0},e:{r:0,c:14}},{s:{r:1,c:0},e:{r:1,c:14}}];
    types.forEach(function(ty){if(types.length>1){aoa.push([cell("▸  "+ty.toUpperCase(),G)].concat(Array(14).fill(cell("",G))));merges.push({s:{r:aoa.length-1,c:0},e:{r:aoa.length-1,c:14}});}
      byType[ty].forEach(function(r){var s=statusOf(r.k,r.id);var cs=comments(r);
        var rv=REVS.map(function(k){var x=revOf(r,k);return x?cell("✓",OK):cell("",B);});
        aoa.push([cell(r.n,B),cell(r.y||"",B),link(r.u,r.u?"Open":""),link(r.h,r.h?"Open in editor":""),cell(r.r||"",B)].concat(rv).concat([
          s.q?cell("✓ "+stampTxt(s.q),OK):cell("",NO),s.c?cell("✓ "+stampTxt(s.c),OK):cell("",NO),s.f?cell(stampTxt(s.f),BAD):cell("",B),
          cell(r.i.map(function(x){return x[1]+(x[2]?" — "+x[2]:"");}).join("\n"),r.i.some(function(x){return x[0]==="bad";})?BAD:B),
          cell(openCount(r),B),cell(cs.map(function(c){return c.n+" ("+when(c.at)+(c.st==="done"?", resolved":"")+"): "+c.t+(c.re||[]).map(function(x){return "\n   ↳ "+x.n+": "+x.t;}).join("");}).join("\n"),B),cell(r.note||"",B)]));});});
    var ws=X.utils.aoa_to_sheet(aoa);ws["!merges"]=merges;ws["!freeze"]={xSplit:1,ySplit:4};
    ws["!cols"]=[{wch:38},{wch:14},{wch:9},{wch:16},{wch:34},{wch:7},{wch:7},{wch:7},{wch:26},{wch:26},{wch:22},{wch:40},{wch:9},{wch:70},{wch:30}];
    ws["!rows"]=[{hpt:26},{hpt:16},{hpt:8},{hpt:22}];
    X.utils.book_append_sheet(wb,ws,g[1].slice(0,31));});
  var gc=comments(GEN);
  var ga=[[cell("GLOBAL NOTES & RULES",T)],[cell("Site-wide instructions from both sides",S)],[],["Who","Side","When","Source","Status","Note","Replies"].map(function(h){return cell(h,H);})];
  gc.forEach(function(c){ga.push([cell(c.n,B),cell(c.sd==="qbs"?"QBS":c.seed||c.sd==="client"?"Client":"",B),cell(when(c.at),B),cell(c.src||"",B),cell(c.st==="done"?"Resolved":"Open",c.st==="done"?OK:NO),cell(c.t,B),cell((c.re||[]).map(function(x){return x.n+": "+x.t;}).join("\n"),B)]);});
  var gs=X.utils.aoa_to_sheet(ga);gs["!cols"]=[{wch:22},{wch:8},{wch:16},{wch:22},{wch:10},{wch:90},{wch:50}];gs["!merges"]=[{s:{r:0,c:0},e:{r:0,c:6}},{s:{r:1,c:0},e:{r:1,c:6}}];gs["!freeze"]={ySplit:4};
  X.utils.book_append_sheet(wb,gs,"Global notes");
  var la=[[cell("ACTIVITY",T)],[cell("Who did what, most recent first",S)],[],["When","Who","Side","Action","Item","Detail"].map(function(h){return cell(h,H);})];
  log.e.slice().reverse().forEach(function(e){la.push([cell(when(e.at),B),cell(e.by,B),cell(e.sd==="qbs"?"QBS":e.sd==="client"?"Client":"",B),cell(ACT[e.a]||e.a,B),cell(e.n,B),cell(e.x||"",B)]);});
  var ls=X.utils.aoa_to_sheet(la);ls["!cols"]=[{wch:16},{wch:22},{wch:8},{wch:26},{wch:40},{wch:60}];ls["!merges"]=[{s:{r:0,c:0},e:{r:0,c:5}},{s:{r:1,c:0},e:{r:1,c:5}}];
  X.utils.book_append_sheet(wb,ls,"Activity");
  return wb;}
function exportXlsx(){if(!hosted){exportCsv();return;}flag("building the Excel file…");
  loadXlsx(function(X){try{var b64=X.write(xlsxBook(X),{bookType:"xlsx",type:"base64"});
    post({type:"download",name:(META.file||"asset-signoff")+"-"+new Date().toISOString().slice(0,10)+".xlsx",mime:"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",b64:b64});
    clearTimeout(csvTimer);csvTimer=setTimeout(function(){flag("the portal did not save the file — sending CSV instead","err");exportCsv();},2500);}
  catch(e){flag("Excel failed — "+(e&&e.message||"")+" — sending CSV","err");exportCsv();}});}

/* ---- view state (per viewer, never saved) ---------------------------------- */
var view={},open={},editing={},confirmDel={},sel={},showDel={},showLog=false,addOpen={},replyOpen={},collapsed={log:true};
function chev(g){return '<button class="chev" data-a="fold" data-g="'+g+'" aria-expanded="'+(!collapsed[g])+'" title="'+(collapsed[g]?"Expand":"Collapse")+'">'+(collapsed[g]?"▸":"▾")+"</button>";}
GK.forEach(function(g){view[g]={f:"all",q:"",y:""};sel[g]={};});
function E(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){
  return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];});}
function when(iso){if(!iso)return "";try{var d=new Date(iso);
  return d.toLocaleDateString(undefined,{day:"numeric",month:"short"})+" "+d.toLocaleTimeString(undefined,{hour:"2-digit",minute:"2-digit"});}catch(e){return "";}}
function matches(r,v){var s=statusOf(r.k,r.id);
  if(v.q){var hay=(r.n+" "+(r.r||"")+" "+(r.t||"")+" "+(r.y||"")+" "+(r.note||"")+" "+r.i.map(function(x){return x[1]+" "+(x[2]||"");}).join(" ")
    +" "+comments(r).map(function(c){return c.t+" "+c.n;}).join(" ")).toLowerCase();if(hay.indexOf(v.q)<0)return false;}
  if(v.y&&(r.y||"")!==v.y)return false;
  switch(v.f){case "all":return true;case "todo":return !s.q&&!s.c&&!s.f;case "qbs":return !!s.q;case "client":return !!s.c;
    case "both":return !!s.q&&!!s.c;case "fix":return !!s.f;case "open":return openCount(r)>0;
    case "issue":return r.i.some(function(x){return x[0]==="bad"||x[0]==="warn";});case "changed":return !!(r.edited||r.added);}
  return true;}
var FILTERS=[["all","All"],["todo","Not reviewed"],["qbs","QBS approved"],["client","Client approved"],["both","Fully approved"],
  ["fix","Needs work"],["open","Open comments"],["issue","Has a finding"],["changed","Edited here"]];
var ACT={"qbs-approve":"QBS approved","qbs-unapprove":"removed QBS approval","client-approve":"Client approved",
  "client-unapprove":"removed client approval","needs-work":"marked needs work","clear-flag":"cleared needs work",
  "comment":"commented on","reply":"replied on","resolve-comment":"resolved a comment on","reopen-comment":"reopened a comment on",
  "edit":"edited","add":"added","delete":"removed","restore":"restored","clear-chip":"cleared a finding on",
  "rev-tick":"ticked a revision on","rev-clear":"cleared a revision on"};

/* ---- rendering -------------------------------------------------------------- */
/* Column widths per group (px); the checkbox column is fixed. Draggable. */
var COLS=[["ck",40],["nm",270],["lk",160],["ev",200],["st",210],["rvs",150],["act",380]];
var colw={};GK.forEach(function(g){colw[g]=COLS.map(function(c){return c[1];});});
var hostv2=false;                        /* host answered whoami → new viewer build */
function stampHtml(lbl,s,k){if(!s)return "";
  return '<span class="by '+k+'">'+lbl+" · <b>"+when(s.at)+"</b> · "+E(s.by)+"</span>";}
function linkHtml(r){var h="";
  if(r.u)h+='<a class="lnk" href="'+E(r.u)+'" target="_blank" rel="noopener">Live ↗</a>';
  if(r.h)h+='<a class="lnk hs" href="'+E(r.h)+'" target="_blank" rel="noopener">HubSpot ↗</a>';
  return h||'<span class="dim">—</span>';}
function chipsHtml(r){
  var chips=r.i.map(function(x){return '<span class="chip c-'+x[0]+'"'+(x[2]?' title="'+E(x[2])+'"':"")+'>'+E(x[1])
    +(r.gen&&!r.deleted?'<button class="x" data-a="chip" data-l="'+E(x[1])+'" aria-label="clear">×</button>':"")+"</span>";}).join("");
  if(r.new)chips='<span class="chip c-ok">new — no original</span>'+chips;
  if(r.added)chips='<span class="chip c-acc">added by '+E(r.by||"")+"</span>"+chips;
  return chips||'<span class="chip c-acc">clear</span>';}
function revsHtml(r){if(r.deleted)return "<td></td>";
  return '<td class="rvs"><span class="revs">'+REVS.map(function(k){var st=revOf(r,k);
    return '<button class="rvb" data-a="rev" data-k="'+k+'" aria-pressed="'+(!!st)+'" title="'+(st?"Rev "+k.slice(1)+" · "+E(st.by)+" · "+when(st.at):"Tick revision "+k.slice(1))+'">R'+k.slice(1)+(st?" ✓":"")+"</button>";}).join("")
    +(r.rs?'<span class="chip c-warn" title="Design Approval Sheet v6">'+E(r.rs)+"</span>":"")+"</span></td>";}
function rowHtml(r){
  var s=statusOf(r.k,r.id),oc=openCount(r),cc=comments(r).length,k=r.k+":"+r.id;
  var cls2="r"+(s.q&&s.c?" done":"")+(s.f?" flag":"")+(r.deleted?" gone":"")+(sel[r.k][r.id]?" sel":"");
  var nm='<td class="nm stk2" title="Double-click a value to edit it"><span class="ttl" data-f="n">'+E(r.n)+"</span>"+(r.y?'<span class="ty" data-f="y">'+E(r.y)+"</span>":'<span class="ty ghost" data-f="y">+ type</span>')
    +(r.note?'<span class="nt" data-f="note">'+E(r.note)+"</span>":'<span class="nt ghost" data-f="note">+ note</span>')
    +(s.q||s.c||s.f?"<div>"+stampHtml("QBS",s.q,"q")+stampHtml("Client",s.c,"c")+stampHtml("Needs work",s.f,"f")+"</div>":"")+"</td>";
  var rv=r.deleted?'<td class="act"><button class="gh" data-a="restore">Restore</button></td>'
    :'<td class="act"><span class="rv">'
      +'<button class="ok" data-a="q" aria-pressed="'+(!!s.q)+'"'+(locked("q")?' disabled title="QBS side only"':"")+'>QBS ✓</button>'
      +'<button class="ok cl" data-a="c" aria-pressed="'+(!!s.c)+'"'+(locked("c")?' disabled title="Client side only"':"")+'>Client ✓</button>'
      +'<button class="fix" data-a="f" aria-pressed="'+(!!s.f)+'">Needs work</button></span>'
      +'<button class="cm'+(oc?" has":cc?" all":"")+'" data-a="cm">'+(cc?(oc?"<b>"+oc+"</b> open":"resolved")+" · "+cc:"Comment")+"</button>"
      +'<button class="gh mini" data-a="edit" title="Edit this row">Edit</button>'
      +(confirmDel[k]?'<span class="del"><span>Remove?</span><button class="danger" data-a="delyes">Yes</button><button class="gh mini" data-a="delno">No</button></span>'
        :'<button class="gh mini" data-a="del" title="Remove this row">✕</button>')+"</td>";
  var h='<tr class="'+cls2+'" data-g="'+r.k+'" data-i="'+E(r.id)+'">'
    +'<td class="ck stk1"><input type="checkbox" data-a="sel"'+(sel[r.k][r.id]?" checked":"")+' aria-label="select"></td>'
    +nm+'<td class="lk">'+linkHtml(r)+"</td>"
    +'<td class="ev" data-f="r"'+(r.t?' title="'+E(r.t)+'"':' title="Double-click to edit"')+">"+(r.r?(/^[\w.-]+\.[a-z]{2,}(\/|$)/i.test(r.t||r.r)?'<a class="old" href="https://'+E(r.t||r.r)+'" target="_blank" rel="noopener" title="Open the old asset">'+E(r.r)+" ↗</a>":E(r.r)):'<span class="dim">—</span>')+"</td>"
    +"<td>"+chipsHtml(r)+"</td>"+revsHtml(r)+rv+"</tr>";
  if(editing[k])h+=editHtml(r);
  if(open[k])h+=threadHtml(r);
  return h;}
function formHtml(r,g,ok,cancel,label,extra){var col=GROUPS.filter(function(x){return x[0]===g;})[0][2]||"Detail";
  return '<div class="form"><label>Name<input data-f="n" value="'+E(r.n||"")+'"></label>'
  +'<label>Type / category<input data-f="y" value="'+E(r.y||"")+'"></label>'
  +'<label>Live link<input data-f="u" value="'+E(r.u||"")+'" placeholder="https://"></label>'
  +'<label>HubSpot link<input data-f="h" value="'+E(r.h||"")+'" placeholder="https://app.hubspot.com/…"></label>'
  +'<label class="wide">'+E(col)+'<input data-f="r" value="'+E(r.r||"")+'"></label>'
  +'<label class="wide">Note<input data-f="note" value="'+E(r.note||"")+'"></label>'
  +'<div class="row"><button data-a="'+ok+'" data-g="'+g+'">'+label+'</button><button class="gh" data-a="'+cancel+'" data-g="'+g+'">Cancel</button>'+(extra||"")+"</div></div>";}
function lastEdit(r){var b={at:"",by:""};for(var f in r.edited)if(later(r.edited[f],b))b=r.edited[f];return b;}
function editHtml(r){return '<tr class="th ed" data-g="'+r.k+'" data-i="'+E(r.id)+'"><td colspan="7">'
  +formHtml(r,r.k,"savedit","canceledit","Save changes",r.edited?'<span class="dim">last edited by '+E(lastEdit(r).by)+" · "+when(lastEdit(r).at)+"</span>":"")+"</td></tr>";}
function sideCls(c){return c.sd==="qbs"?"qbs":(c.sd==="client"||c.seed)?"client":"";}
function threadHtml(r){
  var finds=r.i.filter(function(x){return x[2];}).map(function(x){return '<li><span class="chip c-'+x[0]+'">'+E(x[1])+"</span>"+E(x[2])+"</li>";}).join("");
  var list=comments(r).map(function(c){return cmtHtml(r,c);}).join("");
  if(!list)list='<p class="empty">No comments on this item yet.</p>';
  var hist=log.e.filter(function(e){return e.g===r.k&&e.i===r.id;}).slice(-12).reverse().map(function(e){
    return '<li>'+E(e.by)+" "+E(ACT[e.a]||e.a)+(e.x?': <span>'+E(e.x)+"</span>":"")+' <time>'+when(e.at)+"</time></li>";}).join("");
  return '<tr class="th" data-g="'+r.k+'" data-i="'+E(r.id)+'"><td colspan="7"><div class="panel">'
    +'<div class="card thread"><h4>Comments · '+comments(r).length+"</h4>"+list
    +'<textarea data-a="txt" aria-label="Comment" placeholder="Add a comment about '+E(r.n)+'…"></textarea>'
    +'<div class="row"><button data-a="post">Post comment</button><button class="gh" data-a="close">Close</button></div></div>'
    +'<div><div class="card finds"><h4>Findings — where and what</h4>'+(finds?"<ul>"+finds+"</ul>":'<p class="empty">Nothing outstanding on this item.</p>')+"</div>"
    +'<div class="card hist" style="margin-top:12px"><h4>History</h4>'+(hist?"<ul>"+hist+"</ul>":'<p class="empty">No activity yet.</p>')+"</div></div>"
    +"</div></td></tr>";}
function tally(rows){var t={q:0,c:0,both:0,f:0,todo:0,n:0};rows.forEach(function(r){if(r.deleted)return;t.n++;var s=statusOf(r.k,r.id);
  if(s.q)t.q++;if(s.c)t.c++;if(s.q&&s.c)t.both++;if(s.f)t.f++;if(!s.q&&!s.c&&!s.f)t.todo++;});return t;}
function barHtml(t){var n=t.n||1;return '<i class="a" style="width:'+(t.both/n*100).toFixed(1)+'%"></i><i class="q" style="width:'+((t.q-t.both)/n*100).toFixed(1)+'%"></i><i class="c" style="width:'+((t.c-t.both)/n*100).toFixed(1)+'%"></i><i class="f" style="width:'+(t.f/n*100).toFixed(1)+'%"></i>';}
function selCount(g){var n=0;for(var k in sel[g])if(sel[g][k])n++;return n;}
function groupHtml(g){var gk=g[0],rows=rowsOf(gk),v=view[gk];
  var live=rows.filter(function(r){return !r.deleted;}),delN=rows.length-live.length;
  var base=showDel[gk]?rows:live,shown=base.filter(function(r){return matches(r,v);});
  var t=tally(rows),types=[];live.forEach(function(r){if(r.y&&types.indexOf(r.y)<0)types.push(r.y);});types.sort();
  var btns=FILTERS.map(function(f){return '<button class="f" data-g="'+gk+'" data-f="'+f[0]+'" aria-pressed="'+(v.f===f[0])+'">'+E(f[1])+"</button>";}).join("");
  var tsel=types.length>1?'<select data-g="'+gk+'" data-a="type" aria-label="Type"><option value="">All types</option>'+types.map(function(y){return '<option'+(v.y===y?" selected":"")+">"+E(y)+"</option>";}).join("")+"</select>":"";
  var ns=selCount(gk);
  var bulk=ns?'<div class="bulk"><b>'+ns+" selected</b>"
    +'<button data-a="bq"'+(locked("q")?" disabled":"")+'>QBS approve</button><button data-a="bc"'+(locked("c")?" disabled":"")+'>Client approve</button>'
    +'<button data-a="bf">Needs work</button><button class="gh" data-a="bclear">Clear review</button><button class="gh" data-a="bdel">Remove</button>'
    +'<button class="gh" data-a="bnone">Deselect</button></div>':"";
  var addf=addOpen[gk]?formHtml({},gk,"addsave","addcancel","Add to "+E(g[1])):"";
  var w=colw[gk],cols='<colgroup>'+w.map(function(x){return '<col style="width:'+x+'px">';}).join("")+"</colgroup>";
  var heads=[["ck",'<input type="checkbox" data-a="selall" aria-label="select all shown"'+(shown.length&&shown.every(function(r){return sel[gk][r.id];})?" checked":"")+'>'],
    ["nm","Asset · approvals"],["lk","Links"],["ev",E(g[2]||"Detail")],["st","Status"],["rvs","Revisions"],["act","Review"]];
  var thead=heads.map(function(h,i){return '<th class="'+h[0]+(i===0?" stk1":i===1?" stk2":"")+'">'+h[1]+(i?'<span class="rz" data-c="'+i+'" title="Drag to resize"></span>':"")+"</th>";}).join("");
  var body=collapsed[gk]?"":addf
    +'<div class="filters"><label class="srch"><input type="search" data-g="'+gk+'" value="'+E(v.q)+'" placeholder="Search…" aria-label="Search '+E(g[1])+'"></label>'+tsel+btns
    +'<span class="count">'+shown.length+" of "+live.length+"</span></div>"+bulk
    +'<div class="tscroll"><table style="min-width:'+w.reduce(function(a,b){return a+b;},0)+'px">'+cols+"<thead><tr>"+thead+"</tr></thead><tbody>"
    +(shown.length?shown.map(rowHtml).join(""):'<tr class="r"><td colspan="7" class="ev">Nothing matches.</td></tr>')+"</tbody></table></div>";
  return '<section class="grp'+(collapsed[gk]?" folded":"")+'" id="g-'+gk+'" data-g="'+gk+'"><div class="shead"><div class="hrow">'+chev(gk)+'<h2>'+E(g[1])+'</h2>'
    +'<span class="tct">'+t.both+" / "+t.n+" fully approved</span></div>"
    +'<div class="acts"><button class="gh" data-a="addopen" data-g="'+gk+'">+ Add a row</button>'
    +(delN?'<button class="gh" data-a="showdel" data-g="'+gk+'">'+(showDel[gk]?"Hide":"Show")+" "+delN+" removed</button>":"")+"</div>"
    +'<p class="eyebrow" style="grid-column:1/-1;margin:0">'+t.q+" QBS · "+t.c+" client · "+t.f+" need work · "+t.todo+" not yet reviewed</p>"
    +'<div class="gbar">'+barHtml(t)+"</div></div>"+body+"</section>";}
var showAbout=false;
function cmtHtml(r,c){var re=(c.re||[]).map(function(x){return '<div class="re"><div class="who"><span class="nm2">'+E(x.n)+"</span>"+(x.sd?"<span>"+(x.sd==="qbs"?"QBS":"client")+"</span>":"")+"<span>"+when(x.at)+'</span></div><div class="txt">'+E(x.t)+"</div></div>";}).join("");
  var rk=r.k+":"+r.id+":"+c.id;
  return '<div class="cmt '+sideCls(c)+(c.st==="done"?" done":"")+'" data-c="'+E(c.id)+'"><div class="who"><span class="nm2">'+E(c.n)+"</span>"+(c.sd?"<span>"+(c.sd==="qbs"?"QBS":"client")+"</span>":"")+"<span>"+when(c.at)+"</span>"
    +(c.src?'<em>'+E(c.src)+"</em>":"")+(c.st==="done"?'<b>resolved by '+E(c.rs&&c.rs.by||"")+" "+when(c.rs&&c.rs.at)+"</b>":"")+"</div>"
    +'<div class="txt">'+E(c.t)+"</div>"+re
    +'<div class="cact">'+(c.st==="done"?'<button class="gh mini" data-a="reopen">Reopen</button>':'<button class="mini ok2" data-a="resolve">Resolve ✓</button>')
    +'<button class="gh mini" data-a="reply">Reply</button></div>'
    +(replyOpen[rk]?'<div class="replybox"><textarea data-a="rtxt" placeholder="Reply…"></textarea><div class="row"><button class="mini" data-a="rpost">Post reply</button><button class="gh mini" data-a="rcancel">Cancel</button></div></div>':"")
    +"</div>";}

function genHtml(){var cs=comments(GEN),open_=cs.filter(function(c){return c.st!=="done";}).length;
  return '<section class="gensec" id="g-general"><div class="shead"><div class="hrow">'+chev("_")+'<h2>Global notes &amp; rules</h2><span class="tct">'+open_+" open · "+cs.length+"</span></div>"
    +'<div class="acts"></div>'
    +'<p class="eyebrow" style="grid-column:1/-1;margin:0">Site-wide instructions and anything that is not about one asset — both sides can post, reply and resolve</p></div>'
    +(!collapsed._?'<div class="gen card thread" data-g="_" data-i="general">'+(cs.length?cs.map(function(c){return cmtHtml(GEN,c);}).join(""):'<p class="empty">Nothing here yet.</p>')
      +'<textarea data-a="txt" aria-label="Global note" placeholder="Add a site-wide note, rule or change…"></textarea><div class="row"><button data-a="post">Post</button></div></div>':"")+"</section>";}
function logHtml(){var es=log.e.slice(-60).reverse();
  return '<section class="logsec" id="g-log"><div class="shead"><div class="hrow">'+chev("log")+'<h2>Activity</h2><span class="tct">'+log.e.length+" actions</span></div>"
    +'<div class="acts"></div></div>'
    +(!collapsed.log?(es.length?'<ul class="log">'+es.map(function(e){return "<li><b>"+E(e.by)+"</b>"+(e.sd?' <i>'+(e.sd==="qbs"?"QBS":"client")+"</i>":"")+" "+E(ACT[e.a]||e.a)+" <em>"+E(e.n)+"</em>"
      +(e.x?': <span>'+E(e.x)+"</span>":"")+"<time>"+when(e.at)+"</time></li>";}).join("")+"</ul>":'<p class="empty">Nothing recorded yet.</p>'):"")+"</section>";}
function headerHtml(){var all=[];GK.forEach(function(g){all=all.concat(rowsOf(g));});var t=tally(all);
  var nav='<a href="#g-general"><i></i>Global <b>'+comments(GEN).filter(function(c){return c.st!=="done";}).length+"</b></a>"+GROUPS.map(function(g){var tt=tally(rowsOf(g[0]));var st=tt.n&&tt.both===tt.n?" done":(tt.both||tt.q||tt.c?" part":"");
    return '<a class="'+st+'" href="#g-'+g[0]+'"><i></i>'+E(g[1])+" <b>"+tt.both+"/"+tt.n+"</b></a>";}).join("");
  var ident=user&&user.name?'<span class="me">Signed in as <b>'+E(user.name)+"</b>"+(side?'<span class="side">'+(side==="qbs"?"QBS":"Client")+"</span>":"")+"</span>"
    :'<label for="who">Your name</label><input id="who" value="'+E(who)+'" placeholder="Type your name" autocomplete="name">'
     +'<span class="sideg"><button class="sd" data-s="qbs" aria-pressed="'+(side==="qbs")+'">I am QBS</button><button class="sd" data-s="client" aria-pressed="'+(side==="client")+'">I am the client</button></span>';
  function tile(c,n,l){return '<div class="stat '+c+'"><span class="n">'+n+'</span><span class="l">'+l+"</span></div>";}
  return '<header class="top"><div class="wrap"><div class="hrow">'
    +'<p class="brandline"><span class="dot"></span><span>'+E(META.brandline||"")+"</span></p>"
    +'<span class="tools"><button class="gh" data-a="refresh">↻ Refresh</button><button class="gh" data-a="xlsx">↓ Excel</button>'
    +(hostv2?'<button class="gh" data-a="full">⤢ Full screen</button>':"")+"</span></div>"
    +'<div class="hrow"><h1>'+E(META.title)+'</h1><button class="gh mini" data-a="about">'+(showAbout?"Hide help":"How this works")+"</button></div>"+(META.intro&&showAbout?'<p class="lede">'+E(META.intro)+"</p>":"")
    +'<div class="stats">'+tile("a",t.both,"Fully approved")+tile("q",t.q,"QBS approved")+tile("c",t.c,"Client approved")+tile("f",t.f,"Needs work")+tile("u",t.todo,"Not reviewed")+tile("t",t.n,"Assets")+"</div>"
    +'<div class="prog">'+barHtml(t)+"</div>"
    +'<div class="idbar'+(hosted?"":" ro")+(needSide&&!side?" attn":"")+'" id="idbar">'+(user&&user.name?"":'<span class="step">'+(needSide&&!side?"First, tell the sheet who you are":"Who are you?")+"</span>")+ident
    +(hosted?"":'<span class="dim">Not inside the portal — nothing will save.</span>')+"</div>"
    +(META.share?'<div class="share-row"><span>Client share link (no login):</span><input class="share" readonly value="'+E(META.share)+'" onclick="this.select()"></div>':"")
    +(csvShown?'<div class="csvbox"><p class="note">Your browser could not save the file from here — select all and copy this into a spreadsheet. <button class="gh mini" data-a="csvclose">Close</button></p><textarea readonly onclick="this.select()">'+E(csvText())+"</textarea></div>":"")
    +'<p class="note">'+E(META.note||"")+" Asset list refreshed from HubSpot "+E(META.stamp)+".</p>"
    +'</div></header><div class="wrap"><div class="navbar"><div class="navin"><nav class="jump">'+nav+'</nav><span class="save '+cls+'" id="save">'+E(msg)+"</span></div></div>"
    +genHtml()+GROUPS.map(groupHtml).join("")+logHtml()+"</div>";}
function fitPanels(){[].forEach.call(document.querySelectorAll(".tscroll"),function(sc){
  var w=sc.clientWidth-36;[].forEach.call(sc.querySelectorAll(".panel,.form"),function(p){p.style.width=w+"px";});});}
window.addEventListener("resize",fitPanels);
function render(){var y=window.scrollY,ae=document.activeElement,focusId=ae&&ae.id,pos=ae&&ae.selectionStart;
  document.getElementById("root").innerHTML=headerHtml();window.scrollTo(0,y);fitPanels();
  if(focusId){var el=document.getElementById(focusId);if(el){el.focus();try{el.setSelectionRange(pos,pos);}catch(e){}}}}

var root=document.getElementById("root");
/* ---- inline editing: double-click a value, Enter saves, Esc cancels --------- */
var inl=null;
root.addEventListener("dblclick",function(ev){
  var cell=ev.target.closest("[data-f]");if(!cell||cell.tagName==="INPUT")return;
  var tr=cell.closest("tr.r");if(!tr||tr.classList.contains("gone"))return;
  var g=tr.dataset.g,id=tr.dataset.i,f=cell.dataset.f,r=findRow(g,id);if(!r)return;
  if(inl)finishInline(false);
  var cur=r[f]||"";var inp=document.createElement("input");inp.className="inl";inp.value=cur;inp.dataset.f=f;
  inp.setAttribute("aria-label","Edit "+f);cell.innerHTML="";cell.appendChild(inp);cell.classList.add("editing");
  inl={g:g,id:id,f:f,el:inp,cell:cell};inp.focus();inp.select();
  window.getSelection&&window.getSelection().removeAllRanges&&inp.select();
});
function finishInline(save){if(!inl)return;var x=inl;inl=null;
  if(save){var o={};o[x.f]=x.el.value;editRow(x.g,x.id,o);}render();}
root.addEventListener("keydown",function(ev){if(!inl||ev.target!==inl.el)return;
  if(ev.key==="Enter"){ev.preventDefault();finishInline(true);}else if(ev.key==="Escape"){finishInline(false);}});
root.addEventListener("focusout",function(ev){if(inl&&ev.target===inl.el)setTimeout(function(){if(inl&&inl.el===ev.target)finishInline(true);},0);});

/* ---- column resizing (per viewer, in memory) ------------------------------- */
var rz=null;
document.addEventListener("mousedown",function(ev){var h=ev.target.closest(".rz");if(!h)return;
  var sec=h.closest("section[data-g]"),g=sec.dataset.g,c=+h.dataset.c;
  rz={g:g,c:c,x:ev.clientX,w:colw[g][c],table:sec.querySelector("table")};document.body.classList.add("resizing");ev.preventDefault();});
document.addEventListener("mousemove",function(ev){if(!rz)return;
  var w=Math.max(70,rz.w+ev.clientX-rz.x);colw[rz.g][rz.c]=w;
  var col=rz.table.querySelectorAll("col")[rz.c];if(col)col.style.width=w+"px";
  rz.table.style.minWidth=colw[rz.g].reduce(function(a,b){return a+b;},0)+"px";});
document.addEventListener("mouseup",function(){if(rz){rz=null;document.body.classList.remove("resizing");}});

/* ---- events -------------------------------------------------------------- */
function fields(scope){var o={};[].forEach.call(scope.querySelectorAll("input[data-f]"),function(i){o[i.dataset.f]=i.value;});return o;}
root.addEventListener("click",function(ev){
  var b=ev.target.closest("button");if(!b)return;var a=b.dataset.a;
  if(b.classList.contains("f")){view[b.dataset.g].f=b.dataset.f;render();return;}
  if(b.classList.contains("sd")){side=b.dataset.s;needSide=false;render();return;}
  if(a==="refresh"){refresh();flag("refreshing…");return;}
  if(a==="full"){post({type:"fullscreen"});return;}
  if(a==="csv"){exportCsv();return;}
  if(a==="xlsx"){exportXlsx();return;}
  if(a==="csvclose"){csvShown=false;render();return;}
  if(a==="fold"){collapsed[b.dataset.g]=!collapsed[b.dataset.g];render();return;}
  if(a==="togglegen"){showGen=!showGen;render();return;}
  if(a==="about"){showAbout=!showAbout;render();return;}
  if(a==="addopen"){addOpen[b.dataset.g]=true;render();return;}
  if(a==="addcancel"){addOpen[b.dataset.g]=false;render();return;}
  if(a==="addsave"){var g0=b.dataset.g;addRow(g0,fields(b.closest(".form")));addOpen[g0]=false;render();return;}
  if(a==="showdel"){showDel[b.dataset.g]=!showDel[b.dataset.g];render();return;}
  var sec=b.closest("section[data-g]");
  if(a&&a.charAt(0)==="b"&&sec){var g=sec.dataset.g,ids=Object.keys(sel[g]).filter(function(k){return sel[g][k];});
    if(a==="bnone"){sel[g]={};render();return;}
    if(!side&&(a==="bq"||a==="bc"||a==="bf")){askSide();return;}
    ids.forEach(function(id){var it=item(g,id),s=statusOf(g,id);
      if(a==="bq"&&!s.q&&can("q"))setStatus(g,id,"q");
      else if(a==="bc"&&!s.c&&can("c"))setStatus(g,id,"c");
      else if(a==="bf"&&!s.f)setStatus(g,id,"f");
      else if(a==="bclear"){["q","c","f"].forEach(function(k){if(stat(it,k))it[k]={at:now(),by:me(),x:1};});logIt("clear-flag",g,id,rowName(g,id),"cleared all");touch(gkey(g));}
      else if(a==="bdel")delRow(g,id);});
    sel[g]={};render();return;}
  var tr=b.closest("tr,.gen");if(!tr)return;var g=tr.dataset.g,id=tr.dataset.i,k=g+":"+id;
  if(a==="q"||a==="c"||a==="f"){setStatus(g,id,a);render();return;}
  if(a==="rev"){setRev(g,id,b.dataset.k);render();return;}
  if(a==="cm"){open[k]=!open[k];render();if(open[k]){var ta=root.querySelector('tr.th[data-g="'+g+'"][data-i="'+id+'"] textarea[data-a=txt]');if(ta)ta.focus();}return;}
  if(a==="close"){open[k]=false;render();return;}
  if(a==="post"){var box=tr.querySelector("textarea[data-a=txt]");if(box&&box.value.trim()){addComment(g,id,box.value);render();}return;}
  if(a==="edit"){editing[k]=!editing[k];render();return;}
  if(a==="canceledit"){editing[k]=false;render();return;}
  if(a==="savedit"){editRow(g,id,fields(tr));editing[k]=false;render();return;}
  if(a==="del"){confirmDel[k]=true;render();return;}
  if(a==="delno"){confirmDel[k]=false;render();return;}
  if(a==="delyes"){confirmDel[k]=false;delRow(g,id);render();return;}
  if(a==="restore"){delRow(g,id,true);render();return;}
  if(a==="chip"){dismissChip(g,id,b.dataset.l);render();return;}
  var cm=b.closest(".cmt");if(cm){var cid=cm.dataset.c,rk=k+":"+cid;
    if(a==="resolve"){resolveComment(g,id,cid,true);render();return;}
    if(a==="reopen"){resolveComment(g,id,cid,false);render();return;}
    if(a==="reply"){replyOpen[rk]=true;render();var rt=root.querySelector('.cmt[data-c="'+cid+'"] textarea');if(rt)rt.focus();return;}
    if(a==="rcancel"){replyOpen[rk]=false;render();return;}
    if(a==="rpost"){var rb=cm.querySelector("textarea");if(rb&&rb.value.trim()){replyTo(g,id,cid,rb.value);replyOpen[rk]=false;render();}return;}}
});
root.addEventListener("change",function(ev){var t=ev.target;
  if(t.dataset.a==="sel"){var tr=t.closest("tr");sel[tr.dataset.g][tr.dataset.i]=t.checked;render();return;}
  if(t.dataset.a==="selall"){var sec=t.closest("section"),g=sec.dataset.g;
    [].forEach.call(sec.querySelectorAll("tbody tr.r"),function(tr){sel[g][tr.dataset.i]=t.checked;});render();return;}
  if(t.dataset.a==="type"){view[t.dataset.g].y=t.value;render();}
});
root.addEventListener("input",function(ev){var t=ev.target;
  if(t.id==="who"){who=t.value.trim();return;}
  if(t.type==="search"){var g=t.dataset.g,pos=t.selectionStart;view[g].q=t.value.trim().toLowerCase();render();
    var again=root.querySelector('input[type=search][data-g="'+g+'"]');if(again){again.focus();try{again.setSelectionRange(pos,pos);}catch(e){}}}
});
root.addEventListener("keydown",function(ev){
  if(ev.key==="Enter"&&(ev.metaKey||ev.ctrlKey)&&ev.target.tagName==="TEXTAREA"){var tr=ev.target.closest("tr,.gen");
    if(tr&&ev.target.dataset.a==="txt"){addComment(tr.dataset.g,tr.dataset.i,ev.target.value);render();}}
});

/* ---- boot ---------------------------------------------------------------- */
render();
if(hosted){refresh();post({type:"whoami"});setInterval(function(){if(!Object.keys(dirty).length)refresh();},25000);}
})();
