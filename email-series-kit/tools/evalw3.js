const {chromium}=require('playwright');const fs=require('fs');
const dir=process.argv[2];
(async()=>{const b=await chromium.launch();
const files=fs.readdirSync(dir).filter(f=>f.endsWith('.html'));
const out={};
for(const [w,tag] of [[700,'d'],[375,'m']]){
 const p=await b.newPage({viewport:{width:w,height:900}});
 for(const f of files){
  await p.goto('file://'+process.cwd()+'/'+dir+'/'+f,{waitUntil:'networkidle',timeout:60000}).catch(()=>{});
  await p.addStyleTag({content:'*{text-wrap:wrap !important}'});
  const r=await p.evaluate(()=>{
    const res={};
    [...document.querySelectorAll('td.hs_padded')].forEach((td,mi)=>{
      const els=[...td.querySelectorAll('.hs_cos_wrapper_type_rich_text p, .hs_cos_wrapper_type_rich_text h1')];
      els.forEach((el,ei)=>{
        const st=el.getAttribute('style')||'';
        if(/letter-spacing:1\.[56]px/.test(st))return;
        const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT);const words=[];let n;let broken=false;
        while(n=walker.nextNode()){
          if(n.parentElement.closest('span[style*="border-radius:100px"]'))continue;
          const t=n.textContent;const re=/\S+/g;let m;
          while(m=re.exec(t)){const rg=document.createRange();rg.setStart(n,m.index);rg.setEnd(n,m.index+m[0].length);const rcs=rg.getClientRects();if(rcs.length>1)broken=true;const rc=rcs[0];if(rc)words.push({top:Math.round(rc.top),right:rc.right});}
        }
        if(words.length<4)return;
        const tops=[...new Set(words.map(x=>x.top))].sort((a,b)=>a-b);
        const perLine=tops.map(t=>words.filter(x=>x.top===t).length);const shortLines=perLine.filter(n=>n<=2).length;
        const tdr=td.getBoundingClientRect();
        const over=Math.max(...words.map(x=>x.right))>tdr.right-(parseFloat(getComputedStyle(td).paddingRight)||0)+1;
        res[mi+'|'+ei]=(broken||over)?100:((tops.length>1)?shortLines:0);
      });
    });return res;});
  (out[f.replace('.html','')]=out[f.replace('.html','')]||{})[tag]=r;
 }
 await p.close();
}
fs.writeFileSync(dir+'_short.json',JSON.stringify(out));
await b.close();})();
