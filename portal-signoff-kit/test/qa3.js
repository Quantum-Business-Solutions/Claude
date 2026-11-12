const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1100,height:900}});
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.cwd()+'/host.html');await p.waitForTimeout(900);
const f=p.frameLocator('#f');const R=[];const ck=(n,ok,x)=>R.push((ok?'PASS ':'FAIL ')+n+(x!==undefined?' '+x:''));
const c=f.locator('#c-w-home');await c.locator('summary').click();
const n=await c.locator('.faq').count();
await c.locator('.faq').nth(0).locator('[data-d=ok]').click();await p.waitForTimeout(300);
ck('card stays open',await c.evaluate(e=>e.open));
await c.locator('.faq').nth(1).locator('[data-d=no]').click();await p.waitForTimeout(300);
ck('removed marks',await c.locator('.faq.rm').count()===1);
ck('kept tag',(await c.locator('summary').textContent()).includes('1 of '+n+' kept'),(await c.locator('summary .tag').allTextContents()).join('|'));
for(let i=2;i<n;i++)await c.locator('.faq').nth(i).locator('[data-d=ok]').click();
await p.waitForTimeout(400);
ck('auto approved when all decided',(await c.locator('summary .tag').last().textContent())==='Approved',(await c.locator('summary .tag').allTextContents()).join('|'));
// page approve on fresh card: all kept
const c2=f.locator('#c-w-pricing');await c2.locator('summary').click();await c2.locator('[data-a=ok]').click();await p.waitForTimeout(400);
await c2.locator('summary').click();await p.waitForTimeout(200);
ck('page approve keeps all',await c2.locator('.faq.kp').count()>0,await c2.locator('.faq.kp').count());
// remove one after page approve -> others stay kept
await c2.locator('.faq').nth(0).locator('[data-d=no]').click();await p.waitForTimeout(400);
ck('after remove others kept',(await c2.locator('.faq.kp').count())===(await c2.locator('.faq').count())-1,await c2.locator('.faq.kp').count());
ck('stored d',JSON.stringify(await p.evaluate(()=>window.__store['faq:w-pricing'])).includes('"no"'));
await c2.locator('.faq').nth(1).locator('.fnote').fill('Please soften this');await p.waitForTimeout(1400);ck('faq note saved',JSON.stringify(await p.evaluate(()=>window.__store['faq:w-pricing'])).includes('soften'));await p.screenshot({path:'q3.png'});
console.log(R.join('\n'),'\nerrors',errs);await b.close()})();
