// node build/preview.js <insert> <t> <out.png>  -> one frame of an insert, for review
const { chromium } = require('playwright');const path=require('path');
(async()=>{const [n,t,out]=process.argv.slice(2);const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
await p.goto('file://'+path.resolve(__dirname,'..','inserts','insert.html'));await p.waitForTimeout(800);
await p.evaluate(([n,t])=>window.setT(n,t),[n,parseFloat(t)]);await p.waitForTimeout(200);await p.screenshot({path:out});await b.close()})();
