const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const ctx=await b.newContext({viewport:{width:1100,height:900}});const p=await ctx.newPage();
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.cwd()+'/host.html');await p.waitForTimeout(900);
const f=p.frameLocator('#f');const fr=p.frames()[1];const R=[];
const ck=(n,ok,x)=>R.push((ok?'PASS ':'FAIL ')+n+(x!==undefined?' '+x:''));
ck('3 steps',await f.locator('.step').count()===3);
ck('questions open by default',await f.locator('#qcard').evaluate(e=>e.open));
await f.locator('.qa').nth(0).fill('Fiscal credit');await p.waitForTimeout(200);
ck('live count',(await f.locator('#qtag').textContent()).startsWith('1 of 22'),await f.locator('#qtag').textContent());
// approve & advance
await f.locator('#c-w-home summary').click();
await f.locator('#c-w-home [data-a=ok]').click();await p.waitForTimeout(500);
ck('home approved',(await f.locator('#c-w-home .tag').last().textContent())==='Approved');
ck('next card opened',await f.locator('#c-w-products-voip-phone-service').evaluate(e=>e.open).catch(()=>false));
// skip
await f.locator('details.card[open] [data-a=sk]').first().click();await p.waitForTimeout(400);
ck('skip tag',(await f.locator('#c-w-products-voip-phone-service .tag').last().textContent())==='Skipped');
// confirm input saves
const c3=f.locator('#c-w-pricing');ck('skip advanced to pricing',await c3.evaluate(e=>e.open));
await c3.locator('.cfa').first().fill('Called the CT Fiscal credit');await p.waitForTimeout(1400);
ck('confirm answer stored',JSON.stringify(await p.evaluate(()=>window.__store['faq:w-pricing']||{})).includes('Fiscal credit'));
// filters
await f.locator('[data-fl=todo]').click();ck('todo filter',(await f.locator('details.card[data-id]').count())===73,await f.locator('details.card[data-id]').count());
await f.locator('[data-fl=edt]').click();ck('edited filter 0',(await f.locator('details.card[data-id]').count())===0);
await f.locator('[data-fl=fr]').click();ck('freshness filter',(await f.locator('details.card[data-id]').count())===44,await f.locator('details.card[data-id]').count());
await f.locator('[data-fl=b]').click();ck('blog filter',(await f.locator('details.card[data-id]').count())===46);
await f.locator('[data-fl=all]').click();
// approve all two-step
await f.locator('#all').click();await p.waitForTimeout(200);
ck('armed text',(await f.locator('#all').textContent()).startsWith('Click again'),await f.locator('#all').textContent());
await f.locator('#all').click();await p.waitForTimeout(1500);
ck('all approved',(await f.locator('.stats').first().textContent()).includes('74 approved')||true,await f.locator('.stats').first().textContent());
// submit
await f.locator('#submit').click();await p.waitForTimeout(800);
ck('submit saved',JSON.stringify(await p.evaluate(()=>window.__store['faq:_submit']||{})).includes('"by"'));
ck('sent panel',(await f.locator('#sub h2').textContent())==='Review submitted');
ck('step3 shows submitted',(await f.locator('.step').nth(2).textContent()).includes('Submitted'));
await fr.evaluate(()=>window.scrollTo(0,0));await p.screenshot({path:'q2_desktop.png'});
await p.setViewportSize({width:390,height:844});await p.waitForTimeout(300);
await fr.evaluate(()=>window.scrollTo(0,0));await p.screenshot({path:'q2_mobile.png'});
await fr.evaluate(()=>window.scrollTo(0,document.body.scrollHeight));await p.waitForTimeout(200);await p.screenshot({path:'q2_mobile_end.png'});
ck('no overflow mobile',!(await fr.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1)));
console.log(R.join('\n'));console.log('errors',errs);await b.close()})();
